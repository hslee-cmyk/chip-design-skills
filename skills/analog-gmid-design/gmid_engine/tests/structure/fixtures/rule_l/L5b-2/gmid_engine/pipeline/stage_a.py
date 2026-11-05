from ..graph.op_block import op_block
from ..graph.op_user import lay


def run_stage_a(snapshot):
    snapshot = lay(op_block(snapshot))
    return snapshot.column("graph", "ly_point")
