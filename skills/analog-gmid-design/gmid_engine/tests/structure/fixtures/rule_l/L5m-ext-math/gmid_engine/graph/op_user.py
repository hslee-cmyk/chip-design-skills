import math


def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    v = math.log(op.current)
    return snapshot.write("lay", "iv", {("graph", "ly_point"): {"m1": v}})
