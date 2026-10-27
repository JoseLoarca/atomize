import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from atomize_api.db import Base
from atomize_api.domain.merchant_mapping import (
    get_default_category_for_merchant,
    set_merchant_category_mapping,
)
from atomize_api.models import Category, MerchantCategoryMapping, Receipt

HOUSEHOLD = uuid.uuid4()
USER = uuid.uuid4()


@pytest.fixture
def db() -> Iterator[Session]:
    engine = create_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _category(db: Session, name: str) -> Category:
    category = Category(name=name, sort_order=1)
    db.add(category)
    db.flush()
    return category


def test_unmapped_merchant_returns_none(db: Session) -> None:
    assert get_default_category_for_merchant(db, HOUSEHOLD, "shell") is None


def test_set_then_get(db: Session) -> None:
    gas = _category(db, "Gas")
    mapping = set_merchant_category_mapping(db, HOUSEHOLD, "shell", gas.id, USER)
    assert mapping.updated_by_user_id == USER
    found = get_default_category_for_merchant(db, HOUSEHOLD, "shell")
    assert found is not None
    assert found.id == gas.id


def test_correction_upserts_single_row(db: Session) -> None:
    gas = _category(db, "Gas")
    groceries = _category(db, "Groceries")
    other_user = uuid.uuid4()
    first = set_merchant_category_mapping(db, HOUSEHOLD, "costco", gas.id, USER)
    second = set_merchant_category_mapping(db, HOUSEHOLD, "costco", groceries.id, other_user)
    assert second.id == first.id
    assert second.category_id == groceries.id
    assert second.updated_by_user_id == other_user
    count = db.scalar(select(func.count()).select_from(MerchantCategoryMapping))
    assert count == 1


def test_mappings_are_household_scoped(db: Session) -> None:
    gas = _category(db, "Gas")
    groceries = _category(db, "Groceries")
    other_household = uuid.uuid4()
    set_merchant_category_mapping(db, HOUSEHOLD, "costco", gas.id, USER)
    set_merchant_category_mapping(db, other_household, "costco", groceries.id, USER)
    mine = get_default_category_for_merchant(db, HOUSEHOLD, "costco")
    theirs = get_default_category_for_merchant(db, other_household, "costco")
    assert mine is not None and mine.id == gas.id
    assert theirs is not None and theirs.id == groceries.id


def test_correction_does_not_touch_existing_receipts(db: Session) -> None:
    gas = _category(db, "Gas")
    groceries = _category(db, "Groceries")
    set_merchant_category_mapping(db, HOUSEHOLD, "costco", gas.id, USER)
    receipt = Receipt(
        household_id=HOUSEHOLD,
        merchant_name="Costco",
        merchant_normalized_name="costco",
        transaction_datetime_local=datetime(2026, 3, 1, tzinfo=UTC),
        transaction_timezone="UTC",
        transaction_date_home=datetime(2026, 3, 1, tzinfo=UTC).date(),
        original_currency="USD",
        total_amount=Decimal("50.00"),
        payment_method_label="Cash",
        is_total_only=True,
        single_category_id=gas.id,
        created_by_user_id=USER,
    )
    db.add(receipt)
    db.commit()

    set_merchant_category_mapping(db, HOUSEHOLD, "costco", groceries.id, USER)
    db.commit()
    db.refresh(receipt)

    assert receipt.single_category_id == gas.id
    new_default = get_default_category_for_merchant(db, HOUSEHOLD, "costco")
    assert new_default is not None and new_default.id == groceries.id
