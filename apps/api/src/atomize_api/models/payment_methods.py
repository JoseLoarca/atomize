import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from atomize_api.db import Base
from atomize_api.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class PaymentMethod(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """SPEC.md §15. Lightweight, free-form label — not used for balance tracking."""

    __tablename__ = "payment_method"

    household_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("household.id"))
    label: Mapped[str] = mapped_column(String(100))
