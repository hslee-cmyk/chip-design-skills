def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    snapshot.write("lay", "i2", {("graph", "ly_i"): {"m1": op.current}})
    snapshot.ctx.saved = op
    return snapshot.write("lay", "iv", {("graph", "ly_point"): {"m1": 1.0}})
