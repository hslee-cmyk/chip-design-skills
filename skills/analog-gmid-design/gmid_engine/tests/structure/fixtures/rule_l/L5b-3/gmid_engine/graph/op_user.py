from ..core.compute_block import compute_block

_TABLE = ()


@compute_block("lay", reads=[], writes=[("graph", "ly_point")])
def lay(projection):
    op = projection.value("device", "m1", "dc_op")
    fn = _TABLE[0]
    return {("graph", "ly_point"): fn(op)}
