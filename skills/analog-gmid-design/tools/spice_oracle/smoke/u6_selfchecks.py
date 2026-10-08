# -*- coding: utf-8 -*-
"""u6_selfchecks.py -- U6 신규 측정(.noise·offset Monte-Carlo·스윙/ICMR·.pz)의 자체 점검 (기록 -- test 아님, 판정 증거도 아님).

사용:  python smoke/u6_selfchecks.py <out_dir> [--only noise_rc|mc_5t|swing_5t|pz_5t] [--mc-r 0.05]

작성자(코드 쪽)가 만든 측정이 손계산·독립 경로와 맞는지 보는 점검이다 -- 판정은 auditor 의 격리 복제본 test 가 한다(WP-13).
  noise_rc   저항 분압 RC(tests/conftest.rc_input): 입력 환산 열잡음 밀도 = 4kT(Ra||Rb)/|H|² (H0 = Rb/(Ra+Rb))
  mc_5t      5T OTA(NMOS 차동쌍 + PMOS 미러 + 이상 꼬리 전류원): MC σ_in 대 소자·변수별 1σ 섭동(결정적 .op) 감도의 RSS --
             같은 ngspice 모델의 독립 경로(난수 표본 대 결정적 섭동). vth0 감도는 손계산 slope/sqrt(L_um·W_um·m) 와도 대조.
  swing_5t   같은 5T OTA 의 스윙·ICMR 창과 경계 소자의 부족량
  pz_5t      같은 5T OTA 의 `.pz` (큰 L·C 없는 개루프 넷리스트): 극점 15 개, RHP 0
결과는 <out_dir>/u6_selfchecks.json 에 케이스마다 저장한다.
"""
import argparse
import json
import math
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORACLE = HERE.parent
sys.path.insert(0, str(ORACLE))
sys.path.insert(0, str(ORACLE / "tests"))
import conftest  # noqa: E402
import numpy as np  # noqa: E402
import oracle_netlist as on  # noqa: E402
import oracle_noise as onz  # noqa: E402
import oracle_offset_mc as omc  # noqa: E402
import oracle_simulate as osim  # noqa: E402
import oracle_swing as osw  # noqa: E402

KB = 1.380649e-23


def ota5t_input(lut, itail=20e-6, L=1e-6, fw=4e-6, n=2, vin=0.9, vout=0.9):
    """5T OTA: M1/M2 NMOS 차동쌍(드레인 n1/out), M3/M4 PMOS 미러(M3 다이오드), 꼬리 이상 전류원, 단일 출력 + 1 pF."""
    def dev(name, kind, d, g, s, b, l=L, w=fw, nf=n):
        return {"name": name, "kind": kind, "drain": d, "gate": g, "source": s, "bulk": b, "L": l, "finger_w": w,
                "n_fingers": nf, "W": w * nf}
    inp = {
        "schema": "spice_oracle_input/1", "circuit": "t5t_ota",
        "process": conftest.process_block(lut, diffusion=False),
        "rails": [{"net": "vdd", "voltage": 1.8}, {"net": "gnd", "voltage": 0.0, "reference": True}],
        "devices": [dev("M1", "nmos", "n1", "inp", "tail", "gnd"), dev("M2", "nmos", "out", "inn", "tail", "gnd"),
                    dev("M3", "pmos", "n1", "n1", "vdd", "vdd"), dev("M4", "pmos", "out", "n1", "vdd", "vdd")],
        "sources": [{"name": "It", "kind": "current", "terminals": ["tail", "gnd"], "value": itail, "value_basis": "test"}],
        "passives": [{"name": "CL", "kind": "capacitor", "terminals": ["out", "gnd"], "value": 1e-12}],
        "ports": {"input_p": "inp", "input_n": "inn", "output": "out"},
        "predictions": {"nodes": {"inp": vin, "inn": vin, "out": vout}, "devices": {}, "metrics": []},
        "testbench": conftest.testbench_block(),
    }
    conftest.zero_diffusion(inp)
    return inp


def _save(out_dir, key, value):
    p = Path(out_dir) / "u6_selfchecks.json"
    d = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    d[key] = value
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def noise_rc(out):
    lut = conftest.make_lut(out / "lut_rc.npz")
    inp = conftest.rc_input(lut)
    inp["noise"] = {"f_lo_hz": 1.0, "points_per_decade": 5}
    inp["testbench"]["ac"]["fstop_hz"] = 1e8
    cir = out / "rc.free.cir"
    meta = on.write_netlists(inp, "free", str(cir))
    osim.simulate(str(cir), meta, str(conftest.NGSPICE))
    res = onz.noise_measure(inp, str(cir), meta, str(conftest.NGSPICE))["open_loop"]
    c = conftest.RC
    t_k = 27.0 + 273.15
    hand = 4 * KB * t_k * (c["ra"] * c["rb"] / (c["ra"] + c["rb"])) / (c["rb"] / (c["ra"] + c["rb"])) ** 2
    r = {"th_in_v2hz": res["th_in_v2hz"], "hand_4kT_Req_over_H2": hand, "rel_err": res["th_in_v2hz"] / hand - 1,
         "shares": {x["element"]: x["share_thermal"] for x in res["contrib"] if x["share_thermal"]}}
    _save(out, "noise_rc", r)
    return r


def _5t(out):
    lut = conftest.make_lut(out / "lut_5t.npz")
    inp = ota5t_input(lut)
    cir = out / "t5t.free.cir"
    meta = on.write_netlists(inp, "free", str(cir))
    return inp, cir, meta


def mc_5t(out, r):
    inp, cir, meta = _5t(out)
    inp["offset_mc"] = {"rel_resolution": r, "seed": 7}
    osim.simulate(str(cir), meta, str(conftest.NGSPICE))
    mc = omc.offset_mc_measure(inp, str(cir), meta, str(conftest.NGSPICE))
    text = cir.read_text(encoding="utf-8")
    devs = {d["name"]: d for d in inp["devices"]}
    nv = {nm: len(omc.mismatch_vars(text, inp["process"]["models"][devs[nm]["kind"]]["subckt"])) for nm in devs}
    samples = [{nm: [0.0] * nv[nm] for nm in devs}]
    keys = []
    for nm in devs:
        for j in range(nv[nm]):
            s = {n2: [0.0] * nv[n2] for n2 in devs}
            s[nm][j] = 1e-6 / math.sqrt(devs[nm]["n_fingers"])      # 1σ (z = 1)
            samples.append(s)
            keys.append((nm, j))
    mtext, devvars = omc.build_mc_netlist(text, inp, meta, samples, 1.0)
    scir = out / "t5t.sens.cir"
    scir.write_text(mtext, encoding="utf-8")
    rc, log, _ = osim.run_ngspice(str(conftest.NGSPICE), str(scir), str(out / "t5t.sens.log"), None, None, [])
    sn, outs, ports = meta["spice_node"], meta["output_nodes"], inp["ports"]
    ip, im, o1 = sn[ports["input_p"]].lower(), sn[ports["input_n"]].lower(), outs[0].lower()
    rows = []
    for blk in re.split(r"^MCS\s+", log, flags=re.M)[1:]:
        v = {m.group(2).lower(): float(m.group(3)) for m in omc._NODE_RE.finditer(blk)}
        rows.append((v[ip] - v[im], v[o1]))
    raw = osim.parse_ac_file(str(out / meta["ac_file"]))
    a = complex(raw[1][0], raw[2][0]).real
    vid0, vo0 = rows[0]
    sens = {f"{nm}.{devvars[nm][j].split('__')[-1]}": ((vo - vo0) / a - (vi - vid0)) * 1e3
            for (nm, j), (vi, vo) in zip(keys, rows[1:])}
    rss = math.sqrt(sum(s * s for s in sens.values()))
    slope = 3.356e-3 / math.sqrt(devs["M1"]["L"] * 1e6 * devs["M1"]["W"] * 1e6)       # vth0_slope(nfet, L>=0.5)/sqrt(L_um W_um) [V]
    r_ = {"mc_sigma_in_mV": mc["sigma_in_mV"], "mc_n": mc["n_samples"], "mc_rel_se": mc["rel_se_achieved"],
          "rss_of_sensitivities_mV": rss, "ratio_mc_over_rss": mc["sigma_in_mV"] / rss, "sens_mV": sens,
          "hand_vth0_sens_M1_mV": slope * 1e3, "sim_vth0_sens_M1_mV": abs(sens["M1.vth0_slope_spectre"])}
    _save(out, "mc_5t", r_)
    return r_


def swing_5t(out):
    inp, cir, meta = _5t(out)
    inp["swing_icmr"] = {"swing": True, "icmr": True}
    osim.simulate(str(cir), meta, str(conftest.NGSPICE))
    res = osw.swing_icmr_measure(inp, str(cir), meta, str(conftest.NGSPICE), sat_margin=0.0)
    r = {k: res.get(k) for k in ("status", "swing_out_v", "icmr_v", "icm_margin_v", "ngspice_runs")}
    r["icmr_window"] = {k: (res.get("icmr") or {}).get(k) for k in ("v_in_min", "v_in_max", "lo_hit_rail", "hi_hit_rail")}
    r["swing_window"] = {k: (res.get("swing") or {}).get(k) for k in ("v_lo", "v_hi")}
    _save(out, "swing_5t", r)
    return r


def pz_5t(out):
    inp, cir, meta = _5t(out)
    res = osim.simulate(str(cir), meta, str(conftest.NGSPICE))
    pz = res["ac"]["stability"]["pz"]
    r = {k: pz.get(k) for k in ("status", "P", "n_poles", "reason")}
    r["dominant_poles_rad_s"] = sorted(pz.get("poles") or [], key=lambda p: -p[0])[:3]
    _save(out, "pz_5t", r)
    return r


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--only", choices=["noise_rc", "mc_5t", "swing_5t", "pz_5t"])
    ap.add_argument("--mc-r", type=float, default=0.05)
    a = ap.parse_args(argv)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    todo = [a.only] if a.only else ["noise_rc", "pz_5t", "swing_5t", "mc_5t"]
    for k in todo:
        r = {"noise_rc": lambda: noise_rc(out), "pz_5t": lambda: pz_5t(out), "swing_5t": lambda: swing_5t(out),
             "mc_5t": lambda: mc_5t(out, a.mc_r)}[k]()
        print(k, json.dumps({x: y for x, y in r.items() if x != "sens_mV"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
