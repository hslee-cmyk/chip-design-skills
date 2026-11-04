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


# 규칙 M(XRUN-F1 card B interface card C9, B-T24): 기대 목록은 픽스처 소스 줄을 손으로 읽어 적었다. bad 트리의 정의 모듈
# (search/open_run.py·s3_index.py·__init__.py, core/run_counters.py)은 위반 0 -- 허용 자리 확인.
EXPECTED_BAD_M = [
    ("direct_construct", "search/kernel.py", 6),             # (M-b) 엔진 소스 S3Index()
    ("direct_construct", "search/kernel.py", 7),             # (M-b) import 별칭 Counters() = RunCounters
    ("direct_construct", "tests/test_mb_construct.py", 6),   # (M-b) test 의 S3Index()
    ("direct_construct", "tests/test_mb_construct.py", 7),   # (M-b) test 의 core.RunCounters()(속성)
    ("open_run_ref", "pipeline/session.py", 1),              # (M-a) import 이름 open_run
    ("open_run_ref", "pipeline/session.py", 6),              # (M-a) 이름 open_run
    ("open_run_ref", "pipeline/session.py", 10),             # (M-a) 속성 search.open_run
    ("run_pair_loop", "tests/test_mc_loops.py", 8),          # (M-c) 반복문 밖 open_run, 반복문 안 run_stage_a
    ("run_pair_loop", "tests/test_mc_loops.py", 13),         # (M-c) 내포식 안 run_stage_a(반복문 본문으로 본다)
    ("run_pair_loop", "tests/test_mc_loops.py", 44),         # (M-c) 바깥 반복문 본문 open_run, 안쪽 반복문 run_stage_a(가장 안쪽 반복문 규칙)
    ("run_pair_packed", "tests/test_mc_loops.py", 35),       # (M-c) **kw
    ("run_pair_packed", "tests/test_mc_loops.py", 37),       # (M-c) *args
    ("run_pair_persisted", "tests/test_mf_dump.py", 11),     # (M-f) pickle.dump(donors, f)
    ("run_pair_persisted", "tests/test_mf_dump.py", 12),     # (M-f) json.dumps(counters._rows)(내부 칸)
    ("run_pair_persisted", "tests/test_mf_dump.py", 19),     # (M-f) shelve 항목 대입
    ("run_pair_persisted", "tests/test_mf_dump.py", 20),     # (M-f) pickle.dumps(stage.donors)(결과 칸)
    ("run_pair_reused", "tests/test_mc_loops.py", 18),       # (M-c) 같은 이름 두 run_stage_a -- 첫째
    ("run_pair_reused", "tests/test_mc_loops.py", 19),       # (M-c) 같은 이름 두 run_stage_a -- 둘째
    ("run_pair_source", "tests/test_mc_loops.py", 26),       # (M-c) 안쪽 def 의 자유 변수
    ("run_pair_source", "tests/test_mc_loops.py", 28),       # (M-c) lambda 의 자유 변수
    ("run_pair_source", "tests/test_mc_sources.py", 6),      # (M-c) 매개변수로 받은 쌍
    ("run_pair_source", "tests/test_mc_sources.py", 16),     # (M-c) 결과 칸 a.donors·a.counters
    ("run_pair_source", "tests/test_mc_sources.py", 22),     # (M-c) 다른 호출(make_pair()) 반환
    ("run_pair_source", "tests/test_mc_sources.py", 27),     # (M-c) 튜플 풀기 순서 바뀜(c, d = open_run())
    ("run_pair_source", "tests/test_mc_sources.py", 33),     # (M-c) 다시 묶인 이름(d = make_pair()[0])
    ("run_pair_source", "tests/test_mc_sources.py", 39),     # (M-c) donors·counters 가 서로 다른 open_run()
    ("run_pair_reused", "tests/test_mc_indirect.py", 8),     # (M-c) import 별칭(rsa) 호출 -- 대입 하나를 두 호출에 -- 첫째
    ("run_pair_reused", "tests/test_mc_indirect.py", 9),     # (M-c) import 별칭(rsa) 호출 -- 둘째
    ("run_pair_source", "tests/test_mc_indirect.py", 14),    # (M-c) 이름 대입 간접 호출(go = pipeline.run_stage_a)에 매개변수 쌍
    ("run_pair_source", "tests/test_mc_indirect.py", 18),    # (M-c) getattr(pipeline, "run_stage_a")(...) 에 결과 칸 쌍
    ("run_pair_source", "tests/test_mc_indirect.py", 26),    # (M-c) if 가지 안 대입은 가지 밖 호출을 앞서지 않는다(fail-closed)
    ("run_pair_source", "tests/test_mc_indirect.py", 32),    # (M-c) with 본문 안 대입은 본문 밖 호출을 앞서지 않는다(O-17 (2) 안전 쪽)
    ("run_pair_stored", "tests/conftest.py", 5),             # (M-d) 모듈 수준 이름
    ("run_pair_stored", "tests/conftest.py", 10),            # (M-d) session fixture 반환
    ("run_pair_stored", "tests/conftest.py", 16),            # (M-d) module fixture yield
    ("run_pair_stored", "tests/conftest.py", 20),            # (M-d) pytest_configure 안 config.stash
    ("run_pair_stored", "tests/conftest.py", 25),            # (M-d) request.config 속성
    ("run_pair_stored", "tests/test_md_store.py", 11),       # (M-d) 클래스 속성
    ("run_pair_stored", "tests/test_md_store.py", 14),       # (M-d) 함수 기본 인자값
    ("run_pair_stored", "tests/test_md_store.py", 20),       # (M-d) @functools.lru_cache 함수의 반환
    ("run_pair_stored", "tests/test_md_store.py", 27),       # (M-d) 호출형 functools.cache(make)
    ("run_pair_stored", "tests/test_md_store.py", 31),       # (M-d) 모듈 리스트 append
    ("run_pair_stored", "tests/test_md_store.py", 36),       # (M-d) 모듈 수준 객체(BOX)의 인스턴스 속성
    ("run_pair_stored", "tests/test_md_store.py", 46),       # (M-d) session fixture 가 KernelContext(두 객체를 쥔 값) 반환
    ("run_pair_stored", "tests/test_md_store.py", 56),       # (M-d) package fixture 가 helper 한 겹을 거친 KernelContext 반환
    ("run_pair_stored", "tests/test_md_store.py", 63),       # (M-d) 컨텍스트 칸(case.sctx)을 모듈 리스트에 append
]


def test_rule_m_rejects_bad_fixture(checks, fixture_tree):
    """규칙 M(card B C9): M-a·M-b·M-c 꼴마다·M-d 경로마다·M-f 를 담은 bad 트리를 기대 목록과 정확히 같게 거부한다(실제로 거부)."""
    root = fixture_tree("rule_m", "bad")
    n, v = checks.check_m(root)
    assert n == 13                                           # 픽스처 트리의 .py 파일 수(엔진 6 + tests 7 -- test_mc_indirect 추가)
    assert _keys(v) == sorted(EXPECTED_BAD_M), "\n".join(str(x) for x in v)
    assert {x.kind for x in v} == {"open_run_ref", "direct_construct", "run_pair_source", "run_pair_reused",
                                   "run_pair_loop", "run_pair_packed", "run_pair_stored", "run_pair_persisted"}
    assert checks.m_run_stage_a_calls(root) == 22            # 15 + 별칭·이름 대입·getattr 간접 호출 5 + with 본문 1 + 중첩 반복문 1


def test_rule_m_accepts_good_fixture(checks, fixture_tree):
    """허용: 튜플 풀기 1:1(결과 칸 is 확인 포함), 호출마다 자기 open_run(), 반복문 안 open_run, function fixture 가 open_run() 반환,
    단위 test 한 쌍으로 감쌈 함수 여러 번, 스스로 open_run 하는 helper, session fixture 가 지역 쌍으로 만든 S1 스냅샷만 반환,
    키워드 하나 빠진 TypeError 꼴, 계수 snapshot 값의 json 출력, 정의 모듈의 생성 호출, 엔진 진입이 두 객체를 받기만 함,
    실행 결과의 스냅샷 칸(res.s1 -- 두 객체를 담지 않음)을 모듈 캐시에 둠, 같은 이름을 새 open_run() 튜플 풀기로 다시 대입해 호출마다 하나
    (design 40 §2.4.5 M-c: 대입마다 호출 하나), import 별칭 호출의 1:1."""
    root = fixture_tree("rule_m", "good")
    n, v = checks.check_m(root)
    assert n == 7
    assert v == [], "\n".join(str(x) for x in v)
    assert checks.m_run_stage_a_calls(root) == 10            # 7 + 같은 이름 재대입 2 + 별칭 1


def test_rule_m_targets_tests_but_not_fixtures(checks, engine_root):
    """대상 범위(C9 'test 쪽에도 걸린다'): 진짜 트리에서 tests/ 아래 파일은 대상이고, 이 폴더의 위반 픽스처는 대상이 아니다."""
    files = [p.relative_to(engine_root).as_posix() for p in checks.m_files(engine_root)]
    assert any(f.startswith("tests/") for f in files)
    assert any(not f.startswith("tests/") for f in files)
    assert not any(f.startswith("tests/structure/fixtures/") for f in files)


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


def test_rule_e_vocabulary_is_read_from_declarations(checks):
    """O-198: 뺄 어휘는 하드코딩 목록이 아니라 선언 자리(AXES·CIRCUIT_SPECIFIC_KEYS·_module_map plan_ids)에서 읽힌다.
    세 자리의 대표 원소가 들어 있고, 진짜 회로 이름(레일·회로·소자·포트)은 들어 있지 않다."""
    from gmid_engine._module_map import MODULES
    from gmid_engine.authoring._spec_fields import CIRCUIT_SPECIFIC_KEYS
    from gmid_engine.lut.lut_types import AXES
    vocab = checks.engine_vocabulary()
    assert set(AXES) <= vocab and set(CIRCUIT_SPECIFIC_KEYS) <= vocab
    assert {pid for m in MODULES for pid in m.plan_ids} <= vocab
    assert vocab == set(AXES) | set(CIRCUIT_SPECIFIC_KEYS) | {pid for m in MODULES for pid in m.plan_ids}
    assert not {"vdd", "gnd", "two_stage_ota", "M1", "vin_p"} & vocab


def test_rule_e_vocabulary_removal_is_limited_to_declared_words(checks, library):
    """이름 집합에서 빠지는 것은 (library 이름 ∩ 엔진 어휘)뿐이고, 그 밖 이름은 출처 목록까지 그대로다."""
    _, names = library
    vocab = checks.engine_vocabulary()
    kept = checks.without_engine_vocabulary(names)
    removed = set(names) - set(kept)
    assert removed == set(names) & vocab
    assert removed, "빼는 어휘가 0이면 O-198 이전과 같다 -- 현재 library 와 엔진 사이 우연 일치(VS·Z·Q4·Q8·Q9)가 있어야 한다"
    assert all(kept[k] == names[k] for k in kept)
    assert {"vdd", "gnd", "two_stage_ota", "M1", "vin_p"} <= set(kept)


def test_rule_e_still_rejects_circuit_names_after_vocabulary_removal(checks, fixture_tree, library):
    """거부 fixture(엔진 코드에 진짜 회로 이름 리터럴을 넣은 toy)는 어휘를 뺀 이름 집합에서도 같은 위반을 낸다."""
    _, names = library
    n, v = checks.check_e(fixture_tree("rule_e", "bad"), checks.without_engine_vocabulary(names))
    assert n > 0
    assert sorted((x.kind, x.path, x.line) for x in v) == [
        ("name_literal", "core/names.py", 2),
        ("name_literal", "core/names.py", 3),
        ("name_literal", "core/names.py", 4),
        ("name_literal", "core/names.py", 5),
        ("name_literal", "core/names.py", 5),
    ], "\n".join(str(x) for x in v)


def test_rule_e_vocabulary_word_excused_but_circuit_name_in_same_file_rejected(checks, library, tmp_path):
    """한 파일에 엔진 어휘(LUT 축 'VS'·spec 키 'Z'·plan ID 'Q8')와 진짜 회로 이름('vin_p'·'M1')이 같이 있으면 어휘만 면제된다."""
    _, names = library
    assert {"VS", "Z", "Q8"} <= set(names)                 # 세 어휘가 library 이름과 실제로 겹친다(그렇지 않으면 이 test 가 공허)
    root = tmp_path / "gmid_engine"
    (root / "core").mkdir(parents=True)
    (root / "core" / "toy.py").write_text(
        'AXIS = "VS"\nKEY = "Z"\nPLAN = "Q8"\nBAD = {"M1": "vin_p"}\n', encoding="utf-8")
    n, v = checks.check_e(root, checks.without_engine_vocabulary(names))
    assert n == 1
    assert sorted(x.detail.split(" = ")[0] for x in v) == ["'M1'", "'vin_p'"], "\n".join(str(x) for x in v)
    _, v_all = checks.check_e(root, names)                  # 어휘를 안 뺀 옛 정의는 다섯 개 모두 잡는다(대조)
    assert len(v_all) == 5


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
