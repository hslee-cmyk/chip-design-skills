#!/usr/bin/env bash
# V3 범위 정책 card 20260930-v3-changed-stmt-scope 착수 0단계(오케스트레이터) -- 면제 묶기 card 20260930-v3-exempt-binding 병합·정리 뒤.
# 근거: v3_scope_briefs.md §0.4(A1~A7)·§0.5·§4, v3_cards_commit_plan.md §4.2(push 전까지). v3_binding_launch.sh와 같은 모양.
# 어느 확인이든 실패하면 그 자리에서 멈춘다(set -Eeuo pipefail + ERR trap). push는 하지 않는다(단독 호출 -- final이 명령 출력).
#
#   bash v3_scope_launch.sh pre        # 착수 전 확인(묶기 card 병합 확인·§0.4 A2·A3·A5·A7 자동 대조·줄 번호·엔진 불변), 저장소 변경 없음
#   bash v3_scope_launch.sh local      # pre -> doc -> card -> appr -> final (로컬 커밋 3개, push 안 함)
#   bash v3_scope_launch.sh <단계>     # doc | card | appr | final 하나만(중단 뒤 이어 하기 -- 각 단계가 앞 단계 결과를 확인)
#   bash v3_scope_launch.sh after-push # push 뒤 gate master 대조 + test worktree 명령 출력
#
# 사전 시험 옵션(반드시 단계 이름 앞에): --repo <복제본> --state <상태 파일> --render-tmp <임시 폴더> [--drafts <초안 사본 폴더>]
#   --repo를 주면 --state·--render-tmp 필수(실제 상태 파일·임시 폴더 보호). --drafts(spec·승인 초안 사본 폴더)는 --repo와 함께만.
set -Eeuo pipefail
shopt -s inherit_errexit
NL=$'\n'
trap 'echo "[중단] ${BASH_SOURCE[0]}:${LINENO}: ${BASH_COMMAND%%"$NL"*}" >&2' ERR   # heredoc 명령은 첫 줄만

# MSYS2 자식 bash는 HOME·APPDATA를 잃는다(post_p10b_runbook.sh와 같은 실측). 자식 python stdout은 cp949 -- 문자열 비교용 utf-8
export HOME=/c/Users/HSLEE
export APPDATA='C:\Users\HSLEE\AppData\Roaming' LOCALAPPDATA='C:\Users\HSLEE\AppData\Local' USERPROFILE='C:\Users\HSLEE'
export PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8

R_REAL=/c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
R=$R_REAL
W=/c/Users/HSLEE/Documents/Todoc/fpga/wt
DR=$W/_drafts
STATE_REAL=$DR/v3_scope_state.txt
STATE=$STATE_REAL
T_REAL=$DR/v3_scope_tmp
T=$T_REAL
DRAFTS=$DR
while [ $# -gt 1 ]; do
  case "$1" in
    --repo) R=$2; shift 2 ;;
    --state) STATE=$2; shift 2 ;;
    --render-tmp) T=$2; shift 2 ;;
    --drafts) DRAFTS=$2; shift 2 ;;
    *) break ;;
  esac
done
# 단계 이름 뒤에 옵션을 붙이면 조용히 무시돼 실제 저장소에서 돈다(review_post_p10b_runbook B1과 같은 가드) -- 남은 인자는 단계 이름 하나뿐
[ $# -eq 1 ] || { echo "[중단] 사용법: $0 [--repo R --state S --render-tmp T [--drafts D]] <단계>  (옵션은 단계 이름 앞에만)" >&2; exit 2; }
case "$1" in --*) echo "[중단] 단계 이름 자리에 옵션: $1 (옵션 값이 빠졌거나 순서가 틀렸다)" >&2; exit 2 ;; esac
if [ "$R" != "$R_REAL" ]; then
  [ "$STATE" != "$STATE_REAL" ] || { echo "[중단] --repo 사용 시 --state 필수(실제 상태 파일 보호)" >&2; exit 2; }
  [ "$T" != "$T_REAL" ] || { echo "[중단] --repo 사용 시 --render-tmp 필수(실제 임시 폴더 보호)" >&2; exit 2; }
else
  [ "$STATE" = "$STATE_REAL" ] || { echo "[중단] 실제 저장소에서는 --state를 바꾸지 않는다" >&2; exit 2; }
  [ "$T" = "$T_REAL" ] || { echo "[중단] 실제 저장소에서는 --render-tmp를 바꾸지 않는다" >&2; exit 2; }
  [ "$DRAFTS" = "$DR" ] || { echo "[중단] --drafts는 --repo(복제본)와 함께만" >&2; exit 2; }
fi
echo "== 대상 저장소 R=$R  상태 파일 $STATE  임시 $T  초안 $DRAFTS"

PY=/c/Python314/python.exe
ID=20260930-v3-changed-stmt-scope
BID=20260930-v3-exempt-binding
PATCH=$DR/patch_v3_scope_docs.py
BPATCH=$DR/patch_v3_binding_docs.py
FILL=$DR/fill_v3_approval.py
DRAFT_SPEC=$DRAFTS/draft_v3_scope_policy.spec.md
DRAFT_APR=$DRAFTS/approval_$ID.md
PLAN=docs/01-plan/features/gain-budget-gmid-sizing.plan.md
D05=docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md
F_SPEC=docs/02-design/specs/$ID.spec.md
F_IFC=docs/02-design/specs/$ID.interface.md
F_APR=.ai/approvals/$ID.md
MC=tools/gates/mutate_changed.py
RT=tools/gates/redteam/lib/rt.py
A34=tools/gates/redteam/attacks/34-v3-exempt-binding
A35=tools/gates/redteam/attacks/35-v3-changed-scope
COAUTH="Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
SUBJ_A="docs: $ID 문서 커밋(design 05 §10 V3 ① 대상 = 바뀐 문장과 주변·새 def 전체·대상 밖 not_targeted, 계획 N4.2 V3 대상 문구 -- 약화 승인 A1-b)"
SUBJ_B="docs: 게이트 변경 spec card $ID(V3 대상을 바뀐 문장·감싸는 제어문·뒤 문장·같은 블록 뒤쪽 이름 사용·머리 변경 몫·early_return으로, 데코레이터 변이 NOOP 수정) + interface card"
SUBJ_C="docs: 승인 기록 $ID(A1-b ② N2 + A1-b 정정, target_kind diff -- 판정 기준 적용 범위 축소(약화) 승인)"

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
# patch_v3_*_docs.py JSON 출력의 result 접두(+ plan_tables_hash.unchanged 단정)
patch_state() { "$PY" -B "$1" --root "$R" "${@:2}" | "$PY" -B -c "
import json,sys
r=json.load(sys.stdin)
u=r.get('plan_tables_hash',{}).get('unchanged')
assert u is True, ('plan_tables_hash', r.get('plan_tables_hash'))
print(r['result'].split('(')[0])"; }
approved_ids() { "$PY" -B -c "
import sys;sys.path.insert(0,sys.argv[1]);import reachability as r
print('\n'.join(sorted(r._approved_ids(sys.argv[2],sys.argv[3]))))" "$1" "$R" "$2"; }

# §0.4 자동 대조(A2·A3·A5·A7 + 실측 8 줄 번호 + 엔진 불변 + 이름 충돌). 묶기 card의 '의도한 결과'(그 spec card 계약 1~10, 키트 §2.1)와
# 다르면 멈춘다 -> 범위 spec card·브리프 문구를 병합본에 맞춘 뒤 다시(키트 §0.4 ⑤). A1·A4·A6은 사람 확인(끝에 출력).
binding_merged_check() {
  local C=$1 MREV=$2
  "$PY" -B - "$C" "$R" "$MREV" "$DRAFT_SPEC" "$MC" "$RT" "$BID" <<'EOF'
import ast, re, subprocess, sys
C, R, MREV, SPEC, MC, RT, BID = sys.argv[1:8]
sys.path.insert(0, C)
import reachability as rch

def show(rev, p):
    r = subprocess.run(["git", "-C", R, "show", "%s:%s" % (rev, p)], capture_output=True)
    assert r.returncode == 0, (rev, p, r.stderr[-300:])
    return r.stdout.decode("utf-8")

def git(*a):
    r = subprocess.run(["git", "-C", R] + list(a), capture_output=True)
    assert r.returncode == 0, (a, r.stderr[-300:])
    return r.stdout.decode("utf-8")

head_src, old_src = show("HEAD", MC), show(MREV, MC)
th, to = ast.parse(head_src), ast.parse(old_src)
fh = {n.name: n for n in th.body if isinstance(n, ast.FunctionDef)}
fo = {n.name: n for n in to.body if isinstance(n, ast.FunctionDef)}
# A7: 대상 선택·변이 생성·치환 함수가 card 측정 rev와 AST 동일(변이 id·실측 9·계약 9 전제)
a7 = ("_strip_doc", "def_hash", "changed_defs", "_float_unit", "_path_nodes", "_get", "mutants", "_replace_def")
diff7 = [n for n in a7 if n not in fh or ast.dump(fh[n]) != ast.dump(fo[n])]
assert not diff7, ("A7 깨짐 -- 묶기 병합본이 바꿨다(spec card 계약 9·실측 재측정 필요)", diff7)
main = fh["main"]
# A2: 정상 출력 json.dumps 키 순서 = 묶기 card 계약 6
outs = []
for n in ast.walk(main):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "dumps" and n.args \
            and isinstance(n.args[0], ast.Dict):
        ks = [k.value for k in n.args[0].keys if isinstance(k, ast.Constant)]
        if ks[:2] == ["tool", "verdict"] and not isinstance(n.args[0].values[1], ast.Constant):
            outs.append((ks, n.args[0]))
assert len(outs) == 1, ("A2 정상 출력 json.dumps가 하나가 아니다", [o[0] for o in outs])
keys, dct = outs[0]
want = ["tool", "verdict", "targets", "mutants", "killed", "survivors", "survivor_bindings", "exempt_ignored"]
assert keys == want, ("A2 출력 키 순서", keys)
# A3: mutants = 결과 레코드 수, exempt 레코드 {"id","result":"exempt","bind_hash"}
mv = dict(zip(keys, dct.values))["mutants"]
assert ast.unparse(mv) == "len(results)", ("A3 mutants", ast.unparse(mv))
ex = [n for n in ast.walk(th) if isinstance(n, ast.Dict) and [getattr(k, "value", None) for k in n.keys] == ["id", "result", "bind_hash"]
      and isinstance(n.values[1], ast.Constant) and n.values[1].value == "exempt"]
assert ex, "A3 exempt 레코드 {id, result: exempt, bind_hash} 없음"
# A1(일부): 옛 `if mid in approved` 분기가 없다(묶기 card가 대체) -- 나머지는 사람 확인
old_in = [n for n in ast.walk(main) if isinstance(n, ast.Compare) and isinstance(n.left, ast.Name) and n.left.id == "mid"
          and any(isinstance(o, ast.In) for o in n.ops)]
assert not old_in, "A1 옛 `mid in approved` 분기가 남아 있다"
# not_targeted 미구현(이 card 몫), 이름 충돌: tools/ 0, docs/는 묶기 spec card(용어 절 '대상 밖 변이는 면제 판정을 하지 않는다')만
assert "not_targeted" not in head_src and "targets_by_def" not in head_src and "def_header_changed" not in head_src, "도구에 이 card 이름이 이미 있다"
hits = subprocess.run(["git", "-C", R, "grep", "-l", "-E", "not_targeted|targets_by_def|def_header_changed", "HEAD", "--", "tools/", "docs/"],
                      capture_output=True).stdout.decode("utf-8").split()
hits = [h.split(":", 1)[1] for h in hits]
assert set(hits) <= {"docs/02-design/specs/%s.spec.md" % BID}, ("이름 충돌", hits)
# A5: rt.py out_jsonl 관찰(정적 -- 키 이름 문자열)
rts = show("HEAD", RT)
assert all(s in rts for s in ('"out_jsonl"', '"by_result"', '"lines"')), "A5 rt.py out_jsonl 관찰 문자열 없음"
# 실측 8 줄 번호: spec 초안이 인용하는 rev·줄 번호가 HEAD 도구와 같아야 한다
loop = [x for x in ast.walk(main) if isinstance(x, ast.For) and ast.unparse(x.target) == "path" and ast.unparse(x.iter) == "targets"]
assert len(loop) == 1, "main `for path in targets` 루프"
loop = loop[0]
rcs = [s for s in loop.body if isinstance(s, ast.Assign) and "cat-file" in ast.unparse(s)]
cds = [s for s in loop.body if isinstance(s, ast.For) and ast.unparse(s.iter).startswith("changed_defs(")]
assert len(rcs) == 1 and len(cds) == 1, ("base 읽기·changed_defs 호출 문장", len(rcs), len(cds))
a, b = rcs[0].lineno, cds[0].lineno
cd = fh["changed_defs"]
bm = [s for s in cd.body if isinstance(s, ast.Assign) and ast.unparse(s.targets[0]) == "bmap"]
bi = [s for s in cd.body if isinstance(s, ast.If) and "base_src is not None" in ast.unparse(s.test)]
c, d = bm[0].lineno, bi[0].end_lineno
spec = open(SPEC, encoding="utf-8").read()
m = re.search(r"`mutate_changed\.py` (\d+)~(\d+)행, `changed_defs` (\d+)~(\d+)행 -- `([0-9a-f]{7,40})` 줄 번호", spec)
assert m, "spec 초안 실측 8 줄 번호 문장 형식"
q = tuple(map(int, m.groups()[:4]))
qrev = git("rev-parse", "--verify", m.group(5) + "^{commit}").strip()
assert subprocess.run(["git", "-C", R, "merge-base", "--is-ancestor", qrev, "HEAD"]).returncode == 0, "실측 8 rev가 HEAD 조상이 아니다"
assert git("diff", "--name-only", qrev, "HEAD", "--", MC).strip() == "", \
    "실측 8 rev(%s) 뒤 도구가 바뀌었다 -- HEAD 줄 번호 %d~%d·%d~%d로 spec 초안 실측 8을 고친다" % (m.group(5), a, b, c, d)
assert q == (a, b, c, d), ("실측 8 줄 번호", q, (a, b, c, d))
# 계약 10 인용 줄: merge_gate N4.2 읽기 123~133·plan_tables_object 158~168
mgl = show("HEAD", "tools/gates/merge_gate.py").split("\n")
assert any('"### N4.2 "' in l for l in mgl[122:133]) and mgl[132].strip() == "v_intro[v] = o[0]", "merge_gate 123~133"
assert mgl[157].startswith("def plan_tables_object") and mgl[167].strip() == "}", "merge_gate 158~168"
# 엔진 불변(card 측정 rev -> HEAD, V3 대상 영역 = rch._is_source): B26-1·P9·B34 수치 그대로(키트 §0.2 끝)
eng = [p for p in git("diff", "--name-only", "--no-renames", MREV, "HEAD").split() if p.endswith(".py") and rch._is_source(p)]
assert not eng, ("card 측정 rev 뒤 V3 대상 영역 소스가 바뀌었다 -- B26-1 수치 재측정(measure_b26.py)", eng)
print("묶기 병합본 대조 OK: A7 함수 %d개 AST 동일(%s 대비), A2 키 %s, A3 mutants=len(results)·exempt 레코드, A1 옛 분기 없음, A5 rt.py, "
      "이름 충돌 docs %s, 실측 8 줄 %d~%d·%d~%d(%s), merge_gate 123~133·158~168, 엔진 불변" % (
      len(a7), MREV[:7], ",".join(keys[-2:]), hits or "0", a, b, c, d, m.group(5)))
EOF
}

stage_pre() {
  say "pre: 착수 전 확인(저장소 변경 없음)"
  test -n "$(git config --get user.email)"
  g fetch gate
  test "$(g rev-parse --abbrev-ref HEAD)" = master
  test "$(g rev-parse HEAD)" = "$(g rev-parse gate/master)"
  test -z "$(g for-each-ref refs/heads/role/)"                        # 역할 브랜치가 있으면 문서 push를 EL1이 거부(design 05 §12)
  if g worktree list --porcelain | grep -q -e "/$ID-" -e "/$BID-"; then echo "$ID/$BID worktree가 남아 있다" >&2; false; fi
  g diff --cached --quiet
  test -z "$(g status --porcelain -- docs/ .ai/approvals/ tools/)"
  test ! -e "$R/$F_SPEC"; test ! -e "$R/$F_IFC"; test ! -e "$R/$F_APR"; test ! -e "$R/$A35"
  for f in "$PATCH" "$BPATCH" "$FILL" "$DRAFT_SPEC" "$DRAFT_APR"; do test -s "$f"; done
  test "$(grep -c '<rev-parse>' "$DRAFT_APR")" = 3
  test "$(grep -c '^diff_path: ' "$DRAFT_APR")" = 4
  rm -f "$STATE"; mkdir -p "$T"
  # 묶기 card 병합·정리 끝(문서 3 + spec·interface·승인 + 판정 기록 + redteam 34)
  local f; for f in ".ai/approvals/$BID.md" "docs/02-design/specs/$BID.spec.md" "docs/02-design/specs/$BID.interface.md" \
      ".ai/verification/$BID.json" "$A34/v.json"; do
    test -n "$(g ls-tree --name-only HEAD -- "$f")" || { echo "묶기 card 병합 산출물 없음: $f" >&2; false; }
  done
  test "$(patch_state "$BPATCH" --check)" = already-applied
  # card 측정 rev(승인 초안 재측정 문단 = 단일 출처) -- 엔진 불변·A7 기준
  local ms; ms=$(grep -o 'gate `master` `[0-9a-f]\{7,40\}`에서 독립 프로토타입으로 다시 잼' "$DRAFT_APR" | head -1 | sed -E 's/^gate `master` `([0-9a-f]+)`.*/\1/')
  test -n "$ms"
  local mrev; mrev=$(g rev-parse --verify "$ms^{commit}"); g merge-base --is-ancestor "$mrev" HEAD
  local C H; C=$(cache_dir)
  binding_merged_check "$C" "$mrev"
  test "$(patch_state "$PATCH" --check)" = pending
  H=$(plan_hash "$C"); test ${#H} = 64
  st_set GATE_BASE "$(g rev-parse HEAD)"; st_set PLAN_HASH "$H"; st_set CACHE "$C"; st_set MREV "$mrev"
  approved_ids "$C" "$(g rev-parse HEAD)" > "$T/ids.base"
  st_set N_IDS "$(wc -l < "$T/ids.base" | tr -d ' ')"
  # 사람 확인(스크립트가 보지 않는 것 -- 키트 §0.4)
  echo "   [사람 확인] A1 면제 판정이 '변이 하나 -> (exempt | exempt_ignored 항목)' 한 곳에 있고 그 호출 앞에 대상 판정 자리, A4 exempt_ignored = 이번 실행(대상) 변이 id 규칙,"
  echo "               A6 병합된 $A34/v.json의 X·(c) 변이가 계약 1로 전부 대상(v3scope_kit/binding34_under_scope.py 방식), 계약 8 (a)·(k) out_jsonl 모양 = 병합본 rt.py"
  say "pre OK: gate master $(g rev-parse --short HEAD), _approved_ids $(st_get N_IDS), plan_tables_hash $H, cache $C, 측정 rev $ms"
}

stage_doc() {
  say "doc (A): design 05 §10 V3 ①·계획 N4.2 V3 대상 문구 -- Role: doc"
  test "$(g rev-parse HEAD)" = "$(st_get GATE_BASE)"
  g diff --cached --quiet
  local before05; before05=$(grep -F '`mutate_changed.py`(V3)' "$R/$D05" | tr -d '\r')
  test "$(patch_state "$PATCH" --check)" = pending
  test "$(patch_state "$PATCH")" = applied
  test "$(patch_state "$PATCH" --check)" = already-applied             # 재실행 멱등
  g add -- "$PLAN" "$D05"
  staged_is "$PLAN" "$D05"
  numstat_is "$PLAN" "1 1"; numstat_is "$D05" "1 1"
  local H; H=$(plan_hash "$(st_get CACHE)"); test "$H" = "$(st_get PLAN_HASH)"   # 판정 표 불변 -> plan_tables 승인 불필요
  # spec card 계약 10 인용문 2개가 패치된 두 행 안에 그대로, design 05 V3 행 `|` 개수 불변(sim_sequence.py와 같은 판정)
  "$PY" -B - "$DRAFT_SPEC" "$R/$D05" "$R/$PLAN" "$before05" <<'EOF'
import re, sys
t = open(sys.argv[1], encoding="utf-8").read()
para = re.search(r"\n10\. \*\*문서\*\*: (.*?)\n\n", t, re.S).group(1)
ls = [l.strip() for l in para.split("\n")]
j = ls[0]
for l in ls[1:]:
    j += ("" if j.endswith("·") or l.startswith("(") else " ") + l
qs = re.findall(r'"(① 대상 =.*?\(판정 제외\))"', j) + re.findall(r'"(대상 = diff가 닿은 def 중 AST 해시가 바뀐 것의.*?\(대상 밖 변이는 실행하지 않고 id를 출력\))"', j)
l05 = [l for l in open(sys.argv[2], encoding="utf-8").read().split("\n") if "`mutate_changed.py`(V3)" in l]
lpl = [l for l in open(sys.argv[3], encoding="utf-8").read().split("\n") if l.startswith("| V3 | 뮤테이션 |")]
assert len(qs) == 2 and len(l05) == 1 and len(lpl) == 1, (len(qs), len(l05), len(lpl))
assert qs[0] in l05[0] and qs[1] in lpl[0], "계약 10 인용문이 패치된 행에 없다"
assert l05[0].rstrip("\r").count("|") == sys.argv[4].count("|"), "design 05 V3 행 | 개수"
print("계약 10 인용문 OK (%d자·%d자), design 05 V3 행 | %d개 불변" % (len(qs[0]), len(qs[1]), sys.argv[4].count("|")))
EOF
  g commit -q -m "$SUBJ_A" \
    -m "_drafts/patch_v3_scope_docs.py 적용(spec card $ID 계약 10 문구 그대로, 파일마다 한 줄 교체, 줄 끝 보존, 선행 = $BID 문서 문구). 판정 표 무변경(plan_tables_hash $H). 승인 기록 $ID가 이 커밋의 부모를 diff_base로 가리킨다." \
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
  test "$(grep -c '^| `' "$R/$F_IFC" || true)" = 0                   # 기존 함수·신규 시그니처 0행(게이트 card -- 두 표 빈 모양)
  test "$(wc -l < "$R/$F_IFC" | tr -d ' ')" = 13                       # 게이트 card 선례 모양(키트 §0.3, 묶기 card 모의 13줄)
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
  "$PY" -B "$FILL" --root "$R" --draft "$DRAFT_APR" --base "$base" --head "$head" > "$T/fill.json"
  "$PY" -B -c "import json,sys;r=json.load(open(sys.argv[1],encoding='utf-8'));assert r['result']=='written',r;print('fill OK',r['target'])" "$T/fill.json"
  # target 독립 재계산(캐시 판 weakening_diff -- fill은 작업 트리 tools/gates를 읽는다)
  tgt=$("$PY" -B -c "
import sys,re;sys.path.insert(0,sys.argv[1]);import weakening_diff as wd
t=open(sys.argv[5],encoding='utf-8').read().split('\n---\n',1)[0]
print(wd.diff_hash(sys.argv[2],sys.argv[3],sys.argv[4],re.findall(r'^diff_path: (.+)\$',t,flags=re.M)))" "$C" "$R" "$base" "$head" "$DRAFT_APR")
  test "${#tgt}" = 64
  "$PY" -B "$C/merge_gate.py" parse-approval "$R/$F_APR" > "$T/appr.json"
  "$PY" -B -c "
import json,sys
r=json.load(open(sys.argv[1],encoding='utf-8'))
paths=['$PLAN','$D05','$F_IFC','$F_SPEC']
exp=dict(id=sys.argv[2],date='2026-10-01',target_kind='diff',target=sys.argv[3],diff_base=sys.argv[4],diff_head=sys.argv[5],diff_path=paths)
bad={k:(r.get(k),v) for k,v in exp.items() if r.get(k)!=v}
assert not bad,bad
print('parse_approval_header OK',r['target_kind'],r['target'][:12],r['diff_base'][:7],r['diff_head'][:7],len(r['diff_path']))
" "$T/appr.json" "$ID" "$tgt" "$base" "$head"
  # 바이트 단정: BOM 없음, CR 0, HTML 주석·자리표시 0, '약화 승인' 범위 설명(MSYS2 grep의 CR 패턴 문제 -- Python으로)
  "$PY" -B -c "
import sys
b=open(sys.argv[1],'rb').read()
bad=[k for k,v in (('BOM',b.startswith(b'\xef\xbb\xbf')),('CR',b'\r' in b),('주석',b'<!--' in b),('자리표시',b'<rev-parse>' in b),
                   ('약화 승인 문구 없음','판정 기준 적용 범위 축소(약화) 승인'.encode() not in b)) if v]
assert not bad,bad
print('승인 기록 바이트 OK',len(b))" "$R/$F_APR"
  g add -- "$F_APR"
  staged_is "$F_APR"
  g commit -q -m "$SUBJ_C" \
    -m "사용자 2026-10-01 A1-b \"② N2 (Recommended)\"와 A1-b 정정 \"규칙을 안내에 맞게 넓힘 (Recommended)\" 원문 인용. target = weakening_diff.diff_hash(diff_base = 문서 커밋의 부모, diff_head = spec+interface card 커밋, diff_path 4개) = $tgt (merge_gate.compute_diff_hash와 같은 값). 약화(판정 기준 적용 범위 축소) -- DEC-40 매 건 사용자 승인." \
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
  test "$(g diff-tree --no-commit-id --name-only -r "$(st_get A)" | sort | tr '\n' ' ')" = "$(printf '%s\n' "$PLAN" "$D05" | sort | tr '\n' ' ')"
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
  approved_ids "$C" "$(st_get C)" > "$T/ids.head"
  cmp "$T/ids.base" "$T/ids.head"                                      # V3·V4·V7 decision 원소 불변(diff 기록은 원소 아님)
  test "$(patch_state "$PATCH" --check)" = already-applied
  test "$(patch_state "$BPATCH" --check)" = already-applied
  test "$(plan_hash "$C")" = "$(st_get PLAN_HASH)"
  test -z "$(g status --porcelain -- docs/ .ai/approvals/ tools/)"
  g log --format='%h %s' "$base..HEAD"
  say "final OK -- 다음은 push 단독 호출(병렬·tail 금지):  git -C $R push gate master:master"
  echo "   (승인 초안 끝 주석의 사용자 고지 -- B26-1 대상 수 -- 는 기록에서 지워졌다: 사용자 보고로 따로, 브리프 §0.2·§0.5 4)"
}

stage_after_push() {
  say "after-push: gate master 대조"
  g fetch gate
  test "$(g rev-parse gate/master)" = "$(st_get C)"
  test "$(g rev-parse HEAD)" = "$(g rev-parse gate/master)"
  test "$(g ls-tree --name-only gate/master -- "$F_APR" "$F_SPEC" "$F_IFC" | sort | tr '\n' ' ')" = "$(printf '%s\n' "$F_APR" "$F_SPEC" "$F_IFC" | sort | tr '\n' ' ')"
  test -z "$(g status --porcelain -- docs/ .ai/approvals/ tools/)"
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
