import asyncio
from HPC_bot.telegram.db_interactions import register


async def main():
    for i in range(10):
        await register(i, f"Name{i}", f"Surname{i}")


asyncio.run(main())
