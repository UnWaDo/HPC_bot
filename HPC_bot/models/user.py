from datetime import datetime
from typing import TYPE_CHECKING, List, Sequence

from sqlalchemy import ForeignKey, func, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import BaseDBModel
from HPC_bot.database.database import sessionmaker
from .organization import Organization
from .person import Person

if TYPE_CHECKING:
    from .calculation import Calculation
    from .telegram_user import TelegramUser

NEWLY_REGISTERED_LIMIT = 5
APPROVED_BASE_LIMIT = 50


class AccessLevel:
    BLOCKED = 9999
    NEWLY_REGISTERED = 1000
    APPROVED = 900

    MODERATOR = 100
    ADMIN = 0


class User(BaseDBModel):
    __tablename__ = "hpc_user"

    id: Mapped[int] = mapped_column(primary_key=True)

    calculation_limit: Mapped[int] = mapped_column(default=NEWLY_REGISTERED_LIMIT)
    access_level: Mapped[int] = mapped_column(default=1000)

    blocked: Mapped[bool] = mapped_column(default=False)

    person_id: Mapped[int] = mapped_column(ForeignKey("person.id"))
    person: Mapped[Person] = relationship(back_populates="user", lazy="joined")

    tg_user: Mapped["TelegramUser"] = relationship(
        back_populates="user", lazy="joined", join_depth=2
    )
    calculations: Mapped[List["Calculation"]] = relationship(back_populates="user")

    def get_calculations(self, since: datetime = None) -> List["Calculation"]:
        if since is None:
            return self.calculations

        return list(filter(lambda x: x.start_datetime >= since, self.calculations))
