def inner(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    snapshot.ctx.save(op.current)
    return snapshot


def f(snapshot):
    return inner(snapshot)
