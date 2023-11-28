from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from HPC_BOT.telegram_bot.admin.callbacks_data import (
    OrganizationsCallbackData,
    AdminMenuCallbacksData,
)

# Organizations menu
get_all_organizations_list = InlineKeyboardButton(
    text="🗂 Список организаций",
    callback_data=OrganizationsCallbackData.ALL_ORGANIZATION_LIST.value,
)
add_organization = InlineKeyboardButton(
    text="➕ Добавить организацию",
    callback_data=OrganizationsCallbackData.ADD_ORGANIZATION.value,
)
choose_organization = InlineKeyboardButton(
    text="📄 Открыть меню организации",
    callback_data=OrganizationsCallbackData.CHOOSE_ORGANIZATION.value,
)
back_to_menu = InlineKeyboardButton(
    text="🔙 Назад",
    callback_data=AdminMenuCallbacksData.MAIN.value,
)

organizations_menu_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [get_all_organizations_list],
        [add_organization],
        [choose_organization],
        [back_to_menu],
    ],
    resize_keyboard=True,
)

add_photo_organization = InlineKeyboardButton(
    text="📷 Добавить фотографию",
    callback_data=OrganizationsCallbackData.ADD_PHOTO.value,
)
change_photo_organization = InlineKeyboardButton(
    text="📷 Изменить фотографию",
    callback_data=OrganizationsCallbackData.CHANGE_PHOTO.value,
)

change_abbreviate = InlineKeyboardButton(
    text="🏢 Изменить аббревиатуру",
    callback_data=OrganizationsCallbackData.CHANGE_ABBREVIATE.value,
)
change_full_name = InlineKeyboardButton(
    text="📋 Изменить название",
    callback_data=OrganizationsCallbackData.CHANGE_FULL_NAME.value,
)
get_all_users_by_organization = InlineKeyboardButton(
    text="📰 Список пользователей",
    callback_data=OrganizationsCallbackData.GET_USERS_BY_ORGANIZATION.value,
)
back_to_organizations = InlineKeyboardButton(
                text="🔙 Назад",
                callback_data=OrganizationsCallbackData.MAIN.value,
            )
back_to_organizations_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [back_to_organizations]
    ]
)

organization_menu_with_photo_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [change_photo_organization],
        [change_abbreviate],
        [change_full_name],
        [get_all_users_by_organization],
        [back_to_organizations]
    ],
    resize_keyboard=True,
)

organization_menu_without_photo_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [add_photo_organization],
        [change_abbreviate],
        [change_full_name],
        [get_all_users_by_organization],
        [back_to_organizations]
    ],
    resize_keyboard=True,
)

back_to_organization_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=OrganizationsCallbackData.BACK_TO_ORGANIZATION_MENU.value
        )]
    ],
    resize_keyboard=True,
)