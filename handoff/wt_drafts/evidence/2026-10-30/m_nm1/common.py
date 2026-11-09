# -*- coding: utf-8 -*-
"""m_nm1 측정 공통: library topology 연결만으로 색 그래프, 1-WL, 자기동형 궤도, 정준 위치를 만든다.
엔진 코드는 쓰지 않는다(원칙 8·14). 이름은 구조 키가 아니라 라벨일 뿐이다."""
import json, glob, os, random, itertools, time
import networkx as nx
from networkx.algorithms.isomorphism import GraphMatcher

LIB = r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/library"
ROLEMODE = "family"   # family: p/n 극성 접미를 합친 role 색, exact: role 문자열 그대로
OUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-30/m_nm1"


def circuits():
    return [os.path.basename(f)[:-len(".topology.json")]
            for f in sorted(glob.glob(LIB + "/*.topology.json"))
            if not os.path.basename(f).startswith("_")]


class Model:
    """mos: dict name -> dict(kind,d,g,s,b)   pas: name -> dict(kind,t:[a,b],decl)  isrc: name -> dict(t:[a,b],decl)"""

    def __init__(self, mos, pas, isrc, rails, bias, ports):
        self.mos, self.pas, self.isrc = mos, pas, isrc
        self.rails, self.bias, self.ports = set(rails), set(bias), dict(ports)  # ports: net -> role

    def rename(self, perm_dev, perm_net):
        """이름 전단사 적용한 새 Model."""
        def n(x): return perm_net.get(x, x)
        mos = {perm_dev[k]: dict(v, d=n(v["d"]), g=n(v["g"]), s=n(v["s"]), b=(n(v["b"]) if v.get("b") else None)) for k, v in self.mos.items()}
        pas = {perm_dev[k]: dict(v, t=[n(v["t"][0]), n(v["t"][1])]) for k, v in self.pas.items()}
        isrc = {perm_dev[k]: dict(v, t=[n(v["t"][0]), n(v["t"][1])]) for k, v in self.isrc.items()}
        return Model(mos, pas, isrc, [n(x) for x in self.rails], [n(x) for x in self.bias],
                     {n(k): v for k, v in self.ports.items()})

    def nets(self):
        s = set()
        for m in self.mos.values():
            s |= {m["d"], m["g"], m["s"]}
            if m.get("b"): s.add(m["b"])
        for p in list(self.pas.values()) + list(self.isrc.values()):
            s |= set(p["t"])
        s |= self.rails | self.bias | set(self.ports)
        return s


def load(name):
    d = json.load(open(f"{LIB}/{name}.topology.json", encoding="utf-8"))
    mos = {}
    for x in d["netlist"]:
        mos[x["name"]] = dict(kind=x["kind"], d=x["drain"], g=x["gate"], s=x["source"], b=x.get("bulk"))
    pas = {x["name"]: dict(kind=x["kind"], t=list(x["terminals"]),
                           decl=(x.get("value_ohm", x.get("value_farad")) is not None)) for x in d.get("passive_elements", [])}
    isrc = {x["name"]: dict(t=list(x["terminals"]), decl=(x.get("value_amp") is not None)) for x in (d.get("ideal_sources") or [])}
    ports = {k: v["role"] for k, v in d.get("ports", {}).items() if not k.startswith("_")}
    for x in d.get("ideal_sources") or []:
        assert x["kind"] == "current_source"
    return Model(mos, pas, isrc, d["supply_nets"], d.get("bias_inputs") or [], ports)


# ---------------- 색 그래프 ----------------
def build_graph(M):
    """정점 'D:이름'/'N:넷'. 간선 라벨은 집합(정렬 튜플). MOS d·s 는 같은 채널 라벨 c (DEC-97 (3))."""
    G = nx.Graph()
    def add_edge(u, v, lab):
        if G.has_edge(u, v):
            G[u][v]["lab"] = tuple(sorted(G[u][v]["lab"] + (lab,)))
        else:
            G.add_edge(u, v, lab=(lab,))
    for n in M.nets():
        if n in M.rails: c = "net:rail"
        elif n in M.bias: c = "net:bias"
        elif n in M.ports:
            r = M.ports[n]
            if ROLEMODE == "family": r = r[:-2] if r.endswith(("_p", "_n")) else r
            c = "net:port:" + r
        else: c = "net:plain"
        G.add_node("N:" + n, base=c, kind="net")
    for k, m in M.mos.items():
        diode = (m["g"] == m["d"]) or (m["g"] == m["s"])
        G.add_node("D:" + k, base=f"mos:{m['kind']}:diode={int(diode)}", kind="dev")
        add_edge("D:" + k, "N:" + m["d"], "c"); add_edge("D:" + k, "N:" + m["s"], "c")
        add_edge("D:" + k, "N:" + m["g"], "g")
        if m.get("b"): add_edge("D:" + k, "N:" + m["b"], "b")
    for k, p in M.pas.items():
        G.add_node("D:" + k, base=f"pas:{p['kind']}:decl={int(p['decl'])}", kind="dev")
        add_edge("D:" + k, "N:" + p["t"][0], "p"); add_edge("D:" + k, "N:" + p["t"][1], "p")  # 방향 없는 원소
    for k, p in M.isrc.items():
        G.add_node("D:" + k, base=f"isrc:decl={int(p['decl'])}", kind="dev")
        add_edge("D:" + k, "N:" + p["t"][0], "i0"); add_edge("D:" + k, "N:" + p["t"][1], "i1")  # 방향 있음
    return G


def wl_refine(G, init):
    """init: v -> 정렬 가능한 색(문자열/튜플). 반환: v -> 정수 순위(이름 무관 정렬)."""
    keys = sorted({repr(c) for c in init.values()})
    rk = {k: i for i, k in enumerate(keys)}
    col = {v: rk[repr(c)] for v, c in init.items()}
    ncol = len(set(col.values()))
    while True:
        sig = {v: (col[v], tuple(sorted((G[v][u]["lab"], col[u]) for u in G[v]))) for v in G}
        keys = sorted({repr(s) for s in sig.values()})
        rk = {k: i for i, k in enumerate(keys)}
        new = {v: rk[repr(sig[v])] for v in G}
        nn = len(set(new.values()))
        col = new
        if nn == ncol:
            return col
        ncol = nn


def _sigs(G, c):
    return {v: (c[v], tuple(sorted((G[v][u]["lab"], c[u]) for u in G[v]))) for v in G}


def _refine2(G, cA, cB):
    """두 색칠을 같은 순위표로 동시에 정제. 색 히스토그램이 어긋나면 None."""
    import collections
    while True:
        sA, sB = _sigs(G, cA), _sigs(G, cB)
        keys = sorted({repr(x) for x in sA.values()} | {repr(x) for x in sB.values()})
        rk = {k: i for i, k in enumerate(keys)}
        nA = {v: rk[repr(sA[v])] for v in G}; nB = {v: rk[repr(sB[v])] for v in G}
        if collections.Counter(nA.values()) != collections.Counter(nB.values()):
            return None
        if len(set(nA.values())) == len(set(cA.values())):
            return nA, nB
        cA, cB = nA, nB


def automorphic(G, cA, cB, _nodes=[0]):
    """색 cA 를 색 cB 로 보내는 G 의 자기동형(간선 라벨 보존)이 있는가. 개별화·정제 역추적."""
    r = _refine2(G, cA, cB)
    if r is None: return False
    cA, cB = r
    cellsA, cellsB = {}, {}
    for v in G:
        cellsA.setdefault(cA[v], []).append(v); cellsB.setdefault(cB[v], []).append(v)
    ns = [(len(m), c) for c, m in cellsA.items() if len(m) > 1]
    if not ns:
        mp = {}
        for c, m in cellsA.items(): mp[m[0]] = cellsB[c][0]
        for u, v in G.edges():
            x, y = mp[u], mp[v]
            if not G.has_edge(x, y) or G[x][y]["lab"] != G[u][v]["lab"]: return False
        for v in G:
            if G.nodes[v]["base"] != G.nodes[mp[v]]["base"]: return False
        return True
    _, c = min(ns)
    v0 = min(cellsA[c])
    for w in sorted(cellsB[c]):
        nA = {v: 2 * cA[v] + 1 for v in G}; nA[v0] = 2 * cA[v0]
        nB = {v: 2 * cB[v] + 1 for v in G}; nB[w] = 2 * cB[w]
        if automorphic(G, nA, nB): return True
    return False


def _same_orbit(G, col, u, v, deadline=None):
    cA = {x: 2 * col[x] + 1 for x in G}; cA[u] = 2 * col[u]
    cB = {x: 2 * col[x] + 1 for x in G}; cB[v] = 2 * col[v]
    return automorphic(G, cA, cB)


def orbits(G, wl):
    """자기동형 궤도: wl 클래스 안에서 union-find (정점 전체)."""
    parent = {v: v for v in G}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    classes = {}
    for v in G: classes.setdefault(wl[v], []).append(v)
    for c, mem in classes.items():
        mem = sorted(mem)
        if len(mem) < 2: continue
        reps = []
        for v in mem:
            for r in reps:
                if _same_orbit(G, wl, r, v):
                    parent[find(v)] = find(r); break
            else:
                reps.append(v)
    orb = {}
    for v in G: orb.setdefault(find(v), []).append(v)
    return {v: i for i, (r, mem) in enumerate(sorted(orb.items(), key=lambda kv: (wl[kv[0]], min(kv[1])))) for v in mem} , list(orb.values())


def canon_positions(G, wl, leaf_cap=20000):
    """nauty 식 개별화·정제 + 고정 접두 안정자 궤도 가지치기. 정준 위치 pos: v -> 0..n-1.
    남는 선택(같은 궤도 대표)은 이름 순 첫 번째 = 이름 의존 지점(자기동형이라 형태는 같다)."""
    n = len(G)
    best = {"form": None, "pos": None}
    leaves = [0]

    def refine(col):
        ncol = len(set(col.values()))
        while True:
            sig = {v: (col[v], tuple(sorted((G[v][u]["lab"], col[u]) for u in G[v]))) for v in G}
            keys = sorted({repr(s) for s in sig.values()})
            rk = {k: i for i, k in enumerate(keys)}
            new = {v: rk[repr(sig[v])] for v in G}
            nn = len(set(new.values()))
            col = new
            if nn == ncol: return col
            ncol = nn

    def form_of(col):
        pos = col
        e = sorted((min(pos[u], pos[v]), max(pos[u], pos[v]), G[u][v]["lab"]) for u, v in G.edges())
        bases = [None] * n
        for v in G: bases[pos[v]] = G.nodes[v]["base"]
        return (tuple(bases), tuple(e))

    def rec(col):
        cells = {}
        for v, c in col.items(): cells.setdefault(c, []).append(v)
        nonsingle = [(len(m), c) for c, m in cells.items() if len(m) > 1]
        if not nonsingle:
            leaves[0] += 1
            f = form_of(col)
            if best["form"] is None or f < best["form"]:
                best["form"], best["pos"] = f, dict(col)
            return
        if leaves[0] > leaf_cap: raise RuntimeError("leaf cap")
        _, c = min(nonsingle)
        mem = sorted(cells[c])
        reps = []
        for v in mem:
            for r in reps:
                if _same_orbit_marked(G, col, r, v): break
            else:
                reps.append(v)
        for v in reps:
            nc = {u: (2 * col[u] + 1) for u in col}
            nc[v] = 2 * col[v]
            # 순위를 정수로 재매김(정렬 유지)
            ks = sorted(set(nc.values())); rk = {k: i for i, k in enumerate(ks)}
            nc = {u: rk[x] for u, x in nc.items()}
            rec(refine(nc))

    rec(dict(wl))
    return best["pos"], leaves[0]


def _same_orbit_marked(G, col, u, v):
    return _same_orbit(G, col, u, v)


def devices(G):
    return sorted(v for v in G if v.startswith("D:"))


# ------------ 자기동형 동치(집합 표시) ------------
def sets_equivalent(G, wl, S1, S2):
    """집합 S1 을 S2 로 보내는 색 보존 자기동형이 있는가(정점 이름 'D:..' 집합)."""
    if len(S1) != len(S2): return False
    cA = {x: 2 * wl[x] + (1 if x in S1 else 0) for x in G}
    cB = {x: 2 * wl[x] + (1 if x in S2 else 0) for x in G}
    return automorphic(G, cA, cB)


def append(path, rec):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def random_rename(M, rng):
    devs = list(M.mos) + list(M.pas) + list(M.isrc)
    nets = sorted(M.nets())
    dn = [f"d{i:04d}" for i in range(len(devs))]; rng.shuffle(dn)
    nn = [f"n{i:04d}" for i in range(len(nets))]; rng.shuffle(nn)
    return dict(zip(devs, dn)), dict(zip(nets, nn))
