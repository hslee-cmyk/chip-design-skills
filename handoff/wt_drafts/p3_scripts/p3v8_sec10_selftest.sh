#!/usr/bin/env bash
# design v8 §10 bash 블록의 E3·E3b를 문서에서 그대로 잘라(v8과 v7 둘 다) 합성 커밋에서 실행한다(5차 검토 B2·S2 확인).
# 스크래치 복제본 전용: ISO가 C:/g113 아래가 아니면 멈춘다. 결과는 OUTF에 시나리오마다 append.
# 사용: p3v8_sec10_selftest.sh <design v8 md> <design v7 md> <iso 복제본> <p3v8_e3b_synth.json> <OUTF>
set -u
DOC="$1"; DOC7="$2"; ISO="$3"; SYN="$4"; OUTF="$5"
case "$(cd "$ISO" && pwd -W 2>/dev/null || pwd)" in C:/g113/*|/c/g113/*) ;; *) echo "ISO가 C:/g113 밖: $ISO"; exit 2;; esac
export APPDATA="C:/Users/HSLEE/AppData/Roaming"; export HOME="C:/Users/HSLEE"
PY="C:/Python314/python.exe -B"
B0=$($PY -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8"))["base"])' "$SYN" | tr -d '\r')
rev() { $PY -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8"))[sys.argv[2]])' "$SYN" "$1" | tr -d '\r'; }
BLK8=$(mktemp); BLK7=$(mktemp); BLK8X=$(mktemp)
sed -n '/^# ---- E3: shim 삭제/,/^# ---- E4 ----$/p' "$DOC" | sed '$d' > "$BLK8"
sed -n '/^# ---- E3: shim 삭제/,/^# ---- E4 ----$/p' "$DOC7" | sed '$d' > "$BLK7"
# S2 측정용: v8 블록에서 제외 집합만 '아무것도 빼지 않음'으로 바꾼 사본(판정 명령이 아니라 .ai/verification 파일의 깨짐을 보려는 측정)
sed "s/^EXCL=.*/EXCL='^\$'   # 측정용: 제외 없음/" "$BLK8" > "$BLK8X"
{ echo "== $(date -Iseconds) 잘라낸 줄 수: v8 $(wc -l < "$BLK8"), v7 $(wc -l < "$BLK7"); diff(v7→v8):"; diff "$BLK7" "$BLK8"; echo "B0(기본)=$B0"; } >> "$OUTF"
S=$(mktemp -d)
run_e3() {   # $1 = 시나리오, $2 = 체크아웃할 rev, $3 = 블록, $4 = (선택) B0 대체값
  git -C "$ISO" checkout -q --detach "$2" || { echo "checkout 실패 $2" >> "$OUTF"; return; }
  { echo "---- [$1] HEAD=$(git -C "$ISO" rev-parse --short HEAD) 블록=$3 B0=${4:-$B0}"
    ( B0="${4:-$B0}"; source "$3" ) 2>&1 | tr -d '\r' | sed -n '1,400p'
  } >> "$OUTF"
}
run_e3 "v7 E3b @ syn/b2head, B0=syn/b2base (5차 검토 B2 결함 재현 -- PASS가 나오면 재현)" "$(rev syn/b2head)" "$BLK7" "$(rev syn/b2base)"
run_e3 "v8 E3b @ syn/b2head, B0=syn/b2base (FAIL 기대: star·동적·파싱 오류 세 줄)"        "$(rev syn/b2head)" "$BLK8" "$(rev syn/b2base)"
run_e3 "v8 E3b @ base(분할 전, HEAD = B0) (INVALID 기대)"                                    "$B0"               "$BLK8"
run_e3 "v8 E3b @ syn/m9 (정상 M9 모의 -- PASS 기대)"                                         "$(rev syn/m9)"     "$BLK8"
run_e3 "v8 E3b @ syn/f2drop (F1 없는 F2 -- FAIL 기대)"                                       "$(rev syn/f2drop)" "$BLK8"
run_e3 "측정(S2): v8 블록·제외 없음 @ syn/f2drop -- .ai/verification FAIL 줄을 본다"          "$(rev syn/f2drop)" "$BLK8X"
git -C "$ISO" checkout -q --detach "$B0"
echo "== 끝 $(date -Iseconds)" >> "$OUTF"
rm -rf "$S" "$BLK8" "$BLK7" "$BLK8X"
