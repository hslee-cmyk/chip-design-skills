from ..core.compute_block import compute_block


class _Row:
    def __init__(self, a, c):
        self.a = a
        self.c = c


@compute_block("lay", reads=[], writes=[("graph", "ly_point")])
def lay(projection):
    op = projection.value("device", "m1", "dc_op")
    row = _Row(a=op.current, c=2.0)
    return {("graph", "ly_point"): {"m1": row.c}}
