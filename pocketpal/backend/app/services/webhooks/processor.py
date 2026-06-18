import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.models.webhook import MockBankWebhookPayload
from app.services.fx import FXService, PostgresFXStore
from app.services.reconciliation import ReconciliationService


def normalize_dt(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def bank_transaction_idempotency_key(provider: str, event_id: str, external_transaction_id: str) -> str:
    return f"bank:{provider}:{event_id}:{external_transaction_id}"


def snapshot_idempotency_key(provider: str, event_id: str) -> str:
    return f"snapshot:{provider}:{event_id}"


class WebhookProcessor:
    def __init__(self, db: Any) -> None:
        self.db = db

    async def process_mock_bank(self, payload: MockBankWebhookPayload) -> None:
        account = await self.db.fetchrow(
            """
            SELECT id, user_id, reconciliation_enabled
            FROM public.accounts
            WHERE provider_name = $1 AND provider_account_id = $2
            ORDER BY created_at ASC
            LIMIT 1
            """,
            payload.provider_name,
            payload.provider_account_id,
        )
        if account is None:
            return

        user_id: UUID = account["user_id"]
        await self.db.execute(
            """
            INSERT INTO public.account_connection_events (
              user_id, account_id, provider_name, event_type,
              provider_error_code, provider_payload, handled
            )
            VALUES ($1, $2, $3, $4, $5, $6::jsonb, TRUE)
            """,
            user_id,
            account["id"],
            payload.provider_name,
            payload.event_type,
            payload.error_code,
            json.dumps(payload.model_dump(mode="json")),
        )

        if payload.event_type == "error":
            await self.db.execute(
                """
                UPDATE public.accounts
                SET oauth_status = 'reconnect_required',
                    oauth_error_code = $3,
                    oauth_error_message = $4,
                    oauth_last_failed_at = now(),
                    reconciliation_enabled = FALSE,
                    updated_at = now()
                WHERE user_id = $1 AND id = $2
                """,
                user_id,
                account["id"],
                payload.error_code,
                payload.message,
            )
            return

        fx = FXService(PostgresFXStore(self.db))
        for tx in payload.transactions:
            valuation = await fx.value_transaction(
                user_id,
                tx.currency,
                tx.amount_minor,
                tx.ledger_cutoff_at,
            )
            await self.db.execute(
                """
                INSERT INTO public.transactions (
                  user_id, account_id, currency, amount_minor,
                  base_currency, amount_minor_base, exchange_rate_to_base,
                  exchange_rate_source, exchange_rate_as_of, fx_valuation_status,
                  source, provider_name, external_transaction_id, idempotency_key,
                  ledger_status, match_state, transaction_type, category, vendor,
                  description, ledger_cutoff_at, affects_ledger, affects_analytics
                )
                VALUES (
                  $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                  'sandbox_bank', $11, $12, $13,
                  'cleared', 'matched', $14, $15, $16, $17, $18, TRUE, TRUE
                )
                ON CONFLICT (user_id, source, idempotency_key)
                WHERE idempotency_key IS NOT NULL
                DO NOTHING
                """,
                user_id,
                account["id"],
                tx.currency.upper(),
                tx.amount_minor,
                valuation.base_currency,
                valuation.amount_minor_base,
                valuation.exchange_rate_to_base,
                valuation.exchange_rate_source,
                valuation.exchange_rate_as_of,
                valuation.fx_valuation_status,
                payload.provider_name,
                tx.external_transaction_id,
                bank_transaction_idempotency_key(
                    payload.provider_name,
                    payload.event_id,
                    tx.external_transaction_id,
                ),
                tx.transaction_type,
                tx.category,
                tx.vendor,
                tx.description,
                normalize_dt(tx.ledger_cutoff_at),
            )

        if payload.snapshot is not None:
            snapshot_value = await fx.value_transaction(
                user_id,
                payload.snapshot.currency,
                payload.snapshot.current_balance_minor,
                payload.snapshot.as_of,
            )
            available_value = None
            if payload.snapshot.available_balance_minor is not None:
                available_value = await fx.value_transaction(
                    user_id,
                    payload.snapshot.currency,
                    payload.snapshot.available_balance_minor,
                    payload.snapshot.as_of,
                )
            snapshot = await self.db.fetchrow(
                """
                INSERT INTO public.account_balance_snapshots (
                  user_id, account_id, currency, current_balance_minor,
                  available_balance_minor, base_currency, current_balance_minor_base,
                  available_balance_minor_base, exchange_rate_to_base,
                  exchange_rate_as_of, provider_name, provider_snapshot_id,
                  idempotency_key, as_of
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                ON CONFLICT (account_id, idempotency_key)
                DO UPDATE SET received_at = public.account_balance_snapshots.received_at
                RETURNING id
                """,
                user_id,
                account["id"],
                payload.snapshot.currency.upper(),
                payload.snapshot.current_balance_minor,
                payload.snapshot.available_balance_minor,
                snapshot_value.base_currency,
                snapshot_value.amount_minor_base,
                available_value.amount_minor_base if available_value else None,
                snapshot_value.exchange_rate_to_base,
                snapshot_value.exchange_rate_as_of,
                payload.provider_name,
                payload.event_id,
                snapshot_idempotency_key(payload.provider_name, payload.event_id),
                normalize_dt(payload.snapshot.as_of),
            )
            if account["reconciliation_enabled"] and snapshot is not None:
                await ReconciliationService(self.db).reconcile_snapshot(user_id, snapshot["id"])

