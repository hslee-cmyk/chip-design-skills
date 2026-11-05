def f(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    return snapshot.write("lay", "iv", {("graph", "ly_point"): {"m1": float(op.current)}})
