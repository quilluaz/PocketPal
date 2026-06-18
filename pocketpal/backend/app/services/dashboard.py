from datetime import datetime
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def kpi_totals_from_rows(rows: list[dict[str, Any]]) -> dict[str, int]:
    income = sum(int(row["total"]) for row in rows if row["transaction_type"] == "income")
    expense = sum(int(row["total"]) for row in rows if row["transaction_type"] == "expense")
    return {
        "monthly_income_minor_base": income,
        "monthly_expense_minor_base": abs(expense),
    }


class DashboardService:
    def __init__(self, db: Any) -> None:
        self.db = db

    async def build(self, user_id: UUID) -> dict[str, Any]:
        preferences = await self.db.fetchrow(
            """
            INSERT INTO public.user_preferences (user_id)
            VALUES ($1)
            ON CONFLICT (user_id) DO UPDATE SET updated_at = public.user_preferences.updated_at
            RETURNING timezone, base_currency
            """,
            user_id,
        )
        timezone_name = preferences["timezone"]
        base_currency = preferences["base_currency"].strip()
        accounts = await self.db.fetch(
            """
            SELECT id, account_name, currency, oauth_status, reconciliation_enabled
            FROM public.accounts
            WHERE user_id = $1
            ORDER BY created_at ASC
            """,
            user_id,
        )

        account_rows = []
        settled_total = 0
        pending_total = 0
        for account in accounts:
            balances = await self.db.fetchrow(
                """
                SELECT
                  COALESCE(SUM(amount_minor_base) FILTER (
                    WHERE affects_ledger = TRUE
                      AND ledger_status IN ('cleared', 'adjusted')
                      AND amount_minor_base IS NOT NULL
                  ), 0) AS settled,
                  COALESCE(SUM(amount_minor_base) FILTER (
                    WHERE source = 'manual'
                      AND ledger_status = 'pending'
                      AND match_state = 'match_pending'
                      AND amount_minor_base IS NOT NULL
                  ), 0) AS pending
                FROM public.transactions
                WHERE user_id = $1 AND account_id = $2
                """,
                user_id,
                account["id"],
            )
            settled = int(balances["settled"])
            pending = int(balances["pending"])
            settled_total += settled
            pending_total += pending
            account_rows.append(
                {
                    "account_id": account["id"],
                    "account_name": account["account_name"],
                    "currency": account["currency"].strip(),
                    "oauth_status": account["oauth_status"],
                    "reconciliation_enabled": account["reconciliation_enabled"],
                    "projected_balance_minor_base": settled + pending,
                    "settled_balance_minor_base": settled,
                    "pending_manual_minor_base": pending,
                    "action_required": "reconnect_bank"
                    if account["oauth_status"] == "reconnect_required"
                    else None,
                }
            )

        try:
            tz = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            tz = ZoneInfo("UTC")
        now_local = datetime.now(tz)
        month_start_local = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month_start_local.month == 12:
            next_month_start_local = month_start_local.replace(
                year=month_start_local.year + 1,
                month=1,
            )
        else:
            next_month_start_local = month_start_local.replace(month=month_start_local.month + 1)

        kpi_rows = await self.db.fetch(
            """
            SELECT transaction_type, COALESCE(SUM(amount_minor_base), 0) AS total
            FROM public.analytics_transactions
            WHERE user_id = $1
              AND ledger_cutoff_at >= ($2::timestamp AT TIME ZONE $4)
              AND ledger_cutoff_at < ($3::timestamp AT TIME ZONE $4)
            GROUP BY transaction_type
            """,
            user_id,
            month_start_local.replace(tzinfo=None),
            next_month_start_local.replace(tzinfo=None),
            timezone_name,
        )
        kpis = kpi_totals_from_rows([dict(row) for row in kpi_rows])
        days_elapsed = max(now_local.day, 1)
        kpis["burn_rate_daily_minor_base"] = kpis["monthly_expense_minor_base"] // days_elapsed

        return {
            "base_currency": base_currency,
            "projected_balance_minor_base": settled_total + pending_total,
            "settled_balance_minor_base": settled_total,
            "pending_manual_minor_base": pending_total,
            "accounts": account_rows,
            "kpis": kpis,
        }

