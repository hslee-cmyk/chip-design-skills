from ..graph.op_block import op_block
from ..graph.op_user import place


def run_stage_a(snapshot):
    return place(op_block(snapshot))
