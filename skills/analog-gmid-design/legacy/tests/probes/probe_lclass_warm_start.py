# -*- coding: utf-8 -*-
"""`l_class` theta의 웜스타트 -- 어떤 제약이 걸리고, x0를 받고, 자유변수로 남는가 (2026-09-10).

## 왜 쟀나

사용자 지시: *"warm start에 l_class 포함해서 재탐색해"*.

`search_stage_budget_L_warm_start()`에 타입 하나 추가하면 끝나는 일이 아니었다. 두 가지를
먼저 재야 했다:

  1. **`l_class` theta에 걸리는 제약이 무엇인가.** 기존 고속경로 두 갈래
     (`gain_stages_sum` 방향 판정 / `battery_centering_deviation` 최소화)는 "이 theta의
     devices만 보면 방향을 안다"는 전제 위에 있다. 그 전제가 성립하는지 확인해야 한다.
  2. **웜스타트가 정한 theta는 SLSQP 자유변수에서 빠진다**(`_optimize_theta_slsqp()`의
     `held_names = vote_determined | stage_budget_L`). `l_class`가 거기 들어가면 층3이
     만든 설계 자유도(동치류 공통 L을 탐색이 정한다)를 격자점에 얼리는 셈이다.

**아무것도 고치지 않는다 -- 표만 만든다.**

실행: assets 디렉터리에서 `python tests/probe_lclass_warm_start.py`
"""
import sys
import os
import time

ASSETS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # probes -> tests -> assets
sys.path.insert(0, ASSETS)
sys.path.insert(0, os.path.join(ASSETS, "workspaces"))
import sizing_recipe as sr
import run_harness as H

_RESULT = os.path.splitext(os.path.abspath(__file__))[0] + ".result.txt"
_first = [True]


def emit(*p):
    line = " ".join(str(x) for x in p)
    print(line, flush=True)
    with open(_RESULT, "w" if _first[0] else "a", encoding="utf-8") as f:
        f.write(line + "\n")
    _first[0] = False


emit("=" * 100)
emit("l_class 웜스타트 -- 걸린 제약 / x0 / 자유변수 유지 (4개 회로 전수)")
emit("=" * 100)

for key, cfg in H.SPECS.items():
    topo = os.path.join(ASSETS, "..", "assets", "library", cfg["topology_file"])
    spec = H.canonical_spec(key)
    emit("")
    emit("-" * 100)
    emit(f"[{key}]")
    ev = sr._build_theta_evaluator(topo, spec)
    ms, cons = ev["metrics_specs"], ev["constraints"]

    lc_names = []
    for th in ev["thetas"]:
        f = th.get("feeds")
        if not isinstance(f, dict) or f.get("type") not in ("metric_stage_budget", "l_class"):
            continue
        devs = set(f.get("devices") or ())
        touch = []
        for c in cons:
            fp = sr._metric_device_footprint(c["metric"], ms)
            if fp == "ALL":
                touch.append(f"{c['metric']}[ALL/{ms[c['metric']]['type']}]")
            elif devs & fp:
                touch.append(f"{c['metric']}[{ms[c['metric']]['type']}]")
        if f["type"] == "l_class":
            lc_names.append(th["name"])
        emit(f"  {th['name']:<18} {f['type']:<20} "
             f"bounds=[{th['bounds'][0]*1e6:.3f},{th['bounds'][1]*1e6:.3f}]um n_dev={len(devs)}")
        emit(f"      제약: {touch if touch else '없음'}")

    if not lc_names:
        emit("  l_class theta 없음 -- 이 변경은 이 회로에서 무동작이다")
        continue

    # ── 웜스타트가 실제로 무엇을 정하는가 ──────────────────────────────────
    t0 = time.time()
    try:
        w = sr.presolve_warm_start(topo, spec, ev=ev)
    except Exception as e:
        emit(f"  ★ 웜스타트 실패: {type(e).__name__}: {str(e)[:160]}")
        continue
    emit("")
    emit(f"  웜스타트 {time.time()-t0:.1f}s  x0 feasible={w['feasible']}")
    emit(f"    stage_budget_L(SLSQP 자유변수에서 **제외**) = {w['stage_budget_L']}")
    emit(f"    l_class_L(x0만 받고 자유변수 **유지**)      = {w['l_class_L']}")
    for n in w["l_class_L"]:
        emit(f"      x0 {n} = {w['x0'][n]*1e6:.4f}um")

    # ── 실제로 자유변수로 남는지 (held_names 계산을 그대로 재현) ────────────
    held = set(w["vote_determined"]) | set(w["stage_budget_L"])
    graph = w["dependency_graph"]
    free = [t["name"] for t in ev["thetas"]
            if t["bounds"][0] != t["bounds"][1] and t["name"] not in held
            and graph.get(t["name"], {}).get("classification") in ("coupled", "ambiguous")]
    kept = [n for n in lc_names if n in free]
    emit(f"    SLSQP 자유변수 {len(free)}개 -- 그중 l_class {len(kept)}/{len(lc_names)}개: {kept}")
    if len(kept) != len(lc_names):
        emit("    ★★ l_class가 자유변수에서 빠졌다 -- 층3의 설계 자유도가 얼어붙는다(회귀)")

emit("")
emit("=" * 100)
