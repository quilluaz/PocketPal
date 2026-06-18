from decimal import Decimal

from app.services.money import convert_minor_to_base, major_to_minor, minor_to_major


def test_minor_major_uses_currency_exponent():
    assert minor_to_major(5000, 2) == Decimal("50")
    assert minor_to_major(5000, 0) == Decimal("5000")
    assert minor_to_major(5000, 3) == Decimal("5")


def test_major_to_minor_rounds_with_decimal_not_float():
    assert major_to_minor("10.005", 2) == 1001
    assert major_to_minor("5", 0) == 5
    assert major_to_minor("5.0004", 3) == 5000


def test_convert_minor_to_base_uses_decimal_rate():
    assert (
        convert_minor_to_base(
            amount_minor=12345,
            source_exponent=2,
            base_exponent=2,
            exchange_rate_to_base=Decimal("56.8500000000"),
        )
        == 701813
    )
