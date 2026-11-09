"""B2 측정 드라이버: <root> 사본의 하네스 folded_cascode spec으로
 (a) --full: optimize_full_circuit_budget 전체 실행(하네스와 같은 인자) 결과 요약
 (b) --theta <json>: _build_theta_evaluator(...)["evaluate"](theta) 한 점 평가
결과를 JSON 한 줄로 --out 에 append. 환경변수 P4_SIM/P4_AXIS는 b2_patch.py 참고.
사용: python -B b2_eval.py <root> <label> --out <file> [--full | --theta <json>]
"""
import json
import os
import sys
import time
import traceback

root, label = sys.argv[1], sys.argv[2]
args = sys.argv[3:]
out = args[args.index("--out") + 1]
sys.path.insert(0, os.path.join(root, "workspaces"))
os.chdir(os.path.join(root, "workspaces"))
import run_harness as rh  # noqa: E402
import sizing_recipe as sr  # noqa: E402

CIRCUIT = os.environ.get("P4_CIRCUIT", "folded_cascode")
cfg = rh.SPECS[CIRCUIT]
topo = os.path.join(rh.LIBRARY_DIR, cfg["topology_file"])
spec = cfg["spec_fn"]()
spec.setdefault("floorplan_target", {"max_aspect_ratio": rh.FLOORPLAN_MAX_ASPECT_RATIO,
                                     "min_packing_density": rh.FLOORPLAN_MIN_PACKING_DENSITY})
spec.setdefault("max_layout_retry_rounds", rh.MAX_ITERS)


def num(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return float(v).hex()
    return None


def dump_sized(sized):
    o = {}
    for d, e in sorted(sized.items()):
        if not isinstance(e, dict):
            continue
        o[d] = {k: num(v) for k, v in sorted(e.items()) if num(v) is not None}
    return o


def dump_metrics(m):
    if isinstance(m, dict):
        r = {}
        for k, v in sorted(m.items()):
            if num(v) is not None:
                r[k] = num(v)
            elif isinstance(v, dict) and "value" in v and num(v["value"]) is not None:
                r[k] = num(v["value"])
        return r
    return repr(m)[:300]


rec = {"label": label, "circuit": CIRCUIT, "P4_SIM": os.environ.get("P4_SIM", ""), "P4_AXIS": os.environ.get("P4_AXIS", "")}
t0 = time.time()
try:
    if "--full" in args:
        res = sr.optimize_full_circuit_budget(
            topo, spec, grid_points_per_theta=cfg["grid_points_per_theta"],
            search_method=cfg.get("search_method", "grid"), slsqp_kwargs=cfg.get("slsqp_kwargs"))
        rec["kind"] = "full"
        rec["theta_star"] = {k: float(v) for k, v in res["theta_star"].items()}
        rec["metrics"] = dump_metrics(res["metrics"])
        rec["sized"] = dump_sized(res["sizing"]) if isinstance(res.get("sizing"), dict) else None
        rec["audit_ok"] = res.get("audit_ok")
    else:
        theta = json.loads(args[args.index("--theta") + 1])
        ev = sr._build_theta_evaluator(topo, spec)
        ctx, mres = ev["evaluate"](theta)
        rec["kind"] = "theta"
        rec["sized"] = dump_sized(ctx.sized)
        rec["metrics"] = dump_metrics(mres)
    rec["outcome"] = "ok"
except BaseException as e:  # 측정: 예외 클래스와 MRO를 기록한다
    rec["outcome"] = "exception"
    rec["exc_class"] = type(e).__name__
    rec["exc_mro"] = [c.__name__ for c in type(e).__mro__]
    rec["exc_is_AssertionError"] = isinstance(e, AssertionError)
    rec["exc_msg"] = str(e)[:600]
    rec["tb_tail"] = traceback.format_exc().splitlines()[-8:]
rec["axis_out_count"] = len(getattr(sr, "_P4_AXIS_LOG", []))
rec["axis_out_sample"] = sorted(set(round(v, 4) for v in getattr(sr, "_P4_AXIS_LOG", [])))[:10]
rec["sec"] = round(time.time() - t0, 1)
with open(out, "a", encoding="utf-8") as f:
    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
print(label, rec["outcome"], rec.get("exc_class"), rec["sec"], "axis_out", rec["axis_out_count"])
