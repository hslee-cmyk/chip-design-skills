from ..core.compute_block import compute_block


@compute_block("blk", reads=[("graph", "alpha"), ("graph", "beta")], writes=[("graph", "gamma")])
def blk(projection):
    return {("graph", "gamma"): {"g": len(projection.column("graph", "alpha"))}}
