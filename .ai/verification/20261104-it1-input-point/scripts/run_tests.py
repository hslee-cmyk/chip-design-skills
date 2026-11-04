import subprocess, sys, os, json, time, ctypes

ISO = sys.argv[1]
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)
ROOT = ISO + "/skills/analog-gmid-design"
TESTS = "gmid_engine/tests/"


class M(ctypes.Structure):
    _fields_ = [("l", ctypes.c_ulong), ("load", ctypes.c_ulong), ("tp", ctypes.c_ulonglong), ("ap", ctypes.c_ulonglong),
                ("tf", ctypes.c_ulonglong), ("af", ctypes.c_ulonglong), ("tv", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong), ("x", ctypes.c_ulonglong)]


def free():
    m = M()
    m.l = ctypes.sizeof(M)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.ap / 2**30


card = ["graph/test_coupling_vars.py", "graph/test_gvgs_cycles.py", "graph/test_s1_values.py", "graph/test_s1v_build.py", "graph/test_s1v_fields.py", "graph/test_net_model.py",
        "metrics/test_achievability.py", "search/test_current_symmetry.py", "search/test_orbit_ties.py", "search/test_search_domain.py", "search/test_fd_jacobian.py",
        "sizing/test_block_columns.py", "sizing/test_current_basis.py", "sizing/test_kernel_context.py", "sizing/test_kernel_fields.py", "sizing/test_s2_values.py",
        "sizing/test_scc_order.py", "sizing/test_writer_plan.py", "sizing/test_input_window.py", "sizing/test_scc_newton.py", "sizing/test_kernel_run.py",
        "sizing/test_size_and_seal.py", "sizing/test_size_and_seal_local.py", "integration/test_stage_a_library.py"]
smoke = ["integration/test_stage_b_library.py", "integration/test_s0_layer_9circuits.py", "integration/test_g10_no_recompute_9circuits.py"]
jobs = [(c, 0, "card") for c in card] + [("structure", 0, "structure")] + [(s, 1, "smoke") for s in smoke]
which = sys.argv[3] if len(sys.argv) > 3 else "all"
env = dict(os.environ, OPENBLAS_NUM_THREADS="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
log = open(OUT + "/summary.jsonl", "a", encoding="utf-8")
worst = 1e9
for path, slow, grp in jobs:
    if which != "all" and grp != which:
        continue
    fr = free()
    worst = min(worst, fr)
    if fr < 2.0:
        log.write(json.dumps({"stop": "mem", "free": fr}) + "\n")
        log.flush()
        sys.exit(3)
    name = path.replace("/", "_").replace(".py", "")
    x = OUT + "/" + name + ".xml"
    cmd = [sys.executable, "-m", "pytest", TESTS + path, "-q", "-p", "no:cacheprovider", "--tb=short", f"--junitxml={x}"]
    if slow:
        cmd += ["--run-slow", "-k", "folded_cascode or ngcc_3stage_ff"]
    t = time.time()
    with open(OUT + "/" + name + ".log", "w", encoding="utf-8") as f:
        p = subprocess.run(cmd, cwd=ROOT, env=env, stdout=f, stderr=subprocess.STDOUT)
    tail = open(OUT + "/" + name + ".log", encoding="utf-8", errors="replace").read().strip().splitlines()[-1:]
    log.write(json.dumps({"group": grp, "path": path, "rc": p.returncode, "sec": round(time.time() - t, 1), "free": round(fr, 2), "tail": tail}, ensure_ascii=False) + "\n")
    log.flush()
log.write(json.dumps({"done": True, "min_free": round(worst, 2)}) + "\n")
log.flush()
