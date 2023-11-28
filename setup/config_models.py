from typing import Union

from pydantic import BaseModel
from sqlalchemy import URL


class ConfigURL(BaseModel):
    drivername: str
    username: str
    password: str
    host: str
    port: int
    database: str


class Config(BaseModel):
    database_url: ConfigURL

    telegram_bot_token: str
    telegram_log_chat_id: int

    download_path: str = "download/"
    save_path: str = "download/"

    log_level: Union[str, int] = "INFO"
    log_file: str = None

    alembic_config_path: str = "alembic.ini"

    @property
    def sqlalchemy_url(self) -> URL:
        return URL.create(**self.database_url.model_dump())
