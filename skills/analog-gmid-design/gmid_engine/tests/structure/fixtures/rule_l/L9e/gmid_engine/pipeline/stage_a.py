from ..graph.blk import blk

_SUF = "alpha"


def run_stage_a(snapshot):
    snapshot = blk(snapshot)
    return snapshot.column("graph", "rel_" + _SUF)
