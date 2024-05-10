from enum import Enum

from sqlalchemy import Integer, TypeDecorator


class IntEnum(TypeDecorator):
    impl = Integer

    _enumtype: Enum

    def __init__(self, enumtype=None, *args, **kwargs):
        super(IntEnum, self).__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, dialect):
        if isinstance(value, int):
            return value

        return value.value

    def process_result_value(self, value, dialect):
        return self._enumtype(value)
