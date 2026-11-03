from .defs import h


def run_c(p):
    return h(p.column("device", "dc_op"))
