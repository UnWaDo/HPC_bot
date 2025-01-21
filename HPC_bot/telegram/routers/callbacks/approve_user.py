from HPC_bot.models.user import AccessLevel
from HPC_bot.telegram.db_interactions import approve_user
from HPC_bot.telegram.filters.user_access_filter import UserAccessFilter
from HPC_bot.telegram.keyboards.approve_user import build_approve_user_keyboard
from HPC_bot.telegram.keyboards.factories import (
    UsersActionCallback,
)
from HPC_bot.telegram.routers.responses_text import (
    ADMIN_NO_PEOPLE_TO_APPROVE,
    APPROVE_FAILED,
    APPROVE_LOG,
    APPROVE_NOTIFY,
    APPROVE_OK,
)


from aiogram import F, Router
from aiogram.types import CallbackQuery

from HPC_bot.telegram.utils import create_user_link, log_message


approve_users_callback_router = Router()
approve_users_callback_router.callback_query.filter(
    UserAccessFilter(AccessLevel.MODERATOR),
)

approve_callback = UsersActionCallback(action="approve")


async def approve_user_handler(
    callback: CallbackQuery, callback_data: UsersActionCallback
):
    user = await approve_user(callback_data.object_id)
    if user is None:
        return await callback.answer(APPROVE_FAILED)

    await callback.answer(APPROVE_OK)
    await callback.bot.send_message(
        user.tg_user.tg_id, APPROVE_NOTIFY.format(calc_limit=user.calculation_limit)
    )
    await log_message(
        callback.bot,
        APPROVE_LOG.format(
            user=create_user_link(model=user.tg_user),
            admin=create_user_link(callback.from_user),
            calc_limit=user.calculation_limit,
        ),
    )


approve_callback.create_keyboard_handlers(
    approve_users_callback_router,
    build_approve_user_keyboard,
    ADMIN_NO_PEOPLE_TO_APPROVE,
    "Выберите пользователя для одобрения",
    approve_user_handler,
)
