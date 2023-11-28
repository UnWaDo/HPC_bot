import datetime

from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from .base_model import BaseModel


class Calculation(BaseModel):
    __tablename__ = "calculations"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile: Mapped[int] = mapped_column(ForeignKey("calculation_profiles.id"))
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
