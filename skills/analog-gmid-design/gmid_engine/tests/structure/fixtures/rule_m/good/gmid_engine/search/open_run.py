from gmid_engine.core import RunCounters
from .s3_index import S3Index


def open_run():
    return S3Index(), RunCounters()
