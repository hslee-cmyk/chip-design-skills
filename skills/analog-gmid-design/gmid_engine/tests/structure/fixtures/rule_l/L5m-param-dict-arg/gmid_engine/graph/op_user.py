def keep(cache, v):
    cache["m1"] = v


def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    cache = {}
    keep(cache, op.current)
    return snapshot
