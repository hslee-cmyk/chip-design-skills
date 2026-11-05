from ..core.compute_block import compute_block


@compute_block("gs_groups", reads=[], writes=[("graph", "gs_groups")])
def gs_groups(projection):
    simple = {}
    n, g, s = "a", "g1", "s1"
    simple.setdefault(tuple(sorted((g, s))), n)
    return {("graph", "gs_groups"): simple}
