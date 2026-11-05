from ..graph.blk import blk


def run_stage_a(snapshot):
    snapshot = blk(snapshot)
    return _report(snapshot)


def _report(snapshot):
    return snapshot.column("graph", "alpha")
