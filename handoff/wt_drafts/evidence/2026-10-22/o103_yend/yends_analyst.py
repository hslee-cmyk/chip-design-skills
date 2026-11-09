"""IT-2b dispute 1 측정 -- 탐색 중 θ y 값 분포와 y = 0·1 끝 봉인 결과 (읽기 전용 관찰 래퍼, 반환값 불변).
usage: python -I yends.py <side_root(skills/analog-gmid-design 위)> <side_tag> <circuit> <out_jsonl>
"""
import json
import os
import sys
import time
from pathlib import Path

skill = Path(sys.argv[1]) / "skills" / "analog-gmid-design"
tag, circuit, out = sys.argv[2], sys.argv[3], Path(sys.argv[4])
sys.path.insert(0, str(skill))
sys.path.append("C:/Users/HSLEE/AppData/Roaming/Python/Python314/site-packages")
import gmid_engine.search  # noqa: F401
from gmid_engine.core import BoundedLRU, CANDIDATE_FAILURE_CLASSES, read_pdk_decl
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.search import SearchSettings, build_search_context, find_front, open_run
from gmid_engine.sizing import THETA_Y, build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access

kmod = sys.modules["gmid_engine.search.kernel"]
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))


def emit(rec):
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True, default=repr) + "\n")


def outcome(fn, dc, theta, **kw):
    try:
        ev = fn(dc, theta, **kw)
    except CANDIDATE_FAILURE_CLASSES as exc:
        rec = getattr(exc, "record", None)
        r = getattr(exc, "record", None)
        det = dict(r.detail) if r is not None and getattr(r, "detail", None) else None
        d = {}
        if isinstance(det, dict):
            d = {"item": det.get("item"), "reason": det.get("reason")}
            idet = det.get("item_detail")
            if idet:
                d["slack_v"] = dict(idet).get("slack_v")
        return {"ok": False, "exc": type(exc).__name__, **d}, None
    sealed = ev.sealed is not None
    win = {}
    try:
        for n, w in ev.snapshot.column("node", "dc_window"):
            win[n] = [w.lo, w.hi, getattr(w, "input_status", None)]
    except Exception as e:  # noqa: BLE001 -- 관찰 전용
        win = {"err": repr(e)[:100]}
    return {"ok": True, "sealed": sealed, "report": ev.report.status, "windows": win}, ev


loc = resolve_lut_location(str(skill / "assets" / "lut_v2_location.json"), os.environ)
man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
kinds_map = dict(DEVICE_KINDS)
mins = {}
for e in man["slices"]:
    mins[kinds_map[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds_map[e["device"]], float("inf")))
dm = BoundedLRU(16)
pdk = read_pdk_decl(str(skill / "assets" / "sky130_pdk_decl.json"), dm)
rule = read_pdk_decl(str(skill / "assets" / "sky130_lut_rule_decl.json"), dm)
q = dict(pdk.quantities)
grid = float(man.get("manufacturing_grid_m", 5e-9))
lspec = LutSpec(grid, tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX,
                noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, lspec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                   noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
settings = SearchSettings(7200.0, 40, (1e2, 1e5), (("front_budget_s", "it2b disp"),), (1e-13, 1e-10))
work = out.parent / ("work_" + tag + "_" + circuit)
work.mkdir(parents=True, exist_ok=True)
base_dir = skill / "assets" / "library"
donors, counters = open_run()
t0 = time.perf_counter()
a = run_stage_a(base_dir / (circuit + ".topology.json"), base_dir / (circuit + ".sizing_spec.json"), lut,
                output_dir=work, donors=donors, counters=counters)
head = {"side": tag, "circuit": circuit, "stage_a": a.status}
if a.status != "ok" and a.s1 is None:
    emit({**head, "kind": "stop"})
    sys.exit(0)
memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
b = run_stage_b(a, memo, pdk, output_dir=work, diagnostic=True, settings=settings)
kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo), donors=a.donors, counters=a.counters)
sctx = build_search_context(kctx, a.spec, settings, None, pdk, rule, code_fp=a.code_fp)
INPUTS = {n for n, d in sctx.dc.base.column("node", "port_direction") if d == "input"}
orig = kmod.size_and_seal
calls = []
PROBE_SRC = []


def info(exc):
    r = getattr(exc, "record", None)
    det = dict(r.detail) if r is not None and getattr(r, "detail", None) else None
    d = {"ok": False, "exc": type(exc).__name__}
    if isinstance(det, dict):
        d.update(item=det.get("item"), reason=det.get("reason"))
        idet = det.get("item_detail")
        if idet:
            d["slack_v"] = dict(idet).get("slack_v")
    return d


def wrapped(dc, theta, **kw):
    ys = {k[1]: v for k, v in dict(theta).items() if isinstance(k, tuple) and k[0] == THETA_Y and k[1] in INPUTS}
    try:
        ev = orig(dc, theta, **kw)
    except CANDIDATE_FAILURE_CLASSES as exc:
        calls.append({"y": ys, **info(exc)})
        raise
    calls.append({"y": ys, "ok": True, "sealed": ev.sealed is not None, "report": ev.report.status})
    if ev.sealed is not None and ys and len(PROBE_SRC) < 6:
        PROBE_SRC.append((dc, dict(theta)))
    return ev


kmod.size_and_seal = wrapped
try:
    fr = find_front(sctx, [])
    front_ok = True
except Exception as e:  # noqa: BLE001 -- 관찰 전용
    front_ok = repr(e)[:300]
kmod.size_and_seal = orig
ycount = {"n_calls": len(calls), "n_with_y": sum(1 for c in calls if c["y"]),
          "y_exact_0": sum(1 for c in calls for v in c["y"].values() if v == 0.0),
          "y_exact_1": sum(1 for c in calls for v in c["y"].values() if v == 1.0),
          "y_near_end_1e-6": sum(1 for c in calls for v in c["y"].values() if min(v, 1 - v) <= 1e-6),
          "fail_item7": sum(1 for c in calls if not c.get("ok") and c.get("item") == 7),
          "fail_item7_at_end": sum(1 for c in calls if not c.get("ok") and c.get("item") == 7
                                   and any(min(v, 1 - v) <= 1e-6 for v in c["y"].values()))}
emit({**head, "kind": "search", "front_ok": front_ok, **ycount, "t_s": time.perf_counter() - t0,
      "y_values": sorted({round(v, 9) for c in calls for v in c["y"].values()})[:200]})
for i, (dc, theta) in enumerate(PROBE_SRC):
    ykeys = [k for k in theta if isinstance(k, tuple) and k[0] == THETA_Y and k[1] in INPUTS]
    for yv in (0.0, 1.0):
        th = dict(theta)
        for k in ykeys:
            th[k] = yv
        res, _ev = outcome(orig, dc, th)
        emit({**head, "kind": "probe", "src": i, "y": yv, "ykeys": [k[1] for k in ykeys], **res})
