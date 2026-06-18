from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.models.webhook import HistoricalTransactionIn, MockConnectRequest
from app.services.fx import FXService, PostgresFXStore


def normalize_dt(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def calculate_day_zero_opening_balance(
    snapshot_balance_minor: int,
    historical_transactions: list[HistoricalTransactionIn],
    as_of: datetime,
    currency: str,
) -> int:
    cutoff = normalize_dt(as_of)
    historical_sum = sum(
        tx.amount_minor
        for tx in historical_transactions
        if tx.currency.upper() == currency.upper() and normalize_dt(tx.ledger_cutoff_at) <= cutoff
    )
    return snapshot_balance_minor - historical_sum


class OnboardingService:
    def __init__(self, db: Any) -> None:
        self.db = db

    async def mock_connect(self, user_id: UUID, request: MockConnectRequest) -> dict[str, Any]:
        fx = FXService(PostgresFXStore(self.db))
        opening_balance = calculate_day_zero_opening_balance(
            request.day_zero_current_balance_minor,
            request.historical_transactions,
            request.as_of,
            request.currency,
        )
        as_of = normalize_dt(request.as_of)

        async for conn in self.db.acquire():
            async with conn.transaction():
                account = await conn.fetchrow(
                    """
                    INSERT INTO public.accounts (
                      user_id, account_name, account_type, currency,
                      provider_name, provider_account_id, reconciliation_enabled
                    )
                    VALUES ($1, $2, 'depository', $3, $4, $5, TRUE)
                    ON CONFLICT (user_id, provider_name, provider_account_id)
                    WHERE provider_account_id IS NOT NULL
                    DO UPDATE SET
                      account_name = EXCLUDED.account_name,
                      currency = EXCLUDED.currency,
                      oauth_status = 'active',
                      reconciliation_enabled = TRUE,
                      updated_at = now()
                    RETURNING id
                    """,
                    user_id,
                    request.account_name,
                    request.currency.upper(),
                    request.provider_name,
                    request.provider_account_id,
                )
                account_id = account["id"]

                snapshot_value = await fx.value_transaction(
                    user_id,
                    request.currency,
                    request.day_zero_current_balance_minor,
                    as_of,
                )
                available_value = None
                if request.available_balance_minor is not None:
                    available_value = await fx.value_transaction(
                        user_id,
                        request.currency,
                        request.available_balance_minor,
                        as_of,
                    )

                await conn.fetchrow(
                    """
                    INSERT INTO public.account_balance_snapshots (
                      user_id, account_id, currency, current_balance_minor,
                      available_balance_minor, base_currency, current_balance_minor_base,
                      available_balance_minor_base, exchange_rate_to_base,
                      exchange_rate_as_of, provider_name, provider_snapshot_id,
                      idempotency_key, as_of
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    ON CONFLICT (account_id, idempotency_key) DO NOTHING
                    RETURNING id
                    """,
                    user_id,
                    account_id,
                    request.currency.upper(),
                    request.day_zero_current_balance_minor,
                    request.available_balance_minor,
                    snapshot_value.base_currency,
                    snapshot_value.amount_minor_base,
                    available_value.amount_minor_base if available_value else None,
                    snapshot_value.exchange_rate_to_base,
                    snapshot_value.exchange_rate_as_of,
                    request.provider_name,
                    f"day_zero:{request.provider_account_id}:{as_of.isoformat()}",
                    f"day_zero:{request.provider_account_id}:{as_of.isoformat()}",
                    as_of,
                )

                for tx in request.historical_transactions:
                    valuation = await fx.value_transaction(
                        user_id,
                        tx.currency,
                        tx.amount_minor,
                        tx.ledger_cutoff_at,
                    )
                    await conn.execute(
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
                        account_id,
                        tx.currency.upper(),
                        tx.amount_minor,
                        valuation.base_currency,
                        valuation.amount_minor_base,
                        valuation.exchange_rate_to_base,
                        valuation.exchange_rate_source,
                        valuation.exchange_rate_as_of,
                        valuation.fx_valuation_status,
                        request.provider_name,
                        tx.external_transaction_id,
                        f"bank:{request.provider_name}:{tx.external_transaction_id}",
                        tx.transaction_type,
                        tx.category,
                        tx.vendor,
                        tx.description,
                        normalize_dt(tx.ledger_cutoff_at),
                    )

                opening_value = await fx.value_transaction(
                    user_id,
                    request.currency,
                    opening_balance,
                    as_of,
                )
                await conn.execute(
                    """
                    INSERT INTO public.transactions (
                      user_id, account_id, currency, amount_minor,
                      base_currency, amount_minor_base, exchange_rate_to_base,
                      exchange_rate_source, exchange_rate_as_of, fx_valuation_status,
                      source, provider_name, idempotency_key, ledger_status,
                      match_state, transaction_type, description, ledger_cutoff_at,
                      affects_ledger, affects_analytics
                    )
                    VALUES (
                      $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                      'system', 'pocketpal', $11, 'cleared',
                      'not_required', 'initial_balance', 'Day Zero opening balance',
                      $12, TRUE, FALSE
                    )
                    ON CONFLICT (account_id)
                    WHERE transaction_type = 'initial_balance'
                    DO NOTHING
                    """,
                    user_id,
                    account_id,
                    request.currency.upper(),
                    opening_balance,
                    opening_value.base_currency,
                    opening_value.amount_minor_base,
                    opening_value.exchange_rate_to_base,
                    opening_value.exchange_rate_source,
                    opening_value.exchange_rate_as_of,
                    opening_value.fx_valuation_status,
                    f"opening_balance:{account_id}",
                    as_of,
                )

                await conn.execute(
                    """
                    UPDATE public.accounts
                    SET initialized_at = COALESCE(initialized_at, $3),
                        reconciliation_enabled = TRUE,
                        oauth_status = 'active',
                        updated_at = now()
                    WHERE user_id = $1 AND id = $2
                    """,
                    user_id,
                    account_id,
                    as_of,
                )

        return {
            "account_id": str(account_id),
            "opening_balance_minor": opening_balance,
            "historical_transaction_count": len(request.historical_transactions),
        }

