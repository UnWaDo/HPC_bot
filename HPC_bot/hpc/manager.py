import asyncio
from datetime import datetime
import logging
import os
import re
from random import randint
from typing import List, Tuple, Dict

from .cluster import Cluster
from .runner import Runner
from ..utils import config
from ..models import db, Calculation, CalculationStatus
from ..models import Cluster as ClusterModel


SLURM_ID_RE = re.compile(r'Submitted batch job (\d+)', re.IGNORECASE)

SLURM_RUNNER = Runner(
    program='squeue',
    allowed_args=['-o "%.15i %.5t"'],
    default_args=['-o "%.15i %.5t"']
)


def create_calculation_path(calculation: Calculation) -> str:
    folder_name = os.path.join(
        config.download_path,
        calculation.get_folder_name()
    )
    os.makedirs(folder_name, exist_ok=True)

    return os.path.join(
        folder_name,
        calculation.name
    )


def select_cluster(
    extension: str,
    command: str = None
) -> Tuple[Cluster, Runner, List[str]]:

    clusters = []  # type: List[Tuple[Cluster, Runner]]

    if command is None:
        for cluster in config.clusters:
            runner = cluster.get_runner_by_extension(extension)
            if runner is not None:
                clusters.append((cluster, runner))
    else:
        for cluster in config.clusters:
            runner, _ = cluster.find_suitable_runner(command)
            if runner is not None:
                clusters.append((cluster, runner))

    if len(clusters) == 0:
        return None, None, None

    cluster, runner = clusters[0]

    if command is not None:
        args = runner.split_command(command)
    else:
        args = None

    return cluster, runner, args


def locate_clusters(
    calculations: List[Calculation]
 ) -> Dict[str, List[Calculation]]:
    cluster_labels = set(c.cluster.label for c in calculations)

    return {label: list(
        filter(
            lambda x: x.cluster.label == label,
            calculations
        )
    ) for label in cluster_labels}


async def upload_to_cluster(
    calculation: Calculation,
    cluster: Cluster,
) -> str:
    calculation_path = os.path.join(
        config.download_path,
        calculation.get_folder_name()
    )

    try:
        return cluster.upload_file(
            local_path=calculation_path,
            local_root=config.download_path
        )
    except Exception:
        return None


async def upload_to_clusters():
    calculations = Calculation.get_by_status(CalculationStatus.NOT_STARTED)

    cluster_calc = locate_clusters(calculations)

    updated = []
    for cluster in config.clusters:

        calculations = cluster_calc.get(cluster.label)

        if calculations is None:
            continue

        for calculation in calculations:
            path = await upload_to_cluster(calculation, cluster)

            if path is None:
                calculation.set_status(CalculationStatus.FAILED_TO_UPLOAD)
            else:
                calculation.set_status(CalculationStatus.UPLOADED)
            updated.append(calculation)

    if updated:
        with db.atomic():
            Calculation.bulk_update(
                updated,
                fields=['status']
            )


def start_calculation(
    calculation: Calculation,
    cluster: Cluster,
) -> bool:
    basename = calculation.name
    directory = f'{cluster.upload_path}/{calculation.get_folder_name()}'

    result = cluster.perform_command(
        command=calculation.command,
        filename=basename,
        chdir=directory
    )
    if result is None:
        logging.warning(f'Illegal command {calculation.command}')
        return False

    stdout, stderr = result

    matched = SLURM_ID_RE.search(stdout)
    if matched is None:
        logging.warning(
            'No slurm id returned '
            f'while setting up calculation #{calculation.id} '
            f'({directory}/{basename}). '
            f'Output is {stdout}\nStderr is {stderr}')
        return False

    slurm_id = int(matched.group(1))

    calculation.slurm_id = slurm_id
    return True


async def start_calculations():
    calculations = Calculation.get_by_status(CalculationStatus.UPLOADED)

    cluster_calc = locate_clusters(calculations)

    updated = []
    for cluster in config.clusters:

        calculations = cluster_calc.get(cluster.label)

        if calculations is None:
            continue

        for calculation in calculations:
            started = start_calculation(calculation, cluster)

            if started:
                calculation.set_status(CalculationStatus.PENDING)
                updated.append(started)
            else:
                logging.warning(f'Failed to start calculation {calculation.name}')

    if updated:
        with db.atomic():
            Calculation.bulk_update(
                calculations,
                fields=['status', 'slurm_id']
            )


def update_db():
    clusters = ClusterModel.get_all()

    for cluster in config.clusters:
        if any(c.label == cluster.label for c in clusters):
            continue

        ClusterModel.create(
            name=cluster.label,
            label=cluster.label
        )


async def check_updates():
    calculations = Calculation.get_unfinished()

    cluster_calc = locate_clusters(calculations)

    updated_time = []
    updated_status = []
    for cluster in config.clusters:

        if cluster_calc.get(cluster.label) is None:
            continue

        stdout, stderr = cluster.start_runner(SLURM_RUNNER)
        logging.debug(f'Slurm output is {stdout}\n, stderr is {stderr}')

        slurm_data = [line.split() for line in filter(
            lambda x: x.strip(), stdout.split('\n')[1:]
        )]

        slurm_status = [
            CalculationStatus.from_slurm(status) for _, status in slurm_data
        ]
        slurm_ids = [int(idx) for idx, _ in slurm_data]

        for calc in cluster_calc[cluster.label]:
            if calc.slurm_id is None:
                continue

            try:
                index = slurm_ids.index(calc.slurm_id)
            except ValueError:
                calc.end_datetime = datetime.utcnow()
                calc.set_status(CalculationStatus.FINISHED_OK)
                updated_time.append(calc)
                continue

            if calc.get_status() >= slurm_status[index]:
                continue
            calc.set_status(slurm_status[index])
            updated_status.append(calc)

    if updated_time:
        with db.atomic():
            Calculation.bulk_update(
                updated_time,
                fields=['status', 'end_datetime']
            )
    if updated_status:
        with db.atomic():
            Calculation.bulk_update(
                updated_status,
                fields=['status']
            )


async def load_finished():
    calculations = Calculation.get_by_status(CalculationStatus.FINISHED_OK)

    cluster_calc = locate_clusters(calculations)

    updated = []
    for cluster in config.clusters:
        calcs = cluster_calc.get(cluster.label)

        if calcs is None:
            continue

        folders = [c.get_folder_name() for c in calcs]
        success = cluster.download_dirs(
            folders,
            [config.download_path for f in folders]
        )
        for calc, succ in zip(calcs, success):
            if not succ:
                continue
            calc.set_status(CalculationStatus.LOADED)
            updated.append(calc)

    if len(updated) > 0:
        with db.atomic():
            Calculation.bulk_update(
                updated,
                fields=['status']
            )


async def send_to_cloud():
    calculations = Calculation.get_by_status(CalculationStatus.LOADED)

    cluster_calc = locate_clusters(calculations)

    updated = []
    for cluster in config.clusters:
        calcs = cluster_calc.get(cluster.label)

        if calcs is None:
            continue

        folders = [c.get_folder_name() for c in calcs]
        for fold, calc in zip(folders, calcs):
            try:
                config.storage.put(
                    local_path=os.path.join(
                        config.download_path,
                        fold
                    ),
                    remote_path=fold
                )
            except Exception as e:
                logging.error('Failed to upload to storage', exc_info=e)
                continue
            calc.set_status(CalculationStatus.CLOUDED)
            updated.append(calc)

    if len(updated) > 0:
        with db.atomic():
            Calculation.bulk_update(
                updated,
                fields=['status']
            )
