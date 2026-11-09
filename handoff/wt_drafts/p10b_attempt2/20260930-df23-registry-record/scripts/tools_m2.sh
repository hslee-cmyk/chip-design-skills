#!/usr/bin/env bash
# 재시도 2차 순서 7 게이트 도구(V3·V4·V5·V6·V7): base 판 캐시, 스크립트 형태(-P 없이), 병합본 격리 복제본 C:/g88/m2t.
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=0f237862c007f6a53122f2bdfb3c87e6366ec133; M=e67211cd528850d14b585298cb499f8a76767182
C=C:/g88/gmid-gate-cache/$B; PY=C:/Python314/python.exe; O=C:/g88/out3; R=C:/g88/m2t
A=skills/analog-gmid-design/assets
cd C:/g88
run() { local tag=$1; shift; local P=C:/g88/pyc3_t_$tag; rm -rf $P; mkdir -p $P; PYTHONPYCACHEPREFIX=$P "$@" > $O/tool_$tag.txt 2>&1; echo "$tag exit $?" >> $O/status_tools.txt; }
run V5 $PY $C/weakening_diff.py --root $R --base $B --head $M
run V6 $PY $C/source_lint.py --root $R --base $B --head $M
run V7 $PY $C/reachability.py --root $R --base $B --head $M
run V4card $PY $C/test_lint.py --root $R --base $B --head $M --module-dir $A/tests/tools --interface-card $R/docs/02-design/specs/20260930-df23-registry-record.interface.md
run V4subj $PY $C/test_lint.py --root $R --base $B --head $M --module-dir $A/tests/tools --subject reg_check:check_df23 --subject reg_check:main
run V3 $PY $C/mutate_changed.py --root $R --base $B --head $M --pytest-ini $C/pytest_gate.ini --python $PY --gmid-phase=2 --gmid-strict= --out $O/v3_mut.jsonl
echo DONE >> $O/status_tools.txt
