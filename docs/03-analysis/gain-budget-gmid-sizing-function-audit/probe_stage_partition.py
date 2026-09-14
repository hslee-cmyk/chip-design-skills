# -*- coding: utf-8 -*-
"""probe_stage_partition.py -- graph 기반 stage 분할 실측(저장소 무수정, scratchpad 전용).

재사용(import, 저장소 기존 함수):
  sizing_recipe._load_full_topology_cached  (topology+meta+passive+ports 로딩, 정본)
  sizing_recipe.is_diode_connected          (diode 정본)
  sizing_recipe.true_current_mirror_groups  (미러 정본, 교차확인용)
  sizing_recipe.gain_stage_tails            (선언 기반 tail, 대조용)
  sizing_recipe.signal_path_nodes           (gate/source->drain 신호경로, 대조용)
  sizing_recipe._DEFAULT_RAIL_HI/_LO, stick_diagram._RAIL_NETS (레일 집합)
  stick_diagram.find_differential_pair_candidates (connectivity diffpair, tail 대조용)
  stick_diagram.find_structural_symmetry_candidates (R3 차동/공통모드 net 대응)
  stick_diagram.trace_vdd_to_gnd_branches   (branch 수 교차확인)
신규(이 스크립트에만, [신규] 표시): 신호 엣지 그래프, 교류접지 규칙, 0-1 BFS stage index,
  SCC/응축 최장경로, DFS 피드백 엣지+극성, 모드 뷰(부호 있는 net 병합), R1/R2 역할 분류,
  수동소자 대칭 확장, 선언 stage 파서, 출력노드 gds 기여자/ro 부스트 사슬.
"""
import sys, os, re, json
from collections import defaultdict, deque

ASSETS = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets"
sys.path.insert(0, ASSETS)
import stick_diagram as sd      # noqa: E402
import sizing_recipe as sr      # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "probe_stage_partition.result.md")
CIRCUITS = ["current_reuse_telescopic_ota", "folded_cascode", "two_stage_ota", "nmcnr_amplifier"]
RAILS = set(sr._DEFAULT_RAIL_HI) | set(sr._DEFAULT_RAIL_LO) | set(sd._RAIL_NETS)
SUMMARY = []


def emit(lines):
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------- [신규] 그래프 유틸
def tarjan(nodes, adj):
    idx, low, on, st, comps, counter = {}, {}, set(), [], [], [0]
    for root in sorted(nodes):
        if root in idx:
            continue
        work = [(root, iter(sorted(adj.get(root, ()))))]
        idx[root] = low[root] = counter[0]; counter[0] += 1; st.append(root); on.add(root)
        while work:
            v, it = work[-1]
            nxt = next(it, None)
            if nxt is not None:
                if nxt not in nodes:
                    continue
                if nxt not in idx:
                    idx[nxt] = low[nxt] = counter[0]; counter[0] += 1; st.append(nxt); on.add(nxt)
                    work.append((nxt, iter(sorted(adj.get(nxt, ())))))
                elif nxt in on:
                    low[v] = min(low[v], idx[nxt])
            else:
                work.pop()
                if work:
                    low[work[-1][0]] = min(low[work[-1][0]], low[v])
                if low[v] == idx[v]:
                    comp = []
                    while True:
                        x = st.pop(); on.discard(x); comp.append(x)
                        if x == v:
                            break
                    comps.append(sorted(comp))
    return comps


def zero_one_bfs(sources, edges):
    adj = defaultdict(list)
    for e in edges:
        adj[e["u"]].append((e["v"], e["w"]))
    dist = {s: 0 for s in sources}
    dq = deque(sources)
    while dq:
        u = dq.popleft()
        for v, w in adj[u]:
            nd = dist[u] + w
            if v not in dist or nd < dist[v]:
                dist[v] = nd
                (dq.appendleft if w == 0 else dq.append)(v)
    return dist


def longest_index(sources, edges, reach):
    adj = defaultdict(set)
    for e in edges:
        if e["u"] in reach and e["v"] in reach:
            adj[e["u"]].add(e["v"])
    comps = tarjan(set(reach), adj)
    cid = {n: i for i, c in enumerate(comps) for n in c}
    pos_cycle = set()
    dag = defaultdict(dict)
    indeg = defaultdict(int)
    for e in edges:
        if e["u"] not in reach or e["v"] not in reach:
            continue
        a, b = cid[e["u"]], cid[e["v"]]
        if a == b:
            if e["w"] > 0:
                pos_cycle.add(a)
            continue
        if b not in dag[a] or dag[a][b] < e["w"]:
            if b not in dag[a]:
                indeg[b] += 1
            dag[a][b] = max(dag[a].get(b, 0), e["w"])
    best = {i: (0 if any(n in sources for n in comps[i]) else None) for i in range(len(comps))}
    q = deque(i for i in range(len(comps)) if indeg[i] == 0)
    while q:
        a = q.popleft()
        for b, w in dag[a].items():
            if best[a] is not None:
                cand = best[a] + w
                if best[b] is None or cand > best[b]:
                    best[b] = cand
            indeg[b] -= 1
            if indeg[b] == 0:
                q.append(b)
    return {n: best[cid[n]] for n in reach}, [c for c in comps if len(c) > 1], \
        [comps[i] for i in pos_cycle]


def passive_loop_polarity(mos, pas, no_gs=False):
    """수동소자 u->v가 닫는 루프의 부호 [신규]: v에서 u로 돌아오는 경로의 부호 집합(상태=(노드,부호)
    BFS) x 수동소자 부호. 경로 그래프 = MOS 엣지(+no_gs면 gs 제외) + **다른** 수동소자 엣지
    (Cc-Rz 직렬처럼 수동 전용 중간노드를 지나는 루프를 잡기 위해). 부호 둘 다 나오면 모호."""
    out, seen_pairs = [], set()
    for p in pas:
        key = (p["dev"], p["u"], p["v"])
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        adj = defaultdict(list)
        for e in mos:
            if not (no_gs and e["kind"] == "gs"):
                adj[e["u"]].append((e["v"], e["sign"], False))
        for e in pas:
            if e["dev"] != p["dev"]:
                adj[e["u"]].append((e["v"], e["sign"], True))
        start, goal = p["v"], p["u"]
        seen = {(start, 1, False)}
        q = deque([(start, 1, False)])
        signs_m, signs_p = set(), set()
        while q:
            n, s, used = q.popleft()
            if n == goal:
                (signs_p if used else signs_m).add(s * p["sign"])
                continue
            for v, sg, isp in adj[n]:
                st = (v, s * sg, used or isp)
                if st not in seen:
                    seen.add(st); q.append(st)
        if signs_m or signs_p:
            out.append((p["dev"], p["u"], p["v"], sorted(signs_m), sorted(signs_p)))
    return out


def feedback_edges(sources, edges):
    """DFS(입력에서) back edge + 사이클 부호곱 [신규]."""
    adj = defaultdict(list)
    for e in edges:
        adj[e["u"]].append(e)
    for k in adj:
        adj[k].sort(key=lambda e: (e["v"], e["dev"]))
    visited, out = set(), []
    for s in sorted(sources):
        if s in visited:
            continue
        visited.add(s)
        stack = [(s, iter(adj[s]), 1)]
        pos = {s: 0}
        while stack:
            u, it, _ = stack[-1]
            e = next(it, None)
            if e is None:
                stack.pop(); pos.pop(u, None)
                continue
            v = e["v"]
            if v in pos:
                p = pos[v]
                sign = e["sign"]
                for (_n, _i, sg) in stack[p + 1:]:
                    sign *= sg
                cyc = [x[0] for x in stack[p:]]
                out.append({"edge": e, "cycle": cyc, "sign": sign})
            elif v not in visited:
                visited.add(v)
                pos[v] = len(stack)
                stack.append((v, iter(adj[v]), e["sign"]))
    return out


# ---------------------------------------------------------------- 로딩/선언
def load(name):
    path = os.path.join(ASSETS, "library", name + ".topology.json")
    by_name, passives = sr._load_full_topology_cached(path)          # 재사용
    entry = sr._load_full_topology_cached.__dict__["_cache"][path]
    return path, by_name, passives, entry["ports"], entry["ideal_sources"], entry["meta"]


def gain_metrics(meta):
    ms = ((meta.get("sizing_roles") or {}).get("metrics") or {})
    return {k: v for k, v in ms.items() if isinstance(v, dict) and "gain" in str(v.get("type", ""))}


def io_nets(by_name, ports, ideal, meta, passives):
    """입력/출력 넷: ports 선언 우선, 없으면 제안(근거 표시) [신규]."""
    nets_g, nets_sd = defaultdict(list), defaultdict(list)
    for t in by_name.values():
        nets_g[t.gate].append(t.name)
        nets_sd[t.source].append(t.name); nets_sd[t.drain].append(t.name)
    pas_nets = {n for p in passives for n in p.get("terminals", [])}
    src_nets = {n for s in ideal for n in s.get("terminals", [])}
    inp, outp, how = {}, {}, {}
    for n, p in (ports or {}).items():
        if n.startswith("_") or not isinstance(p, dict):
            continue
        (inp if p.get("direction") == "input" else outp)[n] = p.get("role", "")
    how["input"] = "ports 선언" if inp else None
    how["output"] = "ports 선언" if outp else None
    gm = gain_metrics(meta)
    if not inp:
        exc = set()
        for m in gm.values():
            exc |= {k for k, v in (m.get("excite") or {}).items() if v}
        if exc:
            inp = {n: "" for n in sorted(exc)}; how["input"] = "제안: gain metric excite(0 아닌 값)"
        else:
            cand = [n for n in nets_g if n not in nets_sd and n not in RAILS and n not in pas_nets
                    and n not in src_nets and re.search(r"(?i)in", n)]
            inp = {n: "" for n in sorted(cand)}; how["input"] = "제안: gate-only 비구동 넷 중 이름에 'in'"
    if not outp:
        sen = set()
        for m in gm.values():
            for k in ("sense_p", "sense_n"):
                if m.get(k) and m[k] not in RAILS:
                    sen.add(m[k])
        if sen:
            outp = {n: "" for n in sorted(sen)}; how["output"] = "제안: gain metric sense_p/n"
        else:
            sink = [n for n in nets_sd if n not in RAILS and n not in nets_g
                    and all(by_name[d].drain == n for d in nets_sd[n])]
            outp = {n: "" for n in sorted(sink)}; how["output"] = "제안: drain 전용·게이트 미구동 넷(sink)"
    # p/n 짝
    def pair(d):
        pr = {}
        for n, role in d.items():
            m = re.search(r"_(p|n)$", role) or re.search(r"(?i)[_]?(p|n)$", n)
            if m:
                pr.setdefault(m.group(1).lower(), n)
        return (pr["p"], pr["n"]) if "p" in pr and "n" in pr else None
    return inp, outp, how, pair(inp), pair(outp), nets_g, nets_sd, pas_nets, src_nets


def ac_ground_full(by_name, inp, nets_g, nets_sd, pas_nets, ideal):
    """교류접지 규칙 [신규]: G1 레일, G2 gate-only 비구동 넷(입력 아님, 수동소자/이상원 단자 아님),
    G3 이상 전압원 단자. 이상 전류원 단자는 교류접지 아님(무한 임피던스)."""
    g1 = {n for n in set(nets_g) | set(nets_sd) if n in RAILS}
    src_nets = {n for s in ideal for n in s.get("terminals", [])}
    g2 = {n for n in nets_g if n not in nets_sd and n not in inp and n not in RAILS
          and n not in pas_nets and n not in src_nets}
    g3 = {n for s in ideal if s.get("kind") == "voltage_source" for n in s.get("terminals", [])}
    return g1, g2, g3


# ---------------------------------------------------------------- 뷰
class View:
    def __init__(self, name, ground, rep):
        self.name, self.ground, self._rep = name, ground, rep   # rep: net -> (rep, o)

    def r(self, net):
        if net is None or net in self.ground:
            return None
        return self._rep.get(net, (net, 1))


def build_edges(by_name, passives, view, diode_nodes):
    """MOS 신호 엣지(gd:-1,w1 / sd:+1 / gs:+1) + 수동 양방향 [신규]."""
    mos, pas, selfloops, shunts = [], [], [], []
    for n in sorted(by_name):
        t = by_name[n]
        g, d, s = view.r(t.gate), view.r(t.drain), view.r(t.source)
        if sr.is_diode_connected(t):                               # 재사용
            if d:
                selfloops.append((n, t.drain))
        elif g and d:
            mos.append({"u": g[0], "v": d[0], "sign": -1 * g[1] * d[1], "kind": "gd", "dev": n,
                        "w1": 1, "w2": 0 if t.gate in diode_nodes else 1, "rawg": t.gate})
        if s and d and t.source != t.drain:
            mos.append({"u": s[0], "v": d[0], "sign": s[1] * d[1], "kind": "sd", "dev": n, "w1": 0, "w2": 0})
        if g and s and t.gate != t.source:
            mos.append({"u": g[0], "v": s[0], "sign": g[1] * s[1], "kind": "gs", "dev": n, "w1": 0, "w2": 0})
    for p in passives:
        a, b = p["terminals"]
        ra, rb = view.r(a), view.r(b)
        if ra and rb and ra[0] != rb[0]:
            sg = ra[1] * rb[1]
            for u, v in ((ra[0], rb[0]), (rb[0], ra[0])):
                pas.append({"u": u, "v": v, "sign": sg, "kind": "passive", "dev": p["name"], "w1": 0, "w2": 0})
        elif ra and rb:
            selfloops.append((p["name"], a + "~" + b))
        else:
            shunts.append((p["name"], a, b))
    return mos, pas, selfloops, shunts


def mode_views(by_name, passives, full_ground, inpair, outpair, outputs):
    seeds = {r: r for r in RAILS if any(r in (t.source, t.drain, t.gate) for t in by_name.values())}
    if inpair:
        seeds[inpair[0]], seeds[inpair[1]] = inpair[1], inpair[0]
    if outpair:
        seeds[outpair[0]], seeds[outpair[1]] = outpair[1], outpair[0]
    v = sd.find_structural_symmetry_candidates(list(by_name.values()), seeds, "mirror")  # 재사용
    nm = dict(v.net_map)
    # [신규] 수동소자 대칭 확장(같은 kind + 같은 value_from_spec, 한 단자쌍 대응 -> 나머지 단자 대응)
    added = []
    changed = True
    while changed:
        changed = False
        for p in passives:
            for q in passives:
                if p is q or p["kind"] != q["kind"] or p.get("value_from_spec") != q.get("value_from_spec"):
                    continue
                a1, a2 = p["terminals"]; b1, b2 = q["terminals"]
                for (x, y, xo, yo) in ((a1, b1, a2, b2), (a1, b2, a2, b1)):
                    if nm.get(x) == y and xo not in nm and yo not in nm:
                        nm[xo], nm[yo] = yo, xo; added.append((xo, yo, p["name"], q["name"])); changed = True
                    elif nm.get(x) == y and xo not in nm and yo == xo:
                        nm[xo] = xo; added.append((xo, xo, p["name"], q["name"])); changed = True
    single_out = [o for o in outputs if not (outpair and o in outpair)]
    blocked = []
    for o in single_out:                       # [신규] 단일출력은 병합/가상접지 금지
        if o in nm:
            blocked.append((o, nm[o]))
            partner = nm.pop(o)
            if partner != o:
                nm.pop(partner, None)
    selfmap = {n for n, m in nm.items() if n == m and n not in RAILS}
    rep = {}
    for n, m in nm.items():
        if n != m:
            r0 = min(n, m)
            rep[n] = (r0, 1 if n == r0 else -1)
    dm = View("R3-DM", set(full_ground) | selfmap, rep)
    cm = View("R3-CM", set(full_ground), {n: (r0, 1) for n, (r0, _o) in rep.items()})
    return dm, cm, v, added, blocked, selfmap


# ---------------------------------------------------------------- R1/R2 분류
def classify(by_name, view, mos, inputs_rep, outputs_rep, rule_full, diode_nodes):
    rule = rule_full[:2]                      # "R1ng"/"R2ng" = gs(gate->source) 엣지 제외 변형
    wkey = "w1" if rule == "R1" else "w2"
    ed = [dict(e, w=e[wkey]) for e in mos if not (rule_full.endswith("ng") and e["kind"] == "gs")]
    gs_ok = not rule_full.endswith("ng")
    idx = zero_one_bfs(inputs_rep, ed)
    mx, sccs, poscyc = longest_index(set(inputs_rep), ed, set(idx))
    out_edges = defaultdict(list)
    for e in ed:
        out_edges[e["u"]].append(e)
    role, stage = {}, {}
    for n in sorted(by_name):
        t = by_name[n]
        g, d, s = view.r(t.gate), view.r(t.drain), view.r(t.source)
        gi = idx.get(g[0]) if g else None
        di = idx.get(d[0]) if d else None
        si = idx.get(s[0]) if s else None
        _ = gs_ok
        diode = sr.is_diode_connected(t)
        if not diode and gi is not None and di is not None:
            w = 1 if (rule == "R1" or t.gate not in diode_nodes) else 0
            if w == 1 and di == gi + 1:
                role[n], stage[n] = "input", di
            elif w == 1:
                role[n], stage[n] = "gd_nonadvancing", di
            else:
                role[n], stage[n] = "mirror_out", di
        elif not diode and si is not None and di is not None and gi is None:
            role[n], stage[n] = "cascode", di
        elif diode and di is not None:
            role[n], stage[n] = "diode_load", di
        elif di is not None and gi is None and si is None:
            role[n], stage[n] = "load", di
        elif si is not None and di is None:
            role[n], stage[n] = "source_attached", si
        elif gi is not None and di is None and si is None:
            role[n], stage[n] = "gate_only_sense", None
        else:
            role[n], stage[n] = "not_in_signal", None
    # tail: 입력 소자의 비레일 source 넷을 drain으로 갖는 비입력 소자(원 넷 기준)
    in_src = defaultdict(set)
    for n, r in role.items():
        if r == "input" and by_name[n].source not in RAILS:
            in_src[by_name[n].source].add(stage[n])
    for n in sorted(by_name):
        t = by_name[n]
        if role[n] != "input" and t.drain in in_src:
            role[n], stage[n] = "tail", min(in_src[t.drain])
    # stage 0 이지만 tail 아닌 것
    for n in role:
        if stage[n] == 0 and role[n] not in ("tail",):
            role[n] = role[n] + "@idx0"
    # 출력 노드
    outs = defaultdict(list)
    for node, k in idx.items():
        if k < 1:
            continue
        if rule == "R2" and any(view.r(dn) and view.r(dn)[0] == node for dn in diode_nodes):
            continue
        drives = [e for e in out_edges[node] if e["kind"] == "gd" and e["w"] == 1 and idx.get(e["v"]) == k + 1]
        sink = not any(e["kind"] in ("gd", "sd") for e in out_edges[node])
        if drives or node in outputs_rep or sink:
            outs[k].append(node)
    return {"idx": idx, "max": mx, "sccs": sccs, "poscyc": poscyc, "role": role, "stage": stage, "outs": outs}


# ---------------------------------------------------------------- 선언 파서 [신규]
def declared_refs(meta):
    refs = {}
    comp = meta.get("compensation") or {}
    if comp.get("stage_devices"):
        groups = comp["stage_devices"]
        merged = comp.get("shared_gm_id_groups") or []
        gmap, k = {}, 0
        seen = set()
        for grp in merged:
            for gi in grp:
                gmap[gi] = k; seen.add(gi)
            k += 1
        for gi in range(len(groups)):
            if gi not in seen:
                gmap[gi] = k; k += 1
        order = sorted(set(gmap.values()))
        ref = {}
        for gi, devs in enumerate(groups):
            for d in devs:
                ref[d] = order.index(gmap[gi]) + 1
        refs["compensation.stage_devices" + ("+shared_gm_id_groups" if merged else "")] = ref
    for mname, m in gain_metrics(meta).items():
        if m.get("type") == "gain_stages_sum" and m.get("stages"):
            refs[f"metrics.{mname}.stages(gain_stages_sum)"] = {d: i + 1 for i, s in enumerate(m["stages"]) for d in s}
        fields = {k: v for k, v in m.items() if (k.endswith("_device") or k.endswith("_devices")
                                                   or k.startswith("stage") or k.startswith("fold_")
                                                   or k.startswith("cascode_") or k.startswith("mirror_"))}
        if fields and m.get("type") != "gain_stages_sum":
            ref, rl = {}, {}
            for k, v in fields.items():
                mm = re.match(r"gm(\d)_device", k) or re.match(r"stage(\d)_", k)
                st = int(mm.group(1)) if mm else 1
                for d in (v if isinstance(v, list) else [v]):
                    ref.setdefault(d, st); rl.setdefault(d, k)
            refs[f"metrics.{mname}({m.get('type')}) 역할필드"] = ref
            refs[f"metrics.{mname}({m.get('type')}) 역할필드"]["__roles__"] = rl
    return refs


# ---------------------------------------------------------------- 메인
def run_circuit(name):
    L = [f"\n## {name}\n"]
    path, by_name, passives, ports, ideal, meta = load(name)
    inp, outp, how, inpair, outpair, nets_g, nets_sd, pas_nets, src_nets = io_nets(by_name, ports, ideal, meta, passives)
    g1, g2, g3 = ac_ground_full(by_name, inp, nets_g, nets_sd, pas_nets, ideal)
    ground = g1 | g2 | g3
    diode_nodes = {t.drain for t in by_name.values() if sr.is_diode_connected(t)}
    L += [f"- 소자 {len(by_name)}개, 수동소자 {len(passives)}개, ideal_sources {len(ideal)}개, ports 선언 {'있음' if ports else '없음'}",
          f"- 입력 넷: {sorted(inp)} ({how['input']}); p/n 짝={inpair}",
          f"- 출력 넷: {sorted(outp)} ({how['output']}); p/n 짝={outpair}",
          f"- 교류접지 G1(레일): {sorted(g1)}", f"- 교류접지 G2(gate-only 비구동, 입력·수동·이상원 단자 아님): {sorted(g2)}",
          f"- 교류접지 G3(이상 전압원 단자): {sorted(g3)}",
          f"- diode 노드(is_diode_connected drain): {sorted(diode_nodes)}"]
    exc0 = set()
    for m in gain_metrics(meta).values():
        exc0 |= {k for k, v in (m.get("excite") or {}).items() if v == 0}
    if exc0:
        L.append(f"- 대조: gain metric excite=0(선언 교류접지) {sorted(exc0)} / 규칙 G에 없는 것 {sorted(exc0 - ground)}")
    emit(L); L = []

    full = View("full", ground, {})
    dm, cm, sym, sym_added, blocked, selfmap = mode_views(by_name, passives, ground, inpair, outpair, set(outp))
    L += ["\n### 대칭 net 대응 (find_structural_symmetry_candidates, mirror)",
          f"- 자기대응(차동모드 가상접지로 취급): {sorted(selfmap)}",
          f"- 수동소자로 확장한 대응[신규]: {sym_added}",
          f"- 단일출력이라 대응을 제거한 것[신규 규칙]: {blocked}",
          f"- conflicts={sym.conflicts} unresolved={sym.unresolved} low_conf={[sorted(x) for x in sym.low_confidence_pairs]}"]

    views = {}
    for view in (full, dm, cm):
        mos, pas, selfl, shunts = build_edges(by_name, passives, view, diode_nodes)
        ins = sorted({view.r(n)[0] for n in inp if view.r(n)})
        outs_rep = {view.r(n)[0] for n in outp if view.r(n)}
        rules = {"full": ("R1", "R2", "R1ng", "R2ng"), "R3-DM": ("R1", "R2"), "R3-CM": ("R2", "R2ng")}[view.name]
        res = {r: classify(by_name, view, mos, ins, outs_rep, r, diode_nodes) for r in rules}
        fb = feedback_edges(ins, [dict(e) for e in mos])          # MOS만의 루프
        plp = passive_loop_polarity(mos, pas)
        plp_ng = passive_loop_polarity(mos, pas, no_gs=True)
        allnodes = {e["u"] for e in mos + pas} | {e["v"] for e in mos + pas}
        adj_m, adj_a = defaultdict(set), defaultdict(set)
        for e in mos:
            adj_m[e["u"]].add(e["v"])
        for e in mos + pas:
            adj_a[e["u"]].add(e["v"])
        scc_m = [c for c in tarjan(allnodes, adj_m) if len(c) > 1]
        scc_a = [c for c in tarjan(allnodes, adj_a) if len(c) > 1]
        views[view.name] = (view, mos, pas, res, ins, outs_rep)
        r1 = res[rules[0]]
        L += [f"\n### 뷰 {view.name}: 입력={ins}, 출력={sorted(outs_rep)}",
              f"- MOS 엣지 {len(mos)} (gd {sum(e['kind']=='gd' for e in mos)}, sd {sum(e['kind']=='sd' for e in mos)}, gs {sum(e['kind']=='gs' for e in mos)}), 수동 방향엣지 {len(pas)}",
              f"- diode/수동 자기루프: {selfl}", f"- 접지 shunt 수동소자: {shunts}",
              f"- SCC(MOS만, >1노드): {scc_m}", f"- SCC(MOS+수동, >1노드): {scc_a}"]
        L.append(f"- BFS 레벨({rules[0]} min index 기준; 괄호: {rules[0]} max(응축 DAG 최장경로), 다른 규칙 min):")
        lv = defaultdict(list)
        for n, k in sorted(r1["idx"].items()):
            others = ",".join(f"{r}={res[r]['idx'].get(n)}" for r in rules[1:])
            lv[k].append(f"{n}(max={r1['max'].get(n)},{others})")
        for k in sorted(lv):
            L.append(f"  - idx {k}: {', '.join(lv[k])}")
        L.append("- 양(+) 가중 사이클 SCC(gd 포함 -> 최장경로 불확정): " +
                 " / ".join(f"{r}: {res[r]['poscyc']}" for r in rules))
        L.append("- MOS만의 루프(DFS back edge, 부호곱 -1=반전 +1=비반전):")
        for f in fb:
            e = f["edge"]
            L.append(f"  - {e['dev']}({e['kind']}) {e['u']}->{e['v']} 사이클={f['cycle']} 부호={f['sign']:+d}")
        L.append("- 수동소자가 닫는 루프(수동 u->v + 복귀경로 v=>u 부호집합; -1=부궤환 후보, 저주파 부호; "
                 "[MOS만 복귀]/[다른 수동 경유 복귀], 괄호 뒤=gs 엣지 제외 시):")
        ng = {(d, u, v): (a, b) for d, u, v, a, b in plp_ng}
        for dev, u, v, sm, sp in plp:
            a, b = ng.get((dev, u, v), ([], []))
            L.append(f"  - {dev} {u}->{v}: MOS만 {sm} / 수동경유 {sp} || gs제외: MOS만 {a} / 수동경유 {b}")
        if not pas:
            L.append("  - (수동 엣지 없음)")
        for rule in rules:
            rr = res[rule]
            L.append(f"- {rule} stage 목록:")
            ks = sorted({k for k in rr["stage"].values() if k is not None})
            for k in ks:
                members = defaultdict(list)
                for dname, st in rr["stage"].items():
                    if st == k:
                        members[rr["role"][dname]].append(dname)
                L.append(f"  - stage {k}: 출력노드={sorted(rr['outs'].get(k, []))} | " +
                         "; ".join(f"{ro}={sorted(v)}" for ro, v in sorted(members.items())))
            nis = sorted(d for d, st in rr["stage"].items() if st is None)
            L.append(f"  - 신호그래프 밖: {nis}")
        emit(L); L = []

    # ------------------------------------------------ 선언 대조
    refs = declared_refs(meta)
    L.append("\n### 선언 stage 대조 (소자 단위, 규칙 stage == 선언 stage)")
    L.append("| 선언 | 규칙/뷰 | 일치/전체 | 불일치(소자: 선언→규칙[역할]) |")
    L.append("|---|---|---|---|")
    circ_rates = {}
    for rname, ref in refs.items():
        roles_decl = ref.get("__roles__", {})
        devs = [d for d in ref if d != "__roles__"]
        for vname, rule in (("full", "R1"), ("full", "R2"), ("full", "R1ng"), ("full", "R2ng"),
                            ("R3-DM", "R1"), ("R3-DM", "R2"), ("R3-CM", "R2"), ("R3-CM", "R2ng")):
            rr = views[vname][3][rule]
            ok, bad = 0, []
            for d in devs:
                got = rr["stage"].get(d)
                if got == ref[d]:
                    ok += 1
                else:
                    bad.append(f"{d}:{ref[d]}→{got}[{rr['role'].get(d)}]")
            label = rule if vname == "full" else f"R3({vname[3:]}/{rule})"
            circ_rates.setdefault(rname, {})[label] = (ok, len(devs))
            L.append(f"| {rname} | {label} | {ok}/{len(devs)} | {', '.join(bad) or '-'} |")
        if roles_decl:
            rr = views["R3-DM"][3]["R2"]
            L.append(f"| {rname} 역할필드 vs R3-DM/R2 역할 | | | " +
                     ", ".join(f"{d}:{roles_decl[d]}→{rr['role'].get(d)}" for d in devs) + " |")
    emit(L); L = []

    # ------------------------------------------------ 출력노드 gds 기여자
    L.append("\n### stage 출력노드 gds 기여자 (R3-DM/R2 stage index, 원 넷 기준: 선언 stage-k 소자의 drain 넷 중 "
             "DM idx==k 이고 같은 stage 신호소자의 source가 아닌(=캐스코드 사슬 꼭대기) 넷; diode 노드는 따로 표시)")
    dmv = views["R3-DM"][0]
    dmres = views["R3-DM"][3]["R2"]
    mis_total = set()
    gain_refs = {k: v for k, v in refs.items() if "stages(" in k or "역할필드" in k}
    if not gain_refs:
        gain_refs = {k: v for k, v in refs.items() if k.startswith("compensation")}
        L.append("- (gain metric에 소자 목록이 없음 -> compensation.stage_devices로 대조)")
    for rname, ref in gain_refs.items():
        devs = [d for d in ref if d != "__roles__"]
        for k in sorted({ref[d] for d in devs}):
            sdev = {d for d in devs if ref[d] == k}
            # 사슬 꼭대기 = 같은 stage **선언** 소자의 source가 아닌 drain 넷(1차 실행에서 신호소자 전체로
            # 했더니 class-AB M18b.source=Vom1 때문에 Vom1이 빠졌다 -- 그 사실은 결과에 경계사례로 기록)
            sig_src = {by_name[x].source for x in sdev if x in by_name}
            cand = []
            for d in sorted(sdev):
                if d not in by_name:
                    continue
                dn = by_name[d].drain
                rp = dmv.r(dn)
                if rp and dmres["idx"].get(rp[0]) == k and dn not in sig_src and dn not in cand:
                    cand.append(dn)
            for node in sorted(cand):
                if node in diode_nodes:
                    L.append(f"- [{rname}] stage {k} 노드 {node}: **diode 노드**(저임피던스, 이득 출력노드 아님) "
                             f"-- drain 접속 {sorted(t.name for t in by_name.values() if t.drain == node)}")
                    continue
                dr = sorted(t.name for t in by_name.values() if t.drain == node)
                so = sorted(t.name for t in by_name.values() if t.source == node)
                ps = sorted(p["name"] for p in passives if node in p["terminals"])

                def chain(dev, depth=0, seen=None):
                    seen = seen or {dev}
                    s = by_name[dev].source
                    if s in RAILS or s in dmv.ground or depth > 3:   # DM 가상접지에서 사슬 종료
                        return dev
                    below = [t.name for t in by_name.values() if t.drain == s and t.name not in seen]
                    if not below:
                        return dev
                    return dev + "<-[" + " | ".join(chain(b, depth + 1, seen | {b}) for b in sorted(below)) + "]@" + s
                chains = [chain(d) for d in dr]
                missing_d = [d for d in dr if d not in sdev]
                missing_s = [d for d in so if d not in sdev]
                chain_members = set(re.findall(r"M\w+", " ".join(chains)))
                missing_c = sorted(chain_members - sdev - set(dr))
                if "stages(" in rname or "역할필드" in rname:
                    mis_total |= set(missing_d) | set(missing_s)
                L += [f"- [{rname}] stage {k} 노드 {node}",
                      f"  - drain 접속(gds/ro 사슬): {chains}",
                      f"  - source 접속(소스 들여다본 1/gm 부하): {so}", f"  - 수동소자: {ps}",
                      f"  - 선언 stage 목록 **누락**: drain접속 {missing_d}, source접속 {missing_s}, 사슬 하위 {missing_c}"]
    emit(L); L = []

    # ------------------------------------------------ 재사용 함수 교차확인
    L.append("\n### 기존 함수 교차확인")
    dp = sd.find_differential_pair_candidates(list(by_name.values()))
    pairs = sorted({(tuple(sorted(c["devices"])), c["shared_source"]) for c in (dp or {}).get("candidates", [])})
    L.append(f"- find_differential_pair_candidates: {pairs}")
    tails_rule = {d for d, r in views["R3-DM"][3]["R2"]["role"].items() if r == "tail"}
    tails_decl = sr.gain_stage_tails(by_name, meta)
    L.append(f"- tail: R3-DM/R2 규칙={sorted(tails_rule)} / gain_stage_tails(선언 기반)={tails_decl} / "
             f"diffpair shared_source를 drain으로 갖는 소자={sorted({t.name for t in by_name.values() for (_p, s) in pairs if t.drain == s})}")
    L.append(f"- true_current_mirror_groups: {sr.true_current_mirror_groups(by_name)}")
    br = sd.trace_vdd_to_gnd_branches(list(by_name.values()))
    L.append(f"- trace_vdd_to_gnd_branches: branch {len(br['branches'])}개")
    spn = sr.signal_path_nodes(by_name, set(inp), set(outp))
    mine = set(views["full"][3]["R1"]["idx"])
    L.append(f"- signal_path_nodes(excite=입력, sense=출력; 접지 절단·gs엣지 없음) = {sorted(spn)}")
    L.append(f"  - 이 probe full/R1 도달노드에만 있음: {sorted(mine - spn - set(inp) - set(outp))} / signal_path_nodes에만 있음: {sorted(spn - mine)}")
    emit(L)
    SUMMARY.append((name, circ_rates, sorted(mis_total)))


if __name__ == "__main__":
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("# probe_stage_partition 결과\n\n규칙: R1=gd엣지 1회당 stage+1(sd/gs 0), R2=R1+diode노드 게이트의 gd는 0(미러)+load/tail 분류, "
                 "R3=대칭 net 대응으로 차동(DM, 자기대응 넷=가상접지)/공통(CM) 뷰에서 R2. stage index=입력에서 min 경로(0-1 BFS).\n")
    for c in CIRCUITS:
        try:
            run_circuit(c)
        except Exception as ex:   # 케이스 실패를 기록하고 다음 회로 계속(결과 보존 목적)
            import traceback
            emit([f"\n## {c} -- 실행 실패\n```\n{traceback.format_exc()}\n```"])
    L = ["\n## 요약\n", "| 회로 | 선언 | 규칙 | 일치 |", "|---|---|---|---|"]
    for name, rates, mis in SUMMARY:
        for rname, rr in rates.items():
            for lab, (ok, n) in rr.items():
                L.append(f"| {name} | {rname} | {lab} | {ok}/{n} |")
    for name, rates, mis in SUMMARY:
        L.append(f"- {name}: gain 선언 누락 출력노드 접속 소자 {len(mis)}개 {mis}")
    emit(L)
    print("done", OUT)
