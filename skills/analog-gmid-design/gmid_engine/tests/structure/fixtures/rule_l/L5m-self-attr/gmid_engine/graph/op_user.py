class _K:
    def keep(self, snapshot):
        op = snapshot.value("device", "m1", "dc_op")
        self.v = op.current


def place(snapshot):
    return _K().keep(snapshot)
