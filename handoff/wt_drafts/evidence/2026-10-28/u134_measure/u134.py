"""검증 2 독립 실측: U-134 (가) 구간 대 영점 상쇄값. 엔진 import·읽기만. 회로마다 결과 append."""
import json, math, os, sys, traceback, types
from pathlib import Path
import numpy as np

ENG = Path(sys.argv[1]); OUT = Path(sys.argv[2]); CIRCS = sys.argv[3].split(",")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
sys.path.insert(0, str(ENG)); sys.path.insert(0, str(ENG / "gmid_engine" / "tests" / "integration"))
pt = types.ModuleType("pytest"); pt.fixture = lambda *a, **k: (a[0] if a and callable(a[0]) else (lambda f: f))
class M:
    def __getattr__(self, n): return lambda *a, **k: (a[0] if a and callable(a[0]) else (lambda f: f))
pt.mark = M(); sys.modules.setdefault("pytest", pt)
import test_s0_layer_9circuits as T
from types import SimpleNamespace
from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.search import open_run
from gmid_engine.search.current_box import current_box
from gmid_engine.sizing import pre_layout_lut_access

loc = resolve_lut_location(str(T.SKILL / "assets" / "lut_v2_location.json"), os.environ)
man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
kinds = dict(T.DEVICE_KINDS); mins = {}
for e in man["slices"]:
    k = kinds[e["device"]]; mins[k] = min(e["w_um"] * 1e-6, mins.get(k, float("inf")))
pdk = read_pdk_decl(str(T.SKILL / "assets" / "sky130_pdk_decl.json"), BoundedLRU(16)); q = dict(pdk.quantities)
spec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), T.DEVICE_KINDS, T.CAP_SUFFIX,
               noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                   noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
memo = LutMemo(lut, point=1 << 14, curve=1 << 12, root=1 << 14)
access = pre_layout_lut_access(memo)
env = SimpleNamespace(lut=lut, pdk=pdk, root=OUT.parent / "runs", memo=memo,
                      rule=read_pdk_decl(str(T.SKILL / "assets" / "sky130_lut_rule_decl.json"), BoundedLRU(4)))


def gmid_domain(kind):
    """pre-layout 폭 슬라이스 on_mask 점의 gm/ID 범위(1/V)."""
    sl = access.memo.lut.slice_map[(kind, dict(access.w_keys)[kind])]
    on = np.asarray(sl.on_mask, dtype=bool) & np.isfinite(np.asarray(sl.log_GM)) & np.isfinite(np.asarray(sl.log_ID))
    g = np.exp(np.asarray(sl.log_GM) - np.asarray(sl.log_ID))[on]
    g = g[g > 0]
    return float(g.min()), float(g.max())


def find(snap, field):
    for kind in snap.kinds():
        for key in snap.keys(kind):
            r = snap.record(kind, key)
            if field in r.field_names():
                return r.get(field).value
    return None


def col(snap, kind, field):
    out = {}
    for key in snap.keys(kind):
        r = snap.record(kind, key)
        if field in r.field_names():
            out[key] = r.get(field).value
    return out


for c in CIRCS:
    row = {"circuit": c}
    try:
        topo = json.loads((T.LIBRARY / (c + ".topology.json")).read_text(encoding="utf-8"))
        sspec = json.loads((T.LIBRARY / (c + ".sizing_spec.json")).read_text(encoding="utf-8"))
        ev = sspec["human"].get("element_values", {})
        row["element_values"] = {k: (v if not isinstance(v, dict) else v.get("value_farad") or v.get("value_ohm") or ("engine" if v.get("engine") else str(v)[:80])) for k, v in ev.items()}
        donors, counters = open_run()
        a = run_stage_a(T.LIBRARY / (c + ".topology.json"), T.LIBRARY / (c + ".sizing_spec.json"), lut,
                        output_dir=env.root / c, donors=donors, counters=counters)
        b = run_stage_b(a, memo, pdk, output_dir=env.root / c, diagnostic=True, settings=T._settings())
        s = T._search_context(env, a, b)
        sch = find(s.dc.base, "theta_schema")
        kinds_d = col(s.dc.base, "device", "kind"); pins = {k: dict(v) for k, v in col(s.dc.base, "device", "pins").items()}
        terms = col(s.dc.base, "node", "terminals")
        res = []
        for z in sch.zero_cancel:
            zr = {"resistor": z.resistor, "end": z.end_net, "far": z.far_nets, "cells": z.cells, "reason": z.reason}
            lo_sum = hi_sum = 0.0; cell_info = []
            for cell in z.cells:
                k = kinds_d[cell]; gl, gh = gmid_domain(k); ioff, imax = current_box(access, k)
                lo_sum += gl * ioff; hi_sum += gh * imax
                cell_info.append({"cell": cell, "kind": k, "gmid": [gl, gh], "I_box": [ioff, imax], "pins": pins[cell]})
            zr["cells_info"] = cell_info
            zr["sum_gm_range_S"] = [lo_sum, hi_sum]
            zr["box_ohm"] = [1.0 / hi_sum, 1.0 / lo_sum]
            # 소자별 drain 넷·gate 넷과 그 넷에 붙은 수동소자
            for ci in cell_info:
                for side in ("d", "g"):
                    net = ci["pins"][side]
                    ci["net_" + side] = net
                    ci["passives_" + side] = sorted({e for e, _t in terms.get(net, ()) if e in ev or kinds_d.get(e) in ("capacitor", "resistor")})
            res.append(zr)
        row["zero_cancel"] = res
        row["theta_components_passive"] = [str(cc) for cc in sch.components if cc[0] in ("capacitance", "resistance", "ss_resistance")]
    except Exception:
        row["error"] = traceback.format_exc()[-1500:]
    with OUT.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=repr) + "\n")
    print(c, "done", flush=True)
