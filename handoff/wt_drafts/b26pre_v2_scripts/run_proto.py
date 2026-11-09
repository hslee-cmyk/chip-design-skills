"""b26pre v2 -- 시제품(proto_v2_test_b26pre.py)을 C:/g106/<copy>에 넣고 실행한다.
사용: python -B run_proto.py <copy> <seed...>   결과는 C:/g106/out/baseline.txt에 append."""
import os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.join(HERE, "proto_v2_test_b26pre.py")
REL = "skills/analog-gmid-design/assets/tests/contracts/test_b26pre_proto.py"
PY = "C:/Python314/python.exe"


def place(root):
    shutil.copyfile(PROTO, os.path.join(root, *REL.split("/")))


def run(root, seed="1", extra=(), timeout=1500):
    env = dict(os.environ, PYTHONPYCACHEPREFIX=root + "_pyc", PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED=seed,
               PYTHONIOENCODING="utf-8", APPDATA="C:/Users/HSLEE/AppData/Roaming")
    ini = os.path.join(root, "tools", "gates", "pytest_gate.ini")
    cmd = [PY, "-P", "-m", "pytest", "-c", ini, "--rootdir=" + root, "--confcutdir=" + root, "-q", "-rA", "--color=no",
           "-p", "no:cacheprovider", "--gmid-phase=2", "--gmid-strict=", *extra, os.path.join(root, *REL.split("/"))]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=root, capture_output=True, env=env, timeout=timeout)
        return r.returncode, time.time() - t0, r.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return "timeout", time.time() - t0, ""


if __name__ == "__main__":
    os.makedirs("C:/g106/out", exist_ok=True)
    root = "C:/g106/" + sys.argv[1]
    place(root)
    for seed in sys.argv[2:]:
        rc, dt, txt = run(root, seed)
        last = [l for l in txt.splitlines() if l.strip()][-1:] or [""]
        line = "%s seed=%s rc=%s %.1fs %s" % (sys.argv[1], seed, rc, dt, last[0])
        with open("C:/g106/out/baseline.txt", "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
            if rc != 0:
                fh.write(txt[-8000:] + "\n")
        print(line, flush=True)
        if rc != 0:
            print(txt[-5000:])
