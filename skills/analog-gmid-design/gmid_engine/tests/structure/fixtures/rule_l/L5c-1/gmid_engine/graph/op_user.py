class _Tmp:
    def __init__(self, i):
        self.i = i


def probe(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    tmp = _Tmp(i=op.current)
    return tmp.i * 2.0
