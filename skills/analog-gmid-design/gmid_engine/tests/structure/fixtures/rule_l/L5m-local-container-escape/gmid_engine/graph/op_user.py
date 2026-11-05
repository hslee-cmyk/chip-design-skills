def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    rows = []
    rows.append(op.current)
    snapshot.ctx.keep(rows)
    return snapshot
