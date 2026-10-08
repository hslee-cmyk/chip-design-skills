"""U1b(J 구조 규칙) test 공용 손 회로·helper -- 피검 함수 소스 미열람, 근거는 설계 문서와 계약 문장뿐이다.

근거(oracle 출처):
- 설계 `docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md` 1.12.1~1.12.6(J 구조 규칙), 1.13(실측·기대 표),
  1.4·1.6·1.8(셀·엣지 비용·루프), master edb5ee0 정정(main_path_ambiguous 는 FF 후보 뷰에서만, name_order 동률이 한 자기동형
  궤도면 review 면제).
- 설계 `...40-engine.design.md` 3.2-3(structure.json 형식·concept 어휘·override/confirm/고아/불일치·rule_hash·단계 A 순서).
- 계약 `gmid_engine/graph/CONTRACT.md` 10.6(공개 이름·레코드 모양), `pipeline/CONTRACT.md` 1·2절.

이 모듈은 입력(손 topology·spec·structure 사실)만 만든다 -- 기대값을 계산하지 않는다. 기대값은 각 test 가 아래 손 회로에
설계 규칙을 손으로 적용해 리터럴로 적는다(oracle (a)). 손 회로는 library 이름과 겹치지 않는 소문자 넷·짧은 소자 이름을 쓴다.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from gmid_engine.authoring import load_sizing_spec, load_topology
from gmid_engine.graph import StructureFact, StructureFacts
from gmid_engine.metrics import metric_catalog

import s1v_hand as H

US = {"kind": "user_spec", "record": "hand-made U1b test toy", "decided": "2026-10-09"}

# ---------------------------------------------------------------- 1.12.1 복합 diode 손 회로
# 저항 자기바이어스 캐스코드 기준(MOS 2 + R), 신호 경로 밖. 기준 전류 싱크 Mc, 미러 출력 Md 가 CS(Mi) 의 부하.
#   Ma: d p1 -> (p1 의 DC 단자 Ma.d·Mb.s 둘) -> Mb(source->drain) -> p2 = Ma gate  => 복합 diode, 걷기 {Mb}
#   Mb: d p2 -> (p2 의 DC 단자 Mb.d·Rx 둘; Ma·Md gate 는 세지 않음) -> Rx -> p3 = Mb gate => 복합 diode, 걷기 {Rx}
#   Mc: d p3 -> Rx -> p2 -> Mb(drain->source) -> p1 -> Ma -> vdd(레일) => 실패. Md·Mi: drain out 이 포트 => 실패.
RSELF = H.topo("rself", (("Ma", "pmos", "p1", "p2", "vdd"), ("Mb", "pmos", "p2", "p3", "p1"), ("Mc", "nmos", "p3", "vb", "gnd"),
                         ("Md", "pmos", "out", "p2", "vdd"), ("Mi", "nmos", "out", "in", "gnd")),
               {"in": H.SE_IN, "out": H.SE_OUT}, passives=(("Rx", "resistor", ("p2", "p3")),), bias=("vb",))

# 같은 구조를 신호 경로 위 부하로 쓴 회로(라이브러리 sf 입력단 부하와 같은 모양, 이름 없음):
#   M1(CS, in -> n1), R1(n1-n5), Mb(pmos d n5, g n1, s n56), Ma(pmos d n56, g n5, s vdd), Mo(pmos d out, g n5) + 싱크 Ms.
#   Ma: n56(Ma.d·Mb.s) -> Mb -> n5 = gate => 복합, Mb: n5(Mb.d·R1) -> R1 -> n1 = gate => 복합. M1: n1 -> R1 -> n5 -> Mb ->
#   n56 -> Ma -> vdd 실패. Mo·Ms: out 포트 실패.
SFLOAD = H.topo("sfload", (("M1", "nmos", "n1", "in", "gnd"), ("Mb", "pmos", "n5", "n1", "n56"), ("Ma", "pmos", "n56", "n5", "vdd"),
                           ("Mo", "pmos", "out", "n5", "vdd"), ("Ms", "nmos", "out", "vb", "gnd")),
                {"in": H.SE_IN, "out": H.SE_OUT}, passives=(("R1", "resistor", ("n1", "n5")),), bias=("vb",))

# 레플리카(MOS 2, 전류원 고정): 차동쌍 공통 source tail 위에 Mx(gate b) + 단순 diode My(b) + 전류원 Mi(gate vbp).
#   Mx: d q(Mx.d·My.s 둘) -> My(source->drain) -> b = Mx gate => 복합, 걷기 {My}(지나간 단순 diode). My 는 단순 diode(규칙 1).
#   Mi: d b -> My -> q -> Mx -> tail(DC 단자 4개) 실패. 나머지 drain 은 포트·tail.
_REPL_MOS = (("M1", "nmos", "om", "inp", "tail"), ("M2", "nmos", "op", "inn", "tail"), ("M0", "nmos", "tail", "vb", "gnd"),
             ("M3", "pmos", "om", "vbp", "vdd"), ("M4", "pmos", "op", "vbp", "vdd"),
             ("Mx", "nmos", "q", "b", "tail"), ("My", "nmos", "b", "b", "q"), ("Mi", "pmos", "b", "vbp", "vdd"))
_REPL_PORTS = {"inp": H.DIFF_P, "inn": H.DIFF_N, "op": H.OUT_P, "om": H.OUT_N}
REPL = H.topo("repl", _REPL_MOS, _REPL_PORTS, bias=("vb", "vbp"))
# 직렬 노드 q 에 세 번째 DC 전류 단자(저항 Rq q-gnd) -> q 의 DC 단자 3개 -> Mx 걷기 실패, 복합 diode 0.
REPL_3RD = H.topo("repl3", _REPL_MOS, _REPL_PORTS, passives=(("Rq", "resistor", ("q", "gnd")),), bias=("vb", "vbp"))
# q 에 커패시터만 더함 -> 커패시터 단자는 DC 전류 단자가 아니다 -> 여전히 복합 diode.
REPL_CAP = H.topo("replc", _REPL_MOS, _REPL_PORTS, passives=(("Cq", "capacitor", ("q", "gnd")),), bias=("vb", "vbp"))


def with_ideal_source(doc, name, terminals, stem):
    """doc 사본에 이상 전류원(값 없음, 구현 불가 표시) 하나를 더한다 -- 이상원 단자 넷은 걷기에서 멈춘다(1.12.1 (i))."""
    d = copy.deepcopy(doc)
    d["topology_name"] = stem
    d.setdefault("ideal_sources", []).append(
        {"name": name, "kind": "current_source", "value_amp": None, "implementable": False, "terminals": list(terminals)})
    return d


# 포트에서 멈춤: 입력 CS Mp(in -> b), Mx(nmos d o, g b), My(nmos d b, g b, s o). o 가 출력 포트면 걷기가 o 에서 멈춘다.
#   PORTSTOP: 출력 포트 = o -> Mx 걷기 o(포트) 실패 -> 복합 0.  PORTFREE: 출력 포트 = b -> o 는 포트 아님 -> Mx: o(Mx.d·My.s)
#   -> My -> b = gate => 복합.
_PS_MOS = (("Mp", "pmos", "b", "in", "vdd"), ("Mx", "nmos", "o", "b", "gnd"), ("My", "nmos", "b", "b", "o"))
PORTSTOP = H.topo("portstop", _PS_MOS, {"in": H.SE_IN, "o": H.SE_OUT})
PORTFREE = H.topo("portfree", _PS_MOS, {"in": H.SE_IN, "b": H.SE_OUT})

# ---------------------------------------------------------------- library 9회로 복합 diode 손 유도(oracle (a), 1.12.1 정의 그대로)
# 표기: 소자(drain -> 들어온 단자 말고 다른 DC 단자 원소 -> 반대쪽 넷 ...). DC 전류 단자 = MOS d·s, 저항 단자(gate·커패시터 제외).
# sf_pushpull_output_opamp (레일 vdd·vss·agnd, 이상원 IBias 단자 vdd·NB, 포트 vin_p·vin_n·vout):
#   M6(g N5): N56{M6.d, M5.s} -> M5 -> N5 = g  성공(걷기 M5)       M5(g N1): N5{M5.d, R1a} -> R1a -> N1 = g  성공(걷기 R1a)
#   M8(g N7): N78{M8.d, M7.s} -> M7 -> N7 = g  성공(걷기 M7)       M7(g N2): N7{M7.d, R1b} -> R1b -> N2 = g  성공(걷기 R1b)
#   M14(g N13): N1314{M14.d, M13.s} -> M13 -> N13 = g 성공          M13(g N12): N13{M13.d, R1c} -> R1c -> N12 = g 성공
#   실패 예: M11 N1112 -> M12 -> N12 -> R1c -> N13 -> M13 -> N1314 -> M14 -> vss(레일). M9 N910 -> M10 -> Y -> M15 -> N1516 -> M16
#   -> vss. M17 N17 -> M18 -> vss. M1 N1 -> R1a -> N5 -> M5 -> N56 -> M6 -> vdd. M3 TAIL{M3.d, M1.s, M2.s} 단자 3개.
#   묶음: {M5, M6, R1a}·{M7, M8, R1b}·{M13, M14, R1c}. 기준 = 다른 복합 소자의 걷기에 들지 않는 M6·M8·M14, 캐스코드 M5·M7·M13.
# current_reuse_telescopic_ota (파일럿, 이상원 Iref 단자 Vbias1·gnd):
#   M58(g Vbias2): N58_57{M58.d, M57.s} -> M57 -> Vbias2 = g 성공(지나간 단순 diode M57)
#   M63(g Vbias3): N64_63{M63.d, M64.s} -> M64 -> Vbias3 = g 성공(지나간 단순 diode M64)
#   실패 예: M68 Vbias2 -> M57 -> N58_57 -> M58 -> Vx(단자 5개). M61 Vbias3 -> M64 -> N64_63 -> M63 -> Vy(단자 4개).
#   M12 N11b -> M11b -> N11a11b -> M11a -> vdd. M60 Vbias4 -> M66 -> gnd. M37a Vcmfb -> M36a -> vdd.
# 나머지 7회로: 모든 MOS 의 걷기가 레일·포트·단자 3개 이상 넷에서 멈춘다(예: ngcc M4 V1 -> M2 -> TAIL(3), M8 NP -> M9 -> vdd,
#   nmcnr M109 NodeM2 -> M107 -> NodeF2(3), folded M5 Vg7 -> M7 -> Vg9 -> M9 -> gnd, pushpull M5 A -> M3 -> vss) -> 0.
COMPOSITE = "diode_reference_composite"
CASCODE = "diode_reference_composite_cascode"
_SF_B = {"M6": ("M5", "M6", "R1a"), "M8": ("M7", "M8", "R1b"), "M14": ("M13", "M14", "R1c")}
LIB_COMPOSITE = {
    "sf_pushpull_output_opamp": {
        "M6": (_SF_B["M6"], COMPOSITE), "M5": (_SF_B["M6"], CASCODE),
        "M8": (_SF_B["M8"], COMPOSITE), "M7": (_SF_B["M8"], CASCODE),
        "M14": (_SF_B["M14"], COMPOSITE), "M13": (_SF_B["M14"], CASCODE),
    },
    "current_reuse_telescopic_ota": {"M58": (("M57", "M58"), COMPOSITE), "M63": (("M63", "M64"), COMPOSITE)},
}


# ---------------------------------------------------------------- 1.12.2 feedforward 손 회로
# 3단 CS 사슬 in -M1-> a -M2-> b -M3-> out (부하 P1~P3 gate vbp), 1단 우회 CS M4(gate a -> out),
# 2단 우회 미러 가지: M5(CS, in -> x), diode Pd(x), 미러 Pm(gate x -> out), 묶음 내부 넷 x 의 바이어스 전류원 Nb(gate vbn).
FF3_MOS = (("M1", "nmos", "a", "in", "gnd"), ("P1", "pmos", "a", "vbp", "vdd"),
           ("M2", "nmos", "b", "a", "gnd"), ("P2", "pmos", "b", "vbp", "vdd"),
           ("M3", "nmos", "out", "b", "gnd"), ("P3", "pmos", "out", "vbp", "vdd"),
           ("M4", "nmos", "out", "a", "gnd"),
           ("M5", "nmos", "x", "in", "gnd"), ("Pd", "pmos", "x", "x", "vdd"), ("Pm", "pmos", "out", "x", "vdd"),
           ("Nb", "nmos", "x", "vbn", "gnd"))
FF3 = H.topo("ff3", FF3_MOS, {"in": H.SE_IN, "out": H.SE_OUT}, bias=("vbp", "vbn"))
# 주경로 2단이 병렬 두 갈래(a -M2-> b -M3-> out, a -M6-> c -M7-> out)이고 2단 우회 미러 가지(FF 후보)가 있는 회로.
FFAMB = H.topo("ffamb", tuple(r for r in FF3_MOS if r[0] != "M4") + (
    ("M6", "nmos", "c", "a", "gnd"), ("P4", "pmos", "c", "vbp", "vdd"), ("M7", "nmos", "out", "c", "gnd")),
    {"in": H.SE_IN, "out": H.SE_OUT}, bias=("vbp", "vbn"))
# 같은 병렬 두 갈래에서 FF 후보(미러 가지)를 뺀 회로 -- FF 후보가 없으면 주경로 모호 판정을 하지 않는다(edb5ee0).
PAR2 = H.topo("par2", tuple(r for r in FF3_MOS if r[0] in ("M1", "P1", "M2", "P2", "M3", "P3")) + (
    ("M6", "nmos", "c", "a", "gnd"), ("P4", "pmos", "c", "vbp", "vdd"), ("M7", "nmos", "out", "c", "gnd")),
    {"in": H.SE_IN, "out": H.SE_OUT}, bias=("vbp",))
# K8: 2단(a -M2-> c, 캐스코드 Mc(gate vbc) -> out) 의 블록 내부 노드 c 로 들어오는 셀 Mk(gate in). c 는 블록 출력노드가 아니다.
K8 = H.topo("k8", (("M1", "nmos", "a", "in", "gnd"), ("P1", "pmos", "a", "vbp", "vdd"), ("M2", "nmos", "c", "a", "gnd"),
                   ("Mc", "nmos", "out", "vbc", "c"), ("P2", "pmos", "out", "vbp", "vdd"), ("Mk", "nmos", "c", "in", "gnd")),
            {"in": H.SE_IN, "out": H.SE_OUT}, bias=("vbp", "vbc"))

# ---------------------------------------------------------------- 1.12.3 중첩 Miller 3단 손 회로(이름 없음)
# 1단 PMOS 차동쌍(Q1·Q2, 꼬리 Q0) + NMOS 미러(Q3 diode d1, Q4) -> v1, 2단 CS Q8(v1 -> np, diode Q9) + 미러 Q10 -> v2(싱크 Q11),
# 3단 CS Q13(v2 -> out, 부하 Q12). 중첩 Miller Cm1(v1-out)·Cm2(v2-out), 부하 CL.
NMC3 = H.topo("nmc3", (("Q0", "pmos", "t", "vbp", "vdd"), ("Q1", "pmos", "d1", "inn", "t"), ("Q2", "pmos", "v1", "inp", "t"),
                       ("Q3", "nmos", "d1", "d1", "gnd"), ("Q4", "nmos", "v1", "d1", "gnd"), ("Q8", "nmos", "np", "v1", "gnd"),
                       ("Q9", "pmos", "np", "np", "vdd"), ("Q10", "pmos", "v2", "np", "vdd"), ("Q11", "nmos", "v2", "vbn", "gnd"),
                       ("Q12", "pmos", "out", "vbp", "vdd"), ("Q13", "nmos", "out", "v2", "gnd")),
              {"inp": H.DIFF_P, "inn": H.DIFF_N, "out": H.SE_OUT},
              passives=(("Cm1", "capacitor", ("v1", "out")), ("Cm2", "capacitor", ("v2", "out")), ("CL", "capacitor", ("out", "gnd"))),
              bias=("vbp", "vbn"))

# ---------------------------------------------------------------- 1.12.4 극성 손 회로
# CMFB(s1v_hand) 를 단일 출력 role 로 선언한 회로(포트쌍 대응 없음) -- 루프 cm -M5-> cmfb -M3/M4-> om/op -R1/R2-> cm.
_CMFB_MOS = tuple((e["name"], e["kind"], e["drain"], e["gate"], e["source"]) for e in H.CMFB["netlist"])
_CMFB_PAS = tuple((e["name"], e["kind"], tuple(e["terminals"])) for e in H.CMFB["passive_elements"])
_SE2 = {"inp": H.DIFF_P, "inn": H.DIFF_N, "op": H.SE_OUT, "om": H.SE_OUT}
# om-cm 사이 커패시터 Cx: 사이클 cm -> cmfb -> om -Cx-> cm 은 커패시터 경유(ac_only), R1·R2 사이클은 DC.
POL_AC = H.topo("pol_ac", _CMFB_MOS, _SE2, passives=_CMFB_PAS + (("Cx", "capacitor", ("om", "cm")),), bias=("vb", "vref"))
# follower Mf(drain vdd, gate cmfb, source f) + 저항 Rg(f-cm): 사이클 cm -M5(CS)-> cmfb -Mf(CD)-> f -Rg-> cm 은 부호 -1,
# R1·R2 사이클(M5 CS, M3/M4 CS, 저항)은 +1 -> 같은 루프 뷰 안 DC 사이클 극성이 갈린다.
POL_CONFLICT = H.topo("pol_cf", _CMFB_MOS + (("Mf", "nmos", "vdd", "cmfb", "f"),), _SE2,
                      passives=_CMFB_PAS + (("Rg", "resistor", ("f", "cm")),), bias=("vb", "vref"))

# ---------------------------------------------------------------- 1.12.5 L 주인 손 회로
# 완전 차동 쌍(꼬리 M0 gate vb) + PMOS 전류원 부하 M3/M4(gate vbp). {M3, M4}: tail 아님, diode 기준 없음, stage 시작 아님
# -> name_order 동률. 회로가 M1<->M2, M3<->M4, op<->om 교환에 대칭이라 두 후보가 한 자기동형 궤도다.
FDIFF = H.topo("fdiff", (("M1", "nmos", "om", "inp", "tail"), ("M2", "nmos", "op", "inn", "tail"), ("M0", "nmos", "tail", "vb", "gnd"),
                         ("M3", "pmos", "om", "vbp", "vdd"), ("M4", "pmos", "op", "vbp", "vdd")),
               {"inp": H.DIFF_P, "inn": H.DIFF_N, "op": H.OUT_P, "om": H.OUT_N}, bias=("vb", "vbp"))

# ---------------------------------------------------------------- β 루프 손 회로(단계 A declared_loop_cuts)
# 5T OTA + 되먹임 저항 Rf(out-inn) + 부하 CL. spec feedback = [Rf] -> pm_ss_deg 루프 뷰 cuts = ((Rf, inn),).
UGB = H.topo("ugb", tuple((e["name"], e["kind"], e["drain"], e["gate"], e["source"]) for e in H.OTA5["netlist"]),
             {"inp": H.DIFF_P, "inn": H.DIFF_N, "out": H.SE_OUT},
             passives=(("Rf", "resistor", ("out", "inn")), ("CL", "capacitor", ("out", "gnd"))), bias=("vb",))


# ---------------------------------------------------------------- library 이름 전단사(41 1.11 불변식 입력)
TAG_SECTIONS = ("device_roles", "symmetry", "sizing_roles", "compensation")   # 소자 이름을 담는 주석 태그(엔진은 읽지 않는다)


def library_names(raw):
    """(넷 이름 집합, 원소 이름 집합) -- MOS d/g/s/bulk, 수동소자·이상원 단자, 레일, bias_inputs, 포트 키(엔진 미사용 직접 집계)."""
    nets, elems = set(raw["supply_nets"]) | set(raw.get("bias_inputs") or ()), set()
    nets |= {k for k in raw["ports"] if not k.startswith("_")}
    for e in raw["netlist"]:
        elems.add(e["name"])
        nets |= {e[k] for k in ("drain", "gate", "source", "bulk") if e.get(k)}
    for key in ("passive_elements", "ideal_sources"):
        for e in raw.get(key) or []:
            elems.add(e["name"])
            nets |= set(e["terminals"])
    return nets, elems


def reverse_order_maps(raw, net_prefix="w", elem_prefix="E"):
    """정렬 순서를 뒤집는 새 이름(이름 tie-break 가 결과를 바꾸면 드러나게). 넷·원소 이름 공간을 섞지 않는다."""
    nets, elems = (sorted(x) for x in library_names(raw))
    return ({n: "%s%03d" % (net_prefix, len(nets) - i) for i, n in enumerate(nets)},
            {n: "%s%03d" % (elem_prefix, len(elems) - i) for i, n in enumerate(elems)})


def rename_library(raw, nmap, dmap, seed):
    """library topology 원본 사본의 넷·원소 이름을 사상으로 바꾸고 netlist·수동소자·이상원 순서를 섞는다.
    s1v_hand.rename 이 다루지 않는 키(bulk, ideal_sources, bias_inputs 없음, 포트 주석 키 `_...`)를 다룬다. 소자 이름을 담는 주석 태그
    섹션과 `_` 로 시작하는 주석 키는 뺀다(엔진은 읽지 않는다 -- authoring 계약 머리 IGNORED_TAG_KEYS). linked_topology_files 는 원본
    폴더 기준 경로라 사본에서는 비운다."""
    import random
    f = lambda n: nmap.get(n, n)  # noqa: E731
    d = {k: copy.deepcopy(v) for k, v in raw.items() if not k.startswith("_") and k not in TAG_SECTIONS}
    for e in d["netlist"]:
        e["name"] = dmap.get(e["name"], e["name"])
        for k in ("drain", "gate", "source", "bulk"):
            if e.get(k):
                e[k] = f(e[k])
    for key in ("passive_elements", "ideal_sources"):
        for e in d.get(key) or []:
            e["name"] = dmap.get(e["name"], e["name"])
            e["terminals"] = [f(t) for t in e["terminals"]]
        random.Random(seed + len(key)).shuffle(d.get(key) or [])
    d["supply_nets"] = [f(n) for n in d["supply_nets"]]
    if "bias_inputs" in d:
        d["bias_inputs"] = [f(n) for n in d["bias_inputs"]]
    d["ports"] = {f(k): v for k, v in d["ports"].items() if not k.startswith("_")}
    if "linked_topology_files" in d:
        d["linked_topology_files"] = []
    random.Random(seed).shuffle(d["netlist"])
    return d


# ---------------------------------------------------------------- spec (입력 준비 -- library ngcc spec 을 틀로 쓴다)
def spec_doc(doc, *, pm=True, feedback=(), element_values=None):
    """손 회로용 sizing_spec dict. 틀 = library ngcc_3stage_ff spec 의 human(공급·검색 설정 등 공통 항목). 제약은 pm_ss_deg 하나
    (pm=False 면 제약 없음). element_values 기본 = 손 회로의 수동소자마다 engine 값(커패시터)·value_ohm(저항)."""
    tmpl = json.loads((H.LIBRARY / "ngcc_3stage_ff.sizing_spec.json").read_text(encoding="utf-8"))
    human = copy.deepcopy(tmpl["human"])
    human["supplies_v"] = {"values": {r: H.SUPPLIES.get(r, 0.9) for r in doc["supply_nets"]}, "source": dict(US)}
    if element_values is None:
        element_values = {}
        for e in doc.get("passive_elements") or []:
            if e["kind"] == "resistor":
                element_values[e["name"]] = {"value_ohm": 1.0e4, "source": dict(US)}
            else:
                element_values[e["name"]] = {"engine": True, "source": dict(US)}
    human["element_values"] = element_values
    human["feedback"] = {"elements": list(feedback), "source": dict(US)}
    human["constraints"] = [{"metric": "pm_ss_deg", "op": ">=", "value": 60, "source": dict(US)}] if pm else []
    human["pending_constraints"] = []
    human["compensation_targets"] = (
        {"pm_target_deg": {"value_from_constraint": "pm_ss_deg", "source": {"kind": "reference"}}} if pm else {})
    human["search"].pop("theta_bounds", None)
    return human


def write_pair(tmp_path, doc, *, stem=None, **spec_kw):
    """(topology 경로, spec 경로) -- 같은 stem 으로 tmp 에 쓴다. spec meta.topology_fp 는 로드한 topology 의 지문(입력 준비)."""
    stem = stem or doc["topology_name"]
    tp = Path(tmp_path) / (stem + ".topology.json")
    tp.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    topo = load_topology(str(tp))
    spec = {"meta": {"schema_version": "5", "circuit": doc["topology_name"], "topology_fp": topo.connectivity_fp,
                     "origin": "fixture"},
            "human": spec_doc(doc, **spec_kw)}
    sp = Path(tmp_path) / (stem + ".sizing_spec.json")
    sp.write_text(json.dumps(spec, indent=1), encoding="utf-8")
    return tp, sp


def load_spec(tmp_path, doc, *, stem=None, **spec_kw):
    """(topology doc, SizingSpecDoc) -- 실 metric 카탈로그로 로드."""
    tp, sp = write_pair(tmp_path, doc, stem=stem, **spec_kw)
    topo = load_topology(str(tp))
    return topo, load_sizing_spec(str(sp), topo, metric_catalog())


# ---------------------------------------------------------------- structure.json 사실(입력 준비)
def fact_dict(concept, subject, value, approval="T-1", nets=()):
    return {"concept": concept, "subject": subject, "value": value, "status": "ratified",
            "evidence": {"rule": "hand", "nets": list(nets)}, "approval_id": approval}


def write_structure(path, topology_hash, rule_hash, facts, schema_version="1"):
    Path(path).write_text(json.dumps({"schema_version": schema_version, "topology_hash": topology_hash,
                                      "rule_hash": rule_hash, "facts": list(facts)}), encoding="utf-8")
    return str(path)


def facts(*rows):
    """StructureFacts 직접 생성(로더를 거치지 않는 소비 test 용). rows = (concept, subject, value, approval_id)."""
    return StructureFacts(facts=tuple(StructureFact(c, s, v, a, ()) for c, s, v, a in rows), findings=())


def finding_codes(s1v):
    return sorted([f.code for v in s1v.views for f in v.findings] + [f.code for f in s1v.findings])
