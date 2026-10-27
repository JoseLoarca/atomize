"""Append-only audit log writer (SPEC.md §5).

Every AI-assigned value (on creation) and every user correction (on update) must go
through ``record_audit_entry`` so there is exactly one code path into the audit trail.
"""

import uuid
from datetime import date, datetime
from enum import Enum
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Mapper, Session

from atomize_api.models.audit import AuditChangedBy, AuditEntityType, AuditLogEntry


class AuditLogImmutableError(Exception):
    """Raised when something tries to update or delete an existing audit entry."""


def serialize_audit_value(value: object) -> str | None:
    """Render a field value as the text stored in ``old_value`` / ``new_value``."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    return str(value)  # str, int, UUID, Decimal


def record_audit_entry(
    db: Session,
    *,
    household_id: uuid.UUID,
    entity_type: AuditEntityType,
    entity_id: uuid.UUID,
    field_name: str,
    old_value: object,
    new_value: object,
    changed_by: AuditChangedBy,
    changed_by_user_id: uuid.UUID | None = None,
) -> AuditLogEntry:
    """Append one audit row. Flushes but does not commit; the caller owns the transaction.

    ``changed_by_user_id`` is required for user changes and must be omitted for AI ones
    (SPEC/DATA_MODEL: null when ``changed_by = ai``).
    """
    if changed_by is AuditChangedBy.USER and changed_by_user_id is None:
        raise ValueError("changed_by_user_id is required when changed_by is USER")
    if changed_by is AuditChangedBy.AI and changed_by_user_id is not None:
        raise ValueError("changed_by_user_id must be None when changed_by is AI")

    entry = AuditLogEntry(
        household_id=household_id,
        entity_type=entity_type,
        entity_id=entity_id,
        field_name=field_name,
        old_value=serialize_audit_value(old_value),
        new_value=serialize_audit_value(new_value),
        changed_by=changed_by,
        changed_by_user_id=changed_by_user_id,
    )
    db.add(entry)
    db.flush()
    return entry


@event.listens_for(AuditLogEntry, "before_update")
@event.listens_for(AuditLogEntry, "before_delete")
def _forbid_mutation(mapper: Mapper[Any], connection: Connection, target: AuditLogEntry) -> None:
    raise AuditLogImmutableError("audit_log_entry rows are append-only")
