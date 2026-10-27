import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from atomize_api.db import Base
from atomize_api.models.mixins import UUIDPrimaryKeyMixin


class AuditEntityType(str, enum.Enum):
    RECEIPT = "receipt"
    EXPENSE_ITEM = "expense_item"
    MERCHANT_CATEGORY_MAPPING = "merchant_category_mapping"
    BUDGET = "budget"


class AuditChangedBy(str, enum.Enum):
    AI = "ai"
    USER = "user"


class AuditLogEntry(UUIDPrimaryKeyMixin, Base):
    """SPEC.md §5. Append-only — never updated or deleted.

    Every AI-assigned value is logged on creation (changed_by=AI), and every
    subsequent human correction adds a new row rather than mutating history.
    """

    __tablename__ = "audit_log_entry"

    household_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("household.id"))
    entity_type: Mapped[AuditEntityType] = mapped_column(Enum(AuditEntityType, name="audit_entity_type"))
    entity_id: Mapped[uuid.UUID]
    field_name: Mapped[str] = mapped_column(String(100))
    old_value: Mapped[str | None] = mapped_column(String, nullable=True)
    new_value: Mapped[str | None] = mapped_column(String, nullable=True)
    changed_by: Mapped[AuditChangedBy] = mapped_column(Enum(AuditChangedBy, name="audit_changed_by"))
    changed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
