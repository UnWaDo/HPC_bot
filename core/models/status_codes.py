from enum import Enum, auto


class Status(Enum):
    OK = auto()
    ERROR = auto()

    def __repr__(self):
        return f"{self.name}"

    def __str__(self):
        return self.__repr__()


class Code(Enum):
    SUCCESS_CREATED = auto()
    BAD_PARAMETERS = auto()
    DATA_NOT_FOUND = auto()
    NOT_UNIQUE_DATA = auto()
    BAD_RESPONSE = auto()
    ALREADY_EXIST = auto()

    def __repr__(self):
        return f"{self.name}"

    def __str__(self):
        return self.__repr__()
