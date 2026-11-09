"""IT-2a 소급 측정 -- 블록 안 재계산 효율 (읽기 전용 관찰 래퍼, 반환값 불변).
usage: python -I perf.py <side_root> <side_tag> <circuit> <mode: profile|plain> <out_dir>
yends_analyst.py(o103_yend) 의 준비 순서를 따른다. 래퍼는 원 함수를 그대로 불러 같은 객체를 돌려준다.
"""
import cProfile
import collections
import io
import json
import os
import pstats
import statistics
import sys
import time
from pathlib import Path

skill = Path(sys.argv[1]) / "skills" / "analog-gmid-design"
tag, circuit, mode, out_dir = sys.argv[2], sys.argv[3], sys.argv[4], Path(sys.argv[5])
out_dir.mkdir(parents=True, exist_ok=True)
out = out_dir / "perf.jsonl"
sys.path.insert(0, str(skill))
sys.path.append("C:/Users/HSLEE/AppData/Roaming/Python/Python314/site-packages")
import gmid_engine.search  # noqa: F401
from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.core.graph_snapshot import GraphSnapshot
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.search import SearchSettings, build_search_context, find_front, open_run
from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access

kmod = sys.modules["gmid_engine.search.kernel"]
seal_mod = sys.modules["gmid_engine.sizing.seal"]
cb_mod = sys.modules["gmid_engine.core.compute_block"]
s3_mod = sys.modules["gmid_engine.search.s3_index"]
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))


def emit(rec):
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True, default=repr) + "\n")


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
settings = SearchSettings(7200.0, 40, (1e2, 1e5), (("front_budget_s", "it2a perf"),), (1e-13, 1e-10))
work = out_dir / ("work_" + tag + "_" + circuit + "_" + mode)
work.mkdir(parents=True, exist_ok=True)
base_dir = skill / "assets" / "library"
donors, counters = open_run()
t_prep0 = time.perf_counter()
a = run_stage_a(base_dir / (circuit + ".topology.json"), base_dir / (circuit + ".sizing_spec.json"), lut,
                output_dir=work, donors=donors, counters=counters)
head = {"side": tag, "circuit": circuit, "mode": mode, "stage_a": a.status}
if a.status != "ok" and a.s1 is None:
    emit({**head, "kind": "stop"})
    sys.exit(0)
memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
b = run_stage_b(a, memo, pdk, output_dir=work, diagnostic=True, settings=settings)
kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo), donors=a.donors, counters=a.counters)
sctx = build_search_context(kctx, a.spec, settings, None, pdk, rule, code_fp=a.code_fp)
t_prep = time.perf_counter() - t_prep0
counters_before = {(r.block, r.part): r for r in a.counters.snapshot().blocks}
memo_before = {r: s for r, s in memo.stats()}

# ---------------- 관찰 래퍼 (반환값 불변) ----------------
EXTRA = mode == "profile"   # plain 은 시간만(관찰 부가 계산 없음)
KEEP = []          # id 재사용 방지용 참조 보관(관찰 전용)
ev_log = []        # size_and_seal 1회마다


def snap_size(s):
    nrec = sum(len(r) for r in s.tables.values())
    nfld = sum(len(rec.fields) for r in s.tables.values() for rec in r.values())
    return nrec, nfld


orig_ss = kmod.size_and_seal


def w_size_and_seal(dc, theta, *, parent=None, w_request=()):
    t0 = time.perf_counter()
    exc = None
    try:
        ev = orig_ss(dc, theta, parent=parent, w_request=w_request)
        return ev
    except BaseException as e:
        exc = type(e).__name__
        raise
    finally:
        ev_log.append({"parent": parent is not None, "t": time.perf_counter() - t0, "exc": exc,
                       "parent_id": id(parent.snapshot) if parent is not None else None})
        if parent is not None:
            KEEP.append(parent)


kmod.size_and_seal = w_size_and_seal

dc_log = []
orig_dc = getattr(GraphSnapshot, "derive_child", None)
if orig_dc is not None:
    def w_derive_child(self, keep_writers):
        keep = frozenset(keep_writers)
        t0 = time.perf_counter()
        child = orig_dc(self, keep_writers)
        dt = time.perf_counter() - t0
        if not EXTRA:
            dc_log.append({"t": dt, "pid": id(self), "keep": hash(keep), "rec": 0, "fld": 0, "c_rec": 0, "c_fld": 0,
                           "dropped_writers": [], "dropped_versions": []})
            KEEP.append(self)
            return child
        n_rec, n_fld = snap_size(self)
        c_rec, c_fld = snap_size(child)
        dropped_w = sorted({fv.writer for r in self.tables.values() for rec in r.values() for _n, fv in rec.fields} - keep)
        dc_log.append({"t": dt, "pid": id(self), "keep": hash(keep), "rec": n_rec, "fld": n_fld, "c_rec": c_rec, "c_fld": c_fld,
                       "dropped_writers": dropped_w,
                       "dropped_versions": sorted(set(self.block_versions) - set(child.block_versions))})
        KEEP.append(self)
        return child

    GraphSnapshot.derive_child = w_derive_child

sv_log = []
orig_sv = seal_mod.seal_versions


def w_seal_versions(snapshot, calls, *rest):
    t0 = time.perf_counter()
    item = orig_sv(snapshot, calls, *rest)
    dt = time.perf_counter() - t0
    if not EXTRA:
        sv_log.append({"t": dt, "t_used_replica": 0.0, "t_input_version_replica": 0.0, "sid": id(snapshot), "calls": (),
                       "rec": 0, "fld": 0, "n_used": 0})
        KEEP.append(snapshot)
        return item
    # used-writer 수집 비용 재현(관찰 전용, 같은 식) -- head 의 전체 순회 비용 몫 추정
    t1 = time.perf_counter()
    used = {fv.writer for records in snapshot.tables.values() for record in records.values() for _name, fv in record.fields}
    t_used = time.perf_counter() - t1
    # (1)(2) 부분: 블록마다 input_version 재계산 비용 재현
    t2 = time.perf_counter()
    for block, extras in calls:
        block.input_version(snapshot, *extras)
    t_iv = time.perf_counter() - t2
    n_rec, n_fld = snap_size(snapshot)
    sv_log.append({"t": dt, "t_used_replica": t_used, "t_input_version_replica": t_iv, "sid": id(snapshot),
                   "calls": tuple(b.name for b, _ in calls), "rec": n_rec, "fld": n_fld, "n_used": len(used)})
    KEEP.append(snapshot)
    return item


seal_mod.seal_versions = w_seal_versions

rep_log = []
orig_rep = seal_mod.dc_seal_report


class _RepWrap:
    def __init__(self, blk):
        self._blk = blk

    def __getattr__(self, n):
        return getattr(self._blk, n)

    def __call__(self, snapshot, *extras, donors, counters):
        if not EXTRA:
            t0 = time.perf_counter()
            try:
                return self._blk(snapshot, *extras, donors=donors, counters=counters)
            finally:
                rep_log.append({"t": time.perf_counter() - t0, "outcome": "?"})
        before = {(r.block, r.part): (r.reuses, r.grafts, r.replays, r.computes) for r in counters.snapshot().blocks}
        t0 = time.perf_counter()
        try:
            return self._blk(snapshot, *extras, donors=donors, counters=counters)
        finally:
            dt = time.perf_counter() - t0
            after = {(r.block, r.part): (r.reuses, r.grafts, r.replays, r.computes) for r in counters.snapshot().blocks}
            k = (self._blk.name, "*")
            bv, av = before.get(k, (0, 0, 0, 0)), after.get(k, (0, 0, 0, 0))
            outcome = [n for n, x, y in zip(("reuse", "graft", "replay", "compute"), bv, av) if y > x]
            rep_log.append({"t": dt, "outcome": outcome[0] if outcome else "?"})


seal_mod.dc_seal_report = _RepWrap(orig_rep)

graft_log = collections.defaultdict(lambda: [0, 0.0])
orig_graft = cb_mod.graft


def w_graft(target, block, part, donor, input_version):
    t0 = time.perf_counter()
    r = orig_graft(target, block, part, donor, input_version)
    g = graft_log[block.name]
    g[0] += 1
    g[1] += time.perf_counter() - t0
    return r


cb_mod.graft = w_graft

find_log = collections.defaultdict(lambda: [0, 0, 0.0])   # writer -> [calls, hits, time]
S3 = s3_mod.S3Index
orig_find = S3.find


def w_find(self, writer, part, input_version):
    t0 = time.perf_counter()
    r = orig_find(self, writer, part, input_version)
    f = find_log[writer]
    f[0] += 1
    f[1] += r is not None
    f[2] += time.perf_counter() - t0
    return r


S3.find = w_find

lut_log = collections.Counter()
orig_lookup = LutMemo.lookup


def w_lookup(self, region, fn_name, key, compute):
    lut_log[(region, fn_name)] += 1
    return orig_lookup(self, region, fn_name, key, compute)


LutMemo.lookup = w_lookup

# ---------------- 탐색 ----------------
prof = cProfile.Profile() if mode == "profile" else None
t0 = time.perf_counter()
if prof:
    prof.enable()
try:
    fr = find_front(sctx, [])
    front_ok = True
except Exception as e:  # noqa: BLE001 -- 관찰 전용
    front_ok = repr(e)[:300]
if prof:
    prof.disable()
t_search = time.perf_counter() - t0

# ---------------- 정리 ----------------
def stats_of(xs):
    return {"n": len(xs), "sum": sum(xs), "mean": statistics.fmean(xs) if xs else None,
            "median": statistics.median(xs) if xs else None}


dup_dc = collections.Counter((d["pid"], d["keep"]) for d in dc_log)
dup_sv = collections.Counter(s["sid"] for s in sv_log)
rows_after = a.counters.snapshot().blocks
blocks = {}
for r in rows_after:
    b0 = counters_before.get((r.block, r.part))
    d = [r.reuses - (b0.reuses if b0 else 0), r.grafts - (b0.grafts if b0 else 0), r.replays - (b0.replays if b0 else 0),
         r.computes - (b0.computes if b0 else 0), r.recomputes_same_input - (b0.recomputes_same_input if b0 else 0)]
    if any(d):
        blocks[r.block] = dict(zip(("reuse", "graft", "replay", "compute", "recompute_same_input"), d))
memo_after = {r: s for r, s in memo.stats()}
memo_delta = {r: {"hits": getattr(memo_after[r], "hits", 0) - getattr(memo_before[r], "hits", 0), "misses": getattr(memo_after[r], "misses", 0) - getattr(memo_before[r], "misses", 0)}
              for r in memo_after}
par = [e for e in ev_log if e["parent"]]
nopar = [e for e in ev_log if not e["parent"]]
rec = {**head, "kind": "search", "front_ok": front_ok, "t_prep_s": t_prep, "t_search_s": t_search,
       "size_and_seal": {"all": stats_of([e["t"] for e in ev_log]), "with_parent": stats_of([e["t"] for e in par]),
                         "no_parent": stats_of([e["t"] for e in nopar]),
                         "n_distinct_parent": len({e["parent_id"] for e in par})},
       "evaluate_times": stats_of(list(sctx.eval_times)),
       "sctx_counters": dict(sctx.counters),
       "derive_child": {**stats_of([d["t"] for d in dc_log]), "dup_same_parent_keep": sum(c - 1 for c in dup_dc.values()),
                        "distinct": len(dup_dc), "max_repeat": max(dup_dc.values()) if dup_dc else 0,
                        "parent_fld_mean": statistics.fmean([d["fld"] for d in dc_log]) if dc_log else None,
                        "child_fld_mean": statistics.fmean([d["c_fld"] for d in dc_log]) if dc_log else None,
                        "n_noop": sum(1 for d in dc_log if d["fld"] == d["c_fld"] and not d["dropped_versions"]),
                        "dropped_writers": sorted({w for d in dc_log for w in d["dropped_writers"]}),
                        "dropped_versions": sorted({w for d in dc_log for w in d["dropped_versions"]})},
       "seal_versions": {**stats_of([s["t"] for s in sv_log]), "t_used_replica_sum": sum(s["t_used_replica"] for s in sv_log),
                         "t_input_version_replica_sum": sum(s["t_input_version_replica"] for s in sv_log),
                         "dup_same_snapshot": sum(c - 1 for c in dup_sv.values()),
                         "fld_mean": statistics.fmean([s["fld"] for s in sv_log]) if sv_log else None,
                         "rec_mean": statistics.fmean([s["rec"] for s in sv_log]) if sv_log else None},
       "dc_seal_report": {**stats_of([r["t"] for r in rep_log]), "outcomes": dict(collections.Counter(r["outcome"] for r in rep_log)),
                          "graft_t_sum": graft_log["dc_seal_report"][1] if "dc_seal_report" in graft_log else 0.0,
                          "find": find_log.get("dc_seal_report")},
       "graft_by_block": {k: v for k, v in graft_log.items()},
       "find_total": [sum(v[0] for v in find_log.values()), sum(v[1] for v in find_log.values()), sum(v[2] for v in find_log.values())],
       "lut_lookups_total": sum(lut_log.values()), "lut_lookups_by_fn": {r + ":" + f: n for (r, f), n in lut_log.most_common(25)},
       "memo_delta": memo_delta, "block_counters": blocks}
emit(rec)
if prof:
    s = io.StringIO()
    st = pstats.Stats(prof, stream=s)
    st.sort_stats("cumulative").print_stats(70)
    st.sort_stats("tottime").print_stats(40)
    (out_dir / ("prof_" + tag + "_" + circuit + ".txt")).write_text(s.getvalue(), encoding="utf-8")
    prof.dump_stats(str(out_dir / ("prof_" + tag + "_" + circuit + ".pstats")))
