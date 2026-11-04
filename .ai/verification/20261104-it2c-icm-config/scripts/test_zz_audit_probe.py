"""IT-2c 판정 탐침(복제본 전용, 커밋 대상 아님). 판정자 작성. PROBE_OUT 에 케이스마다 append. base·head 양쪽에서 돈다."""
import cProfile
import gzip
import json
import os
import pstats
import shutil
import tempfile
import time
from pathlib import Path

import numpy
import pytest

from gmid_engine.core import fp_of
from gmid_engine.lut import LutMemo
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.search import build_search_context, find_front, open_run
from gmid_engine.sizing import METRICS_KEY, build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access
import gmid_engine.search.kernel as kernel_mod
import importlib
import sys
import gmid_engine.graph  # noqa: F401
sym = importlib.import_module("gmid_engine.graph.s1_symmetry") if False else sys.modules["gmid_engine.graph.s1_symmetry"]
cf = sys.modules["gmid_engine.graph.canonical_form"]

from test_g10_no_recompute_9circuits import CIRCUITS, LIBRARY, _settings, env  # noqa: F401

OUT = os.environ["PROBE_OUT"]
FLOW = os.environ.get("PROBE_FLOW", "folded_cascode").split(",")


def rec(case, **kw):
    with open(OUT, "ab") as f:
        f.write((json.dumps({"case": case, **kw}, ensure_ascii=False, default=str) + "\n").encode("utf-8"))


def _cert(pos, neighbours, base_rank):
    order = sorted(pos, key=lambda v: pos[v])
    edges = sorted((pos[v], label, pos[u]) for v in pos for label, u in neighbours[v])
    return tuple(base_rank[v] for v in order), tuple(edges)


@pytest.mark.parametrize("circuit", CIRCUITS)
def test_canon(env, circuit, tmp_path, monkeypatch):  # noqa: F811
    """p 포트 정준화: h 자기동형 직접 확인, cert 같음, S1 색·뷰 기록."""
    seen = {}
    real_graph = cf._graph
    real_pf = getattr(sym, "_p_port_first", None)

    def spy_graph(source, em, nm):
        out = real_graph(source, em, nm)
        seen["marked"], seen["neighbours"] = out
        return out

    monkeypatch.setattr(cf, "_graph", spy_graph)
    if real_pf is not None:
        def spy_pf(position, generators, p_port):
            new = real_pf(position, generators, p_port)
            seen["pf"] = (dict(position), dict(new), p_port)
            return new
        monkeypatch.setattr(sym, "_p_port_first", spy_pf)
    donors, counters = open_run()
    try:
        a = run_stage_a(LIBRARY / (circuit + ".topology.json"), LIBRARY / (circuit + ".sizing_spec.json"), env.lut, output_dir=tmp_path / "o",
                        donors=donors, counters=counters)
    except Exception as exc:                   # 정지 회로는 기록만
        rec("canon", circuit=circuit, exc=type(exc).__name__, detail=str(exc)[:200])
        return
    row = {"circuit": circuit, "status": a.status}
    snap = getattr(getattr(a, "s1", None), "snapshot", None)
    row["has_s1"] = snap is not None
    if snap is not None:
        row["node_colour"] = dict(snap.column("node", "dc_colour"))
        row["device_colour"] = dict(snap.column("device", "dc_colour"))
        row["orbits_fp"] = fp_of(snap.value("graph", "s1", "orbits"))
        row["port_role"] = {k: v for k, v in snap.column("node", "port_role") if v}
        row["port_role_writer"] = None
    if "pf" in seen:
        old, new, p = seen["pf"]
        marked, nb = seen["marked"], seen["neighbours"]
        ranks = {s: i for i, s in enumerate(sorted(set(marked.values()), key=repr))}
        base_rank = {v: ranks[marked[v]] for v in marked}
        row["pf_moved"] = sum(1 for v in old if old[v] != new[v])
        row["pf_cert_same"] = _cert(old, nb, base_rank) == _cert(new, nb, base_rank)
        row["pf_pos_bijection"] = sorted(new.values()) == sorted(old.values())
        row["pf_p"] = list(p)
        row["pf_p_pos"] = (old[p], new[p])
    else:
        row["pf_called"] = False
    views = None
    if snap is not None and dict(snap.column("graph", "views")).get("s1v") is not None:
        views = snap.value("graph", "s1v", "views")
    if views is not None:
        row["views"] = [{"excite": v.excite, "sense": v.sense, "kind": v.kind, "default_port": getattr(v, "default_port", None)} for v in views]
    rec("canon", **row)


def _independent(nodal, inputs, excite, sense_signs, span):
    """피검 함수 없이 G 에서 직접: 분할 해, vx·ve, servo 감도, KCL 잔차."""
    n = len(nodal.nodes)
    idx = {net: i for i, net in enumerate(nodal.nodes)}
    fixed = sorted(nodal.fixed)
    unk = [i for i in range(n) if i not in nodal.fixed]
    # 전도 없는 행 제외(그 집합이면 갈래 5 로 먼저 끝난다)
    G = numpy.array(nodal.g)
    def solve(drive):
        v = numpy.zeros(n)
        for i, a in drive.items():
            v[i] = a
        x = numpy.linalg.solve(G[numpy.ix_(unk, unk)], -G[numpy.ix_(unk, fixed)] @ v[fixed])
        v[unk] = x
        return v
    vx = solve({idx[p]: 1.0 for p in inputs})
    c = numpy.zeros(n)
    for net, s in sense_signs:
        c[idx[net]] += s
    if len(inputs) == 1:
        s = vx
        a_e = None
    else:
        ve = solve({idx[p]: span * w for p, w in excite})
        a_e = float(c @ ve) / span
        s = vx - ve / span * (float(c @ vx) / a_e)
    return {net: float(s[i]) for net, i in idx.items()}, a_e, float(numpy.max(numpy.abs(G[unk, :] @ s))) if unk else 0.0, float(c @ s)


def _physics(snap, memo_lut, linear, fh_case):
    """봉인점 하나의 물리 대조(모두 스냅샷 필드에서, 감도는 독립 풀이)."""
    cfg = dict(snap.column("node", "dc_window_cfg"))
    ic = snap.value("graph", METRICS_KEY, "icm_config")
    nodal = snap.value("graph", METRICS_KEY, "ss_nodal")
    out = {"config": ic.config, "pivot_a_e": ic.pivot_a_e, "pivot_res": ic.pivot_resolution, "vcm": (ic.vcm0, ic.vcm_lo, ic.vcm_hi),
           "undef": [(u.code, u.detail) for u in ic.undefined], "cfg": {k: (w.lo, w.hi, w.input_status, w.tol_v) for k, w in cfg.items()}}
    if ic.config is None:
        return out
    from gmid_engine.graph import S1V_KEY
    from gmid_engine.sizing import Circuit
    views = [v for v in snap.value("graph", S1V_KEY, "views") if v.kind == "transfer" and v.default_port]
    roles = dict(snap.column("node", "port_role"))
    v = views[0]
    sense = ((v.sense[0], 1.0),) if len(v.sense) == 1 else tuple((n, 1.0 if "output_p" in roles[n] else -1.0) for n in v.sense)
    dirs = dict(snap.column("node", "port_direction"))
    inputs = tuple(sorted(k for k, d in dirs.items() if d == "input"))
    rails = [x for _n, x in snap.column("node", "dc_rail_v") if x is not None]
    span = max(rails) - min(rails)
    s, a_e, kcl, cs = _independent(nodal, inputs, v.excite, sense, span)
    out.update(independent_a_e=a_e, kcl_residual=kcl, c_dot_s=cs, n_nodes=len(nodal.nodes))
    volts = {**dict(snap.column("node", "dc_rail_v")), **dict(snap.column("node", "dc_v"))}
    circuit = Circuit(snap, lut=memo_lut, linear=linear)
    rows = circuit.region_rows(volts)
    out["rows"] = None if rows is None else len(rows)
    if rows is not None:
        lo, hi, skipped, missing = -float("inf"), float("inf"), 0, 0
        binding = {}
        for a, b, sign, slack, kind in rows:
            missing += (a not in s) + (b not in s)
            rate = sign * (s[a] - s[b])
            if abs(rate) <= 2.220446049250313e-16:
                skipped += 1
                continue
            r = slack / abs(rate)
            if rate > 0:
                if -r > lo:
                    lo, binding["lo"] = -r, (a, b, kind, slack)
            elif r < hi:
                hi, binding["hi"] = r, (a, b, kind, slack)
        out.update(rows_lo=lo, rows_hi=hi, rows_skipped=skipped, rows_missing_nets=missing, binding=binding, min_slack=min(r[3] for r in rows))
        for p in inputs:
            if s[p] != 0:
                aa, bb = (min(rails) - volts[p]) / s[p], (max(rails) - volts[p]) / s[p]
                lo, hi = max(lo, min(aa, bb)), min(hi, max(aa, bb))
        out["independent_ends"] = {p: sorted((volts[p] + s[p] * lo, volts[p] + s[p] * hi)) for p in inputs} if lo <= hi else None
        out["input_slope"] = {p: s[p] for p in inputs}
    return out


NAMES = ("ss_nodal_system", "icm_config_window", "ss_circuit_field", "region_rows", "kvl_sensitivity", "_transfer_resolution", "conductance_matrix", "nodal_factor",
         "ss_evaluate", "size_and_seal", "find_front", "metrics_ss", "metrics_aux", "metrics_dc", "ss_dev", "vdsat", "write_snapshot")


@pytest.mark.parametrize("circuit", FLOW)
def test_flow(env, circuit, tmp_path, monkeypatch):  # noqa: F811
    donors, counters = open_run()
    out = tmp_path / "o"
    a = run_stage_a(LIBRARY / (circuit + ".topology.json"), LIBRARY / (circuit + ".sizing_spec.json"), env.lut, output_dir=out, donors=donors, counters=counters)
    memo = LutMemo(env.lut, point=1 << 16, curve=1 << 14, root=1 << 16)
    b = run_stage_b(a, memo, env.pdk, output_dir=out, diagnostic=True, settings=_settings())
    rec("flow_status", circuit=circuit, a=a.status, b=b.status)
    if (a.status, b.status) != ("ok", "ok"):
        return
    root = tempfile.mkdtemp(prefix="pb", dir=os.environ.get("TEMP") or None)
    real = kernel_mod.ss_evaluate
    kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo), donors=a.donors, counters=a.counters)
    done = {"n": 0, "phys": 0}

    def spy(sealed, ctx, theta, *args, **kw):
        ev = real(sealed, ctx, theta, *args, **kw)
        done["n"] += 1
        th = sorted((list(k), float(v).hex()) for k, v in (theta.values if hasattr(theta, "values") else theta))
        fps = {}
        for f in ("metrics_ss", "metrics_aux", "metrics_dc"):
            got = ev.snapshot.field("graph", METRICS_KEY, f)
            fps[f] = None if got is None else got.value_fp
        rec("eval", circuit=circuit, theta_fp=fp_of(tuple(map(tuple, [(tuple(k), v) for k, v in th]))), fps=fps,
            dc_v=fp_of(tuple(sorted(ev.snapshot.column("node", "dc_v")))), ss_dev=fp_of(tuple(sorted(ev.snapshot.column("device", "ss_dev"), key=lambda kv: kv[0]))),
            inputs={k: dict(ev.snapshot.column("node", "dc_v")).get(k) for k, d in ev.snapshot.column("node", "port_direction") if d == "input"})
        if hasattr(ev.snapshot, "column") and done["phys"] < 6 and os.environ.get("PROBE_HEAD") == "1":
            done["phys"] += 1
            t0 = time.perf_counter()
            rec("phys", circuit=circuit, **_physics(ev.snapshot, ctx.lut, frozenset(ctx.inputs.linear_devices), None))
        return ev

    monkeypatch.setattr(kernel_mod, "ss_evaluate", spy)
    sizes = []
    try:
        sctx = build_search_context(kctx, a.spec, _settings(), root, env.pdk, env.rule, code_fp=a.code_fp)
        pr = cProfile.Profile()
        t = time.perf_counter()
        pr.enable()
        fr = find_front(sctx, [])
        pr.disable()
        wall = time.perf_counter() - t
        st = pstats.Stats(pr)
        prof = {}
        for key, v in st.stats.items():
            if key[2] in NAMES and "site-packages" not in key[0] and "gmid_engine" in key[0]:
                prof.setdefault(key[2], [0, 0.0])
                prof[key[2]][0] += v[0]
                prof[key[2]][1] += v[3]
        perf = dict(fr.perf)
        rows = [dict(r) for r in perf["blocks"]]
        rec("cost", circuit=circuit, wall_s=wall, prof=prof, evals=done["n"],
            blocks={r["block"]: {k: r[k] for k in ("calls", "reuses", "grafts", "replays", "computes", "recomputes_same_input")} for r in rows
                    if r["block"] in ("ss_circuit", "ss_nodal", "icm_config", "metrics_ss", "metrics_aux", "metrics_dc", "ss_dev")})
        snaps = sorted(Path(root, "snapshots").glob("*.gz")) if Path(root, "snapshots").is_dir() else []
        found = list(Path(root).rglob("*.json.gz"))
        for p in found[:3]:
            raw = gzip.open(p, "rb").read()
            d = json.loads(raw)
            lens = {}
            for r in d["records"]:
                if r["kind"] == "graph":
                    for name, fv in r["fields"].items():
                        if name in ("ss_nodal", "ss_circuit", "icm_config"):
                            lens[name] = len(json.dumps(fv["value"]))
            sizes.append({"gz": p.stat().st_size, "raw": len(raw), "fields": lens,
                          "icm_config": next((fv["value"] for r in d["records"] if r["kind"] == "graph" for n, fv in r["fields"].items() if n == "icm_config"), None)})
        rec("archive", circuit=circuit, n_snapshots=len(found), sizes=sizes)
    finally:
        shutil.rmtree(root, ignore_errors=True)
