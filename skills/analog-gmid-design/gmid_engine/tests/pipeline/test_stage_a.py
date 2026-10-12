"""pipeline/stage_a.py -- `run_stage_a(topology_path, spec_path, lut, *, output_dir, supplies_v=None, structure_path=None)`
(pipeline CONTRACT 1·3·4절, 설계 41 0절 단계 A1~A3).

oracle (a): 손 회로의 구조 유도 결과(graph test 의 손 유도)로 단계 A 판정이 정해진다 --
CS(정지 없음) -> ok/0, FF(복합 블록 review_needed 만) -> review_needed/2, XCOUP(교차결합 loop_record_only) -> stopped/2,
topology 거부(passive_elements 키 없음) -> exit 7, s1v None, count_budget 0, tables None.
oracle (b): N_S 는 test_stage_a_budget 의 직접 집계와 같은 정의 -- 여기서는 회로가 쓰는 kind 로만 센다(nmos 만 쓰는 FOLLOWER <
nmos·pmos 를 쓰는 CS).
oracle (d): structure.json `stage_members` 사실(값 = 공백으로 이은 소자 이름)로 declared 대조 -- MILLER 유도 stage 와 맞는 선언은
performed·ok, 섞인 선언은 declared_stage_mismatch(review_needed), 해시 불일치는 structure_fact_stale + not_performed.

[U1b 2026-10-09] 설계 40 3.2-3 파이프라인 수정: (1) 순서 A1 로드 -> 사실 로드(topology 지문 = doc.connectivity_fp, rule_hash =
`structure_rule_fp()`) -> build_s1(structure=) -> build_s1v(structure=, declared_loop_cuts=), (2) cuts = spec 루프 뷰 선언의 끊는 넷 중
`pm_*` 제약이 가리키는 것, (4) 보고서 applied_facts·ff_ratio_candidates. 그래서 structure.json 의 rule_hash 는 structure_rule_fp 로
쓴다. review_needed 만 내는 손 회로는 FF(이제 feedforward, 41 1.12.2) 대신 FOLDED(l_owner_name_order, 41 1.12.5-4). library 정지 표는
41 1.13 으로 바뀐다: sf 는 정지 없음, ngcc·nmcnr 는 spec 없이 돌리면 compensation_internal 의 전체 PM 미선언 정지, 파일럿은
cs_output_low_impedance(1.12.6 '사실 없이 남는다').

[U1b-jrules 2026-10-09] 821fb72·5b5496f(pipeline 계약 1절, graph 계약 10.2): declared_loop_cuts 는 **내부** 루프 뷰 선언(mode loop,
beta != declared)의 끊는 넷만이고, spec feedback 유도 β 루프(beta declared)는 build_s1v 전달과 `loop_cut_unmatched` 대조 양쪽에서
뺀다. 엔진 루프 뷰 끊는 gate 넷에 맞지 않는 내부 선언 넷은 보고서 review_needed `loop_cut_unmatched`(뷰 "", subject = 넷).
옛 test_declared_loop_cuts_reach_build_s1v(β 선언 inn 이 build_s1v 로 간다)는 이 결정과 충돌해 β 제외·내부 전달 두 test 로 바꿨다.
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

import gmid_engine.pipeline.stage_a as stage_a_module
from gmid_engine.authoring import ViewDecl, load_sizing_spec, load_topology
from gmid_engine.graph import build_s1, build_s1v, s1v_rule_fp, structure_rule_fp
from gmid_engine.metrics import metric_catalog
from gmid_engine.pipeline import StageAResult, run_stage_a, structure_count_budget

import jrules_hand as J
import s1v_hand as H


def _write(tmp_path, doc):
    p = tmp_path / (doc["topology_name"] + ".topology.json")
    p.write_text(json.dumps(doc), encoding="utf-8")
    return p


def _run(tmp_path, real_lut, doc, out="out", **kw):
    return run_stage_a(_write(tmp_path, doc), None, real_lut, output_dir=tmp_path / out, supplies_v=H.SUPPLIES, **kw)


def test_clean_circuit_is_ok_exit_0(tmp_path, real_lut):
    r = _run(tmp_path, real_lut, H.CS)
    assert isinstance(r, StageAResult)
    assert (r.exit_code, r.status) == (0, "ok")
    assert r.report["stop_reasons"] == [] and r.report["review_needed"] == []
    assert r.s1v is not None and [v.id for v in r.s1v.views] == ["transfer:0"]


def test_review_needed_only_is_exit_2(tmp_path, real_lut):
    r = _run(tmp_path, real_lut, H.FOLDED)
    assert (r.exit_code, r.status) == (2, "review_needed")
    assert r.report["stop_reasons"] == []
    assert any("l_owner_name_order" in x for x in r.report["review_needed"])


def test_feedforward_toy_is_ok(tmp_path, real_lut):
    # [U1b] s1v_hand.FF 는 feedforward 묶음(41 1.12.2) -- 복합 블록 review 가 없다
    r = _run(tmp_path, real_lut, H.FF)
    assert (r.exit_code, r.status) == (0, "ok")


def test_record_only_branch_stops_exit_2(tmp_path, real_lut):
    r = _run(tmp_path, real_lut, H.XCOUP)
    assert (r.exit_code, r.status) == (2, "stopped")
    assert any("loop_record_only" in x for x in r.report["stop_reasons"])
    assert r.s1v is not None                                   # 진단 모드로 기록을 받아 단계 A 가 판정한다


def test_topology_rejection_is_exit_7(tmp_path, real_lut):
    bad = {k: v for k, v in H.CS.items() if k != "passive_elements"}
    bad["topology_name"] = "cs_bad"
    r = _run(tmp_path, real_lut, bad)
    assert r.exit_code == 7
    assert r.s1v is None
    assert r.report["count_budget"] == 0 and r.report["tables"] is None
    assert len(r.report["stop_reasons"]) == 1 and r.report["stop_reasons"][0].startswith("A1_load: ")
    assert all((tmp_path / "out" / name).is_file() for name in ("cs_bad.stage_a.json", "cs_bad.stage_a.md"))


def test_count_budget_uses_only_kinds_of_the_circuit(tmp_path, real_lut):
    both = _run(tmp_path, real_lut, H.CS, out="a")                 # nmos + pmos
    nmos_only = _run(tmp_path, real_lut, H.FOLLOWER, out="b")      # nmos 만
    assert both.report["count_budget"] == structure_count_budget(real_lut, ("nmos", "pmos"))
    assert nmos_only.report["count_budget"] == structure_count_budget(real_lut, ("nmos",))
    assert nmos_only.report["count_budget"] < both.report["count_budget"]


def test_same_input_same_tables_and_budget(tmp_path, real_lut):
    a = _run(tmp_path, real_lut, H.CMFB, out="a")
    b = _run(tmp_path, real_lut, H.CMFB, out="b")
    assert a.report["tables"] == b.report["tables"]
    assert a.report["count_budget"] == b.report["count_budget"]


def _structure(path, s1_fp, facts, topology_hash=None):
    path.write_text(json.dumps({
        "schema_version": "1", "topology_hash": s1_fp if topology_hash is None else topology_hash,
        "rule_hash": structure_rule_fp(),
        "facts": [{"concept": "stage_members", "subject": name, "value": value, "status": "ratified",
                   "evidence": {"rule": "hand", "nets": []}, "approval_id": "T-%d" % i}
                  for i, (name, value) in enumerate(facts)]}), encoding="utf-8")


def test_declared_comparison_states(tmp_path, real_lut):
    absent = _run(tmp_path, real_lut, H.MILLER, out="o0")
    assert absent.report["declared_comparison"] == "not_performed: miller.structure.json absent"
    s1_fp = absent.s1v.key[0].topology_fp
    side = tmp_path / "miller.structure.json"                       # 기본 경로 = topology 옆 <회로>.structure.json
    _structure(side, s1_fp, [("stage_one", "M1 M2"), ("stage_two", "M6")])
    good = _run(tmp_path, real_lut, H.MILLER, out="o1")
    assert good.report["declared_comparison"] == "performed"
    assert (good.exit_code, good.status) == (0, "ok")

    other = tmp_path / "other.json"
    _structure(other, s1_fp, [("stage_one", "M1 M6"), ("stage_two", "M2")])
    bad = _run(tmp_path, real_lut, H.MILLER, out="o2", structure_path=other)
    assert (bad.exit_code, bad.status) == (2, "review_needed")
    assert any("declared_stage_mismatch" in x for x in bad.report["review_needed"])

    _structure(other, s1_fp, [("stage_one", "M1 M2")], topology_hash="0" * 64)
    stale = _run(tmp_path, real_lut, H.MILLER, out="o3", structure_path=other)
    assert stale.status == "review_needed"
    assert any("structure_fact_stale" in x for x in stale.report["review_needed"])
    assert stale.report["declared_comparison"].startswith("not_performed")

    other.write_text(json.dumps({"schema_version": "1", "topology_hash": s1_fp, "rule_hash": structure_rule_fp(),
                                 "facts": [{"concept": "drive_kind", "subject": "out", "value": "current",
                                            "status": "ratified", "evidence": {"rule": "h", "nets": ["out"]},
                                            "approval_id": "T-9"}]}), encoding="utf-8")
    no_stage = _run(tmp_path, real_lut, H.MILLER, out="o4", structure_path=other)
    assert no_stage.report["declared_comparison"] == "not_performed: other.json has no stage_members facts"


def test_malformed_structure_file_is_rejected(tmp_path, real_lut):
    side = tmp_path / "cs.structure.json"
    side.write_text(json.dumps({"schema_version": "1"}), encoding="utf-8")
    r = _run(tmp_path, real_lut, H.CS)
    # 계약 1절: structure 거부 -> 7 또는 2(정지 전 단계라 s1v None), 보고서는 항상 쓰인다(4절)
    assert r.exit_code in (2, 7) and r.status == "stopped"
    assert r.s1v is None
    assert all(Path(p).is_file() for p in r.report_paths)


@pytest.mark.parametrize("circuit", ["two_stage_ota", "two_stage_ota_sf", "folded_cascode", "common_gate_amplifier",
                                     "pushpull_follower_buffer", "sf_pushpull_output_opamp"])     # [U1b] sf: 41 1.13 sf 행
def test_library_circuits_without_stop(tmp_path, real_lut, circuit):
    # oracle (a)·(d): 아래 회로의 구조 유도 손 요약은 tests/integration/test_sp1_library_summary.py -- 정지 분기·review_needed 없음
    r = run_stage_a(H.LIBRARY / (circuit + ".topology.json"), None, real_lut, output_dir=tmp_path,
                    supplies_v=H.lib_supplies(circuit))
    assert (r.exit_code, r.status) == (0, "ok"), r.report["stop_reasons"] + r.report["review_needed"]


RECORD_ONLY = {"cell_ambiguous", "pass_group_unsupported", "gate_on_current_node", "cs_output_low_impedance",
               "buffer_multi_output", "composite_dag_not_chain", "composite_over_budget", "loop_record_only",
               "cycle_enumeration_over_budget", "undeclared_loop_constraint"}     # 계약 10.3 불변량 8


@pytest.mark.parametrize("circuit,expected", [
    # [U1b] 41 1.12.3: 중첩 Miller 내부 루프는 루프 뷰가 아니고, spec 없이(전체 pm_ss_deg 미선언) 돌리면 정지가 남는다
    ("ngcc_3stage_ff", {"undeclared_loop_constraint"}),
    ("nmcnr_amplifier", {"undeclared_loop_constraint"}),
    # [U1b] 41 1.12.6: 루프 뷰 loop:M37a:Voc 의 cs_output_low_impedance 는 ac_ground_exception 사실 없이는 남는다
    ("current_reuse_telescopic_ota", {"cs_output_low_impedance"}),
])
def test_library_stopping_circuits(tmp_path, real_lut, circuit, expected):
    # [C-6] 파일럿은 library 에 structure.json(ac_ground_exception Vbias2)이 생겼다. 이 test 의 대상은 '사실 없음 -> 정지'이므로
    # 존재하지 않는 경로를 structure_path 로 주어 사실 파일 없는 상태를 그대로 검사한다(기준 불변). 사실 있는 기본 상태는 아래 test.
    r = run_stage_a(H.LIBRARY / (circuit + ".topology.json"), None, real_lut, output_dir=tmp_path,
                    supplies_v=H.lib_supplies(circuit), structure_path=tmp_path / "absent" / (circuit + ".structure.json"))
    assert (r.exit_code, r.status) == (2, "stopped")
    codes = {s.split("|")[1] for s in r.report["stop_reasons"]}
    assert codes <= RECORD_ONLY
    assert expected <= codes


PILOT = "current_reuse_telescopic_ota"


@pytest.mark.parametrize("with_spec", [False, True], ids=["no_spec", "spec"])
def test_library_pilot_default_structure_facts_give_ok(tmp_path, real_lut, with_spec):
    # [C-6] 사용자 결정 2026-10-12: library 파일럿 structure.json 의 ratified 사실 1건(ac_ground_exception Vbias2 @ loop:M37a:Voc).
    # structure_path 를 주지 않으면 topology 옆 기본 파일을 읽는다(계약 1절) -> 41 1.12.6 정지·혼재가 모두 풀려 spec 유무와 무관하게 ok/0,
    # 적용 사실은 그 1건, 정지·review 기록 0(spec 의 안정도 제약은 내부 루프 선언이 아니라 loop_cut_unmatched 도 없다).
    assert (H.LIBRARY / (PILOT + ".structure.json")).is_file()
    sp = H.LIBRARY / (PILOT + ".sizing_spec.json") if with_spec else None
    r = run_stage_a(H.LIBRARY / (PILOT + ".topology.json"), sp, real_lut, output_dir=tmp_path, supplies_v=H.lib_supplies(PILOT))
    assert (r.exit_code, r.status) == (0, "ok"), r.report["stop_reasons"] + r.report["review_needed"]
    assert [tuple(x) for x in r.report["applied_facts"]] == [("ac_ground_exception", "Vbias2")]
    assert r.report["stop_reasons"] == []
    assert r.report["review_needed"] == []


def test_non_json_structure_file_still_writes_report(tmp_path, real_lut):
    # 계약 1절 'structure 거부 -> 7 또는 2', 4절 '보고서 파일은 항상 쓰인다'
    (tmp_path / "cs.structure.json").write_text("{not json", encoding="utf-8")
    r = _run(tmp_path, real_lut, H.CS)
    assert r.exit_code in (2, 7) and r.status == "stopped"
    assert all(Path(p).is_file() for p in r.report_paths)


# ------------------------------------------------------------------ [U1b] 40 3.2-3 파이프라인 수정
def _spy_build_s1v(monkeypatch):
    """단계 A 가 부른 build_s1v 의 declared_loop_cuts 인자를 모은다(실 함수를 그대로 호출 -- 값은 바꾸지 않는다).
    단계 A 모듈이 build_s1v 를 모듈 이름으로 부른다는 것은 모듈 공개 이름(dir)으로만 확인했다(소스 미열람)."""
    import inspect
    real = stage_a_module.build_s1v
    sig = inspect.signature(real)
    seen = []

    def spy(*a, **k):
        bound = sig.bind(*a, **k)
        bound.apply_defaults()
        seen.append(tuple(bound.arguments.get("declared_loop_cuts") or ()))
        return real(*a, **k)

    monkeypatch.setattr(stage_a_module, "build_s1v", spy)
    return seen


def _internal_loop_decl(monkeypatch, cuts):
    """spec 파일을 실 로더로 읽은 뒤 pm_ss_deg 제약의 뷰만 내부 루프 뷰 선언 ViewDecl(mode loop, beta None, cuts)로 바꾼다.
    authoring 은 loop metric 의 명시 view 를 거부하고(SPEC_CONTRACT `view_not_applicable`·`view_shape_not_supported`) feedback 없는
    기본 유도는 beta unity·cuts () 라, 내부 루프 끊는 넷을 담은 선언은 spec 파일로 만들 수 없다(보고 대상). 그래서 로드 결과만
    바꿔 단계 A 의 수집·대조를 본다."""
    real = stage_a_module.load_sizing_spec

    def load(*a, **k):
        spec = real(*a, **k)
        cs = tuple(dataclasses.replace(c, view=ViewDecl("loop", beta=None, cuts=tuple(cuts))) if c.metric == "pm_ss_deg" else c
                   for c in spec.constraints)
        return dataclasses.replace(spec, constraints=cs)

    monkeypatch.setattr(stage_a_module, "load_sizing_spec", load)


def _codes(lines):
    return [x.split("|")[1] for x in lines]


def test_beta_loop_declaration_does_not_reach_build_s1v(tmp_path, real_lut, monkeypatch):
    # [U1b-jrules 5b5496f 결정, pipeline 계약 1절] spec feedback [Rf] 에서 유도된 β 루프 선언(ViewDecl beta declared, cuts ((Rf, inn),))
    # 은 입력 포트 절단(테스트벤치 루프)이라 declared_loop_cuts 에서 뺀다 -> build_s1v 에 inn 이 가지 않는다. oracle (a) 구성: 인자 하나만
    # 다른 두 build_s1v 호출의 키가 정답 후보 둘이다(넘기지 않은 쪽 = 단계 A).
    seen = _spy_build_s1v(monkeypatch)
    tp, sp = J.write_pair(tmp_path, J.UGB, feedback=("Rf",))
    r = run_stage_a(tp, sp, real_lut, output_dir=tmp_path / "o", supplies_v=H.SUPPLIES)
    assert r.s1v is not None
    assert seen and all("inn" not in cuts for cuts in seen)
    monkeypatch.undo()
    topo = load_topology(str(tp))
    spec = load_sizing_spec(str(sp), topo, metric_catalog())
    s1 = build_s1(topo, H.SUPPLIES)
    kw = {"count_budget": r.report["count_budget"], "stop_on_unsupported": False}
    with_cut = build_s1v(s1, spec, declared_loop_cuts=("inn",), **kw)
    without = build_s1v(s1, spec, **kw)
    assert with_cut.key[-1] != without.key[-1]                    # 전제: 인자가 키를 바꾼다
    assert r.s1v.key[-1] == without.key[-1]
    assert "loop_cut_unmatched" not in _codes(r.report["review_needed"])      # 대조에서도 뺀다


def test_internal_loop_declaration_reaches_build_s1v(tmp_path, real_lut, monkeypatch):
    # [U1b-jrules, pipeline 계약 1절] 내부 루프 뷰 선언(mode loop, beta != declared)의 끊는 넷은 build_s1v(declared_loop_cuts=) 로 간다.
    # 손 회로 CMFB(s1v_hand)의 엔진 루프 뷰 끊는 넷 = cm(test_loop_cuts 손 유도: (M5, cm) 이 두 루프 모두의 최다 후보).
    seen = _spy_build_s1v(monkeypatch)
    _internal_loop_decl(monkeypatch, (("M5", "cm"),))
    tp, sp = J.write_pair(tmp_path, H.CMFB)
    r = run_stage_a(tp, sp, real_lut, output_dir=tmp_path / "o", supplies_v=H.SUPPLIES)
    assert r.s1v is not None
    assert seen and all(set(cuts) == {"cm"} for cuts in seen)


def test_unmatched_internal_loop_cut_is_review(tmp_path, real_lut, monkeypatch):
    # [U1b-jrules 821fb72, graph 계약 10.2] 선언 끊는 넷이 어느 엔진 루프 뷰 끊는 gate 넷(CMFB: cm 하나)에도 맞지 않으면
    # loop_cut_unmatched(review_needed, 뷰 "", subject = 그 넷)가 보고서 review_needed 에 오른다(S1v 에는 넣지 않는다).
    # cmfb 는 루프 위 넷이지만 끊는 점(M5 gate cm)이 아니다 -> 불일치. 회로 자체는 기록 없는 ok(아래 일치 test)이므로 상태는 review_needed/2.
    _internal_loop_decl(monkeypatch, (("M3", "cmfb"),))
    tp, sp = J.write_pair(tmp_path, H.CMFB)
    r = run_stage_a(tp, sp, real_lut, output_dir=tmp_path / "o", supplies_v=H.SUPPLIES)
    assert (r.exit_code, r.status) == (2, "review_needed")
    hits = [x.split("|")[:4] for x in r.report["review_needed"] if x.split("|")[1] == "loop_cut_unmatched"]
    assert hits == [["review_needed", "loop_cut_unmatched", "", "cmfb"]]
    assert "loop_cut_unmatched" not in {f.code for f in r.s1v.findings} | {f.code for v in r.s1v.views for f in v.findings}


def test_matching_internal_loop_cut_leaves_no_record(tmp_path, real_lut, monkeypatch):
    _internal_loop_decl(monkeypatch, (("M5", "cm"),))
    tp, sp = J.write_pair(tmp_path, H.CMFB)
    r = run_stage_a(tp, sp, real_lut, output_dir=tmp_path / "o", supplies_v=H.SUPPLIES)
    assert (r.exit_code, r.status) == (0, "ok"), r.report["review_needed"] + r.report["stop_reasons"]
    assert "loop_cut_unmatched" not in _codes(r.report["review_needed"])


@pytest.mark.parametrize("feedback", [("Rf",), ()], ids=["beta_declared", "beta_unity"])
def test_real_spec_beta_loops_never_report_unmatched(tmp_path, real_lut, feedback):
    # 실 spec 파일 그대로(조작 없음): β 루프(declared, 끊는 넷 inn 은 엔진 루프 뷰에 없음)와 unity(cuts 없음) 모두 대조 대상이 아니다
    tp, sp = J.write_pair(tmp_path, J.UGB, feedback=feedback)
    r = run_stage_a(tp, sp, real_lut, output_dir=tmp_path / "o", supplies_v=H.SUPPLIES)
    assert r.s1v is not None
    assert "loop_cut_unmatched" not in _codes(r.report["review_needed"])


def test_cuts_only_from_pm_constraints(tmp_path, real_lut):
    # 40 3.2-3 파이프라인 2: cuts 는 안정도 제약(pm_*) 행이 가리키는 루프 뷰의 끊는 넷만. pm 제약이 없으면(feedback 선언만) 넘기지 않는다
    tp, sp = J.write_pair(tmp_path, J.UGB, feedback=("Rf",), pm=False)
    r = run_stage_a(tp, sp, real_lut, output_dir=tmp_path / "o", supplies_v=H.SUPPLIES)
    topo = load_topology(str(tp))
    spec = load_sizing_spec(str(sp), topo, metric_catalog())
    s1 = build_s1(topo, H.SUPPLIES)
    kw = {"count_budget": r.report["count_budget"], "stop_on_unsupported": False}
    without = build_s1v(s1, spec, **kw)
    with_cut = build_s1v(s1, spec, declared_loop_cuts=("inn",), **kw)
    assert r.s1v.key[-1] == without.key[-1] != with_cut.key[-1]


def _lib_copy(tmp_path, circuit, spec=True):
    import shutil
    d = tmp_path / circuit
    d.mkdir()
    shutil.copy(H.LIBRARY / (circuit + ".topology.json"), d)
    if spec:
        shutil.copy(H.LIBRARY / (circuit + ".sizing_spec.json"), d)
    return d / (circuit + ".topology.json"), (d / (circuit + ".sizing_spec.json")) if spec else None


def test_dc_role_facts_are_loaded_before_build_s1(tmp_path, real_lut):
    # 40 3.2-3 파이프라인 1·3 + 사실 표: ngcc 에 spec(pm_ss_deg 선언 -> compensation_internal 정지 없음) + dc_role override 사실
    # M8·M14 = signal 을 주면 남은 review(dc_role_unresolved_group)가 사라져 ok/0. 사실이 build_s1 전에 로드되지 않으면 S1 DC 역할이
    # 그대로라 review 가 남는다. 사실 없이 같은 입력이면 review_needed/2.
    tp, sp = _lib_copy(tmp_path, "ngcc_3stage_ff")
    plain = run_stage_a(tp, sp, real_lut, output_dir=tmp_path / "o0", supplies_v=H.lib_supplies("ngcc_3stage_ff"))
    assert (plain.exit_code, plain.status) == (2, "review_needed")
    assert [x.split("|")[1] for x in plain.report["review_needed"]] == ["dc_role_unresolved_group"]
    topo_fp = plain.s1v.key[0].topology_fp
    J.write_structure(tp.parent / "ngcc_3stage_ff.structure.json", topo_fp, structure_rule_fp(),
                      [J.fact_dict("dc_role", "M8", "signal", "F-3"), J.fact_dict("dc_role", "M14", "signal", "F-3")])
    r = run_stage_a(tp, sp, real_lut, output_dir=tmp_path / "o1", supplies_v=H.lib_supplies("ngcc_3stage_ff"))
    assert (r.exit_code, r.status) == (0, "ok"), r.report["review_needed"] + r.report["stop_reasons"]
    assert sorted(map(tuple, r.report["applied_facts"])) == [("dc_role", "M14"), ("dc_role", "M8")]
    assert r.s1v.key[0].facts_fp != "none"                        # 40 3.2-3 파이프라인 3: S1 키에 사실 지문


def test_view_scoped_ground_fact_clears_pilot_stop(tmp_path, real_lut):
    # 40 3.2-3 사실 표 파일럿 ac_ground_exception Vbias2 @ loop:M37a:Voc -> 41 1.12.6 정지·혼재 해소 -> ok/0(spec 없이)
    tp, _ = _lib_copy(tmp_path, "current_reuse_telescopic_ota", spec=False)
    plain = run_stage_a(tp, None, real_lut, output_dir=tmp_path / "o0", supplies_v=H.lib_supplies("current_reuse_telescopic_ota"))
    J.write_structure(tp.parent / "current_reuse_telescopic_ota.structure.json", plain.s1v.key[0].topology_fp, structure_rule_fp(),
                      [J.fact_dict("ac_ground_exception", "Vbias2", "loop:M37a:Voc", "C-6")])
    r = run_stage_a(tp, None, real_lut, output_dir=tmp_path / "o1", supplies_v=H.lib_supplies("current_reuse_telescopic_ota"))
    assert (r.exit_code, r.status) == (0, "ok"), r.report["review_needed"] + r.report["stop_reasons"]
    assert [tuple(x) for x in r.report["applied_facts"]] == [("ac_ground_exception", "Vbias2")]


def test_fact_file_written_with_old_s1v_rule_fp_is_stale(tmp_path, real_lut):
    # 40 3.2-3 rule_hash: 단계 A 는 structure_rule_fp 로 stale 을 판정한다 -- s1v_rule_fp 로 쓴 파일은 적용하지 않고 stale(review)
    tp, sp = _lib_copy(tmp_path, "ngcc_3stage_ff")
    first = run_stage_a(tp, sp, real_lut, output_dir=tmp_path / "o0", supplies_v=H.lib_supplies("ngcc_3stage_ff"))
    J.write_structure(tp.parent / "ngcc_3stage_ff.structure.json", first.s1v.key[0].topology_fp, s1v_rule_fp(),
                      [J.fact_dict("dc_role", "M8", "signal", "F-3"), J.fact_dict("dc_role", "M14", "signal", "F-3")])
    r = run_stage_a(tp, sp, real_lut, output_dir=tmp_path / "o1", supplies_v=H.lib_supplies("ngcc_3stage_ff"))
    assert r.status == "review_needed"
    codes = [x.split("|")[1] for x in r.report["review_needed"]]
    assert "structure_fact_stale" in codes and "dc_role_unresolved_group" in codes
    assert r.report["applied_facts"] == []


def test_structure_rejection_stops_before_build_s1(tmp_path, real_lut):
    # 40 3.2-3 파이프라인 1: 사실 로드가 build_s1 앞 -> 거부(알 수 없는 concept)면 S1·S1v 를 만들지 않고 exit 7, 보고서는 쓴다
    # [U17 ①-d] 40 v1.6 은 l_owner 를 concept 어휘에 넣었다(C-3) -- 어휘 밖 예를 frobnicate 로 바꿈
    side = tmp_path / "cs.structure.json"
    J.write_structure(side, "0" * 64, structure_rule_fp(), [J.fact_dict("frobnicate", "M1", "M1")])
    r = _run(tmp_path, real_lut, H.CS)
    assert (r.exit_code, r.status) == (7, "stopped")
    assert r.s1v is None and r.report["tables"] is None
    assert len(r.report["stop_reasons"]) == 1
    assert "structure_concept_unknown" in r.report["stop_reasons"][0]
    assert r.report["stop_reasons"][0].startswith("A2_structure_json")     # pipeline 계약 1절 [U1b] 단계 이름
    assert all(Path(p).is_file() for p in r.report_paths)


# ---------------------------------------------------------------- [U17 ①-d] 40 v1.6 §3.2-3 `l_owner` 사실(C-3)·§6-5 crosstab·diff_pair review

def test_nmcnr_l_owner_fact_clears_name_order_review(tmp_path, real_lut):
    # 40 §3.2-3 사실 표 "nmcnr_amplifier | `l_owner` | `["M104","M105"]` | `M105` | override -- 결정(사용자 결정 2026-10-12 "C-3은 네
    # 제안대로 해") ... 단계 A의 `l_owner_name_order` review가 사라지는지 확인한다" + '사실 파일 상태': "쓴 뒤 nmcnr 단계 A 보고서에서
    # `l_owner_name_order` review가 없어져야 한다". 사실 파일은 library 사본 옆(tmp)에 이 test 가 쓴다(topology 지문 = 사실 없는 첫 실행의
    # S1 키, rule_hash = structure_rule_fp() -- 기존 test_dc_role_facts_are_loaded_before_build_s1 과 같은 준비).
    tp, sp = _lib_copy(tmp_path, "nmcnr_amplifier")
    sup = H.lib_supplies("nmcnr_amplifier")
    plain = run_stage_a(tp, sp, real_lut, output_dir=tmp_path / "o0", supplies_v=sup)
    assert any("|l_owner_name_order|" in x for x in plain.report["review_needed"])          # 전제: 사실 없이는 review
    J.write_structure(tp.parent / "nmcnr_amplifier.structure.json", plain.s1v.key[0].topology_fp, structure_rule_fp(),
                      [J.fact_dict("l_owner", '["M104","M105"]', "M105", "C-3")])
    r = run_stage_a(tp, sp, real_lut, output_dir=tmp_path / "o1", supplies_v=sup)
    assert plain.report["stop_reasons"] == [] and len(plain.report["review_needed"]) == 1   # 전제: 남은 review 는 이것 하나
    assert (r.exit_code, r.status) == (0, "ok"), r.report["review_needed"] + r.report["stop_reasons"]
    assert not any("l_owner_name_order" in x for x in r.report["review_needed"]), r.report["review_needed"]
    assert ("l_owner", '["M104","M105"]') in [tuple(x) for x in r.report["applied_facts"]]
    assert {lc.members: lc.owner for lc in r.s1v.l_classes}[("M104", "M105")] == "M105"
    assert r.s1v.key != plain.s1v.key                                       # 같은 topology 라도 사실이 다르면 다른 키


FDIFF_CL = H.topo("fdiffcl", tuple((e["name"], e["kind"], e["drain"], e["gate"], e["source"]) for e in J.FDIFF["netlist"]),
                  {"inp": H.DIFF_P, "inn": H.DIFF_N, "op": H.OUT_P, "om": H.OUT_N},
                  passives=(("CL1", "capacitor", ("om", "gnd")), ("CL2", "capacitor", ("op", "gnd"))), bias=("vb", "vbp"))


def _find_key(obj, key):
    """보고서(dict/list 중첩) 안에서 key 의 값을 모두 찾는다. 위치는 design 이 정하지 않았다('보고한다'만)."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                out.append(v)
            out.extend(_find_key(v, key))
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            out.extend(_find_key(v, key))
    return out


def _names_in(value):
    import re
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", json.dumps(value, default=repr)))


def test_orbit_matching_crosstab_is_reported(tmp_path, real_lut):
    # 40 §6-5: "대신 대조 표 `orbit_matching_crosstab`을 보고한다. MOS 궤도마다 그 궤도가 걸친 matching 레코드, 그리고 matching 레코드마다
    # 그 레코드가 걸친 궤도를 적는다. 수동소자 궤도(Cc1/Cc2, Rz1/Rz2, R1/R2, CL1/CL2 등)는 matching 대상이 아니므로 표에서 뺀다."
    # 손 회로 FDIFF_CL(완전 차동 + 출력마다 CL): MOS 궤도마다 행이 있으므로 MOS 이름 5개가 모두 나오고, 수동소자 CL1·CL2 는 나오지 않는다.
    # 표의 위치·행 형식은 design 이 정하지 않았다 -> 단계 A 보고서 어디든 그 키로 찾는다(이름 미정 항목으로 보고).
    r = _run(tmp_path, real_lut, FDIFF_CL)
    found = _find_key(r.report, "orbit_matching_crosstab")
    assert len(found) == 1, "orbit_matching_crosstab 이 단계 A 보고서에 정확히 한 번"
    names = _names_in(found[0])
    assert {"M0", "M1", "M2", "M3", "M4"} <= names
    assert not ({"CL1", "CL2"} & names)


def test_diff_pair_members_in_different_orbits_is_review_needed(tmp_path, real_lut):
    # 40 §6-5: "`review_needed`로 올리는 것은 하나뿐이다. `diff_pair` 레코드의 두 멤버가 같은 궤도에 들지 않는 경우다."
    # 합성 최소쌍: FDIFF(완전 차동, M1<->M2 반사가 자기동형 -> diff_pair {M1, M2} 같은 궤도 -> 이 review 없음)와 FDIFF_CX(op 쪽에만 Cx ->
    # op<->om 반사가 자기동형이 아니다 -> M1·M2 다른 궤도 -> review). diff_pair 레코드 {M1, M2}(공통 source tail, gate inp/inn)는 둘에 같다.
    # review 코드 이름은 design 에 없다 -> 'M1·M2 둘을 함께 적은 review 항목'으로 본다(FDIFF_CX 의 다른 review 는 l_owner_name_order {M3, M4}).
    def pair_reviews(rep):
        return [x for x in rep["review_needed"] if "M1" in x.split("|")[3].replace(" ", "").split(",")
                and "M2" in x.split("|")[3].replace(" ", "").split(",")]
    sym = _run(tmp_path, real_lut, J.FDIFF, out="o_sym")
    asym = _run(tmp_path, real_lut, J.FDIFF_CX, out="o_asym")
    assert pair_reviews(sym.report) == []
    assert len(pair_reviews(asym.report)) == 1, asym.report["review_needed"]
    assert asym.status == "review_needed"
