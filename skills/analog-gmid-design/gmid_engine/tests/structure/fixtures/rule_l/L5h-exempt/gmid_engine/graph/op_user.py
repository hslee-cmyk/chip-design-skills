def probe(snapshot):
    return snapshot.value("device", "m1", "dc_op").current * 2.0


def _report(snapshot):
    op = snapshot.value("device", "m1", "dc_op")
    return snapshot.write("rep", "iv", {("graph", "rep"): {"i": op.current}})
