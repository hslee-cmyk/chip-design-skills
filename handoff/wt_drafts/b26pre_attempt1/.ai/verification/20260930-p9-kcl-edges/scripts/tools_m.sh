#!/usr/bin/env bash
# P9 순서 7: $1=fast -> V4·V5·V6·V7, v3 -> V3(--timeout $2). base 판 캐시 도구를 스크립트 형태(-P 없이). 출력 C:/g47/out/tool_<V>.txt
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=7535799302a9ff7cfbfcadb2281d16bf136fadcf; M=b7765b047ac510b7150a3b99b102891e4083e970
C=C:/g47/gmid-gate-cache/$B; PY=C:/Python314/python.exe; R=C:/g47/m; O=C:/g47/out
run() { local tag=$1; shift; rm -rf C:/g47/pyc_t_$tag; mkdir -p C:/g47/pyc_t_$tag; s=$(date +%s); PYTHONPYCACHEPREFIX=C:/g47/pyc_t_$tag "$@" > $O/tool_$tag.txt 2>&1; echo "$tag exit $? $(( $(date +%s)-s ))s" >> $O/status_tools.txt; }
if [ "$1" = fast ]; then
run V5 $PY $C/weakening_diff.py --root $R --base $B --head $M
run V6 $PY $C/source_lint.py --root $R --base $B --head $M
run V7 $PY $C/reachability.py --root $R --base $B --head $M
run V4 $PY $C/test_lint.py --root $R --base $B --head $M --subject stick_diagram:kcl_series_union --subject stick_diagram:_kcl_and_matching_edges
fi
if [ "$1" = v3 ]; then
rm -f $O/v3_mut.jsonl
run V3 $PY $C/mutate_changed.py --root $R --base $B --head $M --pytest-ini $C/pytest_gate.ini --timeout $2 --gmid-phase=2 --gmid-strict= --out $O/v3_mut.jsonl
fi
echo "DONE $1" >> $O/status_tools.txt
