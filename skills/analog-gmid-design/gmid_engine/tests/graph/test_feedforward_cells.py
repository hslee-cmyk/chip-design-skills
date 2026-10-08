"""graph/feedforward_cells.py -- feedforward 셀(설계 41 1.12.2 J-A, master edb5ee0 정정, 계약 graph 10.6).

oracle (a) 손 유도 -- FF3(jrules_hand): 3단 CS 사슬 in -M1-> a -M2-> b -M3-> out, 1단 우회 CS M4(a -> out), 2단 우회 미러 가지
M5(in -> x) + diode Pd(x) + 미러 Pm(x -> out), x 의 바이어스 전류원 Nb.
- 엣지 비용(41 1.6): gate->drain 1, 단 gate 가 diode 단자면 0. D_max(최대 비용): a 1, b 2, out 3, x 1.
- 주경로(slack 0 엣지만): in -M1-> a -M2-> b -M3-> out. 주경로 셀 = {M1, M2, M3}.
- FF 진입 엣지(slack > 0, 주경로 블록 출력노드로 들어옴): M4(a -> out) slack = 3 - 1 - 1 = 1, Pm(x -> out) slack = 3 - 1 - 0 = 2.
- 묶음: Pm 에서 거꾸로 x(비주경로) -> M5 gate in(주경로 넷) => 탭 in, 셀 {M5, Pm}, x 에 drain 이 붙은 바이어스 Nb(ff_bias),
  diode Pd(ff_load). M4 => 탭 a, 셀 {M4}.
- 우회: in -> out 주경로가 지나는 블록 출력노드 a·b 를 FF 가 지나지 않음 -> 처음 우회 블록 (a,). a -> out 은 b 를 우회 -> (b,).
- 부호 = 경로 셀 부호의 곱(CS -1): M5·Pm = +1, M4 = -1.
- FF 셀을 뺀 주경로 블록 사슬: (a,) stage 1 -> (b,) stage 2 -> (out,) stage 3, 복합 블록 0(FF 합류는 복합 블록 아님).
- 비율 후보: FF 마다 (FF, 처음 우회 블록), 관계 r_ff = 1, 출처 You et al. JSSC 1997 / Leung & Mok TCAS-I 2001.
무동작: 우회 없는 병렬 합류(PAR2 -- 그리고 FF 후보가 없으니 main_path_ambiguous 도 없다, edb5ee0), 블록 내부 노드로 들어오는
셀(K8: 2단 캐스코드 내부 노드 c 로 들어오는 Mk -- c 는 블록 출력노드가 아니라 FF 가 아니다).
main_path_ambiguous: 주경로 최장 경로가 둘(a -M2-> b -M3-> out, a -M6-> c -M7-> out)이고 셀 집합이 다르며 FF 후보가 있는 뷰(FFAMB).
oracle (d): library ngcc_3stage_ff -- 41 1.13 기대 행 + 40 3.2-3 사실 표(FF1 = {M6B, M7}·load M6A·bias M5, 탭 ND, merge Vout;
FF2 = {M14}, 탭 V1, merge Vout, 주경로 V1 -> V2 -> Vout, 복합 블록 0). 나머지 8회로 FF 0.
graph `.py` 소스는 열람하지 않았다.
"""
from __future__ import annotations

import pytest

from gmid_engine.graph import FeedforwardCell, FfRatioCandidate

import jrules_hand as J
import s1v_hand as H

SOURCE = "You, Embabi, Sanchez-Sinencio, IEEE JSSC 32(12), 1997; Leung & Mok, IEEE TCAS-I 48(9), 2001"   # 41 1.12.2-5 출처


def _ff(v):
    return {(c.tap, c.merge): (c.cells, c.bias_cells, c.load_cells, c.bypassed_blocks[0] if c.bypassed_blocks else None, c.sign)
            for c in v.feedforward}


def test_three_stage_bundles_tap_merge_and_sign(tmp_path):
    _, s1v = H.build(tmp_path, J.FF3)
    v = H.view(s1v)
    assert _ff(v) == {
        ("in", "out"): (("M5", "Pm"), ("Nb",), ("Pd",), ("a",), 1),
        ("a", "out"): (("M4",), (), (), ("b",), -1),
    }
    assert all(isinstance(c, FeedforwardCell) and c.status == "derived" for c in v.feedforward)


def test_bypassed_blocks_lead_with_first_bypassed(tmp_path):
    # in -> out 은 a·b 둘 다 우회(주경로 순서), a -> out 은 b 만
    _, s1v = H.build(tmp_path, J.FF3)
    got = {(c.tap, c.merge): c.bypassed_blocks for c in H.view(s1v).feedforward}
    assert got == {("in", "out"): (("a",), ("b",)), ("a", "out"): (("b",),)}


def test_main_path_and_block_chain_without_ff_cells(tmp_path):
    _, s1v = H.build(tmp_path, J.FF3)
    v = H.view(s1v)
    assert set(v.main_path) == {"M1", "M2", "M3"}
    assert {b.key: (b.kind, b.stage) for b in v.blocks} == {("a",): ("gain", 1), ("b",): ("gain", 2), ("out",): ("gain", 3)}
    assert v.composites == ()
    # 계약 불변량 (b): FF 묶음 소자는 블록 역할 어디에도 없고 셀 목록에는 있다
    ff_devs = {"M4", "M5", "Pm", "Pd", "Nb"}
    in_blocks = {d for b in v.blocks for d, _ in b.roles}
    assert not (ff_devs & in_blocks)
    assert ff_devs <= set(H.cells(v))
    assert "composite_block_pending_ratify" not in H.all_codes(s1v)


def test_ratio_candidates_per_bundle(tmp_path):
    _, s1v = H.build(tmp_path, J.FF3)
    got = {(c.bypassed_block, c.relation, c.source) for c in H.view(s1v).ff_ratio_candidates}
    assert all(isinstance(c, FfRatioCandidate) for c in H.view(s1v).ff_ratio_candidates)
    assert {b for b, _, _ in got} == {("a",), ("b",)}
    assert {s for _, _, s in got} == {SOURCE}
    assert all("= 1" in r for _, r, _ in got)            # 관계 r_ff = 1 (41 1.12.2-5)
    ids = {c.id for c in H.view(s1v).feedforward}
    assert {c.ff for c in H.view(s1v).ff_ratio_candidates} == ids


def test_parallel_merge_without_bypass_is_not_feedforward(tmp_path):
    # PAR2: a 에서 갈라진 두 2단 갈래가 out 에서 합류 -- 우회한 블록 출력노드가 없고 FF 진입(slack > 0) 엣지도 없다.
    # FF 후보가 없으니 주경로 모호 판정도 하지 않는다(edb5ee0: 병렬 버퍼 가지 오발동 방지)
    _, s1v = H.build(tmp_path, J.PAR2)
    v = H.view(s1v)
    assert v.feedforward == () and v.ff_ratio_candidates == ()
    assert "main_path_ambiguous" not in H.all_codes(s1v)


def test_main_path_ambiguous_only_with_ff_candidate(tmp_path):
    # FFAMB: 최장 경로 둘의 셀 집합이 다르고({M1, M2, M3} / {M1, M6, M7}) FF 후보(미러 가지)가 있다 -> review_needed
    _, s1v = H.build(tmp_path, J.FFAMB)
    hits = [f for f in H.view(s1v).findings if f.code == "main_path_ambiguous"]
    assert [h.severity for h in hits] == ["review_needed"]
    assert {"M2", "M3", "M6", "M7"} <= set(hits[0].subject)


def test_side_injection_into_block_internal_node_is_not_feedforward(tmp_path):
    # K8: 합류 노드 조건(41 1.12.2-2) -- m 은 주경로 블록 출력노드여야 한다. Mk 는 2단 블록(M2 input, Mc cascode, 출력 out)의
    # 내부 노드 c 로 들어온다 -> 측면 주입(K8)이지 feedforward 가 아니다
    _, s1v = H.build(tmp_path, J.K8)
    v = H.view(s1v)
    outputs = {n for b in v.blocks for n in b.key}
    assert "c" not in outputs
    assert v.feedforward == ()
    assert v.ff_ratio_candidates == ()


def test_merge_is_always_a_main_block_output(tmp_path):
    # 41 1.12.2-2 합류 노드 조건을 모든 손 회로·library 회로에 건다
    for doc in (J.FF3, J.FFAMB, J.PAR2, J.K8, H.FF, H.MILLER, H.FOLDED):
        _, s1v = H.build(tmp_path, doc)
        for v in s1v.views:
            outputs = {n for b in v.blocks for n in b.key}
            assert {c.merge for c in v.feedforward} <= outputs, doc["topology_name"]


def test_two_stage_ff_toy_is_one_bundle_not_composite(tmp_path):
    # s1v_hand.FF: 1단 CS M1(in -> a)·2단 CS M3(a -> out) + 병렬 CS M4(in -> out). M4 진입 slack = 2 - 0 - 1 = 1, merge out = 2단
    # 블록 출력노드, 탭 in, 우회 블록 (a,), 부호 -1. FF 합류는 복합 블록으로 묶지 않는다(41 1.9)
    _, s1v = H.build(tmp_path, H.FF)
    v = H.view(s1v)
    assert _ff(v) == {("in", "out"): (("M4",), (), (), ("a",), -1)}
    assert v.composites == ()


def test_ngcc_bundles_match_design_table():
    _, s1v = H.build_lib("ngcc_3stage_ff")
    v = H.view(s1v)
    # 41 1.13 / 40 3.2-3: FF1 탭 ND(1단 블록 내부 미러 입력 넷) merge Vout, 처음 우회 = 1단 블록 (V1,); FF2 탭 V1, 우회 (V2,).
    # 부호: FF1 = M6B(CS -1)·M7(CS -1) = +1, FF2 = M14(CS) = -1
    assert _ff(v) == {
        ("ND", "Vout"): (("M6B", "M7"), ("M5",), ("M6A",), ("V1",), 1),
        ("V1", "Vout"): (("M14",), (), (), ("V2",), -1),
    }
    assert {b.key: b.stage for b in v.blocks} == {("V1",): 1, ("V2",): 2, ("Vout",): 3}
    assert v.composites == ()
    assert {c.bypassed_block for c in v.ff_ratio_candidates} == {("V1",), ("V2",)}


@pytest.mark.parametrize("name", ["common_gate_amplifier", "current_reuse_telescopic_ota", "folded_cascode", "nmcnr_amplifier",
                                  "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota", "two_stage_ota_sf"])
def test_other_library_circuits_have_no_feedforward(name):
    # 41 1.13 무동작 행(sf M17·M20 은 merge 가 블록 출력노드가 아니라 K8). 주경로 모호도 없다(FF 후보 없음, edb5ee0)
    _, s1v = H.build_lib(name)
    assert all(v.feedforward == () and v.ff_ratio_candidates == () for v in s1v.views)
    assert "main_path_ambiguous" not in H.all_codes(s1v)


def test_name_bijection_maps_bundles(tmp_path):
    # 41 1.11 불변식(이름 전단사 + netlist 섞기): 묶음·탭·merge·우회 블록·부호가 사상으로만 바뀐다
    doc = J.FF3
    nets = sorted(H.json_nets(doc))
    elems = sorted(H.json_mos(doc))
    nm = {n: "w%02d" % (len(nets) - i) for i, n in enumerate(nets)}
    dm = {n: "E%02d" % (len(elems) - i) for i, n in enumerate(elems)}
    _, base = H.build(tmp_path, doc, stem="base")
    _, moved = H.build(tmp_path, H.rename(doc, nm, dm, seed=7), stem="moved", supplies={nm[r]: v for r, v in H.SUPPLIES.items()})

    def canon(v, n, d):
        return {(n(c.tap), n(c.merge), frozenset(map(d, c.cells)), frozenset(map(d, c.bias_cells)), frozenset(map(d, c.load_cells)),
                 tuple(tuple(sorted(map(n, k))) for k in c.bypassed_blocks), c.sign) for c in v.feedforward}

    ident = lambda x: x  # noqa: E731
    assert canon(H.view(base), nm.get, dm.get) == canon(H.view(moved), ident, ident)
    assert {dm[x] for x in H.view(base).main_path} == set(H.view(moved).main_path)
