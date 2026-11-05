def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    snapshot.ctx.rows.update({"m1": op.current})
    return snapshot
