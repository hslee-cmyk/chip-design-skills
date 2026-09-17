# -*- coding: utf-8 -*-
"""Independent re-implementation of the gain-budget-gmid-sizing plan rules (N3.2 SP1,
GB0 load gate, DEC-59/60/63/64/70/71/76/81) applied to the 9 library circuits.

Written from the plan text only; no repo engine code was consulted.
Results are APPENDED to out/*.jsonl and out/*.md so a crash keeps partial data.
"""
import json, os, sys, glob, itertools, collections
from pathlib import Path

import networkx as nx

LIB = Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library")
OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)


def emit(tag, obj):
    with open(OUT / "results.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"tag": tag, **obj}, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- loading
class Circuit:
    def __init__(self, path):
        self.path = path
        self.name = Path(path).name.replace(".topology.json", "")
        d = json.load(open(path, encoding="utf-8"))
        self.raw = d
        self.devices = [x for x in (d.get("netlist") or []) if isinstance(x, dict) and "name" in x]
        self.passives = [x for x in (d.get("passive_elements") or []) if isinstance(x, dict) and "name" in x]
        self.isources = [x for x in (d.get("ideal_sources") or []) if isinstance(x, dict) and "name" in x]
        self.supply_nets = d.get("supply_nets")
        ports = d.get("ports") or {}
        self.ports = {k: v for k, v in ports.items() if isinstance(v, dict) and not k.startswith("_")}
        self.sizing_roles = d.get("sizing_roles") or {}
        self.symmetry = d.get("symmetry") or {}
        self.dev = {x["name"]: x for x in self.devices}

    # --- net helpers
    def gate(self, m): return m["gate"]
    def drain(self, m): return m["drain"]
    def source(self, m): return m["source"]

    def all_nets(self):
        s = set()
        for m in self.devices:
            s |= {m["drain"], m["gate"], m["source"]}
            if m.get("bulk"): s.add(m["bulk"])
        for p in self.passives: s |= set(p["terminals"])
        for p in self.isources: s |= set(p["terminals"])
        s |= set(self.ports)
        return s

    def input_ports(self):
        return sorted([k for k, v in self.ports.items() if v.get("direction") == "input"
                       or "input" in str(v.get("role", ""))])

    def output_ports(self):
        return sorted([k for k, v in self.ports.items() if v.get("direction") == "output"
                       or "output" in str(v.get("role", ""))])

    def passive_terms(self):
        s = set()
        for p in self.passives: s |= set(p["terminals"])
        return s

    def isource_terms(self):
        s = set()
        for p in self.isources: s |= set(p["terminals"])
        return s


def load_all():
    out = []
    for f in sorted(LIB.glob("*.topology.json")):
        if "_TEMPLATE" in f.name: continue
        out.append(Circuit(f))
    return out


# ---------------------------------------------------------------- GB0
def dc_conduction_graph(c, prune=False):
    """DEC-70/71 DC conduction graph. edges: MOS channel (d-s), resistors, ideal sources.
    Gates and capacitors are not edges."""
    G = nx.MultiGraph()
    for n in c.all_nets(): G.add_node(n)
    for m in c.devices:
        G.add_edge(m["drain"], m["source"], key="dev:" + m["name"], etype="mos", name=m["name"])
    for p in c.passives:
        if p.get("kind") == "resistor":
            a, b = p["terminals"]
            G.add_edge(a, b, key="res:" + p["name"], etype="res", name=p["name"])
    for p in c.isources:
        a, b = p["terminals"]
        G.add_edge(a, b, key="src:" + p["name"], etype="isrc", name=p["name"])
    if prune:
        rails = set(c.supply_nets or [])
        ports = set(c.ports)
        changed = True
        while changed:
            changed = False
            for n in list(G.nodes()):
                if n in rails or n in ports: continue
                es = list(G.edges(n, keys=True, data=True))
                if len(es) == 1 and es[0][3].get("etype") == "res":
                    G.remove_edge(es[0][0], es[0][1], es[0][2])
                    changed = True
    return G


def gb0_gate(c):
    """GB0 load gate per DEC-60 (i)(ii)(iii) + constraint-source gate (U-35)."""
    res = {"circuit": c.name, "supply_nets": c.supply_nets, "checks": [], "verdict": "pass"}

    def fail(code, msg):
        res["checks"].append({"code": code, "result": "REJECT", "detail": msg})
        res["verdict"] = "reject"

    def ok(code, msg):
        res["checks"].append({"code": code, "result": "pass", "detail": msg})

    def unk(code, msg):
        res["checks"].append({"code": code, "result": "확인 못 함", "detail": msg})
        if res["verdict"] == "pass": res["verdict"] = "확인 못 함 있음"

    # supply_nets required for every library circuit
    if not c.supply_nets:
        fail("DEC-60/supply_nets", "supply_nets 미선언 (library 회로 전부 필수)")
    else:
        ok("DEC-60/supply_nets", f"{len(c.supply_nets)} rails declared: {c.supply_nets}")

    rails = set(c.supply_nets or [])
    # (i)/(ii): rail count & sign of supplies_v
    n_rails = len(rails)
    # authoritative supplies_v: sizing spec (run_harness.SPECS) only; topology _paper_target_spec is NOT authoritative
    SPECS_VDD = {"two_stage_ota": 1.8, "current_reuse_telescopic_ota": 1.8,
                 "folded_cascode": 1.8, "nmcnr_amplifier": 1.8}
    has_exec_spec = c.name in SPECS_VDD
    if n_rails >= 3:
        if has_exec_spec:
            fail("DEC-60(i)", f"레일 {n_rails}개 -> supplies_v 필수인데 실행 spec은 스칼라 vdd뿐")
        else:
            unk("DEC-60(i)",
                f"레일 {n_rails}개 -> DEC-60 '레일 셋 이상은 MG1 전에도 supplies_v 필수'. "
                f"정본 supplies_v(실행 SPECS)가 없음. topology _paper_target_spec.supplies_v는 정본 아님(N3.16). "
                f"판정 입력 부재 -> 계획이 거부/통과 어느 쪽인지 규정하지 않음")
    else:
        if has_exec_spec:
            ok("DEC-60(ii)", f"레일 2개 + 실행 spec 스칼라 vdd -> 전환기 이름집합 해석 허용(MG1 전)")
        else:
            unk("DEC-60(ii)", "레일 2개지만 실행 spec 없음 -> 레일 전압 부호 판정 입력 자체가 없음")

    # (iii) hidden rail candidates
    mos_terms = set()
    for m in c.devices: mos_terms |= {m["drain"], m["gate"], m["source"]}
    cand = []
    Graw = dc_conduction_graph(c, prune=False)
    for n in sorted(c.all_nets()):
        if n in mos_terms: continue
        if n not in (c.passive_terms() | c.isource_terms()): continue
        # DC-connected to any rail?
        conn = False
        for r in rails:
            if r == n: continue   # 판정은 선언과 독립이어야 한다(DEC-60(iii))
            if r in Graw and n in Graw and nx.has_path(Graw, n, r):
                conn = True; break
        if not conn:
            cand.append(n)
    res["hidden_rail_candidates"] = cand
    bad = [n for n in cand if n not in rails]
    if bad:
        fail("DEC-60(iii)", f"숨은 레일 후보 {bad} 가 supply_nets에 없음")
    else:
        ok("DEC-60(iii)", f"숨은 레일 후보 {cand} 전부 supply_nets에 있음" if cand else "숨은 레일 후보 없음")

    # constraint source gate (U-35)
    cons = c.sizing_roles.get("constraints")
    if cons is None:
        res["checks"].append({"code": "U-35/source", "result": "n/a", "detail": "constraints 미선언(사이징 스펙 없음)"})
    else:
        bad = [x for x in cons if not x.get("source")]
        badv = [x.get("metric") for x in cons if x.get("source") not in ("user_spec", "pending_7a", "reference")]
        srcs = collections.Counter(x.get("source") for x in cons)
        res["constraint_sources"] = dict(srcs)
        if bad or badv:
            fail("U-35/source", f"source 없음/허용 밖: {bad or badv}")
        elif len(cons) == 0:
            res["checks"].append({"code": "U-35/source", "result": "pass(공백)",
                                  "detail": "constraints=[] -- 제약 0건. GB0 출처 게이트는 통과하지만 판정 보류(U-35)"})
        else:
            ok("U-35/source", f"{dict(srcs)}")
    return res


# ---------------------------------------------------------------- views
def build_views(c):
    """기본 전달 뷰 (N3.2-2). 비축약 전체 뷰만 만든다 (대칭 축약은 계산 수단)."""
    ins, outs = c.input_ports(), c.output_ports()
    if not ins or not outs:
        return []
    diff_roles = {str(c.ports[p].get("role", "")) for p in ins}
    is_diff = len(ins) == 2 and any("differential" in r for r in diff_roles)
    if is_diff:
        return [{"kind": "transfer", "name": "diff_unreduced", "excite": set(ins), "sense": set(outs)}]
    return [{"kind": "transfer", "name": f"se_{p}", "excite": {p}, "sense": set(outs)} for p in ins]


def ac_ground_base(c, view):
    """Rule 1 (1)(2)(3). (4) is added later (needs signal reachability)."""
    rails = set(c.supply_nets or [])
    g = set(rails)
    # (2) gate-only, undriven nets
    gate_nets, chan_nets = set(), set()
    for m in c.devices:
        gate_nets.add(m["gate"]); chan_nets |= {m["drain"], m["source"]}
    excl = set(c.ports) | c.passive_terms() | c.isource_terms()
    for n in gate_nets - chan_nets:
        if n not in excl:
            g.add(n)
    # (3) ideal voltage source terminals
    for p in c.isources:
        if p.get("kind") == "voltage_source":
            g |= set(p["terminals"])
    return g


def signal_nets(c, view, acg):
    """Rule 3 minimal fixpoint signal-net set."""
    S = set(view["excite"]) - acg
    changed = True
    while changed:
        changed = False
        for m in c.devices:
            if m["gate"] in S:
                for t in (m["drain"], m["source"]):
                    if t not in acg and t not in S:
                        S.add(t); changed = True
            if m["source"] in S:
                t = m["drain"]
                if t not in acg and t not in S:
                    S.add(t); changed = True
        for p in c.passives:
            a, b = p["terminals"]
            for x, y in ((a, b), (b, a)):
                if x in S and y not in acg and y not in S:
                    S.add(y); changed = True
    return S


def fixpoint_edges(c, acg):
    """Directed edges of the minimal-fixpoint graph (for forward-path back-reachability)."""
    E = []
    for m in c.devices:
        E.append((m["gate"], m["drain"]))
        E.append((m["gate"], m["source"]))
        E.append((m["source"], m["drain"]))
    for p in c.passives:
        a, b = p["terminals"]
        E.append((a, b)); E.append((b, a))
    return [(u, v) for u, v in E if u not in acg and v not in acg]


def forward_path(c, view, acg, S):
    """규칙 3 정의: 최소 고정점 신호 넷 그래프에서 여기 포트로부터 도달하고
    출력 포트로 역도달하는 넷의 집합."""
    G = nx.DiGraph()
    G.add_nodes_from(S)
    for u, v in fixpoint_edges(c, acg):
        if u in S and v in S: G.add_edge(u, v)
    back = set()
    for o in view["sense"]:
        if o in G:
            back |= nx.ancestors(G, o) | {o}
    return S & back


def bias_dependent_nets(c, view, acg, S, FWD):
    """Rule 1 (4) 바이어스 종속 넷 술어."""
    out = []
    for b in sorted(S):
        # (0) b is a signal net in this view  -- true by construction
        # (i) signal leaves b only through gates
        leaves_channel = False
        for m in c.devices:
            if m["source"] == b and m["drain"] in S and m["drain"] != b:
                leaves_channel = True
        for p in c.passives:
            if b in p["terminals"]:
                leaves_channel = True  # passive carries current
        if leaves_channel: continue
        reads_gate = [m for m in c.devices if m["gate"] == b]
        if not reads_gate: continue
        # (ii) every channel terminal driving b is either (A) a channel terminal of a device
        #      that reads b as gate, or (B) a device whose gate is outside this view's signal path
        drivers = [m for m in c.devices if b in (m["drain"], m["source"])]
        okii = True
        classA = []
        for m in drivers:
            if m["gate"] == b:
                classA.append(m)
            elif m["gate"] not in S:
                pass  # bias current source
            else:
                okii = False
        if not okii or not classA: continue
        # (iii) one of classA sits on a chain, following source->drain only, not crossing ac-ground,
        #       not revisiting b, starting from a signal node that is still a signal net without b
        S_wo = signal_nets_without(c, view, acg, b)
        found = None
        for m in classA:
            # walk from m: start at m's drain? chain = source->drain direction traversal upstream
            seen = {b}
            stack = [m]
            start = None
            while stack:
                cur = stack.pop()
                if cur["name"] in seen: continue
                seen.add(cur["name"])
                src = cur["source"]
                if src in acg or src == b: continue
                if src in S_wo:
                    start = src; break
                for nxt in c.devices:
                    if nxt["drain"] == src and nxt["name"] not in seen:
                        stack.append(nxt)
            if start:
                found = (m["name"], start); break
        if found:
            out.append({"net": b, "gate_readers": [m["name"] for m in reads_gate],
                        "chain_device": found[0], "chain_start_signal_node": found[1]})
    return out


def signal_nets_without(c, view, acg, b):
    acg2 = set(acg) | {b}
    return signal_nets(c, view, acg2)


# ---------------------------------------------------------------- cells
def classify_cells(c, view, acg, S, FWD):
    """Rule 3 cell classification."""
    cells = {}
    # anti-parallel pass bundles: two devices between the same two nodes, opposite orientation,
    # both with gate outside the signal path
    bundles = []
    off_gate = [m for m in c.devices if m["gate"] not in S]
    for a, b in itertools.combinations(off_gate, 2):
        if a["drain"] == b["source"] and a["source"] == b["drain"] and a["drain"] != a["source"]:
            bundles.append((a["name"], b["name"], a["drain"], a["source"]))
    triple_warn = []
    pairmap = collections.defaultdict(list)
    for m in off_gate:
        pairmap[frozenset((m["drain"], m["source"]))].append(m["name"])
    for k, v in pairmap.items():
        if len(v) >= 3: triple_warn.append(sorted(v))
    in_bundle = set()
    for a, b, _, _ in bundles: in_bundle |= {a, b}

    ambiguous = []
    for m in c.devices:
        nm, g, d, s = m["name"], m["gate"], m["drain"], m["source"]
        if g == d:
            cells[nm] = {"cls": "diode(load)", "out": None, "reason": "gate==drain"}
            continue
        if g in S:  # gate receives signal
            if d in acg:
                cells[nm] = {"cls": "CD", "out": s, "reason": "drain is ac-gnd"}
            elif s in acg:
                cells[nm] = {"cls": "CS", "out": d, "reason": "source is ac-gnd"}
            else:
                cells[nm] = {"cls": "PENDING", "out": None, "reason": "neither terminal ac-gnd"}
                ambiguous.append(nm)
            continue
        # gate outside signal path
        if nm in in_bundle:
            cells[nm] = {"cls": "pass", "out": None, "reason": "anti-parallel pass bundle"}
        elif s in S:
            cells[nm] = {"cls": "CG", "out": d, "reason": "gate off-path, source is signal net"}
        else:
            touches = (d in S) or (s in S)
            cells[nm] = {"cls": "load" if touches else "off_path", "out": None,
                         "reason": "gate off-path, source not signal net"}

    # resolve PENDING (CS/CD dual-output test with forward restriction)
    for nm in ambiguous:
        m = c.dev[nm]
        s = m["source"]
        hit = None
        # does source node touch another signal cell's input terminal or an output port?
        if s in view["sense"]:
            hit = ("output_port", s)
        for m2 in c.devices:
            if m2["name"] == nm: continue
            if m2["gate"] == m2["drain"]: continue        # diode excluded from this test
            inp = None
            cl2 = cells.get(m2["name"], {}).get("cls")
            if m2["gate"] == s and cl2 in ("CS", "CD", "PENDING"): inp = "gate"
            if m2["source"] == s and cl2 == "CG": inp = "source"
            if inp:
                out2 = cells[m2["name"]]["out"]
                if cl2 == "PENDING":
                    hit = ("ambiguous_partner", m2["name"]); break
                if out2 in FWD:
                    hit = ("cell_input", m2["name"]); break
        if hit:
            cells[nm] = {"cls": "review_needed(CS/CD dual output)", "out": None, "reason": str(hit)}
        else:
            cells[nm] = {"cls": "CS", "out": m["drain"], "reason": "degeneration (source touches nothing forward)"}
    return cells, bundles, triple_warn


# ---------------------------------------------------------------- drive kind
def drive_kinds(c, view, acg, S, FWD, cells):
    """용어집 '입력 노드 구동 종류' (우선순위 규정 포함)."""
    CELL = {"CS", "CG", "CD", "pass"}
    res = {}
    for n in sorted(S):
        cur, volt, resist, side = [], [], [], []
        for m in c.devices:
            cl = cells[m["name"]]["cls"]
            if cl not in CELL: continue
            if cl == "pass":
                # 2-terminal bundle has no direction: counted as an outgoing channel path only
                continue
            if m["drain"] == n and cl in ("CS", "CG"):
                cur.append((m["name"], cl))
            if m["source"] == n and cl in ("CS", "CD"):
                # gate로 신호 받는 셀의 source 단자에서 나오는 노드 -> 전압 구동
                volt.append((m["name"], cl))
        if n in view["excite"]:
            volt.append(("<port>", "input_port"))
        for p in c.passives:
            if p.get("kind") == "resistor" and n in p["terminals"]:
                other = [t for t in p["terminals"] if t != n]
                resist.append((p["name"], other[0] if other else None))
        res[n] = {"current_entries": cur, "voltage_entries": volt, "resistor_entries": resist}

    # outgoing terminals
    def outgoing(n):
        gate_out, chan_out = [], []
        for m in c.devices:
            cl = cells[m["name"]]["cls"]
            if m["gate"] == n and cl in ("CS", "CD"):
                gate_out.append(m["name"])
            if cl == "CG" and m["source"] == n:
                chan_out.append(m["name"])
            if cl == "pass" and n in (m["drain"], m["source"]):
                chan_out.append(m["name"])
        return gate_out, chan_out

    verdict = {}
    for n, info in res.items():
        go, co = outgoing(n)
        val_dep = bool(info["resistor_entries"])
        if info["current_entries"] and info["voltage_entries"]:
            # 혼재 우선 규칙 (용어집): 신호 셀 source(전압 진입) + 측면 주입 셀(K8) drain -> 전압 구동.
            # drain 쪽 셀이 K8이 아니면 review_needed.
            k8 = []
            for dn, dcl in info["current_entries"]:
                md = c.dev[dn]
                cd_at = [m2 for m2 in c.devices
                         if cells[m2["name"]]["cls"] == "CD" and m2["source"] == n]
                # K8 also requires: n is not any gain block's output node.  Every CS whose drain
                # is n makes n a block output node, so record that as the blocking condition.
                block_out = any(cells[m2["name"]]["cls"] in ("CS", "CG") and m2["drain"] == n
                                for m2 in c.devices)
                k8.append({"device": dn, "cd_source_at_node": [x["name"] for x in cd_at],
                           "n_is_block_output_node": block_out,
                           "is_K8": bool(cd_at) and not block_out})
            if all(x["is_K8"] for x in k8):
                verdict[n] = {"kind": "voltage", "rule": "혼재 우선 규칙(K8 측면 주입 확인)",
                              "value_dependent": val_dep, "gate_out": go, "chan_out": co,
                              "k8": k8}
            else:
                verdict[n] = {"kind": "review_needed",
                              "rule": "혼재 우선 규칙: drain 쪽 셀이 K8이 아님 -> review_needed(기록만)",
                              "value_dependent": val_dep, "gate_out": go, "chan_out": co,
                              "k8": k8,
                              "flag": "review_needed(혼재 우선 규칙, J12-b/J12-d)"}
            continue
        if info["current_entries"]:
            if go and not co:
                k, r = "voltage", "우선순위: 나가는 단자가 gate뿐"
            elif co and not go:
                k, r = "current", "우선순위: 나가는 단자가 채널뿐"
            elif go and co:
                # gate-side cell's output terminal also on forward path?
                gate_fwd = any(cells[x]["out"] in FWD for x in go)
                if gate_fwd:
                    k, r = "voltage", "우선순위: gate·채널 동시 + gate쪽 출력 단자도 순방향"
                else:
                    k, r = "tap", "우선순위: gate쪽이 순방향을 잇지 못함 -> tap (규칙 9(a))"
            else:
                k, r = "current", "전류 진입만, 나가는 단자 없음(종단)"
            verdict[n] = {"kind": k, "rule": r, "value_dependent": val_dep,
                          "gate_out": go, "chan_out": co}
            continue
        if info["voltage_entries"]:
            verdict[n] = {"kind": "voltage", "rule": "전압 진입만", "value_dependent": val_dep,
                          "gate_out": go, "chan_out": co}
            continue
        if info["resistor_entries"]:
            verdict[n] = {"kind": "inherit", "rule": "저항 진입만 -> 반대쪽 상속",
                          "value_dependent": True, "gate_out": go, "chan_out": co,
                          "inherit_from": [x[1] for x in info["resistor_entries"]]}
            continue
        verdict[n] = {"kind": "none", "rule": "신호 진입 없음", "value_dependent": val_dep,
                      "gate_out": go, "chan_out": co}

    # propagate inheritance
    for _ in range(len(verdict) + 2):
        for n, v in verdict.items():
            if v["kind"] != "inherit": continue
            srcs = [verdict.get(x, {}).get("kind") for x in v.get("inherit_from", [])]
            srcs = [x for x in srcs if x in ("voltage", "current", "tap")]
            if srcs:
                k0 = srcs[0]
                # 용어집: "상속·혼합으로 전류 진입이 붙은 노드도 최종 구동 종류는 위 우선순위가 가른다"
                if k0 == "current":
                    go, co = v["gate_out"], v["chan_out"]
                    if go and not co: k0 = "voltage"
                    elif go and co:
                        k0 = "voltage" if any(cells[x]["out"] in FWD for x in go) else "tap"
                v["kind"] = k0; v["rule"] += f" (상속 후 우선순위 적용: {k0})"
    for n, v in verdict.items():
        if v["kind"] == "inherit":
            v["kind"] = "review_needed"; v["rule"] += " (순환/미정)"
    return res, verdict


# ---------------------------------------------------------------- stages / rule 5
def stage_assign(c, view, cells, dk):
    starts, cascodes, buffers, notes = [], [], [], []
    for nm, info in sorted(cells.items()):
        cl = info["cls"]
        m = c.dev[nm]
        if cl == "CS":
            n = m["gate"]
            k = dk.get(n, {}).get("kind")
            if k == "voltage":
                starts.append((nm, "CS", n))
            elif k in ("current", "tap"):
                notes.append({"device": nm, "cls": "CS", "input_node": n, "drive": k,
                              "rule": "규칙 9 (a) 기록만 -- gate가 전류 구동/tap 노드"})
            else:
                notes.append({"device": nm, "cls": "CS", "input_node": n, "drive": k,
                              "rule": "구동 종류 미정 -> review_needed"})
        elif cl == "CG":
            n = m["source"]
            k = dk.get(n, {}).get("kind")
            if k == "voltage":
                starts.append((nm, "CG(voltage-driven source)", n))
            elif k in ("current", "tap"):
                cascodes.append((nm, n, k))
            else:
                notes.append({"device": nm, "cls": "CG", "input_node": n, "drive": k,
                              "rule": "구동 종류 미정 -> review_needed"})
        elif cl == "CD":
            n = m["gate"]
            buffers.append((nm, n, dk.get(n, {}).get("kind")))
    return {"stage_starts": starts, "cascodes": cascodes, "buffers": buffers, "rule9a_or_undefined": notes}


# ---------------------------------------------------------------- rule 2 loops
def loop_graph(c, view, acg, dk_verdict):
    """방향 신호 그래프 (교류접지 + 여기 포트 제거)."""
    removed = set(acg) | set(view["excite"])
    G = nx.DiGraph()
    for n in c.all_nets():
        if n not in removed: G.add_node(n)
    edge_meta = collections.defaultdict(list)
    for m in c.devices:
        g, d, s = m["gate"], m["drain"], m["source"]
        for u, v, kind in ((g, d, "g->d"), (g, s, "g->s")):
            if u in G and v in G and u != v:
                G.add_edge(u, v); edge_meta[(u, v)].append((m["name"], kind))
        if dk_verdict.get(s, {}).get("kind") in ("current", "tap"):
            if s in G and d in G and s != d:
                G.add_edge(s, d); edge_meta[(s, d)].append((m["name"], "s->d"))
    for p in c.passives:
        a, b = p["terminals"]
        if a in G and b in G and a != b:
            G.add_edge(a, b); edge_meta[(a, b)].append((p["name"], "passive"))
            G.add_edge(b, a); edge_meta[(b, a)].append((p["name"], "passive"))
    return G, edge_meta, removed


def enumerate_cycles(G, edge_meta, c, cap=20000):
    out = []
    passive_names = {p["name"] for p in c.passives}
    for cyc in nx.simple_cycles(G):
        if len(cyc) < 2: continue
        if len(cyc) == 2:
            u, v = cyc
            a = {n for n, k in edge_meta[(u, v)]}
            b = {n for n, k in edge_meta[(v, u)]}
            # 2-terminal passive round trip -> not a closed path
            if (a & b & passive_names):
                continue
        out.append(cyc)
        if len(out) >= cap: break
    return out


def bfs_dist(c, view, acg, cells, dk_verdict, passive_cost):
    """규칙 4 0-1 BFS 거리."""
    removed = set(acg) | (set(view["excite"]) if False else set())
    G = nx.DiGraph()
    for n in c.all_nets():
        if n not in acg: G.add_node(n)
    diode_nets = {m["gate"] for m in c.devices if m["gate"] == m["drain"]}

    def add(u, v, w):
        if u in G and v in G and u != v:
            if G.has_edge(u, v):
                G[u][v]["weight"] = min(G[u][v]["weight"], w)
            else:
                G.add_edge(u, v, weight=w)
    for m in c.devices:
        g, d, s = m["gate"], m["drain"], m["source"]
        add(g, d, 0 if g in diode_nets else 1)
        add(g, s, 0)
        cl = cells[m["name"]]["cls"]
        if cl == "CG" and dk_verdict.get(s, {}).get("kind") == "voltage":
            add(s, d, 1)
        else:
            add(s, d, 0)
    for p in c.passives:
        a, b = p["terminals"]
        add(a, b, passive_cost); add(b, a, passive_cost)
    src = [n for n in view["excite"] if n in G]
    dist = {}
    for s0 in src:
        d0 = nx.single_source_dijkstra_path_length(G, s0, weight="weight")
        for k, v in d0.items():
            dist[k] = min(dist.get(k, 1e9), v)
    return dist


def classify_loops(c, view, acg, S, FWD, cells, dk_verdict, cycles, dist, edge_meta):
    passive_names = {p["name"]: p for p in c.passives}
    ACTIVE = {"CS", "CG", "CD", "pass"}
    out = []
    for cyc in cycles:
        L = len(cyc)
        edges = [(cyc[i], cyc[(i + 1) % L]) for i in range(L)]
        elems = [edge_meta[e] for e in edges]
        seg_is_passive = [all(n in passive_names for n, k in es) for es in elems]
        devs_on = set()
        for es in elems:
            for n, k in es:
                if n not in passive_names: devs_on.add(n)
        rec = {"cycle": cyc, "elements": [[f"{n}({k})" for n, k in es] for es in elems]}

        # (1.5) bias SCC: touches no forward-path node
        if not (set(cyc) & FWD):
            rec["class"] = "(1.5) bias SCC"; out.append(rec); continue

        # (2) Miller: maximal passive-only segment containing a capacitor whose two ends are on FWD
        miller = False
        if any(seg_is_passive):
            # find maximal runs of passive segments on the cycle (circular)
            idx = [i for i in range(L) if seg_is_passive[i]]
            runs = []
            used = set()
            for i in idx:
                if i in used: continue
                run = [i]; used.add(i)
                j = (i + 1) % L
                while seg_is_passive[j] and j not in used:
                    run.append(j); used.add(j); j = (j + 1) % L
                k = (i - 1) % L
                while seg_is_passive[k] and k not in used:
                    run.insert(0, k); used.add(k); k = (k - 1) % L
                runs.append(run)
            for run in runs:
                has_cap = any(any(passive_names[n].get("kind") == "capacitor"
                                  for n, kk in elems[i]) for i in run)
                a = cyc[run[0]]
                b = cyc[(run[-1] + 1) % L]
                if has_cap and a in FWD and b in FWD:
                    miller = True; break
        rec["miller"] = miller

        # return path: maximal contiguous runs of non-increasing-distance edges
        back = []
        for i, (u, v) in enumerate(edges):
            du, dv = dist.get(u), dist.get(v)
            if du is None or dv is None:
                back.append(False)
            else:
                back.append(dv <= du)
        runs = []
        used = set()
        for i in range(L):
            if not back[i] or i in used: continue
            run = [i]; used.add(i)
            j = (i + 1) % L
            while back[j] and j not in used:
                run.append(j); used.add(j); j = (j + 1) % L
            k = (i - 1) % L
            while back[k] and k not in used:
                run.insert(0, k); used.add(k); k = (k - 1) % L
            runs.append(run)
        rec["return_runs"] = [[f"{cyc[i]}->{cyc[(i+1)%L]}" for i in run] for run in runs]

        def run_actives(run):
            a = set()
            for i in run:
                for n, k in elems[i]:
                    if n not in passive_names and cells.get(n, {}).get("cls") in ACTIVE:
                        a.add(n)
            return a

        def run_passives(run):
            p = set()
            for i in run:
                for n, k in elems[i]:
                    if n in passive_names: p.add(n)
            return p

        three_b = False; note = []
        for run in runs:
            ra, rp = run_actives(run), run_passives(run)
            if not ra:
                note.append("(가) 복귀 경로 수동소자만 -> (3-b) 아님"); continue
            if not rp and len(ra) == 2:
                note.append("(나) 수동소자 없는 2능동셀 루프 -> 기록만"); continue
            three_b = True
        rec["return_note"] = note

        # (3-a): active cell not on ANY transfer view's forward path
        three_a = [d for d in devs_on if cells.get(d, {}).get("cls") in ACTIVE
                   and cells[d].get("out") not in FWD and cells[d].get("out") is not None]
        rec["3a_candidates"] = sorted(three_a)

        klass = []
        if miller: klass.append("(2) Miller")
        if three_b: klass.append("(3-b)")
        if not klass:
            if any("(나)" in x for x in note):
                klass.append("기록만(나: 수동소자 없는 2능동셀)")
            else:
                klass.append("(4) 나머지")
        rec["class"] = " + ".join(klass)
        rec["devices"] = sorted(devs_on)
        # break point candidates for loop views
        if "(3-b)" in rec["class"]:
            rec["break_candidates"] = sorted({c.dev[d]["gate"] for d in devs_on
                                              if cells.get(d, {}).get("cls") == "CS"})
        out.append(rec)
    return out


# ---------------------------------------------------------------- DEC-71
def branches_columns(c):
    G = dc_conduction_graph(c, prune=True)
    rails = set(c.supply_nets or [])
    deg = {n: G.degree(n) for n in G.nodes()}
    branch_nodes = {n for n in G.nodes() if deg[n] >= 3}
    nonrail_branch_nodes = sorted(branch_nodes - rails)
    terminals = (branch_nodes | rails)
    # branches: maximal series chains between terminals
    branches = []
    visited_edges = set()
    for t in sorted(terminals):
        for (u, v, k) in list(G.edges(t, keys=True)):
            if (u, v, k) in visited_edges or (v, u, k) in visited_edges: continue
            path_edges = [(u, v, k)]
            visited_edges.add((u, v, k))
            cur = v if u == t else u
            prev = t
            while cur not in terminals:
                nxts = [(a, b, kk) for (a, b, kk) in G.edges(cur, keys=True)
                        if (a, b, kk) not in visited_edges and (b, a, kk) not in visited_edges]
                if len(nxts) != 1: break
                a, b, kk = nxts[0]
                visited_edges.add((a, b, kk))
                path_edges.append((a, b, kk))
                nxt = b if a == cur else a
                prev, cur = cur, nxt
            branches.append({"ends": sorted([t, cur]), "edges": [kk for _, _, kk in path_edges]})
    # columns: node-simple paths between two distinct rail nets, on the branch graph
    BG = nx.MultiGraph()
    for i, b in enumerate(branches):
        BG.add_edge(b["ends"][0], b["ends"][1], key=i)
    cols = []
    rl = sorted(r for r in rails if r in BG)
    for r1, r2 in itertools.combinations(rl, 2):
        try:
            for p in nx.all_simple_edge_paths(BG, r1, r2):
                cols.append({"pair": [r1, r2], "branches": [e[2] for e in p]})
                if len(cols) > 5000: break
        except nx.NetworkXNoPath:
            pass
    used = set()
    for col in cols: used |= set(col["branches"])
    orphan = [i for i in range(len(branches)) if i not in used]
    return {"n_branches": len(branches), "branch_nodes_nonrail": nonrail_branch_nodes,
            "n_branch_nodes_nonrail": len(nonrail_branch_nodes),
            "n_columns": len(cols), "columns": cols, "branches": branches,
            "orphan_branches": orphan}


# ---------------------------------------------------------------- driver
def run():
    circuits = load_all()
    all_res = {}
    for c in circuits:
        rec = {"circuit": c.name, "n_devices": len(c.devices), "n_passives": len(c.passives),
               "n_isources": len(c.isources)}
        rec["gb0"] = gb0_gate(c)
        emit("gb0", rec["gb0"])
        views = build_views(c)
        rec["n_views"] = len(views)
        rec["views"] = []
        for view in views:
            acg0 = ac_ground_base(c, view)
            S0 = signal_nets(c, view, acg0)
            F0 = forward_path(c, view, acg0, S0)
            bd = bias_dependent_nets(c, view, acg0, S0, F0)
            # apply rule 1 (4): bias-dependent nets become ac-ground in views whose excitation
            # does not move the chain start.  In the unreduced differential transfer view the
            # excitation moves every signal node, so we report BOTH readings.
            acg = set(acg0) | {x["net"] for x in bd}
            S = signal_nets(c, view, acg)
            F = forward_path(c, view, acg, S)
            cells, bundles, triples = classify_cells(c, view, acg, S, F)
            dkraw, dk = drive_kinds(c, view, acg, S, F, cells)
            st = stage_assign(c, view, cells, dk)
            counts = collections.Counter(v["cls"] for v in cells.values())
            fwd_counts = collections.Counter(
                v["cls"] for v in cells.values() if v.get("out") in F)
            G, em, removed = loop_graph(c, view, acg, dk)
            cycles = enumerate_cycles(G, em, c)
            loops = {}
            for pc in (0, 1):
                dist = bfs_dist(c, view, acg, cells, dk, pc)
                cl = classify_loops(c, view, acg, S, F, cells, dk, cycles, dist, em)
                kc = collections.Counter(x["class"] for x in cl)
                loops[f"passive_cost_{pc}"] = {"counts": dict(kc), "detail": cl}
            vrec = {"view": view["name"], "excite": sorted(view["excite"]), "sense": sorted(view["sense"]),
                    "ac_ground_base": sorted(acg0), "bias_dependent_nets": bd,
                    "ac_ground_with_rule1_4": sorted(acg),
                    "n_signal_nets": len(S), "signal_nets": sorted(S),
                    "forward_path": sorted(F),
                    "cells": cells, "cell_counts": dict(counts), "cell_counts_forward": dict(fwd_counts),
                    "pass_bundles": bundles, "triple_pass_warn": triples,
                    "drive_kinds": {k: v for k, v in dk.items()},
                    "stages": st,
                    "n_cycles": len(cycles), "loops": loops}
            rec["views"].append(vrec)
            emit("view", {"circuit": c.name, **{k: v for k, v in vrec.items() if k != "loops"}})
            emit("loops", {"circuit": c.name, "view": view["name"],
                           "n_cycles": len(cycles),
                           "counts_pc0": loops["passive_cost_0"]["counts"],
                           "counts_pc1": loops["passive_cost_1"]["counts"],
                           "detail_pc0": loops["passive_cost_0"]["detail"],
                           "detail_pc1": loops["passive_cost_1"]["detail"]})
        rec["dec71"] = branches_columns(c)
        emit("dec71", {"circuit": c.name, **{k: v for k, v in rec["dec71"].items() if k != "columns"}})
        all_res[c.name] = rec
    json.dump(all_res, open(OUT / "all.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("done", len(all_res))


if __name__ == "__main__":
    run()
