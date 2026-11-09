# Phase 3 D0b card `20260930-p3-registry-dest` -- 착수 키트(착수 조건 + test-author·code-author·auditor 브리프 + 오케스트레이터 절차)

작성 2026-10-01. 기준: gate `master` **`5f643a9`**(엔진·`tools/`·계획서·레지스트리는 `19eb475`와 같다). 작업 끝에 `dd60db6`으로 나아감(Phase 2 DoD 기록·백로그·V3 면제 묶기 문서 --
계획서는 839행 한 줄, N3.10·레지스트리·엔진·`tools/` 무변경 → 측정 그대로 유효). 저장소 쓰기·상태 변경 git 없음.
측정은 격리 복제본 `C:/g162/r`(`git clone --no-local`, origin 제거, 빈 hooksPath, 작업 끝에 삭제)에서만. B34·b26pre·backfill·B26-1·B33·G1·D0a는 **모두 미병합**이라
G1은 시제품(`_drafts/g1_kit/install_proto.py` `5790433c…` + `g1_core.py` **`b3c4e391…` -- G1 키트가 작업 중이라 23:16판을 스크래치에 복사해 썼다**), D0a는 시제품(`_drafts/p3kit_d0a/move_plan_proto.py`
`d2f3da97…`, `plan`만)을 읽기 전용으로 썼다. 그래서 아래 수치는 전부 **관찰**이다 -- D0b 이관표는 D0b 자신의 base에서 처음 계산한다(design 30 §6.4).
대상: spec 초안 `_drafts/draft_p3_d0b.spec.md`, 키트 `_drafts/p3kit_d0b/`.

---

## 0. 착수 조건(전부 충족해야 test worktree를 만든다)

| # | 조건 | 지금 | 근거 |
|---|---|---|---|
| S-1 | **Phase 3 design 승인**: UD-0(design 30 + N3.10 개정 3건 + D-19 문안) 승인 기록 `20260930-30-module-split-design`과 **D-19 답** | 질문 전 | design §9.2. D-19 답이 spec (d)-1 표 `rail_declaration` 기대값을 정한다(결정 D0b-6) |
| S-2 | **D0a 병합**(그 앞의 B34 → b26pre → backfill → B26-1 → B33 → G1 포함, 확정 순서) | 미병합 | design §8.1 'B34·b26pre·backfill·B26-1·B33·D0a → D0b'. D0b test가 `tools/migrate/move_plan.py`를 부른다 |
| S-3 | Phase 2 DoD PASS | **충족** -- 판정 기록 `2eefda1`(H = `5f643a9`, PASS) | D-23 |
| S-4 | **D0a 규칙의 빈칸 해소(결정 D0b-2)** -- 모듈 docstring 배정 제외, `--keep` 파일 잔여 단위(A-K), 참조자 없는 단위(A-6 후보) | **D0a 착수 전에 정해야 한다** | 지금 규칙대로면 `unassigned`가 F2 뒤에도 남아(SD·ACF docstring) D0b test·DoD E4가 영원히 FAIL(spec 작성 전 실측 3·4) |
| S-5 | **계층 충돌 해소 방침(결정 D0b-1)** -- A-1↔A-1 2건·A-1→A-4 3건을 UD-0 N3.10 개정에 더할지, A-4 승격 규칙을 design §6.2에 둘지 | **design 승인 질문 전에 정하는 것이 기본안** | 지금 `upward` 34·`cycles` 1. 미리 닫지 않으면 D0b는 base에서 멈추고(spec 계약 8 (a)) D-11 승인을 따로 받아야 한다 |
| S-6 | D0b base에서 `plan`의 `conflicts`·`upward`·`cycles`·`unassigned`·`import_time_high`·MOD7 밖 배정이 **모두 빈 목록** | 미확인 | spec 계약 8. 비면 S-7로, 아니면 '멈춤 절차'(0.4) |
| S-7 | `role/*` 브랜치 0개, D-27 동결 대상 card(B26-2~B26-4·B35·B36·B37a 등 엔진·`tools/gates`·`tools/migrate`·레지스트리 목적지 열을 바꾸는 Phase 3 밖 card)가 대기열에서 **F2 뒤로** 옮겨졌다 | -- | **동결은 D0b 병합에서 시작한다**(design D-27) -- 병합 전에 대기열을 정리해야 병합 직후 위반이 없다 |

**착수 0단계(읽기 전용, S-2 뒤)**:
```
R=C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills; B=$(git -C $R rev-parse gate/master)
git -C $R log --oneline -12 $B                                   # D0a·G1·B33·B26-1·backfill·b26pre·B34 판정 기록이 모두 있는지
git -C $R diff --stat 5f643a9 $B -- docs/01-plan/features/gain-budget-gmid-sizing.plan.md docs/03-analysis/gain-budget-gmid-sizing.function-registry.md tools/gates tools/migrate skills/analog-gmid-design/assets/*.py
git -C $R grep -n -c "보류(Phase 3)" $B -- docs/03-analysis/gain-budget-gmid-sizing.function-registry.md
```
그다음 격리 복제본(새 `C:/g<n>`, 그 폴더만 쓰고 끝나면 삭제)에서 §10 `MP_ARGS`로 `"$ISO/tools/migrate/move_plan.py" plan --root "$ISO" --rev "$B"`를 돌려 S-6을 판정하고, spec '작성 전 실측' 1·3·5·6을
그 판에서 다시 잰다(키트 `p3kit_d0b/run_plan.sh`·`analyze_plan.py`·`regen_registry.py`는 시제품 경로를 인자로 받으므로 `move_plan.py` 실제 파일 경로를 넘긴다). 수치가 바뀌면 spec card '작성 전 실측'의 사실 문장만 고친다.

---

## 0.1 지금 실측 요약(오케스트레이터용 -- 근거는 spec '작성 전 실측')

| 측정 | 결과 |
|---|---|
| `plan`(UD-0 N3.10 개정 적용 모의, D-19 (가)) | exit 1 · `upward` **34** · `cycles` 1(MOD 9개 SCC) · `unassigned` **18** · `conflicts` 0 · `reg_mismatch` 36 · `import_time_high` **[]** · MOD7 밖 배정 **0** · 배정 390 |
| `upward` 규칙 쌍 | A-4→A-1 17, A-4→A-4 12, A-1→A-4 3, **A-1→A-1 2**(`sizing_recipe.py:8060` `_build_theta_evaluator`→`resolve_stack_layout`, `:7683` `require_declared_spec_source`→`spec_fingerprint` -- N3.10 표 안의 모순, 규칙으로 못 푼다) |
| `unassigned` 18 | 모듈 docstring 4 · ACF `sys.path.insert`·`render_report` · SR D 목록 5 · SD 7(D 목록·예시 함수·`SharedFingerWCandidate`/`search_shared_finger_w`) |
| 규칙 후보 | A-K → `unassigned` 15, + A-6 → 6, + A-4 승격 → `upward` 7(배정 47개 바뀜) |
| V 도구 모양(모의 사슬) | V3 `targets []`·V5 `diff_paths []`·V6 `targets []`·V7 `new_defs []` PASS, V4 card만 ERROR → `--subject move_plan:main` PASS(NO-SUBJECT 7) |
| 재생성 모의(규칙 그대로) | `reg_mismatch` 36 → 0, 배정 사상 차이 0(멱등), 레지스트리 diff 409+/409−(열 추가), `reg_check` 발견 0, 레지스트리 계약 test 3파일 210 passed |
| test 모양 시제품 | base 5 failed·2 passed(`import_time_high`·MOD7 단언은 base에서 참) → **모든 test가 '근거 규칙 열 머리' 단언을 먼저**(spec 계약 11 (a)) |
| `plan` 1회 | 12~19초(test 모듈 캐시로 V1당 1회) |

## 0.2 결정 필요(spec '결정 필요 항목' 요약 -- 오케스트레이터가 정하거나 사용자에게 올린다)

* **D0b-1**(S-5): 기본안 = design 승인 질문 **전에** A-1↔A-1 2건·A-1→A-4 3건을 UD-0 N3.10 개정 문안(`p3_doc_amendments.md` §1)에 더하고, A-4 승격 규칙을 design §6.2·D0a 계약 2에 넣는다.
  측정은 시제품 근사다 -- 정확한 목록은 D0a 시제품을 고친 판(S-4 반영)으로 다시 재서 문안을 만든다. 판정 기준(배정 규칙·계획서 표) 변경이라 사용자 승인 몫(UD-0에 흡수하거나 D-11 별도 승인).
* **D0b-2**(S-4): D0a spec card 계약 2 개정 -- (a) 모듈 docstring은 배정 대상 밖 (b) A-K (c) A-6 + 남는 3단위는 N3.10 토큰(D-11) 또는 Phase 4 삭제 선행. D0a 착수 전.
* **D0b-3**: 비대상 행 칸 불변 + `근거 규칙` `-`(기본안).
* **D0b-4**: design §8 D0b 행 '합성 입력' oracle → 이 card는 실제 단위 표본(d)-1, 합성은 D0a test(V2 red 조건). design 문구 사실 정정.
* **D0b-5**: `근거 규칙` 열 = 재생성 시점 규칙(이력, test는 형식만). 대안: 열 삭제.
* **D0b-6**: D-19 답 → (d)-1 표 `rail_declaration` 칸 고정(오케스트레이터가 spec card 커밋 전에).
* **D0b-7**: MOD7 밖 배정이 생기면 M7 실제 card 여부(지금 0).

## 0.3 앞선 card가 같은 입력을 바꾸는 것 -- 착수 때 다시 잴 것

| card | D0b 관련 | 착수 때 |
|---|---|---|
| B34(`20260930-b34-grammar-explicit`) | `_import_analog_grammar`·`find_idiom_matches`·`find_stack_edges`·`audit_theta_root_direction` 본문 -- 참조가 바뀌면 배정·`upward`가 바뀐다 | `plan` 재실행 |
| b26pre(test-only) | 엔진 무변경 | -- |
| backfill(`20261001-b26-backfill-interdig-final-audit`) | `sizing_recipe.py` 한 def 본문 | `plan` 재실행 |
| B26-1(`20260930-b26-rail-accessor-set`) | **새 단위 `rail_declaration`·`RailDeclaration`**, SD 18·SR 2 사이트에 `rails: RailDeclaration` 주석(SD·SR은 `from __future__ import annotations` -- import 시점 읽기 아님), `load_topology` 본문 | (d)-1 표 두 행, `import_time_high`, A-2 `RailDeclaration` → MOD2 |
| B33·G1(게이트) | `reachability.SourceIndex` 단위 키(문장 키가 바인딩 이름인지 -- 시제품은 `<stmt:해시>`), `moved_defs` | 레지스트리 상수 행(`_KNEE_L_CACHE` 등 8)이 대상 행으로 바뀌는지 |
| D0a | 도구 본체, S-4 반영 여부 | spec 계약 2·6의 CLI·출력 키 이름 대조 |
| UD-0 design 커밋(+ S-5 개정) | N3.10 '대표 대상' 토큰 = `plan` A-1 입력 | (d)-1 표 근거 재확인 |

## 0.4 멈춤 절차(spec 계약 8 -- S-6이 비지 않을 때)

1. D0b base `plan` 출력에서 비지 않은 목록을 그대로 판정 근거로 남긴다(격리 복제본 출력, `_drafts/`에 사본).
2. 해소안을 원칙으로 만든다: `conflicts`·A-1이 낀 `upward` → N3.10 토큰 이동, 규칙 공백 → design §6.2 규칙 개정(D0a 도구 변경이면 D0a 후속 card), `import_time_high` → 배정 변경(N3.10), MOD7 밖 → N3.10 또는 M7 card.
3. 사용자 승인(`target_kind: diff`, UD-0 밖 -- 위임 없음, D-11). 질문 문안에 '현재 배정 → 새 배정'과 이유(어느 참조가 위로 가는지, 줄 번호)를 넣는다.
4. 오케스트레이터 문서 커밋(계획서 `docs/01-plan/**`) + 승인 기록 → push → gate `master`에서 S-6 다시. spec card `approval` 줄에 그 승인 id를 더한다.
5. 도구 자체를 고쳐야 하면(규칙 개정) D0a 후속 card(red-green)를 먼저 병합한다 -- M card 판정 사본 출처가 그 card `code_commit`으로 바뀐다(D-16).

---

## 1. gmid-test-author 브리프(순서 2)

```
역할: gmid-test-author. change id = 20260930-p3-registry-dest (red-green, phase 3, gate_change: no).
worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-p3-registry-dest-test (브랜치 role/test/20260930-p3-registry-dest). 절대 경로만.
쓰기 경로: skills/analog-gmid-design/assets/tests/contracts/test_p3_registry_dest.py 하나.
입력: interface card(기존 함수 0행·신규 심볼 0행 -- 생성본 확인) + spec card '관찰 가능한 계약' 1~12·'oracle 종류와 출처'((d)-1 표 포함)·'거부해야 할 입력'·'무동작 판정 입력'.
열람 금지: 엔진 소스, tools/migrate/move_plan.py 소스, tools/gates 소스(import해 쓰는 것은 허용 -- mod_table), _drafts/.
커밋: git -C <worktree> commit --trailer "Role: test" --trailer "Change-Id: 20260930-p3-registry-dest" -m "test: …"
```

**모양 요구**
1. **red 조건 먼저**(계약 11 (a)): 모든 test 함수의 첫 단언 = 레지스트리 함수 표(머리에 `함수`·`이관 목적지` 둘 다) 머리마다 `근거 규칙` 열이 `이관 목적지` 바로 뒤에 있다. 이것이 빠지면
   `import_time_high`·MOD7 test가 base에서 통과해 V2가 깨진다(시제품에서 확인: 7개 중 2개 base 통과).
2. 도구 호출: `[sys.executable, <root>/tools/migrate/move_plan.py, "plan", "--root", <root>, "--rev", "HEAD", *MP_ARGS]` 인자 목록(셸 없음). `MP_ARGS`는 design §6.3 그대로(`--aliases`는
   JSON 문자열 하나). 출력 첫 줄 JSON·`"tool": "move_plan"` 단언 뒤 판정. 모듈 범위 캐시(상한 1) -- test 파일당 1회(12~19초).
3. `<root>` = test 파일 위치에서 계산(`parents[5]`가 저장소 루트 -- contracts/tests/assets/analog-gmid-design/skills 위). MOD 파일 이름 = 계획서 N3.10을 `import_layering.mod_table`로
   읽어 번호 → `<줄기>.py`(`tools/gates`를 `sys.path`에 넣어 import -- `test_ic_markers_match_plan.py`가 `merge_gate`를 쓰는 방식).
4. 계약별 test(이름 접두 `_p3rd_`·`test_p3rd_`): plan exit 0·`verdict` PASS / 여섯 목록 빈 목록 / `import_time_high` 빈 목록 / MOD7 파일 밖 단위의 MOD7 배정 0 / 대상 행 칸 = 배정 줄기(전부, `〃` 없음, 정확 일치) /
   `근거 규칙` 칸 형식 / 같은 키 `mod` 갈림 0 / 대상 행 > 0·표 > 0 / `보류(Phase 3)` 0 / (d)-1 표본 각 행(칸 = 기대 줄기, `plan` `mod`도 같음).
5. 레지스트리 표 읽기는 test 안에서(칸 나누기 `\|` 이스케이프 규칙 -- D0a 계약 2와 같게). 중첩 행(`└`)·비대상 행은 판정하지 않는다(계약 6 (d) -- auditor 몫).
6. 피할 것: 삭제 이름 토큰(T0 card 계약 9 목록), `print`, 회로·넷·소자 이름, `library`·`topology.json` 토큰. if·try 밖 assert ≥ 1.

**자기 실행**: `PT3`로 이 파일만 -- D0b base(열 재생성 전)에서 **전부 FAIL(`AssertionError`)**이어야 한다. 하나라도 PASS면 1번 단언이 빠진 것.
**소요 예상**: 작성 40~60분, 자기 실행 30초 안팎(plan 1회 + 표 읽기).

---

## 2. gmid-code-author 브리프(순서 5)

```
역할: gmid-code-author. change id = 20260930-p3-registry-dest (red-green).
worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-p3-registry-dest-code (브랜치 role/code/20260930-p3-registry-dest, 부모 = T). 절대 경로만.
쓰기 경로: docs/03-analysis/gain-budget-gmid-sizing.function-registry.md 하나(계획 N3.12.2 603행). tools/**·엔진·tests/**·계획서는 쓰지 않는다.
입력: spec card·interface card. test가 틀렸다고 보면 고치지 말고 dispute(<worktree>/docs/02-design/disputes/20260930-p3-registry-dest.md) 커밋 후 멈춘다.
커밋: git -C <worktree> commit --trailer "Role: code" --trailer "Change-Id: 20260930-p3-registry-dest" -m "…"
```

**만들 것 / 지킬 것**
1. **열 = 도구 출력**: worktree에서 `tools/migrate/move_plan.py plan`(§6.3 `MP_ARGS`, `--rev HEAD`)을 돌린 출력으로 대상 행 칸을 쓴다. 손으로 칸을 고르지 않는다 -- test가 대상 행 전부를 정확 일치로 본다.
   변환 스크립트는 스크래치에서만 쓰고 커밋하지 않는다(새 도구를 `tools/`에 두면 D-16 사본 출처·배선 문제가 생긴다).
2. 함수 표마다 `이관 목적지` 바로 뒤에 `근거 규칙` 열(머리·구분선·모든 행 칸 수 +1). 대상 행: 목적지 = 배정 MOD 줄기(`.py` 없이, 다른 글자 없이), 근거 = 그 실행의 `rule`.
   중첩 행(`└`)·비대상 행: 목적지 칸 바이트 그대로, 근거 `-`. 표 밖 문장·다른 열·행 순서는 바꾸지 않는다.
3. §7 `보류(Phase 3)` 9칸 → `보류(Phase 4)`(D-10). 그 밖의 `처리` 칸 불변.
4. **재생성은 한 번**: 근거 규칙은 재생성 **전** 레지스트리로 돌린 출력에서 가져온다(재생성 뒤 다시 돌리면 A-4가 늘어난다 -- spec 실측 5). 재생성 뒤 한 번 더 돌려 `reg_mismatch` 0·배정 사상 같음을 자기 확인.
5. `plan`이 exit 1이고 `reg_mismatch` 밖 목록이 비지 않으면 **쓰지 말고 멈춘다**(dispute가 아니라 오케스트레이터 보고 -- spec 계약 8, 착수 조건 S-6 위반).
6. 줄 끝·인코딩은 원본 그대로(UTF-8, 기존 줄 끝). 레지스트리 머리 문장(기준 커밋 설명)은 고치지 않는다.

**자기 확인(판정 아님)**: `PT3`로 `contracts/test_p3_registry_dest.py`·`test_reg_check.py`·`test_reg_check_df23.py`·`test_df23_inventory.py` PASS, `reg_check.py --registry … --root …` exit 0.

---

## 3. gmid-verification-auditor 브리프(순서 3·7)

```
역할: gmid-verification-auditor. change id = 20260930-p3-registry-dest, red-green, phase 3.
audit worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-p3-registry-dest-audit (브랜치 role/audit/20260930-p3-registry-dest).
격리 복제본에서만, scratch 새 C:/g<n> 하나(끝나면 그 폴더만 삭제), set -euo pipefail, git -C 절대 경로. 실제 저장소 status·reflog 불변 확인.
게이트 코드 = base 판(gate master) 캐시. 작성자 보고는 증거가 아니다. 판정 기록 .ai/verification/20260930-p3-registry-dest.json + {scripts,out}/, Role: audit 커밋.
```

### 3.1 순서 3(freeze·base 확인)
* T 고정, `git diff --name-only <base> <T>` = `tests/contracts/test_p3_registry_dest.py` 하나.
* red: base에서 그 파일 `PT3 --gmid-strict=` → **모든 test FAIL, 원인 = `근거 규칙` 열 머리 단언**(`AssertionError`, 수집 오류 0 -- `GMID_RED_CAPTURE`, `failure_hashes` = base 판 `merge_gate.red_failure_hash`).
* base `plan` 출력 전체를 `out/plan_base.json`으로(재생성 전 이관표 -- 계약 9·10의 비교 기준). 이 출력에서 `conflicts`·`upward`·`cycles`·`unassigned`·`import_time_high`·MOD7 밖이 비지 않으면 **INVALID**로 멈추고 오케스트레이터에 알린다(착수 조건 S-6 위반).
* (d)-1 표본이 spec 표 그대로인지(test 상수와 대조).

### 3.2 순서 7(병합본 판정)

| V | 기대 | 증거 |
|---|---|---|
| V1 | PASS. 전체 `PT3 --gmid-strict=`, base 대비 새 test만 늘고 나머지 같음(레지스트리 소비자 test 포함) | base·병합본 전체 실행 대조 |
| V2 | PASS red-green: red = 새 파일 test 전부(3.1), green = 병합본 전부 PASS | 3.1 기록 + 병합본 |
| V3 | PASS `targets []`(바뀐 소스 def 0 -- 레지스트리·contracts test) | `mutate_changed.py … --gmid-phase=3 --gmid-strict=` |
| V4 | PASS. interface card 두 표가 비어 `--interface-card`만이면 ERROR('피검 심볼이 없다' -- 사전 측정) → `--module-dir tools/migrate --subject move_plan:main`(선례 `20260922-sections-major-merge`). findings NO-SUBJECT만, basis는 oracle 대조 문장((d)-1 표·계약 3~7) | `test_lint.py --root --base --head --module-dir tools/migrate --subject move_plan:main` |
| V5 | PASS `diff_paths []`(새 test 파일) | `weakening_diff.py` |
| V6 | PASS `targets []` | `source_lint.py` |
| V7 | PASS `new_defs []` | `reachability.py` |
| V8·V9 | N/A | -- |
| V10 | PASS. 재현 수치(spec '재현할 수치')와 **계약 확인 측정**(auditor 스크립트, 기대값은 spec 문장): ① 계약 1 범위(`git diff --name-only <base> <merge>` = 레지스트리 + test) ② 계약 6 (c) 대상 행 `근거 규칙` = `out/plan_base.json`의 `rule` ③ 계약 6 (d) 중첩·비대상 행 목적지 칸 base와 바이트 같음, 계약 7 `처리` 칸 변화 = base `보류(Phase 3)` 9칸뿐, 표 밖 줄 변화 0 ④ 계약 9 멱등(base 대 병합본 (키 → `mod`) 사상 차이 0) ⑤ 계약 10 산출물(`out/plan_base.json`·`out/plan_merge.json`·MOD별 단위 목록·`reexports`·규칙 분포) ⑥ '거부해야 할 입력' 각 항목을 병합본 사본에 하나씩 적용해 test FAIL 확인(무동작 게이트 방지) ⑦ `reg_check` exit 0 | auditor 스크립트 |

판정 기록 `approvals` = `["20260930-30-module-split-design"]`(+ 멈춤 절차를 거쳤다면 그 승인 id). 이 기록의 `code_commit`이 **D-27 동결의 시작점**이다(오케스트레이터 0.5).

---

## 4. 순서 요약(오케스트레이터)

design 30 승인(UD-0 + D-19, S-5 반영) → D0a spec 개정(S-4) → (B34 → b26pre → backfill → B26-1 → B33 → G1 → D0a 병합) → 착수 0단계(S-6 판정, 비면 계속 / 아니면 0.4 멈춤 절차) →
spec card(rev·사실 문장 갱신, D-19 칸 고정) + interface card(절대 경로, 기존 함수 0개 확인 -- 계약 절에 엔진 함수 이름을 백틱으로 넣지 않았다) → **S-7 대기열 정리** → 순서 1 test worktree →
test-author(1절) → 순서 3 auditor(3.1) → 순서 4 code worktree → code-author(2절) → 순서 6 병합 → 순서 7 auditor(3.2) → push 단독·전체 출력 확인 → 정리 →
**동결 시작 공지(D-27)**: 이 병합부터 F2 병합까지 엔진 파일·`tools/gates/**`·`tools/migrate/**`·레지스트리 '이관 목적지' 열을 바꾸는 Phase 3 밖 card 병합 금지. 어겼다면 그 card 뒤 D0b 재계산 card
(레지스트리 열 재생성)를 먼저. D0b~M1 base 구간은 DoD가 덮지 않으므로 M1 착수 전 `git diff --stat <D0b code_commit> gate/master -- skills/analog-gmid-design/assets/*.py workspaces/run_harness.py tools`가 빈지 본다.
→ M1(G1·T0·D0b 뒤).

## 5. 키트 파일(`_drafts/p3kit_d0b/` -- 측정 전용, 역할에게 건네지 않는다)

| 파일 | 내용 |
|---|---|
| `apply_n310_amend.py` | `p3_doc_amendments.md` §1 (a)~(d)를 복제본 계획서 522·523·526·528행에 적용('현재' 블록 불일치면 exit 1) |
| `run_plan.sh` | 복제본 커밋 하나에서 `plan`(§6.3 `MP_ARGS`) → JSON |
| `analyze_plan.py` | `plan` JSON 요약: 목록 길이·규칙·MOD별·MOD7 밖·`upward` MOD 쌍/규칙 쌍·두 출력 사상 비교 |
| `mk_variant.py`·`run_variants.sh` | 규칙 후보(A-K·A-6·A-4 승격)를 환경 변수로 켜는 시제품 변형과 네 조합 실행 |
| `regen_registry.py`·`sim_regen.sh` | 레지스트리 행 분류(대상·중첩·비대상·multi)와 열 재생성 모의(`--write`) → 재실행 멱등·`reg_mismatch` |
| `test_p3_registry_dest.proto.py`·`run_proto_test.sh` | test 모양 시제품(red 모양·비용 확인) -- **역할에게 건네지 않는다** |
| `sim_chain_vtools.sh` | base(D0a 대역) → test → code 사슬을 만들고 V3·V4·V5·V6·V7 모양 확인 |
| `out/` | 이 작업의 측정 출력 사본(시제품 근사 -- 관찰) |
