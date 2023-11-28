from typing import Optional, Union

from HPC_BOT.database_api.models import User, Organization
from .responce_model.responce import APIResponse
from .base_api import BaseAPI


class UserAPI(BaseAPI):
    """
    API for interacting with the "users" table,
    inherited from :class: 'models.BaseAPI'
    """

    async def create_user(
        self,
        username: str,
        organization: Union[int, Organization],
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> "APIResponse":
        """
        Method for creating a new user in the database

        :param username: each user's :str: 'username' must be unique
        :param organization: accepts either an :int: 'organization_id' or an object of the :class: 'models.Organization'
        :param first_name: optional, first name of the user
        :param last_name: optional, last name of the user
        :return: method returns :class: 'models.APIResponse' with status of the response ond it's data
        """
        # Validation of the :param organization
        if not (isinstance(organization, Organization) or isinstance(organization, int)):
            return self.bad_params

        async with self.session_factory.begin() as session:
            if isinstance(organization, int):
                organization = await self._id_to_model(Organization, organization, session)
                if not isinstance(organization, Organization):
                    return self.bad_params
            # Verification of the :param organization
            if not await self._check_duplicates(
                Organization, session, id=organization.id
            ):
                return self.data_not_found

            # Validation of the :param username
            if await self._check_duplicates(
                User, session, username=username
            ):
                return self.not_unique_data("username")

            # Create insert statement and execute to database
            return await self._insert_model(User, session,  username=username, organization_id=organization.id, first_name=first_name, last_name=last_name)

    async def get_user_by_id(self, user_id: int) -> APIResponse:
        if not isinstance(user_id, int):
            return self.bad_params

        async with self.session_factory.begin() as session:
            user = await self._get_models(
                User, session, one=True, id=user_id, is_active=True
            )
            return self._check_result_model(user, User)

    async def get_user_by_username(self, username: str) -> APIResponse:
        if not isinstance(username, str):
            return self.bad_params

        async with self.session_factory.begin() as session:
            user = await self._get_models(
                User, session, one=True, username=username, is_active=True
            )
            return self._check_result_model(user, User)

    async def get_all_users(self) -> APIResponse:
        async with self.session_factory.begin() as session:
            users = await self._get_models(
                User, session, is_active=True
            )

            for user in users:
                if not isinstance(user, User):
                    return self.bad_response
                return self.success(response_data=users)
            else:
                return self.data_not_found
