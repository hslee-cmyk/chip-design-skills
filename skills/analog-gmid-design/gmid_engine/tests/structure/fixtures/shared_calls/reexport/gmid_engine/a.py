from gmid_engine.pkg import f


def run_a(p):
    return f(p.column("device", "dc_op"))
