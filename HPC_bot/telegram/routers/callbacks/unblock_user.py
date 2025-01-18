from aiogram import Router
from aiogram.types import CallbackQuery

from HPC_bot.models.user import AccessLevel
from HPC_bot.telegram.db_interactions import unblock_user
from HPC_bot.telegram.filters.user_access_filter import UserAccessFilter
from HPC_bot.telegram.keyboards.factories import UsersActionCallback
from HPC_bot.telegram.keyboards.unblock_user import build_unblock_user_keyboard
from HPC_bot.telegram.routers.responses_text import (
    ADMIN_NO_PEOPLE_TO_UNBLOCK,
    UNBLOCK_FAILED,
    UNBLOCK_LOG,
    UNBLOCK_NOTIFY,
    UNBLOCK_OK,
)
from HPC_bot.telegram.utils import create_user_link, log_message

unblock_users_callback_router = Router()
unblock_users_callback_router.callback_query.filter(
    UserAccessFilter(AccessLevel.MODERATOR),
)

unblock_callback = UsersActionCallback(action="unblock")


async def unblock_user_handler(
    callback: CallbackQuery, callback_data: UsersActionCallback
):
    user = await unblock_user(callback_data.object_id)
    if user is None:
        return await callback.answer(UNBLOCK_FAILED)

    await callback.answer(UNBLOCK_OK)
    await callback.bot.send_message(
        user.tg_user.tg_id, UNBLOCK_NOTIFY.format(calc_limit=user.calculation_limit)
    )
    await log_message(
        callback.bot,
        UNBLOCK_LOG.format(
            user=create_user_link(model=user.tg_user),
            admin=create_user_link(callback.from_user),
            calc_limit=user.calculation_limit,
        ),
    )


unblock_callback.create_keyboard_handlers(
    unblock_users_callback_router,
    build_unblock_user_keyboard,
    ADMIN_NO_PEOPLE_TO_UNBLOCK,
    "Выберите пользователя для разблокировки",
    unblock_user_handler,
)
