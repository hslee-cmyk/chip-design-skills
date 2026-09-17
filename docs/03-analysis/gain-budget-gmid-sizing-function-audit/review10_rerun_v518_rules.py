# -*- coding: utf-8 -*-
"""v5.18 규칙 재구현 (검증자 독립 구현).

전 라운드 스크립트(review9_measure*.py)를 재사용하지 않고 v5.18 본문에서 규칙을 다시 읽어 구현한다.
구현 대상:
  GB0-(iii) 숨은 레일 후보 거부           (DEC-60)
  셀 분류 도달성 = 최소 고정점            (N3.2-3)
  기본 폐경로 = 단순 사이클 - 2단자 수동소자 왕복 (N3.2-2)
  루프 분류 (0)(1)(1.5)(2)(3-a/3-b)(4)    (N3.2-2)
  가지·기둥(노드-단순) + 바이어스 기둥 귀속 (DEC-71 (1)(2))
결과는 케이스마다 out jsonl/txt 에 append 한다(WP-11, 중간에 죽어도 건지게).
"""
import json, os, sys, itertools
from collections import defaultdict, deque

sys.setrecursionlimit(100000)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

LIB = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library"
OUT = os.path.dirname(os.path.abspath(__file__))
JSONL = os.path.join(OUT, "rerun_v518_results.jsonl")
TXT = os.path.join(OUT, "rerun_v518_results.txt")

NAMES = ["current_reuse_telescopic_ota", "folded_cascode", "nmcnr_amplifier",
         "two_stage_ota", "two_stage_ota_sf", "pushpull_follower_buffer",
         "sf_pushpull_output_opamp", "ngcc_3stage_ff"]
RAIL_NAMESET = {"vdd", "gnd", "vss", "vcc", "vee"}
SPEC_CIRCUITS = {"two_stage_ota", "current_reuse_telescopic_ota",
                 "folded_cascode", "nmcnr_amplifier"}
PASSIVE_STAGE_COST = [0]   # 규칙 4 "수동소자 엣지 비용은 6a design이 정한다" -> 미정. 감도 변수.

# J1 기본안을 '손 목록'으로 넣었을 때의 대조용(규칙이 아니라 대조 입력임을 보고서에 명시)
J1_HANDLIST = {
    "current_reuse_telescopic_ota": ["Vbias2", "Vbias3"],
    "sf_pushpull_output_opamp": None,   # 실측으로 결정 (자기바이어스 캐스코드 gate 넷)
}


def load(n):
    with open(os.path.join(LIB, n + ".topology.json"), encoding="utf-8") as f:
        return json.load(f)


def devs(d):
    return [x for x in (d.get("netlist") or []) if isinstance(x, dict) and x.get("name")]


def pas(d):
    return [x for x in (d.get("passive_elements") or []) if isinstance(x, dict)]


def isrc(d):
    return [x for x in (d.get("ideal_sources") or []) if isinstance(x, dict)]


def isrc_t(q):
    t = q.get("terminals")
    if isinstance(t, list) and len(t) >= 2:
        return t[0], t[1]
    for a, b in (("from", "to"), ("plus", "minus"), ("net_from", "net_to")):
        if q.get(a) and q.get(b):
            return q[a], q[b]
    return None


def ports_of(d):
    p = d.get("ports")
    if not isinstance(p, dict):
        return {}
    return {k: v for k, v in p.items() if not k.startswith("_") and isinstance(v, dict)}


def mos_nets(d):
    s = set()
    for m in devs(d):
        for k in ("source", "drain", "gate", "bulk"):
            if m.get(k):
                s.add(m[k])
    return s


def mos_nets_nobulk(d):
    s = set()
    for m in devs(d):
        for k in ("source", "drain", "gate"):
            if m.get(k):
                s.add(m[k])
    return s


def pas_isrc_nets(d):
    s = set()
    for p in pas(d):
        s.update(p.get("terminals") or [])
    for q in isrc(d):
        t = isrc_t(q)
        if t:
            s.update(t)
    return s


def all_nets(d):
    return mos_nets(d) | pas_isrc_nets(d)


def rails_of(d):
    sn = d.get("supply_nets")
    if sn:
        return set(sn), "declared"
    return {n for n in all_nets(d) if n.lower() in RAIL_NAMESET}, "nameset"


# ------------------------------------------------------------------ GB0 (i)(ii)(iii)
def gb0_rail_gate(d, name):
    """DEC-60 v5.18: (i) 선언 / (ii) 이름집합 / (iii) 숨은 레일 후보."""
    declared = bool(d.get("supply_nets"))
    rails, src = rails_of(d)
    supplies_v = None  # library topology 에는 없음(사이징 spec 소관). 실행 spec 은 스칼라 vdd 뿐.
    hidden_nobulk = sorted(pas_isrc_nets(d) - mos_nets_nobulk(d))
    hidden_withbulk = sorted(pas_isrc_nets(d) - mos_nets(d))
    res = {
        "supply_nets_declared": declared,
        "rails": sorted(rails), "rail_source": src, "n_rails": len(rails),
        "hidden_rail_candidates(nobulk)": hidden_nobulk,
        "hidden_rail_candidates(withbulk)": hidden_withbulk,
    }
    # (i)/(ii)
    reject_i_ii = None
    if declared:
        reject_i_ii = False  # 선언이 있으면 (i)은 supplies_v 부호 판정인데 library 에 없음 -> 판정 불가
        res["note_i"] = "supplies_v 미선언이라 (i) 부호 판정 입력 없음"
    else:
        reject_i_ii = (len(rails) != 2)
        res["note_ii"] = "실행 spec 레일 전압 부호 입력 없음(스칼라 vdd 뿐)" if name not in SPEC_CIRCUITS \
            else "실행 spec 스칼라 vdd(양수) -> 부호 거부 없음"
    # (iii)
    reject_iii = (not declared) and bool(hidden_nobulk)
    res["reject_by_i_ii"] = bool(reject_i_ii)
    res["reject_by_iii"] = bool(reject_iii)
    res["verdict"] = "REJECT" if (reject_i_ii or reject_iii) else "PASS"
    return res


# ------------------------------------------------------------------ 교류접지(N3.2-1)
def ac_ground(d, rails, portnets):
    driven = set()
    for m in devs(d):
        driven.add(m["source"]); driven.add(m["drain"])
    pn = pas_isrc_nets(d)
    g = set()
    for m in devs(d):
        gt = m["gate"]
        if gt in rails or gt in driven or gt in pn or gt in portnets:
            continue
        g.add(gt)
    return set(rails) | g


# ------------------------------------------------------------------ 도달성
def minimal_fixpoint_reach(d, acg, excite, cut_nets=frozenset(), b_restricted=False):
    """N3.2-3 v5.18 최소 고정점.
    (a) 신호 넷을 gate 로 받는 소자의 drain·source
    (b) 신호 넷을 source 로 받는 소자의 drain
        b_restricted=True 이면 history H2 문구('전류 구동 source->drain')대로
        source 넷이 '전류 구동'(신호 셀 drain 이 들어오는 노드)일 때만 적용
    (c) 신호 넷에 붙은 2단자 수동소자의 반대 단자
    교류접지·제거 넷(cut_nets)은 넣지 않는다."""
    blocked = set(acg) | set(cut_nets)
    S = {n for n in excite if n not in blocked}
    D = devs(d)
    P = [p for p in pas(d) if len(p.get("terminals") or []) >= 2]
    changed = True
    while changed:
        changed = False
        # (b)의 전류 구동 판정은 현재 S 기준(단조 연산자라 최소 고정점 존재)
        current_driven = set()
        if b_restricted:
            for m in D:
                if m["gate"] in S:            # 신호를 싣는 셀
                    current_driven.add(m["drain"])
        for m in D:
            g, s, dr = m["gate"], m["source"], m["drain"]
            if g in S:
                for x in (dr, s):
                    if x not in blocked and x not in S:
                        S.add(x); changed = True
            if s in S:
                ok = (not b_restricted) or (s in current_driven)
                if ok and dr not in blocked and dr not in S:
                    S.add(dr); changed = True
        for p in P:
            t = p["terminals"]
            for a, b in ((t[0], t[1]), (t[1], t[0])):
                if a in S and b not in blocked and b not in S:
                    S.add(b); changed = True
    return S


def superset_reach(d, acg, excite, cut_nets=frozenset()):
    """v5.17 옛 규정(초집합 방향 그래프 전방 폐포) -- 비교 기준."""
    blocked = set(acg) | set(cut_nets)
    adj = defaultdict(set)
    for m in devs(d):
        adj[m["gate"]].add(m["drain"]); adj[m["gate"]].add(m["source"])
        adj[m["source"]].add(m["drain"])
    for p in pas(d):
        t = p.get("terminals") or []
        if len(t) >= 2:
            adj[t[0]].add(t[1]); adj[t[1]].add(t[0])
    seen, st = set(), [n for n in excite if n not in blocked]
    while st:
        n = st.pop()
        if n in seen or n in blocked:
            continue
        seen.add(n)
        for x in adj.get(n, ()):
            if x not in seen:
                st.append(x)
    return seen


# ------------------------------------------------------------------ 셀 분류
def hop_dist(d, acg, excite, S, cut_nets=frozenset()):
    """방향 도달 순서(CG/pass 판별용) -- 최소 고정점 그래프 위 홉 거리."""
    blocked = set(acg) | set(cut_nets)
    adj = defaultdict(set)
    for m in devs(d):
        g, s, dr = m["gate"], m["source"], m["drain"]
        adj[g].add(dr); adj[g].add(s); adj[s].add(dr)
    for p in pas(d):
        t = p.get("terminals") or []
        if len(t) >= 2:
            adj[t[0]].add(t[1]); adj[t[1]].add(t[0])
    dist, q = {}, deque()
    for e in excite:
        if e in blocked:
            continue
        dist[e] = 0; q.append(e)
    while q:
        n = q.popleft()
        for x in adj.get(n, ()):
            if x in blocked or x in dist or x not in S:
                continue
            dist[x] = dist[n] + 1; q.append(x)
    return dist


def classify_cells(d, acg, excite, outports, S, cut_nets=frozenset()):
    dist = hop_dist(d, acg, excite, S, cut_nets)
    gates = {m["gate"] for m in devs(d)}
    cells, why = {}, {}
    for m in devs(d):
        g, s, dr = m["gate"], m["source"], m["drain"]
        gsig = g in S
        if gsig:
            if dr in acg:
                c = "CD"
            elif s in acg:
                c = "CS"
            else:
                touches = (s in gates and s in S) or (s in outports)
                c = "CS_CD_review" if touches else "CS(degen)"
        else:
            ssig, dsig = (s in S), (dr in S)
            if ssig and dsig:
                ds, dd = dist.get(s, 10**9), dist.get(dr, 10**9)
                c = "CG" if ds < dd else ("pass?" if ds == dd else "pass(rev)")
            elif ssig or dsig:
                c = "load/bias"
            else:
                c = "off_path"
        cells[m["name"]] = c
        why[m["name"]] = {"gate_sig": gsig, "s": s, "d": dr,
                          "ds": dist.get(s), "dd": dist.get(dr)}
    # 역병렬 pass 묶음
    pairs = defaultdict(list)
    for m in devs(d):
        if cells[m["name"]] in ("CG", "pass?", "pass(rev)"):
            pairs[tuple(sorted([m["source"], m["drain"]]))].append(m)
    bundles = []
    for k, ms in pairs.items():
        if len(ms) == 2 and ms[0]["source"] == ms[1]["drain"] and ms[0]["drain"] == ms[1]["source"]:
            bundles.append(sorted([ms[0]["name"], ms[1]["name"]]))
            for mm in ms:
                cells[mm["name"]] = "pass(bundle)"
        elif len(ms) >= 3:
            for mm in ms:
                cells[mm["name"]] = "review(>=3 same pair)"
    return cells, why, bundles, dist


# ------------------------------------------------------------------ 구동 종류
def drive_types(d, acg, cells, S, inports):
    res, detail = {}, {}
    for n in sorted(S | set(inports)):
        if n in acg:
            continue
        kinds = []
        for m in devs(d):
            c = cells.get(m["name"], "")
            sig = c.startswith("CS") or c in ("CD", "CG") or c.startswith("pass")
            if not sig:
                continue
            if m["drain"] == n:
                kinds.append(("current", m["name"] + ".d"))
            if m["source"] == n and c == "CD":
                kinds.append(("voltage", m["name"] + ".s"))
        if n in inports:
            kinds.append(("voltage", "input_port"))
        for p in pas(d):
            t = p.get("terminals") or []
            if n in t and (p.get("kind") or "").lower().startswith("res"):
                kinds.append(("value_dep", p.get("name")))
        ks = {k for k, _ in kinds}
        if not ks:
            v = "none"
        elif "voltage" in ks and "current" in ks:
            v = "voltage(혼재우선)"
        elif "voltage" in ks:
            v = "voltage" + ("+값의존" if "value_dep" in ks else "")
        elif "current" in ks:
            # v5.18 혼합 규칙: 전류 진입 + 저항 진입 -> 전류 구동, '값 의존'은 부속 속성
            v = "current" + ("(+값의존 부속)" if "value_dep" in ks else "")
        else:
            v = "value_dep_only"
        res[n] = v
        detail[n] = sorted(kinds)
    return res, detail


# ------------------------------------------------------------------ 루프 그래프·폐경로
def loop_graph(d, acg, excite, drives):
    removed = set(acg) | set(excite)
    adj = defaultdict(set)
    elab = defaultdict(set)
    for m in devs(d):
        g, s, dr = m["gate"], m["source"], m["drain"]
        for (a, b) in ((g, dr), (g, s)):
            if a in removed or b in removed or a == b:
                continue
            adj[a].add(b); elab[(a, b)].add(("mos", m["name"]))
        dv = drives.get(s, "")
        if dv.startswith("current"):
            if s not in removed and dr not in removed and s != dr:
                adj[s].add(dr); elab[(s, dr)].add(("mos", m["name"]))
    for p in pas(d):
        t = p.get("terminals") or []
        if len(t) >= 2 and t[0] not in removed and t[1] not in removed and t[0] != t[1]:
            adj[t[0]].add(t[1]); adj[t[1]].add(t[0])
            elab[(t[0], t[1])].add(("pas", p.get("name")))
            elab[(t[1], t[0])].add(("pas", p.get("name")))
    return adj, elab


def simple_cycles(adj, cap=2000000):
    nodes = set(adj.keys())
    for v in adj.values():
        nodes |= v
    nodes = sorted(nodes)
    idx = {n: i for i, n in enumerate(nodes)}
    out, budget = [], [cap]

    def dfs(start, node, path, onp):
        if budget[0] <= 0:
            return
        for nxt in sorted(adj.get(node, ())):
            budget[0] -= 1
            if budget[0] <= 0:
                return
            if nxt == start and len(path) >= 2:
                out.append(list(path))
            elif nxt not in onp and idx.get(nxt, -1) > idx[start]:
                path.append(nxt); onp.add(nxt)
                dfs(start, nxt, path, onp)
                path.pop(); onp.discard(nxt)

    for s in nodes:
        dfs(s, s, [s], {s})
    return out, budget[0] <= 0, len(nodes)


def is_passive_roundtrip(cyc, elab):
    """v5.18: 2단자 수동소자 하나의 무향 엣지를 오가는 왕복은 폐경로가 아니다."""
    if len(cyc) != 2:
        return False, None
    a, b = cyc
    f = elab.get((a, b), set())
    r = elab.get((b, a), set())
    fp = {n for (k, n) in f if k == "pas"}
    rp = {n for (k, n) in r if k == "pas"}
    fm = {n for (k, n) in f if k == "mos"}
    rm = {n for (k, n) in r if k == "mos"}
    if fm or rm:
        return False, None
    common = fp & rp
    if common and len(fp) == 1 and len(rp) == 1:
        return True, sorted(common)[0]
    return False, None


# ------------------------------------------------------------------ stage 번호(0-1 BFS, 규칙 4)
def stage_index(d, acg, excite, S, cells=None, drives=None):
    """규칙 4 + 규칙 3 셀 우선순위: 엣지를 셀 종류별로만 만든다.
    (셀 우선순위를 무시하고 g->s·s->d 를 무조건 넣으면 모든 노드가 비용 0이 되어 stage 가 의미를 잃는다.)
    CS: gate->drain 비용 1(gate 넷이 diode 연결이면 0) / CD: gate->source 0
    CG: source->drain (source 가 전압 구동이면 1, 아니면 0) / pass: source<->drain 0
    수동소자: 무향 0(6a design 미정 -- 기본값)."""
    diode_nets = {m["gate"] for m in devs(d) if m["gate"] == m["drain"]}
    edges = defaultdict(list)   # u -> [(v, cost)]
    cells = cells or {}
    drives = drives or {}
    for m in devs(d):
        g, s, dr = m["gate"], m["source"], m["drain"]
        c = cells.get(m["name"], "")
        if c.startswith("CS"):
            edges[g].append((dr, 0 if g in diode_nets else 1))
        elif c == "CD":
            edges[g].append((s, 0))
        elif c == "CG":
            edges[s].append((dr, 1 if str(drives.get(s, "")).startswith("voltage") else 0))
        elif c.startswith("pass"):
            edges[s].append((dr, 0)); edges[dr].append((s, 0))
    pc = PASSIVE_STAGE_COST[0]
    for p in pas(d):
        t = p.get("terminals") or []
        if len(t) >= 2:
            edges[t[0]].append((t[1], pc)); edges[t[1]].append((t[0], pc))
    INF = 10**9
    dist = {n: INF for n in S}
    dq = deque()
    for e in excite:
        if e in S:
            dist[e] = 0; dq.appendleft(e)
    while dq:
        u = dq.popleft()
        for (v, c) in edges.get(u, ()):
            if v not in S or v in acg:
                continue
            nd = dist[u] + c
            if nd < dist.get(v, INF):
                dist[v] = nd
                if c == 0:
                    dq.appendleft(v)
                else:
                    dq.append(v)
    return {k: v for k, v in dist.items() if v < INF}


def forward_sets(d, acg, excite, outports, S):
    """전달 뷰 순방향 경로 근사: 여기에서 도달(S) ∧ 출력 포트로 역도달."""
    fwd = defaultdict(set)
    for m in devs(d):
        fwd[m["gate"]].add(m["drain"]); fwd[m["gate"]].add(m["source"])
        fwd[m["source"]].add(m["drain"])
    for p in pas(d):
        t = p.get("terminals") or []
        if len(t) >= 2:
            fwd[t[0]].add(t[1]); fwd[t[1]].add(t[0])
    rev = defaultdict(set)
    for a, bs in fwd.items():
        for b in bs:
            rev[b].add(a)
    seen, st = set(), [o for o in outports]
    while st:
        n = st.pop()
        if n in seen or n in acg or n not in S:
            continue
        seen.add(n)
        st.extend(rev.get(n, ()))
    fwd_nodes = (S & seen) | {o for o in outports if o in S}
    fwd_dev = set()
    for m in devs(d):
        ins = [m["gate"], m["source"]]
        outs = [m["drain"], m["source"]]
        if any(i in S for i in ins) and any(o in fwd_nodes for o in outs):
            fwd_dev.add(m["name"])
    return fwd_nodes, fwd_dev


def classify_cycles(cycles, elab, d, fwd_dev, fwd_nodes, stage, gate_nets):
    capn = {p["name"] for p in pas(d) if (p.get("kind") or "").lower().startswith("cap")}
    resn = {p["name"] for p in pas(d) if (p.get("kind") or "").lower().startswith("res")}
    tally = defaultdict(int)
    detail = defaultdict(list)
    for cyc in cycles:
        labs = []
        for i in range(len(cyc)):
            a, b = cyc[i], cyc[(i + 1) % len(cyc)]
            labs.append((a, b, sorted(elab.get((a, b), {("?", "?")}))))
        flat = [x for (_a, _b, L) in labs for x in L]
        mos = {n for (k, n) in flat if k == "mos"}
        ps = {n for (k, n) in flat if k == "pas"}
        rec = {"nodes": cyc, "mos": sorted(mos), "pas": sorted(ps)}
        # (1.5) 바이어스 SCC : 전달 뷰 신호 경로 노드를 하나도 지나지 않음
        if not (set(cyc) & fwd_nodes):
            tally["c1_5_bias_scc"] += 1; detail["c1_5"].append(rec); continue
        # (2) Miller / 국소FB
        if (ps & capn) and mos and mos <= fwd_dev:
            tally["c2_miller"] += 1; detail["c2"].append(rec); continue
        if len(mos) == 1 and (ps & resn) and not (set(cyc) & fwd_nodes):
            tally["c2_localfb"] += 1; detail["c2"].append(rec); continue
        # (3-a)
        if mos - fwd_dev:
            tally["c3a"] += 1; detail["c3a"].append(rec); continue
        # (3-b) 복귀 엣지: stage 가 뒤 -> 앞 으로 돌아오는 엣지가 있는가
        back = [(a, b) for (a, b, _L) in labs
                if a in stage and b in stage and stage[a] > stage[b]]
        back_to_gate = [(a, b) for (a, b) in back if b in gate_nets]
        if back_to_gate:
            tally["c3b_strict"] += 1; detail["c3b_strict"].append(dict(rec, back=back_to_gate)); continue
        if back:
            tally["c3b_loose"] += 1; detail["c3b_loose"].append(dict(rec, back=back)); continue
        tally["c4"] += 1; detail["c4"].append(rec)
    return dict(tally), {k: v[:20] for k, v in detail.items()}


# ------------------------------------------------------------------ 가지·기둥(DEC-71)
def dc_edges(d, rails, portnets):
    E = []
    for m in devs(d):
        E.append((m["source"], m["drain"], "mos", m["name"]))
    for p in pas(d):
        if (p.get("kind") or "").lower().startswith("res"):
            t = p.get("terminals") or []
            if len(t) >= 2:
                E.append((t[0], t[1], "res", p["name"]))
    for q in isrc(d):
        t = isrc_t(q)
        if t:
            E.append((t[0], t[1], "isrc", q.get("name")))
    keep = list(range(len(E)))
    ch = True
    while ch:
        ch = False
        deg = defaultdict(list)
        for i in keep:
            deg[E[i][0]].append(i); deg[E[i][1]].append(i)
        for node, ids in list(deg.items()):
            if node in rails or node in portnets:
                continue
            if len(ids) == 1 and E[ids[0]][2] == "res":
                keep.remove(ids[0]); ch = True; break
    return [E[i] for i in keep]


def branches_columns(d, rails, portnets):
    E = dc_edges(d, rails, portnets)
    deg = defaultdict(int); adj = defaultdict(list)
    for i, (u, v, k, n) in enumerate(E):
        deg[u] += 1; deg[v] += 1
        adj[u].append((v, i)); adj[v].append((u, i))
    bn = sorted([n for n, c in deg.items() if c >= 3])
    term = set(bn) | set(rails)
    used, branches = set(), []
    for t in sorted(term):
        for (nb, ei) in adj[t]:
            if ei in used:
                continue
            path = [ei]; used.add(ei); cur = nb
            while cur not in term:
                nxt = [(x, j) for (x, j) in adj[cur] if j not in used]
                if len(nxt) != 1:
                    break
                x, j = nxt[0]; used.add(j); path.append(j); cur = x
            branches.append({"ends": tuple(sorted([t, cur])),
                             "elems": [E[i][3] for i in path]})
    badj = defaultdict(list)
    for bi, b in enumerate(branches):
        a, c = b["ends"]
        badj[a].append((c, bi))
        if a != c:
            badj[c].append((a, bi))
    cols = []
    for r1, r2 in itertools.combinations(sorted(rails), 2):
        st = [(r1, [], {r1})]
        while st:
            node, pb, vis = st.pop()
            if node == r2 and pb:
                cols.append(list(pb)); continue
            for (nb, bi) in badj[node]:
                if bi in pb or nb in vis:
                    continue
                st.append((nb, pb + [bi], vis | {nb}))
    cov = set()
    for c in cols:
        cov.update(c)
    devcol = defaultdict(set)
    for ci, c in enumerate(cols):
        for bi in c:
            for e in branches[bi]["elems"]:
                devcol[e].add(ci)
    return {
        "branches": branches, "columns": cols, "branch_adj_nonrail": [x for x in bn if x not in rails],
        "n_branches": len(branches),
        "n_branch_nodes_nonrail": len([x for x in bn if x not in rails]),
        "n_columns_node_simple": len(cols),
        "uncovered_branches": [branches[bi]["elems"] for bi in range(len(branches)) if bi not in cov],
        "mos_not_in_any_column": [m["name"] for m in devs(d) if not devcol.get(m["name"])],
        "devcol": {k: sorted(v) for k, v in devcol.items()},
    }


def bias_column_attribution(bc, cells):
    """DEC-71 (2) v5.18: 어느 블록에도 속하지 않는 소자만으로 된 가지·기둥 = 바이어스 기둥,
    블록 소자와 섞이면 그 블록 국소 문제 범위 + 공유 소자."""
    block_kinds = ("CS", "CS(degen)", "CG", "CD", "pass(bundle)", "pass?", "pass(rev)",
                   "load/bias", "CS_CD_review")
    def is_block(dev):
        c = cells.get(dev)
        return (c is not None) and (c in block_kinds)
    off = sorted([k for k, v in cells.items() if v == "off_path"])
    pure, mixed, unattributed = [], [], []
    for bi, b in enumerate(bc["branches"]):
        mos = [e for e in b["elems"] if e in cells]
        if not mos:
            continue
        if all(not is_block(e) for e in mos):
            pure.append({"branch": bi, "elems": b["elems"]})
        elif any(not is_block(e) for e in mos):
            mixed.append({"branch": bi, "elems": b["elems"],
                          "off": [e for e in mos if not is_block(e)]})
    attributed = set()
    for r in pure:
        attributed.update([e for e in r["elems"] if e in cells])
    for r in mixed:
        attributed.update(r["off"])
    unattributed = [o for o in off if o not in attributed]
    return {"off_path_devices": off, "n_off_path": len(off),
            "pure_bias_branches": pure, "n_pure_bias_branches": len(pure),
            "mixed_branches": mixed, "n_mixed_branches": len(mixed),
            "off_path_unattributed": unattributed}


# ------------------------------------------------------------------ 회로 하나
def run(name):
    d = load(name)
    ports = ports_of(d)
    portnets = set(ports.keys())
    rails, rsrc = rails_of(d)
    inp = [k for k, v in ports.items()
           if "input" in (v.get("role") or "") or v.get("direction") == "input"]
    outp = [k for k, v in ports.items()
            if "output" in (v.get("role") or "") or v.get("direction") == "output"]
    rec = {"circuit": name, "n_devices": len(devs(d)), "n_passive": len(pas(d)),
           "n_isrc": len(isrc(d)), "in_ports": inp, "out_ports": outp,
           "sizing_spec": name in SPEC_CIRCUITS,
           "gb0": gb0_rail_gate(d, name)}
    acg = ac_ground(d, rails, portnets)
    rec["ac_ground"] = sorted(acg)
    bc = branches_columns(d, rails, portnets)
    rec["columns"] = {k: bc[k] for k in ("n_branches", "n_branch_nodes_nonrail",
                                         "n_columns_node_simple", "uncovered_branches",
                                         "mos_not_in_any_column")}
    if not (inp and outp):
        rec["view"] = "불가(U-08: ports/출력포트 미선언)"
        return rec, bc, None
    rec["view"] = "가능"
    # 도달성 3종
    S_min = minimal_fixpoint_reach(d, acg, inp)
    S_sup = superset_reach(d, acg, inp)
    S_minb = minimal_fixpoint_reach(d, acg, inp, b_restricted=True)
    rec["reach"] = {"min_fixpoint_n": len(S_min), "superset_n": len(S_sup),
                    "identical_min_vs_superset": sorted(S_min) == sorted(S_sup),
                    "min_minus_superset": sorted(S_min - S_sup),
                    "superset_minus_min": sorted(S_sup - S_min),
                    "history_H2_reading(b=current-driven only)_n": len(S_minb),
                    "min_minus_H2reading": sorted(S_min - S_minb)}
    # history H2 문구대로 (b)를 '전류 구동 source->drain'으로 읽었을 때의 셀 분류(대조)
    cH2, _wH2, bH2, _dH2 = classify_cells(d, acg, inp, set(outp), S_minb)
    tH2 = defaultdict(int)
    for v in cH2.values():
        tH2[v] += 1
    rec["cells_H2reading"] = dict(sorted(tH2.items()))
    rec["CG_devices_H2reading"] = sorted([k for k, v in cH2.items() if v == "CG"])
    cells, why, bundles, dist = classify_cells(d, acg, inp, set(outp), S_min)
    tally = defaultdict(int)
    for v in cells.values():
        tally[v] += 1
    rec["cells_minfp"] = dict(sorted(tally.items()))
    rec["cells_detail"] = cells
    rec["pass_bundles"] = bundles
    rec["CG_devices"] = sorted([k for k, v in cells.items() if v == "CG"])
    # J1 대조: 손 목록 예외를 적용했을 때
    hand = J1_HANDLIST.get(name)
    if hand is None and name == "sf_pushpull_output_opamp":
        # 자기바이어스 캐스코드 gate 넷 후보 = diode 연결이 아닌데 R1a/R1b/R1c 가 구동하는 넷
        hand = sorted({m["gate"] for m in devs(d)} &
                      {t for p in pas(d) if (p.get("kind") or "").startswith("res")
                       for t in (p.get("terminals") or [])})
    if hand:
        S_j1 = minimal_fixpoint_reach(d, acg, inp, cut_nets=set(hand))
        c2, _w2, b2, _d2 = classify_cells(d, acg, inp, set(outp), S_j1, cut_nets=set(hand))
        t2 = defaultdict(int)
        for v in c2.values():
            t2[v] += 1
        rec["j1_handlist"] = hand
        rec["cells_with_J1"] = dict(sorted(t2.items()))
        rec["CG_devices_with_J1"] = sorted([k for k, v in c2.items() if v == "CG"])
    drives, ddetail = drive_types(d, acg, cells, S_min, inp)
    rec["drives"] = drives
    adj, elab = loop_graph(d, acg, inp, drives)
    cyc, trunc, nn = simple_cycles(adj)
    kept, dropped = [], []
    for c in cyc:
        rt, nm = is_passive_roundtrip(c, elab)
        (dropped if rt else kept).append((c, nm))
    rec["cycles"] = {"n_simple_cycles_raw": len(cyc),
                     "n_dropped_passive_roundtrip": len(dropped),
                     "dropped": [{"nodes": c, "passive": nm} for c, nm in dropped],
                     "n_basic_closed_paths_v518": len(kept),
                     "truncated": trunc, "n_nodes": nn}
    # v5.17 옛 혼합 처리(전류+저항 -> 'current/value_dep' 는 전류 구동이 아님)로 세면 폐경로가 몇 개인가
    drives_old = {k: ("current" if v == "current" else ("x" + v)) for k, v in drives.items()}
    adj_o, elab_o = loop_graph(d, acg, inp, drives_old)
    cyc_o, _t, _n = simple_cycles(adj_o)
    kept_o = [c for c in cyc_o if not is_passive_roundtrip(c, elab_o)[0]]
    rec["cycles_old_mixed_rule"] = {"n_simple_cycles_raw": len(cyc_o),
                                    "n_basic_after_roundtrip_drop": len(kept_o)}
    stage = stage_index(d, acg, inp, S_min, cells, drives)
    fwd_nodes, fwd_dev = forward_sets(d, acg, inp, outp, S_min)
    gate_nets = {m["gate"] for m in devs(d)}
    cl, det = classify_cycles([c for c, _ in kept], elab, d, fwd_dev, fwd_nodes, stage, gate_nets)
    rec["loop_class_v518"] = cl
    rec["loop_detail"] = det
    rec["stage_index"] = stage
    rec["forward_devices"] = sorted(fwd_dev)
    rec["attribution"] = bias_column_attribution(bc, cells)
    return rec, bc, cells


def is_bundle_roundtrip(cyc, elab, bundles):
    """N3.2-2: pass 묶음 안의 왕복(역병렬 쌍 내부 순환)은 폐경로가 아니다."""
    if len(cyc) != 2 or not bundles:
        return False, None
    a, b = cyc
    f = {n for (k, n) in elab.get((a, b), set()) if k == "mos"}
    r = {n for (k, n) in elab.get((b, a), set()) if k == "mos"}
    fp = {n for (k, n) in elab.get((a, b), set()) if k == "pas"}
    rp = {n for (k, n) in elab.get((b, a), set()) if k == "pas"}
    if fp or rp:
        return False, None
    for bd in bundles:
        if f | r == set(bd):
            return True, bd
    return False, None


VAR_JSONL = os.path.join(OUT, "rerun_v518_variants.jsonl")


def variant(name, cut_nets=frozenset(), b_restricted=False, passive_cost=0,
            drop_bundle_roundtrip=True, label=""):
    PASSIVE_STAGE_COST[0] = passive_cost
    d = load(name)
    ports = ports_of(d)
    portnets = set(ports.keys())
    rails, _ = rails_of(d)
    inp = [k for k, v in ports.items()
           if "input" in (v.get("role") or "") or v.get("direction") == "input"]
    outp = [k for k, v in ports.items()
            if "output" in (v.get("role") or "") or v.get("direction") == "output"]
    if not (inp and outp):
        return {"circuit": name, "label": label, "view": "불가(U-08)"}
    acg = ac_ground(d, rails, portnets) | set(cut_nets)
    S = minimal_fixpoint_reach(d, acg, inp, cut_nets=cut_nets, b_restricted=b_restricted)
    cells, _w, bundles, _dist = classify_cells(d, acg, inp, set(outp), S, cut_nets=cut_nets)
    drives, _dd = drive_types(d, acg, cells, S, inp)
    adj, elab = loop_graph(d, acg, inp, drives)
    cyc, trunc, _n = simple_cycles(adj)
    kept, dropped = [], []
    for c in cyc:
        rt, nm = is_passive_roundtrip(c, elab)
        if rt:
            dropped.append(("passive", c, nm)); continue
        if drop_bundle_roundtrip:
            bt, bd = is_bundle_roundtrip(c, elab, bundles)
            if bt:
                dropped.append(("bundle", c, bd)); continue
        kept.append(c)
    stage = stage_index(d, acg, inp, S, cells, drives)
    fwd_nodes, fwd_dev = forward_sets(d, acg, inp, outp, S)
    gate_nets = {m["gate"] for m in devs(d)}
    cl, det = classify_cycles(kept, elab, d, fwd_dev, fwd_nodes, stage, gate_nets)
    t = defaultdict(int)
    for v in cells.values():
        t[v] += 1
    return {"circuit": name, "label": label, "view": "가능",
            "cut_nets": sorted(cut_nets), "b_restricted": b_restricted,
            "passive_stage_cost": passive_cost,
            "cells": dict(sorted(t.items())),
            "CG": sorted([k for k, v in cells.items() if v == "CG"]),
            "bundles": bundles,
            "n_basic_closed_paths": len(kept),
            "n_dropped": len(dropped),
            "dropped": [(k, c, n) for (k, c, n) in dropped],
            "loop_class": dict(cl), "c4_detail": det.get("c4", []),
            "c3b_detail": det.get("c3b_strict", []) + det.get("c3b_loose", []),
            "stage": stage}


def run_variants():
    if os.path.exists(VAR_JSONL):
        os.remove(VAR_JSONL)
    specs = []
    for n in NAMES:
        specs.append((n, frozenset(), False, 0, "V0: 계획 본문 그대로(수동엣지비용0)"))
        specs.append((n, frozenset(), False, 1, "V1: 수동 엣지 비용 1(감도)"))
        specs.append((n, frozenset(), True, 0, "V2: history H2 문구(b=전류구동만)"))
    specs.append(("current_reuse_telescopic_ota", frozenset({"Vbias2", "Vbias3"}), False, 0,
                  "V3: J1 손목록(Vbias2,Vbias3) 적용"))
    specs.append(("current_reuse_telescopic_ota", frozenset({"Vbias2", "Vbias3"}), False, 1,
                  "V4: J1 손목록 + 수동엣지비용1"))
    specs.append(("sf_pushpull_output_opamp", frozenset({"agnd"}), False, 0,
                  "V5: agnd 를 supply_nets 로 선언했다고 보고(교류접지)"))
    specs.append(("pushpull_follower_buffer", frozenset({"agnd"}), False, 0,
                  "V5: agnd 를 supply_nets 로 선언했다고 보고(교류접지)"))
    for (n, cut, br, pc, lab) in specs:
        try:
            r = variant(n, cut, br, pc, True, lab)
        except Exception:
            import traceback
            r = {"circuit": n, "label": lab, "error": traceback.format_exc()}
        with open(VAR_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("variant", n, lab, r.get("loop_class"), r.get("CG"))
    PASSIVE_STAGE_COST[0] = 0


def main():
    for f in (JSONL, TXT):
        if os.path.exists(f):
            os.remove(f)
    for n in NAMES:
        try:
            rec, bc, cells = run(n)
        except Exception:
            import traceback
            rec = {"circuit": n, "error": traceback.format_exc()}
        with open(JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        with open(TXT, "a", encoding="utf-8") as f:
            f.write("=" * 78 + "\n[" + n + "]\n")
            for k, v in rec.items():
                if k in ("cells_detail", "loop_detail", "drives", "stage_index"):
                    continue
                f.write("  %s: %s\n" % (k, json.dumps(v, ensure_ascii=False)))
            for k in ("cells_detail", "drives", "stage_index", "loop_detail"):
                if rec.get(k):
                    f.write("  %s: %s\n" % (k, json.dumps(rec[k], ensure_ascii=False)))
        print("done", n)


if __name__ == "__main__":
    main()
