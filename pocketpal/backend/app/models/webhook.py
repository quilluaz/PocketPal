from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt


class HistoricalTransactionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    external_transaction_id: str
    amount_minor: StrictInt
    currency: str = Field(min_length=3, max_length=3)
    vendor: str | None = None
    transaction_type: Literal["income", "expense", "transfer"]
    ledger_cutoff_at: datetime
    category: str | None = None
    description: str | None = None


class MockConnectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_name: str
    currency: str = Field(min_length=3, max_length=3)
    provider_name: str = "mock_bank"
    provider_account_id: str
    day_zero_current_balance_minor: StrictInt
    available_balance_minor: StrictInt | None = None
    as_of: datetime
    historical_transactions: list[HistoricalTransactionIn] = []


class MockConnectResponse(BaseModel):
    account_id: str
    opening_balance_minor: int
    historical_transaction_count: int


class MockWebhookSnapshot(BaseModel):
    current_balance_minor: StrictInt
    available_balance_minor: StrictInt | None = None
    currency: str = Field(min_length=3, max_length=3)
    as_of: datetime


class MockWebhookTransaction(BaseModel):
    external_transaction_id: str
    amount_minor: StrictInt
    currency: str = Field(min_length=3, max_length=3)
    vendor: str | None = None
    transaction_type: Literal["income", "expense", "transfer"]
    ledger_cutoff_at: datetime
    category: str | None = None
    description: str | None = None


class MockBankWebhookPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    provider_name: str = "mock_bank"
    provider_account_id: str
    event_type: str
    snapshot: MockWebhookSnapshot | None = None
    transactions: list[MockWebhookTransaction] = []
    error_code: str | None = None
    message: str | None = None

