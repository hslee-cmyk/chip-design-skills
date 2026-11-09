#!/usr/bin/env bash
# design v6 §10 bash 블록 중 E3·import_any 부분을 그 문서에서 그대로 잘라 실행한다(문서 문안 = 실행 문안 확인, 읽기 전용).
# 사용: p3v6_sec10_selftest.sh <design md> <iso> <base 대용 rev> <모의 트리 루트(선택)>
set -u
DOC="$1"; ISO="$2"; B0="$3"; SIMROOT="${4:-}"
PY="C:/Python314/python.exe -B"; GC="$ISO/tools/gates"
# 이 측정 환경(하위 bash)에서 APPDATA가 비어 사용자 site-packages(numpy)를 못 찾는다 -- 측정 환경 보정이지 문서 명령의 일부가 아니다
export PYTHONPATH="C:/Users/HSLEE/AppData/Roaming/Python/Python314/site-packages"
MP_ARGS=(--plan docs/01-plan/features/gain-budget-gmid-sizing.plan.md
         --registry docs/03-analysis/gain-budget-gmid-sizing.function-registry.md
         --split sizing_recipe.py stick_diagram.py topology_library.py design_report.py audit_current_forced.py
         --keep audit_current_forced.py
         --aliases '{"optimizer": "theta_search.py"}')
TMP=$(mktemp)
sed -n '/^# ---- E3: shim 삭제 ----$/,/^# ---- E4 ----$/p' "$DOC" > "$TMP"
sed -n '/^# ---- IMPORT-ANY/,/^import_any "\$ISO"$/p' "$DOC" | sed '$d' >> "$TMP"
echo "== 잘라낸 줄 수: $(wc -l < "$TMP")"
# shellcheck disable=SC1090
source "$TMP"
echo "== import_any on $ISO (HEAD 체크아웃)"
import_any "$ISO"; echo "(끝)"
if [ -n "$SIMROOT" ]; then
  echo "== import_any on 모의 M9 트리 $SIMROOT"
  import_any "$SIMROOT"; echo "(끝)"
fi
rm -f "$TMP"
