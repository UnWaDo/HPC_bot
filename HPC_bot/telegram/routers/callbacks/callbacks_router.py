from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from HPC_bot.telegram.filters.user_access_filter import UserAccessFilter
from HPC_bot.telegram.routers.callbacks.approve_user import (
    approve_users_callback_router,
)
from HPC_bot.telegram.routers.callbacks.block_user import block_users_callback_router
from HPC_bot.telegram.routers.callbacks.search_user import search_users_callback_router
from HPC_bot.telegram.routers.callbacks.unblock_user import (
    unblock_users_callback_router,
)
from HPC_bot.telegram.routers.callbacks.default_router import default_callback_router

callbacks_router = Router()
callbacks_router.include_router(approve_users_callback_router)
callbacks_router.include_router(search_users_callback_router)
callbacks_router.include_router(block_users_callback_router)
callbacks_router.include_router(unblock_users_callback_router)
callbacks_router.include_router(default_callback_router)
