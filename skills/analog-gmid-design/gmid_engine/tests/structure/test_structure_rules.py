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
    assert len(circuits) >= 13, "library topology 회로 %d개(O-181: 13회로)" % len(circuits)
    assert any(o.endswith(":supply_net") for origins in names.values() for o in origins), "레일 이름 수집 0"
    # O-198: 엔진이 선언한 어휘(LUT 축 AXES, spec 키 상수, _module_map plan_ids 칸)는 선언 자리에서 읽어 이름 집합에서 뺀다.
    # 거부 능력은 test_structure_rules_reject_fixtures.py::test_rule_e_vocabulary_* 가 확인한다.
    n, v = checks.check_e(engine_root, checks.without_engine_vocabulary(names))
    _assert_clean(n, v, report, "E")


def test_rule_f_no_broad_except(checks, engine_root, report):
    n, v = checks.check_f(engine_root)
    _assert_clean(n, v, report, "F")


def test_rule_g_no_module_level_mutable_cache(checks, engine_root, report):
    n, v = checks.check_g(engine_root)
    _assert_clean(n, v, report, "G")


def test_rule_i_no_circuit_specific_behavior(checks, engine_root, library, report):
    """규칙 I: 회로 식별·태그 키 리터럴 조회 0 + 이름 리터럴 분기 0(library 이름 리터럴은 규칙 E 몫이라 넘긴다)."""
    _, names = library
    n, v = checks.check_i(engine_root, names)
    _assert_clean(n, v, report, "I")


def test_rule_k_front_query_not_called_in_engine(checks, engine_root, report):
    """규칙 K(설계 40 v1.10 §2.4.3 'front 조회 전용 읽기 경로'): 허용 파일(search/front_query.py·front_entries.py·__init__.py) 밖 엔진 소스에
    front 조회 이름·모듈 참조와 스냅샷 파일 읽기 참조가 없다 -- 다른 실행의 출력이 계산으로 새지 않는다."""
    n, v = checks.check_k(engine_root)
    _assert_clean(n, v, report, "K")


def test_rule_m_run_pair_not_shared(checks, engine_root, report):
    """규칙 M(XRUN-F1 card B interface card C9, B-T23): 엔진 소스·tests/ 트리에서 실행 비공유 위반 0 -- open_run 참조는 허용 파일뿐(M-a),
    S3Index·RunCounters 직접 생성 0(M-b), run_stage_a 마다 같은 함수 open_run() 튜플 풀기 1:1(M-c), 두 객체 보관 0(M-d), 직렬화 0(M-f).
    M-c 가 공허하지 않게 진짜 트리에 run_stage_a 호출이 있는지(재작성 대상 16파일)와 open_run 정의 파일이 있는지 먼저 본다."""
    assert (engine_root / "search" / "open_run.py").is_file(), "search/open_run.py 없음(C0)"
    assert checks.m_run_stage_a_calls(engine_root) >= 16
    n, v = checks.check_m(engine_root)
    _assert_clean(n, v, report, "M")


def test_rule_i_exemptions_are_used(checks, engine_root, library, monkeypatch):
    """예외 목록이 낡지 않았다: 지금 있는 예외 파일마다 예외를 빼면 실제로 걸리는 조회가 있다(쓰이지 않는 예외 0).
    폴더 접두 예외(`report/`)는 그 폴더에 파일이 생기기 전까지 대상이 없을 수 있어 존재하는 파일 항목만 본다."""
    _, names = library
    exempt = checks.TAG_LOOKUP_EXEMPT
    monkeypatch.setattr(checks, "TAG_LOOKUP_EXEMPT", ())
    _, raw = checks.check_i(engine_root, names)
    hit = {v.path for v in raw if v.kind == "tag_key_lookup"}
    assert exempt
    for place, keys, why in exempt:
        assert why and keys and set(keys) <= set(checks.FORBIDDEN_LOOKUP_KEYS), place
        if not place.endswith("/"):
            assert (engine_root / place).is_file(), "예외 파일 없음: %s" % place
            assert place in hit, "쓰이지 않는 예외: %s" % place


def test_rule_i_library_tag_subkeys_classified(checks, engine_root):
    """library 태그 섹션(device_roles 소자별·symmetry·sizing_roles·compensation)의 하위 키(`_` 주석 키 제외)는 전부
    금지 목록(FORBIDDEN_LOOKUP_KEYS) 또는 사유를 적은 비금지 목록(TAG_SUBKEYS_NOT_BANNED) 중 하나에 있다.
    library 에 새 역할 키가 생기면 이 test 가 분류를 요구한다(조용히 규칙 I 밖으로 새지 않게)."""
    import json
    lib = engine_root.parent / "assets" / "library"
    found = set()
    for f in sorted(lib.glob("*.topology.json")):
        if f.name.startswith("_"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        roles = d.get("device_roles")
        if isinstance(roles, dict):
            for entry in roles.values():
                if isinstance(entry, dict):
                    found.update(entry)
        for sec in ("symmetry", "sizing_roles", "compensation"):
            if isinstance(d.get(sec), dict):
                found.update(d[sec])
    found = {k for k in found if not k.startswith("_")}
    assert found, "library 태그 하위 키 수집 0"
    banned, free = set(checks.FORBIDDEN_LOOKUP_KEYS), set(checks.TAG_SUBKEYS_NOT_BANNED)
    assert not banned & free
    assert found <= banned | free, "분류 안 된 태그 하위 키: %s" % sorted(found - banned - free)


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
