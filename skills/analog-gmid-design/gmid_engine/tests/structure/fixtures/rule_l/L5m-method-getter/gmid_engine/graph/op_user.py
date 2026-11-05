class Row:
    def __init__(self, i):
        self.i = i

    def cur(self):
        return self.i


def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    v = Row(op.current).cur()
    return snapshot.write("lay", "iv", {("graph", "ly_point"): {"m1": v}})
