#!/usr/bin/env bash
# DF-35 순서 7: $1=fast -> V4·V5·V6·V7, v3 -> V3. base 판 캐시 도구를 스크립트 형태(-P 없이). 출력 C:/g14/out/tool_<V>.txt
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=c4e5fef0d8ad6ba8eddbd8e2fb6c81a5ceea20da; M=d23f4bb629ed33f8cea4299f128e934660a23cde
C=C:/g14/gmid-gate-cache/$B; PY=C:/Python314/python.exe; R=C:/g14/m; O=C:/g14/out
run() { local tag=$1; shift; rm -rf C:/g14/pyc_t_$tag; mkdir -p C:/g14/pyc_t_$tag; PYTHONPYCACHEPREFIX=C:/g14/pyc_t_$tag "$@" > $O/tool_$tag.txt 2>&1; echo "$tag exit $?" >> $O/status_tools.txt; }
if [ "$1" = fast ]; then
run V5 $PY $C/weakening_diff.py --root $R --base $B --head $M
run V6 $PY $C/source_lint.py --root $R --base $B --head $M
run V7 $PY $C/reachability.py --root $R --base $B --head $M
run V4card $PY $C/test_lint.py --root $R --base $B --head $M --interface-card $R/docs/02-design/specs/20260930-df35-harness-paths.interface.md
run V4files $PY $C/test_lint.py --root $R --base $B --head $M
fi
if [ "$1" = v3 ]; then
run V3 $PY $C/mutate_changed.py --root $R --base $B --head $M --pytest-ini $C/pytest_gate.ini --gmid-phase=2 --gmid-strict= --out $O/v3_mut.json
fi
echo "DONE $1" >> $O/status_tools.txt
