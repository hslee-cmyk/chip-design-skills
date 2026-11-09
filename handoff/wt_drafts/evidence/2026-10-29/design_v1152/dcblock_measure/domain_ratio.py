"""측정 전용(design v1.15.2 M-2/gap 보완): FD 호출이 0이었던 회로(current_reuse·sf_pushpull)와 단계 B까지만 간 ngcc의
탐색 변수 구성(θ 전류 열 비율 = 1회 야코비안의 전류 열 수 / 전체 열 수)을 sctx.domain.variables 에서 잰다.
엔진 파일은 고치지 않는다(import만). 결과는 회로마다 domain_ratio.out.jsonl 에 append."""
import sys, os, json, collections, tempfile, shutil, traceback
sys.dont_write_bytecode = True
SKILL_S = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12/skills/analog-gmid-design"
sys.path.insert(0, SKILL_S)
sys.path.append("C:/Users/HSLEE/AppData/Roaming/Python/Python314/site-packages")
from pathlib import Path
from gmid_engine.core import BoundedLRU, read_pdk_decl, run_counters as rc_mod
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.search import SearchSettings, build_search_context, open_run
from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access
SKILL = Path(SKILL_S); LIBRARY = SKILL / "assets" / "library"
OUT = Path(__file__).parent / "domain_ratio.out.jsonl"
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos")); CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))
loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
kinds = dict(DEVICE_KINDS); mins = {}
for e in man["slices"]:
    mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
dm = BoundedLRU(16); pdk = read_pdk_decl(str(SKILL / "assets" / "sky130_pdk_decl.json"), dm); q = dict(pdk.quantities)
spec_l = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX,
                 noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec_l, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                   noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
rule = read_pdk_decl(str(SKILL / "assets" / "sky130_lut_rule_decl.json"), dm)
def settings():
    return SearchSettings(600.0, 40, (1e2, 1e5), (("front_budget_s", "xrunf1b B-T22 fixture"),), (1e-13, 1e-10))
for circuit in sys.argv[1:]:
    rec = {"circuit": circuit}
    out = Path(tempfile.mkdtemp(prefix="dr_out")); root = tempfile.mkdtemp(prefix="dr_root")
    try:
        donors, counters = open_run()
        a = run_stage_a(LIBRARY / (circuit + ".topology.json"), LIBRARY / (circuit + ".sizing_spec.json"), lut, output_dir=out,
                        donors=donors, counters=counters)
        memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
        b = run_stage_b(a, memo, pdk, output_dir=out, diagnostic=True, settings=settings())
        rec["status_ab"] = [a.status, b.status]
        try:
            kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo), donors=a.donors, counters=a.counters)
            sctx = build_search_context(kctx, a.spec, settings(), root, pdk, rule, code_fp=a.code_fp)
            c = collections.Counter(v.component[0] for v in sctx.domain.variables)
            rec["domain_components"] = dict(c); rec["total"] = len(sctx.domain.variables)
            rec["current_cols"] = c.get("current", 0)
        except BaseException as e:
            rec["domain_error"] = "%s: %s" % (type(e).__name__, str(e)[:400])
    except BaseException as e:
        rec["error"] = "%s: %s" % (type(e).__name__, str(e)[:400]); rec["trace"] = traceback.format_exc()[-1500:]
    finally:
        shutil.rmtree(out, ignore_errors=True); shutil.rmtree(root, ignore_errors=True)
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    print(json.dumps(rec, ensure_ascii=False, default=str)[:600])
