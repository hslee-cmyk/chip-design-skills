from ..core.compute_block import compute_block


def _current(snapshot, key):
    return snapshot.value("device", key, "dc_op").current


@compute_block("lay", reads=[], writes=[("graph", "ly_point")])
def lay(projection):
    bundle = {"m1": _current(projection, "m1")}
    return {("graph", "ly_point"): bundle}
