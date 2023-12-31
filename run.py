import asyncio
import logging
import os
from random import randint

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramMigrateToChat
from aiogram.filters import ExceptionTypeFilter

from HPC_bot.utils import config
from HPC_bot.hpc.manager import update_db, check_updates, upload_to_clusters, start_calculations
from HPC_bot.hpc.manager import load_finished, send_to_cloud
from HPC_bot.telegram.text_router import message_router
from HPC_bot.telegram.chat_router import chat_router
from HPC_bot.telegram.errors_handling import handle_chat_migration
from HPC_bot.telegram.manager import notify_on_finished


async def cluster_updates(bot: Bot):
    while True:
        try:
            await upload_to_clusters()
            await start_calculations()
            await check_updates()
            await load_finished()
            await send_to_cloud()
            await notify_on_finished(bot)
        except asyncio.CancelledError:
            break

        except Exception as e:
            logging.exception(
                'Error while handling updates',
                exc_info=e,
                stack_info=True
            )
        if isinstance(config.fetch_time, int):
            await asyncio.sleep(config.fetch_time)
            continue
        await asyncio.sleep(randint(
            config.fetch_time[0],
            config.fetch_time[1]
        ))


async def main() -> None:
    dp = Dispatcher()
    dp.include_router(message_router)
    dp.include_router(chat_router)

    dp.error.register(
        handle_chat_migration,
        ExceptionTypeFilter([TelegramMigrateToChat])
    )

    bot = Bot(config.bot.token, parse_mode=ParseMode.HTML)

    me = await bot.get_me()
    config.bot.bot_name = me.full_name

    updates = asyncio.create_task(cluster_updates(bot))

    await dp.start_polling(bot, allowed_updates=[
        'message',
        'chat_member',
        'my_chat_member',
    ])
    updates.cancel()
    await updates


if __name__ == "__main__":
    os.makedirs(config.download_path, exist_ok=True)
    update_db()
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info('Bot stopped!')
