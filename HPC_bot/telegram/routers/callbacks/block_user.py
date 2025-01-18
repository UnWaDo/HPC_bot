from aiogram import Router
from aiogram.types import CallbackQuery

from HPC_bot.models.user import AccessLevel
from HPC_bot.telegram.db_interactions import block_user
from HPC_bot.telegram.filters.user_access_filter import UserAccessFilter
from HPC_bot.telegram.keyboards.block_user import build_block_user_keyboard
from HPC_bot.telegram.keyboards.factories import (
    UsersActionCallback,
)
from HPC_bot.telegram.routers.responses_text import (
    ADMIN_NO_PEOPLE_TO_BLOCK,
    BLOCK_FAILED,
    BLOCK_LOG,
    BLOCK_NOTIFY,
    BLOCK_OK,
)
from HPC_bot.telegram.utils import create_user_link, log_message

block_users_callback_router = Router()
block_users_callback_router.callback_query.filter(
    UserAccessFilter(AccessLevel.MODERATOR),
)

block_callback = UsersActionCallback(action="block")


async def block_user_handler(
    callback: CallbackQuery, callback_data: UsersActionCallback
):
    user = await block_user(callback_data.object_id)
    if user is None:
        return await callback.answer(BLOCK_FAILED)

    await callback.answer(BLOCK_OK)
    await callback.bot.send_message(
        user.tg_user.tg_id, BLOCK_NOTIFY.format(calc_limit=user.calculation_limit)
    )
    await log_message(
        callback.bot,
        BLOCK_LOG.format(
            user=create_user_link(model=user.tg_user),
            admin=create_user_link(callback.from_user),
            calc_limit=user.calculation_limit,
        ),
    )


block_callback.create_keyboard_handlers(
    block_users_callback_router,
    build_block_user_keyboard,
    ADMIN_NO_PEOPLE_TO_BLOCK,
    "Выберите пользователя для блокировки",
    block_user_handler,
)
