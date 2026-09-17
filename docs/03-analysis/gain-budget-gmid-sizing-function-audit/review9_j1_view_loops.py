# -*- coding: utf-8 -*-
"""J1을 뷰별로 두었을 때, 끊지 않는 뷰(CM·PSRR)에서 레플리카 루프가 (4)로 떨어지는지 잰다.

배경: J1 기본안 = 차동 전달 뷰에서는 레플리카 구동 넷(`Vbias2`·`Vbias3`)을 교류접지로 끊고,
공통모드·PSRR 뷰에서는 끊지 않는다. 끊지 않는 뷰에서 레플리카 루프가 `기록만`(4)로 떨어지면
그 뷰가 DEC-59로 정지해 `cmrr`·`psrr` 판정이 막힌다. 그 여부만 본다.

구조 그래프는 DM/CM을 구분하지 못한다(가상접지는 대칭 축약이 만든다). 그래서 이 측정은
**"끊은 경우" 대 "끊지 않은 경우"**를 재고, 뷰 이름은 그 둘 중 어느 쪽을 쓰는지의 이름표다.

규칙은 계획 v5.18 N3.2-2를 옮긴다:
  엣지 = gate->drain, gate->source, (source 노드가 전류 구동인 소자의) source->drain, 수동소자 양방향
  교류접지·여기 포트 넷은 그래프에서 뺀다
  폐경로 = 단순 사이클 전수, 2단자 수동소자 하나를 오가는 왕복은 빼다
  분류 (0) 자기엣지 / (1.5) 전달 뷰 신호 경로 노드를 하나도 지나지 않음 = 바이어스 SCC
        (2) 복귀 경로가 수동소자만 + 커패시터 포함 = Miller
        (3-a) 어느 순방향 경로에도 없는 능동 셀 포함 / (3-b) 복귀 경로에 능동 셀 + 블록을 거슬러 감
        (4) 나머지 = 기록만
근사(밝혀 둠): 순방향 경로 = 여기에서 도달 AND 출력 포트로 역도달. 복귀 엣지 = BFS 거리가 줄어드는 엣지
(규칙 7). 수동소자 엣지 비용 = 1(규칙 4 미정, N-05). 대칭 축약 뷰는 재지 않는다.

결과는 stdout이 아니라 같은 이름 `.txt`에 append한다(세션 규칙).
"""
import heapq
import io
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TOPO = os.path.join(ROOT, "skills", "analog-gmid-design", "assets", "library",
                    "current_reuse_telescopic_ota.topology.json")
OUT = os.path.splitext(os.path.abspath(__file__))[0] + ".txt"
RAILS = {"vdd", "gnd"}
J1_CUT = {"Vbias2", "Vbias3"}
EXCITE = ["Vip", "Vim"]
REPLICA = ({"M57", "M58"}, {"M63", "M64"})


def load():
    d = json.load(io.open(TOPO, encoding="utf-8"))
    mos = [m for m in d["netlist"] if isinstance(m, dict)]
    pas = [e for e in (d.get("passive_elements") or []) if isinstance(e, dict)]
    return d, mos, pas


def ac_ground(mos, pas, d, extra):
    driven = set()
    for m in mos:
        driven |= {m["drain"], m["source"]}
    for e in pas:
        driven |= set(e.get("terminals") or [])
    ports = set((d.get("ports") or {}).keys())
    gate_only = {m["gate"] for m in mos} - driven - ports
    return RAILS | gate_only | set(extra)


def signal_nets(mos, pas, acg):
    sig = {n for n in EXCITE if n not in acg}
    changed = True
    while changed:
        changed = False
        for m in mos:
            add = set()
            if m["gate"] in sig:
                add |= {m["drain"], m["source"]}
            if m["source"] in sig:
                add.add(m["drain"])
            for n in add:
                if n not in acg and n not in sig:
                    sig.add(n)
                    changed = True
        for e in pas:
            t = e.get("terminals") or []
            if len(t) == 2:
                for a, b in ((t[0], t[1]), (t[1], t[0])):
                    if a in sig and b not in acg and b not in sig:
                        sig.add(b)
                        changed = True
    return sig


def drive_kind(mos, net, sig):
    """v5.18 우선순위: 전류 진입이 있을 때 나가는 단자로 가른다."""
    current_in = any(m["drain"] == net and (m["gate"] in sig or m["source"] in sig) for m in mos)
    if not current_in:
        return "voltage"
    gate_exit = any(m["gate"] == net for m in mos)
    chan_exit = any(m["source"] == net for m in mos)
    if gate_exit and not chan_exit:
        return "voltage"           # 앞 stage 출력노드
    return "current"               # 채널로 나감(또는 tap)


def build_graph(mos, pas, sig, acg):
    """루프 탐지 그래프. edges[(u,v)] = [(kind, name), ...]"""
    edges = {}

    def add(u, v, kind, name):
        if u in sig and v in sig and u != v:
            edges.setdefault((u, v), []).append((kind, name))

    for m in mos:
        g, s, dr = m["gate"], m["source"], m["drain"]
        if g in sig:
            add(g, dr, "active", m["name"])
            add(g, s, "active", m["name"])
        if s in sig and drive_kind(mos, s, sig) == "current":
            add(s, dr, "active", m["name"])
    for e in pas:
        t = e.get("terminals") or []
        if len(t) == 2:
            kind = "cap" if e.get("kind") == "capacitor" else "passive"
            add(t[0], t[1], kind, e["name"])
            add(t[1], t[0], kind, e["name"])
    return edges


def simple_cycles(edges, nodes, cap=20000):
    """노드-단순 사이클 전수(작은 그래프 전제). 회전 중복은 최소 노드 기준으로 제거."""
    adj = {}
    for (u, v) in edges:
        adj.setdefault(u, set()).add(v)
    order = sorted(nodes)
    idx = {n: i for i, n in enumerate(order)}
    found, seen_keys = [], set()

    def dfs(start, node, path, onpath):
        if len(found) >= cap:
            return
        for nxt in sorted(adj.get(node, ())):
            if idx[nxt] < idx[start]:
                continue
            if nxt == start and len(path) >= 2:
                key = tuple(path)
                rot = min(range(len(key)), key=lambda i: (idx[key[i]],))
                norm = tuple(key[rot:] + key[:rot])
                if norm not in seen_keys:
                    seen_keys.add(norm)
                    found.append(list(path))
            elif nxt not in onpath:
                onpath.add(nxt)
                path.append(nxt)
                dfs(start, nxt, path, onpath)
                path.pop()
                onpath.discard(nxt)

    for s in order:
        dfs(s, s, [s], {s})
    return found


def distances(mos, pas, sig, passive_cost=1):
    dist = {n: float("inf") for n in sig}
    pq = []
    for n in EXCITE:
        if n in sig:
            dist[n] = 0
            heapq.heappush(pq, (0, n))
    adj = {}
    for m in mos:
        g, s, dr = m["gate"], m["source"], m["drain"]
        for a, b, w in ((g, dr, 1), (g, s, 0), (s, dr, 0)):
            if a in sig and b in sig:
                adj.setdefault(a, []).append((b, w))
    for e in pas:
        t = e.get("terminals") or []
        if len(t) == 2 and t[0] in sig and t[1] in sig:
            adj.setdefault(t[0], []).append((t[1], passive_cost))
            adj.setdefault(t[1], []).append((t[0], passive_cost))
    while pq:
        d0, n = heapq.heappop(pq)
        if d0 > dist.get(n, float("inf")):
            continue
        for m2, w in adj.get(n, ()):
            if d0 + w < dist.get(m2, float("inf")):
                dist[m2] = d0 + w
                heapq.heappush(pq, (d0 + w, m2))
    return dist


def forward_nodes(mos, pas, d, sig):
    outs = [n for n, p in (d.get("ports") or {}).items()
            if isinstance(p, dict) and p.get("direction") == "output"]
    rev = {}
    def link(a, b):
        if a in sig and b in sig:
            rev.setdefault(b, set()).add(a)
    for m in mos:
        link(m["gate"], m["drain"])
        link(m["gate"], m["source"])
        link(m["source"], m["drain"])
    for e in pas:
        t = e.get("terminals") or []
        if len(t) == 2:
            link(t[0], t[1])
            link(t[1], t[0])
    seen, stack = set(), [o for o in outs if o in sig]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        stack.extend(rev.get(n, ()))
    return seen


def classify(cycle, edges, dist, fwd, mos):
    """(분류, 소자집합)."""
    n = len(cycle)
    segs = [(cycle[i], cycle[(i + 1) % n]) for i in range(n)]
    labels = [edges[e][0] for e in segs]          # 첫 후보 엣지의 (kind, name)
    devs = {name for _, name in labels}
    kinds = [k for k, _ in labels]

    # 2단자 수동소자 하나를 오가는 왕복
    if n == 2 and len({name for _, name in labels}) == 1 and kinds[0] != "active":
        return "왕복(제외)", devs

    # (1.5) 바이어스 SCC
    if not (set(cycle) & fwd):
        return "(1.5) 바이어스 SCC", devs

    ret = [i for i, (u, v) in enumerate(segs)
           if dist.get(v, float("inf")) < dist.get(u, float("inf"))]
    ret_kinds = [kinds[i] for i in ret]

    # (2) Miller: 복귀 경로가 수동소자만이고 커패시터를 포함
    if ret and all(k != "active" for k in ret_kinds) and "cap" in ret_kinds:
        return "(2) Miller", devs
    # (가) 복귀가 수동소자만인데 커패시터가 없으면 (3-b)가 아니다 -> (4)
    passive_only_return = bool(ret) and all(k != "active" for k in ret_kinds)

    # (3-a) 어느 순방향 경로에도 없는 능동 셀
    active_names = {name for k, name in labels if k == "active"}
    off_fwd = set()
    for m in mos:
        if m["name"] in active_names and m["drain"] not in fwd and m["source"] not in fwd:
            off_fwd.add(m["name"])
    if off_fwd:
        return "(3-a) 루프 뷰", devs

    # (나) 수동소자 없이 능동 셀 둘로만 닫힘 -> J12-h 보류
    if n == 2 and all(k == "active" for k in kinds) and len(devs) == 2:
        return "(나) 2능동셀 루프(보류)", devs

    if ret and not passive_only_return:
        return "(3-b) 루프 뷰", devs
    return "(4) 기록만", devs


def run(label, cut, lines):
    d, mos, pas = load()
    acg = ac_ground(mos, pas, d, cut)
    sig = signal_nets(mos, pas, acg) - set(EXCITE)   # 여기 포트 넷 제거
    edges = build_graph(mos, pas, sig, acg)
    dist = distances(mos, pas, sig | set(EXCITE))
    fwd = forward_nodes(mos, pas, d, sig)
    cycles = simple_cycles(edges, sig)
    tally, rep_hits = {}, []
    for c in cycles:
        kind, devs = classify(c, edges, dist, fwd, mos)
        tally[kind] = tally.get(kind, 0) + 1
        for r in REPLICA:
            if r <= devs:
                rep_hits.append((kind, sorted(devs), c))
    lines.append(f"--- {label}")
    lines.append(f"    교류접지 예외 : {sorted(cut) if cut else '없음(끊지 않음)'}")
    lines.append(f"    신호 넷 {len(sig)} / 순방향 {len(fwd)} / 폐경로 {len(cycles)}")
    for k in sorted(tally):
        lines.append(f"      {k:26s} {tally[k]}")
    if rep_hits:
        for kind, devs, c in rep_hits:
            lines.append(f"    레플리카 루프 {devs} -> **{kind}**  경로 {c}")
    else:
        lines.append("    레플리카 루프: 폐경로에 나타나지 않음(그래프에서 빠짐)")


def main():
    lines = ["=== J1 뷰별 안: 끊지 않는 뷰에서 레플리카 루프가 (4)로 떨어지는가 (파일럿) ===",
             "구조 그래프는 DM/CM을 구분하지 못한다 -- 아래는 '끊은 경우' 대 '끊지 않은 경우'다.", ""]
    run("① 차동 전달 뷰 = J1 끊음", J1_CUT, lines)
    run("② 공통모드·PSRR 뷰 = J1 끊지 않음", set(), lines)
    lines.append("")
    with io.open(OUT, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
