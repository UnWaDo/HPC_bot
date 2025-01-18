from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramMigrateToChat
from aiogram.filters import ExceptionTypeFilter

from HPC_bot.telegram.errors_handling import handle_chat_migration
from HPC_bot.telegram.middlewares.user_authorization import UserAuthorizationMiddleware
from HPC_bot.telegram.routers.admin_router import admin_router
from HPC_bot.telegram.routers.callbacks.callbacks_router import callbacks_router
from HPC_bot.telegram.routers.chat_router import chat_router
from HPC_bot.telegram.routers.non_user_router import non_user_router
from HPC_bot.telegram.routers.user_router import user_router

dispatcher = Dispatcher()
dispatcher.message.outer_middleware(UserAuthorizationMiddleware())
dispatcher.callback_query.outer_middleware(UserAuthorizationMiddleware())
dispatcher.include_router(callbacks_router)
dispatcher.include_router(admin_router)
dispatcher.include_router(user_router)
dispatcher.include_router(non_user_router)
dispatcher.include_router(chat_router)

dispatcher.error.register(
    handle_chat_migration, ExceptionTypeFilter(TelegramMigrateToChat)
)
