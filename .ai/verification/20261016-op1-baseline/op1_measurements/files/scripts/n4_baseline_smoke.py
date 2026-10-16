"""OP-1 N4-1 baseline (part A): smoke oracle_input x {free, forced} through oracle_run.py on base (worktree, read only).
The smoke inputs carry a stale process.lut_npz path (wt/ng-oracle4/..., absent). The verifier patches ONLY that field to the
same-named file in this worktree (assets/sky130_nfet_pfet_lut_sample.npz) and records both sha256. Results appended per case."""
import hashlib, json, os, subprocess, sys, time, glob
SRC = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op1/src/skills/analog-gmid-design"
O = SRC + "/tools/spice_oracle"
BASE = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op1/baseline"
OUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op1/results/n4_baseline.jsonl"
LUT = SRC + "/assets/sky130_nfet_pfet_lut_sample.npz"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def app(rec):
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


os.makedirs(BASE + "/inputs", exist_ok=True)
cases = sys.argv[1:] or ["sizing.engine", "layout.engine", "layout.topology"]
for c in cases:
    src = f"{O}/smoke/current_reuse_telescopic_ota.{c}.oracle_input.json"
    d = json.load(open(src, encoding="utf-8"))
    old = d["process"]["lut_npz"]
    d["process"]["lut_npz"] = LUT.replace("/", "\\")
    pin = f"{BASE}/inputs/current_reuse_telescopic_ota.{c}.oracle_input.json"
    json.dump(d, open(pin, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    od = f"{BASE}/smoke/{c}"
    os.makedirs(od, exist_ok=True)
    cmd = [sys.executable, f"{O}/oracle_run.py", pin, od, "--bias", "free", "forced", "--judge", f"{O}/smoke/smoke_judge.json"]
    t0 = time.perf_counter()
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    dt = time.perf_counter() - t0
    open(f"{od}/oracle_run.stdout.txt", "w", encoding="utf-8").write(r.stdout + "\n--stderr--\n" + r.stderr)
    files = {os.path.basename(p): sha(p) for p in sorted(glob.glob(od + "/*")) if os.path.isfile(p)}
    stab = {}
    for p in glob.glob(od + "/*.sim.json"):
        s = json.load(open(p, encoding="utf-8"))
        ac = s.get("ac") or {}
        stab[os.path.basename(p)] = {k: (ac.get("stability") or {}).get(k) for k in ("verdict", "windows_run", "early_stop", "status")} \
            if isinstance(ac, dict) else None
    app({"case": f"smoke.{c}", "rc": r.returncode, "wall_s": dt, "stdout_tail": r.stdout[-1500:], "stderr_tail": r.stderr[-800:],
         "input_orig": src, "input_orig_sha256": sha(src), "lut_npz_orig": old, "lut_npz_orig_exists": os.path.exists(old),
         "input_patched": pin, "input_patched_sha256": sha(pin), "lut_npz_used": LUT, "lut_sha256": sha(LUT),
         "outputs_sha256": files, "stability": stab})
    print(c, r.returncode, round(dt, 1), flush=True)
