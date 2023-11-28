from enum import Enum


class Status(Enum):
    OK: str = "OK"
    ERROR: str = "ERROR"

    def __repr__(self):
        return '%s.%s' % (self.__class__.__name__, self.name)

    def __str__(self):
        return self.__repr__()
