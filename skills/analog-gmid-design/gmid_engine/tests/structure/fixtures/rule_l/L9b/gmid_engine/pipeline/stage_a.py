from ..graph.blk import blk


def run_stage_a(snapshot):
    snapshot = blk(snapshot)
    out = []
    for name in ("alpha",):
        out.append(snapshot.column("graph", name))
    return out
