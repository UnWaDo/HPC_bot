import pytest

from HPC_bot.hpc import Connection


def test_constructor():
    connection = Connection(
        host='10.0.0.1',
        port=2222,
        user='root',
        password='toor'
    )
    assert connection.host == '10.0.0.1'
    assert connection.port == 2222
    assert connection.user == 'root'
    assert connection.password.get_secret_value() == 'toor'
