from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from core.api.db_api import BaseAPI
from core.models import Organization
from core.models.body import Body
from core.models.response import APIResponse
from core.models.status_codes import Status, Code


class OrganizationAPI(BaseAPI):
    async def createOrganization(self, abbreviate: str, full_name: str) -> Organization:
        async with self.session_factory.begin() as session:
            organization_duplicate = await self._checkDuplicates(
                Organization, session, abbreviate=abbreviate
            )
            if organization_duplicate:
                return APIResponse(
                    status=Status.ERROR,
                    body=Body(code=Code.NOT_UNIQUE_DATA, param="abbreviate"),
                )

            insert_stmt = self._createInsertStatement(
                Organization, abbreviate=abbreviate, full_name=full_name
            )
            return await self._insertStatement(Organization, insert_stmt, session)

    async def getOrganization(
        self, session: AsyncSession = None, **kwargs
    ) -> Optional[Organization]:
        return await self._getModel(Organization, session, **kwargs)

    async def getOrganizations(
        self, session: AsyncSession = None, **kwargs
    ) -> Optional[List[Organization]]:
        return await self._getModels(Organization, session, **kwargs)
