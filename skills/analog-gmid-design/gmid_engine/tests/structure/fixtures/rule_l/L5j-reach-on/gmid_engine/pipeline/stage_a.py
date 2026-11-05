from ..graph.op_block import op_block
from ..graph.tail import _late


def run_stage_a(snapshot):
    snapshot = op_block(snapshot)
    return _late(snapshot)
