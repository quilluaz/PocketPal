from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth import CurrentUser, get_current_user
from app.db import Database, get_db

router = APIRouter(prefix="/preferences", tags=["preferences"])


class PreferencesOut(BaseModel):
    user_id: UUID
    timezone: str
    base_currency: str


class PreferencesPatch(BaseModel):
    timezone: str | None = Field(default=None, examples=["Asia/Manila"])
    base_currency: str | None = Field(default=None, min_length=3, max_length=3)


@router.get("", response_model=PreferencesOut)
async def get_preferences(
    current_user: CurrentUser = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    row = await db.fetchrow(
        """
        INSERT INTO public.user_preferences (user_id)
        VALUES ($1)
        ON CONFLICT (user_id) DO UPDATE SET updated_at = public.user_preferences.updated_at
        RETURNING user_id, timezone, base_currency
        """,
        current_user.user_id,
    )
    return dict(row)


@router.patch("", response_model=PreferencesOut)
async def patch_preferences(
    payload: PreferencesPatch,
    current_user: CurrentUser = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    row = await db.fetchrow(
        """
        INSERT INTO public.user_preferences (user_id, timezone, base_currency)
        VALUES (
          $1,
          COALESCE($2, 'Asia/Manila'),
          COALESCE($3, 'PHP')
        )
        ON CONFLICT (user_id)
        DO UPDATE SET
          timezone = COALESCE($2, public.user_preferences.timezone),
          base_currency = COALESCE($3, public.user_preferences.base_currency),
          updated_at = now()
        RETURNING user_id, timezone, base_currency
        """,
        current_user.user_id,
        payload.timezone,
        payload.base_currency.upper() if payload.base_currency else None,
    )
    return dict(row)

