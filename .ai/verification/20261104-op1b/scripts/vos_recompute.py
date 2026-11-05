# -*- coding: utf-8 -*-
"""card 20261104-op1b C-6 -- MC 표본별 V_os 재계산과 σ_in·mean_in 비트 동일 판정(작성 = 구현, 판정 = auditor A-4).

읽기·식은 dv5_vos_recompute.py(OP-1a)와 같다(옛 oracle_offset_mc.py:130-140, :166-195, :43-49). 옛 코드를 import하지 않는다.
표본별 V_os는 op1b_lib.vos_samples가 낸다(계획 N0.1). 실패 표본은 옛 :173-177처럼 부르기 전에 거른다.
σ·mean = 옛 :185·:190과 같은 식(np.asarray(vos, float), std(ddof=1)*1e3, mean()*1e3).

사용: python -P vos_recompute.py <결과 json> <케이스 폴더> <mc 로그 이름> <meta 이름> <입력 json> [--sim <sim.json>] [--dv5 <dv5_result.json> <dv5 case 이름>]
  --sim: offset_mc.sigma_in_mV·mean_in_mV·a_dc_signed와 비트 비교(R10 기준선 실행 대조).
  --dv5: 같은 case의 per_sample_vos(V_os_hex)·σ·mean과 비트 비교, 기록된 python·numpy 판과 다르면 version_differs 표지(f6).
"""
import hashlib
import json
import math
import os
import platform
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import op1b_lib as L  # noqa: E402

_NODE_RE = re.compile(r"^\s*(v)\(([^)]+)\)\s*=\s*([-+0-9.eE]+)\s*$", re.I | re.M)  # 옛 oracle_offset_mc.py:40


def sha256_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def read_log(p):
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


def parse_ac_file(path):
    # 옛 oracle_simulate.parse_ac_file
    if not path or not os.path.exists(path):
        return None
    fr, re_, im = [], [], []
    with open(path) as f:
        for line in f:
            try:
                vals = [float(x) for x in line.split()]
            except ValueError:
                continue
            if len(vals) >= 3:
                fr.append(vals[0]); re_.append(vals[1]); im.append(vals[2])
    return (fr, re_, im) if fr else None


def a_signed_from_ac(ac_path):
    # 옛 :130-140 (h0 = .ac 첫 점, 실수 판정 1e-3)
    raw = parse_ac_file(ac_path)
    h0 = complex(raw[1][0], raw[2][0]) if raw else None
    if h0 is None or abs(h0) == 0:
        return None
    return h0.real if abs(h0.imag) <= 1e-3 * abs(h0) else None


def sample_count(rel_resolution, max_samples=None):
    # 옛 :43-49
    n = math.ceil(1 + 1 / (2 * rel_resolution ** 2))
    if max_samples is not None and n > max_samples:
        n = int(max_samples)
    return n


def recompute(log, meta, ports, a_signed, n):
    sn, outs = meta["spice_node"], meta["output_nodes"]
    ip, im = sn[ports["input_p"]].lower(), sn[ports["input_n"]].lower()
    o1 = outs[0].lower()
    o2 = None if outs[1] == "0" else outs[1].lower()
    rows = []
    for blk in re.split(r"^MCS\s+", log, flags=re.M)[1:]:
        vals = {m.group(2).lower(): float(m.group(3)) for m in _NODE_RE.finditer(blk)}
        if ip in vals and im in vals and o1 in vals and (o2 is None or o2 in vals):
            rows.append((vals[ip] - vals[im], vals[o1] - (vals[o2] if o2 else 0.0)))
        else:
            rows.append(None)
    if len(rows) != n + 1 or rows[0] is None:
        raise L.Op1bStop("mc_blocks_mismatch", {"n_blocks": len(rows), "n_requested": n})
    if a_signed is None:
        raise L.Op1bStop("mc_gain_undefined")
    ok = [(k, r) for k, r in enumerate(rows) if k > 0 and r is not None]  # 실패 표본은 부르기 전에 거른다
    v_id = [rows[0][0]] + [r[0] for _, r in ok]
    v_out = [rows[0][1]] + [r[1] for _, r in ok]
    vos = L.vos_samples(v_id, v_out, a_signed)
    arr = np.asarray(vos, float)
    cnt = len(arr)
    if cnt <= 1:
        raise L.Op1bStop("mc_too_few_samples", cnt)
    return {"n_samples": cnt, "n_requested": n, "n_failed": n - cnt,
            "sigma_in_mV": float(arr.std(ddof=1) * 1e3), "mean_in_mV": float(arr.mean() * 1e3),
            "per_sample_vos": [{"k": k, "V_os_V": v, "V_os_hex": float(v).hex()} for (k, _), v in zip(ok, vos)]}


def _bit(a, b):
    return a is not None and b is not None and float(a).hex() == float(b).hex()


def main(argv):
    out_p, d, log_n, meta_n, inp_p = argv[:5]
    sim_p = dv5_p = dv5_case = None
    rest = argv[5:]
    while rest:
        if rest[0] == "--sim":
            sim_p, rest = rest[1], rest[2:]
        elif rest[0] == "--dv5":
            dv5_p, dv5_case, rest = rest[1], rest[2], rest[3:]
        else:
            raise L.Op1bStop("bad_args", rest[0])
    meta = json.load(open(os.path.join(d, meta_n), encoding="utf-8"))
    inp = json.load(open(inp_p, encoding="utf-8"))
    ac_p = os.path.join(d, meta["ac_file"])
    a = a_signed_from_ac(ac_p)
    cfg = inp["offset_mc"]
    n = sample_count(float(cfg["rel_resolution"]), cfg.get("max_samples"))
    r = recompute(read_log(os.path.join(d, log_n)), meta, inp["ports"], a, n)
    res = {"python": platform.python_version(), "numpy": np.__version__, "a_dc_signed": a, "a_hex": float(a).hex(),
           "inputs": {nm: sha256_file(p) for nm, p in (("log", os.path.join(d, log_n)), ("meta", os.path.join(d, meta_n)),
                                                        ("input", inp_p), ("ac", ac_p))}, **r}
    if sim_p:
        b = json.load(open(sim_p, encoding="utf-8"))["offset_mc"]
        res["vs_sim"] = {"sigma_bit": _bit(r["sigma_in_mV"], b["sigma_in_mV"]), "mean_bit": _bit(r["mean_in_mV"], b["mean_in_mV"]),
                         "a_bit": _bit(a, b.get("a_dc_signed")), "n_samples_equal": r["n_samples"] == b["n_samples"]}
    if dv5_p:
        rec = json.load(open(dv5_p, encoding="utf-8"))
        res["version_differs"] = {"python": rec["python"] != res["python"], "numpy": rec["numpy"] != res["numpy"],
                                  "recorded": {"python": rec["python"], "numpy": rec["numpy"]}}  # f6
        c = next(x for x in rec["cases"] if x["case"] == dv5_case)
        old = {s["k"]: s["V_os_hex"] for s in c["per_sample_vos"]}
        res["vs_dv5"] = {"sigma_bit": _bit(r["sigma_in_mV"], c["compare"]["sigma_recomputed"]),
                         "mean_bit": _bit(r["mean_in_mV"], c["compare"]["mean_recomputed"]),
                         "samples_bit": old == {s["k"]: s["V_os_hex"] for s in r["per_sample_vos"]}}
    with open(out_p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in res if k not in ("per_sample_vos", "inputs")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
