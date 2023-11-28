from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base_model import BaseModel
from .mixins import DateRelationMixin
from .mixins import UserRelationMixin


class CalculationProfile(BaseModel, UserRelationMixin, DateRelationMixin):
    __tablename__ = "calculation_profiles"

    _user_id_unique = True
    _user_back_populates = "calculation_profile"

    id: Mapped[int] = mapped_column(primary_key=True)
    month_limit: Mapped[int] = mapped_column(Integer(), default=0)
