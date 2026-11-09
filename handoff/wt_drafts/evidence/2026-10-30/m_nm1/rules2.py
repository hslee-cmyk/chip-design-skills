# -*- coding: utf-8 -*-
"""DEC-17 L 동치류 주인(이름 순서)와 DEC-71 루프 끊는 점(사이클 시작점 노드 이름) 측정."""
import sys, time, itertools, collections
import networkx as nx
import common
from common import *
from kcl import driven_nets

rolemode = sys.argv[1] if len(sys.argv) > 1 else "family"
common.ROLEMODE = rolemode
only = sys.argv[2:] or circuits()
RES = OUT + f"/results_rules2_{rolemode}.jsonl"


def sym(M):
    G = build_graph(M)
    wl = wl_refine(G, {v: G.nodes[v]["base"] for v in G})
    orb, groups = orbits(G, wl)
    return G, wl, orb


def signal_nets(M):
    """입력 포트에서 gate->drain/source, 채널 d<->s, 수동소자를 따라 닿는 넷(레일·bias 입력에서 멈춤)."""
    stop = set(M.rails) | set(M.bias)
    seeds = [n for n, r in M.ports.items() if r.startswith(("differential_input", "single_ended_input"))]
    seen = set(seeds); stack = list(seeds)
    adj = collections.defaultdict(set)
    for m in M.mos.values():
        adj[m["g"]] |= {m["d"], m["s"]}
        adj[m["d"]].add(m["s"]); adj[m["s"]].add(m["d"])
    for p in M.pas.values():
        a, b = p["t"]; adj[a].add(b); adj[b].add(a)
    while stack:
        n = stack.pop()
        for u in adj[n]:
            if u not in seen and u not in stop:
                seen.add(u); stack.append(u)
    return seen


# ---------------------------------------------------------------- L 동치류
def l_owner(M, G, wl, orb, c):
    sig = signal_nets(M)
    cls = collections.defaultdict(list)
    for k, m in M.mos.items():
        cls[(m["kind"], m["g"], m["s"])].append(k)
    srccount = collections.Counter(m["s"] for m in M.mos.values())
    out = []
    for key, mem in sorted(cls.items()):
        if len(mem) < 2: continue
        mem = sorted(mem)
        g = key[1]
        bias_gate = (g in M.bias) or (g not in sig and g not in M.rails and g not in M.ports)
        tails = [x for x in mem if bias_gate and srccount[M.mos[x]["d"]] >= 2]
        diodes = [x for x in mem if M.mos[x]["d"] == M.mos[x]["g"]]
        o = lambda xs: len({orb["D:" + x] for x in xs})
        rec = dict(members=mem, gate=g, source=key[2], kind=key[0], orbits=o(mem), bias_gate=bias_gate,
                   tails=tails, diodes=diodes, drains=[M.mos[x]["d"] for x in mem])
        if len(tails) == 1:
            rec.update(step="1_tail_unique", name_reached=False, cand=tails)
        elif len(tails) > 1:
            rec.update(step="1_tail_multi(stage tie-break needs views)", cand=tails,
                       name_reached="unknown(views)", cand_orbits=o(tails))
        elif diodes:
            rec.update(step="2_diode_member" + ("_multi" if len(diodes) > 1 else ""), cand=diodes,
                       name_reached=len(diodes) > 1, cand_orbits=o(diodes))
        else:
            rec.update(step="3_main_path_or_4_name", cand=mem, name_reached="unknown(main_path needs views)",
                       cand_orbits=o(mem))
        out.append(rec)
    return out


# ---------------------------------------------------------------- 루프 끊는 점
def loop_analysis(M, G, wl, orb, cap_cycles=300000, passive_cost=0):
    """신호 방향 그래프(넷 노드): g->d(1; diode gate 넷은 0), g->s(0), s->d(0), 수동 양방향(passive_cost).
    교류접지(레일·bias·gate 전용 비구동) 제거, 입력 포트 넷은 여기원(거리 0 시작, 사이클 노드에서는 제거)."""
    sig = signal_nets(M)
    ports_in = {n for n, r in M.ports.items() if r.startswith(("differential_input", "single_ended_input"))}
    diodenets = {m["g"] for m in M.mos.values() if m["g"] == m["d"]}
    removed = (set(M.rails) | set(M.bias) | ports_in) | {n for n in M.nets() if n not in sig and n not in M.ports}
    D = nx.MultiDiGraph()
    # 간선: (u,v,cost,devname,kindchar)
    def add(u, v, cost, dev, typ):
        D.add_edge(u, v, key=(dev, typ, u, v), cost=cost, dev=dev, typ=typ)
    for k, m in M.mos.items():
        g, d, s = m["g"], m["d"], m["s"]
        if g == d and g == s: continue
        cdg = 0 if g in diodenets else 1
        if g != d: add(g, d, cdg, k, "gd")
        if g != s: add(g, s, 0, k, "gs")
        if s != d: add(s, d, 0, k, "sd")
    for k, p in M.pas.items():
        a, b = p["t"]
        if a == b: continue
        add(a, b, passive_cost, k, "p"); add(b, a, passive_cost, k, "p")
    # 0-1 BFS 거리: 여기 포트 넷에서 시작
    dist = {}
    from collections import deque
    dq = deque()
    for n in ports_in:
        if n in D: dist[n] = 0; dq.append(n)
    while dq:
        u = dq.popleft()
        for _, v, dta in D.out_edges(u, data=True):
            nd = dist[u] + dta["cost"]
            if v not in dist or nd < dist[v]:
                dist[v] = nd
                (dq.appendleft if dta["cost"] == 0 else dq.append)(v)
    # 신호 그래프(제거 집합 뺀 것)
    S = nx.DiGraph()
    for u, v, dta in D.edges(data=True):
        if u in removed or v in removed: continue
        if S.has_edge(u, v): S[u][v]["es"].append(dta)
        else: S.add_edge(u, v, es=[dta])
    res = dict(n_cycles=0, truncated=False, loops=[])
    t0 = time.time()
    cnt = 0
    for cyc in nx.simple_cycles(S):
        cnt += 1
        if cnt > cap_cycles or time.time() - t0 > 90:
            res["truncated"] = True; break
        n = len(cyc)
        if n < 2: continue
        # 간선 선택: 연속 노드쌍마다 병렬 간선(소자) 후보를 모두 고려해 각각 별개 사이클로 확장
        pairs = [(cyc[i], cyc[(i + 1) % n]) for i in range(n)]
        choices = [S[u][v]["es"] for u, v in pairs]
        for combo in itertools.product(*choices):
            # 2단자 수동소자 하나의 왕복(길이 2, 같은 소자)은 폐경로 아님
            if n == 2 and combo[0]["typ"] == "p" and combo[1]["typ"] == "p" and combo[0]["dev"] == combo[1]["dev"]:
                continue
            # 같은 소자 두 번 쓰는 사이클은 제외하지 않음(단순 사이클 정의는 노드 기준)
            INF = 10 ** 9
            unreach = any(dist.get(x, INF) >= INF for x in cyc)
            if unreach:
                res["unreach"] = res.get("unreach", 0) + 1
                continue
            ret = [dist[v] <= dist[u] for (u, v) in pairs]
            # 회전: 이름 정렬 첫 노드에서 시작
            start = min(range(n), key=lambda i: pairs[i][0])
            rot = [(start + i) % n for i in range(n)]
            seq_e = [combo[i] for i in rot]; seq_ret = [ret[i] for i in rot]; seq_p = [pairs[i] for i in rot]
            if all(seq_ret):
                segs = [list(range(n))]
            elif not any(seq_ret):
                segs = []
            else:
                # 순환적 극대 연속 구간. 순환 표현은 시작점 기준이므로 시작점에서 걸치는 구간은 둘로 보지 않고 하나로 합친다.
                segs = []
                i0 = next(i for i in range(n) if not seq_ret[i])  # 비복귀 간선에서 시작
                cur = []
                for j in range(1, n + 1):
                    i = (i0 + j) % n
                    if seq_ret[i]: cur.append(i)
                    else:
                        if cur: segs.append(cur); cur = []
                if cur: segs.append(cur)
            # 구간 순서: 이름 정렬 시작점에서의 첫 등장 위치 순(= '가장 이른 구간')
            segs.sort(key=lambda sg: min(sg))
            has_cap = any(e["dev"] in M.pas and M.pas[e["dev"]]["kind"] == "capacitor" for e in combo)
            def seg_has_active(sg): return any(seq_e[i]["typ"] in ("gd", "gs", "sd") for i in sg)
            # 복귀 구간 다음 첫 gate(gd/gs 간선의 소자)
            def next_gate(sg):
                j = (sg[-1] + 1) % n
                for t in range(n):
                    e = seq_e[(j + t) % n]
                    if e["typ"] in ("gd", "gs"): return e["dev"]
                return None
            cands = [next_gate(sg) for sg in segs]
            active_ret = [seg_has_active(sg) for sg in segs]
            res["loops"].append(dict(nodes=len(cyc), segs=len(segs), has_cap=has_cap, cands=cands,
                                     active_segs=active_ret, devs=sorted({e['dev'] for e in combo}),
                                     cyc=[p[0] for p in seq_p],
                                     ekey=sorted((e['dev'], e['typ'], p[0], p[1]) for e, p in zip(seq_e, seq_p)),
                                     chosen=(cands[0] if cands else None),
                                     allret=all(seq_ret), gates=sorted({e['dev'] for e in combo if e['typ'] in ('gd','gs')})))
    res["n_cycles"] = len(res["loops"])
    return res


def summarise_loops(M, G, wl, orb, res):
    L = res["loops"]
    multi = [l for l in L if l["segs"] >= 2]
    # (3-b) 근사: 복귀 구간 중 능동 셀이 있는 구간이 하나 이상이고 복귀 구간이 있는 루프
    b3 = [l for l in L if l["segs"] >= 1 and any(l["active_segs"])]
    def tie_info(l):
        # 이름 의존 후보: 복귀 구간별 끊는 점 소자들이 서로 다른 소자일 때만 이름이 결정
        cand = [c for c, a in zip(l["cands"], l["active_segs"]) if c is not None]
        dist = sorted(set(cand))
        if len(dist) <= 1: return ("same_cand", len(dist), 1)
        norb = len({orb["D:" + c] for c in dist})
        return ("differs", len(dist), norb)
    ti = [(l, tie_info(l)) for l in b3 if sum(l["active_segs"]) >= 2 or l["segs"] >= 2]
    differs = [(l, t) for l, t in ti if t[0] == "differs"]
    harmless = [(l, t) for l, t in differs if t[2] == 1]
    harmful = [(l, t) for l, t in differs if t[2] > 1]
    allret = [l for l in b3 if l["allret"] and len(l["gates"]) >= 2]
    ar_diff = [l for l in allret if len({orb["D:" + g] for g in l["gates"]}) > 1]
    ar_same = [l for l in allret if len({orb["D:" + g] for g in l["gates"]}) == 1]
    return dict(allret_loops=len(allret), allret_cand_same_orbit=len(ar_same), allret_cand_diff_orbit=len(ar_diff),
                allret_diff_examples=[dict(cyc=l["cyc"], gates=l["gates"], has_cap=l["has_cap"]) for l in ar_diff[:4]],
                unreach_loops=res.get('unreach',0), n_cycles=res["n_cycles"], truncated=res["truncated"], with_ge2_segments=len(multi),
                b3_like=len(b3), b3_ge2_segments=len(ti), name_decides=len(differs),
                name_decides_same_orbit=len(harmless), name_decides_diff_orbit=len(harmful),
                harmful_examples=[dict(cyc=l["cyc"], cands=l["cands"], devs=l["devs"], has_cap=l["has_cap"]) for l, _ in harmful[:5]],
                harmless_examples=[dict(cyc=l["cyc"], cands=l["cands"]) for l, _ in harmless[:2]])


def loop_metamorphic(M, G, wl, orb, res0, pc, nren=3):
    import random
    rng = random.Random(7)
    base = {}
    for l in res0["loops"]:
        if l["segs"] >= 1 and any(l["active_segs"]):
            base[tuple(l["ekey"])] = l["chosen"]
    out = dict(loops=len(base), runs=[])
    for _ in range(nren):
        pd, pn = random_rename(M, rng)
        invd = {v: k for k, v in pd.items()}; invn = {v: k for k, v in pn.items()}
        M2 = M.rename(pd, pn)
        G2, wl2, orb2 = sym(M2)
        r2 = loop_analysis(M2, G2, wl2, orb2, passive_cost=pc)
        mp = {}
        for l in r2["loops"]:
            if l["segs"] >= 1 and any(l["active_segs"]):
                k = tuple(sorted((invd[d], t, invn[u], invn[v]) for d, t, u, v in l["ekey"]))
                mp[k] = invd.get(l["chosen"]) if l["chosen"] else None
        same = diff = diff_same_orbit = missing = 0
        for k, ch in base.items():
            kk = tuple(sorted(k))
            if kk not in mp: missing += 1; continue
            if mp[kk] == ch: same += 1
            else:
                diff += 1
                if ch and mp[kk] and orb["D:" + ch] == orb["D:" + mp[kk]]: diff_same_orbit += 1
        out["runs"].append(dict(same=same, diff=diff, diff_same_orbit=diff_same_orbit, diff_other_orbit=diff - diff_same_orbit, missing=missing))
    return out


for c in only:
    t0 = time.time()
    try:
        M = load(c)
        G, wl, orb = sym(M)
        rec = dict(circuit=c, rolemode=rolemode)
        lo = l_owner(M, G, wl, orb, c)
        rec["l_classes"] = lo
        for pc in (0, 1):
            res = loop_analysis(M, G, wl, orb, passive_cost=pc)
            rec[f"loops_pcost{pc}"] = summarise_loops(M, G, wl, orb, res)
            rec[f"loops_meta_pcost{pc}"] = loop_metamorphic(M, G, wl, orb, res, pc)
        rec["secs"] = round(time.time() - t0, 1)
    except Exception:
        import traceback
        rec = dict(circuit=c, rolemode=rolemode, error=traceback.format_exc())
    append(RES, rec)
    print(c, rec.get("secs"), "ERR" if "error" in rec else "", flush=True)
