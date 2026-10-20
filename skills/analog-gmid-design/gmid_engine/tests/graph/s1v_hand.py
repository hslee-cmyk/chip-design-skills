"""SP1(`build_s1v`) test 공용 손 회로·helper -- 피검 함수 소스 미열람, 근거는 계약과 설계 문서뿐이다.

근거(oracle 출처):
- 계약 `gmid_engine/graph/CONTRACT.md` 10절(SP1 공개 API·동작·불변량 1~8), `gmid_engine/pipeline/CONTRACT.md`.
- 설계 `docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md` 0절(N_S)·1절(FR-1 SP1 알고리즘 1.1~1.10),
  계획 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` N3.2 규칙 1~9(정본)·DEC-17·DEC-63·DEC-65·DEC-81.
- 기대값은 각 test 가 아래 손 회로(구성으로 정답이 정해진 합성 입력, oracle (a))에 위 규칙을 손으로 적용해 리터럴로 적는다.
  이 모듈은 입력(topology JSON)과 결과에서 값을 꺼내는 함수만 둔다 -- 기대값을 계산하지 않는다.

손 회로는 library 넷 이름과 겹치지 않게 소문자 짧은 이름을 쓰고, gate 전용 외부 바이어스 넷은 `bias_inputs` 로 선언한다
(authoring CONTRACT 9절 -- 미선언이면 `gate_only_undeclared` 로 거부된다).
"""
from __future__ import annotations

import copy
import json
import random
from pathlib import Path

from gmid_engine.authoring import load_topology
from gmid_engine.graph import BUILD_S1V_WRITER, S1V_KEY, build_s1, build_s1v

SEVERITY_REVIEW_NEEDED = "review_needed"                 # 계약 10절 Finding.severity 어휘(graph 공개 값 SEVERITY_REVIEW)
SEVERITY_UNSUPPORTED_BRANCH = "unsupported_rule_branch"  # 같은 어휘의 `기록만` 분기


class S1vRead:
    """[U17 ①-b] S1v 필드 읽기(test 쪽) -- 설계 40 v1.9.1 §2.4.8 'graph/s1v: views, l_classes, findings, declared, applied_facts'(D1).
    묶음 객체 `S1v` 는 없어졌고(§2.4.2) `build_s1v` 는 S1Graph 를 돌려준다. 이 객체는 값을 담지 않고 부를 때마다 그 S1Graph 의 `graph/s1v`
    필드를 읽는다. review_needed·unsupported 는 필드의 기록을 severity 로 거른 것(계약 10절 정의를 test 쪽에서 다시 적용)."""

    def __init__(self, graph):
        self.graph = graph

    def _f(self, name):
        return self.graph.value("graph", S1V_KEY, name)

    # S1v 필드를 읽는 엔진 함수(structure_tables 등)에 넘길 수 있게 질의는 그 S1Graph 로 넘긴다
    def value(self, kind, key, field):
        return self.graph.value(kind, key, field)

    def column(self, kind, field):
        return self.graph.column(kind, field)

    @property
    def snapshot(self):
        return getattr(self.graph, "snapshot", self.graph)

    @property
    def key(self):
        """옛 `S1v.key`(재사용 키) 자리 -- 설계 40 §2.4.2 '입력 버전이 같으면 다시 계산하지 않는다': S1v 계산 블록(writer build_s1v)의 입력 버전."""
        return self.snapshot.block_version(BUILD_S1V_WRITER)

    views = property(lambda self: self._f("views"))
    l_classes = property(lambda self: self._f("l_classes"))
    findings = property(lambda self: self._f("findings"))
    declared = property(lambda self: self._f("declared"))
    facts_applied = property(lambda self: self._f("applied_facts"))
    applied_facts = facts_applied

    @property
    def loop_roles(self):
        return tuple(r for v in self.views for r in v.loop_roles)

    @property
    def all_findings(self):
        return tuple(self.findings) + tuple(f for v in self.views for f in v.findings)

    @property
    def review_needed(self):
        return tuple(f for f in self.all_findings if f.severity == SEVERITY_REVIEW_NEEDED)

    @property
    def unsupported(self):
        return tuple(f for f in self.all_findings if f.severity == SEVERITY_UNSUPPORTED_BRANCH)


def read_s1v(graph):
    """S1Graph(또는 GraphSnapshot) -> `S1vRead`."""
    return S1vRead(graph)

# 포트 role 어휘(계약 10.4: `differential_input_p/n`, `differential_output_p/n` -- authoring 어휘 복제)
DIFF_P = {"direction": "input", "role": "differential_input_p"}
DIFF_N = {"direction": "input", "role": "differential_input_n"}
SE_IN = {"direction": "input", "role": "single_ended_input"}
SE_OUT = {"direction": "output", "role": "single_ended_output"}
OUT_P = {"direction": "output", "role": "differential_output_p"}
OUT_N = {"direction": "output", "role": "differential_output_n"}

BIG_BUDGET = 10 ** 6          # 계수 예산 N_S -- 손 회로의 사이클·셀 수보다 충분히 큰 test 입력(기준값 아님)
SUPPLIES = {"vdd": 1.8, "gnd": 0.0}   # 사용자 확정 supplies_v(graph CONTRACT 7절) -- bulk 기본 규칙 입력일 뿐


def topo(name, mos, ports, *, rails=("vdd", "gnd"), passives=(), bias=()):
    """손 topology JSON. mos = ((이름, kind, drain, gate, source), ...), passives = ((이름, kind, (t0, t1)), ...)."""
    return {
        "schema_version": "2.0",
        "topology_name": name,
        "source": "hand-made SP1 test circuit (not a library circuit)",
        "supply_nets": list(rails),
        "bias_inputs": list(bias),
        "netlist": [{"name": n, "kind": k, "drain": d, "gate": g, "source": s} for n, k, d, g, s in mos],
        "passive_elements": [{"name": n, "kind": k, "terminals": list(t)} for n, k, t in passives],
        "ports": dict(ports),
    }


def load(tmp_path: Path, doc: dict, stem: str | None = None):
    p = Path(tmp_path) / ((stem or doc["topology_name"]) + ".topology.json")
    p.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    return load_topology(str(p))


def fresh_run():
    """[XRUN-F1 card B C0] 새 실행 하나의 두 객체 키워드(dict). 부를 때마다 새 open_run() 쌍."""
    from gmid_engine.search import open_run
    donors, counters = open_run()
    return dict(donors=donors, counters=counters)


def build(tmp_path, doc, *, supplies=None, spec=None, stem=None, **kw):
    """(s1, s1v). 기본 = 진단 모드(`stop_on_unsupported=False`)와 큰 계수 예산 -- 정지 test 는 kw 로 바꾼다.
    [XRUN-F1 card B C6] S1·S1v = 이 호출 하나의 실행(새 open_run() 쌍)."""
    run = fresh_run()
    s1 = build_s1(load(tmp_path, doc, stem), dict(supplies or {r: SUPPLIES.get(r, 0.9) for r in doc["supply_nets"]}), **run)
    kw.setdefault("count_budget", BIG_BUDGET)
    kw.setdefault("stop_on_unsupported", False)
    return s1, read_s1v(build_s1v(s1, spec, **kw, **run))


LIBRARY = Path(__file__).resolve().parents[3] / "assets" / "library"
# supplies_v 출처(graph CONTRACT 7절): 사용자 확정 {vdd 1.8, gnd 0}인 5회로, 나머지는 topology `_declared_target_spec.supplies_v`
USER_CONFIRMED = ("two_stage_ota_sf", "two_stage_ota", "current_reuse_telescopic_ota", "folded_cascode",
                  "common_gate_amplifier")


def lib_supplies(name):
    if name in USER_CONFIRMED:
        return dict(SUPPLIES)
    raw = json.loads((LIBRARY / (name + ".topology.json")).read_text(encoding="utf-8"))
    return {k: v for k, v in raw["_declared_target_spec"]["supplies_v"].items() if not k.startswith("_")}


def build_lib(name, spec=None, **kw):
    """library 회로 (s1, s1v) -- 진단 모드·큰 예산 기본. [XRUN-F1 card B C6] 이 호출 하나 = 실행 하나."""
    run = fresh_run()
    s1 = build_s1(load_topology(str(LIBRARY / (name + ".topology.json"))), lib_supplies(name), **run)
    kw.setdefault("count_budget", BIG_BUDGET)
    kw.setdefault("stop_on_unsupported", False)
    return s1, read_s1v(build_s1v(s1, spec, **kw, **run))


def view(s1v, vid="transfer:0"):
    hits = [v for v in s1v.views if v.id == vid]
    assert len(hits) == 1, (vid, [v.id for v in s1v.views])
    return hits[0]


def cells(v):
    return {c.dev: c.kind for c in v.cells}


def drive(v):
    return {d.net: d.kind for d in v.drive_kind}


def codes(v):
    return sorted(f.code for f in v.findings)


def all_codes(s1v):
    return sorted([f.code for v in s1v.views for f in v.findings] + [f.code for f in s1v.findings])


def blocks(v):
    return {b.key: b for b in v.blocks}


def roles(block):
    return dict(block.roles)


def poles(v):
    return {p.net: p for p in v.pole_nodes}


def json_nets(doc):
    """topology JSON 이 단자로 쓰는 넷 전부(MOS d/g/s + 수동소자 단자 + 레일) -- 엔진 미사용 직접 집계."""
    nets = set(doc["supply_nets"])
    for e in doc["netlist"]:
        nets |= {e["drain"], e["gate"], e["source"]}
    for e in doc.get("passive_elements") or []:
        nets |= set(e["terminals"])
    return nets


def json_mos(doc):
    return {e["name"] for e in doc["netlist"]}


def rename(doc, nets: dict, devs: dict, seed: int):
    """넷·원소 이름 전단사 + netlist 순서 섞기(불변량 2 의 입력 변형). 레일·포트 키도 같은 사상으로."""
    d = copy.deepcopy(doc)
    f = lambda n: nets.get(n, n)  # noqa: E731
    for e in d["netlist"]:
        e["name"] = devs.get(e["name"], e["name"])
        for k in ("drain", "gate", "source"):
            e[k] = f(e[k])
    for e in d["passive_elements"]:
        e["name"] = devs.get(e["name"], e["name"])
        e["terminals"] = [f(t) for t in e["terminals"]]
    d["supply_nets"] = [f(n) for n in d["supply_nets"]]
    d["bias_inputs"] = [f(n) for n in d["bias_inputs"]]
    d["ports"] = {f(k): v for k, v in d["ports"].items()}
    random.Random(seed).shuffle(d["netlist"])
    random.Random(seed + 1).shuffle(d["passive_elements"])
    return d


# ---------------------------------------------------------------- 손 회로(구성으로 정답이 정해진 합성 입력)
# 5T OTA: NMOS 차동쌍 M1/M2, PMOS diode 미러 부하 M3(diode)/M4, 꼬리 M5(gate 외부 바이어스 vb).
OTA5 = topo("ota5", (("M1", "nmos", "x", "inp", "tail"), ("M2", "nmos", "out", "inn", "tail"), ("M3", "pmos", "x", "x", "vdd"),
                     ("M4", "pmos", "out", "x", "vdd"), ("M5", "nmos", "tail", "vb", "gnd")),
            {"inp": DIFF_P, "inn": DIFF_N, "out": SE_OUT}, bias=("vb",))
# 2단 Miller: 5T OTA(출력 o1) + PMOS CS M6 + NMOS 전류원 M7(gate vb, 꼬리와 같은 gs 묶음) + Miller Cc(o1-out).
MILLER = topo("miller", (("M1", "nmos", "x", "inp", "tail"), ("M2", "nmos", "o1", "inn", "tail"), ("M3", "pmos", "x", "x", "vdd"),
                         ("M4", "pmos", "o1", "x", "vdd"), ("M5", "nmos", "tail", "vb", "gnd"), ("M6", "pmos", "out", "o1", "vdd"),
                         ("M7", "nmos", "out", "vb", "gnd")),
              {"inp": DIFF_P, "inn": DIFF_N, "out": SE_OUT}, passives=(("Cc", "capacitor", ("o1", "out")),), bias=("vb",))
# 접힌 캐스코드: NMOS 차동쌍 -> 접힘 노드 fx/fy(PMOS 전류원 M3/M4) -> PMOS 캐스코드 M5/M6(gate vbc) -> NMOS diode 미러 M7/M8.
FOLDED = topo("folded", (("M1", "nmos", "fx", "inp", "tail"), ("M2", "nmos", "fy", "inn", "tail"), ("M0", "nmos", "tail", "vb1", "gnd"),
                         ("M3", "pmos", "fx", "vbp", "vdd"), ("M4", "pmos", "fy", "vbp", "vdd"), ("M5", "pmos", "ox", "vbc", "fx"),
                         ("M6", "pmos", "out", "vbc", "fy"), ("M7", "nmos", "ox", "ox", "gnd"), ("M8", "nmos", "out", "ox", "gnd")),
              {"inp": DIFF_P, "inn": DIFF_N, "out": SE_OUT}, bias=("vb1", "vbp", "vbc"))
# source follower: CD M1(drain vdd) + 싱크 M2.
FOLLOWER = topo("follower", (("M1", "nmos", "vdd", "in", "out"), ("M2", "nmos", "out", "vb", "gnd")),
                {"in": SE_IN, "out": SE_OUT}, bias=("vb",))
# 상보 push-pull follower: NMOS CD(drain vdd)·PMOS CD(drain gnd), 같은 입력·같은 출력.
PUSHPULL = topo("pushpull", (("M1", "nmos", "vdd", "in", "out"), ("M2", "pmos", "gnd", "in", "out")), {"in": SE_IN, "out": SE_OUT})
# 완전차동 + CMFB: 출력 om/op 를 R1/R2 로 평균(cm), 오차 증폭 M5(gate cm)/M6(gate vref), 꼬리 M7, diode M8 이 PMOS 부하 M3/M4 gate(cmfb).
CMFB = topo("cmfb", (("M1", "nmos", "om", "inp", "tail"), ("M2", "nmos", "op", "inn", "tail"), ("M0", "nmos", "tail", "vb", "gnd"),
                     ("M3", "pmos", "om", "cmfb", "vdd"), ("M4", "pmos", "op", "cmfb", "vdd"), ("M5", "nmos", "cmfb", "cm", "t2"),
                     ("M6", "nmos", "x6", "vref", "t2"), ("M7", "nmos", "t2", "vb", "gnd"), ("M8", "pmos", "cmfb", "cmfb", "vdd"),
                     ("M9", "pmos", "x6", "x6", "vdd")),
            {"inp": DIFF_P, "inn": DIFF_N, "op": OUT_P, "om": OUT_N},
            passives=(("R1", "resistor", ("om", "cm")), ("R2", "resistor", ("op", "cm"))), bias=("vb", "vref"))
# 단일 CS(PMOS 전류원 부하).
CS = topo("cs", (("M1", "nmos", "out", "in", "gnd"), ("M2", "pmos", "out", "vb", "vdd")), {"in": SE_IN, "out": SE_OUT}, bias=("vb",))
# 전압 구동 CG 증폭기: 입력 포트가 M1 source.
CG = topo("cg", (("M1", "nmos", "out", "vb", "in"), ("M2", "pmos", "out", "vbp", "vdd"), ("M3", "nmos", "in", "vb2", "gnd")),
          {"in": SE_IN, "out": SE_OUT}, bias=("vb", "vbp", "vb2"))
# CS 뒤 역병렬 pass 쌍(M3 nmos a->b, M4 pmos b->a, 두 gate 모두 외부 바이어스)이 출력 포트 b 로 간다.
PASS = topo("passb", (("M1", "nmos", "a", "in", "gnd"), ("M2", "pmos", "a", "vbp", "vdd"), ("M3", "nmos", "a", "vbn", "b"),
                      ("M4", "pmos", "b", "vbp2", "a"), ("M5", "nmos", "b", "vbn2", "gnd")),
            {"in": SE_IN, "b": SE_OUT}, bias=("vbp", "vbn", "vbp2", "vbn2"))
# PASS 에 같은 두 노드 사이 세 번째 소자 M6(a->b) 추가 -> 묶음 소자 3개.
PASS3 = topo("pass3", (("M1", "nmos", "a", "in", "gnd"), ("M2", "pmos", "a", "vbp", "vdd"), ("M3", "nmos", "a", "vbn", "b"),
                       ("M4", "pmos", "b", "vbp2", "a"), ("M6", "nmos", "a", "vbn3", "b"), ("M5", "nmos", "b", "vbn2", "gnd")),
             {"in": SE_IN, "b": SE_OUT}, bias=("vbp", "vbn", "vbp2", "vbn2", "vbn3"))
# 교차결합 PMOS 부하 차동쌍(래치형): om->op(M4 gate->drain), op->om(M3 gate->drain), 수동소자 없음.
XCOUP = topo("xcoup", (("M1", "nmos", "om", "inp", "tail"), ("M2", "nmos", "op", "inn", "tail"), ("M0", "nmos", "tail", "vb", "gnd"),
                       ("M3", "pmos", "om", "op", "vdd"), ("M4", "pmos", "op", "om", "vdd")),
             {"inp": DIFF_P, "inn": DIFF_N, "op": OUT_P, "om": OUT_N}, bias=("vb",))
# feedforward: 1단 CS M1(a) -> 2단 CS M3(out), 병렬 경로 PMOS CS M4(gate in -> out). out 이 두 경로의 합류 노드.
FF = topo("ff", (("M1", "nmos", "a", "in", "gnd"), ("M2", "pmos", "a", "vbp", "vdd"), ("M3", "nmos", "out", "a", "gnd"),
                 ("M4", "pmos", "out", "in", "vdd")), {"in": SE_IN, "out": SE_OUT}, bias=("vbp",))
# 레플리카 바이어스: NMOS 캐스코드 M5/M6 gate b 를 꼬리 노드에 얹힌 diode Mr(+ 전류원 Mi)이 만든다(N3.2-1 (4) 술어 입력).
REPLICA = topo("replica", (("M1", "nmos", "c1", "inp", "tail"), ("M2", "nmos", "c2", "inn", "tail"), ("M0", "nmos", "tail", "vb", "gnd"),
                           ("M5", "nmos", "om", "b", "c1"), ("M6", "nmos", "op", "b", "c2"), ("M3", "pmos", "om", "vbp", "vdd"),
                           ("M4", "pmos", "op", "vbp", "vdd"), ("Mr", "nmos", "b", "b", "tail"), ("Mi", "pmos", "b", "vbp", "vdd")),
               {"inp": DIFF_P, "inn": DIFF_N, "op": OUT_P, "om": OUT_N}, bias=("vb", "vbp"))
# 같은 회로를 단일 입력 두 개(차동 role 아님)로 선언 -> 입력마다 단일 여기 뷰(41 1.1), 꼬리 노드가 움직인다.
REPLICA_SE = topo("replica_se", tuple((n, k, d, {"inp": "in1", "inn": "in2"}.get(g, g), s) for n, k, d, g, s in (
    ("M1", "nmos", "c1", "inp", "tail"), ("M2", "nmos", "c2", "inn", "tail"), ("M0", "nmos", "tail", "vb", "gnd"),
    ("M5", "nmos", "om", "b", "c1"), ("M6", "nmos", "op", "b", "c2"), ("M3", "pmos", "om", "vbp", "vdd"),
    ("M4", "pmos", "op", "vbp", "vdd"), ("Mr", "nmos", "b", "b", "tail"), ("Mi", "pmos", "b", "vbp", "vdd"))),
    {"in1": SE_IN, "in2": SE_IN, "op": SE_OUT, "om": SE_OUT}, bias=("vb", "vbp"))
# CS 의 source s1 이 곧 출력 포트(drain x 는 막다른 가지) -> CD·CS 이중 출력 모호.
AMB = topo("amb", (("M1", "nmos", "x", "in", "s1"), ("M2", "pmos", "x", "vbp", "vdd"), ("M3", "nmos", "s1", "vb", "gnd")),
           {"in": SE_IN, "s1": SE_OUT}, bias=("vbp", "vb"))
# 출력 넷에 CD source(M1)와 신호 소자 drain(M2, gate = 입력 포트)이 함께 든 혼재 노드.
MIXED = topo("mixed", (("M1", "nmos", "vdd", "in", "out"), ("M2", "nmos", "out", "in", "gnd")), {"in": SE_IN, "out": SE_OUT})
# 접힘 노드 fx: drain 진입(M1) 뒤 채널(M5 캐스코드 source)과 gate(Mt, 출력 t 는 막다른 가지) 양쪽으로 나간다 -> tap.
TAP = topo("tap", (("M1", "nmos", "fx", "in", "gnd"), ("M3", "pmos", "fx", "vbp", "vdd"), ("M5", "pmos", "out", "vbc", "fx"),
                   ("M7", "nmos", "out", "vbn", "gnd"), ("Mt", "nmos", "t", "fx", "gnd"), ("Ml", "pmos", "t", "vbp", "vdd")),
           {"in": SE_IN, "out": SE_OUT}, bias=("vbp", "vbc", "vbn"))
# 한 입력에서 CD 둘이 서로 다른 출력 o1·o2 로 -> R(u) 싱크 2개.
BMULTI = topo("bmulti", (("M1", "nmos", "vdd", "in", "o1"), ("M2", "nmos", "vdd", "in", "o2"), ("M3", "nmos", "o1", "vb", "gnd"),
                         ("M4", "nmos", "o2", "vb", "gnd")), {"in": SE_IN, "o1": SE_OUT, "o2": SE_OUT}, bias=("vb",))
# diode 부하 CS(출력 넷을 gate 로 읽는 다른 소자 없음 = 종단 diode 부하).
CSDIODE = topo("csdiode", (("M1", "nmos", "out", "in", "gnd"), ("M2", "pmos", "out", "out", "vdd")), {"in": SE_IN, "out": SE_OUT})
# 신호 노드 in 에서 갈라진 막다른 교차결합 쌍(p<->q): 순방향 노드를 하나도 지나지 않는 루프.
BIASSCC = topo("biasscc", (("M1", "nmos", "out", "in", "gnd"), ("M2", "pmos", "out", "vbp", "vdd"), ("Mg", "nmos", "p", "in", "gnd"),
                           ("Mp1", "pmos", "p", "q", "vdd"), ("Mp2", "pmos", "q", "p", "vdd"), ("Mq", "nmos", "q", "vb", "gnd")),
               {"in": SE_IN, "out": SE_OUT}, bias=("vbp", "vb"))
# 저항 되먹임 CS: in -Rin- g, M1(gate g), Rf(out-g). 복귀 경로가 저항뿐인 루프.
RFB = topo("rfb", (("M1", "nmos", "out", "g", "gnd"), ("M2", "pmos", "out", "vbp", "vdd")), {"in": SE_IN, "out": SE_OUT},
           passives=(("Rin", "resistor", ("in", "g")), ("Rf", "resistor", ("out", "g"))), bias=("vbp",))
# CS drain a 에서 직렬 저항 R1 로만 출력 포트 out 에 닿는다(out 의 구동은 저항 상속).
RSER = topo("rser", (("M1", "nmos", "a", "in", "gnd"), ("M2", "pmos", "a", "vbp", "vdd")), {"in": SE_IN, "out": SE_OUT},
            passives=(("R1", "resistor", ("a", "out")), ("CL", "capacitor", ("out", "gnd"))), bias=("vbp",))
# 5T OTA 의 x-tail 사이 커패시터 두 개(병렬) -- 수동소자만의 왕복·사이클만 생긴다.
CAPROUND = topo("capround", (("M1", "nmos", "x", "inp", "tail"), ("M2", "nmos", "out", "inn", "tail"),
                             ("M3", "pmos", "x", "x", "vdd"), ("M4", "pmos", "out", "x", "vdd"),
                             ("M5", "nmos", "tail", "vb", "gnd")),
                {"inp": DIFF_P, "inn": DIFF_N, "out": SE_OUT},
                passives=(("C1", "capacitor", ("x", "tail")), ("C2", "capacitor", ("x", "tail"))), bias=("vb",))
# 2단 CS 사슬 + 막다른 형제 CS M5(gate a, drain z 는 출력에 닿지 않음). M3·M5 는 같은 (gate a, source gnd) 묶음.
LCREV = topo("lcrev", (("M1", "nmos", "a", "in", "gnd"), ("M2", "pmos", "a", "vbp", "vdd"), ("M3", "nmos", "out", "a", "gnd"),
                       ("M5", "nmos", "z", "a", "gnd"), ("M4", "pmos", "out", "vbp", "vdd"), ("M6", "pmos", "z", "vbp", "vdd")),
             {"in": SE_IN, "out": SE_OUT}, bias=("vbp",))
