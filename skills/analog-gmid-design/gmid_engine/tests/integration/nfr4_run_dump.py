"""NFR-4 실행 하네스(test 쪽 도구): 회로 하나의 사슬을 이 프로세스에서 돌려 실행 기록(`nfr4_compare.FORMAT`)을 파일로 덤프한다.
interface card nfr4c2 C7 '하네스 수집', 설계 40 §2.4.13 (2) 비트 동일 집합·(5) '결과 기록에 없는 칸'.

usage: python -P nfr4_run_dump.py <회로> <출력 기록.json> <작업 폴더> [--eval-budget 40] [--front-budget-s 7200] [--numpy-first]

- 사슬: 단계 A(run_stage_a) -> 단계 B(run_stage_b, diagnostic) -> (둘 다 ok 면) 커널 컨텍스트 -> 탐색 컨텍스트(archive_root = <작업 폴더>/s3)
  -> find_front(sctx, []). 탐색 설정 = E_B 선언(기본 40), 넉넉한 front_budget_s(기본 7200 s -- 벽시계 정지가 나지 않게), θ 상자는
  tests/integration/test_s0_layer_9circuits.py `_settings` 와 같은 입력.
- 관찰 지점(계약, C7): 모듈 `sys.modules["gmid_engine.search.find_front"]` 의 속성 `layer0_start`·`sweep_front` 를 반환값을 기록하고 그대로 돌려주는
  감싸개로 바꾼다. 공개 속성 `SearchContext.cache` 는 실행 뒤 읽기만 한다. 엔진에 비교용 칸을 더하지 않는다.
- 덤프(필드 경로 -> 부류 D·C·K·T, 값, 구역, 분해능 인자): S0 수준 스냅샷 필드(값 지문 `value_fp` -- 연속값을 담은 값이면 C 지문 칸, 아니면 D),
  단계 A·B 보고서 JSON, 층 0 결과, sweep_front 결과(ε 풀이 기록·failed_eps·front·lb_stops), find_front 결과(front·pending·unmeasured·perf·notes),
  평가 캐시(평가마다 status·실패·제약 행·원뿔 행·목적·θ·평가 스냅샷 지문), S3 evals·runs 줄. float 는 `float.hex`.
- 실행마다 달라지는 경로 문자열(작업 폴더·TEMP·표 캐시 폴더)은 기록 전에 표지 문자열로 바꾼다(실행 사이 비교가 경로 차이로 깨지지 않게).
- 부류 규칙(설계 40 §2.4.13 (3)): bool·int·str·None = D, float = C(비유한 float 는 정의 여부라 D), K = 경로 계수 이름(`K_NAMES`·perf 정수),
  T = 시간 칸 이름(`T_NAMES`). C 의 분해능 종류는 칸 이름으로 정한다(`_res_for`), 출처 없는 칸은 unsourced(필드별 비교에서 판정 불능).
진행은 <작업 폴더>/progress.log 에 단계마다 덧붙인다(중간에 죽어도 남게). 기록 파일은 단계마다 다시 쓴다.
"""
from __future__ import annotations

import argparse
import dataclasses
import enum
import json
import math
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[2]
LIBRARY = SKILL / "assets" / "library"
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))
FORMAT = "nfr4_run_record/1"

T_NAMES = frozenset(("wall_s", "eval_time_median_s", "eval_times"))
K_NAMES = frozenset(("iterations", "kernel_calls", "unique_keys", "requests", "hits", "fail_hits", "outside_domain",
                     "recompute_same_key", "n_history", "history_seqs", "sweeps", "nit", "probes", "n_starts", "n_solves",
                     "lut_memo_evictions",
                     "stops_eval_budget", "stops_wall_budget", "message"))
STOP_NAMES = frozenset(("stop", "aborts", "stops"))
MAX_DEPTH = 60


class Dump:
    def __init__(self, normalize):
        self.fields = {}
        self.normalize = normalize            # [(경로 문자열, 표지)]

    # ------------------------------------------------------------ 잎
    def _str(self, s):
        for raw, tag in self.normalize:
            if raw:
                s = s.replace(raw, tag)
        return s

    def put(self, path, cls, value, zone, res=None, fp=False):
        f = {"cls": cls, "value": value, "zone": zone}
        if fp:
            f["fp"] = True
        if res is not None:
            f["res"] = res
        self.fields[path] = f

    def leaf(self, path, v, zone, res=None):
        name = path.rsplit("/", 1)[-1].split("[", 1)[0]
        try:
            import numpy as np
            if isinstance(v, np.generic):
                v = v.item()
        except ImportError:
            pass
        if isinstance(v, bool) or v is None:
            self.put(path, "D", v, zone)
        elif isinstance(v, int):
            k = name in K_NAMES or ("/perf/" in "/" + path + "/" and name != "eval_budget")
            self.put(path, "K" if k else "D", v, zone)
        elif isinstance(v, float):
            if name in T_NAMES:
                self.put(path, "T", float(v).hex(), zone)
            elif not math.isfinite(v):
                self.put(path, "D", repr(v), zone)
            else:
                self.put(path, "C", float(v).hex(), zone, res or _res_for(path))
        elif isinstance(v, str):
            self.put(path, "K" if name in K_NAMES else "D", self._str(v), zone)
        elif isinstance(v, bytes):
            self.put(path, "D", v.hex(), zone)
        elif isinstance(v, enum.Enum):
            self.put(path, "D", "%s.%s" % (type(v).__name__, v.name), zone)
        else:
            r = repr(v)
            self.put(path, "D", self._str(type(v).__name__ if " at 0x" in r else r), zone)

    # ------------------------------------------------------------ 일반 걸음
    def walk(self, path, obj, zone, depth=0):
        if depth > MAX_DEPTH:
            self.leaf(path, "<depth>", zone)
            return
        try:
            import numpy as np
            if isinstance(obj, np.ndarray):
                obj = obj.tolist()
            elif isinstance(obj, np.generic):
                obj = obj.item()
        except ImportError:
            pass
        if obj is None or isinstance(obj, (bool, int, float, str, bytes, enum.Enum)):
            self.leaf(path, obj, zone)
        elif _is_eval(obj):
            self.eval_result(path, obj, zone)
        elif dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            for f in dataclasses.fields(obj):
                if f.name == "history":
                    self.history(path + "/history", getattr(obj, f.name), zone)
                else:
                    self.walk(path + "/" + f.name, getattr(obj, f.name), zone, depth + 1)
        elif isinstance(obj, dict) or (hasattr(obj, "items") and hasattr(obj, "keys")):
            for k in sorted(obj.keys(), key=repr):
                self.walk(path + "/" + _key(k), obj[k], zone, depth + 1)
        elif isinstance(obj, (tuple, list)):
            if _is_pairs(obj):
                for k, v in obj:
                    self.walk(path + "/" + _key(k), v, zone, depth + 1)
            else:
                for i, v in enumerate(obj):
                    self.walk("%s[%d]" % (path, i), v, zone, depth + 1)
        elif isinstance(obj, (set, frozenset)):
            self.leaf(path, json.dumps(sorted(repr(x) for x in obj)), zone)
        elif hasattr(obj, "__dict__"):
            for k in sorted(vars(obj)):
                if not k.startswith("_"):
                    self.walk(path + "/" + k, vars(obj)[k], zone, depth + 1)
        else:
            self.leaf(path, obj, zone)

    def history(self, path, hist, zone):
        """풀이 이력: 길이(K)와 평가 seq 목록(K) -- 이력 원소 자체는 평가 캐시(cache/*)가 담는다."""
        hist = tuple(hist or ())
        self.put(path + "/n_history", "K", len(hist), zone)
        self.put(path + "/history_seqs", "K", json.dumps([getattr(r, "seq", None) for r in hist]), zone)

    # ------------------------------------------------------------ 평가 결과
    def eval_result(self, path, r, zone):
        key = getattr(r, "key", None)
        self.put(path + "/seq", "D", r.seq, zone)
        self.put(path + "/status", "D", r.status, zone)
        if key is not None:
            self.put(path + "/cells", "D", json.dumps(list(getattr(key, "cells", ()) or ())), zone)
        self.walk(path + "/theta", r.theta, zone)
        self.walk(path + "/failure", r.failure, zone)
        names = [c.name for c in r.constraints]
        self.put(path + "/constraint_names", "D", json.dumps(names), zone)
        self.put(path + "/active", "D", json.dumps(sorted(c.name for c in r.constraints if c.active)), zone)
        for c in r.constraints:
            self.leaf(path + "/constraints/" + c.name + "/c", c.c, zone, {"kind": "c"})
        self.put(path + "/cone_active", "D", json.dumps(sorted(c.name for c in r.cone if c.active)), zone)
        for c in r.cone:
            self.leaf(path + "/cone/" + c.name + "/c", c.c, zone, {"kind": "c"})
        self.walk(path + "/unmeasured", r.unmeasured, zone)
        self.walk(path + "/warnings", r.warnings, zone)
        ev = getattr(r, "evaluation", None)
        tol_i = _rail_tol_i(ev)
        ob = r.objectives
        if ob is not None:
            for f in dataclasses.fields(ob):
                v = getattr(ob, f.name)
                if f.name == "power_w":
                    self.leaf(path + "/objectives/power_w", v, zone, {"kind": "power", "tol_i": tol_i} if tol_i else None)
                elif f.name == "kcl_residual_a":
                    self.leaf(path + "/objectives/kcl_residual_a", v, zone, {"kind": "kcl", "tol_i": tol_i} if tol_i else None)
                else:
                    self.walk(path + "/objectives/" + f.name, v, zone)
        if ev is not None:
            snap = getattr(ev, "snapshot", None)
            if snap is not None:
                self.put(path + "/evaluation/snapshot_fp", "C", snap.fp, zone, {"kind": "unsourced"}, fp=True)
            self.walk(path + "/evaluation/report", getattr(ev, "report", None), zone)


def _is_eval(obj):
    return all(hasattr(obj, a) for a in ("key", "theta", "status", "constraints", "cone", "seq", "objectives"))


def _key(k):
    if isinstance(k, tuple):
        return ":".join(str(x) for x in k)
    return str(k)


def _is_pairs(obj):
    if not obj or not all(isinstance(x, tuple) and len(x) == 2 for x in obj):
        return False
    keys = [x[0] for x in obj]
    ok = all(isinstance(k, str) or (isinstance(k, tuple) and all(isinstance(i, (str, int)) for i in k)) for k in keys)
    return ok and len({_key(k) for k in keys}) == len(keys)


def _res_for(path):
    """칸 이름 -> 분해능 종류(설계 40 §2.4.13 (4)). 모르는 칸 = unsourced(필드별 비교에서 판정 불능)."""
    parts = path.split("/")
    name = parts[-1].split("[", 1)[0]
    if "theta" in parts or "theta" in name:
        return {"kind": "theta", "h": None}                      # 실행 뒤 FD 스텝 자료 없음(N-8)
    if name == "c":
        return {"kind": "c"}
    if name == "margin":
        return {"kind": "margin"}
    if name in ("area_m2", "gate_area_m2"):
        return {"kind": "area"}
    if name == "w_m":
        return {"kind": "max_decl_prop", "declared": "W", "propagated": None}
    if name == "area_est_m2":
        return {"kind": "max_decl_prop", "declared": "area", "propagated": None}
    if name == "W":
        return {"kind": "W"}
    if parts[0] == "layer0" and name == "t":
        return {"kind": "t"}
    return {"kind": "unsourced"}


def _has_float(v, budget=None):
    """값 안에 유한·비유한 float 가 있는가(걸음 상한을 넘으면 True -- 보수적으로 연속값 지문 칸으로 둔다)."""
    budget = budget if budget is not None else [200000]
    stack = [v]
    seen = set()
    while stack:
        budget[0] -= 1
        if budget[0] < 0:
            return True
        x = stack.pop()
        if isinstance(x, float):
            return True
        if type(x).__name__ in ("float64", "float32", "float16"):
            return True
        if x is None or isinstance(x, (bool, int, str, bytes, enum.Enum)):
            continue
        if id(x) in seen:
            continue
        seen.add(id(x))
        if type(x).__name__ == "ndarray":
            if x.dtype.kind in "fc":
                return True
            continue
        if dataclasses.is_dataclass(x) and not isinstance(x, type):
            stack.extend(getattr(x, f.name) for f in dataclasses.fields(x))
        elif isinstance(x, dict) or (hasattr(x, "items") and hasattr(x, "keys")):
            stack.extend(x.keys())
            stack.extend(x.values())
        elif isinstance(x, (tuple, list, set, frozenset)):
            stack.extend(x)
        elif hasattr(x, "__dict__"):
            stack.extend(vars(x).values())
    return False


def _rail_tol_i(ev):
    """레일마다 tol_I,k = 그 레일에 채널이 닿는 소자의 max(dc_tol_v·I·gm/ID)(설계 40 §2.4.13 (4) b_P 의 tol_I,k -- tests/search/conftest.py
    `expected_objectives` 와 같은 독립 식). 스냅샷 칸이 없으면 None."""
    snap = getattr(ev, "snapshot", None)
    if snap is None:
        return None
    try:
        from gmid_engine.sizing import DC_KEY
        rails = dict(snap.column("node", "dc_rail_v"))
        basis = snap.value("graph", DC_KEY, "dc_current_basis")
        ops = dict(snap.column("device", "dc_op"))
        tol = dict(snap.column("device", "dc_tol_v"))
    except (KeyError, AttributeError, TypeError, ValueError):
        return None
    out = {}
    for k in rails:
        cands = [tol[el] * ops[el].current * ops[el].gm_id for el, a, b in basis.ends
                 if el in ops and k in (a, b) and tol.get(el) is not None]
        if cands:
            out[k] = abs(max(cands))
    return out or None


def _lines(path):
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def main(argv=None):
    # 바깥 스레드 설정은 엔진 import 전에 읽어 둔다 -- 엔진이 import 때 OPENBLAS_NUM_THREADS 를 1 로 고정하므로(interface card C1)
    # import 뒤에 읽으면 항상 '1' 이 된다. progress.log 의 `start threads_env=` 와 기록의 `threads_env` 가 이 값 하나를 쓴다.
    threads_env = os.environ.get("OPENBLAS_NUM_THREADS")
    ap = argparse.ArgumentParser()
    ap.add_argument("circuit")
    ap.add_argument("out_json")
    ap.add_argument("work")
    ap.add_argument("--eval-budget", type=int, default=40)
    ap.add_argument("--front-budget-s", type=float, default=7200.0)
    ap.add_argument("--numpy-first", action="store_true")
    a_ = ap.parse_args(argv)
    work = Path(a_.work)
    work.mkdir(parents=True, exist_ok=True)
    log = work / "progress.log"

    def note(msg):
        with open(log, "a", encoding="utf-8") as f:
            f.write("%s %s %s\n" % (time.strftime("%H:%M:%S"), a_.circuit, msg))

    note("start threads_env=%s numpy_first=%s" % (threads_env, a_.numpy_first))
    if a_.numpy_first:
        import numpy  # noqa: F401
        import scipy.linalg  # noqa: F401
    if str(SKILL) not in sys.path:
        sys.path.insert(0, str(SKILL))
    import gmid_engine.search  # noqa: F401
    ff_mod = sys.modules["gmid_engine.search.find_front"]
    seen = {"layer0": [], "sweep": []}
    orig_l0, orig_sw = ff_mod.layer0_start, ff_mod.sweep_front

    def l0_wrapped(*args, **kw):
        r = orig_l0(*args, **kw)
        seen["layer0"].append(r)
        return r

    def sw_wrapped(*args, **kw):
        r = orig_sw(*args, **kw)
        seen["sweep"].append(r)
        return r

    ff_mod.layer0_start, ff_mod.sweep_front = l0_wrapped, sw_wrapped

    from gmid_engine.core import BoundedLRU, read_pdk_decl
    from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
    from gmid_engine.pipeline import run_stage_a, run_stage_b
    from gmid_engine.search import SearchSettings, build_search_context, find_front, open_run
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, LutAccess

    loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
    man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
    kinds = dict(DEVICE_KINDS)
    from pdk_min_w import min_finger_w_m
    mins = min_finger_w_m(kinds.values())      # PDK 선언 양(card 20261104-wb1)
    dm = BoundedLRU(16)
    pdk = read_pdk_decl(str(SKILL / "assets" / "sky130_pdk_decl.json"), dm)
    q = dict(pdk.quantities)
    grid = float(man.get("manufacturing_grid_m", 5e-9))
    spec = LutSpec(grid, tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX,
                   noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
    lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_paths,
                       noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path, bin_rule=loc.bin_rule_path)
    rule = read_pdk_decl(str(SKILL / "assets" / "sky130_lut_rule_decl.json"), dm)
    settings = SearchSettings(a_.front_budget_s, a_.eval_budget, (1e2, 1e5), (("front_budget_s", "nfr4 run harness"),), (1e-13, 1e-10))
    note("lut loaded")

    normalize = []
    for raw, tag in ((str(work), "<WORK>"), (os.environ.get("TEMP", ""), "<TEMP>"), (os.environ.get("GMID_LUT_TABLE_CACHE_DIR", ""), "<CACHE>")):
        if raw:
            normalize += [(raw, tag), (raw.replace("\\", "/"), tag), (raw.replace("/", "\\"), tag)]
    d = Dump(sorted(set(normalize), key=lambda x: -len(x[0])))
    record = {"format": FORMAT, "circuit": a_.circuit, "code_fp": None, "searched": False, "env_fp": [],
              "eval_budget_source": None, "stops_wall_budget": None, "stop_values": [],
              "context": {"grid_m": float(q["manufacturing_grid_m"].value_m) if "manufacturing_grid_m" in q else grid,
                          "w_min_m": None, "rails": {}, "node_mos": {}, "mos_tol_v": {}},
              "threads_env": threads_env, "numpy_first": a_.numpy_first, "fields": d.fields}
    out_json = Path(a_.out_json)

    def save():
        stops = []
        for p, f in d.fields.items():
            segs = [s.split("[", 1)[0] for s in p.split("/")]
            if f["cls"] in ("D", "K") and isinstance(f["value"], str) and any(s in STOP_NAMES for s in segs):
                stops.append([p, f["value"]])
        record["stop_values"] = stops
        out_json.write_text(json.dumps(record, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    out = work / "out"
    # [XRUN-F1 card B C6·규칙 M M-c] 회로 실행 하나 = open_run 한 쌍. 단계 B 는 a 의 두 칸, 커널 컨텍스트는 같은 두 객체(card B 사슬)
    donors, counters = open_run()
    a = run_stage_a(LIBRARY / (a_.circuit + ".topology.json"), LIBRARY / (a_.circuit + ".sizing_spec.json"), lut, output_dir=out,
                    donors=donors, counters=counters)
    record["code_fp"] = a.code_fp
    report_a = json.loads(Path(a.report_paths[0]).read_text(encoding="utf-8"))
    record["env_fp"].append(["stage_a", report_a.get("env_fp")])
    d.walk("stage_a/report", report_a, "stage_a")
    if a.s1 is not None:
        d.put("stage_a/s1_snapshot_fp", "C", a.s1.snapshot.fp, "stage_a", {"kind": "unsourced"}, fp=True)
    note("stage A %s" % a.status)
    save()
    memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
    b = run_stage_b(a, memo, pdk, output_dir=out, diagnostic=True, settings=settings)
    report_b = json.loads(Path(b.report_paths[0]).read_text(encoding="utf-8"))
    d.walk("stage_b/report", report_b, "stage_b")
    if getattr(b, "s1", None) is not None:
        d.put("stage_b/s1_snapshot_fp", "C", b.s1.snapshot.fp, "stage_b", {"kind": "unsourced"}, fp=True)
    note("stage B %s" % b.status)
    save()
    snapshot = None
    if (a.status, b.status) == ("ok", "ok"):
        record["searched"] = True
        kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), LutAccess(memo), donors=a.donors, counters=a.counters)
        s3 = work / "s3"
        s3.mkdir(exist_ok=True)
        sctx = build_search_context(kctx, a.spec, settings, str(s3), pdk, rule, code_fp=a.code_fp)
        record["context"]["w_min_m"] = sctx.domain.w_min_m
        snapshot = sctx.dc.base
        note("search context")
        fr = find_front(sctx, [])
        note("find_front")
        perf = dict(fr.perf)
        record["eval_budget_source"] = perf.get("eval_budget_source")
        record["stops_wall_budget"] = perf.get("stops_wall_budget")
        for i, r in enumerate(seen["layer0"]):
            d.walk("layer0[%d]" % i if i else "layer0", r, "layer0")
        for i, sw in enumerate(seen["sweep"]):
            d.walk("sweep[%d]" % i if i else "sweep", sw, "sweep")
        d.walk("result", fr, "result")
        for r in sorted(sctx.cache.values(), key=lambda r: r.seq):
            d.eval_result("cache/%d" % r.seq, r, "eval:%d" % r.seq)
            if not record["context"]["rails"] and getattr(r, "evaluation", None) is not None:
                try:
                    record["context"]["rails"] = {k: float(v) for k, v in r.evaluation.snapshot.column("node", "dc_rail_v")}
                except (KeyError, AttributeError, TypeError, ValueError):
                    pass
        ctx_dir = s3 / sctx.context_fp
        for i, ln in enumerate(_lines(ctx_dir / "evals.jsonl")):
            d.walk("s3/evals[%d]" % i, ln, "s3evals:%d" % i)
        for i, ln in enumerate(_lines(ctx_dir / "runs.jsonl")):
            record["env_fp"].append(["runs", ln.get("env_fp")])
            d.walk("s3/runs[%d]" % i, ln, "s3runs")
    else:
        snapshot = (b.s1 or a.s1).snapshot if (getattr(b, "s1", None) or a.s1) is not None else None
    if snapshot is not None:
        for kind in snapshot.kinds():
            for key in snapshot.keys(kind):
                rec = snapshot.record(kind, key)
                for name in rec.field_names():
                    fv = rec.get(name)
                    p = "s0/%s/%s/%s" % (kind, key, name)
                    if _has_float(fv.value):
                        d.put(p, "C", fv.value_fp, "s0", _res_for(p), fp=True)
                    else:
                        d.put(p, "D", fv.value_fp, "s0")
                    d.put(p + "#writer", "D", str(fv.writer), "s0")
        d.put("s0/#snapshot_fp", "C", snapshot.fp, "s0", {"kind": "unsourced"}, fp=True)
    save()
    note("done fields=%d" % len(d.fields))
    return 0


if __name__ == "__main__":
    sys.exit(main())
