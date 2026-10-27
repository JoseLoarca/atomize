import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from atomize_api.db import Base
from atomize_api.models.mixins import UUIDPrimaryKeyMixin


class Category(UUIDPrimaryKeyMixin, Base):
    """SPEC.md §4. One fixed, global, canonical list — not per-household."""

    __tablename__ = "category"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    sort_order: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class MerchantCategoryMapping(UUIDPrimaryKeyMixin, Base):
    """SPEC.md §9. Household-level, forward-only default category per merchant."""

    __tablename__ = "merchant_category_mapping"
    __table_args__ = (UniqueConstraint("household_id", "merchant_normalized_name"),)

    household_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("household.id"))
    merchant_normalized_name: Mapped[str] = mapped_column(String(255))
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("category.id"))
    updated_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    category: Mapped[Category] = relationship()
