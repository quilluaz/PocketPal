from decimal import Decimal, ROUND_HALF_UP


def _scale(exponent: int) -> Decimal:
    if exponent < 0 or exponent > 6:
        raise ValueError("currency exponent must be between 0 and 6")
    return Decimal(10) ** exponent


def minor_to_major(amount_minor: int, exponent: int) -> Decimal:
    return Decimal(amount_minor) / _scale(exponent)


def major_to_minor(amount_major: str, exponent: int) -> int:
    scaled = Decimal(amount_major) * _scale(exponent)
    return int(scaled.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def convert_minor_to_base(
    amount_minor: int,
    source_exponent: int,
    base_exponent: int,
    exchange_rate_to_base: Decimal,
) -> int:
    source_major = minor_to_major(amount_minor, source_exponent)
    base_major = source_major * exchange_rate_to_base
    base_minor = base_major * _scale(base_exponent)
    return int(base_minor.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

