from typing import Union

from HPC_BOT.database_api.models import Organization
from .responce_model.body import Body
from .responce_model.code import Code
from .responce_model.responce import APIResponse
from .responce_model.status import Status
from .base_api import BaseAPI


class OrganizationAPI(BaseAPI):
    async def create_organization(
        self, abbreviate: str, full_name: str, photo: str = None
    ) -> APIResponse:
        if not (
            isinstance(abbreviate, str)
            and isinstance(full_name, str)
            and (photo is None or isinstance(photo, str))
        ):
            return self.bad_params
        async with self.session_factory.begin() as session:
            organization_duplicate = await self._check_duplicates(
                Organization, session, abbreviate=abbreviate
            )
            if organization_duplicate:
                return self.not_unique_data("abbreviate")
            return await self._insert_model(Organization, session, abbreviate=abbreviate, full_name=full_name, photo=photo)

    async def delete_organization(
        self, organization_id: int = None, abbreviate: str = None
    ) -> APIResponse:
        if not (isinstance(organization_id, int) or isinstance(abbreviate, str)):
            return self.bad_params

        async with self.session_factory.begin() as session:
            organization = await self._get_models(
                Organization,
                session,
                one=True,
                id=organization_id,
                abbreviate=abbreviate,
            )
            if isinstance(organization, Organization):
                result = await self._delete_models(
                    Organization, session, id=organization.id
                )
                if len(result) > 0 and isinstance(result[0], Organization):
                    return APIResponse(
                        status=Status.OK, body=Body(code=Code.SUCCESS, model=result[0])
                    )
            else:
                return APIResponse(
                    status=Status.ERROR, body=Body(code=Code.DATA_NOT_FOUND)
                )

    async def get_organization_by_id(self, organization_id: int) -> APIResponse:
        if not isinstance(organization_id, int):
            return self.bad_params

        async with self.session_factory.begin() as session:
            organization = await self._get_models(
                Organization, session, one=True, id=organization_id
            )
            return self._check_result_model(organization, Organization)

    async def get_organization_by_abbreviate(self, abbreviate: str) -> APIResponse:
        if not isinstance(abbreviate, str):
            return self.bad_params

        async with self.session_factory.begin() as session:
            organization = await self._get_models(
                Organization, session, one=True, abbreviate=abbreviate
            )
            return self._check_result_model(organization, Organization)

    async def get_all_organizations(self) -> APIResponse:
        async with self.session_factory.begin() as session:
            organizations = await self._get_models(Organization, session)
            for organization in organizations:
                if not isinstance(organization, Organization):
                    return self.bad_response
            return APIResponse(
                status=Status.OK,
                body=Body(code=Code.SUCCESS, response_data=organizations),
            )

    async def search_organizations(self, query: str) -> APIResponse:
        query = query.lower()
        result_list = list()
        async with self.session_factory.begin() as session:
            organizations = await self._get_models(Organization, session)
            for organization in organizations:
                if isinstance(organization, Organization):
                    if query in str(organization.abbreviate.lower()) or query in str(
                        organization.full_name.lower()
                    ):
                        result_list.append(organization)
                else:
                    return self.bad_response

        return APIResponse(
            status=Status.OK, body=Body(code=Code.SUCCESS, response_data=result_list)
        )

    async def add_photo(
        self, organization: Union[int, Organization], photo_link: str
    ) -> APIResponse:
        async with self.session_factory.begin() as session:
            if isinstance(organization, int):
                organization = await self._get_models(Organization, session, one=True, id=organization)
            if organization is None:
                return self.bad_params

            result = await self._update_models(
                Organization, session, {"photo": photo_link}, id=organization.id
            )
            if result is not None:
                return self._check_result_model(result[0], Organization)
            else:
                return self.bad_response

    async def change_abbreviate(
        self, organization: Union[int, Organization], new_abbreviate: str
    ) -> APIResponse:
        async with self.session_factory.begin() as session:
            if await self._check_duplicates(
                Organization, session, abbreviate=new_abbreviate
            ):
                return self.not_unique_data(new_abbreviate)
            if isinstance(organization, int):
                organization = await self._id_to_model(Organization, organization, session)
            if organization is None:
                return self.bad_params

            result = await self._update_models(Organization, session, {"abbreviate": new_abbreviate}, id=organization.id)
            return self._check_result_model(result, Organization)

    async def change_full_name(
        self, organization: Union[int, Organization], new_full_name: str
    ) -> APIResponse:
        async with self.session_factory.begin() as session:
            if isinstance(organization, int):
                organization = await self._id_to_model(Organization, organization, session)
            if organization is None:
                return self.bad_params

            result = await self._update_models(Organization, session, {"full_name": new_full_name}, id=organization.id)
            return self._check_result_model(result, Organization)
