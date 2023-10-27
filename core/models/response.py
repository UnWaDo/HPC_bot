from pydantic import BaseModel

from core.models.body import Body
from core.models.status_codes import Status


class APIResponse(BaseModel):
    status: Status
    body: Body

    def __repr__(self):
        return f"{self.status}: {self.body}"

    def __str__(self):
        return self.__repr__()
