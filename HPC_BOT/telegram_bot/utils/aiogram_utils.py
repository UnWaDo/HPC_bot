from typing import Union

from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup

from HPC_BOT.telegram_bot.utils import parse_texts


def _validate_event(event: Union[CallbackQuery, Message]) -> Message:
    if isinstance(event, CallbackQuery):
        return event.message
    elif isinstance(event, Message):
        return event
    else:
        raise TypeError(
            'Parameter event must be "aiogram.types.CallbackQuery" or "aiogram.types.Message" type'
        )


async def edit_text(event: Union[CallbackQuery, Message], kwargs: dict) -> None:
    message = _validate_event(event)

    if message.photo:
        kwargs["caption"] = kwargs.pop("text")
        return message.edit_caption(**kwargs)

    return message.edit_text(**kwargs)


def not_found_organization(
    event: Union[CallbackQuery, Message],
    pathToTexts,
    reply_markup: InlineKeyboardMarkup = None,
):
    text = parse_texts(pathToTexts, "not_found_organizations")
    if isinstance(event, CallbackQuery):
        return event.answer(text=text, show_alert=True)
    elif isinstance(event, Message):
        return event.answer(text=text, reply_markup=reply_markup)
