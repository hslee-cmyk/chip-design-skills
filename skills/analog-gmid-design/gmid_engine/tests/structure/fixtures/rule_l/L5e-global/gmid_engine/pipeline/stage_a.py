from ..graph.op_block import op_block
from ..graph.op_user import f


def run_stage_a(snapshot):
    return f(op_block(snapshot))
