#!/bin/bash
# 판정 test 순차 실행(격리 복제본, 전체 test 아님 -- O-229 범위). 결과는 out/ 파일로.
T=C:/Users/HSLEE/AppData/Local/Temp/la1s_op23_audit
R=$T/iso
PY=C:/Python314/python.exe
export PYTHONPYCACHEPREFIX=$T/pyc OPENBLAS_NUM_THREADS=1 PYTHONUTF8=1
O=$R/skills/analog-gmid-design/tools/spice_oracle
E=$R/skills/analog-gmid-design/gmid_engine/tests
cd $O && $PY -m pytest tests/adapters/ngspice/test_independent.py -q -p no:cacheprovider > $T/out/a3_11.txt 2>&1; echo "a3_11 rc=$?"
cd $R/skills/analog-gmid-design && $PY -m pytest gmid_engine/tests/core/test_oracle_descriptor_engine_sha.py gmid_engine/tests/metrics/test_verified_by.py -q -p no:cacheprovider > $T/out/a3_9_xtests.txt 2>&1; echo "xtests rc=$?"
cd $R/skills/analog-gmid-design && $PY -m pytest gmid_engine/tests/structure -q -p no:cacheprovider > $T/out/a3_9_structure.txt 2>&1; echo "structure rc=$?"
cd $R/skills/analog-gmid-design && $PY -m pytest gmid_engine/tests/integration/test_stage_b_library.py gmid_engine/tests/pipeline/test_stage_b.py gmid_engine/tests/integration/test_s0_layer_9circuits.py gmid_engine/tests/integration/test_g10_no_recompute_9circuits.py --run-slow -k "folded_cascode or ngcc_3stage_ff" -q -p no:cacheprovider > $T/out/a3_10_smoke.txt 2>&1; echo "smoke rc=$?"
