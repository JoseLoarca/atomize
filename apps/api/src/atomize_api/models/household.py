import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from atomize_api.db import Base
from atomize_api.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class HouseholdRole(str, enum.Enum):
    SUPER_USER = "super_user"
    CONTRIBUTOR = "contributor"


class Household(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """SPEC.md §2. The unit of account — not the individual user."""

    __tablename__ = "household"

    name: Mapped[str] = mapped_column(String(255))
    home_timezone: Mapped[str] = mapped_column(String(64))
    currency: Mapped[str] = mapped_column(String(3), default="USD", server_default="USD")

    memberships: Mapped[list["HouseholdMembership"]] = relationship(back_populates="household")
    invites: Mapped[list["HouseholdInvite"]] = relationship(back_populates="household")


class User(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "user"

    email: Mapped[str] = mapped_column(String(320), unique=True)
    name: Mapped[str] = mapped_column(String(255))

    memberships: Mapped[list["HouseholdMembership"]] = relationship(back_populates="user")


class HouseholdMembership(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "household_membership"
    __table_args__ = (UniqueConstraint("household_id", "user_id"),)

    household_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("household.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"))
    role: Mapped[HouseholdRole] = mapped_column(Enum(HouseholdRole, name="household_role"))

    household: Mapped["Household"] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship(back_populates="memberships")


class HouseholdInvite(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """SPEC.md §2. Shareable invite code/link — valid until revoked."""

    __tablename__ = "household_invite"

    household_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("household.id"))
    code: Mapped[str] = mapped_column(String(64), unique=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    household: Mapped["Household"] = relationship(back_populates="invites")
