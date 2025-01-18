from HPC_bot.telegram.keyboards.admin_panel import ADMIN_KEYBOARD


from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, InlineKeyboardMarkup


from typing import Awaitable, Callable, Optional


class PageCallbackFactory(CallbackData, prefix="page"):
    keyboard: str
    action: str
    offset: Optional[int] = None


class ObjectActionCallback(CallbackData, prefix=""):
    action: str
    object_id: Optional[int] = None

    def create_keyboard_handlers(
        self,
        router: Router,
        keyboard_creator: Callable[
            [int, Optional[int]], Awaitable[Optional[InlineKeyboardMarkup]]
        ],
        no_options_message: str,
        keyboard_header: str,
        action: Callable[[CallbackQuery, "ObjectActionCallback"], Awaitable[None]],
        previous_markup: InlineKeyboardMarkup = ADMIN_KEYBOARD,
    ):

        async def start_keyboard(callback: CallbackQuery):
            keyboard = await keyboard_creator()

            if keyboard is None:
                if callback.message.text != no_options_message:
                    await callback.message.edit_text(
                        no_options_message, reply_markup=previous_markup
                    )
                return await callback.answer(no_options_message)

            await callback.message.edit_text(
                keyboard_header,
                reply_markup=keyboard,
            )
            await callback.answer()

        async def next_page(
            callback: CallbackQuery, callback_data: PageCallbackFactory
        ):
            keyboard = await keyboard_creator(last_id=callback_data.offset)

            if keyboard is None:
                return await callback.answer(no_options_message)

            await callback.message.edit_reply_markup(reply_markup=keyboard)

        async def first_page(callback: CallbackQuery):
            keyboard = await keyboard_creator()

            if keyboard is None:
                await callback.message.edit_text(
                    no_options_message, reply_markup=previous_markup
                )
                await callback.answer("Больше пользователей нет")
                return

            await callback.message.edit_reply_markup(reply_markup=keyboard)

        keyboard_name = f"{self.__prefix__}_{self.action}"
        router.callback_query.register(start_keyboard, F.data == keyboard_name)
        router.callback_query.register(
            next_page,
            PageCallbackFactory.filter(
                (F.keyboard == keyboard_name) & (F.action == "forward")
            ),
        )
        router.callback_query.register(
            first_page,
            PageCallbackFactory.filter(
                (F.keyboard == keyboard_name) & (F.action == "back")
            ),
        )
        router.callback_query.register(
            action,
            self.filter(F.action == self.action),
        )


class UsersActionCallback(ObjectActionCallback, prefix="users"):
    pass
