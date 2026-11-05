def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    snapshot.ctx.cache["m1"] = op.current
    return snapshot
