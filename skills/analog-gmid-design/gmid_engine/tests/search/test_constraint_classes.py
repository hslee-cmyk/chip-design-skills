"""search/constraint_classes.py -- 계산 블록 `constraint_classes(snapshot, judged_constraints)` -> S0 수준 필드 `graph/kernel: constraint_classes`
(설계 40 v1.9.1 §2.4.7 'SearchContext 칸 배정' `judged_constraints`·`ss_constraints`·`constraint_notes` 행, §2.4.8 'SearchDomain, 제약 분류 ...' 행, D8;
search CONTRACT 3.14 분류 규칙 -- 옛 `build_search_context` 안 분류를 블록으로 옮긴 것).

oracle (d) 설계·계약 문장(선언 순서대로 하나씩):
- 값이 결정 대기(None)면 notes 에 judgment_pending(metric·op·verdict·reason `constraint_value_pending`·decision).
- 목적 축(`power_dc_w`·`area_search_m2`, search AXES)이면 judged 에 (metric, op, float 값).
- 레지스트리에 있고 ss 뷰가 있으면 ss 에 그 제약의 spec 위치(index) -- 선언 객체 사본을 두지 않는다(D8).
- 그 밖은 notes 에 unmeasured(`metric_not_in_registry_or_no_ss_view`) -- 조용히 통과하지 않는다(S-1).
- 값 형식 = 새 frozen dataclass `ConstraintClasses`(D8). [xrun] 옛 '타입 등록부에 오른다' 단언은 지웠다(설계 40 v1.10 §2.4.3 타입 등록부 삭제).
- 계산 블록: writer = `constraint_classes`(필드 하나 = writer 하나), 같은 입력은 재사용(계산 0, 40 §2.4.2).
입력 metric 이름: `gain_ss_db`(전달 뷰가 있는 ss metric), `supply_current_dc`(레지스트리에 있으나 ss 뷰가 없는 metric) -- 기대 분류는 위 문장에서 손으로 정한다.
"""
import dataclasses

import pytest

from gmid_engine.core import GraphSnapshot
from gmid_engine.search.constraint_classes import constraint_classes
from gmid_engine.search.s0_fields import S0_WRITERS
from gmid_engine.search.search_values import ConstraintClasses
from gmid_engine.sizing import KERNEL_KEY

from .conftest import block_row, fresh_run  # [XRUN-F1 card B C0·C1]


@dataclasses.dataclass(frozen=True)
class Decl:
    """spec 판정 제약 선언의 test 쪽 입력 형식(블록이 읽는 칸만: metric·op·value·value_decision)."""

    metric: str
    op: str
    value: object
    value_decision: object = None


DECLS = (
    Decl("gain_ss_db", ">=", 60.0),                      # 0 -> ss
    Decl("power_dc_w", "<=", 1e-3),                      # 1 -> judged
    Decl("pm_ss_deg", ">=", None, "pending_user"),       # 2 -> judgment_pending
    Decl("supply_current_dc", "<=", 2e-4),               # 3 -> unmeasured
    Decl("area_search_m2", "<=", 1e-9),                  # 4 -> judged
)


def _classes(decls=DECLS):
    snap = constraint_classes(GraphSnapshot.empty(S0_WRITERS), tuple(decls), **fresh_run())
    return snap, snap.value("graph", KERNEL_KEY, "constraint_classes")


def test_classification_follows_declaration_order():
    _snap, cc = _classes()
    assert isinstance(cc, ConstraintClasses)
    assert cc.judged == (("power_dc_w", "<=", 1e-3), ("area_search_m2", "<=", 1e-9))
    assert cc.ss == (0,)
    notes = [dict(n) for n in cc.notes]
    assert notes == [
        {"metric": "pm_ss_deg", "op": ">=", "verdict": "judgment_pending", "reason": "constraint_value_pending", "decision": "pending_user"},
        {"metric": "supply_current_dc", "op": "<=", "value": 2e-4, "verdict": "unmeasured", "reason": "metric_not_in_registry_or_no_ss_view"},
    ]


def test_judged_values_are_float():
    _snap, cc = _classes((Decl("power_dc_w", "<=", 1),))
    assert cc.judged == (("power_dc_w", "<=", 1.0),) and isinstance(cc.judged[0][2], float)


def test_empty_spec_gives_empty_classes():
    _snap, cc = _classes(())
    assert (cc.judged, cc.ss, cc.notes) == ((), (), ())


def test_writer_is_constraint_classes_and_reuse_computes_nothing():
    snap, _cc = _classes()
    assert snap.field("graph", KERNEL_KEY, "constraint_classes").writer == "constraint_classes"
    run = fresh_run()                 # card B C4 판정 1 -- 새 실행 계수(C1)의 그 블록 행 = (calls 1, reuses 1, computes 0)
    again = constraint_classes(snap, DECLS, **run)
    st = block_row(run["counters"], constraint_classes.name)
    assert again is snap and (st[0], st[1], st[4]) == (1, 1, 0)


def test_mutable_extras_rejected():
    with pytest.raises(TypeError):
        constraint_classes(GraphSnapshot.empty(S0_WRITERS), [Decl("power_dc_w", "<=", 1e-3)], **fresh_run())
