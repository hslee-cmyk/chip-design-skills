#!/usr/bin/env bash
# F1/F2 작성 전 실측(측정 전용): 격리 복제본 커밋 쌍(base -> head)에 base 판 게이트(G1 시제품 설치본)의 V3·V5·V6·V7 CLI를 돌린다.
#   bash run_vtools.sh <복제본 루트(C:/g202/...)> <base rev> <head rev> <출력 디렉터리> <이름>
set -u
export APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE" PYTHONIOENCODING=utf-8 TMP=C:/g202/tmp TEMP=C:/g202/tmp
ROOT=$1; B=$2; H=$3; OUT=$4; NM=$5
case "$ROOT" in C:/g202/*) ;; *) echo "scratch must be under C:/g202"; exit 2;; esac
PY=C:/Python314/python.exe
mkdir -p "$OUT"
GC=C:/g202/gc_$NM; rm -rf "$GC"; mkdir -p "$GC"; git -C "$ROOT" archive "$B" tools/gates | tar -x -C "$GC"; C="$GC/tools/gates"
for t in weakening_diff source_lint reachability; do
  s=$(date +%s); PYTHONPATH=$C "$PY" -B "$C/$t.py" --root "$ROOT" --base "$B" --head "$H" > "$OUT/${NM}_$t.json" 2>&1; echo "$NM $t exit $? $(( $(date +%s)-s ))s"
done
s=$(date +%s); PYTHONPATH=$C "$PY" -B "$C/mutate_changed.py" --root "$ROOT" --base "$B" --head "$H" --pytest-ini "$C/pytest_gate.ini" \
  --python C:/Python314/python.exe --gmid-phase=3 --gmid-strict= --out "$OUT/${NM}_v3.jsonl" > "$OUT/${NM}_mutate_changed.json" 2>&1; echo "$NM mutate_changed exit $? $(( $(date +%s)-s ))s"
rm -rf "$GC"
