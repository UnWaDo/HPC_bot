from typing import List
from peewee import CharField

from .base_model import BaseDBModel


class Cluster(BaseDBModel):
    name = CharField(50, unique=True)
    label = CharField(15, unique=True)


    @staticmethod
    def get_all() -> List['Cluster']:
        return Cluster.select()
