from HPC_bot.models.user import AccessLevel
from HPC_bot.telegram.db_interactions import approve_user
from HPC_bot.telegram.filters.user_access_filter import UserAccessFilter
from HPC_bot.telegram.keyboards.admin_panel import (
    ADMIN_KEYBOARD,
)
from HPC_bot.telegram.keyboards.approve_user import build_approve_user_keyboard
from HPC_bot.telegram.keyboards.factories import (
    PageCallbackFactory,
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


@approve_users_callback_router.callback_query(F.data == "users_approve")
async def approve_users_callback(callback: CallbackQuery):
    keyboard = await build_approve_user_keyboard()

    if keyboard is None:
        if callback.message.text != ADMIN_NO_PEOPLE_TO_APPROVE:
            await callback.message.edit_text(
                ADMIN_NO_PEOPLE_TO_APPROVE, reply_markup=ADMIN_KEYBOARD
            )
        return await callback.answer(ADMIN_NO_PEOPLE_TO_APPROVE)

    await callback.message.edit_text(
        "Выберите пользователя для подтверждения",
        reply_markup=keyboard,
    )
    await callback.answer()


@approve_users_callback_router.callback_query(
    PageCallbackFactory.filter(
        (F.keyboard == "users_approve") & (F.action == "forward")
    )
)
async def approve_users_next_page(
    callback: CallbackQuery, callback_data: PageCallbackFactory
):
    keyboard = await build_approve_user_keyboard(last_id=callback_data.offset)

    if keyboard is None:
        return await callback.answer("Больше пользователей нет")

    await callback.message.edit_reply_markup(reply_markup=keyboard)


@approve_users_callback_router.callback_query(
    PageCallbackFactory.filter((F.keyboard == "users_approve") & (F.action == "back"))
)
async def approve_users_back_page(
    callback: CallbackQuery, callback_data: PageCallbackFactory
):
    keyboard = await build_approve_user_keyboard()

    if keyboard is None:
        await callback.message.edit_text(
            ADMIN_NO_PEOPLE_TO_APPROVE, reply_markup=ADMIN_KEYBOARD
        )
        await callback.answer("Больше пользователей нет")
        return

    await callback.message.edit_reply_markup(reply_markup=keyboard)


@approve_users_callback_router.callback_query(
    UsersActionCallback.filter(F.action == "approve")
)
async def approve_user_callback(
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
