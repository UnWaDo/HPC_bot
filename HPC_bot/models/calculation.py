import enum
import os
from datetime import datetime, timezone
from typing import List

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import BaseDBModel
from .cluster import Cluster
from .user import User
from .utils import IntEnum


class CalculationStatus(enum.Enum):
    NOT_STARTED = 0
    UPLOADED = 5
    PENDING = 10
    RUNNING = 50

    FINISHED_OK = 100
    FAILED_TO_UPLOAD = 110

    LOADED = 200
    CLOUDED = 300
    SENDED = 1000

    @staticmethod
    def from_slurm(status: str) -> "CalculationStatus":
        if status == "PD":
            return CalculationStatus.PENDING
        if status == "R":
            return CalculationStatus.RUNNING

        return CalculationStatus.FINISHED_OK

    def __lt__(self, other):
        return self.value < other.value

    def __gt__(self, other):
        return self.value > other.value

    def __ge__(self, other):
        return self.value >= other.value

    def __le__(self, other):
        return self.value <= other.value


class SubmitType(enum.Enum):
    TELEGRAM = 0


class CalculationLimitExceeded(Exception):
    pass


class BlockedException(Exception):
    pass


class Calculation(BaseDBModel):
    __tablename__ = "calculation"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(50))
    command: Mapped[str] = mapped_column(String(255))

    start_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    end_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    slurm_id: Mapped[int] = mapped_column(nullable=True)

    status: Mapped[CalculationStatus] = mapped_column(
        IntEnum(CalculationStatus), default=CalculationStatus.NOT_STARTED
    )
    submit_type: Mapped[SubmitType] = mapped_column(
        IntEnum(SubmitType), default=SubmitType.TELEGRAM
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("hpc_user.id"))
    user: Mapped[User] = relationship(back_populates="calculations", lazy="joined")

    cluster_id: Mapped[int] = mapped_column(ForeignKey("cluster.id"))
    cluster: Mapped[Cluster] = relationship(
        back_populates="calculations", lazy="joined"
    )

    def get_status(self) -> CalculationStatus:
        return self.status

    def set_status(self, e: CalculationStatus):
        self.status = e

    def get_submit_type(self) -> SubmitType:
        return self.submit_type

    def get_folder_name(self) -> str:
        name, _ = os.path.splitext(self.name)

        if self.start_datetime.replace(tzinfo=timezone.utc) < datetime(
            2024, 5, 10, tzinfo=timezone.utc
        ):
            stamp = self.start_datetime.timestamp()
        else:
            stamp = self.start_datetime.replace(tzinfo=timezone.utc).timestamp()

        data = [
            int(stamp),
            self.user_id,
            name,
        ]

        return "_".join(map(str, data))
