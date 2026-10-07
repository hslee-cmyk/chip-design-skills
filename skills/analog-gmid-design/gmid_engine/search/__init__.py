"""MOD6 search -- θ 탐색으로 (전력, 면적) 비지배 front (계획 N3.5·N3.7·DEC-54·77·79·80·95, 설계 design_mod6_search_front).
계약: `CONTRACT.md`. 다른 패키지와 test 는 이 `__all__` 만 쓴다.

공개 흐름: `build_search_context(dc_ctx, spec, settings, archive_root)`(S0 당 1회) -> `find_front(sctx, given_starts)`.
봉인 7 이 VDSAT 접근자 부재로 미정인 동안 모든 점은 '봉인 7 대기'(`seal_status`)라 최종 front 는 비어 있다.
"""
from .archive import S3Archive
from .cell_floor import ln_idu_floors
from .cone_rows import cone_rows
from .constraints import constraint_rows
from .current_box import current_box
from .eps_sweep import sweep_front
from .eval_key import eval_key
from .fd_jacobian import fd_jacobian
from .find_front import find_front
from .front_query import node_across_front
from .kernel import evaluate
from .l_bin_search import polish_l_cells
from .layer0_center import ROW_SEAL_ITEM, SOURCE_LAYER0, STAGE_LAYER0, Layer0Result, layer0_start
from .l_cells import l_cells
from .objectives import objective_values
from .pareto import nondominated
from .seal7_pending import seal_status
from .search_context import SearchContext, build_search_context
from .search_domain import search_domain
from .search_values import (
    ACCEPTED_STATUSES,
    AXES,
    AXIS_AREA,
    AXIS_POWER,
    CON_CONE,
    CON_EPS,
    CON_INVERSION,
    CON_SEAL6,
    CON_WMIN,
    STAGE_FD,
    STAGE_L_SEARCH,
    STAGE_SLSQP,
    STAGE_START,
    STATUS_FAILED,
    STATUS_OUTSIDE_DOMAIN,
    STATUS_PENDING_SEAL7,
    STATUS_SEALED,
    STATUS_UNDEFINED,
    ConstraintRow,
    EvalKey,
    EvalResult,
    FrontPoint,
    NodeRow,
    Objectives,
    ParetoResult,
    SearchDomain,
    SearchFront,
    SearchSettings,
    SolveResult,
    StartPoint,
    Variable,
)
from .slsqp_outer import solve_eps
from .ss_constraints import ss_constraint_rows
from .start_points import start_points

__all__ = (
    "ACCEPTED_STATUSES",
    "AXES",
    "AXIS_AREA",
    "AXIS_POWER",
    "CON_CONE",
    "CON_EPS",
    "CON_INVERSION",
    "CON_SEAL6",
    "CON_WMIN",
    "ConstraintRow",
    "EvalKey",
    "EvalResult",
    "FrontPoint",
    "Layer0Result",
    "NodeRow",
    "Objectives",
    "ParetoResult",
    "ROW_SEAL_ITEM",
    "S3Archive",
    "SOURCE_LAYER0",
    "STAGE_FD",
    "STAGE_LAYER0",
    "STAGE_L_SEARCH",
    "STAGE_SLSQP",
    "STAGE_START",
    "STATUS_FAILED",
    "STATUS_OUTSIDE_DOMAIN",
    "STATUS_PENDING_SEAL7",
    "STATUS_SEALED",
    "STATUS_UNDEFINED",
    "SearchContext",
    "SearchDomain",
    "SearchFront",
    "SearchSettings",
    "SolveResult",
    "StartPoint",
    "Variable",
    "build_search_context",
    "cone_rows",
    "constraint_rows",
    "current_box",
    "eval_key",
    "evaluate",
    "fd_jacobian",
    "find_front",
    "l_cells",
    "layer0_start",
    "ln_idu_floors",
    "node_across_front",
    "nondominated",
    "objective_values",
    "polish_l_cells",
    "search_domain",
    "seal_status",
    "solve_eps",
    "ss_constraint_rows",
    "start_points",
    "sweep_front",
)
