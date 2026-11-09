"""검증2: m4 (i) Rʳ 정적 계수의 판정 논리 점검 -- 순환 SCC의 모든 노드 writer(관계 종류 포함)를 그대로 출력.
작성자 m4_measure.py는 SCC 안에 VGS writer가 하나라도 있으면 그 writer 소자만 허용오차 소자로 본다.
여기서는 VGS writer가 없는 SCC 노드의 writer 관계·소자, 그 소자의 dc_coord.role을 함께 낸다(엔진 무수정, import·읽기만).
사용: python m4_writers.py <회로 ...>  -> m4_writers.out.jsonl append
"""
import sys, os, json, tempfile, shutil, traceback
sys.dont_write_bytecode = True
SKILL_S = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12/skills/analog-gmid-design"
sys.path.insert(0, SKILL_S)
sys.path.append("C:/Users/HSLEE/AppData/Roaming/Python/Python314/site-packages")
from pathlib import Path
from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.search import SearchSettings, build_search_context, open_run
from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access
from gmid_engine.sizing.s2_values import COORD_WRITER, REL_VGS_GATE, REL_VGS_SOURCE

SKILL = Path(SKILL_S); LIBRARY = SKILL / "assets" / "library"
OUT = Path(__file__).parent / "m4_writers.out.jsonl"
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos")); CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))
loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
kinds_map = dict(DEVICE_KINDS); mins = {}
for e in man["slices"]:
    mins[kinds_map[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds_map[e["device"]], float("inf")))
GRID = float(man.get("manufacturing_grid_m", 5e-9))
dm = BoundedLRU(16); pdk = read_pdk_decl(str(SKILL / "assets" / "sky130_pdk_decl.json"), dm); q = dict(pdk.quantities)
spec_l = LutSpec(GRID, tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX,
                 noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec_l, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                   noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
rule = read_pdk_decl(str(SKILL / "assets" / "sky130_lut_rule_decl.json"), dm)


def settings():
    return SearchSettings(600.0, 40, (1e2, 1e5), (("front_budget_s", "xrunf1b B-T22 fixture"),), (1e-13, 1e-10))


for circuit in sys.argv[1:]:
    rec = {"circuit": circuit}
    out = Path(tempfile.mkdtemp(prefix="v2o")); root = tempfile.mkdtemp(prefix="v2r")
    try:
        donors, counters = open_run()
        a = run_stage_a(LIBRARY / (circuit + ".topology.json"), LIBRARY / (circuit + ".sizing_spec.json"), lut, output_dir=out,
                        donors=donors, counters=counters)
        memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
        b = run_stage_b(a, memo, pdk, output_dir=out, diagnostic=True, settings=settings())
        kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo), donors=a.donors, counters=a.counters)
        sctx = build_search_context(kctx, a.spec, settings(), root, pdk, rule, code_fp=a.code_fp)
        base = sctx.dc.base
        coords = dict(base.column("device", "dc_coord"))
        writers = dict(base.column("node", "dc_writer"))
        order = [v for _k, v in base.column("graph", "dc_scc_order")][0]
        rows = []
        for entry in order:
            if not entry.cyclic:
                continue
            nodes = []
            for n in entry.nodes:
                w = writers.get(n)
                el = getattr(w, "element", None) if w is not None else None
                nodes.append(dict(node=n, relation=str(getattr(w, "relation", None)), element=el,
                                  element_role=(str(coords[el].role) if el in coords else None),
                                  is_vgs=(getattr(w, "relation", None) in (REL_VGS_GATE, REL_VGS_SOURCE))))
            devs = sorted(entry.devices)
            rows.append(dict(nodes=nodes, scc_devices=devs,
                             dependent_scc_devices=sorted(d for d in devs if d in coords and coords[d].role != COORD_WRITER)))
        rec["cyclic_scc"] = rows
    except BaseException as exc:
        rec["error"] = "%s: %s" % (type(exc).__name__, str(exc)[:500]); rec["trace"] = traceback.format_exc()[-1500:]
    finally:
        shutil.rmtree(out, ignore_errors=True); shutil.rmtree(root, ignore_errors=True)
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    print(circuit, "error" if "error" in rec else len(rec["cyclic_scc"]))
