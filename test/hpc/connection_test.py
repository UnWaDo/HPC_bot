from distutils import dir_util
import os
import pathlib
import shutil
import sys

import paramiko
import pytest

from HPC_bot.hpc import Connection


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

    def get(self, remotepath, localpath, *args, **kwargs):
        shutil.copyfile(self._build_remote_path(remotepath), localpath)

    def listdir(self, remotepath, *args, **kwargs):
        return os.listdir(self._build_remote_path(remotepath))

    def mkdir(self, remotepath, *args, **kwargs):
        os.mkdir(self._build_remote_path(remotepath))

    def lstat(self, remotepath, *args, **kwargs):
        return os.lstat(self._build_remote_path(remotepath))

    def put(self, localpath, remotepath, *args, **kwargs):
        shutil.copyfile(localpath, self._build_remote_path(remotepath))


class MockSSH:

    def __init__(self, datadir):
        self.datadir = datadir

    def connect(self, *args, **kwargs):
        pass

    def get_transport(self, *args, **kwargs):
        return MockTransport()

    def open_sftp(self, *args, **kwargs):
        return MockSFTP(self.datadir)


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


def test_get_file_by_sftp(connection: Connection, datadir: pathlib.Path):
    connection.get_by_sftp('calculation.inp', str(datadir))
    files = os.listdir(str(datadir))
    assert 'calculation.inp' in files


def test_put_file_by_sftp(connection: Connection, datadir: pathlib.Path):
    connection.put_by_sftp(str(datadir / 'simple_input.inp'), '.')
    files = os.listdir(str(datadir / 'remote'))
    assert 'simple_input.inp' in files


def test_get_folder_by_sftp(connection: Connection, datadir: pathlib.Path):
    folder_name = 'folder'

    connection.get_by_sftp(folder_name, str(datadir))

    local_folder = os.listdir(datadir / folder_name)
    remote_folder = os.listdir(datadir / 'remote' / folder_name)
    assert os.path.exists(datadir / folder_name)
    assert local_folder == remote_folder


def test_put_folder_by_sftp(connection: Connection, datadir: pathlib.Path):
    folder_name = 'new_folder'

    connection.put_by_sftp(datadir / folder_name, '.')

    local_folder = os.listdir(datadir / folder_name)
    remote_folder = os.listdir(datadir / 'remote' / folder_name)
    assert os.path.exists(datadir / 'remote' / folder_name)
    assert local_folder == remote_folder
