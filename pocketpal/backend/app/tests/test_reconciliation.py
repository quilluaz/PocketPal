from datetime import UTC, datetime

from app.services.dashboard import kpi_totals_from_rows
from app.services.reconciliation import compute_snapshot_delta


def test_temporal_snapshot_excludes_future_transactions():
    delta = compute_snapshot_delta(
        snapshot_balance_minor=10_000,
        snapshot_as_of=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
        snapshot_currency="PHP",
        transactions=[
            {
                "amount_minor": 10_000,
                "currency": "PHP",
                "affects_ledger": True,
                "ledger_status": "cleared",
                "ledger_cutoff_at": datetime(2026, 6, 19, 15, 0, tzinfo=UTC),
            }
        ],
    )
    assert delta == 10_000


def test_reconciliation_delta_uses_native_currency_and_cutoff():
    delta = compute_snapshot_delta(
        snapshot_balance_minor=49_000,
        snapshot_as_of=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
        snapshot_currency="PHP",
        transactions=[
            {
                "amount_minor": 50_000,
                "currency": "PHP",
                "affects_ledger": True,
                "ledger_status": "cleared",
                "ledger_cutoff_at": datetime(2026, 6, 19, 11, 0, tzinfo=UTC),
            },
            {
                "amount_minor": -500,
                "currency": "USD",
                "affects_ledger": True,
                "ledger_status": "cleared",
                "ledger_cutoff_at": datetime(2026, 6, 19, 11, 0, tzinfo=UTC),
            },
        ],
    )
    assert delta == -1_000


def test_kpis_use_view_rows_without_system_adjustments():
    rows_from_analytics_view = [{"transaction_type": "expense", "total": -2_500_000}]
    totals = kpi_totals_from_rows(rows_from_analytics_view)
    assert totals["monthly_income_minor_base"] == 0
    assert totals["monthly_expense_minor_base"] == 2_500_000

