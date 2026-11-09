"""ngcc_3stage_ff 단계 A·B(diagnostic) 실행 -- master HEAD 엔진, library 경로 그대로, 소스 수정 0.
usage: python run_stage_ab.py <circuit> <work_dir> <log_file>
결과: work_dir/out/<circuit>.stage_a.json·stage_b.json, log_file 에 케이스마다 append.
LUT 로드 = nfr4_run_dump.py 와 같은 경로(load_lut_set verify_midpoints -- sha 대조 포함).
"""
import json
import os
import sys
import time
import traceback
from pathlib import Path

SKILL = Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
LIBRARY = SKILL / "assets" / "library"
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))


def main():
    circuit, work, logf = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    work.mkdir(parents=True, exist_ok=True)

    def log(msg):
        with open(logf, "a", encoding="utf-8") as f:
            f.write("%s [%s] %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), circuit, msg))

    sys.path.insert(0, str(SKILL))
    from gmid_engine.core import BoundedLRU, read_pdk_decl
    from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
    from gmid_engine.pipeline import run_stage_a, run_stage_b
    from gmid_engine.search import SearchSettings, open_run

    loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
    log("lut manifest=%s" % loc.manifest_path)
    man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
    kinds = dict(DEVICE_KINDS)
    mins = {}
    for e in man["slices"]:
        mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
    dm = BoundedLRU(16)
    pdk = read_pdk_decl(str(SKILL / "assets" / "sky130_pdk_decl.json"), dm)
    q = dict(pdk.quantities)
    grid = float(man.get("manufacturing_grid_m", 5e-9))
    spec = LutSpec(grid, tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX,
                   noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
    lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                       noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
    log("lut loaded (verify_midpoints=%s)" % loc.midpoints_path)
    settings = SearchSettings(300.0, 40, (1e2, 1e5), (("front_budget_s", "icmr4 diag run"),), (1e-13, 1e-10))
    out = work / "out"
    donors, counters = open_run()
    try:
        a = run_stage_a(LIBRARY / (circuit + ".topology.json"), LIBRARY / (circuit + ".sizing_spec.json"), lut, output_dir=out,
                        donors=donors, counters=counters)
    except Exception:
        log("stage A EXC\n" + traceback.format_exc())
        raise
    ra = json.loads(Path(a.report_paths[0]).read_text(encoding="utf-8"))
    log("stage A status=%s exit=%s code_fp=%s" % (a.status, a.exit_code, a.code_fp))
    for k in ("stop_reasons", "review_needed", "declared_comparison"):
        log("stage A %s = %s" % (k, json.dumps(ra.get(k), ensure_ascii=False)))
    memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
    try:
        b = run_stage_b(a, memo, pdk, output_dir=out, diagnostic=True, settings=settings)
        rb = json.loads(Path(b.report_paths[0]).read_text(encoding="utf-8"))
        log("stage B status=%s exit=%s diag=%s" % (b.status, b.exit_code, b.diagnostic))
        log("stage B stop_reasons = %s" % json.dumps(rb.get("stop_reasons"), ensure_ascii=False))
        ach = rb.get("achievability") or {}
        for k in ("verdict", "reasons", "warnings", "headroom", "gain", "buffer_window_report"):
            log("stage B achievability.%s = %s" % (k, json.dumps(ach.get(k), ensure_ascii=False)[:4000]))
    except Exception:
        log("stage B EXC\n" + traceback.format_exc())


if __name__ == "__main__":
    main()
