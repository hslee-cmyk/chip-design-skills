#!/bin/bash
# IT-1 V1 나머지(41faebe0): lut 는 파일 하나씩, 나머지는 디렉터리 하나씩 -- 한 번에 pytest 프로세스 하나, 순차.
# 끝난 단위는 done_<name> 표시가 있어 다시 돌리면 건너뛴다(중단 뒤 이어가기). usage: run_rest.sh <unit list file>
F=C:/Users/HSLEE/AppData/Local/Temp/claude/it1f
O=C:/Users/HSLEE/AppData/Local/Temp/claude/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922/scratchpad/it1-audit/final/r3
mkdir -p "$O"
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 APPDATA=C:/Users/HSLEE/AppData/Roaming
cd "$F/skills/analog-gmid-design" || exit 9
while read -r unit; do
  [ -z "$unit" ] && continue
  name=$(echo "$unit" | sed 's#gmid_engine/tests/##; s#/#__#g; s#\.py$##')
  [ -f "$O/done_$name" ] && continue
  C:/Python314/python.exe -m pytest -p no:cacheprovider -q -rfE --junitxml="$O/junit_$name.xml" "$unit" > "$O/run_$name.txt" 2>&1
  rc=$?
  echo "$name rc=$rc $(tail -1 "$O/run_$name.txt")" >> "$O/progress.txt"
  touch "$O/done_$name"
done < "$1"
echo "DONE $1" >> "$O/progress.txt"
