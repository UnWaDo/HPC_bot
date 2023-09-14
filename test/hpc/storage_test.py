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


def test_webdav_constructor(webdav_connection):
    storage = RemoteStorage(
        webdav=webdav_connection,
        base_path='/'
    )
    assert storage.webdav == webdav_connection
    assert storage.base_path == '/'
