from typing import Any, Awaitable, Callable, Dict
from aiogram.types import Message, TelegramObject
from aiogram import BaseMiddleware

from HPC_bot.models.user import AccessLevel
from HPC_bot.telegram.db_interactions import authorize


class UserAuthorizationMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ):
        tg_user_id = data["event_from_user"].id

        data["authorized_user"] = await authorize(tg_user_id)

        return await handler(event, data)
