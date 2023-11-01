from typing import Optional, Pattern
from aiogram import Bot
from aiogram.types import User

from ..models import TelegramUser as TgUserModel
from ..utils import config


USER_LINK = (
    '<a href="tg://user?id={tg_id}">{name}</a> '
    '({identifier})'
)


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


def create_user_link(user: User = None, model: TgUserModel = None) -> str:
    if user is None and model is None:
        return '???'

    if user is not None:
        tg_id = user.id
    else:
        tg_id = model.tg_id

    identifiers = []
    if user is not None:
        identifiers.append(f'@{user.username}')
    if model is not None:
        identifiers.append(f'#{model.user.id}')

    identifier = ', '.join(identifiers)

    if model is None:
        name = user.full_name
    else:
        name = f'{model.user.person.first_name} {model.user.person.last_name}'

    name = name.strip()
    if name == '':
        name = '???'

    return USER_LINK.format(tg_id=tg_id, name=name, identifier=identifier)


def get_str_from_re(regex: Pattern, string: str,
                    group: int = 0) -> Optional[str]:
    matched = regex.search(string)
    if matched is None:
        return None

    return matched.group(group)
