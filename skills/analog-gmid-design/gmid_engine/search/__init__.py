"""MOD6 search -- θ 탐색으로 (전력, 면적) 비지배 front (계획 N3.5·N3.7·DEC-54·77·79·80·95, 설계 design_mod6_search_front).
계약: `CONTRACT.md`. 다른 패키지와 test 는 이 `__all__` 만 쓴다.

공개 흐름: `build_search_context(dc_ctx, spec, settings, archive_root, pdk_decl, lut_rule_decl, *, code_fp)`(실행당 1회 -- S0 수준 블록, 디스크 저장 없음)
-> `find_front(sctx, given_starts)`.
봉인 7 이 VDSAT 접근자 부재로 미정인 동안 모든 점은 '봉인 7 대기'(`seal_status`)라 최종 front 는 비어 있다.
"""
from .archive import S3Archive
from .area_decl import passive_area_decl
from .cell_floor import ln_idu_floors
from .cone_rows import cone_rows
from .canonical_order import canonical_order
from .canonical_rows import canonical_row_key
from .constraint_classes import constraint_classes
from .constraints import constraint_rows
from .count_budget import count_budget
from .current_symmetry import CurrentSymmetry, current_symmetry
from .current_box import current_box
from .dominant_node import DominantNode, dominant_node
from .eval_budget import EvalBudget
from .eps_sweep import sweep_front
from .eval_key import eval_key
from .fd_jacobian import fd_jacobian
from .find_front import find_front
from .front_entries import read_front_entries
from .front_query import node_across_front
from .kernel import evaluate
from .l_bin_search import polish_l_cells
from .layer0_center import ROW_SEAL_ITEM, SOURCE_LAYER0, STAGE_LAYER0, Layer0Result, layer0_start
from .l_cells import l_cells
from .objectives import objective_values
from .open_run import open_run
from .noise_decl import noise_decl
from .orbit_ties import orbit_ties
from .pareto import nondominated
from .off_judged import check_off_judged_by
from .seal7_pending import seal_status
from .s0_fields import (
    CONSTRAINT_CLASSES_WRITER,
    DOF_NUMERIC_WRITER,
    NOISE_DECL_WRITER,
    PASSIVE_AREA_WRITER,
    RESIDUAL_PROBE_WRITER,
    S0_WRITERS,
    SEARCH_DOMAIN_WRITER,
    SEARCH_S0_WRITERS,
    STAGE_B_KEY,
    START_INTERVALS_WRITER,
    START_KEY,
    START_WRITES,
)
from .s3_index import S3Index
from .search_context import SearchContext, build_search_context
from .tie_expand import expand_ties
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
    ConstraintClasses,
    ConstraintRow,
    EvalKey,
    EvalResult,
    FrontPoint,
    NodeRow,
    Objectives,
    ParetoResult,
    RealizedGeometry,
    SearchDomain,
    SearchFront,
    SearchSettings,
    SolveResult,
    StartPoint,
    Variable,
)
from .search_ceiling import search_ceiling
from .search_stop import search_stop
from .slsqp_outer import solve_eps
from .ss_constraints import ss_constraint_rows
from .start_intervals import start_intervals
from .start_points import start_points
from .start_values import (
    Bound,
    MacroResult,
    StartConflict,
    StartRow,
    StartRung,
)
from .theta_coords import ThetaCoords

__all__ = (
    "ACCEPTED_STATUSES",
    "AXES",
    "AXIS_AREA",
    "AXIS_POWER",
    "Bound",
    "CON_CONE",
    "CON_EPS",
    "CON_INVERSION",
    "CON_SEAL6",
    "CON_WMIN",
    "CONSTRAINT_CLASSES_WRITER",
    "ConstraintClasses",
    "ConstraintRow",
    "DOF_NUMERIC_WRITER",
    "NOISE_DECL_WRITER",
    "PASSIVE_AREA_WRITER",
    "RESIDUAL_PROBE_WRITER",
    "S0_WRITERS",
    "SEARCH_DOMAIN_WRITER",
    "SEARCH_S0_WRITERS",
    "STAGE_B_KEY",
    "START_INTERVALS_WRITER",
    "START_KEY",
    "START_WRITES",
    "EvalKey",
    "EvalResult",
    "FrontPoint",
    "Layer0Result",
    "MacroResult",
    "NodeRow",
    "Objectives",
    "ParetoResult",
    "ROW_SEAL_ITEM",
    "RealizedGeometry",
    "S3Archive",
    "S3Index",
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
    "StartConflict",
    "StartPoint",
    "StartRow",
    "StartRung",
    "ThetaCoords",
    "Variable",
    "build_search_context",
    "canonical_order",
    "canonical_row_key",
    "CurrentSymmetry",
    "DominantNode",
    "EvalBudget",
    "cone_rows",
    "current_symmetry",
    "expand_ties",
    "orbit_ties",
    "passive_area_decl",
    "check_off_judged_by",
    "constraint_classes",
    "constraint_rows",
    "noise_decl",
    "count_budget",
    "dominant_node",
    "current_box",
    "eval_key",
    "evaluate",
    "fd_jacobian",
    "find_front",
    "l_cells",
    "layer0_start",
    "ln_idu_floors",
    "node_across_front",
    "read_front_entries",
    "nondominated",
    "objective_values",
    "open_run",
    "polish_l_cells",
    "search_ceiling",
    "search_domain",
    "search_stop",
    "seal_status",
    "solve_eps",
    "ss_constraint_rows",
    "start_intervals",
    "start_points",
    "sweep_front",
)
