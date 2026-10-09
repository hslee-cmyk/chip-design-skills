"""`_helpers_view.view_system` -- metrics CONTRACT 10.0·10.2: 전달 뷰 -> (고정 노드, 구동, 관측 벡터, 여기 쌍, 감지 쌍).
고정 노드 = 교류접지 ∪ 입력 포트 ∪ 뷰 구동 넷, 전달 뷰 = mode transfer·port·되먹임 없는 loop(β = 1), 그 밖 None.

oracle (a): 손 회로의 넷 이름에서 집합을 손으로 적는다(구성으로 정해진다). (d) CONTRACT 10.0 표 `PARAMETER_ORDER` 문장 = `MosSmallSignal` 필드 순서.
"""
from __future__ import annotations

import dataclasses

import numpy as np

from gmid_engine.authoring import SenseDecl, ViewDecl
from gmid_engine.metrics import MosSmallSignal
from gmid_engine.metrics._helpers_view import PARAMETER_ORDER, view_system

from . import u7_hand as H


def _ss():
    nets, m, r, ground, inputs = H.diff_pair()
    return nets, H.circuit(nets, m, r, ground, inputs)


def test_transfer_view_sets():
    nets, ss = _ss()
    idx = {n: i for i, n in enumerate(nets)}
    fixed, drive, sense, pairs, decl = view_system(ss, H.transfer({"ip": 0.5, "im": -0.5}, "op", "om"))
    assert fixed == {idx[n] for n in ("gnd", "vdd", "vb", "ip", "im")}
    assert drive == {idx["ip"]: 0.5, idx["im"]: -0.5}
    want = np.zeros(len(nets))
    want[idx["op"]], want[idx["om"]] = 1.0, -1.0
    assert np.array_equal(sense, want)
    assert pairs == (("im", -0.5), ("ip", 0.5))
    assert decl == ("op", "om")


def test_excite_net_outside_ports_is_fixed():
    """뷰 구동 넷(포트가 아닌 넷, 예: 꼬리 t)도 고정 노드다."""
    nets, ss = _ss()
    idx = {n: i for i, n in enumerate(nets)}
    fixed, drive, _sense, _pairs, decl = view_system(ss, H.transfer({"t": 1.0}, "op"))
    assert idx["t"] in fixed and drive == {idx["t"]: 1.0} and decl == ("op", None)


def test_port_and_unity_loop_use_weights_and_sense():
    nets, ss = _ss()
    idx = {n: i for i, n in enumerate(nets)}
    sense = SenseDecl("op", "om", "differential")
    for mode in ("port", "loop"):
        view = ViewDecl(mode, weights=(("im", -0.5), ("ip", 0.5)), sense=sense)
        fixed, drive, vec, pairs, decl = view_system(ss, view)
        assert drive == {idx["ip"]: 0.5, idx["im"]: -0.5}
        assert decl == ("op", "om") and vec[idx["op"]] == 1.0 and vec[idx["om"]] == -1.0


def test_non_transfer_views_none():
    _nets, ss = _ss()
    sense = SenseDecl("op", "om", "differential")
    assert view_system(ss, ViewDecl("ratio")) is None
    assert view_system(ss, ViewDecl("none")) is None
    assert view_system(ss, ViewDecl("loop", cuts=(("R1", "om"),), weights=(("om", 1.0),), sense=sense)) is None
    assert view_system(ss, ViewDecl("port")) is None                       # 감지 없음
    assert view_system(ss, None) is None


def test_parameter_order_is_mos_small_signal_field_order():
    names = [f.name for f in dataclasses.fields(MosSmallSignal)]
    assert PARAMETER_ORDER == ("gm", "gmb", "gds")
    assert names[names.index("gm"):names.index("gm") + 3] == list(PARAMETER_ORDER)
