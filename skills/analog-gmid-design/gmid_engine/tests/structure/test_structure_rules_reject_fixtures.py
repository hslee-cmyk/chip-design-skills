"""검사기가 공허하지 않음을 보인다: 규칙마다 위반 픽스처(fixtures/<rule>/bad)를 실제로 거부하고
(기대 위반 목록과 정확히 같음), 허용 픽스처(fixtures/<rule>/good)는 통과시킨다.

기대 목록은 픽스처 소스의 줄을 손으로 읽어 적은 것이다(검사기 출력을 옮긴 것이 아니다).
픽스처는 패키지 밖 가짜 소스 트리라 import·수집되지 않는다(conftest.collect_ignore_glob,
fixtures/ 에 __init__.py 없음). 각 픽스처 파일의 위반 의도는 README '위반 픽스처' 표.
"""
from __future__ import annotations

import pytest


def _keys(violations):
    return sorted((v.kind, v.path, v.line) for v in violations)


EXPECTED_BAD = {
    "rule_a": [
        ("entry_points", "core/decorated_and_plain.py", 1),     # 변형군 1 + 일반 공개 함수 1 = 2
        ("entry_points", "core/mixed_signature_variants.py", 1),  # 같은 데코레이터, 시그니처 2종 = 2
        ("entry_points", "core/no_root.py", 1),                 # 공개 정의 0
        ("entry_points", "core/two_roots.py", 1),               # alpha, beta
    ],
    "rule_b": [
        ("private_attr", "core/b.py", 7),       # amod._secret()
        ("private_attr", "core/b.py", 8),       # gmid_engine.core.a._secret
        ("private_import", "core/b.py", 1),     # from .a import _secret
    ],
    "rule_c": [
        ("import_cycle", "core/cyc_a.py", 0),        # cyc_a <-> cyc_b
        ("import_form", "graph/build.py", 4),        # import gmid_engine.lut
        ("import_form", "graph/build.py", 5),        # from gmid_engine import lut
        ("layer_order", "lut/query.py", 1),          # lut(1) -> report(9)
        ("non_public_path", "graph/build.py", 1),    # from gmid_engine.lut.query import ...
        ("not_in_all", "graph/build.py", 2),         # table 은 lut.__all__ 밖
        ("not_in_all", "graph/build.py", 6),         # import *
        ("unknown_layer", "widgets", 0),             # 층 표 밖 하위 패키지
        ("unknown_layer", "widgets/thing.py", 1),    # 층 없는 패키지에서의 교차 import
    ],
    "rule_d": [
        ("numeric_literal", "core/numbers.py", 5),    # n=10
        ("numeric_literal", "core/numbers.py", 6),    # x == 2 (비교의 2)
        ("numeric_literal", "core/numbers.py", 7),    # 3
        ("numeric_literal", "core/numbers.py", 8),    # 0.5
        ("numeric_literal", "core/numbers.py", 10),   # -2
        ("numeric_literal", "core/numbers.py", 11),   # 1e-6, derive 함수 없음
        ("numeric_literal", "core/numbers.py", 13),   # 2j
        ("numeric_literal", "lut/table.py", 1),       # units.py 밖 단위 계수
    ],
    "rule_f": [
        ("broad_except", "core/errs.py", 7),          # except:
        ("broad_except", "core/errs.py", 11),         # except Exception
        ("broad_except", "core/errs.py", 15),         # (ValueError, BaseException)
        ("broad_except", "core/errs.py", 19),         # builtins.Exception
        ("broad_except", "pipeline/entry.py", 8),     # 진입점의 둘째 광범위 except
    ],
    "rule_g": [
        ("global_cache", "core/state.py", 19),        # @lru_cache(maxsize=None)
        ("global_cache", "core/state.py", 24),        # @functools.cache
        ("global_stmt", "core/state.py", 26),         # global CACHE
        ("module_mutable", "core/state.py", 5),       # {}
        ("module_mutable", "core/state.py", 6),       # TABLE: list = []
        ("module_mutable", "core/state.py", 7),       # set()
        ("module_mutable", "core/state.py", 8),       # defaultdict(list)
        ("module_mutable", "core/state.py", 9),       # dict comprehension
        ("module_mutable", "core/state.py", 10),      # tuple 안의 {}
        ("module_mutable", "core/state.py", 12),      # if 블록 안 []
        ("module_mutable", "core/state.py", 16),      # except 블록 안 dict()
    ],
    "rule_h": [
        ("missing_test", "core/y.py", 0),
        ("missing_test", "lut/q.py", 0),
        ("orphan_test", "tests/core/test_z.py", 0),
    ],
}

CHECKERS = {
    "rule_a": "check_a", "rule_b": "check_b", "rule_c": "check_c", "rule_d": "check_d",
    "rule_f": "check_f", "rule_g": "check_g", "rule_h": "check_h",
}


@pytest.mark.parametrize("rule", sorted(CHECKERS))
def test_rejects_bad_fixture(checks, fixture_tree, rule):
    n, v = getattr(checks, CHECKERS[rule])(fixture_tree(rule, "bad"))
    assert n > 0
    assert _keys(v) == sorted(EXPECTED_BAD[rule]), "\n".join(str(x) for x in v)


@pytest.mark.parametrize("rule", sorted(CHECKERS))
def test_accepts_good_fixture(checks, fixture_tree, rule):
    n, v = getattr(checks, CHECKERS[rule])(fixture_tree(rule, "good"))
    assert n > 0
    assert v == [], "\n".join(str(x) for x in v)


def test_rule_e_rejects_bad_fixture(checks, fixture_tree, library):
    _, names = library
    n, v = checks.check_e(fixture_tree("rule_e", "bad"), names)
    assert n > 0
    assert sorted((x.kind, x.path, x.line) for x in v) == [
        ("name_literal", "core/names.py", 2),    # "vdd"(레일)
        ("name_literal", "core/names.py", 3),    # "two_stage_ota"(회로)
        ("name_literal", "core/names.py", 4),    # f"gnd"(레일, f-string 조각)
        ("name_literal", "core/names.py", 5),    # "M1"(소자)
        ("name_literal", "core/names.py", 5),    # "vin_p"(넷·포트)
    ], "\n".join(str(x) for x in v)


def test_rule_e_accepts_good_fixture(checks, fixture_tree, library):
    _, names = library
    n, v = checks.check_e(fixture_tree("rule_e", "good"), names)
    assert n > 0
    assert v == [], "\n".join(str(x) for x in v)


def test_rule_e_name_set_covers_declared_kinds(library):
    """이름 집합에 회로·소자·넷·포트·레일·수동소자 출처가 모두 들어 있다(수집이 빠지면 E 가 공허해진다)."""
    circuits, names = library
    kinds = {o.split(":", 1)[1] for origins in names.values() for o in origins}
    assert {"file", "topology_name", "device", "net", "port", "supply_net", "passive_elements"} <= kinds, kinds
    for rail in ("vdd", "gnd", "vss", "agnd"):     # 설계 1.4 (나)가 예로 든 레일 이름
        assert rail in names, rail
    assert "two_stage_ota" in circuits
