"""U1b J 구조 규칙 -- library 9회로 발동표와 이름 전단사 불변(설계 41 1.12·1.13, 40 3.2-3·11 U1b 행, 체크리스트 D-J1~D-J6).

발동표(oracle (a) 손 유도 -- 각 회로 topology JSON 에 41 1.12 규칙을 손으로 적용, 41 1.13 기대 행은 기준값이 아니라 대조 대상):
| 회로 | 복합 diode(1.12.1) | feedforward(1.12.2) 탭->merge | 루프 역할(1.12.1-3·1.12.3) | 루프 뷰·극성(1.12.4) | 단계 A(spec·사실 파일 없음) |
|---|---|---|---|---|---|
| common_gate_amplifier | 0 | 0 | 없음 | 없음 | ok |
| two_stage_ota | 0 | 0 | 없음(Miller 사이클만) | 없음 | ok |
| two_stage_ota_sf | 0 | 0 | 없음 | 없음 | ok |
| folded_cascode | 0 | 0 | 없음 | 없음 | ok |
| pushpull_follower_buffer | 0 | 0(병렬 버퍼 가지, FF 후보 없음 -> 모호 판정 안 함) | 없음 | 없음 | ok |
| sf_pushpull_output_opamp | M5·M6·M7·M8·M13·M14 | 0(M17·M20 은 K8) | composite_diode_internal 3({N1,N5},{N2,N7},{N12,N13}) | 없음 | ok |
| current_reuse_telescopic_ota | M58·M63 | 0 | loop_view loop:M37a:Voc | loop:M37a:Voc, 극성 -1 | stopped: cs_output_low_impedance |
| ngcc_3stage_ff | 0 | ND->Vout, V1->Vout | compensation_internal loop:M8:V1 | 없음 | stopped: undeclared_loop_constraint (+ review dc_role_unresolved_group) |
| nmcnr_amplifier | 0 | 0 | compensation_internal loop:M201:NodeM2 | 없음 | stopped: undeclared_loop_constraint (+ review l_owner_name_order) |
손 유도 요지: 복합 diode 걷기는 `tests/graph/jrules_hand.py` LIB_COMPOSITE 주석. FF 는 ngcc 만 -- 주경로 V1 -> V2 -> Vout 에서 M14(V1 ->
Vout)는 2단 블록을, M6B -> NX -> M7 가지는 1·2단 블록을 우회해 블록 출력노드 Vout 으로 들어온다. 나머지 회로는 비주경로 신호 셀이
블록 출력노드로 들어오는 우회 경로가 없다. ngcc·nmcnr 의 3단 중첩 Miller 내부 루프는 사이클 위 능동 셀이 모두 순방향 셀이라
compensation_internal(1.12.3 (a)(b)). 파일럿 CM 루프는 M37a·M7 이 순방향 밖이라 루프 뷰가 남고, DC 사이클 4개가 모두 -1
(CS 셋의 곱), Cc–Rz 경유 2개는 ac_only. nmcnr {M104, M105} 는 tail·diode 기준·stage 시작 셀이 없는 name_order 동률이고 단일 종단
미러 부하 때문에 한 자기동형 궤도가 아니라 edb5ee0 예외에 들지 않는다.
[C-6] 파일럿은 library structure.json(ac_ground_exception Vbias2, 사용자 결정 2026-10-12)이 있어 기본 상태는 spec 유무와 무관하게
ok/0(정지·review 0, 적용 사실 그 1건). 위 표의 단계 A 열은 사실 파일 없는 상태이므로 그 test 는 없는 경로를 structure_path 로 준다.
41 1.13 과 다른 점(보고 대상): sf composite_diode_internal 은 9 가 아니라 3(묶음 내부 혼재 넷을 판정하지 않아 그 넷을 지나는 사이클이
없다 -- tests/graph/test_loop_roles.py 주석), 파일럿 레플리카 루프는 신호 사이클이 없어 0.
spec 있는 단계 A(ngcc·nmcnr spec 은 pm_ss_deg 선언): compensation_internal 정지가 풀려 ngcc = review_needed(dc_role 그룹),
nmcnr = review_needed(l_owner_name_order).
[U1b-jrules] spec 있는 단계 A 9회로 표(손 유도, loop_cut_unmatched 는 어느 회로에도 없음 -- 내부 루프 선언 없음):
| 회로 | spec 안정도 선언 | 단계 A |
|---|---|---|
| ngcc_3stage_ff | pm_ss_deg unity | review_needed {dc_role_unresolved_group} |
| nmcnr_amplifier | pm_ss_deg unity | review_needed {l_owner_name_order} |
| current_reuse_telescopic_ota | pm_ss_deg β(Cf1·Cf2), pm_cm_ss_deg(cm_output) | stopped {cs_output_low_impedance} + review 혼재(loop:M37a:Voc 한정) |
| sf_pushpull_output_opamp·two_stage_ota·two_stage_ota_sf | pm_ss_deg unity(Q-S2, 2026-10-14) | ok |
| 나머지 3회로(common_gate·folded·pushpull) | 없음 | ok |
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

GRAPH_TESTS = Path(__file__).resolve().parents[1] / "graph"
if str(GRAPH_TESTS) not in sys.path:
    sys.path.insert(0, str(GRAPH_TESTS))

from gmid_engine.authoring import load_topology  # noqa: E402
from gmid_engine.core import Projection  # noqa: E402
from gmid_engine.graph import build_s1, build_s1v, composite_diodes, s1_dc_roles  # noqa: E402
from gmid_engine.pipeline import run_stage_a  # noqa: E402
from gmid_engine.search import open_run  # noqa: E402

import jrules_hand as J  # noqa: E402
import s1v_hand as H  # noqa: E402

# [xrun, 사용자 결정 J-1 2026-10-15] run_stage_a 는 PDK 선언·LUT 생성 규칙 선언과 두 선언 경로 인자를 받지 않는다(S0 키에만 쓰이던 인자 --
# 설계 40 v1.10 §2.4.3 'PDK 선언 경로 인자와 진입 sha 대조' 삭제, interface card C1). 옛 상수 PDK_DECL·LUT_RULE_DECL·두 경로를 지웠다.

NINE = ("common_gate_amplifier", "current_reuse_telescopic_ota", "folded_cascode", "ngcc_3stage_ff", "nmcnr_amplifier",
        "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota", "two_stage_ota_sf")

# 위 표의 리터럴(손 유도). loop_roles: 루프 뷰 id 또는 사이클 노드 집합 -> 역할
TABLE = {
    "common_gate_amplifier": dict(composite=set(), ff=set(), roles={}, loop_views={}, stage_a=("ok", set(), set())),
    "two_stage_ota": dict(composite=set(), ff=set(), roles={}, loop_views={}, stage_a=("ok", set(), set())),
    "two_stage_ota_sf": dict(composite=set(), ff=set(), roles={}, loop_views={}, stage_a=("ok", set(), set())),
    "folded_cascode": dict(composite=set(), ff=set(), roles={}, loop_views={}, stage_a=("ok", set(), set())),
    "pushpull_follower_buffer": dict(composite=set(), ff=set(), roles={}, loop_views={}, stage_a=("ok", set(), set())),
    "sf_pushpull_output_opamp": dict(
        composite={"M5", "M6", "M7", "M8", "M13", "M14"}, ff=set(),
        roles={frozenset({"N1", "N5"}): "composite_diode_internal", frozenset({"N2", "N7"}): "composite_diode_internal",
               frozenset({"N12", "N13"}): "composite_diode_internal"},
        loop_views={}, stage_a=("ok", set(), set())),
    "current_reuse_telescopic_ota": dict(
        composite={"M58", "M63"}, ff=set(), roles={"loop:M37a:Voc": "loop_view"}, loop_views={"loop:M37a:Voc": -1},
        stage_a=("stopped", {"cs_output_low_impedance"}, None)),
    "ngcc_3stage_ff": dict(
        composite=set(), ff={("ND", "Vout"), ("V1", "Vout")}, roles={"loop:M8:V1": "compensation_internal"}, loop_views={},
        stage_a=("stopped", {"undeclared_loop_constraint"}, {"dc_role_unresolved_group"})),
    "nmcnr_amplifier": dict(
        composite=set(), ff=set(), roles={"loop:M201:NodeM2": "compensation_internal"}, loop_views={},
        stage_a=("stopped", {"undeclared_loop_constraint"}, {"l_owner_name_order"})),
}


def _role_key(loop_id):
    return loop_id if loop_id.startswith("loop:") else frozenset(json.loads(loop_id))


def _absent_structure(tmp_path, name):
    """[C-6] 사실 파일 없는 상태를 검사하는 test 용 -- 존재하지 않는 structure_path(library 기본 파일을 읽지 않게)."""
    return tmp_path / "absent_structure" / (name + ".structure.json")


def _s1(name, run):
    """run = [XRUN-F1 card B C6] 실행 두 객체 키워드(dict, s1v_hand.fresh_run) -- 부른 test 가 build_s1v 에도 같은 쌍을 넘긴다."""
    return build_s1(load_topology(str(H.LIBRARY / (name + ".topology.json"))), H.lib_supplies(name), **run)


@pytest.mark.parametrize("name", NINE)
def test_firing_table_structure(name):
    row = TABLE[name]
    run = H.fresh_run()
    s1 = _s1(name, run)
    s1v = H.read_s1v(build_s1v(s1, None, count_budget=H.BIG_BUDGET, stop_on_unsupported=False, **run))   # [U17 ①-b] build_s1v -> S1Graph, graph/s1v 필드 읽기
    cds = composite_diodes(Projection.from_snapshot(s1.snapshot, s1_dc_roles.reads))
    assert {m for c in cds for m in c.reference + c.cascode_members} == row["composite"]
    assert {(c.tap, c.merge) for v in s1v.views for c in v.feedforward} == row["ff"]
    assert {_role_key(r.loop_id): r.role for v in s1v.views for r in v.loop_roles} == row["roles"]
    assert {v.id: v.polarity for v in s1v.views if v.kind == "loop"} == row["loop_views"]
    assert sum(1 for v in s1v.views if v.kind == "transfer") == 1


def test_firing_table_totals():
    # D-J1: 복합 diode 발동 = sf 6 + 파일럿 2, 나머지 7회로 0. D-J2: FF 는 ngcc 만(2묶음). D-J3: compensation_internal 2(ngcc·nmcnr)
    assert sum(len(TABLE[n]["composite"]) for n in NINE) == 8
    assert [n for n in NINE if TABLE[n]["composite"]] == ["current_reuse_telescopic_ota", "sf_pushpull_output_opamp"]
    assert [n for n in NINE if TABLE[n]["ff"]] == ["ngcc_3stage_ff"]
    assert sorted(n for n in NINE if "compensation_internal" in TABLE[n]["roles"].values()) == ["ngcc_3stage_ff", "nmcnr_amplifier"]


@pytest.mark.parametrize("name", NINE)
def test_firing_table_stage_a_without_spec(name, real_lut, tmp_path):
    status, stops, reviews = TABLE[name]["stage_a"]
    donors, counters = open_run()          # [XRUN-F1 card B 규칙 M M-c] run_stage_a 호출마다 1:1
    r = run_stage_a(H.LIBRARY / (name + ".topology.json"), None, real_lut, output_dir=tmp_path, supplies_v=H.lib_supplies(name),
                    structure_path=_absent_structure(tmp_path, name), donors=donors, counters=counters)
    assert r.status == status
    assert r.exit_code == (0 if status == "ok" else 2)
    assert {x.split("|")[1] for x in r.report["stop_reasons"]} == stops
    if reviews is not None:
        assert {x.split("|")[1] for x in r.report["review_needed"]} == reviews


@pytest.mark.parametrize("name,status,reviews", [
    ("ngcc_3stage_ff", "review_needed", {"dc_role_unresolved_group"}),
    # [U17 ①-d] 40 v1.8 §3.2-3 사실 표: nmcnr library structure.json l_owner ["M104","M105"] -> M105(사용자 결정 2026-10-12 C-3) 를 쓴 뒤
    # '단계 A 의 l_owner_name_order review 가 사라져야 한다' -> ok, review 0. (사실 파일의 rule_hash 는 규칙 변경 뒤 사용자 재확인 대기 -- 재확인 전에는
    # structure_fact_stale 로 실패하는 것이 예상 상태다.)
    ("nmcnr_amplifier", "ok", set()),
    ("folded_cascode", "ok", set()),
    ("common_gate_amplifier", "ok", set()),
    ("pushpull_follower_buffer", "ok", set()),
    ("sf_pushpull_output_opamp", "ok", set()),
    ("two_stage_ota", "ok", set()),
    ("two_stage_ota_sf", "ok", set()),
])
def test_stage_a_with_library_spec(name, status, reviews, real_lut, tmp_path):
    # [U1b-jrules] 9회로 spec 이 모두 실 metric 카탈로그로 로드된다(옛 파일럿·two_stage 두 회로 A1 거부는 해소). 손 유도(spec JSON):
    # - ngcc·nmcnr: pm_ss_deg 는 feedback 없음 -> beta unity·cuts () -> declared_loop_cuts 없음, 전체 PM 선언이라 compensation_internal
    #   정지가 풀리고(41 1.12.3) 남는 review 는 구조 것뿐: ngcc {M8, M14} 기준 없는 gs 묶음(41 1.13 '남는다'), nmcnr {M104, M105}
    #   name_order 동률(한 궤도 아님 -- test_l_classes 손 확인).
    # - [library spec card, 2026-10-14 Q-S2] sf_pushpull·two_stage·two_stage_sf: pm_ss_deg >= 70 은 feedback 없음 -> beta unity·cuts () ->
    #   declared_loop_cuts 없음. 위 발동표의 루프 역할이 없거나(two_stage·two_stage_sf) composite_diode_internal 뿐(sf)이라 PM 선언이 풀 정지도
    #   새로 생길 정지도 없다 -> ok 유지.
    # - 나머지 3회로(common_gate·folded·pushpull): pm_* 제약 없음 -> 단계 A 는 spec 없는 표(TABLE)와 같은 ok.
    # - 어느 회로도 내부 루프 선언이 없으므로 loop_cut_unmatched 는 0.
    donors, counters = open_run()
    r = run_stage_a(H.LIBRARY / (name + ".topology.json"), H.LIBRARY / (name + ".sizing_spec.json"), real_lut, output_dir=tmp_path,
                    supplies_v=H.lib_supplies(name), donors=donors, counters=counters)
    assert r.status == status, r.report["stop_reasons"]
    assert r.report["stop_reasons"] == []
    assert {x.split("|")[1] for x in r.report["review_needed"]} == reviews


def test_pilot_stage_a_with_spec_has_no_unmatched_cut(real_lut, tmp_path):
    # [U1b-jrules] 파일럿 spec 의 안정도 제약 = pm_ss_deg(feedback Cf1·Cf2 -> β 루프, 끊는 넷 Vip·Vim = 입력 포트)와 pm_cm_ss_deg
    # (mode cm_output, 루프 뷰 선언 아님). 둘 다 declared_loop_cuts·대조 대상이 아니다(pipeline 계약 1절: mode loop 이고 beta != declared
    # 만) -> loop_cut_unmatched 0. 남는 것은 41 1.12.6 '사실 없이 남는' 루프 뷰 loop:M37a:Voc 의 정지 cs_output_low_impedance 이고([U17 ①-d] 옛 혼재 review 는 C-1 로 사라짐), 이 기록은 전부 그 뷰의 것이다(같은 뷰 한정 교류접지 사실이 전부 지운다 -- test_stage_a
    # test_view_scoped_ground_fact_clears_pilot_stop). spec 이 이 판정을 바꾸지 않으므로 spec 유무의 기록이 같다.
    name = "current_reuse_telescopic_ota"
    topo = H.LIBRARY / (name + ".topology.json")
    # [C-6] 이 test 는 사실 파일 없는 상태(41 1.12.6 '사실 없이 남는')를 본다 -- library 기본 structure.json 을 읽지 않게 없는 경로를 준다
    absent = _absent_structure(tmp_path, name)
    d0, c0 = open_run()
    with_spec = run_stage_a(topo, H.LIBRARY / (name + ".sizing_spec.json"), real_lut, output_dir=tmp_path / "a",
                            supplies_v=H.lib_supplies(name), structure_path=absent, donors=d0, counters=c0)
    d1, c1 = open_run()
    plain = run_stage_a(topo, None, real_lut, output_dir=tmp_path / "b", supplies_v=H.lib_supplies(name), structure_path=absent,
                        donors=d1, counters=c1)
    assert (with_spec.exit_code, with_spec.status) == (2, "stopped")
    stops = [x.split("|") for x in with_spec.report["stop_reasons"]]
    reviews = [x.split("|") for x in with_spec.report["review_needed"]]
    assert {s[1] for s in stops} == {"cs_output_low_impedance"}
    # [U17 ①-d] 41 v1.8 §1.5-4 C-1 + 보완 (가): 혼재 노드 review(mixed_drive_signal_drain)는 규칙이 대체돼 없다 -- 루프 뷰의 혼재 넷(N1a2a·N1b2b)은
    # drain 쪽 gate(Vip·Vim)가 그 뷰의 신호 넷이 아니라 전압 구동(tests/integration/test_drive_kind_mixed_9circuits.py)
    assert not {"mixed_drive_signal_drain", "mixed_drive_unresolved_group"} & {x[1] for x in reviews}
    assert "loop_cut_unmatched" not in {x[1] for x in reviews}
    assert {x[2] for x in stops + reviews} == {"loop:M37a:Voc"}
    assert sorted(with_spec.report["stop_reasons"]) == sorted(plain.report["stop_reasons"])
    assert sorted(with_spec.report["review_needed"]) == sorted(plain.report["review_needed"])


@pytest.mark.parametrize("with_spec", [False, True], ids=["no_spec", "spec"])
def test_pilot_stage_a_library_default_facts_ok(real_lut, tmp_path, with_spec):
    # [C-6] library 기본 상태(structure.json 있음, structure_path 미지정): 루프 뷰 loop:M37a:Voc 한정 교류접지 사실이 위 test 의 정지·혼재를
    # 전부 지운다(41 1.12.6) -> spec 유무와 무관하게 ok/0, 적용 사실 [(ac_ground_exception, Vbias2)], 정지·review 0.
    name = "current_reuse_telescopic_ota"
    sp = H.LIBRARY / (name + ".sizing_spec.json") if with_spec else None
    donors, counters = open_run()
    r = run_stage_a(H.LIBRARY / (name + ".topology.json"), sp, real_lut, output_dir=tmp_path, supplies_v=H.lib_supplies(name),
                    donors=donors, counters=counters)
    assert (r.exit_code, r.status) == (0, "ok"), r.report["stop_reasons"] + r.report["review_needed"]
    assert [tuple(x) for x in r.report["applied_facts"]] == [("ac_ground_exception", "Vbias2")]
    assert r.report["stop_reasons"] == []
    assert r.report["review_needed"] == []


@pytest.fixture(scope="module")
def real_lut():
    import os
    from gmid_engine.lut import LutSpec, load_lut_set, resolve_lut_location
    skill = Path(__file__).resolve().parents[3]
    loc = resolve_lut_location(str(skill / "assets" / "lut_v2_location.json"), os.environ)
    manifest = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
    kinds = {"nfet_01v8": "nmos", "pfet_01v8": "pmos"}
    from pdk_min_w import min_finger_w_m
    mins = min_finger_w_m(kinds.values())      # PDK 선언 양(card 20261104-wb1)
    spec = LutSpec(float(manifest.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), tuple(kinds.items()),
                   (("nmos", "_n"), ("pmos", "_p")))
    return load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_paths, bin_rule=loc.bin_rule_path)


# ------------------------------------------------------------------ 이름 전단사 불변(41 1.11 불변식, 9회로 전부)
def _canon(s1, s1v, nm, dm):
    """구조 결과를 사상(nm 넷, dm 원소)으로 옮긴 비교용 표현. 이름 tie-break 하나에만 기대는 L 주인(owner_rule name_order)은 주인 이름을
    비교하지 않는다(불변식 예외 -- test_s1v_build 불변량 2 와 같다)."""
    n = lambda x: nm.get(x, x)  # noqa: E731
    d = lambda x: dm.get(x, x)  # noqa: E731
    a = lambda x: nm.get(x, dm.get(x, x))  # noqa: E731   기록 대상은 넷 또는 원소

    def vid(v):
        if v.kind == "loop":
            _, dev, net = v.id.split(":")
            return ("loop", d(dev), n(net))
        return ("transfer", frozenset(n(x) for x, _ in v.excite))

    def rid(loop_id):
        if loop_id.startswith("loop:"):
            _, dev, net = loop_id.split(":")
            return ("loop", d(dev), n(net))
        return frozenset(map(n, json.loads(loop_id)))

    out = {"dc": {d(k): (v.role, v.status, v.evidence.rule, frozenset(map(d, v.evidence.group)), v.evidence.basis)
                  for k, v in s1.column("device", "dc_role")}}
    cds = composite_diodes(Projection.from_snapshot(s1.snapshot, s1_dc_roles.reads))
    out["composite"] = {(frozenset(map(d, c.members)), frozenset(map(d, c.reference)), frozenset(map(d, c.cascode_members)))
                        for c in cds}
    for v in s1v.views:
        out[vid(v)] = {
            "ground": frozenset(map(n, v.ac_ground)),
            "cells": frozenset((d(c.dev), c.kind) for c in v.cells),
            "drive": frozenset((n(i.net), i.kind) for i in v.drive_kind),
            "starts": frozenset(map(d, v.stage_starts)),
            "mirror": frozenset(map(n, v.mirror_inputs)),
            "blocks": frozenset((frozenset(map(n, b.key)), b.kind, b.stage, frozenset((d(x), r) for x, r in b.roles))
                                for b in v.blocks),
            "loops": frozenset((frozenset(map(n, lp.nodes)), lp.classes, (d(lp.cut[0]), n(lp.cut[1])) if lp.cut else (),
                                lp.polarity, lp.ac_only) for lp in v.loops),
            "main": frozenset(map(d, v.main_path)),
            "ff": frozenset((n(c.tap), n(c.merge), frozenset(map(d, c.cells)), frozenset(map(d, c.bias_cells)),
                             frozenset(map(d, c.load_cells)), tuple(frozenset(map(n, k)) for k in c.bypassed_blocks), c.sign)
                            for c in v.feedforward),
            "roles": frozenset((rid(r.loop_id), r.role, r.reason) for r in v.loop_roles),
            "polarity": v.polarity,
            "findings": sorted((f.code, f.severity, tuple(sorted(map(a, f.subject)))) for f in v.findings),
        }
    out["s1v_findings"] = sorted((f.code, f.severity, tuple(sorted(map(a, f.subject)))) for f in s1v.findings)
    out["l"] = {frozenset(map(d, lc.members)): ((None if lc.owner_rule == "name_order" else d(lc.owner)), lc.owner_rule, lc.status)
                for lc in s1v.l_classes}
    return out


@pytest.mark.parametrize("name", NINE)
def test_name_bijection_invariance(name, tmp_path):
    raw = json.loads((H.LIBRARY / (name + ".topology.json")).read_text(encoding="utf-8"))
    nm, dm = J.reverse_order_maps(raw)
    moved_raw = J.rename_library(raw, nm, dm, seed=17)
    p = tmp_path / (name + ".topology.json")
    p.write_text(json.dumps(moved_raw), encoding="utf-8")
    sup = H.lib_supplies(name)
    run_base, run_moved = H.fresh_run(), H.fresh_run()      # [XRUN-F1 card B C6] 원본·이름 바꾼 쪽 = 다른 실행
    base_s1 = _s1(name, run_base)
    base = H.read_s1v(build_s1v(base_s1, None, count_budget=H.BIG_BUDGET, stop_on_unsupported=False, **run_base))   # [U17 ①-b] build_s1v -> S1Graph, graph/s1v 필드 읽기
    moved_s1 = build_s1(load_topology(str(p)), {nm[k]: v for k, v in sup.items()}, **run_moved)
    moved = H.read_s1v(build_s1v(moved_s1, None, count_budget=H.BIG_BUDGET, stop_on_unsupported=False, **run_moved))   # [U17 ①-b] build_s1v -> S1Graph, graph/s1v 필드 읽기
    assert _canon(base_s1, base, nm, dm) == _canon(moved_s1, moved, {}, {})
