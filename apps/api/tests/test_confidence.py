from decimal import Decimal

import pytest

from atomize_api.domain.confidence import (
    CONFIDENCE_THRESHOLD,
    apply_low_confidence_flag,
    is_low_confidence,
)
from atomize_api.models import ExpenseItem


def test_threshold_value() -> None:
    assert CONFIDENCE_THRESHOLD == Decimal("0.8")


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (Decimal("0.7999"), True),
        (Decimal("0.8000"), False),  # exactly at the threshold is not low
        (Decimal("0.8001"), False),
        (Decimal(0), True),
        (Decimal(1), False),
        (0.79, True),
        (0.8, False),
    ],
)
def test_boundary(score: Decimal | float, expected: bool) -> None:
    assert is_low_confidence(score) is expected


@pytest.mark.parametrize("score", [Decimal("-0.01"), Decimal("1.0001"), 2.0])
def test_out_of_range_rejected(score: Decimal | float) -> None:
    with pytest.raises(ValueError):
        is_low_confidence(score)


def test_apply_sets_flag_both_ways() -> None:
    item = ExpenseItem(confidence_score=Decimal("0.5"))
    assert apply_low_confidence_flag(item) is True
    assert item.is_low_confidence is True
    item.confidence_score = 0.95
    assert apply_low_confidence_flag(item) is False
    assert item.is_low_confidence is False
