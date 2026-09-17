# -*- coding: utf-8 -*-
"""v5.18 확정 규칙(J1 뷰별 포함)으로 회로별 루프 분류 (4) `기록만` 잔여를 다시 잰다.

6a 완료 조건이 "사이징 대상 회로에 (4)가 남아 있지 않음"이라, 범위 결정
("(4)가 끝내 안 없어지는 회로를 사이징 대상에서 뺄지")의 입력이 이 수치다.

적용 규칙(계획 v5.18):
  - 교류접지 = 레일(`supply_nets`) + gate 전용 미구동 넷 + **바이어스 종속 넷**(규칙 1 (4),
    차동 뷰 = 사슬 출발 노드가 움직이지 않는 뷰로 본다)
  - 폐경로 = 단순 사이클 전수, 2단자 수동소자 왕복 제외
  - 복귀 엣지 = 거리가 **늘지 않는** 엣지(동률 포함, 규칙 7)
  - 분류 (0) 자기엣지 / (1.5) 바이어스 SCC / (2) Miller / (3-a)(3-b) / (4)
    (3-b) 배타: (가) 복귀가 수동소자만이면 (3-b) 아님 (나) 수동소자 없는 2능동셀 루프는 보류

같은 폴더 `review9_bias_dependent_net_scan.py`(술어)와 `review9_j1_view_loops.py`(그래프)를
재사용한다 -- 같은 개념을 두 번 구현하지 않는다.

결과는 stdout이 아니라 같은 이름 `.txt`에 append한다(세션 규칙).
"""
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
LIB = os.path.join(ROOT, "skills", "analog-gmid-design", "assets", "library")
OUT = os.path.splitext(os.path.abspath(__file__))[0] + ".txt"
SIZING_TARGETS = {"current_reuse_telescopic_ota", "folded_cascode",
                  "nmcnr_amplifier", "two_stage_ota"}


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


SCAN = _load("review9_bias_dependent_net_scan")
GRAPH = _load("review9_j1_view_loops")


def bias_dependent_nets(d, mos, pas, ex):
    """규칙 1 (4) 술어가 고르는 넷(= 차동 뷰에서 끊는 넷)."""
    rails = SCAN.rails_of(d, mos, pas)
    acg = SCAN.ac_ground(d, mos, pas, rails, set())
    sig = SCAN.signal_nets(mos, pas, ex, acg)
    return {b for b, _dev, _start, _drv in SCAN.candidates(d, mos, pas, acg, sig, ex)}


def classify(cycle, edges, dist, fwd, mos):
    """v5.18 분류. 복귀 엣지는 '거리가 늘지 않는 엣지'(동률 포함)."""
    n = len(cycle)
    segs = [(cycle[i], cycle[(i + 1) % n]) for i in range(n)]
    labels = [edges[e][0] for e in segs]
    devs = {nm for _, nm in labels}
    kinds = [k for k, _ in labels]
    if n == 2 and len({nm for _, nm in labels}) == 1 and kinds[0] != "active":
        return "왕복(제외)", devs
    if not (set(cycle) & fwd):
        return "(1.5) 바이어스 SCC", devs
    ret = [i for i, (u, v) in enumerate(segs)
           if dist.get(v, float("inf")) <= dist.get(u, float("inf"))]
    rk = [kinds[i] for i in ret]
    if ret and all(k != "active" for k in rk) and "cap" in rk:
        return "(2) Miller", devs
    passive_only_return = bool(ret) and all(k != "active" for k in rk)
    active_names = {nm for k, nm in labels if k == "active"}
    if any(m["name"] in active_names and m["drain"] not in fwd and m["source"] not in fwd
           for m in mos):
        return "(3-a) 루프 뷰", devs
    if n == 2 and all(k == "active" for k in kinds) and len(devs) == 2:
        return "(나) 2능동셀 루프(보류)", devs
    if ret and not passive_only_return:
        return "(3-b) 루프 뷰", devs
    return "(4) 기록만", devs


def main():
    lines = ["=== v5.18 확정 규칙에서 (4) `기록만` 잔여 (차동 전달 뷰, J1 적용) ===",
             "6a 완료 조건 '사이징 대상에 (4) 없음'의 현재 입력. ★ = 사이징 대상 회로.", ""]
    tally = []
    for fn in sorted(os.listdir(LIB)):
        if not fn.endswith(".topology.json") or fn.startswith("_TEMPLATE"):
            continue
        d = json.load(io.open(os.path.join(LIB, fn), encoding="utf-8"))
        name = str(d.get("topology_name"))
        mos = [m for m in d["netlist"] if isinstance(m, dict)]
        pas = [e for e in (d.get("passive_elements") or []) if isinstance(e, dict)]
        ex = SCAN.excitation(d)
        mark = "★" if name in SIZING_TARGETS else " "
        if not ex:
            lines.append(f"  {mark} {name:30s} 측정 불가(입력 포트 미선언)")
            continue
        cut = bias_dependent_nets(d, mos, pas, ex)
        rails = SCAN.rails_of(d, mos, pas)
        acg = SCAN.ac_ground(d, mos, pas, rails, cut)
        sig = SCAN.signal_nets(mos, pas, ex, acg) - set(ex)
        edges = GRAPH.build_graph(mos, pas, sig, acg)
        GRAPH.EXCITE = ex                      # 거리·순방향 계산의 여기 넷을 회로에 맞춘다
        dist = GRAPH.distances(mos, pas, sig | set(ex))
        fwd = GRAPH.forward_nodes(mos, pas, d, sig)
        counts = {}
        four = []
        for c in GRAPH.simple_cycles(edges, sig):
            k, devs = classify(c, edges, dist, fwd, mos)
            counts[k] = counts.get(k, 0) + 1
            if k.startswith("(4)"):
                four.append((sorted(devs), c))
        n4 = counts.get("(4) 기록만", 0)
        tally.append((name, name in SIZING_TARGETS, n4))
        detail = " / ".join(f"{k} {v}" for k, v in sorted(counts.items()))
        lines.append(f"  {mark} {name:30s} 끊은 넷 {sorted(cut) or '없음'}")
        lines.append(f"      {detail}")
        for devs, c in four:
            lines.append(f"      (4): {devs} {c}")
    bad = [n for n, t, c in tally if t and c]
    lines += ["",
              f"사이징 대상 중 (4)가 남은 회로: {bad if bad else '없음'}",
              "(4)가 남으면 그 회로는 6c부터 DEC-59로 정지한다 -- 흡수 규칙을 정의하거나 "
              "사이징 대상에서 빼야 한다(계획 N6.2 6a).",
              ""]
    with io.open(OUT, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
