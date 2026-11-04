# -*- coding: utf-8 -*-
"""물리 정합 별도 측정. 사용: a_phys.py <iso_v> <work> <exe> <out.json>
P1 forced 직렬 재배치: 잔차가 큰 예측(비자명 hold 전류)으로 새 넷리스트와, 그 넷리스트의 hold 두 줄만 옛 배치로 되돌린 넷리스트를 돌려 V·i(V)·AC 비교.
   손 기대: 저항 부하 넷 KCL. 부호 = 넷에서 전압원으로 들어가는 전류.
P2 VDSAT: 실제 시뮬레이터 경로에서 큰 여유 -> FAIL 유지, 끈 소자·역방향 소자의 vdsat 인쇄 여부, nan 로그의 처리, sat_unknown 과 FAIL 동시 입력.
P3 D-1: noise·swing·MC 입력 거부(반환·산출물·시뮬레이터 실행 0), PM 칸, 옛 모듈이 실행 경로에 없는지(sys.modules).
"""
import copy, glob, json, os, re, shutil, subprocess, sys

ISO, WORK, EXE, OUT = sys.argv[1:5]
O = os.path.join(ISO, "skills/analog-gmid-design/tools/spice_oracle")
sys.path.insert(0, O)
RUN1 = os.path.join(os.path.dirname(WORK), "run1")
os.makedirs(WORK, exist_ok=True)
home = os.path.join(WORK, "home")
os.makedirs(home, exist_ok=True)
env = dict(os.environ)
env["HOME"] = env["USERPROFILE"] = home
for k in ("HOMEDRIVE", "HOMEPATH", "SPICE_USERINIT_DIR"):
    env.pop(k, None)
res = {}


def run_oracle(inp, name, *args):
    d = os.path.join(WORK, name)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    ip = os.path.join(d, "t.input.json")
    json.dump(inp, open(ip, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    code = ("import sys,json;sys.path.insert(0,%r);import oracle_run;rc=oracle_run.main(sys.argv[1:]);"
            "print('MODS='+json.dumps(sorted(m for m in sys.modules if m.startswith('oracle_') or m in('oracle_netlist','oracle_simulate','oracle_noise','oracle_swing','oracle_offset_mc','oracle_compare'))));sys.exit(rc)") % O
    r = subprocess.run([sys.executable, "-P", "-c", code, ip, os.path.join(d, "o"), *args], cwd=d, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r, os.path.join(d, "o")


base3 = json.load(open(os.path.join(RUN1, "R3", "t.input.json"), encoding="utf-8"))
# ---- P1
i1 = copy.deepcopy(base3)
i1["predictions"]["nodes"]["nout"] = 0.8
i1["predictions"]["nodes"]["pout"] = 0.2
r, od = run_oracle(i1, "p1", "--bias", "forced")
stem = glob.glob(os.path.join(od, "*.forced"))[0]
newcir = open(os.path.join(stem, "bench.cir"), encoding="utf-8").read()
oldcir = re.sub(r"^Vhold_(\S+) (\S+) hs_(\S+) DC (\S+)$", lambda m: f"Vhold_{m.group(1)} hs_{m.group(1)} 0 DC {m.group(4)}", newcir, flags=re.M)
oldcir = re.sub(r"^Lhold_(\S+) hs_(\S+) 0 (\S+)$", lambda m: f"Lhold_{m.group(1)} hs_{m.group(1)} {m.group(1)} {m.group(3)}", oldcir, flags=re.M)
d = os.path.join(WORK, "p1_old")
shutil.rmtree(d, ignore_errors=True)
os.makedirs(d)
open(os.path.join(d, "bench.cir"), "w", encoding="utf-8", newline="\n").write(oldcir)
ro = subprocess.run([EXE, "-b", "bench.cir"], cwd=d, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
oldlog = ro.stdout + ro.stderr
newlog = open(os.path.join(stem, "bench.log"), encoding="utf-8", errors="replace").read()
grab = lambda t: dict(re.findall(r"^\s*((?:v|i|@m)\S*)\s*=\s*(\S+)", t, re.M | re.I))  # noqa: E731
go, gn = grab(oldlog), grab(newlog)
sim = json.load(open(glob.glob(os.path.join(od, "*.forced.sim.json"))[0], encoding="utf-8"))
c = {"hold_lines_new": [x for x in newcir.splitlines() if "hold" in x.lower() and not x.startswith("print")],
     "hold_lines_old": [x for x in oldcir.splitlines() if "hold" in x.lower() and not x.startswith("print")],
     "printed_values_equal": go == gn, "n_values": len(gn), "diff": {k: (go.get(k), gn.get(k)) for k in set(go) | set(gn) if go.get(k) != gn.get(k)},
     "hold_current_A": sim["hold_current_A"], "nodes": sim["nodes"], "ids": {k: v["id"] for k, v in sim["devices"].items()}}
files = sorted(os.path.basename(x) for x in glob.glob(os.path.join(stem, "bench.*.txt")))
c["ac_files_equal"] = {f: open(os.path.join(stem, f), "rb").read() == open(os.path.join(d, f), "rb").read() for f in files}
vdd, rl, rp = base3["rails"][0]["voltage"], next(p for p in base3["passives"] if p["name"] == "RL")["value"], next(p for p in base3["passives"] if p["name"] == "RP")["value"]
# 손 기대: 넷 nout 에 RL 로 들어오는 전류 (vdd-0.8)/RL, M1 드레인으로 나가는 ID -> 전압원으로 들어가는 전류 = (vdd-0.8)/RL - ID_M1
# 넷 pout: MP1 드레인에서 들어오는 전류 ID_MP1(크기), RP 로 나가는 0.2/RP -> 전압원으로 들어가는 전류 = |ID_MP1| - 0.2/RP
c["hand_hold_nout"] = (vdd - 0.8) / rl - abs(sim["devices"]["M1"]["id"])
c["hand_hold_pout"] = abs(sim["devices"]["MP1"]["id"]) - 0.2 / rp
res["P1"] = c
# ---- P2
i2 = copy.deepcopy(base3)
ss = json.load(open(glob.glob(os.path.join(RUN1, "R3", "o", "*.free.sim.json"))[0], encoding="utf-8"))
sat_m1 = ss["devices"]["M1"]["vds"] - ss["devices"]["M1"]["vdsat"]
sat_p1 = ss["devices"]["MP1"]["vds"] - ss["devices"]["MP1"]["vdsat"]
res["P2_margins"] = {"M1": sat_m1, "MP1": sat_p1}
i2.setdefault("predictions", {}).setdefault("devices", {})
for n in ("M1", "MP1"):
    i2["predictions"]["devices"].setdefault(n, {})["off_current_A"] = 0.0
rows = {}
for name, margin in (("below_all", 0.0), ("between", (min(sat_m1, sat_p1) + max(sat_m1, sat_p1)) / 2), ("above_all", max(sat_m1, sat_p1) + 0.1)):
    r, od = run_oracle(i2, f"p2_{name}", "--bias", "free", "--sat-margin-v", repr(margin))
    cj = json.load(open(glob.glob(os.path.join(od, "*.free.compare.json"))[0], encoding="utf-8"))
    a = cj["summary"]["acceptance"]
    rows[name] = {"margin": margin, "rc": r.returncode, "verdict": cj["summary"]["verdict"], "reason": cj["summary"]["verdict_reason"][:200], "unsat": a["unsaturated_conducting"],
                  "unknown": a["saturation_unknown"], "conducting": a["conducting_devices"]}
res["P2_real_path"] = rows
# 끈 소자·역방향 소자의 vdsat
i3 = copy.deepcopy(i2)
i3["predictions"]["nodes"]["nin"] = 0.0             # M1 꺼짐(입력 DC 0)
r, od = run_oracle(i3, "p2_off", "--bias", "free", "--sat-margin-v", "0.0")
s3 = json.load(open(glob.glob(os.path.join(od, "*.free.sim.json"))[0], encoding="utf-8"))
cj3 = json.load(open(glob.glob(os.path.join(od, "*.free.compare.json"))[0], encoding="utf-8"))
res["P2_off"] = {"M1": s3["devices"]["M1"], "verdict": cj3["summary"]["verdict"], "unsat": cj3["summary"]["acceptance"]["unsaturated_conducting"], "unknown": cj3["summary"]["acceptance"]["saturation_unknown"]}
# nan 로그 처리: 어댑터 read 가 nan 을 None 으로 읽는가 + compare 사다리(프로세스 안 합성)
from adapters.ngspice import read as rd  # noqa: E402
res["P2_grab_nan"] = {"nan": rd._grab("@m.x.m[vdsat] = nan\n", "@m.x.m[vdsat]"), "num": rd._grab("@m.x.m[vdsat] = 1.0e-01\n", "@m.x.m[vdsat]"),
                      "inf": rd._grab("@m.x.m[vdsat] = inf\n", "@m.x.m[vdsat]")}
from core import compare as cmp  # noqa: E402
cdir = glob.glob(os.path.join(WORK, "p2_below_all", "o", "*.free.sim.json"))[0]
sim0 = json.load(open(cdir, encoding="utf-8"))
from core.build_circuit import circuit_ir  # noqa: E402
from core.descriptor import load_descriptor  # noqa: E402
D = load_descriptor(os.path.join(O, "descriptors/sky130.oracle_descriptor.json"), env=os.environ)
circ, _ = circuit_ir(i2, "free", descriptor=D)
m = circ.meta
meta = {"bias": "free", "lut_meta": {"corner": "tt", "temp_c": 27.0}, "geometry": m["geometry"], "nets": m["nets"], "held": m["held"], "gate_bias": m["gate_bias"], "inputs": m["inputs"], "notes": m["notes"],
        "blockers": [], "z1": None, "topology_identity": {"status": "unverified", "diffs": []}}
syn = {}
for name, patch, margin in (("vdsat_none_one_device", {"M1": {"vdsat": None}}, 0.0),
                            ("vdsat_none_and_other_fails", {"M1": {"vdsat": None}}, sat_p1 + 0.01),
                            ("vdsat_none_margin_unset", {"M1": {"vdsat": None}}, None),
                            ("control_no_patch", {}, 0.0)):
    s = copy.deepcopy(sim0)
    for k, v in patch.items():
        s["devices"][k].update(v)
    j = cmp.merge_judge(i2.get("judge"), None, margin)
    if margin is None:
        j = dict(j); j["sat_margin_V"] = None
    cr = cmp.compare(i2, meta, s, j)
    syn[name] = {"verdict": cr["summary"]["verdict"], "reason": cr["summary"]["verdict_reason"][:160], "unsat": cr["summary"]["acceptance"]["unsaturated_conducting"], "unknown": cr["summary"]["acceptance"]["saturation_unknown"]}
res["P2_synthetic"] = syn
# ---- P3
base1 = json.load(open(os.path.join(RUN1, "R1", "t.input.json"), encoding="utf-8"))
rows = {}
for name, patch in (("noise", {"noise": {"f_lo_hz": 1.0}}), ("swing_icmr", {"swing_icmr": {"swing": True}}), ("offset_mc", {"offset_mc": {"rel_resolution": 0.1}})):
    i = copy.deepcopy(base1)
    i.update(patch)
    r, od = run_oracle(i, f"p3_{name}", "--bias", "free")
    files = sorted(os.listdir(od))
    rec = json.load(open(os.path.join(od, files[0]), encoding="utf-8")) if len(files) == 1 else None
    rows[name] = {"rc": r.returncode, "files": files, "code": rec and rec["code"], "detail": rec and rec["detail"], "stage": rec and rec["stage"], "mods": r.stdout.strip().splitlines()[-1][:200]}
res["P3_rejects"] = rows
i = copy.deepcopy(json.load(open(os.path.join(RUN1, "R2", "t.input.json"), encoding="utf-8")))
r, od = run_oracle(i, "p3_pm", "--bias", "free", "--sat-margin-v", "0.0")
s = json.load(open(glob.glob(os.path.join(od, "*.free.sim.json"))[0], encoding="utf-8"))
cj = json.load(open(glob.glob(os.path.join(od, "*.free.compare.json"))[0], encoding="utf-8"))
res["P3_pm"] = {"ac": {k: s["ac"].get(k) for k in ("pm_deg", "pm_deg_raw", "pm_undefined", "pm_definition", "pm_crosscheck_deg", "pm_crosscheck_deg_raw", "stability")},
                "constraints": [{k: c.get(k) for k in ("measure", "spice", "judge", "undefined")} for c in cj.get("constraints", [])], "verdict": cj["summary"]["verdict"], "reason": cj["summary"]["verdict_reason"][:200],
                "mods": r.stdout.strip().splitlines()[-1][:200], "rc": r.returncode}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1, default=str)
print(json.dumps(res, ensure_ascii=False, indent=0, default=str))
