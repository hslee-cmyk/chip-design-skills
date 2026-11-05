class A:
    def __init__(self, x):
        self.x = x


def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    v = A(A(A(A(op.current))))
    return snapshot.write("lay", "iv", {("graph", "ly_point"): {"m1": v}})
