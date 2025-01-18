from typing import Awaitable, Callable, Optional, TypeVar

from aiogram.utils.keyboard import InlineKeyboardBuilder

from HPC_bot.models.base_model import BaseDBModel
from HPC_bot.telegram.keyboards.factories import (
    ObjectActionCallback,
    PageCallbackFactory,
)

T = TypeVar("T", bound=BaseDBModel)


async def build_pages_keyboard(
    object_name: str,
    object_action: str,
    loader: Callable[[int, Optional[int]], Awaitable[list[T]]],
    object_callback: ObjectActionCallback,
    formatter: Callable[[T], str] = str,
    limit: int = 10,
    last_id: int = None,
):
    objects = await loader(limit, last_id)

    if not objects:
        return None

    keyboard_type = f"{object_name}_{object_action}"

    builder = InlineKeyboardBuilder()
    for obj in objects:
        builder.button(
            text=formatter(obj),
            callback_data=object_callback(action=object_action, object_id=obj.id),
        )

    if last_id is None:
        builder.button(
            text="|=",
            callback_data=PageCallbackFactory(keyboard=keyboard_type, action="no"),
        )
    else:
        builder.button(
            text="<=(в начало)=|",
            callback_data=PageCallbackFactory(
                keyboard=keyboard_type,
                action="back",
            ),
        )

    if len(objects) == limit:
        builder.button(
            text="|=(следующие)=>",
            callback_data=PageCallbackFactory(
                keyboard=keyboard_type,
                action="forward",
                offset=objects[-1].id,
            ),
        )
    else:
        builder.button(
            text="=|",
            callback_data=PageCallbackFactory(keyboard=keyboard_type, action="no"),
        )

    builder.button(text="Отмена", callback_data="admin_panel_cancel")

    builder.adjust(*[1 for _ in objects], 2, 1)
    return builder.as_markup()
