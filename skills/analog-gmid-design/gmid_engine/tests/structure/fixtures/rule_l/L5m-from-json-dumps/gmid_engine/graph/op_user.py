from json import dumps


def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    return dumps({"i": op.current})
