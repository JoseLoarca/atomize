import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from atomize_api.db import Base
from atomize_api.models.mixins import CreatedUpdatedAtMixin, UUIDPrimaryKeyMixin


class Budget(UUIDPrimaryKeyMixin, CreatedUpdatedAtMixin, Base):
    """SPEC.md §7. Monthly, per-category. No carryover logic lives here."""

    __tablename__ = "budget"
    __table_args__ = (UniqueConstraint("household_id", "category_id", "year_month"),)

    household_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("household.id"))
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("category.id"))
    year_month: Mapped[date] = mapped_column(Date)
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)


class CategoryPacingSetting(UUIDPrimaryKeyMixin, Base):
    """SPEC.md §13. Opt-in per category; defaults true for variable, false for fixed/lump-sum."""

    __tablename__ = "category_pacing_setting"
    __table_args__ = (UniqueConstraint("household_id", "category_id"),)

    household_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("household.id"))
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("category.id"))
    show_pacing: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class BudgetPeriodLedger(UUIDPrimaryKeyMixin, Base):
    """SPEC.md §7. Carryover-into-savings mechanic, computed/finalized at month close.

    The household's running "saved" total is SUM(unspent_amount) across rows —
    a derived aggregate, never a separately maintained counter.
    """

    __tablename__ = "budget_period_ledger"
    __table_args__ = (UniqueConstraint("household_id", "category_id", "year_month"),)

    household_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("household.id"))
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("category.id"))
    year_month: Mapped[date] = mapped_column(Date)
    budgeted_amount: Mapped[float] = mapped_column(Numeric(12, 2))
    actual_spent: Mapped[float] = mapped_column(Numeric(12, 2))
    unspent_amount: Mapped[float] = mapped_column(Numeric(12, 2))
