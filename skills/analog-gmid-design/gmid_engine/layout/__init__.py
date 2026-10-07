"""MOD7 layout -- 레이아웃 계약·W 허용오차·패턴·행 구성(계획 N3.10 stick_diagram.py, N3.17 LY1~LY7).

공개 API: 입력 계약(`LayoutInput`·`LayoutDevice`·`MatchingGroup`·`RowGroup`·`LayoutPdk`), 출력 계약(`LayoutResult`),
진입점 `run_layout`. 옛 stick_diagram.py 정의 본문 복사(AST 해시 = `_copy_manifest.py`)는 `run_layout` 의 계산 블록이
부른다. 계약: CONTRACT.md.
"""

from .contract_input import LayoutDevice, LayoutInput, LayoutPdk, MatchingGroup, RowGroup
from .contract_output import LayoutResult
from .run import run_layout

__all__ = (
    "LayoutDevice",
    "LayoutInput",
    "LayoutPdk",
    "LayoutResult",
    "MatchingGroup",
    "RowGroup",
    "run_layout",
)
