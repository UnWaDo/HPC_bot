import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import BaseModel
from .date_mixin import DateRelationMixin
from .user_mixins import UserRelationMixin

if TYPE_CHECKING:
    from .user import User


class Calculation(BaseModel):
    __tablename__ = "calculations"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile: Mapped[int] = mapped_column(ForeignKey("calculation_profiles.id"))
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
