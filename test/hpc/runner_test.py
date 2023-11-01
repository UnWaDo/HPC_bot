import pytest

from HPC_bot.hpc import Runner


def test_constructor():
    runner = Runner(
        program='ls',
        allowed_args=['-l']
    )
    assert runner.program == 'ls'
    assert runner.allowed_args == ['-l']
    assert runner.default_args == []


def test_constructor_with_name():
    runner = Runner(
        program='ls',
        allowed_args=['-l', '{}']
    )
    assert runner.program == 'ls'
    assert runner.allowed_args == ['-l', '{}']
    assert runner.default_args == ['{}']


def test_constructor_with_default():
    runner = Runner(
        program='ls',
        allowed_args=['-l', '{}'],
        default_args=['-l']
    )
    assert runner.program == 'ls'
    assert runner.allowed_args == ['-l', '{}']
    assert runner.default_args == ['-l']


def test_constructor_with_invalid_default():
    with pytest.raises(ValueError):
        Runner(
            program='ls',
            allowed_args=['-l', '{}'],
            default_args=['-m']
        )


def test_construct_empty_command():
    runner = Runner(
        program='ls',
        allowed_args=['-l', '{}']
    )
    assert runner.create_command([]) == 'ls'


def test_construct_command():
    runner = Runner(
        program='ls',
        allowed_args=['-l', '{}']
    )
    assert runner.create_command(['-l']) == 'ls -l'


def test_construct_command_with_filename():
    runner = Runner(
        program='ls',
        allowed_args=['-l', '{}']
    )
    assert runner.create_command(['-l', '{}'], 'path') == "ls -l 'path'"


def test_construct_default_command():
    runner = Runner(
        program='ls',
        allowed_args=['-l', '{}'],
        default_args=['-l', '{}']
    )
    assert runner.create_command() == "ls -l ''"


def test_construct_default_command_with_path():
    runner = Runner(
        program='ls',
        allowed_args=['-l', '{}'],
        default_args=['-l', '{}']
    )
    assert runner.create_command(filename='path') == "ls -l 'path'"
