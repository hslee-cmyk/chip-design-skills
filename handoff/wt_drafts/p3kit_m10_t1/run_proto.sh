#!/usr/bin/env bash
# measure only: run a pytest target at given revs of the sandbox clone. args: <test rel path> <label> <rev>...
export TMP=C:/g323/tmp TEMP=C:/g323/tmp APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE" PYTHONIOENCODING=utf-8
R=C:/g323/r; GC=C:/g323/cache/tools/gates; T="$1"; L="$2"; shift 2
for rev in "$@"; do
  git -C $R checkout -q --detach "$rev"; git -C $R clean -qfdx -- skills workspaces
  s=$(date +%s)
  out="C:/g323/out/${L}_${rev}.txt"
  PYTHONPATH=$GC PYTHONDONTWRITEBYTECODE=1 C:/Python314/python.exe -P -m pytest -c $GC/pytest_gate.ini --rootdir=$R --confcutdir=$R "$R/$T" --gmid-phase=3 -q -p no:cacheprovider --durations=0 > "$out" 2>&1
  echo "$rev exit=$? s=$(( $(date +%s)-s ))"; grep -E "passed|failed|error" "$out" | tail -2
done
