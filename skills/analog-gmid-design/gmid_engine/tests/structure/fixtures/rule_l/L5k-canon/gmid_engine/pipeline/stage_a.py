from ..graph.gs_groups import gs_groups
from ..graph.s1_structure import s1_structure
from ..graph.user import check, edges

_ARGS = ()


def run_stage_a(snapshot):
    snapshot = gs_groups(s1_structure(snapshot))
    rows = (snapshot.column("device", "is_diode"), snapshot.column("graph", "gs_groups"))
    return check(*_ARGS), edges(*_ARGS), rows
