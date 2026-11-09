#!/usr/bin/env bash
# 순서 7 V2 green: 병합본에서 red 5건의 파일 3개를 -rA로, red 수집 플러그인을 켠 채 실행(허용 타입 red가 0이어야 한다)
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=efbf14a4908c27bc1e5481a5cde91b0cca57a693; C=C:/g10/gmid-gate-cache/$B; PY=C:/Python314/python.exe; R=C:/g10/m; O=C:/g10/out
T=$R/skills/analog-gmid-design/assets/tests
rm -f $O/red_m.jsonl; rm -rf C:/g10/pyc_green_m; mkdir -p C:/g10/pyc_green_m
GMID_RED_CAPTURE=$O/red_m.jsonl GMID_INTERFACE_CARD=$R/docs/02-design/specs/20260930-d-move-tests.interface.md PYTHONPYCACHEPREFIX=C:/g10/pyc_green_m PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R -p merge_gate --continue-on-collection-errors --gmid-phase=2 --gmid-strict= $T/contracts/test_d_move_tests.py $T/unit/test_selftest_sizing_recipe.py $T/unit/test_selftest_stick_diagram.py -rA -p no:cacheprovider > $O/green_m.txt 2>&1
echo "green_m exit $?" > $O/status_green.txt
