from typing import Optional, Tuple, TYPE_CHECKING
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import BaseDBModel
from HPC_bot.database.database import sessionmaker
from .organization import Organization

if TYPE_CHECKING:
    from .user import User


class Person(BaseDBModel):
    __tablename__ = "person"

    id: Mapped[int] = mapped_column(primary_key=True)

    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))

    registered: Mapped[bool] = mapped_column(default=False)
    approved: Mapped[bool] = mapped_column(default=False)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organization.id"), nullable=True
    )
    organization: Mapped[Organization] = relationship(
        back_populates="persons", lazy="joined"
    )

    user: Mapped["User"] = relationship(back_populates="person")

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.organization.abbreviation if self.organization else 'неизвестно'})"
