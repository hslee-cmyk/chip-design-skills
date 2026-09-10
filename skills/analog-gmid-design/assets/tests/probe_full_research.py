# -*- coding: utf-8 -*-
"""B9/B20/B22/B25/B19' 착지 후 **파일럿 재탐색**(SLSQP 자유 탐색, 2026-09-10).

## 왜 이제 돌리는가

지금까지는 **고정 theta에서의 평가**만 확인했다. 엔진이 크게 바뀌었으므로
(vsb를 노드전압에서 유도, 적층 diode 연립, 미러 15소자 강제, `_solve_vgs` rightmost root)
자유 탐색이 찾는 진짜 최적점과 최종 metric을 다시 봐야 한다.

## 무엇을 재는가

  1. SLSQP 3 start x 60 iter -- 수렴 여부와 **iter당 실행시간**(계획 §10.3 B4의 예산 대조)
  2. 최종 metric 전부 + 선언된 제약 5개의 만족 여부
  3. 미러 3그룹의 VGS 퍼짐이 여전히 0인가(배선이 최적점에서도 유지되는가)
  4. vsb가 노드전압과 일치하는가(감사기 재확인)

결과는 **파일에도 남긴다** -- stdout만 쓰면 `| tail` 버퍼가 백그라운드 전환에서 통째로
날아간다(사용자 지시, 이 세션에서 실제로 한 번 더 겪었다). 한 줄 쓸 때마다 append하므로
중간에 죽어도 거기까지는 건진다.

실행: assets 디렉터리에서 `python tests/probe_full_research.py`
"""
import sys
import os
import json
import time
import collections

ASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASSETS)
import numpy as np
import sizing_recipe as sr

_RESULT = os.path.splitext(os.path.abspath(__file__))[0] + ".result.txt"
_first = [True]


def emit(*p):
    line = " ".join(str(x) for x in p)
    print(line, flush=True)
    mode = "w" if _first[0] else "a"
    _first[0] = False
    with open(_RESULT, mode, encoding="utf-8") as f:
        f.write(line + "\n")


TOPO = os.path.join(ASSETS, "library", "current_reuse_telescopic_ota.topology.json")
VDD = 1.8
d = np.load(os.path.join(ASSETS, "sky130_nfet_pfet_lut_sample.npz"))
mk = lambda k: sr.SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_" + k],
                                       d["GM_" + k], d["GDS_" + k], d["CGG_" + k],
                                       W_ref=5e-6, SID_1F=d["SID_1F_" + k])
nmos, pmos = mk("n"), mk("p")
SPEC = {
    "lut_by_kind": {"nmos": nmos, "pmos": pmos}, "lut": nmos, "vdd": VDD,
    "L_candidates": [float(v) for v in nmos.L_grid],
    "VDS_candidates": [0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.2, 1.4],
    "gm_id_grid": [float(4 + i) for i in range(21)],
    "L_min": 0.15e-6, "L_min_by_kind": {"nmos": 0.15e-6, "pmos": 0.15e-6},
    "W_bounds": (1e-6, 200e-6),
    "min_vds_by_role": {"cascode": 0.2, "tail": 0.3, "mirror": 0.3},
    "stage_objective": "power", "stage_w_max": 200e-6,
    "min_finger_w": 1e-6, "max_finger_w": 40e-6,
    "vth0_slope": {"nfet": 3.356e-3, "pfet": 5.856e-3},
    "t_lln": 30e-9, "PM_target_deg": 70.0,
    "Cc": 500e-15, "Cf": 500e-15, "Cs": 500e-15, "C_Ltot": 1e-12,
    "t_settle_total": 40e-9, "omega_c": 6.9 / 30e-9,
    "L_grid_step": 5e-9,
}

emit("=" * 96)
emit("파일럿 재탐색 (SLSQP 3 start x 60 iter)  --  2026-09-10")
emit("=" * 96)
emit("")
_t0 = time.perf_counter()
try:
    res = sr.optimize_full_circuit_budget(TOPO, SPEC, search_method="slsqp",
                                          slsqp_kwargs={"n_starts": 3, "maxiter": 60})
    _dt = time.perf_counter() - _t0
    emit(f"  재탐색 완료: {_dt:.1f}s")
except Exception as e:
    _dt = time.perf_counter() - _t0
    emit(f"  ★ 재탐색 실패({_dt:.1f}s): {type(e).__name__}")
    emit("  " + str(e)[:600])
    emit("")
    emit("완료(실패). 결과 파일:", _RESULT)
    raise SystemExit(1)

metrics = res["metrics"]
sized = res["sizing"]
theta = res["theta_star"] or {}

emit("")
emit("-" * 96)
emit("1. 최종 metric")
emit("-" * 96)
for k in sorted(metrics):
    emit(f"    {k:<28}{metrics[k]:>16.6g}")

topo = json.load(open(TOPO, encoding="utf-8"))
cons = (topo.get("sizing_roles") or {}).get("constraints") or []
emit("")
emit("-" * 96)
emit("2. 선언된 제약 만족 여부")
emit("-" * 96)
emit(f"    {'metric':<26}{'op':>5}{'목표':>10}{'실측':>14}{'판정':>8}")
emit("    " + "-" * 65)
n_bad = 0
for c in cons:
    v = metrics.get(c["metric"])
    if v is None:
        emit(f"    {c['metric']:<26}{c['op']:>5}{c['value']:>10}{'(없음)':>14}{'★':>8}")
        n_bad += 1
        continue
    ok = (v >= c["value"]) if c["op"] == ">=" else (v <= c["value"])
    n_bad += 0 if ok else 1
    emit(f"    {c['metric']:<26}{c['op']:>5}{c['value']:>10}{v:>14.4f}"
         f"{('OK' if ok else '★위반'):>8}")
emit("")
emit(f"    -> 위반 {n_bad}건")

emit("")
emit("-" * 96)
emit("3. 미러 3그룹의 VGS 퍼짐 (배선이 최적점에서도 유지되는가)")
emit("-" * 96)
deps = collections.defaultdict(list)
for n_, dr in topo["device_roles"].items():
    if isinstance(dr, dict) and dr.get("gm_id_match_vgs_of"):
        deps[dr["gm_id_match_vgs_of"]].append(n_)
BEFORE = {"M18_bg": 464.2, "M66": 663.2, "M36a": 9.2}
emit(f"    {'레퍼런스':<12}{'소자':>6}{'VGS 퍼짐(mV)':>16}{'배선 전(mV)':>14}")
emit("    " + "-" * 50)
for ref, ds in sorted(deps.items()):
    vs = []
    for m in [ref] + sorted(ds):
        e = sized[m]
        lut = SPEC["lut_by_kind"][e["kind"]]
        vs.append(lut.vgs_for_gm_id(e["gm_id"], e["L"], e["vds"], e.get("vsb", 0.0)))
    emit(f"    {ref:<12}{len(vs):>6}{(max(vs) - min(vs)) * 1e3:>16.4f}"
         f"{BEFORE.get(ref, float('nan')):>14.1f}")

emit("")
emit("-" * 96)
emit("4. vsb가 노드전압과 일치하는가 (B9 감사기 재확인)")
emit("-" * 96)
trs, _meta = sr.load_topology(TOPO)
by = {t.name: t for t in trs}
bad = sr.audit_vsb_consistency(by, sized, VDD)
emit(f"    전체 {len(by)}소자 중 불일치 {len(bad)}개 (세션 시작 시 26개)")
for r in bad[:8]:
    emit(f"      {r[0]:<8}{r[1]:<6}src={r[2]:<13}선언 {r[4]:>8.4f}  기대 {r[5]:>8.4f}"
         f"  차이 {r[6]:>+8.4f}")

emit("")
emit("-" * 96)
emit("5. theta_star")
emit("-" * 96)
for k in sorted(theta):
    emit(f"    {k:<24}{theta[k]:>14.6g}")

json.dump({k: float(v) for k, v in theta.items()},
          open(os.path.splitext(os.path.abspath(__file__))[0] + ".theta_star.json",
               "w", encoding="utf-8"), indent=1)
emit("")
emit("완료. 결과 파일:", _RESULT)
