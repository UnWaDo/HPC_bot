import datetime
import os
from typing import Union, Optional, BinaryIO

from aiogram import Bot
from aiogram.types import CallbackQuery, Message, FSInputFile

from setup import config

async def send_file(event: Union[CallbackQuery, Message], path_to_file: str) -> None:
    document = FSInputFile(path_to_file)
    if isinstance(event, CallbackQuery):
        await event.message.answer_document(document)
    elif isinstance(event, Message):
        await event.answer_document(document)

    return os.remove(path_to_file)


async def download_file(bot: Bot, file_id: str, file_format: str) -> Optional[BinaryIO]:
    path = f"{config.save_path}Organization_photo - {datetime.datetime.now()}.{file_format}"
    if isinstance(file_id, str) and isinstance(file_format, str):
        await bot.download(
            file=file_id,
            destination=path
        )
        if os.path.exists(path):
            file = open(path, "rb")
            os.remove(path)
            return file
