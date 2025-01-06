from typing import Any, Dict, Generic, List, TypeVar

from sqlalchemy import Column, select
from sqlalchemy.ext.asyncio import AsyncSession

from HPC_bot.models.base_model import BaseDBModel

T = TypeVar("T", bound=BaseDBModel)


class BaseDAO(Generic[T]):
    model: type[T]
    default_order_column: Column = None

    def __init_subclass__(cls):
        cls.model = cls.__orig_bases__[0].__args__[0]

    @classmethod
    async def save(cls, session: AsyncSession, **values):
        new_instance = cls.model(**values)

        session.add(new_instance)
        await session.commit()

        return new_instance

    @classmethod
    async def save_many(cls, session: AsyncSession, instances: List[Dict[str, Any]]):
        new_instances = [cls.model(**values) for values in instances]

        session.add_all(new_instances)
        await session.commit()

        return new_instances

    @classmethod
    async def get_by_id(cls, session: AsyncSession, id: int):
        query = select(cls.model).where(cls.model.id == id)

        return await session.scalar(query)

    @classmethod
    async def get_all(cls, session: AsyncSession):
        query = select(cls.model)

        result = await session.scalars(query)
        return result.all()

    @classmethod
    async def update(cls, session: AsyncSession, obj_id: int, **values):
        obj = await cls.get_by_id(session, obj_id)

        for k, v in values.items():
            setattr(obj, k, v)

        await session.commit()
        return obj
