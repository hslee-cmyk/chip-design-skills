# q8 실측 (미룬 결정 (8) -- LA-1a 범위 1 목표 이득 출처). 엔진 소스 수정 0, library 경로 그대로, 저장소 쓰기 0.
# 측정 대상: 출발 구간 이득 L 하한(설계 41 §6.4-1)의 '블록 목표'를 바꿨을 때 출발점 L 칸이 어떻게 되는가.
#   mode base : as-built 그대로(블록 목표 = A_max 비례, A_max 미인증이면 비활성 -- 재작성 범위 인용용 기준선)
#   mode ga   : (가) 블록 목표 = DEC-105 (1) g_i^(1) = G * found_db_i / sum_j found_db_j (뷰 안 found_db 없는 블록이 있으면 뷰 전부 정의 불능)
#   mode table: 블록 국소 모델 gain(dB)을 모든 LUT L 앵커에서 잰 표만(목표 무관) -- found_db 없는 블록 포함
# 블록 국소 모델 gain 평가는 as-built `iv_gain_l._row/_gain_db`(U9 와 같은 블록 모델)를 측정 도구로만 부른다(원칙 8: 근거가 아니라 측정 수단).
# 결과 = 케이스마다 jsonl Python 바이너리 append.
# usage: python q8_engine_gainL.py <circuit> <mode> [--whatif-dcrole M8,M14]
import os, sys, json, time, pathlib, tempfile, dataclasses, traceback, math
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"; sys.dont_write_bytecode = True
SKILL = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
sys.path.insert(0, str(SKILL))
LIB = SKILL / "assets" / "library"
HERE = pathlib.Path(__file__).parent
OUT = HERE / "q8_engine_gainL.jsonl"
CIR, MODE = sys.argv[1], sys.argv[2]
WHATIF = None
if "--whatif-dcrole" in sys.argv:
    WHATIF = sys.argv[sys.argv.index("--whatif-dcrole") + 1].split(",")
WORK = pathlib.Path(tempfile.mkdtemp(prefix="q8_%s_%s_" % (CIR[:6], MODE), dir=os.environ.get("TEMP")))


def app(rec):
    rec = dict(rec, circuit=CIR, mode=MODE)
    with open(OUT, "ab") as fh:
        fh.write((json.dumps(rec, default=lambda o: repr(o)[:600], ensure_ascii=False) + "\n").encode("utf-8"))


t0 = time.time()
app({"case": "start", "work": str(WORK), "whatif_dcrole": WHATIF, "t": time.strftime("%Y-%m-%d %H:%M:%S")})
import gmid_engine.search  # noqa: F401
si = sys.modules["gmid_engine.search.start_intervals"]
ivc = sys.modules["gmid_engine.search.iv_context"]
ivg = sys.modules["gmid_engine.search.iv_gain_l"]
from gmid_engine.authoring import load_topology
from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.graph import structure_rule_fp
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.metrics import ACH_KEY, ParamTables, block_spec, block_gain_model_of
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.search import SearchSettings, build_search_context, open_run
from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access
from gmid_engine.search.start_values import GainInputs

CAPT = {"gain_inputs": [], "gain_call": [], "fields": []}

# ---- (가) 블록 목표 대체: DEC-105 (1) 정의를 측정 스크립트에서 손으로 계산(엔진 소스 수정 0)
_orig_gain_inputs = ivc._gain_inputs


def gain_inputs_ga(p, views, lut, constraints):
    if not any(m == "gain_ss_db" and op == ">=" for m, op, _v in constraints):
        return None, (("gain_l", "constraint_not_declared"),)
    gain = dict(p.column("graph", "gain_checks")).get(ACH_KEY)
    view = next((v for v in views if v.kind == "transfer"), None)
    found = [b.found_db for b in gain.blocks] if gain is not None else []
    goal = max(float(v) for m, op, v in constraints if m == "gain_ss_db" and op == ">=")
    rec = {"case": "ga_target", "G_db": goal, "found_db": found, "a_max_status": [b.status for b in gain.blocks] if gain else None,
           "ff_found_db": [b.found_db for b in gain.ff] if gain is not None and getattr(gain, "ff", None) else None,
           "block_members": [list(b.members) for b in gain.blocks] if gain else None}
    if gain is None or view is None or not gain.blocks or len(view.blocks) != len(gain.blocks) or any(f is None for f in found):
        rec["g1"] = None
        rec["undefined_reason"] = "found_db_missing" if any(f is None for f in found) else "no_view_or_blocks"
        CAPT["gain_inputs"].append(rec)
        return None, (("gain_l", "found_db_missing(q8 ga)"),)
    total = float(sum(found))
    local = p.value("graph", ACH_KEY, "local_inputs").view
    targets = [goal * f / total for f in found]
    rec["g1"] = targets
    CAPT["gain_inputs"].append(rec)
    blocks = tuple((block_spec(view, block, local), t) for block, t in zip(view.blocks, targets))
    return GainInputs(local, ParamTables(lut.memo, local.w_keys, local.grids), blocks), ()


def gain_inputs_eq(p, views, lut, constraints):
    """(나-2) ⚠ 대조용: 계획에 없는 새 배분 규칙(블록 수 등분 G/N)을 넣었을 때의 출발 L -- 권고 후보 아님, 대칭 비교 실측용."""
    if not any(m == "gain_ss_db" and op == ">=" for m, op, _v in constraints):
        return None, (("gain_l", "constraint_not_declared"),)
    gain = dict(p.column("graph", "gain_checks")).get(ACH_KEY)
    view = next((v for v in views if v.kind == "transfer"), None)
    goal = max(float(v) for m, op, v in constraints if m == "gain_ss_db" and op == ">=")
    local = p.value("graph", ACH_KEY, "local_inputs").view
    n = len(view.blocks)
    CAPT["gain_inputs"].append({"case": "eq_target", "G_db": goal, "n_blocks": n, "target_each": goal / n})
    blocks = tuple((block_spec(view, block, local), goal / n) for block in view.blocks)
    return GainInputs(local, ParamTables(lut.memo, local.w_keys, local.grids), blocks), ()


def gain_inputs_table(p, views, lut, constraints):
    """목표 무관 표: 모든 블록(found_db 없음 포함)을 목표 +inf 로 넣어 앵커마다 gain 만 잰다(L 하한은 쓰지 않음 -- 아래 래퍼가 원 결과를 돌려줌)."""
    gain = dict(p.column("graph", "gain_checks")).get(ACH_KEY)
    view = next((v for v in views if v.kind == "transfer"), None)
    if gain is None or view is None or not gain.blocks or len(view.blocks) != len(gain.blocks):
        return _orig_gain_inputs(p, views, lut, constraints)
    local = p.value("graph", ACH_KEY, "local_inputs").view
    CAPT["gain_inputs"].append({"case": "table_blocks", "found_db": [b.found_db for b in gain.blocks], "members": [list(b.members) for b in gain.blocks]})
    blocks = tuple((block_spec(view, block, local), float("inf")) for block in view.blocks)
    return GainInputs(local, ParamTables(lut.memo, local.w_keys, local.grids), blocks), ()


_orig_gain_l = si.gain_l_bounds


def gain_l_wrap(ctx, elements, resistors, gm_id_lo):
    res = _orig_gain_l(ctx, elements, resistors, gm_id_lo)
    tab = []
    inputs = ctx.gain
    if inputs is not None:
        anchors = [float(a) for a in inputs.local.grids[0]]
        for k, (spec, target) in enumerate(inputs.blocks):
            model, reason = block_gain_model_of(inputs.local, spec)
            row_db = []
            if model is not None:
                for j, L in enumerate(anchors):
                    row = ivg._row(ctx, inputs, model, j, gm_id_lo, elements, resistors)
                    row_db.append(None if row is None else ivg._gain_db(model, inputs, row))
            axes = []
            if model is not None:
                ref = model.normalized[0] if model.normalized else None
                for axis in model.axes:
                    if axis.kind == "current":
                        axes.append({"current_source": str(axis.label[0]), "in_elements": axis.label[0] in elements,
                                     "ref": None if ref is None else str(ref), "ref_in_elements": None if ref is None else ref in elements})
                    elif axis.kind == "resistor":
                        axes.append({"resistor": str(axis.label[0]), "value": resistors.get(axis.label[0])})
            tab.append({"block": k, "members": list(spec.members), "target_db": target, "model_reason": reason, "gain_db_by_anchor": row_db,
                        "cont_axes": axes})
        CAPT["gain_call"].append({"anchors_m": anchors, "blocks": tab, "l_owner": {str(k): str(v) for k, v in dict(ctx.l_owner).items()}})
    CAPT["gain_call"].append({"result_bounds": {m: [b.value for b in bs] for m, bs in res.bounds.items()},
                              "result_conflicts": [repr(c) for c in res.conflicts], "result_inactive": list(res.inactive),
                              "n_elements": len(elements), "elements": {str(k): v for k, v in list(elements.items())[:40]}})
    if MODE == "table":
        return ivg.GainLBounds({}, (), res.inactive)
    return res


_orig_fields = si._fields


def fields_wrap(rows, points, conflicts, inactive, macro, rungs, records, area, t, uncovered):
    CAPT["fields"].append({"n_rungs": len(rungs),
                           "rung0_L": [(repr(c), v) for c, v in (rungs[0].theta if rungs else ()) if c[0] == "L"],
                           "rung0_cells": list(rungs[0].cells) if rungs else None,
                           "inactive": [repr(x)[:300] for x in inactive],
                           "conflicts_L": [repr(c)[:300] for c in conflicts if getattr(c, "quantity", None) == "L"]})
    return _orig_fields(rows, points, conflicts, inactive, macro, rungs, records, area, t, uncovered)


si.gain_l_bounds = gain_l_wrap
si._fields = fields_wrap
if MODE == "ga":
    ivc._gain_inputs = gain_inputs_ga
elif MODE == "table":
    ivc._gain_inputs = gain_inputs_table
elif MODE == "eq":
    ivc._gain_inputs = gain_inputs_eq

DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos")); CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))
loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
man = json.loads(pathlib.Path(loc.manifest_path).read_text(encoding="utf-8"))
kinds = dict(DEVICE_KINDS); mins = {}
for e in man["slices"]:
    mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
dm = BoundedLRU(16)
pdk = read_pdk_decl(str(SKILL / "assets" / "sky130_pdk_decl.json"), dm)
q = dict(pdk.quantities)
lspec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX,
                noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, lspec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                   noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
rule = read_pdk_decl(str(SKILL / "assets" / "sky130_lut_rule_decl.json"), dm)
settings = SearchSettings(300.0, 40, (1e2, 1e5), (("front_budget_s", "q8 start-L measurement"),), (1e-13, 1e-10))
app({"case": "lut", "manifest": loc.manifest_path, "cap_npz": loc.cap_npz_path, "verify_midpoints": loc.midpoints_path})

sp = None
if WHATIF:
    topo = load_topology(str(LIB / (CIR + ".topology.json")))
    st = {"schema_version": "1", "topology_hash": topo.connectivity_fp, "rule_hash": structure_rule_fp(), "facts": [
        {"concept": "dc_role", "subject": m, "value": "signal", "status": "ratified",
         "evidence": {"rule": "q8 temp: O-216 declared dc_role (file is card LA-1a data commit; this is TEMP copy)", "nets": ["V1", "gnd"]},
         "approval_id": "TEMP-q8-O216-content-not-repo"} for m in WHATIF]}
    sp = WORK / (CIR + ".structure.json")
    sp.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
try:
    donors, counters = open_run()
    kw = {"structure_path": sp} if sp else {}
    a = run_stage_a(LIB / (CIR + ".topology.json"), LIB / (CIR + ".sizing_spec.json"), lut, output_dir=WORK / "out", donors=donors, counters=counters, **kw)
    app({"case": "stage_a", "status": a.status, "stop": repr(a.report.get("stop_reasons"))[:600]})
    memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
    b = run_stage_b(a, memo, pdk, output_dir=WORK / "out", diagnostic=True, settings=settings)
    ach = (b.report.get("achievability") or {}).get("gain") or {}
    app({"case": "stage_b", "status": b.status, "gain_blocks": [{k: blk.get(k) for k in ("key", "status", "found_db", "reason", "members")} for blk in (ach.get("blocks") or [])],
         "gain_ff": [{k: blk.get(k) for k in ("key", "status", "found_db", "reason")} for blk in (ach.get("ff") or [])], "target_db": ach.get("target_db")})
    if (a.status, b.status) != ("ok", "ok"):
        app({"case": "stop_before_search"})
        raise SystemExit
    kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo), donors=a.donors, counters=a.counters)
    s3 = WORK / "s3"; s3.mkdir(exist_ok=True)
    sctx = build_search_context(kctx, a.spec, settings, str(s3), pdk, rule, code_fp=a.code_fp)
    dom_cells = None
    try:
        dom = sctx.kctx if False else None
    except Exception:
        pass
    app({"case": "captured", "gain_inputs": CAPT["gain_inputs"], "gain_call": CAPT["gain_call"], "fields": CAPT["fields"], "s": time.time() - t0})
    if "--front" in sys.argv:
        # as-built 외층 경로(find_front)로 커널 판정 gain 행 c 를 잰다 -- 출발점 L 칸만 바뀐 상태의 측정(LA-1a 의 R6·P4 등 다른 범위는 없음)
        from gmid_engine.search import find_front
        t1 = time.time()
        fr = find_front(sctx, [])
        agg, nsealed, Ls_seen = {}, 0, {}
        for r in sorted(sctx.cache.values(), key=lambda r: r.seq):
            if r.status != "sealed":
                continue
            nsealed += 1
            for c in r.constraints:
                if c.c is None:
                    continue
                a_ = agg.setdefault(c.name, [0, -float("inf")])
                a_[0] += int(c.c >= 0)
                a_[1] = max(a_[1], c.c)
            for comp, v in getattr(r, "theta", ()) or ():
                if isinstance(comp, tuple) and comp and comp[0] == "L":
                    Ls_seen.setdefault(str(comp[1]), set()).add(round(float(v) * 1e9))
        app({"case": "front", "n_front": len(getattr(fr, "front", ()) or ()), "n_sealed": nsealed, "s": time.time() - t1,
             "rows": {k: {"pass": v[0], "c_max": v[1]} for k, v in sorted(agg.items()) if k.startswith(("ss:", "spec:"))},
             "L_nm_seen": {k: sorted(v)[:12] for k, v in Ls_seen.items()}, "notes": repr(getattr(fr, "notes", None))[:1500]})
except SystemExit:
    pass
except Exception:
    app({"case": "exc", "tb": traceback.format_exc()[-3000:], "captured": CAPT})
