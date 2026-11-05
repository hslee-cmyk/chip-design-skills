from ..graph.op_block import op_block
from ..graph.op_user import _report, probe


def run_stage_a(snapshot):
    snapshot = op_block(snapshot)
    return probe(snapshot), _report(snapshot)
