from gmid_engine.search.front_query import _read_snapshot_file as load


def peek(path):
    return load(path)
