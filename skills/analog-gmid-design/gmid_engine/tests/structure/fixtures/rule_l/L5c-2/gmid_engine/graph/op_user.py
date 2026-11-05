from ..core.compute_block import compute_block


@compute_block("lay", reads=[], writes=[("graph", "ly_point")])
def lay(projection):
    op = projection.value("device", "m1", "dc_op")
    return {("graph", "ly_point"): {"m1": op.current * 2.0}}
