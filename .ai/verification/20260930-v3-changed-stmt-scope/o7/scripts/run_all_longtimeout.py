"""auditor 측정 보조(20260930-v3-changed-stmt-scope 순서 7): 병합본 복제본의 run_all.py를 그대로 import해 main을 부르되,
케이스 하나의 bash 실행 상한(run_all.py 140행 timeout=3600)만 6900초로 늘린다. 복제본 파일은 바꾸지 않는다.
이유: 15-records(133단계)가 기계 부하(다른 작업의 redteam 동시 실행) 아래 두 번 3600초를 넘어 하네스 ERROR(TimeoutExpired)가 됐다
-- 단계 판정과 무관한 실행 시간 상한이다.
사용: python -u -B run_all_longtimeout.py <redteam 디렉터리> <run_all 인자...>"""
import importlib.util
import subprocess
import sys

R = sys.argv[1]
_orig = subprocess.run
PATCHED = []


def _run(*a, **k):
    if k.get("timeout") == 3600:
        k["timeout"] = 6900
        PATCHED.append(1)
    return _orig(*a, **k)


subprocess.run = _run
spec = importlib.util.spec_from_file_location("run_all", R + "/run_all.py")
m = importlib.util.module_from_spec(spec)
sys.modules["run_all"] = m
spec.loader.exec_module(m)
rc = m.main(sys.argv[2:])
print("timeout_patched_calls=%d" % len(PATCHED), flush=True)
sys.exit(rc)
