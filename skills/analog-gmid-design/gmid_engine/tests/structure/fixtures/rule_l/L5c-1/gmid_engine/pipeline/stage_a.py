from ..graph.op_block import op_block
from ..graph.op_user import probe


def run_stage_a(snapshot):
    return probe(op_block(snapshot))
