import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from atomize_api.db import Base
from atomize_api.models.mixins import CreatedUpdatedAtMixin, UUIDPrimaryKeyMixin


class Receipt(UUIDPrimaryKeyMixin, CreatedUpdatedAtMixin, Base):
    """SPEC.md §3, §6, §9, §10, §12, §14, §19. Receipts are immutable facts (§23)."""

    __tablename__ = "receipt"

    household_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("household.id"))

    merchant_name: Mapped[str] = mapped_column(String(255))
    merchant_normalized_name: Mapped[str] = mapped_column(String(255))

    # §10: local time at point of purchase, plus which home-timezone day it counts toward.
    transaction_datetime_local: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    transaction_timezone: Mapped[str] = mapped_column(String(64))
    transaction_date_home: Mapped[date] = mapped_column(Date)

    location_city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location_country: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location_address: Mapped[str | None] = mapped_column(String(500), nullable=True)

    original_currency: Mapped[str] = mapped_column(String(3))
    exchange_rate: Mapped[float | None] = mapped_column(Numeric(18, 8), nullable=True)

    total_amount: Mapped[float] = mapped_column(Numeric(12, 2))
    tax_total: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    payment_method_label: Mapped[str] = mapped_column(String(100))

    is_total_only: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    # §9: used for v1 total-only (or any v1 single-category) receipts.
    single_category_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("category.id"), nullable=True)

    # §14: special-budget-attributed receipts are excluded from the regular monthly budget math.
    special_budget_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("special_budget.id"), nullable=True)

    # §12: returns/refunds are negative expenses, never deletions.
    is_return: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    original_receipt_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("receipt.id"), nullable=True)

    # §19: image purged after 6 months; metadata/row persists regardless.
    source_image_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    image_deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"))

    items: Mapped[list[ExpenseItem]] = relationship(back_populates="receipt")


class ExpenseItem(UUIDPrimaryKeyMixin, CreatedUpdatedAtMixin, Base):
    """SPEC.md §3, §5, §11, §12. The atomic unit of categorization."""

    __tablename__ = "expense_item"

    receipt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("receipt.id"))

    description: Mapped[str] = mapped_column(String(500))
    quantity: Mapped[float] = mapped_column(Numeric(10, 3))
    unit_price: Mapped[float] = mapped_column(Numeric(12, 4))
    total_price_pretax: Mapped[float] = mapped_column(Numeric(12, 2))

    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("category.id"))

    # §11: largest-remainder allocation, computed receipt-wide then attributed per item.
    allocated_tax_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0, server_default="0")

    # §5: AI confidence score; below the (currently fixed, global) threshold -> highlighted for review.
    confidence_score: Mapped[float] = mapped_column(Numeric(5, 4))
    is_low_confidence: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    tags: Mapped[dict[str, str] | None] = mapped_column(JSON, nullable=True)

    # §12: item-level returns.
    is_return: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    original_item_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("expense_item.id"), nullable=True)

    receipt: Mapped[Receipt] = relationship(back_populates="items")
