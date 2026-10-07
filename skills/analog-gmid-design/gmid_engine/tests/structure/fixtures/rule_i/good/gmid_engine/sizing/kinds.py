COMMENT_PREFIX = "_"


def classify(doc, dev, port, other, rails):
    if dev.kind == "nmos" and port.direction == "input":
        return dev.name == other.name
    if dev.s in rails or dev.name in doc.ports:
        return dev.name.startswith(COMMENT_PREFIX)
    if dev.name == "":
        return None
    return {"nmos": 1, "pmos": -1}[dev.kind], doc.devices
