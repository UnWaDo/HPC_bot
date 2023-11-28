from typing import Union

from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from HPC_BOT.telegram_bot.admin.callbacks_data import AdminMenuCallbacksData
from HPC_BOT.telegram_bot.admin.filter import IsAdmin
from HPC_BOT.telegram_bot.admin.keyboards.general import generalAdminInlineKeyboard
from HPC_BOT.telegram_bot.admin.settings import adminRouter
from HPC_BOT.telegram_bot.settings import BASE_DIR
from HPC_BOT.telegram_bot.utils.parse_texts import parse_texts

pathToTexts = f"{BASE_DIR}/admin/texts.json"


@adminRouter.message(IsAdmin(), Command("admin"))
@adminRouter.callback_query(IsAdmin(), F.data == AdminMenuCallbacksData.MAIN.value)
async def admin_message_handler(
    event: Union[Message, CallbackQuery], state: FSMContext
) -> None:
    await state.clear()
    event_args = {
        "text": parse_texts(pathToTexts, "admin_menu"),
        "reply_markup": generalAdminInlineKeyboard,
    }
    if isinstance(event, Message):
        await event.answer(**event_args)
    elif isinstance(event, CallbackQuery):
        await event.message.edit_text(**event_args)
