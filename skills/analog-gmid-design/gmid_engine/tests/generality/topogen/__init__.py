"""합성 topology 생성기·변형기 (tests/generality 공용, 엔진을 import 하지 않는 순수 dict 조작).

test 는 이 `__all__` 만 쓴다. 파일마다 진입점 1개(규칙 A), 다른 파일의 `_` 이름 import 없음(규칙 B) --
test_generator_sanity 가 구조 검사기로 확인한다. 목록과 확장 방법은 ../README.md.
"""
from .circuits import synthetic_topologies
from .duplicate import duplicate_stage
from .inject import KINDS as VIOLATION_KINDS
from .inject import inject_violation
from .polarity import flip_polarity
from .random_renaming import random_renaming
from .rename import rename
from .shuffle import shuffle_order
from .spec_rename import rename_spec
from .spec_template import synthetic_spec
from .tag_noise import add_tag_noise

__all__ = (
    "VIOLATION_KINDS",
    "add_tag_noise",
    "duplicate_stage",
    "flip_polarity",
    "inject_violation",
    "random_renaming",
    "rename",
    "rename_spec",
    "shuffle_order",
    "synthetic_spec",
    "synthetic_topologies",
)
