def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    snapshot.ctx.rows.append(op.current)
    return snapshot
