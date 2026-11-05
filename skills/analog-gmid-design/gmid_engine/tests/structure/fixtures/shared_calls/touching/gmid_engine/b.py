from .defs import f, h


def run_b(p):
    f(p.column("device", "dc_op"))
    return h(p.column("device", "ss_dev"))
