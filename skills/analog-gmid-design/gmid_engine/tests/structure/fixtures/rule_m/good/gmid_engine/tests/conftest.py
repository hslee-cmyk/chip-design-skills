import pytest

from gmid_engine.graph import build_s1
from gmid_engine.search import open_run


@pytest.fixture
def pair():
    return open_run()


@pytest.fixture(scope="session")
def shared_s1():
    donors, counters = open_run()
    return build_s1("doc", donors=donors, counters=counters)


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: 무거운 test")
