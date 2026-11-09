#!/usr/bin/env bash
# measure only: M10 rejection variants on M9 + proto test (non-real tests), plus ORDER/AST facts. args: none
export TMP=C:/g323/tmp TEMP=C:/g323/tmp APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE" PYTHONIOENCODING=utf-8
R=C:/g323/r; GC=C:/g323/cache/tools/gates; O=C:/g323/out; G="git -C $R -c user.name=m -c user.email=m@x"
M9=9e2651da8c09ada5099eb73e21c95807118b4e64
TST=skills/analog-gmid-design/assets/tests/integration/test_m10_entry_proto.py
for V in none import_via_shim imports_workspaces const_literal print_dropped search_default_dropped keep_dead_imports no_wire; do
  $G checkout -q -B neg_$V $M9; D=$R/skills/analog-gmid-design/assets/tests/integration; mkdir -p $D
  cp C:/g323/kit/m10proto/test_m10_entry_proto.py C:/g323/kit/m10proto/_m10_scen.py $D/; cp $O/m10_golden.json $D/
  if [ $V = none ]; then C:/Python314/python.exe -B C:/g323/kit/gen_m10b.py $R $GC > /dev/null; else C:/Python314/python.exe -B C:/g323/kit/gen_m10b.py $R $GC --variant $V > /dev/null; fi
  $G add -A skills workspaces; $G commit -q -m "neg $V"
  PYTHONPATH=$GC PYTHONDONTWRITEBYTECODE=1 C:/Python314/python.exe -P -m pytest -c $GC/pytest_gate.ini --rootdir=$R --confcutdir=$R "$R/$TST" -k "not real_run" --gmid-phase=3 -q -p no:cacheprovider > $O/negm10_$V.txt 2>&1
  r=$?; f=$(grep -E "^FAILED|^ERROR" $O/negm10_$V.txt | sed 's/.*:://; s/ - .*//' | tr '\n' ' ')
  echo "$V pytest_exit=$r $(tail -1 $O/negm10_$V.txt) FAILED: $f" >> $O/negm10.txt
done
echo finished >> $O/negm10.txt
