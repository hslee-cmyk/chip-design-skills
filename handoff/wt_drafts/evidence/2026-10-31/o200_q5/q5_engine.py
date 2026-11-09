# O-200 Q5 측정 1(엔진 헤드룸 행)·2(꼬리 셀 도달)·3(봉인 7 띠) -- master HEAD 엔진, library 경로 그대로(inplace: 형제 파일 결함 회피,
# stageA_regression/report.md), 단계 A/B -> build_search_context(u13_real._recipe/_contexts 와 같은 설정, 예산 40) -> find_front.
# 읽기·실행만: 엔진 소스 수정 0(모듈 속성 가로채기만), 저장소 쓰기 0(단계 A/B output_dir = TEMP 고유 경로, PYTHONDONTWRITEBYTECODE).
#  (1b) start_intervals 가 부르는 headroom_bounds 를 감싸, 소자 VDS 엣지(헤드룸 행)마다 예산(tol 있음)·예산(tol 없음: 엣지 비용의 tol_vdsat 최솟값을 뺀 경로)
#       ·자기 tol_vdsat 를 기록 -> Σtol = (예산_없음 − 예산_있음) + 자기 tol, gm/ID 하한(있음/없음). 그리고 같은 recipe 로 새 실행(새 open_run)을 하나 더 만들되
#       iv_headroom·iv_domain 의 tol_vdsat 항을 0 으로(엣지 비용에서도 뺌) 두어 출발 구간 칸 0(theta)·행을 tol 있음과 비교한다.
#  (3)  find_front(tol 있음 컨텍스트) 동안 seal_saturation._row·judge 를 감싸 평가마다 행(소자·kind·w_key·L·VGS·VDS·VSB·VDsat·tol)을 기록.
# 산출(케이스마다 Python 바이너리 append): q5_engine_rows.jsonl(봉인 7 행), q5_engine_headroom.jsonl(헤드룸 행), q5_engine_circuits.jsonl(회로 요약).
import os, sys, json, time, traceback, pathlib, tempfile, dataclasses, math, bisect
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"; sys.dont_write_bytecode = True
ENG = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
sys.path.insert(0, str(ENG))
HERE = pathlib.Path(__file__).parent
TMP = pathlib.Path(r"C:/Users/HSLEE/AppData/Local/Temp/q5_1bd9a6b5")
import importlib
import numpy as np
R = importlib.import_module("gmid_engine.tests.search.u13_real")
H = importlib.import_module("gmid_engine.tests.search.u13_hand")
SS = importlib.import_module("gmid_engine.sizing.seal_saturation")
SI = importlib.import_module("gmid_engine.search.start_intervals")
IH = importlib.import_module("gmid_engine.search.iv_headroom")
IDm = importlib.import_module("gmid_engine.search.iv_domain")
HC = importlib.import_module("gmid_engine.search._helpers_curves")
DF = importlib.import_module("gmid_engine.lut.derived_fns")
from gmid_engine.search import find_front, SearchSettings, open_run
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.lut import tol_vdsat_table

F_ROWS = HERE / "q5_engine_rows.jsonl"; F_HEAD = HERE / "q5_engine_headroom.jsonl"; F_CIRC = HERE / "q5_engine_circuits.jsonl"


def app(path, rec):
    with open(path, "ab") as fh:
        fh.write((json.dumps(rec, default=float) + "\n").encode("utf-8"))


ST = dict(circuit=None, mode=None, ev=0, pending=[], head_call=0, nt_budgets={})

# ---------------- 봉인 7 기록
_orig_row, _orig_judge = SS._row, SS.judge


def _row(lut, device, op):
    r, absent = _orig_row(lut, device, op)
    if ST["mode"] == "front":
        ST["pending"].append((device, op, r, lut))
    return r, absent


def _cells(lut, kind, w_key, L, vds):
    sl = lut.memo.lut.slice_map[(kind, w_key)]
    A = [float(a) for a in sl.grids[0]]; Vg = [float(a) for a in sl.grids[2]]
    j = min(range(len(A)), key=lambda i: abs(A[i] - L))
    rows = [j] if abs(A[j] - L) <= 1e-12 * max(1.0, L) * 1e6 or abs(A[j] - L) < 1e-15 else sorted({max(bisect.bisect_left(A, L) - 1, 0), min(bisect.bisect_left(A, L), len(A) - 1)})
    k = min(bisect.bisect_right(Vg, vds) - 1, len(Vg) - 2)
    return [A[i] for i in rows], [Vg[k], Vg[k + 1]]


def _judge(kind, rows, *a, **kw):
    if kind == SS.SEAL_SATURATION and ST["mode"] == "front":
        ST["ev"] += 1
        for device, op, r, lut in ST["pending"]:
            _dev, mag, tol = r[0], r[1], r[2]
            rec = dict(circuit=ST["circuit"], ev=ST["ev"], device=device)
            for f in ("kind", "w_key", "L", "W", "vgs", "vds", "vsb", "current"):
                rec[f] = getattr(op, f, None)
            if mag is not None:
                sat = (mag - 2.0 * tol + op.vds) if tol is not None else (mag + op.vds)
                rec.update(vdsat=sat, tol=tol, slack0=op.vds - sat)
                rec["band"] = (tol is not None) and (0.0 <= op.vds - sat < tol)
                rec["sat_violate"] = op.vds - sat < 0.0
            try:
                rec["cell_L"], rec["cell_vds"] = _cells(lut, op.kind, op.w_key, float(op.L), float(op.vds))
            except Exception as e:
                rec["cell_err"] = repr(e)[:120]
            app(F_ROWS, rec)
        ST["pending"] = []
    return _orig_judge(kind, rows, *a, **kw)


SS._row, SS.judge = _row, _judge

# ---------------- 헤드룸 행 기록 / tol 끄기
_orig_hb = SI.headroom_bounds
_orig_tol_ih, _orig_ec_ih, _orig_tol_dom = IH.tol_vdsat, IH.edge_cost, IDm.tol_vdsat


def _tol_min(ctx, kind):
    """엔진 엣지 비용과 같은 규칙으로 쓰인 tol_vdsat 최솟값(양수 칸 최솟값, 0 칸이 있으면 0) -- 엣지 비용에서 빼기 위한 측정용 재현."""
    w_key = ctx.w_keys[kind]
    sl = ctx.memo.lut.slice_map[(kind, w_key)]
    shp = (len(sl.grids[0]), len(sl.grids[2]))
    g = DF._tol_vdsat_grid(ctx.memo, kind, w_key, shp)
    pos = g[g > 0]
    return float(pos.min()) if pos.size and (g > 0).all() else 0.0


def _edges_nt(ctx):
    out = {}
    for k in sorted({d.kind for d in ctx.devices}):
        ec = _orig_ec_ih(ctx, k)
        out[k] = dataclasses.replace(ec, vds_min_v=ec.vds_min_v - _tol_min(ctx, k))
    return out


def _hb(ctx, lengths, budgets=None):
    res = _orig_hb(ctx, lengths, budgets)
    if ST["mode"] != "on" or ctx.rail_v == {} or not ctx.devices:
        return res
    ST["head_call"] += 1
    try:
        if budgets is None:
            bnt = IH._budgets(ctx, _edges_nt(ctx))
            ST["nt_budgets"] = bnt
        else:
            bnt = ST["nt_budgets"]
        for d in ctx.devices:
            b_on = res.budgets.get((d.name, IH.EDGE_VDS)); b_nt = bnt.get((d.name, IH.EDGE_VDS))
            if b_on is None:
                continue
            L = lengths[d.name]
            bundle = HC.curve_bundle(ctx, d.kind, L)
            if bundle is None:
                continue
            curve = bundle[HC.QUANTITY_VDSAT]
            own = _orig_tol_ih(ctx, d.kind, L, curve.vds)
            f_on = HC.hull(curve.gm_id, curve.values, b_on - own, below=True)
            f_nt = None if b_nt is None else HC.hull(curve.gm_id, curve.values, b_nt, below=True)
            gmin = float(min(curve.gm_id))
            app(F_HEAD, dict(circuit=ST["circuit"], call=ST["head_call"], device=d.name, kind=d.kind, w_key=ctx.w_keys[d.kind], L=L, curve_vds=curve.vds,
                             budget_on=b_on, budget_nt=b_nt, own_tol=own, path_tol=(None if b_nt is None else b_nt - b_on),
                             sum_tol=(None if b_nt is None else b_nt - b_on + own), tol_min=_tol_min(ctx, d.kind),
                             g_lo_on=None if f_on is None else f_on[0], g_lo_nt=None if f_nt is None else f_nt[0], curve_gmid_min=gmin,
                             vdsat_curve_min=float(min(curve.values)), vdsat_curve_max=float(max(curve.values))))
    except Exception as e:
        app(F_HEAD, dict(circuit=ST["circuit"], call=ST["head_call"], error=repr(e)[:300], tb=traceback.format_exc()[-600:]))
    return res


SI.headroom_bounds = _hb


def _notol(on):
    if on:
        IH.tol_vdsat = lambda *a, **k: 0.0
        IDm.tol_vdsat = lambda *a, **k: 0.0
        def ec(ctx, k):
            e = _orig_ec_ih(ctx, k)
            return dataclasses.replace(e, vds_min_v=e.vds_min_v - _tol_min(ctx, k))
        IH.edge_cost = ec
    else:
        IH.tol_vdsat, IH.edge_cost, IDm.tol_vdsat = _orig_tol_ih, _orig_ec_ih, _orig_tol_dom


def start_dump(sctx):
    s = H.start_of(sctx)
    if s is None:
        return None
    out = dict(theta=[[str(k[0]), str(k[1]), float(v)] for k, v in s.theta], rows={r.device: repr(r)[:600] for r in s.rows}, n_conflicts=len(s.conflicts or ()),
               conflicts=repr(s.conflicts)[:1500], inactive=repr(s.inactive)[:600])
    return out


names = sys.argv[1:] or sorted(p.name.replace(".topology.json", "") for p in R.LIBRARY.glob("*.topology.json") if not p.name.startswith("_"))
env = R.real_env()
for c in names:
    ST.update(circuit=c, mode=None, ev=0, pending=[], head_call=0, nt_budgets={})
    t0 = time.time(); rec = dict(circuit=c)
    try:
        out = pathlib.Path(tempfile.mkdtemp(prefix="eng_" + c[:10] + "_", dir=str(TMP)))
        donors, counters = open_run()
        a = run_stage_a(R.LIBRARY / (c + ".topology.json"), R.LIBRARY / (c + ".sizing_spec.json"), env.lut, output_dir=out, donors=donors, counters=counters)
        rec["stageA"] = a.status
        settings = SearchSettings(600.0, R.EVAL_BUDGET, R.RBOX, (("front_budget_s", "u13 test fixture"),), R.CBOX)
        if a.status == "ok":
            b = run_stage_b(a, env.memo, env.pdk, output_dir=out, settings=settings)
            rec["stageB"] = b.status
            if b.status == "ok":
                topo = json.loads((R.LIBRARY / (c + ".topology.json")).read_text(encoding="utf-8"))
                recipe = R._recipe(a, b, topo, settings)
                ST["mode"] = "on"
                case = R._contexts(recipe, dict(donors=a.donors, counters=a.counters))
                s_on = start_dump(case.sctx)
                ST["mode"] = "off"
                case_c = R._contexts(recipe, None)          # 대조: tol 있음 새 실행(결정성 확인)
                s_c = start_dump(case_c.sctx)
                rec["start_ctrl"] = s_c
                rec["ctrl_theta_equal"] = None if (s_on is None or s_c is None) else (s_on["theta"] == s_c["theta"])
                _notol(True)
                try:
                    case_nt = R._contexts(recipe, None)
                    s_nt = start_dump(case_nt.sctx)
                finally:
                    _notol(False)
                rec["start_on"], rec["start_nt"] = s_on, s_nt
                rec["start_theta_equal"] = None if (s_on is None or s_nt is None) else (s_on["theta"] == s_nt["theta"])
                rec["start_rows_differ"] = None if (s_on is None or s_nt is None) else sorted(k for k in s_on["rows"] if s_on["rows"][k] != s_nt["rows"].get(k))
                ST["mode"] = "front"
                front = find_front(case.sctx, ())
                rec.update(stage="front_done", n_front=len(getattr(front, "front", ()) or ()), n_pending=len(getattr(front, "pending_front", ()) or ()))
    except BaseException as e:
        rec.update(error=repr(e)[:500], tb=traceback.format_exc()[-1200:])
    ST["mode"] = None
    rec.update(seal7_evals=ST["ev"], head_calls=ST["head_call"], seconds=round(time.time() - t0, 1))
    app(F_CIRC, rec)
    print(c, rec.get("stageA"), rec.get("stageB"), rec.get("stage"), "seal7", ST["ev"], "theta_eq", rec.get("start_theta_equal"), rec.get("error", "")[:200], rec["seconds"], flush=True)
print("done")
