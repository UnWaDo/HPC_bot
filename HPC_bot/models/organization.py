from typing import List
from peewee import CharField, ForeignKeyField

from .base_model import BaseDBModel


class Organization(BaseDBModel):
    name = CharField(unique=True)
    abbreviation = CharField(15)

    parent = ForeignKeyField(
        model='self',
        backref='children',
        null=True
    )

    @staticmethod
    def find_similar(name: str) -> List['Organization']:
        return Organization.select().where(
            Organization.name ** f'%{name}%' |
            Organization.abbreviation ** f'%{name}%'
        )
