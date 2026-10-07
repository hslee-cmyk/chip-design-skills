# -*- coding: utf-8 -*-
"""§7.5(전체회로 물리 정합성 검증기)가 무엇을 못 보는지 재는 조사 도구 -- 계획 §10.3 B7/B8/B9 근거.

측정 결과(2026-09-08, current_reuse_telescopic_ota):

B7 프로토타입 `node_dc_propagate.py`가 "그대로 이식" 가능한가
  (i)   set 순회 의존 -- 코드상 존재하나 **이 회로에서는 결과가 안 바뀐다**(순회 순서를 뒤집어도
        노드값 32개 전부 동일). 잠재 위험이지 실현된 결함은 아니다.
  (ii)  `if not progressed and not unresolved: break` -- 진전이 없어도 unresolved가 남으면
        20 pass를 조용히 돌고 빠져나온다(진짜 실패를 안 보고).
  (iii) **다중도달 일치검사 미구현** -- `elif src in nodes and drn in nodes:`가 비교 없이
        discard만 한다. 실물에서 21건 중 **4건이 243.5mV 불일치**(Vop1/Vom1에 M2a/M2b/M3a/M3b
        경로가 0.6565 vs 0.9000으로 도달). §7.5의 핵심 검사가 바로 이것인데 없다.
  (iv)  VGS 검사가 3쌍(M1a/M4a, M1b/M4b, M15/M16) 하드코딩.

B8 KCL 잔차 -- §7.5의 세 검사가 전부 전압이라 전류 정합성을 못 본다
  내부 노드 30개 중 3개가 잔차 >1nA:  Vx -3.96uA / Vy +0.65uA / Vbias1 +0.65uA
  레일: vdd -86.27uA vs gnd +88.93uA -> 2.66uA 불일치
  (Vbias1의 +0.65는 Iref 주입이라 metric에서는 value_amp를 함께 세어 상쇄한다)
  이 실측이 `_metric_kcl_residual()`(B8, 2026-09-08 신설)의 근거다.

B9 vs=0이 틀린 값인가 -- **부정확한 전제였다**
  vs=0인 39개 중 **24개는 source가 레일에 직결이라 vs=0이 물리적으로 옳다**.
  진짜 문제는 일관성: 레일이 아닌데 vs=0인 소자 15개 / 반대로 레일인데 vs!=0인 소자 4개
  (M60 0.30 / M61 0.25 / M38 0.30 / M68 0.25). vs의 정의와 후자의 의도 여부는 회로 해석이라
  공동분석 대상으로 남겼다.

실행: assets 디렉터리에서 `python tests/probe_physical_consistency.py`
(자동 테스트가 아니라 조사용.)
"""
import os, sys, json
from collections import defaultdict
ASSETS = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets"
sys.path.insert(0, ASSETS)
import numpy as np, sizing_recipe as sr

TOPO = os.path.join(ASSETS, "library", "current_reuse_telescopic_ota.topology.json")
INST = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\workspaces\current-reuse-telescopic-ota-report\current_reuse_telescopic_ota.instance.json"
VDD = 1.8
RAIL_HI, RAIL_LO = {"vdd", "VDD"}, {"gnd", "GND", "vss", "VSS"}

trs, meta = sr.load_topology(TOPO)
inst = json.load(open(INST, encoding="utf-8"))
sized = inst["sizing"]
by = {t.name: t for t in trs}

# ── B7-(i) set 순회 의존성: 프로토타입 알고리즘을 그대로 재현하되 순회 순서만 바꿔본다 ──
def propagate(order_key):
    nodes = {"vdd": VDD, "gnd": 0.0}
    unresolved = set(by)
    conflicts = []
    for _ in range(20):
        progressed = False
        for name in sorted(unresolved, key=order_key):
            t = by[name]
            src, drn = t.source, t.drain
            if src in nodes and drn not in nodes:
                v = nodes[src] - sized[name]["vds"] if t.kind == "pmos" else nodes[src] + sized[name]["vds"]
                nodes[drn] = v
                unresolved.discard(name); progressed = True
            elif src in nodes and drn in nodes:
                # ★ 프로토타입은 여기서 **일치 검사 없이** discard만 한다(B7-iii)
                exp = nodes[src] - sized[name]["vds"] if t.kind == "pmos" else nodes[src] + sized[name]["vds"]
                conflicts.append((name, drn, nodes[drn], exp, abs(nodes[drn] - exp)))
                unresolved.discard(name)
        if not progressed:
            break
    return nodes, unresolved, conflicts

n1, u1, c1 = propagate(lambda s: s)                       # 이름 오름차순
n2, u2, c2 = propagate(lambda s: s[::-1])                 # 뒤집은 이름순(= 다른 순회 순서)
common = set(n1) & set(n2)
diffs = [(k, n1[k], n2[k]) for k in sorted(common) if abs(n1[k] - n2[k]) > 1e-9]
print("=" * 92)
print("B7-(i) 순회 순서를 바꾸면 결과가 달라지는가")
print("  해소 노드: 순서A %d개 / 순서B %d개, 미해소 %d/%d"
      % (len(n1), len(n2), len(u1), len(u2)))
print("  값이 달라진 노드: %d개" % len(diffs))
for k, a, b in diffs[:8]:
    print("    %-14s A=%.6f  B=%.6f  차이=%.1f mV" % (k, a, b, abs(a - b) * 1e3))
print("  => 프로토타입은 `for name in list(unresolved)`(set 순회)라 이 차이가 그대로 나온다")

print()
print("B7-(iii) 같은 net에 두 경로가 도달할 때의 불일치(프로토타입은 검사 없이 discard)")
c1s = sorted(c1, key=lambda x: -x[4])
print("  다중 도달 %d건, 그중 불일치(>1mV) %d건" % (len(c1s), sum(1 for x in c1s if x[4] > 1e-3)))
for nm, net, have, exp, d in c1s[:8]:
    print("    %-8s net %-12s 기존 %.4f vs 이 경로 %.4f -> **%.1f mV 불일치**" % (nm, net, have, exp, d * 1e3))

# ── B8: 노드별 KCL 잔차 ──────────────────────────────────────────────────
print()
print("=" * 92)
print("B8  노드별 KCL 잔차 (Sum I_into_node)")
inj = defaultdict(float)
for name, t in by.items():
    e = sized.get(name)
    if not e or "ID" not in e:
        continue
    I = e["ID"]
    if t.kind == "nmos":      # ID: drain -> source
        inj[t.drain] -= I; inj[t.source] += I
    else:                      # pmos: source -> drain
        inj[t.source] -= I; inj[t.drain] += I
ideal = meta.get("ideal_sources") or []
print("  ideal_sources %d개: %s" % (len(ideal), [s.get("name") for s in ideal]))
rows = [(n, v) for n, v in inj.items() if n not in RAIL_HI and n not in RAIL_LO]
rows.sort(key=lambda kv: -abs(kv[1]))
print("  내부 노드 %d개, |잔차| 상위:" % len(rows))
for n, v in rows[:12]:
    print("    %-14s %+10.4f uA" % (n, v * 1e6))
big = [r for r in rows if abs(r[1]) > 1e-9]
print("  잔차 > 1nA 인 내부 노드: %d / %d" % (len(big), len(rows)))
print("  레일: vdd %+.4f uA / gnd %+.4f uA" % (inj.get("vdd", 0) * 1e6, inj.get("gnd", 0) * 1e6))

# ── B9: vs=0이 맞는 값인가 ───────────────────────────────────────────────
print()
print("=" * 92)
print("B9  vs=0 이 틀린 값인가 -- source가 레일에 있으면 0이 **맞다**")
zero = [n for n in sized if abs(sized[n].get("vs", 0.0)) < 1e-12]
nz = [n for n in sized if abs(sized[n].get("vs", 0.0)) >= 1e-12]
print("  vs=0 인 소자 %d개 / vs!=0 인 소자 %d개" % (len(zero), len(nz)))
ok, bad = [], []
for n in zero:
    t = by.get(n)
    if t is None: continue
    at_rail = (t.kind == "nmos" and t.source in RAIL_LO) or (t.kind == "pmos" and t.source in RAIL_HI)
    (ok if at_rail else bad).append(n)
print("  그중 source가 레일에 직결 -> vs=0이 물리적으로 **옳다**: %d개" % len(ok))
print("  source가 레일이 아닌데 vs=0 -> **의심**: %d개" % len(bad))
for n in bad[:14]:
    t = by[n]
    print("    %-8s %-5s source=%-12s (레일 아님)" % (n, t.kind, t.source))
print()
print("  vs!=0 인 소자:")
for n in nz:
    t = by[n]
    print("    %-8s %-5s vs=%.4f  source=%s" % (n, t.kind, sized[n]["vs"], t.source))
