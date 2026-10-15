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
    "rule_i": [                                      # 이름 집합 없이 부른 경우(library 이름 리터럴도 (b)가 잡음)
        ("name_branch", "search/branch.py", 2),       # doc.name == "folded_mirror_amp"
        ("name_branch", "search/branch.py", 4),       # dev.s in ("rail_core", "rail_io")
        ("name_branch", "search/branch.py", 6),       # doc.name.startswith("telescopic")
        ("name_branch", "search/branch.py", 8),       # match port.net: case "outp" | "outn"
        ("name_branch", "search/branch.py", 11),      # {"cascode_amp": 5}.get(doc.topology_name)
        ("name_branch", "search/lib_name.py", 2),     # doc.name == "two_stage_ota"(library 이름 -- 이름 집합을 주면 E 몫)
        ("tag_key_lookup", "authoring/topology_schema.py", 3),  # 예외 파일이라도 허용 키(topology_name) 밖
        ("tag_key_lookup", "report/summary.py", 2),   # report/ 예외는 topology_name 만 -- fold_group 은 위반
        ("tag_key_lookup", "search/branch.py", 11),   # doc.topology_name(예외 밖 파일)
        ("tag_key_lookup", "sizing/roles.py", 2),     # doc["device_roles"]
        ("tag_key_lookup", "sizing/roles.py", 3),     # roles.get("fold_group")
        ("tag_key_lookup", "sizing/roles.py", 4),     # "headroom_role" in roles
        ("tag_key_lookup", "sizing/roles.py", 5),     # getattr(dev, "L_role")
        ("tag_key_lookup", "sizing/roles.py", 7),     # case {"gm_id_role": value}
        ("tag_key_lookup", "sizing/roles.py", 9),     # dev.vertical_stack_id
    ],
    "rule_k": [                                       # 허용 파일(search/__init__·front_query)은 bad 트리에도 있으나 위반 0
        ("front_query_module", "convergence/peek.py", 1),     # from gmid_engine.search.front_query import ... (K-b)
        ("front_query_module", "layout/view.py", 1),          # import gmid_engine.search.front_entries as fe (K-b)
        ("front_query_module", "search/kernel.py", 7),        # from . import front_query (K-b, 모듈 객체)
        ("front_query_module", "search/start_points.py", 1),  # from .front_entries import ... (K-b)
        ("front_query_name", "layout/view.py", 5),            # search.read_front_entries(d) (K-a, 속성)
        ("front_query_name", "pipeline/run.py", 1),           # from gmid_engine.search import node_across_front (K-a)
        ("front_query_name", "pipeline/run.py", 5),           # node_across_front(front, node) (K-a, 이름)
        ("front_query_name", "report/table.py", 1),           # import node_across_front as across (K-a, 별칭 원 이름)
        ("front_query_name", "search/start_points.py", 1),    # import 이름 read_front_entries (K-a)
        ("front_query_name", "search/start_points.py", 5),    # read_front_entries(run_dir) (K-a, 이름)
        ("snapshot_read", "convergence/peek.py", 1),          # import 이름 _read_snapshot_file (K-c)
        ("snapshot_read", "search/kernel.py", 2),             # reader = sctx.archive.read_snapshot (K-c, 호출 아닌 참조)
        ("snapshot_read", "search/kernel.py", 8),             # front_query._read_snapshot_file(path) (K-c, 속성)
    ],
}

CHECKERS = {
    "rule_a": "check_a", "rule_b": "check_b", "rule_c": "check_c", "rule_d": "check_d",
    "rule_f": "check_f", "rule_g": "check_g", "rule_h": "check_h", "rule_i": "check_i",
}
# 규칙 K 는 위 매개변수 test 대신 이름에 `rule_k_` 접두가 붙은 아래 두 test 로 건다(`-k rule_k_` 선택, 식별자 충돌 회피 -- README K 행).


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


def test_rule_k_rejects_bad_fixture(checks, fixture_tree):
    """규칙 K(설계 40 v1.10 §2.4.3 'front 조회 전용 읽기 경로' 검사 행): K-a·K-b·K-c 를 하나 이상씩 담은 bad 트리를 기대 목록과 정확히
    같게 거부한다. bad 트리에 있는 허용 파일(search/__init__.py 재수출, search/front_query.py 의 정의·_read_snapshot_file 사용)은 대상 밖."""
    n, v = checks.check_k(fixture_tree("rule_k", "bad"))
    assert n == 6                                           # 허용 파일 2개를 뺀 대상 파일 수(픽스처 트리 구성)
    assert _keys(v) == sorted(EXPECTED_BAD["rule_k"]), "\n".join(str(x) for x in v)
    assert {x.kind for x in v} == {"front_query_name", "front_query_module", "snapshot_read"}


def test_rule_k_accepts_good_fixture(checks, fixture_tree):
    """허용 파일 셋 안의 정의·재수출·_read_snapshot_file 사용, 허용 파일 밖의 무관한 이름(`front_entries_count`, 문자열 안 언급,
    `write_snapshot`)은 통과한다."""
    n, v = checks.check_k(fixture_tree("rule_k", "good"))
    assert n == 2                                           # search/archive.py, pipeline/run.py
    assert v == [], "\n".join(str(x) for x in v)


def test_rule_i_leaves_library_name_literals_to_rule_e(checks, fixture_tree, library):
    """이름 집합을 주면 (b)는 library 이름 리터럴("two_stage_ota")을 규칙 E 에 넘기고 그 밖 리터럴만 잡는다(E 와 겹치지 않음)."""
    _, names = library
    assert "two_stage_ota" in names
    assert not {"folded_mirror_amp", "rail_core", "rail_io", "telescopic", "outp", "outn", "cascode_amp"} & set(names)
    n, v = checks.check_i(fixture_tree("rule_i", "bad"), names)
    assert n > 0
    want = sorted(k for k in EXPECTED_BAD["rule_i"] if k[1] != "search/lib_name.py")
    assert _keys(v) == want, "\n".join(str(x) for x in v)
    n, v = checks.check_e(fixture_tree("rule_i", "bad"), names)
    assert ("name_literal", "search/lib_name.py", 2) in _keys(v)


def test_rule_i_key_list_covers_declared_sources(checks):
    """(a) 키 목록이 출처 문서의 키를 모두 담는다: authoring 의 IGNORED_TAG_KEYS(CONTRACT 머리), 계획 U-50·IC4, 과제 지시."""
    keys = set(checks.FORBIDDEN_LOOKUP_KEYS)
    assert {"device_roles", "symmetry", "sizing_roles", "compensation"} <= keys                 # authoring CONTRACT
    assert {"vertical_stack_id", "fold_group", "headroom_role", "shared_gm_id_groups",
            "budget_reference_device"} <= keys                                                  # U-50
    assert {"gm_id_role", "L_role"} <= keys                                                     # IC4
    assert {"topology_name", "matching_pairs"} <= keys                                          # 과제 지시
    assert len(keys) == len(checks.FORBIDDEN_LOOKUP_KEYS)


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
