# -*- coding: utf-8 -*-
"""L_combo 전수 스캔의 실행시간 예산을 실측하는 조사 도구.

계획 문서 §7.6 "B4 해소 -- 실행시간 예산"(v4.6)의 근거다.

핵심: L_combo 하나당 비용은 **stage 사이징이 아니라 전체 평가 1회**다. 전역 게이트(cmrr/psrr)가
topology의 모든 소자를 요구하기 때문이다(§7.6 B2). 이걸 혼동하면 예산이 44배 틀린다
(stage 2개 6.3ms vs 전체 평가 274.5ms).

측정 결과(2026-09-08, current_reuse_telescopic_ota, L 자유도 3개):
  _build_theta_evaluator()   69 ms   (1회성)
  presolve_warm_start()      16.5 s  (1회성 -- L_combo 루프 안에 들어가면 안 된다)
  전체 평가 1회              274.5 ms
  L_combo 전수(앵커 4^3=64)  17.6 s   -> 중첩(레이아웃 5회 x VDS 2회) 175.7 s = 2.9분
  densify 41점(41^3)         5.3시간  -> 기본 금지

주의: theta 중간값은 infeasible이라(실측) `presolve_warm_start()`가 찾은 feasible 지점을
기준으로 L만 흔들어 잰다. infeasible combo가 섞이는 것은 정상이다(12개 중 2개).

실행: assets 디렉터리에서 `python tests/probe_runtime_budget.py`
(자동 테스트가 아니라 조사용. 웜스타트 때문에 20초 이상 걸린다.)
"""
import os, sys, time, json, tempfile
ASSETS = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets"
sys.path.insert(0, ASSETS)
sys.path.insert(0, os.path.join(ASSETS, "..", "..", "..", "workspaces"))
import numpy as np, sizing_recipe as sr
import run_harness as H

TOPO = os.path.join(ASSETS, "library", "current_reuse_telescopic_ota.topology.json")
d = np.load(os.path.join(ASSETS, "sky130_nfet_pfet_lut_sample.npz"))
mk = lambda k: sr.SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_" + k],
                                       d["GM_" + k], d["GDS_" + k], d["CGG_" + k],
                                       W_ref=5e-6, SID_1F=d["SID_1F_" + k])
nmos, pmos = mk("n"), mk("p")
# 2026-09-10 -- 손으로 복붙한 spec 블록을 폐기하고 **정본**을 쓴다. 복제본은 정본과
# 갈려 있었다(gm_id_grid 21점 vs 57점, L_candidates 12점 vs 41점, VDS_candidates 9점 vs
# 13점, stage_power_tolerance 누락). 같은 블록이 여러 파일에 그대로 퍼져 있었으므로
# 파일마다 다른 판단을 한 게 아니라 복제본 하나가 번진 것이다. 이제
# `sizing_recipe.require_declared_spec_source()`가 라이브러리 회로에 출처 선언을 강제하고,
# 일부러 다르게 쓸 때는 `H.derived_spec(key, why, **overrides)`로 무엇을 왜 바꿨는지 남긴다.
spec = H.canonical_spec("current_reuse_telescopic_ota")
nmos = spec["lut_by_kind"]["nmos"]
pmos = spec["lut_by_kind"]["pmos"]

t0 = time.perf_counter()
ev = sr._build_theta_evaluator(TOPO, spec)
t_build = time.perf_counter() - t0
thetas = ev["thetas"]
print("evaluator 빌드 1회: %.1f ms (theta %d개)" % (t_build * 1e3, len(thetas)))

evaluate = ev["evaluate"]
# 중간값은 infeasible이라(실측) 웜스타트가 찾은 feasible 지점을 기준점으로 쓴다
t0 = time.perf_counter()
warm = sr.presolve_warm_start(TOPO, spec, ev=ev)
print("presolve_warm_start: %.1f s" % (time.perf_counter() - t0))
mid = dict(warm["x0"])

# 워밍업 + 성공 여부 확인
try:
    t0 = time.perf_counter()
    ctx, metrics = evaluate(dict(mid))
    t_first = time.perf_counter() - t0
    print("첫 평가: %.1f ms, sized %d소자" % (t_first * 1e3, len(ctx.sized)))
except Exception as e:
    print("평가 실패:", type(e).__name__, str(e)[:150])
    sys.exit(0)

# L theta만 흔들어 L_combo 하나당 비용을 잰다
L_names = [t["name"] for t in thetas if t["name"].startswith("L_")]
print("L theta:", L_names)
L_anchors = [1.5e-7, 3.5e-7, 5.0e-7, 1.0e-6]
import itertools
combos = list(itertools.product(L_anchors, repeat=len(L_names)))
print("L_combo 전수 = %d개 (앵커 %d^%d)" % (len(combos), len(L_anchors), len(L_names)))

N = min(12, len(combos))
ok = 0
t0 = time.perf_counter()
for c in combos[:N]:
    tv = dict(mid)
    for nm, v in zip(L_names, c):
        tv[nm] = v
    try:
        evaluate(tv); ok += 1
    except Exception:
        pass
dt = (time.perf_counter() - t0) / N
print()
print("=== L_combo 1개당 전체 평가 비용 ===")
print("  %d개 실측 평균: %.1f ms  (성공 %d/%d)" % (N, dt * 1e3, ok, N))
print()
print("=== L_combo 전수 스캔 총비용 ===")
for n, lab in ((4, "bounds 내 앵커 4"), (7, "LUT 전체 앵커 7"),
               (11, "0.05um 등간격 ~11"), (41, "densify 41")):
    tot = n ** len(L_names) * dt
    print("  %-22s %8d combo -> %10.1f s  (%.1f 분)" % (lab, n ** len(L_names), tot, tot / 60))
print()
print("=== 중첩 루프 (레이아웃 수렴 x VDS 재배분) ===")
base = 4 ** len(L_names) * dt
for o, i, lab in ((1, 1, "단일 패스"), (1, 2, "VDS 2회"), (5, 2, "레이아웃 5회 x VDS 2회")):
    print("  %-28s %8.1f s (%.1f 분)" % (lab, base * o * i, base * o * i / 60))
