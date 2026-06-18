from fastapi import APIRouter, Depends

from app.auth import CurrentUser, get_current_user
from app.db import Database, get_db

router = APIRouter(prefix="/fx", tags=["fx"])


@router.get("/rates")
async def get_rates(
    current_user: CurrentUser = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    preferences = await db.fetchrow(
        """
        INSERT INTO public.user_preferences (user_id)
        VALUES ($1)
        ON CONFLICT (user_id) DO UPDATE SET updated_at = public.user_preferences.updated_at
        RETURNING base_currency
        """,
        current_user.user_id,
    )
    currencies = await db.fetch(
        """
        SELECT code, exponent, name, symbol
        FROM public.currencies
        WHERE is_active = TRUE
        ORDER BY code
        """
    )
    rates = await db.fetch(
        """
        SELECT DISTINCT ON (base_currency, quote_currency)
          base_currency, quote_currency, rate, rate_date, source, fetched_at
        FROM public.exchange_rates
        WHERE base_currency = $1
        ORDER BY base_currency, quote_currency, rate_date DESC, fetched_at DESC
        """,
        preferences["base_currency"],
    )
    return {
        "base_currency": preferences["base_currency"].strip(),
        "currencies": [dict(row) for row in currencies],
        "rates": [dict(row) for row in rates],
    }

