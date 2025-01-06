from typing import TYPE_CHECKING, List

from sqlalchemy import String, or_, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import BaseDBModel
from HPC_bot.database.database import sessionmaker

if TYPE_CHECKING:
    from .calculation import Calculation


class Cluster(BaseDBModel):
    __tablename__ = "cluster"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(50), unique=True)
    label: Mapped[str] = mapped_column(String(15), unique=True)

    calculations: Mapped[List["Calculation"]] = relationship(back_populates="cluster")
