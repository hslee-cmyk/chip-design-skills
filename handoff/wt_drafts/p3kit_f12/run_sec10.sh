#!/usr/bin/env bash
# F1/F2 작성 전 실측(측정 전용): design 30 v8.5 §10 bash 블록의 E3·E3b·IMPORT-ANY를 문서에서 그대로 잘라 격리 복제본의 한 커밋에서 실행한다.
#   bash run_sec10.sh <design md> <ISO 복제본(C:/g202/...)> <HEAD로 볼 rev> <B0 rev> <출력 파일> [noexcl]
# ISO를 그 rev로 detach 체크아웃한다(복제본 전용 -- C:/g202 밖이면 멈춘다). noexcl이면 제외 집합(D-9)을 비워 깨지는 판정 기록 스크립트를 본다(측정용).
set -u
DOC="$1"; ISO="$2"; REV="$3"; B0V="$4"; OUTF="$5"; MODE="${6:-}"
case "$ISO" in C:/g202/*) ;; *) echo "ISO가 C:/g202 밖: $ISO"; exit 2;; esac
export APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE" TMP=C:/g202/tmp TEMP=C:/g202/tmp
BLK=$(mktemp -p C:/g202/tmp); IA=$(mktemp -p C:/g202/tmp)
sed -n '/^# ---- E3: shim 삭제/,/^# ---- E4 ----$/p' "$DOC" | sed '$d' > "$BLK"
sed -n '/^# ---- IMPORT-ANY/,/^import_any "\$ISO"$/p' "$DOC" > "$IA"
[ "$MODE" = noexcl ] && sed -i "s/^EXCL=.*/EXCL='^\$'   # 측정용: 제외 없음/" "$BLK"
git -C "$ISO" checkout -q --detach "$REV" || { echo "checkout 실패" >> "$OUTF"; exit 2; }
S=$(mktemp -d -p C:/g202/tmp)
{
  echo "---- rev=$(git -C "$ISO" rev-parse --short HEAD) B0=$B0V mode=${MODE:-default} 블록 줄 수 E3/E3b=$(wc -l < "$BLK") IMPORT-ANY=$(wc -l < "$IA")"
  ( ISO="$ISO"; PY="C:/Python314/python.exe -B"; B0="$B0V"; GC="$ISO/tools/gates"
    MP_ARGS=(--plan docs/01-plan/features/gain-budget-gmid-sizing.plan.md
             --registry docs/03-analysis/gain-budget-gmid-sizing.function-registry.md
             --split sizing_recipe.py stick_diagram.py topology_library.py design_report.py audit_current_forced.py
             --keep audit_current_forced.py
             --aliases '{"optimizer": "theta_search.py"}')
    source "$BLK"; source "$IA" ) 2>&1 | tr -d '\r'
} >> "$OUTF"
rm -rf "$S" "$BLK" "$IA"
