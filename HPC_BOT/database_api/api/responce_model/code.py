from enum import Enum


class Code(Enum):
    SUCCESS: str = "SUCCESS"
    BAD_PARAMETERS: str = "BAD_PARAMETERS"
    DATA_NOT_FOUND: str = "DATA_NOT_FOUND"
    NOT_UNIQUE_DATA: str = "NOT_UNIQUE_DATA"
    BAD_RESPONSE: str = "BAD_RESPONSE"
    ALREADY_EXIST: str = "ALREADY_EXIST"

    def __repr__(self):
        return '%s.%s' % (self.__class__.__name__, self.name)

    def __str__(self):
        return self.__repr__()
