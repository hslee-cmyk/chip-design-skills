#!/usr/bin/env bash
# B33 게이트 card 20260930-v7-registry-edges 착수 0단계(오케스트레이터) -- 34·35·B34·B26pre·backfill·B26-1 병합 뒤, Phase 3(G1) 앞.
# 근거: b33_briefs.md §0.6(착수 직전 재확인 1~8)·§0.7(명령 시퀀스 A~C)·§4, draft_b33.final.spec.md '작성 전 실측'.
# 구조는 v3_binding_launch.sh를 따른다(단계별 함수, 옵션은 단계 이름 앞, measured rev 단일 출처, 불변 대조, 게이트 캐시 절대 경로,
# push는 하지 않음 -- 끝에 단독 호출 명령 출력). 어느 확인이든 실패하면 그 자리에서 멈춘다(set -Eeuo pipefail + ERR trap).
#
#   bash b33_launch.sh kit-cmds   # 착수 때 재측정 명령 출력(실행 안 함 -- 머리 수치·공격 33·34/35 무동작 미리보기)
#   bash b33_launch.sh pre        # 착수 전 확인 + 머리 수치 대조(저장소 변경 없음)
#   bash b33_launch.sh local      # pre -> doc -> card -> appr -> final (로컬 커밋 3개, push 안 함)
#   bash b33_launch.sh <단계>     # doc | card | appr | final 하나만(중단 뒤 이어 하기 -- 각 단계가 앞 단계 결과를 확인)
#   bash b33_launch.sh after-push # push 뒤 gate master 대조 + test worktree 명령 출력
#
# measured rev 단일 출처 = spec card 초안 '작성 전 실측'의 마지막 '(착수…' 문단(`gate master \`<rev>\``)과 그 문단의 수치.
#   pre는 (1) 그 rev와 gate master 사이 V7 그래프 입력(GRAPH_PREFIXES·reachability.py·.ai/verification·reachability_roots)이 같고
#   (2) 머리 수치 출력(<HL>/head.txt 첫 줄 = 그 rev)이 문단 수치와 전부 같을 때만 통과한다. 다르면 멈춘다 -> kit-cmds로 gate master에서
#   다시 재고, 초안 문단을 새 rev·수치로 다시 쓴다(사실 문장 재측정 -- 그 형식은 아래 HL_RE의 문장 그대로).
#
# 사전 시험 옵션(반드시 단계 이름 앞에):
#   --repo <복제본> --state <상태 파일>   복제본에서만(실제 상태 파일 보호)
#   --draft-spec <파일>                   spec card 초안 대신(복제본 전용 -- 문단을 모래상자 rev로 고친 사본)
#   --pred-missing-ok                     선행 card 판정 기록이 없어도 진행(복제본 전용 -- 선행 병합 전 rev의 사전 시험)
#   --headline <디렉터리>                 머리 수치 출력(기본 $DR/b33_kit/out/head_<measured rev 7자>)
set -Eeuo pipefail
shopt -s inherit_errexit
trap 'echo "[중단] ${BASH_SOURCE[0]}:${LINENO}: ${BASH_COMMAND}" >&2' ERR

# MSYS2 자식 bash는 HOME·APPDATA를 잃는다(post_p10b_runbook.sh와 같은 실측)
export HOME=/c/Users/HSLEE
export APPDATA='C:\Users\HSLEE\AppData\Roaming' LOCALAPPDATA='C:\Users\HSLEE\AppData\Local' USERPROFILE='C:\Users\HSLEE'
export PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8

R_REAL=/c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
R=$R_REAL
W=/c/Users/HSLEE/Documents/Todoc/fpga/wt
DR=$W/_drafts
KIT=$DR/b33_kit
STATE_REAL=$DR/b33_launch_state.txt
STATE=$STATE_REAL
DRAFT_SPEC_REAL=$DR/draft_b33.final.spec.md
DRAFT_SPEC=$DRAFT_SPEC_REAL
PRED_MISSING_OK=
HL=
while [ $# -gt 1 ]; do
  case "$1" in
    --repo) R=$2; shift 2 ;;
    --state) STATE=$2; shift 2 ;;
    --draft-spec) DRAFT_SPEC=$2; shift 2 ;;
    --headline) HL=$2; shift 2 ;;
    --pred-missing-ok) PRED_MISSING_OK=1; shift ;;
    *) break ;;
  esac
done
# 단계 이름 뒤에 옵션을 붙이면 조용히 무시돼 실제 저장소에서 돈다(review_post_p10b_runbook B1과 같은 가드) -- 남은 인자는 단계 이름 하나뿐
[ $# -eq 1 ] || { echo "[중단] 사용법: $0 [--repo R --state S [--draft-spec F] [--pred-missing-ok]] [--headline D] <단계>  (옵션은 단계 이름 앞에만)" >&2; exit 2; }
case "$1" in --*) echo "[중단] 단계 이름 자리에 옵션: $1 (옵션 값이 빠졌거나 순서가 틀렸다)" >&2; exit 2 ;; esac
if [ "$R" != "$R_REAL" ]; then
  [ "$STATE" != "$STATE_REAL" ] || { echo "[중단] --repo 사용 시 --state 필수(실제 상태 파일 보호)" >&2; exit 2; }
else
  [ "$STATE" = "$STATE_REAL" ] || { echo "[중단] 실제 저장소에서는 --state를 바꾸지 않는다" >&2; exit 2; }
  [ "$DRAFT_SPEC" = "$DRAFT_SPEC_REAL" ] || { echo "[중단] --draft-spec은 --repo(복제본)와 함께만" >&2; exit 2; }
  [ -z "$PRED_MISSING_OK" ] || { echo "[중단] --pred-missing-ok는 --repo(복제본)와 함께만" >&2; exit 2; }
fi
echo "== 대상 저장소 R=$R  상태 파일 $STATE  spec 초안 $DRAFT_SPEC"

PY=/c/Python314/python.exe
ID=20260930-v7-registry-edges
PATCH=$DR/patch_b33_design05.py
FILL=$DR/fill_v3_approval.py
DRAFT_APR=$DR/approval_$ID.md
IFC_REF=$KIT/out/sim_0f23786/interface.md          # 착수 키트 모의(0f23786)에서 게이트 캐시 interface_card.py가 만든 것(briefs §0.5)
PLAN=docs/01-plan/features/gain-budget-gmid-sizing.plan.md
D05=docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md
F_SPEC=docs/02-design/specs/$ID.spec.md
F_IFC=docs/02-design/specs/$ID.interface.md
F_APR=.ai/approvals/$ID.md
RCH=tools/gates/reachability.py
MUT=tools/gates/mutate_changed.py
RT=tools/gates/redteam/lib/rt.py
SR=skills/analog-gmid-design/assets/sizing_recipe.py
EXEMPT_APR=.ai/approvals/20260930-restore-unwired-until-6a.md   # 면제 두 id(card '덮지 않는 것' -- 미도달 유지)
# 확정 card 순서(briefs 머리, decision_package §1 Q-B34-PHASE): B33 앞 card의 판정 기록이 gate master에 있어야 한다
PRED="20260930-v3-exempt-binding 20260930-v3-changed-stmt-scope 20260930-b34-grammar-explicit 20260930-b26-pre-test-strengthen 20261001-b26-backfill-interdig-final-audit 20260930-b26-rail-accessor-set"
COAUTH="Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
SUBJ_A="docs: $ID 문서 커밋(design 05 §10 V7 행 그래프 규칙 명시 -- 레지스트리 바인딩 네 형식·생성자 호출 위치·dunder 폴백 제거·소스 노드 안 도달, 거부 증명 줄 공격 33)"
SUBJ_B="docs: 게이트 변경 spec card $ID(V7 정적 호출 그래프 -- R1 레지스트리 바인딩, R2 생성자 호출 위치만, R2' dunder 폴백 제거, R3 소스 노드 안 도달) + interface card"
SUBJ_C="docs: 승인 기록 $ID(B33 게이트 변경 승인 + Q1 (a) 호출 위치만, target_kind diff -- spec card·interface card·design 05 V7 행·거부 증명 줄)"

say() { printf '%s\n' "== $*"; }
g() { git -C "$R" "$@"; }
st_set() { touch "$STATE"; grep -v "^$1=" "$STATE" > "$STATE.tmp" || true; printf '%s=%s\n' "$1" "$2" >> "$STATE.tmp"; mv "$STATE.tmp" "$STATE"; }
st_get() { local v; v=$(grep "^$1=" "$STATE" | tail -1 | cut -d= -f2-); test -n "$v"; printf '%s' "$v"; }
# 게이트 코드 캐시 = <git-common-dir>/gmid-gate-cache/<gate master 전체 sha>(hook과 같은 ensure_cache)
cache_dir() {
  local c
  c=$("$PY" -B -c "import sys;sys.path.insert(0,sys.argv[1]);import role_paths as rp;print(rp.ensure_cache(rp.load_env(sys.argv[2])))" "$R/tools/gates" "$R")
  test "$(basename "$c")" = "$(g rev-parse gate/master)"
  test -f "$c/interface_card.py"; test -f "$c/reachability.py"
  printf '%s' "$c"
}
plan_hash() { "$PY" -B "$1/merge_gate.py" plan-tables-hash "$R/$PLAN"; }
staged_is() { test "$(g diff --cached --name-only | sort | tr '\n' ' ')" = "$(printf '%s\n' "$@" | sort | tr '\n' ' ')"; }
numstat_is() { test "$(g diff --cached --numstat -- "$1" | cut -f1-2 | tr '\t' ' ')" = "$2"; }
head_subj_is() { test "$(g log -1 --format=%s)" = "$1"; }
# _approved_ids(<rev>) -- 캐시 판 reachability(읽기 전용)
approved_ids() { "$PY" -B -c "
import sys;sys.path.insert(0,sys.argv[1]);import reachability as r
print('\n'.join(sorted(r._approved_ids(sys.argv[2],sys.argv[3]))))" "$1" "$R" "$2"; }
# spec card 초안 '작성 전 실측' 마지막 '(착수…' 문단의 measured rev(짧은 형)
meas_short() { "$PY" -B - "$DRAFT_SPEC" <<'EOF'
import re, sys
t = open(sys.argv[1], encoding="utf-8").read().replace("\r\n", "\n")
sec = t.split("\n## 작성 전 실측\n", 1)[1].split("\n## ", 1)[0].split("\n")
starts = [i for i, l in enumerate(sec) if l.startswith("(착수")]
assert starts, "'(착수…' 문단 없음"
m = re.search(r"gate master `([0-9a-f]{7,40})`", sec[starts[-1]])
assert m, "마지막 '(착수…' 문단 첫 줄에 gate master `<rev>` 없음"
print(m.group(1))
EOF
}

# 머리 수치 대조: <HL>(run_headline.sh 출력)이 measured rev에서 잰 것이고, 그 수치가 초안 문단 수치와 전부 같다.
headline_check() {
  local meas=$1 hl=$2 exempt
  test -s "$hl/head.txt" && test -s "$hl/m1.jsonl" && test -s "$hl/m4.jsonl"
  test "$(head -1 "$hl/head.txt")" = "HEAD $meas"
  exempt=$(g show "HEAD:$EXEMPT_APR" | grep '^target: ' | head -1 | cut -d' ' -f2- | tr -d '\r')
  test -n "$exempt"
  "$PY" -B - "$hl" "$DRAFT_SPEC" "$exempt" <<'EOF'
import json, re, sys
hl, spec, exempt = sys.argv[1:4]
exempt = [x.strip() for x in exempt.split(",") if x.strip()]
rows = lambda p: [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
m1 = rows(hl + "/m1.jsonl")
setup = [o for o in m1 if o["what"] == "setup"][-1]
var = {o["variant"]: o for o in m1 if o["what"] == "variant"}
mono = {o["variant"]: o for o in m1 if o["what"] == "monotone"}
dinv = [o for o in m1 if o["what"] == "diff_inventory0"][-1]
b, f, mf = var["base"], var["fixed"], mono["fixed"]
r4 = rows(hl + "/m4.jsonl")
scan = [o for o in r4 if o["what"] == "scan"][-1]
pairs = [o for o in r4 if o["what"] == "pair"]
# 불변식(briefs §0.6 ③): 하나라도 어긋나면 card 사실 문장 전체 재측정
inv = {
    "edges_equal_head_tool": b.get("edges_equal_head_tool") is True,
    "개정 미도달 ⊆ base 미도달(R3)": set(f["unreached_list_union+R3"]) <= set(b["unreached_list_union+R3"]),
    "인벤토리 0 회귀 0": dinv["fixed_minus_base"] == [],
    "옛 간선 제거 전부 dunder": mf["missing_all_dunder_targets"] is True,
    "면제 id 도달 0(R3)": f["exempt_reached_union+R3"] == [],
    "면제 두 id 미도달 유지": all(e in f["unreached_list_union+R3"] for e in exempt) and len(exempt) == 2,
    "m4 완료(쌍 수 = 스캔)": len(pairs) == scan["distinct_pairs"],
    "m4 not_same_or_error 0": not [o for o in pairs if "error" in o or not o.get("same_fixed")],
    "m4 base verdict 전부 PASS": {o["base"]["verdict"] for o in pairs} == {"PASS"},
    "m4 --config 전부 head 트리": {o.get("config_from_head") for o in pairs} == {True},
}
bad = [k for k, v in inv.items() if not v]
lost = sum(len(v) for d in ("src_defs_lost_reach_noR3", "src_defs_lost_reach_R3") for v in mf[d].values())
got = {
    "base": (b["unreached_union"], b["unreached_union+R3"], b["unreached_before_phase3+R3"], b["unreached_after_phase3+R3"]),
    "fixed": (f["unreached_union+R3"], f["unreached_before_phase3+R3"], f["unreached_after_phase3+R3"]),
    "leak": (b["nonsource_reached_union"], f["nonsource_reached_union+R3"]),
    "v3": (setup["test_nodes"], b["v3_pairs"], f["v3_pairs"], "%.2f" % (f["v3_pairs"] / b["v3_pairs"])),
    "inv0": (b["v3_inventory0_n"], f["v3_inventory0_n"], len(dinv["fixed_minus_base"])),
    "median": (b["v3_median"], f["v3_median"]),
    "old_edges": (mf["missing_old_edges"], lost),
    "records": (scan["distinct_pairs"],),
}
# 초안 문단(단일 출처) -- 문장 형식은 0f23786 '착수 키트 재측정' 문단 그대로
t = open(spec, encoding="utf-8").read().replace("\r\n", "\n")
sec = t.split("\n## 작성 전 실측\n", 1)[1].split("\n## ", 1)[0].split("\n")
i0 = [i for i, l in enumerate(sec) if l.startswith("(착수")][-1]
j = next((j for j in range(i0 + 1, len(sec)) if re.match(r"^\d+\. ", sec[j])), len(sec))
para = " ".join(sec[i0:j])
HL_RE = {
    "base": r"미도달 base (\d+)\(R3만 (\d+), 두 벌 (\d+)/(\d+)\)",
    "fixed": r"→ 개정 (\d+)\(두 벌 (\d+)/(\d+)",
    "leak": r"비운영 노드 누수 (\d+) → (\d+)",
    "v3": r"test 함수 (\d+), V3 쌍 ([\d,]+) → ([\d,]+)\(([\d.]+)배\)",
    "inv0": r"인벤토리 0 (\d+) → (\d+)\(회귀 (\d+)\)",
    "median": r"중앙값 (\d+) → (\d+)",
    "old_edges": r"옛 간선 제거 (\d+)개\(전부 dunder 폴백\)·도달 감소 (\d+)",
    "records": r"과거 판정 기록 V7 쌍 (\d+)",
}
want, miss = {}, []
for k, rx in HL_RE.items():
    m = re.search(rx, para)
    if not m:
        miss.append(k)
        continue
    want[k] = tuple(x if "." in x else int(x.replace(",", "")) for x in m.groups())
diff = {k: (want.get(k), got[k]) for k in got if want.get(k) != got[k]}
print("머리 수치(측정):", json.dumps(got, ensure_ascii=False))
print("  면제 id:", exempt, " m4 쌍 %d(기록 %d)" % (len(pairs), len({r for o in pairs for r in o["records"]})))
assert not bad, ("불변식 위반 -- card 사실 문장 전체 재측정", bad)
assert not miss, ("초안 문단에서 문장 형식을 못 찾음", miss)
assert not diff, ("초안 문단 수치 != 측정(초안 문단을 이 rev·수치로 다시 쓴다)", diff)
print("headline OK: 불변식 %d개 성립, 초안 문단 수치 %d묶음 일치" % (len(inv), len(want)))
EOF
}

stage_kit_cmds() {
  local gm gm7 n=g'<n>'
  gm=$(g rev-parse gate/master); gm7=${gm:0:7}
  cat <<EOF
== 착수 재측정 명령(gate master $gm7 -- 실행하지 않음, 순서대로. 격리 복제본 C:/$n은 새 번호, 끝나면 그것만 삭제)
# ① 격리 복제본(origin 제거·빈 hooksPath)
mkdir -p /c/$n/nohooks /c/$n/tmp
git clone -q --no-hardlinks --no-local --no-checkout $R C:/$n/r
git -C C:/$n/r remote remove origin; git -C C:/$n/r config core.hooksPath C:/$n/nohooks; git -C C:/$n/r checkout -q -B master $gm
# ② 머리 수치(미도달·누수·V3 쌍 비율·인벤토리 0·간선 단조성 = m1 약 2분, 정적 인벤토리 m5 약 1분, 과거 V7 쌍 m4 약 40분)
#    -> run_in_background + timeout 2시간. 출력 디렉터리가 pre의 기본 --headline 경로다(<measured rev 7자>).
TMP=C:/$n/tmp TEMP=C:/$n/tmp bash $KIT/run_headline.sh C:/$n/r $KIT/out/head_$gm7
$PY -B $KIT/summarize.py $KIT/out/head_$gm7 $KIT/out/head_0f23786/m1.jsonl
# ③ 공격 33 측정 케이스(30단계, base 도구 vs 시제품 -- 경로는 C:/ 형식만. base + 변형 6개 약 16분 -> background)
bash $KIT/run_attack33.sh C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills $gm C:/$n/a33 $KIT/out/a33_$gm7.jsonl fixed,xout,bare,draft,loose,nosuper
$PY -B $KIT/a33_table.py $KIT/out/a33_$gm7.jsonl $KIT/out/a33_$gm7.table.md      # base 13 FAIL / fixed 30 PASS 기대(briefs §0.2)
# ④ 34·35 케이스 무동작 미리보기(③이 만든 두 복제본 재사용 -- 단계 판정 차이 0, 판정은 auditor 계약 14)
ls C:/$n/a33/base/tools/gates/redteam/attacks    # 34-*·35-* 실제 이름 확인 뒤 아래 --only에 넣는다
TMP=C:/$n/tmp TEMP=C:/$n/tmp $PY -B $KIT/run_redteam_variants.py C:/$n/p3435.jsonl C:/$n/a33/base:- C:/$n/a33/head:fixed -- --phase 0.5 --mode direct --only <34-이름>
TMP=C:/$n/tmp TEMP=C:/$n/tmp $PY -B $KIT/run_redteam_variants.py C:/$n/p3435.jsonl C:/$n/a33/base:- C:/$n/a33/head:fixed -- --phase 0.5 --mode direct --only <35-이름>
# ⑤ 사용자 원문 대조(세션 기록 jsonl -- 초안 '사용자 원문'이 바이트 부분 문자열인지)
$PY -B $KIT/check_user_quote.py <세션 jsonl> $DRAFT_APR C:/$n/user_quote.json
# ⑥ 수치가 초안 문단과 다르면 draft_b33.final.spec.md '작성 전 실측' 끝에 새 '(착수 재측정 <날짜>, gate master \`$gm7\`, …' 문단을
#    0f23786 문단과 같은 문장 형식으로 더한다(백업 먼저). 그다음 pre.
EOF
}

stage_pre() {
  say "pre: 착수 전 확인 + 머리 수치 대조(저장소 변경 없음)"
  test -n "$(git config --get user.email)"
  g fetch gate
  test "$(g rev-parse --abbrev-ref HEAD)" = master
  test "$(g rev-parse HEAD)" = "$(g rev-parse gate/master)"
  test -z "$(g for-each-ref refs/heads/role/)"                        # 역할 브랜치가 있으면 문서 push를 EL1이 거부(design 05 §12)
  if g worktree list --porcelain | grep -q -- "/$ID-"; then echo "$ID worktree가 이미 있다" >&2; false; fi
  g diff --cached --quiet
  test -z "$(g status --porcelain -- docs/ .ai/approvals/)"
  test ! -e "$R/$F_SPEC"; test ! -e "$R/$F_IFC"; test ! -e "$R/$F_APR"
  test -z "$(g ls-tree --name-only HEAD tools/gates/redteam/attacks/ | grep '/33-' || true)"   # D-18 번호 33 비어 있음
  for f in "$PATCH" "$FILL" "$DRAFT_SPEC" "$DRAFT_APR" "$IFC_REF"; do test -s "$f"; done
  test "$(grep -c '<rev-parse>' "$DRAFT_APR")" = 3
  test "$(grep '^diff_path: ' "$DRAFT_APR" | cut -d' ' -f2- | tr -d '\r' | sort | tr '\n' ' ')" = "$(printf '%s\n' "$D05" "$F_IFC" "$F_SPEC" | sort | tr '\n' ' ')"
  rm -f "$STATE"
  # 선행 card: 판정 기록이 gate master에 있고 V1~V10 판정이 PASS·N/A뿐
  local id missing=
  for id in $PRED; do
    if g cat-file -e "HEAD:.ai/verification/$id.json" 2>/dev/null; then
      g show "HEAD:.ai/verification/$id.json" | "$PY" -B -c "
import json,sys;o=json.load(sys.stdin);v={k:c.get('verdict') for k,c in o['checks'].items()}
assert o['id']==sys.argv[1] and set(v.values())<={'PASS','N/A'},(sys.argv[1],v);print('   선행',sys.argv[1],'판정 기록 있음')" "$id"
    else missing="$missing $id"; fi
  done
  if [ -n "$missing" ]; then
    [ -n "$PRED_MISSING_OK" ] || { echo "[중단] 선행 card 판정 기록 없음:$missing" >&2; false; }
    echo "   (사전 시험) 선행 판정 기록 없음 허용:$missing"
  fi
  # measured rev(단일 출처)와 gate master 사이: V7 그래프 입력이 같아야 머리 수치·사실 문장이 유효
  local ms meas C H gp
  ms=$(meas_short); meas=$(g rev-parse --verify "$ms^{commit}"); st_set MEAS "$meas"
  g merge-base --is-ancestor "$meas" HEAD
  C=$(cache_dir)
  gp=$("$PY" -B -c "import sys;sys.path.insert(0,sys.argv[1]);import reachability as r;print(' '.join(r.GRAPH_PREFIXES))" "$C")
  # shellcheck disable=SC2086
  g diff --quiet "$meas" HEAD -- $gp "$RCH" .ai/verification/ || { echo "[중단] measured rev $ms 와 gate master 사이 V7 그래프 입력 차이 -- kit-cmds로 다시 재고 초안 문단을 고친다:" >&2; g diff --stat "$meas" HEAD -- $gp "$RCH" .ai/verification/ | tail -5 >&2; false; }
  "$PY" -B -c "
import json,subprocess,sys
cfg=lambda rev:json.loads(subprocess.run(['git','-C',sys.argv[1],'show',rev+':tools/gates/gate_config.json'],capture_output=True,check=True).stdout)['reachability_roots']
assert cfg(sys.argv[2])==cfg('HEAD'),'reachability_roots 다름'" "$R" "$meas"
  # 사실 문장(작성 전 실측 1·2·3·5·7): grep 0건·1건 단정, 인용 줄은 출력(심볼이 앵커 -- 판정 영향 없음, 다르면 card 표기 갱신 후보)
  test -z "$(g grep -l "reachability\|mutate_changed" -- skills/analog-gmid-design/assets/tests || true)"
  test -z "$(g grep -n "reachability" -- tools/gates/gate tools/gates/merge_gate.py tools/gates/integrity.py hooks .githooks || true)"
  test -z "$(g grep -n "library/\|topology.json\|\.topology" -- "$RCH" || true)"
  test -z "$(g grep -n "::=" -- tools/gates || true)"
  test -z "$(g grep -l "_is_source" -- tools/gates | grep -vx "$RCH" | grep -vx "$MUT" || true)"
  test "$(g grep -c "rch\.build_graph(head_files)" -- "$MUT" | cut -d: -f2)" = 1
  test "$(g grep -n "super()\.__" -- 'skills/analog-gmid-design/assets/*.py' workspaces/run_harness.py | wc -l | tr -d ' ')" = 1
  g grep -q "super()\.__init__(message)" -- "$SR"
  echo "   인용 줄(card 표기 0f23786: mutate 215·317·354-356·387-392, rt 523·580, sizing_recipe 6452):"
  g grep -n "rch\.reach(\|rch\.build_graph(head_files)\|except subprocess.TimeoutExpired\|\"result\": \"killed\"" -- "$MUT" | cut -c1-110 | sed 's/^/     /'
  g grep -n "^def build_vrepo\|^def a_vcase" -- "$RT" | cut -c1-80 | sed 's/^/     /'
  g grep -n "super()\.__init__(message)" -- "$SR" | sed 's/^/     /'
  g grep -n "def _refs\|def build_graph\|def reach\|def _is_source\|def _approved_ids\|seen = reach\|new_defs = " -- "$RCH" | cut -c1-70 | sed 's/^/     /'
  # 계획 '운영 경로'(121)·N4.2 V7(843) 행: measured rev와 같은 문장(card가 게이트를 이 문구에 맞춘다)
  local row
  for row in '| 운영 경로 |' '| V7 | 배선 |'; do
    test "$(g show "$meas:$PLAN" | grep -F -- "$row" | tr -d '\r')" = "$(g show "HEAD:$PLAN" | grep -F -- "$row" | tr -d '\r')"
    test "$(g show "HEAD:$PLAN" | grep -cF -- "$row")" = 1
  done
  # 문서 패치 앵커: gate master blob 사본에 적용 -> applied 2, 재실행 already applied(저장소 무쓰기)
  g show "HEAD:$D05" > "$STATE.d05.md"
  "$PY" -B "$PATCH" "$STATE.d05.md" | tee "$STATE.patch1.txt" | sed 's/^/   /'
  grep -q '^applied 2 replacement(s), V7 row line [0-9]*, rejection line [0-9]*' "$STATE.patch1.txt"
  "$PY" -B "$PATCH" "$STATE.d05.md" | grep -q '^already applied'
  rm -f "$STATE.d05.md"
  # 머리 수치
  [ -n "$HL" ] || HL=$KIT/out/head_$ms
  echo "   머리 수치 출력 $HL"
  headline_check "$meas" "$HL"
  H=$(plan_hash "$C"); test ${#H} = 64
  st_set GATE_BASE "$(g rev-parse HEAD)"; st_set PLAN_HASH "$H"; st_set CACHE "$C"
  approved_ids "$C" "$(g rev-parse HEAD)" > "$STATE.ids.base"
  st_set N_IDS "$(wc -l < "$STATE.ids.base" | tr -d ' ')"
  say "pre OK: gate master $(g rev-parse --short HEAD), measured rev $ms, _approved_ids $(st_get N_IDS), plan_tables_hash $H, cache $C"
}

stage_doc() {
  say "doc (A): design 05 §10 V7 행 + 거부 증명 줄 -- Role: doc"
  test "$(g rev-parse HEAD)" = "$(st_get GATE_BASE)"
  g diff --cached --quiet
  test -z "$(g status --porcelain -- docs/)"
  "$PY" -B "$PATCH" "$R" | tee "$STATE.patchA.txt" | sed 's/^/   /'
  grep -q '^applied 2 replacement(s)' "$STATE.patchA.txt"
  "$PY" -B "$PATCH" "$R" | grep -q '^already applied'                  # 재실행 멱등
  g add -- "$D05"
  staged_is "$D05"
  numstat_is "$D05" "2 2"
  local H; H=$(plan_hash "$(st_get CACHE)"); test "$H" = "$(st_get PLAN_HASH)"   # 판정 표 불변 -> plan_tables 승인 불필요
  g commit -q -m "$SUBJ_A" \
    -m "_drafts/patch_b33_design05.py 적용(spec card $ID '문구 변경'·계약 13 문구 그대로, V7 행·거부 증명 줄 두 줄 교체, 줄 끝 보존). 판정 표 무변경(plan_tables_hash $H). 승인 기록 $ID가 이 커밋의 부모를 diff_base로 가리킨다." \
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
print('   parse_spec_card OK', c['phase'], c['evidence_type'], c['gate_change'], c['approval'], '절', len(c['sections']))
" "$C" "$R/$F_SPEC" "$ID" "$R/$PLAN"
  "$PY" -B "$C/interface_card.py" "$R/$F_SPEC" --root "$R" --out "$R/$F_IFC"
  test -s "$R/$F_IFC"
  # 표 행(모듈·심볼) = 착수 키트 모의판(briefs §0.5: 계약 절 design 05 인용문의 맨 __init__·__post_init__ 3행, 신규 시그니처 0행)
  "$PY" -B - "$R/$F_IFC" "$IFC_REF" <<'EOF'
import sys
def rows(p):
    t = open(p, encoding="utf-8").read().replace("\r\n", "\n")
    obs, new = t.split("\n## 신규 시그니처\n", 1)
    f = lambda s: sorted(tuple(c.strip() for c in l.split("|")[1:3]) for l in s.split("\n") if l.startswith("| `"))
    return f(obs), f(new)
got, ref = rows(sys.argv[1]), rows(sys.argv[2])
assert got == ref and got[1] == [], ("interface card 표가 모의판과 다르다", got, ref)
print("   interface card OK: 기존 함수 %d행 %s, 신규 시그니처 0행" % (len(got[0]), [s for m, s in got[0]]))
EOF
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
  local C base head tgt tgt2; C=$(st_get CACHE)
  base=$(st_get GATE_BASE); head=$(st_get B)
  "$PY" -B "$FILL" --root "$R" --draft "$DRAFT_APR" --base "$base" --head "$head" --check > "$STATE.fillcheck.json"
  "$PY" -B -c "import json,sys;r=json.load(open(sys.argv[1],encoding='utf-8'));assert r['result'].startswith('ok'),r" "$STATE.fillcheck.json"
  "$PY" -B "$FILL" --root "$R" --draft "$DRAFT_APR" --base "$base" --head "$head" > "$STATE.fill.json"
  "$PY" -B -c "import json,sys;r=json.load(open(sys.argv[1],encoding='utf-8'));assert r['result']=='written',r;print('   fill OK',r['target'])" "$STATE.fill.json"
  "$PY" -B "$FILL" --root "$R" --draft "$DRAFT_APR" --base "$base" --head "$head" | grep -q 'already-present'   # 멱등
  # target 독립 재계산 두 식(캐시 판 weakening_diff.diff_hash, merge_gate.py diff-hash -- fill은 작업 트리 tools/gates를 읽는다)
  tgt=$("$PY" -B -c "
import sys,re;sys.path.insert(0,sys.argv[1]);import weakening_diff as wd
t=open(sys.argv[5],encoding='utf-8').read().split('\n---\n',1)[0]
print(wd.diff_hash(sys.argv[2],sys.argv[3],sys.argv[4],re.findall(r'^diff_path: (.+)\$',t,flags=re.M)))" "$C" "$R" "$base" "$head" "$DRAFT_APR")
  tgt2=$("$PY" -B "$C/merge_gate.py" diff-hash --repo "$R" --base "$base" --head "$head" "$D05" "$F_IFC" "$F_SPEC")
  test "${#tgt}" = 64; test "$tgt" = "$tgt2"
  "$PY" -B "$C/merge_gate.py" parse-approval "$R/$F_APR" > "$STATE.appr.json"
  "$PY" -B -c "
import json,sys
r=json.load(open(sys.argv[1],encoding='utf-8'))
paths=sys.argv[6:]
exp=dict(id=sys.argv[2],date='2026-10-01',target_kind='diff',target=sys.argv[3],diff_base=sys.argv[4],diff_head=sys.argv[5],diff_path=paths)
bad={k:(r.get(k),v) for k,v in exp.items() if r.get(k)!=v}
assert not bad,bad
print('   parse_approval_header OK',r['target_kind'],r['target'][:12],r['diff_base'][:7],r['diff_head'][:7],len(r['diff_path']))
" "$STATE.appr.json" "$ID" "$tgt" "$base" "$head" "$D05" "$F_IFC" "$F_SPEC"
  # 바이트 단정: BOM 없음, CR 0, HTML 주석·자리표시 0('! grep'은 set -e가 잡지 않고, MSYS2 grep은 CR 하나짜리 패턴을 빈 패턴으로 다룬다 -- 실측)
  "$PY" -B -c "
import sys
b=open(sys.argv[1],'rb').read()
bad=[k for k,v in (('BOM',b.startswith(b'\xef\xbb\xbf')),('CR',b'\r' in b),('주석',b'<!--' in b),('자리표시',b'<rev-parse>' in b)) if v]
assert not bad,bad
print('   승인 기록 바이트 OK',len(b))" "$R/$F_APR"
  g add -- "$F_APR"
  staged_is "$F_APR"
  g commit -q -m "$SUBJ_C" \
    -m "사용자 2026-10-01 \"승인 (Recommended)\"·Q1 \"(a) 호출 위치만 (Recommended)\" 원문 인용. target = weakening_diff.diff_hash(diff_base = 문서 커밋의 부모, diff_head = spec+interface card 커밋, diff_path 3개) = $tgt (merge_gate diff-hash와 같은 값). 강화(거짓 PASS 차단) + 거짓 FAIL 제거." \
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
  test "$(g diff-tree --no-commit-id --name-only -r "$(st_get A)")" = "$D05"
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
print('   gate_change_ok HEAD',ok,' HEAD~1',pre)" "$C" "$R" "$(st_get C)" "$(st_get B)" "$ID"
  "$PY" -B -c "
import sys;sys.path.insert(0,sys.argv[1]);import weakening_diff as wd
hs=wd.approved_hashes(sys.argv[2],sys.argv[3]);assert sys.argv[4] in hs,len(hs);print('   approved_hashes 포함',len(hs))" "$C" "$R" "$(st_get C)" "$(st_get TARGET)"
  grep -qx "target: $(st_get TARGET)" "$R/$F_APR"
  grep -qx "diff_base: $base" "$R/$F_APR"; grep -qx "diff_head: $(st_get B)" "$R/$F_APR"
  # V3·V4·V7이 읽는 decision 원소 집합 불변(diff 기록은 원소가 아니다)
  approved_ids "$C" "$(st_get C)" > "$STATE.ids.head"
  cmp "$STATE.ids.base" "$STATE.ids.head"
  "$PY" -B "$PATCH" "$R" | grep -q '^already applied'
  test "$(plan_hash "$C")" = "$(st_get PLAN_HASH)"
  test -z "$(g status --porcelain -- docs/ .ai/approvals/)"
  g log --format='%h %s' "$base..HEAD" | cut -c1-120
  say "final OK -- 다음은 push 단독 호출(병렬·tail 금지):  git -C $R push gate master:master"
}

stage_after_push() {
  say "after-push: gate master 대조"
  g fetch gate
  test "$(g rev-parse gate/master)" = "$(st_get C)"
  test "$(g rev-parse HEAD)" = "$(g rev-parse gate/master)"
  test "$(g ls-tree --name-only gate/master -- "$F_APR" "$F_SPEC" "$F_IFC" | sort | tr '\n' ' ')" = "$(printf '%s\n' "$F_APR" "$F_SPEC" "$F_IFC" | sort | tr '\n' ' ')"
  test -z "$(g status --porcelain -- docs/ .ai/approvals/)"
  say "after-push OK -- 다음은 test worktree(단독 호출, design 05 §12 순서 1):  git -C $R worktree add $W/$ID-test -b role/test/$ID gate/master"
  say "B33 병합 뒤: G1(20260930-p3-gate-move-aware) 키트의 reachability.py 줄·사실을 B33 병합본에서 다시 잰다(briefs §0.3 마지막 행)"
}

case "$1" in
  kit-cmds) stage_kit_cmds ;;
  pre) stage_pre ;;
  doc) stage_doc ;;
  card) stage_card ;;
  appr) stage_appr ;;
  final) stage_final ;;
  local) stage_pre; stage_doc; stage_card; stage_appr; stage_final ;;
  after-push) stage_after_push ;;
  *) echo "사용: $0 [옵션…] kit-cmds|pre|local|doc|card|appr|final|after-push" >&2; exit 2 ;;
esac
