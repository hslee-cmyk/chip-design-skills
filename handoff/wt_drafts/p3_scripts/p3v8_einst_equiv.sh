#!/usr/bin/env bash
# design v8 §10 E5(5차 검토 S1) 확인: e_inst_p3.py(제안 사본)가 F1 전 트리에서 e_inst_df36.py와 같은 출력(engine_origin 제외)·같은 stdout을 내는지,
# F1(하네스 import 교체) 뒤 근사 트리에서 df36은 깨지고 p3는 도는지, e_lib.py가 근사 F2 트리에서 도는지.
# 스크래치 복제본 전용(C:/g113 아래). 결과는 OUTF에 append(케이스마다).
# 사용: p3v8_einst_equiv.sh <iso 복제본> <p3v8_e3b_synth.json> <e_inst_p3.py> <작업 dir(iso 밖)> <OUTF> [rest]
# rest: 출력 JSON이 이미 있는 케이스는 건너뛴다(첫 실행이 30분 백그라운드 한도로 끊긴 뒤 이어 돌리기)
set -u
ISO="$1"; SYN="$2"; P3="$3"; W="$4"; OUTF="$5"; MODE="${6:-all}"
case "$(cd "$ISO" && pwd -W 2>/dev/null || pwd)" in C:/g113/*|/c/g113/*) ;; *) echo "ISO가 C:/g113 밖: $ISO"; exit 2;; esac
export APPDATA="C:/Users/HSLEE/AppData/Roaming"; export HOME="C:/Users/HSLEE"
PY="C:/Python314/python.exe -B -P"
rev() { C:/Python314/python.exe -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8"))[sys.argv[2]])' "$SYN" "$1" | tr -d '\r'; }
mkdir -p "$W/scripts"
B=$(rev base)
if [ "$MODE" != rest ]; then
# 같은 사본: df36·e_lib는 base 판에서 iso 밖으로 복사(design 20 E4 절차 선례), p3는 제안 사본
git -C "$ISO" show "$B:.ai/verification/20260930-df36-instance-relpath/scripts/e_inst_df36.py" > "$W/scripts/e_inst_df36.py"
git -C "$ISO" show "$B:.ai/verification/20260930-df36-instance-relpath/scripts/e_lib.py" > "$W/scripts/e_lib.py"
cp "$P3" "$W/scripts/e_inst_p3.py"
fi
{ echo "== $(date -Iseconds) MODE=$MODE sha256:"; sha256sum "$W/scripts/"*.py; } >> "$OUTF"
fresh() { git -C "$ISO" checkout -q --detach "$1" && git -C "$ISO" checkout -q -- . && git -C "$ISO" clean -q -fdx; }
run() {   # $1 = 태그, $2 = rev, $3 = 스크립트, $4.. = 인자(<iso> 뒤)
  local tag="$1" r="$2" s="$3"; shift 3
  if [ "$MODE" = rest ] && [ -s "$W/$tag.json" ]; then echo "---- [$tag] 건너뜀(있음)" >> "$OUTF"; return; fi
  fresh "$r" || { echo "checkout 실패 $r" >> "$OUTF"; return; }
  local t0=$(date +%s)
  $PY "$W/scripts/$s" "$ISO" "$@" > "$W/$tag.console.txt" 2>&1; local rc=$?
  { echo "---- [$tag] rev=$(git -C "$ISO" rev-parse --short HEAD) $s $* rc=$rc $(( $(date +%s) - t0 ))s"; tail -3 "$W/$tag.console.txt" | cut -c1-400; } >> "$OUTF"
}
for c in folded_cascode current_reuse_telescopic_ota; do
  run "base_df36_$c" "$B" e_inst_df36.py "$c" "$W/base_df36_$c.json"
  run "base_p3_$c"   "$B" e_inst_p3.py   "$c" "$W/base_p3_$c.json"
  run "f1h_df36_$c"  "$(rev syn/f1h)" e_inst_df36.py "$c" "$W/f1h_df36_$c.json"
  run "f1h_p3_$c"    "$(rev syn/f1h)" e_inst_p3.py   "$c" "$W/f1h_p3_$c.json"
done
run "base_elib" "$B" e_lib.py "$W/base_elib.json"
run "f2drop_elib" "$(rev syn/f2drop)" e_lib.py "$W/f2drop_elib.json"
run "f1h_elib" "$(rev syn/f1h)" e_lib.py "$W/f1h_elib.json"
fresh "$B"
# 비교
C:/Python314/python.exe -B - "$W" >> "$OUTF" 2>&1 <<'EOF'
import json, os, sys, hashlib
sys.stdout.reconfigure(encoding="utf-8")
W = sys.argv[1]
def ld(n):
    p = os.path.join(W, n)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None
import re
def fh(n):   # stdout 사본 비교: SLSQP 진행 줄의 elapsed=<초>s 만 가린다(파일럿은 경과 시간을 찍는다 -- 첫 실행 실측)
    p = os.path.join(W, n)
    return hashlib.sha256(re.sub(rb"elapsed=[0-9.]+s", b"elapsed=<T>s", open(p, "rb").read())).hexdigest() if os.path.exists(p) else None
for c in ("folded_cascode", "current_reuse_telescopic_ota"):
    a, b = ld("base_df36_%s.json" % c), ld("base_p3_%s.json" % c)
    if a is None or b is None:
        print("EQUIV %s: 출력 없음 df36=%s p3=%s" % (c, a is not None, b is not None)); continue
    diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    print("EQUIV %s base: 다른 키 %s | df36 engine_origin %s | p3 engine_origin %s" % (c, diff, sorted(a["engine_origin"]), sorted(b["engine_origin"])))
    print("EQUIV %s base: stdout 사본 같음 %s" % (c, fh("base_df36_%s.json.stdout.txt" % c) == fh("base_p3_%s.json.stdout.txt" % c)))
    f = ld("f1h_p3_%s.json" % c)
    if f:
        print("F1H %s p3: exists=%s fail=%s without_topology_ref 같음(base p3 대비) %s raw 같음 %s stdout 같음 %s engine_origin %s" % (
            c, f.get("exists"), f.get("fail_in_stdout"), f.get("without_topology_ref_sha256") == b.get("without_topology_ref_sha256"),
            f.get("raw_sha256") == b.get("raw_sha256"),
            fh("f1h_p3_%s.json.stdout.txt" % c) == fh("base_p3_%s.json.stdout.txt" % c), sorted(f["engine_origin"])))
    else:
        print("F1H %s p3: 출력 없음" % c)
    print("F1H %s df36: 출력 %s" % (c, "있음" if ld("f1h_df36_%s.json" % c) else "없음"))
e0, e1, e2 = ld("base_elib.json"), ld("f2drop_elib.json"), ld("f1h_elib.json")
print("ELIB base %s / f2drop %s / f1h %s" % (e0 and e0["hash"], e1 and e1["hash"], e2 and e2["hash"]))
EOF
echo "== 끝 $(date -Iseconds)" >> "$OUTF"
