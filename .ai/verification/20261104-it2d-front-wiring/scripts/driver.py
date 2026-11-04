"""판정 측정 순차 실행(무거운 프로세스 하나씩). 시작 전 여유 < 3.7 GB 면 기다림, 실행 중 < 2 GB 면 자기 자식만 끝내고 멈춤. 인자: 작업 JSON 파일."""
import ctypes, json, os, subprocess, sys, time

T = "C:/Users/HSLEE/AppData/Local/Temp/la1s_it2c_audit"
jobs = json.load(open(sys.argv[1], encoding="utf-8"))
log_path = sys.argv[1] + ".log"


class M(ctypes.Structure):
    _fields_ = [("l", ctypes.c_ulong), ("m", ctypes.c_ulong), ("t", ctypes.c_ulonglong), ("a", ctypes.c_ulonglong), ("tp", ctypes.c_ulonglong),
                ("ap", ctypes.c_ulonglong), ("tv", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong), ("x", ctypes.c_ulonglong)]


def free():
    m = M(); m.l = ctypes.sizeof(M); ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.a / 2**30


def log(**kw):
    with open(log_path, "ab") as f:
        f.write((json.dumps(kw, ensure_ascii=False) + "\n").encode("utf-8"))


for job in jobs:
    tries = 0
    while True:
        waited = 0
        while free() < 3.7:
            time.sleep(15); waited += 15
        env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1", **job.get("env", {}))
        t0 = time.time()
        low = free()
        stopped = False
        with open(job["out"], "wb") as f:
            p = subprocess.Popen(job["cmd"], cwd=job["cwd"], env=env, stdout=f, stderr=subprocess.STDOUT)
            rc = None
            while rc is None:
                time.sleep(2)
                rc = p.poll()
                now = free(); low = min(low, now)
                if rc is None and now < 2.0:
                    p.kill(); p.wait()
                    stopped = True
                    break
        if not stopped:
            log(name=job["name"], rc=rc, secs=round(time.time() - t0), waited=waited, low=round(low, 2), tries=tries)
            break
        tries += 1
        log(name=job["name"], paused="mem<2", low=round(low, 2), tries=tries)
        if tries >= 6:
            log(stop="mem<2 6회")
            sys.exit(3)
log(done=True)
