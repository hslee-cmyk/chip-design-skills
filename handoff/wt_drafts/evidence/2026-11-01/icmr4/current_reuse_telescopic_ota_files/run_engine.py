# current_reuse_telescopic_ota 엔진 실행 (nmcnr agent 스크립트 사본, OUT·기본 회로·prefix만 바꿈)(master HEAD, 소스 수정 0, library 경로 그대로, 출력 = TEMP 고유 경로).
# 사슬 = tests/integration/nfr4_run_dump.py main 과 같은 공개 진입점(run_stage_a -> run_stage_b -> build_kernel_context -> build_search_context
# -> find_front). u13_real.real_case 는 쓰지 않는다(형제 파일 미복사 결함). 결과는 케이스마다 Python 바이너리 append.
import os, sys, json, time, math, pathlib, tempfile, dataclasses, traceback
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"; sys.dont_write_bytecode = True
SKILL = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
sys.path.insert(0, str(SKILL))
LIB = SKILL / "assets" / "library"
HERE = pathlib.Path(__file__).parent
OUT = HERE / ("engine_run_eb%s.jsonl" % (sys.argv[3] if len(sys.argv) > 3 else "40"))
CIR = sys.argv[1] if len(sys.argv) > 1 else "current_reuse_telescopic_ota"
FRONT_S = float(sys.argv[2]) if len(sys.argv) > 2 else 300.0
EB = int(sys.argv[3]) if len(sys.argv) > 3 else 40
WORK = pathlib.Path(tempfile.mkdtemp(prefix="icmr4_crt_", dir=os.environ.get("TEMP")))


def app(rec):
    with open(OUT, "ab") as fh:
        fh.write((json.dumps(rec, default=lambda o: repr(o)[:400], ensure_ascii=False) + "\n").encode("utf-8"))


def js(v, d=0):
    if d > 6:
        return repr(v)[:200]
    if v is None or isinstance(v, (str, bool, int)):
        return v
    if isinstance(v, float):
        return v
    try:
        import numpy as np
        if isinstance(v, np.generic):
            return v.item()
        if isinstance(v, np.ndarray):
            return v.tolist()[:50]
    except ImportError:
        pass
    if isinstance(v, dict):
        return {str(k): js(x, d + 1) for k, x in list(v.items())[:200]}
    if isinstance(v, (list, tuple)):
        return [js(x, d + 1) for x in list(v)[:200]]
    if dataclasses.is_dataclass(v) and not isinstance(v, type):
        return {f.name: js(getattr(v, f.name), d + 1) for f in dataclasses.fields(v)}
    return repr(v)[:300]


t0 = time.time()
app({"case": "start", "circuit": CIR, "work": str(WORK), "front_budget_s": FRONT_S, "eval_budget": EB, "t": time.strftime("%Y-%m-%d %H:%M:%S")})
from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.search import SearchSettings, build_search_context, find_front, open_run
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
settings = SearchSettings(FRONT_S, EB, (1e2, 1e5), (("front_budget_s", "icmr4 current_reuse diagnosis run"),), (1e-13, 1e-10))
app({"case": "lut", "manifest": loc.manifest_path, "verify_midpoints": loc.midpoints_path, "pdk_root": str(loc.pdk_root), "s": time.time() - t0})

donors, counters = open_run()
a = run_stage_a(LIB / (CIR + ".topology.json"), LIB / (CIR + ".sizing_spec.json"), lut, output_dir=WORK / "out", donors=donors, counters=counters)
app({"case": "stage_a", "status": a.status, "stop_reasons": js(a.report.get("stop_reasons")), "report_paths": [str(p) for p in a.report_paths]})
memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
b = run_stage_b(a, memo, pdk, output_dir=WORK / "out", diagnostic=True, settings=settings)
app({"case": "stage_b", "status": b.status, "stop_reasons": js(b.report.get("stop_reasons")), "report_paths": [str(p) for p in b.report_paths]})
if (a.status, b.status) != ("ok", "ok"):
    sys.exit(0)
kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo), donors=a.donors, counters=a.counters)
s3 = WORK / "s3"; s3.mkdir(exist_ok=True)
sctx = build_search_context(kctx, a.spec, settings, str(s3), pdk, rule, code_fp=a.code_fp)
app({"case": "search_context", "domain": js(sctx.domain), "ss_constraints": js(sctx.ss_constraints), "judged": js(sctx.judged_constraints)})
try:
    fr = find_front(sctx, [])
except Exception as e:  # noqa: BLE001 -- 측정: 정지 사유 문자열을 그대로 기록
    app({"case": "find_front_exception", "type": type(e).__name__, "msg": str(e)[:4000], "tb": traceback.format_exc()[-4000:]})
    raise
app({"case": "find_front", "front_n": len(fr.front), "pending_n": len(getattr(fr, "pending_front", ()) or ()),
     "unmeasured_n": len(getattr(fr, "unmeasured_front", ()) or ()), "notes": js(fr.notes), "perf": js({k: v for k, v in dict(fr.perf).items() if k not in ("blocks",)})})
# 평가 캐시: 평가마다 status·실패·제약 행
rows = []
for r in sorted(sctx.cache.values(), key=lambda r: r.seq):
    rec = {"seq": r.seq, "status": r.status}
    for nm in ("failure", "fail_reason", "reason", "stop", "warnings", "unmeasured"):
        if hasattr(r, nm):
            rec[nm] = js(getattr(r, nm))
    cons = getattr(r, "constraints", None)
    if cons:
        rec["constraints"] = [{"name": c.name, "c": js(getattr(c, "c", None)), "value": js(getattr(c, "value", None)),
                               "active": js(getattr(c, "active", None))} for c in cons]
    try:
        rec["theta"] = js(r.key.theta if hasattr(r.key, "theta") else r.key)
    except Exception:  # noqa: BLE001
        pass
    rows.append(rec)
    app({"case": "eval", **rec})
app({"case": "done", "s": time.time() - t0, "n_evals": len(rows)})
