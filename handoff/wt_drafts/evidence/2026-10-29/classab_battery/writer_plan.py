# as-built 사실 확인: current_reuse 의 dc_writer_plan 이 class-AB 고리 멤버 중 누구를 종속(cycle_vgs)으로 두는지. 읽기 전용.
import sys, os, json, pathlib
SKILL = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
sys.path.insert(0, str(SKILL))
OUT = pathlib.Path(__file__).with_suffix(".out.txt")
f = open(OUT, "w", encoding="utf-8")
from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a
from gmid_engine.search import open_run
from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access
sys.path.insert(0, str(SKILL / "gmid_engine/tests/integration"))
import nfr4_run_dump as N
loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
man = json.loads(pathlib.Path(loc.manifest_path).read_text(encoding="utf-8"))
kinds = dict(N.DEVICE_KINDS); mins = {}
for e in man["slices"]:
    mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
dm = BoundedLRU(16)
pdk = read_pdk_decl(str(SKILL / "assets" / "sky130_pdk_decl.json"), dm)
q = dict(pdk.quantities)
spec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), N.DEVICE_KINDS, N.CAP_SUFFIX,
               noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                   noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
donors, counters = open_run()
lib = SKILL / "assets/library"
work = pathlib.Path(__file__).parent / "_stage_a"; work.mkdir(exist_ok=True)
a = run_stage_a(lib / "current_reuse_telescopic_ota.topology.json", lib / "current_reuse_telescopic_ota.sizing_spec.json", lut,
                output_dir=work, donors=donors, counters=counters)
f.write(f"stage_a status {a.status}\n"); f.flush()
memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
k = build_kernel_context(a.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo), donors=donors, counters=counters)
coords = dict(k.base.column("device", "dc_coord"))
for m in ["M11a","M11b","M15","M9a","M14a","M14b","M16","M9b","M20a","M20b","M25","M18a","M23a","M24b","M26","M18b","M8","M10","M12","M13"]:
    f.write(f"{m} {coords.get(m)}\n")
writers = dict(k.base.column("node", "dc_writer"))
for n in ["Vg15","Vop1","N11b","N11a11b","N14a14b","N14a_14b","Vom","Vg25","Vom1"]:
    f.write(f"node {n} {writers.get(n)}\n")
f.close()
