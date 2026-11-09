"""측정 공용: 엔진 import만(소스 수정 없음). LUT 적재·회로 목록·결과 append."""
import json
import os
import sys
from pathlib import Path

SKILL = Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design")
sys.path.insert(0, str(SKILL))
OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)
LIBRARY = SKILL / "assets" / "library"
HELDOUT = SKILL / "assets" / "heldout"
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))


def circuits():
    out = []
    for d in (LIBRARY, HELDOUT):
        for p in sorted(d.glob("*.topology.json")):
            if not p.name.startswith("_"):
                out.append((d.name, p.name.removesuffix(".topology.json"), d))
    return out


def load_env():
    from gmid_engine.core import BoundedLRU, read_pdk_decl
    from gmid_engine.lut import LutSpec, load_lut_set, resolve_lut_location
    loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
    man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
    kinds = dict(DEVICE_KINDS)
    mins = {}
    for e in man["slices"]:
        mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
    dm = BoundedLRU(16)
    pdk = read_pdk_decl(str(SKILL / "assets" / "sky130_pdk_decl.json"), dm)
    q = dict(pdk.quantities)
    spec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX,
                   noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
    lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                       noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
    rule = read_pdk_decl(str(SKILL / "assets" / "sky130_lut_rule_decl.json"), dm)
    return lut, pdk, rule


def append(name, obj):
    with open(OUT / name, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, default=repr) + "\n")
