# -*- coding: utf-8 -*-
"""L 탐색 범위를 knee 창으로 좁혀도 되는지 전수 스캔으로 확인하는 조사 도구.

계획 문서 §7.6 "L 탐색 범위 -- knee 창 + 경계 검사"(v4.7)의 근거다.

배경: §7.10은 L knee가 항상 2~3 x L_min이라 했고, §7.7 R4는 "지름길 없이 전수 스캔"을 요구한다.
둘 다 실측 근거가 있어 말로는 못 가리므로, LUT 전 앵커(7 x 3그룹 = 343 combo)를 전수로 돌려
**최적 L이 실제로 어디에 오는지** 본다.

측정 결과(2026-09-08, current_reuse_telescopic_ota):

  면적 예산        전수 최적 L(um)         knee창(<=0.5um) 손해   창 밖?
  무제약           [0.5, 0.15, 1.5]        +1.24%                 예
  <= 500 um2       [0.5, 0.15, 1.5]        +1.24%                 예
  <= 200 um2       [0.5, 0.15, 0.5]        +0.00%                 아니오

**면적 제약이 제대로 걸리면 최적이 knee 창 안으로 들어온다.** 상위 10개 L 분포도 이동해
<=200um2에서는 0.35um이 최다가 되는데, 이는 §7.10의 knee 예측(0.30~0.45um) 한가운데다.

부수 관찰: 전력 스프레드는 6.7%(454~484uA)인데 면적 스프레드는 40배(47~1902um2)다 --
**L 선택은 전력이 아니라 면적을 정한다.** 면적을 제약으로 걸지 않으면 L 탐색은 신호를 못 받는다.

⚠️ 단위 주의(A12): 엔진 metric은 이름과 달리 SI로 반환한다 -- `power_uA` -> A,
   `area_um2` -> m^2. 이 스크립트는 표시 전에 1e6 / 1e12를 곱해 환산한다.

실행: assets 디렉터리에서 `python tests/probe_L_search_window.py`
(자동 테스트가 아니라 조사용. 웜스타트 16.5s + 343 combo 73s = 90초 이상 걸린다.)
"""
import os, sys, time, json, itertools, tempfile
ASSETS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # probes -> tests -> assets
sys.path.insert(0, ASSETS)
sys.path.insert(0, os.path.join(ASSETS, "workspaces"))
import numpy as np, sizing_recipe as sr
import run_harness as H

TOPO_SRC = os.path.join(ASSETS, "..", "assets", "library", "current_reuse_telescopic_ota.topology.json")
topo = json.load(open(TOPO_SRC, encoding="utf-8"))
# L theta bounds를 LUT 전 구간으로 넓힌다(원본은 [0.15,1.0]um라 앵커 4개만 든다)
for th in topo["sizing_roles"]["theta"]:
    if th["name"].startswith("L_"):
        th["bounds"] = [1.5e-7, 4.0e-6]
TOPO = os.path.join(tempfile.gettempdir(), "knee_scan.topology.json")
json.dump(topo, open(TOPO, "w", encoding="utf-8"))

d = np.load(os.path.join(ASSETS, "..", "assets", "sky130_nfet_pfet_lut_sample.npz"))
mk = lambda k: sr.SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_" + k],
                                       d["GM_" + k], d["GDS_" + k], d["CGG_" + k],
                                       W_ref=5e-6, SID_1F=d["SID_1F_" + k])
nmos, pmos = mk("n"), mk("p")
# 2026-09-10 -- 손으로 복붙한 spec 블록을 폐기하고 **정본**을 쓴다. 복제본은 정본과
# 갈려 있었다(gm_id_grid 21점 vs 57점, L_candidates 12점 vs 41점, VDS_candidates 9점 vs
# 13점, stage_power_tolerance 누락). 같은 블록이 여러 파일에 그대로 퍼져 있었으므로
# 파일마다 다른 판단을 한 게 아니라 복제본 하나가 번진 것이다. 이제
# `sizing_recipe.require_declared_spec_source()`가 라이브러리 회로에 출처 선언을 강제한다.
spec = H.canonical_spec("current_reuse_telescopic_ota")
nmos = spec["lut_by_kind"]["nmos"]
pmos = spec["lut_by_kind"]["pmos"]

ev = sr._build_theta_evaluator(TOPO, spec)
warm = sr.presolve_warm_start(TOPO, spec, ev=ev)
base = dict(warm["x0"])
evaluate = ev["evaluate"]
L_names = [t["name"] for t in ev["thetas"] if t["name"].startswith("L_")]
ANCH = [float(v) for v in d["L"]]
L_MIN = 0.15e-6
print("L theta:", L_names)
print("앵커(um):", [round(v * 1e6, 2) for v in ANCH])
print("§7.10 knee 예측: %.2f ~ %.2f um (2~3 x L_min)" % (2 * L_MIN * 1e6, 3 * L_MIN * 1e6))
print()

rows = []
t0 = time.perf_counter()
for combo in itertools.product(ANCH, repeat=len(L_names)):
    tv = dict(base)
    for nm, v in zip(L_names, combo):
        tv[nm] = v
    try:
        ctx, met = evaluate(tv)
    except Exception as e:
        rows.append((combo, None, None, None, type(e).__name__))
        continue
    rows.append((combo, met.get("power_uA"), met.get("area_um2"),
                 met.get("gain_db"), None))
dt = time.perf_counter() - t0
# 엔진 metric은 SI로 반환한다(이름과 달리): power_uA -> A, area_um2 -> m^2. 표시용으로 환산.
conv = [(c, (p * 1e6 if p is not None else None), (a * 1e12 if a is not None else None), g, e)
        for (c, p, a, g, e) in rows]
ok = [r for r in conv if r[4] is None and r[1] is not None]
print("343 combo 전수: %.1f s, 성공 %d / 실패 %d" % (dt, len(ok), len(conv) - len(ok)))
print("환산 후 범위: power %.1f~%.1f uA, area %.1f~%.1f um2"
      % (min(r[1] for r in ok), max(r[1] for r in ok),
         min(r[2] for r in ok if r[2]), max(r[2] for r in ok if r[2])))
print()

ANCHu = [round(v * 1e6, 2) for v in ANCH]
KNEE = [v for v in ANCH if v <= 0.5e-6]

for AREA_BUDGET, lab in ((None, "면적 무제약(v3.3 이전)"), (500.0, "면적 <= 500 um2"),
                          (200.0, "면적 <= 200 um2 (v3.3 정신)")):
    feas = [r for r in ok if r[3] is not None and r[3] >= 54.0
            and (AREA_BUDGET is None or (r[2] is not None and r[2] <= AREA_BUDGET))]
    print("=" * 92)
    print("%s -- feasible %d개" % (lab, len(feas)))
    if not feas:
        print("  feasible 없음"); print(); continue
    best = min(feas, key=lambda r: r[1])
    print("  전수 최적: L=%s um  power=%.2f uA  area=%.1f um2  gain=%.2f dB"
          % ([round(v*1e6,2) for v in best[0]], best[1], best[2] or -1, best[3]))
    from collections import Counter
    c = Counter()
    for r in sorted(feas, key=lambda x: x[1])[:10]:
        for v in r[0]: c[round(v*1e6,2)] += 1
    print("  상위10 L 분포:", dict(sorted(c.items())))
    inwin = [r for r in feas if all(v in KNEE for v in r[0])]
    if inwin:
        b2 = min(inwin, key=lambda r: r[1])
        print("  knee창(<=0.5um, 27combo) 최적: L=%s power=%.2f uA -> 손해 %+.2f%% "
              % ([round(v*1e6,2) for v in b2[0]], b2[1], (b2[1]-best[1])/best[1]*100))
        edge = [n for n, v in zip(L_names, best[0]) if v > 0.5e-6]
        print("  전수 최적이 창 밖으로 나간 축: %s" % (edge or "없음(창 안이 곧 전수 최적)"))
    else:
        print("  knee창 안에 feasible 없음")
    print()
