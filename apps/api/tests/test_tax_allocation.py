from decimal import Decimal

import pytest

from atomize_api.domain.tax import allocate_tax

D = Decimal


def test_even_division() -> None:
    assert allocate_tax(D("1.00"), [D("10.00"), D("10.00")]) == [D("0.50"), D("0.50")]


def test_exact_proportional_split() -> None:
    assert allocate_tax(D("2.00"), [D("10.00"), D("30.00")]) == [D("0.50"), D("1.50")]


def test_remainder_goes_to_largest_fraction() -> None:
    # 1.00 over 1/3 each: shares 0.33 x3, one leftover cent -> first item (tie -> earliest)
    assert allocate_tax(D("1.00"), [D("5.00")] * 3) == [D("0.34"), D("0.33"), D("0.33")]


def test_remainder_prefers_larger_fraction_over_position() -> None:
    # exact shares (cents): 0.5*... tax 0.10 over [1,1,2]: 2.5, 2.5, 5.0 -> trunc 2,2,5 leftover 1
    # tie between first two -> earliest wins
    assert allocate_tax(D("0.10"), [D("1.00"), D("1.00"), D("2.00")]) == [
        D("0.03"),
        D("0.02"),
        D("0.05"),
    ]
    # tax 0.07 over [3, 1, 3]: exact 3, 1, 3 cents... use uneven: [1,2] -> 2.33, 4.67
    assert allocate_tax(D("0.07"), [D("1.00"), D("2.00")]) == [D("0.02"), D("0.05")]


def test_sum_always_equals_tax() -> None:
    items = [D("3.49"), D("12.99"), D("0.79"), D("7.25"), D("1.10")]
    result = allocate_tax(D("2.37"), items)
    assert sum(result) == D("2.37")
    assert all(r >= 0 for r in result)


def test_single_item_gets_all_tax() -> None:
    assert allocate_tax(D("1.23"), [D("20.00")]) == [D("1.23")]


def test_zero_tax() -> None:
    assert allocate_tax(D("0.00"), [D("4.00"), D("6.00")]) == [D("0.00"), D("0.00")]


def test_zero_tax_with_zero_subtotal_ok() -> None:
    assert allocate_tax(D("0"), [D("0.00")]) == [D("0.00")]


def test_more_items_than_cents_of_tax() -> None:
    result = allocate_tax(D("0.02"), [D("1.00")] * 5)
    assert result == [D("0.01"), D("0.01"), D("0.00"), D("0.00"), D("0.00")]
    assert sum(result) == D("0.02")


def test_zero_priced_item_gets_nothing() -> None:
    assert allocate_tax(D("1.00"), [D("0.00"), D("5.00")]) == [D("0.00"), D("1.00")]


def test_negative_return_receipt() -> None:
    result = allocate_tax(D("-1.00"), [D("-5.00")] * 3)
    assert result == [D("-0.34"), D("-0.33"), D("-0.33")]
    assert sum(result) == D("-1.00")


def test_empty_items_zero_tax() -> None:
    assert allocate_tax(D("0.00"), []) == []


def test_empty_items_with_tax_rejected() -> None:
    with pytest.raises(ValueError):
        allocate_tax(D("1.00"), [])


def test_zero_subtotal_with_tax_rejected() -> None:
    with pytest.raises(ValueError):
        allocate_tax(D("1.00"), [D("0.00"), D("0.00")])


def test_mixed_signs_rejected() -> None:
    with pytest.raises(ValueError):
        allocate_tax(D("1.00"), [D("5.00"), D("-2.00")])


def test_sub_cent_input_rejected() -> None:
    with pytest.raises(ValueError):
        allocate_tax(D("1.005"), [D("5.00")])
    with pytest.raises(ValueError):
        allocate_tax(D("1.00"), [D("5.001")])


def test_deterministic() -> None:
    items = [D("2.50"), D("2.50"), D("2.50"), D("2.50")]
    assert allocate_tax(D("0.03"), items) == allocate_tax(D("0.03"), items)
