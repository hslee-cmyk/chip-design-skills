# red 재수집(순서 7 재확인): T 격리 복제본(base 엔진 + 새 test)에서 새 test 파일, merge_gate 플러그인, seed 0·1.
# 같은 명령을 M 복제본(green)에도 돌린다.
set -euo pipefail
W=C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261001-b26-backfill-interdig-final-audit-audit
T=3004096c81b839998518c14c16d3cd2d6ec6c9bf
C=C:/g394/gmid-gate-cache/863a037cc0d774bb984006ea39966c5e4dd741ab
D=C:/g394/isot
if [ ! -e $D ]; then
  git clone -q --no-hardlinks --no-local -c core.autocrlf=false -c core.longpaths=true --no-checkout $W $D
  git -C $D remote remove origin
  test -z "$(git -C $D remote)"
  git -C $D -c advice.detachedHead=false checkout -q --detach $T
fi
export APPDATA=C:/Users/HSLEE/AppData/Roaming HOME=C:/Users/HSLEE PYTHONIOENCODING=utf-8
for pair in "isot T" "iso M"; do
  set -- $pair; ROOT=C:/g394/$1; LB=$2
  for seed in 0 1; do
    L=red7_${LB}_s$seed
    mkdir -p C:/g394/tmp/$L C:/g394/bt
    rm -f C:/g394/out/$L.jsonl
    set +e
    env -C $ROOT TMP=C:/g394/tmp/$L TEMP=C:/g394/tmp/$L TMPDIR=C:/g394/tmp/$L PYTHONHASHSEED=$seed \
      PYTHONPYCACHEPREFIX=C:/g394/pyc/$L PYTHONPATH=$C GMID_RED_CAPTURE=C:/g394/out/$L.jsonl \
      GMID_INTERFACE_CARD=$ROOT/docs/02-design/specs/20261001-b26-backfill-interdig-final-audit.interface.md \
      C:/Python314/python.exe -P -m pytest -c $C/pytest_gate.ini --rootdir=$ROOT --confcutdir=$ROOT \
      --gmid-phase=3 --gmid-strict= -p merge_gate --continue-on-collection-errors --basetemp=C:/g394/bt/$L \
      -p no:cacheprovider -rA -q $ROOT/skills/analog-gmid-design/assets/tests/contracts/test_b26_backfill_interdig.py \
      > C:/g394/out/$L.txt 2>&1
    rc=$?
    set -e
    echo "rc=$rc" >> C:/g394/out/$L.txt
    echo "== $L"; grep -E "^(PASSED|FAILED|E  +assert)|passed|failed" C:/g394/out/$L.txt | head -20
    [ -e C:/g394/out/$L.jsonl ] && cat C:/g394/out/$L.jsonl || echo "(capture 없음)"
  done
done
echo "isot status [$(git -C $D status --porcelain | tr '\n' ';')]"
