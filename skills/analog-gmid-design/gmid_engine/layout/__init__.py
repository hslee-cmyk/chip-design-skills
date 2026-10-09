"""MOD7 layout -- 레이아웃 계약·W 허용오차·패턴·행 구성(계획 N3.10 stick_diagram.py, N3.17 LY1~LY7).

공개 API: 입력 계약(`LayoutInput`·`LayoutDevice`·`MatchingGroup`·`RowGroup`·`LayoutPdk`, role·패턴 이름 상수), 출력 계약(`LayoutResult`),
진입점 `run_layout`, [U14] MOD8 이 쓰는 `area_tie_m2`(ΔA_tie)·`passives_from_decl`(수동소자 면적 입력). 옛 stick_diagram.py 정의 본문 복사(AST 해시 = `_copy_manifest.py`)는 `run_layout` 의 계산 블록이
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
from .contract_output import LayoutResult
from .passives import passives_from_decl
from .run import run_layout

__all__ = (
    "CC_REQUIRED_ROLES",
    "EXCLUDED_ROLES",
    "LayoutDevice",
    "LayoutInput",
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
    "passives_from_decl",
    "run_layout",
)
