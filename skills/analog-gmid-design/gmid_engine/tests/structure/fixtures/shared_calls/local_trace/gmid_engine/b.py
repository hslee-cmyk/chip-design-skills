from .defs import f


def run_b(p):
    return f(p.column("device", "dc_op"))
