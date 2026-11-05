"""usage: dump_chain.py <skill root> <out json>  -- 2회로 사슬의 stage_b gain, S0 지문, metric_structure 를 파일에 쓴다."""
import dataclasses
import importlib.util
import json
import os
import pathlib
import sys
import tempfile

skill = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(skill))
sys.path.insert(0, str(skill / "gmid_engine" / "tests" / "integration"))
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
spec = importlib.util.spec_from_file_location("s0mod", skill / "gmid_engine" / "tests" / "integration" / "test_s0_layer_9circuits.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

from types import SimpleNamespace
from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.lut import LutSpec, load_lut_set, resolve_lut_location

SKILL = skill
loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
man = json.loads(pathlib.Path(loc.manifest_path).read_text(encoding="utf-8"))
kinds = dict(M.DEVICE_KINDS)
mins = {}
for e in man["slices"]:
    mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
dm = BoundedLRU(16)
pdk = read_pdk_decl(str(SKILL / "assets" / "sky130_pdk_decl.json"), dm)
q = dict(pdk.quantities)
lspec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), M.DEVICE_KINDS, M.CAP_SUFFIX,
                noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, lspec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                   noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
tmp = pathlib.Path(tempfile.mkdtemp(prefix="dumpch", dir=os.environ["AUDIT_TMP"]))
env = SimpleNamespace(lut=lut, pdk=pdk, rule=read_pdk_decl(str(SKILL / "assets" / "sky130_lut_rule_decl.json"), dm), root=tmp, runs={})


def plain(v):
    if dataclasses.is_dataclass(v) and not isinstance(v, type):
        return {f.name: plain(getattr(v, f.name)) for f in dataclasses.fields(v)}
    if isinstance(v, (list, tuple)):
        return [plain(x) for x in v]
    if isinstance(v, dict):
        return {str(k): plain(x) for k, x in v.items()}
    if isinstance(v, frozenset):
        return sorted(str(x) for x in v)
    return v if isinstance(v, (int, float, str, type(None), bool)) else repr(v)


out = {}
for circuit in ("folded_cascode", "ngcc_3stage_ff"):
    run = M._chain(env, circuit, "first")
    item = {"status": run.status, "gain": (run.report_b.get("achievability") or {}).get("gain"),
            "ach_keys": {k: M._sha(v) for k, v in (run.report_b.get("achievability") or {}).items()},
            "report_b_keys": {k: M._sha(v) for k, v in run.report_b.items()},
            "report_a_keys": {k: M._sha(v) for k, v in run.report_a.items()},
            "stats": {k: [getattr(r, "computes", None), getattr(r, "recomputes_same_input", None)] for k, r in run.stats.items()}}
    if run.base is not None:
        item["s1v_metric_structure"] = plain(run.base.field("graph", "s1v", "metric_structure").value)
        item["start_fp"] = {f: run.base.field("graph", "start", f).value_fp for f in ("rungs", "conflicts", "inactive", "macro", "records", "area_est_m2", "area_fraction", "uncovered")}
        item["kernel_fp"] = {f: getattr(run.base.field("graph", "kernel", f), "value_fp", None) for f in ("theta_schema", "fixed_values", "resistor_values", "l_ties", "search_domain", "mismatch_source", "passive_area_decl", "model_error")}
        item["metric_structure_fp"] = run.base.field("graph", "s1v", "metric_structure").value_fp
        item["context_fp"] = run.context_fp
    out[circuit] = item
    pathlib.Path(sys.argv[2]).write_text(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True, default=repr), encoding="utf-8")
print("done")
