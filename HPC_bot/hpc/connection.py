import logging
import os
import re
from typing import Dict, List, Optional, Tuple, Pattern
from xml.etree import ElementTree

import aiodav
import aiohttp
import asyncssh
import asyncssh.misc
from pydantic import BaseModel, Field, SecretStr

import yaml

class ConnectionConfig(BaseModel):
    extensions_whitelist: List[str] = ['.out', '.log', '.err']
    files_whitelist: List[str] = []
    filtered_extensions: List[Pattern] = [r'\.tmp', r'\.tmp\..*']

with open('connection_config.yml') as config_file:
    connection_config = yaml.safe_load(config_file)

config = ConnectionConfig.model_validate(connection_config)

class Connection(BaseModel):

    class Config:
        arbitrary_types_allowed = True

    host: str = 'localhost'
    port: int = Field(ge=1)

    user: str

    password: Optional[SecretStr] = None
    key_path: Optional[str] = None

    ssh_client: Optional[asyncssh.SSHClientConnection] = None
    sftp_client: Optional[asyncssh.SFTPClient] = None
    webdav_client: Optional[aiodav.Client] = None

    async def open_ssh(self) -> asyncssh.SSHClientConnection:
        if self.ssh_client is not None:
            self.ssh_client.close()

            await self.ssh_client.wait_closed()

        options = dict(username=self.user, port=self.port)

        if self.key_path:
            options['client_keys'] = [self.key_path]

        else:
            options['password'] = self.password.get_secret_value()

        try:
            self.ssh_client = await asyncssh.connect(self.host,
                                                     **options,
                                                     known_hosts=None)

        except (asyncssh.ChannelOpenError, asyncssh.TimeoutError) as e:

            logging.error('Connection error for {user}@{host}'.format(
                user=self.user, host=self.host),
                          exc_info=e,
                          stack_info=True)
            raise ConnectionError('Failed to connect to server')

        return self.ssh_client

    async def open_sftp(self) -> asyncssh.SFTPClient:
        if self.sftp_client is not None:
            self.sftp_client.exit()

            await self.sftp_client.wait_closed()

        ssh = await self.get_ssh_client()
        self.sftp_client = await ssh.start_sftp_client()

        return self.sftp_client

    def open_webdav(self) -> aiodav.Client:
        if self.key_path:
            password = None
            key = self.key_path
        else:
            password = self.password.get_secret_value()
            key = None

        options = {
            'hostname': (f'{self.host}/remote.php'
                         f'/dav/files/{self.user}'),
            'login': self.user,
            'password': password,
            'token': key
        }
        return aiodav.Client(**options)

    async def is_ssh_active(self) -> bool:
        if self.ssh_client is None:
            return False

        try:
            await self.ssh_client.run('pwd')

        except (asyncssh.ProcessError, asyncssh.misc.ChannelOpenError) as e:
            return False

        return True

    async def get_ssh_client(self) -> asyncssh.SSHClientConnection:
        if await self.is_ssh_active():

            return self.ssh_client

        return await self.open_ssh()

    async def get_sftp_client(self) -> asyncssh.SFTPClient:
        if self.sftp_client is None or not (await self.is_ssh_active()):
            return await self.open_sftp()

        try:
            await self.sftp_client.stat('.')
        except asyncssh.SFTPError:
            return await self.open_sftp()

        return self.sftp_client

    def get_webdav_client(self) -> aiodav.Client:
        if self.webdav_client is None:
            return self.open_webdav()

        return self.webdav_client

    async def execute_by_ssh(self, command: str) -> Tuple[str, str]:
        ssh = await self.get_ssh_client()

        result = await ssh.run(command)

        logging.debug(f'Executed command {command} at '
                      f'{self.user}@{self.host}:{self.port}')

        return result.stdout, result.stderr

    async def get_by_sftp(self,
                          remote_path: str,
                          local_path: str,
                          recurse=True):

        sftp = await self.get_sftp_client()

        logging.debug(f'sftp get from {remote_path} to {local_path}')

        if os.path.isdir(local_path):
            local_path = os.path.join(local_path,
                                      os.path.basename(remote_path))

        if not recurse or not (await self.is_dir_sftp(remote_path)):
            await sftp.get(remotepaths=remote_path, localpath=local_path)
            return

        os.makedirs(local_path, exist_ok=True)

        files = await sftp.listdir(remote_path)
        for file in files:

            if file == '.' or file == '..':
                continue

            path = f'{remote_path}/{file}'

            if await self.is_dir_sftp(path):
                await self.get_by_sftp(path, local_path, recurse)
                continue

            basename, ext = os.path.splitext(os.path.basename(file))
            if (basename not in config.files_whitelist
                    and ext not in config.extensions_whitelist):
                continue

            if any(re_i.search(file) is not None
                    for re_i in config.filtered_extensions):
                continue

            await sftp.get(remotepaths=path,
                           localpath=os.path.join(local_path, file))

    async def mkdir_by_sftp(self, remote_path: str, recurse=False):
        sftp = await self.get_sftp_client()

        logging.debug(f'sftp mkdir {remote_path}')

        if not recurse:
            await sftp.mkdir(remote_path)
            return
        try:
            await sftp.lstat(remote_path)

        except asyncssh.SFTPNoSuchFile:
            dirname = os.path.dirname(remote_path)

            if dirname != '':
                await self.mkdir_by_sftp(dirname, recurse)

            await sftp.mkdir(remote_path)

    async def mkdir_by_webdav(self, remote_path: str, recurse=False):
        webdav = self.get_webdav_client()

        logging.debug(f'webdav mkdir {remote_path}')

        if not recurse:
            await webdav.create_directory(remote_path)
            return

        if await webdav.exists(remote_path):
            return

        dirname = os.path.dirname(remote_path)

        if dirname != '':
            await self.mkdir_by_webdav(dirname, recurse)

        await webdav.create_directory(remote_path)

    async def is_dir_sftp(self, path: str) -> bool:
        sftp = await self.get_sftp_client()

        try:
            stat = await sftp.lstat(path)
            return stat.type == asyncssh.FILEXFER_TYPE_DIRECTORY

        except asyncssh.SFTPNoSuchFile:
            return False

    async def put_by_sftp(self,
                          local_path: str,
                          remote_path: str,
                          recurse: bool = True):
        sftp = await self.get_sftp_client()

        logging.debug(f'sftp put {local_path} to {remote_path}')

        if await self.is_dir_sftp(remote_path):
            remote_path = f'{remote_path}/{os.path.basename(local_path)}'

        if not recurse or not os.path.isdir(local_path):
            await self.mkdir_by_sftp(os.path.dirname(remote_path), True)

            await sftp.put(localpaths=local_path, remotepath=remote_path)
            return

        await self.mkdir_by_sftp(remote_path, recurse=True)

        files = os.listdir(local_path)
        for file in files:
            path = os.path.join(local_path, file)

            if os.path.isdir(path):
                await self.put_by_sftp(path, remote_path, recurse)
                continue

            await sftp.put(localpaths=path, remotepath=f'{remote_path}/{file}')

    async def put_by_webdav(self, local_path: str, remote_path: str):
        webdav = self.get_webdav_client()

        await self.mkdir_by_webdav(os.path.dirname(remote_path), True)

        if os.path.isdir(local_path):
            await webdav.upload_directory(local_path=local_path,
                                          remote_path=remote_path)
            return

        await webdav.upload_file(local_path=local_path,
                                 remote_path=remote_path)

    async def get_request(self,
                          params: Dict[str, str] = None,
                          headers: Dict[str, str] = None,
                          endpoint: str = '') -> str:

        url = f'{self.host}/{endpoint}'

        params = dict(params=params,
                      headers=headers,
                      auth=aiohttp.BasicAuth(
                          login=self.user,
                          password=self.password.get_secret_value()))

        async with aiohttp.ClientSession() as session:
            async with session.get(url, **params) as response:
                if response.status != 200:
                    return None

                return await response.text()

    async def post_request(self,
                           data: Dict[str, str],
                           headers: Dict[str, str] = None,
                           endpoint: str = '') -> str:

        url = f'{self.host}/{endpoint}'

        params = dict(data=data,
                      headers=headers,
                      auth=aiohttp.BasicAuth(
                          login=self.user,
                          password=self.password.get_secret_value()))

        async with aiohttp.ClientSession() as session:
            async with session.post(url, **params) as response:

                if response.status != 200:
                    return None

                return await response.text()

    async def get_shared_link(self, path: str) -> str:
        r = await self.post_request(
            endpoint='ocs/v2.php/apps/files_sharing/api/v1/shares',
            headers={'OCS-APIRequest': 'true'},
            data={
                'path': path,
                'shareType': 3,
                'permissions': 1,
            })

        if r is None:
            return None

        tree = ElementTree.fromstring(r)
        data = tree.find('data')
        return data.find('url').text
