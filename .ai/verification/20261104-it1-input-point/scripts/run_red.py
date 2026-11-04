"""base 엔진 + 동결 test 트리에서 card test 를 파일마다 프로세스 하나로 돌려 실패를 수집."""
import os
import subprocess
import sys

TREE, OUT, PLUG = sys.argv[1], sys.argv[2], sys.argv[3]
ROOT = TREE + "/skills/analog-gmid-design"
FILES = ["graph/test_coupling_vars.py", "graph/test_gvgs_cycles.py", "graph/test_s1_values.py", "graph/test_s1v_build.py", "graph/test_s1v_fields.py", "graph/test_net_model.py",
         "metrics/test_achievability.py", "search/test_current_symmetry.py", "search/test_orbit_ties.py", "search/test_search_domain.py", "search/test_fd_jacobian.py",
         "sizing/test_block_columns.py", "sizing/test_current_basis.py", "sizing/test_kernel_context.py", "sizing/test_kernel_fields.py", "sizing/test_s2_values.py",
         "sizing/test_scc_order.py", "sizing/test_writer_plan.py", "sizing/test_input_window.py", "sizing/test_scc_newton.py", "sizing/test_kernel_run.py",
         "sizing/test_size_and_seal.py", "sizing/test_size_and_seal_local.py", "integration/test_stage_a_library.py", "structure/test_removed_names.py"]
env = dict(os.environ, OPENBLAS_NUM_THREADS="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1", RED_CAP_OUT=OUT, PYTHONPATH=PLUG)
for f in FILES:
    subprocess.run([sys.executable, "-m", "pytest", "gmid_engine/tests/" + f, "-q", "-p", "red_cap", "-p", "no:cacheprovider", "--tb=no", "--continue-on-collection-errors"], cwd=ROOT, env=env, capture_output=True)
