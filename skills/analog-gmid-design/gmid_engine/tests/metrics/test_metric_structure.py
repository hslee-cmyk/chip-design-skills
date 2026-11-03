"""`metric_structure` -- [U17 ①-b] 계산 블록 -> 필드 `graph/s1v: metric_structure`(40 v1.9.1 §2.4.8; 읽기 = u7_ngcc.structure_of). metrics CONTRACT 10.0·10.1: S1v -> 전달 뷰마다 `ViewStruct`(주경로 블록 사슬 stage 순, FF 묶음(merge 블록·처음 우회 블록 B_b·
그 input 셀), 첫 이득 블록 input 셀, 순방향 신호 셀 MOS, 극점 넷, 방향 셀).

oracle:
* (d) 설계 41 §1.13·40 §3.2-3 ngcc 사실 표(FF1 = {M6B, M7}·load M6A·bias M5, 탭 ND, merge Vout; FF2 = {M14}, 탭 V1, merge Vout;
  주경로 V1 -> V2 -> Vout) + 41 §1.12.2-2 'B_b = 처음 우회한 블록'(ND -> Vout 은 V1·V2 를 우회 -> (V1,), V1 -> Vout 은 V2 -> (V2,)).
* (a) FF3 손 회로(tests/graph/jrules_hand.FF3) -- test_feedforward_cells docstring 손 유도: 블록 (a,)·(b,)·(out,) stage 1·2·3, 묶음 (in->out:
  {M5, Pm} + bias Nb + load Pd, B_b (a,)), (a->out: {M4}, B_b (b,)).
* (a) 입력 셀 = 첫 이득 블록의 role input MOS(5T 입력쌍 = M1·M2, CS 사슬 첫 단 = M1). 이름 전단사 불변, 결정론.
"""
from __future__ import annotations

import sys

from gmid_engine.metrics import BlockStruct, FfStruct, MetricStructure, ViewStruct

from . import u7_ngcc as N

import jrules_hand as J  # noqa: E402  (u7_ngcc 가 tests/graph 를 sys.path 에 넣는다)
import s1v_hand as SH  # noqa: E402

assert "s1v_hand" in sys.modules


def test_ngcc_view_struct():
    ms = N.structure_of(N.s1v())
    assert isinstance(ms, MetricStructure)
    (v,) = ms.views
    assert isinstance(v, ViewStruct) and v.id == "transfer:0"
    assert dict(v.excite) == {"Vinp": 0.5, "Vinn": -0.5} and v.sense == ("Vout",)
    assert [(b.key, b.stage, b.kind) for b in v.blocks] == [(("V1",), 1, "gain"), (("V2",), 2, "gain"), (("Vout",), 3, "gain")]
    assert all(isinstance(b, BlockStruct) for b in v.blocks)
    by_key = {b.key: b for b in v.blocks}
    assert by_key[("V1",)].input_cells == ("M1", "M2") and set(by_key[("V1",)].inputs) == {"Vinn", "Vinp"}
    assert "ND" in by_key[("V1",)].nodes                      # 미러 diode 노드는 1단 블록 내부
    assert by_key[("V2",)].input_cells == ("M8",) and by_key[("Vout",)].input_cells == ("M13",)
    ff = {f.tap: f for f in v.ff}
    assert set(ff) == {"ND", "V1"} and all(isinstance(f, FfStruct) for f in v.ff)
    assert ff["ND"].merge == "Vout" and ff["ND"].members == ("M5", "M6A", "M6B", "M7")
    assert ff["ND"].merge_block == ("Vout",) and ff["ND"].bypassed == ("V1",) and ff["ND"].bypassed_input_cells == ("M1", "M2")
    assert ff["V1"].members == ("M14",) and ff["V1"].bypassed == ("V2",) and ff["V1"].bypassed_input_cells == ("M8",)
    assert v.input_cells == ("M1", "M2")
    assert {"M1", "M2", "M8", "M13", "M14", "M7"} <= set(v.signal_devices)
    assert not {"M0", "M5", "M11", "M12"} & set(v.signal_devices)          # 바이어스 전류원은 신호 셀이 아니다
    assert {"V1", "V2", "Vout"} <= set(v.pole_nets)


def test_ff3_hand_circuit(tmp_path):
    _s1, s1v = SH.build(tmp_path, J.FF3)
    (v,) = N.structure_of(s1v).views
    assert [b.key for b in v.blocks] == [("a",), ("b",), ("out",)]
    ff = {(f.tap, f.merge): f for f in v.ff}
    assert ff[("in", "out")].members == ("M5", "Nb", "Pd", "Pm") and ff[("in", "out")].bypassed == ("a",)
    assert ff[("in", "out")].bypassed_input_cells == ("M1",)
    assert ff[("a", "out")].members == ("M4",) and ff[("a", "out")].bypassed == ("b",)
    assert ff[("a", "out")].bypassed_input_cells == ("M2",)
    assert v.input_cells == ("M1",)


def test_name_bijection(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    _s1, s1v = SH.build(tmp_path / "a", J.FF3)
    nets = {"in": "q_in", "a": "zz", "b": "yy", "out": "o9", "x": "k", "vbp": "pb", "vbn": "nb"}
    devs = {"M1": "Z1", "M2": "Y2", "M3": "X3", "M4": "W4", "M5": "V5", "Pd": "A1", "Pm": "A2", "Nb": "B9",
            "P1": "C1", "P2": "C2", "P3": "C3"}
    _s1b, s1v_b = SH.build(tmp_path / "b", SH.rename(J.FF3, nets, devs, seed=3), stem="ff3r")
    (a,) = N.structure_of(s1v).views
    (b,) = N.structure_of(s1v_b).views
    f = lambda n: nets.get(n, n)  # noqa: E731
    g = lambda d: devs.get(d, d)  # noqa: E731
    assert sorted(tuple(map(f, x.key)) for x in a.blocks) == sorted(x.key for x in b.blocks)
    assert {(f(x.tap), f(x.merge)): tuple(sorted(map(g, x.members))) for x in a.ff} == \
        {(x.tap, x.merge): x.members for x in b.ff}
    assert tuple(sorted(map(g, a.input_cells))) == b.input_cells
    assert tuple(sorted(map(g, a.signal_devices))) == b.signal_devices


def test_deterministic_and_hashable_values():
    s1v = N.s1v()
    a, b = N.structure_of(s1v), N.structure_of(s1v)
    assert a == b
    hash(a)                                                    # 블록 입력 버전 지문에 드는 불변 값(tuple·str·float)


def test_non_transfer_views_skipped(tmp_path):
    """루프 뷰 등 transfer 가 아닌 뷰는 구조 입력이 없다 -- CMFB 손 회로(루프 뷰 있음)는 전달 뷰 수만큼만."""
    _s1, s1v = SH.build(tmp_path, SH.CMFB)
    kinds = [v.kind for v in s1v.views]
    ms = N.structure_of(s1v)
    assert len(ms.views) == kinds.count("transfer")
    assert len(kinds) > len(ms.views)


def test_ub1_block_members_and_view_ac_ground():
    """T-12 [UB-1 C-14] oracle (d) ngcc 사실 표(설계 41 §1.13): 블록 `members` = 정렬된 소자 이름 tuple 이고 그 블록 input 셀을 담으며,
    FF 묶음 셀(FF1 = {M5, M6A, M6B, M7}, FF2 = {M14})은 어느 블록 members 에도 없다. 뷰 `ac_ground` = 정렬 tuple 이고
    레일 ∪ bias 입력(topology 선언)을 담고 여기 넷(Vinp·Vinn)은 없다."""
    (v,) = N.structure_of(N.s1v()).views
    ff_cells = {"M5", "M6A", "M6B", "M7", "M14"}
    for b in v.blocks:
        assert isinstance(b.members, tuple) and len(b.members) > 0
        assert b.members == tuple(sorted(b.members))
        assert set(b.input_cells) <= set(b.members), b.key
        assert not ff_cells & set(b.members), b.key
    doc = N.topology()
    declared = set(doc["supply_nets"]) | set(doc.get("bias_inputs") or ())
    assert isinstance(v.ac_ground, tuple) and v.ac_ground == tuple(sorted(v.ac_ground))
    assert declared <= set(v.ac_ground)
    assert not {"Vinp", "Vinn"} & set(v.ac_ground)
