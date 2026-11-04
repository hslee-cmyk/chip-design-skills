"""Two-circuit smoke, one pytest process at a time, memory watched. usage: python -I smoke_2c.py <clone root> <out dir>
Below 2048 MB free the running pytest tree is killed, the record says so, and the remaining files are not started."""
import ctypes, json, os, subprocess, sys, time
import xml.etree.ElementTree as ET
from pathlib import Path

root, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
FILES = ["test_stage_b_library", "test_s0_layer_9circuits", "test_g10_no_recompute_9circuits"]
K = "folded_cascode or ngcc_3stage_ff"


class M(ctypes.Structure):
    _fields_ = [("l", ctypes.c_ulong), ("m", ctypes.c_ulong), ("t", ctypes.c_ulonglong), ("a", ctypes.c_ulonglong), ("x", ctypes.c_ulonglong * 5)]


def free_mb():
    s = M()
    s.l = ctypes.sizeof(M)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s))
    return s.a / 1048576


env = dict(os.environ, OPENBLAS_NUM_THREADS="1", PYTHONIOENCODING="utf-8", PYTHONPYCACHEPREFIX=str(out / "pyc"))
for name in FILES:
    while free_mb() < 3700:
        time.sleep(30)
    rel = "skills/analog-gmid-design/gmid_engine/tests/integration/%s.py" % name
    junit = out / (name + ".xml")
    t0, low, aborted = time.time(), free_mb(), False
    with open(out / (name + ".log"), "wb") as log:
        p = subprocess.Popen([sys.executable, "-P", "-m", "pytest", rel, "--run-slow", "-k", K, "-q", "-rfEx", "--tb=short", "--junitxml=" + str(junit), "-p", "no:cacheprovider"],
                             cwd=str(root), env=env, stdout=log, stderr=subprocess.STDOUT)
        while p.poll() is None:
            low = min(low, free_mb())
            if low < 2048:
                aborted = True
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
                break
            time.sleep(2)
        rc = p.wait()
    rec = {"file": name, "rc": rc, "sec": round(time.time() - t0), "min_free_mb": round(low), "aborted_memory": aborted}
    try:
        r = ET.parse(junit).getroot()
        cases = list(r.iter("testcase"))
        rec.update(tests=len(cases), failed=[c.get("name") for c in cases if c.find("failure") is not None or c.find("error") is not None],
                   skipped=[c.get("name") for c in cases if c.find("skipped") is not None], names=[c.get("name") for c in cases])
    except (OSError, ET.ParseError) as e:
        rec["no_report"] = str(e)
    with open(out / "results.jsonl", "ab") as f:
        f.write((json.dumps(rec, ensure_ascii=False) + "\n").encode("utf-8"))
    if aborted:
        break
print("done")
