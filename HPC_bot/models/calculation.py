from datetime import datetime
import os
from typing import List, Tuple
from peewee import CharField, ForeignKeyField, DateTimeField, IntegerField
from enum import Enum

from .base_model import BaseDBModel
from .cluster import Cluster
from .user import User

from ..hpc import Cluster as ClusterHPC
from ..utils import get_month_start


class CalculationStatus(Enum):
    NOT_STARTED = 0
    UPLOADED = 5
    PENDING = 10
    RUNNING = 50

    FINISHED_OK = 100
    FAILED_TO_UPLOAD = 110

    LOADED = 200
    CLOUDED = 300
    SENDED = 1000

    @staticmethod
    def from_slurm(status: str) -> 'CalculationStatus':
        if status == 'PD':
            return CalculationStatus.PENDING
        if status == 'R':
            return CalculationStatus.RUNNING

        return CalculationStatus.FINISHED_OK

    def __lt__(self, other):
        return self.value < other.value

    def __gt__(self, other):
        return self.value > other.value

    def __ge__(self, other):
        return self.value >= other.value

    def __le__(self, other):
        return self.value <= other.value


class SubmitType(Enum):
    TELEGRAM = 0


class CalculationLimitExceeded(Exception):
    pass


class BlockedException(Exception):
    pass


class Calculation(BaseDBModel):
    name = CharField(50)
    command = CharField(255)

    start_datetime = DateTimeField()
    end_datetime = DateTimeField(null=True)
    slurm_id = IntegerField(null=True)

    status = IntegerField(choices=[(e.value, e.name)
                          for e in CalculationStatus])
    submit_type = IntegerField(choices=[(e.value, e.name) for e in SubmitType])

    user = ForeignKeyField(
        model=User,
        backref='calculations'
    )
    cluster = ForeignKeyField(
        model=Cluster,
        backref='calculations'
    )

    @staticmethod
    def new_calculation(
        name: str,
        command: str,
        user: User,
        submit_type: SubmitType,
        cluster: ClusterHPC
    ) -> 'Calculation':

        if user.blocked:
            raise BlockedException(
                f'User #{user.id} is blocked'
            )
        if len(user.get_calculations(
            get_month_start())
        ) >= user.calculation_limit:

            raise CalculationLimitExceeded(
                f'User #{user.id} exceeded its calculation limit'
            )

        cluster_model, _ = Cluster.get_or_create(
            label=cluster.label,
            defaults={'name': cluster.label}
        )

        return Calculation.create(
            name=name,
            command=command,
            start_datetime=datetime.utcnow(),
            user=user,
            cluster=cluster_model,
            status=CalculationStatus.NOT_STARTED.value,
            submit_type=submit_type.value
        )

    @staticmethod
    def get_all() -> List['Calculation']:
        return Calculation.select()

    @staticmethod
    def get_not_started() -> List['Calculation']:
        return (
            Calculation.select(Calculation, Cluster, User)
            .join(Cluster)
            .switch(Calculation)
            .join(User)
            .where(
                Calculation.status == CalculationStatus.NOT_STARTED.value
            )
        )

    @staticmethod
    def get_unfinished() -> List['Calculation']:
        return (
            Calculation.select(Calculation, Cluster, User)
            .join(Cluster)
            .switch(Calculation)
            .join(User)
            .where(
                Calculation.status < CalculationStatus.FINISHED_OK.value
            )
        )

    @staticmethod
    def get_by_status(status: CalculationStatus) -> List['Calculation']:
        return (
            Calculation.select(Calculation, Cluster, User)
            .join(Cluster)
            .switch(Calculation)
            .join(User)
            .where(
                Calculation.status == status.value
            )
        )

    def get_status(self) -> CalculationStatus:
        return CalculationStatus(self.status)

    def set_status(self, e: CalculationStatus):
        self.status = e.value

    def get_submit_type(self) -> SubmitType:
        return SubmitType(self.status)

    def get_folder_name(self) -> str:
        name, _ = os.path.splitext(self.name)

        return '{timestamp}_{user_id}_{filename}'.format(
            timestamp=int(datetime.timestamp(self.start_datetime)),
            user_id=self.user_id,
            filename=name
        )
