# -*- coding: utf-8 -*-
"""등록된 metric들을 stage-local / stage-분해가능 / 기약 전역 3티어로 실측 분류하는 조사 도구.

계획 문서 §7.6 "B2 해소 -- metric은 3티어이고 게이트도 3티어여야 한다"(v4.4)의 근거다.

방법: 전체 사이징된 ctx와 **stage1 소자만 담은 ctx** 둘로 같은 metric을 호출해 본다.
      후자가 성공하면 stage-local, KeyError면 전역 전용이다.

측정 결과(2026-09-07, current_reuse_telescopic_ota 13개 metric):
  T1 stage-local  : power_uA / area_um2 / mismatch_sigma_mV / noise_v_rthz     0.002~0.006 ms
  T2 stage-분해가능: gain_stages_sum (stage별 합 = 전체, 차이 0.00e+00)          0.003 ms
  T3 기약 전역     : cmrr/psrr/gain_full_circuit/classab/rail level/rz          0.15~0.29 ms

이 분류가 중요한 이유: T3는 `_full_circuit_devices()`가 topology의 **모든** 소자를 요구하므로
stage 사이징 도중에는 원리적으로 계산할 수 없다(`extra_feasible` 콜백 불가). 반대로 T2가
정확히 분해된다는 사실은 §7.9의 배분 DP가 대리 함수가 아니라 진짜 metric을 쓸 수 있게 해준다.

주의: noise metric(`flicker_plus_thermal_sum`)은 LUT을 만들 때 `SID_1F=`를 넘겨야 한다.
      안 넘기면 전체 사이징에서도 실패하는데 그건 엔진 결함이 아니라 LUT 구성 누락이다.

실행: assets 디렉터리에서 `python tests/probe_metric_tiers.py`
(자동 테스트가 아니라 조사용.)
"""
import os, sys, json, time, dataclasses
ASSETS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # probes -> tests -> assets
sys.path.insert(0, ASSETS)
import numpy as np, sizing_recipe as sr
TOPO = os.path.join(ASSETS, "..", "assets", "library", "current_reuse_telescopic_ota.topology.json")
INST = os.path.join(ASSETS, "workspaces", "current-reuse-telescopic-ota-report", "current_reuse_telescopic_ota.instance.json")
trs, meta = sr.load_topology(TOPO)
sized0 = json.load(open(INST, encoding="utf-8"))["sizing"]
kind_of = {t.name: t.kind for t in trs}
d = np.load(os.path.join(ASSETS, "..", "assets", "sky130_nfet_pfet_lut_sample.npz"))
mk=lambda k: sr.SemiEmpiricalGmIdLUT(d["L"],d["VGS"],d["VDS"],d["VS"],d["ID_"+k],d["GM_"+k],d["GDS_"+k],d["CGG_"+k],W_ref=5e-6)
spec={"lut_by_kind":{"nmos":mk("n"),"pmos":mk("p")},"lut":mk("n"),"vdd":1.8,
      "vth0_slope":{"nfet":3.356e-3,"pfet":5.856e-3}}
fields={f.name for f in dataclasses.fields(sr.SizingContext)}
def ctx_of(sz):
    kw={}
    for k,v in (("sized",sz),("spec",spec),("topology_path",TOPO),("kind_of",kind_of),
                ("derived",{}),("seed_currents",{}),("mirror_ratios",{})):
        if k in fields: kw[k]=v
    return sr.SizingContext(**kw)
metrics=(meta.get("sizing_roles") or {}).get("metrics") or {}
stage1=["M1a","M1b","M4a","M4b","M2a","M2b","M3a","M3b"]
partial={k:v for k,v in sized0.items() if k in stage1}
print("%-26s %-26s %-12s %10s  %s"%("metric","type","stage-local?","비용(ms)","비고"))
print("-"*104)
tiers={"local":[], "global":[]}
for nm, ms in metrics.items():
    try:
        full=sr.compute_metric(ms, ctx_of(sized0))
    except Exception as e:
        print("%-26s %-26s %-12s %10s  전체에서도 실패: %s"%(nm,ms.get("type"),"-","-",str(e)[:40])); continue
    try:
        sr.compute_metric(ms, ctx_of(partial)); local=True; note=""
    except Exception as e:
        local=False; note=type(e).__name__+": "+str(e)[:46]
    N=20; t0=time.perf_counter()
    for _ in range(N): sr.compute_metric(ms, ctx_of(sized0))
    cost=(time.perf_counter()-t0)/N*1e3
    tiers["local" if local else "global"].append(nm)
    print("%-26s %-26s %-12s %10.3f  %s"%(nm, ms.get("type"), "YES" if local else "NO", cost, note))
print()
print("stage-local 가능(%d): %s"%(len(tiers["local"]), tiers["local"]))
print("전역 전용(%d)      : %s"%(len(tiers["global"]), tiers["global"]))
