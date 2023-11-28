from enum import Enum


class Method(Enum):
    INSERT: str = "insert"
    SELECT: str = "select"
    UPDATE: str = "update"
    DELETE: str = "delete"
