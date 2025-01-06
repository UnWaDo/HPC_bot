from datetime import datetime
from typing import List

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import subqueryload

from HPC_bot.database.base_dao import BaseDAO
from HPC_bot.database.user_dao import UserDAO
from HPC_bot.models.calculation import Calculation
from HPC_bot.models.organization import Organization
from HPC_bot.models.person import Person
from HPC_bot.models.telegram_user import TelegramUser
from HPC_bot.models.user import User


class TelegramUserDAO(BaseDAO[TelegramUser]):
    @classmethod
    async def get_by_id(cls, session, id):
        query = select(cls.model).where(cls.model.tg_id == id)

        return await session.scalar(query)

    @classmethod
    async def register(
        cls, session: AsyncSession, tg_id: int, first_name: str, last_name: str
    ):
        user = await UserDAO.register(session, first_name, last_name)

        tg_user = TelegramUser(tg_id=tg_id, user=user)
        session.add(tg_user)

        await session.commit()

        return tg_user

    @classmethod
    async def search_users(
        cls,
        session: AsyncSession,
        last_name: str = None,
        first_name: str = None,
        organization: str = None,
    ):

        query = select(TelegramUser).join(User).join(Person)

        if last_name is not None:
            query = query.where(Person.last_name.ilike(last_name))

        if first_name is not None:
            query = query.where(Person.first_name.ilike(first_name))

        if organization is not None:
            query = query.where(
                or_(
                    Organization.name.ilike(organization),
                    Organization.abbreviation.ilike(organization),
                )
            )

        result = await session.scalars(query)
        return result.all()

    @classmethod
    async def get_tg_user(
        cls, session: AsyncSession, tg_id: int = None, user_id: int = None
    ):

        if tg_id is None and user_id is None:
            return None

        query = select(TelegramUser).join(User)

        if tg_id is not None:
            query = query.where(TelegramUser.tg_id == tg_id)
        if user_id is not None:
            query = query.where(User.id == user_id)

        result = await session.execute(query)

        return result.scalar_one_or_none()

    @classmethod
    async def get_tg_user_with_calcs(
        cls,
        session: AsyncSession,
        tg_id: int = None,
        user_id: int = None,
        since: datetime = None,
    ) -> TelegramUser:

        if tg_id is None and user_id is None:
            return None

        query = (
            select(TelegramUser, func.count(Calculation.user_id).label("num_calc"))
            .select_from(TelegramUser)
            .options(
                subqueryload(TelegramUser.user)
                .joinedload(User.person)
                .joinedload(Person.organization)
            )
            .join(User)
            .outerjoin(Calculation)
        )

        if since is not None:
            query = query.where(
                or_(
                    Calculation.start_datetime >= since,
                    Calculation.start_datetime == None,
                )
            )

        if tg_id is not None:
            query = query.where(TelegramUser.tg_id == tg_id)

        if user_id is not None:
            query = query.where(User.id == user_id)

        query = query.group_by(TelegramUser.tg_id)

        result = await session.execute(query)
        data = result.first()

        if data is None:
            return None

        tg_user, count = data
        setattr(tg_user, "num_calc", count)

        return tg_user

    @classmethod
    async def get_all_with_calcs(
        cls, session: AsyncSession, since: datetime = None, remove_blocked: bool = False
    ):

        query = (
            select(TelegramUser, func.count(Calculation.user_id).label("num_calc"))
            .select_from(TelegramUser)
            .options(
                subqueryload(TelegramUser.user)
                .joinedload(User.person)
                .joinedload(Person.organization)
            )
            .join(User)
            .outerjoin(Calculation)
        )

        if since is not None:
            query = query.where(
                or_(
                    Calculation.start_datetime >= since,
                    Calculation.start_datetime == None,
                )
            )

        if remove_blocked:
            query = query.where(~User.blocked)

        query = query.group_by(TelegramUser.tg_id)
        query = query.order_by(desc("num_calc"))

        result = await session.execute(query)

        data = result.all()

        users: List[TelegramUser] = []
        for tg_user, count in data:
            setattr(tg_user, "num_calc", count)

            users.append(tg_user)

        return users
