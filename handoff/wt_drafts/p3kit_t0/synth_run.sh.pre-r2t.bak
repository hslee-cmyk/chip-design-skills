#!/usr/bin/env bash
# T0 계약 6·7 + '거부해야 할 입력' 합성 트리 실행(측정 전용). 트리는 make_synth.py로 만든다.
#   bash synth_run.sh <scratch(C:/g<n>)> <게이트 캐시 tools/gates> <출력 디렉터리>
# 트리 이름: <scratch>/s_<move|copy|rebind>_<old|new>(old = base test, new = T0 시제품 test). 결과는 출력 디렉터리에 트리마다 파일 하나.
set -u
S=$1; CACHE=$2; OUT=$3
K="$(cd "$(dirname "$0")" && pwd)"
C=skills/analog-gmid-design/assets/tests/contracts
IDS=("$C/test_ic5.py::test_gate_docstring_declares_blind_spots"
     "$C/test_dup_w_calc.py::test_size_transistor_calls_new_function"
     "$C/test_ts6_dead_probes.py::test_sizing_recipe_source_has_no_l_role_multipliers"
     "$C/test_ts6_dead_probes.py::test_audit_vsb_consistency_has_operational_caller")
mkdir -p "$OUT"
for mode in move copy rebind; do
  for v in old new; do
    bash "$K/pt3.sh" "$S/s_${mode}_$v" "$CACHE" "$OUT/synth_${mode}_$v.txt" "${IDS[@]}" -- -q -rA -p no:cacheprovider > /dev/null
    echo "== $mode $v"; grep -E "^(PASSED|FAILED|ERROR) " "$OUT/synth_${mode}_$v.txt" | sed -E 's#^([A-Z]+) .*::#\1 #; s# - .*##'
  done
done
