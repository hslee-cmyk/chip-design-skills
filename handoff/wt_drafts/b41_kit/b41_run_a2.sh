#!/usr/bin/env bash
# B41 측정 A 2단계(복제본·gate 사본은 b41_run_a.sh가 만든 것): kill 증명. 사용: bash b41_run_a2.sh /c/g211
# (b41_run_a.sh 1차 실행은 pytest에 --gmid-phase를 넘기지 않아 기준 실행 ERROR -- b41_kill.py가 GMID_PHASE를 넘기게 고친 뒤 이 단계만 다시 돈다)
set -euo pipefail
S=$1
K=$(cd "$(dirname "$0")" && pwd)
PY=/c/Python314/python.exe
case "$S" in /c/g211*) ;; *) echo "스크래치는 /c/g211 아래만"; exit 2;; esac
export APPDATA="C:/Users/HSLEE/AppData/Roaming" TMP="C:/g211/tmp" TEMP="C:/g211/tmp" TMPDIR="C:/g211/tmp" PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 GMID_PHASE=3
R="$S/repo"
test -z "$(git -C "$R" remote)"
test "$(git -C "$R" rev-parse HEAD)" = 36e170eec5b9e893c03927e5bb45635071de7e69
sha256sum "$K"/*.py "$K"/*.sh > "$S/out/kit.a2.sha256"
T=skills/analog-gmid-design/assets/tests/contracts/test_instance_scope_note.py
rm -f "$S/out/kill_existing.jsonl" "$S/out/kill_new.jsonl"
# (a) 기존 inventory 대표(test_df36·test_ic3·test_s088): 4개 생존 기대 (p10과 같은 사실을 직접 재현)
$PY -B -P "$K/b41_kill.py" "$R" "$S/gate" "$S/gate/pytest_gate.ini" "$S/out/kill_existing.jsonl" \
  skills/analog-gmid-design/assets/tests/contracts/test_df36_instance_relpath.py \
  skills/analog-gmid-design/assets/tests/contracts/test_ic3.py \
  "skills/analog-gmid-design/assets/tests/unit/test_selftest_stick_diagram.py::test_s088_save_instance_json" \
  | tee "$S/out/kill_existing.summary.txt"
# (b) 새 test만: stmt_delete 2개 죽음, indent 2개 생존 기대
cp "$K/test_instance_scope_note.py" "$R/$T"
$PY -B -P "$K/b41_kill.py" "$R" "$S/gate" "$S/gate/pytest_gate.ini" "$S/out/kill_new.jsonl" "$T" | tee "$S/out/kill_new.summary.txt"
rm -f "$R/$T"
git -C "$R" status --porcelain | tee "$S/out/status_after_a2.txt"
