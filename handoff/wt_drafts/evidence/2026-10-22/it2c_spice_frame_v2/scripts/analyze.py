"""IT-2c SPICE 틀 판정 -- 분석.

입력: out/<회로>.engine.json, out/<회로>.{A,B}.{up,dn}.json, out/<회로>.spice_info.json, out/tol_tables.json
출력: out/<회로>.analysis.json (+ 화면 요약)

여유(점마다, MOS 마다) = VDS − VDSAT − tol. tol 두 가지:
  tol_seal : 엔진 행과 같은 값(봉인점 (L, VDS) 의 표 값, 소자마다 상수 -- region_rows 와 같다)
  tol_pt   : 같은 표를 SPICE 점의 VDS 에서 읽은 값
SPICE 창 = x0(봉인점 비반전 입력)에서 이어지는 '모든 MOS 여유 ≥ 0' 구간, 끝은 마지막 통과·첫 실패 사이 선형 보간.
"""
import json
import math
import sys
from pathlib import Path

OUT = Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_scratch_it2c_spice\out")
TOL = json.loads((OUT / "tol_tables.json").read_text(encoding="utf-8"))


def tol_at(kind, wk, L, vds):
    t = TOL[f"{kind}|{wk}|{L!r}"]
    i = int(round(vds * 1000))
    if i < 0 or i >= len(t) or t[i] is None:
        return None
    return t[i]


def load_sweep(name, cfg):
    up = json.loads((OUT / f"{name}.{cfg}.up.json").read_text())
    dn = json.loads((OUT / f"{name}.{cfg}.dn.json").read_text())
    cols = up["cols"]
    rows = sorted(dn["rows"][1:] + up["rows"], key=lambda r: r[0])
    return cols, rows, up["rows"][0][0]


def window_from(xs, ok_margin, i0):
    """ok_margin[i] = 최소 여유. i0 에서 이어지는 ≥0 구간, 끝은 선형 보간. 반환 (lo, hi, lo_hit_end, hi_hit_end)."""
    if ok_margin[i0] < 0:
        return None
    def edge(step):
        j = i0
        while 0 <= j + step < len(xs) and ok_margin[j + step] >= 0:
            j += step
        k = j + step
        if not (0 <= k < len(xs)):
            return xs[j], True, j
        m0, m1 = ok_margin[j], ok_margin[k]
        x = xs[j] + (xs[k] - xs[j]) * m0 / (m0 - m1)
        return x, False, j
    lo, lo_end, jlo = edge(-1)
    hi, hi_end, jhi = edge(+1)
    return lo, hi, lo_end, hi_end, jlo, jhi


def lin_window(rows_eng, dv):
    """rows_eng: [(a, b, sign, slack, dev)], dv(net) -> (const, slope) 증분 Δv = const + slope·Δ. 반환 (dlo, dhi, 묶는 소자 lo, hi)."""
    lo, hi, blo, bhi = -math.inf, math.inf, None, None
    for a, b, sign, slack, dev in rows_eng:
        ca, sa = dv(a)
        cb, sb = dv(b)
        c = slack + sign * (ca - cb)
        r = sign * (sa - sb)
        if abs(r) <= sys.float_info.epsilon:
            continue
        reach = -c / r
        if r > 0:
            if reach > lo:
                lo, blo = reach, dev
        else:
            if reach < hi:
                hi, bhi = reach, dev
    return lo, hi, blo, bhi


def run(name):
    eng = json.loads((OUT / f"{name}.engine.json").read_text(encoding="utf-8"))
    info = json.loads((OUT / f"{name}.spice_info.json").read_text(encoding="utf-8"))
    vals = eng["values"]
    non, inv = eng["non"], eng["inv"]
    out = eng["outputs"][0]
    x0 = vals[non]
    devs = {r["device"]: r for r in eng["rows"]}
    probes = info["probes"]
    node = info["spice_node"]
    res = {"circuit": name, "x0": x0, "V_out0": vals[out], "V_inv0": vals[inv], "configs": {}}

    s_th = eng["theta_follower_inv_fixed"]["slope"]
    s_k = eng["kcl_follower"]["slope"]
    s2 = eng.get("theta_s2") or {}
    vx, vu = eng["kcl_follower"]["vx"], eng["kcl_follower"]["vu"]
    rows_eng = [(r["a"], r["b"], r["sign"], r["slack"], r["device"]) for r in eng["rows"]]

    def dv_theta_B(n):
        return 0.0, s_th.get(n, 0.0)

    def dv_kcl_B(n):
        return 0.0, s_k.get(n, 0.0)

    cprime = x0 - vals[out]                      # θ 둘째 우변 크기 (x0 − V_out0)

    def dv_theta_A(n):
        return cprime * s2.get(n, 0.0), s_th.get(n, 0.0)

    cc = vals[out] - vals[inv]                   # 순수 follower 에서 반전 입력이 봉인점보다 더 움직이는 양
    vxo, vuo = vx[out], vu[out]
    dvo_c, dvo_s = vuo * cc / (1 - vuo), vxo / (1 - vuo)

    def dv_kcl_A(n):
        return vu.get(n, 0.0) * (dvo_c + cc), vx.get(n, 0.0) + vu.get(n, 0.0) * dvo_s

    eng_pred = {"B": {"theta": lin_window(rows_eng, dv_theta_B), "kcl": lin_window(rows_eng, dv_kcl_B)},
                "A": {"theta": lin_window(rows_eng, dv_theta_A), "kcl": lin_window(rows_eng, dv_kcl_A)}}
    # 확인: B 의 lin_window 가 엔진 saturation_window 끝과 같아야 한다
    res["check_B_theta_vs_engine"] = [eng_pred["B"]["theta"][0] - eng["theta_follower_inv_fixed"]["dlo"],
                                      eng_pred["B"]["theta"][1] - eng["theta_follower_inv_fixed"]["dhi"]]
    res["check_B_kcl_vs_engine"] = [eng_pred["B"]["kcl"][0] - eng["kcl_follower"]["dlo"], eng_pred["B"]["kcl"][1] - eng["kcl_follower"]["dhi"]]

    for cfg in ("B", "A"):
        try:
            cols, rows, xstart = load_sweep(name, cfg)
        except FileNotFoundError:
            res["configs"][cfg] = {"missing": True}
            continue
        ci = {c.lower(): i for i, c in enumerate(cols)}
        xs = [r[0] for r in rows]
        i0 = min(range(len(xs)), key=lambda i: abs(xs[i] - x0))

        def col(vec):
            j = ci[vec.lower()]
            return [r[j] for r in rows]

        def vnode(n):
            if node.get(n) == "0" or n not in node:
                return [vals[n]] * len(xs) if n in vals and n not in node else ([0.0] * len(xs))
            return col(f"v({node[n]})")
        V = {}
        for n in set(list(node) + [non, inv, out]):
            if n in node:
                V[n] = vnode(n)
        for n, v in eng["rails"].items():
            V.setdefault(n, [v] * len(xs))
        margins_seal, margins_pt, sat_d = {}, {}, {}
        for m, r in devs.items():
            vds = col(probes[m]["vds"])
            vdsat = col(probes[m]["vdsat"])
            sat_d[m] = (vds, vdsat)
            margins_seal[m] = [a - b - r["tol"] for a, b in zip(vds, vdsat)]
            mp = []
            for a, b in zip(vds, vdsat):
                t = tol_at(r["kind"], r["w_key"], r["L"], a)
                mp.append(-1.0 if t is None else a - b - t)
            margins_pt[m] = mp
        rec = {"x_range": [xs[0], xs[-1]], "n_points": len(xs), "i0": i0, "x_at_i0": xs[i0]}
        for tag, M in (("tol_seal", margins_seal), ("tol_pt", margins_pt)):
            mins = [min(M[m][i] for m in M) for i in range(len(xs))]
            w = window_from(xs, mins, i0)
            if w is None:
                rec[tag] = {"nominal_fail": True, "worst": mins[i0], "worst_dev": min(M, key=lambda m: M[m][i0])}
                continue
            lo, hi, lo_end, hi_end, jlo, jhi = w
            blo = min(M, key=lambda m: M[m][max(jlo - 1, 0)]) if not lo_end else None
            bhi = min(M, key=lambda m: M[m][min(jhi + 1, len(xs) - 1)]) if not hi_end else None
            rec[tag] = {"lo": lo, "hi": hi, "dlo": lo - x0, "dhi": hi - x0, "lo_hit_sweep_end": lo_end, "hi_hit_sweep_end": hi_end,
                        "bind_lo": blo, "bind_hi": bhi, "jlo": jlo, "jhi": jhi}
        # 동작점 대조 (x0)
        rec["node_at_x0"] = {n: {"spice": V[n][i0], "engine": vals.get(n), "diff_mV": None if vals.get(n) is None else 1e3 * (V[n][i0] - vals[n])}
                             for n in V}
        rec["margin_at_x0"] = {m: {"spice": margins_seal[m][i0], "engine_slack": devs[m]["slack"],
                                   "vds_spice": sat_d[m][0][i0], "vds_eng": devs[m]["vds"],
                                   "vdsat_spice": sat_d[m][1][i0], "vdsat_eng": devs[m]["vdsat"], "tol": devs[m]["tol"]} for m in devs}

        # 감도 (중앙 차분 ±k 점)
        def deriv(arr, i, k=4):
            a, b = max(i - k, 0), min(i + k, len(xs) - 1)
            return (arr[b] - arr[a]) / (xs[b] - xs[a])
        sens = {}
        for n in V:
            e = {"spice_x0": deriv(V[n], i0), "theta": s_th.get(n), "kcl": s_k.get(n)}
            if "tol_seal" in rec and "jlo" in rec["tol_seal"]:
                e["spice_lo_edge"] = deriv(V[n], rec["tol_seal"]["jlo"])
                e["spice_hi_edge"] = deriv(V[n], rec["tol_seal"]["jhi"])
            sens[n] = e
        rec["sens"] = sens
        # 행 변화율 대조 (x0): 엔진 θ·KCL(VDS 만), SPICE dVDS/dx, SPICE d(여유)/dx
        rrate = {}
        for a, b, sign, slack, dev in rows_eng:
            rrate[dev] = {"a": a, "b": b, "theta": sign * (s_th.get(a, 0.0) - s_th.get(b, 0.0)),
                          "kcl": sign * (s_k.get(a, 0.0) - s_k.get(b, 0.0)),
                          "spice_dvds": deriv(sat_d[dev][0], i0), "spice_dmargin": deriv(margins_seal[dev], i0)}
            if "tol_seal" in rec and "jlo" in rec["tol_seal"]:
                rrate[dev]["spice_dmargin_lo_edge"] = deriv(margins_seal[dev], rec["tol_seal"]["jlo"])
                rrate[dev]["spice_dmargin_hi_edge"] = deriv(margins_seal[dev], rec["tol_seal"]["jhi"])
        rec["row_rates"] = rrate
        # SPICE 접선 예측(SPICE 자신의 x0 여유·x0 변화율로 1차 외삽) -- 곡률 오차 분리용
        tl = lin_window([(dev, None, 1.0, margins_seal[dev][i0], dev) for dev in devs],
                        lambda n: (0.0, rrate[n]["spice_dmargin"]) if n in rrate else (0.0, 0.0))
        rec["spice_tangent_window"] = tl
        tl2 = lin_window([(dev, None, 1.0, margins_seal[dev][i0], dev) for dev in devs],
                         lambda n: (0.0, rrate[n]["spice_dvds"]) if n in rrate else (0.0, 0.0))
        rec["spice_tangent_window_vdsat_frozen"] = tl2
        # 혼합: SPICE x0 여유 + 틀 변화율 -> 변화율(틀) 효과만
        for fr in ("theta", "kcl"):
            rec[f"hybrid_spice_slack_{fr}_rate"] = lin_window([(dev, None, 1.0, margins_seal[dev][i0], dev) for dev in devs],
                                                              lambda n, fr=fr: (0.0, rrate[n][fr]) if n in rrate else (0.0, 0.0))
        rec["engine_pred"] = {fr: {"dlo": eng_pred[cfg][fr][0], "dhi": eng_pred[cfg][fr][1], "bind_lo": eng_pred[cfg][fr][2],
                                   "bind_hi": eng_pred[cfg][fr][3]} for fr in ("theta", "kcl")}
        res["configs"][cfg] = rec
    (OUT / f"{name}.analysis.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


def show(res):
    print("=====", res["circuit"], "x0=%.4f Vout0=%.4f Vinv0=%.4f" % (res["x0"], res["V_out0"], res["V_inv0"]),
          "chk", res["check_B_theta_vs_engine"], res["check_B_kcl_vs_engine"])
    for cfg, rec in res["configs"].items():
        if rec.get("missing"):
            print(cfg, "missing")
            continue
        print(" cfg", cfg, "x", rec["x_range"], "n", rec["n_points"], "x@i0", rec["x_at_i0"])
        for tag in ("tol_seal", "tol_pt"):
            print("  SPICE", tag, {k: (round(v, 5) if isinstance(v, float) else v) for k, v in rec[tag].items() if k not in ("jlo", "jhi")})
        for fr, p in rec["engine_pred"].items():
            s = rec["tol_seal"]
            if "dlo" in s:
                print("  ENG %-5s dlo %+.4f dhi %+.4f  err_lo %+.1f mV err_hi %+.1f mV  bind %s/%s" %
                      (fr, p["dlo"], p["dhi"], 1e3 * (p["dlo"] - s["dlo"]), 1e3 * (p["dhi"] - s["dhi"]), p["bind_lo"], p["bind_hi"]))
        print("  SPICE tangent", [round(v, 4) if isinstance(v, float) else v for v in rec["spice_tangent_window"]],
              "frozen-vdsat", [round(v, 4) if isinstance(v, float) else v for v in rec["spice_tangent_window_vdsat_frozen"]])
        for fr in ("theta", "kcl"):
            print("  hybrid(spice slack, %s rate)" % fr, [round(v, 4) if isinstance(v, float) else v for v in rec[f"hybrid_spice_slack_{fr}_rate"]])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for nm in sys.argv[1:]:
        show(run(nm))
