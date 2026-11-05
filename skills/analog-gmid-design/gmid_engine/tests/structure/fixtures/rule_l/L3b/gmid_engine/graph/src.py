from ..core.compute_block import compute_block


@compute_block(
    "src", reads=[], writes=[("graph", "alpha"), ("graph", "beta"), ("graph", "delta")]
)
def src(projection):
    return {
        ("graph", "alpha"): {"g": 1.0},
        ("graph", "beta"): {"g": 2.0},
        ("graph", "delta"): {"g": 3.0},
    }
