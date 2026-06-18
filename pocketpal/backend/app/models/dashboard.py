from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class AccountDashboardOut(BaseModel):
    account_id: UUID
    account_name: str
    currency: str
    oauth_status: str
    reconciliation_enabled: bool
    projected_balance_minor_base: int
    settled_balance_minor_base: int
    pending_manual_minor_base: int
    action_required: Literal["reconnect_bank"] | None = None


class DashboardKpisOut(BaseModel):
    monthly_income_minor_base: int
    monthly_expense_minor_base: int
    burn_rate_daily_minor_base: int


class DashboardOut(BaseModel):
    base_currency: str
    projected_balance_minor_base: int
    settled_balance_minor_base: int
    pending_manual_minor_base: int
    accounts: list[AccountDashboardOut]
    kpis: DashboardKpisOut

