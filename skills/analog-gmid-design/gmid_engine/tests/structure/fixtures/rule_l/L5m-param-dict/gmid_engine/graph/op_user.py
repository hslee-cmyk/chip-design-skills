def keep(cache, snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    cache["m1"] = op.current


def place(snapshot):
    keep({}, snapshot)
    return snapshot
