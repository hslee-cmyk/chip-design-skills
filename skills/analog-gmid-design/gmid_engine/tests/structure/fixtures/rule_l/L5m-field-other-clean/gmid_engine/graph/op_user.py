class Row:
    def __init__(self, i, n):
        self.i = i
        self.n = n


def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    v = Row(op.current, 1.0).n
    return snapshot.write("lay", "iv", {("graph", "ly_point"): {"m1": v}})
