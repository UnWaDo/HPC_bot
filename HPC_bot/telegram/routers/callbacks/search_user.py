from aiogram import F, Router
from aiogram.types import CallbackQuery

from HPC_bot.models.user import AccessLevel
from HPC_bot.telegram.db_interactions import get_user_by_id
from HPC_bot.telegram.filters.user_access_filter import UserAccessFilter
from HPC_bot.telegram.keyboards.factories import UsersActionCallback
from HPC_bot.telegram.keyboards.search_users import (
    SEARCH_USERS_KEYBOARD,
    build_search_users_full_keyboard,
)
from HPC_bot.telegram.keyboards.user_info import user_info_keyboard
from HPC_bot.telegram.utils import create_user_link


search_users_callback_router = Router()
search_users_callback_router.callback_query.filter(
    UserAccessFilter(AccessLevel.MODERATOR),
)

full_search = UsersActionCallback(action="search_full")
ADMIN_NO_OPTIONS_SEARCH = "Таких пользователей нет"
ADMIN_GET_USER_INFO = "Выберите пользователя"


@search_users_callback_router.callback_query(F.data == "users_search")
async def search_users(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выберите режим", reply_markup=SEARCH_USERS_KEYBOARD
    )
    await callback.answer()


async def get_user_info(callback: CallbackQuery, callback_data: UsersActionCallback):
    user = await get_user_by_id(callback_data.object_id)

    if user is None:
        return await callback.answer("Нет такого пользователя")

    tg_id = user.tg_user.tg_id if f"ID ТГ {user.tg_user}" else "(нет ТГ-аккаунта)"
    await callback.message.answer(
        f"Пользователь {create_user_link(model=user.tg_user)} ({tg_id})\n"
        f"{user.person}\n"
        f"Лимит расчётов: {user.calculation_limit}",
        reply_markup=user_info_keyboard(user, is_admin=True),
    )
    await callback.answer()


full_search.create_keyboard_handlers(
    search_users_callback_router,
    build_search_users_full_keyboard,
    ADMIN_NO_OPTIONS_SEARCH,
    "Список пользователей",
    get_user_info,
    previous_markup=SEARCH_USERS_KEYBOARD,
)
