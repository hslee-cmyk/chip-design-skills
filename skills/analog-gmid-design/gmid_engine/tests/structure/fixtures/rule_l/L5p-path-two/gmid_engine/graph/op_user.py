class Row:
    def __init__(self, current, n):
        self.current = current
        self.n = n


def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    row = Row(op.current, 2.0)
    snapshot.write("lay", "i2", {("graph", "ly_i"): {"m1": op.current}})
    return snapshot.write("lay", "iv", {("graph", "ly_point"): {"m1": row}})
