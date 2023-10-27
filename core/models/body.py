from pydantic import BaseModel

from . import Code


class Body(BaseModel):
    code: Code
    param: str = ""

    def __repr__(self):
        return f"code={self.code}; param={self.param}"

    def __str__(self):
        return self.__repr__()
