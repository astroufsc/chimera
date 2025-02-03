import pytest

from chimera.core.manager import Manager


@pytest.fixture
def manager():
    manager = Manager()
    yield manager
    manager.shutdown()
