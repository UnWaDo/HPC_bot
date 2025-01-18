import os
import re
from aiogram import Router, Bot
from aiogram.types import Message, User as AioUser, Document
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram import F

from HPC_bot.models.user import AccessLevel, User
from HPC_bot.telegram.db_interactions import (
    authorize,
    get_user_with_calcs,
    new_calculation,
    update_person,
)

from HPC_bot.telegram.filters.user_access_filter import UserAccessFilter
from HPC_bot.telegram.routers.responses_text import (
    BLOCKED_DENIAL,
    BLOCKED_DENIAL_LOG,
    HELP_MESSAGE,
    NOT_ALLOWED_RESPONSE,
    RUN_INVALID_FILE,
    RUN_INVALID_FILE_LOG,
    RUN_LIMIT_EXCEEDED,
    RUN_LIMIT_EXCEEDED_LOG,
    RUN_LOG_MESSAGE,
    RUN_MESSAGE,
    RUN_NO_PATH_MESSAGE,
    RUN_NO_RUNNER_LOG_MESSAGE,
    RUN_NO_RUNNER_MESSAGE,
    RUN_NO_RUNNER_WITH_COMMAND,
    RUN_NO_RUNNER_WITH_COMMAND_LOG,
    UNATHORIZED_LOG,
    UPDATE_ALREADY_APPROVED,
    UPDATE_EMPTY_ERROR,
    UPDATE_HELP_MESSAGE,
    UPDATE_ORG_ERROR,
    USER_STATUS,
)
from HPC_bot.telegram.utils import (
    format_organization,
    log_message,
    create_user_link,
    get_str_from_re,
)
from HPC_bot.utils import config, get_month_start
from HPC_bot.models import TelegramUser, Person
from HPC_bot.hpc.manager import create_calculation_path
from HPC_bot.hpc.manager import select_cluster
from HPC_bot.models import CalculationLimitExceeded, BlockedException

user_router = Router()
user_router.message.filter(
    F.chat.type == "private",
    UserAccessFilter(AccessLevel.NEWLY_REGISTERED),
    StateFilter(None),
)

FIRST_NAME_RE = re.compile(r"имя:? (.+?)(,|$|\n)", re.IGNORECASE)
LAST_NAME_RE = re.compile(r"фамилия:? (.+?)(,|$|\n)", re.IGNORECASE)
ORGANIZATION_RE = re.compile(r"организация:? (.+?)(,|$|\n)", re.IGNORECASE)

FILENAME_RE = re.compile(r"[\w.\-_]+\.[\w]+")


async def is_authorized(message: Message) -> TelegramUser:

    tg_user = await authorize(message.from_user.id)

    if tg_user is not None:
        return tg_user

    await not_authorized(message.from_user, message.bot)

    return None


async def not_authorized(user: AioUser, bot: Bot):

    await bot.send_message(
        chat_id=user.id,
        text=NOT_ALLOWED_RESPONSE.format(admin_name=config.bot.admin_name),
    )

    await log_message(bot, UNATHORIZED_LOG.format(user=create_user_link(user)))


def is_file_valid(document: Document) -> bool:
    if document.file_size > config.max_file_size:
        return False
    if document.file_name is None:
        return False
    if len(document.file_name) > 50:
        return False
    if FILENAME_RE.fullmatch(document.file_name) is None:
        return False
    return True


@user_router.message(Command(commands=["help"]))
async def help_message(message: Message):
    await message.answer(
        HELP_MESSAGE.format(
            admin_name=config.bot.admin_name,
            clusters="\n\n".join(str(cluster) for cluster in config.clusters),
        )
    )


@user_router.message(F.content_type.in_({"document"}))
async def parse_file(message: Message, authorized_user: TelegramUser):
    if not is_file_valid(message.document):
        await message.reply(RUN_INVALID_FILE)

        await log_message(
            message.bot,
            RUN_INVALID_FILE_LOG.format(
                user=create_user_link(message.from_user), limit=config.max_file_size
            ),
        )
        return

    file_id = message.document.file_id

    basename, ext = os.path.splitext(os.path.basename(message.document.file_name))

    cluster, runner, args = select_cluster(ext, command=message.caption)

    if runner is None:
        if message.caption is None:
            await message.reply(RUN_NO_RUNNER_MESSAGE)
        else:
            await message.reply(RUN_NO_RUNNER_WITH_COMMAND)

        if message.caption is None:
            await log_message(
                message.bot,
                RUN_NO_RUNNER_LOG_MESSAGE.format(
                    user=create_user_link(message.from_user),
                    filename=message.document.file_name,
                ),
            )
        else:
            await log_message(
                message.bot,
                RUN_NO_RUNNER_WITH_COMMAND_LOG.format(
                    user=create_user_link(message.from_user),
                    filename=message.document.file_name,
                    command=message.caption,
                ),
            )
        return

    if args is not None and "{}" not in args:
        await message.answer(RUN_NO_PATH_MESSAGE)
        return

    try:
        calculation = await new_calculation(
            name=basename + ext,
            command=runner.create_command(args, filename="{}"),
            user=authorized_user.user,
            cluster=cluster,
        )

    except CalculationLimitExceeded:

        await message.reply(
            RUN_LIMIT_EXCEEDED.format(limit=authorized_user.user.calculation_limit)
        )

        await log_message(
            message.bot,
            RUN_LIMIT_EXCEEDED_LOG.format(
                user=create_user_link(message.from_user, authorized_user),
                limit=authorized_user.user.calculation_limit,
            ),
        )

        return

    except BlockedException:

        await message.reply(BLOCKED_DENIAL)
        await log_message(
            message.bot,
            BLOCKED_DENIAL_LOG.format(
                user=create_user_link(message.from_user, authorized_user),
            ),
        )
        return

    file = await message.bot.get_file(file_id)

    calculation_path = create_calculation_path(calculation)

    await message.bot.download_file(file.file_path, calculation_path)

    await message.reply(RUN_MESSAGE.format(program=runner.program))

    await log_message(
        bot=message.bot,
        text=RUN_LOG_MESSAGE.format(
            user=create_user_link(message.from_user, authorized_user),
            program=runner.program,
            command=calculation.command,
        ),
        file=message.document.file_id,
    )


@user_router.message(Command(commands=["upd"]))
async def update_data(message: Message, authorized_user: TelegramUser):
    if message.text.strip().lower() == "/upd":
        await message.answer(UPDATE_HELP_MESSAGE)
        return

    person: Person = authorized_user.user.person
    if person.approved:
        await message.answer(UPDATE_ALREADY_APPROVED)
        return

    first_name, last_name, organization = await update_person(
        person_id=person.id,
        first_name=get_str_from_re(FIRST_NAME_RE, message.text, 1),
        last_name=get_str_from_re(LAST_NAME_RE, message.text, 1),
        organization=get_str_from_re(ORGANIZATION_RE, message.text, 1),
    )

    response = ""

    if first_name is not None:
        response += f"Указано имя {first_name}\n"

    if last_name is not None:
        response += f"Указана фамилия {last_name}\n"

    if organization is not None:
        if organization != "":
            response += f"Указана организация {organization}\n"

        else:
            response += UPDATE_ORG_ERROR

    if len(response) == 0:
        await message.answer(UPDATE_EMPTY_ERROR)
        return

    await message.answer(response)
    await log_message(
        message.bot,
        f"Пользователь {create_user_link(message.from_user, authorized_user)} "
        f"обновил информацию о себе:\n{response}",
    )


@user_router.message(Command(commands=["status"]))
async def user_status(message: Message, command: CommandObject):
    month_ago = get_month_start()

    tg_user = await get_user_with_calcs(tg_id=message.from_user.id, since=month_ago)

    if tg_user is None:
        await not_authorized(message.from_user, message.bot)
        return

    await message.answer(
        USER_STATUS.format(
            user=create_user_link(model=tg_user),
            organization=format_organization(tg_user.user.person.organization),
            limit=tg_user.user.calculation_limit,
            used=tg_user.num_calc,
        )
    )
