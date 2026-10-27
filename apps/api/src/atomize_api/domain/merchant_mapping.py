"""Household-level, forward-only merchant -> category mapping (SPEC.md §9)."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from atomize_api.models.categories import Category, MerchantCategoryMapping


def _get_mapping(
    db: Session, household_id: uuid.UUID, merchant_normalized_name: str
) -> MerchantCategoryMapping | None:
    return db.scalars(
        select(MerchantCategoryMapping).where(
            MerchantCategoryMapping.household_id == household_id,
            MerchantCategoryMapping.merchant_normalized_name == merchant_normalized_name,
        )
    ).one_or_none()


def get_default_category_for_merchant(
    db: Session, household_id: uuid.UUID, merchant_normalized_name: str
) -> Category | None:
    """Default category for total-only receipts from this merchant, or None if unmapped."""
    mapping = _get_mapping(db, household_id, merchant_normalized_name)
    return mapping.category if mapping else None


def set_merchant_category_mapping(
    db: Session,
    household_id: uuid.UUID,
    merchant_normalized_name: str,
    category_id: uuid.UUID,
    updated_by_user_id: uuid.UUID,
) -> MerchantCategoryMapping:
    """Create or update the household's default category for a merchant (upsert).

    Forward-only: this touches only the mapping row. Existing receipts and items are
    never read or modified, so past total-only receipts keep their category. The caller
    owns the transaction (this flushes but does not commit) and is responsible for
    writing the audit entry (see T012).
    """
    mapping = _get_mapping(db, household_id, merchant_normalized_name)
    if mapping is None:
        mapping = MerchantCategoryMapping(
            household_id=household_id,
            merchant_normalized_name=merchant_normalized_name,
            category_id=category_id,
            updated_by_user_id=updated_by_user_id,
        )
        db.add(mapping)
    else:
        mapping.category_id = category_id
        mapping.updated_by_user_id = updated_by_user_id
    db.flush()
    db.refresh(mapping)
    return mapping
