"""graph/buffer_bundles.py -- follower 묶음 R(u)와 버퍼 블록(계약 10.2 '블록' 끝 문장, 설계 41 1.9, 계획 DEC-63).

oracle (a) 손 유도: 전압 구동 넷 u(입력 포트 또는 이득 블록 출력노드)에서 CD 셀의 입력->출력 엣지만 따라 도달하는 노드 R(u).
더 이상 CD 입력으로 쓰이지 않는 노드(싱크)가 하나면 버퍼 블록 {입력 u, 노드 R(u), 출력노드 v}, 둘 이상이면 다출력 버퍼
`buffer_multi_output`(기록만). 버퍼 블록과 앞 이득 블록이 공유하는 넷은 u 하나.
oracle (d): DEC-63 측정 기대(계획서 본문) -- pushpull_follower_buffer {vin; A, B, vout; vout}, sf_pushpull_output_opamp
{Y; N17, N20, vout; vout}, two_stage_ota_sf {OUT; vout; vout}.
"""
from __future__ import annotations

import pytest

import s1v_hand as H

# 2단 Miller 뒤 NMOS follower M8(gate out -> source vout) + 싱크 M9. 출력 포트 = vout
MILLER_SF = H.topo("miller_sf", tuple((e["name"], e["kind"], e["drain"], e["gate"], e["source"]) for e in H.MILLER["netlist"])
                   + (("M8", "nmos", "vdd", "out", "vout"), ("M9", "nmos", "vout", "vb", "gnd")),
                   {"inp": H.DIFF_P, "inn": H.DIFF_N, "vout": H.SE_OUT}, passives=(("Cc", "capacitor", ("o1", "out")),),
                   bias=("vb",))


def _buffers(v):
    return [b for b in v.blocks if b.kind == "buffer"]


def test_single_follower_is_buffer_block(tmp_path):
    _, s1v = H.build(tmp_path, H.FOLLOWER)
    v = H.view(s1v)
    assert [(b.key, b.inputs, b.outputs, b.nodes) for b in _buffers(v)] == [(("out",), ("in",), ("out",), ("in", "out"))]
    assert H.roles(_buffers(v)[0]) == {"M1": "follower"}
    assert [b for b in v.blocks if b.kind == "gain"] == []


def test_complementary_followers_merge_into_one_buffer(tmp_path):
    _, s1v = H.build(tmp_path, H.PUSHPULL)
    v = H.view(s1v)
    # R(in) = {out}(M1·M2 둘 다 in -> out), 싱크 하나 -> 버퍼 블록 하나
    assert [(b.key, b.inputs, b.outputs) for b in _buffers(v)] == [(("out",), ("in",), ("out",))]
    assert H.roles(_buffers(v)[0]) == {"M1": "follower", "M2": "follower"}


def test_follower_after_gain_block_shares_only_u(tmp_path):
    _, s1v = H.build(tmp_path, MILLER_SF)
    v = H.view(s1v)
    bl = H.blocks(v)
    assert sorted(bl) == [("o1",), ("out",), ("vout",)]
    buf = bl[("vout",)]
    assert (buf.kind, buf.inputs, buf.outputs) == ("buffer", ("out",), ("vout",))
    # 앞 이득 블록(out)과 공유하는 넷은 u = out 하나
    assert set(buf.nodes) & set(bl[("out",)].nodes) == {"out"}


def test_two_sinks_is_multi_output_buffer(tmp_path):
    _, s1v = H.build(tmp_path, H.BMULTI)
    v = H.view(s1v)
    hits = [f for f in v.findings if f.code == "buffer_multi_output"]
    assert [h.severity for h in hits] == ["unsupported_rule_branch"]
    assert {"o1", "o2"} <= set(hits[0].subject)


@pytest.mark.parametrize("circuit,expected", [
    ("pushpull_follower_buffer", (("vin",), {"A", "B", "vout"}, ("vout",))),
    ("sf_pushpull_output_opamp", (("Y",), {"N17", "N20", "vout"}, ("vout",))),
    ("two_stage_ota_sf", (("OUT",), {"vout"}, ("vout",))),
])
def test_library_buffer_bundles_match_dec63(circuit, expected):
    _, s1v = H.build_lib(circuit)
    bufs = _buffers(H.view(s1v))
    assert len(bufs) == 1
    u, r_u, v_out = expected
    b = bufs[0]
    assert b.inputs == u and b.outputs == v_out
    assert set(b.nodes) - set(u) == r_u                        # 블록 노드 = u ∪ R(u)
