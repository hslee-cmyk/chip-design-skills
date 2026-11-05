def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    xs = [1.0]
    k = xs.index(op.current)
    t = "abc".startswith(str(op.current))
    v = (k, t)
    return snapshot.write("lay", "iv", {("graph", "ly_point"): {"m1": v}})
