#!/usr/bin/env bash
# measure only: unit/ tests at T1 head with --shuffle-seed 1..5 (C9 D3 precedent), worktree C:/g323/pt
export APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE" TMP=C:/g323/tmp TEMP=C:/g323/tmp PYTHONIOENCODING=utf-8
PT=C:/g323/pt; GC=C:/g323/cache/tools/gates; O=C:/g323/out
git -C $PT checkout -q --detach "$1"; git -C $PT clean -qfdx
for s in 1 2 3 4 5; do t=$(date +%s)
  PYTHONPATH="$GC" PYTHONPYCACHEPREFIX="$(mktemp -d)" C:/Python314/python.exe -P -m pytest -c "$GC/pytest_gate.ini" --rootdir=$PT --confcutdir=$PT \
    "$PT/skills/analog-gmid-design/assets/tests/unit" --gmid-phase=3 -q -p no:cacheprovider --shuffle-seed=$s > "$O/t1_shuffle_$s.txt" 2>&1
  echo "seed=$s exit=$? s=$(( $(date +%s)-t )) $(tail -1 $O/t1_shuffle_$s.txt)" >> $O/t1_shuffle.txt
done
echo finished >> $O/t1_shuffle.txt
