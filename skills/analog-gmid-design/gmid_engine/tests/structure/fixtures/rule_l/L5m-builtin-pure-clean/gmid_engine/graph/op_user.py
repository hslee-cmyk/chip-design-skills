def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    n = len([op.current])
    v = (n, round(abs(op.current), 3))
    return snapshot.write("lay", "iv", {("graph", "ly_point"): {"m1": v}})
