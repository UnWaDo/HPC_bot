from aiogram import F, Router
from aiogram.types import CallbackQuery

from HPC_bot.telegram.keyboards.admin_panel import ADMIN_KEYBOARD
from HPC_bot.telegram.keyboards.factories import PageCallbackFactory


default_callback_router = Router()


@default_callback_router.callback_query(F.data == "admin_panel_cancel")
async def cancel_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        "Панель администратора", reply_markup=ADMIN_KEYBOARD
    )
    await callback.answer()


@default_callback_router.callback_query(F.data == "admin_panel_close")
async def close_panel_callback(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()


@default_callback_router.callback_query(PageCallbackFactory.filter(F.action == "no"))
async def page_no_change_callback(callback: CallbackQuery):
    await callback.answer()


@default_callback_router.callback_query()
async def default_callback(callback: CallbackQuery):
    await callback.answer(
        "Если вы видите это сообщение, то скорее всего эта функция пока в разработке"
    )
