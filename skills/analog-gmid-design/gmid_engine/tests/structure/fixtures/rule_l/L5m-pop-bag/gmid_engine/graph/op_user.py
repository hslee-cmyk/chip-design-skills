def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    bag = {"i": op.current}
    v = bag.pop("i")
    return snapshot.write("lay", "iv", {("graph", "ly_point"): {"m1": v}})
