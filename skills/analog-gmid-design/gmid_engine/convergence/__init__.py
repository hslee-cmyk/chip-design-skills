"""MOD8 convergence -- 사이징↔레이아웃 W_request 수렴 루프, LY7 실현 기하 재검증, 판정 축 재필터 (계획 N3.10 sizing_layout_convergence.py, N3.17 LY1~LY8, DEC-79·84·89,
설계 40 §3.9, 계약 CONTRACT.md).

공개 흐름: `front = find_front(sctx, starts)` -> `converge(sctx, pdk_decl, front.front)` -> `ConvergedFront.front`(판정 축 최종 front).
다른 패키지와 test 는 이 `__all__` 만 쓴다.
"""
from .convergence_values import (
    DROP_DOMINATED,
    DROP_FOLDED,
    DROP_NONCONVERGED,
    RELAX_NOT_AVAILABLE,
    RELAX_NOT_PLACED,
    RELAX_PLACED,
    STATUS_CONVERGED,
    STATUS_INFEASIBLE,
    STATUS_NONCONVERGENT,
    STATUS_UNPLACEABLE,
    STATUSES,
    ConvergedFront,
    ConvergedPoint,
    DroppedPoint,
    Iteration,
    JunctionChange,
    Placement,
    PlacedLayout,
    Relaxation,
)
from .admission import admit_candidates
from .alternation_bound import alternation_bound
from .converge import converge
from .converge_point import converge_point
from .effective_placement import effective_placement
from .junction_change import junction_change
from .key_exclusion import key_exclusion
from .layout_input import layout_input_of
from .place_layout import place_layout
from .realized_geometry import realized_geometry
from .refilter import refilter
from .relaxation import relaxation_decision
from .relaxation_records import relaxation_records
from .w_loop_bound import w_loop_bound

__all__ = (
    "ConvergedFront",
    "ConvergedPoint",
    "DROP_DOMINATED",
    "DROP_FOLDED",
    "DROP_NONCONVERGED",
    "DroppedPoint",
    "Iteration",
    "JunctionChange",
    "PlacedLayout",
    "Placement",
    "RELAX_NOT_AVAILABLE",
    "RELAX_NOT_PLACED",
    "RELAX_PLACED",
    "Relaxation",
    "STATUSES",
    "STATUS_CONVERGED",
    "STATUS_INFEASIBLE",
    "STATUS_NONCONVERGENT",
    "STATUS_UNPLACEABLE",
    "admit_candidates",
    "alternation_bound",
    "converge",
    "converge_point",
    "effective_placement",
    "junction_change",
    "key_exclusion",
    "layout_input_of",
    "place_layout",
    "realized_geometry",
    "refilter",
    "relaxation_decision",
    "relaxation_records",
    "w_loop_bound",
)
