"""Low-confidence flagging (SPEC.md §5, §21)."""

from decimal import Decimal

from atomize_api.models.receipts import ExpenseItem

# Fixed for v1, household-configurable later (SPEC.md §21). Scores are in [0, 1];
# SPEC.md doesn't pick a value, so 0.80 is the product default to revisit with real data.
CONFIDENCE_THRESHOLD = Decimal("0.8000")


def is_low_confidence(confidence_score: Decimal | float) -> bool:
    """True when the score is strictly below the threshold (a score equal to it passes)."""
    score = Decimal(str(confidence_score))
    if not Decimal(0) <= score <= Decimal(1):
        raise ValueError(f"confidence_score must be between 0 and 1, got {confidence_score}")
    return score < CONFIDENCE_THRESHOLD


def apply_low_confidence_flag(item: ExpenseItem) -> bool:
    """Set ``item.is_low_confidence`` from its ``confidence_score`` and return the flag."""
    item.is_low_confidence = is_low_confidence(item.confidence_score)
    return item.is_low_confidence
