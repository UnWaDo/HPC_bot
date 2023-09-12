import json
import logging
from typing import List, Optional, Union

from pydantic import BaseModel, model_validator

from ..hpc import Cluster, Database, RemoteStorage
from ..telegram import Bot


CONFIG_PATH = 'config.json'


class ConfigParseError(ValueError):
    pass


class Config(BaseModel):
    download_path: str = 'downloads/'
    storage: RemoteStorage

    log_level: Union[int, str] = 'DEBUG'
    log_file: str = None

    db: Database = Database()
    bot: Bot = Bot()

    clusters: List[Cluster] = []


try:
    with open(CONFIG_PATH, 'r') as file:
        config = Config.model_validate_json(''.join(file.readlines()))

except FileNotFoundError:
    config = Config()
    logging.warning('No %s file found, using default config' % CONFIG_PATH)

except json.decoder.JSONDecodeError as e:
    logging.error('Invalid config.json file format', exc_info=e)
    raise ConfigParseError('Invalid config file %s' % CONFIG_PATH)
