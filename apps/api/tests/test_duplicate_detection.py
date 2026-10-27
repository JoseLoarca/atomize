import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from atomize_api.db import Base
from atomize_api.domain.duplicates import find_duplicate_receipts
from atomize_api.models import Receipt

HOUSEHOLD = uuid.uuid4()
WHEN = datetime(2026, 3, 1, 12, 30, tzinfo=UTC)


@pytest.fixture
def db() -> Iterator[Session]:
    engine = create_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _receipt(
    db: Session,
    *,
    household_id: uuid.UUID = HOUSEHOLD,
    merchant: str = "starbucks",
    total: str = "4.50",
    when: datetime = WHEN,
    payment: str = "VISA 1234",
) -> Receipt:
    receipt = Receipt(
        household_id=household_id,
        merchant_name=merchant.title(),
        merchant_normalized_name=merchant,
        transaction_datetime_local=when,
        transaction_timezone="UTC",
        transaction_date_home=when.date(),
        original_currency="USD",
        total_amount=Decimal(total),
        payment_method_label=payment,
        created_by_user_id=uuid.uuid4(),
    )
    db.add(receipt)
    db.commit()
    return receipt


def _find(db: Session, **overrides: object) -> list[Receipt]:
    args: dict[str, object] = {
        "household_id": HOUSEHOLD,
        "merchant_normalized_name": "starbucks",
        "total_amount": Decimal("4.50"),
        "transaction_datetime_local": WHEN,
        "payment_method_label": "VISA 1234",
    }
    args.update(overrides)
    return find_duplicate_receipts(db, **args)  # type: ignore[arg-type]


def test_no_receipts_no_match(db: Session) -> None:
    assert _find(db) == []


def test_exact_match_returned(db: Session) -> None:
    existing = _receipt(db)
    assert [r.id for r in _find(db)] == [existing.id]


def test_multiple_matches_all_returned(db: Session) -> None:
    a = _receipt(db)
    b = _receipt(db)
    assert {r.id for r in _find(db)} == {a.id, b.id}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("merchant_normalized_name", "dunkin"),
        ("total_amount", Decimal("4.51")),
        ("transaction_datetime_local", WHEN + timedelta(minutes=1)),
        ("payment_method_label", "Cash"),
        ("household_id", uuid.uuid4()),
    ],
)
def test_any_differing_field_is_not_a_match(db: Session, field: str, value: object) -> None:
    _receipt(db)
    assert _find(db, **{field: value}) == []


def test_other_households_receipts_ignored(db: Session) -> None:
    _receipt(db, household_id=uuid.uuid4())
    assert _find(db) == []


def test_same_instant_in_other_offset_matches(db: Session) -> None:
    existing = _receipt(db)
    est = WHEN.astimezone(timezone(timedelta(hours=-5)))
    assert [r.id for r in _find(db, transaction_datetime_local=est)] == [existing.id]
