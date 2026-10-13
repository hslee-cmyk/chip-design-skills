"""graph/loop_roles.py -- 루프 역할(설계 41 1.12.3 J-B 중첩 Miller 내부 루프, 1.12.1-3 복합 diode 내부, 1.8 분류 순서, 계약 10.6).

oracle (a) 손 유도:
- NMC3(jrules_hand): 3단 사슬 v1 -Q8-> np -Q10(미러, gate np diode 단자)-> v2 -Q13-> out 과 중첩 Miller Cm1(v1-out)·Cm2(v2-out).
  끊는 점 (Q8, v1) 의 루프 사이클 v1 -> np -> v2 -> out -Cm1-> v1 과 v1 -> np -> v2 -Cm2-> out -Cm1-> v1 은
  (a) 모두 커패시터를 포함한 수동소자만의 극대 구간이 전달 뷰 순방향 넷 둘(out·v1 / v2·v1)을 잇는 Miller 사이클이고
  (b) 사이클 위 능동 셀 Q8·Q10·Q13 이 모두 전달 뷰 순방향 셀이다 -> `compensation_internal`, 루프 뷰를 만들지 않는다.
  전달 뷰에 전체 `pm_ss_deg` 가 선언되지 않았으면 `undeclared_loop_constraint`(`기록만`) 를 사유
  `compensation_internal_needs_overall_pm` 으로 유지, 선언되면 그 정지가 없다.
- CMFB(s1v_hand): 루프 cm -M5-> cmfb -M3/M4-> om/op -R-> cm 의 M5 는 전달 뷰 순방향 밖(공통 모드 감지) -> (b) 불만족 ->
  루프 뷰 `loop:M5:cm` 유지(역할 loop_view).
- BIASSCC: 순방향 노드를 하나도 지나지 않는 교차결합 p<->q -> (1.5) 바이어스 SCC(역할 bias_scc), 루프 id = 노드 이름 JSON 배열.
- SFLOAD: 묶음 내부 사이클 -> composite_diode_internal(역할), 루프 id = 정준 회전 노드 JSON 배열(40 3.2-3).
oracle (d): library -- 41 1.13 기대 행: ngcc `loop:M8:V1`·nmcnr `loop:M201:NodeM2` = compensation_internal(루프 뷰 0), 파일럿 CM 루프는
(b) 불만족으로 루프 뷰 유지. 두 회로 spec 에 `pm_ss_deg` 가 있다(spec 파일 직접 확인).
graph `.py` 소스는 열람하지 않았다.
"""
from __future__ import annotations

import json

import pytest

from gmid_engine.authoring import load_sizing_spec, load_topology
from gmid_engine.core import StructureUnresolvedError
from gmid_engine.graph import LoopRole, build_s1, build_s1v
from gmid_engine.metrics import metric_catalog

import jrules_hand as J
import s1v_hand as H

REASON_NEEDS_PM = "compensation_internal_needs_overall_pm"     # 41 1.12.3 '처리' 셋째 줄


def _nmc3(tmp_path, pm, stop=False):
    topo, spec = J.load_spec(tmp_path, J.NMC3, pm=pm)
    s1 = build_s1(topo, H.SUPPLIES)
    return H.read_s1v(build_s1v(s1, spec, count_budget=H.BIG_BUDGET, stop_on_unsupported=stop))


def _lib(name, spec=True, **kw):
    topo = load_topology(str(H.LIBRARY / (name + ".topology.json")))
    sp = load_sizing_spec(str(H.LIBRARY / (name + ".sizing_spec.json")), topo, metric_catalog()) if spec else None
    s1 = build_s1(topo, H.lib_supplies(name))
    kw.setdefault("stop_on_unsupported", False)
    return H.read_s1v(build_s1v(s1, sp, count_budget=H.BIG_BUDGET, **kw))


def _roles(s1v):
    return {(r.loop_id, r.role) for v in s1v.views for r in v.loop_roles}


def test_nested_miller_inner_loop_is_compensation_internal_without_pm(tmp_path):
    s1v = _nmc3(tmp_path, pm=False)
    assert [v.kind for v in s1v.views] == ["transfer"]                        # 루프 뷰 없음
    assert _roles(s1v) == {("loop:Q8:v1", "compensation_internal")}
    v = H.view(s1v)
    assert v.cuts == ()                                                       # 계약 불변량 (c)
    hits = [f for f in v.findings if f.code == "undeclared_loop_constraint"]
    assert [(h.severity, h.subject) for h in hits] == [("unsupported_rule_branch", ("v1",))]
    assert REASON_NEEDS_PM in hits[0].detail
    assert [r.reason for r in v.loop_roles] == [REASON_NEEDS_PM]
    for lp in v.loops:
        if lp.cut == ("Q8", "v1"):
            assert "compensation_internal" in lp.classes and "loop_view" not in lp.classes


def test_nested_miller_with_overall_pm_has_no_stop(tmp_path):
    s1v = _nmc3(tmp_path, pm=True, stop=True)                                 # 기본 모드에서도 정지하지 않는다
    assert [v.kind for v in s1v.views] == ["transfer"]
    assert _roles(s1v) == {("loop:Q8:v1", "compensation_internal")}
    assert "undeclared_loop_constraint" not in J.finding_codes(s1v)
    assert s1v.unsupported == ()


def test_nested_miller_without_pm_stops_by_default(tmp_path):
    with pytest.raises(StructureUnresolvedError) as ei:
        _nmc3(tmp_path, pm=False, stop=True)
    assert dict(ei.value.record.detail)["rule_branch"] == "undeclared_loop_constraint"


def test_feedback_through_out_of_forward_cell_keeps_loop_view(tmp_path):
    _, s1v = H.build(tmp_path, H.CMFB)
    assert _roles(s1v) == {("loop:M5:cm", "loop_view")}
    assert [v.id for v in s1v.views] == ["transfer:0", "loop:M5:cm"]


def test_bias_scc_role_and_cycle_id(tmp_path):
    _, s1v = H.build(tmp_path, H.BIASSCC)
    roles = [r for v in s1v.views for r in v.loop_roles]
    assert [(json.loads(r.loop_id), r.role) for r in roles] == [(["p", "q"], "bias_scc")]


def test_composite_internal_role_and_cycle_id(tmp_path):
    _, s1v = H.build(tmp_path, J.SFLOAD)
    roles = [r for v in s1v.views for r in v.loop_roles]
    assert [(json.loads(r.loop_id), r.role, r.view, r.status) for r in roles] == [
        (["n1", "n5"], "composite_diode_internal", "transfer:0", "derived")]
    assert all(isinstance(r, LoopRole) for r in roles)


@pytest.mark.parametrize("name,loop_id", [("ngcc_3stage_ff", "loop:M8:V1"), ("nmcnr_amplifier", "loop:M201:NodeM2")])
def test_library_nested_miller_loops(name, loop_id):
    without = _lib(name, spec=False)
    assert [v.kind for v in without.views] == ["transfer"]
    assert _roles(without) == {(loop_id, "compensation_internal")}
    stop = [f for v in without.views for f in v.findings if f.code == "undeclared_loop_constraint"]
    assert len(stop) == 1 and REASON_NEEDS_PM in stop[0].detail
    with_spec = _lib(name, spec=True)                                        # spec 에 pm_ss_deg 가 있다
    assert _roles(with_spec) == {(loop_id, "compensation_internal")}
    assert "undeclared_loop_constraint" not in J.finding_codes(with_spec)
    assert "loop_polarity_undefined" not in J.finding_codes(with_spec)      # 41 1.13 극성 행: 미정의는 1.12.3 으로 사라진다


def test_pilot_cm_loop_stays_a_loop_view():
    s1v = _lib("current_reuse_telescopic_ota", spec=False)
    assert _roles(s1v) == {("loop:M37a:Voc", "loop_view")}
    assert [v.id for v in s1v.views] == ["transfer:0", "loop:M37a:Voc"]


def test_sf_composite_internal_cycles():
    # oracle (a): sf 의 묶음 셋에서 41 1.12.1-3 판정 대상 사이클 = 진입 넷 -캐스코드 기준(gate->drain)-> 기준 gate 넷 -저항-> 진입 넷,
    # 묶음마다 하나({N1, N5}·{N2, N7}·{N12, N13}). 묶음 내부 넷 N56·N78·N1314 는 혼재 노드(캐스코드 source 진입 + 기준 drain)인데
    # 1.12.1-2 에 따라 구동 종류 혼재 판정을 하지 않으므로 전류 진입 source->drain 엣지가 없어 그 넷을 지나는 사이클이 없다.
    # (41 1.13 '9개' 는 U1 시점(묶음 내부 넷을 판정하던 그래프)의 record_only 수에서 온 기대값이다 -- 차이는 보고서에 적는다.)
    _, s1v = H.build_lib("sf_pushpull_output_opamp")
    roles = [r for v in s1v.views for r in v.loop_roles]
    assert {frozenset(json.loads(r.loop_id)) for r in roles} == {frozenset({"N1", "N5"}), frozenset({"N2", "N7"}),
                                                                 frozenset({"N12", "N13"})}
    assert {r.role for r in roles} == {"composite_diode_internal"}
    assert [v.kind for v in s1v.views] == ["transfer"]
    assert "loop_record_only" not in J.finding_codes(s1v)
