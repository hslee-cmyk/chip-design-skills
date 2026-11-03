from gmid_engine.defs import f


def run_b(p):
    return f(p.column("device", "dc_op"))
