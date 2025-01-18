from aiogram import F, Router

from HPC_bot.telegram.routers.responses_text import START_MESSAGE, UNRECOGNIZED_COMMAND
from HPC_bot.telegram.routers.user_router import user_router
from HPC_bot.utils import config
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message


non_user_router = Router()
non_user_router.message.filter(
    F.chat.type == "private",
    StateFilter(None),
)


@non_user_router.message(CommandStart())
async def start_message(message: Message):
    await message.answer(
        START_MESSAGE.format(
            user_name=message.from_user.full_name, admin_name=config.bot.admin_name
        )
    )


@user_router.message(Command(commands=["help"]))
async def help_message(message: Message):
    await message.answer(
        START_MESSAGE.format(
            user_name=message.from_user.full_name, admin_name=config.bot.admin_name
        )
    )


@non_user_router.message()
async def default_message(message: Message):
    await message.answer(UNRECOGNIZED_COMMAND)
