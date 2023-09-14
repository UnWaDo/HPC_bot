from aiogram import Router, F
from aiogram.types import ChatMemberUpdated, Message
from aiogram.filters import ChatMemberUpdatedFilter, Command
from aiogram.filters import JOIN_TRANSITION, LEAVE_TRANSITION

from .utils import log_message, create_user_link
from ..utils import config
from ..models import TelegramUser


chat_router = Router()
chat_router.message.filter(F.chat.type != 'private')


ILLEGAL_ADD = 'Только администратор может добавлять бота в беседы'
ADD_ATTEMPT = 'Бота {bot_name} попытались добавить в чат {chat_name}'
ADDED_TO_CHAT = 'Бот {bot_name} добавлен в чат {chat_name}'
BLOCKED = 'Бот {bot_name} заблокирован пользователем {user}'
DELETED = 'Бот {bot_name} удалён из чата {chat_name}'
ALREADY_GRANTED = 'Вам уже предоставлен доступ'
ACCESS_GRANTED = (
    'Доступ предоставлен. Для завершения регистрации '
    'необходимо обновить Ваши данные '
    '(отправьте в личные сообщения бота команду /upd)'
)
NEW_USER = 'Новый пользователь {user}'


@chat_router.my_chat_member(ChatMemberUpdatedFilter(
    member_status_changed=JOIN_TRANSITION))
async def joined_chat(event: ChatMemberUpdated):
    if event.chat.type == 'private':
        return

    left = False

    if event.from_user.username != config.bot.admin_name[1:]:
        await event.bot.send_message(
            event.chat.id,
            ILLEGAL_ADD
        )
        await event.bot.leave_chat(event.chat.id)
        left = True

    if left:
        await log_message(
            event.bot,
            text=ADD_ATTEMPT.format(
                bot_name=config.bot.bot_name,
                chat_name=event.chat.full_name
            )
        )
        return
    await log_message(
        event.bot,
        text=ADDED_TO_CHAT.format(
            bot_name=config.bot.bot_name,
            chat_name=event.chat.full_name
        )
    )


@chat_router.my_chat_member(ChatMemberUpdatedFilter(
    member_status_changed=LEAVE_TRANSITION))
async def left_chat(event: ChatMemberUpdated):
    if event.from_user.id == event.bot.id:
        return

    if event.chat.type == 'private':
        user = event.from_user

        await log_message(
            event.bot,
            text=BLOCKED.format(
                bot_name=config.bot.bot_name,
                user=create_user_link(user)
            )
        )
        return
    await log_message(
        event.bot,
        text=DELETED.format(
            bot_name=config.bot.bot_name,
            chat_name=event.chat.full_name
        )
    )


@chat_router.message(Command(commands=['access']))
async def register(message: Message):
    user = message.from_user
    tg_user = TelegramUser.authenticate(user.id, True)

    if tg_user is not None:
        await message.reply(ALREADY_GRANTED)
        return

    tg_user = TelegramUser.register(
        tg_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name if user.last_name is not None else ''
    )
    await message.reply(ACCESS_GRANTED)

    await log_message(
        message.bot,
        NEW_USER.format(user=create_user_link(user))
    )
