#!/usr/bin/env bash
# E-INST 사이트 줄 통과 횟수(참고값). 사용: einst_sites.sh <복제본> <회로>
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
R="$1"; CIR="$2"; O=C:/g12/out/einst_cov
mkdir -p "$O"
rm -rf C:/g12/ws_eq
PYTHONDONTWRITEBYTECODE=1 C:/Python314/python.exe -P C:/g12/scripts/e_inst_sites.py C:/g12/out/w_sites_base.json "$O/sites_$CIR.json" C:/g12/scripts/e_inst.py "$R" "$CIR" C:/g12/ws_eq "$O/einst_$CIR.json" > "$O/$CIR.log" 2>&1
echo "$CIR exit $?"
cat "$O/sites_$CIR.json"
