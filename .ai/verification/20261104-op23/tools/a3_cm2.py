# -*- coding: utf-8 -*-
"""CM 루프 벤치 원인 확인: 새 벤치에서 입력 AC 를 0 으로만 고쳐 돌리면 기준선 값으로 돌아오는가. 사용: a3_cm2.py <iso_v> <cm_work> <exe> <out.json>"""
import glob, json, os, re, shutil, subprocess, sys
import numpy as np

ISO, WORK, EXE, OUT = sys.argv[1:5]
O = os.path.join(ISO, "skills/analog-gmid-design/tools/spice_oracle")
sys.path.insert(0, O)
from adapters.ngspice import read as R  # noqa: E402
from core.measures_ac import ac_measures, loop_gain  # noqa: E402
from core.requests import NodeV, BranchI, expr_key  # noqa: E402
from core.results import FreqSeries  # noqa: E402

FILES = os.path.join(ISO, ".ai/verification/20261016-op1-baseline/baseline/files")
bs = json.load(open(os.path.join(FILES, "pytest/tmp/cmfb0/out/tcm_cmfb.free.sim.json"), encoding="utf-8"))
ns = json.load(open(os.path.join(WORK, "c0/o/tcm_cmfb.free.sim.json"), encoding="utf-8"))
bench = os.path.join(WORK, "c0/o/tcm_cmfb.free.cmloop")
txt = open(os.path.join(bench, "bench.cir"), encoding="utf-8").read()
lines = [ln for ln in txt.splitlines() if ln.startswith(("Vac_", "Vlb_", "Ilb_"))]
d2 = os.path.join(WORK, "c0_ac0")
shutil.rmtree(d2, ignore_errors=True)
os.makedirs(d2)
fixed = re.sub(r"^(Vac_\S+ \S+ \S+ DC 0) AC \S+$", r"\1 AC 0", txt, flags=re.M)
open(os.path.join(d2, "bench.cir"), "w", encoding="utf-8", newline="\n").write(fixed)
env = dict(os.environ)
env["HOME"] = env["USERPROFILE"] = os.path.join(WORK, "home")
for k in ("HOMEDRIVE", "HOMEPATH", "SPICE_USERINIT_DIR"):
    env.pop(k, None)
subprocess.run([EXE, "-b", "bench.cir"], cwd=d2, env=env, capture_output=True)
nets = ns["cm_loop"]["break_nets"]
w = ns["cm_loop"]["weights"]


def meas(dirp):
    fv, cv = R._cols(os.path.join(dirp, "bench.cm.v.txt"))
    fi, ci = R._cols(os.path.join(dirp, "bench.cm.i.txt"))
    vk = {}
    for j, n in enumerate(nets):
        vk[f"v(lbx_{n})"] = cv[2 * j]
        vk[f"v({n})"] = cv[2 * j + 1]
    ik = {}
    for j, n in enumerate(nets):
        ik[f"i(tb:lb:{n})"] = ci[j]
        ik[f"v({n})"] = ci[len(nets) + j]
    V = FreqSeries(fv, vk, None, None)
    I = FreqSeries(fi, ik, None, None)
    return ac_measures(*loop_gain(V, I, w, nets))


m_new, m_fix = meas(bench), meas(d2)
bm = bs["cm_loop"]["measures"]
res = {"bench_lines": lines, "baseline": {k: bm.get(k) for k in ("gain_dc", "ugf_hz", "pm_deg", "f3db_hz")},
       "new_as_committed": {k: m_new.get(k) for k in ("gain_dc", "ugf_hz", "pm_deg", "f3db_hz")},
       "new_with_input_ac_0": {k: m_fix.get(k) for k in ("gain_dc", "ugf_hz", "pm_deg", "f3db_hz")},
       "rel_gain_committed_vs_baseline": abs(m_new["gain_dc"] - bm["gain_dc"]) / bm["gain_dc"], "rel_gain_fixed_vs_baseline": abs(m_fix["gain_dc"] - bm["gain_dc"]) / bm["gain_dc"]}
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=0))
