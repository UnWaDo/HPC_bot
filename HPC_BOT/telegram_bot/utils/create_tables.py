import datetime
from typing import List, Any

import aiofiles
from aiocsv import AsyncWriter

from HPC_BOT.telegram_bot.settings import config


async def create_table(table_name: str, header_list: List[str], row_list: List[List[Any]]) -> str:
    path = f"{config.save_path}{table_name} - {datetime.datetime.now()}.csv"
    async with aiofiles.open(path, mode="w+", encoding="utf-8", newline="") as afp:
        writer = AsyncWriter(afp, dialect="unix")
        await writer.writerow(header_list)
        for row in row_list:
            if len(header_list) == len(row):
                await writer.writerow(row)

    return path


