"""User model — authentication identity."""
import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPKMixin


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    EMPLOYEE = "employee"


class User(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # Use values_callable so SQLAlchemy maps Python Enum -> DB enum values (the
    # lowercase strings) instead of Enum member names (e.g. 'ADMIN'). This
    # ensures the bound parameter matches the PostgreSQL enum labels created
    # by the migration.
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        default=UserRole.EMPLOYEE,
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    employee = relationship(
        "Employee", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
