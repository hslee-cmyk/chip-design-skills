# V3 두 card 문서 커밋 계획 -- `20260930-v3-exempt-binding` → `20260930-v3-changed-stmt-scope`

작성 2026-10-01. 측정 기준: gate `master` `2d58fd8`(작업 시작 시점). 작업 중 master가 `62ae24f`(P10 test·audit 커밋, 문서 3개는 그대로)로 움직였고, 그 트리에서 `--check`를 다시 돌려 같은 결과를 확인했다.
scratch는 `C:/g81`(격리 복제본 `repo_lf`·`repo_crlf`·`repo_seq`, origin 제거, hooksPath는 빈 폴더)만 썼고 끝나면 지웠다. 저장소 쓰기·상태 변경 git 없음(`--check`는 읽기 전용).

## 0. 산출물

| 파일 | 내용 |
|---|---|
| `patch_v3_binding_docs.py` | card (1) 계약 10 문서 문구 3곳(design 05 §10 V3 ⑤ 면제, design 10 382행, 계획 N4.2 V3 면제) |
| `patch_v3_binding_docs.diff.txt` | 위 패치 결과 `git diff -U0`(base `2d58fd8`) |
| `patch_v3_scope_docs.py` | card (2) 계약 10 문서 문구 2곳(design 05 §10 V3 ①, 계획 N4.2 V3 '대상 ='). **card (1) 문구가 있어야만** 적용 |
| `patch_v3_scope_docs.diff.txt` | card (1) 결과 위에 적용한 `git diff -U0` |
| `fill_v3_approval.py` | 승인 기록 초안의 `<rev-parse>` 세 자리를 채워 `.ai/approvals/<id>.md` 작성(아래 3절) |

패치 스크립트 성질(두 개 같음): UTF-8 바이트 치환, 바꾸는 문자열에 개행이 없어 줄 끝(worktree CRLF, blob LF)을 그대로 둔다. 치환마다 `old` 정확히 1회·`new` 0회 = pending, `old` 0회·`new` 1회 = applied,
그 밖은 거부. 전부 applied면 아무것도 쓰지 않고 exit 0(멱등), pending과 applied가 섞이면 거부(exit 2), 모든 파일 내용을 만들고 검사(줄 수 불변, 바뀐 줄 파일당 1줄, 줄 끝 종류·BOM 불변, UTF-8,
표 `|` 개수 불변은 test에서)를 통과한 뒤에만 쓴다(파일마다 임시 파일 → `os.replace`). 계획서를 바꾸면 `<root>/tools/gates/merge_gate.plan_tables_hash`를 앞뒤로 계산해 다르면 거부한다. `--check`는 쓰지 않는다.

## 1. 문서 문구(card 계약 10 인용 그대로)

card 인용문이 줄바꿈된 자리는 다음처럼 이었다(판단 -- 오케스트레이터가 확인할 것):
`원소 =`|`` `<변이 id>`` → 공백, `같을`|`때만` → 공백, `면제는`|`승인` → 공백, `바뀐 문장·`|`감싸는` → **붙임**(`·` 뒤), `데코레이터`|`인자` → 공백, `새 def는 전체`|`(대상 밖` → **붙임**(괄호 앞).
패치의 `new` 문자열이 card 인용문 전체를 포함함을 대조 스크립트로 확인했다(card (1) 267·107·47자, card (2) 356·129자 인용 모두 `new` 안에 있음). 앞뒤에 붙인 원문(`. 자체 AST 변이기(DEC-39) |`,
`살아남은 변이가 있으면 FAIL. `, `. 변이는 worktree 밖 임시 복사본에서`, ` ② 연산자:`, `| V3 | 뮤테이션 | `, `. 연산자 =`)은 유일성 앵커일 뿐 바뀌지 않는다.

### card (1) `20260930-v3-exempt-binding`

| 곳 | 원문 | 새 문구 |
|---|---|---|
| design 05 317행(§10 V3 ⑤ 뒤) | 등가 변이 면제는 `target_kind: decision`, `target` = 변이 id 목록인 승인 기록 | 등가 변이 면제는 `target_kind: decision`, `target` 원소 = `<변이 id>@<묶기 해시>`(승인할 때 head def 노드 원본 -- docstring 포함 -- 의 `ast.dump` sha256, 정의: spec card `20260930-v3-exempt-binding`)인 승인 기록 -- head의 그 def 묶기 해시가 같을 때만 적용. 해시가 없거나 다르거나 형식이 틀린 원소는 적용하지 않고 출력 `exempt_ignored`에 싣는다 |
| design 10 382행(§6.7 IC3 C8 끝) | `target_kind: decision` 승인 기록(변이 id 목록)으로만 면제한다(N4.2 V3) | `target_kind: decision` 승인 기록으로만 면제한다(N4.2 V3. 원소 형식은 design 05 §10 V3 ⑤ -- 2026-10-01부터 `<변이 id>@<묶기 해시>`) |
| 계획 839행(N4.2 V3) | 등가 변이 면제는 승인 기록으로만 | 등가 변이 면제는 승인 기록으로만(변이 id와 그 def의 AST 묶기 해시에 묶임) |

### card (2) `20260930-v3-changed-stmt-scope`(card (1) 결과 위)

| 곳 | 원문 | 새 문구 |
|---|---|---|
| design 05 317행 ① | ① diff가 닿은 `def` 중 `ast.dump`(docstring 제외) 해시가 base와 다른 것 | ① 대상 = diff가 닿은 `def` 중 `ast.dump`(docstring 제외) 해시가 base와 다른 것. 새 def는 본문 전체, 기존 def는 base와 문장 단위로 맞춘 바뀐 문장·감싸는 제어문·바꾸거나 지운 문장 자리 바로 뒤 문장·바뀌거나 지운 문장이 바꾸는 이름을 같은 블록 뒤쪽(반복문 본문이면 그 본문 전체)에서 읽는 문장·def 머리가 바뀌면 그 자기 필드(기본값·데코레이터 인자·주석)와 바뀐 매개변수를 읽는 문장, 그리고 `early_return`(정의: spec card `20260930-v3-changed-stmt-scope` 계약 1). 대상 밖 변이는 실행하지 않고 수와 id를 출력한다(판정 제외) |
| 계획 839행(N4.2 V3) | 대상 = diff가 닿은 def 중 AST 해시가 바뀐 것 | 대상 = diff가 닿은 def 중 AST 해시가 바뀐 것의 바뀐 문장과 그 주변(정의: spec card `20260930-v3-changed-stmt-scope`), 새 def는 전체(대상 밖 변이는 실행하지 않고 id를 출력) |

두 card의 문구는 겹치지 않는다(같은 줄 317·839에서 서로 다른 구간). 새 문구에 `|`가 없어 표 칸 수가 그대로다(test로 확인).

## 2. 판정 표·다른 해시 입력 확인

* **`plan_tables_hash` 불변**: 패치 앞 `7167e028…6d2596d`, card (1) 뒤·card (2) 뒤 모두 같은 값(`merge_gate.plan_tables_hash`, 계획 839행은 N4.2 'V3' 행의 세 번째 칸이고 해시 입력 `v_intro`는 '도입' 칸만).
  → **`plan_tables` 승인 불필요.** 패치 스크립트가 적용 때 다시 계산해 바뀌면 거부한다.
* design 05·design 10은 게이트 도구가 파싱하지 않는다(`tools/gates` 중 문서 경로를 읽는 것은 `role_paths.PLAN_PATH`(계획서)뿐 -- `grep`), integrity·gate_config에도 문서 경로 없음.

## 3. 커밋 순서 -- 요청 순서와 다른 점(중요)

요청 순서 "문서 커밋 → 승인 기록 → spec+interface card 커밋"은 **그대로는 성립하지 않는다**: 승인 초안 `diff_path`에 spec card·interface card가 들어 있고, `merge_gate.compute_diff_hash`는
`diff_base..diff_head`에서 바뀌지 않은 경로를 거부한다(`diff_path가 바뀌지 않았다`). 승인 기록보다 뒤에 커밋되는 파일은 그 범위에 넣을 수 없다.
그래서 **문서 커밋(A) → spec+interface card 커밋(B) → 승인 기록 커밋(C, `diff_base` = A의 부모, `diff_head` = B)** 으로 한다. 선례: `20260930-v3-history-clone`(spec card + design 05가 `d99919c`,
승인이 뒤 `ab90ec5`), `20260930-phase2-e4-phase`(문서 `fe638ab` 뒤 승인 `2d58fd8`). A와 B를 한 커밋으로 합쳐도 된다(`diff_head` = 그 커밋).

**격리 모의(`C:/g81/repo_seq`, 실제 저장소 복제, push 제외)로 두 card 시퀀스를 끝까지 돌렸다**: 패치 → A → spec 사본 + `interface_card.py` → B → `fill_v3_approval.py` → C. 결과:
`gate_change_ok` True(두 card), 승인 기록 머리 파싱 통과, `weakening_diff.diff_hash` == `merge_gate.compute_diff_hash` == 기록 `target`, `weakening_diff.approved_hashes(HEAD)`에 target 포함,
`parse_spec_card` 통과(phase 0.5, red-green, gate_change yes, approval = 자기 id, 절 11개). interface card는 13줄(기존 함수 0개, 신규 시그니처 빈 표 -- 게이트 card 선례 `20260921-gate-output-utf8`과 같은 모양).
(모의 해시는 예시일 뿐이다 -- 실제 값은 실제 커밋 id로 다시 계산된다.)

**card (2)는 card (1)의 순서 8(gate push)과 정리가 끝난 뒤에 시작한다**: (가) design 05 §12 "역할 브랜치가 있는 동안 문서 커밋의 gate push는 EL1이 거부" (나) card (2) redteam이 card (1)의
rt.py `out_jsonl` 관찰을 쓴다 (다) 패치 스크립트가 card (1) 문구 없이는 거부한다. 지금 `role/*` 브랜치는 없다(`git branch --list 'role/*'` 0개, 2026-10-01 확인 -- 착수 직전에 다시 볼 것).

## 4. 명령 시퀀스(오케스트레이터, MSYS bash)

공통 변수(각 블록 앞에 둔다 -- 셸 상태는 이어지지 않는다):

```bash
set -euo pipefail
R=/c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
W=/c/Users/HSLEE/Documents/Todoc/fpga/wt
DR=$W/_drafts
PY="/c/Python314/python.exe -B"
```

### 4.0 착수 전 확인(두 card 각각)

```bash
git -C "$R" fetch gate
test "$(git -C "$R" rev-parse --abbrev-ref HEAD)" = master
test "$(git -C "$R" rev-parse HEAD)" = "$(git -C "$R" rev-parse gate/master)"
test -z "$(git -C "$R" branch --list 'role/*')"
test -z "$(git -C "$R" status --porcelain -- docs/ .ai/approvals/)"
```

### 4.1 card (1) `20260930-v3-exempt-binding`

```bash
ID=20260930-v3-exempt-binding
BASE=$(git -C "$R" rev-parse HEAD)
# A. 문서 커밋
$PY "$DR/patch_v3_binding_docs.py" --root "$R" --check      # pending 3개, plan_tables_hash unchanged true 확인
$PY "$DR/patch_v3_binding_docs.py" --root "$R"              # result applied
git -C "$R" diff --stat                                      # 문서 3개, 각 1줄
git -C "$R" add -- docs/01-plan/features/gain-budget-gmid-sizing.plan.md \
  docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md \
  docs/02-design/features/gain-budget-gmid-sizing.10-test-separation.design.md
git -C "$R" commit --trailer "Role: doc" -m "docs: $ID 문서 커밋(design 05 §10 V3 ⑤ 면제 원소 = 변이 id@묶기 해시, design 10 §6.7 IC3 382행 원소 형식 이관, 계획 N4.2 V3 면제 묶임 문구)"
# B. spec card + interface card 커밋
cp "$DR/draft_v3_exempt_binding.spec.md" "$R/docs/02-design/specs/$ID.spec.md"
(cd "$R" && $PY tools/gates/interface_card.py "docs/02-design/specs/$ID.spec.md" --root . --out "docs/02-design/specs/$ID.interface.md")
git -C "$R" add -- "docs/02-design/specs/$ID.spec.md" "docs/02-design/specs/$ID.interface.md"
git -C "$R" commit --trailer "Role: doc" -m "docs: 게이트 변경 spec card $ID(V3 등가 변이 면제를 변이 id@def 묶기 해시에 묶음, 해시 다름·없음·형식 오류는 exempt_ignored, exempt를 --out에 기록) + interface card"
SPECC=$(git -C "$R" rev-parse HEAD)
# C. 승인 기록(target = weakening_diff.diff_hash(BASE, SPECC, diff_path 5개), compute_diff_hash로 재대조, 머리 파싱)
$PY "$DR/fill_v3_approval.py" --root "$R" --draft "$DR/approval_$ID.md" --base "$BASE" --head "$SPECC"
git -C "$R" add -- ".ai/approvals/$ID.md"
git -C "$R" commit --trailer "Role: doc" -m "docs: 승인 기록 $ID(A1-a, target_kind diff -- spec card·interface card·design 05 ⑤·design 10 382행·계획 N4.2 V3 면제 문구, 강화)"
# 확인(되돌릴 수 있는 지점 -- push 전)
(cd "$R" && $PY -P -c "import sys;sys.path.insert(0,'tools/gates');import merge_gate as mg;print(mg.gate_change_ok(mg.TreeView(['-C','.'],'HEAD'),'$ID'))")   # True
# D. push -- 단독 실행, 전체 출력 확인(병렬·tail 금지)
git -C "$R" push gate master:master
git -C "$R" fetch gate
git -C "$R" merge --ff-only gate/master
test "$(git -C "$R" rev-parse HEAD)" = "$(git -C "$R" rev-parse gate/master)"
# E. test worktree(design 05 §12 순서 1)
git -C "$R" worktree add "$W/$ID-test" -b "role/test/$ID" gate/master
```

이어서 §12 순서 2~8(test-author → auditor freeze → code-author → 병합 → auditor 판정 → `push gate role/audit/$ID:master`) → 정리(worktree·브랜치 삭제)까지 끝낸 뒤 4.2로 간다.

### 4.2 card (2) `20260930-v3-changed-stmt-scope`(card (1) 병합·정리 뒤)

```bash
ID=20260930-v3-changed-stmt-scope
BASE=$(git -C "$R" rev-parse HEAD)
$PY "$DR/patch_v3_scope_docs.py" --root "$R" --check        # 선행 card 문구 확인 + pending 2개 + plan_tables_hash unchanged
$PY "$DR/patch_v3_scope_docs.py" --root "$R"
git -C "$R" diff --stat                                      # 문서 2개, 각 1줄
git -C "$R" add -- docs/01-plan/features/gain-budget-gmid-sizing.plan.md \
  docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md
git -C "$R" commit --trailer "Role: doc" -m "docs: $ID 문서 커밋(design 05 §10 V3 ① 대상 = 바뀐 문장과 주변·새 def 전체·대상 밖 not_targeted, 계획 N4.2 V3 대상 문구 -- 약화 승인 A1-b)"
cp "$DR/draft_v3_scope_policy.spec.md" "$R/docs/02-design/specs/$ID.spec.md"
(cd "$R" && $PY tools/gates/interface_card.py "docs/02-design/specs/$ID.spec.md" --root . --out "docs/02-design/specs/$ID.interface.md")
git -C "$R" add -- "docs/02-design/specs/$ID.spec.md" "docs/02-design/specs/$ID.interface.md"
git -C "$R" commit --trailer "Role: doc" -m "docs: 게이트 변경 spec card $ID(V3 대상을 바뀐 문장·감싸는 제어문·뒤 문장·같은 블록 뒤쪽 이름 사용·머리 변경 몫·early_return으로, 데코레이터 변이 NOOP 수정) + interface card"
SPECC=$(git -C "$R" rev-parse HEAD)
$PY "$DR/fill_v3_approval.py" --root "$R" --draft "$DR/approval_$ID.md" --base "$BASE" --head "$SPECC"
git -C "$R" add -- ".ai/approvals/$ID.md"
git -C "$R" commit --trailer "Role: doc" -m "docs: 승인 기록 $ID(A1-b ② N2 + A1-b 정정, target_kind diff -- 판정 기준 적용 범위 축소(약화) 승인)"
(cd "$R" && $PY -P -c "import sys;sys.path.insert(0,'tools/gates');import merge_gate as mg;print(mg.gate_change_ok(mg.TreeView(['-C','.'],'HEAD'),'$ID'))")   # True
git -C "$R" push gate master:master
git -C "$R" fetch gate
git -C "$R" merge --ff-only gate/master
test "$(git -C "$R" rev-parse HEAD)" = "$(git -C "$R" rev-parse gate/master)"
git -C "$R" worktree add "$W/$ID-test" -b "role/test/$ID" gate/master
```

`fill_v3_approval.py`: `--base`/`--head`를 rev-parse로 40자리로 바꾸고, target을 `weakening_diff.diff_hash`로 계산해 `merge_gate.compute_diff_hash`(바뀌지 않은 경로·양쪽 없음 거부)와 대조,
초안 끝 `<!-- 오케스트레이터: … -->` 주석은 지우고(선례 기록에 없음), LF·BOM 없이 쓴 뒤 `parse_approval_header`로 다시 파싱한다. 대상 파일이 이미 있고 내용이 다르면 거부, 같으면 멱등.

## 5. 커밋 전에 오케스트레이터가 처리할 것

1. **card (2) 의도 절 원문 인용 오류(실측)**: `draft_v3_scope_policy.spec.md` 28행 인용 "① diff가 닿은 `def` 중 `ast.dump`(docstring 제외) 해시가 base와 다른 것**(새 def 포함)** ②"의
   "(새 def 포함)"은 design 05 317행에 없다(`git log -S` 이력 0건, HEAD 문장은 "…다른 것 ② 연산자: …"). '약화인가 -- 원문 대조' 절이라 커밋 전에 "(새 def 포함)"을 지울 것을 권한다(패치 동작과 무관 --
   패치의 `old`는 실제 원문).
2. 줄바꿈 이음 두 곳(`문장·감싸는`, `전체(대상 밖`)이 의도와 맞는지 확인(1절). 다르면 `patch_v3_scope_docs.py`의 `new` 한 곳만 고치고 `C:/g81` 같은 격리 복제본에서 다시 시험.
3. card (2) 승인 초안 끝 주석의 **사용자 고지**("B26-1 수치 228 → 294, 현실 하한 0.6 h → 0.9 h")는 기록에서 지워지므로 사용자 보고로 따로 한다. B26-1 card V3 수치 갱신·history H 절(v1·v2 정의·옛 수치)·
   백로그 B41·B45·B46은 이 두 패치 범위 밖(history를 같은 커밋에 넣으면 승인 `diff_path`에는 넣지 않는다 -- 넣으려면 초안 `diff_path`도 고쳐야 한다).
4. `.ai/context.md`에 진행을 적으면 Python 바이너리 append로만(heredoc 금지), `git diff --numstat` 삭제 0줄 확인.

## 6. 시험 기록(`C:/g81`, 끝나고 삭제)

* `test_patches.py`(LF 복제본·CRLF 복제본 각각): card (2) 먼저 → 거부·무쓰기, card (1) `--check` pending·무쓰기, 적용 → 파일당 1줄(317·382·839), 멱등, design 10만 되돌린 부분 상태 →
  card (1) 거부·card (2) 거부, card (2) `--check`·적용 → 317·839, design 10 불변, 멱등, card (1) 재실행 already-applied, 줄 끝 개수 보존, V3 표 행 `|` 개수 보존, LF·CRLF 결과 정규화 동일 -- **실패 0**.
* LF 정규화 sha256(계획/05/10): 앞 `78ad5194…`/`bf0e7c9e…`/`4350783b…` → card (1) 뒤 `169f0e74…`/`8097991c…`/`fb0f1870…` → card (2) 뒤 `0db2cc87…`/`1b777253…`/(불변).
* 머리 검증: 두 spec card `parse_spec_card` 통과, 두 승인 초안은 더미 해시(64·40자리)로 `parse_approval_header` 통과(diff_path 5·4개), 원본 초안(`<rev-parse>`)은 예상대로 거부.
* `repo_seq` 모의 시퀀스: 3절 결과. 실제 저장소 `--check`(master `62ae24f`): card (1) pending 3·plan_tables_hash 불변, card (2) 선행 card 문구 없음으로 거부(정상).
