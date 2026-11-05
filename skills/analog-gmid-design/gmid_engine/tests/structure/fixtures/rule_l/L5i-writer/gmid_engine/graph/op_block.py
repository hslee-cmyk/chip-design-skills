from ..core.compute_block import compute_block


@compute_block("op_block", reads=[], writes=[("device", "dc_op")])
def op_block(projection):
    op = projection.value("device", "m1", "dc_op")
    projection.ctx.save(op.current)
    return {("device", "dc_op"): {"m1": 1.0}}
