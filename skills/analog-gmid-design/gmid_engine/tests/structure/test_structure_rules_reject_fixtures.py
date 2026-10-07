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
        ("entry_points", "core/two_roots.py", 1),               # alpha, beta
        ("entry_points", "core/failures_like.py", 1),           # 예외 + 공개 함수 2 -> 데이터 모듈 아님, 진입점 3
        ("entry_points", "core/schema_with_method.py", 1),      # dataclass 에 일반 메서드 -> 데이터 모듈 아님, 진입점 2
        ("helper_single_user", "core/_helpers_lonely.py", 1),   # shared: user_one.py 하나만 사용
        ("helper_single_user", "core/_helpers_lonely.py", 5),   # unused: 사용 0
        ("helper_single_user", "core/_helpers_alias.py", 5),    # 별칭 impl = _impl: user_one.py 하나만 사용
        ("helper_single_user", "core/_helpers_alias.py", 6),    # 별칭 spare = _impl: 사용 0
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
        ("missing_test", "core/_helpers_h.py", 0),   # _ 모듈이라도 함수가 있으면 H 대상
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

# 복사 등록부(D·E·G 예외). bad 트리: graph(유효 2 + 본문 바뀐 복사 + 리터럴 목록 오기 + 없는 정의),
# lut(가짜 등록부 -- 새 코드에 자기 해시를 단 항목 + 패키지 밖 경로), metrics(원본 = 엔진 안 자기 자신),
# search(짧은 항목 + 중복 항목), sizing(정적 tuple 아닌 표), 루트 등록부. 원본 = bad/legacy/old.py.
EXPECTED_COPY_BAD = {
    "check_copy_manifest": [
        ("copy_definition_changed", "graph/changed.py", 4),         # renamed: total->acc (해시 다름)
        ("copy_literal_mismatch", "graph/miscount.py", 4),          # 실제 ['12'], 등록 ()
        ("copy_manifest_duplicate", "search/_copy_manifest.py", 8),  # 같은 (파일, 이름) 두 번
        ("copy_manifest_format", "lut/_copy_manifest.py", 7),       # ../graph/copied.py
        ("copy_manifest_format", "search/_copy_manifest.py", 6),    # 2칸 항목
        ("copy_manifest_format", "sizing/_copy_manifest.py", 5),    # tuple(e for e in ())
        ("copy_manifest_location", "_copy_manifest.py", 0),         # 엔진 루트 등록부
        ("copy_missing_definition", "graph/_copy_manifest.py", 10),  # gone 없음
    ],
    "check_copy_source": [
        ("copy_source_in_engine", "metrics/_copy_manifest.py", 3),  # 원본이 엔진 안 복사본 자신
        ("copy_source_mismatch", "graph/_copy_manifest.py", 10),    # old.py 4~5 는 helper
        ("copy_source_mismatch", "lut/_copy_manifest.py", 6),       # invented 는 원본에 없음
    ],
    "check_d": [                                                    # 등록 안 됨 또는 면제 취소된 정의의 리터럴만
        ("numeric_literal", "graph/changed.py", 7),                 # 5 (해시 다름 -> 면제 취소)
        ("numeric_literal", "graph/copied.py", 13),                 # 7 (같은 파일의 미등록 extra)
        ("numeric_literal", "graph/miscount.py", 5),                # 12 (리터럴 목록 다름 -> 면제 취소)
        ("numeric_literal", "lut/fake.py", 5),                      # 99 (원본 대조 실패)
        ("numeric_literal", "metrics/self_source.py", 5),           # 9 (원본이 엔진 안)
        ("numeric_literal", "search/broken.py", 5),                 # 77 (형식·중복)
        ("numeric_literal", "sizing/loose.py", 5),                  # 66 (표 형식)
    ],
    "check_g": [
        ("module_mutable", "graph/copied.py", 16),                  # 미등록 CACHE = {} (등록 LIMITS 는 면제)
    ],
}


@pytest.mark.parametrize("checker", sorted(EXPECTED_COPY_BAD))
def test_copy_manifest_rejects_bad_fixture(checks, fixture_tree, checker):
    n, v = getattr(checks, checker)(fixture_tree("rule_copy", "bad"))
    assert n > 0
    assert _keys(v) == sorted(EXPECTED_COPY_BAD[checker]), "\n".join(str(x) for x in v)


def test_copy_manifest_rule_e_bad_fixture(checks, fixture_tree, library):
    _, names = library
    n, v = checks.check_e(fixture_tree("rule_copy", "bad"), names)
    assert n > 0
    assert _keys(v) == [("name_literal", "graph/copied.py", 13)], "\n".join(str(x) for x in v)   # 미등록 extra 의 "B"


@pytest.mark.parametrize("checker", sorted(EXPECTED_COPY_BAD))
def test_copy_manifest_accepts_good_fixture(checks, fixture_tree, checker):
    """good 트리의 등록 정의는 규칙 D 밖 리터럴(3, 4, 40)·넷 이름("A", "B")·모듈 수준 dict 를 담는다 --
    면제가 없으면 D·E·G 가 FAIL 하므로 이 통과가 면제 동작의 증거다."""
    n, v = getattr(checks, checker)(fixture_tree("rule_copy", "good"))
    assert n > 0
    assert v == [], "\n".join(str(x) for x in v)


def test_copy_manifest_rule_e_good_fixture(checks, fixture_tree, library):
    _, names = library
    n, v = checks.check_e(fixture_tree("rule_copy", "good"), names)
    assert n > 0
    assert v == [], "\n".join(str(x) for x in v)


def test_copy_manifest_good_fixture_needs_exemption(checks, fixture_tree):
    """면제 대상 판정이 공허하지 않다: good 트리의 등록 정의 3개가 모두 면제되고, 그 정의 안에 실제로 D·E·G 대상이 있다."""
    root = fixture_tree("rule_copy", "good")
    audit = checks.copy_audit(root)
    assert audit.exempt == {"graph/copied.py": frozenset({"LIMITS", "scan"}), "lut/helper_copy.py": frozenset({"helper"})}
    assert audit.compared == audit.entries == 3
