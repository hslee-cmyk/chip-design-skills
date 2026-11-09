# 읽기 전용: as-built 엔진의 start_intervals 가 부르는 `_state`(= current_model + macro_solve)를 가로채 호출별 전류·매크로 gm 을 기록한다.
# 엔진 소스 수정 0, 저장소 쓰기 0 (PYTHONDONTWRITEBYTECODE=1, output_dir = 임시). 매크로 gm_req / F 1회차 전류의 출처로만 쓴다(판정 근거 아님).
import sys, os, json, math, tempfile, pathlib
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True
ENG = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
sys.path.insert(0, str(ENG)); sys.path.insert(0, str(ENG / "gmid_engine/tests/search"))
HERE = pathlib.Path(__file__).parent
import u13_real as R
import importlib; SI = importlib.import_module("gmid_engine.search.start_intervals")
from gmid_engine.pipeline import run_stage_a
from gmid_engine.search import open_run

CALLS = []
_orig = SI._state
def _wrap(ctx, gm_id, lengths, refine=True):
    st = _orig(ctx, gm_id, lengths, refine)
    CALLS.append(dict(n=len(CALLS), refine=refine, gm_id=dict(gm_id), L=dict(lengths), currents=dict(st.currents), refs=dict(st.refs),
                      gm=[(k, v) for k, v in st.macro.gm] if st.macro.gm else None, records=[str(r) for r in st.macro.records],
                      failed=st.macro_failed, area=st.area, budget=ctx.area_budget_m2, w_min=ctx.w_min_m))
    return st
SI._state = _wrap

def run(circuit):
    CALLS.clear()
    env = R.real_env()
    donors, counters = open_run()
    out = pathlib.Path(tempfile.mkdtemp(prefix="mj1b_"))
    a = run_stage_a(R.LIBRARY / (circuit + ".topology.json"), R.LIBRARY / (circuit + ".sizing_spec.json"), env.lut, output_dir=out, donors=donors, counters=counters)
    print(circuit, "stageA", a.status, flush=True)
    from gmid_engine.pipeline import run_stage_b
    from gmid_engine.search import SearchSettings
    st = SearchSettings(600.0, 40, (1e2, 1e5), (("front_budget_s", "m_j1b probe"),), (1e-13, 1e-10))
    b = run_stage_b(a, env.memo, env.pdk, output_dir=out, diagnostic=True, settings=st)
    print(circuit, "stageB", b.status, flush=True)
    sctx = None
    if (a.status, b.status) == ("ok", "ok"):
        from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access
        from gmid_engine.search import build_search_context
        kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(env.memo), donors=a.donors, counters=a.counters)
        sctx = build_search_context(kctx, a.spec, st, None, env.pdk, env.rule, code_fp=a.code_fp)
    return a, b, sctx

if __name__ == "__main__":
    c = sys.argv[1]
    a, b, sctx = run(c)
    print(len(CALLS), "calls")
    for k in CALLS[:3]:
        print(json.dumps({x: k[x] for x in ("n", "refine", "failed", "area", "budget", "w_min", "gm")}, default=str)[:600])
