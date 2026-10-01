---
id: 20260930-df23-registry-record
phase: 2
evidence_type: red-green
gate_change: no
approval: 20260923-20-dead-code-dup-design
approval: 20261001-p10b-v3-equiv
---
## 의도

계획 DF-23(933행) `수정 Phase` 열 `2(전수 목록·레지스트리 기록), 4(일반 규칙으로 교체)`의 **Phase 2 몫 둘째 절반 -- 레지스트리 기록**을 한다. 첫째 절반(전수 목록)은
P10 `20260930-p10-df23-inventory`의 문서 커밋 0fa6ca2가 gate에 넣은 `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json`(`measured_at` = 766b5c2…, 515항목, 항목마다 `phase`)이다.
이 card는 그 목록을 함수 재사용 레지스트리 `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`에 **요약으로** 기록하고, 기록이 목록과 어긋나지 않았는지 기계로
보는 규칙을 레지스트리 검사 도구 `A/tests/tools/reg_check.py`에 더한다. A = `skills/analog-gmid-design/assets`.

**무엇을 기록하는가 -- 요약만, 목록 사본은 두지 않는다**: 레지스트리의 목적은 "이미 있는 것을 다시 만드는 실수를 막는다 … 이름으로 grep한다"(레지스트리 머리 4행)이다.
그래서 기록은 **함수 이름으로 찾을 수 있는 단위**(함수별 행)와 총계, 그리고 정본 목록의 경로·`measured_at`이다. 항목별(파일:줄) 행은 두지 않는다 -- (1) 목록 JSON이 유일한 정본이고
레지스트리에 515행 사본을 두면 두 곳이 따로 틀어진다(상수를 박지 않고 근거 하나만 둔다는 원칙), (2) 줄 번호는 엔진 card마다 움직인다(레지스트리 머리 "줄 번호는 코드가 바뀌면 틀어지므로",
P2 영구 바이트 대조를 P4에서 폐기한 선례 -- 승인 `20260930-p4-relocate-test-retire`). 함수별 행의 값(항목 수·DF·담당 Phase)은 목록에서 계산되는 값이고, 계약 3의 도구 규칙이
그 계산과 같은지 대조한다(손으로 옮긴 숫자가 목록과 어긋나면 도구가 잡는다).

**왜 도구 규칙이고 영구 test가 아닌가**: 실제 레지스트리와 실제 목록을 매번 대조하는 영구 contracts test를 두면, 목록(오케스트레이터 경로, N3.12.2 626행)과 레지스트리(code-author 경로,
603행)를 쓰는 주체가 달라 **다음에 목록을 다시 재는 오케스트레이터 문서 커밋이 gate에 들어가는 순간 그 test가 base에서 실패**하고, 그 뒤 모든 card의 base가 기존 test 실패 상태가 된다
(두 파일을 한 커밋에서 바꿀 수 있는 역할이 없다). 같은 역할이 양쪽을 쓰는 P7의 `test_main_on_this_repository_is_clean`(레지스트리 대 엔진, 둘 다 code-author)과 다르다.
그래서 실제 파일 대조는 **도구 실행**(auditor 측정과 Phase DoD 측정)으로 하고, 영구 test는 도구 규칙을 합성 입력으로 판정한다(P7 `20260930-registry-grade-fix`와 같은 구조).

**E0는 그대로다**: 새 규칙은 새 선택 인자 `--df23-inventory <경로>`를 줄 때만 돈다. 인자 없는 호출(= design 20 §10 E0 명령, 218행)의 동작·출력은 base와 같다.

**순서(착수 조건)**: P10의 판정 기록이 gate `master`에 있은 뒤 착수한다(충족: 62ae24f). 이 card의 base = P10 판정 기록 커밋 62ae24f 또는 그 후손(P10 test 커밋의 `test_df23_inventory.py`·`test_phase2_stale_refs.py` 포함).
게이트 card 순서(사용자 결정 2026-10-01 A1-a의 순서 문구 "P9·P10·P10b 뒤"): **P10 → P10b → V3 면제 묶기 `20260930-v3-exempt-binding` → V3 범위 정책 `20260930-v3-changed-stmt-scope`** -- 그래서 이 card의 V3는
base의 `mutate_changed.py`(지금 규칙)로 판정한다('판정 유형 근거' 끝).
design 20 §8의 P10b 행(195행)은 P10 문서 커밋 0fa6ca2에서 이미 더해졌다.

## 관찰 가능한 계약

1. **레지스트리 §8 (code 커밋)**: 레지스트리 끝(§7 뒤)에 절 하나를 더한다. §0~§7은 base와 바이트 동일하다(`git diff base M -- <레지스트리>`가 파일 끝 추가 줄뿐).
   줄 끝은 기존 파일과 같게 둔다(blob은 LF, 작업 트리는 autocrlf로 CRLF -- 1차 시도 auditor 실측: base blob 524줄이 병합본 601줄의 접두. 섞으면 diff가 끝 추가만이 아니게 된다. 도구는 `str.splitlines()`로 줄을 나누므로 줄 끝 문자는 판정에 들지 않는다).
   모양(제목 줄·표 머리는 이 글자 그대로 -- 도구가 읽는다):
   * 제목 `## 8. DF-23 -- 엔진 이름 리터럴 종속 (전수 목록 기록)`.
   * 제목 다음 본문에 두 줄: `목록: \`docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json\``, `measured_at: \`<목록의 measured_at 값>\``.
     그리고 사용 규칙 한 문장: "목록을 다시 재면 이 절을 같은 Phase 안에서 갱신한다(대조: `reg_check.py --df23-inventory`)."
   * `### 8.1 총계` 아래 표 머리 `| 축 | 값 | 항목 수 |`. 행 = 목록 항목 전부에 대한 목록 필드 `role` 값별 개수(`| role | <값> | <n> |`)와 필드 `phase` 값별 개수(`| phase | <값> | <n> |`). 개수 0인 값의 행은 없다.
   * `### 8.2 함수별 (role = 동작을 정함)` 아래 표 머리 `| 함수 | 파일 | 항목 수 | DF | 담당 Phase |`. 행 = 필드 `role`이 `동작을 정함`인 항목을 (필드 `function`, 필드 `file`의 마지막 `/` 경로 성분)으로 묶은 묶음마다 하나:
     `함수` = 백틱으로 싼 `function` 값 그대로(P10 계약 1 정의 -- 모듈 최상위 정의 단위, 모듈 수준 `<module>`, 클래스 본문, 클래스 직속 메서드의 점 표기 포함), `파일` = 파일 이름(백틱 없음), `항목 수` = 묶음 크기,
     `DF` = 묶음 항목의 필드 `plan_mapping`에서 정규식 `^DF-(\d+)`로 뽑은 번호를 `DF-<n>`으로 중복 없이 모아 정수 오름차순으로 놓고, `신규`로 시작하는 항목이 있으면 끝에 `신규`를 더해 ", "로 이은 것,
     `담당 Phase` = 묶음 항목의 필드 `phase` 값을 중복 없이 **문자열 오름차순**(Python `sorted`, 코드포인트 순)으로 ", "로 이은 것. 행 순서는 (파일, 함수) 문자열 오름차순(도구는 순서를 판정하지 않는다 -- 행 집합만 본다).
     (문자열 오름차순은 P10 계약 2의 닫힌 집합 {`3`, `4`, `5`, `6a`, `6b`, `6c`, `7a`, `7b`, `7c`, `해당 없음`}에서 계획 N6.1 순서와 같다. 도구에 N6.1 순서 목록을 따로 박지 않으려는 정의다.)
2. **E0 불변**: 병합본에서 `reg_check.py --registry <레지스트리> --root <루트>`(인자 추가 없음)는 exit 0 `reg_check: 발견 0`이고, 기존 `test_reg_check.py` 전부 PASS
   (`_section_lines`가 다음 `## ` 줄에서 절을 끊으므로 §8은 §7·§1 규칙 대상이 아니다 -- 실측 5).
3. **도구 규칙 (code 커밋)** -- `reg_check.check_df23(registry_text, inventory, inventory_rel)`이 발견 목록(기존 `check`와 같은 `{"rule", "section", "name", "detail"}` 레코드)을 돌려준다.
   `inventory`는 목록 JSON을 읽은 dict, `inventory_rel`은 목록의 저장소 루트 기준 `/` 상대 경로. 모든 기대값은 `inventory["items"]`에서 계산한다(목록의 `totals`를 믿지 않는다). 규칙:
   * `df23-section`: `## 8.`로 시작하고 `DF-23`을 담은 제목 줄이 없다, 또는 그 절(다음 `## ` 줄 전까지)에 `목록:`·`measured_at:` 줄이나 `### 8.1`·`### 8.2` 소절 아래 계약 1의 표 머리를 가진 표가 없다
     (빠진 것마다 발견 하나, `name` = 빠진 것: `title`·`목록`·`measured_at`·`8.1`·`8.2`). 제목 줄이 없으면 이 발견 하나만 내고 다른 규칙은 보지 않는다.
   * `df23-path`: `목록:` 줄의 백틱 경로 ≠ `inventory_rel`(`name` = 레지스트리 쪽 값).
   * `df23-measured-at`: `measured_at:` 줄의 백틱 값 ≠ `inventory["measured_at"]`(`name` = 레지스트리 쪽 값).
   * `df23-total`: §8.1 행 집합 {(축, 값) → 항목 수} ≠ 항목에서 센 값. 빠진 행·남는 행·다른 수·같은 (축, 값)의 두 번째 행마다 발견 하나(`name` = `<축>:<값>`).
   * `df23-function`: §8.2 행 집합 {(함수, 파일) → (항목 수, DF, 담당 Phase)} ≠ 계약 1 규칙으로 항목에서 만든 값. 빠진 행·남는 행·다른 칸·같은 (함수, 파일)의 두 번째 행마다 발견 하나
     (`name` = `<파일>::<함수>`).
   **절·소절·행 경계**(1차 시도 V3 생존으로 드러난 정의 -- 규칙 문장의 범위를 명시한다): §8 = `## 8.`로 시작하고 `DF-23`을 담은 **첫** 제목 줄부터 그 뒤 처음 `## `로 시작하는 줄 전까지(§8 뒤 절의 줄·표는 읽지 않는다).
   §8.1/§8.2 표 = §8 안에서 `### 8.1`/`### 8.2`로 시작하는 첫 줄부터 그 뒤 처음 `### `로 시작하는 줄 전까지에 있는 표 중 계약 1 표 머리를 가진 것(다른 `###` 소절 아래 같은 머리의 표는 읽지 않는다).
   행의 칸이 표 머리보다 적으면 모자란 칸을 빈 문자열 `""`로 보고(예외를 내지 않는다), 많으면 표 머리 칸 수 뒤의 칸은 무시한다.
   **`detail`**(값이 다른 행의 발견만 판정 대상, 나머지 발견의 `detail`은 자유 문장): `df23-total`의 다른 수 → `detail == f"항목 수 {reg!r} != {exp!r}"`(`reg` = 레지스트리 `항목 수` 칸 문자열, `exp` = 센 수의 10진 문자열),
   `df23-function`의 다른 칸 → `detail == f"(항목 수, DF, 담당 Phase) {reg!r} != {exp!r}"`(`reg` = 레지스트리 세 칸 문자열의 tuple -- 모자란 칸은 `""`, `exp` = 계약 1 규칙으로 만든 세 값 문자열의 tuple).
   칸 문자열은 `|`로 나눈 뒤 앞뒤 공백을 뗀 값이다.
   입력 오류 → `ValueError`: (o) `inventory`가 dict가 아니다, `items`가 list가 아니다, 항목이 dict가 아니다(`TypeError` 등 다른 예외로 새지 않는다), (i) `inventory`에 `measured_at`·`items`가 없다, (ii) 항목에 `file`·`function`·`role`·`phase`·`plan_mapping` 중 하나가 없다, (iii) `function`이 빈 문자열이다,
   (iv) 서로 다른 `file` 값이 같은 마지막 경로 성분을 가진다(파일 칸이 모호), (v) `role`이 `동작을 정함`인 항목의 `plan_mapping`이 `^DF-\d+`에도 맞지 않고 `신규`로도 시작하지 않는다
   (P10 계약 3이 보장하는 형식 -- 다른 표기를 조용히 `신규`로 묶지 않는다).
4. **CLI (code 커밋)**: `main(argv)`에 선택 인자 `--df23-inventory <경로>`. 주면 기존 판정 발견 뒤에 `check_df23` 발견을 더해 같은 형식(JSON 한 줄씩)으로 출력하고 exit 규칙(0 = 발견 0, 1 = 발견, 2 = 입력 오류 --
   목록 파일 없음·JSON 아님·최상위가 dict 아님·`ValueError` 포함)은 기존과 같다. `inventory_rel` = `os.path.relpath(realpath(목록), realpath(--root))`를 `/`로 이은 것이고, 루트 안인지는
   `os.path.normcase(os.path.realpath(…))` 두 값의 `os.path.commonpath`로 판정한다(루트 밖이면 exit 2). 인자를 주지 않으면 출력·exit가 base 도구와 같다.
   발견 0이면 표준 출력의 마지막 줄이 정확히 `reg_check: 발견 0`이다(계약 2·5 (a)가 말하는 출력). 알 수 없는 인자는 `SystemExit`로 새지 않고 `main`이 정확히 2를 돌려준다.
   표준 출력 인코딩이 UTF-8이 아닌 환경(예: 환경 변수 `PYTHONIOENCODING=ascii`로 스크립트를 실행)에서도 `UnicodeEncodeError` 없이 exit 0과 UTF-8 바이트 `reg_check: 발견 0`을 낸다(base 도구의 표준 출력 재설정 동작).
5. **실제 저장소 대조 (auditor 측정 -- 영구 test가 아니다, 위 '왜 도구 규칙인가')**:
   (a) 병합본 격리 복제본에서 `reg_check.py --registry <iso>/docs/03-analysis/gain-budget-gmid-sizing.function-registry.md --root <iso> --df23-inventory <iso>/docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json` → exit 0, `발견 0`.
   (b) 거부 확인: 같은 명령을 base 레지스트리(§8 없음)와 병합본 도구로 돌리면 `df23-section` 발견, exit 1.
   (c) auditor 독립 재계산: auditor 자신의 스크립트(도구·code-author 산출을 쓰지 않는다)로 목록 `items`에서 §8.1·§8.2 값을 다시 만들어 병합본 레지스트리 §8 표와 같음.
   (d) 보충 뮤테이션: '판정 유형 근거' 끝 -- `mutate_changed.py`(V3)는 이 card의 변경 경로에서 대상 0이므로 auditor 자신의 변이 스크립트로 `check_df23`의 규칙 분기마다
   (5규칙, `ValueError` (i)~(v), CLI `--df23-inventory` 경로의 exit 2 분기·루트 밖 분기·발견 합치기) 변이를 넣어 새 test가 죽이는지 재고 `checks.V3.basis`에 적는다(생존 0 -- 승인 `20261001-p10b-v3-equiv`의 변이 id 중 auditor가 2차 병합본에서 등가로 다시 판정한 것만 제외.
   변이 대상 def·연산자는 1차 시도 `scripts/mut_df23.py`와 같게 해 id를 비교할 수 있게 한다).
6. **범위**: `git diff base M`의 경로 = 레지스트리, `A/tests/tools/reg_check.py`, `A/tests/contracts/` 새 test 파일 하나(`test_reg_check_df23.py`). 엔진(`A/*.py`, `workspaces/run_harness.py`)·library·목록 JSON·기존 test는
   바뀌지 않는다(E-LIB·E-INST 자명 동일). 새 코드에 회로·소자·넷·함수 이름 리터럴이 없다(묶음·열 값은 전부 목록 필드에서 온다 -- 일반성. 도구가 아는 리터럴은 목록 필드 이름과 필드 값 `동작을 정함`·`신규`, 표 머리뿐이다).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `reg_check` | `check_df23` | `def check_df23(registry_text: str, inventory: dict, inventory_rel: str) -> list` |

## 판정 유형 근거

red-green: 레지스트리는 gmid-code-author 경로(계획 N3.12.2 603행)이고 도구는 `A/tests/tools/**`(600행, code-author)라 이 card에는 `Role: code` 커밋이 있다 -- code 커밋이 있으면
test-only 모양(`old..new^` 전부 `Role: test`, 병합 없음 -- design 05 §9.2-4 표)이 성립하지 않는다(P2·P7 교훈). equivalence는 새 test가 base에서 통과해야 하는데 base에 `check_df23`이 없다.

**red의 모양**: 새 test 파일은 tools 디렉터리를 `sys.path`에 넣은 뒤(`test_reg_check.py` 51-59행과 같은 방식) **모듈 머리에서 `reg_check`를 가리키는 첫 import 문으로 `from reg_check import check_df23`**를 둔다
(CLI test에 쓰는 `main`은 같은 문의 뒤 이름이나 그 다음 문에서 가져온다). base에서 이 문은 수집 단계 `ImportError`(`name` = `reg_check`, `name_from` = `check_df23` -- Python 3.14 실측)로 실패하고, 그 쌍
(`reg_check`, `check_df23`)이 interface card 신규 시그니처 표의 쌍과 같아 red 수집 플러그인이 허용 타입으로 기록한다(`merge_gate.py` 588-603행 `_ALWAYS_RED`·`_NEW_SYMBOL_TYPES`·`new_symbol_pair`,
수집 오류는 `pytest_exception_interact`가 `__cause__`로 읽는다; 00-common §8.1 302·303행 "`from M import X`의 `ImportError` → (`name`, `name_from`)"). 병합본에서 green.
P7은 같은 자리가 `ModuleNotFoundError`(쌍 (`reg_check`, `*`))였다 -- 이 card는 모듈이 base에 이미 있어 `ImportError` 쌍이다.
**import를 test 함수 안에 두지 않는다**: 그러면 base에서 CLI test 중 exit 2를 기대하는 것(목록 파일 없음·`ValueError`)이 base 도구의 argparse 인자 거부
(`reg_check.py` 191-194행: `SystemExit`를 잡아 2를 돌려줌 -- 실측: HEAD 도구에 `--df23-inventory x`를 주면 `unrecognized arguments`, exit 2)만으로 **통과**해 계획 N4.2 V2(838행) red-green 조건
("새 test가 base에서 FAIL")을 어기고 판별력이 없다. 같은 이유로 exit 2 test는 같은 test 안에서 정상 입력의 exit 0 대조를 짝으로 둔다(병합본에서도 인자 거부와 입력 오류를 가른다).
동작 보존(엔진)은 계약 6(범위)이 대신한다 -- 엔진 경로 변경 0.

**V3(뮤테이션) -- 이 card base에서 적용되는 규칙**: 게이트 card 순서상 이 card는 V3 면제 묶기(`20260930-v3-exempt-binding`, A1-a)와 V3 범위 정책(`20260930-v3-changed-stmt-scope`, A1-b의 N2 (b) + 넓힌 T6)
**앞**에 병합되므로, V3는 base의 `tools/gates/mutate_changed.py`(대상 = diff가 닿은 def 중 AST 해시가 바뀐 것의 본문 전체)로 돈다. 그 도구의 대상 파일은 `reachability._is_source`
(`A/` 바로 아래 `*.py`와 `workspaces/run_harness.py`, 175-177행)뿐이라 이 card의 변경(`A/tests/tools/reg_check.py`, 레지스트리, 새 test)에서는 대상 0이다(P7 판정 기록 V3 `targets []`, `mutants 0` 선례).
두 V3 card가 먼저 들어오더라도 대상 파일 규칙(`_is_source`)은 바꾸지 않으므로 결론은 같다. 그래서 계약 5 (d)의 auditor 보충 뮤테이션(P7 `scripts/mut_regcheck.py` 방식)을 둔다.

## oracle 종류와 출처

(a) 구성 입력: 합성 목록(dict)·합성 레지스트리 조각 -- 기대는 계약 1·3의 규칙 문장으로 test가 직접 만든다(도구 출력을 기대값으로 쓰지 않는다). 합성 목록의 함수·파일 이름은
**지어낸 이름**(`alpha_fn`, `mod_a.py` 등)만 쓴다 -- 삭제·이동 이름 스캔 test(`test_d_delete_dead`·`test_d_delete_telescopic`·`test_d_move_tests`)와 IC 표식 대조(`test_ic_markers_match_plan`)에 걸리지 않게,
그리고 **엔진 def 이름과 같은 문자열을 두지 않는다**(V3·V7 정적 호출 그래프가 def 이름과 같은 문자열 상수를 간선으로 잇는다 -- `reachability.py` 머리 문서; 예: `run`·`main` 금지).
**test 작성 규칙**(test-author가 읽는 절이라 여기 적는다 -- 이유는 '판정 유형 근거'): tools 디렉터리(`A/tests/tools`)를 `sys.path`에 넣은 뒤 **모듈 머리에서 `reg_check`를 가리키는 첫 import 문으로
`from reg_check import check_df23`**를 둔다(test 함수 안에 import를 두지 않는다; `main`은 같은 문의 뒤 이름이나 그 다음 문으로). exit 2를 기대하는 CLI test는 같은 test 안에 정상 입력의 exit 0 대조를 짝으로 둔다.
helper 이름은 `_p10b_` 접두사(P10 test가 `_p10_`를 쓴다 -- 그래프가 이름으로 잇는 '같은 이름의 모든 def' 간선을 피한다), test 함수 이름은 `test_p10b_` 접두사.
피검 심볼은 **직접 호출**한다(`check_df23(...)`, `main([...])` -- `getattr`·parametrize 문자열로 심볼 이름을 넘기지 않는다). 경로를 비교하는 test(루트 밖 판정 등)는 `os.path.normcase(os.path.realpath(…))`로 비교한다.
**판정 문장 모양**(1차 시도 V4 `test_lint` FAIL에서 온 규칙): (1) 모든 test 함수는 **본문에 직접** `assert`를 하나 이상 둔다(helper 안의 assert만으로 판정하지 않는다 -- helper는 값을 돌려주고 test 본문이 판정한다).
(2) 빈 발견은 `assert len(findings) == 0`로 판정한다(`assert findings == []`처럼 피검 함수가 돌려줄 수 있는 리터럴과 같은지 비교하지 않는다 -- `test_lint` (2) '확실한 복사'로 읽힌다).
발견이 있는 경우는 발견 레코드의 (`rule`, `name`) 다중집합이나 `detail` 문자열을 규칙 문장에서 만든 값과 비교한다.
(d) 실측 원자료: 계약 5의 기대는 card base의 목록 JSON(P10 산출, auditor가 독립 재계산).

## 거부해야 할 입력

규칙마다 합성 조각 → 발견: §8 없음·`measured_at:` 줄 없음·§8.2 표 머리 다름(`df23-section`), 경로 다름(`df23-path`), `measured_at` 한 글자 다름(`df23-measured-at`), §8.1에 `phase` 값 행 하나 빠짐·남는 행·수 1 차이·같은 행 두 번
(`df23-total`), §8.2에 묶음 하나 빠짐·목록에 없는 (함수, 파일) 행·`항목 수` 1 차이·`DF` 칸에 `신규` 빠짐·`DF` 칸 번호 순서가 정수 오름차순이 아님(`DF-19, DF-4`가 아니라 `DF-4, DF-19`)·`담당 Phase`가 문자열 오름차순이 아님(`7b, 4`)·같은 행 두 번(`df23-function`).
입력 오류 → `ValueError`(CLI exit 2): `function` 빈 문자열, `phase` 없는 항목, `measured_at` 없는 목록, 같은 파일 이름의 다른 경로, 동작 항목 `plan_mapping`이 `기타`처럼 DF 번호도 `신규`도 아님, 목록 파일 없음, 목록이 루트 밖.
경계·모양(계약 3 '절·소절·행 경계'·`detail`, 계약 4 출력·종료): §8 뒤에 `## 9.` 절을 두고 그 안에 §8.1·§8.2 표 머리와 같은 표(틀린 값)를 둔 레지스트리(→ 그 표를 읽지 않음),
§8 제목과 같은 모양의 두 번째 제목 줄 뒤에 다른 표를 둔 레지스트리(→ 첫 제목의 절만 읽음), `### 8.1` 뒤에 다른 `### ` 소절을 두고 그 아래 §8.1 머리 표(틀린 값)를 둔 레지스트리(§8.2도 같은 모양),
§8.1·§8.2의 칸이 모자란 행(→ 예외 없이 다른 값 발견, `detail`의 `reg`에 `""`)·칸이 표 머리보다 많은 행(→ 앞 칸이 맞으면 발견 0), 값이 다른 행의 `detail` 정확 일치(§8.1·§8.2 각각),
`inventory`가 dict 아님·`items`가 list 아님·항목이 dict 아님(→ `ValueError`, `check_df23` 직접 호출), 발견 0일 때 표준 출력 마지막 줄 `reg_check: 발견 0`,
알 수 없는 인자 → `main`이 정확히 2를 돌려줌, `PYTHONIOENCODING=ascii`로 스크립트 실행(subprocess) → exit 0과 UTF-8 `reg_check: 발견 0`.
발견하면 안 되는 것: §0~§7의 표(§8 밖), 목록 `totals`가 틀렸지만 `items`에서 센 값과 §8이 같은 경우(도구는 `items`만 믿는다), `role`이 `메시지뿐`인 항목(§8.2 대상 아님 -- `plan_mapping`이 `DF-31(…)`처럼 DF 번호로 시작해도,
`신규`로도 DF로도 시작하지 않아도 마찬가지. P10 계약 2·3: 메시지뿐 항목은 옛 목록의 `plan_mapping`을 그대로 가질 수 있다), §8.2 행 순서만 다른 레지스트리.
`--df23-inventory` 없이 §8 없는 레지스트리 → 기존 규칙만(발견 0이면 exit 0).

## library 회로 적용 여부

해당 없음(문서·도구). 엔진 불변이라 E-LIB·E-INST는 base와 같다.

## 무동작 판정 입력(무발동 값)

`--df23-inventory`를 주지 않은 `reg_check.py` 호출 전부(E0 명령, `test_main_on_this_repository_is_clean`) -- 출력·exit가 base와 같다. 엔진·library·기존 test 전부.

## 재현할 수치

auditor가 독립으로 센다: 병합본 §8.1 행(role별·phase별 개수), §8.2 행 수와 행마다 (항목 수, DF, 담당 Phase), 계약 5 (d) 변이 수·죽인 수 -- 값은 card base 목록에서 정해진다(작성자 수를 옮겨 적지 않는다).
비교용(오케스트레이터 작성 전 실측, HEAD 2d58fd8의 목록 -- 62ae24f에서 같은 blob -- 판정 수치가 아니고, 영구 test는 이 수를 쓰지 않는다: 영구 test 입력은 합성 목록뿐): 515항목, role `메시지뿐` 302·`동작을 정함` 213, phase `해당 없음` 317·`4` 63·`3` 61·`7b` 46·`7a` 27·`6b` 1(§8.1 8행),
동작 항목의 (함수, 파일) 묶음 52(§8.2 52행), 빈 `function` 0, 파일 이름 8개 모두 다름, 동작 항목 `plan_mapping` 중 `^DF-\d+`가 아닌 76개 전부 `신규`로 시작.

## 결정 필요 항목

결정됨: 1차 시도(판정 36a6ec8, push 안 됨 -- EL4 거부 사유 V3·V4) 뒤 보충 뮤테이션 생존 중 등가 9개의 면제를 사용자가 승인했다(승인 `20261001-p10b-v3-equiv`, 2026-10-01 "등가 9만 승인").
면제는 그 기록의 변이 id에만 적용되고, auditor가 2차 병합본에서 각 id가 여전히 등가인지(같은 입력에 같은 결과·발견·exit) 다시 판정한다 -- 구조가 바뀌어 id가 맞지 않으면 면제도 적용되지 않는다.
`detail`만 다른 변이 6개는 면제하지 않고 계약 3 `detail` 정의로 판정한다(사용자 선택). 나머지 비등가 30개는 계약 3·4의 경계·모양 문장과 '거부해야 할 입력' 추가 항목으로 test가 죽인다.
오케스트레이터 메모:
* **P10과의 접점(반영됨)**: P10 계약 1이 `function`을 두 card 공통으로 정의하고(모든 항목이 비지 않은 값) 계약 3이 동작 항목 `plan_mapping`을 `^DF-\d+` 또는 `신규`로 제한한다 -- 이 card 계약 3 `ValueError` (iii)·(v)는 그 형식을
  도구 쪽에서 다시 거부하는 것이다(조용한 기본값 금지). 커밋된 목록(0fa6ca2)에서 둘 다 성립한다(재현할 수치).
* **design 20 §8 P10b 행**: P10 문서 커밋 0fa6ca2에서 195행으로 더해졌다(초안 문안 그대로). 이 card는 design 문서를 바꾸지 않는다.
* Phase 2 DoD 브리핑: E3 판정 기준은 바꾸지 않고, 계획 DF-23 행 '레지스트리 기록'의 증거로 계약 5 (a) 명령을 auditor가 한 번 더 돌려 DoD 기록 N6.3 옆에 적는다(판정 기준 변경 아님).

## 작성 전 실측

(첫 측정 HEAD = gate `master` 2d58fd8, 2026-10-01. **62ae24f 재측정 -- 1·5·7 변화 없음**: P10 판정 기록 62ae24f(test 커밋 56b86c6 포함)가 gate에 들어간 뒤 다시 쟀다. `role/*` 브랜치 0.
`git diff 2d58fd8 62ae24f`는 `.ai/verification/20260930-p10-df23-inventory.json`·`…/base_check.json`, `A/tests/contracts/test_df23_inventory.py`·`test_phase2_stale_refs.py` 네 파일뿐이고
`docs/01-plan`·`docs/02-design`·`docs/03-analysis`(레지스트리·목록)·`A/tests/tools`·엔진·`tools/`는 같다. 재실행: E0 명령 exit 0 `발견 0`, `--df23-inventory x` exit 2, 레지스트리 마지막 변경 a410f31,
`test_reg_check.py` 381·424·432·444행 그대로. 바뀐 것은 실측 2의 P10 test 두 파일이 gate에 있다는 점뿐(아래). 저장소 읽기 전용, python `C:\Python314\python.exe -B`, scratch `C:/g79`(측정 뒤 삭제).
이 card의 base = 62ae24f 또는 그 후손.)
1. 사실 문장 재측정: `grep -n "^## " <레지스트리>` → §0(7)·§1(21)·§2(31)·§3(61)·§4(271)·§5(397)·§6(447)·§7(483), 524줄(CRLF 524/524, 끝 `|\r\n\r\n`), 마지막 절 = §7 `기타 모듈 (1)` 표.
   `grep -c "DF-23\|df23" <레지스트리>` → 0(기록 없음). 레지스트리 마지막 변경 a410f31(P9).
   목록(`git show HEAD:<목록>`, json): 최상위 키 `measured_at·scope·scope_files·method·method_params·phase_rule·phase_source·vocabulary·totals·items`, `measured_at` = 766b5c2b486df66e143feb1f9440084a62db0ebc(40자리 소문자 16진),
   515항목, 모든 항목이 `file·function·role·phase·plan_mapping`을 가짐(공통 키: `context·declared_in·file·function·kind·line·literal·mapping_source·new_subcategory·phase·plan_mapping·role·role_reason·scan·source_line`),
   빈 `function` 0, 점 표기·클래스 값 `InfeasibleSizingError`·`SemiEmpiricalGmIdLUT.__init__`·`SemiEmpiricalGmIdLUT.cgg_absolute`(메시지뿐)·`SizingContext`(동작 1), 파일 8개(`A/` 7 + `workspaces/run_harness.py`) 이름 모두 다름.
   items에서 센 값 = `totals.by_role`·`totals.by_phase`(재현할 수치). §8.2 묶음 52, phase 값은 모두 P10 닫힌 집합 안(문자열 오름차순 = N6.1 순서 확인).
   `reg_check.py --registry <레지스트리> --root .` → `reg_check: 발견 0`, exit 0. 같은 명령 + `--df23-inventory x` → argparse `unrecognized arguments`, exit 2(191-194행).
   계획 933행 DF-23 `수정 Phase` 열 `2(전수 목록·레지스트리 기록), 4(일반 규칙으로 교체)`. design 20 §8 195행 P10b 행 있음, §10 E0 218행·E3 221행.
2. 이름 충돌: 새 test `A/tests/contracts/test_reg_check_df23.py` -- 62ae24f의 `ls A/tests/contracts`에 없음(`reg_check` 관련은 `test_reg_check.py`만; 62ae24f에 들어온 P10 test `test_df23_inventory.py`·`test_phase2_stale_refs.py`와 이름이 다르고,
   두 파일은 `reg_check`를 import하지 않으며(`merge_gate`·`role_paths`만, `sys.path.append`) helper 접두사는 `_p10_`, `_p10b_`·`check_df23` 사용 0, test 이름에 `dup_`·`new_topology` 0).
   `grep -rn "glob(" A/tests`(62ae24f) → `*.py`·`probe_*.py`·`<접두>probe_*.py`·`*.topology.json`(P10 test 109행 library 추가)·`*.md`(P10 test 85행 `references` `rglob` 추가) -- 새 파일 이름과 겹침 없음. DoD `-k` 필터(design 20 E1 219행 `dup_w_calc or dup_kcl_edges`, E5 222행 `new_topology`)에 걸리지 않음
   (test 이름에 `dup_`·`new_topology`를 넣지 않는다). `*.py` 전수 스캔 test(삭제 이름·IC 표식·print 판정) 대상이므로 합성 이름은 지어낸 이름만(oracle 절).
3. 원칙의 계약화: '목록이 유일한 정본, 레지스트리는 계산된 요약' → 계약 1(값 정의)·3(`items`에서 계산해 대조)·5(c)(auditor 독립 재계산). '이름 종속을 코드에 넣지 않는다'·'상수를 박지 않는다' → 계약 6 끝,
   계약 1의 `담당 Phase` 순서를 N6.1 목록 상수 대신 문자열 오름차순으로 정의. '조용한 기본값 금지' → 계약 3 `ValueError` (iii)·(v). '작성자≠검증자' → 계약 5는 auditor 측정.
4. 쓰기 경로(계획 N3.12.2 표): 레지스트리 = gmid-code-author(603행), 도구 = gmid-code-author(600행 `A/tests/tools/**`), 새 test = gmid-test-author(618행, 제외 `tests/tools/**`),
   목록 JSON = 오케스트레이터(626행, 레지스트리 제외 -- 이 card는 목록을 바꾸지 않는다), 판정 기록 = auditor(621·622행).
   test-author는 도구 소스를 읽지 않고 interface card(신규 시그니처 표 -- 생성기 출력은 기존 함수 행 0, 실측 9)와 spec card의 '관찰 가능한 계약'·'oracle 종류와 출처'·'거부해야 할 입력'·'재현할 수치' 절만으로 쓴다
   (`.claude/agents/gmid-test-author.md` 21-22행). 그래서 red 모양에 필요한 import 위치 규칙은 oracle 절에도 적었다.
5. 계획서 소비자·E0 영향: 지우거나 바꾸는 이름 없음. `reg_check.py` `_section_lines`(64-78행)가 다음 `## ` 줄(75행)에서 절을 끊고 `check`가 105·112행에서 `## 7.`·`## 1.`만 읽는다 → §8 추가는 E0 규칙 밖.
   `grep -rn "df23-registry\|P10b" docs/01-plan docs/02-design` → design 20 195행(P10b 행), P10 spec card(61·65·77·188·195행 -- 공통 정의·분리 표, 바꾸지 않음).
6. 미배선: 새 def `check_df23`은 `main`의 `--df23-inventory` 경로에서 불리고, `main`은 이 card의 auditor 측정(계약 5)과 Phase 2 DoD 브리핑(결정 필요 항목 셋째 점), 그리고 목록을 다시 잴 때의 갱신 규칙(§8 사용 규칙 문장)에서 실행된다
   -- P7 `check`/`main`과 같은 DoD 측정 도구 배선. 운영 엔진 경로 밖이 맞는 도구(`A/tests/tools/`)이고 V7 그래프 대상(`_is_source`) 밖이라 V7 면제 승인 대상 아님(P7 V7 PASS 선례, 판정은 auditor).
   P7과 다른 점: P7은 `test_main_on_this_repository_is_clean`이 V1마다 실제 저장소에 `main`을 돌렸지만, 이 card의 실제 대조는 '왜 도구 규칙인가'의 이유로 영구 test가 아니다 -- 실제 호출 증거는 계약 5 (a)·(b) 실행 기록이다.
7. 기존 계약 test: `grep -rln "reg_check" A/tests` → `contracts/test_reg_check.py`(와 도구 자신)뿐. 그 test는 `main(["--registry", …, "--root", …])` 형태만 쓰고(381·424·432행) 모르는 인자 거부를
   판정하지 않는다 -- 새 선택 인자와 충돌 없음, 조정 불필요, V5 없음. `test_main_on_this_repository_is_clean`(444행)은 인자 없는 호출이라 §8 추가 뒤에도 exit 0이어야 한다(계약 2).
8. red 타입 실측: `from <있는 모듈> import check_df23`(scratch 모듈) → `ImportError`, `name` = 모듈 이름, `name_from` = `check_df23`(Python 3.14). `merge_gate.new_symbol_pair`가 이 둘을 쌍으로 만든다(600-602행).
9. 머리·interface card 실측(scratch `C:/g79/v.py`): `role_paths.parse_spec_card` → 통과(id `20260930-df23-registry-record`, phase `2`, red-green, gate_change no, approval `20260923-20-dead-code-dup-design` -- `.ai/approvals/`에 있음),
   절 11개가 양식(`_TEMPLATE.spec.md`) 순서와 같다. `interface_card.build`(HEAD 엔진) → '관찰 가능한 계약' 표의 기존 함수 0행(계약 절의 백틱 토큰 중 엔진 def와 같은 이름 없음), '신규 시그니처' 표에
   (`reg_check`, `check_df23`) 1행. 같은 출력에서 `merge_gate.read_new_symbols`·`test_lint.read_card_symbols` → {(`reg_check`, `check_df23`)} -- red 플러그인·V4가 읽는 쌍과 같다.
