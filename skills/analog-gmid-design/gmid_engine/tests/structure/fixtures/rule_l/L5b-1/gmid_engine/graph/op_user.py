class Row:
    def __init__(self, current):
        self.current = current


def _row(snapshot, key):
    op = snapshot.value("device", key, "dc_op")
    return Row(current=op.current)


def place(snapshot):
    row = _row(snapshot, "m1")
    return snapshot.write("lay", "iv", {("graph", "ly_point"): {"m1": row}})
