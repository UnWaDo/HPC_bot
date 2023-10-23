from datetime import datetime, timedelta
import os
import re
from aiogram import Router, Bot
from aiogram.types import Message, User as AioUser, Document
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram import F

from .utils import log_message, create_user_link, get_str_from_re
from ..utils import config, get_month_start
from ..models import TelegramUser, UnauthorizedAccessError, Person
from ..models import User as UserModel
from ..models.manager import (get_all_with_calcs, get_tg_user_with_calcs,
                              get_tg_user, search_users)
from ..hpc.manager import create_calculation_path, start_calculation
from ..hpc.manager import select_cluster
from ..models import SubmitType, Calculation
from ..models import CalculationLimitExceeded, BlockedException


message_router = Router()
message_router.message.filter(F.chat.type == 'private')

FIRST_NAME_RE = re.compile(r'имя:? (.+?)(,|$|\n)', re.IGNORECASE)
LAST_NAME_RE = re.compile(r'фамилия:? (.+?)(,|$|\n)', re.IGNORECASE)
ORGANIZATION_RE = re.compile(r'организация:? (.+?)(,|$|\n)', re.IGNORECASE)

FILENAME_RE = re.compile(r'[\w.\-_]+\.[\w]+')


START_MESSAGE = (
    'Приветствуем, {user_name}!\nЭтот бот предназначен для запуска '
    'квантовохимических расчётов. Бот создан <a href="theorchem.ru">'
    'Группой теоретической химии №24 ИОХ РАН</a>, '
    'для получения доступа обратитесь к {admin_name}'
)
HELP_MESSAGE = (
    'Этот бот предназначен для запуска квантовохимических расчётов\n'
    'Бот создан <a href="theorchem.ru">'
    'Группой теоретической химии №24 ИОХ РАН</a>\n\n'
    'Для постановки в очередь отправьте файл с параметрами расчёта '
    'и опционально укажите аргументы '
    '(аргумент {{}} будет заменён на название файла)\n\n'
    'Доступные кластеры и их команды перечислены ниже\n{clusters}'
)
NOT_ALLOWED_RESPONSE = (
    'Вас нет в списке добавленных пользователей, '
    'для получения доступа обратитесь к {admin_name}'
)
UNATHORIZED_LOG = (
    'Несанкционированная попытка доступа '
    'от пользователя {user}'
)
UPDATE_HELP_MESSAGE = (
    'Команда используется для обновления '
    'данных об имени, фамилии и месте работы/учёбы. '
    'Используйте для этого опции имя: *, фамилия: * и '
    'организация: *, разделённые запятыми или переносами строк'
)
UPDATE_ORG_ERROR = (
    'По указанному запросу найдено несколько организаций '
    'или не найдено организаций, '
    'попробуйте указать название более точно\n'
)
UPDATE_EMPTY_ERROR = (
    'Не найдено параметров для обновления. '
    'Отправьте команду /upd без аргументов для справки'
)
UPDATE_ALREADY_APPROVED = (
    'Ваши данные уже подтверждены администратором, '
    'изменение заблокировано'
)
RUN_MESSAGE = (
    'Будет поставлен расчёт при помощи {program}'
)
RUN_LOG_MESSAGE = (
    'Пользователь {user} поставил расчёт с использованием {program}.'
    ' Расчёт будет запущен с командой <code>{command}</code>'
)
RUN_NO_RUNNER_MESSAGE = (
    'Не найдено программ, отвечающих данному расширению. '
    'Укажите команду вручную или измените расширение файла'
)
RUN_NO_PATH_MESSAGE = (
    'Вы не указали файл в качестве аргумента программы.'
    ' Расчёт не будет поставлен (если это было умышленно,'
    ' обратитесь к администратору)'
)
RUN_NO_RUNNER_LOG_MESSAGE = (
    'Пользователь {user} пытался поставить расчёт, '
    'но соответствующая файлу {filename} команда не найдена'
)
RUN_NO_RUNNER_WITH_COMMAND = (
    'Указана некорректная программа или аргументы'
)
RUN_NO_RUNNER_WITH_COMMAND_LOG = (
    'Пользователь {user} попытался поставить расчёт'
    ' с некорректной командой <code>{command}</code>'
    ' и файлом {filename}'
)
RUN_INVALID_FILE = (
    'Файл превышает максимально разрешённый размер'
    ' или содержит запрещённые символы (в названии файла'
    ' могут быть только буквы, цифры и символы ., -, _)'
)
RUN_INVALID_FILE_LOG = (
    'Пользователь {user} пытался поставить расчёт, '
    'с некорректным названием или больше лимита ({limit} Б)'
)
RUN_LIMIT_EXCEEDED = (
    'Ваш лимит расчётов ({limit} в месяц) исчерпан. '
    'Расчёт проигнорирован'
)
RUN_LIMIT_EXCEEDED_LOG = (
    'Лимит расчётов у пользователя {user} ({limit} в месяц) '
    'исчерпан, расчёт проигнорирован'
)
BLOCKED_DENIAL = (
    'Вы были заблокированы, расчёт проигнорирован'
)
BLOCKED_DENIAL_LOG = (
    'Заблокированный пользователь {user} попытался поставить расчёт'
)
NOT_ALLOWED_COMMAND = (
    'Вы не можете использовать эту команду'
)
APPROVE_HELP = (
    'Для использования этой команды укажите id пользователя '
    'после текста команды, пример: /approve 1'
)
APPROVE_OK = (
    'Пользователь подтверждён, лимит увеличен'
)
APPROVE_FAILED = (
    'Данные пользователя уже подтверждены или '
    'такого пользователя не существует'
)
APPROVE_NOTIFY = (
    'Ваши данные подтверждены, количество доступных расчётов '
    'увеличено до {calc_limit} в месяц'
)
APPROVE_LOG = (
    'Данные пользователя {user} подтверждены пользователем {admin}, '
    'количество доступных расчётов увеличено до {calc_limit} в месяц'
)
UNRECOGNIZED_COMMAND = (
    'Запрос не распознан, для получения информации '
    'отправьте /help'
)
BLOCK_HELP = (
    'Для использования этой команды укажите id пользователя '
    'после текста команды, пример: /block 1'
)
BLOCK_OK = 'Пользователь заблокирован'
BLOCK_FAILED = (
    'Пользователь уже заблокирован или '
    'такого пользователя не существует'
)
BLOCK_NOTIFY = (
    'Доступ к расчётным ресурсам заблокирован. '
    'Для повторного получения доступа обратитесь к администратору'
)
BLOCK_LOG = 'Пользователь {user} заблокирован пользователем {admin}'
UNBLOCK_HELP = (
    'Для использования этой команды укажите id пользователя '
    'после текста команды, пример: /unblock 1'
)
UNBLOCK_OK = 'Пользователь разблокирован'
UNBLOCK_FAILED = (
    'Пользователь не заблокирован или '
    'такого пользователя не существует'
)
UNBLOCK_NOTIFY = (
    'Доступ к расчётным ресурсам разблокирован'
)
UNBLOCK_LOG = 'Пользователь {user} разблокирован пользователем {admin}'
LIST_USERS = (
    '<b>Список пользователей</b>\n'
    '<i>Имя</i> - <i>Лимит расчётов</i> - <i>Расчётов за месяц</i>\n'
    '{users}'
)
USER_STATUS = (
    'Пользователь {user} из организации {organization}\n'
    'Месячный лимит расчётов: {limit}, израсходовано {used}'
)
STATUS_HELP = (
    'Команда /status служит для вывода текущего состояния пользователя. '
    'Администратор может использовать команду /status id для получения '
    'данных других пользователей (например, /status 1)'
)
STATUS_NOT_FOUND = 'Пользователь не найден'
SEARCH_USAGE = (
    'Команда /search служит для поиска пользователей по запросам'
    ' Доступна только администраторам.'
    ' Использование: /search last_name, first_name, organization'
    ' Выводит список пользователей, отвечающих запросу,'
    ' чтобы не искать по одному из параметров, оставьте его пустым'
)
SEARCH_USERS = (
    'Количество найденных пользователей: {count}\n{users}'
)
ALTER_LIMIT_USAGE = (
    'Команда /alter_limit служит для изменения лимита отдельного пользователя.'
    ' Доступна только администраторам.'
    ' Использование: /alter_limit user_id new_limit'
)
ALTER_LIMIT_NOTIFY = (
    'Количество доступных расчётов изменено до {limit}'
)
ALTER_LIMIT_LOG = (
    'Лимит расчётов пользователя {user} изменён до {limit}'
    ' пользователем {admin}'
)
COMMAND_ERROR = 'Ошибка при выполнении команды'


async def is_authorized(
    message: Message,
    apply_join: bool = False
) -> TelegramUser:

    try:
        return TelegramUser.authenticate(
            message.from_user.id, apply_join=apply_join)

    except UnauthorizedAccessError:
        pass

    await not_authorized(message.from_user, message.bot)

    return None


async def not_authorized(
    user: AioUser,
    bot: Bot
):

    await bot.send_message(
        chat_id=user.id,
        text=NOT_ALLOWED_RESPONSE.format(
            admin_name=config.bot.admin_name
        )
    )

    await log_message(
        bot,
        UNATHORIZED_LOG.format(
            user=create_user_link(user)
        )
    )


def is_file_valid(document: Document) -> bool:
    if document.file_size > config.max_file_size:
        return False
    if document.file_name is None:
        return False
    if FILENAME_RE.fullmatch(document.file_name) is None:
        return False
    return True


@message_router.message(CommandStart())
async def start_message(message: Message):
    await message.answer(START_MESSAGE.format(
        user_name=message.from_user.full_name,
        admin_name=config.bot.admin_name
    ))


@message_router.message(Command(commands=['help']))
async def help_message(message: Message):
    if await is_authorized(message) is None:
        return

    await message.answer(HELP_MESSAGE.format(
        clusters='\n\n'.join(
            str(cluster) for cluster in config.clusters
        )
    ))


@message_router.message(F.content_type.in_({'document'}))
async def parse_file(message: Message):
    tg_user = await is_authorized(message, apply_join=True)
    if tg_user is None:
        return

    if not is_file_valid(message.document):
        await message.reply(RUN_INVALID_FILE)

        await log_message(message.bot, RUN_INVALID_FILE_LOG.format(
            user=create_user_link(message.from_user),
            limit=config.max_file_size
        ))
        return

    file_id = message.document.file_id

    basename, ext = os.path.splitext(
        os.path.basename(message.document.file_name))

    cluster, runner, args = select_cluster(ext, command=message.caption)

    if runner is None:
        if message.caption is None:
            await message.reply(RUN_NO_RUNNER_MESSAGE)
        else:
            await message.reply(RUN_NO_RUNNER_WITH_COMMAND)

        if message.caption is None:
            await log_message(message.bot, RUN_NO_RUNNER_LOG_MESSAGE.format(
                user=create_user_link(message.from_user),
                filename=message.document.file_name
            ))
        else:
            await log_message(
                message.bot,
                RUN_NO_RUNNER_WITH_COMMAND_LOG.format(
                    user=create_user_link(message.from_user),
                    filename=message.document.file_name,
                    command=message.caption
                )
            )
        return

    if args is not None and '{}' not in args:
        await message.answer(RUN_NO_PATH_MESSAGE)
        return

    try:
        calculation = Calculation.new_calculation(
            name=basename + ext,
            command=runner.create_command(args, filename='{}'),
            user=tg_user.user,
            submit_type=SubmitType.TELEGRAM,
            cluster=cluster
        )
    except CalculationLimitExceeded:
        await message.reply(RUN_LIMIT_EXCEEDED.format(
            limit=tg_user.user.calculation_limit
        ))
        await log_message(message.bot, RUN_LIMIT_EXCEEDED_LOG.format(
            user=create_user_link(message.from_user, tg_user),
            limit=tg_user.user.calculation_limit
        ))
        return
    except BlockedException:
        await message.reply(BLOCKED_DENIAL)
        await log_message(message.bot, BLOCKED_DENIAL_LOG.format(
            user=create_user_link(message.from_user, tg_user),
        ))
        return

    file = await message.bot.get_file(file_id)

    calculation_path = create_calculation_path(calculation)

    await message.bot.download_file(file.file_path, calculation_path)

    await message.reply(RUN_MESSAGE.format(program=runner.program))

    await log_message(
        bot=message.bot,
        text=RUN_LOG_MESSAGE.format(
            user=create_user_link(message.from_user, tg_user),
            program=runner.program,
            command=calculation.command,
        ),
        file=message.document.file_id
    )


@message_router.message(Command(commands=['upd']))
async def update_data(message: Message):
    tg_user = await is_authorized(message, apply_join=True)
    if tg_user is None:
        return

    if message.text.strip().lower() == '/upd':
        await message.answer(UPDATE_HELP_MESSAGE)
        return

    person = tg_user.user.person  # type: Person
    if person.approved:
        await message.answer(UPDATE_ALREADY_APPROVED)
        return

    first_name, last_name, organization = person.update_from_raw_data(
        first_name=get_str_from_re(FIRST_NAME_RE, message.text, 1),
        last_name=get_str_from_re(LAST_NAME_RE, message.text, 1),
        organization=get_str_from_re(ORGANIZATION_RE, message.text, 1),
    )

    response = ''

    if first_name is not None:
        response += (f'Указано имя {first_name}\n')
    if last_name is not None:
        response += (f'Указана фамилия {last_name}\n')
    if organization is not None:
        if organization != '':
            response += (f'Указана организация {organization}\n')
        else:
            response += UPDATE_ORG_ERROR
    if len(response) == 0:
        await message.answer(UPDATE_EMPTY_ERROR)
        return
    await message.answer(response)
    await log_message(
        message.bot,
        f'Пользователь {create_user_link(message.from_user, tg_user)} '
        f'обновил информацию о себе:\n{response}'
    )


@message_router.message(Command(commands=['approve']))
async def approve_data(message: Message, command: CommandObject):
    if message.from_user.username != config.bot.admin_name[1:]:
        await message.answer(NOT_ALLOWED_COMMAND)
        return

    try:
        idx = int(command.args)
    except (ValueError, TypeError):
        await message.answer(APPROVE_HELP)
        return

    user = UserModel.approve(idx)
    if user is None:
        await message.answer(APPROVE_FAILED)
        return

    await message.answer(APPROVE_OK)
    await message.bot.send_message(
        user.tg_user[0].tg_id,
        APPROVE_NOTIFY.format(
            calc_limit=user.calculation_limit
        )
    )
    await log_message(message.bot, APPROVE_LOG.format(
        user=create_user_link(model=user.tg_user[0]),
        admin=create_user_link(message.from_user),
        calc_limit=user.calculation_limit
    ))


@message_router.message(Command(commands=['block']))
async def block_user(message: Message, command: CommandObject):
    if message.from_user.username != config.bot.admin_name[1:]:
        await message.answer(NOT_ALLOWED_COMMAND)
        return

    try:
        idx = int(command.args)
    except (ValueError, TypeError):
        await message.answer(BLOCK_HELP)
        return

    user = UserModel.block(idx)
    if user is None:
        await message.answer(BLOCK_FAILED)
        return

    await message.answer(BLOCK_OK)
    await message.bot.send_message(user.tg_user[0].tg_id, BLOCK_NOTIFY)
    await log_message(message.bot, BLOCK_LOG.format(
        user=create_user_link(model=user.tg_user[0]),
        admin=create_user_link(message.from_user),
    ))


@message_router.message(Command(commands=['unblock']))
async def unblock_user(message: Message, command: CommandObject):
    if message.from_user.username != config.bot.admin_name[1:]:
        await message.answer(NOT_ALLOWED_COMMAND)
        return

    try:
        idx = int(command.args)
    except (ValueError, TypeError):
        await message.answer(UNBLOCK_HELP)
        return

    user = UserModel.unblock(idx)
    if user is None:
        await message.answer(UNBLOCK_FAILED)
        return

    await message.answer(UNBLOCK_OK)
    await message.bot.send_message(user.tg_user[0].tg_id, UNBLOCK_NOTIFY)
    await log_message(message.bot, UNBLOCK_LOG.format(
        user=create_user_link(model=user.tg_user[0]),
        admin=create_user_link(message.from_user),
    ))


@message_router.message(Command(commands=['list']))
async def list_users(message: Message, command: CommandObject):
    if message.from_user.username != config.bot.admin_name[1:]:
        await message.answer(NOT_ALLOWED_COMMAND)
        return

    remove_blocked = True
    if command.args is not None and command.args.strip() == 'all':
        remove_blocked = False

    users = get_all_with_calcs(
        since=get_month_start(),
        remove_blocked=remove_blocked,
    )

    await message.answer(LIST_USERS.format(
        users='\n'.join([
            f'{i + 1}. {create_user_link(model=u)} - '
            f'{u.user.calculation_limit} - {u.num_calc}'
            for i, u in enumerate(
                sorted(users, key=lambda x: x.num_calc, reverse=True)
            )
        ])
    ))


@message_router.message(Command(commands=['status']))
async def user_status(message: Message, command: CommandObject):
    month_ago = get_month_start()

    if command.args is not None:
        if message.from_user.username != config.bot.admin_name[1:]:
            await message.answer(NOT_ALLOWED_COMMAND)
            return
        try:
            idx = int(command.args)
        except (ValueError, TypeError):
            await message.answer(STATUS_HELP)
            return
        user = get_tg_user_with_calcs(
            user_id=idx,
            since=month_ago
        )
        if user is None:
            await message.answer(STATUS_NOT_FOUND)
            return
    else:
        user = get_tg_user_with_calcs(message.from_user.id, since=month_ago)

        if user is None:
            await not_authorized(message.from_user, message.bot)
            return

    org = user.user.person.organization
    if org is None:
        org_name = '(неизвестно)'
    else:
        org_name = org.name

    await message.answer(
        USER_STATUS.format(user=create_user_link(model=user),
                           organization=org_name,
                           limit=user.user.calculation_limit,
                           used=user.num_calc))


@message_router.message(Command(commands=['search']))
async def search_user(message: Message, command: CommandObject):
    if message.from_user.username != config.bot.admin_name[1:]:
        await message.answer(NOT_ALLOWED_COMMAND)
        return
    if command.args is None:
        await message.answer(SEARCH_USAGE)
        return

    args = [a.strip() for a in command.args.split(',')]
    users = search_users(
        last_name=args[0] if args[0] != '' else None,
        first_name=args[1] if len(args) > 1 and args[1] != '' else None,
        organization=args[2] if len(args) > 2 and args[2] != '' else None,
    )
    users_str = []
    for i, user in enumerate(users):
        org = user.user.person.organization
        if org is None:
            org_name = '(неизвестно)'
        else:
            org_name = org.abbreviation

        users_str.append(
            f'{i + 1}. {create_user_link(model=user)} ({org_name})'
        )
    await message.answer(SEARCH_USERS.format(
        count = len(users_str),
        users='\n'.join(users_str)
    ))


@message_router.message(Command(commands=['alter_limit']))
async def alter_limit(message: Message, command: CommandObject):

    if message.from_user.username != config.bot.admin_name[1:]:
        await message.answer(NOT_ALLOWED_COMMAND)
        return
    if command.args is None:
        await message.answer(ALTER_LIMIT_USAGE)
        return

    args = command.args.split()
    if len(args) < 2:
        await message.answer(ALTER_LIMIT_USAGE)
        return

    try:
        idx = int(args[0])
        limit = int(args[1])
    except (ValueError, TypeError):
        await message.answer(ALTER_LIMIT_USAGE)
        return

    user = get_tg_user(user_id=idx)
    if user is None:
        await message.answer(STATUS_NOT_FOUND)
        return

    org = user.user.person.organization
    if org is None:
        org_name = '(неизвестно)'
    else:
        org_name = org.name

    try:
        user.user.calculation_limit = limit
        user.user.save()
    except Exception:
        await message.answer(COMMAND_ERROR)
        return

    await message.answer(ALTER_LIMIT_NOTIFY.format(
        limit=limit
    ))
    await log_message(
        message.bot,
        ALTER_LIMIT_LOG.format(
            user=create_user_link(model=user),
            limit=limit,
            admin=create_user_link(message.from_user)
        )
    )


@message_router.message()
async def default_message(message: Message):
    await message.answer(UNRECOGNIZED_COMMAND)
