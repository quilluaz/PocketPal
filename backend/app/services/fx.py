from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.services.money import convert_minor_to_base


@dataclass(frozen=True)
class FXValuation:
    base_currency: str
    amount_minor_base: int | None
    exchange_rate_to_base: Decimal | None
    exchange_rate_source: str | None
    exchange_rate_as_of: datetime | None
    fx_valuation_status: str


class PostgresFXStore:
    def __init__(self, db: Any) -> None:
        self.db = db

    async def get_preferences(self, user_id: UUID) -> dict[str, Any]:
        row = await self.db.fetchrow(
            """
            INSERT INTO public.user_preferences (user_id)
            VALUES ($1)
            ON CONFLICT (user_id) DO UPDATE SET updated_at = public.user_preferences.updated_at
            RETURNING timezone, base_currency
            """,
            user_id,
        )
        assert row is not None
        return dict(row)

    async def get_currency(self, code: str) -> dict[str, Any] | None:
        row = await self.db.fetchrow(
            "SELECT code, exponent, name, symbol FROM public.currencies WHERE code = $1",
            code.upper(),
        )
        return dict(row) if row else None

    async def get_latest_exchange_rate(
        self,
        base_currency: str,
        quote_currency: str,
        rate_date,
    ) -> dict[str, Any] | None:
        row = await self.db.fetchrow(
            """
            SELECT base_currency, quote_currency, rate, rate_date, source, fetched_at
            FROM public.exchange_rates
            WHERE base_currency = $1
              AND quote_currency = $2
              AND rate_date <= $3
            ORDER BY rate_date DESC, fetched_at DESC
            LIMIT 1
            """,
            base_currency,
            quote_currency,
            rate_date,
        )
        return dict(row) if row else None


def local_rate_date(ledger_cutoff_at: datetime, timezone_name: str):
    try:
        tz = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("UTC")
    if ledger_cutoff_at.tzinfo is None:
        ledger_cutoff_at = ledger_cutoff_at.replace(tzinfo=ZoneInfo("UTC"))
    return ledger_cutoff_at.astimezone(tz).date()


class FXService:
    def __init__(self, store: Any) -> None:
        self.store = store

    async def value_transaction(
        self,
        user_id: UUID,
        currency: str,
        amount_minor: int,
        ledger_cutoff_at: datetime,
        timezone_name: str | None = None,
    ) -> FXValuation:
        currency = currency.upper()
        preferences = await self.store.get_preferences(user_id)
        base_currency = preferences["base_currency"].strip().upper()
        timezone_name = timezone_name or preferences["timezone"]

        source_currency = await self.store.get_currency(currency)
        base = await self.store.get_currency(base_currency)
        if source_currency is None or base is None:
            return FXValuation(
                base_currency=base_currency,
                amount_minor_base=None,
                exchange_rate_to_base=None,
                exchange_rate_source=None,
                exchange_rate_as_of=None,
                fx_valuation_status="missing",
            )

        if currency == base_currency:
            return FXValuation(
                base_currency=base_currency,
                amount_minor_base=amount_minor,
                exchange_rate_to_base=Decimal("1"),
                exchange_rate_source="identity",
                exchange_rate_as_of=ledger_cutoff_at,
                fx_valuation_status="not_required",
            )

        rate_date = local_rate_date(ledger_cutoff_at, timezone_name)
        rate = await self.store.get_latest_exchange_rate(base_currency, currency, rate_date)
        if rate is None:
            return FXValuation(
                base_currency=base_currency,
                amount_minor_base=None,
                exchange_rate_to_base=None,
                exchange_rate_source=None,
                exchange_rate_as_of=None,
                fx_valuation_status="missing",
            )

        amount_minor_base = convert_minor_to_base(
            amount_minor=amount_minor,
            source_exponent=source_currency["exponent"],
            base_exponent=base["exponent"],
            exchange_rate_to_base=Decimal(rate["rate"]),
        )
        return FXValuation(
            base_currency=base_currency,
            amount_minor_base=amount_minor_base,
            exchange_rate_to_base=Decimal(rate["rate"]),
            exchange_rate_source=rate["source"],
            exchange_rate_as_of=datetime.combine(rate["rate_date"], datetime.min.time()).replace(
                tzinfo=ZoneInfo("UTC")
            ),
            fx_valuation_status="final",
        )

