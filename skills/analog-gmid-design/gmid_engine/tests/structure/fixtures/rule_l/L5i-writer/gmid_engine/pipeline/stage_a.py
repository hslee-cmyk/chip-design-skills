from ..graph.op_block import op_block


def run_stage_a(snapshot):
    snapshot = op_block(snapshot)
    return snapshot.value("device", "m1", "dc_op")
