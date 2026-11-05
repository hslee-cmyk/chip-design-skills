from ..core.compute_block import compute_block


@compute_block("src", reads=[], writes=[("graph", "alpha"), ("graph", "beta")])
def src(projection):
    return {("graph", "alpha"): {"g": 1.0}, ("graph", "beta"): {"g": 2.0}}
