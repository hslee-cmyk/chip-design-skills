# -*- coding: utf-8 -*-
"""OP-1a (d) 선택 대조 -- base 판 옛 함수 `offset_mc_measure`를 기준선 MC 로그에 돌린다(design §13.2: 모듈 전역 `run_ngspice` 이름 교체 경로).

검증자 작성. 옛 함수(5fea301:skills/analog-gmid-design/tools/spice_oracle/oracle_offset_mc.py:109-194)를 격리 복제본에서 import하고,
`oracle_offset_mc.run_ngspice`(:38에서 들어온 이름)를 저장된 기준선 로그를 돌려주는 함수로 바꾼다. 시뮬레이터가 돌지 않음을 보이려고
`subprocess.run`·`subprocess.Popen`을 부르면 예외를 내는 함수로 바꾸고 호출 수를 센다(0이어야 한다).
옛 함수가 쓰는 파일(.mc.cir)은 작업 폴더 사본에 쓴다(커밋된 기준선 파일을 바꾸지 않는다). 그 .mc.cir을 기준선 .mc.cir과 바이트 대조한다.
이 대조는 재계산 스크립트(dv5_vos_recompute.py)를 대신하지 않는다 -- 옛 함수는 표본별 V_os를 반환하지 않는다.
주의: 옛 `mismatch_vars`는 넷리스트 .include 대상(C:/pdk/sky130_fd_pr 모델 카드)을 읽는다(저장소 밖 읽기 -- 이 선택 대조에만).

사용: python -P dv5_d_old_function.py <base 판 spice_oracle 폴더> <record 폴더> <작업 폴더> <결과 json>
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

ORACLE, REC, WORK, OUT = sys.argv[1:5]
FILES = os.path.join(REC, "baseline", "files")
sys.path.insert(0, ORACLE)
import oracle_offset_mc as omc  # noqa: E402

calls = {"subprocess": 0, "run_ngspice": []}


def _deny(*a, **k):
    calls["subprocess"] += 1
    raise RuntimeError("subprocess 금지(선택 대조는 시뮬레이터를 돌리지 않는다)")


subprocess.run = _deny
subprocess.Popen = _deny


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


CASES = [
    {"case": "pytest/mc5t0", "dir": "pytest/tmp/mc5t0/o", "stem": "t5ota.free", "input": os.path.join(FILES, "pytest/tmp/mc5t0/o/t.input.json"),
     "baseline": ("sim.json", "t5ota.free.sim.json")},
    {"case": "u6/mc_5t", "dir": "u6", "stem": "t5t.free", "input": os.path.join(REC, "input_bundle/u6/mc_5t.input.json"),
     "baseline": ("u6", "u6_selfchecks.json")},
]
res = {"script": os.path.basename(__file__), "script_sha256": sha(__file__), "oracle_dir": ORACLE.replace("\\", "/"),
       "old_module_file": os.path.abspath(omc.__file__).replace("\\", "/"), "old_module_sha256": sha(omc.__file__), "cases": []}
for c in CASES:
    src = os.path.join(FILES, c["dir"])
    wd = os.path.join(WORK, c["case"].replace("/", "_"))
    os.makedirs(wd, exist_ok=True)
    meta = json.load(open(os.path.join(src, c["stem"] + ".cir.meta.json"), encoding="utf-8"))
    for f in (c["stem"] + ".cir", c["stem"] + ".cir.meta.json", meta["ac_file"]):
        shutil.copyfile(os.path.join(src, f), os.path.join(wd, f))
    inp = json.load(open(c["input"], encoding="utf-8"))
    log_src = os.path.join(src, c["stem"] + ".mc.log")
    kind, bname = c["baseline"]
    bj = json.load(open(os.path.join(src, bname), encoding="utf-8"))
    rc_base = bj["offset_mc"]["ngspice_rc"] if kind == "sim.json" else 0

    def fake_run_ngspice(exe, cir_path, log_path, timeout_s=None, cache_dir=None, outputs=(), _src=log_src, _rc=rc_base):
        calls["run_ngspice"].append(os.path.basename(cir_path))
        shutil.copyfile(_src, log_path)                       # 옛 run_ngspice처럼 로그 파일을 log_path에 두고
        with open(log_path, encoding="utf-8", errors="replace") as f:   # oracle_simulate.py:120-121과 같은 읽기
            return _rc, f.read(), None

    omc.run_ngspice = fake_run_ngspice
    out = omc.offset_mc_measure(inp, os.path.join(wd, c["stem"] + ".cir"), meta, "(시뮬레이터 없음)", None, None)
    out_rt = json.loads(json.dumps(out, ensure_ascii=False))
    mc_new, mc_base = os.path.join(wd, c["stem"] + ".mc.cir"), os.path.join(src, c["stem"] + ".mc.cir")
    rec = {"case": c["case"], "run_ngspice_calls": list(calls["run_ngspice"]), "subprocess_calls": calls["subprocess"],
           "mc_cir_sha256": sha(mc_new), "baseline_mc_cir_sha256": sha(mc_base), "mc_cir_bit_identical": sha(mc_new) == sha(mc_base),
           "sigma_in_mV": out.get("sigma_in_mV"), "mean_in_mV": out.get("mean_in_mV"), "status": out.get("status")}
    if kind == "sim.json":
        b = bj["offset_mc"]
        diff = sorted(k for k in set(b) | set(out_rt) if b.get(k, "<없음>") != out_rt.get(k, "<없음>"))
        rec.update(baseline_sigma=b["sigma_in_mV"], baseline_mean=b["mean_in_mV"],
                   sigma_bit_identical=float(out["sigma_in_mV"]).hex() == float(b["sigma_in_mV"]).hex(),
                   mean_bit_identical=float(out["mean_in_mV"]).hex() == float(b["mean_in_mV"]).hex(),
                   whole_offset_mc_dict_equal=not diff, differing_keys=diff)
    else:
        b = bj["mc_5t"]
        rec.update(baseline_sigma=b["mc_sigma_in_mV"], baseline_mean=None,
                   sigma_bit_identical=float(out["sigma_in_mV"]).hex() == float(b["mc_sigma_in_mV"]).hex(),
                   mean_bit_identical=None, n_samples_equal=out.get("n_samples") == b["mc_n"],
                   rel_se_equal=out.get("rel_se_achieved") == b["mc_rel_se"])
    calls["run_ngspice"].clear()
    res["cases"].append(rec)
res["subprocess_calls_total"] = calls["subprocess"]
res["all_sigma_mean_bit_identical"] = all(r["sigma_bit_identical"] and r["mean_bit_identical"] in (True, None) for r in res["cases"])
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print(json.dumps({r["case"]: {k: r.get(k) for k in ("sigma_bit_identical", "mean_bit_identical", "whole_offset_mc_dict_equal", "differing_keys",
                                                     "mc_cir_bit_identical", "run_ngspice_calls", "subprocess_calls")} for r in res["cases"]},
                 ensure_ascii=False, indent=1))
