import functools

from gmid_engine.search import open_run
from gmid_engine.sizing import build_kernel_context
import pytest

RUNS = []


class Holder:
    pair = open_run()


def helper(pair=open_run()):
    return pair


@functools.lru_cache(maxsize=None)
def cached():
    return open_run()


def make():
    return open_run()


cached_call = functools.cache(make)


def test_append():
    RUNS.append(open_run())


class Box:
    def __init__(self):
        self.pair = open_run()


BOX = Box()


@pytest.fixture(scope="session")
def kernel_ctx():
    d, c = open_run()
    ctx = build_kernel_context("s1", "inputs", "lut", donors=d, counters=c)
    return ctx


def _ctx_helper():
    d, c = open_run()
    return build_kernel_context("s1", "inputs", "lut", donors=d, counters=c)


@pytest.fixture(scope="package")
def via_helper():
    return _ctx_helper()


SCTX = []


def test_context_attr(case):
    SCTX.append(case.sctx)
