from ..graph.blk import blk


def run_stage_a(snapshot):
    return blk(snapshot)


def _dead(snapshot):
    return snapshot.column("graph", "alpha")
