"""필수 test 일괄: 격리 복제본 안에서, 무거운 프로세스 하나씩. 인자: 복제본 결과폴더 [scopes]"""
import os, subprocess, sys, time
root, out = sys.argv[1], sys.argv[2]
scopes = sys.argv[3].split(",") if len(sys.argv) > 3 else ["card", "structure", "canon", "smoke"]
os.makedirs(out, exist_ok=True)
env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
E = "gmid_engine/tests"
CARD = """graph/test_s1_symmetry.py graph/test_views.py metrics/test__helpers_nodal.py metrics/test_icm_config.py
metrics/test_records.py metrics/test_ss_circuit.py metrics/test_ss_evaluate.py metrics/test_ss_metrics.py metrics/test_ss_types.py
metrics/test_stamp_mos.py metrics/test_stamp_two_terminal.py sizing/test__helpers_dc_solve.py sizing/test_block_columns.py
sizing/test_input_window.py sizing/test_s2_values.py sizing/test_writer_plan.py""".split()
S = {
    "card": [f"{E}/{c}" for c in CARD],
    "structure": [f"{E}/structure"],
    "canon": [f"{E}/search/test_canonical_order.py"],
    "smoke": ["--run-slow", "-k", "folded_cascode or ngcc_3stage_ff", f"{E}/integration/test_stage_b_library.py",
              f"{E}/integration/test_s0_layer_9circuits.py", f"{E}/integration/test_g10_no_recompute_9circuits.py"],
}
for name in scopes:
    t = time.time()
    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--tb=short", f"--junitxml={out}/{name}.xml"] + S[name]
    with open(f"{out}/{name}.txt", "wb") as f:
        rc = subprocess.call(cmd, cwd=f"{root}/skills/analog-gmid-design", env=env, stdout=f, stderr=subprocess.STDOUT)
    with open(f"{out}/rc.txt", "a", encoding="utf-8") as f:
        f.write(f"{name} rc={rc} {time.time()-t:.0f}s\n")
