from ..core.compute_block import compute_block
from .helper import beta_len


@compute_block("blk", reads=[("graph", "alpha"), ("graph", "beta")], writes=[("graph", "gamma")])
def blk(projection):
    p = projection
    return {("graph", "gamma"): {"g": len(projection.column("graph", "alpha")) + beta_len(p)}}
