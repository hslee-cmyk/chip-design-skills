#!/usr/bin/env bash
# D0a card 20260930-p3-move-plan-tool 착수 0단계(오케스트레이터) -- Phase 3 design 승인 기록 커밋 뒤, G1 병합 뒤, D0b 앞.
# 근거: spec card 초안(draft_p3_d0a.spec.md) '의도'(G1 병합 뒤 base, Phase 2 DoD PASS 뒤)·'결정 필요 항목'(착수 조건 = G1 병합 뒤 base, SourceIndex.tree)·
#       '작성 전 실측' 머리(G1 병합 뒤 base에서 G1 이름 위치를 다시 잰다), d0a_briefs.md 머리 '착수 조건'·'착수 0단계'·0.5·4절,
#       design 30 §8.1 확정 순서(B34 → b26pre → backfill → B26-1 → B33 → G1 → D0a).
# 구조는 b26pre_launch.sh를 따른다(단계별 함수, 옵션은 단계 이름 앞, measured rev 단일 출처, 게이트 캐시 절대 경로, push·worktree는 출력만 -- EL1 판정 대상).
# 어느 확인이든 실패하면 그 자리에서 멈춘다(set -Eeuo pipefail + ERR trap).
#
# 커밋 순서(push 한 번 -- 승인 기록 20260930-30-module-split-design은 p3_design_commit.sh가 이미 올렸다, 착수 조건 1):
#   S  spec card + interface card(게이트 캐시 interface_card.py, 절대 경로)  -> push (단독)
#
#   bash d0a_launch.sh conds       # 착수 조건 1~8을(8 = 계약 2 가장자리 (e1)·(e4) AST 스캔 -- D0a-S2) 지금 로컬 gate/master에서 판정(읽기 전용, fetch도 안 함)
#                                  #   exit 0 = 전부 충족, 3 = 미충족 있음(표), 1 = 규약 불일치(초안 머리·measured 앵커 사슬 -- 표를 믿지 않는다)
#   bash d0a_launch.sh local       # pre -> card -> final  (로컬 커밋 S, push 안 함 -- 끝에 push 명령 출력)
#   bash d0a_launch.sh after-push  # push 뒤: gate master = S, 게이트 캐시 새 판 + test worktree 명령 출력
#   bash d0a_launch.sh <단계>      # pre | card | final 하나만(중단 뒤 이어 하기 -- 각 단계가 앞 단계 결과를 확인)
#
# 사전 시험 옵션(반드시 단계 이름 앞에): --repo <복제본> --state <상태 파일> --wt <worktree 부모> [--draft-spec <초안 사본>]
#   --repo를 주면 --state·--wt 필수. --draft-spec은 복제본 모드에서만(실제 저장소에서는 초안 정본만 -- review_launch_scripts S1).
#   실제 저장소 판별은 launch_common.sh lc_repo_guard(git-common-dir 정규화 비교 -- 별칭·worktree 경로도 실제 저장소).
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
STATE_REAL=$DR/d0a_launch_state.txt
STATE=$STATE_REAL
DRAFT_REAL=$DR/draft_p3_d0a.spec.md
DRAFT_SPEC=$DRAFT_REAL
while [ $# -gt 1 ]; do
  case "$1" in
    --repo) R=$2; shift 2 ;;
    --state) STATE=$2; shift 2 ;;
    --wt) W=$2; shift 2 ;;
    --draft-spec) DRAFT_SPEC=$2; shift 2 ;;
    *) break ;;
  esac
done
# 단계 이름 뒤에 옵션을 붙이면 조용히 무시돼 실제 저장소에서 돈다(review_post_p10b_runbook B1과 같은 가드) -- 남은 인자는 단계 이름 하나뿐
[ $# -eq 1 ] || { echo "[중단] 사용법: $0 [--repo R --state S --wt W [--draft-spec F]] <단계>  (옵션은 단계 이름 앞에만)" >&2; exit 2; }
case "$1" in --*) echo "[중단] 단계 이름 자리에 옵션: $1 (옵션 값이 빠졌거나 순서가 틀렸다)" >&2; exit 2 ;; esac
lc_repo_guard "$R" "$R_REAL"
if [ "$LC_REAL" = 0 ]; then
  lc_need_sandbox --state "$STATE" "$STATE_REAL"; lc_need_sandbox --wt "$W" "$W_REAL"
  case "$DRAFT_SPEC" in /*|[A-Za-z]:[/\\]*) ;; *) echo "[중단] --draft-spec은 절대 경로로($DRAFT_SPEC)" >&2; exit 2 ;; esac
else
  lc_need_real --state "$STATE" "$STATE_REAL"; lc_need_real --wt "$W" "$W_REAL"; lc_need_real --draft-spec "$DRAFT_SPEC" "$DRAFT_REAL"
  STATE=$STATE_REAL; W=$W_REAL; DRAFT_SPEC=$DRAFT_REAL
fi
lc_tmp_setup "$STATE"
echo "== 대상 저장소 R=$R  상태 파일 $STATE  worktree 부모 $W  초안 $DRAFT_SPEC"

PY=$LC_PY
ID=20260930-p3-move-plan-tool
AID=20260930-30-module-split-design
G1ID=20260930-p3-gate-move-aware
# 선행 card(design 30 §8.1 확정 순서 -- D0a 앞 전부). G1은 마지막(조건 6이 measured rev에서 다시 본다)
# card 35 V3 범위 정책(20260930-v3-changed-stmt-scope)은 G1 base의 전제(design §5.5) -- review_d0a_d0b_ready D0a m3. a17b8bd 병합·판정 기록 dafe5cf(7243f28에서 충족)
PREDS="20260930-b34-grammar-explicit 20260930-b26-pre-test-strengthen 20261001-b26-backfill-interdig-final-audit 20260930-b26-rail-accessor-set 20260930-v7-registry-edges 20260930-v3-changed-stmt-scope $G1ID"
PLAN=docs/01-plan/features/gain-budget-gmid-sizing.plan.md
REG=docs/03-analysis/gain-budget-gmid-sizing.function-registry.md
D30=docs/02-design/features/gain-budget-gmid-sizing.30-module-split.design.md
DOD=docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/phase2-dod.md
F_SPEC=docs/02-design/specs/$ID.spec.md
F_IFC=docs/02-design/specs/$ID.interface.md
A=skills/analog-gmid-design/assets
TOOL=tools/migrate/move_plan.py
NEWT=$A/tests/tooling/test_move_plan.py
# measured rev 이후 바뀌면 card 사실 문장(작성 전 실측 1·4·5·10 -- reachability 줄·재사용 이름·tools/migrate·tooling)을 다시 재야 하는 경로(d0a_briefs 착수 0단계 diff 경로 그대로)
MEAS_PATHS="tools/gates tools/migrate $PLAN $REG $A/tests/tooling"
COAUTH="Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
APPR_IDS="$AID"
NSEC=11
# interface card 정본 모양(d0a_briefs 0.5-3·0.1 interface 행): '기존 함수' 0행, 신규 = 모듈 move_plan(*)과 main
IFC_NEW="move_plan.* move_plan.main"
NCOND=8
SUBJ_S="docs: D0a spec card $ID(tools/migrate/move_plan.py plan·check -- 이관표·PLAN-LAYER·import_time_high·mod_imports·import_conflicts·MOVE-AST·ORDER·SHIM·CACHE-ID, G1 SourceIndex·moved_defs 재사용, red-green, phase 3, 승인 $AID) + interface card"

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
head_subj_is() { test "$(g log -1 --format=%s)" = "$1"; }
trailer_is() {   # <커밋> <키> <값|-(없음)>
  local v; v=$(g log -1 --format="%(trailers:key=$2,valueonly)" "$1" | tr -d '\r' | grep -v '^$' || true)
  if [ "$3" = - ]; then test -z "$v"; else test "$v" = "$3"; fi
}
approved_ids() { "$PY" -B -c "
import sys;sys.path.insert(0,sys.argv[1]);import reachability as r
print('\n'.join(sorted(r._approved_ids(sys.argv[2],sys.argv[3]))))" "$1" "$R" "$2"; }
# card 머리 블록의 approval 줄(순서 그대로)
draft_approvals() {
  "$PY" -B -c "
import sys
t=open(sys.argv[1],encoding='utf-8').read().replace('\r\n','\n')
assert t.startswith('---\n'); h=t.split('\n---\n',1)[0]
print(' '.join(l.split(':',1)[1].strip() for l in h.split('\n') if l.startswith('approval:')))" "$DRAFT_SPEC"
}
# card 머리 id(초안 사본이 다른 card를 가리키는 실수 방지)
draft_id() { sed -n '2p' "$DRAFT_SPEC" | tr -d '\r' | sed -n 's/^id: //p'; }
# 게이트 캐시 판 parse-approval로 <H>의 승인 기록 id 일치(0) / 없음(3) / 머리 위반(3). 파일 이름 <id>.md만 받으므로 임시 디렉터리에 꺼낸다
approval_rc() {   # <H> <캐시> <id>
  local H=$1 C=$2 a=$3 t
  g cat-file -e "$H:.ai/approvals/$a.md" 2>/dev/null || { echo "      승인 기록 $a: gate ${H:0:7}에 없음" >&2; return 3; }
  t=$(mktemp -d)
  g show "$H:.ai/approvals/$a.md" > "$t/$a.md"
  if "$PY" -B "$C/merge_gate.py" parse-approval "$t/$a.md" | "$PY" -B -c "import json,sys;r=json.load(sys.stdin);assert r['id']==sys.argv[1],r['id']" "$a"; then
    rm -rf "$t"; return 0
  fi
  rm -rf "$t"; echo "      승인 기록 $a: parse-approval 실패 또는 id 다름" >&2; return 3
}
# measured rev 단일 출처 = spec card 초안 '작성 전 실측'의 '**measured at `<rev>`**'(마지막 출현 -- launch_common m8, 다른 launch 스크립트와 같은 규약)
MEAS_PAT='\*\*measured at `[0-9a-f]\{7,40\}`\*\*'
meas_rev() {
  local s; s=$(lc_meas_short "$R" "$DRAFT_SPEC" "$MEAS_PAT")
  test -n "$s"
  g rev-parse --verify "$s^{commit}"
}

# ---------------------------------------------------------------- 착수 조건(초안에 명령 목록이 없다 -- 근거 문장을 조건 함수로 옮겼다)
# 각 함수는 0 = 충족, 3 = 미충족, 1 = 규약 불일치(표를 믿지 않는다). '||' 문맥에서 불리므로 set -e에 기대지 않고 실패마다 명시적으로 return 한다(review S2).
COND_TITLE_1="Phase 3 design 승인 기록 $AID + design 30 문서가 gate에 있다(UD-0, p3_design_commit.sh)"
cond_1() {
  local H=$1 C=$2 r=0
  approval_rc "$H" "$C" "$AID" || r=$?
  [ "$r" = 0 ] || return 3
  g cat-file -e "$H:$D30" 2>/dev/null || { echo "      design 30 문서 $D30 없음" >&2; return 3; }
  return 0
}
COND_TITLE_2="선행 card 병합(B34·b26pre·backfill·B26-1·B33·card 35 V3 범위 정책·G1 판정 기록 V1~V10 PASS·N/A -- lc_pred_ok)"
cond_2() {
  local H=$1 id bad=0
  for id in $PREDS; do lc_pred_ok "$R" "$H" "$id" || bad=1; done
  [ "$bad" = 0 ] || return 3
  return 0
}
COND_TITLE_3="Phase 2 DoD PASS(phase2-dod.md '## 판정' 다음 첫 줄 '판정: PASS' -- phase 3 card, 계획 993행)"
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
COND_TITLE_4="G1 공개 표면과 재사용 이름(계약 5): SourceIndex.tree·units·global_names·binding_origin, moved_defs, read_tree, mod_table, read_section_table, _is_empty_dict"
cond_4() {
  local H=$1 t r
  t=$(mktemp -d)
  g show "$H:tools/gates/reachability.py" > "$t/reachability.py" 2>/dev/null || { rm -rf "$t"; echo "      reachability.py 없음" >&2; return 3; }
  g show "$H:tools/gates/import_layering.py" > "$t/import_layering.py" 2>/dev/null || { rm -rf "$t"; return 3; }
  g show "$H:tools/gates/role_paths.py" > "$t/role_paths.py" 2>/dev/null || { rm -rf "$t"; return 3; }
  g show "$H:tools/gates/source_lint.py" > "$t/source_lint.py" 2>/dev/null || { rm -rf "$t"; return 3; }
  r=0
  "$PY" -B - "$t" <<'EOF' || r=$?
import ast, os, sys
d = sys.argv[1]
def top(f):
    m = ast.parse(open(os.path.join(d, f), encoding="utf-8").read())
    fns = {n.name for n in m.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    cls = {n.name: {b.name for b in n.body if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef))} for n in m.body if isinstance(n, ast.ClassDef)}
    return fns, cls
miss = []
f, c = top("reachability.py")
for n in ("moved_defs", "read_tree"):
    if n not in f: miss.append("reachability." + n)
si = c.get("SourceIndex")
if si is None: miss.append("reachability.SourceIndex")
else:
    for n in ("tree", "units", "global_names", "binding_origin"):   # tree = G1 spec card v9(키트 0.3 결정 -- 내부 속성 우회 금지)
        if n not in si: miss.append("SourceIndex." + n)
for mod, n in (("import_layering.py", "mod_table"), ("role_paths.py", "read_section_table"), ("source_lint.py", "_is_empty_dict")):
    if n not in top(mod)[0]: miss.append(mod[:-3] + "." + n)
if miss:
    sys.stderr.write("      없는 이름: %s\n" % ", ".join(miss)); sys.exit(3)
EOF
  rm -rf "$t"
  [ "$r" = 0 ] || { [ "$r" = 3 ] && return 3; return 1; }
  return 0
}
COND_TITLE_5="이름 충돌 없음: $TOOL·$NEWT가 아직 없다(작성 전 실측 2)"
cond_5() {
  local H=$1 bad=0
  if g cat-file -e "$H:$TOOL" 2>/dev/null; then echo "      $TOOL이 이미 있다" >&2; bad=1; fi
  if g cat-file -e "$H:$NEWT" 2>/dev/null; then echo "      $NEWT가 이미 있다" >&2; bad=1; fi
  [ "$bad" = 0 ] || return 3
  return 0
}
COND_TITLE_6="measured rev(초안 '**measured at \`<rev>\`**' 마지막 출현)가 G1 병합 뒤이고 그 뒤 $MEAS_PATHS 변경 0"
cond_6() {
  local H=$1 n M ch
  n=$(grep -c -- "$MEAS_PAT" "$DRAFT_SPEC" || true)
  [ "${n:-0}" -gt 0 ] || { echo "      초안에 measured 앵커가 없다 -- G1 병합 뒤 base에서 착수 0단계(d0a_briefs 머리)를 재고 '작성 전 실측'에 '**measured at \`<rev>\`**' 문장을 더한다" >&2; return 3; }
  M=$(meas_rev) || return 1                                          # 앵커가 있는데 rev를 못 찾거나 '마지막 = 최신' 규약 위반 -- 규약 불일치
  g merge-base --is-ancestor "$M" "$H" || { echo "      measured ${M:0:7}가 gate ${H:0:7}의 조상이 아니다" >&2; return 1; }
  lc_pred_ok "$R" "$M" "$G1ID" || { echo "      measured ${M:0:7}가 G1 병합 앞이다 -- G1 병합 뒤 base에서 다시 잰다(작성 전 실측 머리)" >&2; return 3; }
  # shellcheck disable=SC2086
  ch=$(g diff --name-only "$M" "$H" -- $MEAS_PATHS | wc -l | tr -d ' ')
  [ "$ch" = 0 ] || { echo "      measured ${M:0:7} -> gate ${H:0:7}: card 사실 문장 대상 $ch파일 변경 -- 다시 재고 measured 문장을 고친다" >&2; g diff --name-only "$M" "$H" -- $MEAS_PATHS | sed 's/^/        /' >&2; return 3; }
  echo "      measured ${M:0:7} -> gate ${H:0:7}: 대상 경로 변경 0, G1 판정 기록 있음" >&2
  return 0
}
COND_TITLE_7="역할 브랜치 role/* 0개, $ID worktree 없음(design 05 §12 -- 문서 push 전제)"
cond_7() {
  local bad=0
  [ -z "$(g for-each-ref refs/heads/role/)" ] || { echo "      역할 브랜치: $(g for-each-ref --format='%(refname:short)' refs/heads/role/ | tr '\n' ' ')" >&2; bad=1; }
  if g worktree list --porcelain | grep -q -- "/$ID-"; then echo "      $ID worktree가 이미 있다" >&2; bad=1; fi
  [ "$bad" = 0 ] || return 3
  return 0
}
# 조건 8(review_d0a_d0b_ready D0a-S2): 계약 2 가장자리 (e1)·(e4)가 실제 트리에서 0인지 도구 없이 AST로 미리 본다 -- 0이 아니면 D0a V10(계약 8 (a) exit ≠ 2)과
# D0b S-4가 늦게 막힌다(B34·backfill·B26-1 실제 코드가 최상위 재바인딩을 더할 수 있다). 대상 파일 = 계약 2 '배정 대상'(design 30 §6.3 MP_ARGS의 --split 파일 +
# A-0 대상 = gate 트리에 있고 --split에 없는 N3.10 파일). 단위 = 최상위 def·class·문장(모듈 docstring·import 문·`if __name__ == "__main__":` 블록 제외 -- G1 SourceIndex.units와 같은 범위),
# 단위 키 = 계약 2(def·class = 이름, 문장 = 바인딩 이름 정렬 ',' 연결, 무바인딩 = 문장 AST 덤프 -- 같은 덤프 = 같은 <stmt:해시>).
# (e1) 한 파일 안 같은 단위 키 둘 이상, (e4) 레지스트리 함수 표(머리에 '함수'·'이관 목적지') 행의 함수 칸 첫 백틱 토큰('.' 앞)이 두 파일 이상의 단위 키에 맞음.
COND_TITLE_8="계약 2 가장자리 (e1) 파일 안 단위 키 중복 0·(e4) 두 파일 이상에 맞는 레지스트리 이름 0(AST 스캔, MP_ARGS --split + A-0 파일)"
cond_8() {
  local H=$1 C=$2 r=0
  g cat-file -e "$H:$D30" 2>/dev/null || { echo "      design 30 문서 없음 -- MP_ARGS를 읽을 수 없다" >&2; return 1; }
  "$PY" -B - "$C" "$R" "$H" "$D30" "$PLAN" "$REG" "$A" <<'EOF' || r=$?
import ast, json, shlex, subprocess, sys
C, R, H, D30, PLAN, REG, A = sys.argv[1:8]
sys.path.insert(0, C)
import import_layering as il, role_paths as rp
def show(p):
    return subprocess.run(["git", "-C", R, "show", "%s:%s" % (H, p)], capture_output=True, check=True).stdout.decode("utf-8").replace("\r\n", "\n")
def exists(p):
    return subprocess.run(["git", "-C", R, "cat-file", "-e", "%s:%s" % (H, p)], capture_output=True).returncode == 0
# MP_ARGS(design 30 §6.3 첫 블록 -- d0b_launch.sh mpargs_load와 같은 읽기)
t = show(D30)
blk = []
for l in t[t.index("\nMP_ARGS=(") + 1:].split("\n"):
    blk.append(l)
    if l.rstrip().endswith(")"):
        break
s = "\n".join(blk)
a = shlex.split(s[len("MP_ARGS=("):s.rstrip().rindex(")")])
def vals(k):
    i = a.index(k) + 1; out = []
    while i < len(a) and not a[i].startswith("--"):
        out.append(a[i]); i += 1
    return out
split = vals("--split")
assert split and all(x.endswith(".py") for x in split), split
mt = il.mod_table(show(PLAN))
files = [x for x in split if exists(A + "/" + x)]
absent = [x for x in split if x not in files]
a0 = sorted(f + ".py" for f in mt if f + ".py" not in split and exists(A + "/" + f + ".py"))
files += a0
COMPS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
def bound(stmt):   # G1 계약 1 바인딩(시제품 _g1_bound_names와 같은 범위)
    out = set()
    def visit(n, in_comp=False):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(n.name)
            for d in n.decorator_list:
                visit(d)
            return
        if isinstance(n, ast.Lambda):
            for d in n.args.defaults + [x for x in n.args.kw_defaults if x is not None]:
                visit(d)
            return
        if isinstance(n, COMPS):
            for ch in ast.iter_child_nodes(n):
                visit(ch, True)
            return
        if isinstance(n, ast.NamedExpr):
            out.add(n.target.id); visit(n.value, in_comp); return
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)) and not in_comp:
            out.add(n.id)
        if isinstance(n, ast.ExceptHandler) and n.name:
            out.add(n.name)
        if isinstance(n, (ast.MatchAs, ast.MatchStar)) and n.name:
            out.add(n.name)
        if isinstance(n, ast.MatchMapping) and n.rest:
            out.add(n.rest)
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            for x in n.names:
                if x.name != "*":
                    out.add(x.asname or x.name.split(".")[0])
        for ch in ast.iter_child_nodes(n):
            visit(ch, in_comp)
    visit(stmt)
    return out
def is_main(n):
    return (isinstance(n, ast.If) and isinstance(n.test, ast.Compare) and isinstance(n.test.left, ast.Name)
            and n.test.left.id == "__name__" and len(n.test.comparators) == 1
            and isinstance(n.test.comparators[0], ast.Constant) and n.test.comparators[0].value == "__main__")
keys_by_file, e1 = {}, []
for f in files:
    body = ast.parse(show(A + "/" + f)).body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]                                   # 모듈 docstring(계약 2 v8.4)
    cnt = {}
    for n in body:
        if isinstance(n, (ast.Import, ast.ImportFrom)) or is_main(n):
            continue
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            k = n.name
        else:
            b = bound(n)
            k = ",".join(sorted(b)) if b else "<stmt:%s>" % ast.dump(n, include_attributes=False)
        cnt.setdefault(k, []).append(n.lineno)
    keys_by_file[f] = set(cnt)
    e1 += ["%s::%s (줄 %s)" % (f, k if not k.startswith("<stmt:") else "<stmt>", ",".join(map(str, v))) for k, v in sorted(cnt.items()) if len(v) > 1]
# 레지스트리 함수 표 -- 칸 나누기는 게이트 role_paths._split_cells(`\|` 이스케이프)
rows, hdr = [], None
for l in show(REG).split("\n"):
    if not l.startswith("|"):
        hdr = None; continue
    c = [x.strip() for x in rp._split_cells(l)]
    if hdr is None:
        hdr = c; continue
    if set("".join(c)) <= set("-: "):
        continue
    if "함수" in hdr and "이관 목적지" in hdr and len(c) > hdr.index("함수"):
        cell = c[hdr.index("함수")]
        if "`" in cell:
            rows.append(cell.split("`")[1].split(".")[0])
e4 = []
for nm in sorted(set(rows)):
    fs = sorted(f for f in files if nm in keys_by_file[f])
    if len(fs) > 1:
        e4.append("%s -> %s" % (nm, " ".join(fs)))
sys.stderr.write("      대상 파일 %d(--split %s%s, A-0 %s), 레지스트리 함수 행 이름 %d개 -- (e1) %d, (e4) %d\n" % (
    len(files), " ".join(x for x in split if x in files), (" -- 없는 split " + " ".join(absent)) if absent else "", " ".join(a0) or "없음", len(set(rows)), len(e1), len(e4)))
for x in e1[:20]:
    sys.stderr.write("        (e1) %s\n" % x)
for x in e4[:20]:
    sys.stderr.write("        (e4) %s\n" % x)
sys.exit(3 if (e1 or e4) else 0)
EOF
  [ "$r" = 0 ] && return 0
  [ "$r" = 3 ] && { echo "      -> 0이 아니면 D0a 착수 전에 멈춘다: 그 트리에서 D0a plan은 exit 2(계약 1·2 r1)라 V10 계약 8 (a)와 D0b S-4가 막힌다 -- 원인 card(최상위 재바인딩·같은 이름 def)를 먼저 고친다" >&2; return 3; }
  return 1
}
# 초안 자체 규약(머리 id·approval 줄) -- 어긋나면 규약 불일치 1
draft_ok() {
  test -s "$DRAFT_SPEC" || { echo "[중단] 초안 $DRAFT_SPEC 없음" >&2; return 1; }
  [ "$(draft_id)" = "$ID" ] || { echo "[중단] 초안 머리 id $(draft_id) != $ID" >&2; return 1; }
  [ "$(draft_approvals)" = "$APPR_IDS" ] || { echo "[중단] 초안 approval 줄 '$(draft_approvals)' != '$APPR_IDS'" >&2; return 1; }
}
# 조건 1~NCOND 표 + 요약 rc. <H> <캐시> -> CRC(0/3/1), RC<n>
conds_eval() {
  local H=$1 C=$2 n r out=""
  CRC=0
  draft_ok || { CRC=1; return 0; }
  for n in $(seq 1 "$NCOND"); do
    r=0; "cond_$n" "$H" "$C" || r=$?
    eval "RC$n=$r"; out="$out $n:$r"
    printf '   [%s] %-6s %s\n' "$n" "$( [ "$r" = 0 ] && echo 충족 || { [ "$r" = 3 ] && echo 미충족 || echo 규약오류; } )" "$(eval echo "\$COND_TITLE_$n")"
    if [ "$r" = 1 ]; then CRC=1; elif [ "$r" != 0 ] && [ "$CRC" = 0 ]; then CRC=3; fi
  done
  echo "   착수 조건(gate master ${H:0:7}) exit:$out -> $CRC"
}
# interface card 모양 확인(<card 파일>): '관찰 가능한 계약'(기존 함수) 0행, '신규 시그니처' = IFC_NEW
ifc_check() {
  "$PY" -B -c "
import sys
t=open(sys.argv[1],encoding='utf-8').read().replace('\r\n','\n')
sec={}; cur=None
for l in t.split('\n'):
    if l.startswith('## '): cur=l[3:].strip(); sec[cur]=[]
    elif cur and l.startswith('| \`'): sec[cur].append(l)
old=sec.get('관찰 가능한 계약'); new=sec.get('신규 시그니처')
assert old is not None and new is not None, ('interface card 절 이름', list(sec))
key=lambda l: l.split('|')[1].strip().strip('\`')+'.'+l.split('|')[2].strip().strip('\`')
assert not old, ('기존 함수 %d행 -- 초안 \'관찰 가능한 계약\'의 백틱 엔진 이름을 생성기가 잡았다(d0a_briefs 0.5-3). 그 절에서 백틱을 빼고 다시' % len(old), sorted(map(key, old)))
got=sorted(map(key,new)); exp=sorted(sys.argv[2].split())
assert got==exp, ('신규 시그니처 행', got, exp)
print('   interface card: 기존 함수 0개, 신규', ' '.join(got))" "$1" "$IFC_NEW"
}

stage_conds() {
  say "conds: 착수 조건 1~$NCOND(읽기 전용 -- fetch 안 함, 지금 로컬 gate/master 기준)"
  local H C; H=$(g rev-parse gate/master)
  C=$(cache_dir)
  conds_eval "$H" "$C"
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
  rm -f "$STATE"
  local H C P M; H=$(g rev-parse gate/master); C=$(cache_dir)
  conds_eval "$H" "$C"
  [ "$CRC" = 0 ] || { echo "[중단] 착수 조건 미충족(exit $CRC) -- 위 표" >&2; return 1; }
  # interface card를 미리 만들어 모양 확인(커밋 전 -- 기존 함수 행이 생기면 card 단계까지 가지 않는다)
  "$PY" -B "$C/interface_card.py" "$DRAFT_SPEC" --root "$R" --out "$STATE.ifc.pre.md" > /dev/null
  ifc_check "$STATE.ifc.pre.md"
  M=$(meas_rev); P=$(plan_hash "$C"); test ${#P} = 64
  st_set MEAS "$M"; st_set GATE_BASE "$H"; st_set PLAN_HASH "$P"; st_set CACHE "$C"
  approved_ids "$C" "$H" > "$STATE.ids.base"
  say "pre OK: gate master ${H:0:7}, measured ${M:0:7}, _approved_ids $(wc -l < "$STATE.ids.base" | tr -d ' '), plan_tables_hash ${P:0:16}…, cache $C"
}

stage_card() {
  say "card (S): spec card + interface card(게이트 캐시 interface_card.py, 절대 경로) -- Role: doc"
  local H; H=$(g rev-parse gate/master)
  test "$(g rev-parse HEAD)" = "$(st_get GATE_BASE)"
  test "$H" = "$(st_get GATE_BASE)"                                   # gate master가 그사이 움직이지 않았다
  g diff --cached --quiet
  local C; C=$(cache_dir); test "$C" = "$(st_get CACHE)"
  conds_eval "$H" "$C"                                                # 착수 조건 전부 -- card 커밋 직전
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
  g show "HEAD:$F_SPEC" | cmp - "$DRAFT_SPEC"                          # 커밋된 card = 초안 바이트 동일
  # decision 원소 집합 불변(이 커밋은 승인 기록을 더하지 않는다)
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
  say "after-push OK -- 다음은 test worktree(단독 호출, design 05 §12 순서 1):  git -C $R worktree add $W/$ID-test -b role/test/$ID gate/master"
  echo "   (d0a_briefs 4절: test-author 1절 -> auditor 3.1(산출물은 쓰기만, 커밋하지 않는다 -- 커밋은 순서 7에서 M 위 한 커밋) -> code worktree -> code-author 2절 -> 병합(전에 git -C $W/$ID-audit log --oneline role/test/$ID..HEAD 출력이 비어야 한다, 아니면 멈춤) -> auditor 3.2 -> push -> 정리 -> D0b. 판정 기록 code_commit = M card·DoD가 쓸 move_plan.py 사본 출처)"
}

case "$1" in
  conds) stage_conds ;;
  pre) stage_pre ;;
  card) stage_card ;;
  final) stage_final ;;
  local) stage_pre; stage_card; stage_final ;;
  after-push) stage_after_push ;;
  *) echo "사용: $0 [옵션…] conds|pre|local|card|final|after-push" >&2; exit 2 ;;
esac
