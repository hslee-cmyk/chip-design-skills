"""plan v6.38.4 P4 실측 -- 층 0 점 없음 경로 출발점: as-built 출발 사다리 칸이 정하지 않아 `_box_centre`(상자 중심)·
`_current_centre`(Chebyshev 전류 중심)가 메우는 θ 성분을 library 9회로에서 센다(엔진 import·읽기만, 엔진 수정 0).

목적: 계획 규칙(DEC-104 R3·R4·R5'(2)·R6·R7, DEC-92 (3), R13 F 구간 선택점)이 각 성분의 writer를 정하는지 대조할 as-built gap 목록.
엔진 인용 용도 = 재작성 범위(as-built가 상자 중심으로 메우는 성분 = LA-1 이 규칙으로 대체해야 할 성분) -- 근거·본보기 아님(O-165 (b)).
결과는 회로마다 out.jsonl 에 append.
"""
import json, os, sys, traceback, types
sys.dont_write_bytecode = True
from pathlib import Path
from types import SimpleNamespace
ENG = Path("C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/skills/analog-gmid-design")
OUT = Path(__file__).parent / "uncovered.jsonl"
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
sys.path.insert(0, str(ENG)); sys.path.insert(0, str(ENG / "gmid_engine" / "tests" / "integration"))
sys.path.append("C:/Users/HSLEE/AppData/Roaming/Python/Python314/site-packages")
pt = types.ModuleType("pytest")
pt.fixture = lambda *a, **k: (a[0] if a and callable(a[0]) else (lambda f: f))
class _M:
    def __getattr__(self, n): return lambda *a, **k: (a[0] if a and callable(a[0]) else (lambda f: f))
pt.mark = _M(); sys.modules.setdefault("pytest", pt)
import test_s0_layer_9circuits as T
from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.search import open_run

loc = resolve_lut_location(str(T.SKILL / "assets" / "lut_v2_location.json"), os.environ)
man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
kinds = dict(T.DEVICE_KINDS); mins = {}
for e in man["slices"]:
    mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
pdk = read_pdk_decl(str(T.SKILL / "assets" / "sky130_pdk_decl.json"), BoundedLRU(16)); q = dict(pdk.quantities)
spec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), T.DEVICE_KINDS, T.CAP_SUFFIX,
               noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                   noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
RUNS = Path(os.environ.get("TEMP", "C:/tmp")) / "la1a_uncovered_runs"
env = SimpleNamespace(lut=lut, pdk=pdk, root=RUNS)

only = sys.argv[1:] or None
for c in sorted(p.name[:-len(".sizing_spec.json")] for p in T.LIBRARY.glob("*.sizing_spec.json")):
    if only and c not in only:
        continue
    row = {"circuit": c}
    try:
        donors, counters = open_run()
        kw = {}
        if c == "ngcc_3stage_ff":  # O-216 선언 내용을 TEMP 사본으로만(파일 작성 = card data 커밋)
            from gmid_engine.authoring import load_topology
            from gmid_engine.graph import structure_rule_fp
            topo = load_topology(str(T.LIBRARY / (c + ".topology.json")))
            st = {"schema_version": "1", "topology_hash": topo.connectivity_fp, "rule_hash": structure_rule_fp(), "facts": [
                {"concept": "dc_role", "subject": m, "value": "signal", "status": "ratified",
                 "evidence": {"rule": "TEMP O-216 content", "nets": ["V1", "gnd"]}, "approval_id": "TEMP-la1a-design"} for m in ("M8", "M14")]}
            (env.root / c).mkdir(parents=True, exist_ok=True)
            sp = env.root / c / (c + ".structure.json"); sp.write_text(json.dumps(st), encoding="utf-8")
            kw = {"structure_path": sp}
        a = run_stage_a(T.LIBRARY / (c + ".topology.json"), T.LIBRARY / (c + ".sizing_spec.json"), lut, output_dir=env.root / c,
                        donors=donors, counters=counters, **kw)
        row["stage_a"] = a.status
        if a.status != "ok":
            row["stop"] = repr(a.report.get("stop_reasons"))[:300]
            with OUT.open("ab") as fh:
                fh.write((json.dumps(row, ensure_ascii=False, default=repr) + "\n").encode("utf-8"))
            continue
        env.memo = LutMemo(lut, point=1 << 14, curve=1 << 12, root=1 << 14)
        b = run_stage_b(a, env.memo, pdk, output_dir=env.root / c, diagnostic=True, settings=T._settings())
        env.rule = read_pdk_decl(str(T.SKILL / "assets" / "sky130_lut_rule_decl.json"), BoundedLRU(4))
        sctx = T._search_context(env, a, b)
        variables = [v.component for v in sctx.domain.variables]
        row["n_theta_vars"] = len(variables)
        row["kinds"] = sorted({str(v[0]) for v in variables})
        row["r_vars"] = [str(v[1]) for v in variables if str(v[0]) == "resistance"]
        row["c_vars"] = [str(v[1]) for v in variables if str(v[0]) == "capacitance"]
        rungs = sctx.rungs
        row["n_rungs"] = None if rungs is None else len(rungs)
        per = []
        for k, rung in enumerate(rungs or (None,)):
            given = set() if rung is None else {comp for comp, _v in rung.theta}
            miss = [comp for comp in variables if comp not in given]
            bykind = {}
            for comp in miss:
                bykind.setdefault(str(comp[0]), []).append(str(comp[1]))
            per.append({"rung": k, "n_given": len(given), "n_missing": len(miss), "missing_by_kind": bykind})
        row["rungs"] = per
    except Exception:
        row["error"] = traceback.format_exc()[-1200:]
    with OUT.open("ab") as fh:
        fh.write((json.dumps(row, ensure_ascii=False, default=repr) + "\n").encode("utf-8"))
    print(c, "done", flush=True)
