def disk_reader(sctx):
    reader = sctx.archive.read_snapshot
    return reader


def private_reader(path):
    from . import front_query
    return front_query._read_snapshot_file(path)
