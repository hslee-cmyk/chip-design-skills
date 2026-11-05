def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    rows = []
    rows.append(op.current)
    v = sum(rows)
    return snapshot.write("lay", "iv", {("graph", "ly_point"): {"m1": v}})
