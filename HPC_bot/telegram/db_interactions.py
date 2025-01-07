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
async def authorize(tg_id: int, session: AsyncSession):
    return await TelegramUserDAO.get_by_id(session, tg_id)


@db_connection
async def register(tg_id: int, first_name: str, last_name: str, session: AsyncSession):
    return await TelegramUserDAO.register(session, tg_id, first_name, last_name)


@db_connection
async def get_finished_calculations(session: AsyncSession):
    return await CalculationDAO.get_finished(session)


@db_connection
async def update_calculations(calculations: List[Calculation], session: AsyncSession):
    for calculation in calculations:
        session.add(calculation)

    await session.commit()


@db_connection
async def new_calculation(
    name: str, command: str, user: User, cluster: Cluster, session: AsyncSession
):
    return await CalculationDAO.new_calculation(
        session, name, command, user, SubmitType.TELEGRAM, cluster
    )


@db_connection
async def update_person(
    person_id: int,
    session: AsyncSession,
    first_name: str = None,
    last_name: str = None,
    organization: str = None,
):
    return await PersonDAO.update_from_raw_data(
        session, person_id, first_name, last_name, organization
    )


@db_connection
async def block_user(user_id: int, session: AsyncSession):
    return await UserDAO.block(session, user_id)


@db_connection
async def unblock_user(user_id: int, session: AsyncSession):
    return await UserDAO.unblock(session, user_id)


@db_connection
async def approve_user(user_id: int, session: AsyncSession):
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
    last_name: str, first_name: str, organization: str, session: AsyncSession
):
    return await TelegramUserDAO.search_users(
        session, last_name, first_name, organization
    )


@db_connection
async def alter_limit(user_id: int, limit: int, session: AsyncSession):
    return await UserDAO.update(session, user_id, limit=limit)
