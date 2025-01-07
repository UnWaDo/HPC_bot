import logging
from enum import Enum
from typing import Callable, Optional, TypeVar

import yaml
from pydantic import BaseModel, SecretStr, model_validator
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from HPC_bot.hpc.connection import Connection

DB_CONFIG_PATH = "database_config.yml"


class DBConfigError(ValueError):
    pass


class DatabaseTypes(Enum):
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"

    def get_default_driver(self) -> str:
        if self == DatabaseTypes.SQLITE:
            return "aiosqlite"
        elif self == DatabaseTypes.MYSQL:
            return "asyncmy"
        elif self == DatabaseTypes.POSTGRESQL:
            return "asyncpg"

        return None


class DatabaseConfig(BaseModel):
    database_type: DatabaseTypes = DatabaseTypes.SQLITE
    driver: Optional[str] = None
    database_name: str = ":memory:"

    log_level: str = "INFO"

    connection: Optional[Connection] = None

    @model_validator(mode="after")
    def get_driver_from_type(self):

        if self.driver is not None:
            return self

        driver = self.database_type.get_default_driver()
        if driver is not None:
            self.driver = driver
            logging.info(f"Driver {self.driver} is used")
            return self

        raise ValueError(f"Can't assign driver, please provide it in {DB_CONFIG_PATH}")

    @model_validator(mode="after")
    def warn_on_sqlite(self):
        if self.database_type == DatabaseTypes.SQLITE:
            logging.warning("DB type is SQLite. Do not use it in production")

        return self

    @classmethod
    def load_config(cls, path: str) -> "DatabaseConfig":
        with open(path) as config_file:
            connection_config = yaml.safe_load(config_file)

        return cls.model_validate(connection_config)

    @property
    def db_url(self) -> str:
        protocol = f"{self.database_type.value}+{self.driver}"

        auth = ""
        if self.connection is not None:
            conn = self.connection
            auth = f"{conn.user}:{conn.password.get_secret_value()}@{conn.host}"

        return f"{protocol}://{auth}/{self.database_name}"

    @property
    def echo(self) -> bool:
        return logging.getLogger().level <= logging.DEBUG


db_config = None
try:
    db_config = DatabaseConfig.load_config(DB_CONFIG_PATH)

except FileNotFoundError:
    logging.warning(f"No db config file {DB_CONFIG_PATH} found. Using default config")

except yaml.YAMLError:
    raise DBConfigError(f"Invalid config file {DB_CONFIG_PATH}")

finally:
    if db_config is None:
        db_config = DatabaseConfig()

engine = create_async_engine(db_config.db_url, echo=db_config.echo)
sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

RT = TypeVar("RT")  # return type


def db_connection(method: Callable[..., RT]) -> Callable[..., RT]:

    async def wrapper(*args, **kwargs):
        async with sessionmaker() as session:
            try:
                return await method(*args, session=session, **kwargs)

            except Exception as e:
                await session.rollback()
                raise e

    return wrapper
