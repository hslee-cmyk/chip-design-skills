#!/usr/bin/env bash
# G1 게이트 card 20260930-p3-gate-move-aware 착수 0단계(오케스트레이터) -- redteam 32, 사용자 UD-5 "(가) 전역 이동 인식 (Recommended)".
# 근거: g1_briefs.md §0.7(착수 직전 재확인 1~9)·§0.8(명령 시퀀스 A~E)·§4, draft_p3_g1.spec.md(v9 + v8.4 재검토), design 30 v8.5 §8·§8.1.
# 구조는 b33_launch.sh를 따른다(단계별 함수, 옵션은 단계 이름 앞, 상태 파일, 게이트 캐시 절대 경로, push는 하지 않음 -- 끝에 단독 호출 명령 출력).
# 어느 확인이든 실패하면 그 자리에서 멈춘다(set -Eeuo pipefail + ERR trap). EL1이 판정하는 git 명령(push·worktree add/remove·branch -D·reset 등)은
# 실행하지 않고 출력만 한다(launch_common.sh B1).
#
#   bash g1_launch.sh kit-cmds    # 착수 때 재측정 명령 출력(실행 안 함 -- briefs §0.7 ③⑤⑥: 줄·키, H·W·엔진 사실, 공격 32·무동작 미리보기)
#   bash g1_launch.sh pre         # 착수 조건 + 착수 전 확인(저장소 변경 없음)
#   bash g1_launch.sh local       # pre -> doc -> card -> appr -> final (로컬 커밋 3개, push 안 함)
#   bash g1_launch.sh <단계>      # doc | card | appr | final 하나만(중단 뒤 이어 하기 -- 각 단계가 앞 단계 결과를 확인)
#   bash g1_launch.sh after-push  # push 뒤 gate master 대조 + 게이트 캐시 새 판 + test worktree 명령 출력
#
# 커밋 3개(briefs §0.8, 34·35·B33 선례):
#   A 문서 커밋(Role: doc): g1_kit/patch_g1_docs.py -- design 05 §10 V3·V6·V7 행 + 거부 증명 줄(공격 32), 계획 N3.10 이동 규칙 줄(533행) 한 문장
#   B spec card + interface card(Role: doc): draft_p3_g1.spec.md 그대로 + 게이트 캐시 interface_card.py(신규 시그니처 7행 -- SourceIndex.tree 포함, 기존 함수 0행)
#   C 승인 기록(Role: doc): fill_v3_approval.py(target_kind diff, diff_base = A^, diff_head = B, diff_path 4개 = 계획·design 05·interface·spec)
#   final: gate_change_ok(C) True / (B) False, 로컬 EL4 receive(캐시 merge_gate) exit 0
#
# 착수 조건(pre가 멈추는 것):
#   (1) 선행 card 판정 기록(launch_common lc_pred_ok, 단일 기준): 34·35·B34·b26pre·backfill·B26-1·B33 -- design 30 §8.1 'B33·34·35 → G1'과 확정 순서
#       FU(20261002-p3-future-annotations)·T0(20260930-p3-tests-location-free)는 G1과 독립(§8.1 'T0·FU는 G1과 독립') -- 병합 여부만 보고,
#       FU가 병합됐으면 spec card '작성 전 실측' 8의 future 문장('DR·ACF 없음')이 바뀌었어야 한다.
#   (2) Phase 3 design 승인 기록 20260930-30-module-split-design + design 30 문서가 gate master에 있다(UD-0), .ai/context.md에 UD-5 답 줄.
#   (3) UD-5 답 = (가): 승인 기록 초안 '사용자 원문'이 세션 jsonl AskUserQuestion(tool_use toolu_01VKN8qT3BbTikfZQyV9sdQi) 질문·선택지 라벨·설명·답과 바이트 일치,
#       date = 답 시각(KST) 날짜, 초안 = g1_kit 양식에서 자리표시 줄만 채운 것, 초안 범위의 단계 수 = spec card 계약 12(red·거부·합계).
#   (4) measured rev: spec card '작성 전 실측'의 '(…gate `master` `<rev>`…' 문단 rev 중 가장 새 것(나머지는 전부 그 조상)과 gate master 사이
#       G1 입력(게이트 도구 3개·test_lint·rt.py·run_all.py·엔진 assets/*.py·run_harness.py, gate_config reachability_roots)이 같다.
#       다르면 멈춘다 -> kit-cmds로 gate master에서 다시 재고 spec 초안에 '(착수 재측정 <날짜>, gate `master` `<rev>`, …' 문단을 더한다.
#
# 사전 시험(모래상자 -- 실제 저장소·gate는 읽기만):
#   bash g1_launch.sh --sbx /c/g<n>/<이름> [--sim-pred all|none|omit:<id>|fail:<id>] mk-sandbox
#        실제 저장소 복제 + (sim-pred) 34·35·B33 문서 패치 흉내 커밋 + 선행 7건 자리표시 판정 기록(audit 커밋, DRY_RUN 표지)
#        + 합성 audit 커밋(gate 경로만 모래상자로) + 가짜 gate(실제 pre-receive·gate-runner = EL4, core.hooksPath = .githooks = EL3)
#   bash g1_launch.sh --repo <복제본> --state <상태 파일> --wt <worktree 부모> [--draft-spec F] [--draft-apr F] <단계>
#   --draft-spec·--draft-apr는 복제본 전용(초안을 고친 사본으로 시험). 실제 저장소 판별은 launch_common.sh lc_repo_guard(git-common-dir 정규화 비교).
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
KIT=$DR/g1_kit
STATE_REAL=$DR/g1_launch_state.txt
STATE=$STATE_REAL
DRAFT_SPEC_REAL=$DR/draft_p3_g1.spec.md
DRAFT_SPEC=$DRAFT_SPEC_REAL
DRAFT_APR_REAL=$DR/approval_20260930-p3-gate-move-aware.md      # 채운 판(p3_design_commit.sh DRAFT_G1APR와 같은 파일)
DRAFT_APR=$DRAFT_APR_REAL
SBX=
SIM_PRED=all
while [ $# -gt 1 ]; do
  case "$1" in
    --repo) R=$2; shift 2 ;;
    --state) STATE=$2; shift 2 ;;
    --wt) W=$2; shift 2 ;;
    --draft-spec) DRAFT_SPEC=$2; shift 2 ;;
    --draft-apr) DRAFT_APR=$2; shift 2 ;;
    --sbx) SBX=$2; shift 2 ;;
    --sim-pred) SIM_PRED=$2; shift 2 ;;
    *) break ;;
  esac
done
# 단계 이름 뒤에 옵션을 붙이면 조용히 무시돼 실제 저장소에서 돈다(review_post_p10b_runbook B1과 같은 가드) -- 남은 인자는 단계 이름 하나뿐
[ $# -eq 1 ] || { echo "[중단] 사용법: $0 [--repo R --state S --wt W [--draft-spec F] [--draft-apr F]] <단계> | $0 --sbx /c/g<n>/<이름> [--sim-pred …] mk-sandbox  (옵션은 단계 이름 앞에만)" >&2; exit 2; }
case "$1" in --*) echo "[중단] 단계 이름 자리에 옵션: $1 (옵션 값이 빠졌거나 순서가 틀렸다)" >&2; exit 2 ;; esac
STEP=$1

PY=/c/Python314/python.exe
ID=20260930-p3-gate-move-aware
DAID=20260930-30-module-split-design                                 # Phase 3 design 승인 기록(UD-0·D-19·UD-1)
PATCH=$KIT/patch_g1_docs.py
FILL=$DR/fill_v3_approval.py
TEMPLATE_APR=$KIT/approval_$ID.md                                    # 양식(자리표시 3곳) -- 채운 판은 이 양식에서 자리표시 줄만 다르다
JSONL=/c/Users/HSLEE/.claude/projects/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922.jsonl
ASK_ID=toolu_01VKN8qT3BbTikfZQyV9sdQi
UD5_ANS="(가) 전역 이동 인식 (Recommended)"
PLAN=docs/01-plan/features/gain-budget-gmid-sizing.plan.md
D05=docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md
D30=docs/02-design/features/gain-budget-gmid-sizing.30-module-split.design.md
F_SPEC=docs/02-design/specs/$ID.spec.md
F_IFC=docs/02-design/specs/$ID.interface.md
F_APR=.ai/approvals/$ID.md
F_DAPR=.ai/approvals/$DAID.md
AS=skills/analog-gmid-design/assets
MUT=tools/gates/mutate_changed.py
RCH=tools/gates/reachability.py
SL=tools/gates/source_lint.py
RT=tools/gates/redteam/lib/rt.py
RUNALL=tools/gates/redteam/run_all.py
# measured rev와 gate master 사이 같아야 하는 G1 입력(spec card '작성 전 실측' 1·2·5·7·8과 머리 수치 H·W·공격 32 base 열이 읽는 것)
G1_INPUTS=("$RCH" "$MUT" "$SL" tools/gates/test_lint.py "$RT" "$RUNALL" ":(glob)$AS/*.py" workspaces/run_harness.py)
# 선행 card(design 30 §8.1 확정 순서: 34 → 35 → B34 → b26pre → backfill → B26-1 → B33 → Phase 3: T0, FU, G1)
PRED="20260930-v3-exempt-binding 20260930-v3-changed-stmt-scope 20260930-b34-grammar-explicit 20260930-b26-pre-test-strengthen 20261001-b26-backfill-interdig-final-audit 20260930-b26-rail-accessor-set 20260930-v7-registry-edges"
FU_ID=20261002-p3-future-annotations
T0_ID=20260930-p3-tests-location-free
COAUTH="Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
SUBJ_A="docs: $ID 문서 커밋(design 05 §10 V3·V6·V7 행 '옮긴 단위는 이동 원본과 비교', 거부 증명 줄 공격 32, 계획 N3.10 이동 규칙 V6·V7 한 문장)"
SUBJ_B="docs: 게이트 변경 spec card $ID(G1 -- V3·V6·V7 옮긴 단위 인식, design 30 §3 MOVED) + interface card"
SUBJ_C="docs: 승인 기록 $ID(UD-5 G1 게이트 변경 승인, target_kind diff -- spec card·interface card·design 05 §10·계획 N3.10 한 문장)"

say() { printf '%s\n' "== $*"; }
g() { git -C "$R" "$@"; }

# ---------------------------------------------------------------- 모래상자 만들기(실제 저장소·gate는 읽기만 -- p3_design_commit.sh mk-sandbox 모양)
if [ "$STEP" = mk-sandbox ]; then
  [ -n "$SBX" ] || { echo "[중단] mk-sandbox에는 --sbx 필수" >&2; exit 2; }
  # glob /c/g[0-9]*/*는 /c/g196x/…도 받는다(실측 -- p3_design_commit.sh mk-sandbox와 같은 구멍) -> 정규식으로 번호만
  [[ "$SBX" =~ ^/c/g[0-9]+/[A-Za-z0-9._-]+$ ]] || { echo "[중단] 모래상자는 /c/g<번호>/<이름>만: $SBX" >&2; exit 2; }
  [ "$R" = "$R_REAL" ] || { echo "[중단] mk-sandbox에는 --repo를 쓰지 않는다(원본 = 실제 저장소, 읽기만)" >&2; exit 2; }
  case "$SIM_PRED" in all|none|omit:*|fail:*) ;; *) echo "[중단] --sim-pred all|none|omit:<id>|fail:<id>: $SIM_PRED" >&2; exit 2 ;; esac
  SW=$(printf '%s' "$SBX" | sed -E 's#^/([a-zA-Z])/#\U\1:/#')
  test ! -e "$SBX/r"; test ! -e "$SBX/gate.git"
  mkdir -p "$SBX"
  lc_tmp_setup "$SBX/setup"
  test -n "$(git config --get user.email)"
  # (pre-r1g) -c core.autocrlf=false: 복제본 config에 남겨 작업 트리를 LF로(시스템 gitconfig autocrlf=true -- 검토 minor 5)
  git clone -c core.autocrlf=false -q --no-hardlinks --no-local --no-checkout "$R_REAL" "$SBX/r"
  git -C "$SBX/r" config core.longpaths true
  # 모래상자 master = 실제 gate master(메인 master는 보내지 않은 문서 커밋으로 gate보다 앞설 수 있다 -- 2026-10-06 실측: 메인 300fd65 = gate dafe5cf + D-11 2커밋.
  # 그대로 master를 꺼내면 아래 단정이 멈췄다). gate master 객체는 메인 master의 조상이라 --no-local 복제에 들어 있다.
  GM_REAL=$(git -C "$R_REAL" rev-parse gate/master)
  git -C "$R_REAL" merge-base --is-ancestor "$GM_REAL" master || { echo "[중단] gate master가 메인 master의 조상이 아니다" >&2; exit 2; }
  git -C "$SBX/r" checkout -q -B master "$GM_REAL"
  test "$(git -C "$SBX/r" rev-parse HEAD)" = "$GM_REAL"
  if [ "$SIM_PRED" != none ]; then
    # 선행 card 문서 커밋 흉내(34 → 35 → B33 -- G1 문서 패치의 선행 문구. 코드 변경은 흉내 내지 않는다)
    "$PY" -B "$DR/patch_v3_binding_docs.py" --root "$SBX/r" | sed 's/^/   34 /'
    "$PY" -B "$DR/patch_v3_scope_docs.py" --root "$SBX/r" | sed 's/^/   35 /'
    "$PY" -B "$DR/patch_b33_design05.py" "$SBX/r" | sed 's/^/   B33 /'
    if ! git -C "$SBX/r" diff --quiet; then
      git -C "$SBX/r" commit -q -a -m "docs: DRY-RUN 34·35·B33 문서 패치 흉내(실제 card 문서 커밋 아님)" --trailer "Role: doc"
    fi
    # 선행 7건 자리표시 판정 기록(card마다 audit 커밋 하나 -- 실제 판정 아님). omit = 빠뜨림, fail = V1 FAIL
    for id in $PRED; do
      [ "$SIM_PRED" = "omit:$id" ] && { echo "   (omit) $id 판정 기록 없음"; continue; }
      v1=PASS; [ "$SIM_PRED" = "fail:$id" ] && v1=FAIL
      "$PY" -B -c "
import json,sys
ck={'V%d'%i:{'verdict':'N/A'} for i in range(1,11)}; ck['V1']={'verdict':sys.argv[2]}; ck['V10']={'verdict':'PASS'}
open(sys.argv[3],'w',encoding='utf-8',newline='\n').write(json.dumps({'id':sys.argv[1],'DRY_RUN':'합성 자리표시 -- 실제 판정 기록 아님','checks':ck},ensure_ascii=False,indent=1)+'\n')" "$id" "$v1" "$SBX/r/.ai/verification/$id.json"
      git -C "$SBX/r" add -- ".ai/verification/$id.json"
      git -C "$SBX/r" commit -q -m "audit: $id 판정 기록(DRY-RUN 자리표시, V1 $v1)" --trailer "Role: audit" --trailer "Change-Id: $id"
    done
  fi
  # 합성 audit 커밋: gate_config.json gate_path·workspace_path와 pre-receive 실행 경로만 모래상자로(EL3·EL4가 실제 gate 대신 모래상자 gate를 본다)
  "$PY" -B - "$SBX/r" "$SW" <<'EOF'
import json, sys, os
r, sw = sys.argv[1], sys.argv[2]
p = os.path.join(r, "tools", "gates", "gate_config.json")
raw = open(p, "rb").read()
crlf = b"\r\n" in raw
cfg = json.loads(raw.decode("utf-8"))
cfg["gate_path"] = sw + "/gate.git"
cfg["workspace_path"] = sw + "/r"
out = json.dumps(cfg, ensure_ascii=False, indent=2) + "\n"
if crlf:
    out = out.replace("\n", "\r\n")
open(p, "wb").write(out.encode("utf-8"))
q = os.path.join(r, "tools", "gates", "gate", "pre-receive")
b = open(q, "rb").read()
old = b"C:/Users/HSLEE/Documents/Todoc/fpga/gmid-gate.git/gate-runner.py"
assert b.count(old) == 1
open(q, "wb").write(b.replace(old, (sw + "/gate.git/gate-runner.py").encode()))
EOF
  git -C "$SBX/r" add -- tools/gates/gate_config.json tools/gates/gate/pre-receive
  git -C "$SBX/r" commit -q -m "audit: g1-launch DRY-RUN 합성(모래상자 gate 경로만 바꿈, 실제 판정 아님)" --trailer "Role: audit" --trailer "Change-Id: 20261002-g1-launch-dryrun"
  SYN=$(git -C "$SBX/r" rev-parse HEAD)
  git clone -q --bare --no-hardlinks --no-local "$SBX/r" "$SBX/gate.git"
  rm -rf "$SBX/gate.git/hooks"; mkdir -p "$SBX/gate.git/hooks"
  git -C "$SBX/r" show "HEAD:tools/gates/gate/pre-receive" > "$SBX/gate.git/hooks/pre-receive"
  git -C "$SBX/r" show "HEAD:tools/gates/gate/gate-runner.py" > "$SBX/gate.git/gate-runner.py"
  BL=$("$PY" -B -c "import json,sys;print(json.load(open(sys.argv[1],encoding='utf-8'))['baseline_commit'])" "$SBX/r/tools/gates/gate_config.json")
  printf '%s %s 2026-10-02T00:00:00\n%s %s 2026-10-02T00:00:01\n' "$BL" "$BL" "$BL" "$SYN" > "$SBX/gate.git/gmid-accept-log"
  git -C "$SBX/r" remote remove origin
  git -C "$SBX/r" remote add gate "$SW/gate.git"
  git -C "$SBX/r" fetch -q gate
  git -C "$SBX/r" branch -q --set-upstream-to=gate/master master
  git -C "$SBX/r" config core.hooksPath "$SW/r/.githooks"
  mkdir -p "$SBX/r/.claude/hooks"
  cp "$R_REAL/.claude/hooks/"role_*.py "$SBX/r/.claude/hooks/"
  cp "$R_REAL/.claude/settings.json" "$SBX/r/.claude/settings.json"
  test "$(git -C "$SBX/r" rev-parse gate/master)" = "$SYN"
  echo "모래상자 준비: $SBX/r HEAD = gate master = $SYN (sim-pred $SIM_PRED + 합성 audit)"
  exit 0
fi
[ -z "$SBX" ] || { echo "[중단] --sbx는 mk-sandbox 전용" >&2; exit 2; }
[ "$SIM_PRED" = all ] || { echo "[중단] --sim-pred는 mk-sandbox 전용" >&2; exit 2; }

lc_repo_guard "$R" "$R_REAL"
if [ "$LC_REAL" = 0 ]; then
  lc_need_sandbox --state "$STATE" "$STATE_REAL"; lc_need_sandbox --wt "$W" "$W_REAL"
else
  lc_need_real --state "$STATE" "$STATE_REAL"; lc_need_real --wt "$W" "$W_REAL"
  lc_same_path "$DRAFT_SPEC" "$DRAFT_SPEC_REAL" || { echo "[중단] --draft-spec은 --repo(복제본)와 함께만" >&2; exit 2; }
  lc_same_path "$DRAFT_APR" "$DRAFT_APR_REAL" || { echo "[중단] --draft-apr은 --repo(복제본)와 함께만" >&2; exit 2; }
  STATE=$STATE_REAL; W=$W_REAL; DRAFT_SPEC=$DRAFT_SPEC_REAL; DRAFT_APR=$DRAFT_APR_REAL
fi
lc_tmp_setup "$STATE"
echo "== 대상 저장소 R=$R  상태 파일 $STATE  spec 초안 $DRAFT_SPEC  승인 초안 $DRAFT_APR  worktree 부모 $W  (실제 저장소=$LC_REAL)"

st_set() { touch "$STATE"; grep -v "^$1=" "$STATE" > "$STATE.tmp" || true; printf '%s=%s\n' "$1" "$2" >> "$STATE.tmp"; mv "$STATE.tmp" "$STATE"; }
st_get() { local v; v=$(grep "^$1=" "$STATE" | tail -1 | cut -d= -f2-); test -n "$v"; printf '%s' "$v"; }
# 게이트 코드 캐시 = <git-common-dir>/gmid-gate-cache/<gate master 전체 sha>(hook과 같은 ensure_cache)
cache_dir() {
  local c
  c=$("$PY" -B -c "import sys;sys.path.insert(0,sys.argv[1]);import role_paths as rp;print(rp.ensure_cache(rp.load_env(sys.argv[2])))" "$R/tools/gates" "$R")
  test "$(basename "$c")" = "$(g rev-parse gate/master)"
  test -f "$c/interface_card.py"; test -f "$c/merge_gate.py"; test -f "$c/weakening_diff.py"; test -f "$c/reachability.py"
  printf '%s' "$c"
}
plan_hash() { "$PY" -B "$1/merge_gate.py" plan-tables-hash "$R/$PLAN"; }
staged_is() { test "$(g diff --cached --name-only | sort | tr '\n' ' ')" = "$(printf '%s\n' "$@" | sort | tr '\n' ' ')"; }
numstat_is() { test "$(g diff --cached --numstat -- "$1" | cut -f1-2 | tr '\t' ' ')" = "$2"; }
head_subj_is() { test "$(g log -1 --format=%s)" = "$1"; }
trailer_is() {   # <커밋> <키> <값|-(없음)>
  local v; v=$(g log -1 --format="%(trailers:key=$2,valueonly)" "$1" | tr -d '\r' | grep -v '^$' || true)
  if [ "$3" = - ]; then test -z "$v"; else test "$v" = "$3"; fi
}
# _approved_ids(<rev>) -- 캐시 판 reachability(읽기 전용)
approved_ids() { "$PY" -B -c "
import sys;sys.path.insert(0,sys.argv[1]);import reachability as r
print('\n'.join(sorted(r._approved_ids(sys.argv[2],sys.argv[3]))))" "$1" "$R" "$2"; }

# spec 초안 '작성 전 실측'에서 '(' 로 시작하는 문단 첫 줄의 gate `master` `<rev>`들 -> 가장 새 rev(나머지는 전부 그 조상이어야 한다 -- 순서 무관).
#   G1 초안은 새 문단을 위에 쌓는다(v8.4 재검토 dd60db6 → v9 키트 0f23786 → 기준 7535799) -- '마지막 출현' 규약(launch_common m8) 대신 조상 관계로 고른다.
meas_newest() {
  local all x y best=
  all=$("$PY" -B - "$DRAFT_SPEC" <<'EOF'
import re, sys
t = open(sys.argv[1], encoding="utf-8").read().replace("\r\n", "\n")
sec = t.split("\n## 작성 전 실측\n", 1)[1].split("\n## ", 1)[0].split("\n")
revs = [m.group(1) for l in sec if l.startswith("(") for m in [re.search(r"gate `master` `([0-9a-f]{7,40})`", l)] if m]
assert revs, "'작성 전 실측'에 '(… gate `master` `<rev>`' 문단 없음"
print("\n".join(revs))
EOF
)
  all=$(printf '%s\n' "$all" | tr -d '\r')                            # Windows Python 줄 끝 CRLF -- 가운데 줄의 CR은 명령 치환이 지우지 않는다(실측)
  for x in $all; do
    g rev-parse --verify -q "$x^{commit}" > /dev/null || { echo "[중단] measured rev $x를 $R에서 찾지 못했다" >&2; return 1; }
    local ok=1
    for y in $all; do g merge-base --is-ancestor "$y" "$x" || { ok=0; break; }; done
    [ "$ok" = 0 ] || { best=$x; break; }
  done
  [ -n "$best" ] || { echo "[중단] '작성 전 실측' measured rev들($(echo $all))이 한 줄 조상 사슬이 아니다" >&2; return 1; }
  printf '%s' "$best"
}

# 사용자 원문 바이트 대조(세션 jsonl AskUserQuestion tool_use·tool_result, p3_design_commit.sh check_quote와 같은 식) + UD-5 답 = (가) + date = 답 시각 KST 날짜
#   <승인 기록 파일> -> 출력: 답 날짜(YYYY-MM-DD)
check_quote() {
  "$PY" -B - "$JSONL" "$ASK_ID" "$1" "$UD5_ANS" <<'EOF'
import datetime, json, re, sys
J, TID, F, WANT = sys.argv[1:5]
use = res = ts = None
with open(J, "rb") as fh:
    for line in fh:
        if TID.encode() not in line:
            continue
        o = json.loads(line)
        for c in (o.get("message") or {}).get("content") or []:
            if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("id") == TID:
                use = c["input"]
            if isinstance(c, dict) and c.get("type") == "tool_result" and c.get("tool_use_id") == TID:
                res, ts = o.get("toolUseResult"), o.get("timestamp")
if use is None or res is None or not ts:
    sys.exit("[중단] jsonl에서 질문(tool_use)이나 답(tool_result)을 찾지 못함")
q = [x for x in use["questions"] if x["header"] == "UD-5"]
if len(q) != 1:
    sys.exit("[중단] UD-5 질문이 정확히 하나가 아니다: %d" % len(q))
q = q[0]
ans = res["answers"].get(q["question"])
if ans != WANT:
    sys.exit("[중단] UD-5 답이 %r -- (가)가 아니면 이 card는 쓰지 않는다(briefs 머리: (나)면 선언 대조 card, 보류면 멈춤)" % ans)
t = open(F, "rb").read().decode("utf-8")
miss = [s[:60] for s in [q["question"], '답: "%s"' % ans, "> %s" % ans] + [o["label"] for o in q["options"]] + [o["description"] for o in q["options"]] if s not in t]
if miss:
    sys.exit("[중단] 사용자 원문 바이트 대조 실패(%s): %r" % (F, miss))
day = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
m = re.search(r"^date: (\S+)$", t.split("\n---\n", 1)[0].replace("\r\n", "\n"), flags=re.M)
if not m or m.group(1) != day:
    sys.exit("[중단] 승인 기록 date %r != UD-5 답 날짜(KST) %s" % (m and m.group(1), day))
sys.stderr.write("   사용자 원문 바이트 대조 OK: UD-5 질문·선택지 3개(라벨·설명)·답 %r, 답 %s = %s KST\n" % (ans, ts, day))
print(day)
EOF
}

# 초안 = g1_kit 양식에서 자리표시 줄(date·사용자 원문·질문 출처 문단)만 바꾼 것 + 단계 수가 spec card 계약 12와 같다
check_apr_draft() {
  "$PY" -B - "$TEMPLATE_APR" "$DRAFT_APR" "$DRAFT_SPEC" <<'EOF'
import difflib, re, sys
tpl, drf, spec = [open(p, encoding="utf-8").read().replace("\r\n", "\n") for p in sys.argv[1:4]]
# 단계 수 구절은 아래에서 spec card와 따로 대조한다(양식도 같은 구절을 가진다 -- 정정이 양식·채운 판 어느 쪽에 먼저 들어가도 양식 대조는 그 구절을 보지 않는다)
STEPS = re.compile(r"red \d+ \+ 거부 \d+ = \d+단계")
TL, DL = STEPS.sub("<steps>", tpl).split("\n"), STEPS.sub("<steps>", drf).split("\n")
PH = ("<승인일 YYYY-MM-DD>", "<UD-5 답 원문", "<날짜·시각>")
ph = {i for i, l in enumerate(TL) if any(p in l for p in PH)}
bad = []
if len(ph) != 3:
    bad.append(("양식 자리표시 줄 수", len(ph)))
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, TL, DL, autojunk=False).get_opcodes():
    if tag == "equal":
        continue
    if tag == "insert" and i1 > 0 and (i1 - 1) in ph:      # 자리표시 줄 바로 뒤에 덧붙인 줄(질문 원문 인용)
        continue
    if tag in ("replace", "delete") and set(range(i1, i2)) <= ph and j2 > j1:
        continue
    bad.append(("양식 밖 차이", tag, TL[i1:i2][:2], DL[j1:j2][:2]))
left = [p for p in PH + ("<답 라벨>",) if p in drf]
if left:
    bad.append(("남은 자리표시", left))
if drf.count("<rev-parse>") != 3:
    bad.append(("<rev-parse> 수", drf.count("<rev-parse>")))
# 단계 수: spec card 계약 12 표 아래 문장('나머지 N단계는 거부 단계 … -- T단계', red = T - N) vs 초안 범위 '(red r + 거부 n = t단계'
m = re.search(r"나머지 (\d+)단계는 거부 단계\(base = 병합본\) -- (\d+)단계", spec)
a = re.search(r"red (\d+) \+ 거부 (\d+) = (\d+)단계", drf)
if not m or not a:
    bad.append(("단계 수 문장을 못 찾음", bool(m), bool(a)))
else:
    rej, tot = int(m.group(1)), int(m.group(2))
    want, got = (tot - rej, rej, tot), tuple(int(x) for x in a.groups())
    if want != got:
        bad.append(("초안 범위 단계 수 != spec card 계약 12(red, 거부, 합계)", got, want))
if bad:
    sys.exit("[중단] 승인 기록 초안 확인 실패: %r" % bad)
print("   승인 초안 OK: 양식에서 자리표시 줄만 다름, 단계 수 = spec card 계약 12 (red %d + 거부 %d = %d단계)" % want)
EOF
}

stage_kit_cmds() {
  local gm gm7 n=g'<n>'
  gm=$(g rev-parse gate/master); gm7=${gm:0:7}
  cat <<EOF
== 착수 재측정 명령(gate master $gm7 -- 실행하지 않음, 순서대로. 격리 복제본 C:/$n은 새 번호, TMP도 그 아래, 끝나면 그것만 삭제)
# ③ 도구 줄·키(card '작성 전 실측' 1·2 -- 심볼이 앵커, 줄 번호는 표기 갱신 후보)
git -C $R grep -n 'changed_defs(\|mutants(\|json.dumps\|def def_hash\|def _strip_doc' $gm -- $MUT
git -C $R grep -n 'base_defs\|new_defs = \|^def main\|^def build_graph' $gm -- $RCH
git -C $R grep -n '^def compare\|findings += compare\|module_text' $gm -- $SL
git -C $R grep -n 'observe\|v4_first\|out_jsonl\|tool_tmpdir\|root_state' $gm -- $RT
git -C $R grep -n 'observed_equals' $gm -- $RUNALL
# ⑤ 머리 수치·엔진 사실(H·W -- m9_measure 약 1시간 -> run_in_background, timeout 2시간). 주의: install_proto.py 앵커는 a17b8bd 판(card 35 병합본 --
#    dafe5cf에서도 installed 4; 35 전 판 사본은 install_proto.py.pre-35.bak)이라 B33 병합본(reachability main·build_graph)에 맞지 않으면 exit 1·무쓰기 --
#    그때 rch 앵커를 고친 사본을 C:/$n 아래에서 쓴다(briefs §0.3 끝). g7_facts.py는 --scratch C:/$n 인자, tree_check.py는 경로 C:/g143 하드코딩 -- 사본에서 바꾼다.
#    setup_clones.sh 셋째 인자 = 체크아웃 rev(메인 master가 gate보다 앞서 있어도 gate 판을 잰다). 자식 bash는 APPDATA·HOME을 잃어 pytest가 안 보인다 --
#    키트 스크립트가 export·import pytest 단정을 하므로 아래 TMP=… $PY 줄도 같은 셸이면 APPDATA가 있는지 먼저 본다.
bash $KIT/setup_clones.sh C:/$n $(cygpath -m "$R") $gm
TMP=C:/$n/tmp TEMP=C:/$n/tmp $PY -B $KIT/m9_measure.py C:/$n C:/$n/b C:/$n/p <order sim WORK> $KIT/out/m9_$gm7.json
# ⑥ 공격 32 미리보기(base 도구 93단계 exit = 표 왼쪽 열) + 34·35 무동작 미리보기(B33 병합 뒤 --only 33- 추가). 비교 기준선 out/noop_base_dafe5cf.*
bash $KIT/run_attack32.sh C:/$n b base_$gm7 -
bash $KIT/run_noop.sh C:/$n b base_$gm7 --only 34- --only 35-
# 수치·사실이 card와 다르면 draft_p3_g1.spec.md '작성 전 실측'에 새 '(착수 재측정 <날짜>, gate \`master\` \`$gm7\`, …' 문단을 더한다(백업 먼저).
# 같으면 같은 형식의 문단에 '변화 없음'과 잰 값을 적는다 -- pre의 measured rev 대조(G1 입력 불변)가 그 rev를 기준으로 한다.
EOF
}

stage_pre() {
  say "pre: 착수 조건 + 착수 전 확인(저장소 변경 없음)"
  test -n "$(git config --get user.email)"
  g fetch -q gate
  test "$(g rev-parse --abbrev-ref HEAD)" = master
  test "$(g rev-parse HEAD)" = "$(g rev-parse gate/master)"
  test -z "$(g for-each-ref refs/heads/role/)"                        # 역할 브랜치가 있으면 문서 push를 EL1이 거부(design 05 §12) -- 선행 card 정리 끝
  if g worktree list --porcelain | grep -q -- "/$ID-"; then echo "[중단] $ID worktree가 이미 있다" >&2; false; fi
  g diff --cached --quiet
  test -z "$(g status --porcelain -- docs/ .ai/approvals/)"
  test ! -e "$R/$F_SPEC"; test ! -e "$R/$F_IFC"; test ! -e "$R/$F_APR"
  if g cat-file -e "HEAD:$F_APR" 2>/dev/null; then echo "[중단] 승인 기록 $ID가 이미 gate master에 있다" >&2; false; fi
  for f in "$PATCH" "$FILL" "$DRAFT_SPEC" "$DRAFT_APR" "$TEMPLATE_APR" "$JSONL"; do test -s "$f"; done
  rm -f "$STATE"
  # (1) 선행 card: 판정 기록이 gate master에 있고 V1~V10 정확히·전부 PASS·N/A(launch_common lc_pred_ok 단일 기준, m6)
  local id
  for id in $PRED; do
    lc_pred_ok "$R" HEAD "$id" || { echo "[중단] 선행 card $id가 병합 기준에 맞지 않는다(design 30 §8.1 순서)" >&2; false; }
    echo "   선행 $id 판정 기록 V1~V10 PASS·N/A"
  done
  # FU·T0: G1과 독립(design 30 §8.1) -- 보고만. FU가 병합됐으면 spec '작성 전 실측' 8 future 문장이 바뀌었어야 한다(briefs §0.7 ①)
  local nfu
  nfu=$( (g grep -h "^from __future__ import annotations" HEAD -- "$AS/design_report.py" "$AS/audit_current_forced.py" || true) | wc -l | tr -d ' ')
  if g cat-file -e "HEAD:.ai/verification/$FU_ID.json" 2>/dev/null; then echo "   FU $FU_ID 판정 기록 있음"; else echo "   FU $FU_ID 판정 기록 없음(G1과 독립)"; fi
  if g cat-file -e "HEAD:.ai/verification/$T0_ID.json" 2>/dev/null; then echo "   T0 $T0_ID 판정 기록 있음"; else echo "   T0 $T0_ID 판정 기록 없음(G1과 독립)"; fi
  case "$nfu" in
    0) grep -q "(DR·ACF 없음" "$DRAFT_SPEC" || { echo "[중단] FU 미병합(DR·ACF future 0)인데 spec '작성 전 실측' 8에 'DR·ACF 없음' 문장이 없다" >&2; false; } ;;
    2) if grep -q "(DR·ACF 없음" "$DRAFT_SPEC"; then echo "[중단] FU 병합됨(DR·ACF future 2) -- spec '작성 전 실측' 8의 'DR·ACF 없음'을 재측정 문장으로 고친다" >&2; false; fi ;;
    *) echo "[중단] DR·ACF future 줄 수 $nfu(0 또는 2가 아님 -- FU 부분 상태)" >&2; false ;;
  esac
  echo "   DR·ACF future 줄 $nfu (FU $( [ "$nfu" = 2 ] && echo 병합 || echo 미병합)) -- spec 8 문장과 맞음"
  # (2) Phase 3 design 승인(UD-0): 승인 기록 + design 30 문서 + context.md UD-5 줄
  g cat-file -e "HEAD:$D30" 2>/dev/null || { echo "[중단] design 30 문서가 gate master에 없다(p3_design_commit.sh 먼저)" >&2; false; }
  g cat-file -e "HEAD:$F_DAPR" 2>/dev/null || { echo "[중단] design 승인 기록 $DAID가 gate master에 없다(UD-0 -- p3_design_commit.sh 먼저)" >&2; false; }
  local C; C=$(cache_dir)
  mkdir -p "$STATE.tmpd/dappr"; g show "HEAD:$F_DAPR" > "$STATE.tmpd/dappr/$DAID.md"
  "$PY" -B "$C/merge_gate.py" parse-approval "$STATE.tmpd/dappr/$DAID.md" > "$STATE.dappr.json"
  "$PY" -B -c "
import json,sys;sys.path.insert(0,sys.argv[2]);import weakening_diff as wd
r=json.load(open(sys.argv[1],encoding='utf-8'))
assert r['id']==sys.argv[4] and r['target_kind']=='diff',r
assert r['target'] in wd.approved_hashes(sys.argv[3],'HEAD'),'design 승인 target이 approved_hashes(HEAD)에 없다'
print('   design 승인 기록 %s: diff target %s… approved_hashes(HEAD)에 있음, date %s'%(r['id'],r['target'][:12],r['date']))" "$STATE.dappr.json" "$C" "$R" "$DAID"
  g show HEAD:.ai/context.md | grep -qF "UD-5 \"$UD5_ANS\"" || { echo "[중단] .ai/context.md(HEAD)에 UD-5 답 줄이 없다" >&2; false; }
  # (3) UD-5 답 = (가) + 사용자 원문 바이트 대조 + 초안 모양
  local day; day=$(check_quote "$DRAFT_APR"); st_set APR_DATE "$day"
  check_apr_draft
  test "$(grep '^diff_path: ' "$DRAFT_APR" | cut -d' ' -f2- | tr -d '\r' | tr '\n' ' ')" = "$PLAN $D05 $F_IFC $F_SPEC "
  grep -qx "id: $ID" "$DRAFT_APR"; grep -qx "target_kind: diff" "$DRAFT_APR"
  # spec card 머리(phase 0.5·red-green·gate_change yes·approval 자기 id)
  "$PY" -B -c "
import sys;sys.path.insert(0,sys.argv[1]);import role_paths as rp, merge_gate as mg
c=rp.parse_spec_card(open(sys.argv[2],encoding='utf-8').read(),sys.argv[3])
assert (c['phase'],c['evidence_type'],c['gate_change'],c['approval'])==('0.5','red-green','yes',[sys.argv[3]]),c
assert c['phase'] in mg.read_plan_tables(sys.argv[4]).phase_order
print('   spec 초안 머리 OK',c['phase'],c['evidence_type'],c['gate_change'],c['approval'],'절',len(c['sections']))" "$C" "$DRAFT_SPEC" "$ID" "$R/$PLAN"
  # (4) measured rev(가장 새 '(…gate master' 문단)와 gate master 사이 G1 입력 불변 -- 다르면 card 사실 문장·머리 수치 재측정
  local meas ms; ms=$(meas_newest); meas=$(g rev-parse --verify "$ms^{commit}"); st_set MEAS "$meas"
  g merge-base --is-ancestor "$meas" HEAD
  g diff --quiet "$meas" HEAD -- "${G1_INPUTS[@]}" || { echo "[중단] measured rev $ms 와 gate master 사이 G1 입력 차이 -- kit-cmds로 다시 재고 spec 초안에 '(착수 재측정 …, gate \`master\` \`<rev>\`' 문단을 더한다:" >&2; g diff --stat "$meas" HEAD -- "${G1_INPUTS[@]}" | tail -8 >&2; false; }
  "$PY" -B -c "
import json,subprocess,sys
cfg=lambda rev:json.loads(subprocess.run(['git','-C',sys.argv[1],'show',rev+':tools/gates/gate_config.json'],capture_output=True,check=True).stdout)['reachability_roots']
assert cfg(sys.argv[2])==cfg('HEAD'),'reachability_roots 다름'" "$R" "$meas"
  echo "   measured rev $ms(${meas:0:12}) .. gate master: G1 입력 ${#G1_INPUTS[@]}묶음·reachability_roots 같음"
  # 사실(briefs §0.7 ②③④): 32 번호 비어 있음, merge_gate 불변(0f23786 이후), 새 이름 tools/ 0건
  test -z "$(g ls-tree --name-only HEAD tools/gates/redteam/attacks/ | grep '/32-' || true)"
  echo "   attacks: $(g ls-tree --name-only HEAD tools/gates/redteam/attacks/ | sed 's#.*/##' | { grep -E '^3[0-9]-' || true; } | tr '\n' ' ')(32-* 없음)"
  g diff --quiet 0f23786 HEAD -- tools/gates/merge_gate.py
  test -z "$(g grep -n -E "moved_defs|SourceIndex|global_names|binding_origin|move_rejected|global-dynamic" HEAD -- tools || true)"
  echo "   새 이름 tools/ 0건; docs/01-plan·docs/02-design $( (g grep -n -E "moved_defs|SourceIndex|global_names|binding_origin|move_rejected|global-dynamic" HEAD -- docs/01-plan docs/02-design || true) | wc -l | tr -d ' ')줄(design 30 승인본 포함 -- card '작성 전 실측' 2의 '0건'은 design 커밋 전 측정)"
  echo "   게이트 밖 changed_defs·def_hash 호출(card '작성 전 실측' 5 -- 계약 8 호환 대상):"
  { g grep -n -E "(mc|mutate_changed)\.(changed_defs|def_hash)\(" HEAD -- '*.py' ':!tools/gates/' || true; } | sed 's/^HEAD://; s/^/     /' | cut -c1-120
  echo "   인용 줄(card 표기 -- 심볼이 앵커):"
  g grep -n "changed_defs(\|def def_hash\|def _strip_doc\|json.dumps" HEAD -- "$MUT" | sed 's/^HEAD://' | cut -c1-110 | sed 's/^/     /'
  g grep -n "base_defs\|new_defs = " HEAD -- "$RCH" | sed 's/^HEAD://' | cut -c1-110 | sed 's/^/     /'
  # 문서 패치: gate master blob 사본에 적용 -> check ok(would apply 5) -> applied 5 -> already applied(저장소 무쓰기)
  local P="$STATE.tmpd/patchroot"
  rm -rf "$P"; mkdir -p "$P/$(dirname "$D05")" "$P/$(dirname "$PLAN")"
  g show "HEAD:$D05" > "$P/$D05"; g show "HEAD:$PLAN" > "$P/$PLAN"
  "$PY" -B "$PATCH" --root "$P" --check | tee "$STATE.patch0.txt" | cut -c1-200 | sed 's/^/   /'
  grep -q '^check ok (would apply 5)' "$STATE.patch0.txt"
  "$PY" -B "$PATCH" --root "$P" | grep -q '^applied 5 replacement(s)'
  "$PY" -B "$PATCH" --root "$P" | grep -q '^already applied'
  rm -rf "$P"
  local H; H=$(plan_hash "$C"); test ${#H} = 64
  st_set GATE_BASE "$(g rev-parse HEAD)"; st_set PLAN_HASH "$H"; st_set CACHE "$C"
  approved_ids "$C" "$(g rev-parse HEAD)" > "$STATE.ids.base"
  st_set N_IDS "$(wc -l < "$STATE.ids.base" | tr -d ' ')"
  say "pre OK: gate master $(g rev-parse --short HEAD), measured rev $ms, 승인 date $day, _approved_ids $(st_get N_IDS), plan_tables_hash $H, cache $C"
}

stage_doc() {
  say "doc (A): design 05 §10 V3·V6·V7 행 + 거부 증명 줄 + 계획 N3.10 533행 -- Role: doc"
  test "$(g rev-parse HEAD)" = "$(st_get GATE_BASE)"
  g diff --cached --quiet
  test -z "$(g status --porcelain -- docs/)"
  "$PY" -B "$PATCH" --root "$R" --check | grep -q '^check ok (would apply 5)'
  "$PY" -B "$PATCH" --root "$R" | tee "$STATE.patchA.txt" | cut -c1-200 | sed 's/^/   /'
  grep -q '^applied 5 replacement(s)' "$STATE.patchA.txt"
  "$PY" -B "$PATCH" --root "$R" | grep -q '^already applied'                  # 재실행 멱등
  g add -- "$D05" "$PLAN"
  staged_is "$D05" "$PLAN"
  numstat_is "$D05" "4 4"; numstat_is "$PLAN" "1 1"
  local H; H=$(plan_hash "$(st_get CACHE)"); test "$H" = "$(st_get PLAN_HASH)"   # 판정 표 불변 -> plan_tables 승인 불필요
  g commit -q -m "$SUBJ_A" \
    -m "_drafts/g1_kit/patch_g1_docs.py 적용(spec card $ID 계약 13: design 05 §10 V3 행 ① 끝·V6 행·V7 행(B33 문구 뒤)·거부 증명 줄 공격 32, 계획 N3.10 이동 규칙 줄 끝 한 문장 -- 줄 안 삽입 5곳, 줄 수 불변, 줄 끝 보존). 판정 표 무변경(plan_tables_hash $H). 승인 기록 $ID가 이 커밋의 부모를 diff_base로 가리킨다." \
    --trailer "Role: doc" --trailer "$COAUTH"
  head_subj_is "$SUBJ_A"
  test "$(g rev-parse HEAD^)" = "$(st_get GATE_BASE)"
  trailer_is HEAD Role doc; trailer_is HEAD Change-Id -
  st_set A "$(g rev-parse HEAD)"
  say "doc OK: $(g rev-parse --short HEAD)"
}

stage_card() {
  say "card (B): spec card + interface card(게이트 캐시 interface_card.py, 절대 경로) -- Role: doc"
  test "$(g rev-parse HEAD)" = "$(st_get A)"
  g diff --cached --quiet
  local C; C=$(cache_dir); test "$C" = "$(st_get CACHE)"              # gate master가 그사이 움직이지 않았다
  test ! -e "$R/$F_SPEC"; test ! -e "$R/$F_IFC"
  cp "$DRAFT_SPEC" "$R/$F_SPEC"
  "$PY" -B "$C/interface_card.py" "$R/$F_SPEC" --root "$R" --out "$R/$F_IFC"
  test -s "$R/$F_IFC"
  # 표 행: 기존 함수 0행(v9 -- 계약 6 토큰 reachability.build_graph), 신규 시그니처 = spec '신규 시그니처' 표 그대로 7행(SourceIndex.tree 포함, D0a 계약 6)
  "$PY" -B - "$R/$F_IFC" "$R/$F_SPEC" <<'EOF'
import sys
def rows(s):
    return [tuple(c.strip() for c in l.split("|")[1:3]) for l in s.split("\n") if l.startswith("| `")]
t = open(sys.argv[1], encoding="utf-8").read().replace("\r\n", "\n")
obs, new = t.split("\n## 신규 시그니처\n", 1)
sp = open(sys.argv[2], encoding="utf-8").read().replace("\r\n", "\n").split("\n## 신규 시그니처\n", 1)[1].split("\n## ", 1)[0]
o, n, want = rows(obs), rows(new), rows(sp)
assert o == [], ("interface card 기존 함수 행이 0이 아니다(spec '관찰 가능한 계약' 토큰이 엔진 def와 겹침)", o)
assert n == want and len(n) == 7 and ("`reachability`", "`SourceIndex.tree`") in n, ("신규 시그니처 표가 spec 표(7행, SourceIndex.tree)와 다르다", n, want)
print("   interface card OK: 기존 함수 0행, 신규 시그니처 %d행 %s" % (len(n), [s for m, s in n]))
EOF
  g add -- "$F_SPEC" "$F_IFC"
  staged_is "$F_SPEC" "$F_IFC"
  test "$(g diff --cached --numstat -- "$F_SPEC" | cut -f2)" = 0
  test "$(g show ":$F_SPEC" | "$PY" -B -c "import sys,hashlib;print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())")" = \
       "$("$PY" -B -c "import sys,hashlib;print(hashlib.sha256(open(sys.argv[1],'rb').read().replace(b'\r\n',b'\n')).hexdigest())" "$DRAFT_SPEC")"   # spec blob = 초안 바이트(LF)
  g commit -q -m "$SUBJ_B" --trailer "Role: doc" --trailer "$COAUTH"
  head_subj_is "$SUBJ_B"
  trailer_is HEAD Role doc; trailer_is HEAD Change-Id -
  st_set B "$(g rev-parse HEAD)"
  say "card OK: $(g rev-parse --short HEAD) (interface $(wc -l < "$R/$F_IFC" | tr -d ' ')줄)"
}

stage_appr() {
  say "appr (C): 승인 기록 $ID(target_kind diff, diff_base = A^, diff_head = B, diff_path 4) -- Role: doc"
  test "$(g rev-parse HEAD)" = "$(st_get B)"
  g diff --cached --quiet
  # 중단 뒤 이어 하기: 승인 기록 파일은 없거나(처음) fill이 같은 내용이라고 확인하는 추적 안 된 파일 하나만
  test -z "$(g status --porcelain --untracked-files=all -- .ai/approvals | grep -vxF "?? $F_APR" || true)"
  local C base head tgt tgt2; C=$(st_get CACHE)
  base=$(st_get GATE_BASE); head=$(st_get B)
  check_apr_draft
  "$PY" -B "$FILL" --root "$R" --draft "$DRAFT_APR" --base "$base" --head "$head" --check > "$STATE.fillcheck.json"
  "$PY" -B -c "import json,sys;r=json.load(open(sys.argv[1],encoding='utf-8'));assert r['result'].startswith('ok') or r['result'].startswith('already-present'),r" "$STATE.fillcheck.json"
  "$PY" -B "$FILL" --root "$R" --draft "$DRAFT_APR" --base "$base" --head "$head" > "$STATE.fill.json"
  "$PY" -B -c "import json,sys;r=json.load(open(sys.argv[1],encoding='utf-8'));assert r['result'] in ('written','already-present(같은 내용)'),r;print('   fill OK',r['result'],r['target'])" "$STATE.fill.json"
  "$PY" -B "$FILL" --root "$R" --draft "$DRAFT_APR" --base "$base" --head "$head" | grep -q 'already-present'   # 멱등
  # target 독립 재계산 두 식(캐시 판 weakening_diff.diff_hash, merge_gate.py diff-hash -- fill은 작업 트리 tools/gates를 읽는다)
  tgt=$("$PY" -B -c "
import sys,re;sys.path.insert(0,sys.argv[1]);import weakening_diff as wd
t=open(sys.argv[5],encoding='utf-8').read().replace('\r\n','\n').split('\n---\n',1)[0]
print(wd.diff_hash(sys.argv[2],sys.argv[3],sys.argv[4],re.findall(r'^diff_path: (.+)\$',t,flags=re.M)))" "$C" "$R" "$base" "$head" "$DRAFT_APR")
  tgt2=$("$PY" -B "$C/merge_gate.py" diff-hash --repo "$R" --base "$base" --head "$head" "$PLAN" "$D05" "$F_IFC" "$F_SPEC")
  test "${#tgt}" = 64; test "$tgt" = "$tgt2"
  "$PY" -B "$C/merge_gate.py" parse-approval "$R/$F_APR" > "$STATE.appr.json"
  "$PY" -B -c "
import json,sys
r=json.load(open(sys.argv[1],encoding='utf-8'))
paths=sys.argv[7:]
exp=dict(id=sys.argv[2],date=sys.argv[6],target_kind='diff',target=sys.argv[3],diff_base=sys.argv[4],diff_head=sys.argv[5],diff_path=paths)
bad={k:(r.get(k),v) for k,v in exp.items() if r.get(k)!=v}
assert not bad,bad
print('   parse_approval_header OK',r['date'],r['target_kind'],r['target'][:12],r['diff_base'][:7],r['diff_head'][:7],len(r['diff_path']))
" "$STATE.appr.json" "$ID" "$tgt" "$base" "$head" "$(st_get APR_DATE)" "$PLAN" "$D05" "$F_IFC" "$F_SPEC"
  check_quote "$R/$F_APR" > /dev/null                                   # 쓴 기록에서도 사용자 원문·date 대조
  # 바이트 단정: BOM 없음, CR 0, HTML 주석·자리표시 0('! grep'은 set -e가 잡지 않고, MSYS2 grep은 CR 하나짜리 패턴을 빈 패턴으로 다룬다 -- 실측)
  "$PY" -B -c "
import sys
b=open(sys.argv[1],'rb').read()
bad=[k for k,v in (('BOM',b.startswith(b'\xef\xbb\xbf')),('CR',b'\r' in b),('주석',b'<!--' in b),('자리표시',b'<rev-parse>' in b or '<승인일'.encode() in b or '<답 라벨>'.encode() in b)) if v]
assert not bad,bad
print('   승인 기록 바이트 OK',len(b))" "$R/$F_APR"
  g add -- "$F_APR"
  staged_is "$F_APR"
  g commit -q -m "$SUBJ_C" \
    -m "사용자 $(st_get APR_DATE) UD-5 \"$UD5_ANS\" 원문과 질문·선택지 원문(세션 jsonl tool_use $ASK_ID 바이트 대조)을 인용. target = weakening_diff.diff_hash(diff_base = 문서 커밋의 부모 $base, diff_head = spec+interface card 커밋 $head, diff_path 4개) = $tgt (merge_gate diff-hash와 같은 값). 강화(옮긴 단위를 이동 원본과 비교 -- 거부 단계 전부 거부, 판정식 불변)." \
    --trailer "Role: doc" --trailer "$COAUTH"
  head_subj_is "$SUBJ_C"
  trailer_is HEAD Role doc; trailer_is HEAD Change-Id -
  st_set TARGET "$tgt"; st_set C "$(g rev-parse HEAD)"
  say "appr OK: $(g rev-parse --short HEAD), target $tgt"
}

stage_final() {
  say "final: push 전 종합 확인(로컬 EL4 receive 포함) -- push는 하지 않는다"
  test "$(g rev-parse HEAD)" = "$(st_get C)"
  local base C GD; base=$(st_get GATE_BASE); C=$(cache_dir); test "$C" = "$(st_get CACHE)"
  test "$(g rev-parse gate/master)" = "$base"                          # gate master가 그사이 움직이지 않았다
  test -z "$(g for-each-ref refs/heads/role/)"
  test "$(g rev-list --count "$base..HEAD")" = 3
  test "$(g rev-list --first-parent "$base..HEAD" | tr '\n' ' ')" = "$(g rev-list "$base..HEAD" | tr '\n' ' ')"   # 병합 없음
  test "$(g log --format=%s "$base..HEAD" | tac | tr '\n' '|')" = "$SUBJ_A|$SUBJ_B|$SUBJ_C|"
  test "$(g diff-tree --no-commit-id --name-only -r "$(st_get A)" | sort | tr '\n' ' ')" = "$(printf '%s\n' "$D05" "$PLAN" | sort | tr '\n' ' ')"
  test "$(g diff-tree --no-commit-id --name-only -r "$(st_get B)" | sort | tr '\n' ' ')" = "$(printf '%s\n' "$F_SPEC" "$F_IFC" | sort | tr '\n' ' ')"
  test "$(g diff-tree --no-commit-id --name-only -r "$(st_get C)")" = "$F_APR"
  local c; for c in $(g rev-list "$base..HEAD"); do trailer_is "$c" Role doc; trailer_is "$c" Change-Id -; done
  # 게이트 변경 조건: 승인 커밋에서만 True(spec card만 있고 승인 기록이 없으면 False, 문서 커밋·base는 spec card도 없음)
  "$PY" -B -c "
import sys;sys.path.insert(0,sys.argv[1]);import merge_gate as mg
v=[mg.gate_change_ok(mg.TreeView(['-C',sys.argv[2]],r),sys.argv[3]) for r in sys.argv[4:]]
assert v==[True,False,False,False],v
print('   gate_change_ok C',v[0],' B',v[1],' A',v[2],' base',v[3])" "$C" "$R" "$ID" "$(st_get C)" "$(st_get B)" "$(st_get A)" "$base"
  "$PY" -B -c "
import sys;sys.path.insert(0,sys.argv[1]);import weakening_diff as wd
hs=wd.approved_hashes(sys.argv[2],sys.argv[3]);assert sys.argv[4] in hs,len(hs)
assert sys.argv[4] not in wd.approved_hashes(sys.argv[2],sys.argv[5])
print('   approved_hashes(C) 포함·(B) 없음',len(hs))" "$C" "$R" "$(st_get C)" "$(st_get TARGET)" "$(st_get B)"
  grep -qx "target: $(st_get TARGET)" "$R/$F_APR"
  grep -qx "diff_base: $base" "$R/$F_APR"; grep -qx "diff_head: $(st_get B)" "$R/$F_APR"
  # V3·V4·V7이 읽는 decision 원소 집합 불변(diff 기록은 원소가 아니다)
  approved_ids "$C" "$(st_get C)" > "$STATE.ids.head"
  cmp "$STATE.ids.base" "$STATE.ids.head"
  "$PY" -B "$PATCH" --root "$R" | grep -q '^already applied'
  test "$(plan_hash "$C")" = "$(st_get PLAN_HASH)"
  test -z "$(g status --porcelain -- docs/ .ai/approvals/)"
  # 로컬 EL4: gate master 판 게이트 코드(캐시)의 merge_gate receive -- 실제 push 때 pre-receive가 돌리는 것과 같은 판정
  GD=$(g rev-parse --path-format=absolute --git-common-dir)
  "$PY" -B "$C/merge_gate.py" receive --git-dir "$GD" --old "$base" --new "$(st_get C)"
  echo "   로컬 EL4 receive(gate master 판 merge_gate) exit 0"
  g log --format='%h %s' "$base..HEAD" | cut -c1-120 | sed 's/^/   /'
  say "final OK -- 오케스트레이터가 단독 호출할 push 명령(EL1 판정 대상, 병렬 호출·tail 금지, 전체 출력 확인):"
  lc_push_cmd "$R"; echo
}

stage_after_push() {
  say "after-push: gate master 대조"
  g fetch -q gate
  test "$(g rev-parse gate/master)" = "$(st_get C)"
  test "$(g rev-parse HEAD)" = "$(g rev-parse gate/master)"
  test "$(g ls-tree --name-only gate/master -- "$F_APR" "$F_SPEC" "$F_IFC" | sort | tr '\n' ' ')" = "$(printf '%s\n' "$F_APR" "$F_SPEC" "$F_IFC" | sort | tr '\n' ' ')"
  test -z "$(g status --porcelain -- docs/ .ai/approvals/)"
  # 게이트 캐시는 gate master 하나만 둔다(ensure_cache 상한, WP-10) -- push 뒤 새 판으로 다시 받고 plan 표 불변 확인
  local C; C=$(cache_dir); test "$(plan_hash "$C")" = "$(st_get PLAN_HASH)"
  "$PY" -B -c "
import sys;sys.path.insert(0,sys.argv[1]);import merge_gate as mg
assert mg.gate_change_ok(mg.TreeView(['-C',sys.argv[2]],'gate/master'),sys.argv[3]) is True
print('   gate_change_ok(gate/master) True')" "$C" "$R" "$ID"
  st_set CACHE "$C"
  say "after-push OK -- 다음은 test worktree(단독 호출, design 05 §12 순서 1, EL1 판정 대상):"
  echo "git -C $R worktree add $W/$ID-test -b role/test/$ID gate/master"
  say "이어서 briefs §1(test-author) → §3.1(auditor freeze·base 표; 산출물은 쓰기만, 커밋하지 않는다 -- 커밋은 순서 7에서 M 위 한 커밋) → code worktree(부모 = T) → §2(code-author) → 병합(전에 git -C $W/$ID-audit log --oneline role/test/$ID..HEAD 출력이 비어야 한다, 아니면 멈춤) → §3.2·3.3 → push role/audit/$ID:master → 정리 → D0a 키트"
}

case "$STEP" in
  kit-cmds) stage_kit_cmds ;;
  pre) stage_pre ;;
  doc) stage_doc ;;
  card) stage_card ;;
  appr) stage_appr ;;
  final) stage_final ;;
  local) stage_pre; stage_doc; stage_card; stage_appr; stage_final ;;
  after-push) stage_after_push ;;
  *) echo "사용: $0 [옵션…] kit-cmds|pre|local|doc|card|appr|final|after-push | --sbx … mk-sandbox" >&2; exit 2 ;;
esac
