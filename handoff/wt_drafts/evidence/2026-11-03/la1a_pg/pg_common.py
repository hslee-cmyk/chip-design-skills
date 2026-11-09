# LA-1a 계획 공백 PG-1~5 독립 실측 공용 도구. 엔진 소스 수정 0, 저장소 쓰기 0(바이트코드 없음, 작업 경로 = TEMP).
# 엔진 인용 용도 = 재작성 범위·엔진 밖 사실 측정 도구(원칙 8). 값은 근거가 아니라 측정 입력.
# ngcc dc_role = O-216 선언 내용을 TEMP 사본으로만(파일 작성은 card data 커밋 몫).
import os, sys, json, pathlib, tempfile, traceback, math, time
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"; sys.dont_write_bytecode = True
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
ENGINE_ROOT = os.environ.get("PG_ENGINE_ROOT", r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/skills/analog-gmid-design")
SKILL = pathlib.Path(ENGINE_ROOT)
sys.path.insert(0, str(SKILL))
LIB = SKILL / "assets" / "library"
HERE = pathlib.Path(__file__).parent
TEMP_ROOT = pathlib.Path(r"C:/Users/HSLEE/AppData/Local/Temp/la1a_pg_a")
if not TEMP_ROOT.is_dir():
    raise SystemExit("temp root missing")

import gmid_engine.search  # noqa: F401
from gmid_engine.authoring import load_topology
from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.graph import structure_rule_fp
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.search import SearchSettings, build_search_context, open_run
from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access

si = sys.modules["gmid_engine.search.start_intervals"]
l0 = sys.modules["gmid_engine.search.layer0_center"]

DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos")); CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))
ALL = ["common_gate_amplifier", "current_reuse_telescopic_ota", "folded_cascode", "ngcc_3stage_ff", "nmcnr_amplifier",
       "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota", "two_stage_ota_sf"]
TARGET4 = ["nmcnr_amplifier", "ngcc_3stage_ff", "current_reuse_telescopic_ota", "sf_pushpull_output_opamp"]


def load_env():
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
    return lut, pdk, rule


def build(c, lut, pdk, rule, budget_s=300.0, extra_structure=None):
    """(a, b, sctx) -- 단계 A·B·탐색 컨텍스트. 정지면 sctx None."""
    work = pathlib.Path(tempfile.mkdtemp(prefix="pg_%s_" % c[:6], dir=str(TEMP_ROOT)))
    donors, counters = open_run()
    kw = {}
    if c == "ngcc_3stage_ff":
        topo = load_topology(str(LIB / (c + ".topology.json")))
        st = {"schema_version": "1", "topology_hash": topo.connectivity_fp, "rule_hash": structure_rule_fp(), "facts": [
            {"concept": "dc_role", "subject": m, "value": "signal", "status": "ratified",
             "evidence": {"rule": "TEMP O-216 content", "nets": ["V1", "gnd"]}, "approval_id": "TEMP-la1a-pg"} for m in ("M8", "M14")]}
        sp = work / (c + ".structure.json"); sp.write_text(json.dumps(st), encoding="utf-8")
        kw = {"structure_path": sp}
    a = run_stage_a(LIB / (c + ".topology.json"), LIB / (c + ".sizing_spec.json"), lut, output_dir=work / c, donors=donors, counters=counters, **kw)
    if a.status != "ok":
        return a, None, None
    memo = LutMemo(lut, point=1 << 14, curve=1 << 12, root=1 << 14)
    settings = SearchSettings(budget_s, 40, (1e2, 1e5), (("front_budget_s", "la1a pg measurement"),), (1e-13, 1e-10))
    b = run_stage_b(a, memo, pdk, output_dir=work / c, diagnostic=True, settings=settings)
    if b.status != "ok":
        return a, b, None
    kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo), donors=a.donors, counters=a.counters)
    s3 = work / c / "s3"; s3.mkdir(parents=True, exist_ok=True)
    sctx = build_search_context(kctx, a.spec, settings, str(s3), pdk, rule, code_fp=a.code_fp)
    return a, b, sctx


def app(path, row):
    with open(path, "ab") as fh:
        fh.write((json.dumps(row, ensure_ascii=False, default=lambda o: repr(o)[:400]) + "\n").encode("utf-8"))
