# O-200 Q5 측정 1b 보강 -- 출발점 칸 0 theta 이동을 tol 항 자리별로 가른다(엔진 소스 수정 0, 모듈 속성 가로채기만, 단계 A/B 출력 TEMP).
# 변형: base(그대로) / ih(iv_headroom 의 자기 tol_vdsat·엣지 비용 tol 최솟값 = 0) / dom(iv_domain VDS 탐침의 tol_vdsat = 0) / both.
# 각 변형은 같은 recipe 의 새 실행(새 open_run). 산출: q5_engine_attrib.jsonl (회로·변형마다 append).
import os, sys, json, time, traceback, pathlib, tempfile, dataclasses
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"; sys.dont_write_bytecode = True
ENG = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
sys.path.insert(0, str(ENG))
HERE = pathlib.Path(__file__).parent
TMP = pathlib.Path(r"C:/Users/HSLEE/AppData/Local/Temp/q5_1bd9a6b5")
import importlib
R = importlib.import_module("gmid_engine.tests.search.u13_real")
H = importlib.import_module("gmid_engine.tests.search.u13_hand")
IH = importlib.import_module("gmid_engine.search.iv_headroom")
IDm = importlib.import_module("gmid_engine.search.iv_domain")
DF = importlib.import_module("gmid_engine.lut.derived_fns")
from gmid_engine.search import SearchSettings, open_run
from gmid_engine.pipeline import run_stage_a, run_stage_b
OUT = HERE / "q5_engine_attrib.jsonl"
O_TOL_IH, O_EC_IH, O_TOL_DOM = IH.tol_vdsat, IH.edge_cost, IDm.tol_vdsat


def tol_min(ctx, kind):
    w = ctx.w_keys[kind]; sl = ctx.memo.lut.slice_map[(kind, w)]
    g = DF._tol_vdsat_grid(ctx.memo, kind, w, (len(sl.grids[0]), len(sl.grids[2])))
    pos = g[g > 0]
    return float(pos.min()) if pos.size and (g > 0).all() else 0.0


def setv(v):
    IH.tol_vdsat, IH.edge_cost, IDm.tol_vdsat = O_TOL_IH, O_EC_IH, O_TOL_DOM
    if v in ("ih", "both"):
        IH.tol_vdsat = lambda *a, **k: 0.0
        IH.edge_cost = lambda ctx, k: dataclasses.replace(O_EC_IH(ctx, k), vds_min_v=O_EC_IH(ctx, k).vds_min_v - tol_min(ctx, k))
    if v in ("dom", "both"):
        IDm.tol_vdsat = lambda *a, **k: 0.0


names = sys.argv[1:] or ["common_gate_amplifier", "current_reuse_telescopic_ota", "folded_cascode", "nmcnr_amplifier", "pushpull_follower_buffer",
                         "sf_pushpull_output_opamp", "two_stage_ota", "two_stage_ota_sf"]
env = R.real_env()
for c in names:
    try:
        out = pathlib.Path(tempfile.mkdtemp(prefix="att_" + c[:10] + "_", dir=str(TMP)))
        donors, counters = open_run()
        a = run_stage_a(R.LIBRARY / (c + ".topology.json"), R.LIBRARY / (c + ".sizing_spec.json"), env.lut, output_dir=out, donors=donors, counters=counters)
        settings = SearchSettings(600.0, R.EVAL_BUDGET, R.RBOX, (("front_budget_s", "u13 test fixture"),), R.CBOX)
        b = run_stage_b(a, env.memo, env.pdk, output_dir=out, settings=settings)
        recipe = R._recipe(a, b, json.loads((R.LIBRARY / (c + ".topology.json")).read_text(encoding="utf-8")), settings)
        th = {}
        for v in ("base", "ih", "dom", "both"):
            setv(v)
            try:
                s = H.start_of(R._contexts(recipe, None).sctx)
                th[v] = {f"{k[0]}|{k[1]}": float(x) for k, x in s.theta}
            finally:
                setv("base")
        rec = dict(circuit=c, theta=th)
        for v in ("ih", "dom", "both"):
            d = {k: th[v][k] - th["base"][k] for k in th["base"] if k.startswith("ln_idu") and th[v].get(k) != th["base"][k]}
            rec[f"max_dln_{v}"] = max((abs(x) for x in d.values()), default=0.0)
            rec[f"n_changed_{v}"] = len(d)
    except BaseException as e:
        rec = dict(circuit=c, error=repr(e)[:400], tb=traceback.format_exc()[-800:])
    with open(OUT, "ab") as fh:
        fh.write((json.dumps(rec) + "\n").encode("utf-8"))
    print(c, {k: rec.get(k) for k in ("max_dln_ih", "max_dln_dom", "max_dln_both", "n_changed_ih", "n_changed_dom", "n_changed_both")}, rec.get("error", ""), flush=True)
print("done")
