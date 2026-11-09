"""측정 전용: 한 회로를 test_g10_no_recompute_9circuits.py 와 같은 흐름으로 돌리며 monkeypatch 계측. 엔진 파일은 건드리지 않는다."""
import sys, os, json, time, math, shutil, tempfile, collections, traceback
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
SKILL_S = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12/skills/analog-gmid-design"
sys.path.insert(0, SKILL_S)
sys.path.append("C:/Users/HSLEE/AppData/Roaming/Python/Python314/site-packages")
from pathlib import Path
SKILL = Path(SKILL_S)
OUT = Path(__file__).parent / "results.jsonl"
circuit = sys.argv[1]

from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.core import run_counters as rc_mod
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.search import SearchSettings, build_search_context, find_front, open_run
from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access
from gmid_engine.sizing.block_columns import dc_columns
from gmid_engine.sizing.block_widths import dc_widths
from gmid_engine.sizing.block_currents import dc_currents
from gmid_engine.lut._helpers_bins import bin_index

fdm = sys.modules["gmid_engine.search.fd_jacobian"]
kmod = sys.modules["gmid_engine.search.kernel"]

LIBRARY = SKILL / "assets" / "library"
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))
E_B = 40
NOT_SEARCHED = {"ngcc_3stage_ff"}
BLOCKS = ("dc_columns", "dc_widths", "dc_currents")

# ---------------- 계측 상태 ----------------
st = {"fd": False, "kind": None, "phase": "pre"}
cnt_all = collections.Counter()       # (phase, block, outcome)
cnt_fd = collections.Counter()        # (block, outcome)  FD 중
cnt_fdk = collections.Counter()       # (kind, block, outcome)
fd_calls = [0]
fd_cols_nominal = collections.Counter()   # kind -> 열 수(호출 누적, 명목)
fd_first_dims = {}
fd_eval_req = collections.Counter()   # kind -> evaluate 요청 수
fd_eval_kernel = collections.Counter()  # kind -> 실제 커널 실행 수(캐시 미적중)
t_blocks = collections.defaultdict(list)   # block -> [(dt, fd_flag, kind)]
t_kernel = []                         # size_and_seal 시간
fd_kernel_time = collections.Counter()

orig_record = rc_mod.RunCounters.record
def record(self, block, part, outcome, input_version):
    if block in BLOCKS:
        cnt_all[(st["phase"], block, outcome)] += 1
        if st["fd"]:
            cnt_fd[(block, outcome)] += 1
            cnt_fdk[(st["kind"], block, outcome)] += 1
    return orig_record(self, block, part, outcome, input_version)
rc_mod.RunCounters.record = record

orig_steps = fdm._steps
def steps(sctx, variables, base):
    fd_calls[0] += 1
    c = collections.Counter(v.component[0] for v in variables)
    for k, n in c.items():
        fd_cols_nominal[k] += n
    if not fd_first_dims:
        fd_first_dims.update(dict(c)); fd_first_dims["_total"] = len(variables)
    return orig_steps(sctx, variables, base)
fdm._steps = steps

orig_eval = fdm.evaluate
def fd_evaluate(sctx, theta, cells, parent=None, origin=(), geometry=None):
    var = sys._getframe(1).f_locals.get("var")
    kind = var.component[0] if var is not None else "?"
    prev = (st["fd"], st["kind"])
    st["fd"], st["kind"] = True, kind
    fd_eval_req[kind] += 1
    k0 = sctx.counters["kernel_calls"]
    t0 = time.perf_counter()
    try:
        return orig_eval(sctx, theta, cells, parent=parent, origin=origin, geometry=geometry)
    finally:
        dk = sctx.counters["kernel_calls"] - k0
        fd_eval_kernel[kind] += dk
        fd_kernel_time[kind] += time.perf_counter() - t0
        st["fd"], st["kind"] = prev
fdm.evaluate = fd_evaluate

def wrap_fn(block, name):
    orig = block.fn
    def timed(projection):
        t0 = time.perf_counter()
        try:
            return orig(projection)
        finally:
            t_blocks[name].append((time.perf_counter() - t0, st["fd"], st["kind"]))
    block.fn = timed
for b in (dc_columns, dc_widths, dc_currents):
    wrap_fn(b, b.name)

orig_sas = kmod.size_and_seal
def sas(*a, **k):
    t0 = time.perf_counter()
    try:
        return orig_sas(*a, **k)
    finally:
        t_kernel.append((time.perf_counter() - t0, st["fd"]))
kmod.size_and_seal = sas

# ---------------- env (test fixture 복제) ----------------
loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
kinds = dict(DEVICE_KINDS)
mins = {}
for e in man["slices"]:
    mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
dm = BoundedLRU(16)
pdk = read_pdk_decl(str(SKILL / "assets" / "sky130_pdk_decl.json"), dm)
q = dict(pdk.quantities)
spec_l = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX,
                 noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec_l, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                   noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
rule = read_pdk_decl(str(SKILL / "assets" / "sky130_lut_rule_decl.json"), dm)

def settings():
    return SearchSettings(600.0, E_B, (1e2, 1e5), (("front_budget_s", "xrunf1b B-T22 fixture"),), (1e-13, 1e-10))

def emit(rec):
    rec["circuit"] = circuit
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")

def rows_of(cnt, keyf):
    out = {}
    for b in BLOCKS:
        r = {o: keyf(b, o) for o in ("reuse", "graft", "replay", "compute")}
        calls = sum(r.values())
        out[b] = dict(calls=calls, reuses=r["reuse"], grafts=r["graft"], replays=r["replay"], computes=r["compute"],
                      reuse_ratio=(None if not calls else (r["reuse"] + r["graft"] + r["replay"]) / calls))
    return out

def stats(lst):
    xs = [x for x, *_ in lst]
    return dict(n=len(xs), sum_s=sum(xs), mean_ms=(1000 * sum(xs) / len(xs) if xs else None))

t_run0 = time.perf_counter()
out = Path(tempfile.mkdtemp(prefix="dcm_out"))
root = None
try:
    donors, counters = open_run()
    a = run_stage_a(LIBRARY / (circuit + ".topology.json"), LIBRARY / (circuit + ".sizing_spec.json"), lut, output_dir=out,
                    donors=donors, counters=counters)
    memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
    b = run_stage_b(a, memo, pdk, output_dir=out, diagnostic=True, settings=settings())
    searched = (a.status, b.status) == ("ok", "ok")
    status = "ok" if searched else "stage-B만 (a=%s b=%s)" % (a.status, b.status)
    rec = {"status": status, "searched": searched}
    snap = a.counters.snapshot()
    rec["stageAB_blocks"] = [dict(block=r.block, calls=r.calls, reuses=r.reuses, grafts=r.grafts, replays=r.replays, computes=r.computes)
                             for r in snap.blocks if r.block in BLOCKS]
    if not searched:
        rec["wall_run_s"] = time.perf_counter() - t_run0
        try:
            sn0 = b.s1.snapshot
            from gmid_engine.authoring import INPUT_DIRECTION as _ID
            dcw0 = dict(sn0.column("node", "dc_writer")); pd0 = dict(sn0.column("node", "port_direction"))
            rec["input_dc_mode"] = getattr(a.spec.input_dc, "mode", None)
            rec["input_ports"] = sorted(n for n, d in pd0.items() if d == _ID)
            rec["w4_input_roots"] = sorted(n for n, w in dcw0.items() if w.relation == "free_window" and pd0.get(n) == _ID)
            rec["w4_note"] = "단계 B s1.snapshot 의 dc_writer 에서"
        except BaseException as e0:
            rec["w4_note"] = "미판정: %s: %s" % (type(e0).__name__, e0)
        emit(rec)
        sys.exit(0)
    root = tempfile.mkdtemp(prefix="g10", dir=os.environ.get("TEMP") or None)
    kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo), donors=a.donors, counters=a.counters)
    sctx = build_search_context(kctx, a.spec, settings(), root, pdk, rule, code_fp=a.code_fp)
    st["phase"] = "search"
    t_s0 = time.perf_counter()
    fr = find_front(sctx, [])
    wall_search = time.perf_counter() - t_s0
    st["phase"] = "post"
    wall_run = time.perf_counter() - t_run0
    perf = dict(fr.perf)
    rec.update(wall_run_s=wall_run, wall_search_s=wall_search, eval_budget=perf.get("eval_budget"), stops_wall_budget=perf.get("stops_wall_budget"),
               kernel_calls=perf.get("kernel_calls"), requests=perf.get("requests"), hits=perf.get("hits"))
    # perf.blocks 정본 행
    rec["perf_blocks"] = [dict(r) for r in perf["blocks"] if r["block"] in BLOCKS]
    # 1. FD 행 / 전체 행
    rec["fd_rows"] = rows_of(cnt_fd, lambda bl, o: cnt_fd[(bl, o)])
    rec["search_rows_mine"] = rows_of(cnt_all, lambda bl, o: cnt_all[("search", bl, o)])
    rec["fd_rows_by_kind"] = {k: rows_of(cnt_fdk, lambda bl, o, k=k: cnt_fdk[(k, bl, o)])
                              for k in sorted({kk for kk, _b, _o in cnt_fdk})}
    rec["fd_calls"] = fd_calls[0]
    rec["fd_cols_nominal_by_kind"] = dict(fd_cols_nominal)
    rec["fd_first_jacobian_dims"] = fd_first_dims
    rec["fd_eval_req_by_kind"] = dict(fd_eval_req)
    rec["fd_eval_kernel_by_kind"] = dict(fd_eval_kernel)
    rec["fd_kernel_time_by_kind_s"] = dict(fd_kernel_time)
    # 2. 시간
    rec["time"] = {b_: dict(all=stats(t_blocks[b_]), fd=stats([x for x in t_blocks[b_] if x[1]]),
                            by_kind={k: stats([x for x in t_blocks[b_] if x[1] and x[2] == k])
                                     for k in sorted({x[2] for x in t_blocks[b_] if x[1]})}) for b_ in BLOCKS}
    rec["time_kernel_size_and_seal"] = dict(all=stats(t_kernel), fd=stats([x for x in t_kernel if x[1]]))
    # 5. 입력 포트 W4 뿌리 / 슬라이스 변화
    base = sctx.dc.base
    dcw = dict(base.column("node", "dc_writer")) if True else {}
    portdir = dict(base.column("node", "port_direction"))
    from gmid_engine.authoring import INPUT_DIRECTION
    w4_input_roots = sorted(n for n, w in dcw.items() if w.relation == "free_window" and portdir.get(n) == INPUT_DIRECTION)
    rec["input_dc_mode"] = getattr(a.spec.input_dc, "mode", None)
    rec["input_ports"] = sorted(n for n, d in portdir.items() if d == INPUT_DIRECTION)
    rec["w4_input_roots"] = w4_input_roots
    rec["w4_input_root_verdict"] = ("예" if w4_input_roots else "아니오")
    wk = dict(sctx.dc.lut.w_keys)
    slices = lut.slice_map
    kind_slices = collections.defaultdict(list)
    for (kd, key), sl in slices.items():
        kind_slices[kd].append((key, sl.w_m, sl.l_bins.w_bin if sl.l_bins and sl.l_bins.bins else None))
    rec["ref_slices"] = {kd: dict(key=k, w_m=slices[(kd, k)].w_m, w_bin=slices[(kd, k)].l_bins.w_bin) for kd, k in wk.items()}
    rec["slices_per_kind"] = {kd: sorted(v) for kd, v in kind_slices.items()}
    pts = [p_.result for p_ in fr.front]
    pool = "front"
    if not pts:
        pool = "sctx.cache sealed (front 비어 있음)"
        pts = sorted((r_ for r_ in sctx.cache.values() if getattr(r_, "status", None) == "sealed" and r_.evaluation is not None),
                     key=lambda r_: r_.seq)
    rec["point_pool"] = pool
    rec["front_size"] = len(fr.front)
    rec["sealed_in_cache"] = sum(1 for r_ in sctx.cache.values() if getattr(r_, "status", None) == "sealed")
    rec["pending_front_size"] = len(fr.pending_front); rec["unmeasured_front_size"] = len(fr.unmeasured_front)
    rec["cache_status_counts"] = dict(collections.Counter(getattr(r_, "status", None) for r_ in sctx.cache.values()))
    # 점 선택: 최대 5 (균등 간격)
    if len(pts) > 5:
        idx = sorted({round(i * (len(pts) - 1) / 4) for i in range(5)})
        pts = [pts[i] for i in idx]
    point_recs = []
    for p in pts:
        ev = p.evaluation
        if ev is None:
            continue
        sn = ev.snapshot
        ops = dict(sn.column("device", "dc_op"))
        coords = dict(sn.column("device", "dc_coord"))
        per = {"writer": [0, 0], "dependent": [0, 0]}   # [장치수, 슬라이스 바뀜]
        detail = []
        for m, op in sorted(ops.items()):
            role = coords[m].role if m in coords else "?"
            ref_key = wk[op.kind]
            ref_sl = slices[(op.kind, ref_key)]
            wb = ref_sl.l_bins.w_bin if ref_sl.l_bins.bins else None
            if wb is None:
                detail.append(dict(m=m, role=role, W=op.W, note="no_bin_map")); continue
            w_hi = wb[1]
            mm = max(1, math.ceil(op.W / w_hi * (1 - 1e-12)))
            w_f = op.W / mm
            cands = [key for key, _w, bn in kind_slices[op.kind] if bn is not None and bin_index([bn], w_f) is not None]
            changed = ref_key not in cands
            per.setdefault(role, [0, 0])
            per[role][0] += 1
            per[role][1] += int(changed)
            detail.append(dict(m=m, role=role, rel=getattr(coords[m], "relation", None), kind=op.kind, W=op.W, w_hi=w_hi, m_fingers=mm, w_f=w_f,
                               ref_key=ref_key, cand_keys=cands, changed=changed, op_w_key=op.w_key))
        point_recs.append(dict(point_id=str(p.seq), per_role=per, devices=detail))
    rec["points"] = point_recs
    emit(rec)
except SystemExit:
    pass
except BaseException as exc:
    emit({"status": "실패: %s: %s" % (type(exc).__name__, exc), "trace": traceback.format_exc()[-3000:]})
finally:
    shutil.rmtree(out, ignore_errors=True)
    if root:
        shutil.rmtree(root, ignore_errors=True)
