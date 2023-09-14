from peewee import BigIntegerField, ForeignKeyField, DoesNotExist, JOIN

from .base_model import BaseDBModel
from .user import User
from .person import Person


class UnauthorizedAccessError(Exception):
    pass


class TelegramUser(BaseDBModel):
    tg_id = BigIntegerField(primary_key=True)

    user = ForeignKeyField(
        model=User,
        backref='tg_user'
    )

    class Meta:
        table_name = 'tg_user'

    @staticmethod
    def authenticate(tg_id: int, no_throw: bool = False,
                     apply_join: bool = False) -> 'TelegramUser':
        try:
            if not apply_join:
                user = TelegramUser.get_by_id(tg_id)
            else:
                users = (TelegramUser.select(TelegramUser, User, Person)
                         .join(User)
                         .join(Person)
                         .where(TelegramUser.tg_id == tg_id)
                         )
                if len(users) == 0:
                    user = None
                else:
                    user = users[0]
        except DoesNotExist:
            user = None

        if user is None and not no_throw:
            raise UnauthorizedAccessError(
                'User with id %d is unauthorized' % tg_id)
        return user

    @staticmethod
    def register(tg_id: int, first_name: str, last_name: str):
        user = User.register(first_name, last_name)

        return TelegramUser.create(tg_id=tg_id, user=user)
