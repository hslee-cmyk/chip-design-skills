def f(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    holder = snapshot
    holder.cur = op.current
    return holder
