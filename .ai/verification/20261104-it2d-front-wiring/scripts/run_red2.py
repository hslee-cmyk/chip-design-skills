"""엔진 커밋(인자 2) + 머리 test 트리(d5f5b8e6)에서 test 파일마다 프로세스 하나로 실패 수집. 인자: 복제본, 엔진 커밋, 결과 jsonl, 플러그인 폴더, 파일 쉼표 목록."""
import os, shutil, subprocess, sys
TREE, COMMIT, OUT, PLUG, FILES = sys.argv[1:6]
ROOT = TREE + "/skills/analog-gmid-design"
subprocess.check_call(["git", "-C", TREE, "switch", "-q", "-f", "--detach", COMMIT])
TESTS = ROOT + "/gmid_engine/tests"
shutil.rmtree(TESTS)
subprocess.check_call("git -C %s archive d5f5b8e6 skills/analog-gmid-design/gmid_engine/tests | tar -x -C %s" % (TREE, TREE), shell=True)
env = dict(os.environ, OPENBLAS_NUM_THREADS="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1", RED_CAP_OUT=OUT, PYTHONPATH=PLUG)
for f in FILES.split(","):
    subprocess.run([sys.executable, "-m", "pytest", "gmid_engine/tests/" + f, "-q", "-p", "red_cap", "-p", "no:cacheprovider", "--tb=no", "--continue-on-collection-errors"], cwd=ROOT, env=env, capture_output=True)
print("done")
