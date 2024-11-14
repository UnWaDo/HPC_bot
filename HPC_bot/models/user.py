from datetime import datetime
from typing import TYPE_CHECKING, List, Sequence

from sqlalchemy import ForeignKey, func, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import BaseDBModel, sessionmaker
from .organization import Organization
from .person import Person

if TYPE_CHECKING:
    from .calculation import Calculation
    from .telegram_user import TelegramUser

NEWLY_REGISTERED_LIMIT = 5
APPROVED_BASE_LIMIT = 50


class User(BaseDBModel):
    __tablename__ = 'hpc_user'

    id: Mapped[int] = mapped_column(primary_key=True)

    calculation_limit: Mapped[int] = mapped_column()
    access_level: Mapped[int] = mapped_column(default=1000)

    blocked: Mapped[bool] = mapped_column(default=False)

    person_id: Mapped[int] = mapped_column(ForeignKey('person.id'))
    person: Mapped[Person] = relationship(back_populates='user', lazy='joined')

    tg_user: Mapped['TelegramUser'] = relationship(back_populates='user',
                                                   lazy='joined', join_depth=2)
    calculations: Mapped[List['Calculation']] = relationship(
        back_populates='user')

    @staticmethod
    async def register(first_name: str,
                       last_name: str,
                       organization: Organization = None) -> 'User':

        async with sessionmaker() as session:
            async with session.begin():

                person = Person(
                    first_name=first_name,
                    last_name=last_name,
                    organization=organization,
                    registered=True,
                )
                user = User(
                    calculation_limit=NEWLY_REGISTERED_LIMIT,
                    person=person,
                )

                session.add(user)
                await session.commit()

        return user

    @staticmethod
    async def approve(id: int) -> 'User':
        async with sessionmaker() as session:
            async with session.begin():
                user = await session.get(User, id)

                if user is None:
                    return None

                if user.person.approved:
                    return None

                user.person.approved = True
                user.calculation_limit = APPROVED_BASE_LIMIT

                await session.commit()

        return user

    @staticmethod
    async def block(id: int) -> 'User':
        async with sessionmaker() as session:
            async with session.begin():
                user = await session.get(User, id)

                if user.blocked:
                    return None

                user.blocked = True

                await session.commit()

        return user

    @staticmethod
    async def unblock(id: int) -> 'User':
        async with sessionmaker() as session:
            async with session.begin():
                user = await session.get(User, id)

                if not user.blocked:
                    return None

                user.blocked = False

                await session.commit()

        return user

    def get_calculations(self, since: datetime = None) -> List['Calculation']:
        if since is None:
            return self.calculations

        return list(
            filter(lambda x: x.start_datetime >= since, self.calculations))
