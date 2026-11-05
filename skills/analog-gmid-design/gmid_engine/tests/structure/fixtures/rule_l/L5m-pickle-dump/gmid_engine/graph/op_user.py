import pickle


def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    pickle.dump(op.current, snapshot.fh)
    return snapshot
