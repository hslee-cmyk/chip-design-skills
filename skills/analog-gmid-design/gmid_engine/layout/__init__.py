"""MOD7 layout -- 레이아웃 계약·W 허용오차·패턴·행 구성(계획 N3.10 stick_diagram.py, N3.17 LY1~LY7).

공개 API: 입력 계약(`LayoutInput`·`LayoutDevice`·`MatchingGroup`·`RowGroup`·`LayoutPdk`, role·패턴 이름 상수), 출력 계약(`LayoutResult` =
설계점 스냅샷 하나, 설계 40 v1.6 §2.4.7), 진입점 `run_layout`, 소비자가 설계점 스냅샷에서 읽는 레이아웃 필드 이름(graph 레코드 key
`LAYOUT_KEY`, `F_POINT`·`F_GROUPS_IN`·`F_GROUPS`·`F_FINGER`·`F_FLOORPLAN`·`F_DIFFUSION`), 필드 파생 출력 `layout_outputs`(`LayoutOutputs`), [U14] MOD8 이 쓰는 `area_tie_m2`(ΔA_tie)·`passives_from_decl`(수동소자 면적 입력). 옛 stick_diagram.py 정의 본문 복사(AST 해시 = `_copy_manifest.py`)는 `run_layout` 의 계산 블록이
부른다. 계약: CONTRACT.md.
"""

from .area_tie import area_tie_m2
from .contract_input import (
    CC_REQUIRED_ROLES,
    EXCLUDED_ROLES,
    PATTERN_COMMON_CENTROID,
    PATTERN_INTERDIGITATION,
    PATTERNS,
    ROLE_BIAS_DISTRIBUTION,
    ROLE_BRANCH_SYMMETRIC,
    ROLE_DIFF_PAIR,
    ROLE_FEEDBACK_SHARED,
    ROLE_MIRROR,
    LayoutDevice,
    LayoutInput,
    LayoutPdk,
    MatchingGroup,
    RowGroup,
)
from ._ly_fields import F_DIFFUSION, F_FINGER, F_FLOORPLAN, F_GROUPS, F_GROUPS_IN, F_POINT
from ._ly_fields import GRAPH_KEY as LAYOUT_KEY
from .contract_output import LayoutOutputs, LayoutResult
from .outputs import layout_outputs
from .passives import passives_from_decl
from .run import run_layout

__all__ = (
    "CC_REQUIRED_ROLES",
    "EXCLUDED_ROLES",
    "F_DIFFUSION",
    "F_FINGER",
    "F_FLOORPLAN",
    "F_GROUPS",
    "F_GROUPS_IN",
    "F_POINT",
    "LAYOUT_KEY",
    "LayoutDevice",
    "LayoutInput",
    "LayoutOutputs",
    "LayoutPdk",
    "LayoutResult",
    "MatchingGroup",
    "PATTERNS",
    "PATTERN_COMMON_CENTROID",
    "PATTERN_INTERDIGITATION",
    "ROLE_BIAS_DISTRIBUTION",
    "ROLE_BRANCH_SYMMETRIC",
    "ROLE_DIFF_PAIR",
    "ROLE_FEEDBACK_SHARED",
    "ROLE_MIRROR",
    "RowGroup",
    "area_tie_m2",
    "layout_outputs",
    "passives_from_decl",
    "run_layout",
)
