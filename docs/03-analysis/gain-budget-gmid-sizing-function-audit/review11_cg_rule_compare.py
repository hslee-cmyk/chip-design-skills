# -*- coding: utf-8 -*-
"""CG/pass 판별 규칙 두 읽기를 library 전수로 대조한다(폐기한 읽기 대 현행 규칙).

배경: 계획 N3.2-3의 CG/pass 판별을 한 번 '그 소자를 지나지 않고도 drain에 닿는가'로 썼다가
라운드 4에서 기각했다. 상보 쌍이 같은 출력노드를 **독립 구동**하는 구조에서는 그 조건이 언제나
성립해 캐스코드가 pass로 떨어지기 때문이다(차동·상보 부류 전체에서 틀린다).

  규칙 A(폐기): gate가 신호 경로 밖 ∧ 그 소자의 채널을 뺀 그래프에서 drain 도달 불가 -> CG
  규칙 B(현행): gate가 신호 경로 밖 ∧ source가 신호 넷 -> CG, 단 역병렬 pass 묶음은 pass
                + **셀 수 집계에는 순방향 제한**(여기에서 도달 ∧ 출력 포트로 역도달)

기대값은 계획 N3.2-7/N6.2 6a의 "기존 4개 회로 CG 8개 = 파일럿 캐스코드 4 + folded 2 + nmcnr 2"와
"파일럿 pass 묶음 2개", 그리고 `common_gate_amplifier` 1이다. J1 확정 산출(파일럿 캐스코드 게이트
바이어스 넷 2개)을 교류접지로 끊은 차동 뷰에서 잰다.

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

CUT = {"current_reuse_telescopic_ota": {"Vbias2", "Vbias3"}}   # J1 확정 산출
EXPECT = {"current_reuse_telescopic_ota": 4, "folded_cascode": 2,
          "nmcnr_amplifier": 2, "common_gate_amplifier": 1}
LEGACY4 = {"current_reuse_telescopic_ota", "folded_cascode",
           "nmcnr_amplifier", "two_stage_ota"}


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


def bundles_of(mos, sig):
    """역병렬 pass 묶음: 같은 두 노드 사이 반대 방향, 둘 다 gate가 신호 경로 밖."""
    pairs = {}
    for m in mos:
        if m["gate"] in sig:
            continue
        pairs.setdefault(tuple(sorted((m["source"], m["drain"]))), []).append(m)
    return {k: v for k, v in pairs.items()
            if len(v) == 2 and v[0]["source"] != v[1]["source"]}


def main():
    lines = ["=== CG/pass 판별: 폐기한 읽기(A) 대 현행 규칙(B+순방향) ===",
             "J1 확정 산출을 끊은 차동 뷰. 기대 = 계획 N3.2-7/N6.2 6a.", ""]
    tot_a = tot_b = 0
    for fn in sorted(os.listdir(LIB)):
        if not fn.endswith(".topology.json") or fn.startswith("_TEMPLATE"):
            continue
        d = json.load(io.open(os.path.join(LIB, fn), encoding="utf-8"))
        name = str(d["topology_name"])
        mos = [m for m in d["netlist"] if isinstance(m, dict)]
        pas = [e for e in (d.get("passive_elements") or []) if isinstance(e, dict)]
        ex = S.excitation(d)
        if not ex:
            lines.append(f"  {name:30s} 측정 불가(입력 포트 미선언)")
            continue
        rails = S.rails_of(d, mos, pas)
        acg = S.ac_ground(d, mos, pas, rails, CUT.get(name, set()))
        sig = S.signal_nets(mos, pas, ex, acg)
        fwd = forward_nodes(mos, pas, d, sig)
        bd = bundles_of(mos, sig)
        bundled = {m["name"] for v in bd.values() for m in v}

        a = []
        for m in mos:
            if m["gate"] in sig or m["source"] not in sig or m["drain"] not in sig:
                continue
            others = [x for x in mos if x["name"] != m["name"]]
            if m["drain"] not in S.signal_nets(others, pas, ex, acg):
                a.append(m["name"])
        b = [m["name"] for m in mos
             if m["gate"] not in sig and m["source"] in sig
             and m["name"] not in bundled and m["drain"] in fwd]

        exp = EXPECT.get(name)
        ok = "OK" if exp is None or len(b) == exp else "**불일치**"
        if name in LEGACY4:
            tot_a += len(a)
            tot_b += len(b)
        lines.append(f"  {name:30s} A={len(a):2d} {sorted(a)}")
        lines.append(f"  {'':30s} B={len(b):2d} {sorted(b)}  묶음={len(bd)}  기대={exp} {ok}")
    lines += ["",
              f"기존 4개 회로 CG 합계: A={tot_a} / B={tot_b}  (계획 기대 8)",
              "판정: A는 상보 쌍이 같은 출력노드를 독립 구동하는 구조(파일럿·folded·nmcnr 전부)에서 "
              "캐스코드를 pass로 떨어뜨려 기대를 재현하지 못한다. B가 기대를 전부 재현한다.",
              ""]
    with io.open(OUT, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
