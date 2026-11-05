class Arc:
    def append_eval(self, rec):
        with open("x", "a") as fh:
            fh.write(repr(rec))


def place(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    snapshot.arc.append_eval({"i": op.current})
    return snapshot
