from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from HPC_BOT.database_api import Status
from HPC_BOT.telegram_bot.admin.callbacks_data import UsersCallbackData
from HPC_BOT.telegram_bot.admin.filter import IsAdmin
from HPC_BOT.telegram_bot.admin.keyboards.users import users_menu_keyboard, back_to_users_menu
from HPC_BOT.telegram_bot.admin.settings import adminRouter
from HPC_BOT.telegram_bot.settings import BASE_DIR, user_api
from HPC_BOT.telegram_bot.utils import parse_texts, create_table, send_file
from HPC_BOT.telegram_bot.utils.aiogram_utils import edit_text

pathToTexts = f"{BASE_DIR}/admin/texts.json"


@adminRouter.callback_query(IsAdmin(), F.data == UsersCallbackData.MAIN.value)
async def admin_callback_handler(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    await state.clear()
    await state.clear()
    kwargs = {
        "text": parse_texts(pathToTexts, "users_menu"),
        "reply_markup": users_menu_keyboard,
    }
    return await edit_text(callback_query, kwargs)


@adminRouter.callback_query(IsAdmin(), F.data == UsersCallbackData.ALL_USERS_LIST.value)
async def admin_callback_handler(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    response = await user_api.get_all_users()
    if response.status == Status.OK:
        users = response.body.response_data
        row_list = list(
            map(lambda user: [user.id, user.username, user.organization.id, user.organization.abbreviate, user.telegram_user.telegram_id, user.first_name, user.last_name, user.is_verified, user.is_admin, user.is_banned], users)
        )
        path = await create_table(
            "Users", ["id", "username", "organization id", "organization abbreviate", "telegram id", "first name", "last name", "is verified", "is admin", "is banned"], row_list
        )
        await send_file(callback_query, path)
    else:
        await callback_query.message.answer(
            text=response.body.code.value, reply_markup=back_to_users_menu
        )
