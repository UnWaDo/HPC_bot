import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import BaseModel
from .date_mixin import DateRelationMixin
from .user_mixins import UserRelationMixin

if TYPE_CHECKING:
    from .user import User


class CalculationProfile(BaseModel, UserRelationMixin, DateRelationMixin):
    __tablename__ = "calculation_profiles"

    # _user_id_nullable: bool = False
    _user_id_unique: bool = True
    _user_back_populates: str | None = "calculation"

    id: Mapped[int] = mapped_column(primary_key=True)
    limit: Mapped[int] = mapped_column(default=0, server_default=0)
