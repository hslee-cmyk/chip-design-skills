#!/usr/bin/env bash
# design 30 §10 PT3(10 §10 PT에서 --gmid-phase=1만 =3) -- 측정 전용 실행기.
#   bash pt3.sh <iso 루트> <게이트 캐시 tools/gates 디렉터리> <출력 파일> [test 경로(iso 기준 상대)…] [-- pytest 옵션…]
# test 경로가 없으면 tests 전체. 출력 파일에 pytest 출력 전부를 쓴다(WP-11). 종료 코드 = pytest 종료 코드.
set -u
ISO=$1; CACHE=$2; OUT=$3; shift 3
export APPDATA='C:\Users\HSLEE\AppData\Roaming' HOME='C:\Users\HSLEE' PYTHONIOENCODING=utf-8
paths=(); opts=()
while [ $# -gt 0 ]; do
  if [ "$1" = "--" ]; then shift; opts=("$@"); break; fi
  paths+=("$ISO/$1"); shift
done
[ ${#paths[@]} -eq 0 ] && paths=("$ISO/skills/analog-gmid-design/assets/tests")
PYTHONPATH="$CACHE" PYTHONPYCACHEPREFIX="$(mktemp -d)" C:/Python314/python.exe -P -m pytest -c "$CACHE/pytest_gate.ini" \
  --rootdir="$ISO" --confcutdir="$ISO" "${paths[@]}" --gmid-phase=3 "${opts[@]}" > "$OUT" 2>&1
rc=$?
tail -n 3 "$OUT"
echo "pt3 rc=$rc"
exit $rc
