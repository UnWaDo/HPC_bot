from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from core.api.db_api import BaseAPI
from core.models import User, Organization, Code
from core.models.body import Body
from core.models.response import APIResponse
from core.models.status_codes import Status


class UserAPI(BaseAPI):
    """
    API for interacting with the "users" table,
    inherited from :class: 'models.BaseAPI'
    """

    async def createUser(
        self,
        username: str,
        organization: int | Organization,
        first_name: str = None,
        last_name: str = None,
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
        if type(organization) not in (int, Organization):
            return APIResponse(
                status=Status.ERROR,
                body=Body(code=Code.BAD_PARAMETERS, param="organization_id"),
            )

        organization_id = organization
        if type(organization) == Organization:
            organization_id = organization.id

        async with self.session_factory.begin() as session:
            # Verification of the :param organization
            organization_duplicate = await self._checkDuplicates(
                Organization, session, id=organization_id
            )
            if not organization_duplicate:
                return APIResponse(
                    status=Status.ERROR,
                    body=Body(code=Code.DATA_NOT_FOUND, param="organization"),
                )

            # Validation of the :param username
            user_duplicate = await self._checkDuplicates(
                User, session, username=username
            )
            if user_duplicate:
                return APIResponse(
                    status=Status.ERROR,
                    body=Body(code=Code.NOT_UNIQUE_DATA, param="username"),
                )

            # Create insert statement and execute to database
            insert_stmt = self._createInsertStatement(
                User,
                username=username,
                organization_id=organization_id,
                first_name=first_name,
                last_name=last_name,
            )
            return await self._insertStatement(User, insert_stmt, session)

    async def getUser(self, session: AsyncSession = None, **kwargs) -> Optional[User]:
        """
        Method for obtaining one User based on specified parameters

        :param session: optional, for if you want use already existing connection
        :param kwargs: custom, to filter the response
        :return: :class: 'models.User' if according to the given parameters it finds User, else None
        """
        return await self._getModel(User, session, **kwargs)

    async def getUsers(
        self, session: AsyncSession = None, **kwargs
    ) -> Optional[List[User]]:
        """
        Method for obtaining one User based on specified parameters

        :param session: optional, for if you want use already existing connection
        :param kwargs: custom, to filter the response
        :return: list of :class: 'models.User' if according to the given parameters it finds at least one User, else None
        """
        return await self._getModels(User, session, **kwargs)
