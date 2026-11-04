from .defs import f


def run_a(p):
    f(p.column("device", "dc_op"))
    return f(p.column("device", "dc_op"))
