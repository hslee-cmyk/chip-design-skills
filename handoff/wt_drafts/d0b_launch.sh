#!/usr/bin/env bash
# D0b card 20260930-p3-registry-dest 착수 0단계(오케스트레이터) -- FU·D0a 병합 뒤, M1 앞. D0b 병합이 D-27 동결의 시작점이다.
# 근거: spec card 초안(draft_p3_d0b.spec.md) '의도'·계약 3·5·8(멈춤 조건)·oracle (d)-1 표·'작성 전 실측', d0b_briefs.md 0절 착수 조건 S-1~S-7·'착수 0단계'·0.4 멈춤 절차·4절(동결 공지),
#       design 30 §6.3 MP_ARGS(정본 -- gate의 design 30 문서에서 읽는다)·§8 D0b 행·§8.1 확정 순서·D-27.
# 구조는 b26pre_launch.sh를 따른다(단계별 함수, 옵션은 단계 이름 앞, measured rev 단일 출처, 게이트 캐시 절대 경로, push·worktree는 출력만 -- EL1 판정 대상).
# 어느 확인이든 실패하면 그 자리에서 멈춘다(set -Eeuo pipefail + ERR trap).
#
# 커밋 순서(push 한 번 -- 승인 기록 20260930-30-module-split-design은 p3_design_commit.sh가 이미 올렸다, S-1):
#   S  spec card + interface card(게이트 캐시 interface_card.py, 절대 경로)  -> push (단독)
#
#   bash d0b_launch.sh --iso /c/g<n>/d0b-iso conds   # S-1~S-7 판정(읽기 전용 -- fetch 안 함). S-4·S-5·S-7은 gate 트리의 D0a 도구 plan을 격리 복제본에서 돌린다(그 폴더만 쓰고 지운다)
#                                                    #   exit 0 = 전부 충족, 3 = 미충족(표 + 멈춤 절차 안내), 1 = 규약 불일치(초안 머리·measured 앵커 사슬·plan exit 2·MP_ARGS 모양)
#   bash d0b_launch.sh --iso … local                  # pre -> card -> final  (로컬 커밋 S, push 안 함 -- 끝에 push 명령 출력)
#   bash d0b_launch.sh after-push                     # push 뒤: gate master = S, 게이트 캐시 새 판 + S-6 대기열 + test worktree 명령 출력
#   bash d0b_launch.sh freeze                         # D0b 판정 기록 병합 뒤: D-27 동결 공지(시작 = 판정 기록 code_commit)와 M1 착수 전 확인 명령 출력
#   bash d0b_launch.sh <단계>                         # pre | card | final 하나만(중단 뒤 이어 하기 -- 각 단계가 앞 단계 결과를 확인)
#   plan 출력은 gate master 판마다 상태 파일 옆에 캐시한다(<상태>.plan.<sha>.json -- 같은 판이면 다시 돌리지 않는다, 19~33초). 캐시가 없을 때만 --iso가 필요하다.
#   plan 요약(S-4·S-5·S-7 판정 입력, (d)-1 표본 대조 포함)은 (gate sha, 초안 sha256, 이 스크립트 sha256)마다 따로 캐시한다(<상태>.plan.<sha>.json.sum.<초안 16자>.<스크립트 16자>.json) -- 초안 표나 스크립트 상수·요약 코드를 고치면 다시 계산한다.
#   S-7 표 사실 요약((d)-1 표 파싱 단일 출처 + 레지스트리 행 유무·base red·표본 수·행 없는 A-6 표본 -- plan 없이 gate 트리만 읽는다, D0a 전에도 돈다)도 같은 키로 캐시한다(<상태>.facts.<sha>.<초안 16자>.<스크립트 16자>.json).
#   plan이 exit 2·첫 줄 JSON 아님이면 S-4가 규약오류(1)와 함께 캐시 지우는 명령(rm -f -- <상태>.plan.<sha>.json*)을 출력한다 -- 지우기 전까지 같은 판은 그 캐시를 다시 쓴다.
#   단 exit 2가 D0a 계약 2 (e5)·(e6)(레지스트리 칸 모순)이면 지워도 같다 -- spec 계약 8 (g) 경로(N3.10 토큰, D-11).
#
# 사전 시험 옵션(반드시 단계 이름 앞에): --repo <복제본> --state <상태 파일> --wt <worktree 부모> [--draft-spec <초안 사본>]
#   --repo를 주면 --state·--wt 필수. --draft-spec은 복제본 모드에서만. 실제 저장소 판별은 launch_common.sh lc_repo_guard.
#   --iso <C:/g<n>/…>(모든 모드): 없는 경로여야 하고 이 스크립트가 만들고 지운다.
set -Eeuo pipefail
shopt -s inherit_errexit
trap 'echo "[중단] ${BASH_SOURCE[0]}:${LINENO}: ${BASH_COMMAND}" >&2' ERR
. "$(dirname -- "${BASH_SOURCE[0]}")/launch_common.sh"

# MSYS2 자식 bash는 HOME·APPDATA를 잃는다(post_p10b_runbook.sh와 같은 실측). TEMP·TMP는 lc_tmp_setup(상태 파일 옆)
export HOME=/c/Users/HSLEE
export APPDATA='C:\Users\HSLEE\AppData\Roaming' LOCALAPPDATA='C:\Users\HSLEE\AppData\Local' USERPROFILE='C:\Users\HSLEE'
export PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8

R_REAL=$LC_R_REAL
R=$R_REAL
W_REAL=$LC_W_REAL
W=$W_REAL
DR=$W_REAL/_drafts
STATE_REAL=$DR/d0b_launch_state.txt
STATE=$STATE_REAL
DRAFT_REAL=$DR/draft_p3_d0b.spec.md
DRAFT_SPEC=$DRAFT_REAL
ISO=
while [ $# -gt 1 ]; do
  case "$1" in
    --repo) R=$2; shift 2 ;;
    --state) STATE=$2; shift 2 ;;
    --wt) W=$2; shift 2 ;;
    --draft-spec) DRAFT_SPEC=$2; shift 2 ;;
    --iso) ISO=$2; shift 2 ;;
    *) break ;;
  esac
done
# 단계 이름 뒤에 옵션을 붙이면 조용히 무시돼 실제 저장소에서 돈다(review_post_p10b_runbook B1과 같은 가드) -- 남은 인자는 단계 이름 하나뿐
[ $# -eq 1 ] || { echo "[중단] 사용법: $0 [--repo R --state S --wt W [--draft-spec F]] [--iso /c/g<n>/<이름>] <단계>  (옵션은 단계 이름 앞에만)" >&2; exit 2; }
case "$1" in --*) echo "[중단] 단계 이름 자리에 옵션: $1 (옵션 값이 빠졌거나 순서가 틀렸다)" >&2; exit 2 ;; esac
lc_repo_guard "$R" "$R_REAL"
if [ "$LC_REAL" = 0 ]; then
  lc_need_sandbox --state "$STATE" "$STATE_REAL"; lc_need_sandbox --wt "$W" "$W_REAL"
  case "$DRAFT_SPEC" in /*|[A-Za-z]:[/\\]*) ;; *) echo "[중단] --draft-spec은 절대 경로로($DRAFT_SPEC)" >&2; exit 2 ;; esac
else
  lc_need_real --state "$STATE" "$STATE_REAL"; lc_need_real --wt "$W" "$W_REAL"; lc_need_real --draft-spec "$DRAFT_SPEC" "$DRAFT_REAL"
  STATE=$STATE_REAL; W=$W_REAL; DRAFT_SPEC=$DRAFT_REAL
fi
# 격리 복제본 경로: /c/g<번호>/<이름> 하나(그 폴더만 쓰고 지운다 -- 저장소·wt·_drafts 밖). 정규화 뒤 c:/g<n>/… 모양만
if [ -n "$ISO" ]; then
  ISO_N=$(lc_norm "$ISO") || { echo "[중단] --iso 경로 해석 실패: $ISO" >&2; exit 2; }
  case "$ISO_N" in c:/g[0-9]*/?*) ;; *) echo "[중단] --iso는 /c/g<번호>/<이름>만($ISO -> $ISO_N)" >&2; exit 2 ;; esac
  case "${ISO_N#c:/g}" in [0-9]*/*) ;; *) echo "[중단] --iso 모양: $ISO" >&2; exit 2 ;; esac
  ISO=$(cygpath -u -- "$ISO_N")
fi
lc_tmp_setup "$STATE"
# plan 요약 캐시 키에 초안 sha256을 넣는다(review_d0a_d0b_ready D0b-S1): 요약에는 초안에서 읽은 (d)-1 표본 대조가 들어 있어 gate sha만으로 키를 잡으면
# 같은 판에서 표를 고친 초안을 다시 재도 낡은 S-7 판정이 나온다. 초안이 없으면 draft_ok가 규약 불일치로 멈추므로 여기서는 키를 none으로 둔다
DRAFT_SHA=$( [ -s "$DRAFT_SPEC" ] && sha256sum < "$DRAFT_SPEC" | cut -c1-64 || printf none)   # 표준 입력으로 -- 경로의 역슬래시가 출력 앞에 '\'를 붙이지 않게
# 키에 이 스크립트 자신의 sha256도 넣는다(review_d0a_d0b_ready_r1 D0b-r1-m1): 요약은 RULE_IDS·SIX·D11NAME 상수와 plan_sum heredoc 요약 코드에도 의존한다.
# 멈춤 절차 뒤 상수·요약 코드만 고치고 같은 판·같은 초안으로 다시 재도 새 키라 다시 계산된다. 파일 경로 길이(260자) 때문에 두 sha는 앞 16자씩만 쓴다
SELF_SHA=$(sha256sum < "${BASH_SOURCE[0]}" | cut -c1-64)
SUM_KEY=${DRAFT_SHA:0:16}.${SELF_SHA:0:16}
echo "== 대상 저장소 R=$R  상태 파일 $STATE  worktree 부모 $W  초안 $DRAFT_SPEC(sha256 ${DRAFT_SHA:0:16}…)  스크립트 sha256 ${SELF_SHA:0:16}…  격리 복제본 ${ISO:-(없음)}"

PY=$LC_PY
ID=20260930-p3-registry-dest
AID=20260930-30-module-split-design
D0AID=20260930-p3-move-plan-tool
FUID=20261002-p3-future-annotations
# UD-6(2026-10-02): [D-11] (가) N3.10 MOD1 `_QUERY_CACHE_MAX` 토큰 -- target_kind diff 승인, D0b spec card approval 둘째 줄(spec 계약 8 (a)). 문서 커밋 29d2fc2 + 승인 기록 300fd65 -- gate에 있다(S-1이 다시 본다)
D11ID=20261002-p3-d11-query-cache-max
D11TOK='`_multilinear_interp_point_multi`, `_QUERY_CACHE_MAX`, `_solve_vgs`'
# S-7(review_ud6 m4): 승인 기록 '재검토'·runbook §3 -- D0b base plan에서 이 단위의 배정 근거 규칙이 A-1이어야 한다(mod 줄기 gmid_lut는 (d)-1 표가 본다)
D11NAME=_QUERY_CACHE_MAX
D11RULE=A-1
# 선행 card(design 30 §8 D0b 행·§8.1: B34 → b26pre → backfill → B26-1 → B33 → G1 → FU → D0a, FU는 B33 뒤 D0b 전 아무 때나)
B26ID=20260930-b26-rail-accessor-set
PREDS="20260930-b34-grammar-explicit 20260930-b26-pre-test-strengthen 20261001-b26-backfill-interdig-final-audit $B26ID 20260930-v7-registry-edges 20260930-p3-gate-move-aware $FUID $D0AID"
# S-7 (te2, review_d0b_te S-1): (d)-1 표에서 'B26-1 병합 뒤에만 있다'고 적힌 행 = B26-1이 더하는 표본(이름 목록은 표가 정본 -- 여기 적지 않는다)
B26MARK='B26-1 병합 뒤에만 있다'
PLAN=docs/01-plan/features/gain-budget-gmid-sizing.plan.md
REG=docs/03-analysis/gain-budget-gmid-sizing.function-registry.md
D30=docs/02-design/features/gain-budget-gmid-sizing.30-module-split.design.md
DOD=docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/phase2-dod.md
F_SPEC=docs/02-design/specs/$ID.spec.md
F_IFC=docs/02-design/specs/$ID.interface.md
A=skills/analog-gmid-design/assets
TOOL=tools/migrate/move_plan.py
NEWT=$A/tests/contracts/test_p3_registry_dest.py
FU_FILES="$A/design_report.py $A/audit_current_forced.py"
# measured rev 이후 바뀌면 D0b base 사실(plan 입력 전부 + 새 test 경로)을 다시 재야 하는 경로 -- plan 입력 = 계획서·레지스트리·엔진(split 5파일 포함)·게이트·도구
MEAS_PATHS=("$PLAN" "$REG" tools/gates tools/migrate ":(glob)$A/*.py" workspaces/run_harness.py "$A/tests/contracts")   # 배열 -- 글롭이 bash에서 풀리지 않게, :(glob) = 하위 디렉터리 제외
# D0a 계약 2 규칙 ID 집합(design 30 §6.2 D-31) -- spec 계약 6 (c)와 같은 집합
RULE_IDS="A-0 A-1 A-2 A-3 A-4 A-K A-5 A-6 A-7"
# reg_mismatch 밖 여섯(spec 계약 3·8 (a)~(d), d0b_briefs S-5)
SIX="conflicts upward cycles unassigned import_time_high import_conflicts"
COAUTH="Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
APPR_IDS="$AID $D11ID"
NSEC=11
NCOND=8
SUBJ_S="docs: D0b spec card $ID(레지스트리 '이관 목적지' 열 = move_plan plan 배정 + 근거 규칙 열, 보류(Phase 3) 9 -> 보류(Phase 4), 계약 test test_p3_registry_dest -- plan 판정 목록 일곱 빈 목록·MOD7·(d)-1 표본, red-green, phase 3, 승인 $AID·$D11ID; 병합부터 D-27 동결) + interface card"

say() { printf '%s\n' "== $*"; }
g() { git -C "$R" "$@"; }
st_set() { touch "$STATE"; grep -v "^$1=" "$STATE" > "$STATE.tmp" || true; printf '%s=%s\n' "$1" "$2" >> "$STATE.tmp"; mv "$STATE.tmp" "$STATE"; }
st_get() { local v; v=$(grep "^$1=" "$STATE" | tail -1 | cut -d= -f2-); test -n "$v"; printf '%s' "$v"; }
cache_dir() {
  local c
  c=$("$PY" -B -c "import sys;sys.path.insert(0,sys.argv[1]);import role_paths as rp;print(rp.ensure_cache(rp.load_env(sys.argv[2])))" "$R/tools/gates" "$R")
  test "$(basename "$c")" = "$(g rev-parse gate/master)"
  test -f "$c/interface_card.py"
  printf '%s' "$c"
}
plan_hash() { "$PY" -B "$1/merge_gate.py" plan-tables-hash "$R/$PLAN"; }
staged_is() { test "$(g diff --cached --name-only | sort | tr '\n' ' ')" = "$(printf '%s\n' "$@" | sort | tr '\n' ' ')"; }
head_subj_is() { test "$(g log -1 --format=%s)" = "$1"; }
trailer_is() {   # <커밋> <키> <값|-(없음)>
  local v; v=$(g log -1 --format="%(trailers:key=$2,valueonly)" "$1" | tr -d '\r' | grep -v '^$' || true)
  if [ "$3" = - ]; then test -z "$v"; else test "$v" = "$3"; fi
}
approved_ids() { "$PY" -B -c "
import sys;sys.path.insert(0,sys.argv[1]);import reachability as r
print('\n'.join(sorted(r._approved_ids(sys.argv[2],sys.argv[3]))))" "$1" "$R" "$2"; }
draft_approvals() {
  "$PY" -B -c "
import sys
t=open(sys.argv[1],encoding='utf-8').read().replace('\r\n','\n')
assert t.startswith('---\n'); h=t.split('\n---\n',1)[0]
print(' '.join(l.split(':',1)[1].strip() for l in h.split('\n') if l.startswith('approval:')))" "$DRAFT_SPEC"
}
draft_id() { sed -n '2p' "$DRAFT_SPEC" | tr -d '\r' | sed -n 's/^id: //p'; }
approval_rc() {   # <H> <캐시> <id> -- 0 있음(parse-approval id 일치) / 3 없음·위반
  local H=$1 C=$2 a=$3 t
  g cat-file -e "$H:.ai/approvals/$a.md" 2>/dev/null || { echo "      승인 기록 $a: gate ${H:0:7}에 없음" >&2; return 3; }
  t=$(mktemp -d)
  g show "$H:.ai/approvals/$a.md" > "$t/$a.md"
  if "$PY" -B "$C/merge_gate.py" parse-approval "$t/$a.md" | "$PY" -B -c "import json,sys;r=json.load(sys.stdin);assert r['id']==sys.argv[1],r['id']" "$a"; then
    rm -rf "$t"; return 0
  fi
  rm -rf "$t"; echo "      승인 기록 $a: parse-approval 실패 또는 id 다름" >&2; return 3
}
MEAS_PAT='\*\*measured at `[0-9a-f]\{7,40\}`\*\*'
meas_rev() {
  local s; s=$(lc_meas_short "$R" "$DRAFT_SPEC" "$MEAS_PAT")
  test -n "$s"
  g rev-parse --verify "$s^{commit}"
}

# ---------------------------------------------------------------- MP_ARGS 단일 출처 = gate <H>의 design 30 §6.3 bash 배열(첫 'MP_ARGS=(' 블록). 실패 1
# 결과: $STATE.mpargs.<H>(NUL 구분). 모양 단언: --plan·--registry 값이 이 스크립트의 PLAN·REG, --split·--keep·--aliases 있음, --aliases 값 JSON
mpargs_load() {   # <H>
  local H=$1 f="$STATE.mpargs.$1"
  [ -s "$f" ] && return 0
  g cat-file -e "$H:$D30" 2>/dev/null || { echo "      design 30 문서 없음 -- MP_ARGS를 읽을 수 없다" >&2; return 1; }
  g show "$H:$D30" | "$PY" -B -c "
import json, shlex, sys
t = sys.stdin.buffer.read().decode('utf-8').replace('\r\n', '\n')
i = t.index('\nMP_ARGS=(') + 1
blk = t[i:].split('\n')
body = []
for l in blk:
    body.append(l)
    if l.rstrip().endswith(')'):
        break
s = '\n'.join(body)
assert s.startswith('MP_ARGS=(') and s.rstrip().endswith(')'), s[:80]
a = shlex.split(s[len('MP_ARGS=('):s.rstrip().rindex(')')])
assert a[0:2] == ['--plan', sys.argv[1]] and a[2:4] == ['--registry', sys.argv[2]], a[:4]
for k in ('--split', '--keep', '--aliases'):
    assert k in a, k
json.loads(a[a.index('--aliases') + 1])
sys.stdout.buffer.write(b'\0'.join(x.encode('utf-8') for x in a))
" "$PLAN" "$REG" > "$f.tmp" || { rm -f "$f.tmp"; echo "      design 30 §6.3 MP_ARGS 블록 모양이 다르다" >&2; return 1; }
  mv "$f.tmp" "$f"
}

# ---------------------------------------------------------------- gate 트리의 D0a 도구로 plan(격리 복제본, 판마다 캐시). <H> -> $STATE.plan.<H>.json + .rc
ISO_MADE=0
iso_cleanup() { if [ "$ISO_MADE" = 1 ] && [ -n "$ISO" ] && [ -d "$ISO" ]; then rm -rf -- "$ISO"; fi; ISO_MADE=0; }
trap 'iso_cleanup' EXIT
plan_at() {   # <H>
  local H=$1 out="$STATE.plan.$1.json" rc=0
  [ -s "$out" ] && [ -s "$out.rc" ] && return 0
  g cat-file -e "$H:$TOOL" 2>/dev/null || { echo "      gate ${H:0:7}에 $TOOL 없음(D0a 미병합)" >&2; return 3; }
  [ -n "$ISO" ] || { echo "      plan 캐시가 없다 -- --iso /c/g<n>/<이름>을 단계 이름 앞에 준다" >&2; return 1; }
  [ ! -e "$ISO" ] || { echo "      --iso $ISO가 이미 있다(없는 경로만)" >&2; return 1; }
  mpargs_load "$H" || return 1
  local -a MP; mapfile -d '' MP < "$STATE.mpargs.$H"
  mkdir -p "$ISO/nohooks"; ISO_MADE=1
  git init -q "$ISO/r"
  git -C "$ISO/r" config core.hooksPath "$ISO/nohooks"
  git -C "$ISO/r" config core.longpaths true
  git -C "$ISO/r" fetch -q --no-tags "$R" "+refs/remotes/gate/master:refs/heads/base" || { iso_cleanup; return 1; }
  [ "$(git -C "$ISO/r" rev-parse base)" = "$H" ] || { iso_cleanup; echo "      격리 복제본 base != ${H:0:7}" >&2; return 1; }
  git -C "$ISO/r" checkout -q base
  local t0=$SECONDS
  "$PY" -B "$ISO/r/$TOOL" plan --root "$ISO/r" --rev "$H" "${MP[@]}" > "$out.tmp" 2> "$out.err" || rc=$?
  echo "      plan(gate ${H:0:7}의 $TOOL, 격리 복제본) exit $rc, $((SECONDS - t0))초" >&2
  iso_cleanup
  rm -f "$out".sum.*                                                  # 새 plan 출력이면 옛 출력의 요약은 모두 낡았다(캐시를 지우고 다시 잰 경우 -- D0b-r1-m2)
  mv "$out.tmp" "$out"; printf '%s' "$rc" > "$out.rc"
}
# plan 출력 요약((gate 판, 초안 sha256, 스크립트 sha256)마다 캐시 -- D0b-S1·r1-m1): <H> <캐시> -> $(sum_path <H>)
sum_path() { printf '%s' "$STATE.plan.$1.json.sum.$SUM_KEY.json"; }
# plan 캐시 지우기 안내(D0b-r1-m2): exit 2·첫 줄 JSON 아님은 일시 오류일 수도 있는데 판마다 캐시되어 같은 판에서는 계속 규약오류다
plan_clear_hint() { printf '      (일시 오류였으면 이 판의 plan 캐시와 요약을 지우고 --iso로 다시: rm -f -- %q*  -- 같은 판이면 지우기 전까지 이 캐시를 다시 쓴다)\n' "$STATE.plan.$1.json" >&2; }
# S-7 표 사실 요약((gate 판, 초안 sha256, 스크립트 sha256)마다 캐시 -- plan_sum과 같은 키): <H> <캐시> -> $(fact_path <H>)
# plan 없이 gate 트리만 읽는다(레지스트리·계획 N3.10·design 30 §6.3 MP_ARGS·엔진 파일 = A/*.py 최상위 + workspaces/run_harness.py -- reg_check의 엔진 정의와 같은 집합).
# 입력은 전부 gate <H> 트리(키의 H)와 초안(키의 초안 sha) -- MP_ARGS도 H의 design 30에서 읽는다(mpargs_load).
#   rows        (d)-1 표(단위, 기대 줄기, '행', '규칙', 근거) -- 표 파싱의 단일 출처(plan_sum도 이것을 읽는다). 칸 분할은 게이트 role_paths._split_cells(`\|` 이스케이프 인식, review_d0b_s7 m6)
#   decl        표 아래 선언 '표본 **N**개 = 표 M행 전부(행 있는 X·없는 Y)'의 [N, M, X, Y]  / decl_red '행 있는 표본 X개 중 Y개의 칸이 기대 줄기와 다르다'의 [X, Y]
#               -- 두 문장 모두 절 안에 정확히 한 번(재측정 문단이 옛 수를 담은 문장을 덧붙이면 멈춘다, m5)
#   row_mismatch [단위, 표 '행', base 레지스트리에 함수 칸 첫 토큰 = 단위인 행 있음] 중 '행'과 다른 것((a)) / n_o_measured·red 행 있는 표본 수와 칸 != 기대 줄기 수
#   absent·b26_marked  엔진 최상위 이름에 없는 표본 / 근거 칸에 B26MARK가 있는 표본((c))
#   a6x         '행' × · '규칙' A-6 표본마다 bad(멈춤)·info(D0a 병합 뒤 plan으로 재확인) 목록((b)):
#               레지스트리 행 있음·엔진 안 참조자(자기 def 밖 Name·Attribute·import -- 문자열 참조(getattr·__all__)는 세지 않는다 = card 근거 칸 정의.
#               D0a 병합 뒤 move_plan A-5 참조자 정의(design 30 §6.2 'A-5 소비자 따라', A-2 '문자열 주석 포함')와 같은지 한 번 대조할 것 -- review_d0b_s7 m1)·
#               기대 줄기가 MOD7이면 def 파일 = 그 줄기(계약 5)·부르는 단위의 MOD 최댓값 = 기대(design 30 §6.2 A-6, N3.10 번호 -- 아래 est):
#                 부르는 단위 = 몸체(중첩 범위 포함)의 최상위 이름(같은 파일 + 엔진 파일 import -- `from X import n [as m]`·`import X [as m]` 뒤 m.n).
#                 단위 MOD 손적용(review_d0b_s7 m2, §6.2 우선순위): A-0(--split 밖 N3.10 파일) -> A-1 토큰(식별자·글롭·`<모듈>.<이름>`·`<파일>.py`) ->
#                 A-2 레코드 클래스(참조자 최소 MOD <= 부르는 쪽이라 최댓값에 보태지 않는다 -- 자기 참조의 승격만) -> 칸 MOD(줄기·--aliases 별칭) 하나 A-4·둘 이상 A-3(가장 작은 것)
#                 + 승격(max(칸, 그 단위가 부르는 단위들), A-4는 MOD7 상한) -> --keep 파일 잔여 A-K(번호 없음) / --split·N3.10 밖 파일(배정 없음).
#                 정확히 정해지지 않는 것(A-5·A-6·A-7 단위, `〃` 칸, 토큰 여러 MOD, 지역 이름과 겹치는 최상위 이름, 순환, MP_ARGS 없음)은 하한만 쓴다:
#                 하한 최댓값 > 기대 또는 전부 정확한데 최댓값 != 기대 -> 멈춤(bad), 그 밖의 미정 -> info('D0a 병합 뒤 plan으로 재확인'). info는 통과가 아니다 --
#                 S-7 충족에는 cond_7_plan(plan mod 줄기 = 기대, D0a 도구)이 따로 필요하다
fact_path() { printf '%s' "$STATE.facts.$1.$SUM_KEY.json"; }
fact_sum() {   # <H> <캐시>
  local H=$1 C=$2 fp mpf=; fp=$(fact_path "$1")
  [ -s "$fp" ] && return 0
  if mpargs_load "$H" 2> /dev/null; then mpf=$STATE.mpargs.$H; fi   # 없으면 빈 값 -- A-0·A-K·별칭이 필요한 단위는 info(미정)로 남는다
  "$PY" -B - "$C" "$R" "$H" "$DRAFT_SPEC" "$PLAN" "$REG" "$A" "$B26MARK" "$mpf" > "$fp.tmp" <<'EOF' || { rm -f "$fp.tmp"; echo "      S-7 표 사실 요약(fact_sum: 초안 (d)-1 표·gate ${H:0:7} 레지스트리·계획 N3.10·엔진 AST) 실행 실패 -- 위 traceback" >&2; return 1; }
import ast, builtins, fnmatch, json, re, subprocess, sys
C, R, H, DRAFT, PLANP, REGP, A, B26MARK, MPF = sys.argv[1:10]
sys.path.insert(0, C)
import import_layering as il
import role_paths as rp
s = {}
def done():
    print(json.dumps(s, ensure_ascii=False)); sys.exit(0)
cells = rp._split_cells   # 게이트 표 칸 규약(이스케이프 `\|`는 칸 안 문자)
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
# ---- (d)-1 표와 선언 문장(초안)
t = open(DRAFT, encoding="utf-8").read().replace("\r\n", "\n")
try:
    sec = t.split("\n## oracle 종류와 출처", 1)[1].split("\n## ", 1)[0]
except IndexError:
    s["error"] = "'## oracle 종류와 출처' 절 없음"; done()
rows, hdr = [], None
for l in sec.split("\n"):
    ls = l.strip()
    if hdr is None:
        if ls.startswith("| 단위(함수 칸 첫 토큰) | 기대 목적지 |"):
            hdr = cells(ls)
            try:
                ir, iu, ib = hdr.index("행"), hdr.index("규칙"), hdr.index("근거(손적용)")
            except ValueError:
                s["error"] = "표 머리에 '행'·'규칙'·'근거(손적용)' 열 없음: %r" % hdr; done()
        continue
    if not ls.startswith("|"):
        break
    c = cells(ls)
    if set("".join(c)) <= set("-: "):
        continue
    if len(c) < len(hdr):
        s["error"] = "(d)-1 표 행 칸 수 %d < 머리 %d칸: %r" % (len(c), len(hdr), ls[:160]); done()
    rows.append({"unit": c[0].strip("`"), "exp": c[1].strip("`"), "row": c[ir], "rule": c[iu], "basis": "|".join(c[ib:])})
s["rows"] = rows
if not rows:
    s["error"] = "(d)-1 표 행 0"; done()
bad_mark = [r["unit"] for r in rows if r["row"] not in ("○", "×")]
if bad_mark:
    s["error"] = "'행' 열 값이 ○·×가 아니다: %r" % bad_mark; done()
s["n_o"] = sum(r["row"] == "○" for r in rows); s["n_x"] = len(rows) - s["n_o"]
m = re.findall(r"표본 \*\*(\d+)\*\*개 = 표 (\d+)행 전부\(행 있는 (\d+)·없는 (\d+)\)", sec)
mr = re.findall(r"행 있는 표본 (\d+)개 중 (\d+)개의 칸이 기대 줄기와 다르다", sec)
if not m or not mr:
    s["error"] = "표 아래 선언 문장(표본 수 '표본 **N**개 = 표 N행 전부(행 있는 X·없는 Y)' 또는 base red '행 있는 표본 X개 중 Y개의 칸이 기대 줄기와 다르다') 없음"; done()
if len(m) != 1 or len(mr) != 1:
    s["error"] = ("표 아래 선언 문장은 절 안에 한 번씩이어야 한다(표본 수 문장 %d번 %r, base red 문장 %d번 %r) -- "
                  "재측정은 옛 문장을 고쳐 쓴다(덧붙이면 어느 수가 선언인지 정해지지 않는다)" % (len(m), m, len(mr), mr)); done()
s["decl"] = [int(x) for x in m[0]]; s["decl_red"] = [int(x) for x in mr[0]]
# ---- gate <H> 트리: 레지스트리·계획·엔진 파일(cat-file --batch 한 번)
ls = subprocess.run(["git", "-C", R, "ls-tree", "--name-only", H, "--", A + "/"], capture_output=True, check=True).stdout.decode("utf-8").split("\n")
eng = sorted(p for p in ls if p.endswith(".py")) + ["workspaces/run_harness.py"]
paths = [REGP, PLANP] + eng
out = subprocess.run(["git", "-C", R, "cat-file", "--batch"], input="".join("%s:%s\n" % (H, p) for p in paths).encode("utf-8"),
                     capture_output=True, check=True).stdout
blob, i = {}, 0
for p in paths:
    j = out.index(b"\n", i); h = out[i:j].split()
    if h[-1] == b"missing":
        blob[p] = None; i = j + 1; continue
    n = int(h[2]); blob[p] = out[j + 1:j + 1 + n].decode("utf-8"); i = j + 1 + n + 1
if blob[REGP] is None or blob[PLANP] is None:
    s["error"] = "gate %s에 레지스트리 또는 계획서 없음" % H[:7]; done()
plan_txt = blob[PLANP].replace("\r\n", "\n")
mods = il.mod_table(plan_txt)
# 레지스트리 함수 표(머리에 '함수'·'이관 목적지'): 함수 칸 첫 백틱 토큰 -> 이관 목적지 칸들
names = {r["unit"] for r in rows}
reg, rh, short = {}, None, []
for l in blob[REGP].replace("\r\n", "\n").split("\n"):
    if not l.startswith("|"):
        rh = None; continue
    c = cells(l)
    if rh is None:
        rh = c; continue
    if set("".join(c)) <= set("-: ") or "함수" not in rh or "이관 목적지" not in rh:
        continue
    fi, di = rh.index("함수"), rh.index("이관 목적지")
    if len(c) <= max(fi, di):
        if names & set(IDENT.findall(l)):
            short.append(l[:160])                   # 표본 이름이 있는 짧은 행 -- 건너뛰면 '행 없음'으로 거짓 판정될 수 있다
        continue
    mt = re.search(r"`([^`]+)`", c[fi])
    if mt:
        reg.setdefault(mt.group(1), []).append(c[di])
if short:
    s["error"] = "레지스트리 함수 표의 칸 수가 머리보다 적은 행에 표본 이름이 있다: %r" % short; done()
# (a) '행' 열 = 레지스트리 행 유무, 행 있는 표본 수, base red(칸이 기대 줄기와 정확히 같지 않음 -- T-E가 재생성 칸 = 줄기를 단언하므로
#     'gmid_sizing_engine.py'처럼 .py가 붙은 칸도 red다. card 선언 23/24와 같은 정의, review_d0b_te ③)
s["row_mismatch"] = [[r["unit"], r["row"], r["unit"] in reg] for r in rows if (r["row"] == "○") != (r["unit"] in reg)]
has = [r for r in rows if r["unit"] in reg]
s["n_o_measured"] = len(has)
s["red"] = sum(any(d.strip() != r["exp"] for d in reg[r["unit"]]) for r in has)
s["multi_rows"] = [r["unit"] for r in has if len(reg[r["unit"]]) > 1]
# 엔진 최상위 이름
trees = {}
for p in eng:
    if blob[p] is not None:
        trees[p] = ast.parse(blob[p], filename=p)
top = {}
for p, tr in trees.items():
    for n in tr.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nm = [n.name]
        elif isinstance(n, ast.Assign):
            nm = [x.id for x in n.targets if isinstance(x, ast.Name)]
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            nm = [n.target.id]
        else:
            nm = []
        for x in nm:
            top.setdefault(x, []).append((p, n))
# (c) 트리에 없는 표본 / B26-1 표시 행
s["absent"] = [r["unit"] for r in rows if r["unit"] not in top]
s["b26_marked"] = [r["unit"] for r in rows if B26MARK in r["basis"].replace("**", "")]
# ---- (b) 행 없는 A-6 표본
def refs(name, skip):
    o = []
    for p, tr in trees.items():
        st = [tr]
        while st:
            n = st.pop()
            if any(n is k for k in skip):
                continue
            if (isinstance(n, ast.Name) and n.id == name) or (isinstance(n, ast.Attribute) and n.attr == name) \
                    or (isinstance(n, ast.alias) and name in (n.name.split(".")[-1], n.asname)):
                o.append("%s:%d" % (p.rsplit("/", 1)[-1], getattr(n, "lineno", 0)))
            st.extend(ast.iter_child_nodes(n))
    return sorted(o)
base = lambda p: p.rsplit("/", 1)[-1]
stem2p = {base(p)[:-3]: p for p in trees if p.startswith(A + "/")}
# MP_ARGS(design 30 §6.3, gate <H>): --split·--keep 파일, --aliases(별칭 키 -> MOD 줄기)
mp = None
if MPF:
    a = open(MPF, "rb").read().decode("utf-8").split("\0")
    def opt(k):
        v = []
        if k in a:
            for x in a[a.index(k) + 1:]:
                if x.startswith("--"):
                    break
                v.append(x)
        return v
    mp = {"split": set(opt("--split")), "keep": set(opt("--keep")),
          "aliases": {k: v[:-3] if v.endswith(".py") else v for k, v in json.loads((opt("--aliases") or ["{}"])[0]).items()}}
s["mp"] = bool(mp)
# A-1 토큰(N3.10 '대표 대상' 백틱): 식별자(글롭 *)·<모듈>.<이름> -> 이름, <파일>.py -> 그 파일 전체. 그 밖은 무시(design 30 §6.2 A-1)
th, trs = rp.read_section_table(plan_txt, "### N3.10 ")
tid = [k for k, x in enumerate(th) if x.strip() == "ID"]; tcol = [k for k, x in enumerate(th) if "대표 대상" in x]
a1_id, a1_file, a1_ok = [], {}, len(tid) == 1 and len(tcol) == 1
if a1_ok:
    for r in trs:
        mm = re.fullmatch(r"MOD([0-9]+)", r[tid[0]].strip())
        if not mm or len(r) <= tcol[0]:
            continue
        for tok in re.findall(r"`([^`]+)`", r[tcol[0]]):
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\.py", tok):
                a1_file.setdefault(tok[:-3], set()).add(int(mm.group(1)))
            elif re.fullmatch(r"[A-Za-z_*][A-Za-z0-9_*]*", tok):
                a1_id.append((tok, int(mm.group(1))))
            elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*", tok):
                a1_id.append((tok.rsplit(".", 1)[1], int(mm.group(1))))
def a1(name, stem):
    return sorted({mo for tok, mo in a1_id if fnmatch.fnmatchcase(name, tok)} | a1_file.get(stem, set()))
def file_imports(p):
    """엔진 파일 p의 이름 -> (단위, 엔진 파일) / 모듈 별칭 -> 엔진 파일(최상위와 함수 안 import 모두)."""
    fr, md = {}, {}
    for n in ast.walk(trees[p]):
        if isinstance(n, ast.ImportFrom) and n.module and n.module.split(".")[-1] in stem2p:
            for al in n.names:
                fr[al.asname or al.name] = (al.name, stem2p[n.module.split(".")[-1]])
        elif isinstance(n, ast.Import):
            for al in n.names:
                if al.name.split(".")[-1] in stem2p:
                    md[al.asname or al.name.split(".")[0]] = stem2p[al.name.split(".")[-1]]
    return fr, md
FI = {p: file_imports(p) for p in trees}
def unit_refs(node, p):
    """단위 node(파일 p)가 참조하는 최상위 단위 {(이름, 파일)} 와 지역 이름과 겹쳐 정하지 못한 이름 목록(design 30 §6.1 R(u) -- 모든 하위 범위)."""
    fr, md = FI[p]
    loc, glb = set(), set()
    for n in ast.walk(node):
        if isinstance(n, ast.Global):
            glb |= set(n.names)
        elif isinstance(n, ast.arg):
            loc.add(n.arg)
        elif isinstance(n, ast.Name) and not isinstance(n.ctx, ast.Load):
            loc.add(n.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            loc |= {al.asname or al.name.split(".")[0] for al in n.names}
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n is not node:
            loc.add(n.name)
    loc -= glb
    got, amb = set(), set()
    def hit(nm):
        if nm in fr and any(q == fr[nm][1] for q, _ in top.get(fr[nm][0], [])):
            return fr[nm]
        if any(q == p for q, _ in top.get(nm, [])):
            return (nm, p)
        return None
    for n in ast.walk(node):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            u = hit(n.id)
            if u and n.id in loc and n.id not in fr:
                amb.add(n.id)
            elif u:
                got.add(u)
        elif isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id in md:
            q = md[n.value.id]
            if any(x == q for x, _ in top.get(n.attr, [])):
                got.add((n.attr, q))
    return got, sorted(amb)
def node_of(name, p):
    l = [n for q, n in top.get(name, []) if q == p]
    return l[0] if len(l) == 1 else None
EXC = {k for k in dir(builtins) if isinstance(getattr(builtins, k), type) and issubclass(getattr(builtins, k), BaseException)}
def is_record(n, p, seen=()):
    if not isinstance(n, ast.ClassDef):
        return False
    for d in n.decorator_list:
        f = d.func if isinstance(d, ast.Call) else d
        if (isinstance(f, ast.Name) and f.id == "dataclass") or (isinstance(f, ast.Attribute) and f.attr == "dataclass"):
            return True
    if not any(isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)) for x in n.body):
        return True
    for b in n.bases:
        if isinstance(b, ast.Name) and (b.id in EXC or (b.id not in seen and is_record(node_of(b.id, p), p, seen + (b.id,)))):
            return True
    return False
def cell_mods(cl):
    st = set()
    for w in IDENT.findall(cl):
        if w in mods:
            st.add(mods[w])
        elif mp and w in mp["aliases"] and mp["aliases"][w] in mods:
            st.add(mods[mp["aliases"][w]])
    return st
memo, busy = {}, set()
def est(name, p):
    """(하한 MOD 번호 또는 None(최댓값에 보태지 않음), 정확한가, 근거). 정확하지 않으면 하한만 믿는다."""
    k = (name, p)
    if k in memo:
        return memo[k]
    if k in busy:
        return (None, False, "순환 참조")
    busy.add(k)
    r = est1(name, p)
    busy.discard(k); memo[k] = r
    return r
def promote(node, p, b, cap7, tag):
    rr, amb = unit_refs(node, p)
    sub = [(x, est(*x)) for x in sorted(rr) if x[0] != node_name(node)]
    loose = [x[0] for x, v in sub if not v[1]] + amb
    vals = [v[0] for _, v in sub if v[0] is not None]
    if loose:
        return (b, False, "%s, 승격 미정(부르는 단위 %s) -- 하한 MOD%s" % (tag, loose[:4], b))
    q = max([b] + vals) if b is not None else (max(vals) if vals else None)
    if cap7 and q == 7 and b != 7:
        q = b
    return (q, True, "%s -> MOD%s" % (tag, q) if q is not None else tag + " -> 번호 없음")
def node_name(n):
    return getattr(n, "name", None) or ([x.id for x in getattr(n, "targets", []) if isinstance(x, ast.Name)] or [getattr(getattr(n, "target", None), "id", None)])[0]
def est1(name, p):
    stem, fn = base(p)[:-3], base(p)
    if mp is None:
        return (None, False, "MP_ARGS 없음(--split·--keep·별칭 미정)")
    if fn not in mp["split"]:
        if p.startswith(A + "/") and stem in mods:
            return (mods[stem], True, "A-0 MOD%d" % mods[stem])
        return (None, True, "배정 대상 밖 파일(N3.10·--split 밖)")
    n = node_of(name, p)
    if n is None:
        return (None, False, "최상위 정의가 하나가 아님")
    if not a1_ok:
        return (None, False, "N3.10 '대표 대상' 열 없음")
    t1 = a1(name, stem)
    if len(t1) == 1:
        return (t1[0], True, "A-1 토큰 MOD%d" % t1[0])
    if len(t1) > 1:
        return (None, False, "A-1 토큰 여러 MOD %s(conflicts)" % t1)
    if is_record(n, p):   # A-2: 참조자 최소 MOD <= 부르는 쪽 -- 자기 참조의 승격만 최댓값에 닿는다(MOD7 상한은 칸 기준을 몰라 7이면 미정)
        v = promote(n, p, None, False, "A-2 레코드")
        if v[1] and v[0] == 7:
            return (None, False, "A-2 레코드 승격 MOD7(상한 판정에 참조자 MOD 필요)")
        return v
    cl = reg.get(name)
    if cl:
        if any(x.strip() == "〃" for x in cl):
            return (None, False, "칸 `〃`(위 행 -- 손적용 안 함)")
        st = {frozenset(cell_mods(x)) for x in cl}
        if len(st) != 1:
            return (None, False, "레지스트리 행 여럿의 칸 MOD가 다르다 %s" % [sorted(x) for x in st])
        ms = sorted(next(iter(st)))
        if len(ms) == 1:
            return promote(n, p, ms[0], True, "A-4 칸 MOD%d" % ms[0])
        if len(ms) > 1:
            return promote(n, p, ms[0], False, "A-3 칸 MOD%s -> 가장 작은 %d" % (ms, ms[0]))
    if fn in mp["keep"]:
        return (None, True, "A-K --keep 파일 잔여(N3.10 번호 없음)")
    return (None, False, "칸에 MOD 줄기 없음·행 없음(A-5·A-6·A-7 -- 손적용 안 함)")
a6x = []
for r in rows:
    if r["row"] != "×" or r["rule"] != "A-6":
        continue
    u, e, b, info, x = r["unit"], r["exp"], [], [], {"unit": r["unit"], "exp": r["exp"]}
    if u in reg:
        b.append("레지스트리 행 있음(칸 %r)" % reg[u])
    defs = [(p, n) for p, n in top.get(u, []) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    if len(defs) != 1:
        b.append("엔진 최상위 정의 %d개" % len(defs)); x["bad"] = b; x["info"] = info; a6x.append(x); continue
    p, d = defs[0]
    x["def"] = "%s:%d" % (base(p), d.lineno)
    rr = refs(u, [d])
    x["referrers"] = rr
    if rr:
        b.append("엔진 안 참조자 %s" % rr)
    en = mods.get(e)
    if en is None:
        b.append("기대 줄기 %s가 N3.10 파일 줄기가 아니다" % e)
    elif en == 7 and base(p)[:-3] != e:
        b.append("기대 MOD7인데 def 파일 %s != %s(계약 5 -- MOD7은 자기 파일 단위만)" % (p, e))
    got, amb = unit_refs(d, p)
    callees = sorted(c for c in got if c[0] != u)
    x["callees"] = {}
    for cn, cp in callees:
        v = est(cn, cp)
        x["callees"][cn if cp == p else "%s(%s)" % (cn, base(cp))] = v[2]
    for nm in amb:
        x["callees"][nm] = "지역 이름과 겹침(정하지 못함)"
    if not callees and not amb:
        b.append("부르는 최상위 단위 0")
    elif en is not None:
        vs = [est(*c) for c in callees]
        lo = [v[0] for v in vs if v[0] is not None]
        exact = all(v[1] for v in vs) and not amb
        mx = max(lo) if lo else None
        x["max"] = mx
        if mx is not None and mx > en:
            b.append("부르는 단위 MOD 하한 최댓값 MOD%d > 기대 %s(MOD%d): %s" % (mx, e, en, x["callees"]))
        elif exact and mx != en:
            b.append("부르는 단위 MOD 최댓값 %s != 기대 %s(MOD%d): %s" % ("MOD%d" % mx if mx is not None else "없음(번호 있는 단위 0 -- A-6 아님)", e, en, x["callees"]))
        elif not exact:
            info.append("부르는 단위 MOD를 손적용으로 다 정하지 못했다(하한 최댓값 %s <= 기대 MOD%d): %s" % ("MOD%d" % mx if mx is not None else "없음", en, x["callees"]))
    x["bad"] = b; x["info"] = info
    a6x.append(x)
s["a6x"] = a6x
done()
EOF
  mv "$fp.tmp" "$fp"
}
fget() {   # <H> <파이썬 식(s = 표 사실 요약)>
  "$PY" -B -c "import json,sys;s=json.load(open(sys.argv[1],encoding='utf-8'));print($2)" "$(fact_path "$1")"
}
plan_sum() {   # <H> <캐시>
  local H=$1 C=$2 out="$STATE.plan.$1.json" sp ff; sp=$(sum_path "$1")
  [ -s "$sp" ] && ! grep -q '"facts_missing": true' "$sp" && return 0   # 표 사실 없이 만든 요약은 캐시로 다시 쓰지 않는다(다음 실행에서 다시 잰다)
  g show "$H:$PLAN" > "$out.plan.md"
  # (d)-1 표 파싱은 fact_sum 하나가 한다(단일 출처). 실패해도 S-4·S-5는 plan 출력만으로 판정한다 -- S-7만 규약오류(review_d0b_s7 m3)
  if fact_sum "$H" "$C"; then ff=$(fact_path "$H"); else
    ff=; echo "      (S-4·S-5) S-7 표 사실 요약(fact_sum)이 실패했다 -- plan 요약은 (d)-1 표본 대조 없이 만든다(S-4·S-5는 그대로 판정, S-7은 규약오류 -- 원인은 S-7 줄)" >&2
  fi
  "$PY" -B - "$C" "$out" "$(cat "$out.rc")" "$out.plan.md" "$ff" "$RULE_IDS" "$SIX" "$D11NAME" > "$sp.tmp" <<'EOF' || { rm -f "$sp.tmp"; echo "      plan 요약(plan_sum) Python 실패 -- 위 traceback(S-4·S-5·S-7 판정 불가)" >&2; return 1; }
import json, re, sys
C, OUT, RC, PLANF, FACTS, RULES, SIX, D11NAME = sys.argv[1:9]
sys.path.insert(0, C)
import import_layering as il
lines = open(OUT, encoding="utf-8").read().splitlines()
s = {"exit": int(RC)}
try:
    o = json.loads(lines[0])
except (IndexError, ValueError) as e:   # 첫 줄이 없거나 JSON이 아니면 규약 위반(cond_4가 1로)
    s["json_error"] = "%s: %s" % (type(e).__name__, str(e)[:200]); print(json.dumps(s, ensure_ascii=False)); sys.exit(0)
s["tool"] = o.get("tool"); s["verdict"] = o.get("verdict"); s["error"] = o.get("error")
s["missing_keys"] = [k for k in ("assignment", "reg_mismatch", "mod_imports") + tuple(SIX.split()) if k not in o]
a = o.get("assignment") or {}
s["assigned"] = len(a)
s["lists"] = {k: len(o.get(k) or []) for k in tuple(SIX.split()) + ("reg_mismatch",)}
s["heads"] = {k: (o.get(k) or [])[:3] for k in SIX.split() if o.get(k)}
rules = {}
for v in a.values():
    rules[v.get("rule")] = rules.get(v.get("rule"), 0) + 1
s["rules"] = rules
s["bad_rules"] = sorted(str(r) for r in rules if r not in RULES.split())
mt = il.mod_table(open(PLANF, encoding="utf-8").read())
m7 = [f for f, n in mt.items() if n == 7]
s["mod7"] = m7
s["mod7_outside"] = sorted(k for k, v in a.items() if m7 and v.get("mod") == m7[0] + ".py" and k.split("::")[0] != m7[0] + ".py")
# oracle (d)-1 표(S-7): 단위 -> 기대 줄기. 도구 mod 줄기와 대조만(기대값은 card 표가 정본). 표 파싱은 fact_sum 요약의 rows(단일 출처)
rows = [(r["unit"], r["exp"], r["row"]) for r in json.load(open(FACTS, encoding="utf-8")).get("rows", [])] if FACTS else []
if not FACTS:
    s["facts_missing"] = True
s["samples"] = len(rows)
by = {}
for k, v in a.items():
    by.setdefault(k.split("::", 1)[1], set()).add(v.get("mod", "")[:-3] if v.get("mod", "").endswith(".py") else v.get("mod"))
s["sample_missing"] = [u for u, e, _ in rows if u not in by]
s["sample_mismatch"] = [[u, e, sorted(by[u])] for u, e, _ in rows if u in by and by[u] != {e}]
# [D-11] 단위의 근거 규칙(S-7, review_ud6 m4): 그 이름으로 배정된 단위 전부의 rule 집합
s["d11_rules"] = sorted({str(v.get("rule")) for k, v in a.items() if k.split("::", 1)[-1] == D11NAME})
print(json.dumps(s, ensure_ascii=False))
EOF
  mv "$sp.tmp" "$sp"
}
sum_get() {   # <H> <파이썬 식(s = 요약)>
  "$PY" -B -c "import json,sys;s=json.load(open(sys.argv[1],encoding='utf-8'));print($2)" "$(sum_path "$1")"
}

# ---------------------------------------------------------------- 착수 조건 S-1~S-7(+ measured). 0 충족 / 3 미충족 / 1 규약 불일치. '||' 문맥 -- 실패마다 명시적 return(review S2)
COND_TITLE_1="S-1 Phase 3 design 승인 기록 $AID + design 30 문서 + [D-11] 승인 기록 $D11ID·N3.10 MOD1 토큰이 gate에 있다"
cond_1() {
  local H=$1 C=$2 r=0
  approval_rc "$H" "$C" "$AID" || r=$?
  [ "$r" = 0 ] || return 3
  g cat-file -e "$H:$D30" 2>/dev/null || { echo "      design 30 문서 $D30 없음" >&2; return 3; }
  approval_rc "$H" "$C" "$D11ID" || r=$?            # UD-6 [D-11] (가) -- 승인 기록 + 계획 N3.10 MOD1 토큰
  [ "$r" = 0 ] || return 3
  [ "$(g show "$H:$PLAN" | grep -c -F "| MOD1 | \`gmid_lut.py\`")" = 1 ] && g show "$H:$PLAN" | grep -F "| MOD1 | \`gmid_lut.py\`" | grep -q -F "$D11TOK" \
    || { echo "      계획 N3.10 MOD1 행에 [D-11] 토큰 \`_QUERY_CACHE_MAX\` 없음(UD-6 문서 커밋 전)" >&2; return 3; }
  return 0
}
COND_TITLE_2="S-2 선행 card 병합(B34·b26pre·backfill·B26-1·B33·G1·FU·D0a 판정 기록 V1~V10 PASS·N/A -- lc_pred_ok) + FU 두 줄"
cond_2() {
  local H=$1 id f bad=0
  for id in $PREDS; do lc_pred_ok "$R" "$H" "$id" || bad=1; done
  for f in $FU_FILES; do
    g show "$H:$f" 2>/dev/null | grep -q '^from __future__ import annotations' || { echo "      FU: $f에 'from __future__ import annotations' 없음" >&2; bad=1; }
  done
  [ "$bad" = 0 ] || return 3
  return 0
}
COND_TITLE_3="S-3 Phase 2 DoD PASS(phase2-dod.md '## 판정' 다음 첫 줄 '판정: PASS')"
cond_3() {
  local H=$1 r
  g cat-file -e "$H:$DOD" 2>/dev/null || { echo "      $DOD 없음" >&2; return 3; }
  r=$(g show "$H:$DOD" | "$PY" -B -c "
import sys
L=sys.stdin.buffer.read().decode('utf-8').replace('\r\n','\n').split('\n')
v=[i for i,l in enumerate(L) if l in ('판정: PASS','판정: FAIL')]
h=[i for i,l in enumerate(L) if l=='## 판정']
ok=len(v)==1 and len(h)==1 and L[v[0]]=='판정: PASS' and all(not x.strip() for x in L[h[0]+1:v[0]]) and v[0]>h[0]
print(0 if ok else 3)") || return 1
  return "$r"
}
# S-4·S-5·S-7은 plan 하나를 같이 쓴다(판마다 캐시)
plan_ready() {   # <H> <캐시> -> 0 / 3 / 1
  local H=$1 C=$2 r=0
  [ "${PLAN_READY_H:-}" = "$H" ] && return "$PLAN_READY_RC"
  plan_at "$H" || r=$?
  if [ "$r" = 0 ]; then plan_sum "$H" "$C" || r=1; fi
  PLAN_READY_H=$H; PLAN_READY_RC=$r
  return "$r"
}
COND_TITLE_4="S-4 gate 트리의 D0a 도구가 v8.4 계약 2 모양(첫 줄 JSON tool=move_plan, exit≠2, import_conflicts·mod_imports 키, 규칙 ID ⊆ {$RULE_IDS})"
cond_4() {
  local H=$1 C=$2 r=0
  plan_ready "$H" "$C" || r=$?
  [ "$r" = 0 ] || return "$r"
  [ "$(sum_get "$H" "s.get('json_error') or ''")" = "" ] || { echo "      plan 첫 줄 JSON 아님: $(sum_get "$H" "s['json_error']")" >&2; plan_clear_hint "$H"; return 1; }
  [ "$(sum_get "$H" "s['tool']")" = move_plan ] || { echo "      plan tool 키 다름" >&2; return 1; }
  [ "$(sum_get "$H" "s['exit']")" != 2 ] || { echo "      plan exit 2(ERROR): $(sum_get "$H" "s['error']")" >&2; echo "      D0a 계약 2 (e5)·(e6)(레지스트리 칸 모순)이면 캐시를 지워도 같다 -- spec 계약 8 (g) 경로(그 단위를 N3.10 토큰으로, D-11)·d0b_briefs 0.4. (e1)·(e4)·인자 모양이면 원인 보고 후 멈춤" >&2; plan_clear_hint "$H"; return 1; }
  [ "$(sum_get "$H" "' '.join(s['missing_keys'])")" = "" ] || { echo "      plan 출력에 없는 키: $(sum_get "$H" "' '.join(s['missing_keys'])") -- D0a가 v8.4 계약 2(import_conflicts·mod_imports)로 병합되지 않았다(S-4)" >&2; return 3; }
  [ "$(sum_get "$H" "' '.join(s['bad_rules'])")" = "" ] || { echo "      규칙 ID 집합 밖: $(sum_get "$H" "' '.join(s['bad_rules'])") -- 집합이 바뀌었으면 D0a 후속 card가 spec 계약 6 (c)를 함께 고친다" >&2; return 3; }
  echo "      배정 $(sum_get "$H" "s['assigned']"), 규칙 $(sum_get "$H" "s['rules']")" >&2
  return 0
}
COND_TITLE_5="S-5 plan(D0b base): reg_mismatch 밖 여섯 빈 목록 + MOD7 파일 밖 MOD7 배정 0 + reg_mismatch 비지 않음(T-A red) + exit 1"
cond_5() {
  local H=$1 C=$2 r=0 k n bad=0 rm ex
  plan_ready "$H" "$C" || r=$?
  [ "$r" = 0 ] || return "$r"
  [ "$(sum_get "$H" "' '.join(s['missing_keys'])")" = "" ] || { echo "      plan 출력 키 결함(S-4) -- 여섯 목록 판정 불가" >&2; return 3; }
  for k in $SIX; do
    n=$(sum_get "$H" "s['lists']['$k']")
    [ "$n" = 0 ] || { echo "      $k $n개 (앞 3: $(sum_get "$H" "s['heads'].get('$k')"))" >&2; bad=1; }
  done
  n=$(sum_get "$H" "len(s['mod7_outside'])")
  [ "$n" = 0 ] || { echo "      MOD7($(sum_get "$H" "s['mod7']")) 파일 밖 MOD7 배정 $n개: $(sum_get "$H" "s['mod7_outside'][:5]")" >&2; bad=1; }
  if [ "$bad" = 1 ]; then
    echo "      -> 멈춤 절차(d0b_briefs 0.4, spec 계약 8): conflicts·A-1 원천 upward/cycles -> N3.10 토큰 개정(D-11 별도 승인), unassigned·A-1 밖 upward -> design §6.2 규칙 개정(D0a 후속 card)," >&2
    echo "         import_time_high -> 배정 변경(N3.10), import_conflicts -> __future__면 FU 병합 확인 / 이름 출처면 배정 변경, MOD7 밖 -> N3.10. 출력 사본: $STATE.plan.$H.json" >&2
    return 3
  fi
  rm=$(sum_get "$H" "s['lists']['reg_mismatch']"); ex=$(sum_get "$H" "s['exit']")
  [ "$rm" -gt 0 ] || { echo "      reg_mismatch 0 -- base에 T-A red가 없다(열이 이미 재생성됐나?): red-green card가 성립하지 않는다" >&2; return 3; }
  [ "$ex" = 1 ] || { echo "      reg_mismatch $rm인데 plan exit $ex(1이어야 한다)" >&2; return 1; }
  echo "      여섯 목록 0, MOD7 밖 0, reg_mismatch $rm(T-A red), exit 1" >&2
  return 0
}
COND_TITLE_6="S-6 역할 브랜치 role/* 0개, $ID worktree 없음, 새 test 경로 없음(동결 대상 대기열 정리는 after-push 출력)"
cond_6() {
  local H=$1 bad=0
  [ -z "$(g for-each-ref refs/heads/role/)" ] || { echo "      역할 브랜치: $(g for-each-ref --format='%(refname:short)' refs/heads/role/ | tr '\n' ' ')" >&2; bad=1; }
  if g worktree list --porcelain | grep -q -- "/$ID-"; then echo "      $ID worktree가 이미 있다" >&2; bad=1; fi
  if g cat-file -e "$H:$NEWT" 2>/dev/null; then echo "      $NEWT가 이미 있다" >&2; bad=1; fi
  [ "$bad" = 0 ] || return 3
  return 0
}
COND_TITLE_7="S-7 oracle (d)-1 표: 표본 수 = 표 행 수 = card 선언(D0b base = B26-1 병합 판, 표 전부 트리에 있음) + '행' 열 = base 레지스트리 행 유무(행 있는 수·base red = card 선언) + 행 없는 A-6 표본 근거(행 없음·엔진 안 참조자 0·부르는 단위 = 기대 줄기) + 표본 전부 plan mod 줄기 = 기대 + $D11NAME 배정 규칙 = $D11RULE([D-11] 승인 재검토). 어긋나면 test-author 전에 표를 고친 spec card"
# 표 사실 쪽(plan 없이 -- D0a 전에도 돈다). 0 / 3 / 1(초안 표·선언 문장 모양)
fact_fail() { echo "      S-7 표 사실 요약 $(fact_path "$1") 읽기 실패 -- 위 traceback(review_d0b_s7 m4: 빈 값으로 진행하지 않는다)" >&2; }
cond_7_facts() {   # '||' 문맥(set -e 꺼짐) -- fget 실패마다 명시적 return 1(review_d0b_s7 m4)
  local H=$1 C=$2 bad=0 e v n no nx dn dm dno dnx rm mo red dro dred ab mk nmk a6 a6i
  fact_sum "$H" "$C" || return 1
  e=$(fget "$H" "s.get('error') or ''") || { fact_fail "$H"; return 1; }
  [ -z "$e" ] || { echo "      (d)-1 표·선언 문장을 초안에서 읽지 못했다: $e" >&2; return 1; }
  v=$(fget "$H" "' '.join(map(str, [len(s['rows']), s['n_o'], s['n_x']] + s['decl']))") || { fact_fail "$H"; return 1; }
  read -r n no nx dn dm dno dnx <<< "$v"
  # (c) 표본 수: 표 행 수(정본)와 card 선언 문장이 같은지 -- 수를 이 스크립트에 적지 않는다
  if [ "$n" != "$dn" ] || [ "$n" != "$dm" ] || [ "$no" != "$dno" ] || [ "$nx" != "$dnx" ]; then
    echo "      card 선언 '표본 **$dn**개 = 표 ${dm}행 전부(행 있는 ${dno}·없는 ${dnx})' != 표 실제 ${n}행(○ ${no}·× ${nx}) -- 초안 표와 선언 문장을 맞춘다" >&2; return 1
  fi
  # (a) '행' 열 = gate 레지스트리 함수 칸 첫 토큰 행 유무 + 행 있는 수·base red = 선언
  rm=$(fget "$H" "s['row_mismatch']") || { fact_fail "$H"; return 1; }
  v=$(fget "$H" "' '.join(map(str, [s['n_o_measured'], s['red']] + s['decl_red']))") || { fact_fail "$H"; return 1; }
  read -r mo red dro dred <<< "$v"
  if [ "$rm" != "[]" ] || [ "$mo" != "$dro" ] || [ "$red" != "$dred" ]; then
    echo "      '행' 열 대 gate ${H:0:7} 레지스트리 어긋남 [단위, 표 '행', 레지스트리 행 있음] $rm; 행 있는 수 표 ○ ${no}·선언 $dro -> 측정 $mo, base red 선언 $dred -> 측정 $red/$mo" >&2
    echo "      -> 멈춤: spec card (d)-1 표의 '행' 열·행 있는 수·base red 크기(표 아래 선언 문장 둘 포함)를 고친 spec card 커밋이 test-author 착수 전에 먼저다(B26-1이 행을 더했으면 × -> ○ -- T-E가 그 행 칸도 단언한다, review_d0b_te S-1)" >&2
    bad=1
  else
    echo "      (a) '행' 열 = gate ${H:0:7} 레지스트리 행 유무(○ ${no} 모두 행 있음·× ${nx} 모두 없음), base red ${red}/${mo} = 선언" >&2
  fi
  v=$(fget "$H" "s['multi_rows'] or ''") || { fact_fail "$H"; return 1; }
  [ -z "$v" ] || echo "      (정보) 함수 칸 첫 토큰이 같은 레지스트리 행이 여럿인 표본: $v" >&2
  # (c) D0b base = B26-1 병합 판: 표 전부가 트리에 있다. 그 전에는 없는 표본 = 표의 B26-1 표시 행이어야 한다(관찰 수 + B26-1 수 = 표 행 수)
  ab=$(fget "$H" "' '.join(s['absent'])") || { fact_fail "$H"; return 1; }
  mk=$(fget "$H" "' '.join(s['b26_marked'])") || { fact_fail "$H"; return 1; }
  nmk=$(fget "$H" "len(s['b26_marked'])") || { fact_fail "$H"; return 1; }
  if lc_pred_ok "$R" "$H" "$B26ID" 2> /dev/null; then
    if [ -z "$ab" ]; then echo "      (c) B26-1 병합 판: 표본 ${n}개(표 행 수 = card 선언) 전부 gate 트리에 있다" >&2
    else echo "      B26-1 병합 판인데 표본 ${n}개 중 gate 트리에 없는 것: $ab -- 표본 수명 위반(지우거나 옮긴 card가 표를 고친다)이거나 표를 고친 spec card가 먼저" >&2; bad=1; fi
  elif [ "$ab" = "$mk" ]; then
    echo "      D0b base 전(B26-1 $B26ID 판정 기록 없음 -- S-2): 표본 ${n}개 = gate 관찰 $((n - nmk))개 + B26-1 표본 ${nmk}개($mk) -- B26-1 병합 뒤 다시 잰다" >&2; bad=1
  else
    echo "      B26-1 미병합 판에서 트리에 없는 표본 [$ab] != 표의 B26-1 표시 행 [$mk]('$B26MARK')" >&2; bad=1
  fi
  # (b) 행 없는 A-6 표본(표에서 '행' ×·'규칙' A-6인 행). bad = 멈춤, info = 규칙 손적용으로 다 못 정함 -> D0a 병합 뒤 plan으로 재확인(통과 아님 -- cond_7_plan이 정본 대조)
  a6=$(fget "$H" "'; '.join('%s: %s' % (x['unit'], ', '.join(x['bad'])) for x in s['a6x'] if x['bad'])") || { fact_fail "$H"; return 1; }
  a6i=$(fget "$H" "'; '.join('%s: %s' % (x['unit'], ', '.join(x['info'])) for x in s['a6x'] if x['info'] and not x['bad'])") || { fact_fail "$H"; return 1; }
  if [ -n "$a6" ]; then
    echo "      행 없는 A-6 표본이 base에서 근거와 다르다 -- $a6" >&2
    echo "      -> 멈춤: 그 표본 행(기대·'행'·'규칙'·근거)을 고친 spec card 커밋이 test-author 착수 전에 먼저다(d0b_briefs S-7 (te))" >&2
    bad=1
  else
    v=$(fget "$H" "'; '.join('%s(def %s, 레지스트리 행 없음, 엔진 안 참조자 0, 부르는 단위 MOD 최댓값 MOD%s = 기대 %s: %s)' % (x['unit'], x['def'], x['max'], x['exp'], x['callees']) for x in s['a6x'] if not x['info']) or '없음(표에 × A-6 행 0 또는 모두 아래 정보)'") || { fact_fail "$H"; return 1; }
    echo "      (b) 행 없는 A-6 표본: $v" >&2
  fi
  [ -z "$a6i" ] || echo "      (정보) 행 없는 A-6 표본 -- D0a 병합 뒤 plan으로 재확인(S-7 plan 쪽 표본 mod 줄기 대조가 판정한다): $a6i" >&2
  [ "$bad" = 0 ] || return 3
  return 0
}
cond_7() {
  local H=$1 C=$2 rf=0 rp=0
  cond_7_facts "$H" "$C" || rf=$?
  [ "$rf" != 1 ] || return 1
  cond_7_plan "$H" "$C" || rp=$?
  [ "$rp" != 1 ] || return 1
  [ "$rf" = 0 ] && [ "$rp" = 0 ] && return 0
  return 3
}
# plan 쪽: 표본 mod 줄기·[D-11] 규칙
cond_7_plan() {
  local H=$1 C=$2 r=0 ns mi mm dr
  plan_ready "$H" "$C" || r=$?
  [ "$r" = 0 ] || { echo "      plan 쪽(표본 mod 줄기·$D11NAME 규칙)은 plan이 없어 판정하지 않았다 -- S-4 줄 참조" >&2; return "$r"; }
  ns=$(sum_get "$H" "s['samples']") || { echo "      plan 요약 $(sum_path "$H") 읽기 실패 -- 위 traceback" >&2; return 1; }
  [ "$ns" -gt 0 ] || { echo "      (d)-1 표를 초안에서 읽지 못했다" >&2; return 1; }
  mi=$(sum_get "$H" "s['sample_missing']") || { echo "      plan 요약 읽기 실패 -- 위 traceback" >&2; return 1; }
  mm=$(sum_get "$H" "s['sample_mismatch']") || { echo "      plan 요약 읽기 실패 -- 위 traceback" >&2; return 1; }
  [ "$mi" = "[]" ] && [ "$mm" = "[]" ] || { echo "      표본 $ns개 중 plan에 없음 $mi, 기대와 다름 [단위, 기대, plan] $mm" >&2; return 3; }
  dr=$(sum_get "$H" "' '.join(s['d11_rules']) if 'd11_rules' in s else '?'") || { echo "      plan 요약 읽기 실패 -- 위 traceback" >&2; return 1; }
  [ "$dr" != "?" ] || { echo "      plan 요약 캐시에 d11_rules가 없다(옛 판 캐시) -- $(sum_path "$H")를 지우고 다시" >&2; return 1; }
  [ "$dr" = "$D11RULE" ] || { echo "      $D11NAME 배정 규칙 [${dr:-없음}] -- $D11RULE 하나여야 한다(승인 20261002-p3-d11-query-cache-max '재검토': 깨지면 멈추고 다시 묻는다)" >&2; return 3; }
  echo "      표본 $ns개 모두 plan mod 줄기 = 기대, $D11NAME 규칙 $D11RULE" >&2
  return 0
}
COND_TITLE_8="measured rev(초안 '**measured at \`<rev>\`**' 마지막 출현)가 D0a 병합 뒤이고 그 뒤 plan 입력·새 test 경로 변경 0"
cond_8() {
  local H=$1 n M ch
  n=$(grep -c -- "$MEAS_PAT" "$DRAFT_SPEC" || true)
  [ "${n:-0}" -gt 0 ] || { echo "      초안에 measured 앵커가 없다 -- D0b base에서 착수 0단계(d0b_briefs 0절)를 재고 '작성 전 실측' 사실 문장을 고친 뒤 '**measured at \`<rev>\`**'를 더한다" >&2; return 3; }
  M=$(meas_rev) || return 1
  g merge-base --is-ancestor "$M" "$H" || { echo "      measured ${M:0:7}가 gate ${H:0:7}의 조상이 아니다" >&2; return 1; }
  lc_pred_ok "$R" "$M" "$D0AID" || { echo "      measured ${M:0:7}가 D0a 병합 앞이다 -- D0b 이관표는 D0b 자신의 base에서 처음 계산한다(design §6.4)" >&2; return 3; }
  ch=$(g diff --name-only "$M" "$H" -- "${MEAS_PATHS[@]}" | wc -l | tr -d ' ')
  [ "$ch" = 0 ] || { echo "      measured ${M:0:7} -> gate ${H:0:7}: plan 입력 $ch파일 변경 -- 다시 잰다" >&2; g diff --name-only "$M" "$H" -- "${MEAS_PATHS[@]}" | sed 's/^/        /' >&2; return 3; }
  echo "      measured ${M:0:7} -> gate ${H:0:7}: plan 입력 변경 0, D0a 판정 기록 있음" >&2
  return 0
}
draft_ok() {
  test -s "$DRAFT_SPEC" || { echo "[중단] 초안 $DRAFT_SPEC 없음" >&2; return 1; }
  [ "$(draft_id)" = "$ID" ] || { echo "[중단] 초안 머리 id $(draft_id) != $ID" >&2; return 1; }
  [ "$(draft_approvals)" = "$APPR_IDS" ] || { echo "[중단] 초안 approval 줄 '$(draft_approvals)' != '$APPR_IDS' (멈춤 절차로 승인이 늘었으면 APPR_IDS도 함께)" >&2; return 1; }
}
conds_eval() {
  local H=$1 C=$2 n r out=""
  CRC=0; PLAN_READY_H=
  draft_ok || { CRC=1; return 0; }
  for n in $(seq 1 "$NCOND"); do
    r=0; "cond_$n" "$H" "$C" || r=$?
    eval "RC$n=$r"; out="$out $n:$r"
    printf '   [%s] %-6s %s\n' "$n" "$( [ "$r" = 0 ] && echo 충족 || { [ "$r" = 3 ] && echo 미충족 || echo 규약오류; } )" "$(eval echo "\$COND_TITLE_$n")"
    if [ "$r" = 1 ]; then CRC=1; elif [ "$r" != 0 ] && [ "$CRC" = 0 ]; then CRC=3; fi
  done
  echo "   착수 조건(gate master ${H:0:7}) exit:$out -> $CRC"
}
# interface card: 두 표 모두 빈 표(d0b_briefs 0.1 -- V4는 --module-dir tools/migrate --subject move_plan:main 우회 전제)
ifc_check() {
  "$PY" -B -c "
import sys
t=open(sys.argv[1],encoding='utf-8').read().replace('\r\n','\n')
sec={}; cur=None
for l in t.split('\n'):
    if l.startswith('## '): cur=l[3:].strip(); sec[cur]=[]
    elif cur and l.startswith('| \`'): sec[cur].append(l)
assert '관찰 가능한 계약' in sec and '신규 시그니처' in sec, list(sec)
assert not sec['관찰 가능한 계약'], ('기존 함수 행 -- 초안 계약 절의 백틱 엔진 이름(작성 전 실측 15)', sec['관찰 가능한 계약'])
assert not sec['신규 시그니처'], ('신규 시그니처 행', sec['신규 시그니처'])
print('   interface card: 기존 함수 0개, 신규 0행')" "$1"
}
# 진행 중(판정 기록 없는) spec card 목록 -- S-6 동결 대상 대기열 확인용(정보)
inflight_cards() {   # <H>
  local H=$1 f id
  for f in $(g ls-tree --name-only "$H" -- docs/02-design/specs/ | grep '\.spec\.md$'); do
    id=$(basename "$f" .spec.md)
    case "$id" in _*) continue ;; esac                                 # _TEMPLATE
    g cat-file -e "$H:.ai/verification/$id.json" 2>/dev/null || printf '%s\n' "$id"
  done
}

stage_conds() {
  say "conds: 착수 조건 S-1~S-7 + measured(읽기 전용 -- fetch 안 함, 지금 로컬 gate/master 기준)"
  local H C; H=$(g rev-parse gate/master); C=$(cache_dir)
  conds_eval "$H" "$C"
  echo "   진행 중 spec card(판정 기록 없음 -- 엔진·tools/gates·tools/migrate·레지스트리 열을 바꾸는 Phase 3 밖 card는 F2 뒤로, S-6): $(inflight_cards "$H" | grep -v -x "$ID" | tr '\n' ' ')"
  [ "$CRC" = 0 ] || echo "   (exit $CRC)"
  trap - ERR                                                          # 3·1은 판정 결과다 -- ERR 표지를 찍지 않는다
  exit "$CRC"
}

stage_pre() {
  say "pre: 착수 전 확인(저장소 변경 없음)"
  test -n "$(git config --get user.email)"
  g fetch gate
  test "$(g rev-parse --abbrev-ref HEAD)" = master
  test "$(g rev-parse HEAD)" = "$(g rev-parse gate/master)"
  g diff --cached --quiet
  test -z "$(g status --porcelain -- docs/02-design/specs/ .ai/approvals/)"
  test ! -e "$R/$F_SPEC"; test ! -e "$R/$F_IFC"
  local H C P M; H=$(g rev-parse gate/master); C=$(cache_dir)
  # 상태 파일은 지우되 이 판의 plan 캐시는 남긴다(같은 판 -- 다시 돌리지 않는다). 요약 캐시는 초안·스크립트 sha256이 키라 표를 고친 초안이나 상수를 고친 스크립트면 다시 계산된다(D0b-S1·r1-m1)
  rm -f "$STATE" "$STATE.ids.base" "$STATE.ids.head"
  conds_eval "$H" "$C"
  [ "$CRC" = 0 ] || { echo "[중단] 착수 조건 미충족(exit $CRC) -- 위 표" >&2; return 1; }
  "$PY" -B "$C/interface_card.py" "$DRAFT_SPEC" --root "$R" --out "$STATE.ifc.pre.md" > /dev/null
  ifc_check "$STATE.ifc.pre.md"
  M=$(meas_rev); P=$(plan_hash "$C"); test ${#P} = 64
  st_set MEAS "$M"; st_set GATE_BASE "$H"; st_set PLAN_HASH "$P"; st_set CACHE "$C"; st_set PLAN_BASE "$STATE.plan.$H.json"
  approved_ids "$C" "$H" > "$STATE.ids.base"
  say "pre OK: gate master ${H:0:7}, measured ${M:0:7}, plan base 출력 $STATE.plan.$H.json(reg_mismatch $(sum_get "$H" "s['lists']['reg_mismatch']") -- auditor 3.1이 다시 잰다), plan_tables_hash ${P:0:16}…"
}

stage_card() {
  say "card (S): spec card + interface card(게이트 캐시 interface_card.py, 절대 경로) -- Role: doc"
  local H; H=$(g rev-parse gate/master)
  test "$(g rev-parse HEAD)" = "$(st_get GATE_BASE)"
  test "$H" = "$(st_get GATE_BASE)"
  g diff --cached --quiet
  local C; C=$(cache_dir); test "$C" = "$(st_get CACHE)"
  conds_eval "$H" "$C"                                                # 같은 판이라 plan은 캐시
  [ "$CRC" = 0 ] || { echo "[중단] 착수 조건 미충족(exit $CRC)" >&2; return 1; }
  test ! -e "$R/$F_SPEC"; test ! -e "$R/$F_IFC"
  cp "$DRAFT_SPEC" "$R/$F_SPEC"
  "$PY" -B -c "
import sys, os
sys.path.insert(0, sys.argv[1])
import role_paths as rp, merge_gate as mg
c = rp.parse_spec_card(open(sys.argv[2], encoding='utf-8').read(), sys.argv[3])
exp = ('3', 'red-green', 'no', sys.argv[5].split(), [], int(sys.argv[6]))
got = (c['phase'], c['evidence_type'], c['gate_change'], c['approval'], c['activated_ic_case'], len(c['sections']))
assert got == exp, (got, exp)
po = mg.read_plan_tables(sys.argv[4]).phase_order
assert c['phase'] in po, po
for a in c['approval']:
    assert os.path.isfile(os.path.join(sys.argv[7], '.ai', 'approvals', a + '.md')), a
print('   parse_spec_card OK', got)
" "$C" "$R/$F_SPEC" "$ID" "$R/$PLAN" "$APPR_IDS" "$NSEC" "$R"
  "$PY" -B "$C/interface_card.py" "$R/$F_SPEC" --root "$R" --out "$R/$F_IFC"
  test -s "$R/$F_IFC"
  ifc_check "$R/$F_IFC"
  g add -- "$F_SPEC" "$F_IFC"
  staged_is "$F_SPEC" "$F_IFC"
  test "$(g diff --cached --numstat -- "$F_SPEC" | cut -f2)" = 0
  g commit -q -m "$SUBJ_S" --trailer "Role: doc" --trailer "Change-Id: $ID" --trailer "$COAUTH"
  head_subj_is "$SUBJ_S"
  st_set S "$(g rev-parse HEAD)"
  say "card OK: $(g rev-parse --short HEAD) (interface $(wc -l < "$R/$F_IFC" | tr -d ' ')줄)"
}

stage_final() {
  say "final: push 전 종합 확인"
  test "$(g rev-parse HEAD)" = "$(st_get S)"
  local base C; base=$(st_get GATE_BASE); C=$(cache_dir)
  test "$(g rev-parse gate/master)" = "$base"
  test "$C" = "$(st_get CACHE)"
  test "$(g rev-list --count "$base..HEAD")" = 1
  test "$(g rev-parse HEAD^)" = "$base"
  test "$(g log -1 --format=%s)" = "$SUBJ_S"
  test "$(g diff-tree --no-commit-id --name-only -r HEAD | sort | tr '\n' ' ')" = "$(printf '%s\n' "$F_SPEC" "$F_IFC" | sort | tr '\n' ' ')"
  trailer_is HEAD Role doc; trailer_is HEAD Change-Id "$ID"
  g show "HEAD:$F_SPEC" | cmp - "$DRAFT_SPEC"
  approved_ids "$C" HEAD > "$STATE.ids.head"
  cmp "$STATE.ids.base" "$STATE.ids.head"
  test "$(plan_hash "$C")" = "$(st_get PLAN_HASH)"
  test -z "$(g status --porcelain -- docs/ .ai/approvals/)"
  g log --format='%h %s' "$base..HEAD"
  say "final OK -- 다음은 push 단독 호출(병렬·tail 금지):  $(lc_push_cmd "$R")   그 뒤 after-push"
}

stage_after_push() {
  say "after-push: gate master = S"
  g fetch gate
  test "$(g rev-parse gate/master)" = "$(st_get S)"
  test "$(g rev-parse HEAD)" = "$(g rev-parse gate/master)"
  local H; H=$(g rev-parse gate/master)
  test "$(g ls-tree --name-only "$H" -- "$F_SPEC" "$F_IFC" | sort | tr '\n' ' ')" = "$(printf '%s\n' "$F_SPEC" "$F_IFC" | sort | tr '\n' ' ')"
  test -z "$(g status --porcelain -- docs/ .ai/approvals/)"
  # 게이트 캐시는 gate master 하나만 둔다(ensure_cache 상한, WP-10) -- push 뒤 새 판으로 다시 받고 plan 표 불변 확인(역할 agent가 쓸 캐시)
  local C; C=$(cache_dir); test "$(plan_hash "$C")" = "$(st_get PLAN_HASH)"
  st_set CACHE "$C"
  echo "   S-6 동결 대상 대기열(test worktree 전에 정리 -- D-27은 D0b 병합에서 시작한다): 진행 중 spec card $(inflight_cards "$H" | grep -v -x "$ID" | tr '\n' ' ')"
  echo "      F2 뒤로 옮길 것: 엔진(A/*.py, workspaces/run_harness.py)·tools/gates/**·tools/migrate/**·레지스트리 '이관 목적지' 열을 바꾸는 Phase 3 밖 card(B26-2~B26-4·B35·B36·B37a 등)"
  say "after-push OK -- 다음은 test worktree(단독 호출, design 05 §12 순서 1):  git -C $R worktree add $W/$ID-test -b role/test/$ID gate/master"
  echo "   (d0b_briefs 4절: test-author 1절 -> auditor 3.1(base plan 출력 out/plan_base.json, 멈춤 조건 재확인; 산출물은 쓰기만, 커밋하지 않는다 -- 커밋은 순서 7에서 M 위 한 커밋) -> code worktree -> code-author 2절 -> 병합(전에 git -C $W/$ID-audit log --oneline role/test/$ID..HEAD 출력이 비어야 한다, 아니면 멈춤) -> auditor 3.2 -> push -> 정리 -> 'bash $0 freeze')"
}

# D0b 판정 기록이 gate에 있은 뒤: D-27 동결 공지(시작 = 판정 기록 code_commit) + M1 착수 전 확인 명령. 읽기 전용
stage_freeze() {
  say "freeze: D-27 동결 공지(D0b 병합 확인)"
  local H cc; H=$(g rev-parse gate/master)
  # 아래 두 거부는 판정 결과다 -- ERR 표지를 찍지 않고 exit 1(conds와 같다, review_d0a_d0b_ready D0b m6)
  lc_pred_ok "$R" "$H" "$ID" || { echo "[거부] D0b 판정 기록이 gate ${H:0:7}에 없거나 병합 기준 미달 -- 동결은 D0b 병합에서 시작한다" >&2; trap - ERR; exit 1; }
  cc=$(g show "$H:.ai/verification/$ID.json" | "$PY" -B -c "import json,sys;o=json.loads(sys.stdin.buffer.read().decode('utf-8'));print(o.get('code_commit') or '')")
  [ -n "$cc" ] && g rev-parse --verify -q "$cc^{commit}" > /dev/null || { echo "[거부] 판정 기록 code_commit을 읽지 못했다($cc)" >&2; trap - ERR; exit 1; }
  cat <<EOF
   ===== D-27 동결 공지 =====
   시작: D0b $ID 병합(판정 기록 code_commit ${cc:0:12}, gate master ${H:0:7}) -- 끝: F2 병합.
   이 구간에 다음을 바꾸는 Phase 3 밖 card는 병합하지 않는다: 엔진 파일(skills/analog-gmid-design/assets/*.py, workspaces/run_harness.py),
     tools/gates/**, tools/migrate/**, 레지스트리 $REG의 '이관 목적지' 열.
   어겼다면 그 card 뒤 D0b 재계산 card(레지스트리 열 재생성)를 먼저 한다(design 30 D-27). B26-2~B26-4·B35는 F2 뒤.
   D0b~M1 base 구간은 DoD가 덮지 않는다 -- M1 착수 전에 아래가 빈 출력인지 본다:
     git -C $R diff --stat $cc gate/master -- ':(glob)skills/analog-gmid-design/assets/*.py' workspaces/run_harness.py tools
   진행 중 spec card(판정 기록 없음): $(inflight_cards "$H" | tr '\n' ' ')
EOF
}

case "$1" in
  conds) stage_conds ;;
  pre) stage_pre ;;
  card) stage_card ;;
  final) stage_final ;;
  local) stage_pre; stage_card; stage_final ;;
  after-push) stage_after_push ;;
  freeze) stage_freeze ;;
  *) echo "사용: $0 [옵션…] conds|pre|local|card|final|after-push|freeze" >&2; exit 2 ;;
esac
