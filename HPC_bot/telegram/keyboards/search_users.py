from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from HPC_bot.telegram.db_interactions import search_users
from HPC_bot.telegram.keyboards.factories import UsersActionCallback
from HPC_bot.telegram.keyboards.pages_keyboard import build_pages_keyboard

SEARCH_USERS_PANEL_CALLBACKS = {
    "users_search_full": "Ручной поиск",
    "users_search_by_name": "Поиск по имени",
    "users_search_by_org": "Поиск по организации",
    "users_search_by_attributes": "Поиск по атрибутам",
    "admin_panel_cancel": "Вернуться",
}
SEARCH_USERS_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=v, callback_data=k)]
        for k, v in SEARCH_USERS_PANEL_CALLBACKS.items()
    ]
)


async def build_search_users_full_keyboard(
    limit: int = 10,
    last_id: int = None,
):
    return await build_pages_keyboard(
        object_action="search_full",
        object_name="users",
        object_callback=UsersActionCallback,
        last_id=last_id,
        limit=limit,
        loader=search_users,
    )
