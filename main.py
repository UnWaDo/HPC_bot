import asyncio
from time import time

from core.api import UserAPI


# print(Config.databaseUrl)
# BaseAPI()
async def main():
    st = time()
    print(
        await UserAPI().createUser(
            username="glori332", organization=3, first_name="stas"
        )
    )
    print(time() - st)


asyncio.run(main())
