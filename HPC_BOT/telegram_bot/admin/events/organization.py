import os

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    Message,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from HPC_BOT.database_api import Status, Code
from HPC_BOT.telegram_bot.admin.callbacks_data import OrganizationsCallbackData
from HPC_BOT.telegram_bot.admin.filter import IsAdmin
from HPC_BOT.telegram_bot.admin.keyboards.organizations import (
    organizations_menu_keyboard,
    back_to_organizations_menu,
    organization_menu_with_photo_keyboard,
    organization_menu_without_photo_keyboard,
    back_to_organization_menu,
)
from HPC_BOT.telegram_bot.admin.keyboards.general import to_admin_menu
from HPC_BOT.telegram_bot.admin.settings import (
    adminRouter,
    GET_ORGANIZATIONS_COMMAND,
    SUPPORTED_IMAGE_FORMATS,
)
from HPC_BOT.telegram_bot.admin.states import AddOrganizationStates, ManageOrganization
from HPC_BOT.telegram_bot.settings import (
    organizations_api,
    BASE_DIR,
    rSession,
    telegram_user_api,
)
from HPC_BOT.telegram_bot.utils import send_file, create_table, parse_texts
from HPC_BOT.telegram_bot.utils.aiogram_utils import edit_text, not_found_organization
from HPC_BOT.telegram_bot.utils.handle_files import download_file
from HPC_BOT.telegram_bot.utils.upload_photo import upload_photo

pathToTexts = f"{BASE_DIR}/admin/texts.json"


# ORGANIZATIONS MAIN MENU #
@adminRouter.callback_query(IsAdmin(), F.data == OrganizationsCallbackData.MAIN.value)
async def admin_callback_handler(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    await state.clear()
    kwargs = {
        "text": parse_texts(pathToTexts, "organizations_menu"),
        "reply_markup": organizations_menu_keyboard,
    }
    return await edit_text(callback_query, is_delete_photo=True, **kwargs)


# ALL ORGANIZATIONS LIST #
@adminRouter.callback_query(
    IsAdmin(), F.data == OrganizationsCallbackData.ALL_ORGANIZATION_LIST.value
)
async def admin_callback_handler(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    response = await organizations_api.get_all_organizations()
    if response.status == Status.OK:
        organizations = response.body.response_data
        row_list = list(
            map(lambda org: [org.id, org.abbreviate, org.full_name], organizations)
        )
        path = await create_table(
            "Organizations", ["id", "abbreviate", "full name"], row_list
        )
        await send_file(callback_query, path)
    else:
        await callback_query.message.answer(
            text=response.body.code.value, reply_markup=back_to_organizations_menu
        )


# ADD NEW ORGANIZATION #
@adminRouter.callback_query(
    IsAdmin(), F.data == OrganizationsCallbackData.ADD_ORGANIZATION.value
)
async def admin_callback_handler(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    await state.clear()
    await callback_query.message.edit_text(
        text=parse_texts(pathToTexts, "enter_abbreviate"),
        reply_markup=back_to_organizations_menu,
    )
    await state.set_state(AddOrganizationStates.abbreviate)


@adminRouter.message(IsAdmin(), AddOrganizationStates.abbreviate)
async def admin_callback_handler(message: Message, state: FSMContext) -> None:
    abbreviate = message.text
    duplicate = (
        await organizations_api.get_organization_by_abbreviate(abbreviate)
    ).body.model
    if duplicate:
        await message.answer(
            text=parse_texts(pathToTexts, "not_unique_abbreviate"),
            reply_markup=back_to_organizations_menu,
        )
    else:
        await message.answer(
            text=parse_texts(pathToTexts, "enter_full_name"),
            reply_markup=back_to_organizations_menu,
        )
        await state.set_data({"abbreviate": abbreviate})
        await state.set_state(AddOrganizationStates.full_name)


@adminRouter.message(IsAdmin(), AddOrganizationStates.full_name)
async def admin_callback_handler(message: Message, state: FSMContext) -> None:
    full_name = message.text
    data = await state.get_data()
    abbreviate = data.get("abbreviate", None)
    if abbreviate is not None:
        response = await organizations_api.create_organization(abbreviate, full_name)
        if response.status == Status.OK:
            organization = response.body.model
            await message.answer(
                text=parse_texts(pathToTexts, "success_created_organization").format(
                    id=organization.id,
                    abbreviate=organization.abbreviate,
                    full_name=organization.full_name,
                ),
                reply_markup=back_to_organizations_menu,
            )
        if response.status == Status.ERROR:
            if response.body.code == Code.BAD_RESPONSE:
                await message.answer(
                    text=parse_texts(pathToTexts, "organization_bad_response"),
                    reply_markup=back_to_organizations_menu,
                )

    else:
        await message.answer(
            text=parse_texts(pathToTexts, "forget_abbreviate"),
            reply_markup=to_admin_menu,
        )
        await state.clear()


# HANDLE ORGANIZATION #
@adminRouter.callback_query(
    IsAdmin(), F.data == OrganizationsCallbackData.CHOOSE_ORGANIZATION.value
)
async def admin_callback_handler(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    bot_data = await callback_query.bot.get_me()
    await callback_query.message.edit_text(
        text=parse_texts(pathToTexts, "choose_organization_admins").format(
            bot_name=bot_data.username
        ),
        reply_markup=back_to_organizations_menu,
    )


@adminRouter.inline_query(IsAdmin(), F.query.startswith(GET_ORGANIZATIONS_COMMAND))
async def admin_inline_query_handler(
    inline_query: InlineQuery, state: FSMContext
) -> None:
    query = inline_query.query.removeprefix(GET_ORGANIZATIONS_COMMAND + " ")
    if query == "/getorg":
        text = (
            f"Введите запрос после {GET_ORGANIZATIONS_COMMAND} для поиска организации"
        )
        result = [
            InlineQueryResultArticle(
                id="0",
                title="Введите запрос",
                description=text,
                input_message_content=InputTextMessageContent(message_text=text),
            )
        ]
        await inline_query.answer(results=result, is_personal=True, cache_time=1)
        return

    response = await organizations_api.search_organizations(query)
    if response.status == Status.OK:
        organizations = response.body.response_data
        if organizations:
            answer = list()
            for organization in organizations:
                answer.append(
                    InlineQueryResultArticle(
                        id=str(organization.id),
                        title=organization.abbreviate,
                        description=organization.full_name,
                        input_message_content=InputTextMessageContent(
                            message_text=f"#vieworganzation={organization.id}",
                            parse_mode="HTML",
                        ),
                    )
                )
            await inline_query.answer(results=answer, is_personal=True, cache_time=1)


@adminRouter.message(IsAdmin(), F.text.startswith("#vieworganzation"))
async def admin_message_handler(message: Message, state: FSMContext):
    await message.delete()
    organization_id = message.text.split("=")[-1]
    try:
        organization_id = int(organization_id)
    except ValueError:
        pass
    if isinstance(organization_id, int):
        organization_response = await organizations_api.get_organization_by_id(
            organization_id
        )
        if organization_response.status == Status.OK:
            organization = organization_response.body.model
            organization_data = {
                "abbreviate": organization.abbreviate,
                "organization_id": organization.id,
                "full_name": organization.full_name,
                "organization_photo": organization.photo,
            }

            await state.set_state(ManageOrganization.manage)
            await state.set_data(organization_data)
            text = parse_texts(pathToTexts, "organization_view").format(
                **organization_data
            )
            if organization.photo:
                await message.answer_photo(
                    caption=text,
                    reply_markup=organization_menu_with_photo_keyboard,
                    photo=organization.photo,
                )
            else:
                await message.answer(
                    text=text,
                    reply_markup=organization_menu_without_photo_keyboard,
                )


@adminRouter.callback_query(
    IsAdmin(),
    F.data == OrganizationsCallbackData.ADD_PHOTO.value,
)
async def admin_callback_handler(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    data = await state.get_data()
    if data.get("organization_id") is None:
        return await callback_query.answer(
            text=parse_texts(pathToTexts, "not_found_organizations"), show_alert=True
        )
    await callback_query.message.edit_text(
        text=parse_texts(pathToTexts, "add_photo_to_organization").format(
            abbreviate=data.get("abbreviate", None),
            image_formats=", ".join(SUPPORTED_IMAGE_FORMATS),
        ),
        reply_markup=back_to_organization_menu,
    )
    await state.set_state(ManageOrganization.add_photo)


@adminRouter.message(IsAdmin(), ManageOrganization.add_photo, F.document)
async def admin_message_handler(message: Message, state: FSMContext):
    if message.photo:
        return await message.answer(
            text=parse_texts(pathToTexts, "photo_instead_document_error"),
            reply_markup=back_to_organization_menu,
        )

    data = await state.get_data()
    organization_id = data.get("organization_id", None)
    if organization_id is None:
        return not_found_organization(message, pathToTexts, back_to_organization_menu)
    document_format = message.document.file_name.split(".")[-1].lower()
    if document_format in SUPPORTED_IMAGE_FORMATS:
        file_id = message.document.file_id
        file = await download_file(message.bot, file_id, document_format)
        photo_link = await upload_photo(rSession, file)
        response = await organizations_api.add_photo(organization_id, photo_link)
        if response.status == Status.OK:
            data["organization_photo"] = photo_link
            await state.set_data(data)

            await message.answer_photo(
                caption=parse_texts(pathToTexts, "organization_view").format(**data),
                reply_markup=organization_menu_with_photo_keyboard,
                photo=photo_link,
            )
    else:
        await message.answer(
            text=parse_texts(pathToTexts, "document_error"),
            reply_markup=back_to_organization_menu,
        )


@adminRouter.callback_query(
    IsAdmin(),
    F.data == OrganizationsCallbackData.CHANGE_PHOTO.value,
)
async def admin_callback_handler(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    data = await state.get_data()
    if data.get("organization_id", None) is None:
        return not_found_organization(
            callback_query, pathToTexts, back_to_organization_menu
        )
    await callback_query.message.delete()
    await callback_query.message.answer(
        text=parse_texts(pathToTexts, "change_photo_to_organization").format(
            abbreviate=data.get("abbreviate", None),
            image_formats=", ".join(SUPPORTED_IMAGE_FORMATS),
        ),
        reply_markup=back_to_organization_menu,
    )
    await state.set_state(ManageOrganization.change_photo)


@adminRouter.message(IsAdmin(), ManageOrganization.change_photo, F.document)
async def admin_message_handler(message: Message, state: FSMContext):
    if message.photo:
        return await message.answer(
            text=parse_texts(pathToTexts, "photo_instead_document_error"),
            reply_markup=back_to_organization_menu,
        )

    data = await state.get_data()
    organization_id = data.get("organization_id", None)
    if organization_id is None:
        return not_found_organization(message, pathToTexts, back_to_organization_menu)

    document_format = message.document.file_name.split(".")[-1].lower()
    if document_format in SUPPORTED_IMAGE_FORMATS:
        file_id = message.document.file_id
        file = await download_file(message.bot, file_id, document_format)
        photo_link = await upload_photo(rSession, file)
        response = await organizations_api.add_photo(organization_id, photo_link)
        if response.status == Status.OK:
            data["organization_photo"] = photo_link
            await state.set_data(data)

            await message.answer_photo(
                caption=parse_texts(pathToTexts, "organization_view").format(**data),
                reply_markup=organization_menu_with_photo_keyboard,
                photo=photo_link,
            )
    else:
        await message.answer(
            text=parse_texts(pathToTexts, "document_error"),
            reply_markup=back_to_organization_menu,
        )


@adminRouter.callback_query(
    IsAdmin(), F.data == OrganizationsCallbackData.BACK_TO_ORGANIZATION_MENU.value
)
async def admin_callback_handler(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    data = await state.get_data()
    if data.get("organization_id", None) is None:
        bot_data = await callback_query.bot.get_me()
        kwargs = {
            "text": parse_texts(pathToTexts, "choose_organization_admins").format(
                bot_name=bot_data.username
            ),
            "reply_markup": back_to_organizations_menu,
        }
        if callback_query.message.photo:
            await callback_query.message.delete()
            await callback_query.message.answer(**kwargs)
        else:
            await callback_query.message.edit_text(**kwargs)
    else:
        text = parse_texts(pathToTexts, "organization_view").format(**data)
        kwargs = {
            "caption": text,
            "reply_markup": organization_menu_with_photo_keyboard,
            "photo": data.get("photo", None),
        }
        if data.get("photo", None) is None:
            kwargs.pop("photo")
            kwargs["reply_markup"] = organization_menu_without_photo_keyboard
            if callback_query.message.photo:
                await callback_query.message.delete()
                await callback_query.message.answer(**kwargs)
            else:
                await callback_query.message.edit_text(
                    text=text,
                    reply_markup=organization_menu_without_photo_keyboard,
                )
        else:
            if callback_query.message.photo:
                await callback_query.message.edit_caption(**kwargs)
            else:
                await callback_query.message.delete()
            await callback_query.message.answer_photo(**kwargs)


@adminRouter.callback_query(
    IsAdmin(), F.data == OrganizationsCallbackData.CHANGE_ABBREVIATE.value
)
async def admin_callback_handler(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    data = await state.get_data()
    if data.get("organization_id", None) is None:
        return not_found_organization(
            callback_query, pathToTexts, back_to_organization_menu
        )

    kwargs = {
        "text": parse_texts(pathToTexts, "change_abbreviate").format(
            abbreviate=data.get("abbreviate", None)
        ),
        "reply_markup": back_to_organization_menu,
    }
    await state.set_state(ManageOrganization.change_abbreviate)

    if callback_query.message.photo:
        await callback_query.message.delete()
        await callback_query.message.answer(**kwargs)
    else:
        await callback_query.message.edit_text(**kwargs)


@adminRouter.message(IsAdmin(), ManageOrganization.change_abbreviate)
async def admin_message_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    organization_id = data.get("organization_id", None)
    if organization_id is None:
        return not_found_organization(message, pathToTexts, back_to_organization_menu)

    response = await organizations_api.change_abbreviate(organization_id, message.text)
    if response.status == Status.OK:
        data["abbreviate"] = message.text
        await state.set_data(data)
        text = parse_texts(pathToTexts, "organization_view").format(**data)
        photo = data.get("organization_photo", None)
        if photo is None:
            await message.answer(
                text=text, reply_markup=organization_menu_without_photo_keyboard
            )
        else:
            await message.answer_photo(
                photo=photo,
                caption=text,
                reply_markup=organization_menu_with_photo_keyboard,
            )
    else:
        if response.body.code == Code.NOT_UNIQUE_DATA:
            await message.answer(
                text=parse_texts(pathToTexts, "not_unique_abbreviate_on_change"),
                reply_markup=back_to_organization_menu,
            )


@adminRouter.callback_query(
    IsAdmin(), F.data == OrganizationsCallbackData.CHANGE_FULL_NAME.value
)
async def admin_callback_handler(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    data = await state.get_data()
    if data.get("organization_id", None) is None:
        return not_found_organization(
            callback_query, pathToTexts, back_to_organization_menu
        )

    kwargs = {
        "text": parse_texts(pathToTexts, "change_full_name").format(
            abbreviate=data.get("abbreviate", None)
        ),
        "reply_markup": back_to_organization_menu,
    }
    await state.set_state(ManageOrganization.change_full_name)

    if callback_query.message.photo:
        await callback_query.message.delete()
        await callback_query.message.answer(**kwargs)
    else:
        await callback_query.message.edit_text(**kwargs)


@adminRouter.message(IsAdmin(), ManageOrganization.change_full_name)
async def admin_message_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    organization_id = data.get("organization_id", None)
    if organization_id is None:
        return not_found_organization(message, pathToTexts, back_to_organization_menu)
    else:
        response = await organizations_api.change_full_name(
            organization_id, message.text
        )
        if response.status == Status.OK:
            data["full_name"] = message.text
            await state.set_data(data)
            text = parse_texts(pathToTexts, "organization_view").format(**data)
            photo = data.get("organization_photo", None)
            if photo is None:
                await message.answer(
                    text=text, reply_markup=organization_menu_without_photo_keyboard
                )
            else:
                await message.answer_photo(
                    photo=photo,
                    caption=text,
                    reply_markup=organization_menu_with_photo_keyboard,
                )


@adminRouter.callback_query(
    IsAdmin(), F.data == OrganizationsCallbackData.GET_USERS_BY_ORGANIZATION.value
)
async def admin_callback_handler(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    data = await state.get_data()
    organization_id = data.get("organization_id", None)
    if organization_id is None:
        return not_found_organization(
            callback_query, pathToTexts, back_to_organization_menu
        )
    response = await telegram_user_api.get_users_by_organization(organization_id)
    if response.status == Status.OK:
        tg_users_list = response.body.response_data
        if tg_users_list:
            row_list = list()
            for tg_user in tg_users_list:
                user = tg_user.user
                row_list.append(
                    [
                        tg_user.telegram_id,
                        tg_user.telegram_username,
                        user.username,
                        user.first_name,
                    ]
                )
            path = await create_table(
                f'User of {data.get("abbreviate", None)} organization',
                ["telegram id", "telegram username", "username", "first_name"],
                row_list,
            )
            await send_file(callback_query, path)
        else:
            await callback_query.message.answer(
                text=Code.BAD_RESPONSE.value, reply_markup=back_to_organizations_menu
            )
