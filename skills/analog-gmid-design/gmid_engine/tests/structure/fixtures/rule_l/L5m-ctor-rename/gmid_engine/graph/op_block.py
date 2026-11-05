from ..core.compute_block import compute_block


@compute_block("op_block", reads=[], writes=[("device", "dc_op")])
def op_block(projection):
    return {("device", "dc_op"): {"m1": 1.0}}
