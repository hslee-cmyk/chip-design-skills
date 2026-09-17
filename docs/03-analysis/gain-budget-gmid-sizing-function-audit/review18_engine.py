# -*- coding: utf-8 -*-
"""Independent re-implementation of gain-budget-gmid-sizing plan rules (N3.2 SP1 1..9,
DEC-59/60/63/64/70/71/76/81) applied to the 9 library topologies.

Written from the plan text only (no prior reviewer scripts consulted).
Results are APPENDED to out/*.jsonl and out/report.txt so partial runs survive.
"""
import json, os, sys, itertools, collections
import networkx as nx

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library"
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

def emit(tag, obj):
    with open(os.path.join(OUT, "results.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"tag": tag, "data": obj}, ensure_ascii=False) + "\n")

def log(s):
    with open(os.path.join(OUT, "report.txt"), "a", encoding="utf-8") as f:
        f.write(s + "\n")
    print(s)

# ---------------------------------------------------------------- loading
class Circuit:
    def __init__(self, path):
        d = json.load(open(path, encoding="utf-8"))
        self.raw = d
        self.name = d.get("topology_name") or os.path.basename(path).replace(".topology.json", "")
        self.file = os.path.basename(path)
        self.devs = []
        for t in d.get("netlist", []):
            if not isinstance(t, dict) or "name" not in t:
                continue
            self.devs.append({"name": t["name"], "kind": t.get("kind"),
                              "d": t.get("drain"), "g": t.get("gate"), "s": t.get("source"),
                              "bulk": t.get("bulk")})
        self.pas = []
        for p in (d.get("passive_elements") or []):
            self.pas.append({"name": p["name"], "kind": p.get("kind"),
                             "t": list(p.get("terminals") or []),
                             "value": p.get("value_ohm", p.get("value_farad"))})
        self.ideal = []
        for p in (d.get("ideal_sources") or []):
            self.ideal.append({"name": p["name"], "kind": p.get("kind"),
                               "t": list(p.get("terminals") or []), "value": p.get("value_amp", p.get("value_volt"))})
        self.supply_nets = d.get("supply_nets")
        ports = d.get("ports") or {}
        self.ports = {k: v for k, v in ports.items() if not k.startswith("_") and isinstance(v, dict)}
        self.inputs = [k for k, v in self.ports.items() if v.get("direction") == "input"]
        self.outputs = [k for k, v in self.ports.items() if v.get("direction") == "output"]
        sym = d.get("symmetry") or {}
        self.matching_pairs = sym.get("matching_pairs") or []
        sr = d.get("sizing_roles")
        self.sizing_roles = sr if isinstance(sr, dict) else None
        self.constraints = (sr or {}).get("constraints") if isinstance(sr, dict) else None

    # ---- net helpers
    def nets(self):
        s = set()
        for t in self.devs:
            s |= {t["d"], t["g"], t["s"]}
        for p in self.pas:
            s |= set(p["t"])
        for p in self.ideal:
            s |= set(p["t"])
        s.discard(None)
        return s

    def mos_terminal_nets(self):
        s = set()
        for t in self.devs:
            s |= {t["d"], t["g"], t["s"]}
        s.discard(None)
        return s

    def channel_nets(self):
        s = set()
        for t in self.devs:
            s |= {t["d"], t["s"]}
        s.discard(None)
        return s


def load_all():
    out = []
    for fn in sorted(os.listdir(LIB)):
        if not fn.endswith(".topology.json") or fn.startswith("_TEMPLATE"):
            continue
        out.append(Circuit(os.path.join(LIB, fn)))
    return out

# ---------------------------------------------------------------- DC conduction graph (DEC-70/71)
def dc_graph(c, prune_leaf_resistors=True):
    """edges = MOS channel (d-s), resistors (after leaf pruning), ideal sources. gates/caps are not edges."""
    G = nx.MultiGraph()
    for t in c.devs:
        G.add_edge(t["d"], t["s"], key=t["name"], kind="mos", name=t["name"])
    for p in c.pas:
        if p["kind"] == "resistor" and len(p["t"]) == 2:
            G.add_edge(p["t"][0], p["t"][1], key=p["name"], kind="res", name=p["name"])
    for p in c.ideal:
        if len(p["t"]) == 2:
            G.add_edge(p["t"][0], p["t"][1], key=p["name"], kind="ideal", name=p["name"])
    if prune_leaf_resistors:
        rails = set(c.supply_nets or [])
        portn = set(c.ports)
        changed = True
        while changed:
            changed = False
            for n in list(G.nodes()):
                if n in rails or n in portn:
                    continue
                inc = list(G.edges(n, keys=True, data=True))
                if len(inc) == 1 and inc[0][3]["kind"] == "res":
                    G.remove_edge(inc[0][0], inc[0][1], inc[0][2])
                    if G.degree(n) == 0:
                        G.remove_node(n)
                    changed = True
    return G

# ---------------------------------------------------------------- GB0 load gate (DEC-60)
def gb0(c):
    res = {"circuit": c.name, "checks": [], "verdict": "pass"}
    def fail(code, detail):
        res["checks"].append({"code": code, "status": "REJECT", "detail": detail})
        res["verdict"] = "reject"
    def ok(code, detail):
        res["checks"].append({"code": code, "status": "pass", "detail": detail})
    def note(code, detail):
        res["checks"].append({"code": code, "status": "note", "detail": detail})

    # supply_nets required for every library circuit
    if not c.supply_nets:
        fail("DEC-60/supply_nets", "supply_nets 미선언")
    else:
        ok("DEC-60/supply_nets", f"{c.supply_nets}")

    # (iii) hidden rail candidate: net never on a MOS terminal, only on passive/ideal terminals,
    #       and DC-isolated from every rail net in the PRE-PRUNING dc graph.
    mosn = c.mos_terminal_nets()
    pasn = set()
    for p in c.pas:
        pasn |= set(p["t"])
    for p in c.ideal:
        pasn |= set(p["t"])
    cand = sorted(n for n in pasn if n not in mosn)
    Graw = dc_graph(c, prune_leaf_resistors=False)
    rails = set(c.supply_nets or [])
    hidden = []
    for n in cand:
        connected = False
        if n in Graw:
            comp = nx.node_connected_component(Graw, n)
            connected = bool(comp & rails)
        if not connected:
            hidden.append(n)
    if hidden:
        missing = [n for n in hidden if n not in rails]
        if missing:
            fail("DEC-60(iii)/hidden_rail", f"DC 고립 넷 {missing} 이(가) supply_nets에 없음")
        else:
            ok("DEC-60(iii)/hidden_rail", f"DC 고립 넷 {hidden} 전부 supply_nets에 선언됨")
    else:
        ok("DEC-60(iii)/hidden_rail", "DC 고립 후보 없음")

    # supplies_v: topology.json 밖(실행 SPECS/sizing_spec.json). 여기서는 존재 여부만 기록.
    note("DEC-60/supplies_v", "topology.json에는 supplies_v가 없다(스펙 측 선언). 이 측정에서는 확인 못 함")

    # ports (기본 전달 뷰 가능 여부)
    if not c.inputs:
        fail("GB0/ports.input", "input 역할 포트 없음 -> 기본 전달 뷰 불가")
    if not c.outputs:
        fail("GB0/ports.output", "output 역할 포트 없음 -> 순방향 경로 불가")
    if c.inputs and c.outputs:
        ok("GB0/ports", f"in={c.inputs} out={c.outputs}")

    # 제약값 출처
    if c.constraints is None:
        note("GB0/constraints", "sizing_roles.constraints 키 없음(사이징 스펙 미선언 회로)")
    elif c.constraints == []:
        note("GB0/constraints", "constraints=[] (빈 목록)")
    else:
        srcs = []
        for k in c.constraints:
            srcs.append({"metric": k.get("metric"), "source": k.get("source"),
                         "has_value": ("value" in k or "value_from_spec" in k)})
            if not k.get("source"):
                fail("GB0/constraint_source", f"{k.get('metric')}: source 없음")
            elif "paper" in str(k.get("source")).lower() or "논문" in str(k.get("source")):
                fail("GB0/constraint_source", f"{k.get('metric')}: 논문 출처")
        res["constraint_sources"] = srcs
        ok("GB0/constraint_source", f"{len(c.constraints)}건 검사")
    return res

# ---------------------------------------------------------------- views
def build_views(c):
    """기본 전달 뷰(N3.2-2). metric 선언이 없으므로 ports로 만든다."""
    views = []
    if not c.inputs or not c.outputs:
        return views
    sym_pair = False
    if len(c.inputs) == 2:
        # find_structural_symmetry_candidates 대용: 두 입력 포트를 gate로 받는 소자가
        # 같은 source 노드를 공유하는 매칭 쌍이면 대응으로 본다.
        a, b = c.inputs
        da = [t for t in c.devs if t["g"] == a]
        db = [t for t in c.devs if t["g"] == b]
        if da and db and {t["s"] for t in da} == {t["s"] for t in db} and len(da) == len(db):
            sym_pair = True
    if sym_pair:
        views.append({"id": "dm", "excite": set(c.inputs), "sense": set(c.outputs), "mode": "differential(비축약)"})
    else:
        for i in c.inputs:
            views.append({"id": f"se_{i}", "excite": {i}, "sense": set(c.outputs), "mode": "single"})
    return views

# ---------------------------------------------------------------- rule 1 ac ground
def ac_ground_base(c):
    """(1) rails (2) gate-only undriven nets (3) ideal voltage source terminals"""
    s = set(c.supply_nets or [])
    chan = c.channel_nets()
    pasn = set()
    for p in c.pas:
        pasn |= set(p["t"])
    idn = set()
    for p in c.ideal:
        idn |= set(p["t"])
    portn = set(c.ports)
    gate_only = set()
    for t in c.devs:
        g = t["g"]
        if g in chan or g in pasn or g in idn or g in portn:
            continue
        gate_only.add(g)
    s |= gate_only
    for p in c.ideal:
        if p["kind"] in ("voltage_source", "vsource"):
            s |= set(p["t"])
    s.discard(None)
    return s, gate_only

def signal_nets(c, excite, acg, removed=frozenset()):
    """규칙 3 최소 고정점 신호 넷 그래프."""
    S = set(n for n in excite if n not in acg)
    changed = True
    while changed:
        changed = False
        for t in c.devs:
            if t["g"] in S:
                for n in (t["d"], t["s"]):
                    if n and n not in acg and n not in removed and n not in S:
                        S.add(n); changed = True
            if t["s"] in S:
                n = t["d"]
                if n and n not in acg and n not in removed and n not in S:
                    S.add(n); changed = True
        for p in c.pas:
            if len(p["t"]) != 2:
                continue
            u, v = p["t"]
            for a, b in ((u, v), (v, u)):
                if a in S and b not in acg and b not in removed and b not in S:
                    S.add(b); changed = True
    return S

def signal_digraph(c, S, acg):
    """최소 고정점 그래프의 방향 엣지(순방향 경로 계산용)."""
    G = nx.DiGraph()
    G.add_nodes_from(S)
    for t in c.devs:
        if t["g"] in S:
            for n in (t["d"], t["s"]):
                if n in S:
                    G.add_edge(t["g"], n, via=t["name"])
        if t["s"] in S and t["d"] in S:
            G.add_edge(t["s"], t["d"], via=t["name"])
    for p in c.pas:
        if len(p["t"]) == 2 and p["t"][0] in S and p["t"][1] in S:
            G.add_edge(p["t"][0], p["t"][1], via=p["name"])
            G.add_edge(p["t"][1], p["t"][0], via=p["name"])
    return G

def forward_path(c, view, S, acg):
    G = signal_digraph(c, S, acg)
    fwd = set()
    src = [n for n in view["excite"] if n in G]
    snk = [n for n in view["sense"] if n in G]
    reach = set()
    for n in src:
        reach |= nx.descendants(G, n) | {n}
    rrev = set()
    Gr = G.reverse()
    for n in snk:
        rrev |= nx.descendants(Gr, n) | {n}
    fwd = reach & rrev
    return fwd, G

# ---------------------------------------------------------------- rule 1 (4) bias-dependent nets
def bias_dependent_nets(c, view, S, acg):
    """규칙 1 (4) 술어. 반환: {net: evidence}"""
    out = {}
    for b in sorted(S):
        # (0) b is a signal net in this view  -- by construction
        # (i) signal leaves b only through gates
        if any(t["s"] == b for t in c.devs):
            continue
        # additionally: a passive attached to b would carry signal out by rule (c)
        if any(b in p["t"] for p in c.pas):
            continue
        readers = [t for t in c.devs if t["g"] == b]
        if not readers:
            continue
        drivers = [t for t in c.devs if t["d"] == b]
        if not drivers:
            continue
        # (ii) every driving channel terminal is either a device that reads b as gate,
        #      or a device whose gate is off the signal path
        selfgate, biassrc = [], []
        okii = True
        for t in drivers:
            if t["g"] == b:
                selfgate.append(t)
            elif t["g"] not in S:
                biassrc.append(t)
            else:
                okii = False
        if not okii or not selfgate:
            continue
        # (iii) one of the self-gate devices lies on a chain reached by channel terminals only
        #       from a signal node of this view: walk source->(device with that drain)->source ...
        #       never crossing an ac-ground net, never revisiting b.
        ev = None
        for t in selfgate:
            seen = {b}
            node = t["s"]
            hops = []
            while node is not None and node not in seen and node not in acg:
                seen.add(node)
                if node in S and node != b:
                    # candidate departure node; must still be a signal net with b removed
                    S_wo = signal_nets(c, view["excite"], acg | {b})
                    if node in S_wo:
                        ev = {"self_gate_dev": t["name"], "chain": hops + [node]}
                    break
                nxt = [u for u in c.devs if u["d"] == node]
                if not nxt:
                    break
                hops.append(node)
                node = nxt[0]["s"]
            if ev:
                break
        if ev:
            out[b] = ev
    return out

# ---------------------------------------------------------------- rule 3 cells
def classify_cells(c, view, S, acg, fwd):
    cells = {}
    # antiparallel pass bundle candidates
    bypair = collections.defaultdict(list)
    for t in c.devs:
        if t["g"] in S:
            continue
        key = tuple(sorted([t["d"], t["s"]]))
        bypair[key].append(t)
    bundles = {}
    for key, ts in bypair.items():
        if len(ts) == 2 and ts[0]["d"] == ts[1]["s"] and ts[0]["s"] == ts[1]["d"] and ts[0]["d"] != ts[0]["s"]:
            bundles[key] = [t["name"] for t in ts]
        elif len(ts) >= 3:
            bundles[key] = None  # >=3 -> review_needed (DEC-76)
    for t in c.devs:
        n = t["name"]
        if t["g"] == t["d"]:
            cells[n] = {"cls": "diode(load)", "why": "gate==drain"}
            continue
        key = tuple(sorted([t["d"], t["s"]]))
        if t["g"] not in S and key in bundles:
            if bundles[key] is None:
                cells[n] = {"cls": "review_needed", "why": "같은 두 노드에 3소자 이상(DEC-76)"}
            else:
                cells[n] = {"cls": "pass", "why": f"역병렬 pass 묶음 {bundles[key]}"}
            continue
        if t["g"] in S:
            if t["d"] in acg:
                cells[n] = {"cls": "CD", "why": "drain 교류접지"}
            elif t["s"] in acg:
                cells[n] = {"cls": "CS", "why": "source 교류접지"}
            else:
                # dual-output ambiguity with forward restriction
                touch = []
                for u in c.devs:
                    if u["name"] == n:
                        continue
                    if u["g"] == u["d"]:
                        continue  # diode 는 이중 출력 판정 대상 아님
                    inp = None
                    if u["g"] == t["s"] and u["g"] in S:
                        inp, outt = "gate", (u["d"] if u["d"] not in acg else u["s"])
                    elif u["s"] == t["s"] and u["g"] not in S:
                        inp, outt = "source(CG)", u["d"]
                    if inp and outt in fwd:
                        touch.append(u["name"])
                if t["s"] in view["sense"]:
                    touch.append("<output port>")
                if touch:
                    cells[n] = {"cls": "review_needed", "why": f"CS·CD 이중 출력(상대 {touch})"}
                else:
                    cells[n] = {"cls": "CS", "why": "degeneration"}
        else:
            if t["s"] in S:
                cells[n] = {"cls": "CG", "why": "gate 신호밖 + source 신호넷"}
            elif t["d"] in S or t["s"] in S:
                cells[n] = {"cls": "off_path", "why": "gate 신호밖, source 비신호"}
            else:
                cells[n] = {"cls": "off_path", "why": "채널이 신호 넷에 없음"}
    # forward restriction for aggregation: cell output terminal net in fwd
    for t in c.devs:
        n = t["name"]
        cl = cells[n]["cls"]
        outnet = None
        if cl == "CS":
            outnet = t["d"]
        elif cl == "CD":
            outnet = t["s"]
        elif cl == "CG":
            outnet = t["d"]
        elif cl == "pass":
            outnet = None  # 2단자 묶음: 어느 한쪽이 fwd면 순방향으로 본다
        cells[n]["fwd"] = (outnet in fwd) if outnet else ((t["d"] in fwd) or (t["s"] in fwd))
    return cells, bundles

# ---------------------------------------------------------------- driving type
def driving_types(c, view, S, acg, fwd, cells):
    """입력 노드 구동 종류(용어집). 반환 {net: {'type':..,'value_dep':bool,'why':..}}"""
    sig_cell = {n: v for n, v in cells.items() if v["cls"] in ("CS", "CG", "CD", "pass")}
    dev = {t["name"]: t for t in c.devs}
    cur_in = collections.defaultdict(list)   # node <- signal cell drain
    volt_in = collections.defaultdict(list)  # node <- gate-driven cell's source, input port, prev-stage output
    res_in = collections.defaultdict(list)
    for n, v in sig_cell.items():
        t = dev[n]
        if v["cls"] in ("CS", "CG") and t["d"] in S:
            cur_in[t["d"]].append(n)
        if v["cls"] in ("CD",) and t["s"] in S:
            volt_in[t["s"]].append(n)
        if v["cls"] == "CS" and t["s"] in S and t["s"] not in acg:
            # gate로 신호를 받는 셀의 source 단자로 신호가 나오는 노드 (용어집: 전부 전압 구동)
            volt_in[t["s"]].append(n + "(CS source)")
    for p in c.pas:
        if p["kind"] == "resistor" and len(p["t"]) == 2:
            for a, b in ((p["t"][0], p["t"][1]), (p["t"][1], p["t"][0])):
                if a in S and b in S:
                    res_in[a].append((p["name"], b))
    for i in view["excite"]:
        volt_in[i].append("<input port>")

    out = {}
    for k in sorted(S):
        has_c, has_v, has_r = bool(cur_in[k]), bool(volt_in[k]), bool(res_in[k])
        val_dep = has_r
        if has_c:
            # priority: how does signal leave k?
            exits_gate = [t["name"] for t in c.devs if t["g"] == k]
            exits_chan = [t["name"] for t in c.devs if (t["s"] == k and t["d"] in S)]
            # pass bundles leaving k
            for n, v in cells.items():
                if v["cls"] == "pass":
                    t = dev[n]
                    if k in (t["d"], t["s"]):
                        exits_chan.append(n + "(pass)")
            if has_v:
                # 혼재 우선 규칙: 신호 셀 source(전압 진입) + drain 진입
                lateral = all(is_lateral_injection(c, cells, dev[x], S, acg, fwd) for x in cur_in[k])
                out[k] = {"type": "voltage", "value_dep": val_dep,
                          "why": f"혼재 우선(전압 진입 {volt_in[k]} + drain 진입 {cur_in[k]})",
                          "flag": None if lateral else "review_needed(혼재: drain 쪽이 측면 주입 아님)"}
                continue
            if exits_gate and not exits_chan:
                out[k] = {"type": "voltage", "value_dep": val_dep, "why": f"전류 진입 {cur_in[k]}, 나가는 곳 gate뿐 {exits_gate}"}
            elif exits_chan and not exits_gate:
                out[k] = {"type": "current", "value_dep": val_dep, "why": f"전류 진입 {cur_in[k]}, 나가는 곳 채널뿐"}
            elif exits_gate and exits_chan:
                # gate 쪽 셀의 출력 단자도 순방향이면 전압 구동, 아니면 tap
                gate_fwd = []
                for x in exits_gate:
                    t = dev[x]
                    cl = cells[x]["cls"]
                    o = t["d"] if cl in ("CS", "CG") else (t["s"] if cl == "CD" else None)
                    if o and o in fwd:
                        gate_fwd.append(x)
                if gate_fwd:
                    out[k] = {"type": "voltage", "value_dep": val_dep, "why": f"gate·채널 동시 배출, gate측 순방향 {gate_fwd}"}
                else:
                    out[k] = {"type": "current", "value_dep": val_dep, "why": "gate·채널 동시 배출, gate측 순방향 아님 -> tap(규칙 9(a))",
                              "tap_cells": exits_gate}
            else:
                out[k] = {"type": "current", "value_dep": val_dep, "why": f"전류 진입 {cur_in[k]}, 배출 없음(종단)"}
        elif has_v:
            out[k] = {"type": "voltage", "value_dep": val_dep, "why": f"{volt_in[k]}"}
        elif has_r:
            out[k] = {"type": "inherit", "value_dep": True, "why": f"저항 진입만 {res_in[k]}"}
        else:
            out[k] = {"type": "undefined", "value_dep": False, "why": "신호 진입 단자 없음"}
    # 상속 전파
    for _ in range(len(S) + 2):
        moved = False
        for k, v in out.items():
            if v["type"] == "inherit":
                others = [out[b]["type"] for (_nm, b) in res_in[k] if b in out]
                cand = [x for x in others if x in ("voltage", "current")]
                if cand:
                    v["type"] = cand[0]; v["why"] += f" -> 상속 {cand[0]}"; moved = True
        if not moved:
            break
    for k, v in out.items():
        if v["type"] == "inherit":
            v["type"] = "review_needed"; v["why"] += " -> 순환/미정"
    return out, cur_in, volt_in, res_in


def is_lateral_injection(c, cells, t, S, acg, fwd):
    """K8 측면 주입 판정(간이): DC 역할 바이어스 전류원 + AC 역할 gate 신호수신 CS +
       drain 노드에 신호 CD 셀 source가 붙음 + gate 넷이 그 CD 입력넷에서 CD 엣지로 미도달."""
    if cells.get(t["name"], {}).get("cls") != "CS":
        return False
    k = t["d"]
    cds = [u for u in c.devs if cells.get(u["name"], {}).get("cls") == "CD" and u["s"] == k]
    if not cds:
        return False
    return True

# ---------------------------------------------------------------- rule 5 stages / blocks
def stages(c, view, S, acg, fwd, cells, drv, dc_roles):
    dev = {t["name"]: t for t in c.devs}
    starters, cascodes, buffers, notes = [], [], [], []
    for n, v in cells.items():
        t = dev[n]
        if not v.get("fwd"):
            continue
        cl = v["cls"]
        if cl == "CS":
            innode = t["g"]
            dt = drv.get(innode, {}).get("type")
            if dc_roles.get(n) == "bias_current_source":
                notes.append(f"{n}: DC 역할 바이어스 전류원 -> stage 시작 안 함(규칙 5 예외/K8)")
            elif dt == "voltage":
                starters.append((n, "CS", innode))
            elif dt == "current":
                notes.append(f"{n}: CS인데 입력노드 {innode} 전류 구동 -> 규칙 9(a) 기록만")
            else:
                notes.append(f"{n}: CS 입력노드 {innode} 구동종류 {dt}")
        elif cl == "CG":
            innode = t["s"]
            dt = drv.get(innode, {}).get("type")
            if dt == "voltage":
                starters.append((n, "CG(전압구동)", innode))
            elif dt == "current":
                cascodes.append(n)
            else:
                notes.append(f"{n}: CG 입력노드 {innode} 구동종류 {dt}")
        elif cl == "CD":
            buffers.append(n)
    return {"starters": starters, "cascodes": cascodes, "buffers": buffers, "notes": notes}

# ---------------------------------------------------------------- DC roles (simplified)
def dc_roles(c):
    """DC 역할(간이): diode 기준 / 바이어스 전류원 / 신호 소자.
    - gate==drain -> diode 기준
    - gate 넷이 diode 소자의 drain(미러 게이트)이거나 gate-only 미구동 넷(고정 바이어스) -> 바이어스 전류원
    - 그 외 -> 신호 소자"""
    diode_nets = {t["d"] for t in c.devs if t["g"] == t["d"]}
    chan = c.channel_nets()
    pasn = set()
    for p in c.pas:
        pasn |= set(p["t"])
    idn = set()
    for p in c.ideal:
        idn |= set(p["t"])
    portn = set(c.ports)
    roles = {}
    for t in c.devs:
        if t["g"] == t["d"]:
            roles[t["name"]] = "diode_ref"
        elif t["g"] in diode_nets:
            roles[t["name"]] = "bias_current_source"
        elif t["g"] not in chan and t["g"] not in pasn and t["g"] not in idn and t["g"] not in portn:
            roles[t["name"]] = "bias_current_source"
        else:
            roles[t["name"]] = "signal"
    return roles

# ---------------------------------------------------------------- DEC-71 branches / columns
def branches_columns(c):
    G = dc_graph(c, prune_leaf_resistors=True)
    rails = set(c.supply_nets or []) & set(G.nodes())
    # branch nodes: DC edge degree >= 3 (multigraph degree)
    deg = {n: G.degree(n) for n in G.nodes()}
    branch_nodes = {n for n in G.nodes() if deg[n] >= 3} | rails
    # branches: maximal series chains between rails/branch-nodes
    branches = []
    visited_edges = set()
    for u, v, k in G.edges(keys=True):
        if (u, v, k) in visited_edges or (v, u, k) in visited_edges:
            continue
        # walk both directions through degree-2 non-terminal nodes
        chain = [(u, v, k)]
        visited_edges.add((u, v, k))
        # extend from v
        ends = []
        for start, other in ((v, u), (u, v)):
            cur, prev = start, other
            while cur not in branch_nodes:
                nxt = [(a, b, kk) for a, b, kk in G.edges(cur, keys=True)
                       if not ((a, b, kk) in visited_edges or (b, a, kk) in visited_edges)]
                if len(nxt) != 1:
                    break
                a, b, kk = nxt[0]
                visited_edges.add((a, b, kk))
                chain.append((a, b, kk))
                cur = b if a == cur else a
            ends.append(cur)
        names = [G.edges[e]["name"] for e in chain]
        branches.append({"ends": sorted(ends), "elements": sorted(names)})
    # columns: simple paths between distinct rail nets, node-simple
    Gs = nx.Graph()
    for u, v, k in G.edges(keys=True):
        Gs.add_edge(u, v)
    cols = []
    railpairs = list(itertools.combinations(sorted(rails), 2))
    for a, b in railpairs:
        if a in Gs and b in Gs:
            try:
                for p in nx.all_simple_paths(Gs, a, b):
                    cols.append((a, b, tuple(p)))
                    if len(cols) > 20000:
                        break
            except nx.NetworkXNoPath:
                pass
    return {"n_branches": len(branches), "branches": branches,
            "branch_nodes_nonrail": sorted(n for n in branch_nodes if n not in rails),
            "n_columns": len(cols),
            "columns_by_pair": collections.Counter((a, b) for a, b, _ in cols),
            "rails_in_dc_graph": sorted(rails),
            "dc_nodes": sorted(G.nodes())}

# ---------------------------------------------------------------- DEC-64 G_vgs cycles
def gvgs_cycles(c):
    """G_vgs: MOS gate-source 무향 엣지 + 레일 병합 고정 노드. 기본 사이클 분류."""
    rails = set(c.supply_nets or [])
    def rn(n):
        return "<RAIL>" if n in rails else n
    G = nx.MultiGraph()
    for t in c.devs:
        G.add_edge(rn(t["g"]), rn(t["s"]), key=t["name"], name=t["name"])
    # basic cycles via spanning forest
    simpleG = nx.Graph()
    tree_edges = set()
    cycles = []
    for u, v, k in G.edges(keys=True):
        if u == v:
            cycles.append(("self", [k]))
            continue
        if simpleG.has_edge(u, v):
            # parallel edge -> v0 equal_vgs
            cycles.append(("v0", [simpleG.edges[u, v]["name"], k]))
            continue
        if u in simpleG and v in simpleG and nx.has_path(simpleG, u, v):
            path = nx.shortest_path(simpleG, u, v)
            mem = [k] + [simpleG.edges[path[i], path[i + 1]]["name"] for i in range(len(path) - 1)]
            cycles.append(("cyc", mem))
        else:
            simpleG.add_edge(u, v, name=k)
            tree_edges.add(k)
    inports = {n for n, v in c.ports.items() if v.get("direction") == "input"}
    dev = {t["name"]: t for t in c.devs}
    out = {"v0": [], "v1": [], "v2": [], "self": []}
    for kind, mem in cycles:
        if kind == "self":
            out["self"].append(mem); continue
        if kind == "v0":
            out["v0"].append(mem); continue
        nodes = set()
        for m in mem:
            nodes |= {dev[m]["g"], dev[m]["s"]}
        if len(nodes & inports) >= 2:
            out["v1"].append(sorted(mem))
        else:
            out["v2"].append(sorted(mem))
    # VDS-1: cycles in G_vgs+VDS graph containing exactly one drain-source edge -- approximate:
    return out

# ---------------------------------------------------------------- rule 2 loops
def loop_analysis(c, view, S, acg, fwd, cells, drv, cur_in, maxcycles=200000):
    dev = {t["name"]: t for t in c.devs}
    removed = set(acg) | set(view["excite"])
    nodes = [n for n in S if n not in removed]
    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    edge_kind = {}
    def add(u, v, name, kind):
        if u in G and v in G and u != v:
            if G.has_edge(u, v):
                G.edges[u, v]["names"].append(name)
            else:
                G.add_edge(u, v, names=[name], kinds=set())
            G.edges[u, v]["kinds"].add(kind)
    passnames = {n for n, v in cells.items() if v["cls"] == "pass"}
    done_bundle = set()
    for t in c.devs:
        n = t["name"]
        cl = cells[n]["cls"]
        if cl == "pass":
            key = tuple(sorted([t["d"], t["s"]]))
            if key in done_bundle:
                continue
            done_bundle.add(key)
            add(t["d"], t["s"], n + "(passbundle)", "active")
            add(t["s"], t["d"], n + "(passbundle)", "active")
            continue
        if t["g"] in S and t["g"] not in removed:
            add(t["g"], t["d"], n, "active")
            add(t["g"], t["s"], n, "active")
        # source->drain only if the source node has current entry (signal cell drain enters)
        if t["s"] in S and cur_in.get(t["s"]):
            add(t["s"], t["d"], n, "active")
    for p in c.pas:
        if len(p["t"]) == 2:
            add(p["t"][0], p["t"][1], p["name"], "passive")
            add(p["t"][1], p["t"][0], p["name"], "passive")
    cycles = []
    try:
        for i, cyc in enumerate(nx.simple_cycles(G)):
            cycles.append(cyc)
            if len(cycles) > maxcycles:
                break
    except Exception as e:
        return {"error": str(e)}
    # drop 2-node round trips over a single 2-terminal passive
    def is_passive_roundtrip(cyc):
        if len(cyc) != 2:
            return False
        a, b = cyc
        k1 = G.edges[a, b]["kinds"]; k2 = G.edges[b, a]["kinds"]
        n1 = set(G.edges[a, b]["names"]); n2 = set(G.edges[b, a]["names"])
        return k1 == {"passive"} and k2 == {"passive"} and bool(n1 & n2)
    def is_bundle_roundtrip(cyc):
        if len(cyc) != 2:
            return False
        a, b = cyc
        n1 = set(G.edges[a, b]["names"]); n2 = set(G.edges[b, a]["names"])
        return bool(n1 & n2) and any("passbundle" in x for x in n1)
    kept = [cy for cy in cycles if not is_passive_roundtrip(cy) and not is_bundle_roundtrip(cy)]
    dropped = len(cycles) - len(kept)

    # BFS distance (rule 4) for return-path computation
    dist = bfs_cost(c, view, S, acg, cells, drv)

    cls = collections.Counter()
    detail = []
    for cy in kept:
        info = classify_loop(c, G, cy, fwd, cells, dist, dev)
        cls[info["class"]] += 1
        detail.append(info)
    return {"n_basic_cycles_raw": len(cycles), "n_dropped_roundtrip": dropped,
            "n_cycles": len(kept), "classes": dict(cls), "detail": detail,
            "n_graph_nodes": G.number_of_nodes(), "n_graph_edges": G.number_of_edges()}


def bfs_cost(c, view, S, acg, cells, drv):
    """규칙 4: gate->drain 1, source->drain 0, gate->source 0,
       gate 넷이 diode 단자면 gate->drain 0, source가 전압구동인 CG의 source->drain 1.
       수동소자 엣지 비용은 계획 미확정 -> 0으로 둔다(민감도는 별도 보고)."""
    dev = {t["name"]: t for t in c.devs}
    diode_nets = {t["d"] for t in c.devs if t["g"] == t["d"]}
    G = nx.DiGraph()
    G.add_nodes_from(S)
    def add(u, v, w):
        if u in G and v in G:
            if not G.has_edge(u, v) or G.edges[u, v]["w"] > w:
                G.add_edge(u, v, w=w)
    for t in c.devs:
        if t["g"] in S:
            add(t["g"], t["d"], 0 if t["g"] in diode_nets else 1)
            add(t["g"], t["s"], 0)
        if t["s"] in S and t["d"] in S:
            w = 1 if (cells.get(t["name"], {}).get("cls") == "CG" and drv.get(t["s"], {}).get("type") == "voltage") else 0
            add(t["s"], t["d"], w)
    for p in c.pas:
        if len(p["t"]) == 2:
            add(p["t"][0], p["t"][1], 0)
            add(p["t"][1], p["t"][0], 0)
    src = [n for n in view["excite"] if n in G]
    dist = {}
    for s in src:
        d = nx.single_source_dijkstra_path_length(G, s, weight="w")
        for k, v in d.items():
            dist[k] = min(dist.get(k, 1e9), v)
    return dist


def classify_loop(c, G, cy, fwd, cells, dist, dev):
    L = len(cy)
    edges = [(cy[i], cy[(i + 1) % L]) for i in range(L)]
    kinds = [G.edges[e]["kinds"] for e in edges]
    names = [G.edges[e]["names"] for e in edges]
    info = {"nodes": cy, "edges": [list(n) for n in names]}
    # (1.5) bias SCC: touches no forward-path node
    if not (set(cy) & set(fwd)):
        info["class"] = "(1.5)bias_SCC"
        return info
    # (2) Miller: maximal passive-only run containing a capacitor, joining two forward-path nodes
    capnames = {p["name"] for p in c.pas if p["kind"] == "capacitor"}
    is_pas = ["passive" in k and "active" not in k for k in kinds]
    miller = False
    for i in range(L):
        if not is_pas[i]:
            continue
        # maximal run
        j = i
        run = [i]
        while is_pas[(j + 1) % L] and (j + 1) % L != i:
            j = (j + 1) % L
            run.append(j)
        if i > 0 and is_pas[i - 1]:
            continue  # not the start of a maximal run
        segnames = set()
        for r in run:
            segnames |= set(names[r])
        if segnames & capnames:
            a = edges[run[0]][0]
            b = edges[run[-1]][1]
            if a in fwd and b in fwd:
                miller = True
                info["miller_seg"] = sorted(segnames)
    # (3-b) return path: edges where BFS distance does not increase (ties included)
    ret = []
    for i, (u, v) in enumerate(edges):
        du, dv = dist.get(u), dist.get(v)
        if du is None or dv is None:
            continue
        if dv <= du:
            ret.append(i)
    ret_kinds = set()
    ret_names = set()
    for i in ret:
        ret_kinds |= kinds[i]
        ret_names |= set(names[i])
    has_active_ret = "active" in ret_kinds
    has_passive_ret = "passive" in ret_kinds
    # (3-a): active cell not on any transfer view forward path
    active_devs = set()
    for nm in itertools.chain(*names):
        base = nm.split("(")[0]
        if base in dev:
            active_devs.add(base)
    off_fwd = [n for n in active_devs if not cells.get(n, {}).get("fwd")]
    if miller:
        info["class"] = "(2)Miller"
        info["also_3b"] = bool(has_active_ret and has_passive_ret)
        return info
    if off_fwd:
        info["class"] = "(3-a)"
        info["off_fwd_cells"] = sorted(off_fwd)
        return info
    if has_active_ret and not has_passive_ret and len(active_devs) == 2:
        info["class"] = "기록만(수동소자 없는 2능동셀 루프)"
        return info
    if has_active_ret and has_passive_ret:
        info["class"] = "(3-b)"
        info["return_edges"] = sorted(ret_names)
        return info
    if ret and not has_active_ret:
        info["class"] = "(4)"
        info["why"] = "복귀 경로 수동소자만(배타 (가))"
        return info
    info["class"] = "(4)"
    info["why"] = "나머지"
    return info

# ---------------------------------------------------------------- rule 9
def rule9(c, view, S, acg, fwd, cells, drv, dc_r):
    dev = {t["name"]: t for t in c.devs}
    a, b, cc = [], [], []
    diode_nets = {t["d"] for t in c.devs if t["g"] == t["d"]}
    for n, v in cells.items():
        t = dev[n]
        if v["cls"] == "CS" and drv.get(t["g"], {}).get("type") == "current":
            a.append({"dev": n, "gate": t["g"], "why": drv[t["g"]]["why"]})
        if v["cls"] == "CG":
            pr = c.ports.get(list(view["excite"])[0], {}) if view["excite"] else {}
            # (b) 입력 포트가 전류 입력인 CG -- ports 선언에 전류 입력 표기가 없으면 전압
            if t["s"] in view["excite"] and str(pr.get("role", "")).find("current") >= 0:
                b.append({"dev": n})
    # (c) CS로 시작하지만 출력노드 임피던스 등급이 낮은 블록
    for n, v in cells.items():
        t = dev[n]
        if v["cls"] != "CS" or not v.get("fwd"):
            continue
        k = t["d"]
        if k not in fwd:
            continue
        low = impedance_low(c, k, acg, cells)
        if low:
            # diode 갈래: k가 diode drain이고 그 노드를 gate로 읽는 소자의 출력이 순방향이면 미러 입력
            if k in diode_nets:
                readers = [u for u in c.devs if u["g"] == k and u["g"] != u["d"]]
                mirror_out = []
                for u in readers:
                    cl = cells.get(u["name"], {}).get("cls")
                    o = u["d"] if cl in ("CS", "CG") else (u["s"] if cl == "CD" else u["d"])
                    if o in fwd:
                        mirror_out.append(u["name"])
                if mirror_out:
                    continue  # 미러 입력 -> (c) 발동 안 함
            cc.append({"dev": n, "outnode": k, "why": low})
    return {"a": a, "b": b, "c": cc}


def impedance_low(c, k, acg, cells):
    """낮음 = gm 차수 컨덕턴스 단자(그 뷰 교류접지 gate의 source 단자, diode 소자의 drain+gate)가 붙음"""
    why = []
    for t in c.devs:
        if t["s"] == k and t["g"] in acg:
            why.append(f"{t['name']}.source(gate 교류접지)")
        if t["g"] == t["d"] == k:
            why.append(f"{t['name']}.diode")
    return why
