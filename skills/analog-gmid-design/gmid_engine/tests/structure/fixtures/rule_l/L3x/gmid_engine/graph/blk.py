from ..core.compute_block import compute_block


def _reads():
    return [("graph", "alpha")]


@compute_block("blk", reads=_reads(), writes=[("graph", "alpha")])
def blk(projection):
    return {("graph", "alpha"): {"g": 1.0}}
