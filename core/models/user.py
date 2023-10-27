import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime, String

from .base_model import BaseModel
from .date_mixin import DateRelationMixin

if TYPE_CHECKING:
    from .organization import Organization
    from .telegram_user import TelegramUser
    from .calculation import Calculation


class User(BaseModel, DateRelationMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    first_name: Mapped[str | None] = mapped_column(
        String(30), default=None, nullable=True
    )
    last_name: Mapped[str | None] = mapped_column(
        String(30), default=None, nullable=True
    )

    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    organization: Mapped["Organization"] = relationship(back_populates="users")

    is_banned: Mapped[bool] = mapped_column(default=False)
    is_admin: Mapped[bool] = mapped_column(default=False)

    telegram_user: Mapped["TelegramUser"] = relationship(back_populates="user")
    calculation: Mapped["Calculation"] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"{self.first_name} {self.last_name if self.last_name else ''}"
