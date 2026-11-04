"""base 엔진(4d39eaf5) + 동결 test 트리(dc8ccefe)에서 card test 를 파일마다 프로세스 하나로 돌려 실패를 수집. 인자: 트리, 결과 jsonl, 플러그인 폴더."""
import os
import shutil
import subprocess
import sys

TREE, OUT, PLUG, SRC = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
ROOT = TREE + "/skills/analog-gmid-design"
TESTS = ROOT + "/gmid_engine/tests"
if os.path.isdir(TESTS):
    shutil.rmtree(TESTS)
subprocess.check_call("git -C %s archive dc8ccefe skills/analog-gmid-design/gmid_engine/tests | tar -x -C %s" % (SRC, TREE), shell=True)
FILES = """graph/test_s1_symmetry.py graph/test_views.py metrics/test__helpers_nodal.py metrics/test_icm_config.py metrics/test_records.py metrics/test_ss_circuit.py metrics/test_ss_evaluate.py metrics/test_ss_metrics.py metrics/test_ss_types.py metrics/test_stamp_mos.py metrics/test_stamp_two_terminal.py sizing/test__helpers_dc_solve.py sizing/test_block_columns.py sizing/test_input_window.py sizing/test_s2_values.py sizing/test_writer_plan.py search/test_canonical_order.py""".split()
env = dict(os.environ, OPENBLAS_NUM_THREADS="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1", RED_CAP_OUT=OUT, PYTHONPATH=PLUG)
for f in FILES:
    subprocess.run([sys.executable, "-m", "pytest", "gmid_engine/tests/" + f, "-q", "-p", "red_cap", "-p", "no:cacheprovider", "--tb=no", "--continue-on-collection-errors"], cwd=ROOT, env=env, capture_output=True)
print("done")
