from decimal import Decimal

from app.services.money import convert_minor_to_base


def test_historical_fx_value_is_frozen_after_insert():
    frozen_value = convert_minor_to_base(
        amount_minor=-1000,
        source_exponent=2,
        base_exponent=2,
        exchange_rate_to_base=Decimal("56.8500000000"),
    )
    changed_live_value = convert_minor_to_base(
        amount_minor=-1000,
        source_exponent=2,
        base_exponent=2,
        exchange_rate_to_base=Decimal("60.0000000000"),
    )

    stored_transaction = {"amount_minor_base": frozen_value}

    assert stored_transaction["amount_minor_base"] == -56850
    assert changed_live_value == -60000
    assert stored_transaction["amount_minor_base"] != changed_live_value

