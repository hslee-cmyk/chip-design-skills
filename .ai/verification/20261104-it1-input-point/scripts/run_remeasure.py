"""회로마다 프로세스 하나로 재측정. 인자: 복제본 루트, 출력 폴더, 쉼표 회로 목록."""
import ctypes
import json
import os
import shutil
import subprocess
import sys

ISO, OUT, CIRCUITS = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
os.makedirs(OUT, exist_ok=True)
ROOT = ISO + "/skills/analog-gmid-design"
TESTDIR = ROOT + "/gmid_engine/tests/integration"
shutil.copy(os.path.dirname(os.path.abspath(__file__)) + "/test_zz_remeasure.py", TESTDIR + "/test_zz_remeasure.py")


class M(ctypes.Structure):
    _fields_ = [("l", ctypes.c_ulong), ("load", ctypes.c_ulong), ("tp", ctypes.c_ulonglong), ("ap", ctypes.c_ulonglong),
                ("tf", ctypes.c_ulonglong), ("af", ctypes.c_ulonglong), ("tv", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong), ("x", ctypes.c_ulonglong)]


def free():
    m = M()
    m.l = ctypes.sizeof(M)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.ap / 2**30


log = open(OUT + "/log.jsonl", "ab")
try:
    for c in CIRCUITS:
        fr = free()
        if fr < 2.0:
            log.write((json.dumps({"stop": "mem", "free": fr}) + "\n").encode())
            log.flush()
            sys.exit(3)
        env = dict(os.environ, OPENBLAS_NUM_THREADS="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1", RM_CIRCUIT=c, RM_OUT=OUT + "/" + c + ".json")
        p = subprocess.run([sys.executable, "-m", "pytest", "gmid_engine/tests/integration/test_zz_remeasure.py", "-q", "-p", "no:cacheprovider", "--tb=short"], cwd=ROOT, env=env, capture_output=True, encoding="utf-8", errors="replace")
        log.write((json.dumps({"circuit": c, "rc": p.returncode, "free": round(fr, 2), "tail": p.stdout.strip().splitlines()[-6:]}, ensure_ascii=False) + "\n").encode("utf-8"))
        log.flush()
finally:
    os.remove(TESTDIR + "/test_zz_remeasure.py")
log.write(b'{"done": true}\n')
log.close()
