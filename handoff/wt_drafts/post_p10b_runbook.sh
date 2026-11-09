#!/usr/bin/env bash
# P10b push 직후 오케스트레이터 절차 -- 문서 커밋 1 + md 일치 card(20261001-topology-md-sync) 커밋 D·승인 기록·spec card.
# 설명서: _drafts/post_p10b_runbook.md. 어느 확인이든 실패하면 그 자리에서 멈춘다(set -euo pipefail + ERR trap).
#
#   bash post_p10b_runbook.sh pre        # 착수 전 확인만(저장소 변경 없음)
#   bash post_p10b_runbook.sh local      # pre -> c1 -> d -> appr -> card -> e2 -> e2appr -> ubf -> final (로컬 커밋 7개, push 안 함)
#   bash post_p10b_runbook.sh <단계>     # c1 | d | appr | card | e2 | e2appr | ubf | final 하나만(중단 뒤 이어 하기 -- 각 단계가 앞 단계 결과를 확인)
#   (v2, 2026-10-01: md 일치 card 단계 뒤에 Q-P2DOD-E2 문구 정정 커밋 e2 + 그 승인 기록 e2appr, U-BF 승인 기록 ubf를 더함)
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
# 단계 이름 뒤에 옵션을 붙이면 조용히 무시돼 실제 저장소에서 돈다(review_post_p10b_runbook B1) -- 남은 인자는 단계 이름 하나뿐이어야 한다
[ $# -eq 1 ] || { echo "[중단] 사용법: $0 [--repo R --state S --render-tmp T [--wt W]] <단계>  (옵션은 단계 이름 앞에만)" >&2; exit 2; }
# --repo를 주면(사전 시험) 상태 파일·렌더 임시 경로도 반드시 따로 준다 -- 실제 상태 파일을 지우지 않게
if [ "$R" != /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills ]; then
  [ "$STATE" != "$DR/post_p10b_state.txt" ] || { echo "[중단] --repo 사용 시 --state 필수" >&2; exit 2; }
  [ "$T" != "$DR/b47_render" ] || { echo "[중단] --repo 사용 시 --render-tmp 필수" >&2; exit 2; }
fi
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
# v2: Q-P2DOD-E2 문구 정정(사용자 2026-10-01 "문구 정정 (Recommended)") + U-BF 승인 기록(사용자 2026-10-01 "결함으로 고침 (Recommended)")
E2ID=20261001-p2dod-e2-wording
UBFID=20261001-b26-backfill-interdig-fix
F_APR_E2=.ai/approvals/$E2ID.md
F_APR_UBF=.ai/approvals/$UBFID.md
SUBJ_E2="docs: design 20 §10 E2 통과 기준 정정(exit 0, 면제되지 않은 발견 0 -- 면제 = decision 승인 기록의 path::rule, 현재 20260929-p4-scan-exempt 1건, Q-P2DOD-E2)"
SUBJ_E2APR="docs: 승인 기록 $E2ID(Q-P2DOD-E2 design 20 §10 E2 문구 정정, diff -- 사용자 답과 질문 원문 인용)"
SUBJ_UBF="docs: 승인 기록 $UBFID(U-BF relaxed_pairs interdig_ok를 정리 뒤 반환 audit 3b로 채우는 수정, decision -- 사용자 답과 질문 원문 인용)"

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
           approval_20261001-b47-md-sync.md draft_md_sync.final.spec.md \
           patch_e2_wording.py fill_v3_approval.py "approval_$E2ID.md" "approval_$UBFID.md"; do test -s "$DR/$f"; done
  # v2: E2 문구 정정 대상 줄(OLD)이 정확히 하나 남아 있다(이미 적용·문구 바뀜이면 멈춘다), 새 승인 기록 두 개는 아직 없다
  test "$("$PY" -B "$DR/patch_e2_wording.py" "$R" --check)" = pending
  test ! -e "$R/$F_APR_E2"; test ! -e "$R/$F_APR_UBF"
  test "$(grep -c '<rev-parse>' "$DR/approval_$E2ID.md")" = 3
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

stage_e2() {
  say "e2: design 20 §10 E2 통과 기준 문구 정정(patch_e2_wording.py) -- Role: doc, Change-Id: $E2ID"
  test "$(g rev-parse HEAD)" = "$(st_get CARD)"
  g diff --cached --quiet
  test -z "$(g status --porcelain -- "$F_D20")"
  local out
  out=$("$PY" -B "$DR/patch_e2_wording.py" "$R" --check); test "$out" = pending
  out=$("$PY" -B "$DR/patch_e2_wording.py" "$R"); printf '%s\n' "$out"; test "$out" = applied
  out=$("$PY" -B "$DR/patch_e2_wording.py" "$R" --check); test "$out" = already-applied   # NEW 줄 1개·OLD 줄 0개
  g add -- "$F_D20"
  staged_is "$F_D20"
  numstat_is "$F_D20" "1 1"
  test "$(g diff --cached -U0 -- "$F_D20" | grep -c -E '^[-+]\| E2 \|' || true)" = 2      # 바뀐 줄은 E2 행 하나(-1 +1)
  local C H; C=$(st_get CACHE); H=$(plan_hash "$C"); test "$H" = "$(st_get PLAN_HASH)"   # 계획 판정 표 불변
  g commit -q -m "$SUBJ_E2" \
    -m "_drafts/patch_e2_wording.py 적용 -- design 20 §10 E2 행 '통과 기준' 칸 한 줄만 교체(줄 끝 보존). 옛 \"exit 0, 발견 0\"(2026-09-23)은 그 뒤 승인된 스캐너 면제(20260929-p4-scan-exempt, 2026-09-29)와 스캐너 계약(P4 spec card 20260929-probe-engine-dup 계약 1 -- 면제 줄도 발견으로 출력하고 exempt true를 붙여 exit 판정에서 뺀다)과 어긋났다. 사용자 결정 Q-P2DOD-E2 \"문구 정정 (Recommended)\"(2026-10-01). 새 면제를 더하지 않는다. 승인 기록 $E2ID가 이 커밋을 diff_head로 가리킨다. 판정 표 무변경(plan_tables_hash $H)." \
    --trailer "Role: doc" --trailer "Change-Id: $E2ID" --trailer "$COAUTH"
  head_subj_is "$SUBJ_E2"
  test "$(g rev-parse HEAD^)" = "$(st_get CARD)"
  test "$(g log -1 --format='%(trailers:key=Change-Id,valueonly)' | tr -d '\r\n ')" = "$E2ID"
  st_set E2 "$(g rev-parse HEAD)"
  say "e2 OK: $(g rev-parse --short HEAD)"
}

stage_e2appr() {
  say "e2appr: 승인 기록 $E2ID(target_kind diff, target = weakening_diff.diff_hash(E2^, E2, design 20)) -- Role: doc, Change-Id 없음"
  test "$(g rev-parse HEAD)" = "$(st_get E2)"
  g diff --cached --quiet
  test ! -e "$R/$F_APR_E2"
  local C base head tgt; C=$(st_get CACHE)
  base=$(g rev-parse "$(st_get E2)^"); head=$(g rev-parse "$(st_get E2)")
  # 초안의 <rev-parse> 세 자리를 채워 .ai/approvals/<id>.md를 쓴다(기존 도구: weakening_diff.diff_hash와 merge_gate.compute_diff_hash 대조, 파싱 확인)
  "$PY" -B "$DR/fill_v3_approval.py" --root "$R" --draft "$DR/approval_$E2ID.md" --base "$base" --head "$head" > "$STATE.e2fill.json"
  "$PY" -B -c "import json,sys;r=json.load(open(sys.argv[1],encoding='utf-8'));assert r['result']=='written',r;print('fill OK',r['target'])" "$STATE.e2fill.json"
  # target 독립 재계산(지시된 명령 그대로: 저장소 루트에서 PYTHONPATH=tools/gates)
  tgt=$(cd "$R" && PYTHONPATH=tools/gates "$PY" -B -c "import weakening_diff; print(weakening_diff.diff_hash('.', '$base', '$head', ['$F_D20']))")
  test "${#tgt}" = 64
  "$PY" -B "$C/merge_gate.py" parse-approval "$R/$F_APR_E2" > "$STATE.e2appr.json"
  "$PY" -B -c "
import json,sys
r=json.load(open(sys.argv[1],encoding='utf-8'))
exp=dict(id=sys.argv[2],date='2026-10-01',target_kind='diff',target=sys.argv[3],diff_base=sys.argv[4],diff_head=sys.argv[5],diff_path=[sys.argv[6]])
bad={k:(r.get(k),v) for k,v in exp.items() if r.get(k)!=v}
assert not bad,bad
print('parse_approval_header OK',r['target_kind'],r['target'][:12],r['diff_base'][:7],r['diff_head'][:7],r['diff_path'])
" "$STATE.e2appr.json" "$E2ID" "$tgt" "$base" "$head" "$F_D20"
  g add -- "$F_APR_E2"
  staged_is "$F_APR_E2"
  g commit -q -m "$SUBJ_E2APR" \
    -m "Q-P2DOD-E2 사용자 답 \"문구 정정 (Recommended)\"(2026-10-01 19:25 KST)과 질문 원문·선택지를 그대로 옮겼다. target = weakening_diff.diff_hash(diff_base = 정정 커밋의 부모, diff_head = 정정 커밋, design 20) = $tgt (merge_gate.compute_diff_hash와 같은 값). Phase 2 완료 판정(DoD) 착수 조건: 이 기록과 정정 커밋이 DoD 측정 판 H의 조상. Change-Id를 달지 않는다(선례 2d58fd8)." \
    --trailer "Role: doc" --trailer "$COAUTH"
  head_subj_is "$SUBJ_E2APR"
  test -z "$(g log -1 --format='%(trailers:key=Change-Id,valueonly)' | tr -d '\r\n ')"
  st_set E2TARGET "$tgt"; st_set E2APPR "$(g rev-parse HEAD)"
  say "e2appr OK: $(g rev-parse --short HEAD)"
}

stage_ubf() {
  say "ubf: 승인 기록 $UBFID(target_kind decision, U-BF) -- Role: doc, Change-Id 없음"
  test "$(g rev-parse HEAD)" = "$(st_get E2APPR)"
  g diff --cached --quiet
  test ! -e "$R/$F_APR_UBF"
  local C; C=$(st_get CACHE)
  cp "$DR/approval_$UBFID.md" "$R/$F_APR_UBF"
  "$PY" -B "$C/merge_gate.py" parse-approval "$R/$F_APR_UBF" > "$STATE.ubf.json"
  "$PY" -B -c "import json,sys;r=json.load(open(sys.argv[1],encoding='utf-8'));assert r['id']==sys.argv[2] and r['target_kind']=='decision' and r['target_list']==['U-BF-BACKFILL-INTERDIG'] and r['date']=='2026-10-01' and r['diff_path']==[],r;print('parse_approval_header OK',r['target_kind'],r['target_list'])" "$STATE.ubf.json" "$UBFID"
  g add -- "$F_APR_UBF"
  staged_is "$F_APR_UBF"
  g commit -q -m "$SUBJ_UBF" \
    -m "U-BF 사용자 답 \"결함으로 고침 (Recommended)\"(2026-10-01 19:19 KST)과 사용자에게 보인 질문 원문·선택지를 그대로 옮겼다(배경 전체는 준비 문서 _drafts/b26_backfill_question.md). 이 기록이 code card 20261001-b26-backfill-interdig-final-audit test의 판정 기준(oracle (d))이고, 순서는 b26pre test card 뒤·B26-1 앞. 게이트 필수 아님. Change-Id를 달지 않는다." \
    --trailer "Role: doc" --trailer "$COAUTH"
  head_subj_is "$SUBJ_UBF"
  test -z "$(g log -1 --format='%(trailers:key=Change-Id,valueonly)' | tr -d '\r\n ')"
  st_set UBF "$(g rev-parse HEAD)"
  say "ubf OK: $(g rev-parse --short HEAD)"
}

stage_final() {
  say "final: push 전 종합 확인"
  test "$(g rev-parse HEAD)" = "$(st_get UBF)"
  local base; base=$(st_get GATE_BASE)
  test "$(g rev-parse gate/master)" = "$base"
  test "$(g rev-list --count "$base..HEAD")" = 7
  test "$(g rev-list --first-parent "$base..HEAD" | tr '\n' ' ')" = "$(g rev-list "$base..HEAD" | tr '\n' ' ')"   # 병합 없음
  test "$(g log --format=%s "$base..HEAD" | tac | tr '\n' '|')" = "$SUBJ_C1|$SUBJ_D|$SUBJ_APR|$SUBJ_CARD|$SUBJ_E2|$SUBJ_E2APR|$SUBJ_UBF|"
  # v2: E2 Change-Id 커밋은 정확히 하나(e2)이고 design 20만 바꾼다, 승인 기록 diff_head = 그 커밋, 승인 두 개의 경로·내용 확인
  local e2c; e2c=$(for c in $(g rev-list "$base..HEAD"); do [ "$(g log -1 --format='%(trailers:key=Change-Id,valueonly)' "$c" | tr -d '\r\n ')" = "$E2ID" ] && echo "$c"; done; true)
  test "$e2c" = "$(st_get E2)"
  test "$(g diff-tree --no-commit-id --name-only -r "$e2c")" = "$F_D20"
  test "$("$PY" -B "$DR/patch_e2_wording.py" "$R" --check)" = already-applied
  test "$(g diff-tree --no-commit-id --name-only -r "$(st_get E2APPR)")" = "$F_APR_E2"
  test "$(g diff-tree --no-commit-id --name-only -r "$(st_get UBF)")" = "$F_APR_UBF"
  grep -qx "diff_head: $e2c" "$R/$F_APR_E2"
  grep -qx "target: $(st_get E2TARGET)" "$R/$F_APR_E2"
  g merge-base --is-ancestor "$e2c" HEAD; g merge-base --is-ancestor "$(st_get E2APPR)" HEAD
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
  test "$(g rev-parse gate/master)" = "$(st_get UBF)"
  test "$(g rev-parse HEAD)" = "$(g rev-parse gate/master)"
  g merge-base --is-ancestor "$(st_get E2)" gate/master; g merge-base --is-ancestor "$(st_get E2APPR)" gate/master
  # ('<rev>:.ai/…' 인자는 MSYS2가 경로 목록으로 바꿔 깨진다 -- 실측. ls-tree로 확인)
  test "$(g ls-tree --name-only gate/master -- "$F_APR_E2" "$F_APR_UBF" | sort | tr '\n' ' ')" = "$(printf '%s\n' "$F_APR_E2" "$F_APR_UBF" | sort | tr '\n' ' ')"
  test -z "$(g status --porcelain -- "$F_CTX" "$L" .ai/approvals docs/02-design/specs)"
  say "after-push OK -- 다음은 test worktree(단독 호출, 설명서 §6):  git -C $R worktree add $W/$ID-test -b role/test/$ID gate/master"
}

case "${1:-}" in
  pre) stage_pre ;;
  c1) stage_c1 ;;
  d) stage_d ;;
  appr) stage_appr ;;
  card) stage_card ;;
  e2) stage_e2 ;;
  e2appr) stage_e2appr ;;
  ubf) stage_ubf ;;
  final) stage_final ;;
  local) stage_pre; stage_c1; stage_d; stage_appr; stage_card; stage_e2; stage_e2appr; stage_ubf; stage_final ;;
  after-push) stage_after_push ;;
  *) echo "사용: $0 pre|local|c1|d|appr|card|e2|e2appr|ubf|final|after-push" >&2; exit 2 ;;
esac
