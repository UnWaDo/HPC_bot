import os
from stat import S_ISDIR
from typing import Dict, Optional, Tuple
from xml.etree import ElementTree
from pydantic import BaseModel, Field, SecretStr
from paramiko import SSHClient, AutoAddPolicy
from paramiko.ssh_exception import SSHException
from webdav3.client import Client as WebdavClient
from pysftp import Connection as SFTPClient
import logging
import requests
from requests.auth import HTTPBasicAuth


class Connection(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    host: str = 'localhost'
    port: int = Field(ge=1)

    user: str

    password: Optional[SecretStr] = None
    key_path: Optional[str] = None

    ssh_client: Optional[SSHClient] = None
    sftp_client: Optional[SFTPClient] = None
    webdav_client: Optional[WebdavClient] = None

    def open_ssh(self) -> SSHClient:
        if self.ssh_client is not None:
            self.ssh_client.close()

        self.ssh_client = SSHClient()
        self.ssh_client.set_missing_host_key_policy(AutoAddPolicy())

        if self.key_path:
            password = None
            key = self.key_path
        else:
            password = self.password.get_secret_value()
            key = None

        try:
            self.ssh_client.connect(
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=password,
                key_filename=key,
            )
        except (SSHException, TimeoutError) as e:
            logging.error('Connection error for {user}@{host}'.format(
                user=self.user,
                host=self.host
            ), exc_info=e, stack_info=True)
            raise ConnectionError('Failed to connect to server')

        return self.ssh_client

    def open_sftp(self) -> SFTPClient:
        if self.sftp_client is not None:
            self.sftp_client.close()

        ssh = self.get_ssh_client()
        self.sftp_client = ssh.open_sftp()
        return self.sftp_client

    def open_webdav(self) -> WebdavClient:
        if self.key_path:
            password = ''
            key = self.key_path
        else:
            password = self.password.get_secret_value()
            key = ''

        options = {
            'webdav_hostname': (
                f'{self.host}/remote.php'
                f'/dav/files/{self.user}'
            ),
            'webdav_login': self.user,
            'webdav_password': password,
            'webdav_token': key
        }
        return WebdavClient(options)

    def is_ssh_active(self) -> bool:
        if self.ssh_client is None:
            return False
        transport = self.ssh_client.get_transport()
        return (transport is not None) and transport.is_alive()

    def get_ssh_client(self) -> SSHClient:
        if self.is_ssh_active():
            return self.ssh_client
        return self.open_ssh()

    def get_sftp_client(self) -> SFTPClient:
        if self.sftp_client is None or not self.is_ssh_active():
            return self.open_sftp()
        return self.sftp_client

    def get_webdav_client(self) -> WebdavClient:
        if self.webdav_client is None:
            return self.open_webdav()
        return self.webdav_client

    def execute_by_ssh(self, command: str) -> Tuple[str, str]:
        ssh = self.get_ssh_client()

        stdin, stdout, stderr = ssh.exec_command(command)
        stdin.close()

        return ''.join(stdout.readlines()), ''.join(stderr.readlines())

    def get_by_sftp(self, remote_path: str, local_path: str, recurse=True):
        sftp = self.get_sftp_client()

        logging.debug(f'sftp get from {remote_path} to {local_path}')

        if os.path.isdir(local_path):
            local_path = os.path.join(
                local_path,
                os.path.basename(remote_path)
            )

        if not recurse or not self.is_dir_sftp(remote_path):
            sftp.get(remotepath=remote_path, localpath=local_path)
            return

        os.makedirs(local_path, exist_ok=True)

        files = sftp.listdir(remote_path)
        for file in files:
            path = f'{remote_path}/{file}'
            if self.is_dir_sftp(path):
                self.get_by_sftp(path, local_path, recurse)
                continue
            sftp.get(
                remotepath=path,
                localpath=os.path.join(
                    local_path,
                    file
                )
            )

    def mkdir_by_sftp(self, remote_path: str, recurse=False):
        sftp = self.get_sftp_client()

        logging.debug(f'sftp mkdir {remote_path}')

        if not recurse:
            sftp.mkdir(remote_path)
            return
        try:
            sftp.lstat(remote_path)
        except IOError:
            dirname = os.path.dirname(remote_path)

            if dirname != '':
                self.mkdir_by_sftp(dirname, recurse)
            sftp.mkdir(remote_path)

    def mkdir_by_webdav(self, remote_path: str, recurse=False):
        webdav = self.get_webdav_client()

        logging.debug(f'webdav mkdir {remote_path}')

        if not recurse:
            webdav.mkdir(remote_path)
            return

        if webdav.check(remote_path):
            return

        dirname = os.path.dirname(remote_path)

        if dirname != '':
            self.mkdir_by_webdav(dirname, recurse)
        webdav.mkdir(remote_path)

    def is_dir_sftp(self, path: str) -> bool:
        sftp = self.get_sftp_client()

        try:
            if S_ISDIR(sftp.lstat(path).st_mode):
                return True
        except IOError:
            return False

    def put_by_sftp(
        self,
        local_path: str,
        remote_path: str,
        recurse: bool = True
    ):
        sftp = self.get_sftp_client()

        logging.debug(f'sftp put {local_path} to {remote_path}')

        if self.is_dir_sftp(remote_path):
            remote_path = f'{remote_path}/{os.path.basename(local_path)}'

        if not recurse or not os.path.isdir(local_path):
            self.mkdir_by_sftp(os.path.dirname(remote_path), True)

            sftp.put(localpath=local_path, remotepath=remote_path)
            return

        self.mkdir_by_sftp(remote_path, recurse=True)

        files = os.listdir(local_path)
        for file in files:
            path = os.path.join(local_path, file)
            if os.path.isdir(path):
                self.put_by_sftp(path, remote_path, recurse)
                continue
            sftp.put(
                localpath=path,
                remotepath=f'{remote_path}/{file}'
            )

    def put_by_webdav(self, local_path: str, remote_path: str):
        webdav = self.get_webdav_client()

        self.mkdir_by_webdav(os.path.dirname(remote_path), True)

        if os.path.isdir(local_path):
            webdav.upload_directory(
                local_path=local_path,
                remote_path=remote_path
            )
            return
        webdav.upload_file(
            local_path=local_path,
            remote_path=remote_path
        )

    def get_request(
        self,
        params: Dict[str, str] = None,
        headers: Dict[str, str] = None,
        endpoint: str = ''
    ) -> requests.Response:

        return requests.get(
            f'{self.host}/{endpoint}',
            params=params,
            headers=headers,
            auth=HTTPBasicAuth(
                username=self.user,
                password=self.password.get_secret_value()
            )
        )

    def post_request(
        self,
        data: Dict[str, str],
        headers: Dict[str, str] = None,
        endpoint: str = ''
    ) -> requests.Response:

        return requests.post(
            f'{self.host}/{endpoint}',
            data=data,
            headers=headers,
            auth=HTTPBasicAuth(
                username=self.user,
                password=self.password.get_secret_value()
            )
        )

    def get_shared_link(self, path: str) -> str:
        r = self.post_request(
            endpoint='ocs/v2.php/apps/files_sharing/api/v1/shares',
            headers={'OCS-APIRequest': 'true'},
            data={
                'path': path,
                'shareType': 3,
                'permissions': 1,
            }
        )
        if r.status_code != 200:
            return None

        tree = ElementTree.fromstring(r.content)
        data = tree.find('data')
        return data.find('url').text
