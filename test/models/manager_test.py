import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError

from HPC_bot.database.telegram_user_dao import TelegramUserDAO
from HPC_bot.database.calculation_dao import CalculationDAO
from HPC_bot.database.database import engine, sessionmaker
from HPC_bot.database.user_dao import UserDAO
from HPC_bot.hpc.cluster import Cluster as ClusterHPC
from HPC_bot.hpc.connection import Connection
from HPC_bot.models.base_model import BaseDBModel
from HPC_bot.models.calculation import (
    BlockedException,
    Calculation,
    CalculationLimitExceeded,
    SubmitType,
)
from HPC_bot.models.person import Person
from HPC_bot.models.user import NEWLY_REGISTERED_LIMIT, AccessLevel, User


@pytest_asyncio.fixture
async def session():
    session = sessionmaker()
    yield session
    await session.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def refresh_db():
    async with engine.begin() as conn:
        await conn.run_sync(BaseDBModel.metadata.drop_all)
        await conn.run_sync(BaseDBModel.metadata.create_all)


@pytest.fixture()
def users():
    return [
        {
            "first_name": "Ivan",
            "last_name": "Ivanov",
            "id": 1,
            "tg_id": 123123,
            "approved": False,
            "blocked": False,
        },
        {
            "first_name": "Maria",
            "last_name": "Pavlova",
            "id": 2,
            "tg_id": 12877,
            "approved": True,
            "blocked": False,
        },
        {
            "first_name": "Ekaterina",
            "last_name": "Sidorova",
            "id": 3,
            "tg_id": 999123,
            "approved": False,
            "blocked": True,
        },
    ]


@pytest_asyncio.fixture(scope="function", autouse=True)
async def update_values(session, users):
    for user in users:
        await TelegramUserDAO.register(
            session, user["tg_id"], user["first_name"], user["last_name"]
        )

        if user["approved"]:
            await UserDAO.approve(session, user["id"])
        if user["blocked"]:
            await UserDAO.block(session, user["id"])


@pytest.mark.asyncio
@pytest.mark.parametrize("first_name,last_name", [("John", "Doe"), ("Jane", "Doe")])
async def test_valid_user_save(first_name, last_name, session):
    new = await UserDAO.save(
        session, **{"first_name": first_name, "last_name": last_name}
    )

    assert new.id is not None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "first_name,last_name,organization", [("John", "Doe", None), ("Jane", "Doe", None)]
)
async def test_valid_user_registration(first_name, last_name, organization, session):

    new = await UserDAO.register(session, first_name, last_name, organization)

    assert new.id is not None
    assert new.person.first_name == first_name
    assert new.person.last_name == last_name
    assert (
        new.person.organization is None and organization is None
    ) or new.person.organization.name == organization


@pytest_asyncio.fixture
async def not_approved_user(session, users):
    for user in users:
        if not user["approved"]:
            return await UserDAO.get_by_id(session, user["id"])


@pytest_asyncio.fixture
async def approved_user(session, users):
    for user in users:
        if user["approved"]:
            return await UserDAO.get_by_id(session, user["id"])


@pytest_asyncio.fixture
async def blocked_user(session, users):
    for user in users:
        if user["blocked"]:
            return await UserDAO.get_by_id(session, user["id"])


@pytest.mark.asyncio
async def test_user_approval(session, not_approved_user):
    await UserDAO.approve(session, not_approved_user.id)
    user = await UserDAO.get_by_id(session, not_approved_user.id)

    assert user.person.approved


@pytest.mark.asyncio
async def test_approved_user_approval(session, approved_user):
    user = await UserDAO.approve(session, approved_user.id)

    assert user is None

    user = await UserDAO.get_by_id(session, approved_user.id)
    assert user.person.approved


@pytest.mark.asyncio
async def test_nonexisting_user_approval(session):
    user_id = 10000

    user = await UserDAO.get_by_id(session, user_id)
    assert user is None

    user = await UserDAO.approve(session, user_id)
    assert user is None


@pytest.fixture
def cluster_hpc():
    return ClusterHPC(
        label="cluster",
        connection=Connection(port=80, user="user"),
        upload_path="/home/user",
    )


@pytest.mark.asyncio
async def test_new_calculation(session, approved_user, cluster_hpc):
    new = await CalculationDAO.new_calculation(
        session,
        "new calculation",
        "run_calc",
        approved_user,
        SubmitType.TELEGRAM,
        cluster_hpc,
    )
    assert new.id is not None

    retrieved = await CalculationDAO.get_by_id(session, new.id)
    assert retrieved is not None
    assert retrieved.id == new.id
    assert retrieved.name == new.name
    assert retrieved.command == new.command
    assert retrieved.user_id == new.user_id
    assert retrieved.submit_type == new.submit_type
    assert retrieved.cluster.label == new.cluster.label


@pytest.mark.asyncio
async def test_new_calculation_blocked(session, blocked_user, cluster_hpc):
    with pytest.raises(BlockedException):
        await CalculationDAO.new_calculation(
            session,
            "new calculation",
            "run_calc",
            blocked_user,
            SubmitType.TELEGRAM,
            cluster_hpc,
        )


@pytest.mark.asyncio
async def test_calculation_limit(session, not_approved_user, cluster_hpc):
    for i in range(NEWLY_REGISTERED_LIMIT):
        new = await CalculationDAO.new_calculation(
            session,
            "new calculation",
            "run_calc",
            not_approved_user,
            SubmitType.TELEGRAM,
            cluster_hpc,
        )
        assert new.id is not None

    with pytest.raises(CalculationLimitExceeded):
        await CalculationDAO.new_calculation(
            session,
            "new calculation",
            "run_calc",
            not_approved_user,
            SubmitType.TELEGRAM,
            cluster_hpc,
        )


@pytest.mark.asyncio
async def test_calculation_count(session, not_approved_user, cluster_hpc):
    assert await CalculationDAO.count_for_user(session, not_approved_user.id) == 0

    await CalculationDAO.new_calculation(
        session,
        "new calculation",
        "run_calc",
        not_approved_user,
        SubmitType.TELEGRAM,
        cluster_hpc,
    )

    assert await CalculationDAO.count_for_user(session, not_approved_user.id) == 1


@pytest.mark.asyncio
async def test_calculation_get_all(session, not_approved_user, cluster_hpc):
    assert not await CalculationDAO.get_all(session)

    await CalculationDAO.new_calculation(
        session,
        "new calculation",
        "run_calc",
        not_approved_user,
        SubmitType.TELEGRAM,
        cluster_hpc,
    )

    calculations = await CalculationDAO.get_all(session)
    assert len(calculations) == 1
    assert calculations[0].name == "new calculation"
    assert calculations[0].command == "run_calc"
    assert calculations[0].user_id == not_approved_user.id
    assert calculations[0].submit_type == SubmitType.TELEGRAM
    assert calculations[0].cluster.name == cluster_hpc.label


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tg_id,first_name,last_name", [(123, "John", "Doe"), (132132, "Jane", "Doe")]
)
async def test_telegram_registration(session, tg_id, first_name, last_name):
    new = await TelegramUserDAO.register(session, tg_id, first_name, last_name)

    assert new.tg_id == tg_id
    assert new.user_id is not None
    assert new.user.person.first_name == first_name
    assert new.user.person.last_name == last_name


@pytest.mark.asyncio
async def test_telegram_get_with_calcs(
    session, users, approved_user, not_approved_user, cluster_hpc
):
    tg_users = await TelegramUserDAO.get_all_with_calcs(session)
    assert len(tg_users) == len(users)

    for user in tg_users:
        assert user.num_calc == 0

    await CalculationDAO.new_calculation(
        session,
        "calc 1",
        "run_calc",
        not_approved_user,
        SubmitType.TELEGRAM,
        cluster_hpc,
    )
    await CalculationDAO.new_calculation(
        session, "calc 2", "run_calc", approved_user, SubmitType.TELEGRAM, cluster_hpc
    )

    tg_users = await TelegramUserDAO.get_all_with_calcs(session)
    assert len(users) == len(tg_users)

    for user in tg_users:
        if not user.user.blocked:
            assert user.num_calc == 1

    assert tg_users[-1].num_calc == 0


@pytest.mark.asyncio
async def test_authorize(session, users):
    user = await TelegramUserDAO.get_if_authorized(session, users[0]["tg_id"])
    assert user is not None

    user = await TelegramUserDAO.get_if_authorized(
        session, users[0]["tg_id"], AccessLevel.ADMIN
    )
    assert user is None

    user = await TelegramUserDAO.get_if_authorized(session, -1000)
    assert user is None


@pytest.mark.asyncio
async def test_join_when_getting_tg_user(session, users):
    user = await TelegramUserDAO.get_by_id(session, users[0]["tg_id"])

    assert user is not None
    assert user.user.person.first_name == users[0]["first_name"]
    assert user.user.person.last_name == users[0]["last_name"]
