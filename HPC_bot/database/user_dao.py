from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from HPC_bot.database.base_dao import BaseDAO
from HPC_bot.models.organization import Organization
from HPC_bot.models.person import Person
from HPC_bot.models.telegram_user import TelegramUser
from HPC_bot.models.user import APPROVED_BASE_LIMIT, AccessLevel, User


class UserDAO(BaseDAO[User]):
    @classmethod
    async def register(
        cls,
        session: AsyncSession,
        first_name: str,
        last_name: str,
        organization: Organization = None,
    ):
        person = Person(
            first_name=first_name,
            last_name=last_name,
            organization=organization,
            registered=True,
        )
        user = User(
            person=person,
        )

        session.add(user)
        await session.commit()

        return user

    save = register

    @classmethod
    async def get_unapproved_filled_users(
        cls, session: AsyncSession, limit: int = None, last_id: int = None
    ):
        query = (
            select(User)
            .join(Person)
            .where(
                ~Person.approved,
                Person.organization != None,
            )
            .limit(limit)
            .order_by(User.id)
        )
        if last_id is not None:
            query = query.where(User.id > last_id)

        result = await session.scalars(query)
        return result.all()

    @classmethod
    async def approve(cls, session: AsyncSession, user_id: int):
        user = await cls.get_by_id(session, user_id)

        if user is None or user.person.approved:
            return None

        user.person.approved = True
        if user.access_level < AccessLevel.APPROVED:
            user.access_level = AccessLevel.APPROVED.value

        if user.calculation_limit < APPROVED_BASE_LIMIT:
            user.calculation_limit = APPROVED_BASE_LIMIT

        await session.commit()
        return user

    @classmethod
    async def block(cls, session: AsyncSession, user_id: int):
        user = await cls.get_by_id(session, user_id)

        if user is None or user.blocked:
            return None

        user.blocked = True

        await session.commit()
        return user

    @classmethod
    async def unblock(cls, session: AsyncSession, user_id: int):
        user = await cls.get_by_id(session, user_id)

        if user is None or not user.blocked:
            return None

        user.blocked = False

        await session.commit()
        return user

    @classmethod
    async def get_blocked_users(
        cls,
        session: AsyncSession,
        limit: int = None,
        last_id: int = None,
    ):
        query = (
            select(User)
            .where(
                User.blocked,
            )
            .limit(limit)
            .order_by(User.id)
        )
        if last_id is not None:
            query = query.where(User.id > last_id)

        result = await session.scalars(query)
        return result.all()

    @classmethod
    async def get_nonblocked_users(
        cls,
        session: AsyncSession,
        limit: int = None,
        last_id: int = None,
    ):
        query = (
            select(User)
            .where(
                ~User.blocked,
            )
            .limit(limit)
            .order_by(User.id)
        )
        if last_id is not None:
            query = query.where(User.id > last_id)

        result = await session.scalars(query)
        return result.all()
