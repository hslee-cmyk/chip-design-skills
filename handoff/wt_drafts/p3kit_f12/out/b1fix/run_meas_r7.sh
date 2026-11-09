#!/usr/bin/env bash
# F2 r7 재측정(측정 전용 -- 6c724de 사슬). No cd. 케이스마다 $O/*.txt에 쓰고 요약을 $O/summary.txt에 append.
#   env: S(스크래치 C:/g*) R(사슬 복제본) B0(G1 커밋) REVS("이름=rev ...") K(p3kit_f12) DES(design 30 사본)
set -u
O="$S/out"; PY=C:/Python314/python.exe
export TMP="$S/tmp" TEMP="$S/tmp" APPDATA="${APPDATA:-C:/Users/HSLEE/AppData/Roaming}" HOME="${HOME:-C:/Users/HSLEE}" PYTHONDONTWRITEBYTECODE=1
EXCL='^(\.ai/verification/|docs/03-analysis/gain-budget-gmid-sizing-function-audit/probe_stage_partition\.py$)'
"$PY" -B "$K/out/b1fix/mk_e3_exec_r7.py" "$DES" "$O" "$K" || exit 1
cp -f "$K/test_p3_shim_delete.proto.py" "$O/test_p3sd_r7.py"; cp -f "$K/test_p3_shim_delete.proto.py.pre-r7.bak" "$O/test_p3sd_r6.py"
SUM="$O/summary.txt"; : > "$SUM"
for pair in $REVS; do
  nm=${pair%%=*}; h=${pair#*=}
  for e in ast exec; do
    F="$O/e3_${e}_$nm"
    {
      for f in sizing_recipe topology_library design_report; do
        git -C "$R" cat-file -e "$h:skills/analog-gmid-design/assets/$f.py" 2>/dev/null && echo "E3 FAIL: $f.py 있음"
      done
      "$PY" -c "$(cat "$O/e3_$e.py")" "$R" "$B0" 2>"$F.b0.err" | tr -d '\r' > "$F.b0.txt"; rc=${PIPESTATUS[0]}
      if [ "$rc" -ne 0 ]; then echo "E3 FAIL(도구 오류 rc=$rc rev=$B0)"; else
        { [ "$(grep -c '^stmt ' "$F.b0.txt")" -gt 0 ] && [ "$(grep -c '^call ' "$F.b0.txt")" -gt 0 ]; } || echo "E3 INVALID: base에서 빈 결과(명령 고장)"; fi
      "$PY" -c "$(cat "$O/e3_$e.py")" "$R" "$h" 2>"$F.head.err" | tr -d '\r' > "$F.head.txt"; rc=${PIPESTATUS[0]}
      if [ "$rc" -ne 0 ]; then echo "E3 FAIL(도구 오류 rc=$rc rev=$h)"; else
        OUT=$(sed 's/^[A-Za-z-]* //; s/:[0-9]*$//' "$F.head.txt" | sort -u | grep -v -E "$EXCL")
        [ -z "$OUT" ] && echo "E3 PASS" || { echo "E3 FAIL:"; echo "$OUT"; }; fi
    } > "$F.txt" 2>&1
    echo "E3[$e] $nm $h verdict=$(grep -E '^E3 (PASS|FAIL:|INVALID)' "$F.txt" | head -3 | tr '\n' ';') fail_files=$(sed -n '/^E3 FAIL:$/,$p' "$F.txt" | tail -n +2 | wc -l)" \
         "b0_stmt=$(grep -c '^stmt ' "$F.b0.txt") b0_call=$(grep -c '^call ' "$F.b0.txt") b0_exec=$(grep -c -E '^(exec-|EXEC-)' "$F.b0.txt")" \
         "head_lines=$(wc -l < "$F.head.txt") head_exec_hits=$(grep -c -E '^exec-(stmt|call) ' "$F.head.txt") head_exec_d9out=$(grep -E '^exec-(stmt|call) ' "$F.head.txt" | sed 's/^[a-z-]* //; s/:[0-9]*$//' | grep -v -E -c "$EXCL")" \
         "head_markers=$(grep -c -E '^EXEC-(PARSE-ERROR|FSTRING) ' "$F.head.txt") scanned=[$(grep -h exec_strings_scanned "$F.b0.err" "$F.head.err" | sed 's/RECORD //' | tr '\n' ' ')]" \
         "record_outside_head=$(grep -c '^RECORD outside' "$F.head.err")" >> "$SUM"
  done
  W="$S/w_$nm"
  [ -d "$W" ] || git -C "$R" worktree add -q --detach "$W" "$h"
  for v in r6 r7; do
    P3SD_KIT="$K" P3SD_ROOT="$W" P3SD_REPORT="$O/proto_${v}_unres_$nm.txt" P3SD_REPORT_A="$O/proto_${v}_imp_$nm.txt" \
      "$PY" -B -P -m pytest -q -p no:cacheprovider --rootdir="$O" "$O/test_p3sd_$v.py" > "$O/proto_${v}_$nm.txt" 2>&1; rc=$?
    echo "PROTO[$v] $nm rc=$rc $(tail -1 "$O/proto_${v}_$nm.txt") | b: $(head -1 "$O/proto_${v}_unres_$nm.txt" 2>/dev/null) | a: $(head -1 "$O/proto_${v}_imp_$nm.txt" 2>/dev/null)" \
         "failed=[$(grep -E '^FAILED' "$O/proto_${v}_$nm.txt" | sed 's/^FAILED [^:]*:://; s/ - .*//' | tr '\n' ' ')] nonassert=$(grep -E '^E +[A-Za-z]+(Error|Exception)' "$O/proto_${v}_$nm.txt" | grep -v -c AssertionError)" >> "$SUM"
  done
done
cat "$SUM"
