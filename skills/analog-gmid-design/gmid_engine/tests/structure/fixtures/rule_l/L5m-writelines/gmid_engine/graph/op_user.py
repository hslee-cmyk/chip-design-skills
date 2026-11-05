def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    snapshot.fh.writelines([str(op.current)])
    return snapshot
