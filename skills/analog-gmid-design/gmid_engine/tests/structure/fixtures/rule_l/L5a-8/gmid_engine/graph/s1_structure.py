from ..core.compute_block import compute_block


@compute_block("s1_structure", reads=[], writes=[("device", "is_diode")])
def s1_structure(projection):
    pins = {"m1": {"g": "n1", "d": "n1"}}
    return {("device", "is_diode"): {k: v["g"] == v["d"] for k, v in pins.items()}}
