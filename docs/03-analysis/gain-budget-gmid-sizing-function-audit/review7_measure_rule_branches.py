# -*- coding: utf-8 -*-
"""review7 일반성 재감사 -- 규칙 분기 발동 측정(순수 구조 계산, topology.json만 읽는다).

계획서 v5.12(커밋 69b151f)의 새 규칙 중 회로마다 발동 여부를 셀 수 있는 것만 센다.
사이징·LUT·탐색은 일절 돌리지 않는다.

측정 항목
  A. 레일 판정(DEC-60 전환기 이름집합 대 agnd 포함)
  B. 기본 전달 뷰 가능 여부(N3.2-2, ports 선언 유무)
  C. 교류접지 집합 3분류(N3.2-1)
  D. 셀 분류(N3.2-3): CS / CD / CG·pass 후보 / 비셀
  E. 노드 구동 종류(용어집): 전압 / 전류 / 값 의존
  F. follower 묶음 R(u) (DEC-63)
  G. G_vgs 사이클 분류 v0/v1/v2 및 VDS-1 (DEC-64)
  H. 측면 주입 K8 (N3.7)
  I. 병렬 셀(같은 노드 합류) 블록 후보
  J. DC 전도 그래프: 잎 가지치기 저항(DEC-70), 가지·기둥(DEC-71)
  K. 출력 포트 방향 분류 class-A / push-pull (DEC-65)
  L. 신호 그래프 루프 분류 (0)~(4) 근사(N3.2-2)

결과는 케이스마다 out 파일에 append 한다(WP-11).
"""
from __future__ import annotations

import json
import os
import sys
import itertools
from collections import defaultdict

LIB = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "measure_results.txt")

# DEC-60 전환기 해석: 현 코드 이름 집합 (sizing_recipe _DEFAULT_RAIL_HI/_DEFAULT_RAIL_LO)
RAIL_HI = {"vdd", "VDD"}
RAIL_LO = {"gnd", "GND", "vss", "VSS"}
NAME_SET_RAILS = RAIL_HI | RAIL_LO
# 사람이 보면 레일인 중간 전위 넷(DEC-60 본문이 예로 든 agnd)
EXTRA_RAIL_CANDIDATES = {"agnd", "AGND"}

PATH_LIMIT = 100000


def emit(fh, *a):
    s = " ".join(str(x) for x in a)
    print(s)
    fh.write(s + "\n")
    fh.flush()


def load(name):
    with open(os.path.join(LIB, name), encoding="utf-8") as f:
        return json.load(f)


class Ckt:
    def __init__(self, fname, d):
        self.fname = fname
        self.name = d.get("topology_name") or fname
        self.dev = [x for x in (d.get("netlist") or []) if x.get("kind") in ("nmos", "pmos")]
        self.other_dev = [x for x in (d.get("netlist") or []) if x.get("kind") not in ("nmos", "pmos")]
        self.pas = list(d.get("passive_elements") or [])
        self.isrc = list(d.get("ideal_sources") or [])
        p = d.get("ports") or {}
        self.ports = {k: v for k, v in p.items() if isinstance(v, dict) and "role" in v}
        self.supply_nets = d.get("supply_nets")
        self.symmetry = d.get("symmetry") or {}
        self.declared_stack = {}
        for k in ("device_roles", "sizing_roles"):
            v = d.get(k)
            if isinstance(v, dict):
                for dn, dv in v.items():
                    if isinstance(dv, dict) and "vertical_stack_id" in dv:
                        self.declared_stack[dn] = dv["vertical_stack_id"]

        self.nets = set()
        for x in self.dev:
            self.nets |= {x["drain"], x["gate"], x["source"]}
        for x in self.pas:
            self.nets |= set(x.get("terminals") or [])
        for x in self.isrc:
            self.nets |= set(x.get("terminals") or [])

    # ---------- A. 레일 ----------
    def rails(self, include_extra=False):
        if self.supply_nets:
            return set(self.supply_nets) & self.nets
        r = set(n for n in self.nets if n in NAME_SET_RAILS)
        if include_extra:
            r |= set(n for n in self.nets if n in EXTRA_RAIL_CANDIDATES)
        return r

    def extra_rail_nets(self):
        return set(n for n in self.nets if n in EXTRA_RAIL_CANDIDATES)

    # ---------- C. 교류접지 ----------
    def ac_ground(self, rails):
        cls1 = set(rails)
        # (2) gate에만 붙고 구동되지 않는 넷 (입력 포트·수동소자 단자·이상원 단자 제외)
        gate_nets, chan_nets = set(), set()
        for x in self.dev:
            gate_nets.add(x["gate"])
            chan_nets |= {x["drain"], x["source"]}
        pas_nets = set()
        for x in self.pas:
            pas_nets |= set(x.get("terminals") or [])
        for x in self.isrc:
            pas_nets |= set(x.get("terminals") or [])
        cls2 = {n for n in gate_nets
                if n not in chan_nets and n not in pas_nets and n not in self.ports and n not in cls1}
        cls3 = set()  # 이상 전압원 단자 -- library 7개에 이상 전압원 없음
        return cls1, cls2, cls3

    # ---------- 신호 도달성(초집합 방향 그래프) ----------
    def reach(self, acg, excite_nets):
        adj = defaultdict(set)
        for x in self.dev:
            g, dn, s = x["gate"], x["drain"], x["source"]
            adj[g].add(dn); adj[g].add(s)
            adj[s].add(dn); adj[dn].add(s)
        for x in self.pas:
            t = x.get("terminals") or []
            if len(t) == 2:
                adj[t[0]].add(t[1]); adj[t[1]].add(t[0])
        # 이상 전류원은 AC에서 개방으로 둔다(계획서에 명시 없음 -- 가정 표시)
        seen = set()
        stack = [n for n in excite_nets if n not in acg]
        seen |= set(stack)
        while stack:
            u = stack.pop()
            for v in adj[u]:
                if v in acg or v in seen:
                    continue
                seen.add(v); stack.append(v)
        return seen

    # ---------- D. 셀 분류 ----------
    def cells(self, acg, reach):
        """N3.2-3 셀 우선순위를 그대로 구현.

        'source 노드가 다른 신호 셀의 입력 단자나 출력 포트에 닿을 때' 이중 출력
        review_needed, 닿지 않으면 CS(degeneration).
        '다른 신호 셀의 입력 단자'는 (gate가 신호를 받는 소자의 gate 넷) ∪
        (gate 밖 소자의 source 넷: CG 후보의 입력 단자) ∪ 출력 포트로 근사했다.
        """
        gate_sig_nets, outside_src_nets = set(), set()
        for x in self.dev:
            g = x["gate"]
            if (g in reach) and (g not in acg):
                gate_sig_nets.add(g)
            else:
                if x["source"] in reach and x["source"] not in acg:
                    outside_src_nets.add(x["source"])
        outports = {n for n, v in self.ports.items() if "output" in (v.get("role") or "")}
        touch = gate_sig_nets | outside_src_nets | outports

        out = {}
        for x in self.dev:
            nm, g, dn, s = x["name"], x["gate"], x["drain"], x["source"]
            g_sig = (g in reach) and (g not in acg)
            if g_sig:
                if dn in acg:
                    out[nm] = ("CD", s)
                elif s in acg:
                    out[nm] = ("CS", dn)
                elif s in touch:
                    out[nm] = ("CS_CD_dual_review", None)   # `기록만` -> DEC-59 정지
                else:
                    out[nm] = ("CS", dn)                    # degeneration
            else:
                sd_in = (s in reach) and (s not in acg)
                dd_in = (dn in reach) and (dn not in acg)
                if sd_in and dd_in:
                    out[nm] = ("CG_or_pass", dn)            # 2차 통과에서 가른다
                elif sd_in or dd_in:
                    out[nm] = ("load_or_bias", None)
                else:
                    out[nm] = ("offpath", None)

        # 2차 통과: CG(=source가 전류 구동) / pass 가르기
        curr_nodes = set()
        for x in self.dev:
            if out[x["name"]][0] in ("CS", "CG_or_pass"):
                curr_nodes.add(x["drain"])
        for x in self.dev:
            nm, s, dn = x["name"], x["source"], x["drain"]
            if out[nm][0] != "CG_or_pass":
                continue
            if s in curr_nodes:
                out[nm] = ("CG", dn)
            else:
                out[nm] = ("pass", dn)
        return out

    # ---------- E. 노드 구동 종류 ----------
    def driving(self, acg, reach, cells):
        volt, curr, resdep = set(), set(), set()
        for x in self.dev:
            nm, dn, s = x["name"], x["drain"], x["source"]
            c = cells[nm][0]
            if c == "CD":
                volt.add(s)
            elif c in ("CS", "CG"):
                curr.add(dn)
        for pn, pv in self.ports.items():
            if "input" in (pv.get("role") or ""):
                volt.add(pn)
        for x in self.pas:
            if x.get("kind") == "resistor":
                t = x.get("terminals") or []
                for n in t:
                    if n in reach and n not in acg:
                        resdep.add(n)
        live = {n for n in reach if n not in acg}
        return (volt & live), (curr & live), (resdep & live)

    # ---------- F. follower 묶음 (DEC-63) ----------
    def follower_bundles(self, acg, reach, cells):
        cd = [(x["name"], x["gate"], x["source"]) for x in self.dev
              if cells[x["name"]][0] == "CD"]
        if not cd:
            return []
        # u = 전압 구동 넷(입력 포트 또는 이득 블록 출력노드) 후보 = CD gate 중 CD source가 아닌 것
        cd_src = {s for _, _, s in cd}
        starts = sorted({g for _, g, _ in cd if g not in cd_src})
        bundles = []
        for u in starts:
            R, frontier, used = set(), [u], []
            while frontier:
                n = frontier.pop()
                for nm, g, s in cd:
                    if g == n and nm not in used:
                        used.append(nm)
                        if s not in R:
                            R.add(s); frontier.append(s)
            sinks = sorted(n for n in R if not any(g == n for _, g, _ in cd))
            bundles.append({"u": u, "R": sorted(R), "devices": sorted(used),
                            "sinks": sinks,
                            "class": "계산규칙있음" if len(sinks) == 1 else "기록만(다출력)"})
        return bundles

    # ---------- G. G_vgs 사이클 (DEC-64) ----------
    def gvgs_cycles(self, rails):
        RAIL = "<RAIL>"
        def rn(n):
            return RAIL if n in rails else n
        edges = []  # (u, v, devname)
        for x in self.dev:
            edges.append((rn(x["gate"]), rn(x["source"]), x["name"]))
        # 스패닝 포리스트
        parent, rank = {}, {}
        def find(a):
            parent.setdefault(a, a)
            while parent[a] != a:
                parent[a] = parent[parent[a]]; a = parent[a]
            return a
        def union(a, b):
            ra, rb = find(a), find(b)
            if ra == rb:
                return False
            parent[ra] = rb
            return True
        tree, nontree = [], []
        for e in edges:
            u, v, nm = e
            if u == v:
                nontree.append(e)   # 자기 루프(gate==source, 있으면 비정상)
                continue
            if union(u, v):
                tree.append(e)
            else:
                nontree.append(e)
        # 트리 인접
        adj = defaultdict(list)
        for u, v, nm in tree:
            adj[u].append((v, nm)); adj[v].append((u, nm))
        def tree_path(a, b):
            if a == b:
                return []
            prev = {a: None}
            st = [a]
            while st:
                u = st.pop()
                if u == b:
                    break
                for v, nm in adj[u]:
                    if v not in prev:
                        prev[v] = (u, nm); st.append(v)
            if b not in prev:
                return None
            out, cur = [], b
            while prev[cur] is not None:
                u, nm = prev[cur]
                out.append((nm, cur, u)); cur = u
            return out
        inport = {n for n, v in self.ports.items() if "input" in (v.get("role") or "")}
        res = {"v0": [], "v1": [], "v2": [], "selfloop": []}
        for u, v, nm in nontree:
            if u == v:
                res["selfloop"].append([nm]); continue
            path = tree_path(u, v)
            if path is None:
                continue
            members = sorted({nm} | {p[0] for p in path})
            nodes = {u, v} | {p[1] for p in path} | {p[2] for p in path}
            # v0: 같은 (gate, source) 평행 엣지
            parallel = False
            for tu, tv, tnm in tree:
                if {tu, tv} == {u, v} and len(path) == 1:
                    parallel = True
            if parallel:
                res["v0"].append(members)
            elif len({n for n in nodes if n in inport}) >= 2:
                res["v1"].append(members)
            else:
                res["v2"].append({"members": members, "via_rail": RAIL in nodes})
        return res

    def vds1_cycles(self, rails):
        """G_vgs + VDS 엣지에서 VDS 엣지를 정확히 하나 포함하는 기본 사이클 수(근사 계수)."""
        RAIL = "<RAIL>"
        def rn(n):
            return RAIL if n in rails else n
        nodes = set()
        eg, ed = [], []
        for x in self.dev:
            g, s, dn = rn(x["gate"]), rn(x["source"]), rn(x["drain"])
            nodes |= {g, s, dn}
            eg.append((g, s, "VGS:" + x["name"]))
            ed.append((dn, s, "VDS:" + x["name"]))
        # 총 사이클 차원과 VGS만의 사이클 차원의 차 = VDS 엣지를 포함하는 독립 사이클 수
        def cyc_dim(edges):
            parent = {}
            def find(a):
                parent.setdefault(a, a)
                while parent[a] != a:
                    parent[a] = parent[parent[a]]; a = parent[a]
                return a
            c = 0
            for u, v, _ in edges:
                ru, rv = find(u), find(v)
                if ru == rv:
                    c += 1
                else:
                    parent[ru] = rv
            return c
        return {"cyc_dim_vgs_only": cyc_dim(eg),
                "cyc_dim_vgs_plus_vds": cyc_dim(eg + ed),
                "vds_bearing_independent_cycles": cyc_dim(eg + ed) - cyc_dim(eg)}

    # ---------- H. K8 측면 주입 ----------
    def k8(self, acg, reach, cells):
        cd = [(x["name"], x["gate"], x["source"]) for x in self.dev if cells[x["name"]][0] == "CD"]
        cd_src = {s for _, _, s in cd}
        hits = []
        for x in self.dev:
            nm = x["name"]
            if cells[nm][0] != "CS":
                continue
            k = x["drain"]
            if k not in cd_src:
                continue
            # DC 역할이 바이어스 전류원인가: gate 넷이 다른 소자의 diode/미러 기준 넷인가로 근사
            hits.append({"cell": nm, "gate": x["gate"], "k": k})
        return hits

    # ---------- I. 병렬 셀(같은 노드 합류) ----------
    def parallel_merge(self, acg, reach, cells):
        bym = defaultdict(list)
        for x in self.dev:
            c, outn = cells[x["name"]]
            if c in ("CS", "CD") and outn is not None:
                bym[outn].append((x["name"], c, x["gate"]))
        return {k: v for k, v in bym.items() if len(v) >= 2}

    # ---------- J. DC 전도 그래프 ----------
    def dc_graph(self, rails):
        edges = []  # (u, v, label, kind)
        for x in self.dev:
            edges.append((x["drain"], x["source"], x["name"], "mos"))
        for x in self.pas:
            if x.get("kind") == "resistor":
                t = x.get("terminals") or []
                if len(t) == 2:
                    edges.append((t[0], t[1], x["name"], "res"))
        for x in self.isrc:
            t = x.get("terminals") or []
            if len(t) == 2:
                edges.append((t[0], t[1], x["name"], "isrc"))
        return edges

    def prune_leaf_resistors(self, edges, rails):
        keep = list(edges)
        pruned = []
        changed = True
        while changed:
            changed = False
            deg = defaultdict(list)
            for i, (u, v, nm, k) in enumerate(keep):
                deg[u].append(i); deg[v].append(i)
            for n, idxs in list(deg.items()):
                if n in rails or n in self.ports:
                    continue
                if len(idxs) == 1 and keep[idxs[0]][3] == "res":
                    pruned.append(keep[idxs[0]][2])
                    keep.pop(idxs[0])
                    changed = True
                    break
        return keep, pruned

    def branches_columns(self, edges, rails):
        deg = defaultdict(int)
        for u, v, nm, k in edges:
            deg[u] += 1; deg[v] += 1
        junction = {n for n in deg if deg[n] >= 3} | set(rails)
        junction &= set(deg)
        # 가지: junction 사이의 극대 직렬 사슬
        adj = defaultdict(list)
        for i, (u, v, nm, k) in enumerate(edges):
            adj[u].append((v, i)); adj[v].append((u, i))
        used = set()
        branches = []
        for j in sorted(junction):
            for (nb, ei) in adj[j]:
                if ei in used:
                    continue
                chain = [edges[ei][2]]
                used.add(ei)
                prev, cur = j, nb
                while cur not in junction:
                    nxt = [(w, e2) for (w, e2) in adj[cur] if e2 != ei and e2 not in used]
                    if len(nxt) != 1:
                        break
                    w, e2 = nxt[0]
                    chain.append(edges[e2][2]); used.add(e2); ei = e2
                    prev, cur = cur, w
                branches.append({"a": j, "b": cur, "devices": chain})
        # 기둥: 하단 레일 -> 상단 레일 단순 경로(가지 그래프)
        badj = defaultdict(list)
        for i, b in enumerate(branches):
            badj[b["a"]].append((b["b"], i)); badj[b["b"]].append((b["a"], i))
        lo = sorted(n for n in rails if n in ("gnd", "GND", "vss", "VSS"))
        hi = sorted(n for n in rails if n in ("vdd", "VDD"))
        paths = []
        overflow = False
        if lo and hi:
            start, goal = lo[0], set(hi)
            def dfs(node, visited_nodes, used_b):
                nonlocal overflow
                if len(paths) > PATH_LIMIT:
                    overflow = True; return
                if node in goal and used_b:
                    paths.append(tuple(used_b)); return
                for (w, bi) in badj[node]:
                    if bi in used_b or w in visited_nodes:
                        continue
                    dfs(w, visited_nodes | {w}, used_b + [bi])
            dfs(start, {start}, [])
        return branches, junction, paths, overflow

    # ---------- K. 출력 방향 분류 (DEC-65) ----------
    def output_class(self, acg, reach, cells):
        outp = [n for n, v in self.ports.items() if "output" in (v.get("role") or "")]
        res = {}
        for k in outp:
            sigma, beta, other = [], [], []
            for x in self.dev:
                if k not in (x["drain"], x["source"]):
                    continue
                c = cells[x["name"]][0]
                if c in ("CS", "CD", "CG", "CS_CD_dual_review"):
                    sigma.append(x["name"] + ":" + c)
                elif c in ("load_or_bias", "offpath"):
                    beta.append(x["name"])
                else:
                    other.append(x["name"] + ":" + c)
            if len(sigma) >= 2 and not beta:
                cl = "push-pull(두 방향 sigma)"
            elif sigma and beta:
                cl = "class-A(한 방향만 sigma)"
            elif sigma and not beta and len(sigma) == 1:
                cl = "확인못함(sigma 1개, 반대방향 소자 없음)"
            else:
                cl = "확인못함"
            res[k] = {"sigma": sigma, "beta": beta, "other": other, "class": cl}
        return res

    # ---------- L2. 루프 분류 (0)~(4) ----------
    def loop_classify(self, acg, reach, excite, cells):
        """N3.2-2의 기본 폐경로를 모아 (0)~(4)로 분류(근사).

        엣지: MOS g->d, g->s, 그리고 source 노드가 전류 구동인 소자의 s->d, 수동소자 양방향.
        교류접지 집합과 여기 포트 넷은 제거한다.
        무향 스패닝 트리의 비트리 엣지마다 기본 사이클 하나를 만들어 분류한다.
        """
        removed = set(acg) | set(excite)
        curr_nodes = set()
        for x in self.dev:
            if cells.get(x["name"], ("",))[0] in ("CS", "CG"):
                curr_nodes.add(x["drain"])
        edges = []  # (u, v, label, kind) kind in {act, pas_c, pas_r}
        for x in self.dev:
            g, dn, s = x["gate"], x["drain"], x["source"]
            for a, b in ((g, dn), (g, s)):
                if a not in removed and b not in removed:
                    edges.append((a, b, x["name"], "act"))
            if s in curr_nodes and s not in removed and dn not in removed:
                edges.append((s, dn, x["name"], "act"))
        for x in self.pas:
            t = x.get("terminals") or []
            if len(t) == 2 and t[0] not in removed and t[1] not in removed:
                edges.append((t[0], t[1], x["name"],
                              "pas_c" if x.get("kind") == "capacitor" else "pas_r"))
        # 순방향 소자 집합 근사: 여기에서 도달 가능하고 출력 포트로 도달 가능한 소자
        outports = {n for n, v in self.ports.items() if "output" in (v.get("role") or "")}
        fwd_adj = defaultdict(set)
        rev_adj = defaultdict(set)
        for u, v, nm, k in edges:
            fwd_adj[u].add((v, nm))
            rev_adj[v].add((u, nm))
            if k.startswith("pas"):
                fwd_adj[v].add((u, nm)); rev_adj[u].add((v, nm))
        def bfs(adj, seeds):
            seen = set(seeds); st = list(seeds)
            while st:
                u = st.pop()
                for v, _ in adj[u]:
                    if v not in seen:
                        seen.add(v); st.append(v)
            return seen
        src_seed = [n for x in self.dev for n in (x["gate"],)
                    if n in reach and n not in removed]
        from_in = bfs(fwd_adj, [n for n in reach if n not in removed])
        to_out = bfs(rev_adj, [n for n in outports if n not in removed])
        fwd_dev = set()
        for u, v, nm, k in edges:
            if k == "act" and u in from_in and v in to_out:
                fwd_dev.add(nm)
        # 스패닝 트리
        parent = {}
        def find(a):
            parent.setdefault(a, a)
            while parent[a] != a:
                parent[a] = parent[parent[a]]; a = parent[a]
            return a
        tree, nontree = [], []
        seen_pair = set()
        for e in edges:
            u, v, nm, k = e
            if u == v:
                continue
            ru, rv = find(u), find(v)
            if ru == rv:
                nontree.append(e)
            else:
                parent[ru] = rv; tree.append(e)
        adj = defaultdict(list)
        for u, v, nm, k in tree:
            adj[u].append((v, nm, k)); adj[v].append((u, nm, k))
        def tpath(a, b):
            prev = {a: None}; st = [a]
            while st:
                u = st.pop()
                if u == b:
                    break
                for v, nm, k in adj[u]:
                    if v not in prev:
                        prev[v] = (u, nm, k); st.append(v)
            if b not in prev:
                return None
            out, cur = [], b
            while prev[cur] is not None:
                u, nm, k = prev[cur]
                out.append((nm, k)); cur = u
            return out
        res = {"(2)Miller형_수동복귀": [], "(3)루프뷰_순방향밖능동": [],
               "(4)기록만_정지": [], "총_기본폐경로": 0}
        for u, v, nm, k in nontree:
            p = tpath(u, v)
            if p is None:
                continue
            res["총_기본폐경로"] += 1
            members = [(nm, k)] + p
            kinds = [kk for _, kk in members]
            devs = [dd for dd, kk in members if kk == "act"]
            n_act = sum(1 for kk in kinds if kk == "act")
            n_cap = sum(1 for kk in kinds if kk == "pas_c")
            n_res = sum(1 for kk in kinds if kk == "pas_r")
            outside = [d for d in devs if d not in fwd_dev]
            if n_cap >= 1 and n_act == 0:
                res["(2)Miller형_수동복귀"].append(sorted(set(devs)) or ["passive-only"])
            elif n_cap >= 1 and n_act >= 1 and not outside:
                # 커패시터 복귀 경로 + 순방향 능동 셀 -> Miller형 후보
                res["(2)Miller형_수동복귀"].append(sorted(set(devs)))
            elif outside:
                res["(3)루프뷰_순방향밖능동"].append(sorted(set(outside)))
            else:
                res["(4)기록만_정지"].append(sorted(set(devs))[:6])
        return res

    # ---------- L. 신호 루프(근사) ----------
    def signal_loops(self, acg, reach, excite):
        """N3.2-2 루프 탐지 그래프의 사이클 차원과 SCC로 근사 계수."""
        removed = set(acg) | set(excite)
        nodes = {n for n in self.nets if n not in removed}
        und = set()
        directed = defaultdict(set)
        for x in self.dev:
            g, dn, s = x["gate"], x["drain"], x["source"]
            for a, b in ((g, dn), (g, s), (s, dn)):
                if a in nodes and b in nodes:
                    directed[a].add(b); und.add(frozenset((a, b)))
        pas_edges = set()
        for x in self.pas:
            t = x.get("terminals") or []
            if len(t) == 2 and t[0] in nodes and t[1] in nodes:
                directed[t[0]].add(t[1]); directed[t[1]].add(t[0])
                und.add(frozenset(t)); pas_edges.add(frozenset(t))
        # 무향 사이클 차원
        parent = {}
        def find(a):
            parent.setdefault(a, a)
            while parent[a] != a:
                parent[a] = parent[parent[a]]; a = parent[a]
            return a
        cyc = 0
        for e in und:
            t = tuple(e)
            if len(t) < 2:
                continue
            a, b = t
            ra, rb = find(a), find(b)
            if ra == rb:
                cyc += 1
            else:
                parent[ra] = rb
        # 방향 SCC (Tarjan 반복)
        index, low, onstk, stk, idx = {}, {}, set(), [], [0]
        sccs = []
        for root in sorted(nodes):
            if root in index:
                continue
            work = [(root, iter(sorted(directed[root])))]
            index[root] = low[root] = idx[0]; idx[0] += 1
            stk.append(root); onstk.add(root)
            while work:
                v, it = work[-1]
                adv = False
                for w in it:
                    if w not in index:
                        index[w] = low[w] = idx[0]; idx[0] += 1
                        stk.append(w); onstk.add(w)
                        work.append((w, iter(sorted(directed[w]))))
                        adv = True
                        break
                    elif w in onstk:
                        low[v] = min(low[v], index[w])
                if adv:
                    continue
                work.pop()
                if work:
                    low[work[-1][0]] = min(low[work[-1][0]], low[v])
                if low[v] == index[v]:
                    comp = []
                    while True:
                        w = stk.pop(); onstk.discard(w); comp.append(w)
                        if w == v:
                            break
                    if len(comp) > 1:
                        sccs.append(sorted(comp))
        return {"undirected_cycle_dim": cyc, "nontrivial_sccs": sccs,
                "passive_edges_in_graph": len(pas_edges)}


def main():
    files = sorted(f for f in os.listdir(LIB)
                   if f.endswith(".topology.json") and not f.startswith("_"))
    with open(OUT, "w", encoding="utf-8") as fh:
        emit(fh, "# review7 규칙 분기 발동 측정 (plan v5.12 / 69b151f)")
        emit(fh, "# library 회로:", len(files))
        for f in files:
            d = load(f)
            c = Ckt(f, d)
            emit(fh, "")
            emit(fh, "=" * 78)
            emit(fh, "CIRCUIT", c.name, "| file", f, "| MOS", len(c.dev),
                 "| passive", len(c.pas), "| ideal_src", len(c.isrc))

            # A
            r_ns = c.rails(False)
            r_ex = c.rails(True)
            emit(fh, "[A 레일] supply_nets 선언:", c.supply_nets,
                 "| 이름집합 판정:", sorted(r_ns),
                 "| agnd류 넷:", sorted(c.extra_rail_nets()),
                 "| 이름집합이 놓치는 레일:", sorted(r_ex - r_ns))
            rails = r_ex  # 이후 계산은 agnd를 레일로 본 해석(사람 판독)으로 한다
            emit(fh, "[A2] 이후 계산에 쓴 레일 집합:", sorted(rails))

            # B
            inport = sorted(n for n, v in c.ports.items() if "input" in (v.get("role") or ""))
            outport = sorted(n for n, v in c.ports.items() if "output" in (v.get("role") or ""))
            emit(fh, "[B 기본 전달 뷰] input ports:", inport, "| output ports:", outport,
                 "| 가능:", bool(inport and outport))
            if not inport:
                emit(fh, "[B!] ports 선언 없음 -> N3.2-2 기본 전달 뷰 구성 불가 -> "
                         "SP1·셀·구동종류·루프·K8·DEC-63·DEC-65 전부 발동 0(측정 불가). U-08 대기")
                # 그래도 DC 쪽(G_vgs, 가지·기둥, 저항)은 잰다
                acg = (rails, set(), set())
                acgall = rails
                cells = {}
            else:
                cls1, cls2, cls3 = c.ac_ground(rails)
                acgall = cls1 | cls2 | cls3
                emit(fh, "[C 교류접지] (1)레일", sorted(cls1), "| (2)gate전용 미구동",
                     sorted(cls2), "| (3)이상전압원", sorted(cls3))
                reach = c.reach(acgall, inport)
                emit(fh, "[C2] 신호 도달 넷 수:", len(reach), "/", len(c.nets))
                cells = c.cells(acgall, reach)
                tally = defaultdict(list)
                for nm, (cl, _) in sorted(cells.items()):
                    tally[cl].append(nm)
                emit(fh, "[D 셀 분류]", {k: len(v) for k, v in sorted(tally.items())})
                for k in sorted(tally):
                    emit(fh, "    ", k, "=", tally[k])
                volt, curr, resdep = c.driving(acgall, reach, cells)
                emit(fh, "[E 구동 종류] 전압:", sorted(volt), "| 전류:", sorted(curr),
                     "| 값의존(저항 접속):", sorted(resdep),
                     "| 혼재(전압&전류):", sorted(volt & curr))
                b = c.follower_bundles(acgall, reach, cells)
                emit(fh, "[F DEC-63 follower 묶음] 개수:", len(b))
                for x in b:
                    emit(fh, "    ", x)
                h = c.k8(acgall, reach, cells)
                emit(fh, "[H K8 측면 주입 후보] 개수:", len(h), h)
                pm = c.parallel_merge(acgall, reach, cells)
                emit(fh, "[I 병렬 셀 합류 노드] 개수:", len(pm))
                for k, v in sorted(pm.items()):
                    emit(fh, "    ", k, "<-", v)
                oc = c.output_class(acgall, reach, cells)
                emit(fh, "[K DEC-65 출력 방향 분류]")
                for k, v in sorted(oc.items()):
                    emit(fh, "    ", k, v)
                sl = c.signal_loops(acgall, reach, inport)
                emit(fh, "[L 신호 루프(근사)] 무향 사이클 차원:", sl["undirected_cycle_dim"],
                     "| 비자명 SCC 수:", len(sl["nontrivial_sccs"]),
                     "| 그래프 내 수동 엣지:", sl["passive_edges_in_graph"])
                for s in sl["nontrivial_sccs"]:
                    emit(fh, "     SCC:", s)
                lc = c.loop_classify(acgall, reach, inport, cells)
                emit(fh, "[L2 루프 분류 (0)~(4)] 총 기본폐경로:", lc["총_기본폐경로"],
                     "| (2)Miller형:", len(lc["(2)Miller형_수동복귀"]),
                     "| (3)루프뷰:", len(lc["(3)루프뷰_순방향밖능동"]),
                     "| (4)기록만->DEC-59 정지:", len(lc["(4)기록만_정지"]))
                for kk in ("(2)Miller형_수동복귀", "(3)루프뷰_순방향밖능동", "(4)기록만_정지"):
                    for x in lc[kk][:12]:
                        emit(fh, "      ", kk, x)

            # G
            g = c.gvgs_cycles(rails)
            emit(fh, "[G DEC-64 G_vgs 사이클] v0(equal_vgs):", len(g["v0"]),
                 "| v1(포트 차):", len(g["v1"]), "| v2(kvl_branch):", len(g["v2"]),
                 "| self:", len(g["selfloop"]))
            for x in g["v1"]:
                emit(fh, "     v1:", x)
            for x in g["v2"]:
                emit(fh, "     v2:", x)
            emit(fh, "[G2 VDS-1 후보]", c.vds1_cycles(rails))

            # J
            edges = c.dc_graph(rails)
            kept, pruned = c.prune_leaf_resistors(edges, rails)
            all_res = [x["name"] for x in c.pas if x.get("kind") == "resistor"]
            emit(fh, "[J1 DEC-70 저항 판정] 전체 저항:", all_res,
                 "| 잎 가지치기로 잘림(파생값):", pruned,
                 "| 남음(theta):", [n for n in all_res if n not in pruned])
            br, junc, paths, ovf = c.branches_columns(kept, rails)
            emit(fh, "[J2 DEC-71 가지·기둥] 분기/레일 노드:", len(junc), sorted(junc))
            emit(fh, "     가지 수:", len(br))
            for x in br:
                emit(fh, "        ", x["a"], "--", x["b"], x["devices"])
            emit(fh, "     기둥(하단레일->상단레일 단순경로) 수:", len(paths),
                 "| 열거 상한 초과:", ovf)
            emit(fh, "     손선언 vertical_stack_id 개수:", len(c.declared_stack),
                 "| 서로 다른 값:", len(set(c.declared_stack.values())))
        emit(fh, "")
        emit(fh, "# end")


if __name__ == "__main__":
    main()
