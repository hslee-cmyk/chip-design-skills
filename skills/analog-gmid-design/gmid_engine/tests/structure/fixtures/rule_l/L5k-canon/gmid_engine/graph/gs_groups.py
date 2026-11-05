from ..core.compute_block import compute_block


@compute_block("gs_groups", reads=[], writes=[("graph", "gs_groups")])
def gs_groups(projection):
    return {("graph", "gs_groups"): {"k": 1.0}}
