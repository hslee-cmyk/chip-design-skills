#!/usr/bin/env bash
# backfill card V2 사전 회귀(B34 위) -- 모의 사슬의 T(= BP + 이 card 시제품 test, base 엔진)와 H(= T + 수정 후보) git 복제본에서
# A/tests 전체를 한 번씩(PYTHONHASHSEED=1). .git이 있는 복제본이라 test_ts6_probe_relocate도 돈다(archive 사본 한계 없음).
#   bash run_fullsuite.sh <T> <H>   결과: C:/g128/out/fs_<t|h>.txt
set -euo pipefail
export HOME=/c/Users/HSLEE APPDATA=/c/Users/HSLEE/AppData/Roaming PYTHONIOENCODING=utf-8 TMP=C:/g128/tmp TEMP=C:/g128/tmp
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=1
T=$1; H=$2
for n in t h; do
  rev=$T; [ "$n" = h ] && rev=$H
  d=C:/g128/fs/$n
  if [ ! -e "$d" ]; then
    git clone -c core.autocrlf=false -q --no-hardlinks --no-local --no-checkout C:/g128/sim/r "$d"
    git -C "$d" remote remove origin
    git -C "$d" checkout -q --detach "$rev"
  fi
done
run() {
  local n=$1 d=C:/g128/fs/$1 t0 rc=0
  t0=$(date +%s)
  PYTHONPYCACHEPREFIX=C:/g128/fs/pyc_$n C:/Python314/python.exe -P -m pytest -c C:/g128/gate0/tools/gates/pytest_gate.ini --rootdir=$d --confcutdir=$d \
    -q -rfE --color=no -p no:cacheprovider --gmid-phase=2 --gmid-strict= $d/skills/analog-gmid-design/assets/tests > C:/g128/out/fs_$n.full.txt 2>&1 || rc=$?
  { echo "rev=$(git -C $d rev-parse HEAD) rc=$rc elapsed_s=$(( $(date +%s) - t0 ))"; grep -E "^(FAILED|ERROR)" C:/g128/out/fs_$n.full.txt || true; tail -1 C:/g128/out/fs_$n.full.txt; } > C:/g128/out/fs_$n.txt
}
run t & run h & wait
cat C:/g128/out/fs_t.txt C:/g128/out/fs_h.txt
