import os
import re
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram import F

from .utils import log_message, create_user_link, get_str_from_re
from ..utils import config
from ..models import TelegramUser, UnauthorizedAccessError, Person
from ..models import User as UserModel
from ..hpc.manager import create_calculation_path, start_calculation
from ..hpc.manager import select_cluster
from ..models import SubmitType, Calculation, CalculationLimitExceeded


message_router = Router()
message_router.message.filter(F.chat.type == 'private')

FIRST_NAME_RE = re.compile(r'имя:? (.+?)(,|$|\n)', re.IGNORECASE)
LAST_NAME_RE = re.compile(r'фамилия:? (.+?)(,|$|\n)', re.IGNORECASE)
ORGANIZATION_RE = re.compile(r'организация:? (.+?)(,|$|\n)', re.IGNORECASE)
ID_RE = re.compile(r'id:? (\d+?)', re.IGNORECASE)


START_MESSAGE = (
    'Приветствуем, {user_name}!\nЭтот бот предназначен для запуска '
    'квантовохимических расчётов. Бот создан <a href="theorchem.ru">'
    'Группой теоретической химии №24 ИОХ РАН</a>, '
    'для получения доступа обратитесь к {admin_name}'
)
HELP_MESSAGE = (
    'Этот бот предназначен для запуска квантовохимических расчётов\n'
    'Бот создан <a href="theorchem.ru">'
    'Группой теоретической химии №24 ИОХ РАН</a>, '
    'для постановки в очередь отправьте файл с параметрами расчёта '
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
    'Пользователь {user} поставил расчёт с использованием {program}'
)
RUN_NO_RUNNER_MESSAGE = (
    'Не найдено программ, отвечающих данному расширению. '
    'Укажите команду вручную или измените расширение файла'
)
RUN_NO_RUNNER_LOG_MESSAGE = (
    'Пользователь {user} пытался поставить расчёт, '
    'но соответствующая файлу {filename} команда не найдена'
)
RUN_LIMIT_EXCEEDED = (
    'Ваш лимит расчётов ({limit} в месяц) исчерпан. '
    'Расчёт проигнорирован'
)
RUN_LIMIT_EXCEEDED_LOG = (
    'Лимит расчётов у пользователя {user} ({limit} в месяц) '
    'исчерпан, расчёт проигнорирован'
)
NOT_ALLOWED_COMMAND = (
    'Вы не можете использовать эту команду'
)
APPROVE_HELP = (
    'Для использования этой команды укажите id пользователя для '
    'подтверждения в формате id: *'
)
APPROVE_OK = (
    'Пользователь подтверждён, лимит увеличен'
)
APPROVE_FAILED = (
    'Данные пользователя уже подтверждены или '
    'такого пользователя не существует'
)
UNREOGNIZED_COMMAND = (
    'Запрос не распознан, для получения информации '
    'отправьте /help'
)


async def is_authorized(
        message: Message,
        apply_join: bool = False
) -> TelegramUser:

    try:
        return TelegramUser.authenticate(
            message.from_user.id, apply_join=apply_join)

    except UnauthorizedAccessError:
        pass

    await message.answer(NOT_ALLOWED_RESPONSE.format(
        admin_name=config.bot.admin_name
    ))

    await log_message(message.bot, UNATHORIZED_LOG.format(
        user=create_user_link(message.from_user)
    ))

    return None


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

    file_id = message.document.file_id
    basename, ext = os.path.splitext(
        os.path.basename(message.document.file_name))

    cluster, runner, args = select_cluster(ext)

    if runner is None:
        await message.reply(RUN_NO_RUNNER_MESSAGE)

        await log_message(message.bot, RUN_NO_RUNNER_LOG_MESSAGE.format(
            user=create_user_link(message.from_user),
            filename=message.document.file_name
        ))
        return

    try:
        calculation = Calculation.new_calculation(
            name=basename + ext,
            user=tg_user.user,
            submit_type=SubmitType.TELEGRAM,
            cluster=cluster
        )
    except CalculationLimitExceeded:
        await message.reply(RUN_LIMIT_EXCEEDED.format(
            limit=tg_user.user.calculation_limit
        ))
        await log_message(message.bot, RUN_LIMIT_EXCEEDED_LOG.format(
            user=create_user_link(message.from_user, tg_user.user),
            limit=tg_user.user.calculation_limit
        ))
        return

    file = await message.bot.get_file(file_id)

    calculation_path = create_calculation_path(calculation)

    await message.bot.download_file(file.file_path, calculation_path)

    start_calculation(
        path=calculation_path,
        calculation=calculation,
        cluster=cluster,
        runner=runner,
        args=args
    )

    await message.reply(RUN_MESSAGE.format(program=runner.program))

    await log_message(
        bot=message.bot,
        text=RUN_LOG_MESSAGE.format(
            user=create_user_link(message.from_user, tg_user.user),
            program=runner.program
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
        f'Пользователь {create_user_link(message.from_user, tg_user.user)} '
        f'обновил информацию о себе:\n{response}'
    )


@message_router.message(Command(commands=['approve']))
async def approve_data(message: Message):
    if message.from_user.username != config.bot.admin_name[1:]:
        await message.answer(NOT_ALLOWED_COMMAND)
        return

    idx = get_str_from_re(ID_RE, message.text, 1)
    if idx is None:
        await message.answer(APPROVE_HELP)
        return

    if UserModel.approve(int(idx)):
        await message.answer(APPROVE_OK)
    else:
        await message.answer(APPROVE_FAILED)


@message_router.message()
async def default_message(message: Message):
    await message.answer(UNREOGNIZED_COMMAND)
