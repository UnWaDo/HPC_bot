from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class BaseDBModel(AsyncAttrs, DeclarativeBase):
    pass
