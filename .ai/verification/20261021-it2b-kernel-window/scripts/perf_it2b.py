"""IT-2b 감사 I-perf 재계산 측정(감사 전용, 관찰 래퍼는 반환값 불변).

usage: python -I perf_it2b.py <repo_root> <side> <circuit> <theta_json> <out_json> [--reps 5]
theta_json = {"theta": [[[kind, key], hex], ...], "cells": [...]} (같은 θ 를 base·head 에 넣는다).

- 새 실행 컨텍스트(open_run 새로)에서 `search.kernel.evaluate(sctx, θ, cells)` 한 번 = 평가 1회. 반복 reps 회(매번 새 컨텍스트 -- graph reuse·S3 graft 없음)로
  벽시계 중앙값, 그리고 한 번은 cProfile 로 `dc_columns` 누적 시간.
- `dc_columns` 한 호출 안(구간 = `block_columns._solve_input_window` 와 head `_windows` 실행 중)에서 함수별 호출 수와 같은 인자 재호출 수:
  `_solve`(인자 지문 = (override, theta)), `_measure`(root, values), `_Circuit.input_windows`(values, roots), `_tolerance`(values),
  `_Circuit.tolerance`(devices, values), `_Circuit.region_rows`(values), LUT `op_point`·`vdsat`(memo 뺀 인자), `tol_v_cell`(lut 뺀 인자).
  지문 = 값 tuple(실수는 hex)의 sha256. 같은 지문 재호출은 첫 호출자 줄(파일:줄)과 함께 적는다.
"""
import argparse
import cProfile
import hashlib
import json
import os
import pstats
import statistics
import sys
import time
from pathlib import Path


def fpv(x):
    if isinstance(x, float):
        return x.hex()
    if isinstance(x, dict):
        return tuple(sorted((repr(k), fpv(v)) for k, v in x.items()))
    if isinstance(x, (tuple, list)):
        return tuple(fpv(v) for v in x)
    if hasattr(x, "item") and not isinstance(x, (str, bytes)):
        try:
            return float(x.item()).hex()
        except Exception:  # noqa: BLE001
            return repr(x)
    return repr(x)


def H(x):
    return hashlib.sha256(repr(fpv(x)).encode("utf-8")).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo"); ap.add_argument("side"); ap.add_argument("circuit"); ap.add_argument("theta"); ap.add_argument("out")
    ap.add_argument("--reps", type=int, default=5)
    a_ = ap.parse_args()
    skill = Path(a_.repo) / "skills" / "analog-gmid-design"
    sys.path.insert(0, str(skill))
    sys.path.append("C:/Users/HSLEE/AppData/Roaming/Python/Python314/site-packages")
    import gmid_engine.search  # noqa: F401
    import gmid_engine.sizing.block_columns  # noqa: F401
    bc = sys.modules["gmid_engine.sizing.block_columns"]
    import gmid_engine.lut.point_query  # noqa: F401
    from gmid_engine.core import BoundedLRU, read_pdk_decl
    from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
    from gmid_engine.pipeline import run_stage_a, run_stage_b
    from gmid_engine.search import SearchSettings, build_search_context, open_run
    from gmid_engine.search.kernel import evaluate
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access

    T = {"on": 0, "calls": {}, "n_dc": 0}

    def note(name, key):
        if T["on"] <= 0:
            return
        f = sys._getframe(2)
        site = "%s:%d" % (Path(f.f_code.co_filename).name, f.f_lineno)
        d = T["calls"].setdefault(name, {"n": 0, "fps": {}})
        d["n"] += 1
        e = d["fps"].setdefault(H(key), {"n": 0, "sites": {}})
        e["n"] += 1
        e["sites"][site] = e["sites"].get(site, 0) + 1

    def wrap_fn(mod, attr, name, keyf):
        orig = getattr(mod, attr)

        def w(*args, **kw):
            note(name, keyf(args, kw))
            return orig(*args, **kw)
        setattr(mod, attr, w)
        return orig

    def scope(mod, attr):
        orig = getattr(mod, attr)

        def w(*args, **kw):
            T["on"] += 1
            if attr == "_solve_input_window":
                T["n_dc"] += 1
            try:
                return orig(*args, **kw)
            finally:
                T["on"] -= 1
        setattr(mod, attr, w)

    wrap_fn(bc, "_solve", "_solve", lambda a, k: (a[0].override, a[0].theta))
    if hasattr(bc, "_measure"):
        wrap_fn(bc, "_measure", "_measure", lambda a, k: (a[1], a[2]))
    if hasattr(bc, "_tolerance"):
        wrap_fn(bc, "_tolerance", "_tolerance", lambda a, k: (a[1],))
    C = bc._Circuit
    wrap_fn(C, "input_windows", "Circuit.input_windows", lambda a, k: (a[1], a[2]))
    wrap_fn(C, "tolerance", "Circuit.tolerance", lambda a, k: (a[1], a[2]))
    if hasattr(C, "region_rows"):
        wrap_fn(C, "region_rows", "Circuit.region_rows", lambda a, k: (a[1],))
    if hasattr(C, "saturation_rows"):
        wrap_fn(C, "saturation_rows", "Circuit.saturation_rows", lambda a, k: (a[1],))
    wrap_fn(bc, "vdsat", "lut.vdsat", lambda a, k: (a[1:], k))
    wrap_fn(bc, "tol_v_cell", "tol_v_cell", lambda a, k: (a[1:], k))
    orig_op = sys.modules["gmid_engine.lut.point_query"].op_point
    for name, mod in list(sys.modules.items()):
        if name.startswith("gmid_engine") and getattr(mod, "op_point", None) is orig_op:
            def opw(*args, __o=orig_op, **kw):
                note("lut.op_point", (args[1:], kw))
                return __o(*args, **kw)
            setattr(mod, "op_point", opw)
    scope(bc, "_solve_input_window")
    if hasattr(bc, "_windows"):
        scope(bc, "_windows")

    DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
    CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))
    loc = resolve_lut_location(str(skill / "assets" / "lut_v2_location.json"), os.environ)
    man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
    kinds_map = dict(DEVICE_KINDS)
    mins = {}
    for e in man["slices"]:
        mins[kinds_map[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds_map[e["device"]], float("inf")))
    dm = BoundedLRU(16)
    pdk = read_pdk_decl(str(skill / "assets" / "sky130_pdk_decl.json"), dm)
    q = dict(pdk.quantities)
    lspec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX,
                    noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
    lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, lspec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                       noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
    rule = read_pdk_decl(str(skill / "assets" / "sky130_lut_rule_decl.json"), dm)
    settings = SearchSettings(7200.0, 40, (1e2, 1e5), (("front_budget_s", "it2b perf"),), (1e-13, 1e-10))
    base_dir = skill / "assets" / "library"
    work = Path(a_.out).parent / ("work_perf_" + a_.side + "_" + a_.circuit)
    work.mkdir(parents=True, exist_ok=True)
    donors, counters = open_run()
    a = run_stage_a(base_dir / (a_.circuit + ".topology.json"), base_dir / (a_.circuit + ".sizing_spec.json"), lut,
                    output_dir=work, donors=donors, counters=counters)
    memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
    b = run_stage_b(a, memo, pdk, output_dir=work, diagnostic=True, settings=settings)
    inputs_decl = dc_inputs_from_spec(a.spec)
    tj = json.loads(Path(a_.theta).read_text(encoding="utf-8"))
    theta = {tuple(k): float.fromhex(v) for k, v in tj["theta"]}
    cells = tuple(tj["cells"])

    def fresh():
        d2, c2 = open_run()
        m2 = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)      # LUT memo 도 새로(앞 평가의 승인 예외 memo 적중을 빼고 같은 조건)
        k2 = build_kernel_context(b.s1, inputs_decl, pre_layout_lut_access(m2), donors=d2, counters=c2)
        return build_search_context(k2, a.spec, settings, None, pdk, rule, code_fp=a.code_fp)

    # 1) 계수 실행(새 컨텍스트 하나)
    sc = fresh()
    T["calls"], T["n_dc"] = {}, 0
    r = evaluate(sc, dict(theta), cells)
    calls = {}
    for name, d in sorted(T["calls"].items()):
        rep = [{"fp": fp, "n": e["n"], "sites": e["sites"]} for fp, e in d["fps"].items() if e["n"] > 1]
        calls[name] = {"calls": d["n"], "distinct": len(d["fps"]), "repeat_calls": d["n"] - len(d["fps"]),
                       "repeated": sorted(rep, key=lambda x: -x["n"])[:12]}
    out = {"side": a_.side, "circuit": a_.circuit, "status": r.status, "dc_columns_calls": T["n_dc"], "calls": calls}
    # 2) 시간: 새 컨텍스트마다 evaluate 한 번(컨텍스트 생성은 시간에서 뺀다)
    times = []
    for _ in range(a_.reps):
        sc = fresh()
        t = time.perf_counter()
        evaluate(sc, dict(theta), cells)
        times.append(time.perf_counter() - t)
    out["eval_s"] = times
    out["eval_s_median"] = statistics.median(times)
    # 3) cProfile 한 번
    sc = fresh()
    pr = cProfile.Profile()
    pr.enable()
    evaluate(sc, dict(theta), cells)
    pr.disable()
    st = pstats.Stats(pr)
    prof = {}
    for (fn, line, name), (cc, nc, tt, ct, callers) in st.stats.items():
        if name in ("dc_columns", "_solve_input_window", "_solve", "_measure", "input_windows", "_tolerance", "tolerance", "region_rows",
                    "saturation_rows", "op_point", "vdsat", "tol_v_cell", "_windows", "_refine_ends", "evaluate", "size_and_seal"):
            prof["%s:%d:%s" % (Path(fn).name, line, name)] = {"ncalls": nc, "tottime": tt, "cumtime": ct}
    out["cprofile"] = prof
    Path(a_.out).write_text(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
