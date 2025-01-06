from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, joinedload, mapped_column, relationship

from .base_model import BaseDBModel
from HPC_bot.database.database import sessionmaker
from .user import User


class UnauthorizedAccessError(Exception):
    pass

class TelegramUser(BaseDBModel):
    __tablename__ = 'tg_user'

    tg_id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey('hpc_user.id'))
    user: Mapped[User] = relationship(back_populates='tg_user', lazy='joined', join_depth=2)

    @staticmethod
    async def authenticate(tg_id: int,
                           no_throw: bool = False,
                           apply_join: bool = False) -> 'TelegramUser':
        async with sessionmaker() as session:
            async with session.begin():

                options = None
                if apply_join:
                    options = [joinedload(TelegramUser.user)]

                user = await session.get(TelegramUser, tg_id, options=options)

        if user is not None:
            return user

        if not no_throw:
            raise UnauthorizedAccessError(
                f'User with id {tg_id} is unauthorized')

        return user
