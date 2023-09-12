from aiogram import Router, F
from aiogram.types import ChatMemberUpdated, Message
from aiogram.filters import ChatMemberUpdatedFilter, JOIN_TRANSITION, LEAVE_TRANSITION, Command

from .utils import log_message, create_user_link
from ..utils import config
from ..models import TelegramUser


chat_router = Router()
chat_router.message.filter(F.chat.type != 'private')


@chat_router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def joined_chat(event: ChatMemberUpdated):
    if event.chat.type == 'private':
        return

    left = False

    if event.from_user.username != config.bot.admin_name[1:]:
        await event.bot.send_message(
            event.chat.id,
            'Только администратор может добавлять бота в беседы'
        )
        await event.bot.leave_chat(event.chat.id)
        left = True

    if left:
        await log_message(
            event.bot,
            text=f'Бота {config.bot.bot_name} попытались добавить в чат {event.chat.full_name}')
        return
    await log_message(
        event.bot,
        text=f'Бот {config.bot.bot_name} добавлен в чат {event.chat.full_name}')


@chat_router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=LEAVE_TRANSITION))
async def left_chat(event: ChatMemberUpdated):
    if event.from_user.id == event.bot.id:
        return

    if event.chat.type == 'private':
        user = event.from_user

        await log_message(
            event.bot,
            text=f'Бот {config.bot.bot_name} заблокирован пользователем '
                 f'{create_user_link(user)}'
        )
        return
    await log_message(
        event.bot,
        text=f'Бот {config.bot.bot_name} удалён из чата {event.chat.full_name}')


@chat_router.message(Command(commands=['access']))
async def register(message: Message):
    user = message.from_user
    tg_user = TelegramUser.authenticate(user.id, True)
    
    if tg_user is not None:
        await message.reply('Вам уже предоставлен доступ')
        return

    tg_user = TelegramUser.register(
        tg_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name if user.last_name is not None else ''
    )
    await message.reply('Доступ предоставлен. Для завершения регистрации '
                  'необходимо обновить Ваши данные '
                  '(отправьте в личные сообщения бота команду /upd)')

    await log_message(
        message.bot,
        f'Новый пользователь {create_user_link(user)}'
    )
