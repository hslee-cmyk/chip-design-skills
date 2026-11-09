# LA-1a 착수 조건 (3) 실현 가능성 실측 -- 칸 0(as-built 출발 사다리)이 정하지 않는 θ 성분을 library 13회로에서 센다.
# 엔진 소스 수정 0, 엔진 값은 재작성 범위 인용(원칙 8). ngcc dc_role = O-216 선언 내용을 TEMP 사본으로만. 회로마다 append.
import os, sys, json, pathlib, tempfile, traceback
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"; sys.dont_write_bytecode = True
SKILL = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/skills/analog-gmid-design")
sys.path.insert(0, str(SKILL))
LIB = SKILL / "assets" / "library"
OUT = pathlib.Path(__file__).parent / "uncovered.jsonl"
WORK = pathlib.Path(tempfile.mkdtemp(prefix="la1a_theta_", dir=os.environ.get("TEMP")))
from gmid_engine.authoring import load_topology
from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.graph import structure_rule_fp
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.search import SearchSettings, build_search_context, open_run
from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access

DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos")); CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))
loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
man = json.loads(pathlib.Path(loc.manifest_path).read_text(encoding="utf-8"))
kinds = dict(DEVICE_KINDS); mins = {}
for e in man["slices"]:
    mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
dm = BoundedLRU(16)
pdk = read_pdk_decl(str(SKILL / "assets" / "sky130_pdk_decl.json"), dm)
q = dict(pdk.quantities)
lspec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX,
                noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, lspec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                   noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
rule = read_pdk_decl(str(SKILL / "assets" / "sky130_lut_rule_decl.json"), dm)
settings = SearchSettings(300.0, 40, (1e2, 1e5), (("front_budget_s", "la1a theta measurement"),), (1e-13, 1e-10))


def app(row):
    with open(OUT, "ab") as fh:
        fh.write((json.dumps(row, ensure_ascii=False, default=repr) + "\n").encode("utf-8"))


for c in sorted(p.name[:-len(".sizing_spec.json")] for p in LIB.glob("*.sizing_spec.json")):
    row = {"circuit": c}
    try:
        donors, counters = open_run()
        kw = {}
        if c == "ngcc_3stage_ff":
            topo = load_topology(str(LIB / (c + ".topology.json")))
            st = {"schema_version": "1", "topology_hash": topo.connectivity_fp, "rule_hash": structure_rule_fp(), "facts": [
                {"concept": "dc_role", "subject": m, "value": "signal", "status": "ratified",
                 "evidence": {"rule": "TEMP O-216 content", "nets": ["V1", "gnd"]}, "approval_id": "TEMP-la1a-design"} for m in ("M8", "M14")]}
            sp = WORK / (c + ".structure.json"); sp.write_text(json.dumps(st), encoding="utf-8")
            kw = {"structure_path": sp}
        a = run_stage_a(LIB / (c + ".topology.json"), LIB / (c + ".sizing_spec.json"), lut, output_dir=WORK / c, donors=donors, counters=counters, **kw)
        row["stage_a"] = a.status
        if a.status != "ok":
            row["stop"] = repr(a.report.get("stop_reasons"))[:300]
            app(row); continue
        memo = LutMemo(lut, point=1 << 14, curve=1 << 12, root=1 << 14)
        b = run_stage_b(a, memo, pdk, output_dir=WORK / c, diagnostic=True, settings=settings)
        row["stage_b"] = b.status
        if b.status != "ok":
            row["stage_a"] = "b:" + str(b.status)
            app(row); continue
        kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo), donors=a.donors, counters=a.counters)
        s3 = WORK / c / "s3"; s3.mkdir(parents=True, exist_ok=True)
        sctx = build_search_context(kctx, a.spec, settings, str(s3), pdk, rule, code_fp=a.code_fp)
        variables = [v.component for v in sctx.domain.variables]
        row["n_theta_vars"] = len(variables)
        row["r_vars"] = [str(v[1]) for v in variables if str(v[0]) == "resistance"]
        row["c_vars"] = [str(v[1]) for v in variables if str(v[0]) == "capacitance"]
        rungs = sctx.rungs
        row["n_rungs"] = None if rungs is None else len(rungs)
        given = set() if not rungs else {comp for comp, _v in rungs[0].theta}
        miss = {}
        for comp in variables:
            if comp not in given:
                miss.setdefault(str(comp[0]), []).append(str(comp[1]))
        row["rungs"] = [{"missing_by_kind": miss}]
    except Exception:
        row["error"] = traceback.format_exc()[-1000:]
    app(row)
print("done")
