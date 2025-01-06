from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from HPC_bot.database.base_dao import BaseDAO
from HPC_bot.database.user_dao import UserDAO
from HPC_bot.models.telegram_user import TelegramUser


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
