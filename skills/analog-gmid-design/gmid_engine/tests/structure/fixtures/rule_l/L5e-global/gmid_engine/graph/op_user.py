_LAST = None


def f(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    global _LAST
    _LAST = op.current
    return snapshot
