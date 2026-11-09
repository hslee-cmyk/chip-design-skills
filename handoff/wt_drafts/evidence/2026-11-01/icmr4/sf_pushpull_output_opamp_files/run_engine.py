"""sf_pushpull_output_opamp 엔진 실행 재현 (master HEAD, 소스 수정 0, library 경로 그대로).

단계 A -> B -> 커널 컨텍스트 -> 탐색 컨텍스트 -> layer0_start, 결과를 케이스마다 jsonl append.
인자: eval_budget(정수) [front 여부 'front'].
출력 폴더 = TEMP 고유 경로.
"""
import json, os, sys, time, tempfile, subprocess, traceback
from pathlib import Path

REPO = Path("C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills")
SKILL = REPO / "skills" / "analog-gmid-design"
sys.path.insert(0, str(SKILL))
HERE = Path(__file__).resolve().parent
OUT = HERE / "engine_runs.jsonl"
CIRCUIT = "sf_pushpull_output_opamp"
LIBRARY = SKILL / "assets" / "library"


def log(rec):
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


def main():
    eb = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    from gmid_engine.core import BoundedLRU, read_pdk_decl
    from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
    from gmid_engine.pipeline import run_stage_a, run_stage_b
    from gmid_engine.search import SearchSettings, build_search_context, layer0_start, open_run
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access
    loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
    man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
    kinds = {"nfet_01v8": "nmos", "pfet_01v8": "pmos"}
    mins = {}
    for e in man["slices"]:
        mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
    dm = BoundedLRU(16)
    pdk = read_pdk_decl(str(SKILL / "assets" / "sky130_pdk_decl.json"), dm)
    q = dict(pdk.quantities)
    spec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())),
                   (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos")), (("nmos", "_n"), ("pmos", "_p")),
                   noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
    lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                       noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
    rule = read_pdk_decl(str(SKILL / "assets" / "sky130_lut_rule_decl.json"), dm)
    settings = SearchSettings(300.0, eb, None, (("front_budget_s", "icmr4 evidence run (spec wall_clock 300)"),
                                               ("eval_budget", "icmr4 evidence run arg"),), None)
    out = Path(tempfile.mkdtemp(prefix="icmr4_sf_"))
    rec = {"case": f"layer0 eb={eb}", "head": head, "out_dir": str(out), "lut_manifest": loc.manifest_path}
    t0 = time.time()
    try:
        donors, counters = open_run()
        a = run_stage_a(LIBRARY / (CIRCUIT + ".topology.json"), LIBRARY / (CIRCUIT + ".sizing_spec.json"), lut,
                        output_dir=out, donors=donors, counters=counters)
        rec["stage_a"] = a.status
        memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
        b = run_stage_b(a, memo, pdk, output_dir=out, diagnostic=True, settings=settings)
        rec["stage_b"] = b.status
        kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo), donors=a.donors,
                                    counters=a.counters)
        sctx = build_search_context(kctx, a.spec, settings, None, pdk, rule, code_fp=a.code_fp)
        r = layer0_start(sctx)
        rec.update({"stop": r.stop, "start_is_none": r.start is None, "start_status": r.start_status,
                    "start_failure": repr(r.start_failure)[:3000], "probes": r.probes, "kernel_calls": r.kernel_calls,
                    "t": r.t, "hard_ok": r.hard_ok, "origin_point": r.origin_point})
    except Exception as exc:
        rec["exception"] = repr(exc)[:2000]
        rec["traceback"] = traceback.format_exc()[-4000:]
    rec["wall_s"] = round(time.time() - t0, 1)
    log(rec)
    print(json.dumps(rec, ensure_ascii=False, default=str)[:6000])


if __name__ == "__main__":
    main()
