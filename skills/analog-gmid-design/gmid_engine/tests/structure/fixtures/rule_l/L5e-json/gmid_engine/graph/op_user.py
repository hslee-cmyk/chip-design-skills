import json


def f(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    return json.dumps({"i": op.current})
