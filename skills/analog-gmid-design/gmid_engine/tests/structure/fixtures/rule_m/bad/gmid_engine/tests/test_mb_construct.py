from gmid_engine.search import S3Index
from gmid_engine import core


def test_direct():
    index = S3Index()
    counters = core.RunCounters()
    assert index is not counters
