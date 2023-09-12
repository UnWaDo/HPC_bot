from peewee import PostgresqlDatabase, Model

from ..utils import config


db = PostgresqlDatabase(
    database = config.db.name,
    host = config.db.connection.host,
    port = config.db.connection.port,
    user = config.db.connection.user,
    password = config.db.connection.password.get_secret_value()
)


class BaseDBModel(Model):
    class Meta:
        database = db
