import os
import stat
import pathlib
import shutil

import asyncssh
import pytest

from HPC_bot.hpc import Connection

pytest_plugins = ('pytest_asyncio',)

class MockTransport:

    def is_alive(self, *args, **kwargs):
        return True


class FileData:

    def __init__(self, mode):
        self.st_mode = mode


class MockSFTP:

    def _build_remote_path(self, path: pathlib.Path) -> pathlib.Path:
        return self.datadir / 'remote' / path

    def __init__(self, datadir):
        self.datadir = datadir

    async def get(self, remotepaths, localpath, *args, **kwargs):
        shutil.copyfile(self._build_remote_path(remotepaths), localpath)

    async def listdir(self, remotepath, *args, **kwargs):
        return os.listdir(self._build_remote_path(remotepath))

    async def mkdir(self, remotepath, *args, **kwargs):
        os.mkdir(self._build_remote_path(remotepath))

    async def stat(self, remotepath, *args, **kwargs):
        return os.stat(self._build_remote_path(remotepath))

    async def lstat(self, remotepath, *args, **kwargs):
        try:
            file_stat = os.lstat(self._build_remote_path(remotepath))

        except FileNotFoundError:
            raise asyncssh.SFTPNoSuchFile("")

        if stat.S_ISDIR(file_stat.st_mode):
            file_type = asyncssh.FILEXFER_TYPE_DIRECTORY
        else:
            file_type = asyncssh.FILEXFER_TYPE_REGULAR

        return asyncssh.SFTPAttrs(type=file_type)

    async def put(self, localpaths, remotepath, *args, **kwargs):
        shutil.copyfile(localpaths, self._build_remote_path(remotepath))


class MockSSH:

    def __init__(self, datadir):
        self.datadir = datadir

    def connect(self, *args, **kwargs):
        pass

    def get_transport(self, *args, **kwargs):
        return MockTransport()

    async def open_sftp(self, *args, **kwargs):
        return MockSFTP(self.datadir)
    
    async def run(self, command, *args, **kwargs):
        pass



class MockHTTP:
    pass


class MockWebdav:
    pass


class MockOCS:
    pass


@pytest.fixture
def datadir(tmp_path: pathlib.Path, request):
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    if os.path.isdir(test_dir):
        shutil.copytree(test_dir, str(tmp_path), dirs_exist_ok=True)

    return tmp_path


@pytest.fixture
def connection(datadir):
    conn = Connection(host='localhost', port=22, user='test', password='test')
    conn.ssh_client = MockSSH(datadir)
    conn.sftp_client = MockSFTP(datadir)
    return conn


def test_constructor():
    connection = Connection(host='10.0.0.1',
                            port=2222,
                            user='root',
                            password='toor')
    assert connection.host == '10.0.0.1'
    assert connection.port == 2222
    assert connection.user == 'root'
    assert connection.password.get_secret_value() == 'toor'

@pytest.mark.asyncio
async def test_get_file_by_sftp(connection: Connection, datadir: pathlib.Path):
    await connection.get_by_sftp('calculation.inp', str(datadir))
    files = os.listdir(str(datadir))
    assert 'calculation.inp' in files

@pytest.mark.asyncio
async def test_get_filtered_file_by_sftp(connection: Connection, datadir: pathlib.Path):
    await connection.get_by_sftp('.', str(datadir))
    files = os.listdir(str(datadir))
    assert 'calculation.tmp.log' not in files

@pytest.mark.asyncio
async def test_get_non_whitelist_file_by_sftp(connection: Connection, datadir: pathlib.Path):
    await connection.get_by_sftp('.', str(datadir))
    files = os.listdir(str(datadir))
    assert 'calculation.lol' not in files

@pytest.mark.asyncio
async def test_put_file_by_sftp(connection: Connection, datadir: pathlib.Path):
    await connection.put_by_sftp(str(datadir / 'simple_input.inp'), '.')
    files = os.listdir(str(datadir / 'remote'))
    assert 'simple_input.inp' in files


@pytest.mark.asyncio
async def test_get_folder_by_sftp(connection: Connection, datadir: pathlib.Path):
    folder_name = 'folder'

    await connection.get_by_sftp(folder_name, str(datadir))

    local_folder = os.listdir(datadir / folder_name)
    remote_folder = os.listdir(datadir / 'remote' / folder_name)
    assert os.path.exists(datadir / folder_name)
    assert local_folder == remote_folder


@pytest.mark.asyncio
async def test_put_folder_by_sftp(connection: Connection, datadir: pathlib.Path):
    folder_name = 'new_folder'

    await connection.put_by_sftp(datadir / folder_name, '.')

    local_folder = os.listdir(datadir / folder_name)
    remote_folder = os.listdir(datadir / 'remote' / folder_name)
    assert os.path.exists(datadir / 'remote' / folder_name)
    assert local_folder == remote_folder
