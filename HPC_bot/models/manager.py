from datetime import datetime
from sqlalchemy import func, or_, select
from typing import Sequence

from . import User, TelegramUser, Person, Calculation, Organization
from .user import User
from .base_model import sessionmaker


async def get_all_with_calcs(
        since: datetime = None,
        remove_blocked: bool = False) -> Sequence[TelegramUser]:

    subquery = select(Calculation.user_id).group_by(Calculation.user_id)

    if since is not None:
        subquery = subquery.where(Calculation.start_datetime >= since)

    query = select(TelegramUser).where(TelegramUser.user_id.in_(subquery))

    if remove_blocked:
        query = query.join(User).where(~User.blocked)

    async with sessionmaker() as session:
        async with session.begin():
            result = await session.execute(query)

            return result.scalars().all()


async def search_users(last_name: str = None,
                       first_name: str = None,
                       organization: str = None) -> Sequence[TelegramUser]:

    query = select(TelegramUser).join(User).join(Person)

    if last_name is not None:
        query = query.where(Person.last_name.ilike(last_name))

    if first_name is not None:
        query = query.where(Person.first_name.ilike(first_name))

    if organization is not None:
        query = query.where(
            or_(Organization.name.ilike(organization),
                Organization.abbreviation.ilike(organization)))

    async with sessionmaker() as session:
        async with session.begin():
            result = await session.execute(query)

            return result.scalars().all()


async def get_tg_user(tg_id: int = None, user_id: int = None) -> TelegramUser:

    if tg_id is None and user_id is None:
        return None

    query = select(TelegramUser).join(User)

    if tg_id is not None:
        query = query.where(TelegramUser.tg_id == tg_id)
    if user_id is not None:
        query = query.where(User.id == user_id)

    async with sessionmaker() as session:
        async with session.begin():
            result = await session.execute(query)

            return result.scalar_one_or_none()


async def get_tg_user_with_calcs(tg_id: int = None,
                                 user_id: int = None,
                                 since: datetime = None) -> TelegramUser:

    if tg_id is None and user_id is None:
        return None

    subquery = select(Calculation.user_id).group_by(Calculation.user_id)

    if since is not None:
        subquery = subquery.where(Calculation.start_datetime >= since)

    query = select(TelegramUser).where(TelegramUser.user_id.in_(subquery))

    if tg_id is not None:
        query = query.where(TelegramUser.tg_id == tg_id)

    if user_id is not None:
        query = query.join(User).where(User.id == user_id)

    async with sessionmaker() as session:
        async with session.begin():
            result = await session.execute(query)

            return result.scalar_one_or_none()
