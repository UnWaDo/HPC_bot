import logging
from configparser import ConfigParser, NoSectionError, SectionProxy
from typing import List

from sqlalchemy.engine.url import URL

from core.models import DatabaseConfig


class Config:
    CONFIG_PATH: str = 'config.ini'

    config = ConfigParser()
    config.read(CONFIG_PATH)

    SECTIONS: List[str] = config.sections()

    @classmethod
    def _getConfigSection(cls, section: str) -> SectionProxy:
        if section in cls.SECTIONS:
            return cls.config[section]
        else:
            logging.exception(f"Секция {section} не найдена в файле {cls.CONFIG_PATH}!")
            raise NoSectionError(section)

    @classmethod
    @property
    def databaseUrl(cls) -> URL:
        SECTION = "Database"

        db_config = cls._getConfigSection(SECTION)
        url = URL.create(
            drivername=f'{db_config.get("dialect", None)}+{db_config.get("driver", None)}',
            username=db_config.get("username", None),
            password=db_config.get("password", None),
            host=db_config.get("host", None),
            port=db_config.get("port", None),
            database=db_config.get("database", None),
            query={}
        )
        return url

    @classmethod
    @property
    def databaseConfig(cls) -> DatabaseConfig:
        SECTION = "Database"
        db_config = cls._getConfigSection(SECTION)

        return DatabaseConfig(
            dialect=db_config.get("dialect", None),
            driver=db_config.get("driver", None),
            username=db_config.get("username", None),
            password=db_config.get("password", None),
            host=db_config.get("host", None),
            port=db_config.get("port", None),
            database=db_config.get("database", None)
        )
