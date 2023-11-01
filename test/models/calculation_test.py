from datetime import datetime
import pytest

from HPC_bot.models import Calculation, User
from HPC_bot.models import CalculationStatus


@pytest.fixture
def pending_calculation():
    return Calculation(
        id=1,
        name='test',
        start_datetime=datetime.utcnow(),
        slurm_id=1,
        status=CalculationStatus.PENDING
    )


@pytest.fixture
def finished_calculation():
    return Calculation(
        id=1,
        name='test',
        start_datetime=datetime.utcnow(),
        end_datetime=datetime.now(),
        slurm_id=1,
        status=CalculationStatus.FINISHED_OK
    )


def test_calc_ge(pending_calculation, finished_calculation):
    assert finished_calculation.status >= pending_calculation.status
