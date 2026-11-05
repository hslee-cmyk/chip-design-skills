import dataclasses


@dataclasses.dataclass(frozen=True)
class B:
    a: float


@dataclasses.dataclass(frozen=True)
class Row(B):
    b: float


def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    v = Row(op.current, 1.0).a
    return snapshot.write("lay", "iv", {("graph", "ly_point"): {"m1": v}})
