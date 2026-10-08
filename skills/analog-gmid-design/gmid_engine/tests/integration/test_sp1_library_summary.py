"""SP1(`build_s1v`) library 5회로 구조 요약 -- 정지 없는 회로 중 손으로 유도할 수 있는 것만(graph CONTRACT 10절, 설계 41 1절).

oracle (a): 각 회로 topology JSON 의 connectivity 에 41 1절·계획 N3.2 규칙을 손으로 적용한 값(아래 주석). oracle (d): DEC-63·DEC-65
측정 기대(계획서 본문). supplies_v 출처 = graph CONTRACT 7절. 정지 4회로(current_reuse·ngcc·nmcnr·sf_pushpull)는
tests/pipeline/test_stage_a.py 가 exit code 와 정지 코드로 본다.
"""
from __future__ import annotations

import sys
from pathlib import Path

GRAPH_TESTS = Path(__file__).resolve().parents[1] / "graph"
if str(GRAPH_TESTS) not in sys.path:
    sys.path.insert(0, str(GRAPH_TESTS))

import s1v_hand as H  # noqa: E402


def _summary(name):
    _, s1v = H.build_lib(name, stop_on_unsupported=True)          # 정지가 없어야 한다(기본 모드)
    v = H.view(s1v)
    return s1v, v, {b.key: (b.kind, b.stage, b.inputs) for b in v.blocks}


def test_two_stage_ota():
    s1v, v, blocks = _summary("two_stage_ota")
    assert [x.id for x in s1v.views] == ["transfer:0"]
    assert (v.excite, v.sense) == ((("vin_n", -0.5), ("vin_p", 0.5)), ("OUT",))
    # 1단: 차동쌍 M1/M2 + diode 미러 M3/M4 -> 출력 O1(stage 1). 2단: M6 CS(gate O1) -> OUT(stage 2)
    assert blocks == {("O1",): ("gain", 1, ("vin_n", "vin_p")), ("OUT",): ("gain", 2, ("O1",))}
    assert H.cells(v) == {"M1": "cs", "M2": "cs", "M3": "diode_load", "M4": "cs", "M5": "off", "M6": "cs", "M7": "off"}
    # 보상 루프 O1 -M6-> OUT -Cc-> N_cc_rz -Rz-> O1: Miller, 루프 뷰 없음
    assert [(set(lp.nodes), lp.classes) for lp in v.loops] == [({"O1", "OUT", "N_cc_rz"}, ("miller",))]
    assert {lc.members: lc.owner for lc in s1v.l_classes} == {("M3", "M4"): "M3", ("M5", "M7"): "M5"}


def test_two_stage_ota_sf():
    s1v, v, blocks = _summary("two_stage_ota_sf")
    # two_stage_ota 와 같은 2단 + follower M8(gate OUT -> vout) 버퍼 블록(DEC-63 {OUT; vout; vout})
    # 버퍼 블록의 stage 번호는 계약에 정의가 없어(gain stage 를 올리지 않음만 정함) 보지 않는다
    assert {k: (kind, inputs) for k, (kind, _, inputs) in blocks.items()} == {
        ("O1",): ("gain", ("vin_n", "vin_p")), ("OUT",): ("gain", ("O1",)), ("vout",): ("buffer", ("OUT",))}
    assert (blocks[("O1",)][1], blocks[("OUT",)][1]) == (1, 2)
    assert H.cells(v)["M8"] == "cd" and H.cells(v)["M9"] == "off"
    assert [(set(lp.nodes), lp.classes) for lp in v.loops] == [({"O1", "OUT"}, ("miller",))]
    assert {lc.members: lc.owner for lc in s1v.l_classes} == {("M3", "M4"): "M3", ("M5", "M7", "M9"): "M5"}


def test_folded_cascode():
    s1v, v, blocks = _summary("folded_cascode")
    # NMOS 차동쌍 -> 접힘 X/Y(PMOS 전류원 M3/M4) -> PMOS 캐스코드 M5/M6(gate bias3, 전류 구동 CG) -> NMOS 캐스코드 미러 -> out
    assert blocks == {("out",): ("gain", 1, ("vin_n", "vin_p"))}
    c = H.cells(v)
    assert (c["M1"], c["M2"], c["M5"], c["M6"]) == ("cs", "cs", "cg", "cg")
    assert all(c[d] == "diode_load" for d in ("MP", "MN", "M7", "M9"))
    assert v.loops == ()
    # tail M11(차동쌍 공통 source 공급) / diode MP / diode M9
    assert {lc.members: lc.owner for lc in s1v.l_classes} == {("M10", "M9"): "M9", ("M11", "MN"): "M11",
                                                             ("M3", "M4", "MP"): "MP"}


def test_common_gate_amplifier():
    s1v, v, blocks = _summary("common_gate_amplifier")
    assert (v.excite, v.sense) == ((("vin", 1.0),), ("vout",))
    # M2: gate VNBias2 교류접지, source vin(여기 포트) -> 전압 구동 CG, stage 시작(source->drain 비용 1)
    assert H.cells(v) == {"M1": "off", "M2": "cg", "M3": "off"}
    assert v.stage_starts == ("M2",)
    assert dict(v.dist) == {"vin": 0, "vout": 1}
    assert blocks == {("vout",): ("gain", 1, ("vin",))}
    assert v.loops == () and s1v.l_classes == ()


def test_pushpull_follower_buffer():
    s1v, v, blocks = _summary("pushpull_follower_buffer")
    # 레벨 시프트 CD M3/M4(vin -> A/B) 뒤 상보 CD M1/M2(A/B -> vout): 버퍼 블록 하나 {vin; A, B, vout; vout}(DEC-63)
    assert H.cells(v) == {"M1": "cd", "M2": "cd", "M3": "cd", "M4": "cd", "M5": "off", "M6": "off"}
    assert {k: (kind, inputs) for k, (kind, _, inputs) in blocks.items()} == {("vout",): ("buffer", ("vin",))}
    assert [(o.net, o.topology) for o in v.output_direction if o.net == "vout"] == [("vout", "push_pull")]
    assert v.loops == () and s1v.l_classes == ()
