from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.models.sync import ManualSyncEntry, ManualSyncRequest
from app.services.fx import FXValuation
from app.services.sync import SyncService, manual_idempotency_key


class InMemorySyncStore:
    def __init__(self):
        self.account_id = uuid4()
        self.transactions = {}

    async def get_account(self, user_id, account_id):
        if account_id != self.account_id:
            return None
        return {
            "id": account_id,
            "provider_name": "mock_bank",
            "last_reconciled_snapshot_at": None,
        }

    async def currency_exists(self, currency):
        return currency in {"PHP", "USD"}

    async def value_entry(self, user_id, entry, timezone_name):
        return FXValuation(
            base_currency="PHP",
            amount_minor_base=entry.amount_minor,
            exchange_rate_to_base=Decimal("1"),
            exchange_rate_source="identity",
            exchange_rate_as_of=entry.ledger_cutoff_at,
            fx_valuation_status="not_required",
        )

    async def upsert_manual_transaction(self, payload):
        existing = self.transactions.get(payload["idempotency_key"])
        if existing is None:
            transaction_id = uuid4()
            self.transactions[payload["idempotency_key"]] = {
                "id": transaction_id,
                "amount_minor": payload["amount_minor"],
                "client_revision": payload["client_revision"],
                "ledger_status": payload["ledger_status"],
                "match_state": payload["match_state"],
            }
            return {"id": transaction_id, "status": "inserted", "error": None}

        if payload["client_revision"] == existing["client_revision"]:
            return {"id": existing["id"], "status": "already_synced", "error": None}
        if payload["client_revision"] < existing["client_revision"]:
            return {"id": existing["id"], "status": "stale_ignored", "error": None}
        if existing["ledger_status"] in {"cleared", "adjusted"} or existing[
            "match_state"
        ] not in {"not_required", "match_pending"}:
            return {
                "id": existing["id"],
                "status": "failed",
                "error": "transaction_finalized",
            }

        existing["amount_minor"] = payload["amount_minor"]
        existing["client_revision"] = payload["client_revision"]
        return {"id": existing["id"], "status": "updated", "error": None}


def make_request(account_id, local_id, amount_minor, revision):
    return ManualSyncRequest(
        sync_batch_id=uuid4(),
        timezone="Asia/Manila",
        entries=[
            ManualSyncEntry(
                local_transaction_uuid=local_id,
                account_id=account_id,
                client_revision=revision,
                currency="PHP",
                amount_minor=amount_minor,
                transaction_type="expense",
                category="food",
                vendor="Shopwise",
                ledger_cutoff_at=datetime(2026, 6, 19, 6, 0, tzinfo=UTC),
            )
        ],
    )


@pytest.mark.asyncio
async def test_offline_edit_revision_two_wins():
    store = InMemorySyncStore()
    service = SyncService(store, now_factory=lambda: datetime(2026, 6, 19, 7, 0, tzinfo=UTC))
    user_id = UUID("00000000-0000-4000-8000-000000000001")
    local_id = uuid4()

    first = await service.sync_manual_entries(user_id, make_request(store.account_id, local_id, -50000, 1))
    second = await service.sync_manual_entries(user_id, make_request(store.account_id, local_id, -5000, 2))

    key = manual_idempotency_key(local_id)
    assert first.results[0].status == "inserted"
    assert second.results[0].status == "updated"
    assert store.transactions[key]["amount_minor"] == -5000
    assert store.transactions[key]["client_revision"] == 2


@pytest.mark.asyncio
async def test_stale_overwrite_is_ignored():
    store = InMemorySyncStore()
    service = SyncService(store, now_factory=lambda: datetime(2026, 6, 19, 7, 0, tzinfo=UTC))
    user_id = UUID("00000000-0000-4000-8000-000000000001")
    local_id = uuid4()

    await service.sync_manual_entries(user_id, make_request(store.account_id, local_id, -5000, 2))
    stale = await service.sync_manual_entries(user_id, make_request(store.account_id, local_id, -50000, 1))

    key = manual_idempotency_key(local_id)
    assert stale.results[0].status == "stale_ignored"
    assert store.transactions[key]["amount_minor"] == -5000
