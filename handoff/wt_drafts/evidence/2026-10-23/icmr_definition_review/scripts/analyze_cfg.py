"""ICMR 측정 구성 비교 -- 분석 (진단 전용, 저장소 파일 안 고침).

구성: A = 순수 follower(V_inv = V_out), L = 봉인점 유지 follower(V_inv = V_out - c, v2 'B'),
      S = servo(V_inv = V_out - c + (x - x0): 출력은 봉인점 값에 묶이고 두 입력이 함께 움직임 -- oracle_swing ICMR 구성).
창 = x0 에서 이어지는 '모든 엔진 행 MOS 여유 >= 0' 구간 (여유 = VDS - VDSAT - tol, tol = tol_seal(엔진 행 값) 또는 0).
엔진 선형 예측(KCL, graph.ss_nodal 과 같은 G 의 vx·vu 감도)도 세 구성에 대해 같은 lin_window 로 낸다.
결과: out/<회로>.cfg_analysis.json, out/results.jsonl 에 회로마다 append.
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_scratch_icmr_def")
OUT = ROOT / "out"


def window_from(xs, m, i0):
    if m[i0] < 0:
        return None

    def edge(step):
        j = i0
        while 0 <= j + step < len(xs) and m[j + step] >= 0:
            j += step
        k = j + step
        if not (0 <= k < len(xs)):
            return xs[j], True, j
        return xs[j] + (xs[k] - xs[j]) * m[j] / (m[j] - m[k]), False, j
    lo, le, jlo = edge(-1)
    hi, he, jhi = edge(+1)
    return lo, hi, le, he, jlo, jhi


def lin_window(rows, dv):
    lo, hi, blo, bhi = -math.inf, math.inf, None, None
    for a, b, sign, slack, dev in rows:
        ca, sa = dv(a)
        cb, sb = dv(b)
        c = slack + sign * (ca - cb)
        r = sign * (sa - sb)
        if abs(r) <= sys.float_info.epsilon:
            continue
        reach = -c / r
        if r > 0 and reach > lo:
            lo, blo = reach, dev
        if r < 0 and reach < hi:
            hi, bhi = reach, dev
    return lo, hi, blo, bhi


def load(name, cfg):
    up = json.loads((OUT / f"{name}.{cfg}.up.json").read_text())
    dn = json.loads((OUT / f"{name}.{cfg}.dn.json").read_text())
    cols = up["cols"]
    rows = list(reversed(dn["rows"][1:])) + up["rows"]
    return cols, rows


def run(name):
    eng = json.loads((OUT / f"{name}.engine.json").read_text(encoding="utf-8"))
    info = json.loads((OUT / f"{name}.spice_info.json").read_text(encoding="utf-8"))
    vals = eng["values"]
    non, inv, out = eng["non"], eng["inv"], eng["outputs"][0]
    x0 = vals[non]
    rails = sorted(eng["rails"].values())
    devs = {r["device"]: r for r in eng["rows"] if r.get("row_kind", "sat") == "sat"}
    rows_eng = [(r["a"], r["b"], r["sign"], r["slack"], r["device"]) for r in devs.values()]
    vx, vu = eng["kcl_follower"]["vx"], eng["kcl_follower"]["vu"]
    vxo, vuo = vx.get(out, 0.0), vu.get(out, 0.0)
    cc = vals[out] - vals[inv]
    # 엔진 선형(KCL) 예측
    s_L = vxo / (1 - vuo)                        # δV_out/Δ, follower(u 증분 = V_out 증분)
    s_S = (vxo + vuo) / (1 - vuo)                # servo: δu = δV_out + Δ  -> 이상적이면 0 근처... (아래 확인)
    pred = {
        "L": lin_window(rows_eng, lambda n: (0.0, vx.get(n, 0.0) + vu.get(n, 0.0) * s_L)),
        "S": lin_window(rows_eng, lambda n: (0.0, vx.get(n, 0.0) + vu.get(n, 0.0) * (s_S + 1.0))),
    }
    pred["T"] = lin_window(rows_eng, lambda n: (0.0, vx.get(n, 0.0) - vu.get(n, 0.0) * vxo / vuo))   # 이상 servo: δV_out = 0
    dvo_c, dvo_s = vuo * cc / (1 - vuo), s_L
    pred["A"] = lin_window(rows_eng, lambda n: (vu.get(n, 0.0) * (dvo_c + cc), vx.get(n, 0.0) + vu.get(n, 0.0) * dvo_s))
    res = {"circuit": name, "x0": x0, "V_out0": vals[out], "V_inv0": vals[inv], "rails": rails, "out": out,
           "engine_lin_dVout_per_dx": {"L": s_L, "S": s_S}, "configs": {}}
    probes, node = info["probes"], info["spice_node"]
    for cfg in ("A", "L", "S", "T"):
        try:
            cols, rows = load(name, cfg)
        except FileNotFoundError:
            res["configs"][cfg] = {"missing": True}
            continue
        ci = {c.lower(): i for i, c in enumerate(cols)}
        xs = [r[0] for r in rows]
        i0 = min(range(len(xs)), key=lambda i: abs(xs[i] - x0))

        def col(v):
            return [r[ci[v.lower()]] for r in rows]
        vout = col(f"v({node[out]})")
        rec = {"n": len(xs), "vout_at_x0": vout[i0]}
        for tag in ("tol_seal", "tol0"):
            M = {m: [a - b - (r["tol"] if tag == "tol_seal" else 0.0) for a, b in zip(col(probes[m]["vds"]), col(probes[m]["vdsat"]))]
                 for m, r in devs.items()}
            mins = [min(M[m][i] for m in M) for i in range(len(xs))]
            ivs, st = [], None
            for i, v in enumerate(mins):
                if v >= 0 and st is None:
                    st = i
                if v < 0 and st is not None:
                    ivs.append((xs[st], xs[i - 1])); st = None
            if st is not None:
                ivs.append((xs[st], xs[-1]))
            rec[tag + "_all_intervals"] = ivs
            w = window_from(xs, mins, i0)
            if w is None:
                rec[tag] = {"nominal_fail": True, "worst": mins[i0], "worst_dev": min(M, key=lambda m: M[m][i0])}
                continue
            lo, hi, le, he, jlo, jhi = w
            blo = None if le else min(M, key=lambda m: M[m][max(jlo - 1, 0)])
            bhi = None if he else min(M, key=lambda m: M[m][min(jhi + 1, len(xs) - 1)])
            rec[tag] = {"lo": lo, "hi": hi, "width": hi - lo, "lo_rail": le, "hi_rail": he, "bind_lo": blo, "bind_hi": bhi,
                        "vout_lo": vout[jlo], "vout_hi": vout[jhi]}
        lo_, hi_, blo_, bhi_ = pred[cfg]
        rec["engine_lin"] = {"lo": max(rails[0], x0 + lo_), "hi": min(rails[-1], x0 + hi_), "bind_lo": blo_, "bind_hi": bhi_}
        res["configs"][cfg] = rec
    (OUT / f"{name}.cfg_analysis.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    with open(OUT / "results.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(res) + "\n")
    print(json.dumps({c: {k: res["configs"][c].get("tol_seal") for k in ["x"]} for c in res["configs"]}, default=str)[:2000])


if __name__ == "__main__":
    for nm in sys.argv[1:]:
        run(nm)
