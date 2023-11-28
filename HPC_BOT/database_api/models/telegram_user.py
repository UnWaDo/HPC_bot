from sqlalchemy import UniqueConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from .base_model import BaseModel
from .mixins import DateRelationMixin
from .mixins import UserRelationMixin


class TelegramUser(BaseModel, UserRelationMixin, DateRelationMixin):
    __tablename__ = "telegram_users"

    _user_id_unique: bool = True
    _user_back_populates: str | None = "telegram_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True)
    telegram_username: Mapped[str] = mapped_column(String(100), nullable=True)

    __table_args__ = (UniqueConstraint("user_id"),)

    def __repr__(self):
        return f"TelegramUser(tg_id={self.telegram_id}, user_id={self.user_id})"

    def __str__(self):
        return self.__repr__()
