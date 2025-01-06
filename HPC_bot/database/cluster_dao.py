from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from HPC_bot.database.base_dao import BaseDAO
from HPC_bot.models.cluster import Cluster


class ClusterDAO(BaseDAO[Cluster]):

    @classmethod
    async def get_or_create(cls, session: AsyncSession, name: str, label: str):

        query = select(Cluster).where(or_(Cluster.label == label, Cluster.name == name))

        result = await session.scalars(query)

        cluster = result.one_or_none()
        if cluster is not None:
            return cluster

        cluster = Cluster(name=name, label=label)
        session.add(cluster)

        await session.flush()

        return cluster
