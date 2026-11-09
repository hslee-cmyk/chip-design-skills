#!/usr/bin/env bash
# design v7 §10 bash 블록의 E3·E3b·import_any를 그 문서에서 그대로 잘라 합성 커밋·모의 트리에서 실행한다(4차 검토 N1·S1·S2 확인).
# 스크래치 복제본 전용: ISO가 C:/g95b 아래가 아니면 멈춘다. 결과는 OUTF에 시나리오마다 append(중간에 죽어도 남는다).
# 사용: p3v7_sec10_selftest.sh <design v7 md> <design v6 md> <iso 복제본> <synth.json> <모의 트리 root: top> <모의 트리 root: bottom7> <OUTF>
set -u
DOC="$1"; DOC6="$2"; ISO="$3"; SYN="$4"; TREE_TOP="$5"; TREE_B7="$6"; OUTF="$7"
case "$(cd "$ISO" && pwd -W 2>/dev/null || pwd)" in C:/g95b/*|/c/g95b/*) ;; *) echo "ISO가 C:/g95b 밖: $ISO"; exit 2;; esac
PY="C:/Python314/python.exe -B"; GC_OK="$ISO/tools/gates"
# 측정 환경 보정(하위 bash에서 APPDATA가 비어 사용자 site-packages를 못 찾는다) -- 문서 명령의 일부가 아니다
export PYTHONPATH="C:/Users/HSLEE/AppData/Roaming/Python/Python314/site-packages"
MP_ARGS=(--plan docs/01-plan/features/gain-budget-gmid-sizing.plan.md
         --registry docs/03-analysis/gain-budget-gmid-sizing.function-registry.md
         --split sizing_recipe.py stick_diagram.py topology_library.py design_report.py audit_current_forced.py
         --keep audit_current_forced.py
         --aliases '{"optimizer": "theta_search.py"}')
B0=$($PY -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8"))["base"])' "$SYN" | tr -d '\r')
rev() { $PY -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8"))[sys.argv[2]])' "$SYN" "$1" | tr -d '\r'; }
E3BLK=$(mktemp); E3OLD=$(mktemp); IABLK=$(mktemp); IAOLD=$(mktemp)
sed -n '/^# ---- E3: shim 삭제/,/^# ---- E4 ----$/p' "$DOC" | sed '$d' > "$E3BLK"
sed -n '/^# ---- E3: shim 삭제/,/^# ---- E4 ----$/p' "$DOC6" | sed '$d' > "$E3OLD"
sed -n '/^# ---- IMPORT-ANY/,/^import_any "\$ISO"$/p' "$DOC" | sed '$d' > "$IAOLD.new"; mv "$IAOLD.new" "$IABLK"
sed -n '/^# ---- IMPORT-ANY/,/^import_any "\$ISO"$/p' "$DOC6" | sed '$d' > "$IAOLD"
{ echo "== $(date -Iseconds) 잘라낸 줄 수: E3+E3b(v7) $(wc -l < "$E3BLK"), E3(v6) $(wc -l < "$E3OLD"), import_any(v7) $(wc -l < "$IABLK"), import_any(v6) $(wc -l < "$IAOLD")"; echo "B0=$B0"; } >> "$OUTF"
S=$(mktemp -d)

run_e3() {   # $1 = 시나리오 이름, $2 = 체크아웃할 rev, $3 = 블록 파일, $4 = (선택) B0 대체값
  git -C "$ISO" checkout -q --detach "$2" || { echo "checkout 실패 $2" >> "$OUTF"; return; }
  { echo "---- [$1] HEAD=$(git -C "$ISO" rev-parse --short HEAD) 블록=$(basename "$3") B0=${4:-$B0}"
    ( GC="$GC_OK"; B0="${4:-$B0}"; source "$3" ) 2>&1 | tr -d '\r' | sed -n '1,400p'
  } >> "$OUTF"
}
run_e3 "e3+e3b @ base(분할 전, a796468)"              "$B0"                "$E3BLK"
run_e3 "e3+e3b @ syn/m9(SD 재수출 유지)"              "$(rev syn/m9)"      "$E3BLK"
run_e3 "e3+e3b @ syn/dropone(재수출 하나 삭제)"        "$(rev syn/dropone)" "$E3BLK"
run_e3 "e3+e3b @ syn/f2drop(F1 없이 F2)"               "$(rev syn/f2drop)"  "$E3BLK"
run_e3 "e3+e3b @ syn/e3clean"                          "$(rev syn/e3clean)" "$E3BLK"
run_e3 "e3+e3b @ syn/e3nonascii(비ASCII importer)"     "$(rev syn/e3nonascii)" "$E3BLK"
run_e3 "v6 E3 @ syn/e3nonascii(옛 블록 -- fail-open 재현)" "$(rev syn/e3nonascii)" "$E3OLD"
run_e3 "v6 E3 @ syn/e3clean(옛 블록)"                  "$(rev syn/e3clean)" "$E3OLD"
run_e3 "e3+e3b @ syn/e3bnonascii(비ASCII SD reader)"   "$(rev syn/e3bnonascii)" "$E3BLK"
run_e3 "e3+e3b @ syn/m9, 고장 B0(없는 커밋) -- 도구 오류 = FAIL" "$(rev syn/m9)" "$E3BLK" deadbeefdeadbeefdeadbeefdeadbeefdeadbeef
git -C "$ISO" checkout -q --detach "$B0"

run_ia() {   # $1 = 이름, $2 = 트리, $3 = GC, $4 = 블록
  { echo "---- [$1] 트리=$2 GC=$3 블록=$(basename "$4")"
    ( GC="$3"; source "$4"; import_any "$2"; echo "import_any rc=$?" ) 2>&1 | tr -d '\r'
  } >> "$OUTF"
}
run_ia "import_any v7 @ 모의 M9 top(순환 있음), 올바른 GC"    "$TREE_TOP" "$GC_OK" "$IABLK"
run_ia "import_any v7 @ 모의 M9 bottom7(D-22 배치), 올바른 GC" "$TREE_B7"  "$GC_OK" "$IABLK"
run_ia "import_any v7 @ 모의 M9 top, 고장 GC(없는 경로)"       "$TREE_TOP" "C:/g95b/no_such_gates" "$IABLK"
run_ia "import_any v7 @ base 트리, 올바른 GC"                  "$ISO"      "$GC_OK" "$IABLK"
run_ia "import_any v7 @ 잘못된 트리 루트(assets 없음)"         "C:/g95b/no_such_tree" "$GC_OK" "$IABLK"
run_ia "import_any v6 @ 모의 M9 top, 고장 GC(옛 블록 -- 일부만 보고 재현)" "$TREE_TOP" "C:/g95b/no_such_gates" "$IAOLD"
echo "== 끝 $(date -Iseconds)" >> "$OUTF"
rm -rf "$S" "$E3BLK" "$E3OLD" "$IABLK" "$IAOLD"
