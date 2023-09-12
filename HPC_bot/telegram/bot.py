from typing import Union
from pydantic import BaseModel


class Bot(BaseModel):
    token: str = None
    admin_name: str = '@admin'
    log_chat_id: Union[int, str] = None
    log_chat_level: Union[int, str] = 'INFO'

    bot_name: str = None
