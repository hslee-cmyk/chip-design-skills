from .defs import f


def _row(x):
    return f(x)


def run_a(p):
    return _row(p.column("device", "dc_op"))
