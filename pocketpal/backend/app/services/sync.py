from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from app.models.sync import ManualSyncEntry, ManualSyncRequest, ManualSyncResponse, ManualSyncResult
from app.services.fx import FXService, PostgresFXStore

FINAL_STATUSES = {"cleared", "adjusted"}
MUTABLE_MATCH_STATES = {"not_required", "match_pending"}


def utc_now() -> datetime:
    return datetime.now(UTC)


def normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def manual_idempotency_key(local_transaction_uuid: UUID) -> str:
    return f"manual:{local_transaction_uuid}"


class PostgresSyncStore:
    def __init__(self, db: Any) -> None:
        self.db = db
        self.fx = FXService(PostgresFXStore(db))

    async def get_account(self, user_id: UUID, account_id: UUID) -> dict[str, Any] | None:
        row = await self.db.fetchrow(
            """
            SELECT id, provider_name, currency, reconciliation_enabled, last_reconciled_snapshot_at
            FROM public.accounts
            WHERE user_id = $1 AND id = $2
            """,
            user_id,
            account_id,
        )
        return dict(row) if row else None

    async def currency_exists(self, currency: str) -> bool:
        row = await self.db.fetchrow(
            "SELECT 1 FROM public.currencies WHERE code = $1 AND is_active = TRUE",
            currency.upper(),
        )
        return row is not None

    async def value_entry(
        self,
        user_id: UUID,
        entry: ManualSyncEntry,
        timezone_name: str,
    ):
        return await self.fx.value_transaction(
            user_id=user_id,
            currency=entry.currency,
            amount_minor=entry.amount_minor,
            ledger_cutoff_at=entry.ledger_cutoff_at,
            timezone_name=timezone_name,
        )

    async def get_manual_transaction(
        self,
        user_id: UUID,
        idempotency_key: str,
    ) -> dict[str, Any] | None:
        row = await self.db.fetchrow(
            """
            SELECT id, client_revision, ledger_status, match_state
            FROM public.transactions
            WHERE user_id = $1
              AND source = 'manual'
              AND idempotency_key = $2
            """,
            user_id,
            idempotency_key,
        )
        return dict(row) if row else None

    async def insert_manual_transaction(self, payload: dict[str, Any]) -> UUID:
        row = await self.db.fetchrow(
            """
            INSERT INTO public.transactions (
              user_id, account_id, currency, amount_minor,
              base_currency, amount_minor_base, exchange_rate_to_base,
              exchange_rate_source, exchange_rate_as_of, fx_valuation_status,
              source, provider_name, idempotency_key, sync_batch_id,
              local_transaction_uuid, client_revision, ledger_status, match_state,
              transaction_type, category, vendor, description, ledger_cutoff_at,
              server_received_at, is_backfilled, requires_reconciliation_review,
              affects_ledger, affects_analytics
            )
            VALUES (
              $1, $2, $3, $4,
              $5, $6, $7,
              $8, $9, $10,
              'manual', 'manual', $11, $12,
              $13, $14, $15, $16,
              $17, $18, $19, $20, $21,
              now(), $22, $23,
              TRUE, $24
            )
            RETURNING id
            """,
            payload["user_id"],
            payload["account_id"],
            payload["currency"],
            payload["amount_minor"],
            payload["base_currency"],
            payload["amount_minor_base"],
            payload["exchange_rate_to_base"],
            payload["exchange_rate_source"],
            payload["exchange_rate_as_of"],
            payload["fx_valuation_status"],
            payload["idempotency_key"],
            payload["sync_batch_id"],
            payload["local_transaction_uuid"],
            payload["client_revision"],
            payload["ledger_status"],
            payload["match_state"],
            payload["transaction_type"],
            payload["category"],
            payload["vendor"],
            payload["description"],
            payload["ledger_cutoff_at"],
            payload["is_backfilled"],
            payload["requires_reconciliation_review"],
            payload["affects_analytics"],
        )
        assert row is not None
        return row["id"]

    async def update_manual_transaction(self, transaction_id: UUID, payload: dict[str, Any]) -> UUID:
        row = await self.db.fetchrow(
            """
            UPDATE public.transactions
            SET amount_minor = $2,
                base_currency = $3,
                amount_minor_base = $4,
                exchange_rate_to_base = $5,
                exchange_rate_source = $6,
                exchange_rate_as_of = $7,
                fx_valuation_status = $8,
                ledger_cutoff_at = $9,
                client_revision = $10,
                category = $11,
                vendor = $12,
                description = $13,
                is_backfilled = $14,
                requires_reconciliation_review = $15,
                affects_analytics = $16,
                updated_at = now()
            WHERE id = $1
              AND source = 'manual'
              AND ledger_status = 'pending'
              AND match_state IN ('not_required', 'match_pending')
            RETURNING id
            """,
            transaction_id,
            payload["amount_minor"],
            payload["base_currency"],
            payload["amount_minor_base"],
            payload["exchange_rate_to_base"],
            payload["exchange_rate_source"],
            payload["exchange_rate_as_of"],
            payload["fx_valuation_status"],
            payload["ledger_cutoff_at"],
            payload["client_revision"],
            payload["category"],
            payload["vendor"],
            payload["description"],
            payload["is_backfilled"],
            payload["requires_reconciliation_review"],
            payload["affects_analytics"],
        )
        assert row is not None
        return row["id"]


class SyncService:
    def __init__(self, store: Any, now_factory=utc_now) -> None:
        self.store = store
        self.now_factory = now_factory

    async def sync_manual_entries(
        self,
        user_id: UUID,
        request: ManualSyncRequest,
    ) -> ManualSyncResponse:
        results = []
        for entry in request.entries:
            results.append(await self._sync_entry(user_id, request, entry))
        return ManualSyncResponse(sync_batch_id=request.sync_batch_id, results=results)

    async def _sync_entry(
        self,
        user_id: UUID,
        request: ManualSyncRequest,
        entry: ManualSyncEntry,
    ) -> ManualSyncResult:
        try:
            account = await self.store.get_account(user_id, entry.account_id)
            if account is None:
                return ManualSyncResult(
                    local_transaction_uuid=entry.local_transaction_uuid,
                    status="failed",
                    error="account_not_found",
                )
            if not await self.store.currency_exists(entry.currency):
                return ManualSyncResult(
                    local_transaction_uuid=entry.local_transaction_uuid,
                    status="failed",
                    error="currency_not_supported",
                )

            ledger_cutoff_at = normalize_timestamp(entry.ledger_cutoff_at)
            if ledger_cutoff_at > self.now_factory() + timedelta(hours=24):
                return ManualSyncResult(
                    local_transaction_uuid=entry.local_transaction_uuid,
                    status="failed",
                    error="ledger_cutoff_too_far_in_future",
                )

            last_reconciled = account.get("last_reconciled_snapshot_at")
            is_backfilled = bool(last_reconciled and ledger_cutoff_at <= normalize_timestamp(last_reconciled))
            ledger_status = "cleared" if account.get("provider_name") == "manual" else "pending"
            match_state = "not_required" if ledger_status == "cleared" else entry.match_state
            affects_analytics = entry.transaction_type in {"income", "expense"}
            valuation = await self.store.value_entry(user_id, entry, request.timezone)
            idempotency_key = manual_idempotency_key(entry.local_transaction_uuid)
            payload = {
                "user_id": user_id,
                "account_id": entry.account_id,
                "currency": entry.currency.upper(),
                "amount_minor": entry.amount_minor,
                "base_currency": valuation.base_currency,
                "amount_minor_base": valuation.amount_minor_base,
                "exchange_rate_to_base": valuation.exchange_rate_to_base,
                "exchange_rate_source": valuation.exchange_rate_source,
                "exchange_rate_as_of": valuation.exchange_rate_as_of,
                "fx_valuation_status": valuation.fx_valuation_status,
                "idempotency_key": idempotency_key,
                "sync_batch_id": request.sync_batch_id,
                "local_transaction_uuid": entry.local_transaction_uuid,
                "client_revision": entry.client_revision,
                "ledger_status": ledger_status,
                "match_state": match_state,
                "transaction_type": entry.transaction_type,
                "category": entry.category,
                "vendor": entry.vendor,
                "description": entry.description,
                "ledger_cutoff_at": ledger_cutoff_at,
                "is_backfilled": is_backfilled,
                "requires_reconciliation_review": is_backfilled,
                "affects_analytics": affects_analytics,
            }

            existing = await self.store.get_manual_transaction(user_id, idempotency_key)
            if existing is None:
                transaction_id = await self.store.insert_manual_transaction(payload)
                return ManualSyncResult(
                    local_transaction_uuid=entry.local_transaction_uuid,
                    server_transaction_id=transaction_id,
                    status="inserted",
                )

            if entry.client_revision == existing["client_revision"]:
                return ManualSyncResult(
                    local_transaction_uuid=entry.local_transaction_uuid,
                    server_transaction_id=existing["id"],
                    status="already_synced",
                )
            if entry.client_revision < existing["client_revision"]:
                return ManualSyncResult(
                    local_transaction_uuid=entry.local_transaction_uuid,
                    server_transaction_id=existing["id"],
                    status="stale_ignored",
                )
            if (
                existing["ledger_status"] in FINAL_STATUSES
                or existing["match_state"] not in MUTABLE_MATCH_STATES
            ):
                return ManualSyncResult(
                    local_transaction_uuid=entry.local_transaction_uuid,
                    server_transaction_id=existing["id"],
                    status="failed",
                    error="transaction_finalized",
                )

            transaction_id = await self.store.update_manual_transaction(existing["id"], payload)
            return ManualSyncResult(
                local_transaction_uuid=entry.local_transaction_uuid,
                server_transaction_id=transaction_id,
                status="updated",
            )
        except Exception as exc:  # pragma: no cover - defensive API boundary
            return ManualSyncResult(
                local_transaction_uuid=entry.local_transaction_uuid,
                status="failed",
                error=str(exc),
            )

