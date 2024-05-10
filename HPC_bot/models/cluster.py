from typing import TYPE_CHECKING, List

from sqlalchemy import String, or_, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import BaseDBModel, sessionmaker

if TYPE_CHECKING:
    from .calculation import Calculation


class Cluster(BaseDBModel):
    __tablename__ = 'cluster'

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(50), unique=True)
    label: Mapped[str] = mapped_column(String(15), unique=True)

    calculations: Mapped[List['Calculation']] = relationship(
        back_populates='cluster')

    @staticmethod
    async def get_all() -> List['Cluster']:
        async with sessionmaker() as session:
            async with session.begin():

                statement = select(Cluster)
                result = await session.execute(statement)

                return result.scalars().all()

    @staticmethod
    async def get_or_create(name: str, label: str):

        async with sessionmaker() as session:
            async with session.begin():
                query = select(Cluster).where(
                    or_(Cluster.label == label, Cluster.name == name))

                result = await session.execute(query)

                cluster = result.scalar_one_or_none()

                if cluster is not None:
                    return cluster

                cluster = Cluster(name=name, label=label)
                session.add(cluster)

                await session.commit()

                return cluster
