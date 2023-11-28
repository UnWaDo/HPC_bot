from pydantic import BaseModel

from .body import Body
from .status import Status


class APIResponse(BaseModel):
    status: Status
    body: Body

    def __repr__(self):
        return "%s: %s" % (self.status, self.body)

    def __str__(self):
        return self.__repr__()
