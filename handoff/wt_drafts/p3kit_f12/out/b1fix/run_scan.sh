#!/usr/bin/env bash
# exec-string full scan with SD deletion set (49) on F1 mock base / old F1 mock / fixed F1 mock / gate 6c724de. No cd.
export TMP=C:/g347/tmp TEMP=C:/g347/tmp
R=C:/g347/f/r; K=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/p3kit_f12; PY=C:/Python314/python.exe
"$PY" - <<'EOF'
import json, re
log = open("C:/g347/chain.log", encoding="utf-8").read()
m = re.search(r"stick_diagram\.py dropped 49 (\[.*?\])", log)
names = eval(m.group(1))
assert len(names) == 49
json.dump(names, open("C:/g347/out/sd_drop49.json", "w", encoding="utf-8"))
print("drop", len(names))
EOF
for c in 37f776a d37ffc5 a198913 6c724de; do
  echo "== $c"; "$PY" -B "$K/f12_execstr.py" "$R" "$c" "C:/g347/out/execstr_$c.json" --drop C:/g347/out/sd_drop49.json | cut -c1-600
done
