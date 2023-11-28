import os

from aiogram import Bot
from aiogram.enums import ParseMode

from setup import config

from HPC_BOT.database_api import OrganizationAPI, UserAPI, TelegramUserAPI
from HPC_BOT.telegram_bot.utils.async_session import AsyncSession

BASE_DIR = os.path.dirname(__file__)

organizations_api = OrganizationAPI()
user_api = UserAPI()
telegram_user_api = TelegramUserAPI()

rSession = AsyncSession()

bot = Bot(token=config.telegram_bot_token, parse_mode=ParseMode.HTML)