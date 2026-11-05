_CACHE = {}


def f(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    _CACHE["i"] = op.current
    return snapshot
