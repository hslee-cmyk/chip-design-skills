---
id: 20260930-df23-registry-record
phase: 2
evidence_type: red-green
gate_change: no
approval: 20260923-20-dead-code-dup-design
---
## 의도

계획 DF-23(933행) `수정 Phase` 열 `2(전수 목록·레지스트리 기록), 4(일반 규칙으로 교체)`의 **Phase 2 몫 둘째 절반 -- 레지스트리 기록**을 한다. 첫째 절반(전수 목록)은
P10 `20260930-p10-df23-inventory`가 card base에서 다시 잰 `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json`(`measured_at`·항목마다 `phase`)이다.
이 card는 그 목록을 함수 재사용 레지스트리 `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`에 **요약으로** 기록하고, 기록이 목록과 어긋나지 않았는지 기계로
보는 규칙을 레지스트리 검사 도구 `A/tests/tools/reg_check.py`에 더한다. A = `skills/analog-gmid-design/assets`.

**무엇을 기록하는가 -- 요약만, 목록 사본은 두지 않는다**: 레지스트리의 목적은 "이미 있는 것을 다시 만드는 실수를 막는다 … 이름으로 grep한다"(레지스트리 머리 3-4행)이다.
그래서 기록은 **함수 이름으로 찾을 수 있는 단위**(함수별 행)와 총계, 그리고 정본 목록의 경로·`measured_at`이다. 항목별(파일:줄) 행은 두지 않는다 -- (1) 목록 JSON이 유일한 정본이고
레지스트리에 590행 사본을 두면 두 곳이 따로 틀어진다(상수를 박지 않고 근거 하나만 둔다는 원칙), (2) 줄 번호는 엔진 card마다 움직인다(레지스트리 머리 "줄 번호는 코드가 바뀌면 틀어지므로",
P2 영구 바이트 대조를 P4에서 폐기한 선례 -- 승인 `20260930-p4-relocate-test-retire`). 함수별 행의 값(항목 수·DF·담당 Phase)은 목록에서 계산되는 값이고, 계약 3의 도구 규칙이
그 계산과 같은지 대조한다(손으로 옮긴 숫자가 목록과 어긋나면 도구가 잡는다).

**왜 도구 규칙이고 영구 test가 아닌가**: 실제 레지스트리와 실제 목록을 매번 대조하는 영구 contracts test를 두면, 목록(오케스트레이터 경로, N3.12.2 626행)과 레지스트리(code-author 경로,
603행)를 쓰는 주체가 달라 **다음에 목록을 다시 재는 오케스트레이터 문서 커밋이 gate에 들어가는 순간 그 test가 base에서 실패**하고, 그 뒤 모든 card의 base가 기존 test 실패 상태가 된다
(두 파일을 한 커밋에서 바꿀 수 있는 역할이 없다). 같은 역할이 양쪽을 쓰는 P7의 `test_main_on_this_repository_is_clean`(레지스트리 대 엔진, 둘 다 code-author)과 다르다.
그래서 실제 파일 대조는 **도구 실행**(auditor 측정과 Phase DoD 측정)으로 하고, 영구 test는 도구 규칙을 합성 입력으로 판정한다(P7 `20260930-registry-grade-fix`와 같은 구조).

**E0는 그대로다**: 새 규칙은 새 선택 인자 `--df23-inventory <경로>`를 줄 때만 돈다. 인자 없는 호출(= design 20 §10 E0 명령)의 동작·출력은 base와 같다.

**순서**: P10(목록 재측정·`phase`·`measured_at`)의 판정 기록이 gate `master`에 있은 뒤 착수한다(착수 조건). 이 card의 base = P10 판정 기록 커밋 또는 그 후손.
design 20 §8의 P10b 행은 P10 card의 문서 커밋에서 더한다(P10 초안 '결정 필요 항목' 셋째 점) -- 행 문안은 아래 '결정 필요 항목'.

## 관찰 가능한 계약

1. **레지스트리 §8 (code 커밋)**: 레지스트리 끝(§7 뒤)에 절 하나를 더한다. §0~§7은 base와 바이트 동일하다(`git diff base M -- <레지스트리>`가 파일 끝 추가 줄뿐).
   줄 끝은 기존 파일과 같은 CRLF다(실측: 524줄 전부 `\r\n`, 파일 끝 빈 줄 -- 섞으면 diff가 끝 추가만이 아니게 되고 도구의 표 머리 대조가 `\r`에 걸린다. 도구는 줄 끝 `\r`을 떼고 읽는다).
   모양(제목 줄·표 머리는 이 글자 그대로 -- 도구가 읽는다):
   * 제목 `## 8. DF-23 -- 엔진 이름 리터럴 종속 (전수 목록 기록)`.
   * 제목 다음 본문에 두 줄: `목록: \`docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json\``, `measured_at: \`<40자리 소문자 16진>\``.
     그리고 사용 규칙 한 문장: "목록을 다시 재면 이 절을 같은 Phase 안에서 갱신한다(대조: `reg_check.py --df23-inventory`)."
   * `### 8.1 총계` 아래 표 머리 `| 축 | 값 | 항목 수 |`. 행 = 목록 항목 전부에 대한 `role` 값별 개수(`| role | <값> | <n> |`)와 `phase` 값별 개수(`| phase | <값> | <n> |`). 개수 0인 값의 행은 없다.
   * `### 8.2 함수별 (role = 동작을 정함)` 아래 표 머리 `| 함수 | 파일 | 항목 수 | DF | 담당 Phase |`. 행 = `role == "동작을 정함"` 항목을 (`function`, `file`의 마지막 경로 성분)으로 묶은 묶음마다 하나:
     `함수` = 백틱으로 싼 `function` 값 그대로(P10 계약 1 정의 -- `<module>`·`Class`·`Class.method` 포함), `파일` = 파일 이름, `항목 수` = 묶음 크기, `DF` = 묶음 항목 `plan_mapping`에서 정규식 `^DF-\d+`로 뽑은 번호와
     (맞지 않는 항목이 있으면) `신규`를 중복 없이 모아 ", "로 이은 것(순서: DF 번호 오름차순, `신규`는 끝), `담당 Phase` = 묶음 항목 `phase` 값을 중복 없이 계획 N6.1 Phase 순서
     (`3`, `4`, `5`, `6a`, `6b`, `6c`, `7a`, `7b`, `7c`, 끝에 `해당 없음`)로 ", "로 이은 것. 행 순서는 (파일, 함수) 오름차순.
2. **E0 불변**: 병합본에서 `reg_check.py --registry <레지스트리> --root <루트>`(인자 추가 없음)는 exit 0 `reg_check: 발견 0`이고, 기존 `test_reg_check.py` 전부 PASS
   (`_section_lines`가 `## 7.`을 다음 `## ` 줄에서 끊으므로 §8은 E0 규칙 대상이 아니다 -- 실측 5).
3. **도구 규칙 (code 커밋)** -- `reg_check.check_df23(registry_text, inventory, inventory_rel)`이 발견 목록(기존과 같은 `{"rule", "section", "name", "detail"}` 레코드)을 돌려준다.
   `inventory`는 목록 JSON을 읽은 dict, `inventory_rel`은 목록의 저장소 루트 기준 `/` 상대 경로. 모든 기대값은 `inventory["items"]`에서 계산한다(목록의 `totals`를 믿지 않는다). 규칙:
   * `df23-section`: `## 8.`로 시작하고 `DF-23`을 담은 제목 줄이 없다, 또는 그 절에 `목록:`·`measured_at:` 줄이나 `### 8.1`·`### 8.2` 표(계약 1의 표 머리)가 없다.
   * `df23-path`: `목록:` 줄의 백틱 경로 ≠ `inventory_rel`.
   * `df23-measured-at`: `measured_at:` 줄의 백틱 값 ≠ `inventory["measured_at"]`.
   * `df23-total`: §8.1 행 집합 {(축, 값) → 항목 수} ≠ 항목에서 센 값(빠진 행·남는 행·다른 수 모두, 발견 하나에 (축, 값) 하나).
   * `df23-function`: §8.2 행 집합 {(함수, 파일) → (항목 수, DF, 담당 Phase)} ≠ 계약 1 규칙으로 항목에서 만든 값(빠진 행·남는 행·다른 칸 모두, 발견 하나에 (함수, 파일) 하나).
   입력 오류 → `ValueError`: `inventory`에 `measured_at`·`items`가 없다, 항목에 `file`·`function`·`role`·`phase`·`plan_mapping` 중 하나가 없다, `function`이 빈 문자열이다,
   서로 다른 `file` 값이 같은 마지막 경로 성분을 가진다(파일 칸이 모호).
4. **CLI (code 커밋)**: `main(argv)`에 선택 인자 `--df23-inventory <경로>`. 주면 기존 판정 발견에 `check_df23` 발견을 더해 같은 형식으로 출력하고 exit 규칙(0 = 발견 0, 1 = 발견, 2 = 입력 오류 --
   목록 파일 없음·JSON 아님·`ValueError` 포함)은 기존과 같다. `inventory_rel`은 목록 경로를 `--root` 기준 상대로 바꾼 `/` 표기(루트 밖이면 exit 2). 인자를 주지 않으면 출력·exit가 base 도구와 같다.
5. **실제 저장소 대조 (auditor 측정 -- 영구 test가 아니다, 위 '왜 도구 규칙인가')**:
   (a) 병합본 격리 복제본에서 `reg_check.py --registry <iso>/docs/03-analysis/gain-budget-gmid-sizing.function-registry.md --root <iso> --df23-inventory <iso>/docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json` → exit 0, `발견 0`.
   (b) 거부 확인: 같은 명령을 base 레지스트리(§8 없음)와 병합본 도구로 돌리면 `df23-section` 발견, exit 1.
   (c) auditor 독립 재계산: auditor 자신의 스크립트(도구·code-author 산출을 쓰지 않는다)로 목록 `items`에서 §8.1·§8.2 값을 다시 만들어 병합본 레지스트리 §8 표와 같음.
   (d) 보충 뮤테이션: `mutate_changed.py`(V3)는 엔진 소스의 def만 대상으로 잡아 `A/tests/tools/` 변경에는 대상 0이다(P7 판정 기록 V3 `targets []`). P7처럼 auditor 자신의 변이
   스크립트로 `check_df23`의 규칙 분기마다(5규칙·`ValueError` 4조건·CLI `--df23-inventory` 경로) 변이를 넣어 새 test가 죽이는지 재고 `checks.V3.basis`에 적는다(생존 0).
6. **범위**: `git diff base M`의 경로 = 레지스트리, `A/tests/tools/reg_check.py`, `A/tests/contracts/` 새 test 파일 하나. 엔진(`A/*.py`, `workspaces/run_harness.py`)·library·목록 JSON·기존 test는
   바뀌지 않는다(E-LIB·E-INST 자명 동일). 새 코드에 회로·소자·넷·함수 이름 리터럴이 없다(묶음·열 값은 전부 목록 필드에서 온다 -- 일반성).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `reg_check` | `check_df23` | `def check_df23(registry_text: str, inventory: dict, inventory_rel: str) -> list` |

## 판정 유형 근거

red-green: 레지스트리는 gmid-code-author 경로(계획 N3.12.2 603행)이고 도구는 `A/tests/tools/**`(600행, code-author)라 이 card에는 `Role: code` 커밋이 있다 -- code 커밋이 있으면
test-only 모양(`old..new^` 전부 `Role: test`, 병합 없음 -- design 05 §9.2-4 표)이 성립하지 않는다(P2·P7 교훈). equivalence는 새 test가 base에서 통과해야 하는데 base에 `check_df23`이 없다.
base에서 새 test 파일은 **모듈 머리의 `from reg_check import check_df23`**(tools 디렉터리를 `sys.path`에 넣는 방식은 `test_reg_check.py` 44-61행과 같다)가 수집 단계
`ImportError`(`name` = `reg_check`, `name_from` = `check_df23` -- interface card 신규 심볼 쌍 (`reg_check`, `check_df23`)과 같아 red 플러그인 허용 타입, 00-common §8.1)로 실패하고(red),
병합본에서 green. **import를 test 함수 안에 두지 않는다**: 그러면 base에서 CLI test 중 exit 2를 기대하는 것(목록 파일 없음·`ValueError`)이 base 도구의 argparse 인자 거부
(`reg_check.py` 192-194행: `SystemExit`를 잡아 2를 돌려줌 -- 리뷰어 실측)만으로 **통과**해 계획 N4.2 V2 red-green 조건("새 test가 base에서 FAIL")을 어기고 판별력이 없다.
같은 이유로 exit 2 test는 같은 test 안에서 정상 입력의 exit 0 대조를 짝으로 둔다(병합본에서도 인자 거부와 입력 오류를 가른다).
동작 보존(엔진)은 계약 6(범위)이 대신한다 -- 엔진 경로 변경 0.

## oracle 종류와 출처

(a) 구성 입력: 합성 목록(dict)·합성 레지스트리 조각 -- 기대는 계약 1·3의 규칙 문장으로 test가 직접 만든다(도구 출력을 기대값으로 쓰지 않는다). 합성 목록의 함수·파일 이름은
**지어낸 이름**(`alpha_fn`, `mod_a.py` 등)만 쓴다 -- 삭제·이동 이름 스캔 test(`test_d_delete_dead`·`test_d_delete_telescopic`·`test_d_move_tests`)와 IC 표식 대조(`test_ic_markers_match_plan`)에 걸리지 않게.
(d) 실측 원자료: 계약 5의 기대는 card base의 목록 JSON(P10 산출, auditor가 독립 재계산).

## 거부해야 할 입력

규칙마다 합성 조각 → 발견: §8 없음·`measured_at:` 줄 없음(`df23-section`), 경로 다름(`df23-path`), `measured_at` 한 글자 다름(`df23-measured-at`), §8.1에 `phase` 값 행 하나 빠짐·남는 행·수 1 차이
(`df23-total`), §8.2에 묶음 하나 빠짐·목록에 없는 (함수, 파일) 행·`항목 수` 1 차이·`DF` 칸에 `신규` 빠짐·`담당 Phase` 순서가 N6.1 순서가 아님(`df23-function`).
입력 오류 → `ValueError`(CLI exit 2): `function` 빈 문자열, `phase` 없는 항목, `measured_at` 없는 목록, 같은 파일 이름의 다른 경로, 목록 파일 없음.
발견하면 안 되는 것: §0~§7의 표(§8 밖), 목록 `totals`가 틀렸지만 `items`에서 센 값과 §8이 같은 경우(도구는 `items`만 믿는다), `role`이 `메시지뿐`인 항목(§8.2 대상 아님 -- `plan_mapping`이 `DF-31(…)`처럼 DF 번호로 시작해도 마찬가지. P10 계약 2·3: 메시지뿐 항목은 옛 목록의 `plan_mapping`을 그대로 가질 수 있다).
`--df23-inventory` 없이 §8 없는 레지스트리 → 기존 규칙만(발견 0이면 exit 0).

## library 회로 적용 여부

해당 없음(문서·도구). 엔진 불변이라 E-LIB·E-INST는 base와 같다.

## 무동작 판정 입력(무발동 값)

`--df23-inventory`를 주지 않은 `reg_check.py` 호출 전부(E0 명령, `test_main_on_this_repository_is_clean`) -- 출력·exit가 base와 같다. 엔진·library·기존 test 전부.

## 재현할 수치

auditor가 독립으로 센다: 병합본 §8.1 행(role별·phase별 개수), §8.2 행 수와 행마다 (항목 수, DF, 담당 Phase) -- 값은 P10 재측정 목록에서 정해진다(작성자 수를 옮겨 적지 않는다).
비교용 현재 상태(1e2e243 목록, P10 전 -- 계약 수치가 아니다): 동작 항목 266, (함수, 파일) 묶음 46, 그중 `function == ""` 90항목(4파일)·`<module>` 21항목.
P10 준비 후보(cd64170에서 잰 `_drafts/p10_prep/df23_inventory.candidate.json` -- 역시 계약 수치가 아니다, 입력은 P10 card base에서 다시 잰 목록): 동작 항목 213, (함수, 파일) 묶음 52,
빈 `function` 0, 클래스 단위 값은 `SizingContext`(class 본문, 동작 1·메시지 4)·`InfeasibleSizingError`(메시지 1)·`SemiEmpiricalGmIdLUT.__init__`·`SemiEmpiricalGmIdLUT.cgg_absolute`(메시지).

## 결정 필요 항목

없음(사용자 결정 대상 아님). 오케스트레이터 조정 두 가지:
* **P10 초안 보강(반영됨, reconcile 2026-09-30)**: 계약 3이 `function` 빈 문자열을 입력 오류로 본다. 옛 목록은 동작 항목 90개가 `function == ""`(줄기 substring 보충 스캔 항목)라
  이대로면 이 card가 exit 2로 막힌다. P10 계약 1이 `function`을 두 card 공통으로 정의한다 -- 그 줄을 감싼 모듈 최상위 정의 단위(데코레이터 줄 포함): 최상위 `def` → 이름, 최상위 `class`의
  직속 메서드 → `Class.method`, class 본문의 다른 줄 → `Class`, 어디에도 없으면 `<module>`, 중첩 정의는 감싼 단위로 올림. **모든** 항목이 비지 않은 값(레지스트리가 함수를 적는
  `name`·`Class.method` 단위와 같다). 이 card §8.2의 `함수` 칸은 그 값을 그대로 쓴다(빈 값을 '함수 밖'으로 조용히 묶지 않는다 -- 조용한 기본값 금지).
* **design 20 §8 P10b 행 문안(P10 문서 커밋에서 더한다)**: `| P10b | \`df23-registry-record\` | 레지스트리 §8에 DF-23 목록 기록(목록 경로·\`measured_at\`·총계·함수별 행)과
  \`reg_check.py --df23-inventory\` 대조 규칙 | red-green(레지스트리·도구 code 커밋) | (a) 도구 합성 입력, (d) card base 목록 | 레지스트리 기록 |`.
  P10 초안의 '분리한 것' 표 첫 행 처리 칸("test는 목록 총계와 대조 -- base에서 기록 없음으로 red")은 이 card 방식(도구 규칙 + auditor 실제 대조, 영구 실파일 test 없음)으로 고친다.
* Phase 2 DoD 브리핑: E3 판정 기준은 바꾸지 않고, 계획 DF-23 행 '레지스트리 기록'의 증거로 계약 5 (a) 명령을 auditor가 한 번 더 돌려 DoD 기록 N6.3 옆에 적는다(판정 기준 변경 아님).

## 작성 전 실측

(HEAD = gate `master` cd64170, 2026-09-30. 리뷰 중 gate가 B28 병합으로 8790b24가 됐고 레지스트리·`reg_check.py`·목록·test는 cd64170과 같다(`git diff --name-only`, 리뷰어 실측). 저장소 읽기 전용, python `C:\Python314\python.exe -B`, 출력 scratch `C:/g22/out/p10b_measure.txt`. P10 병합 뒤 card base에서 1·5·7을 다시 잰다.)
1. 사실 문장 재측정: `grep -n "^## " <레지스트리>` → §0(7)·§1(21)·§2(31)·§3(61)·§4(271)·§5(397)·§6(447)·§7(483), 524줄, 마지막 절 = §7 `기타 모듈 (1)` 표. `grep -c "DF-23\|df23" <레지스트리>` → 0(기록 없음).
   목록(`python` json 로드): 최상위 키 `scope·method·vocabulary·totals·items`, `measured_at` 없음, `phase` 가진 항목 0/590, 동작 항목 266, (함수, 파일 이름) 묶음 46, `function == ""` 동작 90·전체 414,
   `<module>` 21, 파일 이름 8개 모두 다름(`audit_current_forced`·`design_report`·`run_harness`·`sizing_recipe`·`sky130_lut_sweep`·`stick_diagram`·`topology_library`·`topology_to_markdown`).
   `reg_check.py --registry <레지스트리> --root .` → `reg_check: 발견 0`, exit 0. 계획 933행 DF-23 `수정 Phase` 열 `2(전수 목록·레지스트리 기록), 4(일반 규칙으로 교체)`, 1017행 N6.2 `2`(레지스트리 기록 언급 없음).
2. 이름 충돌: 새 test `A/tests/contracts/test_reg_check_df23.py` -- `ls A/tests/contracts` 에 없음(`test_reg_check.py`만). P10의 `test_df23_inventory.py`와 다름.
   `grep -rn "glob(" A/tests` → `*.py`·`probe_*.py`·`test_probe_*.py`·`*.topology.json`·`*.md`(tools) -- 겹침 없음. DoD `-k` 필터(design 20 218·221행: `dup_w_calc or dup_kcl_edges`, `dup_`, `new_topology`)에 걸리지 않음.
   `*.py` 전수 스캔 test(삭제 이름·IC 표식·print 판정) 대상이므로 합성 이름은 지어낸 이름만(oracle 절).
3. 원칙의 계약화: '목록이 유일한 정본, 레지스트리는 계산된 요약' → 계약 1(값 정의)·3(`items`에서 계산해 대조)·5(c)(auditor 독립 재계산). '이름 종속을 코드에 넣지 않는다' → 계약 6 끝.
   '조용한 기본값 금지' → 계약 3 입력 오류(빈 `function`). '작성자≠검증자' → 계약 5는 auditor 측정.
4. 쓰기 경로(계획 N3.12.2 표): 레지스트리 = gmid-code-author(603행), 도구 = gmid-code-author(600행 `A/tests/tools/**`), 새 test = gmid-test-author(618행, 제외 `tests/tools/**`),
   목록 JSON = 오케스트레이터(626행, 레지스트리 제외 -- 이 card는 목록을 바꾸지 않는다), design §8 행 = 오케스트레이터(624행, P10 문서 커밋), 판정 기록 = auditor(621·622행).
   test-author는 도구 소스를 읽지 않고 interface card(계약 1·3·4 문장과 신규 시그니처)만으로 쓴다.
5. 계획서 소비자·E0 영향: 지우거나 바꾸는 이름 없음. `reg_check.py` 75행 `_section_lines`가 다음 `## ` 줄에서 절을 끊고 105·112행이 `## 7.`·`## 1.`만 읽는다 → §8 추가는 E0 규칙 밖.
   `grep -rn "df23-registry\|P10b\|레지스트리 기록" docs/01-plan docs/02-design` → 계획 933행, design 20 194행(P10 행 '레지스트리 기록') 두 곳뿐 -- 194행은 P10 문서 커밋이 고친다.
6. 미배선: 새 def `check_df23`은 `main`의 `--df23-inventory` 경로에서 불리고, `main`은 이 card의 auditor 측정(계약 5)과 Phase 2 DoD 브리핑(결정 필요 항목 셋째 점)에서 실행된다
   -- P7 `check`/`main`과 같은 DoD 측정 도구 배선. 운영 엔진 경로 밖이 맞는 도구(`A/tests/tools/`)라 V7 면제 승인 대상 아님(P7 V7 PASS 선례, 판정은 auditor).
7. 기존 계약 test: `grep -rln "reg_check" A/tests` → `contracts/test_reg_check.py`(와 도구 자신)뿐. 그 test는 `main(["--registry", …, "--root", …])` 형태만 쓰고(381·424·432행) 모르는 인자 거부를
   판정하지 않는다 -- 새 선택 인자와 충돌 없음, 조정 불필요, V5 없음. `test_main_on_this_repository_is_clean`(444행)은 인자 없는 호출이라 §8 추가 뒤에도 exit 0이어야 한다(계약 2).
