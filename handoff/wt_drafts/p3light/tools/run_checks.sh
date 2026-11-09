#!/usr/bin/env bash
# Phase 3 가벼운 절차 '매 변경 뒤' 검증 묶음(PROCEDURE 남기는 것 3·4).
#
#   bash run_checks.sh <root> <base_rev> <head_rev> <outdir> [회로 ...]
#
# <root>   : git 저장소(읽기만 -- 판마다 <outdir>/wt 에 임시 worktree를 떠서 재고 지운다. 작업 트리·브랜치는 건드리지 않는다)
# <outdir> : 저장소 밖 경로. 결과는 <outdir>/summary.txt 에 단계마다 append(중간에 죽어도 남는다).
# 회로     : E-INST 회로(기본 design 30 §10 E5 = current_reuse_telescopic_ota folded_cascode)
#
# 단계: (1) ast_check.py base head  (2) 판마다 같은 경로 worktree에서 IMPORT-ANY · 전체 pytest(PT3 모양, junit) ·
#       E-LIB(e_lib_p3.py, MASK 없음) · E-INST(e_inst_p3.py) -- 스크립트는 head 판(없으면 base 판)의 메인 커밋 6c8287f 사본을
#       <outdir>/scripts 에 한 번 꺼내 두 판에 같은 사본을 쓴다  (3) base 대 head 비교: pytest id별 결과 같음, E-LIB 해시 같음,
#       E-INST 출력 키 같음(engine_origin 제외 -- 새 MOD가 더해지는 것이 정상, 경로는 모두 worktree assets 안인지만 본다),
#       stdout 사본 같음(elapsed=…s 가림).
# base 측정은 <outdir>/rev_<sha> 에 캐시(같은 base로 다시 부르면 건너뜀).
# exit 0 = 전부 같음, 1 = 차이/실패, 2 = 실행 오류.
set -u
ROOT=$(cd "$1" && pwd); BASE=$2; HEAD=$3; OUT=$4; shift 4
CIRCUITS=("$@"); [ ${#CIRCUITS[@]} -eq 0 ] && CIRCUITS=(current_reuse_telescopic_ota folded_cascode)
PY=C:/Python314/python.exe
TOOLS=$(cd "$(dirname "$0")" && pwd)
export APPDATA="${APPDATA:-C:/Users/HSLEE/AppData/Roaming}" HOME="${HOME:-C:/Users/HSLEE}"
mkdir -p "$OUT" || exit 2
SUM="$OUT/summary.txt"
log() { printf '%s\n' "$*" | "$PY" -c 'import sys; open(sys.argv[1], "ab").write(sys.stdin.buffer.read())' "$SUM"; printf '%s\n' "$*"; }
B=$(git -C "$ROOT" rev-parse "$BASE^{commit}") || exit 2
H=$(git -C "$ROOT" rev-parse "$HEAD^{commit}") || exit 2
log "== run_checks $(date '+%F %T') root=$ROOT base=$B head=$H circuits=${CIRCUITS[*]}"
SP=docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts
mkdir -p "$OUT/scripts" "$OUT/gc"
for s in e_inst_p3.py e_lib_p3.py; do
  git -C "$ROOT" show "$H:$SP/$s" > "$OUT/scripts/$s" 2>/dev/null || git -C "$ROOT" show "$B:$SP/$s" > "$OUT/scripts/$s" || { log "ERROR: $s 없음"; exit 2; }
done
git -C "$ROOT" archive "$H" tools/gates | tar -x -C "$OUT/gc" || { log "ERROR: tools/gates 꺼내기 실패"; exit 2; }
GC="$OUT/gc/tools/gates"
log "scripts sha256: $(cd "$OUT/scripts" && sha256sum e_inst_p3.py e_lib_p3.py | tr '\n' ' ')"

# ---- (1) ast_check
"$PY" -B "$TOOLS/ast_check.py" "$B" "$H" --root "$ROOT" --out "$OUT/ast_check.json" > "$OUT/ast_check.txt" 2>&1
AC=$?; log "ast_check exit=$AC ($(grep -m1 '"verdict"' "$OUT/ast_check.txt"))"

# ---- (2) 판마다 측정
WT="$OUT/wt"
measure() {   # $1 = sha, $2 = 결과 디렉터리
  local sha=$1 R=$2 c
  if [ -f "$R/done" ]; then log "rev ${sha:0:7}: 캐시 사용 ($R)"; return 0; fi
  rm -rf "$R"; mkdir -p "$R"
  git -C "$ROOT" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$WT"; git -C "$ROOT" worktree prune
  git -C "$ROOT" worktree add -q --detach "$WT" "$sha" || { log "ERROR: worktree add $sha"; return 2; }
  local A="$WT/skills/analog-gmid-design/assets"
  # IMPORT-ANY (design 30 §10 import_any 모양: N3.10 파일과 split 파일 중 있는 것을 각각 새 프로세스에서 맨 처음 import)
  local mods n_try=0 n_fail=0
  mods=$("$PY" -c 'import sys; sys.path.insert(0, sys.argv[1]); import import_layering as il; print(" ".join(il.mod_table(open(sys.argv[2], encoding="utf-8").read())))' \
         "$GC" "$WT/docs/01-plan/features/gain-budget-gmid-sizing.plan.md" | tr -d '\r')
  for m in $(printf '%s\n' $mods sizing_recipe stick_diagram topology_library design_report audit_current_forced | sort -u); do
    [ -f "$A/$m.py" ] || continue
    n_try=$((n_try + 1))
    ( cd "$A" && "$PY" -B -c "import $m" ) > "$R/import_$m.txt" 2>&1 || { n_fail=$((n_fail + 1)); echo "$m" >> "$R/import_fail.txt"; }
  done
  echo "$n_try $n_fail" > "$R/import_any.txt"
  log "rev ${sha:0:7}: IMPORT-ANY tried=$n_try failed=$n_fail $( [ -f "$R/import_fail.txt" ] && tr '\n' ' ' < "$R/import_fail.txt")"
  # 전체 pytest(PT3 모양: gate ini, --gmid-phase=3)
  PYTHONPATH="$GC" PYTHONPYCACHEPREFIX="$OUT/pycache_${sha:0:7}" "$PY" -P -m pytest -c "$GC/pytest_gate.ini" --rootdir="$WT" --confcutdir="$WT" \
      "$A/tests" --gmid-phase=3 -p no:cacheprovider -q --junitxml="$R/pytest.xml" > "$R/pytest.txt" 2>&1
  log "rev ${sha:0:7}: pytest exit=$? $(tail -1 "$R/pytest.txt")"
  "$PY" -P "$OUT/scripts/e_lib_p3.py" "$WT" "$R/elib.json" > "$R/elib.txt" 2>&1
  log "rev ${sha:0:7}: E-LIB exit=$? $(head -1 "$R/elib.txt")"
  for c in "${CIRCUITS[@]}"; do
    "$PY" -B -P "$OUT/scripts/e_inst_p3.py" "$WT" "$c" "$R/einst_$c.json" > "$R/einst_$c.txt" 2>&1
    log "rev ${sha:0:7}: E-INST $c exit=$?"
    git -C "$WT" checkout -q -- . ; git -C "$WT" clean -q -fdx -e '__pycache__'   # 하네스 산출을 지우고 다음 회로
  done
  git -C "$ROOT" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$WT"; git -C "$ROOT" worktree prune
  touch "$R/done"
}
measure "$B" "$OUT/rev_$B" || exit 2
rm -f "$OUT/rev_$H/done"
measure "$H" "$OUT/rev_$H" || exit 2

# ---- (3) 비교
"$PY" - "$OUT/rev_$B" "$OUT/rev_$H" "$WT" "${CIRCUITS[@]}" > "$OUT/compare.txt" 2>&1 <<'PYEOF'
import hashlib, json, os, re, sys
import xml.etree.ElementTree as ET
RB, RH, WT, circuits = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
bad = []
def junit(p):
    out = {}
    if not os.path.exists(p):
        return None
    for tc in ET.parse(p).getroot().iter("testcase"):
        tid = "%s::%s" % (tc.get("classname"), tc.get("name"))
        st = "passed"
        for ch in tc:
            if ch.tag in ("failure", "error"):
                st = ch.tag
            elif ch.tag == "skipped":
                st = "xfail" if "xfail" in (ch.get("type") or "") + (ch.get("message") or "") else "skipped"
        out[tid] = st
    return out
jb, jh = junit(os.path.join(RB, "pytest.xml")), junit(os.path.join(RH, "pytest.xml"))
if jb is None or jh is None:
    print("PYTEST INVALID: junit 없음"); bad.append("pytest")
else:
    diff = sorted(k for k in set(jb) | set(jh) if jb.get(k) != jh.get(k))
    cnt = lambda j: {s: list(j.values()).count(s) for s in sorted(set(j.values()))}
    print("PYTEST base %d %s / head %d %s / id별 차이 %d" % (len(jb), cnt(jb), len(jh), cnt(jh), len(diff)))
    for k in diff[:50]:
        print("  diff %s base=%s head=%s" % (k, jb.get(k), jh.get(k)))
    if diff:
        bad.append("pytest")
    nf = [k for k, v in jh.items() if v in ("failure", "error")]
    print("PYTEST head failure/error %d" % len(nf))
for tag, R in (("base", RB), ("head", RH)):
    n_try, n_fail = open(os.path.join(R, "import_any.txt")).read().split()
    print("IMPORT-ANY %s tried=%s failed=%s" % (tag, n_try, n_fail))
    if tag == "head" and n_fail != "0":
        bad.append("import-any")
ld = lambda p: json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None
eb, eh = ld(os.path.join(RB, "elib.json")), ld(os.path.join(RH, "elib.json"))
ok = eb is not None and eh is not None and eb["hash"] == eh["hash"]
print("E-LIB %s (base %s head %s)" % ("같음" if ok else "다름/실패", eb and eb["hash"][:12], eh and eh["hash"][:12]))
ok or bad.append("E-LIB")
fh = lambda p: hashlib.sha256(re.sub(rb"elapsed=[0-9.]+s", b"elapsed=<T>s", open(p, "rb").read())).hexdigest() if os.path.exists(p) else None
for c in circuits:
    pb, ph = os.path.join(RB, "einst_%s.json" % c), os.path.join(RH, "einst_%s.json" % c)
    b, h = ld(pb), ld(ph)
    if b is None or h is None:
        print("E-INST %s INVALID: 출력 없음" % c); bad.append("einst:" + c); continue
    keys = sorted(k for k in set(b) | set(h) if k != "engine_origin" and b.get(k) != h.get(k))
    A = os.path.normcase(os.path.join(WT, "skills", "analog-gmid-design", "assets"))
    inside = all(os.path.normcase(os.path.dirname(os.path.abspath(f))) == A for f in h["engine_origin"].values())
    added = sorted(set(h["engine_origin"]) - set(b["engine_origin"]))
    same_out = fh(pb + ".stdout.txt") == fh(ph + ".stdout.txt")
    ok = not keys and inside and same_out and h.get("exists") and not h.get("fail_in_stdout")
    print("E-INST %s %s (다른 키 %s, engine_origin 더해진 모듈 %s, 경로 안 %s, stdout 같음 %s)" % (c, "같음" if ok else "다름/실패", keys, added, inside, same_out))
    ok or bad.append("einst:" + c)
print("COMPARE PASS" if not bad else "COMPARE FAIL " + ",".join(bad))
sys.exit(1 if bad else 0)
PYEOF
CP=$?
"$PY" -c 'import sys; open(sys.argv[1], "ab").write(open(sys.argv[2], "rb").read())' "$SUM" "$OUT/compare.txt"; cat "$OUT/compare.txt"
log "== 결과: ast_check exit=$AC, compare exit=$CP"
[ "$AC" -eq 0 ] && [ "$CP" -eq 0 ] && exit 0 || exit 1
