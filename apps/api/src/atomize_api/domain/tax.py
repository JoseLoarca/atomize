"""Proportional tax allocation using the largest-remainder method (SPEC.md §11, §8)."""

from decimal import Decimal
from fractions import Fraction

_CENT = Decimal("0.01")


def _to_cents(value: Decimal, name: str) -> int:
    cents = value / _CENT
    if cents != cents.to_integral_value():
        raise ValueError(f"{name} must have at most two decimal places, got {value}")
    return int(cents)


def allocate_tax(tax_total: Decimal, item_pretax_totals: list[Decimal]) -> list[Decimal]:
    """Split ``tax_total`` across items in proportion to their pre-tax totals.

    Each item's exact share is truncated to the cent, then the leftover cents are handed
    out one at a time to the items with the largest fractional remainder (ties go to the
    earlier item, so the result is deterministic). The returned amounts always sum
    exactly to ``tax_total`` and are returned in input order.

    All items must share a sign (a return receipt has all-negative items and a
    negative tax). Raises ``ValueError`` for amounts with sub-cent precision, mixed-sign
    items, or a non-zero tax with a zero pre-tax subtotal.
    """
    if not item_pretax_totals:
        if tax_total != 0:
            raise ValueError("Cannot allocate non-zero tax across zero items")
        return []

    tax_cents = _to_cents(tax_total, "tax_total")
    item_cents = [_to_cents(v, "item pre-tax total") for v in item_pretax_totals]

    if any(c > 0 for c in item_cents) and any(c < 0 for c in item_cents):
        raise ValueError("Item pre-tax totals must not mix positive and negative amounts")

    subtotal = sum(item_cents)
    if tax_cents == 0:
        return [Decimal("0.00")] * len(item_cents)
    if subtotal == 0:
        raise ValueError("Cannot allocate non-zero tax when the pre-tax subtotal is zero")

    # Work on magnitudes so truncation/remainder logic is sign-agnostic.
    sign = -1 if tax_cents < 0 else 1
    abs_tax = abs(tax_cents)
    abs_subtotal = abs(subtotal)
    exact = [Fraction(abs_tax * abs(c), abs_subtotal) for c in item_cents]
    shares = [int(e) for e in exact]  # truncate (magnitudes are non-negative)
    leftover = abs_tax - sum(shares)

    by_remainder = sorted(range(len(exact)), key=lambda i: (-(exact[i] - shares[i]), i))
    for i in by_remainder[:leftover]:
        shares[i] += 1

    return [Decimal(sign * s) * _CENT for s in shares]
