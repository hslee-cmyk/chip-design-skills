# 독립 검토 -- P10 `20260930-p10-df23-inventory` / P10b `20260930-df23-registry-record` (2026-09-30)

검토자: 독립 reviewer(작성자 아님). 저장소 읽기 전용(`git show/diff/grep/log`, `-B` import만), scratch `C:/g38`(끝나고 삭제).
입력: `draft_p10_b22.spec.md`, `draft_p10b.spec.md`, `p10_reconcile_log.md`, `p10_prep/`(regen_df23.py, df23_inventory.candidate.json, regen_report.md, b22_lines.md).
`check_contracts.py`는 증거로 쓰지 않았다 -- 아래 수치는 모두 리뷰어 자신의 스크립트(`C:/g38/measure.py`, 삭제됨)로 잰 값이다.
정정본: `draft_p10_b22.reviewed.spec.md`, `draft_p10b.reviewed.spec.md`(둘 다 `role_paths.parse_spec_card` 통과 -- test-only/no, red-green/no, approval `20260923-20-dead-code-dup-design`, 11절;
`interface_card.build` 기존 함수 행 P10 0개(원본 1개 -- 아래 M2), P10b 0개 + 신규 `reg_check.check_df23`).

**HEAD 변동**: 검토 도중 gate `master`가 B28 병합으로 `8790b24`가 됐다(`role/*` 브랜치 0). `git diff --name-only cd64170 8790b24 -- skills workspaces docs/01-plan docs/02-design <레지스트리>` → 빈 출력.
두 초안의 사실 수치는 그대로 유효하고, P10 목록의 `measured_at`만 문서 커밋 직전 gate 머리로 다시 만들면 된다.

## 독립 실측 요약 (리뷰어 스크립트)

| 항목 | 값 | 초안 주장과 |
|---|---|---|
| 계획 DF 표 머리(909행) | `ID·결함·위치(함수)·수정 Phase·비고`, 37행, 셀 수 불일치 0 | 같음 |
| `plan_phase_tokens` 괄호 밖 토큰(정본, 00-common §9.2) | DF-19 {4}, DF-23 {2,4}, DF-26 {4}, DF-29 {2,7a}, DF-30 {7a}, DF-31 {7b}, DF-32 {6b,6c}, DF-33 {7b}, DF-34 {4,7b} | 초안 '괄호 깊이 0 쉼표' 규칙과 `2` 제외 뒤 같음 |
| `read_plan_tables(...).phase_order` | (0.5, 1, 2, 3, 4, 5, 6a, 6b, 6c, 7a, 7b, 7c) | 닫힌 집합과 같음 |
| library R | {agnd, gnd, vdd, vss} | 같음 |
| 후보 목록 계약 1~4(내 구현) | 위반 0, 515항목(메시지뿐 302·동작 213), `totals` 4종 일치, 동작 (함수, 파일) 묶음 52, 파일 이름 충돌 0 | 같음 |
| 동작 항목 DF별 | DF-19 62, DF-23 1, DF-30 27, DF-31 16, DF-32 1, DF-33 12, DF-34 18, 비DF 76(전부 `신규(계획 DF-29~34 대상 외)`) | 같음 |
| 계약 5 대상 줄 | 19줄(초안 목록과 파일·줄 모두 같음) | 같음 |
| N 정의 위치 | 삭제 16개 정의 0, 이동 5개는 `tests/tools/interleave_splits.py`·`regression_runner.py`에만, SR 두 레지스트리 키 `diff_pair_tail` 하나씩 | 같음 |
| `reg_check.main` 모르는 인자 | `SystemExit`를 잡아 `return 2`(192-194행) | 같음 |
| 레지스트리 | §0~§7(`## ` 8개), 524줄 전부 CRLF, 끝 빈 줄 | 줄 끝은 초안에 없음(M4) |
| `.ai/context.md` 14943·14950·14966·14977, history 4002 | B22 원문 확인 | 같음 |
| 새 test 이름 | `test_df23_inventory.py`·`test_phase2_stale_refs.py`·`test_reg_check_df23.py` -- 파일·내용 충돌 0 | 같음 |

## Blocking

### B1. P10 계약 1의 "measured_at blob = card base blob"이 영구 test 계약이다 -- 다음 엔진 card부터 모든 card를 막는다
* 근거: 계약 1 둘째 문장이 이 사실을 계약으로 두고, oracle 절은 "영구 계약 test = … 계약 1~5 문장만으로 쓴다". 영구 test는 'card base'를 알 수 없으므로 실제로는 작업 트리(HEAD)와 비교하게 되고,
  P3·B26 등 다음 엔진 card 병합본에서 즉시 FAIL한다. 계약 7 (a)에서 "줄 번호 일치를 영구 test로 두지 않는 이유"로 스스로 적은 논리(P2 → P4 폐기 선례)와 P10b의 '왜 도구 규칙인가'와도 모순이다.
* 수정(정정본 반영): 영구 test는 `measured_at` 형식만. blob 동일은 계약 7 (e) auditor 측정 `git diff --name-only <measured_at> <old> -- A/*.py workspaces/run_harness.py` = 빈 출력.

### B2. P10 계약 6의 기준이 옛 초안 base `070cf69`다 -- 계약이 글자 그대로 거짓
* 근거: `git diff --name-only 070cf69 HEAD`에 `skills/analog-gmid-design/assets/stick_diagram.py`(DF-36)와 `tests/contracts/test_df36_instance_relpath.py`가 있다.
  계약 6은 "070cf69 이후 이 card가 바꾼 경로 … `A/*.py`·기존 test 불변"이라 auditor가 문자 그대로 재면 FAIL이다.
* 수정: 기준을 `measured_at`(= 문서 커밋의 부모)으로, 범위 = `git diff --name-only <measured_at> <new>`(판정 기록·spec card·interface card 제외).

### B3. P10 계약 5가 실행 시점에 엔진 AST를 읽는다 -- Phase 3에서 확정적으로 깨지고, 고치려면 V5 승인
* 근거: 계약 5는 "정의가 `A/*.py`에 있으면 제약 없음 / `A/tests/tools/<모듈>.py`에만 있으면 이동 / 어디에도 없으면 삭제", 선택 키는 "SR `_CMRR_ESTIMATOR_REGISTRY`·`_PSRR_ESTIMATOR_REGISTRY`
  딕셔너리 리터럴의 키(AST)". 계획 N6.1 3행은 "`sizing_recipe.py` 삭제"다 -- SR를 지정해 읽는 test는 Phase 3 equivalence card 병합본에서 FAIL(파일 없음)하고, 이동 이름을 뒤 Phase가 지우면
  문서(오케스트레이터 경로)와 무관한 code card가 이 test를 깬다. test의 이름 상수·분기를 고치는 것은 V5 '기대값 리터럴 변경'이라 사용자 승인이 필요하다. 계약 1~4는 오케스트레이터 파일만
  읽는데 계약 5만 code-author 파일에 묶여, P10b가 스스로 든 '쓰는 주체가 다른 두 파일을 대조하는 영구 test' 결함을 그대로 가진다.
* 수정(정정본 반영): 삭제/이동 분류를 Phase 2의 사실로 **고정한 데이터**로 계약에 적고(이동 = `find_interleaved_symmetric_splits` → `tests/tools/interleave_splits.py`, 회귀 4이름 →
  `tests/tools/regression_runner.py`, 나머지 삭제), test는 문서만 읽는다. 분류가 base 사실과 같은지는 계약 7 (f) auditor 측정(리뷰어 실측으로 이미 같음). '되살린 경우 제약 없음'은 뺐다 --
  되살아나도 "Phase 2에서 삭제"는 이력으로 참이다.

## Should-fix

### S1. P10 계약 8(거부 확인)의 기록 위치·절차가 없다 -- `red` 필드에 적으면 로더 거부
* 00-common §8.1 표: `red`는 "`red-green`일 때만 필수, 그 밖에는 금지". test-only 판정 기록에 `red`로 적으면 merge gate 스키마/로더가 거부한다.
* '문서 커밋 직전 커밋'은 spec card·interface card 커밋 순서에 따라 모호하다.
* 수정: `measured_at` 커밋 체크아웃 격리 복제본에 T의 새 test 파일만 복사해 실행, 결과는 `checks.V2.basis`·`reproduced_numbers`, 문서 커밋은 하나이고 `git rev-parse <문서 커밋>^ == measured_at`을 함께 적는다.

### S2. P10 계약 2·3이 새 파서를 정의한다 -- 정본 재사용
* conftest와 `test_ic*.py`가 이미 `merge_gate.read_plan_tables`로 계획서를 읽는다(선례). N5.2 표는 `role_paths.read_section_table(text, "### N5.2 ")`, Phase 토큰은 `merge_gate.plan_phase_tokens`
  괄호 밖 집합이 정본(00-common §9.2)이고, 리뷰어 실측으로 초안 규칙과 9행 모두 같은 값이다. 새 파서를 만들면 '만들기 전 정본 확인' 원칙 위반이고 두 규칙이 갈라질 여지가 생긴다.
* 수정(정정본 반영): 닫힌 집합 = `phase_order`의 `2` 뒤 + `해당 없음`, 토큰 = `plan_phase_tokens` 괄호 밖 − {`2`}. 열 이름 `수정 Phase` 없으면 FAIL은 유지.
* 참고: 계획서에서 표를 읽는 test는 선례가 있어 허용되고, 계획서·목록·library가 모두 오케스트레이터 경로라 표 개정과 목록 재생성을 한 문서 커밋에서 맞출 수 있다(깨짐 위험은 B3과 달리 한 역할 안).

### S3. P10 계약 7 (b)의 어휘 정의가 판정 대상(목록의 `method`) 안에만 있다
* auditor가 "`vocabulary` 재계산"을 하려면 어떤 topology 필드가 소자·넷·회로 이름인지 알아야 하는데 그 정의는 목록 JSON `method`·`method_params`(작성자 산출)에만 있다 -- 판정 대상이 판정 규칙을 정한다.
* 수정(정정본 '작성 전 실측' 1c): 생성기 `build_vocab`(171-214행) 규칙을 문장으로 옮겼다 -- 회로 = 파일 줄기(`_TEMPLATE` 포함), 소자 = `netlist`·`passive_elements`·`ideal_sources`의 `name`,
  넷 = `netlist` 원소의 `source/drain/gate/body/bulk` + `terminals` + `supply_nets` 중 길이 2 이상. HEAD 102/101/10.

### S4. P10b red: import 위치를 계약에 적지 않으면 새 test 일부가 base에서 통과한다
* `reg_check.main`은 모르는 인자를 `return 2`로 돌려준다(192-194행, 실측). `--df23-inventory`로 exit 2(파일 없음·`ValueError`)를 기대하는 CLI test는 base에서 인자 거부만으로 **통과**한다.
  import를 test 함수 안에 두면 이 test들은 base PASS -- 계획 N4.2 V2 "새·바뀐 test가 base에서 assertion FAIL" 위반, 판별력 없음.
* red 허용 타입 확인: 모듈 머리 `from reg_check import check_df23`는 수집 단계 `ImportError`(`name` = `reg_check`, `name_from` = `check_df23`)이고 interface card 신규 심볼 쌍 (`reg_check`, `check_df23`)과
  같아 허용(00-common §8.1). `import reg_check` 뒤 속성 접근이면 `AttributeError`(`reg_check`, `check_df23`)도 허용이지만 위 CLI test 문제는 남는다. `SystemExit`는 도구가 잡으므로 나오지 않는다.
* 수정(정정본 반영): 모듈 머리 import(P7 `test_reg_check.py` 선례처럼 파일 전체가 수집 red), exit 2 test는 정상 입력 exit 0 대조를 짝으로.

### S5. P10b V3가 공허하다 -- 보충 뮤테이션을 계약에
* `mutate_changed.py`는 엔진 def만 대상으로 잡아 `A/tests/tools/` 변경은 대상 0(P7 판정 기록 V3 `targets []`, auditor가 별도 변이 스크립트로 보충). P10b에 이 요구가 없으면 auditor가 V3 PASS(대상 0)로 끝낼 수 있다.
* 수정(정정본 계약 5 (d)): 규칙 분기마다 auditor 자신의 변이, 생존 0, `checks.V3.basis`.

### S6. `measured_at` 재생성 시점
* gate 머리가 8790b24로 움직였다(엔진·계획·library·references·레지스트리 불변 실측). 후보의 `measured_at` = cd64170은 커밋 대상이 아니다 -- 초안 절차대로 문서 커밋 직전 gate 머리에서 다시 생성.
  B26-1·P3 등 엔진 card가 먼저 병합되면 목록 수치(레일 62 등)가 바뀌므로 그때는 '재현할 수치'의 비교용 수치만 달라지고 계약은 그대로다.
* **추가(검토 종료 시점)**: 작업 저장소 master가 `7535799`(P9 spec card `20260930-p9-kcl-edges` + interface card)로 더 움직였다. P9는 `sizing_recipe.py`의 `kcl_series_union` 본문을 바꾸는
  엔진 card이므로 (1) P9 역할 브랜치가 있는 동안 P10 문서 push는 EL1이 거부하고 (2) P9 병합 뒤 SR 줄 번호가 움직이므로 P10 목록은 **P9 판정 기록이 gate에 들어간 뒤의 머리**에서 생성해야 한다
  (P10 초안 '작성 전 실측'의 cd64170 수치는 비교용으로만 남는다). 계약 문장은 바뀌지 않는다.

## Minor

* M1. P10 38·113행 "design 05 §10-3·4 / §10-4 표(290행)" → 실제는 **§9.2-3·4**(§10은 auditor 도구). P10b는 §9.2-4로 맞게 적었다. 정정본 반영.
* M2. P10 계약 1의 예시 `` `SemiEmpiricalGmIdLUT.cgg_absolute` ``가 interface card 생성기(계약 절 백틱 이름 ↔ 엔진 정의 대조)에 걸려 `sizing_recipe.SemiEmpiricalGmIdLUT.cgg_absolute`가
  '관찰 가능한 계약' 피검 표에 들어간다(리뷰어가 `interface_card.build`로 실측: 1행). V4가 interface card 심볼을 피검 함수로 보므로 혼동 소지. 정정본에서 백틱 제거(→ 0행).
* M3. P10 새 test 이름에 `dup_`·`new_topology`를 넣지 말 것(design 20 E1·E5 `-k` 필터). P10b는 이미 적었다. 정정본 반영.
* M4. P10b: 레지스트리는 CRLF(524/524). §8 추가도 CRLF여야 "§0~§7 바이트 동일, 끝 추가뿐"이 성립. 정정본 반영.
* M5. P10b §8.2 `DF` 칸은 `^DF-\d+` 아닌 것을 모두 `신규`로 적는다. P10 쪽에서 비DF 동작 항목의 `plan_mapping`이 `신규`로 시작함을 계약에 두어야 다른 표기가 조용히 `신규`로 묶이지 않는다(후보는 76/76 `신규(계획 DF-29~34 대상 외)`). 정정본 계약 3에 한 문장.
* M6. 계획 687행의 test-only 열거(TS0·TS2·TS3·TS5·TS7, TS6, redteam 데이터)에 '문서 산출 + 계약 test'가 없다. 근거는 승인된 design 20 §8 P10 행 "test-only(문서)"와 design 05 §9.2-4 모양 -- 초안이 둘 다 인용하므로 결함은 아니다. 판정 기록 V2 basis에 이 근거를 적으면 충분.
* M7. 계약 5가 `known-incidents.md` 104·125, `SKILL.md` 74처럼 **사고 이력** 줄에도 표시를 요구한다. `b22_lines.md` 문안이 괄호 표시만 붙이므로 이력은 보존된다 -- 수용 가능, 참고.

## 지정 점검 5개에 대한 답

1. **P10은 test-only인가 / references·SKILL.md는 누가 쓰나** -- 그렇다. code 커밋이 없다. 쓰기 경로(계획 N3.12.2, HEAD 실측): references `**` = 오케스트레이터 640행, `SKILL.md` 638행,
   `skill-validation-prompt.md` 639행(모두 조건 '없음' -- `판정 트리` 행보다 우선), 목록·생성기(`mk_df23_inventory.py`)·요약 = 626행 `docs/03-analysis/**`(레지스트리 제외), design = 624행,
   test = test-author 618행, 판정 기록 = auditor 621·622행. 오케스트레이터 references 수정 선례 `f48f5f6`(2026-09-22). 레지스트리(603행 code-author)를 뺀 분리는 옳다.
   docs 아래 `.py`는 `판정 환경` 행(`workspaces/*.py`·conftest 등)에 들지 않는다.
2. **test-author가 계약 문장만으로 쓸 수 있나 / base에서 통과인가 실패인가** -- test-author는 spec card와 interface card를 받는다(agent 정의). JSON 필드·닫힌 집합·열 이름은 계약에 다 있고,
   계획서를 test에서 읽는 것은 선례(conftest·`test_ic*`의 `read_plan_tables`)로 허용된다. **test-only는 base(문서 커밋 포함)에서 PASS여야 한다**: design 05 §9.2-4 test-only 모양은 병합이 없고
   T = `new^`, `code_commit` null, `red` 금지(00-common §8.1), 계획 N4.2 V2 test-only 증거는 'PASS'뿐. 거부 능력은 합성 입력 자기 점검 + 계약 8(`measured_at`에서 FAIL)로 보이며 CC-3 TS7 선례
   ("대조 test의 red는 합성 test 파일에서 FAIL")와 같은 구조 -- 일관된다. 리뷰어 실측으로 후보 목록은 계약 1~4를 만족하고, 계약 5는 19줄 표시 뒤 통과한다. 단 B1·B3을 고치지 않으면 '지금은 통과,
   다음 엔진 card에서 실패'다.
3. **P10b red** -- 모듈 머리 import면 수집 단계 `ImportError`(`reg_check`, `check_df23`) = 허용 타입(신규 심볼 쌍 일치). `SystemExit`는 도구가 잡는다. S4대로 import 위치를 계약에 둘 것.
4. **`reg_check.py` 경로와 E0** -- `A/tests/tools/**` = code-author 600행, 레지스트리 = 603행 → red-green이 맞다. E0 불변: `_section_lines`는 다음 `## ` 줄에서 끊으므로(64-78행) §7 판정은
   `## 8.` 추가와 무관하고, 새 규칙은 `--df23-inventory`가 있을 때만 돈다. `test_main_on_this_repository_is_clean`은 인자 없는 호출이라 영향 없음. 레지스트리를 파싱하는 다른 test·도구는
   `test_reg_check.py`뿐(git grep).
5. **순서 P10 → P10b, `measured_at` = 문서 커밋의 부모** -- 일관된다. 계획 N3.12.3 순서 1(design 05 §12 순서 0): spec card·interface card(와 이 card의 문서 커밋)를 gate에 push한 **뒤**
   `gate/master`에서 test worktree. 문서 커밋은 역할 커밋이 아니라 §9.2-3 '역할 커밋 없는 push'로 판정되고 card의 `old..new`에 들지 않는다. 역할 브랜치가 있는 동안 문서 push는 EL1이 거부하는데
   B28 브랜치는 검토 중 정리됐다(`role/*` 0). 문서 커밋이 spec card 커밋 앞이든 뒤든 엔진 blob은 같으므로 충돌 없음 -- 다만 '직전 커밋'이라는 말 대신 `measured_at`을 기준으로 적어야
   계약 6·8이 모호하지 않다(B2·S1). P10b는 P10 판정 기록이 gate에 들어간 뒤 착수, design 20 §8 P10b 행은 P10 문서 커밋에서 더한다 -- 순서 문제 없음.

## 정정본에서 바꾼 곳 (요약)

* P10: 순서 단락(§9.2 인용, 문서 커밋 하나·부모 = `measured_at`), 계약 1(blob 동일 → 7 (e), 예시 이름 백틱 제거), 계약 2(`phase_order`), 계약 3(`read_section_table`·`plan_phase_tokens`, 비DF → `신규`),
  계약 5(고정 분류, 엔진 미열람), 계약 6(`measured_at` 기준), 계약 7 (e)(f)·어휘 정의 인용, 계약 8(절차·기록 필드), 판정 유형 근거(§9.2-4, V2 basis), oracle 절, 재현할 수치, 결정 필요 항목 절차 문장,
  작성 전 실측 1c(어휘 정의)·1d(HEAD 8790b24)·2(`-k` 필터).
* P10b: 판정 유형 근거(모듈 머리 import, exit 2 짝 대조), 계약 1(CRLF), 계약 5 (d)(보충 뮤테이션), 작성 전 실측 머리(HEAD 8790b24).
* 사용자 결정 필요 항목: 없음(판정 기준 E3·E0 불변, 기존 test 변경 없음 → V5 없음).
