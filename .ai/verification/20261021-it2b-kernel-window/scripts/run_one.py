"""test 파일 하나를 이 프로세스 안에서 pytest 로 돌리고, 끝나면 프로세스 최대 작업 집합(PeakWorkingSetSize, Windows)을 한 줄로 낸다.
usage: python run_one.py <junit_xml> <test 파일> [pytest 인자...]   (cwd = skills/analog-gmid-design)
출력 마지막 줄: RUN_ONE rc=<rc> peak_mb=<MB>
(IT-2a 감사 run_one.py 복사본 -- GetProcessMemoryInfo argtypes 를 지정해 OverflowError 를 고침)
"""
import ctypes
import ctypes.wintypes as wt
import os
import sys

sys.path.insert(0, os.getcwd())
import pytest  # noqa: E402


class PMC(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t)]


def peak_mb():
    try:
        c = PMC()
        c.cb = ctypes.sizeof(PMC)
        k32 = ctypes.WinDLL("kernel32")
        psapi = ctypes.WinDLL("psapi")
        k32.GetCurrentProcess.restype = wt.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [wt.HANDLE, ctypes.POINTER(PMC), wt.DWORD]
        psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(c), c.cb)
        return c.PeakWorkingSetSize / 2 ** 20
    except Exception:  # noqa: BLE001 -- 계측 실패는 pytest 결과에 영향 없음
        return -1.0


def main():
    junit, target, rest = sys.argv[1], sys.argv[2], sys.argv[3:]
    rc = pytest.main(["-p", "no:cacheprovider", "-q", "-rfE", "--tb=short", "--run-slow", "--junitxml=" + junit, target] + rest)
    sys.stdout.flush()
    print("RUN_ONE rc=%d peak_mb=%.0f" % (int(rc), peak_mb()), flush=True)
    sys.exit(int(rc))


if __name__ == "__main__":
    main()
