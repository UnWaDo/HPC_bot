import asyncio

from HPC_BOT.database_api import (
    OrganizationAPI,
    Organization,
)


async def test():
    org = Organization()
    organizations_api = OrganizationAPI()
    async with organizations_api.session_factory.begin() as session:
        print(su((await organizations_api._get_models(Organization, session))[0]))
    #
    # async def create_organization():
    #     result = await organizations_api.create_organization(
    #         abbreviate="ITMO", full_name="ITMO"
    #     )
    #     if result.status == Status.OK:
    #         return result.body.model
    #
    # async def get_organization(_id):
    #     result = await organizations_api.get_organization_by_id(_id)
    #     print(result)
    #     result = await organizations_api.get_organization_by_abbreviate("ITMO")
    #     print(result)
    #
    # async def delete_organization(id_: int):
    #     result = await organizations_api.delete_organization(organization_id=id_)
    #     if result.status == Status.OK:
    #         return result.body.model
    #
    # async def add_photo(photo, org_id):
    #     return await organizations_api.add_photo(org_id, photo)
    #
    # print(await add_photo("vfdevdv", 23))
    # from sqlalchemy import update
    #
    # stmt = update(User)
    # stmt = stmt.values(first_name="user #5")
    # print(stmt.values(last_name="FJE"))
asyncio.run(test())
