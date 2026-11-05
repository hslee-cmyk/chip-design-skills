from ..core.compute_block import compute_block

_R1 = (("graph", "alpha"),)
_R2 = (("graph", "beta"), ("graph", "delta"))


@compute_block("blk", reads=_R1 + _R2, writes=[("graph", "gamma")])
def blk(projection):
    return {("graph", "gamma"): {"g": len(projection.column("graph", "alpha"))}}
