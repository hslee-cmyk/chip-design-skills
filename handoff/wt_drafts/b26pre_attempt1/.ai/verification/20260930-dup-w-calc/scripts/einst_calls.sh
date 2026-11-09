#!/usr/bin/env bash
# 병합본 E-INST에서 width_from_id_density 본문 줄(return, 병합본 101행)의 실행 횟수 = 호출 수(참고값, 시간 측정과 별도).
# 사용: einst_calls.sh <복제본> <회로>
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
R="$1"; CIR="$2"; O=C:/g12/out/einst_calls
mkdir -p "$O"
rm -rf C:/g12/ws_eq
PYTHONDONTWRITEBYTECODE=1 C:/Python314/python.exe -P C:/g12/scripts/e_inst_sites.py C:/g12/out/newfn_line.json "$O/calls_$CIR.json" C:/g12/scripts/e_inst.py "$R" "$CIR" C:/g12/ws_eq "$O/einst_$CIR.json" > "$O/$CIR.log" 2>&1
echo "$CIR exit $?"
cat "$O/calls_$CIR.json"
