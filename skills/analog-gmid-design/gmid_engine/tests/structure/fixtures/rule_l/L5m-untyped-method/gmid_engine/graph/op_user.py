def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    holder = snapshot.items
    k = holder.index(op.current)
    v = k
    return snapshot.write("lay", "iv", {("graph", "ly_point"): {"m1": v}})
