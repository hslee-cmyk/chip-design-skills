"""n9 한 회로 실행 + 메모리 기록. 인자 = 회로 이름. 여유 < 2 GB면 자식을 멈추고 기록. 결과는 n9_memory.jsonl에 append.
Windows API(GlobalMemoryStatusEx, GetProcessMemoryInfo)로 읽기만 한다. 측정 값은 n9_mw1_feas.py가 jsonl에 append한다."""
import ctypes
import ctypes.wintypes as wt
import json
import os
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).parent
LOG = HERE / "n9_memory.jsonl"
FLOOR = 2 * 1024 ** 3


class MS(ctypes.Structure):
    _fields_ = [("dwLength", wt.DWORD), ("dwMemoryLoad", wt.DWORD), ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


class PMC(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]


k32 = ctypes.WinDLL("kernel32", use_last_error=True)
psapi = ctypes.WinDLL("psapi", use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
psapi.GetProcessMemoryInfo.argtypes = [wt.HANDLE, ctypes.POINTER(PMC), wt.DWORD]


def avail():
    m = MS()
    m.dwLength = ctypes.sizeof(MS)
    k32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.ullAvailPhys, m.ullTotalPhys


def peak(handle):
    c = PMC()
    c.cb = ctypes.sizeof(PMC)
    if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(c), c.cb):
        return None
    return max(c.PeakPagefileUsage, c.PeakWorkingSetSize)


def gb(x):
    return None if x is None else round(x / 1024 ** 3, 2)


circuit = sys.argv[1]
attempt = sys.argv[2] if len(sys.argv) > 2 else "1"
a0, total = avail()
rec = {"circuit": circuit, "attempt": attempt, "avail_start_gb": gb(a0), "total_gb": gb(total)}
if a0 < FLOOR:
    rec["outcome"] = "not_started_low_memory"
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    print(rec)
    sys.exit(3)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
t0 = time.time()
out = (HERE / ("n9_stdout_%s_%s.txt" % (circuit, attempt))).open("w", encoding="utf-8")
p = subprocess.Popen([sys.executable, "n9_mw1_feas.py", circuit], cwd=str(HERE), env=env, stdout=out, stderr=subprocess.STDOUT)
h = k32.OpenProcess(0x1000 | 0x0400, False, p.pid)
low, pk, stopped = a0, 0, False
while p.poll() is None:
    time.sleep(3)
    a, _ = avail()
    low = min(low, a)
    v = peak(h)
    pk = max(pk, v or 0)
    if a < FLOOR:
        stopped = True
        p.kill()
        break
p.wait()
out.close()
a1, _ = avail()
rec.update(avail_end_gb=gb(a1), avail_min_gb=gb(low), child_peak_gb=gb(pk), seconds=round(time.time() - t0, 1), returncode=p.returncode,
           outcome="stopped_below_2gb" if stopped else ("done" if p.returncode == 0 else "failed"))
with LOG.open("a", encoding="utf-8") as f:
    f.write(json.dumps(rec) + "\n")
print(rec)
