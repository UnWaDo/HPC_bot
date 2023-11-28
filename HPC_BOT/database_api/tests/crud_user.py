import asyncio

from HPC_BOT.database_api import OrganizationAPI, Status, TelegramUserAPI, UserAPI


async def test():
    organization_api = OrganizationAPI()
    user_api = UserAPI()
    tg_user_api = TelegramUserAPI()

    async def create_organization(abbreviate, full_name):
        response = await organization_api.create_organization(abbreviate, full_name)
        if response.status == Status.OK:
            return response.body.model

    async def get_organization(_id):
        result_id = await organization_api.get_organization_by_id(_id)
        result = await organization_api.get_organization_by_abbreviate("ITMO")
        return result_id, result

    async def delete_organization(id_: int):
        result = await organization_api.delete_organization(organization_id=id_)
        if result.status == Status.OK:
            return result.body.model

    async def create_user(username, organization):
        response = await user_api.create_user(username, organization)
        if response.status == Status.OK:
            return response.body.model
        else:
            return response

    async def create_tg_user(user, tg_user, tg_id):
        response = await tg_user_api.create_telegram_user(tg_id, tg_user, user)
        if response.status == Status.OK:
            return response.body.model
        else:
            return response

    res = await create_organization("ITMO", "It's more than university")
    print(res)
    user = await create_user("Glori55", res)
    print(user)
    print(await create_tg_user(user, "634141678"))

asyncio.run(test())
