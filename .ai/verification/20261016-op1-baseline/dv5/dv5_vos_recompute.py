# -*- coding: utf-8 -*-
"""OP-1a (a)(b)(c) -- 기준선 표본별 V_os 재계산과 σ_in·mean_in 비트 동일 판정(design B-26: (b)·(c) 한 스크립트).

재구현 대상 = 5fea301e35c1461be10d9969bfccdd827b668c98:skills/analog-gmid-design/tools/spice_oracle/oracle_offset_mc.py:166-195
  (blob 274559cc3c308ff2518552f35ffe329d18d5b029, 같은 blob이 3fc2f20(2026-10-09) 이후 바뀌지 않음 -- 기준선 실행 2026-10-16과 같은 판).
  보조로 같은 함수의 차동 이득 A 결정 :130-140(`.ac` 첫 점 h0, |Im h0| <= 1e-3·|h0|이면 A = Re h0)와
  `oracle_simulate.parse_ac_file`(:161-174), 로그 읽기(run_ngspice :120-121 = utf-8·errors=replace 텍스트 모드), 노드 정규식 :40을 다시 쓴다.
옛 코드를 import하지 않는다(검증자 독립 재구현). 옛 함수는 표본별 V_os를 반환하지 않으므로(지역 변수 `vos`) 이 스크립트가 낸다(O-9).
입력은 커밋된 판정용 텍스트만(<files 루트> = .ai/verification/20261016-op1-baseline/baseline/files, 그리고 input_bundle/u6).

사용: python -P dv5_vos_recompute.py <record 폴더(.ai/verification/20261016-op1-baseline)> <결과 json>
"""
import hashlib
import json
import math
import os
import platform
import re
import sys

import numpy as np

REC, OUT = sys.argv[1:3]
FILES = os.path.join(REC, "baseline", "files")
BASE_SHA = "5fea301e35c1461be10d9969bfccdd827b668c98"
OLD_BLOB = "274559cc3c308ff2518552f35ffe329d18d5b029"

# oracle_offset_mc.py:40
_NODE_RE = re.compile(r"^\s*(v)\(([^)]+)\)\s*=\s*([-+0-9.eE]+)\s*$", re.I | re.M)


def sha256(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def read_log(p):
    # oracle_simulate.py:120-121 (run_ngspice가 돌려주는 로그 텍스트와 같은 읽기)
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


def parse_ac_file(path):
    # oracle_simulate.py:161-174
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


def a_signed_from_ac(ac_path):
    # oracle_offset_mc.py:130-140 (h0 = .ac 첫 점, 실수 판정 1e-3)
    h0 = None
    raw = parse_ac_file(ac_path)                                   # :131
    if raw:                                                        # :132
        h0 = complex(raw[1][0], raw[2][0])                         # :133
    if h0 is None or abs(h0) == 0:                                 # :134-136
        return None, h0
    a_signed = h0.real if abs(h0.imag) <= 1e-3 * abs(h0) else None  # :137-140
    return a_signed, h0


def sample_count(rel_resolution, max_samples=None):
    # oracle_offset_mc.py:43-49 (호출 :141)
    n = math.ceil(1 + 1 / (2 * rel_resolution ** 2))
    capped = False
    if max_samples is not None and n > max_samples:
        n, capped = int(max_samples), True
    return n, capped, 1 / math.sqrt(2 * (n - 1))


def old_166_195(log, meta, ports, a_signed, n):
    """oracle_offset_mc.py:166-195 줄 단위 재구현. 표본 번호 k(1..n)를 붙여 표본별 값을 함께 돌려준다."""
    sn, outs = meta["spice_node"], meta["output_nodes"]                                  # :166
    ip, im = sn[ports["input_p"]].lower(), sn[ports["input_n"]].lower()                  # :167
    o1 = outs[0].lower()                                                                 # :168
    o2 = None if outs[1] == "0" else outs[1].lower()                                     # :169
    rows, fails = [], 0                                                                  # :170
    for blk in re.split(r"^MCS\s+", log, flags=re.M)[1:]:                                # :171
        vals = {m.group(2).lower(): float(m.group(3)) for m in _NODE_RE.finditer(blk)}  # :172
        if ip in vals and im in vals and o1 in vals and (o2 is None or o2 in vals):      # :173
            rows.append((vals[ip] - vals[im], vals[o1] - (vals[o2] if o2 else 0.0)))     # :174
        else:                                                                            # :175
            rows.append(None)                                                            # :176
            fails += 1                                                                   # :177
    if len(rows) != n + 1 or rows[0] is None:                                            # :178
        return {"status": "failed", "n_blocks": len(rows), "n_failed": fails}            # :179-182 (사유 문장은 생략)
    vid0, vout0 = rows[0]                                                                # :183
    vos = [(vo - vout0) / a_signed - (vi - vid0) for r in rows[1:] if r is not None for vi, vo in [r]]  # :184
    ks = [k for k, r in enumerate(rows) if k > 0 and r is not None]                      # (표본 번호 -- 옛 코드에 없는 기록용 칸)
    arr = np.asarray(vos, float)                                                         # :185
    ok = len(arr)                                                                        # :186
    return {                                                                             # :187-191
        "status": "ok" if ok > 1 else "failed", "n_samples": ok, "n_requested": n, "n_failed": fails,
        "rel_se_achieved": 1 / math.sqrt(2 * (ok - 1)) if ok > 1 else None,
        "sigma_in_mV": float(arr.std(ddof=1) * 1e3) if ok > 1 else None,                 # :190
        "mean_in_mV": float(arr.mean() * 1e3) if ok else None,                           # :190
        "_rows0": [vid0, vout0], "_rows": [[k] + list(rows[k]) for k in ks], "_vos": vos, "_ks": ks,
    }


def bit(a, b):
    return a is not None and b is not None and float(a).hex() == float(b).hex()


CASES = [
    {   # test_oracle_offset_mc.py:54-63 fixture mc_run (seed 0, r 0.05) -> oracle_run CLI
        "case": "pytest/mc5t0", "dir": os.path.join(FILES, "pytest/tmp/mc5t0/o"),
        "log": "t5ota.free.mc.log", "meta": "t5ota.free.cir.meta.json", "input": os.path.join(FILES, "pytest/tmp/mc5t0/o/t.input.json"),
        "baseline_out": ("sim.json", "t5ota.free.sim.json"),
    },
    {   # u6_selfchecks.py:91-127 mc_5t (seed 7, r 0.05) -> offset_mc_measure 직접 호출
        "case": "u6/mc_5t", "dir": os.path.join(FILES, "u6"),
        "log": "t5t.free.mc.log", "meta": "t5t.free.cir.meta.json", "input": os.path.join(REC, "input_bundle/u6/mc_5t.input.json"),
        "baseline_out": ("u6", "u6_selfchecks.json"),
    },
]

res = {"script": os.path.basename(__file__), "script_sha256": sha256(__file__), "reimplements": f"{BASE_SHA}:skills/analog-gmid-design/tools/spice_oracle/oracle_offset_mc.py:166-195",
       "old_blob": OLD_BLOB, "python": platform.python_version(), "numpy": np.__version__, "cases": []}
for c in CASES:
    d = c["dir"]
    meta_p, log_p = os.path.join(d, c["meta"]), os.path.join(d, c["log"])
    meta = json.load(open(meta_p, encoding="utf-8"))
    inp = json.load(open(c["input"], encoding="utf-8"))
    ac_p = os.path.join(d, meta["ac_file"])
    a_ac, h0 = a_signed_from_ac(ac_p)
    kind, bname = c["baseline_out"]
    bpath = os.path.join(d, bname)
    bj = json.load(open(bpath, encoding="utf-8"))
    cfg = inp["offset_mc"]
    n, capped, _ = sample_count(float(cfg["rel_resolution"]), cfg.get("max_samples"))
    if kind == "sim.json":
        b = bj["offset_mc"]
        base_vals = {"sigma_in_mV": b["sigma_in_mV"], "mean_in_mV": b["mean_in_mV"], "n_samples": b["n_samples"],
                     "n_requested": b["n_requested"], "n_failed": b["n_failed"], "rel_se_achieved": b["rel_se_achieved"],
                     "a_dc_signed": b["a_dc_signed"], "seed": b["seed"]}
        a_use = b["a_dc_signed"]
    else:
        b = bj["mc_5t"]
        base_vals = {"sigma_in_mV": b["mc_sigma_in_mV"], "mean_in_mV": None, "n_samples": b["mc_n"], "rel_se_achieved": b["mc_rel_se"],
                     "a_dc_signed": None, "seed": cfg.get("seed")}
        a_use = a_ac
    r = old_166_195(read_log(log_p), meta, inp["ports"], a_use, n)
    cmp = {
        "a_from_ac_first_point": a_ac, "a_from_ac_hex": float(a_ac).hex() if a_ac is not None else None,
        "a_used": a_use, "a_used_source": "기준선 출력 a_dc_signed" if kind == "sim.json" else "기준선 .ac 첫 점(:130-140 재구현) -- 기준선 출력에 a 칸 없음",
        "a_bit_identical_ac_vs_baseline": bit(a_ac, base_vals["a_dc_signed"]) if base_vals["a_dc_signed"] is not None else None,
        "n_from_sample_count": n, "n_requested_baseline": base_vals.get("n_requested"),
        "sigma_recomputed": r.get("sigma_in_mV"), "sigma_baseline": base_vals["sigma_in_mV"],
        "sigma_bit_identical": bit(r.get("sigma_in_mV"), base_vals["sigma_in_mV"]),
        "mean_recomputed": r.get("mean_in_mV"), "mean_baseline": base_vals["mean_in_mV"],
        "mean_bit_identical": bit(r.get("mean_in_mV"), base_vals["mean_in_mV"]) if base_vals["mean_in_mV"] is not None else None,
        "n_samples_equal": r.get("n_samples") == base_vals["n_samples"],
        "rel_se_bit_identical": bit(r.get("rel_se_achieved"), base_vals["rel_se_achieved"]),
        "n_failed_equal": (r.get("n_failed") == base_vals["n_failed"]) if "n_failed" in base_vals else None,
    }
    judged = [cmp["sigma_bit_identical"], cmp["n_samples_equal"], cmp["rel_se_bit_identical"]]
    judged += [x for x in (cmp["mean_bit_identical"], cmp["a_bit_identical_ac_vs_baseline"], cmp["n_failed_equal"]) if x is not None]
    verdict = "BIT_IDENTICAL" if all(judged) and r.get("status") == "ok" else "DIFFERENT_STOP"
    samples = [{"k": k, "V_id": row[1], "V_out": row[2], "V_os_V": v, "V_os_hex": float(v).hex()}
               for k, row, v in zip(r["_ks"], r["_rows"], r["_vos"])] if r.get("status") == "ok" else []
    res["cases"].append({
        "case": c["case"], "verdict": verdict, "status": r.get("status"), "seed": base_vals["seed"],
        "inputs": {os.path.relpath(p, REC).replace("\\", "/"): sha256(p) for p in (log_p, meta_p, c["input"], ac_p, bpath)},
        "baseline_kind": kind, "compare": cmp, "sample0": {"V_id0": r["_rows0"][0], "V_out0": r["_rows0"][1]} if r.get("status") == "ok" else None,
        "per_sample_vos": samples,
    })
res["all_bit_identical"] = all(c["verdict"] == "BIT_IDENTICAL" for c in res["cases"])
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print(json.dumps({c["case"]: {"verdict": c["verdict"], **{k: c["compare"][k] for k in ("sigma_recomputed", "sigma_baseline", "sigma_bit_identical",
                                                                                         "mean_recomputed", "mean_baseline", "mean_bit_identical",
                                                                                         "a_bit_identical_ac_vs_baseline")}, "n": len(c["per_sample_vos"])}
                  for c in res["cases"]}, ensure_ascii=False, indent=1))
