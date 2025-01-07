from typing import Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from HPC_bot.database.base_dao import BaseDAO
from HPC_bot.database.organization_dao import OrganizationDAO
from HPC_bot.models.organization import Organization
from HPC_bot.models.person import Person


class PersonDAO(BaseDAO[Person]):
    @classmethod
    async def update_from_raw_data(
        cls,
        session: AsyncSession,
        obj_id: int,
        first_name: str = None,
        last_name: str = None,
        organization: str = None,
    ):

        data = {}
        result: Tuple[str, str, str] = [None, None, None]

        if first_name is not None:
            first_name = first_name.strip()
        if last_name is not None:
            last_name = last_name.strip()
        if organization is not None:
            organization = organization.strip()

        if first_name is not None and first_name != "":
            data["first_name"] = first_name
            result[0] = first_name

        if last_name is not None and last_name != "":
            data["last_name"] = last_name
            result[1] = last_name

        obj = await cls.get_by_id(session, obj_id)
        if obj is None:
            return None

        if organization is not None and organization != "":
            organizations = await OrganizationDAO.find_similar(session, organization)

            if len(organizations) == 1:
                if (obj.organization is None) or (
                    obj.organization.id != organizations[0].id
                ):
                    data["organization"] = organizations[0]

                result[2] = organizations[0].abbreviation
            else:
                result[2] = ""

        if any(x is not None and x != "" for x in result):
            data["approved"] = False

            await cls.update(session, obj_id, **data)

        return tuple(result)
