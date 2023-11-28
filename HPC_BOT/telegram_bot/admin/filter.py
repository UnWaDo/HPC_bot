from aiogram.filters import Filter
from aiogram.types import Message

from HPC_BOT.telegram_bot.settings import telegram_user_api


class IsAdmin(Filter):
    async def __call__(self, message: Message) -> bool:
        adminList = await telegram_user_api.admin_users
        if message.from_user.id in list(map(lambda TgUser: TgUser.telegram_id, adminList)):
            return True
        return False
