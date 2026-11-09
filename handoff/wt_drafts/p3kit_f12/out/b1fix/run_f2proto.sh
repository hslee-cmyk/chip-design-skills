#!/usr/bin/env bash
# F2 prototype (contract 6) on old F2 mock da36b86 (B34 string not rewritten) and fixed F2 mock 35d83ca. No cd.
export TMP=C:/g347/tmp TEMP=C:/g347/tmp APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE"
K=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/p3kit_f12; R=/c/g347/f/r
for c in da36b86 35d83ca; do
  W="C:/g347/w_$c"
  [ -d "$W" ] || git -C "$R" worktree add -q --detach "$W" "$c"
  P3SD_ROOT="$W" P3SD_REPORT="C:/g347/out/f2proto_unres_$c.txt" PYTHONPYCACHEPREFIX=C:/g347/tmp/pyc C:/Python314/python.exe -P -m pytest \
    -q -p no:cacheprovider --rootdir=C:/g347/out C:/g347/out/test_p3sd_proto.py > "C:/g347/out/f2proto_$c.txt" 2>&1
  echo "$c rc=$? $(tail -1 "C:/g347/out/f2proto_$c.txt")"
done
