class Row:
    def __init__(self, i):
        self.current = i


def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    v = Row(op.current).current
    return snapshot.write("lay", "iv", {("graph", "ly_point"): {"m1": v}})
