"""IT-2a 감사 측정 하네스 v2 = v1 + 평가마다 지문 칸(eval_fps: snapshot_fp·dc_seal_report 값 지문·봉인 4 새 detail 키를 뺀 지문·부분 스냅샷 지문). v1 = IT-1 감사 하네스 measure_it1.py 복사본 + 블록 계수 칸 하나(block_counters: find_front 실행의 RunCounters 행) 추가 -- 측정 식 불변.
(아래는 원문) IT-1 감사 측정 하네스(IT-0 measure_it0.py 복사본, HEAD 어휘에 맞춘 치환 5곳만 -- 측정 식 불변). 원문: IT-0 기준선 측정 하네스(감사 측정 전용 -- 엔진 모듈이 아니다, 엔진 소스를 고치지 않는다).

usage: python -I measure_it0.py <repo_root> <side AB|SIM> <circuit> <set library|heldout> <out_dir> [--nowrap] [--tag T] [--eval-budget 40]

- 사슬(tests/integration/nfr4_run_dump.py 와 같은 공개 API): run_stage_a -> run_stage_b(diagnostic) -> build_kernel_context -> build_search_context
  -> find_front(sctx, []). heldout 은 OS 칸만(단계 A 스냅샷 + 쓰기 계획 시도).
- 관찰 래퍼(반환값을 바꾸지 않는다): find_front 모듈 속성 layer0_start(결과 기록), block_columns 모듈 속성 _solve_input_window·_interior_solution·
  _refine_ends·k_max 와 _Circuit.input_windows(호출·반환 기록), authoring input_terminal_nets(호출 수). --nowrap 이면 하나도 깔지 않는다(래퍼 무해 확인).
- 커널 창 상태 판정 식(관찰한 windows/again 열과 tol 을 as-built 와 같은 식으로 비교 -- 원문 block_columns.py `_solve_input_window`):
    settled = all(abs(a - b) <= tol for root in roots for a, b in zip(again[root], windows[root]))      # block_columns.py:725 (c237d96e)
    again is None -> break                                                                                   # block_columns.py:723-724
    tol = c.tolerance(...) 가 SealViolationError -> 창 한 번 적용(k_max 루프 없음)                         # block_columns.py:714-718
    windows is None 이고 _interior_solution None -> 종래 사상                                               # block_columns.py:708-712
- 결과: <out_dir>/<side>/<circuit>.json(회로 하나 전부) + <out_dir>/cases.jsonl(칸마다 한 줄 즉시 append).
"""
import argparse
import dataclasses
import enum
import json
import math
import os
import sys
import time
from pathlib import Path

DEBUG_PATH = os.environ.get("IT0_DEBUG")
ICMR_METRICS = ("icm_margin_v", "icmr_v", "required_input_cm_v")


def J(x, depth=0):
    if depth > 40:
        return repr(x)
    if x is None or isinstance(x, (bool, int, str)):
        return x
    if isinstance(x, float):
        return x if math.isfinite(x) else repr(x)
    if isinstance(x, enum.Enum):
        return x.value
    if dataclasses.is_dataclass(x) and not isinstance(x, type):
        return {f.name: J(getattr(x, f.name), depth + 1) for f in dataclasses.fields(x)}
    if hasattr(x, "_asdict"):
        return {k: J(v, depth + 1) for k, v in x._asdict().items()}
    if isinstance(x, dict):
        return [[J(k, depth + 1), J(v, depth + 1)] for k, v in sorted(x.items(), key=lambda kv: repr(kv[0]))]
    if isinstance(x, (tuple, list)):
        return [J(v, depth + 1) for v in x]
    if isinstance(x, (set, frozenset)):
        return sorted((J(v, depth + 1) for v in x), key=repr)
    return repr(x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo"); ap.add_argument("side"); ap.add_argument("circuit"); ap.add_argument("set"); ap.add_argument("out")
    ap.add_argument("--nowrap", action="store_true"); ap.add_argument("--tag", default="")
    ap.add_argument("--eval-budget", type=int, default=40)
    a_ = ap.parse_args()
    skill = Path(a_.repo) / "skills" / "analog-gmid-design"
    sys.path.insert(0, str(skill))
    sys.path.append("C:/Users/HSLEE/AppData/Roaming/Python/Python314/site-packages")   # numpy/scipy (-I drops user site)
    out_root = Path(a_.out)
    side_dir = out_root / (a_.side + a_.tag)
    side_dir.mkdir(parents=True, exist_ok=True)
    cases = out_root / "cases.jsonl"
    rec = {"circuit": a_.circuit, "side": a_.side, "set": a_.set, "tag": a_.tag, "wrapped": not a_.nowrap, "repo": str(a_.repo)}
    out_json = side_dir / (a_.circuit + ".json")

    def save():
        out_json.write_text(json.dumps(rec, ensure_ascii=False, sort_keys=True, indent=1), encoding="utf-8")

    def case(col, value):
        rec[col] = value
        with cases.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"circuit": a_.circuit, "side": a_.side + a_.tag, "col": col, "value": value,
                                "t": time.strftime("%Y-%m-%dT%H:%M:%S")}, ensure_ascii=False, sort_keys=True) + "\n")
        save()

    import gmid_engine.search  # noqa: F401
    import gmid_engine.sizing.block_columns; bc = sys.modules['gmid_engine.sizing.block_columns']
    import gmid_engine.sizing.input_window; iwm = sys.modules['gmid_engine.sizing.input_window']
    import gmid_engine.sizing.writer_plan; wp = sys.modules['gmid_engine.sizing.writer_plan']
    import gmid_engine.search.find_front; ff = sys.modules['gmid_engine.search.find_front']
    from gmid_engine.core import BoundedLRU, read_pdk_decl, fp_of, SealViolationError, StructureUnresolvedError
    from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
    from gmid_engine.pipeline import run_stage_a, run_stage_b
    from gmid_engine.search import SearchSettings, build_search_context, find_front, open_run
    from gmid_engine.search.kernel import evaluate
    from gmid_engine.search.pareto import nondominated
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access, DC_KEY
    from gmid_engine.sizing import s2_values as sv
    from gmid_engine.authoring import INPUT_DIRECTION
    import gmid_engine.authoring._feedback_cuts; fcm = sys.modules['gmid_engine.authoring._feedback_cuts']

    # ------------------------------------------------------------ 관찰 래퍼
    ST = {"collect": False, "kw": [], "rec": None, "ltn": {"stage_a": 0, "after_stage_a": 0}, "phase": "stage_a",
          "layer0": [], "sens": False}
    if not a_.nowrap:
        orig_l0 = ff.layer0_start

        def l0(*args, **kw):
            r = orig_l0(*args, **kw)
            ST["layer0"].append(r)
            return r
        ff.layer0_start = l0

        orig_itn = fcm.input_terminal_nets

        def itn(*args, **kw):
            ST["ltn"][ST["phase"]] += 1
            return orig_itn(*args, **kw)
        for name, mod in list(sys.modules.items()):
            if name.startswith("gmid_engine") and getattr(mod, "input_terminal_nets", None) is orig_itn:
                setattr(mod, "input_terminal_nets", itn)

        orig_siw, orig_int, orig_ref, orig_kmax = bc._solve_input_window, bc._interior_solution, bc._refine_ends, bc.k_max
        orig_iwin = bc._Circuit.input_windows

        def iwin(self, values, roots):
            r = orig_iwin(self, values, roots)
            R = ST["rec"]
            if R is not None:
                label = {"first": "first", "post_first": "loop"}.get(R["phase"], R["phase"])
                R["iw"].append((label, None if r is None else {k: tuple(v) for k, v in r.items()}))
                if R["phase"] == "first":
                    R["phase"] = "post_first"
            return r

        def interior(c, key, requested):
            R = ST["rec"]
            if R is not None:
                R["phase"] = "interior"
            r = orig_int(c, key, requested)
            if R is not None:
                R["interior"] = "none" if r is None else "found"
                R["interior_windows"] = None if r is None else {k: tuple(v) for k, v in r[2].items()}
                R["phase"] = "post_first"
            return r

        def refine(c, roots, windows, tol):
            R = ST["rec"]
            if R is not None:
                R["phase"] = "refine"
                R["refine"] = True
                R["tol"] = tol                                   # _solve_input_window 이 넘긴 tol 그대로
                R["kmax"] = orig_kmax(c.hi - c.lo, tol)          # block_columns.py:719 range(k_max(c.hi - c.lo, tol)) 와 같은 인자
            return orig_ref(c, roots, windows, tol)

        def kmax(width, tol):
            return orig_kmax(width, tol)

        def siw(c):
            roots = tuple(c.input_roots())
            R = {"roots": roots, "phase": "first", "iw": [], "interior": None, "refine": False, "kmax": None, "tol": None}
            prev = ST["rec"]
            ST["rec"] = R
            try:
                values, logs = orig_siw(c)
            finally:
                ST["rec"] = prev
            st = classify(R)
            st["trace"] = repr({k: (v if k != "iw" else [(ph, w is None) for ph, w in v]) for k, v in R.items() if k != "interior_windows"})[:600]
            if DEBUG_PATH:
                with open(DEBUG_PATH, "a", encoding="utf-8") as fdbg:
                    fdbg.write(repr({k: (v if k != "iw" else [(ph, w is None) for ph, w in v]) for k, v in R.items()}) + " " + " " + st["status"] + chr(10))
            if ST["sens"] and roots:
                unknown = tuple(net for net, w in c.canonical_writers() if w.relation not in bc.FIXED_RELATIONS)
                sl = {}
                for r in roots:
                    try:
                        s = iwm._sensitivities(unknown, r, values, c.writer_grad)
                    except SealViolationError as e:
                        s = "SealViolationError"
                    sl[r] = s
                st["slopes"] = sl
                st["values"] = {k: float(v) for k, v in values.items()}
            if ST["collect"]:
                ST["kw"].append(st)
            return values, logs

        bc._Circuit.input_windows = iwin
        bc._interior_solution, bc._refine_ends, bc.k_max, bc._solve_input_window = interior, refine, kmax, siw

    def classify(R):
        if not R["roots"]:
            return {"status": "no_root", "roots": []}
        first = [w for ph, w in R["iw"] if ph == "first"]
        interior = R["interior"] == "found"
        if R["interior"] == "none":
            return {"status": "unmeasured", "roots": list(R["roots"]), "interior": False}
        windows = R["interior_windows"] if interior else (first[-1] if first else None)
        if windows is None:
            return {"status": "unmeasured_unclassified", "roots": list(R["roots"])}
        if not R["refine"]:
            return {"status": "tol_undefined", "roots": list(R["roots"]), "interior": interior}
        loop = [w for ph, w in R["iw"] if ph == "loop"]
        tol = R["tol"]
        it = 0
        for again in loop:
            it += 1
            if again is None:
                return {"status": "remeasure_failed", "roots": list(R["roots"]), "interior": interior, "iterations": it, "k_max": R["kmax"]}
            settled = all(abs(a - b) <= tol for root in R["roots"] for a, b in zip(again[root], windows[root]))
            windows = again
            if settled:
                return {"status": "settled", "roots": list(R["roots"]), "interior": interior, "iterations": it, "k_max": R["kmax"]}
        return {"status": "k_max_exhausted" if it == R["kmax"] else "loop_ended_unclassified", "roots": list(R["roots"]),
                "interior": interior, "iterations": it, "k_max": R["kmax"]}

    # ------------------------------------------------------------ 입력
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
    grid = float(man.get("manufacturing_grid_m", 5e-9))
    lspec = LutSpec(grid, tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX,
                    noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
    lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, lspec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                       noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
    rule = read_pdk_decl(str(skill / "assets" / "sky130_lut_rule_decl.json"), dm)
    settings = SearchSettings(7200.0, a_.eval_budget, (1e2, 1e5), (("front_budget_s", "it0 harness"),), (1e-13, 1e-10))

    base_dir = skill / "assets" / a_.set
    work = side_dir / ("work_" + a_.circuit)
    work.mkdir(parents=True, exist_ok=True)
    donors, counters = open_run()
    t0 = time.perf_counter()
    a = run_stage_a(base_dir / (a_.circuit + ".topology.json"), base_dir / (a_.circuit + ".sizing_spec.json"), lut,
                    output_dir=work, donors=donors, counters=counters)
    ST["phase"] = "after_stage_a"
    rec["stage_a"] = {"status": a.status, "exit_code": a.exit_code}
    save()
    if a.s1 is None or a.spec is None:
        case("output_structure", {"engine": "stage_a_" + a.status, "value": None})
        return
    s1snap = a.s1.snapshot
    inputs_decl = dc_inputs_from_spec(a.spec)
    rails = {n for n, r in s1snap.column("node", "is_rail") if r}
    pdir = dict(s1snap.column("node", "port_direction"))
    in_ports = sorted(n for n, d in pdir.items() if d == INPUT_DIRECTION)
    out_ports = sorted(n for n, d in pdir.items() if d == "output")
    w3 = {n for n, _v in inputs_decl.node_targets}
    in_dc_declared = inputs_decl.input_dc_v is not None
    classes = dict(s1snap.column("device", "element_class"))
    kinds = dict(s1snap.column("device", "kind"))
    pins = dict(s1snap.column("device", "pins"))
    diode = dict(s1snap.column("device", "is_diode"))
    try:
        dcol = dict(s1snap.column("device", "dc_colour"))
    except Exception:
        dcol = {n: 0 for n in classes}
    edges_no_tie = wp._edges(classes, kinds, pins, diode, dcol, sv.NO_ORDER_HINTS)

    # ------------------------------------------------------------ 쓰기 계획(AB/SIM)
    b = None
    kctx = None
    plan_stop = None
    if a.status == "ok":
        memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
        b = run_stage_b(a, memo, pdk, output_dir=work, diagnostic=True, settings=settings)
        rec["stage_b"] = {"status": b.status, "exit_code": getattr(b, "exit_code", None)}
        save()
        access = pre_layout_lut_access(memo)
        try:
            kctx = build_kernel_context(b.s1, inputs_decl, access, donors=a.donors, counters=a.counters)
        except StructureUnresolvedError as e:
            plan_stop = J(getattr(e, "detail", None)) or repr(e)
    else:
        plan_stop = "stage_a_" + a.status
    writers = dict(kctx.base.column("node", "dc_writer")) if kctx is not None else None

    # ------------------------------------------------------------ OS (D41 4.7-1a 측정 oracle)
    fprime = set(rails) | (set(in_ports) if in_dc_declared else set())
    adj = {}
    for _key, rank, name, x, y in edges_no_tie:
        adj.setdefault(x, []).append((rank, name, y))
        adj.setdefault(y, []).append((rank, name, x))
    os_rows = []
    fb = getattr(a.spec, "feedback", None)
    fb_kind = "tuple_nonempty" if isinstance(fb, tuple) and fb else ("empty_tuple" if fb == () else repr(type(fb).__name__) + ":" + repr(fb)[:80])
    for o in out_ports:
        if o not in adj:
            cls, comp, hit = "high_impedance", [o], []
        else:
            seen, queue = {o}, [o]
            while queue:
                u = queue.pop(0)
                for _r, _n, v in adj.get(u, ()):
                    if v not in seen:
                        seen.add(v)
                        queue.append(v)
            hit = sorted(seen & fprime)
            cls = "kvl_fixed" if hit else "high_impedance"
            comp = sorted(seen)
        sos1 = None
        chain = []
        if writers is not None and cls == "high_impedance":
            n = o
            while n is not None and n in writers and len(chain) < 200:
                chain.append([n, writers[n].tier, writers[n].relation])
                n = writers[n].known
            root = chain[-1][0] if chain else None
            sos1 = bool(root is not None and root != o and root in w3)
        os_rows.append({"output": o, "class": cls, "w3": o in w3, "component_size": len(comp), "fprime_hit": hit,
                        "engine_path": "plan_ok" if writers is not None else {"stop": plan_stop},
                        "writer_chain": chain, "s_os1": sos1})
    w3_hard_mos = sum(1 for r in os_rows if r["w3"] and r["class"] == "kvl_fixed")
    case("output_structure", {"rows": os_rows, "n_outputs": len(out_ports), "w3_declared": sorted(w3),
                              "w3_outputs_on_hard_path": w3_hard_mos, "input_dc_declared": in_dc_declared,
                              "spec_feedback_kind": fb_kind,
                              "s_os2_tuple": bool(len(out_ports) >= 2 and isinstance(fb, tuple) and len(fb) > 0),
                              "s_os2_empty": bool(len(out_ports) >= 2 and fb == ()),
                              "plan_stop": plan_stop})
    if a_.set != "library" or kctx is None:
        rec["wall_s"] = time.perf_counter() - t0
        save()
        return

    base = kctx.base
    coords = dict(base.column("device", "dc_coord"))
    ties = base.value("graph", DC_KEY, "dc_tie_breaks")
    fixed = {n for n, w in writers.items() if w.relation in (sv.REL_RAIL, sv.REL_TARGET, sv.REL_INPUT_DC)}
    free_inputs = tuple(n for n in in_ports if n not in fixed)
    # ------------------------------------------------------------ M-I1 / M-I1-r / M-I6 / M-I7 원자료
    dep = {m: c.dependency if hasattr(c, "dependency") else J(c) for m, c in coords.items()}
    w4 = {n: w.y_key for n, w in writers.items() if w.relation == sv.REL_WINDOW}
    w4_roots = {n: y for n, y in w4.items()}
    port_writer = {p: [writers[p].tier, writers[p].relation, writers[p].element, writers[p].known, writers[p].y_key] for p in in_ports}
    m_i1 = {"writers": J(writers), "coords": J(coords), "tie_breaks": J(ties),
            "dependent": sorted([m, J(c)] for m, c in coords.items() if getattr(c, "role", None) == sv.COORD_DEPENDENT),
            "w4": sorted([n, y] for n, y in w4_roots.items()), "input_port_writer": port_writer,
            "fields_fp": {"dc_writer": fp_of(J(writers)), "dc_coord": fp_of(J(coords)), "dc_tie_breaks": fp_of(J(ties))}}
    edge_nets = {x for _k, _r, _n, x, _y in edges_no_tie} | {y for _k, _r, _n, _x, y in edges_no_tie}
    in_roots = [p for p in in_ports if p in w4_roots]
    m_i1r = {"input_w4_roots": in_roots, "multi_root": len(in_roots) >= 2, "n_input_w4_roots": len(in_roots),
             "isolated_input": [p for p in free_inputs if p not in edge_nets],
             "f_component_undeclared": [p for p in free_inputs if writers[p].relation not in (sv.REL_WINDOW, getattr(sv, 'REL_TIE', '<absent>'))]}
    # M-I6: 쓰기 계획 _edges 출력 그대로(AB = free_inputs 포함 _TIE, SIM = 패치된 dc_writer_plan 과 같은 () 입력)
    edges = wp._edges(classes, kinds, pins, diode, dict(base.column("device", "dc_colour")), sv.NO_ORDER_HINTS)
    F = ("<F>",)
    vmap = lambda n: F if n in fixed else n
    par = {}

    def find(x):
        while par.setdefault(x, x) != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    verts = set()
    for _k, _r, _n, x, y in edges:
        x, y = vmap(x), vmap(y)
        verts |= {x, y}
        par[find(x)] = find(y)
    ncomp = len({find(v) for v in verts})
    cyc = len(edges) - len(verts) + ncomp
    ndep = sum(1 for c in coords.values() if getattr(c, "role", None) == sv.COORD_DEPENDENT)
    m_i6 = {"E": len(edges), "V": len(verts), "components": ncomp, "cycles": cyc, "dependent": ndep, "equal": cyc == ndep,
            "tie_edges": sum(1 for e in edges if e[1] == getattr(wp, "_TIE", "<absent>"))}
    case("m_i1", m_i1); case("m_i1_r", m_i1r); case("m_i6", m_i6)

    # ------------------------------------------------------------ C2 / C3
    if DEBUG_PATH:
        with open(DEBUG_PATH, "a", encoding="utf-8") as fdbg:
            fdbg.write("DBGV %r" % ([(k, [(getattr(x, "mode", None), getattr(x, "kind", None)) for x in v]) for k, v in base.column("graph", "views")],))
    views = []
    for cdecl in getattr(a.spec, "constraints", ()):
        v = getattr(cdecl, "view", None)
        if v is not None and v not in views:
            views.append(v)
    acg = {n for n, c in base.column("node", "ac_ground_class") if c is not None}
    allowed = acg | set(in_ports)
    c2 = []
    for v in views:
        mode = getattr(v, "mode", None)
        if mode == "transfer":
            pairs = v.transfer.ac_excite
        elif mode in ("port", "loop") and getattr(v, "sense", None) is not None and not getattr(v, "cuts", ()):
            pairs = v.weights
        else:
            continue
        nets = sorted({n for n, _a in pairs})
        bad = [n for n in nets if n not in allowed]
        c2.append({"view": repr(v)[:200], "mode": mode, "pair_nets": nets, "outside": bad})
    case("drive_pair_nets", {"views": c2, "n_views": len(c2), "failing_views": sum(1 for r in c2 if r["outside"])})

    sctx = build_search_context(kctx, a.spec, settings, None, pdk, rule, code_fp=a.code_fp)
    nd = sctx.noise_decl
    fbv = getattr(nd, "feedback", "NO_ATTR")
    case("feedback_slot", {"noise_decl_feedback": J(fbv),
                           "kind": "tuple_nonempty" if isinstance(fbv, tuple) and fbv else ("empty_tuple" if fbv == () else ("None" if fbv is None else "other")),
                           "spec_feedback": J(fb)[:300] if isinstance(J(fb), str) else J(fb)})
    ach = b.s1.snapshot if hasattr(b.s1, "snapshot") else None
    try:
        from gmid_engine.metrics import ACH_KEY
        dof = ach.value("graph", ACH_KEY, "dof")
    except Exception as e:
        dof = "unreadable:" + repr(e)[:200]
    m_i5 = {"dof": J(dof), "tie_equations": sum(1 for w in writers.values() if w.relation == getattr(sv, 'REL_TIE', '<absent>') and w.known is not None)}
    case("m_i5", m_i5)

    # [IT-2a 감사 v2] 평가마다 지문(관찰만, 반환값 그대로): search.kernel.evaluate 를 이름으로 가진 모듈 속성을 감싼다
    import hashlib
    import gmid_engine.search.kernel as skm
    FP = {"on": False, "rows": []}
    NEW_KEYS = ("foreign_writers", "base_call_overlap")

    def jh(x):
        return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()

    def strip_new(jrep):
        if isinstance(jrep, dict):
            return {k: strip_new(v) for k, v in jrep.items()}
        if isinstance(jrep, list):
            return [strip_new(v) for v in jrep if not (isinstance(v, list) and len(v) == 2 and v[0] in NEW_KEYS)]
        return jrep

    def snap_row(snap):
        if snap is None:
            return None
        try:
            rep = snap.value("graph", DC_KEY, "dc_seal_report")
        except Exception as e:
            return {"snapshot_fp": snap.fp, "report": "unreadable:" + type(e).__name__}
        jr = J(rep)
        return {"snapshot_fp": snap.fp, "report_value_fp": jh(jr), "report_fp_without_new_keys": jh(strip_new(jr))}
    orig_eval = skm.evaluate

    def ev_wrap(*args, **kw):
        r = orig_eval(*args, **kw)
        if FP["on"]:
            FP["rows"].append({"status": r.status, "theta_hex": list(r.key.theta_hex),
                               "evaluation": snap_row(None if r.evaluation is None else r.evaluation.snapshot),
                               "partial": snap_row(r.partial)})
        return r
    for name, mod in list(sys.modules.items()):
        if name.startswith("gmid_engine") and getattr(mod, "evaluate", None) is orig_eval:
            setattr(mod, "evaluate", ev_wrap)
    FP["on"] = True
    # ------------------------------------------------------------ find_front (KW 수집)
    ST["collect"] = True
    fr = find_front(sctx, [])
    ST["collect"] = False
    kw_main = list(ST["kw"])
    ST["kw"] = []
    l0 = ST["layer0"][0] if ST["layer0"] else None
    m_i2 = None if l0 is None else {
        "start": None if l0.start is None else {"theta": J(l0.start.theta), "cells": J(l0.start.cells)},
        "stop": l0.stop, "t": l0.t, "hard_ok": l0.hard_ok, "start_status": l0.start_status,
        "start_failure": J(l0.start_failure)[:2000] if isinstance(J(l0.start_failure), str) else J(l0.start_failure),
        "probes": l0.probes, "origin_point": l0.origin_point, "kernel_calls": l0.kernel_calls}
    case("m_i2", m_i2 if m_i2 is not None else "unwrapped")

    def pt(p):
        r = p.result
        return {"point_id": p.point_id, "status": r.status, "theta": [[list(k), float(v).hex()] for k, v in r.theta],
                "cells": list(r.key.cells), "power_w": float(r.objectives.power_w).hex(), "area_m2": float(r.objectives.area_m2).hex()}
    fronts = {"front": [pt(p) for p in fr.front], "pending": [pt(p) for p in fr.pending_front],
              "unmeasured": [pt(p) for p in fr.unmeasured_front]}
    ykeys = sorted({k[1] for p in fr.front + fr.pending_front + fr.unmeasured_front for k, _v in p.result.theta if k[0] == sv.THETA_Y})
    dom_y = [J(v.component) for v in sctx.domain.variables if v.component[0] == sv.THETA_Y]
    dties = getattr(sctx.domain, "ties", None)
    y_tied = sorted({J(m) for _rep, mem in (dties or ()) for m in mem if m[0] == sv.THETA_Y}, key=repr)
    m_i3 = {"n_front": len(fr.front), "n_pending": len(fr.pending_front), "n_unmeasured": len(fr.unmeasured_front),
            "front_fp": fp_of(fronts), "fronts": fronts, "result_y_keys": ykeys, "theta_y_components": dom_y,
            "n_theta_y": len(dom_y), "domain_tied_y": y_tied, "failed_eps": len(fr.failed_eps),
            "perf": {k: v for k, v in fr.perf if isinstance(v, (int, float, str)) and k != "wall_s"}}
    case("m_i3", m_i3)
    FP["on"] = False
    case("eval_fps", {"n": len(FP["rows"]), "rows": FP["rows"]})
    pc = a.counters.snapshot()       # [IT-2a 감사 추가] find_front 실행(단계 A~find_front 같은 RunCounters)의 블록 계수 행
    case("block_counters", {"rows": [[r.block, r.part, r.calls, r.reuses, r.grafts, r.replays, r.computes, r.recomputes_same_input] for r in pc.blocks],
                            "totals": J(pc.block_totals)})
    statuses = {}
    for s in kw_main:
        statuses[s["status"]] = statuses.get(s["status"], 0) + 1
    if in_dc_declared:
        kwv = {"defined": False, "reason": "정의 안 됨(as-built 창 없음 -- 입력 DC 선언, O-72 (3))", "counts": statuses, "n_evals": len(kw_main)}
    else:
        kwv = {"defined": True, "counts": statuses, "n_evals": len(kw_main), "trace_first3": [s.get("trace") for s in kw_main[:3]],
               "n_with_root": sum(1 for s in kw_main if s["status"] != "no_root"),
               "interior_aux": sum(1 for s in kw_main if s.get("interior")),
               "rates": {k: v / len(kw_main) for k, v in statuses.items()} if kw_main else {}}
    case("kernel_window_status", kwv)

    # ------------------------------------------------------------ 재평가(FE·M-I4·SP): 새 실행 컨텍스트에서 front 점·θ0 봉인점
    def fresh():
        d2, c2_ = open_run()
        k2 = build_kernel_context(b.s1, inputs_decl, access, donors=d2, counters=c2_)
        return build_search_context(k2, a.spec, settings, None, pdk, rule, code_fp=a.code_fp)

    def node_tols(snap):
        try:
            j = snap.value("graph", DC_KEY, "dc_seal_1")
        except Exception as e:
            return None, "unreadable:" + repr(e)[:120]
        rows = getattr(j, "rows", None)
        if rows is None:
            return None, "no_rows_attr:" + type(j).__name__
        out = {}
        for r in rows:
            r = tuple(getattr(r, "_fields", None) and tuple(r) or r) if not isinstance(r, tuple) else r
            out[r[0]] = r[2] if len(r) > 2 else None
        return out, None

    def reeval(theta, cells, label):
        if a_.nowrap:
            return {"label": label, "skipped": "nowrap"}
        sc = fresh()
        ST["collect"], ST["sens"], ST["kw"] = True, True, []
        try:
            res = evaluate(sc, dict(theta), tuple(cells))
        finally:
            ST["collect"], ST["sens"] = False, False
        kws = ST["kw"]
        ST["kw"] = []
        out = {"label": label, "status": res.status, "kw": [s["status"] for s in kws]}
        snap = None if res.evaluation is None else res.evaluation.snapshot
        if snap is not None:
            dcv = dict(snap.column("node", "dc_v"))
            tols, why = node_tols(snap)
            pairs = []
            for i, p in enumerate(in_ports):
                for qn in in_ports[i + 1:]:
                    if p in dcv and qn in dcv:
                        diff = abs(dcv[p] - dcv[qn])
                        tp, tq = (None, None) if tols is None else (tols.get(p), tols.get(qn))
                        tl = [t for t in (tp, tq) if t is not None]
                        if tl:
                            exceed = diff > max(tl)
                        else:
                            exceed = dcv[p] != dcv[qn]
                        pairs.append({"p": p, "q": qn, "diff": diff, "tol_p": tp, "tol_q": tq, "exceed": exceed,
                                      "rule": "max_tol" if tl else "bit_identical"})
            out["port_pairs"] = pairs
            out["tol_source"] = why or "graph/dc_seal_1 rows"
        sp = []
        for s in kws:
            for r, sl in (s.get("slopes") or {}).items():
                for p in in_ports:
                    if p == r or p in s["roots"]:
                        continue
                    if isinstance(sl, dict) and p in sl:
                        sp.append({"root": r, "port": p, "dVp_dx": sl[p], "sign": (sl[p] > 0) - (sl[p] < 0)})
                    elif sl is None or isinstance(sl, str):
                        sp.append({"root": r, "port": p, "dVp_dx": None, "why": "singular" if sl is None else sl})
        out["s_p"] = sp
        return out

    re_front = [reeval(dict(p.result.theta), p.result.key.cells, "front:%s" % p.point_id) for p in fr.front]
    re_l0 = [] if (l0 is None or l0.start is None) else [reeval(dict(l0.start.theta), l0.start.cells, "theta0_layer0")]
    rec["reeval"] = {"front": re_front, "theta0": re_l0}
    save()
    # M-I4
    exceed_pts = [r["label"] for r in re_front + re_l0 if any(pp["exceed"] for pp in r.get("port_pairs", ()))]
    case("m_i4", {"points": len(re_front) + len(re_l0), "exceed_points": exceed_pts, "has_diff": bool(exceed_pts),
                  "pairs": {r["label"]: r.get("port_pairs") for r in re_front + re_l0}})
    neg = [[r["label"], s] for r in re_front + re_l0 for s in r["s_p"] if s.get("sign") == -1]
    case("s_p_sign", {"rows": {r["label"]: r["s_p"] for r in re_front + re_l0}, "negative": neg, "o49_p2_fires": bool(neg)})
    # FE
    icmr = sorted({getattr(d, "metric", None) for d in sctx.ss_constraints} & set(ICMR_METRICS))
    excl, excl_aux = set(), set()
    for p, r in zip(fr.front, re_front):
        sts = set(r.get("kw", ()))
        if icmr and sts & {"tol_undefined", "k_max_exhausted"}:
            excl.add(p.point_id)
        if icmr and sts & {"tol_undefined", "k_max_exhausted", "unmeasured"}:
            excl_aux.add(p.point_id)

    def refilter(ex):
        pool = [p for p in fr.front if p.point_id not in ex]
        pts = tuple((p.point_id, (p.result.objectives.power_w, p.result.objectives.area_m2),
                     sum(rr.c for rr in p.result.constraints if rr.active)) for p in pool)
        b_p = {p.point_id: p.result.objectives.power_resolution_w for p in pool}
        res = nondominated(pts, (lambda x, y: max(b_p[x], b_p[y]), sctx.domain.area_resolution_m2))
        return len(res.kept)
    case("front_empty", {"icmr_constraints": icmr, "n_front": len(fr.front), "excluded": sorted(excl),
                         "after_refilter": refilter(excl) if fr.front else 0,
                         "empty": bool(fr.front) and refilter(excl) == 0,
                         "aux_unmeasured_excluded": sorted(excl_aux), "aux_after": refilter(excl_aux) if fr.front else 0,
                         "front_was_empty_before": not fr.front,
                         "undefined_for_report": [] if icmr else [r["label"] for r in re_front if set(r.get("kw", ())) & {"tol_undefined", "k_max_exhausted"}]})
    case("loop_cut", {"input_terminal_nets_calls": dict(ST["ltn"]), "wrapped": not a_.nowrap,
                      "interval": "build_kernel_context..find_front..재평가 전 구간(dc_writer_plan·run_kernel·seal_dc 구간을 포함하는 상위 구간)"})
    rec["wall_s"] = time.perf_counter() - t0
    save()


if __name__ == "__main__":
    main()
