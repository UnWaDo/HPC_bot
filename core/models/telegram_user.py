import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import BaseModel
from .date_mixin import DateRelationMixin
from .user_mixins import UserRelationMixin

if TYPE_CHECKING:
    from .user import User


class TelegramUser(BaseModel, UserRelationMixin, DateRelationMixin):
    __tablename__ = "telegram_users"

    # _user_id_nullable: bool = False
    _user_id_unique: bool = True
    _user_back_populates: str | None = "telegram_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[str] = mapped_column(unique=True)

    __table_args__ = (UniqueConstraint("user_id"),)
