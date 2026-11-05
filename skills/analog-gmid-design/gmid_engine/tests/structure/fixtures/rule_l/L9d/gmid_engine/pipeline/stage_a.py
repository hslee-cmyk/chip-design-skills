from ..graph.blk import blk
from ..core.graph_snapshot import read_any


def run_stage_a(snapshot):
    snapshot = blk(snapshot)
    return read_any(snapshot, "alpha"), snapshot.column("graph", "alpha")
