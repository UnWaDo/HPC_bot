from datetime import datetime
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from HPC_bot.database.calculation_dao import CalculationDAO
from HPC_bot.database.database import db_connection
from HPC_bot.database.person_dao import PersonDAO
from HPC_bot.database.telegram_user_dao import TelegramUserDAO
from HPC_bot.database.user_dao import UserDAO
from HPC_bot.hpc.cluster import Cluster
from HPC_bot.models.calculation import Calculation, SubmitType
from HPC_bot.models.user import User


@db_connection
async def authorize(session: AsyncSession, tg_id: int):
    return await TelegramUserDAO.get_by_id(session, tg_id)


@db_connection
async def register(session: AsyncSession, tg_id: int, first_name: str, last_name: str):
    return await TelegramUserDAO.register(session, tg_id, first_name, last_name)


@db_connection
async def get_finished_calculations(session: AsyncSession):
    return await CalculationDAO.get_finished(session)


@db_connection
async def update_calculations(session: AsyncSession, calculations: List[Calculation]):
    for calculation in calculations:
        session.add(calculation)

    await session.commit()


@db_connection
async def new_calculation(
    session: AsyncSession, name: str, command: str, user: User, cluster: Cluster
):
    return await CalculationDAO.new_calculation(
        session, name, command, user, SubmitType.TELEGRAM, cluster
    )


@db_connection
async def update_person(
    session: AsyncSession,
    person_id: int,
    first_name: str = None,
    last_name: str = None,
    organization: str = None,
):
    return await PersonDAO.update_from_raw_data(
        session, person_id, first_name, last_name, organization
    )


@db_connection
async def block_user(session: AsyncSession, user_id: int):
    return await UserDAO.block(session, user_id)


@db_connection
async def unblock_user(session: AsyncSession, user_id: int):
    return await UserDAO.unblock(session, user_id)


@db_connection
async def approve_user(session: AsyncSession, user_id: int):
    return await UserDAO.approve(session, user_id)


@db_connection
async def get_all_with_calcs(
    session: AsyncSession, since: datetime = None, remove_blocked=False
):
    return await TelegramUserDAO.get_all_with_calcs(session, since, remove_blocked)


@db_connection
async def get_user_with_calcs(
    session: AsyncSession,
    tg_id: int = None,
    user_id: int = None,
    since: datetime = None,
):
    return await TelegramUserDAO.get_tg_user_with_calcs(session, tg_id, user_id, since)


@db_connection
async def search_users(
    session: AsyncSession,
    last_name: str = None,
    first_name: str = None,
    organization: str = None,
    limit: int = None,
    last_id: int = None,
):
    return await UserDAO.search_users(
        session, last_name, first_name, organization, limit, last_id
    )


@db_connection
async def alter_limit(session: AsyncSession, user_id: int, limit: int):
    return await UserDAO.update(session, user_id, limit=limit)


@db_connection
async def get_unapproved_filled_users(
    session: AsyncSession,
    limit: int = None,
    last_id: int = None,
):
    return await UserDAO.get_unapproved_filled_users(
        session=session, limit=limit, last_id=last_id
    )


@db_connection
async def get_blocked_users(
    session: AsyncSession, limit: int = None, last_id: int = None
):
    return await UserDAO.get_blocked_users(
        session=session, limit=limit, last_id=last_id
    )


@db_connection
async def get_nonblocked_users(
    session: AsyncSession, limit: int = None, last_id: int = None
):
    return await UserDAO.get_nonblocked_users(
        session=session, limit=limit, last_id=last_id
    )


@db_connection
async def get_user_by_id(session: AsyncSession, user_id: int):
    return await UserDAO.get_by_id(session, user_id)
