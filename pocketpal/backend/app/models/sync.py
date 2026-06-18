from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt


class ManualSyncEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    local_transaction_uuid: UUID
    account_id: UUID
    client_revision: StrictInt = Field(default=1, gt=0)
    currency: str = Field(min_length=3, max_length=3)
    amount_minor: StrictInt
    transaction_type: Literal["income", "expense", "transfer"]
    category: str | None = None
    vendor: str | None = None
    description: str | None = None
    ledger_cutoff_at: datetime
    match_state: Literal["not_required", "match_pending", "matched", "unmatched_review"] = (
        "match_pending"
    )


class ManualSyncRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sync_batch_id: UUID
    timezone: str
    entries: list[ManualSyncEntry]


class ManualSyncResult(BaseModel):
    local_transaction_uuid: UUID
    server_transaction_id: UUID | None = None
    status: Literal["inserted", "updated", "stale_ignored", "already_synced", "failed"]
    error: str | None = None


class ManualSyncResponse(BaseModel):
    sync_batch_id: UUID
    results: list[ManualSyncResult]

