#!/usr/bin/env bash
export TMP=C:/g369/tmp TEMP=C:/g369/tmp PYTHONIOENCODING=utf-8 APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE"
R=C:/g369/r; PT=C:/g369/pt; GC=C:/g369/cache/tools/gates; O=C:/g369/out
[ -d $PT ] || git -C $R worktree add -q --detach $PT 7fd4b16
for lr in t1base=7fd4b16 t1head=93d7c0a; do L=${lr%%=*}; V=${lr#*=}
  git -C $PT checkout -q --detach "$V"; git -C $PT clean -qfdx
  bash C:/g369/kit/pt3.sh $PT "$L" $GC $O
  echo "$L $V $(tail -2 $O/$L.pt3.txt | tr '\n' ' ')" >> $O/pt3_pair.txt
done
git -C $PT checkout -q --detach 93d7c0a; git -C $PT clean -qfdx
for s in 1 2 3 4 5; do t=$(date +%s)
  PYTHONPATH="$GC" PYTHONPYCACHEPREFIX="$(mktemp -d)" C:/Python314/python.exe -P -m pytest -c "$GC/pytest_gate.ini" --rootdir=$PT --confcutdir=$PT \
    "$PT/skills/analog-gmid-design/assets/tests/unit" --gmid-phase=3 -q -p no:cacheprovider --shuffle-seed=$s > "$O/t1_shuffle_$s.txt" 2>&1
  echo "seed=$s exit=$? s=$(( $(date +%s)-t )) $(tail -1 $O/t1_shuffle_$s.txt)" >> $O/t1_shuffle.txt
done
echo finished >> $O/t1_shuffle.txt
