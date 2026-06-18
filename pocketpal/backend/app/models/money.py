from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


class CurrencyOut(BaseModel):
    code: str
    exponent: int
    name: str
    symbol: str | None = None


class ExchangeRateOut(BaseModel):
    base_currency: str
    quote_currency: str
    rate: Decimal
    rate_date: date
    source: str
    fetched_at: datetime


class FXValuationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    base_currency: str
    amount_minor_base: int | None
    exchange_rate_to_base: Decimal | None
    exchange_rate_source: str | None
    exchange_rate_as_of: datetime | None
    fx_valuation_status: Literal["not_required", "provisional", "final", "missing"]

