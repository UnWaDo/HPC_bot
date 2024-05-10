import enum
import os
from datetime import datetime, timezone
from typing import List

from sqlalchemy import DateTime, ForeignKey, String, func, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..hpc import Cluster as ClusterHPC
from ..utils import get_month_start
from .base_model import BaseDBModel, sessionmaker
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
    def from_slurm(status: str) -> 'CalculationStatus':
        if status == 'PD':
            return CalculationStatus.PENDING
        if status == 'R':
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
    __tablename__ = 'calculation'

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(50))
    command: Mapped[str] = mapped_column(String(255))

    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                     default=func.now())
    end_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                   nullable=True)

    slurm_id: Mapped[int] = mapped_column(nullable=True)

    status: Mapped[CalculationStatus] = mapped_column(
        IntEnum(CalculationStatus), default=CalculationStatus.NOT_STARTED)
    submit_type: Mapped[SubmitType] = mapped_column(
        IntEnum(SubmitType), default=SubmitType.TELEGRAM)

    user_id: Mapped[int] = mapped_column(ForeignKey('hpc_user.id'))
    user: Mapped[User] = relationship(back_populates='calculations',
                                      lazy='joined')

    cluster_id: Mapped[int] = mapped_column(ForeignKey('cluster.id'))
    cluster: Mapped[Cluster] = relationship(back_populates='calculations',
                                            lazy='joined')

    @staticmethod
    async def count_for_user(user: User, since: datetime = None) -> int:
        query = select(func.count()).select_from(Calculation).where(
            Calculation.user == user)

        if since is not None:
            query = query.where(Calculation.start_datetime >= since)

        async with sessionmaker() as session:
            async with session.begin():

                return await session.scalar(query)

    @staticmethod
    async def new_calculation(name: str, command: str, user: User,
                              submit_type: SubmitType,
                              cluster: ClusterHPC) -> 'Calculation':

        if user.blocked:
            raise BlockedException(f'User #{user.id} is blocked')

        user_calculations = await Calculation.count_for_user(
            user, since=get_month_start())

        if user_calculations >= user.calculation_limit:

            raise CalculationLimitExceeded(
                f'User #{user.id} exceeded its calculation limit')

        cluster_model = await Cluster.get_or_create(cluster.label,
                                                    cluster.label)

        async with sessionmaker() as session:
            async with session.begin():

                calculation = Calculation(
                    name=name,
                    command=command,
                    user=user,
                    cluster=cluster_model,
                    submit_type=submit_type,
                )
                session.add(cluster_model)
                session.add(calculation)

                await session.commit()

                return calculation

    @staticmethod
    async def get_all() -> List['Calculation']:
        async with sessionmaker() as session:
            async with session.begin():

                query = select(Calculation).order_by(
                    Calculation.start_datetime)

                result = await session.execute(query)

                return result.scalars().all()

    @staticmethod
    async def get_not_started() -> List['Calculation']:
        async with sessionmaker() as session:
            async with session.begin():

                query = select(Calculation).where(
                    Calculation.status ==
                    CalculationStatus.NOT_STARTED).order_by(
                        Calculation.start_datetime)

                result = await session.execute(query)

                return result.scalars().all()

    @staticmethod
    async def get_unfinished() -> List['Calculation']:
        async with sessionmaker() as session:
            async with session.begin():

                query = select(Calculation).where(
                    Calculation.status <
                    CalculationStatus.FINISHED_OK).order_by(
                        Calculation.start_datetime)

                result = await session.execute(query)

                return result.scalars().all()

    @staticmethod
    async def get_by_status(status: CalculationStatus) -> List['Calculation']:
        async with sessionmaker() as session:
            async with session.begin():

                query = select(Calculation).where(
                    Calculation.status == status).order_by(
                        Calculation.start_datetime)

                result = await session.execute(query)

                return result.scalars().all()

    def get_status(self) -> CalculationStatus:
        return self.status

    def set_status(self, e: CalculationStatus):
        self.status = e

    def get_submit_type(self) -> SubmitType:
        return self.submit_type

    def get_folder_name(self) -> str:
        name, _ = os.path.splitext(self.name)

        data = [
            int(self.start_datetime.replace(tzinfo=timezone.utc).timestamp()),
            self.user_id,
            name,
        ]

        return '_'.join(map(str, data))
