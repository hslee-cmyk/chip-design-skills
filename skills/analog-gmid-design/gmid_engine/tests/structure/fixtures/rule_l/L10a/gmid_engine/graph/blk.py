from ..core.compute_block import compute_block


@compute_block("blk", reads=[], writes=[("graph", "alpha")])
def blk(projection):
    return {("graph", "alpha"): {"g": 1.0}}
