from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression
from sqlalchemy.types import String

from .base_model import BaseModel
from .mixins import DateRelationMixin

if TYPE_CHECKING:
    from .organization import Organization
    from .telegram_user import TelegramUser
    from .calculation_profile import CalculationProfile


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

    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id",  ondelete="CASCADE"))
    organization: Mapped["Organization"] = relationship(back_populates="users", lazy='subquery')

    is_banned: Mapped[bool] = mapped_column(default=False)
    is_admin: Mapped[bool] = mapped_column(default=False)

    is_active: Mapped[bool] = mapped_column(default=True)

    telegram_user: Mapped["TelegramUser"] = relationship(back_populates="user", lazy="subquery")
    is_verified: Mapped[bool] = mapped_column(default=False)
    calculation_profile: Mapped["CalculationProfile"] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"User(id={self.id}, username={self.username})"

    def __str__(self):
        return self.__repr__()
