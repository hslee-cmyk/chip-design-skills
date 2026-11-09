"""IT-2c SPICE 틀 판정 -- 엔진 쪽 (읽기 전용, 엔진 import 만).

_scratch_it2c/scripts/meas_it2c.py 와 같은 봉인점(layer0 시작점 봉인)을 다시 만들고, 같은 계산으로
  (가) θ 고정 follower 창·감도 (saturation_window + _Circuit.writer_grad)
  (나) KCL follower 창·감도 (conductance_matrix + nodal_factor, u = V_out Schur 1칸)
을 낸다. 더해 SPICE 대조에 필요한 봉인점 값(노드 dc_v, 소자 W·L·전류·VDsat·tol, 바이어스·전류원 값)을 out/<회로>.engine.json 에 쓴다.
"""
import json
import os
import sys
import tempfile
import traceback
from pathlib import Path

SKILL = Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_scratch_it2c\src\skills\analog-gmid-design")
sys.path.insert(0, str(SKILL))
OUTDIR = Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_scratch_it2c_spice\out")

import numpy  # noqa: E402

from gmid_engine.core import BoundedLRU, read_pdk_decl  # noqa: E402
from gmid_engine.core.projection import Projection  # noqa: E402
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location  # noqa: E402
from gmid_engine.metrics import ss_evaluate  # noqa: E402
from gmid_engine.metrics._helpers_nodal import conductance_matrix, nodal_factor, nodal_solve  # noqa: E402
from gmid_engine.metrics.metrics_aux import _ss_of  # noqa: E402
from gmid_engine.pipeline import run_stage_a, run_stage_b  # noqa: E402
from gmid_engine.search import SearchSettings, build_search_context, open_run  # noqa: E402
from gmid_engine.search.layer0_center import layer0_start  # noqa: E402
from gmid_engine.search.tie_expand import expand_ties  # noqa: E402
from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access, size_and_seal  # noqa: E402
from gmid_engine.sizing.block_columns import MOS_TERMINAL_NAMES, _Circuit, dc_columns, w_key_of  # noqa: E402
from gmid_engine.sizing.input_window import saturation_window  # noqa: E402
from gmid_engine.sizing.kernel_run import _COLUMN_KINDS  # noqa: E402
from gmid_engine.sizing.s2_values import KERNEL_KEY  # noqa: E402
from gmid_engine.sizing.scc_order import FIXED_RELATIONS  # noqa: E402
from gmid_engine.sizing.theta_check import check_theta  # noqa: E402
from gmid_engine.lut.vdsat_query import vdsat  # noqa: E402
from gmid_engine.lut.vdsat_tolerance import tol_vdsat_table  # noqa: E402

LIBRARY = SKILL / "assets" / "library"
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))
SETTINGS = SearchSettings(600.0, 40, (1e2, 1e5), (("front_budget_s", "it2c"),), (1e-13, 1e-10))


def load_env():
    loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
    man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
    kinds = dict(DEVICE_KINDS)
    mins = {}
    for e in man["slices"]:
        mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
    dm = BoundedLRU(16)
    pdk = read_pdk_decl(str(SKILL / "assets" / "sky130_pdk_decl.json"), dm)
    q = dict(pdk.quantities)
    spec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX,
                   noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
    lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                       noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
    rule = read_pdk_decl(str(SKILL / "assets" / "sky130_lut_rule_decl.json"), dm)
    return lut, pdk, rule, loc


LUT, PDK, RULE, LOC = load_env()


def jsonable(v, depth=0):
    if depth > 6:
        return repr(v)[:200]
    if isinstance(v, (str, int, bool)) or v is None:
        return v
    if isinstance(v, float):
        return v
    if isinstance(v, (numpy.floating,)):
        return float(v)
    if isinstance(v, dict):
        return {str(k): jsonable(x, depth + 1) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [jsonable(x, depth + 1) for x in v]
    if hasattr(v, "_asdict"):
        return {k: jsonable(x, depth + 1) for k, x in v._asdict().items()}
    if hasattr(v, "__dataclass_fields__"):
        return {k: jsonable(getattr(v, k), depth + 1) for k in v.__dataclass_fields__}
    return repr(v)[:300]


def run(name):
    rec = {"circuit": name, "lut_location": jsonable(LOC)}
    tmp = Path(tempfile.mkdtemp(prefix="it2cs_" + name))
    a_d, a_c = open_run()
    a = run_stage_a(LIBRARY / (name + ".topology.json"), LIBRARY / (name + ".sizing_spec.json"), LUT, output_dir=tmp,
                    donors=a_d, counters=a_c)
    memo = LutMemo(LUT, point=200000, curve=200000, root=4096)
    b = run_stage_b(a, memo, PDK, output_dir=tmp, diagnostic=True, settings=SETTINGS)
    kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo), donors=a_d, counters=a_c)
    sctx = build_search_context(kctx, a.spec, SETTINGS, None, PDK, RULE, code_fp=a.code_fp)
    l0 = layer0_start(sctx)
    if l0.start is None:
        rec["skip"] = "layer0_start None"
        return rec
    theta = expand_ties(sctx.domain.ties, dict(l0.start.theta), sctx.domain.negated, sctx.domain.zeros)
    rec["theta"] = jsonable(theta)
    ev = size_and_seal(sctx.dc, theta)
    if ev.sealed is None:
        rec["seal_report"] = repr(getattr(ev.report, "items", ev.report))[:800]
        return rec
    ssev = ss_evaluate(ev.sealed, sctx.dc, theta, sctx.ss_constraints, (), junction=sctx.junction, area_decl=sctx.area_decl,
                       noise_decl=sctx.noise_decl, mismatch=sctx.mismatch, structure=sctx.structure, driving=sctx.driving)
    snap = ssev.lineage.snapshot

    # ---- 봉인점 값 (SPICE 넷리스트 입력)
    cols = {}
    for fld in ("w", "l", "nf", "kind", "pins", "bulk", "dc_op", "dc_current", "dc_drop_current", "dc_L", "dc_coord", "element_class",
                "passive_value", "dc_tol_v", "dc_gm", "ss_dev"):
        try:
            cols[fld] = {str(k): jsonable(v) for k, v in snap.column("device", fld)}
        except Exception as exc:  # noqa: BLE001 -- 측정 스크립트: 없는 열은 기록만
            cols[fld] = "ERR " + repr(exc)[:200]
    rec["device_cols"] = cols
    ncols = {}
    for fld in ("dc_v", "dc_rail_v", "port_direction", "dc_output_structure", "dc_writer"):
        try:
            ncols[fld] = {str(k): jsonable(v) for k, v in snap.column("node", fld)}
        except Exception as exc:  # noqa: BLE001
            ncols[fld] = "ERR " + repr(exc)[:200]
    rec["node_cols"] = ncols
    rec["dc_inputs"] = jsonable(sctx.dc.inputs)

    # ---- 봉인점 컨덕턴스 계 (graph.ss_nodal 설계 조립)
    ss, _ssv, _o = _ss_of(snap)
    size = len(ss.nodes)
    index = {n: i for i, n in enumerate(ss.nodes)}
    fixed = {index[n] for n in tuple(ss.ground_nets) + tuple(ss.input_nets)}
    g = conductance_matrix(ss.circuit, size)
    fac = nodal_factor(g, fixed)
    rails = {n: v for n, v in snap.column("node", "dc_rail_v") if v is not None}
    outs = [n for n, d in snap.column("node", "port_direction") if d == "output"]
    rec.update(ss_ground=list(ss.ground_nets), ss_inputs=list(ss.input_nets), outputs=outs, rails=rails)

    # ---- θ 고정 연립
    base = sctx.dc.base
    items = check_theta(base.value("graph", KERNEL_KEY, "theta_schema"), theta)
    items = items.values if hasattr(items, "values") and not isinstance(items, dict) else items
    column_items = tuple(((kind, key), v) for (kind, key), v in items if kind in _COLUMN_KINDS)
    extras = (column_items, base.value("graph", KERNEL_KEY, "fixed_values"), base.value("graph", KERNEL_KEY, "resistor_values"),
              sctx.dc.lut) + ((sctx.dc.inputs.linear_devices,) if sctx.dc.inputs.linear_devices else ())
    rec["fixed_values"] = jsonable(base.value("graph", KERNEL_KEY, "fixed_values"))
    rec["resistor_values"] = jsonable(base.value("graph", KERNEL_KEY, "resistor_values"))
    proj = Projection.from_snapshot(snap, dc_columns.reads, extras)
    c = _Circuit(proj)
    values = dict(rails)
    values.update(dict(snap.column("node", "dc_v")))
    rec["values"] = {k: float(v) for k, v in values.items() if v is not None}
    rec["linear_devices"] = sorted(c.linear)
    rec["writers"] = {n: [w.relation, getattr(w, "element", None), getattr(w, "known", None)] for n, w in c.writers.items()}
    rows = c.region_rows(values)
    if rows is None:
        rec["rows"] = None
        return rec
    order = sorted(c.coord, key=lambda x: (c.device_colour.get(x, 0), x))
    rowrec = []
    for m, row in zip(order, rows):
        vgs, vds, vsb = c.mos_point(m, values)
        w_key = w_key_of(c.lut, c.kinds[m])
        sat = vdsat(c.lut.memo, c.kinds[m], w_key, c.L[m], vgs, vds, vsb)
        tol = tol_vdsat_table(c.lut.memo, c.kinds[m], w_key).at(c.L[m], vds)
        rowrec.append({"device": m, "kind": c.kinds[m], "pins": c.pins[m], "bulk": c.bulk[m], "L": c.L[m], "w_key": w_key,
                       "a": row[0], "b": row[1], "sign": row[2], "slack": row[3], "row_kind": row[4],
                       "vgs": vgs, "vds": vds, "vsb": vsb, "vdsat": sat, "tol": tol})
    rec["rows"] = rowrec
    if len(outs) != 1 or len(ss.input_nets) != 2:
        rec["compare"] = "skip"
        return rec
    out = outs[0]
    span = max(rails.values()) - min(rails.values())
    T = {}
    for p in ss.input_nets:
        volt, _rel = nodal_solve(fac, size, {index[p]: span})
        T[p] = float(volt[index[out]]) / span
    neg = [p for p in ss.input_nets if T[p] < 0]
    pos = [p for p in ss.input_nets if T[p] > 0]
    rec["T"] = T
    inv, non = neg[0], pos[0]
    rec["inv"], rec["non"] = inv, non
    head, rel = c.writer_head(out)
    rec["out_writer_head"] = [head, rel]

    plain = [non, inv]
    roots = tuple(plain) + ((head, out),)
    moving = frozenset(plain)
    unknown = tuple(n for n, w in c.canonical_writers() if w.relation not in FIXED_RELATIONS or n in moving)
    th = saturation_window(unknown, roots, values, c.writer_grad, rows)
    # θ 고정 (반전 입력 고정판: 앞 분석의 inv_fixed -- 창은 같았다)
    plain_a = [non]
    roots_a = tuple(plain_a) + ((head, out),)
    unknown_a = tuple(n for n, w in c.canonical_writers() if w.relation not in FIXED_RELATIONS or n in frozenset(plain_a))
    th_a = saturation_window(unknown_a, roots_a, values, c.writer_grad, rows)
    rec["theta_follower"] = None if th is None else {"dlo": th[0], "dhi": th[1], "slope": th[2]}
    rec["theta_follower_inv_fixed"] = None if th_a is None else {"dlo": th_a[0], "dhi": th_a[1], "slope": th_a[2]}

    vx, _r1 = nodal_solve(fac, size, {index[non]: 1.0})
    vu, _r2 = nodal_solve(fac, size, {index[inv]: 1.0})
    u = vx[index[out]] / (1.0 - vu[index[out]])
    s_kcl = {n: float(vx[i] + u * vu[i]) for n, i in index.items()}
    kw = saturation_window((), (), {}, None, rows, slope=s_kcl)
    rec["kcl_follower"] = {"dlo": kw[0], "dhi": kw[1], "slope": s_kcl, "u": float(u),
                           "vx": {n: float(vx[i]) for n, i in index.items()}, "vu": {n: float(vu[i]) for n, i in index.items()}}
    # θ 고정 둘째 우변(계획 N3.8 '우변 둘': 동작점 출력 차 x0 − V_out0) -- W4 뿌리 행 = V_out 1, 비반전 입력은 움직이지 않음
    from gmid_engine.sizing.input_window import _sensitivities
    s2 = _sensitivities(unknown_a, ((head, out),), values, c.writer_grad)
    try:
        g_non = c.writer_grad(non, values)
        rec["writer_grad_non"] = jsonable(g_non)
    except Exception as exc:  # noqa: BLE001
        rec["writer_grad_non"] = "ERR " + repr(exc)[:300]
    rec["theta_s2"] = s2
    return rec


if __name__ == "__main__":
    for nm in sys.argv[1:]:
        try:
            r = run(nm)
        except Exception:  # noqa: BLE001 -- 측정 스크립트: 실패를 기록하고 다음 회로로
            r = {"circuit": nm, "error": traceback.format_exc()[-3000:]}
        (OUTDIR / (nm + ".engine.json")).write_text(json.dumps(r, ensure_ascii=False, indent=1, default=repr), encoding="utf-8")
        print(nm, "done", "error" in r, flush=True)
