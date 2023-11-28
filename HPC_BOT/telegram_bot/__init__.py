from aiogram import Dispatcher
from .admin import adminRouter
from .settings import bot

dp = Dispatcher()
dp.include_router(adminRouter)

__all__ = ["dp", "bot"]