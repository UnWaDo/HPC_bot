import json
import logging
from typing import List, Tuple, Union

from pydantic import BaseModel, model_validator

from ..hpc import Cluster, Database, RemoteStorage
from ..telegram import Bot


CONFIG_PATH = 'config.json'


class ConfigParseError(ValueError):
    pass


class Config(BaseModel):
    download_path: str = 'downloads/'
    storage: RemoteStorage = None
    fetch_time: Union[int, Tuple[int, int]] = (120, 240)

    log_level: Union[int, str] = 'DEBUG'
    log_file: str = None

    db: Database = Database()
    bot: Bot = Bot()

    clusters: List[Cluster] = []


is_default = True
config = Config()

try:
    with open(CONFIG_PATH, 'r') as file:
        config = Config.model_validate_json(''.join(file.readlines()))
    is_default = False

except FileNotFoundError:
    pass

except json.decoder.JSONDecodeError as e:
    raise ConfigParseError('Invalid config file %s' % CONFIG_PATH)

finally:
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=config.log_level,
        filename=config.log_file
    )
    if is_default:
        logging.warning('No %s file found, using default config' % CONFIG_PATH)