from typing import Optional, Pattern
from aiogram import Bot
from aiogram.types import User

from ..models import User as UserModel
from ..utils import config


async def log_message(bot: Bot, text: str, file: str = None):
    if config.bot.log_chat_id is None:
        return

    if file is not None:
        await bot.send_document(
            config.bot.log_chat_id,
            document=file,
            caption=text
        )
    else:
        await bot.send_message(config.bot.log_chat_id, text)


def create_user_link(user: User, model: UserModel = None) -> str:
    identifier = f'@{user.username}' + (
        '' if model is None else f', id {model.id}'
    )

    if model is None:
        name = user.full_name
    else:
        name = f'{model.person.first_name} {model.person.last_name}'

    return (f'<a href="tg://user?id={user.id}">{name}</a> '
            f'({identifier})')


def get_str_from_re(regex: Pattern, string: str,
                    group: int = 0) -> Optional[str]:
    matched = regex.search(string)
    if matched is None:
        return None

    return matched.group(group)
