from ..core.compute_block import compute_block


@compute_block("blk", reads=[("graph", "alpha")], writes=[("graph", "alpha")])
def blk(projection):
    seen = projection.column("graph", "alpha")
    return {("graph", "alpha"): {"g": len(seen)}}
