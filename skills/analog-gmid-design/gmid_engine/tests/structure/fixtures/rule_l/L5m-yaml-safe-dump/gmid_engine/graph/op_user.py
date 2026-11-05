import yaml


def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    return yaml.safe_dump({"i": op.current})
