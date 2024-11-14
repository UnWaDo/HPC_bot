import logging
import os
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, model_validator

from .connection import Connection
from .runner import Runner


class Cluster(BaseModel):
    label: str

    connection: Connection
    upload_path: str

    runners: List[Runner] = []

    associations: Dict[str, Runner] = {}

    @model_validator(mode='after')
    def validate_runners(self) -> 'Cluster':
        for runner in self.runners:
            for association in runner.associations:
                if self.associations.get(association) is not None:
                    raise ValueError(
                        'Associations must be unique within the cluster, '
                        f'but {association} occured more than once')
                self.associations[association] = runner
        return self

    def get_runner_by_extension(self, ext: str) -> Optional[Runner]:
        return self.associations.get(ext)

    def find_suitable_runner(self, command: str) -> Tuple[Runner, List[str]]:
        args = None
        for runner in self.runners:
            args = runner.split_command(command, throws=False)
            if args is not None:
                break

        if args is None:
            return None, []
        return runner, args

    async def start_runner(self,
                           runner: Runner,
                           args: List[str] = None,
                           filename: str = None,
                           chdir: str = None) -> Tuple[str, str]:

        return await self.connection.execute_by_ssh(
            ('' if chdir is None else f"cd '{chdir}';") +
            runner.create_command(args, filename))

    async def perform_command(self,
                              command: str,
                              filename: str = None,
                              chdir: str = None) -> Optional[Tuple[str, str]]:
        runner, args = self.find_suitable_runner(command)

        if runner is None:
            return None

        return await self.start_runner(
            runner,
            args,
            filename,
            chdir,
        )

    async def upload_file(self,
                          local_path: str,
                          local_root: str = None,
                          remote_path: str = None) -> str:

        local_path = local_path.replace('\\', '/').replace('//', '/')

        if local_root is not None:
            rel_path = os.path.relpath(local_path, local_root)
        else:
            rel_path = os.path.basename(local_path)

        rel_path = rel_path.replace('\\', '/').replace('//', '/')

        if remote_path is None:
            remote_path = rel_path.replace('\\', '/').replace('//', '/')

        remote_path = f'{self.upload_path}/{rel_path}'

        await self.connection.put_by_sftp(local_path, remote_path)
        return remote_path

    async def download_file(self, remote_path: str, local_path: str) -> str:
        remote_path = f'{self.upload_path}/{remote_path}'

        await self.connection.get_by_sftp(remote_path, local_path)
        return local_path

    async def download_dirs(self, remotes: List[str],
                            locals: List[str]) -> List[bool]:

        success = [False for _ in zip(remotes, locals)]
        remotes = [f'{self.upload_path}/{r}' for r in remotes]

        for i, (r, l) in enumerate(zip(remotes, locals)):
            try:
                await self.connection.get_by_sftp(r, l)
                success[i] = True
            except Exception as e:
                logging.error(f'Failed to download {r} from {self.label}',
                              exc_info=e)

        return success

    def __str__(self) -> str:
        return f'Кластер {self.label}, доступные программы:\n' + \
            '\n'.join(str(runner) for runner in self.runners)
