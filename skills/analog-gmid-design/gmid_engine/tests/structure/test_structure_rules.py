"""gmid_engine 구조 규칙 A~G 를 진짜 엔진 트리에 건다(규칙 H 는 test_structure_test_mapping.py).

검사 대상이 0개(패키지가 아직 비어 있음)여도 PASS 하지만, 대상 수는 실행 끝 요약
'gmid_engine 구조 규칙 -- 검사 대상 수'에 항상 찍힌다. 검사기가 공허하지 않다는 증거는
test_structure_rules_reject_fixtures.py(위반 픽스처를 실제로 거부하는지)가 맡는다.
규칙 문구·출처: README.md, structure_checks.py 상단.
"""
from __future__ import annotations


def _assert_clean(n_targets, violations, report, rule):
    report(n_targets, len(violations))
    assert not violations, "규칙 %s 위반 %d건(대상 %d개):\n%s" % (
        rule, len(violations), n_targets, "\n".join(str(v) for v in violations))


def test_rule_a_one_entry_point_per_file(checks, engine_root, report):
    n, v = checks.check_a(engine_root)
    _assert_clean(n, v, report, "A")


def test_rule_b_no_private_name_import(checks, engine_root, report):
    n, v = checks.check_b(engine_root)
    _assert_clean(n, v, report, "B")


def test_rule_c_layering_public_api_no_cycles(checks, engine_root, report):
    n, v = checks.check_c(engine_root)
    _assert_clean(n, v, report, "C")


def test_rule_d_numeric_literals(checks, engine_root, report):
    n, v = checks.check_d(engine_root)
    _assert_clean(n, v, report, "D")


def test_rule_e_no_circuit_name_literals(checks, engine_root, library, report):
    circuits, names = library
    # 이름 집합이 비면 이 test 는 공허하다 -- library 9회로(설계 1.4)와 레일 선언이 실제로 모였는지 먼저 본다.
    assert len(circuits) >= 9, "library topology 회로 %d개(설계 1.4: 9회로)" % len(circuits)
    assert any(o.endswith(":supply_net") for origins in names.values() for o in origins), "레일 이름 수집 0"
    n, v = checks.check_e(engine_root, names)
    _assert_clean(n, v, report, "E")


def test_rule_f_no_broad_except(checks, engine_root, report):
    n, v = checks.check_f(engine_root)
    _assert_clean(n, v, report, "F")


def test_rule_g_no_module_level_mutable_cache(checks, engine_root, report):
    n, v = checks.check_g(engine_root)
    _assert_clean(n, v, report, "G")


def test_rule_copy_manifest_matches_copies(checks, engine_root, report):
    """복사 등록부(하위 패키지 `_copy_manifest.py`): 형식, 등록 정의 존재, 복사본 AST 해시·규칙 D 밖 리터럴 목록 일치.
    해시·리터럴은 검사기가 복사본에서 다시 잰다. 어긋난 정의는 D·E·G 면제도 취소된다(README '복사 등록부')."""
    n, v = checks.check_copy_manifest(engine_root)
    _assert_clean(n, v, report, "복사 등록부(복사본)")


def test_rule_copy_manifest_matches_original(checks, engine_root, report):
    """복사 등록부의 원본 대조: COPY_SOURCE(엔진 밖) 파일을 다시 파싱해 등록 행 범위의 같은 이름 정의
    AST 해시가 등록 해시와 같다. 등록 항목 전부가 원본과 대조되어야 한다."""
    n_entries, _ = checks.check_copy_manifest(engine_root)
    n, v = checks.check_copy_source(engine_root)
    _assert_clean(n, v, report, "복사 등록부(원본)")
    assert n == n_entries, "원본과 대조한 항목 %d개 != 등록 항목 %d개" % (n, n_entries)
