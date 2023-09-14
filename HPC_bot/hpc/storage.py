import os
from pydantic import BaseModel

from .connection import Connection


class RemoteStorage(BaseModel):
    webdav: Connection
    base_path: str

    def put(self, local_path: str, remote_path: str = None) -> str:
        if remote_path is None:
            remote_path = os.path.basename(local_path)

        self.webdav.put_by_webdav(
            local_path,
            f'{self.base_path}/{remote_path}'
        )

        return remote_path

    def get_shared(self, path: str) -> str:
        return self.webdav.get_shared_link(
            f'{self.base_path}/{path}'
        )

    def get(self, remote_path: str, local_path: str) -> str:
        webdav = self.webdav.open_webdav_client()
        webdav.download(local_path=local_path, remote_path=remote_path)

        return remote_path
