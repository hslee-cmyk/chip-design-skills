def _late(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    snapshot.ctx.save(op.current)
    return snapshot


_X = _late(None)
