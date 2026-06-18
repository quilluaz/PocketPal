from fastapi import APIRouter, Depends

from app.auth import CurrentUser, get_current_user
from app.db import Database, get_db
from app.models.dashboard import DashboardOut
from app.services.dashboard import DashboardService

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardOut)
async def dashboard(
    current_user: CurrentUser = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    return await DashboardService(db).build(current_user.user_id)

