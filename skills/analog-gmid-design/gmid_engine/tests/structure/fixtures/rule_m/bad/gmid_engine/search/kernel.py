from .s3_index import S3Index
from gmid_engine.core import RunCounters as Counters


def evaluate():
    index = S3Index()
    counts = Counters()
    return index, counts
