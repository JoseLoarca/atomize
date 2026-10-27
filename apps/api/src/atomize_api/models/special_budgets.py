import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from atomize_api.db import Base
from atomize_api.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class SpecialBudget(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """SPEC.md §14. Budget groups (travel/events), isolated from regular monthly budgets."""

    __tablename__ = "special_budget"

    household_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("household.id"))
    name: Mapped[str] = mapped_column(String(255))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    pacing_enabled_default: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    estimates: Mapped[list["SpecialBudgetEstimate"]] = relationship(back_populates="special_budget")


class SpecialBudgetEstimate(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "special_budget_estimate"

    special_budget_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("special_budget.id"))
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("category.id"))
    estimate_min: Mapped[float] = mapped_column(Numeric(12, 2))
    estimate_max: Mapped[float] = mapped_column(Numeric(12, 2))

    special_budget: Mapped["SpecialBudget"] = relationship(back_populates="estimates")
