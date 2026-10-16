import pytest

from gmid_engine.search import open_run

PAIR = open_run()


@pytest.fixture(scope="session")
def shared_pair():
    return open_run()


@pytest.fixture(scope="module")
def module_pair():
    d, c = open_run()
    yield d, c


def pytest_configure(config):
    config.stash["pair"] = open_run()


@pytest.fixture
def via_request(request):
    request.config.pair = open_run()
    return 1
