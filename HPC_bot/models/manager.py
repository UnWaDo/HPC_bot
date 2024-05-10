from datetime import datetime
from sqlalchemy import func, or_, select
from sqlalchemy.orm import contains_eager, subqueryload
from typing import Sequence

from . import User, TelegramUser, Person, Calculation, Organization
from .user import User
from .base_model import sessionmaker


async def get_all_with_calcs(
        since: datetime = None,
        remove_blocked: bool = False) -> Sequence[TelegramUser]:

    query = select(TelegramUser, func.count()).options(
        subqueryload(TelegramUser.user).joinedload(User.person).joinedload(
            Person.organization)).join(User).outerjoin(Calculation)

    if since is not None:
        query = query.where(
            or_(Calculation.start_datetime >= since,
                Calculation.start_datetime == None))

    if remove_blocked:
        query = query.where(~User.blocked)

    query = query.group_by(TelegramUser.tg_id)

    async with sessionmaker() as session:
        async with session.begin():
            result = await session.execute(query)

            data = result.all()

    users = []
    for tg_user, count in data:
        setattr(tg_user, 'num_calc', count)

        users.append(tg_user)

    return users


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

    query = select(TelegramUser, func.count()).options(
        subqueryload(TelegramUser.user).joinedload(User.person).joinedload(
            Person.organization)).join(User).outerjoin(Calculation)

    if since is not None:
        query = query.where(
            or_(Calculation.start_datetime >= since,
                Calculation.start_datetime == None))

    if tg_id is not None:
        query = query.where(TelegramUser.tg_id == tg_id)

    if user_id is not None:
        query = query.where(User.id == user_id)

    query = query.group_by(TelegramUser.tg_id)

    async with sessionmaker() as session:
        async with session.begin():
            result = await session.execute(query)

            data = result.first()

    if data is None:
        return None

    tg_user, count = data
    setattr(tg_user, 'num_calc', count)

    return tg_user
