"""복사본 뮤턴트(판정자). 트리 = <T>/mut (git archive HEAD). 파일을 바이너리 치환 -> 지정 test 실행 -> 복원. 결과는 줄마다 append."""
import json, os, subprocess, sys, tempfile, time, re
T = sys.argv[1]
ROOT = os.path.join(T, "mut", "skills", "analog-gmid-design")
E = os.path.join(ROOT, "gmid_engine")
OUT = os.path.join(T, "out", "mutants.jsonl")
A = "gmid_engine/tests/"
MUT = [
 ("m1_rows_tol", "sizing/_helpers_dc_solve.py", "vds - bound.vdsat_v, _ROW_SAT", "vds - bound.vdsat_v - (bound.tol_v or 0.0), _ROW_SAT",
  ["sizing/test_block_columns.py", "sizing/test_input_window.py", "metrics/test_icm_config.py", "sizing/test__helpers_dc_solve.py"]),
 ("m2_sat_v_tol", "metrics/metrics_aux.py", "op.vgs, bound.vdsat_v, bound.tol_v,", "op.vgs, (None if bound.vdsat_v is None else bound.vdsat_v + (bound.tol_v or 0.0)), bound.tol_v,",
  ["metrics/test_metrics_aux.py", "lut/test_sat_threshold.py", "metrics/test_ss_off_gate.py"]),
 ("m3_domain_tol", "search/iv_domain.py", "_snap_up_vds(ctx, d.kind, float(vdsat.values[j]))", "_snap_up_vds(ctx, d.kind, float(vdsat.values[j]) + 0.002)",
  ["search/test_iv_domain.py", "search/test_iv_headroom.py"]),
 ("m4_headroom_tol", "search/iv_headroom.py", "level, values, source = budget, curve.values, SRC_HEADROOM_VDSAT", "level, values, source = budget - 0.002, curve.values, SRC_HEADROOM_VDSAT",
  ["search/test_iv_headroom.py"]),
 ("m5_edge_strict", "lut/derived_fns.py", "saturable = vds >= np.asarray(vdsat)", "saturable = vds > np.asarray(vdsat)",
  ["lut/test_derived_fns.py"]),
 ("m6_seal_tol", "sizing/seal_region.py", "    if bound.reason is None:\n        return bound.vdsat_v\n", "    if bound.reason is None:\n        return bound.vdsat_v + (bound.tol_v or 0.0)\n",
  ["sizing/test_seal_region.py"]),
 ("m7_reverse_le", "lut/sat_threshold.py", "if vds < 0:", "if vds <= 0:", ["lut/test_sat_threshold.py"]),
 ("m8_grid_no_check", "lut/sat_threshold_grid.py", "    slice_grids = memo.lut.slice_map[(kind, w_key)].grids\n", "    return src.array\n    slice_grids = memo.lut.slice_map[(kind, w_key)].grids\n",
  ["lut/test_sat_threshold_grid.py"]),
 ("m9_off_entry_gone", "sizing/block_widths.py", "if region == REGION_OFF:", "if region == REGION_OFF and False:", ["sizing/test_block_widths.py"]),
 ("m10_ref_vds_no_idu", "lut/derived_fns.py", "probe = vdsat_curve if sat_threshold_grid(memo, kind, w_key) is not None else idu_curve", "probe = vdsat_curve",
  ["search/test_iv_headroom.py", "lut/test_derived_fns.py"]),
 ("m11_rows_ignore_field", "sizing/_helpers_dc_solve.py", "self.L[m], vgs, vds, vsb) if sat is None else sat[m]", "self.L[m], vgs, vds, vsb)",
  ["metrics/test_icm_config.py", "lut/test_sat_threshold.py"]),
 ("m12_tol_string_restored", "lut/vdsat_tolerance.py", '("table", "tol_" + TOL_VDSAT_METRICS[0])', '("table", "tol_vdsat")',
  ["lut/test_sat_threshold.py", "lut/test_vdsat_tolerance.py", "lut/test_lut_memo.py"]),
 ("m13_tol_call_probe", "lut/sat_threshold.py", "    return SatBound(value, tol_vdsat_table(memo, kind, w_key).at(L, vds), None)\n",
  "    return SatBound(value, tol_vdsat_table(memo, kind, w_key).at(L, vds), None)\n\n\ndef _x(tol_vdsat):\n    return tol_vdsat(1)\n", ["lut/test_sat_threshold.py"]),
]
only = set(sys.argv[2:])
env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", PYTHONPYCACHEPREFIX=tempfile.mkdtemp(prefix="pyc_mut_", dir=os.path.join(T, "out")), PYTHONIOENCODING="utf-8")
for name, rel, old, new, tests in [("m0_control", None, None, None, ["lut/test_sat_threshold.py", "lut/test_derived_fns.py", "sizing/test_seal_region.py"])] + MUT:
    if only and name not in only:
        continue
    path = None if rel is None else os.path.join(E, rel)
    raw = None
    if path:
        raw = open(path, "rb").read()
        crlf = b"\r\n" in raw
        a, b = old.encode("utf-8"), new.encode("utf-8")
        if crlf:
            a, b = a.replace(b"\n", b"\r\n"), b.replace(b"\n", b"\r\n")
        assert raw.count(a) >= 1, (name, "pattern 없음")
        open(path, "wb").write(raw.replace(a, b))
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "--no-header", "--tb=no"] + [A + t for t in tests], cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=400)
        tail = [l for l in p.stdout.splitlines() if l.startswith("FAILED") or l.startswith("ERROR")][:6]
        last = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else ""
        rec = {"m": name, "rc": p.returncode, "summary": last, "failed": tail, "sec": round(time.time() - t0)}
    finally:
        if path:
            open(path, "wb").write(raw)
    with open(OUT, "ab") as f:
        f.write((json.dumps(rec, ensure_ascii=False) + "\n").encode("utf-8"))
with open(OUT, "ab") as f:
    f.write(b'{"m":"END"}\n')
