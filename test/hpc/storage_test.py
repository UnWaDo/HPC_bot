import pytest

from HPC_bot.hpc import RemoteStorage, Connection


@pytest.fixture()
def ssh_connection():
    return Connection(
        host='localhost',
        port=22,
        user='root',
        password='toor',
    )


@pytest.fixture()
def webdav_connection():
    return Connection(
        host='localhost',
        port=80,
        user='root',
        password='toor',
    )


def test_sftp_constructor(ssh_connection):
    storage = RemoteStorage(
        sftp=ssh_connection,
        base_path='/'
    )
    assert storage.webdav == None
    assert storage.sftp == ssh_connection
    assert storage.base_path == '/'


def test_webdav_constructor(webdav_connection):
    storage = RemoteStorage(
        webdav=webdav_connection,
        base_path='/'
    )
    assert storage.webdav == webdav_connection
    assert storage.sftp == None
    assert storage.base_path == '/'


def test_no_connection_constructor(webdav_connection):
    pytest.raises(ValueError, RemoteStorage, base_path='/')

