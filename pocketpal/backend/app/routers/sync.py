from fastapi import APIRouter, Depends

from app.auth import CurrentUser, get_current_user
from app.db import Database, get_db
from app.models.sync import ManualSyncRequest, ManualSyncResponse
from app.services.sync import PostgresSyncStore, SyncService

router = APIRouter(tags=["sync"])


@router.post("/sync", response_model=ManualSyncResponse)
async def sync_manual_entries(
    payload: ManualSyncRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    return await SyncService(PostgresSyncStore(db)).sync_manual_entries(
        current_user.user_id,
        payload,
    )

