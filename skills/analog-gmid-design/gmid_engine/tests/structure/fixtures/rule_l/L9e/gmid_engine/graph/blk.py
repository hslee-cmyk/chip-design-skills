from ..core.compute_block import compute_block


@compute_block("blk", reads=[], writes=[("graph", "rel_alpha")])
def blk(projection):
    return {("graph", "rel_alpha"): {"g": 1.0}}
