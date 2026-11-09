#!/usr/bin/env bash
# B33 `20260930-v7-registry-edges` 착수 절차 모의(모래상자 전용 -- 실제 저장소·gate는 읽기만).
#   bash sim_launch.sh <원본 저장소> <gate master 전체 sha> <모래상자 디렉터리(없어야 함)> <결과 디렉터리>
# 단계: 0 모래상자(복제본 r + bare 가짜 gate gate.git + 게이트 캐시) → S 선행 card 문서 패치 겹침 확인(버리는 브랜치)
#       → A design 05 패치 커밋 → B spec card + interface card(게이트 캐시의 interface_card.py, 절대 경로) 커밋
#       → C 승인 기록(fill_v3_approval.py, target = weakening_diff.diff_hash 독립 재계산 대조) 커밋
#       → G gate_change_ok(HEAD) True / (HEAD~1) False → E EL4 receive(가짜 gate, 게이트 캐시의 merge_gate.py) exit 0 + 대조(트레일러 없는 커밋) exit 1
# 어느 확인이든 어긋나면 멈춘다(set -e + 단정). 결과는 결과 디렉터리에 단계마다 남긴다.
set -Eeuo pipefail
shopt -s inherit_errexit
trap 'echo "[sim] 실패: 줄 $LINENO: $BASH_COMMAND" | tee -a "$OUT/sim.log" >&2' ERR
export HOME=/c/Users/HSLEE
export APPDATA=/c/Users/HSLEE/AppData/Roaming
export PYTHONIOENCODING=utf-8
test -n "$(git config --get user.email)"
SRC=$1; GM=$2; S=$3; OUT=$4
PY=/c/Python314/python.exe
DR=/c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts
ID=20260930-v7-registry-edges
D05=docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md
PLAN=docs/01-plan/features/gain-budget-gmid-sizing.plan.md
test ${#GM} -eq 40
test ! -e "$S"
mkdir -p "$S/tmp" "$S/nohooks" "$OUT"
export TMP="$S/tmp" TEMP="$S/tmp"
log() { echo "$*" | tee -a "$OUT/sim.log"; }
: > "$OUT/sim.log"

# ---- 0 모래상자
git clone -c core.autocrlf=false -q --no-hardlinks --no-local --no-checkout "$SRC" "$S/r"
git -C "$S/r" remote remove origin
git -C "$S/r" config core.longpaths true
git -C "$S/r" config core.hooksPath "$S/nohooks"
git -C "$S/r" checkout -q -B master "$GM"
git clone -q --bare --no-hardlinks --no-local "$S/r" "$S/gate.git"
rm -rf "$S/gate.git/hooks"; mkdir -p "$S/gate.git/hooks"     # hook 없음 -- EL4는 아래에서 merge_gate.py receive를 직접 부른다
git -C "$S/r" remote add gate "$S/gate.git"
git -C "$S/r" fetch -q gate
test "$(git -C "$S/r" rev-parse gate/master)" = "$GM"
R="$S/r"
CD=$(git -C "$R" rev-parse --path-format=absolute --git-common-dir)
"$PY" -B - "$R" "$GM" "$CD" <<'EOF' > "$OUT/cache.txt"
# role_paths.ensure_cache와 같은 일(tree_blobs → extract_blobs → dir_matches)을 gate master로 -- 캐시 이름 = 전체 sha
import os, sys
r, gm, cd = sys.argv[1:4]
sys.path.insert(0, os.path.join(r, "tools", "gates"))
import role_paths as rp
m = rp.tree_blobs(["-C", r], gm, rp.GATE_CODE_PREFIX, rp.GATE_CODE_EXCLUDE)
dest = os.path.join(cd, "gmid-gate-cache", gm)
os.makedirs(dest)
rp.extract_blobs(["-C", r], m, dest)
assert rp.dir_matches(dest, m)
print(dest.replace("\\", "/"), len(m))
EOF
CACHE=$(cut -d' ' -f1 "$OUT/cache.txt")
test "$(basename "$CACHE")" = "$GM"
test -f "$CACHE/interface_card.py" && test -f "$CACHE/merge_gate.py" && test -f "$CACHE/weakening_diff.py"
git -C "$R" show "$GM:tools/gates/interface_card.py" > "$S/tmp/ic_blob.py"
cmp "$CACHE/interface_card.py" "$S/tmp/ic_blob.py"
log "0 모래상자: r = gate master $GM, 캐시 $CACHE ($(cut -d' ' -f2 "$OUT/cache.txt") 파일, blob 대조 통과)"
PH0=$("$PY" -B "$CACHE/merge_gate.py" plan-tables-hash "$R/$PLAN")
log "0 plan_tables_hash $PH0"

# ---- S 선행 card(34·35) 문서 패치 위에서도 B33 패치가 적용되는지(버리는 브랜치 stack -- 커밋하지 않음)
git -C "$R" checkout -q -b stack
"$PY" -B "$DR/patch_v3_binding_docs.py" --root "$R" > "$OUT/stack_34.txt"
"$PY" -B "$DR/patch_v3_scope_docs.py" --root "$R" > "$OUT/stack_35.txt"
"$PY" -B "$DR/patch_b33_design05.py" "$R" > "$OUT/stack_b33.txt"
grep -q '^applied 2 replacement' "$OUT/stack_b33.txt"
git -C "$R" diff --numstat > "$OUT/stack_numstat.txt"
log "S 34·35 문서 패치 뒤 B33 패치: $(cat "$OUT/stack_b33.txt") / numstat: $(tr '\n' ';' < "$OUT/stack_numstat.txt")"
git -C "$R" checkout -q -- docs
test -z "$(git -C "$R" status --porcelain)"
git -C "$R" checkout -q master
git -C "$R" branch -q -D stack

# ---- 4.0 착수 전 확인(실제 절차와 같은 단정)
test "$(git -C "$R" rev-parse --abbrev-ref HEAD)" = master
test "$(git -C "$R" rev-parse HEAD)" = "$(git -C "$R" rev-parse gate/master)"
test -z "$(git -C "$R" branch --list 'role/*')"
test -z "$(git -C "$R" status --porcelain -- docs/ .ai/approvals/)"
test -z "$(ls "$R/tools/gates/redteam/attacks" | grep '^33-' || true)"
BASE=$(git -C "$R" rev-parse HEAD)

# ---- A design 05 패치 커밋
"$PY" -B "$DR/patch_b33_design05.py" "$R" | tee -a "$OUT/sim.log"
"$PY" -B "$DR/patch_b33_design05.py" "$R" | tee "$OUT/patch_rerun.txt"
grep -q '^already applied' "$OUT/patch_rerun.txt"
test "$(git -C "$R" diff --numstat | tr '\t' ' ')" = "2 2 $D05"
test "$("$PY" -B "$CACHE/merge_gate.py" plan-tables-hash "$R/$PLAN")" = "$PH0"
git -C "$R" add -- "$D05"
git -C "$R" commit -q --trailer "Role: doc" -m "docs: $ID 문서 커밋(design 05 §10 V7 행 그래프 규칙 명시 -- 레지스트리 바인딩 네 형식·생성자 호출 위치·dunder 폴백 제거·소스 노드 안 도달, 거부 증명 줄 공격 33)"
A=$(git -C "$R" rev-parse HEAD)
log "A 문서 커밋 $A (numstat 2 2, plan_tables_hash 불변)"

# ---- B spec card + interface card(게이트 캐시의 interface_card.py, 모두 절대 경로)
cp "$DR/draft_b33.final.spec.md" "$R/docs/02-design/specs/$ID.spec.md"
"$PY" -B "$CACHE/interface_card.py" "$R/docs/02-design/specs/$ID.spec.md" --root "$R" --out "$R/docs/02-design/specs/$ID.interface.md"
cp "$R/docs/02-design/specs/$ID.interface.md" "$OUT/interface.md"
"$PY" -B - "$R" "$CACHE" "$ID" <<'EOF' | tee -a "$OUT/sim.log"
import os, sys
r, cache, cid = sys.argv[1:4]
sys.path.insert(0, cache)
import role_paths as rp
import merge_gate as mg
card = rp.parse_spec_card(open(os.path.join(r, "docs/02-design/specs/%s.spec.md" % cid), encoding="utf-8").read(), cid)
assert (card["phase"], card["evidence_type"], card["gate_change"], card["approval"]) == ("0.5", "red-green", "yes", [cid]), card
pt = mg.read_plan_tables(os.path.join(r, "docs/01-plan/features/gain-budget-gmid-sizing.plan.md"))
assert "0.5" in pt.phase_order, pt.phase_order
print("B parse_spec_card ok: phase 0.5 red-green gate_change yes approval [%s], 절 %d개" % (cid, len(card["sections"])))
EOF
git -C "$R" add -- "docs/02-design/specs/$ID.spec.md" "docs/02-design/specs/$ID.interface.md"
git -C "$R" commit -q --trailer "Role: doc" -m "docs: 게이트 변경 spec card $ID(V7 정적 호출 그래프 -- R1 레지스트리 바인딩, R2 생성자 호출 위치만, R2' dunder 폴백 제거, R3 소스 노드 안 도달) + interface card"
SPECC=$(git -C "$R" rev-parse HEAD)
log "B spec+interface 커밋 $SPECC"

# ---- C 승인 기록(fill_v3_approval.py: diff_hash·compute_diff_hash 대조, 주석 제거, 머리 파싱)
"$PY" -B "$DR/fill_v3_approval.py" --root "$R" --draft "$DR/approval_$ID.md" --base "$BASE" --head "$SPECC" --check | tee "$OUT/fill_check.json"
"$PY" -B "$DR/fill_v3_approval.py" --root "$R" --draft "$DR/approval_$ID.md" --base "$BASE" --head "$SPECC" | tee "$OUT/fill.json"
grep -q '"result": "written"' "$OUT/fill.json"
"$PY" -B "$DR/fill_v3_approval.py" --root "$R" --draft "$DR/approval_$ID.md" --base "$BASE" --head "$SPECC" | grep -q 'already-present'
# 독립 재계산: PYTHONPATH = 게이트 캐시(= gate master의 tools/gates)
TGT=$(PYTHONPATH="$CACHE" "$PY" -B -c "import sys,weakening_diff as wd;print(wd.diff_hash(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4:]))" \
      "$R" "$BASE" "$SPECC" "$D05" "docs/02-design/specs/$ID.interface.md" "docs/02-design/specs/$ID.spec.md")
TGT2=$("$PY" -B "$CACHE/merge_gate.py" diff-hash --repo "$R" --base "$BASE" --head "$SPECC" "$D05" "docs/02-design/specs/$ID.interface.md" "docs/02-design/specs/$ID.spec.md")
test "$TGT" = "$TGT2"
grep -q "^target: $TGT\$" "$R/.ai/approvals/$ID.md"
"$PY" -B "$CACHE/merge_gate.py" parse-approval "$R/.ai/approvals/$ID.md" > "$OUT/parse_approval.json"
! grep -q '<!--' "$R/.ai/approvals/$ID.md"
! grep -q $'\r' "$R/.ai/approvals/$ID.md"
test "$(head -c3 "$R/.ai/approvals/$ID.md" | od -An -tx1 | tr -d ' ')" != "efbbbf"
cp "$R/.ai/approvals/$ID.md" "$OUT/approval_filled.md"
git -C "$R" add -- ".ai/approvals/$ID.md"
git -C "$R" commit -q --trailer "Role: doc" -m "docs: 승인 기록 $ID(B33 게이트 변경 승인 + Q1 (a) 호출 위치만, target_kind diff -- spec card·interface card·design 05 V7 행·거부 증명 줄)"
C=$(git -C "$R" rev-parse HEAD)
log "C 승인 기록 커밋 $C, target $TGT (weakening_diff.diff_hash == merge_gate diff-hash == 기록)"
test "$(git -C "$R" show --format= --name-only HEAD)" = ".ai/approvals/$ID.md"

# ---- G gate_change_ok
"$PY" -B - "$R" "$CACHE" "$ID" "$TGT" <<'EOF' | tee -a "$OUT/sim.log"
import sys
r, cache, cid, tgt = sys.argv[1:5]
sys.path.insert(0, cache)
import merge_gate as mg
import weakening_diff as wd
import reachability as rch
ok_head = mg.gate_change_ok(mg.TreeView(["-C", r], "HEAD"), cid)
ok_prev = mg.gate_change_ok(mg.TreeView(["-C", r], "HEAD~1"), cid)
assert ok_head is True and ok_prev is False, (ok_head, ok_prev)
assert tgt in wd.approved_hashes(r, "HEAD")
n_prev, n_head = len(rch._approved_ids(r, "HEAD~1")), len(rch._approved_ids(r, "HEAD"))
assert n_prev == n_head, (n_prev, n_head)
print("G gate_change_ok HEAD True / HEAD~1 False, approved_hashes(HEAD)에 target 있음, _approved_ids %d 그대로(diff 기록은 V3·V7 면제 원소 아님)" % n_head)
EOF

# ---- E EL4 receive(가짜 gate, 게이트 캐시의 merge_gate.py = gate master 판)
git -C "$S/gate.git" fetch -q "$R" "master:refs/heads/incoming"
rc_ok=0
"$PY" -B "$CACHE/merge_gate.py" receive --git-dir "$S/gate.git" --old "$GM" --new "$C" > "$OUT/el4_ok.out" 2> "$OUT/el4_ok.err" || rc_ok=$?
log "E EL4 receive --old gate master --new C: exit $rc_ok $(cat "$OUT/el4_ok.err")"
test "$rc_ok" -eq 0
# 대조: 트레일러 없는 문서 커밋 하나를 더한 것 → 거부여야 한다(게이트가 실제로 거부하는지)
git -C "$R" checkout -q -b neg
echo "neg" >> "$R/docs/02-design/specs/$ID.interface.md"
git -C "$R" commit -q -am "neg: 트레일러 없음"
NEG=$(git -C "$R" rev-parse HEAD)
git -C "$S/gate.git" fetch -q "$R" "neg:refs/heads/neg"
rc_neg=0
"$PY" -B "$CACHE/merge_gate.py" receive --git-dir "$S/gate.git" --old "$GM" --new "$NEG" > "$OUT/el4_neg.out" 2> "$OUT/el4_neg.err" || rc_neg=$?
log "E 대조(트레일러 없는 커밋): exit $rc_neg $(head -c 300 "$OUT/el4_neg.err")"
test "$rc_neg" -eq 1
git -C "$R" checkout -q master
log "끝: BASE $BASE A $A SPECC $SPECC C $C target $TGT"
