# -*- coding: utf-8 -*-
"""`mirror_ratio_error_pct` 상한을 **선언된 것에서 유도**하기 위한 실측 (2026-09-10).

## 무엇을 근거로 삼나

`mirror_ratio_error_pct`는 ratio 매칭 쌍의 VDS 차이가 만드는 **계통(systematic)** 전류비
오차다(1차 CLM: `dI/I = |dVDS| / V_A`, `V_A = ID/gds`). 이 회로는 같은 "전류비가 틀어지는
현상"의 **랜덤** 성분에 대해서는 이미 예산을 선언해 뒀다:

    {"metric": "mismatch_sigma_mV", "op": "<=", "value": 5.0}   # M1a/M1b, Pelgrom sigma_Vth

랜덤 Vth 오차는 전류비 오차로 직접 환산된다 -- `dI/I = gm*dVth/I = (gm/ID) * dVth`.
즉 **선언된 5.0mV가 이미 몇 %의 전류비 오차를 허용하고 있는지**를 계산할 수 있고, 그것이
계통 성분 상한의 자연스러운 기준이 된다: **계통 오차가 이미 받아들이기로 한 랜덤 오차보다
크면 안 된다.** 새 숫자를 지어내는 게 아니라 선언된 5.0mV를 단위 변환하는 것이다.

여기서는 세 가지를 잰다:

  1. 선언된 `mismatch_sigma_mV <= 5.0`의 **전류비 등가 %** (입력쌍 gm_id로 환산).
  2. 각 ratio 매칭 쌍의 **자기 랜덤 성분**(그 쌍의 실제 W·L에서 나오는 Pelgrom sigma)의
     전류비 등가 % -- 쌍마다 다르므로 "이 쌍에서 계통이 랜덤을 넘는가"를 직접 본다.
  3. 현재 계통 오차(쌍별) -- 어느 쌍이 최댓값을 만드는지.

**아무것도 고치지 않는다 -- 표만 만든다.**

실행: assets 디렉터리에서 `python tests/probe_mirror_ratio_bound.py`
"""
import sys
import os
import json
import math

ASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASSETS)
sys.path.insert(0, os.path.join(ASSETS, "..", "..", "..", "workspaces"))
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


emit("=" * 104)
emit("mirror_ratio_error_pct 상한 유도 -- 선언된 랜덤 예산의 전류비 등가와 비교")
emit("=" * 104)

for key, cfg in H.SPECS.items():
    topo = os.path.join(ASSETS, "library", cfg["topology_file"])
    spec = H.canonical_spec(key)
    emit("")
    emit("-" * 104)
    emit(f"[{key}]")
    ev = sr._build_theta_evaluator(topo, spec)
    ms, cons = ev["metrics_specs"], ev["constraints"]

    # ── 1. 선언된 랜덤 예산 ────────────────────────────────────────────────
    mm = [(c, ms[c["metric"]]) for c in cons
          if ms.get(c["metric"], {}).get("type") == "pelgrom_mismatch"]
    if not mm:
        emit("  pelgrom_mismatch 제약이 선언돼 있지 않다 -- 이 회로에선 이 유도를 못 쓴다")
        continue
    ratio_pairs = [p for p in sr._matching_pairs_cached(topo)
                   if p.get("matching_sensitivity") == "ratio" and len(p.get("names") or []) >= 2]
    if not ratio_pairs:
        emit("  ratio 매칭 쌍이 없다 -- mirror_ratio_error가 정의되지 않는다")
        continue

    # 정본 theta_star로 평가(없으면 중점)
    star = os.path.join(ASSETS, "tests", "canonical_theta_star.json")
    st = json.load(open(star, encoding="utf-8")) if os.path.exists(star) else {}
    th = {t["name"]: st.get(t["name"],
          (float(t["bounds"][0]) + float(t["bounds"][1])) / 2.0 if t.get("bounds") else 0.0)
          for t in ev["thetas"]}
    try:
        ctx, metrics = ev["evaluate"](th)
    except Exception as e:
        emit(f"  ★ 평가 실패: {type(e).__name__}: {str(e)[:150]}")
        continue

    for c, mspec in mm:
        devs = mspec["devices"]
        gm_ids = [ctx.sized[d].get("gm_id") for d in devs if ctx.sized.get(d, {}).get("gm_id")]
        if not gm_ids:
            continue
        gm_id = sum(gm_ids) / len(gm_ids)
        eq = c["value"] * 1e-3 * gm_id * 100.0
        emit(f"  선언된 랜덤 예산: {c['metric']} <= {c['value']}mV  (devices={devs}, "
             f"gm_id={gm_id:.2f}/V)")
        emit(f"     -> 전류비 등가 dI/I = gm_id x sigma = {eq:.2f}%   "
             f"(현재 실측 sigma={metrics[c['metric']]:.3f}mV -> {metrics[c['metric']]*1e-3*gm_id*100:.2f}%)")

    # ── 2/3. 쌍별 계통 오차 vs 그 쌍 자신의 랜덤 성분 ──────────────────────
    emit("")
    emit(f"    {'쌍':<16} {'dVDS(V)':>8} {'V_A(V)':>8} {'계통%':>8} {'랜덤sig(mV)':>11}"
         f" {'gm_id':>7} {'랜덤%':>7}  판정")
    rows = []
    for p in ratio_pairs:
        a, b = p["names"][0], p["names"][1]
        ea, eb = ctx.sized.get(a), ctx.sized.get(b)
        if not ea or not eb or ea.get("vds") is None or eb.get("vds") is None or not ea.get("gds"):
            continue
        v_a = ea["ID"] / ea["gds"]
        dvds = abs(eb["vds"] - ea["vds"])
        sysp = dvds / v_a * 100.0
        kind = ctx.kind_of.get(a)
        slope = (spec.get("vth0_slope") or {}).get("pfet" if kind == "pmos" else "nfet")
        sig = None
        if slope:
            sig = math.sqrt(sum(
                sr.estimate_mismatch_sigma(slope, ctx.sized[d]["W"] * 1e6,
                                            ctx.sized[d]["L"] * 1e6) ** 2 for d in (a, b)))
        gi = ea.get("gm_id") or 0.0
        randp = (sig * gi * 100.0) if (sig and gi) else None
        rows.append((sysp, f"{a}/{b}", dvds, v_a, sysp, (sig * 1e3) if sig else None, gi, randp))
    rows.sort(reverse=True)
    for _, nm, dv, va, sp, sg, gi, rp in rows:
        verdict = "" if rp is None else ("계통>랜덤 ★" if sp > rp else "계통<=랜덤")
        emit(f"    {nm:<16} {dv:8.4f} {va:8.3f} {sp:8.3f} "
             f"{('-' if sg is None else f'{sg:11.3f}')} {gi:7.2f} "
             f"{('-' if rp is None else f'{rp:7.2f}')}  {verdict}")
    emit(f"    -> 현재 mirror_ratio_error_pct = {metrics.get('mirror_ratio_error_pct', float('nan')):.3f}% "
         f"(aggregate=max, 최댓값 쌍 = {rows[0][1] if rows else '-'})")

emit("")
emit("=" * 104)
