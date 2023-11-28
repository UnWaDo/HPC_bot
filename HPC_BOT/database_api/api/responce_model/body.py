from typing import Any, Optional, List

from pydantic import BaseModel, SkipValidation

from .code import Code


class Body(BaseModel):
    class Config:
        validation = False

    code: Code
    model: Any = None
    response_data: Any = None

    def __repr__(self):
        return "%s: model: %s; data: %s" % (self.code, self.model, self.response_data)

    def __str__(self):
        return self.__repr__()