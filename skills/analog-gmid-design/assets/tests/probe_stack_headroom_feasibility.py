# -*- coding: utf-8 -*-
"""B1 배선 전 사전계산 1/2 -- diode 자기일관 vds가 스택 KVL 예산에 들어가는가(계획 §7.3, v4.13).

배선 후에 `allocate_stack_headroom()`의 "합=vdd" assert로 알게 되면 원인을 되짚기 어려우므로
**미리** 전수 계산한다. 값-동일 그룹(offset 매칭 쌍)은 대표 1개만 합산하고, budget_reference_
device가 선언된 스택은 예산을 `vdd - ref_vds`로 잡는다(엔진 관례와 동일).

측정 결과(2026-09-08, current_reuse_telescopic_ota):
  22개 스택 중 **7개 초과**. 최대는 biasgen_vom/vop_battery_a 로 3.146 V vs 예산 1.800 V.
  **가장 걱정했던 M36a/M36b(1.361V 요구)는 문제가 아니었다** -- cmfb_load_a/b가 각각 단독
  컬럼이라 여유 0.439V가 남는다. 실제 병목은 **diode 2개가 직렬로 쌓인 컬럼**이다
  (M11a+M11b 각 0.873V에 비-diode M12의 1.400V가 더해져 3.146V).

원리적 가능성 판정은 짝 스크립트 `probe_diode_min_vgs.py` 참고 -- 결론은 "불가능한 스택은
하나도 없다"다.

실행: assets 디렉터리에서 `python tests/probe_stack_headroom_feasibility.py`
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

trs, meta = sr.load_topology(TOPO)
sized = json.load(open(INST, encoding="utf-8"))["sizing"]
for v in sized.values():
    if "vs" in v and "vsb" not in v:
        v["vsb"] = v.pop("vs")
npz = np.load(os.path.join(ASSETS, "sky130_nfet_pfet_lut_sample.npz"))
mk = lambda k: sr.SemiEmpiricalGmIdLUT(npz["L"], npz["VGS"], npz["VDS"], npz["VS"],
                                       npz["ID_" + k], npz["GM_" + k], npz["GDS_" + k],
                                       npz["CGG_" + k], W_ref=5e-6)
lut = {"nmos": mk("n"), "pmos": mk("p")}
by = {t.name: t for t in trs}
roles = meta.get("device_roles", {})
diode = {n for n, t in by.items() if sr.is_diode_connected(t)}

# diode 자기일관해 미리 계산
star = {}
for n in diode:
    e = sized[n]
    try:
        star[n] = sr.solve_diode_connected_vds(lut[e["kind"]], e["gm_id"], e["L"], e.get("vsb", 0.0))
    except sr.DiodeSelfConsistencyError:
        star[n] = None

# vertical_stack_id 그룹
grp = defaultdict(list)
for n in sized:
    vs = roles.get(n, {}).get("vertical_stack_id")
    if vs:
        grp[vs].append(n)

# matching_pairs 의 offset 그룹은 값-동일로 묶여 예산에 한 번만 들어간다(엔진 관례)
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

print("%-26s %2s %2s %9s %9s %9s %9s  %s" %
      ("vertical_stack_id", "n", "d", "현재합", "신규합", "예산", "여유", "판정"))
print("-" * 104)
danger = []
for vs in sorted(grp):
    members = sorted(grp[vs])
    reps, seen = [], set()
    for m in members:                       # 값-동일 그룹당 대표 1개만 합산
        r = find(m)
        if r in seen:
            continue
        seen.add(r); reps.append(m)
    ref = None
    for m in members:
        rd = roles.get(m, {}).get("budget_reference_device")
        if rd:
            ref = rd; break
    ref_vds = sized.get(ref, {}).get("vds") if ref else None
    budget = VDD - ref_vds if ref_vds is not None else VDD
    cur = sum(sized[m]["vds"] for m in reps if sized.get(m, {}).get("vds") is not None)
    new = 0.0; unknown = False
    for m in reps:
        if m in diode:
            if star.get(m) is None:
                unknown = True; break
            new += star[m]
        else:
            new += sized[m].get("vds", 0.0)
    nd = sum(1 for m in reps if m in diode)
    if unknown:
        verdict = "diode 해 없음"
    elif new <= budget + 1e-9:
        verdict = "OK"
    else:
        verdict = "★ 초과 %.3fV" % (new - budget)
        danger.append((vs, members, new, budget))
    print("%-26s %2d %2d %9.4f %9.4f %9.4f %+9.4f  %s"
          % (vs, len(reps), nd, cur, new, budget, budget - new, verdict))

print()
print("=" * 104)
print("예산 초과 스택: %d개" % len(danger))
for vs, members, new, budget in danger:
    print()
    print("  [%s]  필요 %.4f V > 예산 %.4f V  (초과 %.4f V)" % (vs, new, budget, new - budget))
    for m in sorted(members):
        e = sized[m]
        mark = "diode" if m in diode else "     "
        v_new = star.get(m) if m in diode else e.get("vds")
        print("    %-8s %-5s %s  현재 %.4f -> %s  (gm_id=%.2f, L=%.3fum)"
              % (m, e.get("kind"), mark, e.get("vds", float("nan")),
                 ("%.4f" % v_new) if v_new is not None else "해없음",
                 e.get("gm_id", float("nan")), e.get("L", 0) * 1e6))
