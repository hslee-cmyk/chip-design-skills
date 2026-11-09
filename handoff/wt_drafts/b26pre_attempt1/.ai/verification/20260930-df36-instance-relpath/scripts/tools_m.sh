#!/usr/bin/env bash
# DF-36 순서 7: $1=fast -> V4·V5·V6·V7, v3 -> V3. base 판 캐시 도구를 스크립트 형태(-P 없이). 출력 C:/g16/out/tool_<V>.txt
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=070cf6937e2841bdd3b4781eb9b8ba5bba9cc606; M=b29be01281e66cc041e7e507a946b5373092a346
C=C:/g16/gmid-gate-cache/$B; PY=C:/Python314/python.exe; R=C:/g16/m; O=C:/g16/out
run() { local tag=$1; shift; rm -rf C:/g16/pyc_t_$tag; mkdir -p C:/g16/pyc_t_$tag; PYTHONPYCACHEPREFIX=C:/g16/pyc_t_$tag "$@" > $O/tool_$tag.txt 2>&1; echo "$tag exit $?" >> $O/status_tools.txt; }
if [ "$1" = fast ]; then
run V5 $PY $C/weakening_diff.py --root $R --base $B --head $M
run V6 $PY $C/source_lint.py --root $R --base $B --head $M
run V7 $PY $C/reachability.py --root $R --base $B --head $M
run V4 $PY $C/test_lint.py --root $R --base $B --head $M --subject stick_diagram:save_instance_json --subject stick_diagram:_topology_ref_relpath
fi
if [ "$1" = v3 ]; then
run V3 $PY $C/mutate_changed.py --root $R --base $B --head $M --pytest-ini $C/pytest_gate.ini --gmid-phase=2 --gmid-strict= --out $O/v3_mut.json
fi
echo "DONE $1" >> $O/status_tools.txt
