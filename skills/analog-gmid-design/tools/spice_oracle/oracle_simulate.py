# -*- coding: utf-8 -*-
"""oracle_simulate.py -- ngspice 배치 실행 + .op/.ac 결과 추출.

진입점(단독 실행):
    python oracle_simulate.py <netlist.cir> <out_sim.json> --ngspice <ngspice_con.exe> [--timeout-s S]

  <netlist.cir>.meta.json(oracle_netlist.py 가 씀)을 읽어 probe 이름을 알고, ngspice -b 를 돌려
  .op(소자별 id/gm/gds/vth/vdsat/vgs/vds/vbs, 넷 전압, 레일 공급전류, forced 고정원 전류)와
  .ac(wrdata 파일 -> dc gain, f-3dB, UGF, PM)를 sim JSON 으로 쓴다.

공개 함수: run_ngspice(exe, cir, log, timeout_s), parse_op(log_text, meta), parse_ac_file(path),
          ac_measures(freq, re, im), simulate(cir_path, meta, exe, timeout_s)

부호 규칙(출력)
  * 소자 값은 ngspice 원값. BSIM4 @ 값은 극성 정규화돼 있다(PMOS 도 id/vgs/vds 양수, vbs=type*(Vb-Vs)).
  * rail_current_A[net] = 그 레일 전압원이 회로에 공급하는 전류 = -i(Vrail).
  * hold_current_A[net] = forced 고정원으로 그 넷에서 빠져나가는 전류 = i(Vhold) (KCL 잔차).
  * PM = 180 - (DC 위상 - UGF 위상) [deg], UGF = |H|=1 첫 하강 교차(log-log 보간),
    f-3dB = |H| < |H(f_first)|/sqrt(2) 인 첫 주파수 점(보간 없음), gain_dc = |H(f_first)|.
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys

_NUM = r"([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)"


def run_ngspice(exe, cir_path, log_path, timeout_s=None):
    with open(log_path, "w", encoding="utf-8", errors="replace") as fo:
        r = subprocess.run([exe, "-b", os.path.basename(cir_path)], cwd=os.path.dirname(os.path.abspath(cir_path)),
                           stdout=fo, stderr=subprocess.STDOUT, timeout=timeout_s)
    with open(log_path, encoding="utf-8", errors="replace") as f:
        return r.returncode, f.read()


def _grab(text, expr):
    m = re.search(r"^\s*" + re.escape(expr) + r"\s*=\s*" + _NUM, text, re.I | re.M)
    return float(m.group(1)) if m else None


def parse_op(log, meta):
    devices = {}
    for name, pr in meta["probes"].items():
        devices[name] = {p: _grab(log, expr) for p, expr in pr.items()}
    nodes = {}
    for net in meta["nets"]:
        nodes[net] = _grab(log, f"v({meta['spice_node'][net].lower()})")
    rails = {}
    for net, src in meta["rail_sources"].items():
        v = _grab(log, f"i({src.lower()})")
        rails[net] = None if v is None else -v
    hold = {}
    for net in meta["held"]:
        hold[net] = _grab(log, f"i(vhold_{net.lower()})")
    return {"devices": devices, "nodes": nodes, "rail_current_A": rails, "hold_current_A": hold}


def parse_ac_file(path):
    if not path or not os.path.exists(path):
        return None
    fr, re_, im = [], [], []
    with open(path) as f:
        for line in f:
            parts = line.split()
            try:
                vals = [float(x) for x in parts]
            except ValueError:
                continue
            if len(vals) >= 3:
                fr.append(vals[0]); re_.append(vals[1]); im.append(vals[2])
    return (fr, re_, im) if fr else None


def ac_measures(freq, re_, im):
    import numpy as np
    f = np.asarray(freq)
    H = np.asarray(re_) + 1j * np.asarray(im)
    mag = np.abs(H)
    ph = np.unwrap(np.angle(H))
    out = {"f_first_hz": float(f[0]), "gain_dc": float(mag[0]), "dc_gain_db": float(20 * np.log10(mag[0])),
           "phase_dc_deg": float(np.degrees(ph[0]))}
    i3 = np.where(mag < mag[0] / math.sqrt(2))[0]
    out["f3db_hz"] = float(f[i3[0]]) if len(i3) else None
    iu = np.where(mag < 1.0)[0]
    if len(iu) and iu[0] > 0:
        k = iu[0]
        lf = np.interp(0.0, [np.log10(mag[k]), np.log10(mag[k - 1])], [np.log10(f[k]), np.log10(f[k - 1])])
        phu = np.interp(lf, [np.log10(f[k - 1]), np.log10(f[k])], [ph[k - 1], ph[k]])
        lag = math.degrees(ph[0] - phu)
        out["ugf_hz"] = float(10 ** lf)
        out["phase_lag_at_ugf_deg"] = float(lag)
        out["pm_deg"] = float(180.0 - lag)
    else:
        out["ugf_hz"] = None
        out["phase_lag_at_ugf_deg"] = None
        out["pm_deg"] = None
    out["a0_f3db_hz"] = out["gain_dc"] * out["f3db_hz"] if out["f3db_hz"] else None
    return out


def simulate(cir_path, meta, exe, timeout_s=None):
    base = os.path.splitext(cir_path)[0]
    log_path = base + ".log"
    ac_path = os.path.join(os.path.dirname(os.path.abspath(cir_path)), meta["ac_file"]) if meta.get("ac_file") else None
    if ac_path and os.path.exists(ac_path):
        os.remove(ac_path)
    rc, log = run_ngspice(exe, cir_path, log_path, timeout_s)
    res = parse_op(log, meta)
    res["ngspice_rc"] = rc
    res["log"] = log_path
    errs = [ln.strip() for ln in log.splitlines() if re.search(r"error|fatal|singular|abort", ln, re.I)]
    res["log_errors"] = errs[:40]
    res["op_ok"] = any(v.get("id") is not None for v in res["devices"].values())
    raw = parse_ac_file(ac_path)
    res["ac"] = ac_measures(*raw) if raw else None
    res["ac_file"] = ac_path
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description="ngspice 실행 + .op/.ac 추출")
    ap.add_argument("netlist")
    ap.add_argument("out_json")
    ap.add_argument("--ngspice", required=True, help="ngspice 콘솔 실행 파일 경로")
    ap.add_argument("--timeout-s", type=float, default=None)
    a = ap.parse_args(argv)
    with open(a.netlist + ".meta.json", encoding="utf-8") as f:
        meta = json.load(f)
    res = simulate(a.netlist, meta, a.ngspice, a.timeout_s)
    with open(a.out_json, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("wrote", a.out_json, "op_ok=", res["op_ok"], "ac=", None if res["ac"] is None else
          {k: res["ac"][k] for k in ("dc_gain_db", "ugf_hz", "pm_deg")})
    return 0 if res["op_ok"] else 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
