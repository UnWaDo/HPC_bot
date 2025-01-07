from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from HPC_bot.database.calculation_dao import CalculationDAO
from HPC_bot.database.cluster_dao import ClusterDAO
from HPC_bot.database.database import db_connection
from HPC_bot.hpc.cluster import Cluster
from HPC_bot.models.calculation import Calculation, CalculationStatus


@db_connection
async def get_calculations_by_status(status: CalculationStatus, session: AsyncSession):
    return await CalculationDAO.get_by_status(session, status)


@db_connection
async def get_unfinished_calculations(session: AsyncSession):
    return await CalculationDAO.get_unfinished(session)


@db_connection
async def get_finished_calculations(session: AsyncSession):
    return await CalculationDAO.get_finished(session)


@db_connection
async def update_calculations(calculations: List[Calculation], session: AsyncSession):
    for calculation in calculations:
        session.add(calculation)

    await session.commit()


@db_connection
async def update_clusters(clusters: List[Cluster], session: AsyncSession):
    existing_clusters = await ClusterDAO.get_all(session)

    new_clusters = []
    for cluster in clusters:
        if any(c.label == cluster.label for c in existing_clusters):
            continue

        new_clusters.append({"name": cluster.label, "label": cluster.label})

    return await ClusterDAO.save_many(session, new_clusters)
