"""graph/s1v_fields.py -- S1v 필드 계산 블록 `s1v_fields`(writer `build_s1v`) (U17 ①-b, 규칙 H 1:1 test).

근거: 설계 40 v1.9.1 §2.4.2('S0 수준 값은 계산 블록으로 만들고 S0 수준 스냅샷에 쓴다. 입력 버전이 같으면 다시 계산하지 않는다'),
§2.4.8 S1v 행 + D1('graph/s1v: views, l_classes, findings, declared, applied_facts. 옛 별도 필드 blocks·composite_blocks·pole_nodes·loops·cuts 는
만들지 않고 coverage 는 폐기'), 41 §1 뷰 id 규칙(전달 뷰 `transfer:<순번>`), 계약 10.2(정지는 진입점 build_s1v 의 몫 -- 블록은 기록을 쓴다).
oracle (d) 선언값 그대로 + oracle (a) 손 회로(s1v_hand).
"""
from __future__ import annotations

from gmid_engine.core import StructureUnresolvedError
from gmid_engine.graph import S1V_WRITERS, s1v_fields

import pytest

import s1v_hand as H

D1_FIELDS = ("views", "l_classes", "findings", "declared", "applied_facts")


def _run(s1, *, declared=(), cuts=(), budget=H.BIG_BUDGET, run=None):
    """[XRUN-F1 card B C4] run = 실행 두 객체 키워드(dict), 없으면 새 실행 하나."""
    return s1v_fields(s1.snapshot.widen(S1V_WRITERS), (), budget, tuple(declared), (), (), tuple(cuts),
                      **(run if run is not None else H.fresh_run()))


def test_block_name_and_writes_are_design_fields():
    assert s1v_fields.name == "build_s1v"
    assert set(s1v_fields.writes) == {("graph", f) for f in D1_FIELDS}


def test_writes_exactly_d1_fields_no_copies(tmp_path):
    s1, _ = H.build(tmp_path, H.MILLER)
    snap = _run(s1)
    fields = {name for name, _fv in snap.record("graph", "s1v").fields}
    assert fields == set(D1_FIELDS)
    assert not fields & {"blocks", "composite_blocks", "pole_nodes", "loops", "cuts", "coverage"}


def test_hand_circuit_values(tmp_path):
    # CS: 신호 입력 in 하나, 출력 out 하나 -> 기본 전달 뷰 하나 transfer:0. declared·사실 없음 -> 빈 요약·적용 없음.
    s1, _ = H.build(tmp_path, H.CS)
    snap = _run(s1)
    assert [v.id for v in snap.value("graph", "s1v", "views")] == ["transfer:0"]
    assert snap.value("graph", "s1v", "declared") == ()
    assert snap.value("graph", "s1v", "applied_facts") == ()


def test_declared_summary_counts_stage_groups(tmp_path):
    # declared 대조 요약 ((출처, stage 묶음 수), ...) -- 손 입력 comp 의 묶음은 (M1,M2)·(M6) 두 개
    s1, _ = H.build(tmp_path, H.MILLER)
    snap = _run(s1, declared=(("comp", (("M1", "M2"), ("M6",))),))
    assert snap.value("graph", "s1v", "declared") == (("comp", 2),)


def test_block_records_but_does_not_stop(tmp_path):
    # AMB 는 cell_ambiguous(unsupported_rule_branch) -- 블록은 정지하지 않고 기록을 쓴다(정지는 build_s1v)
    s1, _ = H.build(tmp_path, H.AMB)
    snap = _run(s1)
    codes = [f.code for v in snap.value("graph", "s1v", "views") for f in v.findings] + [f.code for f in snap.value("graph", "s1v", "findings")]
    assert "cell_ambiguous" in codes
    with pytest.raises(StructureUnresolvedError):
        H.build(tmp_path, H.AMB, stop_on_unsupported=True)


def test_same_input_reuses_and_changed_extra_recomputes(tmp_path):
    # oracle 대조: card B C4 판정 1·4 -- 실행 계수(C1) 행 (calls, reuses, computes) 의 구간 값
    s1, _ = H.build(tmp_path, H.CMFB)
    first = _run(s1)
    run = H.fresh_run()
    again = s1v_fields(first, (), H.BIG_BUDGET, (), (), (), (), **run)
    assert again is first

    def row():
        rows = [r for r in run["counters"].snapshot().blocks if r.block == s1v_fields.name]
        return (rows[0].calls, rows[0].reuses, rows[0].computes) if rows else (0, 0, 0)
    assert row() == (1, 1, 0)
    other = s1v_fields(first, (), H.BIG_BUDGET + 1, (), (), (), (), **run)
    assert row()[2] == 1
    assert other.block_version("build_s1v") != first.block_version("build_s1v")
