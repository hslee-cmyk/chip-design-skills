import_any() {   # $1 = 체크아웃된 트리 루트. N3.10 파일과 --split 파일 중 있는 것을 각각 새 프로세스에서 맨 처음 import
  local A="$1/skills/analog-gmid-design/assets" m mods split exp n_try=0 n_fail=0
  mods=$($PY -c 'import sys; sys.path.insert(0, sys.argv[1]); import import_layering as il; print(" ".join(il.mod_table(open(sys.argv[2], encoding="utf-8").read())))' \
         "$GC" "$1/docs/01-plan/features/gain-budget-gmid-sizing.plan.md") || { echo "IMPORT-ANY INVALID: 모듈 목록 계산 실패"; return 2; }
  mods=$(printf '%s' "$mods" | tr -d '\r')
  split=$(printf '%s\n' "${MP_ARGS[@]}" | sed -n '/^--split$/,/^--keep$/p' | grep '\.py$' | sed 's/\.py$//')
  [ -n "$mods" ] && [ -n "$split" ] || { echo "IMPORT-ANY INVALID: 모듈 목록이 비었다"; return 2; }
  # 기대 수(독립 계산): import_layering의 present(N3.10 중 있는 파일) ∪ 트리에 있는 --split 파일
  local pres; pres=$($PY "$GC/import_layering.py" --root "$1" | $PY -c 'import json,sys; print("\n".join(json.load(sys.stdin)["present"]))') \
    || { echo "IMPORT-ANY INVALID: import_layering present 계산 실패"; return 2; }
  exp=$( { printf '%s\n' "$pres"; for m in $split; do [ -f "$A/$m.py" ] && echo "$m"; done; } | tr -d '\r' | sort -u | grep -c .)
  for m in $(printf '%s\n' $mods $split | sort -u); do
    [ -f "$A/$m.py" ] || continue
    n_try=$((n_try + 1))
    ( cd "$A" && $PY -c "import $m" ) > /dev/null 2>&1 || { echo "IMPORT-ANY FAIL: $m"; n_fail=$((n_fail + 1)); }
  done
  echo "IMPORT-ANY tried=$n_try expected=$exp failed=$n_fail"
  [ "$n_try" -gt 0 ] && [ "$n_try" -eq "$exp" ] || { echo "IMPORT-ANY INVALID: 시도 수 $n_try ≠ 기대 수 $exp"; return 2; }
  [ "$n_fail" -eq 0 ]
}
