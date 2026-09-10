# -*- coding: utf-8 -*-
"""`parasitic_pm_deg`(§7.11)를 **4개 회로 전부**에서 재는 조사 도구(2026-09-10).

## 왜 재는가

두 가지를 동시에 확인한다:

  1. **상한을 정할 근거** -- 이 metric을 constraint로 걸려면 값을 지어내지 말고
     여러 회로에서 먼저 재야 한다(`mirror_ratio_error`/`kcl_residual`과 같은 선례).
  2. **일반성 검증** -- 이 metric이 토폴로지에 안 묶여 있는가. 특히
     `undetermined`(고임피던스인데 용량을 못 세는 노드)가 다른 회로에서도 0인지.

## 경로 선언에 대하여 -- ★ 확인 필요

`parasitic_pm_deg`는 "어느 경로의 위상여유인가"를 선언에서 받는다(전 노드를 세면
bias 노드가 각각 ~90도를 먹어 -1004도가 나온다, §7.11). 그런데 4개 회로 중:

    current_reuse_telescopic_ota   `gain_full_circuit_db`가 이미 선언 -> **그대로 사용**
    two_stage_ota                  `gain_db`(smallsignal)가 이미 선언 -> **그대로 사용**
    folded_cascode                 선언 없음 -> 넷리스트 이름에서 **제안**(vin_p/vin_n -> out)
    nmcnr_amplifier                선언 없음 -> 넷리스트 이름에서 **제안**(Vin_p/Vin_n -> Vout)

뒤의 둘은 **이 스크립트가 주입할 뿐 토폴로지를 고치지 않는다** -- 경로 판정은 회로위상
해석이라 사용자 확인 후에 선언으로 넣는다. 여기서는 "값이 나오는지"만 본다.

`excite`에서 **0으로 여기된 단자는 AC 접지**라 신호원으로 세지 않는다(two_stage_ota의
`bias`/`vdd`가 그 경우).

실행: assets 디렉터리에서 `python tests/probe_parasitic_pm_all_circuits.py`
"""
import sys
import os
import json
import math
import time

ASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASSETS)
sys.path.insert(0, os.path.join(ASSETS, "..", "..", "..", "workspaces"))
import numpy as np
import sizing_recipe as sr
import run_harness as H

_RESULT = os.path.splitext(os.path.abspath(__file__))[0] + ".result.txt"
_first = [True]


def emit(*p):
    line = " ".join(str(x) for x in p)
    print(line, flush=True)
    mode = "w" if _first[0] else "a"
    _first[0] = False
    with open(_RESULT, mode, encoding="utf-8") as f:
        f.write(line + "\n")


# 경로: 선언이 있으면 그것을, 없으면 제안(★표시)
PATHS = {
    "current_reuse_telescopic_ota": ({"Vip", "Vim"}, {"Vop", "Vom"}, "선언(gain_full_circuit_db)"),
    "two_stage_ota":                ({"vin_p", "vin_n"}, {"OUT"},    "선언(gain_db)"),
    "folded_cascode":               ({"vin_p", "vin_n"}, {"out"},    "★제안(넷 이름)"),
    "nmcnr_amplifier":              ({"Vin_p", "Vin_n"}, {"Vout"},   "★제안(넷 이름)"),
}
# current_reuse는 SLSQP가 비싸므로 이미 구해둔 theta를 재사용한다(있으면).
CACHED = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "probe_node_voltage_audit.theta_star.json")

emit("=" * 100)
emit("parasitic_pm_deg -- 4개 회로 전수 (2026-09-10, §7.11)")
emit("=" * 100)

summary = []
for name in ("current_reuse_telescopic_ota", "two_stage_ota",
             "folded_cascode", "nmcnr_amplifier"):
    cfg = H.SPECS[name]
    topo = os.path.join(ASSETS, "library", cfg["topology_file"])
    spec = cfg["spec_fn"]()
    ex, sn, how = PATHS[name]
    emit("")
    emit("-" * 100)
    emit(f"[{name}]   경로: {sorted(ex)} -> {sorted(sn)}   ({how})")
    emit("-" * 100)
    t0 = time.perf_counter()
    try:
        if name == "current_reuse_telescopic_ota" and os.path.exists(CACHED):
            env = sr._build_theta_evaluator(topo, spec)
            ctx, metrics = env["evaluate"](json.load(open(CACHED, encoding="utf-8")))
            emit(f"  (캐시 theta 재사용, {time.perf_counter()-t0:.1f}s)")
        else:
            kw = {"grid_points_per_theta": cfg.get("grid_points_per_theta", 5)}
            if cfg.get("search_method"):
                kw["search_method"] = cfg["search_method"]
            if cfg.get("slsqp_kwargs"):
                kw["slsqp_kwargs"] = cfg["slsqp_kwargs"]
            res = sr.optimize_full_circuit_budget(topo, spec, **kw)
            env = sr._build_theta_evaluator(topo, spec)
            ctx, metrics = env["evaluate"](res["theta_star"] or {})
            emit(f"  (사이징 {time.perf_counter()-t0:.1f}s)")
    except Exception as e:
        emit(f"  ★ 사이징 실패: {type(e).__name__}: {str(e)[:200]}")
        summary.append((name, None, None, None, f"사이징 실패({type(e).__name__})"))
        continue

    by, _p = sr._load_full_topology_cached(topo)
    omega_c = spec.get("omega_c")
    if not omega_c:
        emit("  ★ spec에 omega_c가 없다 -- 이 회로는 크로스오버 기준이 선언돼 있지 않다")
        summary.append((name, None, None, None, "omega_c 없음"))
        continue
    path = sr.signal_path_nodes(by, ex, sn)
    rep = sr.node_pole_estimate(by, ctx.sized, spec, only=path)
    f_c = omega_c / (2 * math.pi)
    emit(f"  f_c = {f_c/1e6:.2f} MHz   경로 노드 {len(path)}개 -> 셀 수 있음 "
         f"{len(rep['poles'])} / 저임피던스 제외 {len(rep['skipped_low_impedance'])} / "
         f"★못셈 {len(rep['undetermined'])}")
    if rep["undetermined"]:
        emit(f"    ★ 못 세는 노드: {rep['undetermined']}")
    if not rep["poles"]:
        summary.append((name, None, None, len(rep["undetermined"]), "셀 수 있는 pole 없음"))
        continue
    emit(f"    {'노드':<14}{'f_pole(MHz)':>14}{'f_pole/f_c':>12}{'위상(도)':>11}")
    emit("    " + "-" * 51)
    tot = 0.0
    for n_, w in sorted(rep["poles"].items(), key=lambda kv: kv[1]):
        ph = math.degrees(math.atan(omega_c / w))
        tot += ph
        emit(f"    {n_:<14}{w/(2*math.pi)/1e6:>14.2f}{w/omega_c:>12.2f}{ph:>11.3f}")
    pm = 90.0 - tot
    pmt = spec.get("PM_target_deg")
    emit(f"    -> PM_parasitic = 90 - {tot:.3f} = **{pm:.3f}도**"
         + (f"   (PM_target {pmt}도)" if pmt else ""))
    summary.append((name, pm, pmt, len(rep["undetermined"]), ""))

emit("")
emit("=" * 100)
emit("요약")
emit("=" * 100)
emit("")
emit(f"  {'회로':<32}{'PM_parasitic':>14}{'PM_target':>11}{'못셈':>7}   비고")
emit("  " + "-" * 84)
for name, pm, pmt, und, note in summary:
    emit(f"  {name:<32}"
         + (f"{pm:>14.3f}" if pm is not None else f"{'--':>14}")
         + (f"{pmt:>11}" if pmt else f"{'--':>11}")
         + (f"{und:>7}" if und is not None else f"{'--':>7}")
         + f"   {note}")
emit("")
emit("완료. 결과 파일:", _RESULT)
