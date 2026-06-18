from fastapi import APIRouter, Depends

from app.auth import CurrentUser, get_current_user
from app.db import Database, get_db
from app.models.webhook import MockConnectRequest, MockConnectResponse
from app.services.onboarding import OnboardingService

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("")
async def list_accounts(
    current_user: CurrentUser = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    rows = await db.fetch(
        """
        SELECT id, account_name, account_type, currency, provider_name,
               provider_account_id, oauth_status, reconciliation_enabled,
               initialized_at, last_reconciled_snapshot_at
        FROM public.accounts
        WHERE user_id = $1
        ORDER BY created_at ASC
        """,
        current_user.user_id,
    )
    return [dict(row) for row in rows]


@router.post("/mock-connect", response_model=MockConnectResponse)
async def mock_connect(
    payload: MockConnectRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result = await OnboardingService(db).mock_connect(current_user.user_id, payload)
    return MockConnectResponse(**result)

