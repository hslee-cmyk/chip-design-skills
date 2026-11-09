"""Full pytest split into per-target processes (brief: one process per LUT-loading unit), sequential.
Stops the running target when free memory < 2 GB, waits for > 3 GB, retries the target (at most MAX_TRIES).
usage: run_split.py <clone> <outdir> [target-subdir ...]   (default = every dir, integration per file)
Per-target JUnit + a progress log appended case by case."""
import ctypes, glob, os, subprocess, sys, time


class MS(ctypes.Structure):
    _fields_ = [("l", ctypes.c_ulong), ("load", ctypes.c_ulong), ("total", ctypes.c_ulonglong),
                ("avail", ctypes.c_ulonglong), ("tp", ctypes.c_ulonglong), ("ap", ctypes.c_ulonglong),
                ("tv", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong), ("e", ctypes.c_ulonglong)]


def free_mb():
    m = MS(); m.l = ctypes.sizeof(MS)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.avail / 1048576


clone, out = sys.argv[1], sys.argv[2]
only = sys.argv[3:]
os.makedirs(out, exist_ok=True)
T = "skills/analog-gmid-design/gmid_engine/tests"
root = os.path.join(clone, T)
targets = []
for name in sorted(os.listdir(root)):
    p = os.path.join(root, name)
    if name.startswith("__") or name == "fixtures":
        continue
    if os.path.isdir(p):
        if name == "integration":
            targets += [T + "/integration/" + os.path.basename(f) for f in sorted(glob.glob(p + "/test_*.py"))]
        elif glob.glob(p + "/**/test_*.py", recursive=True):
            targets.append(T + "/" + name)
    elif name.startswith("test_"):
        targets.append(T + "/" + name)
if only:
    targets = [t for t in targets if any(t == T + "/" + o or t.startswith(T + "/" + o + "/") for o in only)]
env = dict(os.environ, OPENBLAS_NUM_THREADS="1", PYTHONIOENCODING="utf-8", PYTHONPYCACHEPREFIX=out + "/pyc")
MAX_TRIES = 4
prog = open(out + "/progress.log", "a", encoding="utf-8")


def log(s):
    prog.write(s + "\n"); prog.flush()


for i, t in enumerate(targets):
    tag = "%02d_%s" % (i, t.rsplit("/", 1)[-1].removesuffix(".py"))
    for attempt in range(1, MAX_TRIES + 1):
        while free_mb() < 3072:
            time.sleep(30)
        t0 = time.time(); low = 1e12; aborted = False
        cmd = [r"C:\Python314\python.exe", "-P", "-m", "pytest", t, "-q", "-rfE", "--tb=short",
               "--junitxml=%s/%s.xml" % (out, tag), "-p", "no:cacheprovider"]
        with open("%s/%s.log" % (out, tag), "wb") as f:
            p = subprocess.Popen(cmd, cwd=clone, env=env, stdout=f, stderr=subprocess.STDOUT)
            while p.poll() is None:
                fm = free_mb(); low = min(low, fm)
                if fm < 2048:
                    aborted = True
                    subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
                    break
                time.sleep(5)
            p.wait()
        log("%s try=%d rc=%s aborted=%s sec=%d min_free_mb=%.0f" % (t, attempt, p.returncode, aborted, time.time() - t0, low))
        if not aborted:
            break
    else:
        log("GAVE_UP %s" % t)
log("DONE")
