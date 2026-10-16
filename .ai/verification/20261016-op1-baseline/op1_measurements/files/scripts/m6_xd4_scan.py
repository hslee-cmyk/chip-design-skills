"""X-D4: baseline oracle inputs whose testbench.options lack reltol / vntol / abstol (design §8.3: such an input stops with
dc_tolerance_undeclared until the adapter default tolerances have a manual page). Scans every JSON under baseline/ with
schema spice_oracle_input/1 (smoke patched inputs + inputs the oracle tests wrote to tmp)."""
import glob, json, os, collections
B = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op1/baseline"
OUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op1/results/m6_xd4_scan.json"
KEYS = ("reltol", "vntol", "abstol")
rows = []
for p in glob.glob(B + "/**/*.json", recursive=True):
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue
    if not isinstance(d, dict) or d.get("schema") != "spice_oracle_input/1":
        continue
    o = {k.lower(): v for k, v in (((d.get("testbench") or {}).get("options")) or {}).items()}
    miss = [k for k in KEYS if k not in o]
    rows.append({"file": os.path.relpath(p, B), "circuit": d.get("circuit"), "missing": miss,
                 "has_mc_or_noise_or_swing": [k for k in ("offset_mc", "noise", "swing_icmr") if d.get(k)]})
aff = [r for r in rows if r["missing"]]
by_test = collections.Counter(r["file"].split(os.sep)[1] if r["file"].startswith("pytest") else r["file"].split(os.sep)[0] for r in aff)
res = {"n_inputs": len(rows), "n_missing_any": len(aff), "missing_patterns": {"+".join(k): v for k, v in collections.Counter(tuple(r["missing"]) for r in aff).items()},
       "affected_by_dir": dict(by_test), "affected": aff}
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print({k: v for k, v in res.items() if k != "affected"})
