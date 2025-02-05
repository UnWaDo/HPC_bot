from aiogram import F, Router
from HPC_bot.models.telegram_user import TelegramUser
from HPC_bot.models.user import AccessLevel, User
from HPC_bot.telegram.db_interactions import (
    alter_limit,
    approve_user,
    block_user,
    get_all_with_calcs,
    get_user_with_calcs,
    search_users,
    unblock_user,
)
from HPC_bot.telegram.filters.user_access_filter import UserAccessFilter
from HPC_bot.telegram.keyboards.admin_panel import (
    ADMIN_KEYBOARD,
)
from HPC_bot.telegram.routers.responses_text import (
    ALTER_LIMIT_LOG,
    ALTER_LIMIT_NOTIFY,
    ALTER_LIMIT_USAGE,
    APPROVE_FAILED,
    APPROVE_HELP,
    APPROVE_LOG,
    APPROVE_NOTIFY,
    APPROVE_OK,
    BLOCK_FAILED,
    BLOCK_HELP,
    BLOCK_LOG,
    BLOCK_NOTIFY,
    BLOCK_OK,
    LIST_USERS,
    NOT_ALLOWED_COMMAND,
    SEARCH_USAGE,
    SEARCH_USERS,
    STATUS_HELP,
    STATUS_NOT_FOUND,
    UNBLOCK_FAILED,
    UNBLOCK_HELP,
    UNBLOCK_LOG,
    UNBLOCK_NOTIFY,
    UNBLOCK_OK,
    USER_STATUS,
)
from HPC_bot.telegram.routers.user_router import not_authorized
from HPC_bot.telegram.utils import create_user_link, log_message
from HPC_bot.utils import config, get_month_start


from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.types import Message

admin_router = Router()
admin_router.message.filter(
    F.chat.type == "private",
    UserAccessFilter("MODERATOR"),
    StateFilter(None),
)


@admin_router.message(Command(commands=["admin"]))
async def admin_panel(message: Message):
    await message.answer("Панель администратора", reply_markup=ADMIN_KEYBOARD)


@admin_router.message(Command(commands=["approve"]))
async def approve_command(message: Message, command: CommandObject):
    if message.from_user.username != config.bot.admin_name[1:]:
        await message.answer(NOT_ALLOWED_COMMAND)
        return

    try:
        idx = int(command.args)
    except (ValueError, TypeError):
        await message.answer(APPROVE_HELP)
        return

    user = await approve_user(idx)
    if user is None:
        await message.answer(APPROVE_FAILED)
        return

    await message.answer(APPROVE_OK)
    await message.bot.send_message(
        user.tg_user.tg_id, APPROVE_NOTIFY.format(calc_limit=user.calculation_limit)
    )
    await log_message(
        message.bot,
        APPROVE_LOG.format(
            user=create_user_link(model=user.tg_user),
            admin=create_user_link(message.from_user),
            calc_limit=user.calculation_limit,
        ),
    )


@admin_router.message(Command(commands=["block"]))
async def block_command(message: Message, command: CommandObject):
    if message.from_user.username != config.bot.admin_name[1:]:
        await message.answer(NOT_ALLOWED_COMMAND)
        return

    try:
        idx = int(command.args)
    except (ValueError, TypeError):
        await message.answer(BLOCK_HELP)
        return

    user = await block_user(idx)
    if user is None:
        await message.answer(BLOCK_FAILED)
        return

    await message.answer(BLOCK_OK)
    await message.bot.send_message(user.tg_user.tg_id, BLOCK_NOTIFY)
    await log_message(
        message.bot,
        BLOCK_LOG.format(
            user=create_user_link(model=user.tg_user),
            admin=create_user_link(message.from_user),
        ),
    )


@admin_router.message(Command(commands=["unblock"]))
async def unblock_command(message: Message, command: CommandObject):
    if message.from_user.username != config.bot.admin_name[1:]:
        await message.answer(NOT_ALLOWED_COMMAND)
        return

    try:
        idx = int(command.args)
    except (ValueError, TypeError):
        await message.answer(UNBLOCK_HELP)
        return

    user = await unblock_user(idx)
    if user is None:
        await message.answer(UNBLOCK_FAILED)
        return

    await message.answer(UNBLOCK_OK)
    await message.bot.send_message(user.tg_user.tg_id, UNBLOCK_NOTIFY)
    await log_message(
        message.bot,
        UNBLOCK_LOG.format(
            user=create_user_link(model=user.tg_user),
            admin=create_user_link(message.from_user),
        ),
    )


@admin_router.message(Command(commands=["search"]))
async def search_command(message: Message, command: CommandObject):
    if message.from_user.username != config.bot.admin_name[1:]:
        await message.answer(NOT_ALLOWED_COMMAND)
        return
    if command.args is None:
        await message.answer(SEARCH_USAGE)
        return

    args = [a.strip() for a in command.args.split(",")]
    users = await search_users(
        last_name=args[0] if args[0] != "" else None,
        first_name=args[1] if len(args) > 1 and args[1] != "" else None,
        organization=args[2] if len(args) > 2 and args[2] != "" else None,
    )
    users_str = []
    for i, user in enumerate(users):
        org = user.person.organization
        if org is None:
            org_name = "(неизвестно)"
        else:
            org_name = org.abbreviation

        users_str.append(f"{i + 1}. {create_user_link(model=user.tg_user)} ({org_name})")
    await message.answer(
        SEARCH_USERS.format(count=len(users_str), users="\n".join(users_str))
    )


@admin_router.message(Command(commands=["alter_limit"]))
async def alter_limit_command(message: Message, command: CommandObject):

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

    user = await alter_limit(user_id=idx, limit=limit)
    if user is None:
        await message.answer(STATUS_NOT_FOUND)
        return

    await message.answer(ALTER_LIMIT_NOTIFY.format(limit=limit))
    await log_message(
        message.bot,
        ALTER_LIMIT_LOG.format(
            user=create_user_link(model=user.tg_user),
            limit=limit,
            admin=create_user_link(message.from_user),
        ),
    )


@admin_router.message(Command(commands=["list"]))
async def list_users(
    message: Message, command: CommandObject, authorized_user: TelegramUser
):
    if message.from_user.username != config.bot.admin_name[1:]:
        await message.answer(NOT_ALLOWED_COMMAND)
        return

    remove_blocked = True
    if command.args is not None and command.args.strip() == "all":
        remove_blocked = False

    users = await get_all_with_calcs(
        since=get_month_start(),
        remove_blocked=remove_blocked,
    )

    await message.answer(
        LIST_USERS.format(
            users="\n".join(
                [
                    f"{i + 1}. {create_user_link(model=u)} - "
                    f"{u.user.calculation_limit} - {u.num_calc}"
                    for i, u in enumerate(
                        sorted(users, key=lambda x: x.num_calc, reverse=True)
                    )
                ]
            )
        )
    )


@admin_router.message(Command(commands=["status"]))
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

        user = await get_user_with_calcs(user_id=idx, since=month_ago)
        if user is None:
            await message.answer(STATUS_NOT_FOUND)
            return
    else:
        user = await get_user_with_calcs(tg_id=message.from_user.id, since=month_ago)

        if user is None:
            await not_authorized(message.from_user, message.bot)
            return

    org = user.user.person.organization
    if org is None:
        org_name = "(неизвестно)"
    else:
        org_name = org.name

    await message.answer(
        USER_STATUS.format(
            user=create_user_link(model=user),
            organization=org_name,
            limit=user.user.calculation_limit,
            used=user.num_calc,
        )
    )
