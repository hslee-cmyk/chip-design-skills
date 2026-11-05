def beta_len(projection):
    return _inner(projection)


def _inner(projection):
    return len(projection.column("graph", "beta"))
