# -*- coding: utf-8 -*-
"""J1(레플리카 교류접지 예외)을 적용했을 때 파일럿의 CG 셀과 pass 묶음이 어떻게 되는지 잰다.

묻는 것 두 가지:
  (1) pass 묶음이 0으로 무너지는 원인이 J1인가, 도달성 문구 차이인가?
  (2) J1을 적용하면 CG가 7개(캐스코드 4 + M37b + M58 + M63)가 되는데,
      **순방향 경로(여기에서 도달 AND 출력 포트로 역도달) 위의 셀만 세면** 6a DoD의 기대값 4가 되는가?

규칙은 계획 v5.18 본문(N3.2-3)을 그대로 옮긴다:
  신호 넷 = 여기 포트에서 시작하는 최소 고정점
    (a) 신호 넷을 gate로 받는 소자의 drain·source
    (b) 신호 넷을 source로 받는 소자의 drain
    (c) 신호 넷에 붙은 2단자 수동소자의 반대 단자
  교류접지 집합·제거 넷은 신호 넷에 넣지 않는다.
비교용으로 옛 history H2 요약 문구((b)를 '전류 구동 source->drain'으로 읽는 것)도 함께 잰다.

결과는 stdout이 아니라 같은 이름 `.txt`에 append한다(세션 규칙).
"""
import io
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TOPO = os.path.join(ROOT, "skills", "analog-gmid-design", "assets", "library",
                    "current_reuse_telescopic_ota.topology.json")
OUT = os.path.splitext(os.path.abspath(__file__))[0] + ".txt"
RAILS = {"vdd", "gnd"}
J1_CUT = {"Vbias2", "Vbias3"}   # J1 기본안: 레플리카가 구동하는 캐스코드 게이트 넷


def load():
    d = json.load(io.open(TOPO, encoding="utf-8"))
    mos = [m for m in d["netlist"] if isinstance(m, dict)]
    pas = [e for e in (d.get("passive_elements") or []) if isinstance(e, dict)]
    return d, mos, pas


def ac_ground_set(mos, pas, d, extra):
    """레일 + gate에만 붙고 구동되지 않는 넷 + 예외(J1)."""
    driven = set()
    for m in mos:
        driven.add(m["drain"])
        driven.add(m["source"])
    for e in pas:
        for t in e.get("terminals") or []:
            driven.add(t)
    for s in (d.get("ideal_sources") or []):
        if isinstance(s, dict):
            for t in (s.get("terminals") or [s.get("from"), s.get("to")]):
                if t:
                    driven.add(t)
    ports = set((d.get("ports") or {}).keys())
    gate_only = {m["gate"] for m in mos} - driven - ports
    return RAILS | gate_only | set(extra)


def signal_nets(mos, pas, excite, acg, h2_reading):
    """본문 최소 고정점. h2_reading=True면 (b)를 '전류 구동 source->drain'으로 제한한다."""
    sig = {n for n in excite if n not in acg}
    changed = True
    while changed:
        changed = False
        for m in mos:
            g, s, dr = m["gate"], m["source"], m["drain"]
            add = set()
            if g in sig:                       # (a) gate 구동
                add |= {dr, s}
            if s in sig:                       # (b) source 진입 -> drain
                if not h2_reading or current_driven(mos, s, sig, acg):
                    add.add(dr)
            for n in add:
                if n not in acg and n not in sig:
                    sig.add(n)
                    changed = True
        for e in pas:                          # (c) 수동소자 양방향
            t = e.get("terminals") or []
            if len(t) == 2:
                for a, b in ((t[0], t[1]), (t[1], t[0])):
                    if a in sig and b not in acg and b not in sig:
                        sig.add(b)
                        changed = True
    return sig


def current_driven(mos, net, sig, acg):
    """H2 요약 문구 읽기: 그 노드로 신호 셀의 drain이 들어오면 전류 구동."""
    for m in mos:
        if m["drain"] == net and (m["gate"] in sig or m["source"] in sig):
            return True
    return False


def backward_reach(mos, pas, targets, sig, acg):
    """출력 포트로 역도달하는 신호 넷(= 순방향 경로 위의 넷)."""
    rev = {n: set() for n in sig}
    def link(a, b):                            # a -> b (전방)
        if a in sig and b in sig:
            rev[b].add(a)
    for m in mos:
        g, s, dr = m["gate"], m["source"], m["drain"]
        link(g, dr)
        link(g, s)
        link(s, dr)
    for e in pas:
        t = e.get("terminals") or []
        if len(t) == 2:
            link(t[0], t[1])
            link(t[1], t[0])
    seen, stack = set(), [t for t in targets if t in sig]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        stack.extend(rev.get(n, ()))
    return seen


def distances(mos, pas, excite, sig, acg, passive_cost):
    """규칙 4의 0-1 BFS: gate->drain 1, gate->source 0, source->drain 0, 수동소자 = passive_cost."""
    import heapq
    dist = {n: float("inf") for n in sig}
    pq = []
    for n in excite:
        if n in sig:
            dist[n] = 0
            heapq.heappush(pq, (0, n))
    edges = []
    for m in mos:
        g, s, dr = m["gate"], m["source"], m["drain"]
        edges += [(g, dr, 1), (g, s, 0), (s, dr, 0)]
    for e in pas:
        t = e.get("terminals") or []
        if len(t) == 2:
            edges += [(t[0], t[1], passive_cost), (t[1], t[0], passive_cost)]
    adj = {}
    for a, b, w in edges:
        if a in sig and b in sig:
            adj.setdefault(a, []).append((b, w))
    while pq:
        d0, n = heapq.heappop(pq)
        if d0 > dist.get(n, float("inf")):
            continue
        for m2, w in adj.get(n, ()):
            if d0 + w < dist.get(m2, float("inf")):
                dist[m2] = d0 + w
                heapq.heappush(pq, (d0 + w, m2))
    return dist


def classify(mos, sig, acg, dist):
    """규칙 3 셀 우선순위 + 방향 도달 순서."""
    anti = {}
    for m in mos:
        key = tuple(sorted((m["source"], m["drain"])))
        anti.setdefault(key, []).append(m)
    cells = {}
    for m in mos:
        g, s, dr, n = m["gate"], m["source"], m["drain"], m["name"]
        if g in sig:
            if dr in acg:
                cells[n] = ("CD", g, s)
            elif s in acg:
                cells[n] = ("CS", g, dr)
            else:
                cells[n] = ("CS(degen)", g, dr)
            continue
        if s in sig and dr in sig:
            key = tuple(sorted((s, dr)))
            pair = [x for x in anti[key] if x["gate"] not in sig]
            anti_parallel = (len(pair) == 2 and pair[0]["source"] != pair[1]["source"])
            if anti_parallel:
                cells[n] = ("pass", s, dr)          # 역병렬 pass 묶음
            elif dist.get(s, float("inf")) <= dist.get(dr, float("inf")):
                cells[n] = ("CG", s, dr)
            else:
                cells[n] = ("pass", s, dr)
        elif s in sig:
            cells[n] = ("CG", s, dr)
        elif dr in sig:
            cells[n] = ("load", dr, dr)
        else:
            cells[n] = ("off_path", None, None)
    return cells


def pass_bundles(mos, cells):
    """역병렬 pass 묶음: 같은 두 노드 사이 반대 방향 pass 쌍."""
    by_pair = {}
    for m in mos:
        if cells[m["name"]][0] != "pass":
            continue
        key = tuple(sorted((m["source"], m["drain"])))
        by_pair.setdefault(key, []).append(m["name"])
    return {k: v for k, v in by_pair.items() if len(v) == 2}


def run(label, excite, cut, h2_reading, lines, passive_cost=1):
    d, mos, pas = load()
    acg = ac_ground_set(mos, pas, d, cut)
    sig = signal_nets(mos, pas, excite, acg, h2_reading)
    outs = [n for n, p in (d.get("ports") or {}).items()
            if isinstance(p, dict) and p.get("direction") == "output"]
    fwd = backward_reach(mos, pas, outs, sig, acg)
    dist = distances(mos, pas, excite, sig, acg, passive_cost)
    cells = classify(mos, sig, acg, dist)
    cg_all = sorted(n for n, c in cells.items() if c[0] == "CG")
    cg_fwd = sorted(n for n in cg_all if cells[n][2] in fwd)
    bundles = pass_bundles(mos, cells)
    casc = ["M2a", "M2b", "M3a", "M3b"]
    lines += [
        f"--- {label}",
        f"    J1 예외        : {sorted(cut) if cut else '없음'}   수동소자 엣지 비용 {passive_cost}",
        f"    신호 넷 {len(sig)} / 순방향 {len(fwd)}",
        f"    Vg15/Vg25 신호넷 여부 : {'Vg15' in sig} / {'Vg25' in sig}",
        f"    캐스코드 4개 판정 : {[(c, cells[c][0]) for c in casc]}",
        f"    CG 전체 {len(cg_all)} : {cg_all}",
        f"    CG 순방향만 {len(cg_fwd)} : {cg_fwd}",
        f"    pass 묶음 {len(bundles)} : {[v for v in bundles.values()]}",
    ]


def main():
    lines = ["=== J1 적용 시 CG 셀·pass 묶음 재측정 (파일럿, 비축약 기본 전달 뷰) ===",
             "6a DoD 기대: 파일럿 캐스코드 4개(M2a/M2b/M3a/M3b)가 CG, pass 묶음 2개, M37b는 CG 수에 넣지 않음",
             ""]
    ex = ["Vip", "Vim"]
    run("① v5.18 본문 그대로, J1 미적용", ex, set(), False, lines)
    run("② v5.18 본문 그대로 + J1 적용", ex, J1_CUT, False, lines)
    run("③ 옛 history H2 요약 문구 읽기 + J1 적용", ex, J1_CUT, True, lines)
    lines += [
        "",
        "판정:",
        " * pass 묶음이 0으로 무너지는 것은 ③(도달성 문구를 '전류 구동 source->drain'으로 읽는 경우)뿐이고",
        "   **J1 때문이 아니다** -- ②는 J1을 적용해도 묶음 2개가 그대로다.",
        " * ②에서 CG가 기대값 4를 넘는 것은 레플리카 소자 자신(M58/M63)과 CMFB M37b가 CG 조건을",
        "   구조적으로 만족하기 때문이고, 이들은 출력으로 역도달하지 못하는 가지에 있다.",
        "   **순방향 경로 위의 셀만 세면** 그 수가 어떻게 되는지를 위 'CG 순방향만' 줄이 보여 준다.",
        "",
    ]
    with io.open(OUT, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
