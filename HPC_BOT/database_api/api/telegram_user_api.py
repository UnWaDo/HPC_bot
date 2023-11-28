from typing import List, Optional, Union

from sqlalchemy import select

from HPC_BOT.database_api.models import User, TelegramUser, Organization
from .base_api import BaseAPI
from .responce_model.responce import APIResponse


class TelegramUserAPI(BaseAPI):
    async def _get_from_users(self, **kwargs) -> Optional[List[TelegramUser]]:
        statement = select(TelegramUser).join(User.telegram_user)
        for attribute, value in kwargs.items():
            model_attribute = User.__dict__.get(attribute, None)
            if self._validate_model_attribute(model_attribute, value):
                statement = statement.where(model_attribute == value)
        async with self.session_factory.begin() as session:
            return await self._get_models(User, session, statement=statement)

    async def check_tg_user(self, telegram_id: int | str) -> bool:
        if isinstance(telegram_id, str):
            telegram_id = int(telegram_id)
        async with self.session_factory.begin() as session:
            return await self._check_duplicates(TelegramUser, session, telegram_id=telegram_id)

    @property
    async def admin_users(self) -> List[TelegramUser]:
        return await self._get_from_users(is_admin=True)

    @property
    async def baned_users_list(self) -> List[TelegramUser]:
        return await self._get_from_users(is_banned=True)

    async def create_telegram_user(self, telegram_id: Union[int, str], telegram_username: str, user: Union[int, User]) -> APIResponse:
        if not (isinstance(user, int) or isinstance(user, User)):
            return self.bad_params
        async with self.session_factory.begin() as session:
            if isinstance(user, int):
                user = await self._id_to_model(User, user, session)
            if not user:
                return self.data_not_found
            if isinstance(telegram_id, str):
                telegram_id = int(telegram_id)
            if await self._check_duplicates(TelegramUser, session, telegram_id=telegram_id):
                return self.already_exist

            result = await self._insert_model(TelegramUser, session, telegram_id=telegram_id, telegram_username=telegram_username, user_id=user.id)
            return self._check_result_model(result, TelegramUser)

    async def get_users_by_organization(self, organization: Union[int, "Organization"]) -> APIResponse:
        async with self.session_factory.begin() as session:
            if isinstance(organization, int):
                organization = await self._get_models(
                    Organization, session, one=True, id=organization
                )
                if not isinstance(organization, Organization):
                    return self.bad_response

            users = await self._get_from_users(organization_id=organization.id)
            if users is not None:
                for user in users:
                    if not isinstance(user, TelegramUser):
                        return self.bad_response
                return self.success(response_data=users)

            return self.bad_response