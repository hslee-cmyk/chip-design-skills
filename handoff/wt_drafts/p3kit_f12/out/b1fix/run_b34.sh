#!/usr/bin/env bash
# B34 test file only, PT3 style (gate 6c724de pytest_gate.ini), one worktree per commit -- no cd.
export TMP=C:/g347/tmp TEMP=C:/g347/tmp APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE"
R=/c/g347/f/r
[ -d /c/g347/gt/tools/gates ] || { mkdir -p /c/g347/gt && git -C "$R" archive 6c724de tools/gates | tar -x -C /c/g347/gt; }
for c in "$@"; do
  W="C:/g347/w_$c"
  [ -d "$W" ] || git -C "$R" worktree add -q --detach "$W" "$c"
  PYTHONPATH=C:/g347/gt/tools/gates PYTHONPYCACHEPREFIX=C:/g347/tmp/pyc C:/Python314/python.exe -P -m pytest \
    -c C:/g347/gt/tools/gates/pytest_gate.ini --rootdir="$W" --confcutdir="$W" \
    "$W/skills/analog-gmid-design/assets/tests/contracts/test_b34_grammar_explicit.py" --gmid-phase=3 -q -p no:cacheprovider \
    > "C:/g347/out/b34_$c.txt" 2>&1
  echo "$c rc=$? $(tail -1 "C:/g347/out/b34_$c.txt")"
done
