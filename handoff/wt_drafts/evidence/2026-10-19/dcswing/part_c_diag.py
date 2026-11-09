"""(c) 9 library 회로: 층 0 대표 점(엔진 layer0_start, 기존 탐색 경로) -> 같은 θ 로 size_and_seal 재실행(블록 _Circuit 포획, 런타임 감싸개만)
-> ① ls_swing as-built ② 모든 전도 MOS VGS 등식 제약계 ③ 끝 풀이(출력 넷 고정 DC 재풀이) 출력 창 + 입력 창. 결과 out/c.jsonl (회로마다 append)."""
import math
import sys
import tempfile
import time
import traceback
from pathlib import Path

from common import LIBRARY, append, load_env

import gmid_engine.sizing  # noqa: F401
bc = sys.modules['gmid_engine.sizing.block_columns']
import gmid_engine.metrics  # noqa: F401
lsm = sys.modules['gmid_engine.metrics.ls_swing']
from gmid_engine.lut import LutMemo
from gmid_engine.metrics.metrics_aux import _swing
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.search import SearchSettings, build_search_context
from gmid_engine.search.layer0_center import layer0_start
from gmid_engine.search.tie_expand import expand_ties
from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access, size_and_seal
from gmid_engine.sizing.s2_values import REL_INPUT_DC, REL_WINDOW, INPUT_GROUP_KEY

only = []
lut, pdk, rule = load_env()
SETTINGS = SearchSettings(600.0, 40, (1e2, 1e5), (("front_budget_s", "dcswing measurement (same as test fixtures)"),), (1e-13, 1e-10))
BISECT_TOL = 1e-5     # V, 측정용 이분 끝 분해능

# ---- 런타임 감싸개: dc_columns 가 만든 _Circuit 를 포획(엔진 소스 수정 없음)
_captured = {}
_orig_siw = bc._solve_input_window


def _wrap_siw(c):
    out = _orig_siw(c)
    _captured["c"] = c
    return out


bc._solve_input_window = _wrap_siw


def all_vgs_constraints(devices, rail_nets):
    out = []
    for m in devices:
        if not m.linear:
            hi_net, lo_net = (m.d, m.s) if m.polarity > 0 else (m.s, m.d)
            out.append((hi_net, lo_net, m.sat_v, m.sat_tol_v))
        shift = m.polarity * m.vgs_v       # 모든 전도 MOS: VGS 등식(바이어스 고정 DC 범위)
        out.append((m.g, m.s, shift, m.vgs_tol_v))
        out.append((m.s, m.g, -shift, m.vgs_tol_v))
    return tuple(out)


def swing_summary(s):
    return {"swing_out_v": s.swing_out_v, "icmr_v": s.icmr_v, "icm_margin_v": s.icm_margin_v,
            "out_ranges": [list(r) for r in (s.out_ranges or ())], "window": s.window, "v_icm": s.v_icm,
            "undefined": [u.code for u in getattr(s, "undefined", ())]}


def min_slack(c, values):
    rows = c.saturation_rows(values)
    if rows is None:
        return None, None
    worst = min(rows, key=lambda r: r[3])
    return worst[3], worst


def solve_at(c, setter, x):
    """setter(x) 적용 뒤 풀이. -> (values, min_slack) 또는 (None, None)."""
    undo = setter(x)
    try:
        values, _logs = bc._solve(c)
    except bc._FAILURES:
        undo()
        return None, None
    s, _w = min_slack(c, values)
    undo()
    return values, s


def bisect_end(c, setter, x0, x_lim, probe):
    """x0(가능) 에서 x_lim 쪽으로 '풀림 + 전 소자 포화 여유 ≥ 0' 이 끝나는 x. -> (x_end, probe 값, 원인)."""
    v, s = solve_at(c, setter, x_lim)
    if v is not None and s is not None and s >= 0:
        return x_lim, probe(v), "rail"
    good, bad = x0, x_lim
    vgood = solve_at(c, setter, x0)[0]
    while abs(bad - good) > BISECT_TOL:
        mid = 0.5 * (good + bad)
        v, s = solve_at(c, setter, mid)
        if v is not None and s is not None and s >= 0:
            good, vgood = mid, v
        else:
            bad = mid
    return good, (None if vgood is None else probe(vgood)), "sat"


def pin(c, net, x):
    prev = c.override.get(net, None)
    c.override[net] = (x, x)

    def undo():
        if prev is None:
            c.override.pop(net, None)
        else:
            c.override[net] = prev
    return undo


def set_fixed(c, nets, x):
    prev = {n: c.fixed[n] for n in nets}
    for n in nets:
        c.fixed[n] = x

    def undo():
        c.fixed.update(prev)
    return undo


def refine_output_root(c, root, values, tol):
    """J-E _refine_ends 와 같은 방식(saturation_window 기울기 + 끝 x 고정 재풀이 되풀이)을 출력 W4 뿌리에 적용."""
    win = c.input_windows(values, (root,))
    if win is None:
        return None, "window_unmeasurable"
    saved = dict(c.override)
    refined = bc._refine_ends(c, (root,), win, tol)
    c.override = saved
    return refined[root], win[root]


def run(name):
    rec = {"circuit": name}
    t0 = time.time()
    tmp = Path(tempfile.mkdtemp(prefix="c_" + name))
    a = run_stage_a(LIBRARY / (name + ".topology.json"), LIBRARY / (name + ".sizing_spec.json"), lut, output_dir=tmp)
    rec["stage_a"] = a.status
    if a.status != "ok":
        rec["skip"] = "stage A not ok -> 탐색 컨텍스트 없음(test_s0_layer_9circuits 와 같은 규칙)"
        return rec
    memo = LutMemo(lut, point=200000, curve=200000, root=4096)
    b = run_stage_b(a, memo, pdk, output_dir=tmp, diagnostic=True, settings=SETTINGS)
    rec["stage_b"] = b.status if hasattr(b, "status") else None
    kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo))
    sctx = build_search_context(kctx, a.spec, SETTINGS, None, pdk, rule, code_fp=a.code_fp)
    l0 = layer0_start(sctx)
    rec["layer0"] = {"kernel_calls": sctx.counters["kernel_calls"]}
    rec["layer0_fields"] = {k: repr(getattr(l0, k))[:200] for k in getattr(l0, "__dataclass_fields__", {}) if k not in ("start",)}
    if l0.start is None:
        rec["skip"] = "layer0 시작점 없음"
        return rec
    theta = expand_ties(sctx.domain.ties, dict(l0.start.theta), sctx.domain.negated, sctx.domain.zeros)
    _captured.clear()
    ev = size_and_seal(sctx.dc, theta)
    rec["sealed"] = ev.sealed is not None
    rec["seal_items"] = repr(getattr(ev.report, "items", ev.report))[:600]
    snap = ev.snapshot
    c = _captured.get("c")
    dev_colour = dict(snap.column("device", "dc_colour"))
    canonical = lambda n: (dev_colour.get(n, -1), n)  # noqa: E731
    node_v = {n: v for n, v in snap.column("node", "dc_rail_v") if v is not None}
    node_v.update(dict(snap.column("node", "dc_v")))
    linear = sctx.dc.inputs.linear_devices
    in_dc = sctx.dc.inputs.input_dc_v
    rec["node_v"] = node_v
    rec["input_dc_v"] = in_dc
    rec["dc_window"] = {n: [w.lo, w.hi] for n, w in snap.column("node", "dc_window")} if True else None
    # ① as-built
    s1 = _swing(snap, sctx.dc.lut, linear, canonical, node_v, in_dc)
    rec["asbuilt"] = swing_summary(s1)
    # ② 모든 전도 MOS VGS 등식
    orig = lsm._constraints
    lsm._constraints = all_vgs_constraints
    try:
        s2 = _swing(snap, sctx.dc.lut, linear, canonical, node_v, in_dc)
    finally:
        lsm._constraints = orig
    rec["allvgs"] = swing_summary(s2)
    # ③ 끝 풀이
    if c is None:
        rec["endsolve"] = "no captured circuit"
        return rec
    values, _ = bc._solve(c)
    rec["resolve_matches_snapshot"] = max(abs(values[n] - node_v[n]) for n in node_v if n in values)
    ms, worst = min_slack(c, values)
    rec["op_min_slack"] = [ms, worst]
    ports = dict(snap.column("node", "port_direction"))
    outs = [n for n, d in ports.items() if d == "output"]
    ins = [n for n, d in ports.items() if d == "input"]
    in_roots = c.input_roots()
    in_fixed = [n for n in ins if c.writers[n].relation == REL_INPUT_DC]
    devs = tuple(sorted(c.coord, key=lambda m: (c.device_colour.get(m, 0), m)))
    try:
        tol = c.tolerance(devs, values)
    except Exception as exc:  # noqa: BLE001
        tol = None
        rec["tol_error"] = repr(exc)[:200]
    rec["tol"] = tol
    # 출력 끝 풀이: 입력(뿌리 또는 선언 DC)은 봉인 값에 고정(서보 관례 -- 입력 CM 고정, 출력만 움직임)
    pins_in = [pin(c, r, values[r]) for r in in_roots]
    end = {}
    for o in outs:
        w = c.writers[o]
        e = {"writer": (w.relation, w.element, w.known)}
        if w.relation == REL_WINDOW:
            # (i) J-E 방식(기울기 + 끝 재풀이)
            if tol is not None:
                try:
                    ref, first = refine_output_root(c, o, values, tol)
                    e["je_refined"] = ref
                    e["je_first_slope_window"] = first
                except Exception as exc:  # noqa: BLE001
                    e["je_error"] = repr(exc)[:300]
            # (ii) 이분(같은 DC 모형, 끝 재풀이로 판정)
            lo_end = bisect_end(c, lambda x: pin(c, o, x), values[o], c.lo, lambda v: v[o])
            hi_end = bisect_end(c, lambda x: pin(c, o, x), values[o], c.hi, lambda v: v[o])
            e["bisect"] = [lo_end, hi_end]
        else:
            # KVL 로 정해지는 출력: 사슬 끝 구동자(W4 뿌리 또는 선언 입력 DC)를 훑어 출력 값을 읽는다
            cur, chain = o, []
            while c.writers[cur].known is not None:
                chain.append((cur, c.writers[cur].relation, c.writers[cur].element))
                cur = c.writers[cur].known
            chain.append((cur, c.writers[cur].relation, None))
            e["chain"] = chain
            drv = cur
            rel = c.writers[drv].relation
            if rel == REL_WINDOW:
                setter = lambda x: pin(c, drv, x)  # noqa: E731
            elif rel == REL_INPUT_DC:
                group = in_fixed
                setter = lambda x: set_fixed(c, group, x)  # noqa: E731
            else:
                e["note"] = "구동자 = %s(%s) -- DC 쓰기 계획에서 움직일 자유 변수 없음" % (drv, rel)
                end[o] = e
                continue
            lo_end = bisect_end(c, setter, values[drv], c.lo, lambda v: v[o])
            hi_end = bisect_end(c, setter, values[drv], c.hi, lambda v: v[o])
            e["driver"] = drv
            e["bisect_driver_ends"] = [lo_end, hi_end]
        end[o] = e
    for u in pins_in:
        u()
    rec["end_out"] = end
    rec["diag"] = DIAG(c, values, outs, in_roots, tol)
    # 입력 창(③ 쪽): 출력 W4 뿌리는 봉인 값에 고정(서보 관례), 입력을 훑는다
    out_roots = [o for o in outs if c.writers[o].relation == REL_WINDOW]
    pins_out = [pin(c, o, values[o]) for o in out_roots]
    inend = {}
    if in_roots:
        r = in_roots[0]
        inend["root"] = r
        inend["bisect"] = [bisect_end(c, lambda x: pin(c, r, x), values[r], c.lo, lambda v: v[r]),
                           bisect_end(c, lambda x: pin(c, r, x), values[r], c.hi, lambda v: v[r])]
    elif in_fixed:
        inend["fixed"] = in_fixed
        x0 = c.fixed[in_fixed[0]]
        inend["bisect"] = [bisect_end(c, lambda x: set_fixed(c, in_fixed, x), x0, c.lo, lambda v: v[in_fixed[0]]),
                           bisect_end(c, lambda x: set_fixed(c, in_fixed, x), x0, c.hi, lambda v: v[in_fixed[0]])]
    for u in pins_out:
        u()
    # 입력 창(엔진 관례: 출력 W4 는 y 위치로 따라 움직임) -- 핀 없이 훑기
    if in_roots:
        r = in_roots[0]
        inend["bisect_output_free"] = [bisect_end(c, lambda x: pin(c, r, x), values[r], c.lo, lambda v: v[r]),
                                       bisect_end(c, lambda x: pin(c, r, x), values[r], c.hi, lambda v: v[r])]
    rec["end_in"] = inend
    rec["wall_s"] = time.time() - t0
    return rec



def DIAG(c, values, outs, in_roots, tol):
    out = {}
    pins_in = [pin(c, r, values[r]) for r in in_roots]
    for o in outs:
        if c.writers[o].relation != REL_WINDOW:
            continue
        # J-E 끝 다듬기 궤적: _solve 와 input_windows 를 감싸 기록
        trace = []
        orig_iw = c.input_windows
        def iw(v, roots, _o=orig_iw):
            w = _o(v, roots)
            ms, wst = min_slack(c, v)
            trace.append({"x_pinned": c.override.get(o), "window": None if w is None else w.get(o), "min_slack": ms, "worst": wst})
            return w
        c.input_windows = iw
        saved = dict(c.override)
        win = orig_iw(values, (o,))
        try:
            ref = bc._refine_ends(c, (o,), win, tol)
        finally:
            c.input_windows = orig_iw
            c.override = saved
        checks = {}
        for side in (0, 1):
            x = ref[o][side]
            v, sl = solve_at(c, lambda xx: pin(c, o, xx), x)
            checks[side] = {"x": x, "solved": v is not None, "min_slack": sl,
                            "worst": None if v is None else min_slack(c, v)[1]}
        out[o] = {"trace": trace, "refined": ref[o], "check_at_refined_end": checks}
    for u in pins_in:
        u()
    return out

for name in sys.argv[1:]:
    try:
        rec = run(name)
        rec = {"circuit": name, "diag": rec.get("diag"), "end_out": rec.get("end_out")}
    except Exception as exc:  # noqa: BLE001
        rec = {"circuit": name, "error": repr(exc)[:500], "tb": traceback.format_exc()[-2500:]}
    append("diag.jsonl", rec)
    print(name, "done", flush=True)
