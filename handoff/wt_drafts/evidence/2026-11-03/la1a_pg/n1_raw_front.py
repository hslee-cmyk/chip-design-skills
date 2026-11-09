# N1: 출발 θ 의 원시 값(값, 목표, 판정 부호)과 외층 결과. usage: n1_raw_front.py <circuit> <run> <eval_budget|None>
# 외층은 as-built(강제 출발), 예산 조건을 함께 기록. 결과 = n1_raw_front.jsonl, 케이스마다 append.
from n0_common import *
CIR, RUN, EB = sys.argv[1], sys.argv[2], (None if sys.argv[3] == "None" else int(sys.argv[3]))
OUT = HERE / "n1_raw_front.jsonl"
use_d1(RUN)
sctx = build_ctx(CIR, EB, 280.0)
tg = targets(sctx)
theta = load_theta(CIR, RUN)
_v, _t, cells = l0._box_centre(sctx, sctx.rungs[0])
res, raw = ev(sctx, theta, cells)
row = {"circuit": CIR, "run": RUN, "eval_budget": EB, "status": res.status, "start": judge(tg, raw), "unmeasured": [str(u)[:70] for u in (res.unmeasured or ())],
       "power_w": res.objectives.power_w if res.objectives else None, "area_m2": res.objectives.area_m2 if res.objectives else None}
log = []
_o = km.ss_constraint_rows


def wrap2(bundle, declared, model_error=()):
    log.append({str(k.metric): v.value for k, v in bundle.entries})
    return _o(bundle, declared, model_error)


km.ss_constraint_rows = wrap2
if res.status in l0.ACCEPTED_STATUSES:
    start = l0.StartPoint("layer0", res.theta, cells, l0.SOURCE_LAYER0)
    lr = l0.Layer0Result(start, 0.0, True, "pg_forced", None, res.status, None, 0, 0, (), (), 0, (), 0, RUN)
    ff.layer0_start = lambda s, origin=(): lr
    n0 = sctx.counters["kernel_calls"]
    try:
        t1 = time.time()
        fr = find_front(sctx, [])
        best = {}
        for raws in log:
            for m, v in raws.items():
                if m not in tg or v is None:
                    continue
                op, t = tg[m]
                z = best.setdefault(m, [0, None])
                ok = v >= t if op == ">=" else v <= t
                z[0] += int(ok)
                z[1] = v if z[1] is None else (max(z[1], v) if op == ">=" else min(z[1], v))
        both = 0
        for raws in log:
            if all((raws.get(m) is not None) and ((raws[m] >= tg[m][1]) if tg[m][0] == ">=" else (raws[m] <= tg[m][1])) for m in tg):
                both += 1
        row["outer"] = {"n_front": len(getattr(fr, "front", ()) or ()), "n_points": len(log), "kernel_calls": sctx.counters["kernel_calls"] - n0, "s": round(time.time() - t1, 1),
                        "E_B": sctx.eval_budget, "all_rows_pass_points": both,
                        "best": {m: {"best": float("%.4g" % v[1]), "target": tg[m][1], "op": tg[m][0], "pass_points": v[0]} for m, v in best.items()}}
    except Exception:
        row["outer_error"] = traceback.format_exc()[-500:]
app(OUT, row)
print("done", CIR, RUN, EB, row["status"], (row.get("outer") or {}).get("n_front"))
