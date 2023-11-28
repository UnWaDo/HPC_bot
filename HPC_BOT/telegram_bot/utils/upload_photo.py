import os
from typing import BinaryIO

from HPC_BOT.telegram_bot.utils.async_session import AsyncSession


async def upload_photo(rSession: AsyncSession, photo: BinaryIO) -> str:
    session = await rSession.get_session()
    send_data = {
        "name": "file",
        "value": photo,
    }
    async with session.post("https://telegra.ph/upload", data=send_data, ssl=False) as response:
        img_src = await response.json()

    return "http://telegra.ph" + img_src[0]['src']