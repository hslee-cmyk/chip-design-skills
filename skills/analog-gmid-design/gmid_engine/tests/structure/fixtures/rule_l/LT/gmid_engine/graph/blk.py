from ..core.compute_block import compute_block


def _writes():
    return [("graph", "alpha")]


@compute_block("blk", reads=[], writes=_writes())
def blk(projection):
    return {("graph", "alpha"): {"g": 1.0}}
