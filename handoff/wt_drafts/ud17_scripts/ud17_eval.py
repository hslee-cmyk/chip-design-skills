"""UD-17 결정 자료 측정: C:/g67/repo(HEAD 7535799 git archive 사본)에서 하네스 회로 θ* 한 점(또는 전체 실행)을 평가.

모드(환경변수 UD17_VS):
  clamp  (기본) -- HEAD 그대로(LUT VS 축 밖은 보간 함수가 끝점으로 클램프)
  extrap        -- VS 축 밖 점만 마지막 구간(0.6~0.8 / 0~0.2) 기울기로 선형 외삽(가상의 '연장 LUT' 근사)
  raise         -- VS 축 밖이면 ValueError('lut_axis_out_of_range')
산출: 소자별 sized 항목, metrics, 노드전압 전파 추적(노드마다 값을 정한 소자·경로), conflicts 경로, 축 밖 조회 수.
사용: python -B ud17_eval.py <circuit> <theta json | --full> <out jsonl> <label>
결과는 케이스마다 out jsonl에 한 줄 append(중간에 죽어도 남는다).
"""
import json
import os
import sys
import time
import traceback

ROOT = os.environ.get("UD17_ROOT", "C:/g67/repo")
circuit, theta_arg, out, label = sys.argv[1:5]
sys.path.insert(0, os.path.join(ROOT, "workspaces"))
os.chdir(os.path.join(ROOT, "workspaces"))
import run_harness as rh  # noqa: E402
import sizing_recipe as sr  # noqa: E402

MODE = os.environ.get("UD17_VS", "clamp")
AXLOG = []

_o1, _o2 = sr._multilinear_interp, sr._multilinear_interp_point_multi


def _vs_state(grids, pt):
    g = grids[3]
    lo, hi = float(g[0]), float(g[-1])
    v = float(pt[3])
    if v > hi + 1e-12:
        return "hi", g[-1], g[-2]
    if v < lo - 1e-12:
        return "lo", g[0], g[1]
    return None, None, None


def w2(grids, arrays, point):
    st, a, b = _vs_state(grids, point)
    if st is None:
        return _o2(grids, arrays, point)
    AXLOG.append(float(point[3]))
    if MODE == "raise":
        raise ValueError(f"lut_axis_out_of_range: vsb={point[3]!r}")
    if MODE == "clamp":
        return _o2(grids, arrays, point)
    pa = list(point); pa[3] = float(a)
    pb = list(point); pb[3] = float(b)
    fa, fb = _o2(grids, arrays, pa), _o2(grids, arrays, pb)
    t = (float(point[3]) - float(a)) / (float(a) - float(b))
    return [x + t * (x - y) for x, y in zip(fa, fb)]


def w1(grids, values, points):
    import numpy as np
    ps = points.tolist() if hasattr(points, "tolist") else points
    if ps and not hasattr(ps[0], "__len__"):
        ps = [ps]
    if MODE == "clamp" and not any(_vs_state(grids, p)[0] for p in ps):
        return _o1(grids, values, points)
    gl = [g.tolist() if hasattr(g, "tolist") else list(g) for g in grids]
    return np.asarray([w2(gl, [values], p)[0] for p in ps])


sr._multilinear_interp, sr._multilinear_interp_point_multi = w1, w2

cfg = rh.SPECS[circuit]
topo = os.path.join(rh.LIBRARY_DIR, cfg["topology_file"])
spec = cfg["spec_fn"]()
spec.setdefault("floorplan_target", {"max_aspect_ratio": rh.FLOORPLAN_MAX_ASPECT_RATIO,
                                     "min_packing_density": rh.FLOORPLAN_MIN_PACKING_DENSITY})
spec.setdefault("max_layout_retry_rounds", rh.MAX_ITERS)
RAILS = {n: spec["vdd"] for n in sr._DEFAULT_RAIL_HI}
RAILS.update({n: 0.0 for n in sr._DEFAULT_RAIL_LO})


def trace_propagate(by_name, sized, vdd):
    """propagate_node_voltages()와 같은 순서·규칙으로 돌며 노드마다 '누가 정했나'를 기록한다(엔진 결과와 대조)."""
    nodes = dict(RAILS)
    setter = {n: None for n in nodes}
    unresolved = set(by_name)
    conflicts = []
    for _ in range(50):
        prog = False
        for name in sorted(unresolved):
            tr = by_name[name]
            e = sized.get(name)
            if e is None or e.get("vds") is None:
                continue
            vds = e["vds"]
            sgn = -1.0 if tr.kind == "pmos" else 1.0
            sk, dk = tr.source in nodes, tr.drain in nodes
            if sk and not dk:
                nodes[tr.drain] = nodes[tr.source] + sgn * vds
                setter[tr.drain] = (name, tr.source)
                unresolved.discard(name); prog = True
            elif dk and not sk:
                nodes[tr.source] = nodes[tr.drain] - sgn * vds
                setter[tr.source] = (name, tr.drain)
                unresolved.discard(name); prog = True
            elif sk and dk:
                exp = nodes[tr.source] + sgn * vds
                d = abs(nodes[tr.drain] - exp)
                if d > 1e-6:
                    conflicts.append({"device": name, "net": tr.drain, "existing": nodes[tr.drain], "via_this": exp, "diff": d,
                                      "this_from": tr.source})
                unresolved.discard(name); prog = True
        if not prog:
            break

    def chain(net):
        out, n = [], net
        while setter.get(n):
            dev, frm = setter[n]
            e = sized[dev]
            out.append(f"{n}={nodes[n]:.4f} <- {dev}({by_name[dev].kind}, vds={e['vds']:.4f}) <- {frm}")
            n = frm
        out.append(f"{n}={nodes[n]:.4f} (rail)")
        return out

    for c in conflicts:
        c["path_existing"] = chain(c["net"])
        c["path_this"] = [f"{c['net']}={c['via_this']:.4f} <- {c['device']}({by_name[c['device']].kind}, vds={sized[c['device']]['vds']:.4f}) <- {c['this_from']}"] + chain(c["this_from"])
    conflicts.sort(key=lambda c: -c["diff"])
    return nodes, setter, conflicts


def fl(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else (v if isinstance(v, str) else None)


def dump_sized(sized):
    o = {}
    for d, e in sorted(sized.items()):
        if isinstance(e, dict):
            o[d] = {k: fl(v) for k, v in sorted(e.items()) if fl(v) is not None}
    return o


def dump_metrics(m):
    r = {}
    if isinstance(m, dict):
        for k, v in sorted(m.items()):
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                r[k] = float(v)
            elif isinstance(v, dict) and isinstance(v.get("value"), (int, float)):
                r[k] = float(v["value"])
    return r


rec = {"label": label, "circuit": circuit, "mode": MODE}
t0 = time.time()
try:
    if theta_arg == "--full":
        res = sr.optimize_full_circuit_budget(
            topo, spec, grid_points_per_theta=cfg["grid_points_per_theta"],
            search_method=cfg.get("search_method", "grid"), slsqp_kwargs=cfg.get("slsqp_kwargs"))
        rec["kind"] = "full"
        rec["theta_star"] = {k: float(v) for k, v in res["theta_star"].items()}
        rec["metrics"] = dump_metrics(res["metrics"])
        sized = res.get("sizing") if isinstance(res.get("sizing"), dict) else {}
        rec["sized"] = dump_sized(sized)
    else:
        theta = json.loads(theta_arg)
        ev = sr._build_theta_evaluator(topo, spec)
        ctx, mres = ev["evaluate"](theta)
        rec["kind"] = "theta"
        rec["theta"] = theta
        rec["sized"] = dump_sized(ctx.sized)
        rec["metrics"] = dump_metrics(mres)
        by_name = ev["by_name"]
        nodes, setter, conflicts = trace_propagate(by_name, ctx.sized, spec["vdd"])
        rep = sr.propagate_node_voltages(by_name, ctx.sized, spec["vdd"])
        same = (set(rep.nodes) == set(nodes) and all(abs(rep.nodes[k] - nodes[k]) < 1e-12 for k in nodes)
                and len(rep.conflicts) == len(conflicts))
        rec["trace_matches_engine"] = same
        rec["nodes"] = nodes
        rec["setter"] = {k: v for k, v in setter.items() if v}
        rec["conflicts"] = conflicts
        rec["devices"] = {n: {"kind": t.kind, "source": t.source, "drain": t.drain, "gate": t.gate} for n, t in sorted(by_name.items())}
    rec["outcome"] = "ok"
except BaseException as e:
    rec["outcome"] = "exception"
    rec["exc_class"] = type(e).__name__
    rec["exc_msg"] = str(e)[:800]
    rec["tb_tail"] = traceback.format_exc().splitlines()[-6:]
rec["axis_out_count"] = len(AXLOG)
rec["axis_out_values"] = sorted(set(round(v, 4) for v in AXLOG))[:60]
rec["sec"] = round(time.time() - t0, 1)
with open(out, "a", encoding="utf-8") as f:
    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
print(label, rec["outcome"], rec.get("exc_class"), rec["sec"], "axis_out", rec["axis_out_count"], "trace_ok", rec.get("trace_matches_engine"))
