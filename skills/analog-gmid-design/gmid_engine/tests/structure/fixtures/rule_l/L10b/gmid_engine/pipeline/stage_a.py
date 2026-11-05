from ..graph.blk import blk


def run_stage_a(snapshot):
    snapshot = blk(snapshot)
    return snapshot.column("graph", "alpha")
