#!/usr/bin/env bash
# V3 면제 묶기 card 20260930-v3-exempt-binding 착수 0단계(오케스트레이터) -- Phase 2 DoD 뒤.
# 근거: v3_binding_briefs.md 머리 '착수 0단계'·§4, v3_cards_commit_plan.md §4.0·§4.1 A~C(push 전까지).
# 어느 확인이든 실패하면 그 자리에서 멈춘다(set -Eeuo pipefail + ERR trap). push는 하지 않는다(단독 호출 -- 끝에 명령 출력).
#
#   bash v3_binding_launch.sh pre        # 착수 전 확인 + 0단계 집계 대조(저장소 변경 없음)
#   bash v3_binding_launch.sh local      # pre -> doc -> card -> appr -> final (로컬 커밋 3개, push 안 함)
#   bash v3_binding_launch.sh <단계>     # doc | card | appr | final 하나만(중단 뒤 이어 하기 -- 각 단계가 앞 단계 결과를 확인)
#   bash v3_binding_launch.sh after-push # push 뒤 gate master 대조 + 게이트 캐시 새 판 + test worktree 명령 출력
#
# 사전 시험 옵션(반드시 단계 이름 앞에): --repo <복제본> --state <상태 파일> --wt <worktree 부모> [--tools-ref <커밋>]
#   --repo를 주면 --state·--wt 필수(실제 상태 파일·worktree 부모 보호). 실제 저장소 판별은 launch_common.sh lc_repo_guard(git-common-dir 정규화 비교).
#   --tools-ref: 도구·문서 불변 대조의 기준(기본 = 집계 measured rev). 모래상자의 gate 경로 합성 커밋처럼 tools/가 일부러 다른
#                복제본에서만 쓴다 -- 실제 저장소(별칭 포함)에서 주면 거부.
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
STATE_REAL=$DR/v3_binding_state.txt
STATE=$STATE_REAL
TOOLS_REF=
while [ $# -gt 1 ]; do
  case "$1" in
    --repo) R=$2; shift 2 ;;
    --state) STATE=$2; shift 2 ;;
    --wt) W=$2; shift 2 ;;
    --tools-ref) TOOLS_REF=$2; shift 2 ;;
    *) break ;;
  esac
done
# 단계 이름 뒤에 옵션을 붙이면 조용히 무시돼 실제 저장소에서 돈다(review_post_p10b_runbook B1과 같은 가드) -- 남은 인자는 단계 이름 하나뿐
[ $# -eq 1 ] || { echo "[중단] 사용법: $0 [--repo R --state S --wt W [--tools-ref C]] <단계>  (옵션은 단계 이름 앞에만)" >&2; exit 2; }
case "$1" in --*) echo "[중단] 단계 이름 자리에 옵션: $1 (옵션 값이 빠졌거나 순서가 틀렸다)" >&2; exit 2 ;; esac
lc_repo_guard "$R" "$R_REAL"
if [ "$LC_REAL" = 0 ]; then
  lc_need_sandbox --state "$STATE" "$STATE_REAL"; lc_need_sandbox --wt "$W" "$W_REAL"
else
  [ -z "$TOOLS_REF" ] || { echo "[중단] --tools-ref는 --repo(복제본)와 함께만" >&2; exit 2; }
  lc_need_real --state "$STATE" "$STATE_REAL"; lc_need_real --wt "$W" "$W_REAL"
  STATE=$STATE_REAL; W=$W_REAL
fi
lc_tmp_setup "$STATE"
echo "== 대상 저장소 R=$R  상태 파일 $STATE  worktree 부모 $W"

PY=/c/Python314/python.exe
ID=20260930-v3-exempt-binding
CENSUS=$DR/v3_scripts/v3_decision_census.py
PATCH=$DR/patch_v3_binding_docs.py
FILL=$DR/fill_v3_approval.py
DRAFT_SPEC=$DR/draft_v3_exempt_binding.spec.md
DRAFT_APR=$DR/approval_$ID.md
PLAN=docs/01-plan/features/gain-budget-gmid-sizing.plan.md
D05=docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md
D10=docs/02-design/features/gain-budget-gmid-sizing.10-test-separation.design.md
F_SPEC=docs/02-design/specs/$ID.spec.md
F_IFC=docs/02-design/specs/$ID.interface.md
F_APR=.ai/approvals/$ID.md
STICK=skills/analog-gmid-design/assets/stick_diagram.py
EDS=skills/analog-gmid-design/assets/tests/tools/engine_dup_scan.py
COAUTH="Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
SUBJ_A="docs: $ID 문서 커밋(design 05 §10 V3 ⑤ 면제 원소 = 변이 id@묶기 해시, design 10 §6.7 IC3 382행 원소 형식 이관, 계획 N4.2 V3 면제 묶임 문구)"
SUBJ_B="docs: 게이트 변경 spec card $ID(V3 등가 변이 면제를 변이 id@def 묶기 해시에 묶음, 해시 다름·없음·형식 오류는 exempt_ignored, exempt를 --out에 기록) + interface card"
SUBJ_C="docs: 승인 기록 $ID(A1-a, target_kind diff -- spec card·interface card·design 05 ⑤·design 10 382행·계획 N4.2 V3 면제 문구, 강화)"

say() { printf '%s\n' "== $*"; }
g() { git -C "$R" "$@"; }
st_set() { touch "$STATE"; grep -v "^$1=" "$STATE" > "$STATE.tmp" || true; printf '%s=%s\n' "$1" "$2" >> "$STATE.tmp"; mv "$STATE.tmp" "$STATE"; }
st_get() { local v; v=$(grep "^$1=" "$STATE" | tail -1 | cut -d= -f2-); test -n "$v"; printf '%s' "$v"; }
# 게이트 코드 캐시 = <git-common-dir>/gmid-gate-cache/<gate master 전체 sha>(hook과 같은 ensure_cache)
cache_dir() {
  local c
  c=$("$PY" -B -c "import sys;sys.path.insert(0,sys.argv[1]);import role_paths as rp;print(rp.ensure_cache(rp.load_env(sys.argv[2])))" "$R/tools/gates" "$R")
  test "$(basename "$c")" = "$(g rev-parse gate/master)"
  test -f "$c/interface_card.py"
  printf '%s' "$c"
}
plan_hash() { "$PY" -B "$1/merge_gate.py" plan-tables-hash "$R/$PLAN"; }
staged_is() { test "$(g diff --cached --name-only | sort | tr '\n' ' ')" = "$(printf '%s\n' "$@" | sort | tr '\n' ' ')"; }
numstat_is() { test "$(g diff --cached --numstat -- "$1" | cut -f1-2 | tr '\t' ' ')" = "$2"; }
head_subj_is() { test "$(g log -1 --format=%s)" = "$1"; }
# patch_v3_binding_docs.py JSON 출력의 result 접두와 plan_tables_hash.unchanged 판정
patch_state() { "$PY" -B "$PATCH" --root "$R" "$@" | "$PY" -B -c "
import json,sys
r=json.load(sys.stdin)
u=r.get('plan_tables_hash',{}).get('unchanged')
assert u is True, ('plan_tables_hash', r.get('plan_tables_hash'))
print(r['result'].split('(')[0])"; }
# _approved_ids(<rev>) -- 캐시 판 reachability(읽기 전용)
approved_ids() { "$PY" -B -c "
import sys;sys.path.insert(0,sys.argv[1]);import reachability as r
print('\n'.join(sorted(r._approved_ids(sys.argv[2],sys.argv[3]))))" "$1" "$R" "$2"; }

# 0단계 집계: 초안(승인 기록 '덮는 것' 첫 항목)의 measured rev·수치 = 단일 출처. gate master 집계가 measured rev 집계와
# rev 줄 말고 바이트 단위로 같아야 한다(수치만이 아니라 원소·경로·묶기 해시 앞 16자까지). spec card measured 문장도 같은 수치여야 한다.
census_check() {
  local meas_short meas cur out_m out_c
  meas_short=$(lc_meas_short "$R" "$DRAFT_APR" 'measured at gate `master` `[0-9a-f]\{7,40\}`')   # 단일 출처 규약(마지막 출현, launch_common m8)
  test -n "$meas_short"
  meas=$(g rev-parse --verify "$meas_short^{commit}")
  cur=$(g rev-parse gate/master)
  g merge-base --is-ancestor "$meas" "$cur"
  out_m="$STATE.census.measured.txt"; out_c="$STATE.census.txt"
  "$PY" -B "$CENSUS" --repo "$R" --rev "$meas" --out "$out_m" > /dev/null
  "$PY" -B "$CENSUS" --repo "$R" --rev "$cur" --out "$out_c" > /dev/null
  # (MSYS2에서 프로세스 치환 <(…)은 /dev/fd가 없어 실패한다 -- 실측. 파일로 비교)
  tail -n +2 "$out_m" > "$out_m.body"; tail -n +2 "$out_c" > "$out_c.body"
  diff "$out_m.body" "$out_c.body"                                      # 다르면 멈춤 -> spec card 이행 근거·수치를 다시 쓴다
  "$PY" -B - "$out_c" "$DRAFT_APR" "$DRAFT_SPEC" "$meas_short" <<'EOF'
import re, sys
cen = open(sys.argv[1], encoding="utf-8").read()
apr = open(sys.argv[2], encoding="utf-8").read()
spec = open(sys.argv[3], encoding="utf-8").read()
ms = sys.argv[4]
m = re.search(r"measured at gate `master` `%s`: decision 기록 (\d+), 원소 (\d+), V3 모양 (\d+) = 대상 영역 (\d+) \+ 대상 영역 밖 (\d+)" % ms, apr)
assert m, "승인 초안 measured 문장 형식"
dec, el, v3, ind, outd = map(int, m.groups())
got = (int(re.search(r"^decision 기록 (\d+)$", cen, re.M).group(1)),
       int(re.search(r"^원소\(자체 합집합\) (\d+)  _approved_ids\(<rev>\) (\d+)  같음 True$", cen, re.M).group(1)),
       int(re.search(r"^V3 모양 원소 (\d+)  그중 @ 접미사 있음 0$", cen, re.M).group(1)),   # (나) @ 접미사 0 -- 아니면 매치 실패
       int(re.search(r"대상 영역\(_is_source\) 모듈 (\d+)  대상 밖 (\d+)$", cen, re.M).group(1)),
       int(re.search(r"대상 영역\(_is_source\) 모듈 (\d+)  대상 밖 (\d+)$", cen, re.M).group(2)))
assert got == (dec, el, v3, ind, outd), ("집계가 초안 수치와 다르다", got, (dec, el, v3, ind, outd))
# (가) 대상 영역 V3 모양 원소는 전부 20260922-ic3-v3-exempt의 stick_diagram 원소(기록별 V3 모양 수: ic3 = 대상 영역 수, 나머지 기록 합 = 대상 밖 수)
per = dict((k, int(n)) for k, n in re.findall(r"^  (\S+)\s+원소\s+\d+  V3 모양\s+(\d+)$", cen, re.M))
assert per.get("20260922-ic3-v3-exempt") == ind, per
assert sum(v for k, v in per.items() if k != "20260922-ic3-v3-exempt") == outd, per
dom = re.findall(r"^  (\S+)  -> .*\[V3대상\|", cen, re.M)
assert len(dom) == ind and all(e.startswith("stick_diagram:") for e in dom), dom
# (다) 대상 밖 원소는 모두 _is_source 밖 경로 하나뿐(basename 충돌 없음)
outl = re.findall(r"^  (\S+)  -> (.*)$", cen, re.M)
outl = [(e, r) for e, r in outl if "[V3대상|" not in r]
assert len(outl) == outd and all(";" not in r and "[V3대상밖|" in r for e, r in outl), outl
# spec card measured 문장 = 같은 rev·수치
assert ("**measured at `%s`**" % ms) in spec, "spec card measured rev"
assert ("decision 기록 **%d**, 원소 **%d**" % (dec, el)) in spec and ("V3 모양 **%d** = V3 대상 영역 **%d**" % (v3, ind)) in spec \
    and ("대상 영역 밖 **%d**" % outd) in spec, "spec card measured 수치"
print("census OK measured=%s decision=%d 원소=%d V3모양=%d 대상영역=%d 밖=%d (가)(나)(다) 성립" % (ms, dec, el, v3, ind, outd))
EOF
  st_set MEAS "$meas"
}

stage_pre() {
  say "pre: 착수 전 확인 + 0단계 집계(저장소 변경 없음)"
  test -n "$(git config --get user.email)"
  g fetch gate
  test "$(g rev-parse --abbrev-ref HEAD)" = master
  test "$(g rev-parse HEAD)" = "$(g rev-parse gate/master)"
  test -z "$(g for-each-ref refs/heads/role/)"                        # 역할 브랜치가 있으면 문서 push를 EL1이 거부(design 05 §12)
  if g worktree list --porcelain | grep -q -- "/$ID-"; then echo "$ID worktree가 이미 있다" >&2; false; fi
  g diff --cached --quiet
  test -z "$(g status --porcelain -- docs/ .ai/approvals/)"
  test ! -e "$R/$F_SPEC"; test ! -e "$R/$F_IFC"; test ! -e "$R/$F_APR"
  for f in "$CENSUS" "$PATCH" "$FILL" "$DRAFT_SPEC" "$DRAFT_APR"; do test -s "$f"; done
  test "$(grep -c '<rev-parse>' "$DRAFT_APR")" = 3
  test "$(grep -c '^diff_path: ' "$DRAFT_APR")" = 5
  rm -f "$STATE"
  census_check
  # (다') 도구·엔진 대상 파일·문서 패치 대상·engine_dup_scan 불변(card 줄 번호·해시 앵커·패치 앵커의 전제)
  local ref; ref=${TOOLS_REF:-$(st_get MEAS)}
  [ -z "$TOOLS_REF" ] || echo "   (사전 시험) 불변 대조 기준 = --tools-ref $TOOLS_REF"
  test -z "$(g diff --name-only "$ref" HEAD -- tools/ "$STICK" "$EDS" "$PLAN" "$D05" "$D10")"
  test "$(patch_state --check)" = pending
  local C H; C=$(cache_dir); H=$(plan_hash "$C"); test ${#H} = 64
  st_set GATE_BASE "$(g rev-parse HEAD)"; st_set PLAN_HASH "$H"; st_set CACHE "$C"
  approved_ids "$C" "$(g rev-parse HEAD)" > "$STATE.ids.base"
  st_set N_IDS "$(wc -l < "$STATE.ids.base" | tr -d ' ')"
  say "pre OK: gate master $(g rev-parse --short HEAD), _approved_ids $(st_get N_IDS), plan_tables_hash $H, cache $C"
}

stage_doc() {
  say "doc (A): design 05 ⑤·design 10 382행·계획 N4.2 V3 면제 문구 -- Role: doc"
  test "$(g rev-parse HEAD)" = "$(st_get GATE_BASE)"
  g diff --cached --quiet
  test "$(patch_state --check)" = pending
  test "$(patch_state)" = applied
  test "$(patch_state --check)" = already-applied                     # 재실행 멱등
  g add -- "$PLAN" "$D05" "$D10"
  staged_is "$PLAN" "$D05" "$D10"
  numstat_is "$PLAN" "1 1"; numstat_is "$D05" "1 1"; numstat_is "$D10" "1 1"
  local H; H=$(plan_hash "$(st_get CACHE)"); test "$H" = "$(st_get PLAN_HASH)"   # 판정 표 불변 -> plan_tables 승인 불필요
  g commit -q -m "$SUBJ_A" \
    -m "_drafts/patch_v3_binding_docs.py 적용(spec card $ID 계약 10 문구 그대로, 파일마다 한 줄 교체, 줄 끝 보존). 판정 표 무변경(plan_tables_hash $H). 승인 기록 $ID가 이 커밋의 부모를 diff_base로 가리킨다." \
    --trailer "Role: doc" --trailer "$COAUTH"
  head_subj_is "$SUBJ_A"
  test "$(g rev-parse HEAD^)" = "$(st_get GATE_BASE)"
  st_set A "$(g rev-parse HEAD)"
  say "doc OK: $(g rev-parse --short HEAD)"
}

stage_card() {
  say "card (B): spec card + interface card(게이트 캐시 interface_card.py, 절대 경로) -- Role: doc"
  test "$(g rev-parse HEAD)" = "$(st_get A)"
  g diff --cached --quiet
  local C; C=$(cache_dir); test "$C" = "$(st_get CACHE)"              # gate master가 그사이 움직이지 않았다
  cp "$DRAFT_SPEC" "$R/$F_SPEC"
  "$PY" -B -c "
import sys
sys.path.insert(0, sys.argv[1])
import role_paths as rp, merge_gate as mg
c = rp.parse_spec_card(open(sys.argv[2], encoding='utf-8').read(), sys.argv[3])
assert (c['phase'], c['evidence_type'], c['gate_change'], c['approval']) == ('0.5', 'red-green', 'yes', [sys.argv[3]]), c
po = mg.read_plan_tables(sys.argv[4]).phase_order
assert c['phase'] in po, po
print('parse_spec_card OK', c['phase'], c['evidence_type'], c['gate_change'], c['approval'], len(c['sections']))
" "$C" "$R/$F_SPEC" "$ID" "$R/$PLAN"
  "$PY" -B "$C/interface_card.py" "$R/$F_SPEC" --root "$R" --out "$R/$F_IFC"
  test -s "$R/$F_IFC"
  test "$(grep -c '^| `' "$R/$F_IFC" || true)" = 0                   # 기존 함수·신규 시그니처 0행(게이트 card)
  g add -- "$F_SPEC" "$F_IFC"
  staged_is "$F_SPEC" "$F_IFC"
  test "$(g diff --cached --numstat -- "$F_SPEC" | cut -f2)" = 0
  g commit -q -m "$SUBJ_B" --trailer "Role: doc" --trailer "$COAUTH"
  head_subj_is "$SUBJ_B"
  st_set B "$(g rev-parse HEAD)"
  say "card OK: $(g rev-parse --short HEAD) (interface $(wc -l < "$R/$F_IFC" | tr -d ' ')줄)"
}

stage_appr() {
  say "appr (C): 승인 기록 $ID(target_kind diff, diff_base = A^, diff_head = B) -- Role: doc"
  test "$(g rev-parse HEAD)" = "$(st_get B)"
  g diff --cached --quiet
  test ! -e "$R/$F_APR"
  local C base head tgt; C=$(st_get CACHE)
  base=$(st_get GATE_BASE); head=$(st_get B)
  "$PY" -B "$FILL" --root "$R" --draft "$DRAFT_APR" --base "$base" --head "$head" > "$STATE.fill.json"
  "$PY" -B -c "import json,sys;r=json.load(open(sys.argv[1],encoding='utf-8'));assert r['result']=='written',r;print('fill OK',r['target'])" "$STATE.fill.json"
  # target 독립 재계산(캐시 판 weakening_diff -- fill은 작업 트리 tools/gates를 읽는다)
  tgt=$("$PY" -B -c "
import sys,re;sys.path.insert(0,sys.argv[1]);import weakening_diff as wd
t=open(sys.argv[5],encoding='utf-8').read().split('\n---\n',1)[0]
print(wd.diff_hash(sys.argv[2],sys.argv[3],sys.argv[4],re.findall(r'^diff_path: (.+)\$',t,flags=re.M)))" "$C" "$R" "$base" "$head" "$DRAFT_APR")
  test "${#tgt}" = 64
  "$PY" -B "$C/merge_gate.py" parse-approval "$R/$F_APR" > "$STATE.appr.json"
  "$PY" -B -c "
import json,sys
r=json.load(open(sys.argv[1],encoding='utf-8'))
paths=['$PLAN','$D05','$D10','$F_IFC','$F_SPEC']
exp=dict(id=sys.argv[2],date='2026-10-01',target_kind='diff',target=sys.argv[3],diff_base=sys.argv[4],diff_head=sys.argv[5],diff_path=paths)
bad={k:(r.get(k),v) for k,v in exp.items() if r.get(k)!=v}
assert not bad,bad
print('parse_approval_header OK',r['target_kind'],r['target'][:12],r['diff_base'][:7],r['diff_head'][:7],len(r['diff_path']))
" "$STATE.appr.json" "$ID" "$tgt" "$base" "$head"
  # 바이트 단정: BOM 없음, CR 0, HTML 주석·자리표시 0('! grep'은 set -e가 잡지 않고, MSYS2 grep은 CR 하나짜리 패턴을 빈 패턴으로 다룬다 -- 실측)
  "$PY" -B -c "
import sys
b=open(sys.argv[1],'rb').read()
bad=[k for k,v in (('BOM',b.startswith(b'\xef\xbb\xbf')),('CR',b'\r' in b),('주석',b'<!--' in b),('자리표시',b'<rev-parse>' in b)) if v]
assert not bad,bad
print('승인 기록 바이트 OK',len(b))" "$R/$F_APR"
  g add -- "$F_APR"
  staged_is "$F_APR"
  g commit -q -m "$SUBJ_C" \
    -m "사용자 2026-10-01 A1-a \"승인 (Recommended)\" 원문 인용. target = weakening_diff.diff_hash(diff_base = 문서 커밋의 부모, diff_head = spec+interface card 커밋, diff_path 5개) = $tgt (merge_gate.compute_diff_hash와 같은 값). 강화(면제 적용 범위 축소)." \
    --trailer "Role: doc" --trailer "$COAUTH"
  head_subj_is "$SUBJ_C"
  st_set TARGET "$tgt"; st_set C "$(g rev-parse HEAD)"
  say "appr OK: $(g rev-parse --short HEAD)"
}

stage_final() {
  say "final: push 전 종합 확인"
  test "$(g rev-parse HEAD)" = "$(st_get C)"
  local base C; base=$(st_get GATE_BASE); C=$(st_get CACHE)
  test "$(g rev-parse gate/master)" = "$base"
  test "$(g rev-list --count "$base..HEAD")" = 3
  test "$(g rev-list --first-parent "$base..HEAD" | tr '\n' ' ')" = "$(g rev-list "$base..HEAD" | tr '\n' ' ')"   # 병합 없음
  test "$(g log --format=%s "$base..HEAD" | tac | tr '\n' '|')" = "$SUBJ_A|$SUBJ_B|$SUBJ_C|"
  test "$(g diff-tree --no-commit-id --name-only -r "$(st_get A)" | sort | tr '\n' ' ')" = "$(printf '%s\n' "$PLAN" "$D05" "$D10" | sort | tr '\n' ' ')"
  test "$(g diff-tree --no-commit-id --name-only -r "$(st_get B)" | sort | tr '\n' ' ')" = "$(printf '%s\n' "$F_SPEC" "$F_IFC" | sort | tr '\n' ' ')"
  test "$(g diff-tree --no-commit-id --name-only -r "$(st_get C)")" = "$F_APR"
  local c; for c in $(g rev-list "$base..HEAD"); do
    test "$(g log -1 --format='%(trailers:key=Role,valueonly)' "$c" | tr -d '\r' | grep -c .)" = 1
    test "$(g log -1 --format='%(trailers:key=Role,valueonly)' "$c" | tr -d '\r\n ')" = doc
  done
  # 게이트 변경 조건: 승인 커밋에서만 True(spec card만 있고 승인 기록이 없으면 False)
  "$PY" -B -c "
import sys;sys.path.insert(0,sys.argv[1]);import merge_gate as mg
ok=mg.gate_change_ok(mg.TreeView(['-C',sys.argv[2]],sys.argv[3]),sys.argv[5])
pre=mg.gate_change_ok(mg.TreeView(['-C',sys.argv[2]],sys.argv[4]),sys.argv[5])
assert ok is True and pre is False,(ok,pre)
print('gate_change_ok HEAD',ok,' HEAD~1',pre)" "$C" "$R" "$(st_get C)" "$(st_get B)" "$ID"
  "$PY" -B -c "
import sys;sys.path.insert(0,sys.argv[1]);import weakening_diff as wd
hs=wd.approved_hashes(sys.argv[2],sys.argv[3]);assert sys.argv[4] in hs,len(hs);print('approved_hashes 포함',len(hs))" "$C" "$R" "$(st_get C)" "$(st_get TARGET)"
  grep -qx "target: $(st_get TARGET)" "$R/$F_APR"
  grep -qx "diff_base: $base" "$R/$F_APR"; grep -qx "diff_head: $(st_get B)" "$R/$F_APR"
  # V3·V4·V7이 읽는 decision 원소 집합 불변(diff 기록은 원소가 아니다)
  approved_ids "$C" "$(st_get C)" > "$STATE.ids.head"
  cmp "$STATE.ids.base" "$STATE.ids.head"
  test "$(patch_state --check)" = already-applied
  test "$(plan_hash "$C")" = "$(st_get PLAN_HASH)"
  test -z "$(g status --porcelain -- docs/ .ai/approvals/)"
  g log --format='%h %s' "$base..HEAD"
  say "final OK -- 다음은 push 단독 호출(병렬·tail 금지):  $(lc_push_cmd "$R")"
}

stage_after_push() {
  say "after-push: gate master 대조"
  g fetch gate
  test "$(g rev-parse gate/master)" = "$(st_get C)"
  test "$(g rev-parse HEAD)" = "$(g rev-parse gate/master)"
  test "$(g ls-tree --name-only gate/master -- "$F_APR" "$F_SPEC" "$F_IFC" | sort | tr '\n' ' ')" = "$(printf '%s\n' "$F_APR" "$F_SPEC" "$F_IFC" | sort | tr '\n' ' ')"
  test -z "$(g status --porcelain -- docs/ .ai/approvals/)"
  # 게이트 캐시는 gate master 하나만 둔다(ensure_cache 상한, WP-10) -- push 뒤 새 판으로 다시 받고 plan 표 불변 확인(역할 agent가 쓸 캐시, 8개 스크립트 같은 모양)
  local C; C=$(cache_dir); test "$(plan_hash "$C")" = "$(st_get PLAN_HASH)"
  st_set CACHE "$C"
  say "after-push OK -- 다음은 test worktree(단독 호출, design 05 §12 순서 1):  git -C $R worktree add $W/$ID-test -b role/test/$ID gate/master"
}

case "$1" in
  pre) stage_pre ;;
  doc) stage_doc ;;
  card) stage_card ;;
  appr) stage_appr ;;
  final) stage_final ;;
  local) stage_pre; stage_doc; stage_card; stage_appr; stage_final ;;
  after-push) stage_after_push ;;
  *) echo "사용: $0 [옵션…] pre|local|doc|card|appr|final|after-push" >&2; exit 2 ;;
esac
