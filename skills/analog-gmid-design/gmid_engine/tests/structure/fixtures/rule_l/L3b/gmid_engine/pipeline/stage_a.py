from ..graph.blk import blk
from ..graph.src import src


def run_stage_a(snapshot):
    snapshot = blk(src(snapshot))
    return (
        snapshot.column("graph", "alpha"),
        snapshot.column("graph", "beta"),
        snapshot.column("graph", "delta"),
        snapshot.column("graph", "gamma"),
    )
