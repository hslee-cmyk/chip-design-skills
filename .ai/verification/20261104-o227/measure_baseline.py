"""O-227 auditor baseline measurement: one circuit per process, one output file per run (appends one JSON line).

usage: measure_baseline.py <checkout root> <circuit> <out jsonl>

Reports only the stage A/B level keys the fixture form holds for circuits with status != [ok, ok] (precedent: ngcc_3stage_ff):
stage_a_sha = every stage A report key except env_fp, stage_b_sha = every stage B report key except achievability,
achievability_sha = every achievability key (empty when achievability is null).
sha = canonical JSON sha256 by the test module's own `_sha`. Does not read the fixture to produce values.
Also records `shape`: per key, whether the report value is null / empty / non-empty.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT, CIRCUIT, OUT = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
SKILL = ROOT / "skills" / "analog-gmid-design"
sys.path[:0] = [str(SKILL), str(SKILL / "gmid_engine" / "tests" / "integration")]
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import test_s0_layer_9circuits as t  # noqa: E402
from gmid_engine.core import BoundedLRU, read_pdk_decl  # noqa: E402
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location  # noqa: E402
from gmid_engine.pipeline import run_stage_a, run_stage_b  # noqa: E402
from gmid_engine.search import open_run  # noqa: E402

assert Path(t.__file__).resolve().is_relative_to(ROOT.resolve()), t.__file__
loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
kinds = dict(t.DEVICE_KINDS)
mins = {}
for e in man["slices"]:
    mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
dm = BoundedLRU(16)
pdk = read_pdk_decl(str(SKILL / "assets" / "sky130_pdk_decl.json"), dm)
q = dict(pdk.quantities)
spec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), t.DEVICE_KINDS, t.CAP_SUFFIX,
               noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                   noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)


def shape(v):
    if v is None:
        return "null"
    if isinstance(v, (list, dict, str, tuple)) and len(v) == 0:
        return "empty"
    return "value"


def chain(tag):
    out = Path(tempfile.mkdtemp(prefix="o227m")) / tag
    donors, counters = open_run()
    a = run_stage_a(t.LIBRARY / (CIRCUIT + ".topology.json"), t.LIBRARY / (CIRCUIT + ".sizing_spec.json"), lut, output_dir=out,
                    donors=donors, counters=counters)
    memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
    b = run_stage_b(a, memo, pdk, output_dir=out, diagnostic=True, settings=t._settings())
    ra = json.loads(Path(a.report_paths[0]).read_text(encoding="utf-8"))
    rb = json.loads(Path(b.report_paths[0]).read_text(encoding="utf-8"))
    return [a.status, b.status], ra, rb, Path(a.report_paths[0]).read_bytes(), Path(b.report_paths[0]).read_bytes()


status, ra, rb, ba, bb = chain("first")
status2, _ra2, _rb2, ba2, bb2 = chain("second")
ach = rb.get("achievability")
entry = {"status": status,
         "stage_a_sha": {k: t._sha(v) for k, v in sorted(ra.items()) if k != "env_fp"},
         "stage_b_sha": {k: t._sha(v) for k, v in sorted(rb.items()) if k != "achievability"},
         "achievability_sha": {} if ach is None else {k: t._sha(v) for k, v in sorted(ach.items())}}
rec = {"circuit": CIRCUIT, "root": str(ROOT), "entry": entry,
       "second_run_identical": [status == status2, ba == ba2, bb == bb2],
       "shape": {"stage_a": {k: shape(v) for k, v in sorted(ra.items()) if k != "env_fp"},
                 "stage_b": {k: shape(v) for k, v in sorted(rb.items())},
                 "achievability": {} if ach is None else {k: shape(v) for k, v in sorted(ach.items())}},
       "counts": {"a_stop": len(ra.get("stop_reasons") or []), "a_review": len(ra.get("review_needed") or []),
                  "b_stop": len(rb.get("stop_reasons") or []), "exit": [ra.get("exit_code"), rb.get("exit_code")]}}
if ach is not None:
    g = ach["gain"]
    rec["gain"] = {"verdict": g.get("verdict"), "target_db": g.get("target_db"),
                   "blocks": [{"key": blk.get("key"), "members": blk.get("members"), "status": blk.get("status"),
                               "reason": blk.get("reason"), "pi": blk.get("pi"), "a_max_db": blk.get("a_max_db"),
                               "n_axes": len(blk.get("axes") or [])} for blk in list(g["blocks"]) + list(g["ff"])]}
    rec["ach_verdict"] = ach.get("verdict")
    rec["area_keys"] = sorted(ach["area"]) if isinstance(ach.get("area"), dict) else None
with open(OUT, "a", encoding="utf-8") as sink:
    sink.write(json.dumps(rec, ensure_ascii=False) + "\n")
print("appended", CIRCUIT)
