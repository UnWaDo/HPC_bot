from typing import List

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from HPC_bot.database.base_dao import BaseDAO
from HPC_bot.models.organization import Organization


class OrganizationDAO(BaseDAO[Organization]):
    @classmethod
    async def find_similar(
        cls, session: AsyncSession, name: str
    ) -> List["Organization"]:
        statement = select(cls.model).where(
            or_(
                cls.model.name.ilike(f"%{name}%"),
                cls.model.abbreviation.ilike(f"%{name}%"),
            )
        )

        result = await session.scalars(statement)
        return result.all()
