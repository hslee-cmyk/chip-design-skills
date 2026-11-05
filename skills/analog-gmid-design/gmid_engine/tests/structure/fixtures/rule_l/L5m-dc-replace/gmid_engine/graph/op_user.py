import dataclasses


def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    v = dataclasses.replace(snapshot.row, i=op.current)
    return snapshot.write("lay", "iv", {("graph", "ly_point"): {"m1": v}})
