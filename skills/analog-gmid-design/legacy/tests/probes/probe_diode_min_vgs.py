# -*- coding: utf-8 -*-
"""B1 배선 전 사전계산 2/2 -- 초과 스택이 **원리적으로** 감당 가능한가(계획 §7.3, v4.13).

diode의 자기일관 vds(=Vgs)는 gm_id가 클수록 작아진다(weak inversion일수록 오버드라이브가
작다). 따라서 gm_id/L을 훑어 얻는 **최소 Vgs**가 그 소자가 낼 수 있는 하한이고, 그 합이
예산을 넘으면 그 스택은 **어떤 사이징으로도 성립하지 않는다**.

측정 결과(2026-09-08, current_reuse_telescopic_ota):
  **원리적으로 불가능한 스택은 하나도 없다.**
    4개(battery_a x2, vbias2_stack, cmfb_vocdes_gen) -- 비-diode를 그대로 둬도 가능
    3개(battery_b x2, vbias3_stack)                  -- 비-diode도 0.10~0.14V 내려가야 한다
  즉 feasible 영역이 비어 있지 않아 배선+재탐색(정공법)이 실현 가능하다.

정직한 한계: 그 최소 Vgs는 `gm_id 25~26.5` / `L=0.15um`에서 나오는데, A11의 gain 정점
(18~20.5)을 지나 떨어지는 영역이고 §7.10의 knee(0.30~0.45um)보다 낮은 L이라 **대가가 크다**.
이 표는 해의 존재를 보이는 하한 증명이지 설계안이 아니다 -- 실제 해는 탐색이 찾아야 한다.

부수 관찰: PMOS 최소 Vgs가 0.0658V(거의 서브스레숄드 극단)인 반면 NMOS는 0.2505V로 차이가
크다. M57만 L=0.500um에서 최소가 나오는데 vsb=0.25 때문으로 보인다.

실행: assets 디렉터리에서 `python tests/probe_diode_min_vgs.py`
(자동 테스트가 아니라 조사용. gm_id 46점 x L 7점을 diode 16개에 돌려 수십 초 걸린다.)
"""
import os, sys, json
from collections import defaultdict
ASSETS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # probes -> tests -> assets
sys.path.insert(0, ASSETS)
import numpy as np, sizing_recipe as sr

TOPO = os.path.join(ASSETS, "..", "assets", "library", "current_reuse_telescopic_ota.topology.json")
INST = os.path.join(ASSETS, "workspaces", "current-reuse-telescopic-ota-report", "current_reuse_telescopic_ota.instance.json")
VDD = 1.8

trs, meta = sr.load_topology(TOPO)
sized = json.load(open(INST, encoding="utf-8"))["sizing"]
for v in sized.values():
    if "vs" in v and "vsb" not in v:
        v["vsb"] = v.pop("vs")
npz = np.load(os.path.join(ASSETS, "..", "assets", "sky130_nfet_pfet_lut_sample.npz"))
mk = lambda k: sr.SemiEmpiricalGmIdLUT(npz["L"], npz["VGS"], npz["VDS"], npz["VS"],
                                       npz["ID_" + k], npz["GM_" + k], npz["GDS_" + k],
                                       npz["CGG_" + k], W_ref=5e-6)
lut = {"nmos": mk("n"), "pmos": mk("p")}
by = {t.name: t for t in trs}
roles = meta.get("device_roles", {})
diode = {n for n, t in by.items() if sr.is_diode_connected(t)}
L_ANCH = [float(v) for v in npz["L"]]
GM_GRID = [4.0 + 0.5 * i for i in range(46)]      # 4 ~ 26.5


def min_vgs(kind, vsb, L_list=None):
    """(gm_id, L)을 훑어 이 소자가 낼 수 있는 **최소 자기일관 Vgs**와 그 조건."""
    best = None
    for L in (L_list if L_list is not None else L_ANCH):
        for g in GM_GRID:
            try:
                v = sr.solve_diode_connected_vds(lut[kind], g, L, vsb)
            except sr.DiodeSelfConsistencyError:
                continue
            if best is None or v < best[0]:
                best = (v, g, L)
    return best


print("=== 각 diode 소자가 낼 수 있는 최소 Vgs ===")
print("%-8s %-5s %8s %9s | %9s %8s %9s" %
      ("소자", "kind", "현재gmid", "현재v*", "최소v*", "그때gmid", "그때L(um)"))
print("-" * 76)
lower = {}
for n in sorted(diode):
    e = sized[n]
    cur = None
    try:
        cur = sr.solve_diode_connected_vds(lut[e["kind"]], e["gm_id"], e["L"], e.get("vsb", 0.0))
    except sr.DiodeSelfConsistencyError:
        pass
    b = min_vgs(e["kind"], e.get("vsb", 0.0))
    lower[n] = b[0] if b else None
    print("%-8s %-5s %8.2f %9s | %9.4f %8.1f %9.3f"
          % (n, e["kind"], e["gm_id"], ("%.4f" % cur) if cur else "-",
             b[0], b[1], b[2] * 1e6))

# L을 현재 값으로 고정했을 때의 최소도 함께(레이아웃 제약을 존중하는 경우)
print()
print("=== 초과 스택의 원리적 가능성 ===")
grp = defaultdict(list)
for n in sized:
    vs = roles.get(n, {}).get("vertical_stack_id")
    if vs:
        grp[vs].append(n)
pairs = (meta.get("symmetry") or {}).get("matching_pairs") or []
parent = {n: n for n in sized}
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
for p in pairs:
    if p.get("matching_sensitivity") != "offset":
        continue
    ns = [x for x in p.get("names", []) if x in parent]
    for a, b in zip(ns, ns[1:]):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

OVER = ["biasgen_vom_battery_a", "biasgen_vop_battery_a", "vbias2_stack",
        "biasgen_vom_battery_b", "biasgen_vop_battery_b", "vbias3_stack", "cmfb_vocdes_gen"]
for vs in OVER:
    members = sorted(grp[vs])
    reps, seen = [], set()
    for m in members:
        r = find(m)
        if r in seen:
            continue
        seen.add(r); reps.append(m)
    ref = next((roles.get(m, {}).get("budget_reference_device") for m in members
                if roles.get(m, {}).get("budget_reference_device")), None)
    ref_vds = sized.get(ref, {}).get("vds") if ref else None
    budget = VDD - ref_vds if ref_vds is not None else VDD
    d_min = sum(lower[m] for m in reps if m in diode and lower[m] is not None)
    nd_cur = sum(sized[m].get("vds", 0.0) for m in reps if m not in diode)
    print()
    print("  [%s] 예산 %.4f V (ref=%s)" % (vs, budget, ref))
    print("    diode 최소합            %.4f V  (%s)"
          % (d_min, ", ".join("%s %.3f" % (m, lower[m]) for m in reps if m in diode)))
    print("    비-diode 현재합          %.4f V" % nd_cur)
    print("    최선(비-diode 그대로)    %.4f V -> %s"
          % (d_min + nd_cur, "가능" if d_min + nd_cur <= budget + 1e-9
             else "**불가 %.4f V 초과**" % (d_min + nd_cur - budget)))
    slack = budget - d_min
    print("    비-diode가 쓸 수 있는 몫  %.4f V %s"
          % (slack, "" if slack > 0 else "  <- diode만으로 이미 예산 초과"))
    if slack > 0 and any(m not in diode for m in reps):
        nd = [m for m in reps if m not in diode]
        print("      -> 비-diode %d개가 평균 %.4f V 이하로 내려가야 한다(현재 평균 %.4f V)"
              % (len(nd), slack / len(nd), nd_cur / len(nd)))
