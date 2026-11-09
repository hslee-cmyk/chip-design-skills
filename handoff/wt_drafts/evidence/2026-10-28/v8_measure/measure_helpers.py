"""O-168 사실 실측(엔진 읽기·import만). library 9회로: 입력 포트 자기동형 궤도, 입력 포트 W4 뿌리·writer.
결과는 회로마다 out.jsonl에 append."""
import json, os, sys, traceback
from pathlib import Path

ENG_ROOT = Path(sys.argv[1])           # .../skills/analog-gmid-design
OUT = Path(sys.argv[2])
sys.path.insert(0, str(ENG_ROOT))
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
sys.path.insert(0, str(ENG_ROOT / "gmid_engine" / "tests" / "integration"))
import types as _types
_pt = _types.ModuleType("pytest")
_pt.fixture = lambda *a, **k: (a[0] if a and callable(a[0]) else (lambda f: f))
class _Mark:
    def __getattr__(self, name):
        return lambda *a, **k: (a[0] if a and callable(a[0]) else (lambda f: f))
_pt.mark = _Mark()
sys.modules.setdefault("pytest", _pt)
import test_s0_layer_9circuits as T    # env 구성·설정 helper 재사용(읽기만)
from types import SimpleNamespace
from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.search import open_run
from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access


def make_env(tmp):
    loc = resolve_lut_location(str(T.SKILL / "assets" / "lut_v2_location.json"), os.environ)
    man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
    kinds = dict(T.DEVICE_KINDS)
    mins = {}
    for e in man["slices"]:
        mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
    dm = BoundedLRU(16)
    pdk = read_pdk_decl(str(T.SKILL / "assets" / "sky130_pdk_decl.json"), dm)
    q = dict(pdk.quantities)
    spec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), T.DEVICE_KINDS, T.CAP_SUFFIX,
                   noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
    lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                       noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
    return SimpleNamespace(lut=lut, pdk=pdk, root=Path(tmp))


def find_field(snap, field):
    for kind in snap.kinds():
        for key in snap.keys(kind):
            rec = snap.record(kind, key)
            if field in rec.field_names():
                return kind, key, rec.get(field)
    return None


def column(snap, kind, field):
    out = {}
    for key in snap.keys(kind):
        rec = snap.record(kind, key)
        if field in rec.field_names():
            out[key] = rec.get(field).value
    return out


def main():
    env = make_env(OUT.parent / "runs")
    for circuit in T.CIRCUITS:
        row = {"circuit": circuit}
        try:
            donors, counters = open_run()
            out = env.root / circuit
            a = run_stage_a(T.LIBRARY / (circuit + ".topology.json"), T.LIBRARY / (circuit + ".sizing_spec.json"), env.lut,
                            output_dir=out, donors=donors, counters=counters)
            row["stage_a"] = a.status
            snap = a.s1.snapshot
            topo = json.loads((T.LIBRARY / (circuit + ".topology.json")).read_text(encoding="utf-8"))
            spec = json.loads((T.LIBRARY / (circuit + ".sizing_spec.json")).read_text(encoding="utf-8"))
            row["input_dc_spec"] = spec.get("input_dc", spec.get("human", {}).get("input_dc") if isinstance(spec.get("human"), dict) else None)
            pdir = column(snap, "node", "port_direction")
            inputs = sorted(n for n, d in pdir.items() if d == "input")
            row["port_direction"] = {n: d for n, d in pdir.items() if d}
            row["inputs"] = inputs
            orb = find_field(snap, "orbits")
            o = orb[2].value
            node_orb = dict(o.nodes)
            el_orb = dict(o.devices)
            row["input_node_orbits"] = {n: node_orb.get(n) for n in inputs}
            row["inputs_same_orbit"] = len({node_orb.get(n) for n in inputs}) == 1 if len(inputs) > 1 else None
            groups = {}
            for e, oid in el_orb.items():
                groups.setdefault(oid, []).append(e)
            row["nontrivial_element_orbits"] = sorted(sorted(g) for g in groups.values() if len(g) > 1)
            ngroups = {}
            for n, oid in node_orb.items():
                ngroups.setdefault(oid, []).append(n)
            row["nontrivial_node_orbits"] = sorted(sorted(g) for g in ngroups.values() if len(g) > 1)
            # 입력 포트 gate 소자
            pins = column(snap, "device", "pins")
            gate_of = {}
            for dev, p in pins.items():
                p = dict(p)
                if p.get("g") in inputs:
                    gate_of.setdefault(p["g"], []).append(dev)
            row["input_gate_devices"] = {k: sorted(v) for k, v in gate_of.items()}
            row["input_gate_device_orbits"] = {k: [el_orb.get(d) for d in sorted(v)] for k, v in gate_of.items()}
            # 쓰기 계획
            try:
                kctx = build_kernel_context(a.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(LutMemo(env.lut, point=1 << 12, curve=1 << 10, root=1 << 12)),
                                            donors=a.donors, counters=a.counters)
                base = kctx.base if hasattr(kctx, "base") else kctx[0]
                writers = column(base, "node", "dc_writer")
                row["input_writers"] = {n: repr(writers.get(n)) for n in inputs}
                roots = [n for n, w in writers.items() if getattr(w, "relation", None) == "window" or "window" in repr(w).lower()]
                row["w4_roots_all"] = sorted(roots)
                row["input_w4_roots"] = sorted(n for n in roots if n in inputs)
                coords = column(base, "device", "dc_coord")
                row["dependents"] = {d: repr(c) for d, c in coords.items() if "dependent" in repr(c).lower()}
                row["writer_plan"] = "ok"
            except Exception as exc:
                row["writer_plan"] = "error: " + type(exc).__name__ + " " + repr(getattr(exc, "detail", exc))[:600]
        except Exception as exc:
            row["error"] = traceback.format_exc()[-1500:]
        with OUT.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False, default=repr) + "\n")
        print(circuit, "done", flush=True)


main()
