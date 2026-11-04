from .defs import f


def run_a(p):
    v = p.column("device", "dc_op")
    return f(v)
