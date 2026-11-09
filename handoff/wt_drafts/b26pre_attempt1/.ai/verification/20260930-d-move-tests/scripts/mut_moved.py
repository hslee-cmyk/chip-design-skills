"""auditor 변이: 이관된 두 새 모듈에 변이를 하나씩 넣고 그 이름을 쓰는 test(V1 형태 명령, 해당 test id만)를 돌린다.
대조군(변이 없음) 2개로 명령 자체가 PASS함을 먼저 보인다. 끝나면 원본 바이트 복원. 결과는 <out.jsonl>에 변이마다 append.
사용: python -P mut_moved.py <복제본> <캐시> <out.jsonl>"""
import json, os, subprocess, sys, time
root, cache, out = sys.argv[1:4]
A = os.path.join(root, "skills", "analog-gmid-design", "assets")
RR = os.path.join(A, "tests", "tools", "regression_runner.py")
IS = os.path.join(A, "tests", "tools", "interleave_splits.py")
T_S004 = A + "/tests/unit/test_selftest_sizing_recipe.py::test_s004_optimize_multistage"
T_S022 = A + "/tests/unit/test_selftest_stick_diagram.py::test_s022_common_centroid_layout"
MUTANTS = [
    ("control_rr_none", RR, "import json\n", "import json\n", T_S004),
    ("control_is_none", IS, "def find_interleaved_symmetric_splits", "def find_interleaved_symmetric_splits", T_S022),
    ("is_return_empty", IS, "    if count_a != count_b:\n        return []", "    if True:\n        return []", T_S022),
    ("is_no_sort", IS, "    splits.sort(key=lambda s: abs(s[0] - s[1]))\n", "", T_S022),
    ("is_raise", IS, "    if count_a != count_b:\n        return []", "    if True:\n        raise ValueError('mut')", T_S022),
    ("rr_engines_empty", RR, '    "optimize_multistage": _run_optimize_multistage_case,\n', "", T_S004),
    ("rr_gms_cmp_flip", RR, "        if abs(a_gm - e_gm) / e_gm > rel_tol:", "        if abs(a_gm - e_gm) / e_gm < rel_tol:", T_S004),
    ("rr_stage_cmp_flip", RR, "            if abs(a_val - e_val) / max(abs(e_val), 1e-15) > rel_tol:", "            if abs(a_val - e_val) / max(abs(e_val), 1e-15) < rel_tol:", T_S004),
    ("rr_final_ok_false", RR, "    return RegressionVerdict(ok=True, case_key=case_key, actual=actual,", "    return RegressionVerdict(ok=False, case_key=case_key, actual=actual,", T_S004),
    ("rr_wref_1e-6", RR, 'd["CGG_n"], W_ref=5e-6)', 'd["CGG_n"], W_ref=1e-6)', T_S004),
    ("rr_gm_id_grid_drop", RR, '        gm_id_grid=search["gm_id_grid"],', '        gm_id_grid=search["gm_id_grid"][::2],', T_S004),
    ("rr_objective_area", RR, 'objective=constraints.get("objective", "power")', 'objective="area"', T_S004),
    ("rr_rel_tol_huge", RR, "def run_regression_case(reference_json_path: str, case_key: str, rel_tol: float = 0.01)", "def run_regression_case(reference_json_path: str, case_key: str, rel_tol: float = 10.0)", T_S004),
]
env = dict(os.environ, PYTHONPATH=cache, PYTHONDONTWRITEBYTECODE="1")
for name, path, old, new, test in MUTANTS:
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")
    if "\r\n" in text:   # 작업 트리는 core.autocrlf=true라 CRLF
        old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
    n = text.count(old)
    rec = {"mutant": name, "file": os.path.basename(path), "test": test.split("::")[-1], "matches": n}
    if n != 1:
        rec["status"] = "SKIP(match != 1)"
    else:
        try:
            open(path, "wb").write(text.replace(old, new).encode("utf-8"))
            t = time.time()
            p = subprocess.run([sys.executable, "-P", "-m", "pytest", "-c", cache + "/pytest_gate.ini", "--rootdir=" + root,
                                "--confcutdir=" + root, "--gmid-phase=2", "--gmid-strict=", "-q", "-p", "no:cacheprovider", test],
                               capture_output=True, env=env, timeout=900)
            status = "KILLED" if p.returncode != 0 else "SURVIVED"
            if name.startswith("control"):
                status = "CONTROL_PASS" if p.returncode == 0 else "CONTROL_FAIL"
            rec.update(exit=p.returncode, status=status,
                       tail=p.stdout.decode("utf-8", "replace").strip().splitlines()[-1][:200], secs=round(time.time() - t, 1))
        finally:
            open(path, "wb").write(orig)
    with open(out, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps(rec, ensure_ascii=False), flush=True)
