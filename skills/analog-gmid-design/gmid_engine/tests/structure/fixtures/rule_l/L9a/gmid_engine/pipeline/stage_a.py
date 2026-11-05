from ..graph.blk import blk


def read_field(snapshot, name):
    return snapshot.column("graph", name)


def run_stage_a(snapshot):
    snapshot = blk(snapshot)
    return read_field(snapshot, "alpha")
