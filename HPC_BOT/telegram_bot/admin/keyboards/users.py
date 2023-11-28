from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from HPC_BOT.telegram_bot.admin.callbacks_data import AdminMenuCallbacksData, UsersCallbackData

get_all_users_list = InlineKeyboardButton(
    text="🗂 Список пользователей",
    callback_data=UsersCallbackData.ALL_USERS_LIST.value,
)
choose_user = InlineKeyboardButton(
    text="📄 Открыть панель пользователя",
    callback_data=UsersCallbackData.CHOOSE_USER.value,
)
back_to_menu = InlineKeyboardButton(
    text="🔙 Назад",
    callback_data=AdminMenuCallbacksData.MAIN.value,
)

users_menu_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [get_all_users_list],
        [choose_user],
        [back_to_menu],
    ],
    resize_keyboard=True,
)

back_to_users = InlineKeyboardButton(
                text="🔙 Назад",
                callback_data=UsersCallbackData.MAIN.value,
            )
back_to_users_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [back_to_users]
    ]
)