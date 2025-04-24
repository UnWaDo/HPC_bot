import asyncio
import os
from pydantic import BaseModel

from .connection import Connection


class RemoteStorage(BaseModel):
    rclone_config: str = None
    remote_name: str
    webdav: Connection
    base_path: str

    async def put(self, local_path: str, remote_path: str = None) -> str:
        if remote_path is None:
            remote_path = os.path.basename(local_path)

        args = ["rclone"]
        if self.rclone_config is not None:
            args.append("--config")
            args.append(self.rclone_config)
        args.extend(
            ["copy", local_path, f"{self.remote_name}:/{self.base_path}/{remote_path}"]
        )

        proc = await asyncio.create_subprocess_exec(*args)

        result = await proc.wait()
        if result != 0:
            raise RuntimeError("Failed to upload to remote")

        return remote_path

    async def get_shared(self, path: str) -> str:
        return await self.webdav.get_shared_link(f"{self.base_path}/{path}")

    async def get(self, remote_path: str, local_path: str) -> str:
        webdav = self.webdav.open_webdav()
        await webdav.download(local_path=local_path, remote_path=remote_path)

        return remote_path
