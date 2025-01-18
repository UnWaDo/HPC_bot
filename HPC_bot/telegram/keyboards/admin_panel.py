from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


ADMIN_PANEL_CALLBACKS = {
    "users_approve": "Подтвердить данные",
    "users_search": "Поиск пользователей",
    "users_alter": "Изменить пользователя",
    "users_block": "Заблокировать пользователя",
    "users_unblock": "Разблокировать пользователя",
    "admin_panel_close": "Закрыть панель",
}
ADMIN_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=v, callback_data=k)]
        for k, v in ADMIN_PANEL_CALLBACKS.items()
    ]
)
