import os, subprocess, sys
H = os.path.dirname(os.path.abspath(__file__))
env = dict(os.environ, PYTHONIOENCODING="utf-8", OPENBLAS_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
def log(t):
    with open(os.path.join(H, "run_all.log"), "ab") as f:
        f.write((t + "\n").encode("utf-8"))
for m in ("base", "ga", "da1", "da1m", "da2", "da3"):
    try:
        r = subprocess.run([sys.executable, "q8_la1a.py", "two_stage_ota_sf", m, "--front"], cwd=H, env=env, capture_output=True, timeout=500)
        open(os.path.join(H, "q8_sf_%s.stdout.txt" % m), "wb").write(r.stdout + r.stderr)
        log("two_stage_ota_sf %s rc=%s" % (m, r.returncode))
    except subprocess.TimeoutExpired:
        log("two_stage_ota_sf %s timeout" % m)
try:
    r = subprocess.run([sys.executable, "la1a_uncovered.py"], cwd=H, env=env, capture_output=True, timeout=900)
    open(os.path.join(H, "uncovered.stdout.txt"), "wb").write(r.stdout + r.stderr)
    log("uncovered rc=%s" % r.returncode)
except subprocess.TimeoutExpired:
    log("uncovered timeout")
