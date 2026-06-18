from datetime import UTC, datetime

from app.models.webhook import HistoricalTransactionIn
from app.services.onboarding import calculate_day_zero_opening_balance


def test_day_zero_opening_balance_avoids_reconciliation_adjustment():
    opening_balance = calculate_day_zero_opening_balance(
        snapshot_balance_minor=5_000_000,
        historical_transactions=[
            HistoricalTransactionIn(
                external_transaction_id="hist_001",
                amount_minor=-1_000_000,
                currency="PHP",
                vendor="Historical Spend",
                transaction_type="expense",
                ledger_cutoff_at=datetime(2026, 6, 10, 12, 0, tzinfo=UTC),
            )
        ],
        as_of=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
        currency="PHP",
    )

    assert opening_balance == 6_000_000

