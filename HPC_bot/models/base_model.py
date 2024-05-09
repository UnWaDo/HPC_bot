import logging

from sqlalchemy.ext.asyncio import (AsyncAttrs, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import DeclarativeBase

from ..hpc import DatabaseTypes
from ..utils import config

if config.db.db_type == DatabaseTypes.SQLITE:
    logging.warning('DB type is SQLite. Do not use it in production')
    driver = 'sqlite+aiosqlite'

elif config.db.db_type == DatabaseTypes.MYSQL:
    logging.info('DB type is MySQL')
    driver = 'mysql+asyncmy'

else:

    if config.db.db_type != DatabaseTypes.POSTGRESQL:
        logging.warning('Unrecognized db type, selecting PostgreSQL')
    else:
        logging.info('DB type is PostgreSQL')

    driver = 'postgresql+asyncpg'

DB_URL = (
    f'{driver}://'
    f'{config.db.connection.user}:{config.db.connection.password.get_secret_value()}@'
    f'{config.db.connection.host}/{config.db.name}')

engine = create_async_engine(DB_URL, echo=True)
sessionmaker = async_sessionmaker(engine, expire_on_commit=False)


class BaseDBModel(AsyncAttrs, DeclarativeBase):
    pass
