# -*- coding: utf-8 -*-
"""규칙 9 (c)의 diode 미러 갈래가 실제로 정지를 푸는지 잰다.

계획 N3.2-9 (c)에 넣은 갈래: **diode 연결 소자의 drain 노드는 그 자체로 블록 출력노드가 아니다** --
그 노드를 **gate로 읽는 다른 소자가 있고 그 소자의 출력 단자가 순방향 경로 위에 있으면** 미러
입력이고 블록은 미러 출력 쪽으로 이어진다. 그런 소자가 없으면 진짜 diode 부하이고 (c)다.

라운드 5 실측에서 사이징 대상 4회로의 9 (c) 정지 사유가 전부 diode 노드였다. 이 갈래를 적용하면
그중 몇 건이 '미러 입력'으로 빠지는지(= 정지가 풀리는지)를 회로별로 센다.

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

spec = importlib.util.spec_from_file_location(
    "scan", os.path.join(HERE, "review9_bias_dependent_net_scan.py"))
S = importlib.util.module_from_spec(spec)
sys.modules["scan"] = S
spec.loader.exec_module(S)

CUT = {"current_reuse_telescopic_ota": {"Vbias2", "Vbias3"}}
SIZING = {"current_reuse_telescopic_ota", "folded_cascode", "nmcnr_amplifier", "two_stage_ota"}


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
    seen, st = set(), [o for o in outs if o in sig]
    while st:
        n = st.pop()
        if n in seen:
            continue
        seen.add(n)
        st.extend(rev.get(n, ()))
    return seen


def out_terminal(m, acg):
    """그 소자의 신호 출력 단자(drain이 교류접지면 source)."""
    return m["source"] if m["drain"] in acg else m["drain"]


def main():
    lines = ["=== 규칙 9 (c) diode 미러 갈래 측정 ===",
             "diode 노드마다: 그 노드를 gate로 읽는 다른 소자가 있고 그 소자의 출력 단자가 순방향 경로 "
             "위인가 → 미러 입력(블록이 이어짐, (c) 아님) / 아니면 진짜 diode 부하((c)).", ""]
    tot_mirror = tot_load = 0
    for fn in sorted(os.listdir(LIB)):
        if not fn.endswith(".topology.json") or fn.startswith("_TEMPLATE"):
            continue
        d = json.load(io.open(os.path.join(LIB, fn), encoding="utf-8"))
        name = str(d["topology_name"])
        mos = [m for m in d["netlist"] if isinstance(m, dict)]
        pas = [e for e in (d.get("passive_elements") or []) if isinstance(e, dict)]
        ex = S.excitation(d)
        if not ex:
            lines.append(f"  {name:30s} 측정 불가")
            continue
        rails = S.rails_of(d, mos, pas)
        acg = S.ac_ground(d, mos, pas, rails, CUT.get(name, set()))
        sig = S.signal_nets(mos, pas, ex, acg)
        fwd = forward_nodes(mos, pas, d, sig)
        diodes = [m for m in mos if m["gate"] == m["drain"]]
        mark = "★" if name in SIZING else " "
        if not diodes:
            lines.append(f"  {mark} {name:30s} diode 소자 0개")
            continue
        rows = []
        for dm in diodes:
            node = dm["drain"]
            readers = [x for x in mos if x["gate"] == node and x["name"] != dm["name"]]
            fwd_readers = [x for x in readers if out_terminal(x, acg) in fwd]
            verdict = "미러 입력((c) 아님)" if fwd_readers else "diode 부하((c))"
            if name in SIZING:
                if fwd_readers:
                    tot_mirror += 1
                else:
                    tot_load += 1
            rd = ",".join(x["name"] for x in readers) or "없음"
            fr = ",".join(x["name"] for x in fwd_readers) or "없음"
            rows.append(f"      {dm['name']:6s} node={node:12s} 읽는 소자={rd:<22} "
                        f"순방향={fr:<16} -> {verdict}")
        lines.append(f"  {mark} {name:30s} diode {len(diodes)}개")
        lines += rows
    lines += ["",
              f"사이징 대상 4회로 합계: 미러 입력 {tot_mirror}건 / 진짜 diode 부하 {tot_load}건",
              "미러 입력으로 빠진 건수만큼 규칙 9 (c) 정지가 풀린다. 남은 '진짜 diode 부하'는 "
              "여전히 (c)이고 그 판정이 옳은지는 J2 ratify 대상이다.",
              ""]
    with io.open(OUT, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
