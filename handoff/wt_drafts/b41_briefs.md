# B41 scope_note test card `20261002-b41-scope-note-test` -- 착수 키트(두 역할 브리프 + 착수 확인)

작성 2026-10-02. 측정 판: gate `master` `4a286f0`. 저장소 쓰기·상태 변경 git 없음. 측정은 격리 복제본 `C:/g232`(origin 제거, `core.autocrlf=false`, 측정 뒤 삭제)에서만.
대상 산출물: `draft_b41_scope_note.spec.md`. test-only라 code-author 브리프가 없다(K 없음). 측정 시제품·스크립트는 `C:/g232`에서 만들고 지웠다(키트 사본 없음 -- B41 분석 키트 `_drafts/b41_kit/`는 `36e170e` 판, 이 card 시제품과 다르다).
자리: Phase 4, **#2(`20261002-d4-delete-unwired`) 앞**(Phase 4 첫 card). 사용자 결정 없음(원칙 기본안 -- card '결정 필요 항목').
(r1b, 2026-10-02) 독립 검토 `review_b41.md` 반영: card S1(추적 instance.json 12 = workspaces 6 + 판정 기록 einst 6, 모두 키 없음 -- 재측정)·m1~m4, 이 키트 m5(§0.1-1 B41a). 원본 `b41_briefs.pre-r1b.bak`·`draft_b41_scope_note.spec.pre-r1b.bak`.

---

**(gate master fd4ef8c 재측정 2026-10-06)**: gate `master` `fd4ef8c`(card 35 병합 -- V3가 바뀐 문장 범위만 실행, 출력에 `not_targeted`·`targets_by_def`)에서 격리 복제본 `C:/g286`(끝나면 삭제)으로 card 사전 측정을 다시 했다(card '재현할 수치'·'작성 전 실측'의 같은 제목 문단). 반영 전 사본 `*.pre-fd4.bak`. 브리프 문장 변경: 2.2 V3·V10 행에 card 35 출력 키, 아래 0.2-5·2.1 끝 순서 3 커밋 금지 근거. 계약·역할 경계 변경 0.
* `bind_hash(save_instance_json)` = `4a96ecf0…`(0.2-3 기대값 그대로), interface card 2행, 시제품 37 passed, 변이 표 그대로, 이 card V3 = `targets` []·`mutants` 0·`not_targeted` 0·`targets_by_def` {}.
* F2 뒤 다시 볼 것은 0.2 그대로(정의 파일·interface card 모듈·`bind_hash`·변이 id 접두) + V3를 그때 gate 도구로.

## 0. 착수 확인(오케스트레이터)

### 0.1 card 전에 할 문서 일(오케스트레이터, Change-Id 없는 문서 커밋 -- card 계약 7 범위 밖)

1. design 40 초안 §3.3 '[Phase 4 선두, 순서 고정]'에 `B41(test-only) ─> #2`를 넣고, "Phase 4 첫 card = #2" 문장을 "첫 card = B41 test-only, 다음 #2"로, §5 표에 행 추가, §1.4의 B41 문장을 "B41 scope_note 몫 = `20261002-b41-scope-note-test`, indent 몫 = `with` 블록을 바꾸는 첫 card의 승인, 빈 문자열·비 str `scope_note` 동작 = 백로그 B41a(의도 확인 뒤 별도 card)"로. **UD-0 질문 전에**(사용자가 design 승인으로 순서를 본다).
   **(r1b) 반영 완료**: design 40 초안 v0.9.10(§1.4 B41 문장 -- B41a 포함, §1.5-1·§3.3 'B41 → #2', §5.1 B41 행·#2 행 (i)).
2. 백로그: B41 항목에 처리 방침(위 1), 새 후보 B41a(빈 문자열 `scope_note`를 버림 -- docstring '그대로 옮겨 쓴다'와 어긋나 보임).
3. #2 초안(`draft_p4_first.spec.md`) 'P3 -- Phase 3 뒤 다시 잴 것'에 "B41 card 병합 뒤 base 전체 suite +37 passed" 한 줄(그 card의 수치는 어차피 base에서 다시 잰다).

### 0.2 착수 직전에 다시 볼 것(하나라도 어긋나면 멈추고 card '작성 전 실측' P 항목 재측정)

1. card '착수 조건' 1~5(명령은 card 본문 그대로).
2. 정의 파일·interface card: gate master 사본에서 게이트 캐시 `interface_card.py`로 만든 표가 **2행**(`save_instance_json`·`run_topology_pipeline`, 모듈은 R-DEF 정의 파일)인지. 3행 이상이면 계약 절 백틱 토큰이 새 엔진 def와 겹친 것 -- 토큰을 고친다.
3. `bind_hash(save_instance_json)`가 `4a96ecf0e82205e0828ea62f88e187b83a1096d557a97ae0b410b9f3cce2ceee`와 같은지(다르면 docstring만 바뀌었는지 보고 '거부해야 할 입력' 변이 경로를 다시 잰다).
4. 셸 가드: 절대 경로·`git -C`만, `(cd … && …)` 금지(role_guard), 상대 경로 쓰기 금지.
5. (gate master fd4ef8c 재측정 2026-10-06) 게이트 캐시 `mutate_changed.py`가 card 35 판인지: `grep -c not_targeted "$CACHE/mutate_changed.py"` ≥ 1(아니면 2.2 V3 행의 출력 키가 없다 -- 캐시를 gate master로 다시 만든다).

### 0.3 명령 시퀀스(MSYS bash -- 0.2 통과 뒤)

```bash
R=/c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
DR=/c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts
W=/c/Users/HSLEE/Documents/Todoc/fpga/wt
PY=C:/Python314/python.exe
ID=20261002-b41-scope-note-test
git -C "$R" fetch gate
test "$(git -C "$R" rev-parse HEAD)" = "$(git -C "$R" rev-parse gate/master)"
test -z "$(git -C "$R" for-each-ref refs/heads/role/)"
GM=$(git -C "$R" rev-parse gate/master)
CACHE=$(git -C "$R" rev-parse --path-format=absolute --git-common-dir)/gmid-gate-cache/$GM
test -f "$CACHE/interface_card.py"
# spec card + interface card (Role: doc, Change-Id: $ID)
cp "$DR/draft_b41_scope_note.spec.md" "$R/docs/02-design/specs/$ID.spec.md"
$PY -B "$CACHE/interface_card.py" "$R/docs/02-design/specs/$ID.spec.md" --root "$R" --out "$R/docs/02-design/specs/$ID.interface.md"
grep -c '^| `' "$R/docs/02-design/specs/$ID.interface.md"     # 2 (관찰 가능한 계약 표 행)
git -C "$R" add -- "docs/02-design/specs/$ID.spec.md" "docs/02-design/specs/$ID.interface.md"
git -C "$R" commit --trailer "Role: doc" --trailer "Change-Id: $ID" -m "docs: test-only spec card $ID(B41 save_instance_json scope_note 선택 키 복사 계약 test) + interface card"
# push -- 단독 실행, 전체 출력 확인
git -C "$R" push gate master:master
git -C "$R" fetch gate
test "$(git -C "$R" rev-parse HEAD)" = "$(git -C "$R" rev-parse gate/master)"
git -C "$R" worktree add "$W/$ID-test" -b "role/test/$ID" gate/master
```

이어서 순서 2(test-author, 1절) → 3(auditor freeze·base 확인, 2.1) → (순서 7 전 오케스트레이터: `git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261002-b41-scope-note-test-audit log --oneline role/test/20261002-b41-scope-note-test..HEAD` 출력이 비어야 한다 -- 비어 있지 않으면 순서 3 커밋이 섞인 것, 판정 커밋 전에 멈춤) → 7(auditor 판정, 2.2) → 8(`push gate role/audit/$ID:master`) → 정리. code worktree 없음.

---

## 1. test-author 브리프(gmid-test-author)

```
역할: gmid-test-author. change id = 20261002-b41-scope-note-test (test-only, phase 4).
worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261002-b41-scope-note-test-test (브랜치 role/test/20261002-b41-scope-note-test). 모든 명령은 절대 경로(git -C, cd 금지).
쓰기 경로: skills/analog-gmid-design/assets/tests/contracts/test_b41_scope_note.py 하나(새 파일). 기존 test·conftest·tests/tools/**는 고치지 않는다.
입력: interface card docs/02-design/specs/20261002-b41-scope-note-test.interface.md(피검 2행), spec card '관찰 가능한 계약'(공통 입력·계약 0~4·'계약이 아닌 것'), 'oracle 종류와 출처', '거부해야 할 입력'.
열람 금지: 엔진 소스(skills/analog-gmid-design/assets/*.py, workspaces/run_harness.py), _drafts/b41_kit/(B41 분석 시제품 -- 기대값의 출처가 될 수 없다).
      기존 계약 test(tests/contracts/test_ic3.py·test_df36_instance_relpath.py)의 입력 구성 모양은 읽어도 된다.
커밋: git -C <worktree> commit --trailer "Role: test" --trailer "Change-Id: 20261002-b41-scope-note-test" -m "test: …"
```

### 1.1 산출물과 구성 규칙

* test 함수 5개: 계약 0(빈 판정 금지, 매개변수 없음) + 계약 1~4 각각 `LIB` 파일 이름으로 `parametrize` → 수집 `1 + 4 × len(LIB)`.
* import: 모듈 머리에서 interface card 표의 모듈에서 `save_instance_json`·`run_topology_pipeline`을 가져온다(`sys.path`에 `A`를 넣는 머리 모양은 `test_df36_instance_relpath.py`와 같게). test 본문에서 `save_instance_json(...)`을 네 위치 인자로 **직접** 부른다.
* 공통 입력은 card 문장 그대로: `overrides`·`SZ`의 값, `NOTE(n)` 문자열(첫 줄 + `\n` + 앞 공백 2칸·끝 공백 1칸 둘째 줄), 호출마다 깊은 복사, 회로마다 `run_topology_pipeline` 한 번(상한 있는 캐시 -- `functools.lru_cache(maxsize=16)` 같은).
* 읽기는 `json.load`만. 파일 바이트·해시·원문 비교 금지(계약 '계약이 아닌 것' -- 들여쓰기 변이에서 test가 실패하면 안 된다).
* 계약 3 (b)는 `json.dumps(…, sort_keys=True, ensure_ascii=False)` 문자열 비교, (a)는 정렬 목록 비교.
* 각 test 함수에 `if`·`try` 밖의 `assert` 하나 이상, print·logging 판정 금지, `gmid_ic` 표식 없음. 이름·id에 `dup_`·`new_topology` 금지. 이름 접두 `test_b41_`·`_b41_`.
* 기대값은 card 문장과 test가 만든 문자열에서만. 회로·소자 이름을 적지 않는다.

### 1.2 자기 점검(커밋 전)

* `C:/Python314/python.exe -P -m pytest -c <worktree>/tools/gates/pytest_gate.ini --rootdir=<worktree> --confcutdir=<worktree> -q -p no:cacheprovider --gmid-phase=4 --gmid-strict= <새 파일>` → 전부 PASS(기존 동작 고정 -- base에서 green이어야 한다).
  실패하면 test를 card 문장과 다시 대조하고, card 문장이 base 동작과 어긋난다고 보면 고치지 말고 dispute를 쓰고 멈춘다.

---

## 2. auditor 브리프(gmid-verification-auditor)

```
역할: gmid-verification-auditor. change id = 20261002-b41-scope-note-test, evidence_type test-only, phase 4.
audit worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261002-b41-scope-note-test-audit (브랜치 role/audit/20261002-b41-scope-note-test).
모든 측정은 격리 복제본에서: git clone --no-hardlinks --no-local -c core.autocrlf=false <audit worktree> <scratch>/iso → git -C <scratch>/iso remote remove origin.
scratch는 새 C:/g<n> 하나만(TMP·TEMP도 그 아래, "." 금지), 끝나면 그 폴더만 삭제. set -euo pipefail, git -C <절대 경로>만, (cd … && …) 금지. 끝나면 실제 저장소 git status·reflog 불변 확인.
게이트 코드는 base 판(card 커밋 뒤 gate master)을 git archive로 추출한 사본.
작성자(test) 보고와 오케스트레이터 사전 측정(spec card '재현할 수치'의 모래상자 값)은 증거로 받지 않는다 -- 다시 잰다.
판정 기록 .ai/verification/20261002-b41-scope-note-test.json + .ai/verification/20261002-b41-scope-note-test/{scripts,out}/, Role: audit 커밋(판정 순서에서만 한 커밋 -- 순서 3 산출물은 쓰기만).
```

### 2.1 순서 3(freeze·base 확인 → `base_check.json`)

* **커밋하지 않는다**: base_check.json 등 산출물은 audit worktree에 쓰기만 하고 커밋하지 않는다(커밋은 순서 7에서 T 위 한 커밋 -- test-only라 병합 M 없음).
* T 해시 고정. `git diff --name-only <base> <T>` = 새 test 파일 하나.
* T 복제본에서 새 test만 실행 → 전부 PASS, 수집 수 `1 + 4 × len(LIB)`(`LIB`는 auditor가 library에서 다시 센다).
* base 정의 파일(R-DEF)의 `save_instance_json` `bind_hash`, 도구 변이 id 목록(`mutate_changed.mutants`) 기록.
* (gate master fd4ef8c 재측정 2026-10-06) 순서 3 커밋 금지의 실례: card 35에서 순서 3 커밋(`dcf6269`)이 생겨 버려졌고, 판정 커밋 `dafe5cf`가 오케스트레이터 보존본에서 산출물 29파일을 재배치했다(그 판정 기록 `auditor_run` '순서 3 산출물 재배치'). 이 브리프는 그래서 `git -C <audit worktree> status`로 산출물이 미커밋인지, `log role/test/<id>..HEAD`가 비었는지를 auditor가 순서 3 끝에 스스로 확인해 `base_check.json`에 적게 한다(0.3 끝의 오케스트레이터 확인과 이중). 로그 사본 해시는 작업 사본(CRLF)과 커밋 blob(LF, core.autocrlf=true) 두 값을 적는다(같은 기록의 관찰).

### 2.2 순서 7(판정)

* 순서 3 산출물(base_check.json 등)은 이미 audit worktree에 미커밋으로 있다 -- 이 순서 7의 한 커밋(T 위, `Role: audit`)에 판정 기록과 함께 넣는다.

| V | 판정 | 근거·측정 |
|---|---|---|
| V1 | PASS 기대 | 전체 suite(base 판 `pytest_gate.ini`, `--gmid-phase=4`, 엄격 집합 base 판, `-k`·`--deselect`·`-x` 없음) |
| V2 | PASS 기대 | test-only 모양(T 사슬 전부 `Role: test`, new = `Role: audit`, 병합 없음). base 통과 test 전부 PASS + 새 test PASS. **계약 6 변이 측정**: base 사본에 card '거부해야 할 입력' M-a·M-b·H1~H6을 하나씩 넣어 새 test 파일만 실행 → 모두 실패, P1~P5 → 모두 PASS. 변이 위치는 (def, 문장 원문)으로 base에서 찾고 auditor 자신의 스크립트로 넣는다. 결과는 `checks.V2.basis`·`reproduced_numbers`(red 필드 없음) |
| V3 | PASS 기대 | base 판 `mutate_changed.py --base <base> --head <new^>` → targets 빈 목록, mutants 0 ((gate master fd4ef8c 재측정 2026-10-06) card 35 도구 출력 키까지: `not_targeted` 0·`targets_by_def` {}·`exempt_ignored` []) |
| V4 | PASS 기대 | base 판 `test_lint.py --interface-card <interface card>`. + 계약 5 oracle 독립(import 목록, 바이트 비교 0, 기대값 출처) |
| V5 | PASS 기대 | `weakening_diff.py` findings 0(새 test 파일) |
| V6·V7 | PASS 기대 | 바뀐 소스 0 |
| V8 | N/A | 'N/A -- 계측 미도입(#13 전), 폴백 경로 불변'(design 40 P-38) |
| V9 | N/A | 도입 6b |
| V10 | PASS | card '재현할 수치' (A)·(B)·(D)를 다시 잰다. (C)(뒤 card 모의 V3)는 참고 측정 -- 시간이 허락하면 같은 모의 변경으로 base 도구 실행, 아니면 `notes`에 '미측정'으로. ((gate master fd4ef8c 재측정 2026-10-06) (C) 비교 대상은 card의 card 35 도구 값 -- (i) PASS 대상 4·killed 4·`not_targeted` 11, (ii) FAIL 생존 2(분기). 옛 도구 값((i) 생존 2 indent·(ii) 생존 4)과 비교하지 않는다. 두 실행 합 약 24분) |

* 계약 7 범위: `<measured_at>..<new>` 중 `Change-Id: 20261002-b41-scope-note-test` 커밋의 경로 합집합 = 새 test 파일(+ spec·interface card·판정 기록).
* `approvals` = card 머리의 Phase 4 design 승인 id(기록이 `new` 트리에 있는지 로더 규칙 6으로 확인).
