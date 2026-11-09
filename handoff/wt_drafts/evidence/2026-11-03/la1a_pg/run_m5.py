import os, subprocess, sys
H = os.path.dirname(os.path.abspath(__file__))
env = dict(os.environ, PYTHONIOENCODING="utf-8", OPENBLAS_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
for spec in sys.argv[1:]:
    c, run = spec.split(":")
    try:
        r = subprocess.run([sys.executable, "m5_eval_start.py", c, run, "--front"], cwd=H, env=env, capture_output=True, timeout=500)
        tail = (r.stdout + r.stderr).decode("utf-8", "replace").strip().split("\n")[-1][:300]
    except subprocess.TimeoutExpired:
        tail = "timeout"
    with open(os.path.join(H, "m5_status.txt"), "ab") as f:
        f.write(("%s %s\n" % (spec, tail)).encode("utf-8"))
