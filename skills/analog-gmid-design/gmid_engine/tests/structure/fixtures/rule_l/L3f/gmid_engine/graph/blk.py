from ..core.compute_block import compute_block


@compute_block("blk", reads=[("graph", "alpha"), ("graph", "beta")], writes=[("graph", "gamma")])
def blk(projection):
    p = projection
    s1 = projection
    return {("graph", "gamma"): {"g": len(p.column("graph", "alpha")) + len(s1.column("graph", "beta"))}}
