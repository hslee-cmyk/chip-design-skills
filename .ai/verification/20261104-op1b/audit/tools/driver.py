"""판정자 실행 제어(저장소 밖): run_op1b.py run을 입력 하나씩 순차로 부른다. 메모리 문턱은 브리핑 값(3.7 GB 대기, 2 GB 멈춤).
문턱은 판정 값이 아니라 동시 실행 안전 지시다. 입력마다 결과를 파일에 append한다."""
import ctypes, json, os, subprocess, sys, threading, time

B, ISO, EXE, DECL = sys.argv[1:5]
IDS = sys.argv[5:]
RUN = os.path.join(B, "run")
os.makedirs(RUN, exist_ok=True)
LOG = os.path.join(RUN, "driver.jsonl")
TOOL = os.path.join(ISO, ".ai/verification/20261104-op1b/scripts/run_op1b.py")
GB = 1024 ** 3
WAIT, STOP = 3.7 * GB, 2.0 * GB


class M(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong), ("a", ctypes.c_ulonglong), ("b", ctypes.c_ulonglong),
                ("c", ctypes.c_ulonglong), ("d", ctypes.c_ulonglong), ("e", ctypes.c_ulonglong)]


def avail():
    m = M()
    m.dwLength = ctypes.sizeof(M)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.ullAvailPhys


def note(rec):
    with open(LOG, "ab") as f:
        f.write((json.dumps(rec, ensure_ascii=False) + "\n").encode("utf-8"))


env = dict(os.environ)
env["OPENBLAS_NUM_THREADS"] = "1"
env["PYTHONPYCACHEPREFIX"] = os.path.join(B, "pyc")
min_all = avail()
note({"start": time.strftime("%H:%M:%S"), "avail_GB": min_all / GB, "ids": IDS})
for rid in IDS:
    while avail() < WAIT:
        note({"id": rid, "waiting_avail_GB": avail() / GB, "t": time.strftime("%H:%M:%S")})
        time.sleep(20)
    t0 = time.time()
    cmd = [sys.executable, TOOL, "run", "--repo", ISO, "--location", "skills/analog-gmid-design/assets/lut_v2_location.json",
           "--old-root", os.path.join(B, "old"), "--exe", EXE, "--decl", DECL, "--adapter", "ngspice",
           "--work", os.path.join(RUN, "work"), "--baseline", os.path.join(RUN, "baseline"), "--ids", rid]
    so = open(os.path.join(RUN, rid + ".stdout.txt"), "wb")
    se = open(os.path.join(RUN, rid + ".stderr.txt"), "wb")
    p = subprocess.Popen(cmd, stdout=so, stderr=se, env=env, cwd=ISO)
    lo = [avail()]
    killed = [False]

    def watch():
        while p.poll() is None:
            a = avail()
            lo[0] = min(lo[0], a)
            if a < STOP and not killed[0]:
                killed[0] = True
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
            time.sleep(0.5)

    th = threading.Thread(target=watch)
    th.start()
    rc = p.wait()
    th.join()
    so.close(); se.close()
    min_all = min(min_all, lo[0])
    rec = {"id": rid, "rc": rc, "seconds": round(time.time() - t0, 1), "min_avail_GB": lo[0] / GB, "killed_low_mem": killed[0]}
    # 호환 환경 사후 확인: 출력 폴더·HOME에 .spiceinit 없음(선언 spiceinit_text 빈 문자열)
    wd = os.path.join(RUN, "work", rid)
    rec["spiceinit_out"] = os.path.exists(os.path.join(wd, "o", ".spiceinit"))
    rec["home_files"] = os.listdir(os.path.join(wd, "home")) if os.path.isdir(os.path.join(wd, "home")) else None
    note(rec)
    if rc != 0:
        note({"stopped_at": rid, "min_avail_all_GB": min_all / GB})
        sys.exit(rc if rc else 9)
note({"done": True, "min_avail_all_GB": min_all / GB, "end": time.strftime("%H:%M:%S")})
