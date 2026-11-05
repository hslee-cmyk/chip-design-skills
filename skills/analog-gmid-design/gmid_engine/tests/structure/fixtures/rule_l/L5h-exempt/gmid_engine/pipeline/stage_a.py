from ..graph.op_block import op_block
from ..graph.op_user import _report, probe


def run_stage_a(snapshot):
    snapshot = op_block(snapshot)
    report = _report(snapshot)
    return probe(snapshot), snapshot.write("rep", "iv", {("graph", "rep"): report})
