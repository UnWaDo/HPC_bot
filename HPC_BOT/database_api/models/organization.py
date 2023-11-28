from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import BaseModel
from .mixins import DateRelationMixin

if TYPE_CHECKING:
    from .user import User


class Organization(BaseModel, DateRelationMixin):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    abbreviate: Mapped[str] = mapped_column(String(20), unique=True)
    full_name: Mapped[str] = mapped_column(String(200))
    photo: Mapped[str] = mapped_column(String(500), nullable=True)

    users: Mapped[list["User"]] = relationship(back_populates="organization", cascade="all, delete")

    def __repr__(self):
        return f"Organization(id={self.id}, abbreviate={self.abbreviate})"

    def __str__(self):
        return self.__repr__()
