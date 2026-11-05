from ..graph.blk import blk

_FIELDS = (("graph", "alpha"),)


def run_stage_a(snapshot):
    snapshot = blk(snapshot)
    out = []
    for kind, name in _FIELDS:
        out.append(snapshot.column(kind, name))
    return out
