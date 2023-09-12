from enum import Enum
from pydantic import BaseModel, SecretStr

from .connection import Connection


DB_DEFAULT_NAME = 'hpc_bot.db'


class DatabaseTypes(Enum):
    SQLITE = 'sqlite'
    POSTGRESQL = 'postgresql'
    MYSQL = 'mysql'


class Database(BaseModel):
    name: str = DB_DEFAULT_NAME

    connection: Connection = Connection(
        host='localhost',
        port='5432',
        user='postgres',
        password='postgres'
    )

    db_type: DatabaseTypes = DatabaseTypes.POSTGRESQL
