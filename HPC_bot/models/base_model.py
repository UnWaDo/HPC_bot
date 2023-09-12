import logging
from peewee import PostgresqlDatabase, Model, SqliteDatabase, MySQLDatabase

from ..hpc import DatabaseTypes
from ..utils import config


parameters = {
    'database': config.db.name,
    'host': config.db.connection.host,
    'port': config.db.connection.port,
    'user': config.db.connection.user,
    'password': config.db.connection.password.get_secret_value()
}

if config.db.db_type == DatabaseTypes.SQLITE:
    logging.warning('DB type is SQLite. Do not use it in production')
    db = SqliteDatabase(config.db.name)
elif config.db.db_type == DatabaseTypes.MYSQL:
    logging.info('DB type is MySQL')
    db = MySQLDatabase(charset='utf8', **parameters)
else:
    if config.db.db_type != DatabaseTypes.POSTGRESQL:
        logging.warning('Unrecognized db type, selecting PostgreSQL')
    else:
        logging.info('DB type is PostgreSQL')
    db = PostgresqlDatabase(**parameters)


class BaseDBModel(Model):
    class Meta:
        database = db
