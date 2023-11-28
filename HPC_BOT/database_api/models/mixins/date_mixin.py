import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import declared_attr, Mapped, mapped_column


class DateRelationMixin:
    @declared_attr
    def update_at(cls) -> Mapped[datetime.datetime]:
        return mapped_column(
            DateTime(timezone=True), onupdate=func.now(), server_default=func.now()
        )

    @declared_attr
    def joined_at(cls) -> Mapped[datetime.datetime]:
        return mapped_column(DateTime(timezone=True), server_default=func.now())
