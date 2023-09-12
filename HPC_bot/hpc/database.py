from pydantic import BaseModel, SecretStr

from .connection import Connection


DB_DEFAULT_NAME = 'hpc_bot.db'


class Database(BaseModel):
    name: str = DB_DEFAULT_NAME

    connection: Connection = Connection(
        host='localhost',
        port='5432',
        user='postgres',
        password='postgres'
    )
