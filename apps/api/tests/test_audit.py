import uuid
from collections.abc import Iterator
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from atomize_api.db import Base
from atomize_api.domain.audit import (
    AuditLogImmutableError,
    record_audit_entry,
    serialize_audit_value,
)
from atomize_api.models.audit import AuditChangedBy, AuditEntityType, AuditLogEntry

HOUSEHOLD = uuid.uuid4()
ENTITY = uuid.uuid4()
USER = uuid.uuid4()


@pytest.fixture
def db() -> Iterator[Session]:
    engine = create_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _user_entry(db: Session) -> AuditLogEntry:
    return record_audit_entry(
        db,
        household_id=HOUSEHOLD,
        entity_type=AuditEntityType.EXPENSE_ITEM,
        entity_id=ENTITY,
        field_name="category_id",
        old_value="a",
        new_value="b",
        changed_by=AuditChangedBy.USER,
        changed_by_user_id=USER,
    )


def test_ai_origin_entry(db: Session) -> None:
    cat = uuid.uuid4()
    entry = record_audit_entry(
        db,
        household_id=HOUSEHOLD,
        entity_type=AuditEntityType.RECEIPT,
        entity_id=ENTITY,
        field_name="single_category_id",
        old_value=None,
        new_value=cat,
        changed_by=AuditChangedBy.AI,
    )
    db.commit()
    assert entry.changed_by is AuditChangedBy.AI
    assert entry.changed_by_user_id is None
    assert entry.old_value is None
    assert entry.new_value == str(cat)
    assert entry.changed_at is not None


def test_user_origin_entry(db: Session) -> None:
    entry = _user_entry(db)
    db.commit()
    assert entry.changed_by is AuditChangedBy.USER
    assert entry.changed_by_user_id == USER
    assert (entry.old_value, entry.new_value) == ("a", "b")


def test_user_entry_requires_user_id(db: Session) -> None:
    with pytest.raises(ValueError):
        record_audit_entry(
            db,
            household_id=HOUSEHOLD,
            entity_type=AuditEntityType.BUDGET,
            entity_id=ENTITY,
            field_name="amount",
            old_value=1,
            new_value=2,
            changed_by=AuditChangedBy.USER,
        )


def test_ai_entry_rejects_user_id(db: Session) -> None:
    with pytest.raises(ValueError):
        record_audit_entry(
            db,
            household_id=HOUSEHOLD,
            entity_type=AuditEntityType.BUDGET,
            entity_id=ENTITY,
            field_name="amount",
            old_value=1,
            new_value=2,
            changed_by=AuditChangedBy.AI,
            changed_by_user_id=USER,
        )


def test_each_call_appends_a_row(db: Session) -> None:
    _user_entry(db)
    _user_entry(db)
    db.commit()
    assert db.scalar(select(func.count()).select_from(AuditLogEntry)) == 2


def test_update_is_forbidden(db: Session) -> None:
    entry = _user_entry(db)
    db.commit()
    entry.new_value = "tampered"
    with pytest.raises(AuditLogImmutableError):
        db.commit()
    db.rollback()
    db.refresh(entry)
    assert entry.new_value == "b"


def test_delete_is_forbidden(db: Session) -> None:
    entry = _user_entry(db)
    db.commit()
    db.delete(entry)
    with pytest.raises(AuditLogImmutableError):
        db.commit()
    db.rollback()
    assert db.scalar(select(func.count()).select_from(AuditLogEntry)) == 1


def test_serialization() -> None:
    uid = uuid.uuid4()
    assert serialize_audit_value(None) is None
    assert serialize_audit_value(True) == "true"
    assert serialize_audit_value(False) == "false"
    assert serialize_audit_value(AuditChangedBy.AI) == "ai"
    assert serialize_audit_value(Decimal("4.50")) == "4.50"
    assert serialize_audit_value(uid) == str(uid)
    assert serialize_audit_value(date(2026, 3, 1)) == "2026-03-01"
    assert serialize_audit_value(datetime(2026, 3, 1, 12, tzinfo=UTC)) == "2026-03-01T12:00:00+00:00"
    assert serialize_audit_value(7) == "7"
    assert serialize_audit_value("x") == "x"
