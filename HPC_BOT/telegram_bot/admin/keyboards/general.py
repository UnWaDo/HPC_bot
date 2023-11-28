from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from HPC_BOT.telegram_bot.admin.callbacks_data import (
    AdminMenuCallbacksData,
    OrganizationsCallbackData,
    UsersCallbackData,
    MailingCallbackData,
)

organizationsButton = InlineKeyboardButton(
    text="🏢 Организации", callback_data=OrganizationsCallbackData.MAIN.value
)
usersButton = InlineKeyboardButton(
    text="👤 Пользователи", callback_data=UsersCallbackData.MAIN.value
)
mailingButton = InlineKeyboardButton(
    text="📫 Рассылка", callback_data=MailingCallbackData.MAIN.value
)

generalAdminInlineKeyboard = InlineKeyboardMarkup(
    inline_keyboard=[[organizationsButton], [usersButton], [mailingButton]],
    resize_keyboard=True,
)

to_admin_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🏠 В меню",
                callback_data=AdminMenuCallbacksData.MAIN.value,
            )
        ]
    ]
)