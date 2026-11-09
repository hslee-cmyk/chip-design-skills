#!/usr/bin/env bash
# T0 card 20260930-p3-tests-location-free V5 승인 운반(두 번 시도) -- 오케스트레이터. 1차 시도(순서 1~3, auditor V5 FAIL로 멈춤) 뒤, 2차 시도 착수 전·중·뒤.
# 근거: design 05 §12 'V5 승인 운반' 행 (1)~(4)와 '정리'·'재시도' 행, §9.2-4 test-only 모양(병합 없음), §9.2-9(V5 승인은 new 트리에서 찾는다 -- merge_gate.py
#       `load_approvals(new_view)`, weakening_diff.approved_hashes(root, head)), phase3_runbook §18 X-1 판단(_drafts/phase3_runbook.md §8.4).
#   왜 두 번인가(X-1): V5 승인 target = diff 해시 = (경로, base blob, head blob) 식(00-common §8.2) -- head blob은 test-author가 쓴 T의 내용이라 T 전에 정할 수 없다
#   (오케스트레이터가 test blob을 미리 쓰면 작성자≠검증자 위반). 승인 기록(.ai/approvals/**, 오케스트레이터 Role: doc)은 test-only push 모양(old..new^ 전부 Role: test +
#   Role: audit 1개 -- 다른 커밋 금지)에 낄 수 없고, 역할 브랜치가 있는 동안 메인 master 문서 push는 EL1이 거부한다 -> 1차 정리 뒤 문서 커밋으로 gate에 넣고 2차 시도.
# 구조는 b26_1_carry.sh를 따른다(단계별 함수, 옵션은 단계 이름 앞, 단일 출처, 게이트 캐시 절대 경로, EL1 판정 git 명령(worktree remove·branch -D·push)은 실행하지 않고 출력만).
# test-only라 code worktree·K·V3 기록·dispute(코드 작성자 몫) 없음. 어느 확인이든 실패하면 그 자리에서 멈춘다(set -Eeuo pipefail + ERR trap). 재시도 루프 없음.
#
# 단일 출처: B1 = t0_launch.sh 상태 파일의 'S='(launch after-push가 확인한 gate master = 1차 base). T1 = 1차 role/test 끝(check가 한 번 읽어 상태 파일에 적는다).
#   target = 1차 auditor base_check.json의 diff_hash = 게이트 캐시 weakening_diff 재실행 = merge_gate.py diff-hash(셋이 같아야 한다).
#   승인 기록 본문 = _drafts/approval_20260930-p3-tests-location-free.md(오케스트레이터가 사용자 답을 받은 뒤 <DATE>·<V5_…> 자리를 채운다 -- records가 해시·커밋·경로·발견 자리를 채운다).
#
#   bash t0_carry.sh prep        # check -> archive  ((2) 정리 전 추출·보관 -- 메인 worktree에 운반 파일만 쓰고 커밋 없음) + V5 질문 재료 $ADIR/v5_question.txt·선택지 $ADIR/v5_options.txt
#     -> 오케스트레이터: V5 질문(AskUserQuestion -- 질문 문안에 v5_question.txt 전체를 바이트 그대로 담고, 선택지 label = v5_options.txt 두 줄 그대로('(Recommended)' 등 덧붙이지 않음))
#        -> 답을 승인 초안의 <DATE>·<V5_ASKED_AT>('YYYY-MM-DD HH:MM KST' = 그 tool_use 줄 timestamp의 KST 분)·<V5_JSONL_NAME>·<V5_TOOLU>·<V5_QUESTION>·<V5_ANSWER>에 Edit
#   bash t0_carry.sh records     # 승인 기록 작성(미커밋) + parse-approval + jsonl 원문 대조(인용 블록마다 자기 jsonl·toolu, 질문·고른 답 전체 일치 -- t0_quote_check.py)
#                                #   + V5 블록 = 이 target(질문 ⊇ v5_question.txt 전체, 그 안 diff_hash(target) 줄 = 상태 DIFF_HASH)·답 = 승인 label·질문 시각 > ARCHIVED_AT·V5_ASKED_AT 일치
#                                #   + 입력 핀(T0_DRAFT_SHA256 = 초안 canon, T0_QCHK_SHA256 = t0_quote_check.py)
#   bash t0_carry.sh cleanup     # 정리 명령 **출력만**(worktree remove --force 두 경로, branch -D 두 개) -- 오케스트레이터가 하나씩 단독 호출
#   bash t0_carry.sh cleaned     # refs/heads/role/ 0줄, 이 card worktree 0 (저장소 변경 없음)
#   bash t0_carry.sh local       # cleaned -> commit -> final  (Role: doc 커밋 하나 = 승인 기록 + 운반 blob + paths.tsv -- 끝에 push 명령 출력, push 안 함)
#   bash t0_carry.sh after-push  # push 뒤: gate master = C = 2차 base B2, B1·B2 사이 skills/·workspaces/ 같음, B2 트리 V5 조회가 target을 찾음 + 2차 시도 명령
#   bash t0_carry.sh t2-check    # 2차 test 커밋 뒤·순서 3 전: B2..T2 = Role: test 사슬, 바뀐 경로·blob 전부 = 1차(B1..T1), head에서 다시 낸 V5 = approved·같은 해시
#   bash t0_carry.sh purge       # T0 병합(순서 8)·정리 뒤: 운반 디렉터리 삭제 Role: doc 커밋(design 05 §12 (4)) -- 끝에 push 명령 출력
#   bash t0_carry.sh <단계>      # check | archive | commit | final 하나만(중단 뒤 이어 하기 -- 각 단계가 앞 단계 결과를 확인)
#                                #   archive가 중간에 죽었으면 다시 실행이 멈추며 지울 두 경로(보관·미추적 운반 디렉터리)의 rm 명령을 정확히 출력한다(자동 삭제 없음)
#
# 사전 시험 옵션(반드시 단계 이름 앞에): --repo <복제본> --state <상태 파일> --launch-state <launch 상태 파일> --archive <보관 디렉터리> --wt <worktree 부모>
#   --draft <승인 초안 사본> --jsonl <세션 jsonl>(--jsonl은 실제 실행에서도 줄 수 있다. 인용 블록의 jsonl 이름은 이 파일의 폴더에서 찾는다 -- 읽기만 한다)
#   출력하는 다음 단계 명령에는 받은 옵션이 그대로 붙는다($SELF).
set -Eeuo pipefail
shopt -s inherit_errexit
trap 'echo "[중단] ${BASH_SOURCE[0]}:${LINENO}: ${BASH_COMMAND}" >&2' ERR
. "$(dirname -- "${BASH_SOURCE[0]}")/launch_common.sh"

# MSYS2 자식 bash는 HOME·APPDATA를 잃는다(post_p10b_runbook.sh와 같은 실측). TEMP·TMP는 lc_tmp_setup(상태 파일 옆)
export HOME=/c/Users/HSLEE
export APPDATA='C:\Users\HSLEE\AppData\Roaming' LOCALAPPDATA='C:\Users\HSLEE\AppData\Local' USERPROFILE='C:\Users\HSLEE'
export PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8

R_REAL=$LC_R_REAL
W_REAL=$LC_W_REAL
DR=$W_REAL/_drafts
ID=20260930-p3-tests-location-free
VAID=$ID                                                                            # V5 diff 승인 id(card 머리 approval 줄 둘째)
STATE_REAL=$DR/t0_carry_state.txt
LSTATE_REAL=$DR/t0_launch_state.txt
ADIR_REAL=$DR/t0_attempt1
DRAFT_REAL=$DR/approval_$VAID.md
JSONL=$HOME/.claude/projects/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922.jsonl
R=$R_REAL; W=$W_REAL; STATE=$STATE_REAL; LSTATE=$LSTATE_REAL; ADIR=$ADIR_REAL; DRAFT=$DRAFT_REAL
OPTQ=""                                                                             # review_t0_carry m5: 받은 옵션 그대로(%q) -- 출력하는 다음 명령에 붙인다
while [ $# -gt 1 ]; do
  case "$1" in
    --repo|--state|--launch-state|--archive|--wt|--draft|--jsonl) OPTQ="$OPTQ $(printf '%q %q' "$1" "$2")" ;;
  esac
  case "$1" in
    --repo) R=$2; shift 2 ;;
    --state) STATE=$2; shift 2 ;;
    --launch-state) LSTATE=$2; shift 2 ;;
    --archive) ADIR=$2; shift 2 ;;
    --wt) W=$2; shift 2 ;;
    --draft) DRAFT=$2; shift 2 ;;
    --jsonl) JSONL=$2; shift 2 ;;
    *) break ;;
  esac
done
SELF="bash $0$OPTQ"
# 단계 이름 뒤에 옵션을 붙이면 조용히 무시돼 실제 저장소에서 돈다(review_post_p10b_runbook B1과 같은 가드) -- 남은 인자는 단계 이름 하나뿐
[ $# -eq 1 ] || { echo "[중단] 사용법: $0 [--repo R --state S --launch-state L --archive A --wt W --draft D] [--jsonl J] <단계>  (옵션은 단계 이름 앞에만)" >&2; exit 2; }
case "$1" in --*) echo "[중단] 단계 이름 자리에 옵션: $1 (옵션 값이 빠졌거나 순서가 틀렸다)" >&2; exit 2 ;; esac
lc_repo_guard "$R" "$R_REAL"
if [ "$LC_REAL" = 0 ]; then
  lc_need_sandbox --state "$STATE" "$STATE_REAL"; lc_need_sandbox --launch-state "$LSTATE" "$LSTATE_REAL"
  lc_need_sandbox --archive "$ADIR" "$ADIR_REAL"; lc_need_sandbox --wt "$W" "$W_REAL"; lc_need_sandbox --draft "$DRAFT" "$DRAFT_REAL"
else
  lc_need_real --state "$STATE" "$STATE_REAL"; lc_need_real --launch-state "$LSTATE" "$LSTATE_REAL"
  lc_need_real --archive "$ADIR" "$ADIR_REAL"; lc_need_real --wt "$W" "$W_REAL"; lc_need_real --draft "$DRAFT" "$DRAFT_REAL"
  STATE=$STATE_REAL; LSTATE=$LSTATE_REAL; ADIR=$ADIR_REAL; W=$W_REAL; DRAFT=$DRAFT_REAL
fi
lc_tmp_setup "$STATE"
echo "== 대상 저장소 R=$R  상태 $STATE  launch 상태 $LSTATE  보관 $ADIR  worktree 부모 $W  승인 초안 $DRAFT"

PY=/c/Python314/python.exe
QCHK=$(realpath -- "$(dirname -- "${BASH_SOURCE[0]}")/t0_quote_check.py")      # 초안 산문 canon + 인용 대조(records가 import -- review_t0_carry S1·m1)
# 입력 바이트 핀(b26_1_carry.sh U3_DRAFT_SHA256·U3_FILL_SHA256과 같은 성격): 한쪽만 바뀐 것(drift) 탐지용, 무결성 증거 아님(초안·핀 동시 수정은 못 막는다).
#   T0_DRAFT_SHA256 = sha256(canon(초안)) -- canon은 오케스트레이터 자리(date·V5 머리 줄 세 자리·V5 질문·V5 답)만 자리표시로 되돌린다 -> 그 밖 산문 변경(예: '기대값 불변(계약 5)')은 불일치.
#   T0_QCHK_SHA256 = t0_quote_check.py 바이트. 정당한 초안·검사기 변경은 같은 변경에서 이 값을 새 sha256으로 고친다. 두 값은 commit 본문에 남긴다.
T0_DRAFT_SHA256=ca5385a60be28e5c8e85be8989221f428e06ac10e08e7c58a712f8b7ab11a094
T0_QCHK_SHA256=03d07619cca7c93888a900f1314e2a5a86892cbe962ab4491385ac7fa8974421
F_A=.ai/approvals/$VAID.md
A=skills/analog-gmid-design/assets
D=docs/03-analysis/gain-budget-gmid-sizing-30-module-split/v5-carry/$ID          # design 05 §12 (2) 운반 경로(<feature>-<design> = gain-budget-gmid-sizing-30-module-split)
AUD=.ai/verification/$ID                                                            # 1차 audit worktree 안 auditor 순서 3 산출물(커밋 안 됨)
WT_T=$W/$ID-test; WT_A=$W/$ID-audit
# card 계약 8: 바뀌는 파일 = 정확히 이 여덟(실제 실행은 같음, 모래상자는 부분집합 -- B26-1 전 base에는 계약 10 파일이 없다)
EXPECT8="$A/tests/contracts/_engine_defs.py $A/tests/contracts/test_ic5.py $A/tests/contracts/test_dup_w_calc.py $A/tests/contracts/test_ts6_dead_probes.py $A/tests/contracts/test_b26_rail_accessor.py $A/tests/unit/test_selftest_topology_library.py $A/tests/unit/test_selftest_sizing_recipe.py $A/tests/unit/test_selftest_design_report.py"
COAUTH="Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
SUBJ_C="docs: T0 1차 시도 운반 -- 승인 기록 $VAID(V5 diff, test 커밋 발견 경로 해시) + V5 운반 blob·paths.tsv(design 05 §12 'V5 승인 운반')"
SUBJ_P="docs: T0 운반 디렉터리 삭제 -- $D(병합 뒤, design 05 §12 'V5 승인 운반' (4))"
if [ "$ADIR" = "$ADIR_REAL" ]; then A_LABEL="_drafts/t0_attempt1/"; else A_LABEL="$ADIR/"; fi

say() { printf '%s\n' "== $*"; }
g() { git -C "$R" "$@"; }
st_set() { touch "$STATE"; grep -v "^$1=" "$STATE" > "$STATE.tmp" || true; printf '%s=%s\n' "$1" "$2" >> "$STATE.tmp"; mv "$STATE.tmp" "$STATE"; }
st_get() { local v; v=$(grep "^$1=" "$STATE" | tail -1 | cut -d= -f2-); test -n "$v"; printf '%s' "$v"; }
lst_get() { local v; v=$(grep "^$1=" "$LSTATE" | tail -1 | cut -d= -f2-); test -n "$v"; printf '%s' "$v"; }
cache_dir() {   # 게이트 코드 캐시 = <git-common-dir>/gmid-gate-cache/<gate master 전체 sha>(hook과 같은 ensure_cache)
  local c
  c=$("$PY" -B -c "import sys;sys.path.insert(0,sys.argv[1]);import role_paths as rp;print(rp.ensure_cache(rp.load_env(sys.argv[2])))" "$R/tools/gates" "$R")
  test "$(basename "$c")" = "$(g rev-parse gate/master)"
  test -f "$c/merge_gate.py" && test -f "$c/weakening_diff.py"
  printf '%s' "$c"
}
staged_is() { test "$(g diff --cached --name-only | sort | tr '\n' ' ')" = "$(printf '%s\n' "$@" | sort | tr '\n' ' ')"; }
trailer_of() { g log -1 --format="%(trailers:key=$2,valueonly)" "$1" | tr -d '\r' | grep -v '^$' || true; }
role_branches() { g for-each-ref --format='%(refname)' refs/heads/role/; }
sums_ok() { ( cd "$ADIR" && sha256sum -c --quiet SHA256SUMS ); }
# 검사기 바이트 핀(아래 T0_QCHK_SHA256 설명) -- archive(선택지 label을 꺼내기 전)와 records(기록 쓰기 전)
qchk_pin_ok() {
  local ph; ph=$(sha256sum -b < "$QCHK" | cut -c1-64)
  if [ "$ph" != "$T0_QCHK_SHA256" ]; then echo "[중단] t0_quote_check.py sha256 핀 불일치: $QCHK = $ph, 핀 T0_QCHK_SHA256 = $T0_QCHK_SHA256 -- 정당한 변경이면 핀 상수를 고친다" >&2; return 1; fi
}
# 바이트 단정: BOM·CR·HTML 주석·자리표시('<대문자·숫자·_>')·닫는 태그('</이름' -- 도구 호출 찌꺼기 </content>·</invoke>, review_t0_carry S2) 0, 끝 줄바꿈 하나(b26_1_carry.sh bytes_ok + 태그)
bytes_ok() {
  "$PY" -B -c "
import re,sys
b=open(sys.argv[1],'rb').read()
bad=[k for k,v in (('BOM',b.startswith(b'\xef\xbb\xbf')),('CR',b'\r' in b),('주석',b'<!--' in b or b'-->' in b),('자리표시',re.search(rb'<[A-Z][A-Z0-9_]*>',b) is not None),('태그',re.search(rb'</[A-Za-z]',b) is not None)) if v]
assert not bad,(sys.argv[1],bad,'태그 = 닫는 태그 모양 </이름 -- V5 질문 문안(AskUserQuestion)에서 </ 를 피해 다시 묻는다' if '태그' in bad else '')
assert b.endswith(b'\n') and not b.endswith(b'\n\n'),'끝 줄바꿈 하나'
print('   바이트 OK',sys.argv[1].rsplit('/',1)[-1],len(b))" "$1"
}
# 1차·2차 test 사슬: <base> <tip> -- 첫 부모 사슬, 병합 없음, 전부 Role: test·Change-Id: $ID, 1개 이상
test_chain_ok() {
  local b=$1 t=$2 c
  test "$t" != "$b"; g merge-base --is-ancestor "$b" "$t"
  test "$(g rev-list "$b..$t" | tr '\n' ' ')" = "$(g rev-list --first-parent "$b..$t" | tr '\n' ' ')"
  for c in $(g rev-list "$b..$t"); do
    test "$(g rev-list --parents -1 "$c" | wc -w | tr -d ' ')" = 2
    test "$(trailer_of "$c" Role)" = test || { echo "[중단] ${c:0:12}: Role: test가 아니다" >&2; return 1; }
    test "$(trailer_of "$c" Change-Id)" = "$ID" || { echo "[중단] ${c:0:12}: Change-Id: $ID가 아니다" >&2; return 1; }
  done
}
# <base> <head> -> '경로<TAB>head blob' 줄(정렬) -- 바뀐 경로 전부(이름 바꿈 없음)
changed_blobs() {
  local b=$1 h=$2 p
  for p in $(g diff --name-only --no-renames "$b" "$h" | tr -d '\r' | LC_ALL=C sort); do printf '%s\t%s\n' "$p" "$(g rev-parse "$h:$p")"; done
}
# weakening_diff 실행(게이트 캐시 판) -> 출력 JSON 파일. exit 0(PASS)·1(FAIL)만 받는다(2 = 실행 오류 -> 멈춤)
wd_run() {   # <캐시> <base> <head> <출력 파일>
  local rc=0
  "$PY" -B "$1/weakening_diff.py" --root "$R" --base "$2" --head "$3" > "$4" || rc=$?
  [ "$rc" = 0 ] || [ "$rc" = 1 ] || { echo "[중단] weakening_diff exit $rc: $(head -c 400 "$4")" >&2; return 1; }
}

# ------------------------------------------------------------------ check (1차 시도 상태 확인 -- 저장소 변경 없음, fetch만)
stage_check() {
  say "check: 1차 시도 상태 확인(순서 1~3 끝, auditor base_check.json V5 FAIL)"
  test -s "$LSTATE"
  local B1; B1=$(lst_get S)
  test -n "$(git config --get user.email)"
  g fetch gate
  test "$(g rev-parse --abbrev-ref HEAD)" = master
  test "$(g rev-parse gate/master)" = "$B1"                           # 1차 시도 중 gate가 움직이지 않았다(역할 브랜치가 있는 동안 문서 push는 EL1 거부)
  test "$(g rev-parse HEAD)" = "$B1"
  g diff --cached --quiet
  test -z "$(g status --porcelain -- docs/ .ai/)"
  # 역할 브랜치 = 정확히 이 card의 test·audit 둘(test-only -- code 없음. 그 밖이 있으면 정리 뒤에도 EL1이 문서 push를 거부한다)
  test "$(role_branches | sort | tr '\n' ' ')" = "$(printf 'refs/heads/role/%s/%s\n' audit "$ID" test "$ID" | sort | tr '\n' ' ')"
  test ! -e "$W/$ID-code"
  local wl; wl=$(g worktree list --porcelain | tr -d '\r')
  local r p; for r in test audit; do
    p=$("$PY" -B -c "import os,sys;print(os.path.normcase(os.path.abspath(sys.argv[1])))" "$W/$ID-$r")
    printf '%s\n' "$wl" | "$PY" -B -c "
import os,sys
blocks=sys.stdin.read().strip().split('\n\n')
want=(sys.argv[1],'branch refs/heads/role/%s/%s'%(sys.argv[2],sys.argv[3]))
ok=[b for b in blocks if os.path.normcase(os.path.abspath(b.split('\n')[0][len('worktree '):]))==want[0] and want[1] in b.split('\n')]
assert len(ok)==1,('worktree 없음 또는 브랜치 다름',want)" "$p" "$r" "$ID"
  done
  local T1; T1=$(g rev-parse "refs/heads/role/test/$ID")
  test_chain_ok "$B1" "$T1"
  # audit worktree = T1, 병합 상태 없음(test-only -- 병합 없음), 추적 파일 변경 없음(순서 3 산출물은 미추적), test worktree 깨끗(운반 대상 = 커밋된 T1)
  test "$(git -C "$WT_A" rev-parse HEAD)" = "$T1"
  if git -C "$WT_A" rev-parse -q --verify MERGE_HEAD > /dev/null; then echo "[중단] 1차 audit worktree에 병합 상태가 있다" >&2; false; fi
  test -z "$(git -C "$WT_A" status --porcelain --untracked-files=no)"
  test -z "$(git -C "$WT_A" log --oneline "role/test/$ID..HEAD")"      # 순서 3 커밋 없음(runbook §1-3)
  test -z "$(git -C "$WT_T" status --porcelain)"
  test -s "$WT_A/$AUD/base_check.json" || { echo "[중단] 1차 auditor 산출물 $AUD/base_check.json이 없다 -- target 출처(브리프 3.1 '1차 시도')" >&2; false; }
  if g cat-file -e "$T1:$F_A" 2>/dev/null; then echo "[중단] $F_A가 이미 T1 트리에 있다" >&2; false; fi
  # 바뀐 경로 = card 계약 8(실제 실행: 여덟 정확히, 모래상자: 부분집합)
  changed_blobs "$B1" "$T1" > "$STATE.t1_blobs.tsv"
  "$PY" -B - "$STATE.t1_blobs.tsv" "$EXPECT8" "$LC_REAL" <<'EOF'
import sys
got = [l.split("\t")[0] for l in open(sys.argv[1], encoding="utf-8").read().splitlines()]
exp = set(sys.argv[2].split())
assert got and set(got) <= exp, ("바뀐 경로가 card 계약 8 밖", sorted(set(got) - exp))
if sys.argv[3] == "1":
    assert set(got) == exp, ("바뀐 경로가 계약 8의 여덟이 아니다", sorted(exp - set(got)))
print("   바뀐 경로 %d개(계약 8 %s)" % (len(got), "여덟 정확히" if sys.argv[3] == "1" else "부분집합 -- 모래상자"))
EOF
  local C; C=$(cache_dir)
  wd_run "$C" "$B1" "$T1" "$STATE.v5_attempt1.json"
  local paths; paths=$("$PY" -B -c "import json,sys;print(' '.join(json.load(open(sys.argv[1],encoding='utf-8'))['diff_paths']))" "$STATE.v5_attempt1.json")
  test -n "$paths" || { echo "[중단] 1차 V5 발견 0 -- 운반할 승인이 없다(두 번 시도 불필요: 1차를 정리하지 말고 그대로 순서 7로 -- 판단을 오케스트레이터에게)" >&2; false; }
  local dh; dh=$("$PY" -B "$C/merge_gate.py" diff-hash --repo "$R" --base "$B1" --head "$T1" $paths)
  local out; out=$("$PY" -B - "$WT_A/$AUD/base_check.json" "$STATE.v5_attempt1.json" "$dh" "$STATE.t1_blobs.tsv" "$STATE.findings.tsv" <<'EOF'
import json, sys, re
bc = json.load(open(sys.argv[1], encoding="utf-8"))
rr = json.load(open(sys.argv[2], encoding="utf-8"))
dh = sys.argv[3]
changed = {l.split("\t")[0] for l in open(sys.argv[4], encoding="utf-8").read().splitlines()}
hs, ps = set(), []
def walk(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "diff_hash" and v is not None: hs.add(v)
            if k == "diff_paths": ps.append(v)
            walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
walk(bc)
assert len(hs) == 1 and re.fullmatch(r"[0-9a-f]{64}", next(iter(hs))), ("base_check.json diff_hash가 정확히 하나가 아니다", hs)
h = hs.pop()
assert rr["tool"] == "V5" and rr["verdict"] == "FAIL" and rr["approved"] is False, (rr.get("verdict"), rr.get("approved"))
assert ps and all(p == rr["diff_paths"] for p in ps), ("base_check.json diff_paths != 재실행", ps, rr["diff_paths"])
assert set(rr["diff_paths"]) <= changed, ("diff_paths가 T1 바뀐 경로 밖", sorted(set(rr["diff_paths"]) - changed))
assert rr["diff_hash"] == h == dh, ("diff_hash 불일치(base_check·재실행·diff-hash)", h, rr["diff_hash"], dh)
assert {f["path"] for f in rr["findings"]} == set(rr["diff_paths"])
with open(sys.argv[5], "w", encoding="utf-8", newline="\n") as fh:
    for f in sorted(rr["findings"], key=lambda f: (f["path"], f["unit"], f["pattern"])):
        fh.write("%s\t%s\t%s\t%s\n" % (f["path"], f["unit"], f["pattern"], " ".join(str(f.get("detail", "")).split())))
print(h)
EOF
)
  echo "   V5: base_check.json diff_hash = weakening_diff 재실행 = diff-hash = ${out:0:16}…, diff_paths $(echo $paths | wc -w | tr -d ' ')개, 발견 $(wc -l < "$STATE.findings.tsv" | tr -d ' ')개"
  st_set B1 "$B1"; st_set T1 "$T1"; st_set DIFF_HASH "$out"; st_set DIFF_PATHS "$paths"; st_set CACHE "$C"
  st_set CHECK_OK 1
  say "check OK: B1 ${B1:0:7} T1 ${T1:0:7} -- 다음은 archive"
}

# ------------------------------------------------------------------ archive ((2) 운반 blob·paths.tsv + 보관 -- 정리 전, 커밋 없음)
stage_archive() {
  say "archive: (2) 운반 blob·paths.tsv(메인 worktree $D) + 보관 디렉터리 $ADIR(저장소 밖) + V5 질문 재료"
  test "$(st_get CHECK_OK)" = 1
  local B1 T1 DH paths; B1=$(st_get B1); T1=$(st_get T1); DH=$(st_get DIFF_HASH); paths=$(st_get DIFF_PATHS)
  test "$(g rev-parse "refs/heads/role/test/$ID")" = "$T1"
  if g cat-file -e "$B1:$D" 2>/dev/null; then echo "[중단] 운반 디렉터리가 이미 B1 트리에 있다" >&2; false; fi
  # review_t0_carry m3: archive가 끝까지 가면 ARCHIVED=1 -> 다시 실행 거부(덮어쓰지 않는다). 중간에 죽었으면(ARCHIVED 없음) 남은 두 디렉터리는 이 단계 산출물뿐이다
  #   -- 지우지 않고(fail-closed) 정확한 복구 명령을 출력하고 멈춘다: 운반 디렉터리가 index·B1 트리에 없음을 확인한 뒤에만 그 rm을 안내한다.
  if [ -e "$ADIR" ] || [ -e "$R/$D" ]; then
    if [ "$(st_get ARCHIVED 2>/dev/null || true)" = 1 ]; then echo "[중단] archive는 이미 끝났다(ARCHIVED=1) -- 보관 $ADIR·운반 $R/$D를 덮어쓰지 않는다. 다음 단계는 records" >&2; false; fi
    test -z "$(g ls-files -- "$D")" || { echo "[중단] 운반 디렉터리 $D가 index에 있다 -- 손으로 확인(자동 복구 안내 없음)" >&2; false; }
    echo "[중단] 앞선 archive가 중간에 멈춘 흔적(ARCHIVED 없음): 아래 두 줄을 단독 실행(이 단계 산출물만 -- 미추적 운반 디렉터리·저장소 밖 보관)한 뒤 $SELF archive 를 다시 실행한다:" >&2
    echo "     rm -rf -- $(printf '%q' "$ADIR")" >&2
    echo "     rm -rf -- $(printf '%q' "$R/$D")" >&2
    false
  fi
  mkdir -p "$R/$D" "$ADIR/v5-carry" "$ADIR/T1_files"
  # ① 발견 경로마다 T1 blob -- 파일 이름 = blob id(판정 환경 이름 회피), 바이트 그대로(cat-file blob은 줄바꿈 변환을 하지 않는다)
  local p b
  : > "$R/$D/paths.tsv"
  for p in $paths; do
    b=$(g rev-parse "$T1:$p")
    git -C "$WT_T" cat-file blob "$T1:$p" > "$R/$D/$b.blob"
    test "$(git hash-object "$R/$D/$b.blob")" = "$b"
    printf '%s\t%s\n' "$p" "$b" >> "$R/$D/paths.tsv"
    cp "$R/$D/$b.blob" "$ADIR/v5-carry/"
  done
  cp "$R/$D/paths.tsv" "$ADIR/v5-carry/"
  # ② 커밋 id ③ T1 전체 patch(2차 test-author가 발견 밖 경로를 다시 쓸 때의 출처 -- B26-1과 같은 방식) + T1 바뀐 파일 전부(오케스트레이터 대조용)
  printf 'B1 %s\nT1 %s\n' "$B1" "$T1" > "$ADIR/commits.txt"
  g diff --no-color --no-ext-diff --no-renames "$B1" "$T1" > "$ADIR/T1.patch"
  local bb; while IFS=$'\t' read -r p bb; do
    mkdir -p "$ADIR/T1_files/$(dirname -- "$p")"
    g cat-file blob "$bb" > "$ADIR/T1_files/$p"
    test "$(git hash-object "$ADIR/T1_files/$p")" = "$bb"
    grep -qF "diff --git a/$p b/$p" "$ADIR/T1.patch"
  done < "$STATE.t1_blobs.tsv"
  cp "$STATE.t1_blobs.tsv" "$ADIR/t1_blobs.tsv"
  # ④ 1차 auditor 산출물(정리 때 사라진다) + 재실행 V5 출력·발견 목록
  cp "$WT_A/$AUD/base_check.json" "$ADIR/attempt1_base_check.json"
  cp -r "$WT_A/$AUD" "$ADIR/attempt1_audit"
  diff -r "$WT_A/$AUD" "$ADIR/attempt1_audit" > /dev/null
  cp "$STATE.v5_attempt1.json" "$ADIR/attempt1_v5_rerun.json"
  cp "$STATE.findings.tsv" "$ADIR/attempt1_findings.tsv"
  # V5 질문 재료(오케스트레이터가 AskUserQuestion 문안에 그대로 -- card '결정 필요 항목' 범위 문장 + 이 발견 목록 + 해시)
  {
    echo "T0 V5 질문 재료 -- 1차 시도 base B1 $B1, test 끝 T1 $T1"
    echo "diff_hash(target) $DH"
    echo "diff_paths:"; for p in $paths; do echo "  $p"; done
    echo "발견(경로 / 단위 / 패턴 / 내용):"
    while IFS=$'\t' read -r p u pt dt; do echo "  $p / $u / $pt / $dt"; done < "$STATE.findings.tsv"
    echo "공개(해시 밖): unit selftest 3파일 import 출처 변경 3줄(7이름, 계약 11 -- [W-1] 답 (가))"
  } > "$ADIR/v5_question.txt"
  # V5 선택지 label(review_t0_carry_r1 S1): 정본 = t0_quote_check.py V5_APPROVE_LABEL·V5_REJECT_LABEL(records의 check_record가 같은 상수로 답을 잰다) -- 검사기 핀 먼저
  qchk_pin_ok
  "$PY" -B "$QCHK" labels > "$ADIR/v5_options.txt"
  test "$(wc -l < "$ADIR/v5_options.txt" | tr -d ' ')" = 2
  # ⑤ sha256 목록(①~④ 전부). 임시 출력은 보관 디렉터리 밖에(안에 두면 find가 그 파일 자체를 목록에 넣는다)
  ( cd "$ADIR" && find . -type f ! -name SHA256SUMS | LC_ALL=C sort | sed 's#^\./##' | while IFS= read -r f; do sha256sum -- "$f"; done ) > "$STATE.sums.tmp"
  mv "$STATE.sums.tmp" "$ADIR/SHA256SUMS"
  sums_ok
  # archive 끝 시각(UTC) -- records가 V5 tool_use 줄 timestamp > 이 값을 본다(이 보관 뒤에 물은 질문). 보관 디렉터리 밖(상태)에 둔다: SHA256SUMS가 다시 실행에서 바이트 같음(m3)
  st_set ARCHIVED_AT "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  st_set ARCHIVED 1
  echo "   운반: $D/ blob $(echo $paths | wc -w | tr -d ' ')개 + paths.tsv, 보관 $(wc -l < "$ADIR/SHA256SUMS" | tr -d ' ')파일(SHA256SUMS 대조 통과)"
  echo "   V5 질문 재료: $ADIR/v5_question.txt  선택지 label(두 줄 그대로): $ADIR/v5_options.txt"
  say "archive OK -- 다음: V5 질문(AskUserQuestion: 질문 문안에 v5_question.txt 전체를 바이트 그대로 담고(앞뒤 문장 추가 가능, '</'는 쓰지 않는다), 선택지 label = v5_options.txt 두 줄 그대로) -> 답을 $DRAFT의 <DATE>·<V5_ASKED_AT>('YYYY-MM-DD HH:MM KST' = 그 tool_use 줄 timestamp의 KST 분)·<V5_JSONL_NAME>·<V5_TOOLU>·<V5_QUESTION>·<V5_ANSWER>에 Edit(질문·답은 jsonl 원문 그대로, 여러 줄이면 줄마다 '> '·빈 줄은 '>' -- records가 그 toolu의 질문·고른 답 전체 일치 + V5 = 이 target·승인 label·archive 뒤 질문을 본다) -> records"
}

# ------------------------------------------------------------------ records (승인 기록 작성 -- 메인 worktree, 미커밋)
stage_records() {
  say "records: 승인 기록 $VAID(diff) 작성 + 사용자 원문 jsonl 대조 + parse-approval"
  test "$(st_get ARCHIVED)" = 1
  local B1 T1 DH paths C; B1=$(st_get B1); T1=$(st_get T1); DH=$(st_get DIFF_HASH); paths=$(st_get DIFF_PATHS); C=$(st_get CACHE)
  test "$C" = "$(cache_dir)"
  test -s "$DRAFT"; test -s "$JSONL"
  sums_ok
  # (pin) review_t0_carry m1: 검사기 바이트·초안 canon sha256 = 핀 상수(위 T0_*_SHA256 설명). 다르면 어떤 기록도 쓰기 전에 멈춘다
  local ph AAT
  qchk_pin_ok
  AAT=$(st_get ARCHIVED_AT)
  ph=$("$PY" -B "$QCHK" canon-sha "$DRAFT")
  if [ "$ph" != "$T0_DRAFT_SHA256" ]; then echo "[중단] 승인 초안 산문 핀 불일치(오케스트레이터 자리 밖이 바뀌었다): canon($DRAFT) = $ph, 핀 T0_DRAFT_SHA256 = $T0_DRAFT_SHA256 -- 정당한 변경이면 핀 상수를 고친다" >&2; false; fi
  if g cat-file -e "$B1:$F_A" 2>/dev/null; then echo "[중단] $F_A가 이미 B1 트리에 있다" >&2; false; fi
  # 중단 뒤 다시 실행: 미추적·미커밋 기록 파일만 다시 만든다(출력은 입력에서 결정적으로 나온다)
  if [ -e "$R/$F_A" ]; then g diff --cached --quiet -- "$F_A"; echo "   (다시 실행) 미커밋 $F_A를 지우고 다시 만든다"; rm -f "$R/$F_A"; fi
  # 초안 = 오케스트레이터가 사용자 답을 채운 판. 이 단계가 채우는 자리 = 해시·base·head·diff_path·발견 목록(정확히 한 번씩), 나머지 자리표시가 남으면 bytes_ok가 거부한다.
  # 사용자 원문 대조(review_t0_carry S1 -- fill_u3 check_jsonl 방식): '## 사용자 원문' 절 = 인용 블록 나열, 블록마다 머리 줄의 세션 jsonl 이름·toolu id 하나에 묶어
  #   질문 인용 = 그 tool_use input.questions[].question 하나와 전체 일치, 답 인용 = 그 tool_result 줄 toolUseResult.answers[질문]과 전체 일치(t0_quote_check.check_quotes).
  #   jsonl 이름은 --jsonl 파일의 폴더에서 찾는다(V5를 다른 세션에서 물었으면 V5 머리 줄의 이름이 그 세션 -- 읽기만).
  # review_t0_carry_r1 S1·m1: V5 블록은 이 target에 묶는다(t0_quote_check.check_record) -- 질문 인용 ⊇ 보관 v5_question.txt 전체(sums_ok 통과본, 그 안
  #   'diff_hash(target) <DIFF_HASH>' 줄), 답 = V5_APPROVE_LABEL(선택지에 있음), V5 tool_use 줄 timestamp > ARCHIVED_AT, V5_ASKED_AT = 그 timestamp KST 분.
  "$PY" -B - "$DRAFT" "$R/$F_A" "$DH" "$B1" "$T1" "$paths" "$STATE.findings.tsv" "$JSONL" "$QCHK" "$ADIR/v5_question.txt" "$AAT" <<'EOF'
import os, re, sys
draft, outp, dh, b1, t1, paths, ftsv, jsonl, qchk, v5qf, aat = sys.argv[1:12]
sys.path.insert(0, os.path.dirname(qchk))
import t0_quote_check as qc
t = open(draft, "rb").read().decode("utf-8")
assert "\r" not in t and not t.startswith("\ufeff")
def put(t, k, v):
    assert t.count(k) == 1, ("자리표시 %s가 정확히 한 번이 아니다" % k, t.count(k))
    return t.replace(k, v)
t = put(t, "<TARGET_DIFF_HASH_64>", dh)
t = put(t, "<DIFF_BASE_40>", b1)
t = put(t, "<DIFF_HEAD_40>", t1)
t = put(t, "diff_path: <DIFF_PATHS>", "\n".join("diff_path: " + p for p in paths.split()))
rows = [l.split("\t") for l in open(ftsv, encoding="utf-8").read().splitlines()]
t = put(t, "<FINDINGS_LIST>", "\n".join("* `%s` · `%s` · %s -- %s" % tuple(r) for r in rows))
left = re.findall(r"<[A-Z][A-Z0-9_]*>", t)
assert not left, ("채우지 않은 자리표시가 남았다(사용자 답을 초안에 먼저 Edit)", sorted(set(left)))
v5q = open(v5qf, "rb").read().decode("utf-8")
ok = qc.check_record(t, os.path.dirname(os.path.abspath(jsonl)), v5q, dh, aat)
open(outp, "wb").write(t.encode("utf-8"))
print("   초안 채움: 해시·base·head·diff_path %d줄·발견 %d줄, 인용 블록 %d개 = 자기 jsonl·toolu의 질문·고른 답 전체 일치: %s"
      % (len(paths.split()), len(rows), len(ok), "; ".join("%s(%s) 답 %r" % (tu, jn[:8], a) for tu, jn, a in ok)))
print("   V5 블록 = 이 target: 질문 ⊇ v5_question.txt 전체(diff_hash %s…), 답 = 승인 label %r, 질문 시각 > archive %s, V5_ASKED_AT 일치" % (dh[:16], qc.V5_APPROVE_LABEL, aat))
EOF
  bytes_ok "$R/$F_A"
  "$PY" -B "$C/merge_gate.py" parse-approval "$R/$F_A" > "$STATE.appr.json"
  "$PY" -B - "$STATE.appr.json" "$VAID" "$DH" "$B1" "$T1" "$paths" <<'EOF'
import json, sys
a = json.load(open(sys.argv[1], encoding="utf-8"))
aid, dh, b1, t1, paths = sys.argv[2:7]
exp = dict(id=aid, target_kind="diff", target=dh, diff_base=b1, diff_head=t1, diff_path=paths.split())
bad = {k: (a.get(k), v) for k, v in exp.items() if a.get(k) != v}
assert not bad, bad
print("   parse-approval OK: %s diff target %s… base %s head %s path %d" % (aid, dh[:16], b1[:7], t1[:7], len(paths.split())))
EOF
  st_set RECORDS 1
  say "records OK -- 다음은 cleanup(정리 명령 출력 -- 실행은 오케스트레이터 단독 호출, 되돌릴 수 없음)"
}

# ------------------------------------------------------------------ cleanup: 확인 + 명령 출력(실행하지 않는다 -- launch_common B1)
stage_cleanup() {
  say "cleanup: 1차 시도 정리 전 마지막 확인 + 정리 명령 출력(design 05 §12 '정리' 재시도 형태 -- test-only: test·audit 둘)"
  test "$(st_get RECORDS)" = 1
  local T1 C b p; T1=$(st_get T1); C=$(st_get CACHE)
  sums_ok
  "$PY" -B "$C/merge_gate.py" parse-approval "$R/$F_A" > /dev/null
  while IFS=$'\t' read -r p b; do test "$(git hash-object "$R/$D/$b.blob")" = "$b"; done < <(tr -d '\r' < "$R/$D/paths.tsv")
  test "$(g rev-parse "refs/heads/role/test/$ID")" = "$T1"
  local r n=0
  echo "   아래 명령을 순서대로 하나씩 단독 호출한다(병렬·묶음·tail 금지, 전체 출력 확인; EL1 거부면 출력 전체를 보고하고 멈춘다 -- 재시도 루프 금지):"
  for r in test audit; do
    if [ -e "$W/$ID-$r" ]; then n=$((n+1)); echo "     git -C $R worktree remove --force $W/$ID-$r"; fi
  done
  for r in test audit; do
    if g rev-parse -q --verify "refs/heads/role/$r/$ID" > /dev/null; then n=$((n+1)); echo "     git -C $R branch -D role/$r/$ID"; fi
  done
  st_set CLEANUP_PRINTED 1
  say "cleanup 명령 ${n}개 출력 -- 실행 뒤: $SELF local  (= cleaned -> commit -> final)"
}

stage_cleaned() {
  say "cleaned: 정리 결과 확인 -- refs/heads/role/ 0줄, $ID worktree 0"
  test "$(st_get RECORDS)" = 1; test "$(st_get CLEANUP_PRINTED)" = 1
  local r
  test -z "$(role_branches)" || { echo "[중단] refs/heads/role/에 브랜치가 남았다: $(role_branches | tr '\n' ' ') -- cleanup이 출력한 branch -D를 실행했는가(EL1이 문서 push를 거부한다)" >&2; false; }
  if g worktree list --porcelain | grep -q -- "/$ID-"; then echo "[중단] $ID worktree가 남았다 -- cleanup이 출력한 worktree remove를 실행했는가" >&2; false; fi
  for r in test code audit; do test ! -e "$W/$ID-$r" || { echo "[중단] $W/$ID-$r 경로가 남았다" >&2; false; }; done
  sums_ok
  st_set CLEANED 1
  say "cleaned OK: refs/heads/role/ 0줄 -- 다음은 commit"
}

# ------------------------------------------------------------------ commit: Role: doc 커밋 하나(승인 기록 + 운반 blob + paths.tsv)
stage_commit() {
  say "commit: 승인 기록 + 운반 blob·paths.tsv -- Role: doc 커밋 하나(spec card는 바꾸지 않는다 -- 머리 approval 줄에 $VAID가 이미 있다)"
  test "$(st_get CLEANED)" = 1
  local B1 T1 DH C p b files=""; B1=$(st_get B1); T1=$(st_get T1); DH=$(st_get DIFF_HASH)
  C=$(cache_dir); test "$C" = "$(st_get CACHE)"
  test "$(g rev-parse HEAD)" = "$B1"; test "$(g rev-parse gate/master)" = "$B1"
  test -z "$(role_branches)"
  g diff --cached --quiet
  while IFS=$'\t' read -r p b; do files="$files $D/$b.blob"; done < <(tr -d '\r' < "$R/$D/paths.tsv")
  # shellcheck disable=SC2086
  g add -- "$F_A" "$D/paths.tsv" $files
  # shellcheck disable=SC2086
  staged_is "$F_A" "$D/paths.tsv" $files
  local sums; sums=$("$PY" -B -c "
import sys
S = {}
for line in open(sys.argv[1], encoding='utf-8').read().splitlines():
    assert line[64] == ' ' and line[65] in ' *', line          # '<64자 해시> <' ' 또는 '*'><이름>'
    S[line[66:]] = line[:64]
keep = ['attempt1_base_check.json', 'attempt1_v5_rerun.json', 'commits.txt', 'T1.patch', 't1_blobs.tsv']
print('; '.join('%s %s' % (f, S[f]) for f in keep))" "$ADIR/SHA256SUMS")
  g commit -q -m "$SUBJ_C" \
    -m "T0 1차 시도(test-only, 순서 1~3): base B1 $B1, test 끝 T1 $T1 -- 정리됨(refs/heads/role/ 0줄, EL1 _judge_push). V5: weakening_diff --base B1 --head T1 FAIL, diff_hash $DH = 승인 기록 target. 2차 시도는 이 커밋을 담은 gate master(B2)에서 순서 1부터(test-author는 paths.tsv대로 .blob을 cp, _drafts/t0_carry.sh t2-check)." \
    -m "1차 산출물 보관 $A_LABEL(SHA256SUMS 발췌): $sums" \
    -m "승인 기록 입력 바이트 핀(records 대조값 -- 한쪽만 바뀐 것 탐지용, 무결성 증거 아님): 초안 _drafts/approval_$VAID.md canon sha256 $T0_DRAFT_SHA256, _drafts/t0_quote_check.py sha256 $T0_QCHK_SHA256." \
    --trailer "Role: doc" --trailer "Change-Id: $ID" --trailer "$COAUTH"
  test "$(g log -1 --format=%s)" = "$SUBJ_C"
  # 커밋 트리 대조: 운반 blob = T1 blob(줄바꿈 변환 없음), head 트리 V5 조회가 target을 찾는다
  while IFS=$'\t' read -r p b; do
    test "$(g rev-parse "HEAD:$D/$b.blob")" = "$b"
    test "$(g rev-parse "HEAD:$D/$b.blob")" = "$(g rev-parse "$T1:$p")"
  done < <(g show "HEAD:$D/paths.tsv" | tr -d '\r')
  "$PY" -B - "$C" "$R" "$DH" "$VAID" <<'EOF'
import sys
sys.path.insert(0, sys.argv[1])
import weakening_diff as wd, merge_gate as mg
c, r, dh, aid = sys.argv[1:5]
assert dh in wd.approved_hashes(r, "HEAD"), "V5 조회(head 트리)가 승인 기록을 못 찾음"
apps = mg.load_approvals(mg.TreeView(["-C", r], "HEAD"))
assert any(a["id"] == aid and a["target_kind"] == "diff" and a["target"] == dh for a in apps)
print("   HEAD 조회: weakening_diff.approved_hashes ∋ target, merge_gate.load_approvals ∋ %s" % aid)
EOF
  st_set C "$(g rev-parse HEAD)"
  say "commit OK: $(g rev-parse --short HEAD)"
}

stage_final() {
  say "final: push 전 종합 확인"
  local B1 CC; B1=$(st_get B1); CC=$(st_get C)
  test "$(g rev-parse HEAD)" = "$CC"; test "$(g rev-parse HEAD^)" = "$B1"
  test "$(g rev-parse gate/master)" = "$B1"
  test "$(g rev-list --count "$B1..HEAD")" = 1
  test -z "$(role_branches)"
  if g worktree list --porcelain | grep -q -- "/$ID-"; then echo "[중단] $ID worktree가 남았다" >&2; false; fi
  test "$(trailer_of HEAD Role)" = doc; test "$(trailer_of HEAD Change-Id)" = "$ID"
  test -z "$(g status --porcelain -- docs/ .ai/)"
  test -z "$(g diff --name-only "$B1" HEAD -- skills/ workspaces/ tools/)"
  sums_ok
  g log --format='%h %s' "$B1..HEAD"
  g diff-tree --no-commit-id --name-status -r HEAD
  say "final OK -- 다음은 push 단독 호출(병렬·tail 금지, 전체 출력 확인, 거부면 출력 전체를 보고하고 멈춘다 -- 재시도 루프 금지):  $(lc_push_cmd "$R")   그 뒤 $SELF after-push"
}

stage_after_push() {
  say "after-push: gate master = C = 2차 base B2"
  local B1 CC DH b p; B1=$(st_get B1); CC=$(st_get C); DH=$(st_get DIFF_HASH)
  g fetch gate
  test "$(g rev-parse gate/master)" = "$CC"
  test "$(g rev-parse HEAD)" = "$CC"
  local B2=$CC
  g diff --quiet "$B1" "$B2" -- skills/ workspaces/ tools/            # B1·B2 사이 엔진·test·게이트 같음 -> 발견 경로 base blob 같음 -> 해시 식 입력 같음
  local C; C=$(cache_dir); st_set CACHE "$C"                           # 게이트 캐시는 gate master 하나(ensure_cache 상한) -- 2차 역할·auditor가 쓸 B2 판
  "$PY" -B - "$C" "$R" "$B2" "$DH" <<'EOF'
import sys
sys.path.insert(0, sys.argv[1])
import weakening_diff as wd
c, r, b2, dh = sys.argv[1:5]
assert dh in wd.approved_hashes(r, b2)
print("   gate master(B2) 트리: V5 승인 target 있음")
EOF
  st_set B2 "$B2"
  say "after-push OK -- B2 = $B2. 2차 시도(오케스트레이터 단독 호출, 이 스크립트는 실행하지 않는다):"
  echo "   순서 1:  git -C $R worktree add $W/$ID-test -b role/test/$ID gate/master"
  echo "   순서 2 test-author(t0_briefs.md 1절 + '2차 시도' 문단): $D/paths.tsv대로 각 .blob을 cp로 원래 경로에(손으로 다시 쓰지 않는다),"
  echo "     paths.tsv는 'git -C $W/$ID-test show HEAD:$D/paths.tsv'로 읽는다(작업 트리 사본은 core.autocrlf로 CRLF일 수 있다 -- blob id 끝 \\r),"
  echo "     발견 밖 경로는 ${A_LABEL}T1.patch의 + 줄로 Write/Edit(apply·cherry-pick 금지), Role: test 커밋(여럿 가능)."
  echo "   2차 test 커밋 뒤, 순서 3 전:  $SELF t2-check   (바뀐 경로·blob 전부 = 1차, head V5 approved -- 다르면 test-author에게 고치게 하고 다시)"
  echo "   순서 3:  git -C $R worktree add $W/$ID-audit -b role/audit/$ID role/test/$ID   (auditor 3.1 -- 쓰기만, 커밋 금지)"
  echo "   순서 7 전 빈 브랜치 가드:  git -C $W/$ID-audit log --oneline role/test/$ID..HEAD   (빈 출력) -- test-only: 순서 4·5·6(병합) 없음, audit 커밋은 T2 바로 위"
  echo "   순서 7 auditor(3.2): V1 -c 캐시 old = B2, V5 approved target $DH(basis에 'B1·B2 사이 skills/·workspaces/·tools/ 같음, t2-check 같음'), approvals 셋"
  # review_t0_carry m4·m5: 순서 8 뒤 메인을 gate master로 fast-forward(purge가 HEAD = gate/master를 요구) -- 명령은 한 줄씩 단독, 옵션까지 그대로
  echo "   순서 8:  git -C $W/$ID-audit push gate role/audit/$ID:master   (단독, 전체 출력 확인)"
  echo "     ->  git -C $R fetch gate   ->  git -C $R merge --ff-only gate/master   (HEAD = gate/master 확인)"
  echo "     ->  정리(한 줄씩 단독):  git -C $R worktree remove --force $W/$ID-test  ·  git -C $R worktree remove --force $W/$ID-audit  ·  git -C $R branch -D role/test/$ID  ·  git -C $R branch -D role/audit/$ID"
  echo "     ->  $SELF purge   ->  push 단독:  $(lc_push_cmd "$R")"
}

# ------------------------------------------------------------------ t2-check: 2차 test 커밋 = 1차와 같은 blob(순서 3 전)
stage_t2_check() {
  say "t2-check: 2차 test 끝 T2 = 1차 T1과 바뀐 경로·blob 전부 같음, head V5 approved"
  local B2 DH paths C; B2=$(st_get B2); DH=$(st_get DIFF_HASH); paths=$(st_get DIFF_PATHS)
  g fetch gate
  test "$(g rev-parse gate/master)" = "$B2"
  test "$(role_branches | tr '\n' ' ')" = "refs/heads/role/test/$ID "     # 순서 3 전(audit 없음)
  local T2; T2=$(g rev-parse "refs/heads/role/test/$ID")
  test_chain_ok "$B2" "$T2"
  test -z "$(git -C "$WT_T" status --porcelain)" || { echo "[중단] 2차 test worktree에 미커밋 변경이 있다" >&2; false; }
  # review_t0_carry m2: 1차 기준 = 보관 $ADIR/t1_blobs.tsv(SHA256SUMS 대조 -- 커밋 본문 발췌와 한 사슬), 상태 파일 옆 사본과도 같아야 한다
  sums_ok || { echo "[중단] 보관 $ADIR SHA256SUMS 대조 실패" >&2; false; }
  cmp -s "$ADIR/t1_blobs.tsv" "$STATE.t1_blobs.tsv" || { echo "[중단] 보관 t1_blobs.tsv != 상태 파일 옆 사본 $STATE.t1_blobs.tsv" >&2; false; }
  changed_blobs "$B2" "$T2" > "$STATE.t2_blobs.tsv"
  if ! cmp -s "$ADIR/t1_blobs.tsv" "$STATE.t2_blobs.tsv"; then
    echo "[중단] 2차 바뀐 경로·blob이 1차와 다르다(< 1차, > 2차) -- test-author에게 차이를 고치게 한다(새 Role: test 커밋), 해시가 달라지면 승인 무효:" >&2
    diff "$ADIR/t1_blobs.tsv" "$STATE.t2_blobs.tsv" >&2 || true
    false
  fi
  C=$(cache_dir); test "$C" = "$(st_get CACHE)"
  wd_run "$C" "$B2" "$T2" "$STATE.v5_attempt2.json"
  "$PY" -B - "$STATE.v5_attempt2.json" "$DH" "$paths" <<'EOF'
import json, sys
rr = json.load(open(sys.argv[1], encoding="utf-8"))
assert rr["diff_paths"] == sys.argv[3].split(), ("2차 diff_paths != 1차", rr["diff_paths"])
assert rr["diff_hash"] == sys.argv[2], ("2차 diff_hash != target", rr["diff_hash"])
assert rr["approved"] is True and rr["verdict"] == "PASS", (rr["verdict"], rr["approved"])
print("   2차 V5(base B2, head T2): PASS approved, diff_hash = target, diff_paths = 1차")
EOF
  st_set T2 "$T2"
  say "t2-check OK: T2 ${T2:0:7} -- 다음은 순서 3(audit worktree, 단독 호출)"
}

# ------------------------------------------------------------------ purge: 병합 뒤 운반 디렉터리 삭제(design 05 §12 (4))
stage_purge() {
  say "purge: T0 병합·정리 뒤 운반 디렉터리 $D 삭제 -- Role: doc 커밋"
  g fetch gate
  local H; H=$(g rev-parse gate/master)
  test "$(g rev-parse HEAD)" = "$H"
  test -z "$(role_branches)"
  if g worktree list --porcelain | grep -q -- "/$ID-"; then echo "[중단] $ID worktree가 남았다" >&2; false; fi
  lc_pred_ok "$R" "$H" "$ID" || { echo "[중단] gate master에 $ID 판정 기록(V1~V10 PASS·N/A)이 없다 -- 병합 전에는 지우지 않는다" >&2; false; }
  g cat-file -e "$H:$F_A"
  g cat-file -e "$H:$D/paths.tsv"
  g diff --cached --quiet
  test -z "$(g status --porcelain -- docs/ .ai/)"
  g rm -r -q -- "$D"
  test -z "$(g diff --cached --name-only | grep -v "^$D/" || true)"
  g commit -q -m "$SUBJ_P" -m "승인 기록 $F_A는 남긴다(판정 기록 approvals가 가리킨다)." --trailer "Role: doc" --trailer "Change-Id: $ID" --trailer "$COAUTH"
  test "$(g log -1 --format=%s)" = "$SUBJ_P"
  test "$(g rev-parse HEAD^)" = "$H"
  if g cat-file -e "HEAD:$D" 2>/dev/null; then echo "[중단] 커밋 뒤에도 $D가 있다" >&2; false; fi
  g cat-file -e "HEAD:$F_A"
  g diff-tree --no-commit-id --name-status -r HEAD
  say "purge OK -- 다음은 push 단독 호출(병렬·tail 금지, 전체 출력 확인):  $(lc_push_cmd "$R")"
}

case "$1" in
  check) stage_check ;;
  archive) stage_archive ;;
  prep) stage_check; stage_archive ;;
  records) stage_records ;;
  cleanup) stage_cleanup ;;
  cleaned) stage_cleaned ;;
  commit) stage_commit ;;
  final) stage_final ;;
  local) stage_cleaned; stage_commit; stage_final ;;
  after-push) stage_after_push ;;
  t2-check) stage_t2_check ;;
  purge) stage_purge ;;
  *) echo "사용: $0 [옵션…] prep|check|archive|records|cleanup|cleaned|local|commit|final|after-push|t2-check|purge" >&2; exit 2 ;;
esac
