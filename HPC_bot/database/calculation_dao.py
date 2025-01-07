from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from HPC_bot.database.base_dao import BaseDAO
from HPC_bot.database.cluster_dao import ClusterDAO
from HPC_bot.hpc import Cluster as ClusterHPC
from HPC_bot.models.calculation import (
    BlockedException,
    Calculation,
    CalculationLimitExceeded,
    CalculationStatus,
    SubmitType,
)
from HPC_bot.models.user import User
from HPC_bot.utils.utils import get_month_start


class CalculationDAO(BaseDAO[Calculation]):
    default_order_column = Calculation.start_datetime

    @classmethod
    async def count_for_user(
        cls, session: AsyncSession, user_id: int, since: datetime = None
    ) -> int:
        query = (
            select(func.count())
            .select_from(cls.model)
            .where(cls.model.user_id == user_id)
        )

        if since is not None:
            query = query.where(cls.model.start_datetime >= since)

        return await session.scalar(query)

    @classmethod
    async def get_all(cls, session: AsyncSession):
        query = select(cls.model).order_by(cls.model.start_datetime)

        result = await session.scalars(query)
        return result.all()

    @staticmethod
    async def get_not_started(cls, session: AsyncSession):
        query = (
            select(cls.model)
            .where(cls.model.status == CalculationStatus.NOT_STARTED)
            .order_by(cls.model.start_datetime)
        )

        result = await session.scalars(query)

        return result.all()

    @classmethod
    async def get_unfinished(cls, session: AsyncSession):

        query = (
            select(cls.model)
            .where(cls.model.status < CalculationStatus.FINISHED_OK)
            .order_by(cls.model.start_datetime)
        )

        result = await session.execute(query)

        return result.scalars().all()

    @classmethod
    async def get_by_status(cls, session: AsyncSession, status: CalculationStatus):

        query = (
            select(cls.model)
            .where(cls.model.status == status)
            .order_by(cls.model.start_datetime)
        )

        result = await session.scalars(query)

        return result.all()

    @classmethod
    async def get_finished(cls, session: AsyncSession):
        query = (
            select(cls.model)
            .where(cls.model.submit_type == SubmitType.TELEGRAM)
            .where(
                or_(
                    cls.model.status == CalculationStatus.CLOUDED,
                    cls.model.status == CalculationStatus.FAILED_TO_UPLOAD,
                )
            )
        )
        result = await session.scalars(query)
        return result.all()

    @classmethod
    async def new_calculation(
        cls,
        session: AsyncSession,
        name: str,
        command: str,
        user: User,
        submit_type: SubmitType,
        cluster: ClusterHPC,
    ):

        if user.blocked:
            raise BlockedException(f"User #{user.id} is blocked")

        user_calculations = await cls.count_for_user(
            session, user.id, since=get_month_start()
        )

        if user_calculations >= user.calculation_limit:

            raise CalculationLimitExceeded(
                f"User #{user.id} exceeded its calculation limit"
            )

        cluster_model = await ClusterDAO.get_or_create(
            session, cluster.label, cluster.label
        )

        calculation = cls.model(
            name=name,
            command=command,
            user=user,
            cluster=cluster_model,
            submit_type=submit_type,
            start_datetime=datetime.now(timezone.utc),
        )
        session.add(cluster_model)
        session.add(calculation)

        await session.commit()

        return calculation
