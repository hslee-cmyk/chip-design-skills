from ..graph.blk import blk


def _make(name):
    def get(snapshot):
        return snapshot.column("graph", name)

    return get


def run_stage_a(snapshot):
    snapshot = blk(snapshot)
    reader = _make("alpha")
    return reader(snapshot)
