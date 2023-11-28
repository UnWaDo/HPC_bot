import asyncio
import logging

from setup import *
from HPC_BOT.telegram_bot import *

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=config.log_level,
    # filename="log.log"
)


async def main():
    await dp.start_polling(
        bot,
    )



if __name__ == "__main__":
    asyncio.run(main())
