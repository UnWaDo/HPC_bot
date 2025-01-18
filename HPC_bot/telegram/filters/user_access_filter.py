from typing import Any, Dict
from aiogram.types import TelegramObject
from aiogram.filters import BaseFilter

from HPC_bot.models.telegram_user import TelegramUser
from HPC_bot.models.user import AccessLevel


class UserAccessFilter(BaseFilter):
    access_level: AccessLevel

    def __init__(self, access_level: AccessLevel):
        if isinstance(access_level, str):
            self.access_level = AccessLevel[access_level]
        elif isinstance(access_level, int):
            self.access_level = AccessLevel(access_level)
        else:
            self.access_level = access_level

    async def __call__(
        self, event: TelegramObject, authorized_user: TelegramUser = None
    ):
        if authorized_user is None:
            return False

        if authorized_user.user.access_level >= self.access_level:
            return True

        return False
