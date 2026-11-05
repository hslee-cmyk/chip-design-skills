import copy


def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    v = copy.copy(op)
    return snapshot.write("lay", "iv", {("graph", "ly_point"): {"m1": v}})
