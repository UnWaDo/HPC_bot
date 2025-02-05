from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from HPC_bot.models.user import User
from HPC_bot.telegram.keyboards.factories import UsersActionCallback


def user_info_keyboard(user: User, is_admin: bool = False):
    builder = InlineKeyboardBuilder()

    builder.button(
        text="Показать расчёты",
        callback_data=UsersActionCallback(
            action="list_calculations", object_id=user.id
        ),
    )
    builder.button(
        text="Изменить данные",
        callback_data=UsersActionCallback(action="alter", object_id=user.id),
    )

    if not is_admin:
        builder.button(text="Закрыть панель", callback_data="delete_message")
        builder.adjust(1)
        return builder.as_markup()

    if user.blocked:
        builder.button(
            text="Разблокировать",
            callback_data=UsersActionCallback(action="unblock", object_id=user.id),
        )
    else:
        builder.button(
            text="Заблокировать",
            callback_data=UsersActionCallback(action="block", object_id=user.id),
        )

    if user.person.approved:
        builder.button(
            text="Снять подтверждение",
            callback_data=UsersActionCallback(action="disapprove", object_id=user.id),
        )
    else:
        builder.button(
            text="Подтвердить",
            callback_data=UsersActionCallback(action="approve", object_id=user.id),
        )

    builder.button(text="Закрыть панель", callback_data="delete_message")
    builder.adjust(1)

    return builder.as_markup()
