import numpy as np


def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    np.save("x.npy", op.current)
    return snapshot
