#!/usr/bin/env bash
# P10b push 직후 오케스트레이터 절차 -- 문서 커밋 1 + md 일치 card(20261001-topology-md-sync) 커밋 D·승인 기록·spec card.
# 설명서: _drafts/post_p10b_runbook.md. 어느 확인이든 실패하면 그 자리에서 멈춘다(set -euo pipefail + ERR trap).
#
#   bash post_p10b_runbook.sh pre        # 착수 전 확인만(저장소 변경 없음)
#   bash post_p10b_runbook.sh local      # pre -> c1 -> d -> appr -> card -> final (로컬 커밋 4개, push 안 함)
#   bash post_p10b_runbook.sh <단계>     # c1 | d | appr | card | final 하나만(중단 뒤 이어 하기 -- 각 단계가 앞 단계 결과를 확인)
#   (push는 이 스크립트가 하지 않는다 -- 설명서 §5: `git -C <R> push gate master:master` 단독 호출, EL1 판정 대상)
#   bash post_p10b_runbook.sh after-push # push 뒤 gate master 대조 + test worktree 명령 출력
#
# 사전 시험 옵션(단계 앞에): --repo <복제본> --render-tmp <임시 폴더> --state <상태 파일> --wt <worktree 루트>
set -Eeuo pipefail
shopt -s inherit_errexit   # $(...) 안의 실패도 멈춤(cache_dir·st_get의 test)
trap 'echo "[중단] ${BASH_SOURCE[0]}:${LINENO}: ${BASH_COMMAND}" >&2' ERR

# MSYS2 자식 bash는 HOME·APPDATA를 잃는다(실측: HOME=/home/HSLEE -> git user.email 없음, APPDATA 없음 -> 사용자 site-packages 없음)
export HOME=/c/Users/HSLEE
export APPDATA='C:\Users\HSLEE\AppData\Roaming' LOCALAPPDATA='C:\Users\HSLEE\AppData\Local' USERPROFILE='C:\Users\HSLEE'
export PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8   # 자식 bash의 python stdout은 cp949(실측) -- 판정 문자열 비교용

R=/c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
DR=/c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts
W=/c/Users/HSLEE/Documents/Todoc/fpga/wt
T=/c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b47_render
STATE=$DR/post_p10b_state.txt
# 사전 시험용 옵션(환경 변수는 MSYS2 자식 bash에 전달되지 않는다 -- 실측). 실제 실행은 옵션 없이.
while [ $# -gt 1 ]; do
  case "$1" in
    --repo) R=$2; shift 2 ;;
    --render-tmp) T=$2; shift 2 ;;
    --state) STATE=$2; shift 2 ;;
    --wt) W=$2; shift 2 ;;
    *) break ;;
  esac
done
echo "== 대상 저장소 R=$R  상태 파일 $STATE"
PY=/c/Python314/python.exe
ID=20261001-topology-md-sync
P10B=20260930-df23-registry-record
A=skills/analog-gmid-design/assets
L=$A/library
PLAN=docs/01-plan/features/gain-budget-gmid-sizing.plan.md
F_D20=docs/02-design/features/gain-budget-gmid-sizing.20-dead-code-dup.design.md
F_TPL=docs/02-design/specs/_TEMPLATE.spec.md
F_HIS=docs/01-plan/features/gain-budget-gmid-sizing.history.md
F_CTX=.ai/context.md
F_APR=.ai/approvals/20261001-b47-md-sync.md
F_SPEC=docs/02-design/specs/$ID.spec.md
F_IFC=docs/02-design/specs/$ID.interface.md
COAUTH="Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
SUBJ_C1="docs: design 20 §11-1 정정(A2 뒤 DF-19·DF-26 넷 몫 = B26-1~B26-4, MG1과 한 자리 아님), spec card 양식 작성 전 실측 8~13, history H1·H2 2026-09-30~10-01 행, P10·P10b 완료 기록"
SUBJ_D="docs: B47 library topology.md 재생성 $ID(folded_cascode M1/M2 게이트 넷 -- 7ec8eff 극성 정정 반영, current_reuse_telescopic_ota CL/Cf/Cs 수동 소자 6개 -- 8ae82e7 보상망 connectivity 반영), 나머지 4개 md 차이 0"
SUBJ_APR="docs: 승인 기록 20261001-b47-md-sync(B47 md 재생성 + md 일치 test card 진행, decision -- 오케스트레이터 방침 원문과 사용자 답 인용), 사용자 결정 기록"
SUBJ_CARD="docs: md 일치 spec card $ID(library 추적 topology.md 표 <-> json connectivity 영구 계약 test, test-only, approval 20261001-b47-md-sync) + interface card"

say() { printf '%s\n' "== $*"; }
g() { git -C "$R" "$@"; }
st_set() { touch "$STATE"; grep -v "^$1=" "$STATE" > "$STATE.tmp" || true; printf '%s=%s\n' "$1" "$2" >> "$STATE.tmp"; mv "$STATE.tmp" "$STATE"; }
st_get() { local v; v=$(grep "^$1=" "$STATE" | tail -1 | cut -d= -f2-); test -n "$v"; printf '%s' "$v"; }
# 게이트 코드 캐시 = <git-common-dir>/gmid-gate-cache/<gate master 전체 sha>(hook과 같은 ensure_cache). sha가 gate/master와 같아야 한다.
cache_dir() {
  local c
  c=$("$PY" -B -c "import sys;sys.path.insert(0,sys.argv[1]);import role_paths as rp;print(rp.ensure_cache(rp.load_env(sys.argv[2])))" "$R/tools/gates" "$R")
  test "$(basename "$c")" = "$(g rev-parse gate/master)"
  test -f "$c/interface_card.py"
  printf '%s' "$c"
}
plan_hash() { "$PY" -B "$1/merge_gate.py" plan-tables-hash "$R/$PLAN"; }
# 스테이징된 경로 집합이 정확히 인자들과 같다
staged_is() { test "$(g diff --cached --name-only | sort | tr '\n' ' ')" = "$(printf '%s\n' "$@" | sort | tr '\n' ' ')"; }
# numstat "추가 삭제" 단정(스테이징 기준)
numstat_is() { test "$(g diff --cached --numstat -- "$1" | cut -f1-2 | tr '\t' ' ')" = "$2"; }
# .diff.txt의 index 줄(index <before>..<after>)에서 기대 blob 접두를 읽는다
diff_ids() { grep -m1 '^index ' "$DR/$1.diff.txt" | sed -E 's/^index ([0-9a-f]+)\.\.([0-9a-f]+).*/\1 \2/'; }
head_subj_is() { test "$(g log -1 --format=%s)" = "$1"; }

stage_pre() {
  say "pre: 착수 전 확인"
  test -n "$(git config --get user.email)"
  g fetch gate
  test "$(g rev-parse --abbrev-ref HEAD)" = master
  test "$(g rev-parse HEAD)" = "$(g rev-parse gate/master)"            # P10b push 뒤 merge --ff-only gate/master까지 끝난 상태
  test -z "$(g for-each-ref refs/heads/role/)"                        # P10b 정리 끝(역할 브랜치가 있으면 문서 push를 EL1이 거부)
  if g worktree list --porcelain | grep -q -- "$P10B-"; then echo "P10b worktree가 남았다" >&2; false; fi
  local n; n=$(g log --format=%s gate/master | grep -c "^audit: $P10B" || true)
  test "$n" = 1                                                       # P10b 판정 기록이 gate master에 정확히 1개(재시도 1차 기록은 gate에 없다)
  g merge-base --is-ancestor a796468889741bb7eb8da121ffefb0589cb2b769 HEAD
  g diff --cached --quiet
  test -z "$(g status --porcelain -- "$F_D20" "$F_TPL" "$F_HIS" "$F_CTX" "$L" .ai/approvals docs/02-design/specs)"
  test ! -e "$R/$F_APR"; test ! -e "$R/$F_SPEC"; test ! -e "$R/$F_IFC"
  # 재생성 기대 blob(711a5910…/2a3e67a5…)의 전제: a796468 뒤 library·렌더러 불변(비면 통과 -- 비지 않으면 blob·card 계약 9 값을 다시 잰다)
  test -z "$(g diff --name-only a796468889741bb7eb8da121ffefb0589cb2b769 HEAD -- "$L" "$A/topology_to_markdown.py" "$A/stick_diagram.py")"
  # 패치 세 개의 기준 blob이 .diff.txt를 만든 때와 같다(아니면 패치 문안을 다시 본다)
  local b a
  read -r b a <<<"$(diff_ids patch_design20_231)";   [[ "$(g rev-parse "HEAD:$F_D20")" == "$b"* ]]
  read -r b a <<<"$(diff_ids patch_template)";       [[ "$(g rev-parse "HEAD:$F_TPL")" == "$b"* ]]
  read -r b a <<<"$(diff_ids patch_history_groupAB)"; [[ "$(g rev-parse "HEAD:$F_HIS")" == "$b"* ]]
  for f in patch_design20_231.py patch_template.py patch_history_groupAB.py post_p10b_context_append.py \
           approval_20261001-b47-md-sync.md draft_md_sync.final.spec.md; do test -s "$DR/$f"; done
  local C; C=$(cache_dir)
  local H; H=$(plan_hash "$C"); test ${#H} = 64
  rm -f "$STATE"
  st_set GATE_BASE "$(g rev-parse HEAD)"; st_set PLAN_HASH "$H"; st_set CACHE "$C"
  say "pre OK: gate master $(g rev-parse --short HEAD), plan_tables_hash $H, cache $C"
}

stage_c1() {
  say "c1: 설계서 20 §11-1·양식·history 패치 + context(P10·P10b 완료) -- Role: doc, Change-Id 없음"
  test "$(g rev-parse HEAD)" = "$(st_get GATE_BASE)"
  g diff --cached --quiet
  local p out
  for p in patch_design20_231 patch_template patch_history_groupAB; do
    out=$("$PY" -B "$DR/$p.py" --root "$R")
    printf '%s\n' "$out"
    [[ "$out" == 적용:* ]]                                            # '이미 적용'·'중단'이면 멈춘다
  done
  g add -- "$F_D20" "$F_TPL" "$F_HIS"
  local b a
  read -r b a <<<"$(diff_ids patch_design20_231)";   [[ "$(g rev-parse ":$F_D20")" == "$a"* ]]
  read -r b a <<<"$(diff_ids patch_template)";       [[ "$(g rev-parse ":$F_TPL")" == "$a"* ]]
  read -r b a <<<"$(diff_ids patch_history_groupAB)"; [[ "$(g rev-parse ":$F_HIS")" == "$a"* ]]
  numstat_is "$F_D20" "1 1"
  numstat_is "$F_TPL" "6 0"
  numstat_is "$F_HIS" "14 0"
  local C H; C=$(st_get CACHE); H=$(plan_hash "$C"); test "$H" = "$(st_get PLAN_HASH)"   # 판정 표 불변
  local note=()
  if [ -s "$DR/p10b_context_note.txt" ]; then note=(--p10b-note "$DR/p10b_context_note.txt"); fi
  "$PY" -B "$DR/post_p10b_context_append.py" --root "$R" --mode c1 --plan-hash "$H" "${note[@]}"
  g add -- "$F_CTX"
  numstat_is "$F_CTX" "4 0"                                           # 바이너리 append, 삭제 0줄
  staged_is "$F_D20" "$F_TPL" "$F_HIS" "$F_CTX"
  g commit -q -m "$SUBJ_C1" \
    -m "_drafts의 patch_design20_231.py·patch_template.py·patch_history_groupAB.py 적용 -- 기존 바이트 불변(design 20은 231행 한 줄 교체, 양식 +6줄, history H1 +13행·H2 +1행). 판정 표 무변경(plan_tables_hash 전후 동일 $H). .ai/context.md는 바이너리 append(삭제 0줄)." \
    --trailer "Role: doc" --trailer "$COAUTH"
  head_subj_is "$SUBJ_C1"
  test "$(g rev-parse HEAD^)" = "$(st_get GATE_BASE)"
  st_set C1 "$(g rev-parse HEAD)"
  say "c1 OK: $(g rev-parse --short HEAD)"
}

stage_d() {
  say "d: 문서 커밋 D -- 낡은 md 2개 재생성(Role: doc, Change-Id: $ID)"
  test "$(g rev-parse HEAD)" = "$(st_get C1)"
  g diff --cached --quiet
  test -z "$(g status --porcelain -- "$L")"
  local MEAS; MEAS=$(g rev-parse HEAD)                                 # = D^ = card measured_at
  ( cd "$R/$A"
    for n in folded_cascode current_reuse_telescopic_ota; do
      "$PY" -B topology_to_markdown.py "library/$n.topology.json" > /dev/null
    done
    test ! -e "$T"
    mkdir -p "$T"
    for n in ngcc_3stage_ff pushpull_follower_buffer sf_pushpull_output_opamp two_stage_ota_sf; do
      "$PY" -B topology_to_markdown.py "library/$n.topology.json" "$T/$n.topology.md" > /dev/null
      diff --strip-trailing-cr "library/$n.topology.md" "$T/$n.topology.md"   # 차이 0(있으면 멈춤)
    done
    rm -rf "$T" )
  g add -- "$L/folded_cascode.topology.md" "$L/current_reuse_telescopic_ota.topology.md"
  staged_is "$L/folded_cascode.topology.md" "$L/current_reuse_telescopic_ota.topology.md"
  test "$(g rev-parse ":$L/folded_cascode.topology.md")" = 711a59108bd53891ea410963e235617a6955b416
  test "$(g rev-parse ":$L/current_reuse_telescopic_ota.topology.md")" = 2a3e67a5ccef1aae8829688bedaa3098b57d74e2
  test -z "$(g status --porcelain --untracked-files=all -- "$L" "$A/__pycache__" | grep -v '^M  ' || true)"   # library 다른 변경·pycache 0
  numstat_is "$L/folded_cascode.topology.md" "5 5"
  numstat_is "$L/current_reuse_telescopic_ota.topology.md" "12 6"
  g commit -q -m "$SUBJ_D" \
    -m "json connectivity를 고친 두 커밋(8ae82e7 2026-09-10, 7ec8eff 2026-09-17)이 topology_to_markdown.py를 다시 돌리지 않아 md가 낡았다. assets에서 \`python -B topology_to_markdown.py library/<n>.topology.json\`으로 두 파일만 다시 만들었다(folded의 \`소스:\` 줄도 다른 md와 같은 \`library/...\` 형식이 된다). json·엔진·test 불변. 이 md를 읽는 test·게이트·기준선은 없다(판정 불변, DEC-40 무관)." \
    -m "다음 card $ID(test-only)가 md 표와 json의 일치를 영구 test로 잡는다 -- 이 커밋의 부모가 그 card의 measured_at이다." \
    --trailer "Role: doc" --trailer "Change-Id: $ID" --trailer "$COAUTH"
  head_subj_is "$SUBJ_D"
  test "$(g rev-parse HEAD^)" = "$MEAS"
  test "$(g log -1 --format='%(trailers:key=Change-Id,valueonly)' | tr -d '\r\n ')" = "$ID"
  st_set MEASURED_AT "$MEAS"; st_set D "$(g rev-parse HEAD)"
  say "d OK: D $(g rev-parse --short HEAD), measured_at = D^ = $(g rev-parse --short HEAD^)"
}

stage_appr() {
  say "appr: 승인 기록 20261001-b47-md-sync + 사용자 결정 기록(Role: doc, Change-Id 없음 -- card 계약 9 범위 밖)"
  test "$(g rev-parse HEAD)" = "$(st_get D)"
  g diff --cached --quiet
  local C; C=$(st_get CACHE)
  cp "$DR/approval_20261001-b47-md-sync.md" "$R/$F_APR"
  "$PY" -B "$C/merge_gate.py" parse-approval "$R/$F_APR" > "$STATE.appr.json"
  "$PY" -B -c "import json,sys;r=json.load(open(sys.argv[1],encoding='utf-8'));assert r['id']=='20261001-b47-md-sync' and r['target_kind']=='decision' and r['target_list']==['B47-MD-SYNC'] and r['date']=='2026-10-01',r;print('parse_approval_header OK',r['target_kind'],r['target_list'])" "$STATE.appr.json"
  "$PY" -B "$DR/post_p10b_context_append.py" --root "$R" --mode b47 --d-commit "$(st_get D)" --measured-at "$(st_get MEASURED_AT)"
  g add -- "$F_APR" "$F_CTX"
  numstat_is "$F_CTX" "1 0"
  staged_is "$F_APR" "$F_CTX"
  g commit -q -m "$SUBJ_APR" \
    -m "B47 처리 방침(md 2개 재생성 + 일치 test card)을 알린 오케스트레이터 보고(2026-10-01 15:30 KST)와 사용자 답 \"응, 그렇게 진행해\"(15:32), 검토 요약 뒤 같은 답(16:40)을 원문 그대로 옮겼다. 게이트 필수 아님(gate_change no) -- 판정 기록 approvals[] 근거·착수 조건 추적용. Change-Id를 달지 않는다(card 계약 9 범위 밖)." \
    --trailer "Role: doc" --trailer "$COAUTH"
  head_subj_is "$SUBJ_APR"
  test -z "$(g log -1 --format='%(trailers:key=Change-Id,valueonly)' | tr -d '\r\n ')"
  st_set APPR "$(g rev-parse HEAD)"
  say "appr OK: $(g rev-parse --short HEAD)"
}

stage_card() {
  say "card: spec card + interface card(게이트 캐시 interface_card.py, gate master 전체 sha) -- Role: doc, Change-Id: $ID"
  test "$(g rev-parse HEAD)" = "$(st_get APPR)"
  g diff --cached --quiet
  local C; C=$(cache_dir); test "$C" = "$(st_get CACHE)"              # gate master가 그사이 움직이지 않았다
  cp "$DR/draft_md_sync.final.spec.md" "$R/$F_SPEC"
  "$PY" -B -c "
import sys
sys.path.insert(0, sys.argv[1])
import role_paths as rp, merge_gate as mg
c = rp.parse_spec_card(open(sys.argv[2], encoding='utf-8').read(), sys.argv[3])
assert (c['phase'], c['evidence_type'], c['gate_change'], c['approval']) == ('2', 'test-only', 'no', ['20261001-b47-md-sync']), c
po = mg.read_plan_tables(sys.argv[4]).phase_order
assert c['phase'] in po, po
print('parse_spec_card OK', c['phase'], c['evidence_type'], c['gate_change'], c['approval'], len(c['sections']))
" "$C" "$R/$F_SPEC" "$ID" "$R/$PLAN"
  "$PY" -B "$C/interface_card.py" "$R/$F_SPEC" --root "$R" --out "$R/$F_IFC"
  test -s "$R/$F_IFC"
  test "$(grep -c '^| `' "$R/$F_IFC" || true)" = 0                   # 피검 심볼 0행(기존 함수·신규 시그니처 모두)
  g add -- "$F_SPEC" "$F_IFC"
  staged_is "$F_SPEC" "$F_IFC"
  g commit -q -m "$SUBJ_CARD" --trailer "Role: doc" --trailer "Change-Id: $ID" --trailer "$COAUTH"
  head_subj_is "$SUBJ_CARD"
  st_set CARD "$(g rev-parse HEAD)"
  say "card OK: $(g rev-parse --short HEAD)"
}

stage_final() {
  say "final: push 전 종합 확인"
  test "$(g rev-parse HEAD)" = "$(st_get CARD)"
  local base; base=$(st_get GATE_BASE)
  test "$(g rev-parse gate/master)" = "$base"
  test "$(g rev-list --count "$base..HEAD")" = 4
  test "$(g rev-list --first-parent "$base..HEAD" | tr '\n' ' ')" = "$(g rev-list "$base..HEAD" | tr '\n' ' ')"   # 병합 없음
  test "$(g log --format=%s "$base..HEAD" | tac | tr '\n' '|')" = "$SUBJ_C1|$SUBJ_D|$SUBJ_APR|$SUBJ_CARD|"
  # card 계약 9 미리보기: 이 Change-Id 커밋(D·card)의 경로 합집합 - spec/interface = md 2개
  local paths=""
  for c in $(g rev-list "$base..HEAD"); do
    if [ "$(g log -1 --format='%(trailers:key=Change-Id,valueonly)' "$c" | tr -d '\r\n ')" = "$ID" ]; then
      paths="$paths$(g diff-tree --no-commit-id --name-only -r "$c")"$'\n'
    fi
  done
  test "$(printf '%s' "$paths" | grep -v -e "^$F_SPEC\$" -e "^$F_IFC\$" | sort -u | grep -v '^$' | tr '\n' ' ')" = "$L/current_reuse_telescopic_ota.topology.md $L/folded_cascode.topology.md "
  test "$(g diff --name-only "$(st_get MEASURED_AT)" HEAD -- "$L" "$A/topology_to_markdown.py" "$A/stick_diagram.py" | tr '\n' ' ')" = "$L/current_reuse_telescopic_ota.topology.md $L/folded_cascode.topology.md "
  test "$(g diff --numstat "$base" HEAD -- "$F_CTX" | cut -f2)" = 0   # context 삭제 0줄
  test "$(plan_hash "$(st_get CACHE)")" = "$(st_get PLAN_HASH)"
  test -z "$(g status --porcelain -- "$F_D20" "$F_TPL" "$F_HIS" "$F_CTX" "$L" .ai/approvals docs/02-design/specs)"
  g log --format='%h %s' "$base..HEAD"
  say "final OK -- 다음은 push 단독 호출(설명서 §5):  git -C $R push gate master:master"
}

stage_after_push() {
  say "after-push: gate master 대조"
  g fetch gate
  test "$(g rev-parse gate/master)" = "$(st_get CARD)"
  test "$(g rev-parse HEAD)" = "$(g rev-parse gate/master)"
  test -z "$(g status --porcelain -- "$F_CTX" "$L" .ai/approvals docs/02-design/specs)"
  say "after-push OK -- 다음은 test worktree(단독 호출, 설명서 §6):  git -C $R worktree add $W/$ID-test -b role/test/$ID gate/master"
}

case "${1:-}" in
  pre) stage_pre ;;
  c1) stage_c1 ;;
  d) stage_d ;;
  appr) stage_appr ;;
  card) stage_card ;;
  final) stage_final ;;
  local) stage_pre; stage_c1; stage_d; stage_appr; stage_card; stage_final ;;
  after-push) stage_after_push ;;
  *) echo "사용: $0 pre|local|c1|d|appr|card|final|after-push" >&2; exit 2 ;;
esac
