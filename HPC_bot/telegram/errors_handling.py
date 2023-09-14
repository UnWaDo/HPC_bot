import logging

from aiogram.types import ErrorEvent
from aiogram.exceptions import TelegramMigrateToChat

from ..utils import config


async def handle_chat_migration(event: ErrorEvent):
    old_id = event.update.message.chat.id
    new_id = event.exception.migrate_to_chat_id

    logging.warning(f'Chat {event.update.message.chat.title} '
                    f'changed id from {old_id} to {new_id}')

    if config.bot.log_chat_id:
        if config.bot.log_chat_id == old_id:
            config.bot.log_chat_id = new_id

        await event.bot.send_message(
            config.bot.log_chat_id,
            f'Чат {event.update.message.chat.title} сменил идентификатор '
            f'с {old_id} на {new_id}. '
            'Не забудьте обновить конфигурационный файл, если это необходимо'
        )
    text = event.update.message.text
    await event.bot.send_message(new_id, text)
