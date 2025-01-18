from HPC_bot.telegram.db_interactions import get_nonblocked_users
from HPC_bot.telegram.keyboards.factories import UsersActionCallback
from HPC_bot.telegram.keyboards.pages_keyboard import build_pages_keyboard


async def build_block_user_keyboard(
    limit: int = 10,
    last_id: int = None,
):
    return await build_pages_keyboard(
        object_action="block",
        object_name="users",
        object_callback=UsersActionCallback,
        last_id=last_id,
        limit=limit,
        loader=get_nonblocked_users,
    )
