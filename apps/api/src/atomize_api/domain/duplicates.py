"""Duplicate receipt detection (SPEC.md §6). A soft warning, never a hard block."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from atomize_api.models.receipts import Receipt


def find_duplicate_receipts(
    db: Session,
    *,
    household_id: uuid.UUID,
    merchant_normalized_name: str,
    total_amount: Decimal,
    transaction_datetime_local: datetime,
    payment_method_label: str,
) -> list[Receipt]:
    """Return existing receipts in the household matching all four SPEC §6 fields.

    Matching is exact on every field (the datetime is compared as an instant, so the
    same moment expressed in a different UTC offset still matches). Oldest first.
    The caller decides what to do with matches; nothing here blocks an upload.
    """
    # Normalize to UTC so the comparison doesn't depend on the DB's handling of offsets.
    when_utc = transaction_datetime_local.astimezone(UTC)
    stmt = (
        select(Receipt)
        .where(
            Receipt.household_id == household_id,
            Receipt.merchant_normalized_name == merchant_normalized_name,
            Receipt.total_amount == total_amount,
            Receipt.transaction_datetime_local == when_utc,
            Receipt.payment_method_label == payment_method_label,
        )
        .order_by(Receipt.created_at, Receipt.id)
    )
    return list(db.scalars(stmt))
