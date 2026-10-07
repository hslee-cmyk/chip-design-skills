# usage: bash v1.sh <clone_root> <label>   -- V1 형태 전체 실행(-k·--deselect·-x 없음), cwd = 복제본 루트(env -C)
set -euo pipefail
ROOT=$1; LABEL=$2
C=C:/g394/gmid-gate-cache/863a037cc0d774bb984006ea39966c5e4dd741ab
mkdir -p C:/g394/out C:/g394/pyc/v1_$LABEL C:/g394/tmp/$LABEL
export APPDATA=C:/Users/HSLEE/AppData/Roaming HOME=C:/Users/HSLEE PYTHONIOENCODING=utf-8
export TMP=C:/g394/tmp/$LABEL TEMP=C:/g394/tmp/$LABEL TMPDIR=C:/g394/tmp/$LABEL
export PYTHONHASHSEED=0
set +e
env -C $ROOT PYTHONPYCACHEPREFIX=C:/g394/pyc/v1_$LABEL PYTHONPATH=$C C:/Python314/python.exe -P -m pytest -c $C/pytest_gate.ini --rootdir=$ROOT --confcutdir=$ROOT $ROOT/skills/analog-gmid-design/assets/tests --gmid-phase=3 --gmid-strict= -rA > C:/g394/out/v1_$LABEL.txt 2>&1
rc=$?
set -e
echo "rc=$rc" >> C:/g394/out/v1_$LABEL.txt
tail -n 2 C:/g394/out/v1_$LABEL.txt
echo "status after: [$(git -C $ROOT status --porcelain --ignored | head -20 | tr '\n' ';')]"
