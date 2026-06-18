from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.services.fx import FXService, PostgresFXStore


def normalize_dt(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def compute_snapshot_delta(
    snapshot_balance_minor: int,
    snapshot_as_of: datetime,
    snapshot_currency: str,
    transactions: list[dict[str, Any]],
) -> int:
    cutoff = normalize_dt(snapshot_as_of)
    ledger_sum = sum(
        int(tx["amount_minor"])
        for tx in transactions
        if tx.get("currency", "").upper() == snapshot_currency.upper()
        and tx.get("affects_ledger") is True
        and tx.get("ledger_status") in {"cleared", "adjusted"}
        and normalize_dt(tx["ledger_cutoff_at"]) <= cutoff
    )
    return snapshot_balance_minor - ledger_sum


class ReconciliationService:
    def __init__(self, db: Any) -> None:
        self.db = db

    async def reconcile_snapshot(self, user_id: UUID, snapshot_id: UUID) -> dict[str, Any]:
        snapshot = await self.db.fetchrow(
            """
            SELECT s.*, a.reconciliation_enabled
            FROM public.account_balance_snapshots s
            JOIN public.accounts a ON a.id = s.account_id
            WHERE s.user_id = $1 AND s.id = $2
            """,
            user_id,
            snapshot_id,
        )
        if snapshot is None:
            return {"status": "snapshot_not_found", "delta_amount_minor": None}
        if not snapshot["reconciliation_enabled"]:
            return {"status": "reconciliation_disabled", "delta_amount_minor": None}

        ledger_sum = await self.db.fetchrow(
            """
            SELECT COALESCE(SUM(amount_minor), 0) AS amount_minor
            FROM public.transactions
            WHERE user_id = $1
              AND account_id = $2
              AND currency = $3
              AND affects_ledger = TRUE
              AND ledger_cutoff_at <= $4
              AND ledger_status IN ('cleared', 'adjusted')
            """,
            user_id,
            snapshot["account_id"],
            snapshot["currency"],
            snapshot["as_of"],
        )
        local_sum = int(ledger_sum["amount_minor"]) if ledger_sum else 0
        delta = int(snapshot["current_balance_minor"]) - local_sum
        if delta == 0:
            await self.db.execute(
                """
                UPDATE public.accounts
                SET last_reconciled_snapshot_at = GREATEST(
                      COALESCE(last_reconciled_snapshot_at, '-infinity'::timestamptz),
                      $3
                    ),
                    updated_at = now()
                WHERE user_id = $1 AND id = $2
                """,
                user_id,
                snapshot["account_id"],
                snapshot["as_of"],
            )
            return {"status": "balanced", "delta_amount_minor": 0}

        fx = FXService(PostgresFXStore(self.db))
        valuation = await fx.value_transaction(
            user_id,
            snapshot["currency"],
            delta,
            snapshot["as_of"],
        )
        transaction = await self.db.fetchrow(
            """
            INSERT INTO public.transactions (
              user_id, account_id, currency, amount_minor,
              base_currency, amount_minor_base, exchange_rate_to_base,
              exchange_rate_source, exchange_rate_as_of, fx_valuation_status,
              source, provider_name, idempotency_key, ledger_status, match_state,
              transaction_type, description, ledger_cutoff_at,
              affects_ledger, affects_analytics
            )
            VALUES (
              $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
              'system', 'pocketpal', $11, 'adjusted', 'not_required',
              'reconciliation', 'Snapshot reconciliation adjustment', $12,
              TRUE, FALSE
            )
            ON CONFLICT (user_id, source, idempotency_key)
            WHERE idempotency_key IS NOT NULL
            DO NOTHING
            RETURNING id
            """,
            user_id,
            snapshot["account_id"],
            snapshot["currency"],
            delta,
            valuation.base_currency,
            valuation.amount_minor_base,
            valuation.exchange_rate_to_base,
            valuation.exchange_rate_source,
            valuation.exchange_rate_as_of,
            valuation.fx_valuation_status,
            f"reconciliation:{snapshot_id}",
            snapshot["as_of"],
        )
        if transaction is not None:
            await self.db.execute(
                """
                INSERT INTO public.reconciliation_adjustments (
                  user_id, account_id, snapshot_id, adjustment_transaction_id,
                  delta_amount_minor, currency
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (account_id, snapshot_id) DO NOTHING
                """,
                user_id,
                snapshot["account_id"],
                snapshot_id,
                transaction["id"],
                delta,
                snapshot["currency"],
            )
        await self.db.execute(
            """
            UPDATE public.accounts
            SET last_reconciled_snapshot_at = GREATEST(
                  COALESCE(last_reconciled_snapshot_at, '-infinity'::timestamptz),
                  $3
                ),
                updated_at = now()
            WHERE user_id = $1 AND id = $2
            """,
            user_id,
            snapshot["account_id"],
            snapshot["as_of"],
        )
        return {"status": "adjusted", "delta_amount_minor": delta}

