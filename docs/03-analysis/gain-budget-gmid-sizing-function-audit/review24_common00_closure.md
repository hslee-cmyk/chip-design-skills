# review24 -- `00-common` design v1.3 닫힘 검증(review23 M-01~M-11, M-23)

* 대상: `docs/02-design/features/gain-budget-gmid-sizing.00-common.design.md` v1.3(작업 트리, 627줄), 계획서 v5.19(`git diff HEAD -- docs/01-plan`), `.ai/approvals/_TEMPLATE.md`, `.ai/verification/_schema.json`, `workspaces/run_harness.py`, `skills/analog-gmid-design/assets/sizing_recipe.py`
* 기준: review23의 M-01~M-11(S2)과 M-23(숨은 열린 질문)
* 검증자: 독립 검증 agent. 이 설계도, review21~23도 쓰지 않았다. 측정 스크립트는 저장소 밖 scratchpad `review24/`에 있다: `cells.py`(+`cells.txt`, 표 셀 수), `tok.py`(+`tok.txt`, Phase 토큰), `pt/`(pytest 수집 오류 실측). 저장소에서 바꾼 파일은 이 보고서 하나다.
* 심각도: **S1** = 승인을 막는다(틀림·모순·구현 불가) / **S2** = 승인 전에 고친다 / **S3** = 경미

---

## 1. 닫힘 표

| ID | 판정 | 근거(인용) |
|---|---|---|
| M-01 | **닫힘** | 계획 N4.3 공격 15: "`00-common` §8.1 로더 규칙(번호와 무관하게 전부)에 걸리는 상태로". 설계 §14 CC-1: "로더 규칙마다 거부 케이스 1개 이상 + review21·22·23 독립 검증 케이스". |
| M-02 | **닫힘** | `_TEMPLATE.md` 주석: "양식의 정본은 … §8.2다. 머리 규칙, 허용 키, 값 형식, diff 해시 명령은 그 절에만 적는다(여기에 옮겨 적지 않는다)". 옛 명령이 없어졌다. 머리 자리표시자도 §8.2와 같다. |
| M-03 | **닫힘**(S3 잔여 R-08) | §8.1 로더 10: "`basis`가 `도입 <Phase>: <사유>` 형식으로 시작하며 그 `<Phase>`가 `introduced_phase`와 같다". 첫 토큰을 대조하므로 괄호 밖/합집합 문제가 없어졌다. 다만 계획 N4.2는 아직 "`N/A(사유, 도입 Phase)`로 판정 기록에 적는다"이다. |
| M-04 | **닫힘** | 계획 DF-37: "기반 클래스를 잡는 `except InfeasibleSizingError` 핸들러 18곳 … `CANDIDATE_FAILURE_CLASSES`로 바꾼다". 설계 §7.3에도 같은 문장이 있다. raise 지점 분류는 §17에서 `40-defect-fixes`로 넘겼다. |
| M-05 | **닫힘**(S3 잔여 R-10) | 계획 N3.12.4 EL3: "한 경로는 한 분류에만 든다(파일을 명시한 규칙이 glob 규칙보다 우선한다)", "허용 조합표는 N3.12.2 쓰기 경로표에서 생성하고 정본은 `05-role-separation`". 한 경로가 두 분류에 드는 문제는 풀렸다. 남은 것: `tools/gates/merge_gate.py`(`V_CHECKS`·`PHASE_ORDER`를 담은 판정 입력)는 여전히 '도구'이고, EL3 행은 여전히 6셀이다. |
| M-06 | **부분** | §9.4: "실행하는 gate 코드(`plan_phase_tokens` 포함)는 **base 판**, 대조하는 상수와 계획서는 **병합본 판**". 규칙은 생겼다. 그러나 상수가 gate 코드와 **같은 파일**(`merge_gate.py`, §9.1·§9.3)에 있어서, 병합본 상수를 어떻게 읽는지 정하지 않으면 규칙이 성립하지 않는다(R-04). |
| M-07 | **부분** | §8.1에 수집 단계(`pytest_collectreport`), setup 단계, `--rootdir`, `GMID_RED_CAPTURE`, 허용 예외 타입이 들어갔다. 그러나 수집 단계의 "예외 타입"은 실측하면 `_pytest.nodes.Collector.CollectError`다. 허용 집합에 없으므로 CC-3의 ImportError red가 거부된다(R-02). |
| M-08 | **닫힘** | §9.2: "pytest 옵션 `--gmid-phase <Phase>`(… 기본값 없음 -- 없거나 `PHASE_ORDER` 밖이면 수집 오류). V1 전체 실행에서 auditor가 spec card `Phase`를 넘긴다(CC-3 범위)". |
| M-09 | **부분** | §6.3 옮기기 표와 단계 필터가 생겼다. 그러나 `where`/`scope`를 N3.16 '저장 위치'(새 이름이 놓일 곳)에서 만든다. 이 규칙은 §6.2의 `vs` 행(`where="topology"`, `scope="/device_roles/*"`)과 모순된다(R-03). |
| M-10 | **부분** | §10.1: `wrap_evaluate`는 빌더 안에서 반환 직전에 감싸고, `instrument`는 `contextvars.ContextVar` 하나로 전달한다. 이 부분은 닫혔다. 그러나 `wrap_search`의 대상인 "레이아웃 수렴 루프를 뺀 θ 탐색 함수 호출"은 현재 코드에 함수로 존재하지 않는다. 그 함수를 만드는 주체도 계획 쪽에 없다(R-05). |
| M-11 | **부분** | §10 적용 시작("CC-7이 병합된 **다음** … card부터"), §11.1(CC-8 다음부터), §11.4(예외로 끝난 실행은 `FailureRecord` 해시 비교)가 들어갔다. 그러나 새로 넣은 Phase 4 소급 규칙("base = Phase 4 시작 커밋")은 실행할 수 없다(R-01). |
| M-23 | **부분** | §17 표에 넘길 곳이 생겼고(U-38 → `05`, 탐색 진입 함수 → `30-module-split`, raise 지점 → `40`), §16 `diff_path`가 다섯 파일로 늘었다. 그러나 (1) `30-module-split`으로 넘긴 항목이 계획 N9.1 `30` 행에 없다(R-05). (2) §16 "`diff_path`는 … 다섯"과 §8.2 "design 문서의 승인은 … `diff_path`는 그 design 문서다"가 서로 어긋난다(R-07). |

**집계: 닫힘 6(M-01·02·03·04·05·08) / 부분 6(M-06·07·09·10·11·23) / 안 닫힘 0**

---

## 2. 새 결함

### S1

#### R-01 (S1) §11.1 Phase 4 소급 무동작 비교는 base 쪽을 실행할 수 없다
* **위치**: §11.1 "Phase 4 끝에 base = Phase 4 시작 커밋, 병합본 = Phase 4 마지막 병합 커밋으로 §11.4 산출물 비교", §11.5 "§10.2 절차 1~3 … 를 base와 병합본 각각에 적용한다"
* **근거**: Phase 4 시작 커밋은 DF-35·36·37과 CC-8보다 앞이다. 현재 하네스로 확인하면 다음과 같다.
  * `run_harness.py` 35·42~45행은 메인 체크아웃 절대 경로(`sys.path.insert(0, r"C:\…\assets")`, `LUTFILE`)다. §10.2-2 사전 검사("LUT 경로·library 경로가 모두 `<worktree>` 안")에 걸려 exit 8(`tool_measurement_setup`)로 끝난다.
  * `run(circuit_key)`는 `output_dir`·`activations_out` 인자를 받지 않는다(421행). §11.2 호출은 `TypeError`가 난다.
  * `save_instance_json`의 절대 `topology_ref`(DF-36)는 §11.4 경로 누출 검사에서 FAIL이다.
  * `run()`의 `except Exception`(511행)이 예외를 삼키고, `FailureRecord`는 아직 없다. 그래서 §11.4 "양쪽 예외면 레코드 해시 비교"도 할 수 없다.
  * 결과: N6.3의 Phase 4 무동작 증명이 항상 FAIL이 되거나, 구현자가 건너뛰게 된다(WP-02).
* **수정**: base를 "DF-35·DF-36·CC-8이 모두 병합된 첫 커밋"으로 바꾼다. 그 앞 Phase 4 card의 무동작은 판정 대상이 아니라고 명시하거나 equivalence로 대신한다. 또는 base 쪽에 한해 도구가 쓸 대체 진입 절차를 정한다.

### S2

#### R-02 (S2) 수집 단계 red의 예외 타입이 `Collector.CollectError`라 허용 집합에 걸린다
* **위치**: §8.1 "수집 단계 실패 … `pytest_collectreport`의 실패 보고에서 … 예외 타입 = 수집 오류의 예외 타입", 허용 예외 타입 목록, §14 CC-3("red는 ImportError 허용")
* **실측**(pytest 9.0.2, `review24/pt/`): 없는 모듈을 import하는 test 파일과, 있는 모듈에서 없는 심볼을 import하는 test 파일을 수집했다. `pytest_exception_interact`의 `call.excinfo.type`은 두 경우 모두 `_pytest.nodes.Collector.CollectError`였다. 원래 예외는 `__cause__`에만 있었다(`ModuleNotFoundError` / `ImportError`). `CollectReport`에는 예외 타입 필드가 없고(`longrepr` 문자열뿐), 없는 심볼 import는 `AttributeError`가 아니라 `ImportError`로 난다.
* **영향**: 문구대로 구현하면 CC-3의 정당한 ImportError red가 허용 밖 타입으로 거부된다. 구현자가 `__cause__`를 쓰는지, `longrepr`를 파싱하는지, 어느 훅을 쓰는지가 갈리고, 해시도 따라서 갈린다. "신규 심볼 import인 경우에 한해"를 무엇으로 판정할지(`ImportError.name` 대 interface card)도 없다.
* **수정**: "수집 오류는 `pytest_exception_interact`(또는 `pytest_make_collect_report` hookwrapper)에서 `call.excinfo.value.__cause__`의 타입을 쓴다. `__cause__`가 없으면 `CollectError` 그대로 쓰고 허용 밖으로 본다"로 정한다. 신규 심볼 판정은 `exc.name`(모듈 이름)을 interface card의 신규 모듈 목록과 대조한다고 적는다.

#### R-03 (S2) §6.3 '저장 위치 → `where`/`scope`' 규칙이 옛 이름의 실제 위치가 아니라 새 이름의 위치를 준다
* **위치**: §6.3 표 '저장 위치' 행, §6.2 "대체"(`vs` 행 `where="topology"`, `scope="/device_roles/*"`)
* **근거**: N3.16 `vs` 행의 저장 위치는 "sizing_spec derived"다. §6.3을 적용하면 `where="harness_spec"`(7b 전)가 된다. 그런데 옛 이름 `vs`가 실제로 있는 곳은 topology `device_roles`다(`validate_no_legacy_vs_key(device_roles)`, `sizing_recipe.py` 5790). §6.2는 topology로 적었다. test-author는 §6.3대로 harness_spec에 `vs`를 넣는 red를 만들고, code-author는 §6.2대로 topology를 훑는다. 그러면 red가 영원히 FAIL하거나, topology의 옛 키를 잡는 test가 없게 된다. 다른 행도 같다(예: `rail_nets`는 저장 위치 topology이지만 metric 인자에도 있다).
* **수정**: `where`/`scope`는 "옛 이름이 **지금** 나타나는 파일 종류·위치"로 정한다. 옛 이름의 위치를 N3.16 '저장 위치'에서 읽을 수 없는 행은 계획 N3.16에 '옛 이름 위치' 열을 더해 적는다. 그 전까지는 AST·JSON 실측 목록을 spec card에 적는다.

#### R-04 (S2) '상수는 병합본 판'을 읽는 방법이 없다. 상수가 base 판 gate 코드와 같은 파일에 있다
* **위치**: §9.4 '어느 판을 대조하나', §9.1·§9.3(`V_CHECKS`·`PHASE_ORDER`는 `tools/gates/merge_gate.py`), 계획 N4.3 공격 16
* **근거**: base의 `merge_gate.py`가 실행되면서 병합본의 `merge_gate.py` 안 상수를 읽어야 한다. 방법은 두 가지이고 둘 다 정해지지 않았다.
  * 병합본 모듈을 import하는 경우: 병합본 코드가 gate 프로세스 안에서 실행된다. import 시점 코드가 base 모듈의 `plan_phase_tokens`나 로더를 바꿔치기할 수 있다. 그러면 §9.4 "합성 커밋이 자기검사 코드를 고쳐 통과하는 경로는 없다"가 거짓이 된다.
  * AST로 추출하는 경우: `V_CHECKS`가 `VCheck(...)` 호출 매핑이라 `ast.literal_eval`로는 읽히지 않는다. 별도 해석기가 필요하다.
  * 로더 규칙 10이 **판정에** 쓰는 `V_CHECKS`·`PHASE_ORDER`가 base 판인지 병합본 판인지도 정해지지 않았다.
* **수정**: 상수를 데이터 파일(예: `tools/gates/merge_gate_tables.json`, 판정 입력이므로 EL3 '소스')로 분리해 병합본 판을 **파싱만** 한다. 판정에는 base 판 상수를 쓴다고 적는다. 계획 공격 16에 (ii) 케이스(계획과 상수를 함께 맞춘 병합 → 통과)와 이 판 규칙을 적는다.

#### R-05 (S2) `wrap_search`가 감쌀 "θ 탐색 함수"가 없고, 만드는 주체가 계획에 없다
* **위치**: §10.1 "`wrap_search`: θ 탐색 1회 = **레이아웃 수렴 루프를 뺀** θ 탐색 함수 호출(지금 `optimize_full_circuit_budget` 안의 탐색부. 이관 뒤 … `30-module-split` 이관표가 정한다)", §17, 계획 N9.1 `30-module-split` 행, N6.2 Phase 3 "이동 커밋마다 AST 해시 동일"
* **근거**(`sizing_recipe.py`):
  * 탐색부는 식별할 수 있다. 9701~9798행의 `if not thetas / slsqp / slsqp_block_coordinate / grid` 분기이고, 레이아웃(9800행 이후, `_evaluate_row_split`과 재시도 루프 10025~10072행)과 나뉜다.
  * 그러나 grid 분기(9722~9795행)는 인라인 루프라 함수 호출이 아니다. 빌더 호출(9693행)도 탐색부 밖에 있다.
  * 동시성(thread·process pool)은 없으므로 `ContextVar` 전달 자체는 성립한다.
  * 탐색부를 함수로 뽑는 일을 §17은 `30`에 넘겼다. 그러나 N9.1 `30` 행의 '반드시 담을 것'에 없고, Phase 3 이동 커밋은 AST 해시가 같아야 해서 추출 리팩터링이 들어갈 자리가 명시되지 않았다. CC-7 범위에도 추출이 없다.
  * 구현자에 따라 `optimize_full_circuit_budget` 전체를 감싸거나(레이아웃 포함), 분기 네 곳을 각각 감싸거나, 새 함수를 MOD6/MOD8 어느 쪽에 만든다.
* **수정**: "탐색부 추출(빌더 호출은 포함/제외)"을 CC-7 범위 또는 Phase 3 equivalence 커밋 하나로 지정한다. N9.1 `30` 행에 §17 항목을 더한다. 빌더 시간을 `wall_clock_s`에 넣는지도 적는다(R-13).

### S3

* **R-06** diff 해시: 설계 §8.2 명령을 `HEAD~3 HEAD -- plan.md`에 두 번 돌렸다. `-c diff.context=7`을 줬을 때와 안 줬을 때 모두 `62b23409…`로 **같았다**(`diff.interHunkContext=20`, `diff.noprefix`, `diff.mnemonicPrefix`, `diff.algorithm=histogram`, `diff.indentHeuristic=false`도 같음). 그러나 `-c diff.suppressBlankEmpty=true`에서는 `fc363359…`로 바뀌었다. 더 넓은 범위(`HEAD~15`, docs·skills)에서도 바뀐다. `GIT_CONFIG_NOSYSTEM`·`GIT_CONFIG_GLOBAL`은 저장소 로컬·worktree 설정을 끄지 못한다. 명령에 `-c diff.suppressBlankEmpty=false`를 더한다.
* **R-07** §8.2 "design 문서의 승인은 … `diff_path`는 그 design 문서다"와 §16 "`diff_path`는 … 다섯이다"가 어긋난다.
* **R-08** 계획 N4.2 "`N/A(사유, 도입 Phase)`"와 로더 10 "`도입 <Phase>: <사유>`"는 형식이 다르다. N4.2가 기계 형식을 가리키지 않는다. 계획 공격 16에는 설계의 (ii) 케이스와 판 규칙이 없다.
* **R-09** history review23 반영 절 "S1은 세 라운드 연속 0"은 사실이 아니다. review21은 S1 3건(C-01~C-03)이었다.
* **R-10** EL3 행(계획 616행)이 v5.19에서 다시 고쳐졌는데도 `Role: code|test|audit|doc`의 파이프 때문에 6셀(머리 3셀)이다(M-19 권고 미반영). 또 `merge_gate.py`는 판정 입력인데 '도구'로 남아 있다(M-05 잔여).
* **R-11** §7.1 "파이프라인 진입점은 최상위에서 예외를 잡아 `exit_code_for`로 종료한다"와 §10.2-6 "진입점 호출 전체를 잡는다"가 충돌한다. 진입점(MOD10)이 `sys.exit`하면 도구는 `SystemExit`만 받아 `failure_class`를 찾지 못한다. 변환하는 층(하네스 `__main__`인지 MOD10 함수인지)을 정한다.
* **R-12** 토큰 정규식(`6[abc]|7[abc]` 등)은 base 판 코드다. 그래서 Phase를 새로 더하는 개정(정규식 + 계획 + 상수)을 한 병합으로 넣으면 옛 정규식이 새 N6.1 행을 빈 집합으로 읽어 거부된다. 교착은 아니다. "정규식 변경을 먼저 단독 병합, 그다음 계획과 상수"의 두 단계로 풀린다. 이 순서를 §9.4에 적는다.
* **R-13** `wall_clock_s`에는 빌더(9693행)와 레이아웃이 빠진다. 계획 N6.3의 "파일럿 탐색 1회의 **전체** wall-clock"과 문구가 어긋난다. 설계는 "`wall_clock_s`다"라고 단정한다. 계획 문구를 맞추거나 `pipeline_wall_clock_s`와의 관계를 N6.3에 적는다.
* **R-14** §6.3 "JSON 쪽 토큰만 쓴다"는 `MG1(코드), MG0(문서)` 행(`supplies_v`)에서 하나로 정해지지 않는다. 두 쪽 모두 JSON을 건드린다: MG1은 spec 키(`harness_spec`), MG0은 topology 문서 필드(`sky130_supplies_v`).

---

## 3. 지정 점검 (a)~(e)

* **(a) §9.4 판 규칙**: 상수가 `merge_gate.py`에 있어서 규칙대로 실행할 방법이 정해지지 않았다(R-04, S2). 계획 공격 16의 "현 계획서와 일치하는 상수는 통과"는 '현 계획서 = 병합본 판'으로 읽으면 설계와 일치한다. 하지만 계획에는 판 규칙과 (ii) 케이스가 없다(R-08). 계획만 바뀐 병합을 거부하는 것은 교착이 아니다. 상수를 맞추는 card가 들어오면 풀린다. 정규식 변경은 두 단계가 필요하다(R-12).
* **(b) §10.1과 코드 구조**: 탐색부는 9701~9798행으로 식별된다. 레이아웃 루프(9800행~)와도 분리된다. 그러나 함수가 아니고(grid 인라인), 빌더는 밖에 있으며, 추출 주체가 없다(R-05). `ContextVar`는 동시성이 없으므로 성립한다. `wrap_evaluate`를 빌더 안에 두면 운영 호출 지점 6곳(9576·9693·10275·10469·10691·11200)이 모두 덮인다.
* **(c) §11.1 소급 규칙**: 실행할 수 없다(R-01, S1).
* **(d) diff 해시**: `diff.context=7`이 있든 없든 해시가 같다(`62b234091665fcd7…`, 2회 반복 동일). 잔여는 `diff.suppressBlankEmpty`다(R-06).
* **(e) 표 셀 수**(`cells.txt`):
  * 설계 표 16개: 파손 행 0.
  * 계획에서 `git diff HEAD`가 건드린 표 13개(N0.4, N3.10, N3.12.1, N3.12.2, N3.12.4, N3.14, N4.1, N4.3, N5.2, N6.1, N6.2, N7.2, N9.1): 파손 2행. 616행 EL3(6/3, 이번 판에 고친 행, R-10), 985행 U-04(5/4, 기존).
  * history에서 건드린 표 2개: Version History의 4.8·4.11·4.13·4.36 행이 파손돼 있다(기존 행, 이번 diff 밖).
  * 참고: N4.1·N4.2·N6.1 토큰(`tok.txt`)은 설계 §9.4-3 주장과 일치한다(IC7 괄호 안 {6c}만, N6.1 빈 집합 행은 `0`·`0(문서)` 둘).

---

## 4. 집계와 판정

| 구분 | 건수 | ID |
|---|---|---|
| 닫힘 | 6 | M-01, M-02, M-03, M-04, M-05, M-08 |
| 부분 | 6 | M-06, M-07, M-09, M-10, M-11, M-23 |
| 안 닫힘 | 0 | -- |
| 새 S1 | 1 | R-01 |
| 새 S2 | 4 | R-02, R-03, R-04, R-05 |
| 새 S3 | 9 | R-06 ~ R-14 |

**판정: 수정 후 승인.** R-01은 소급 비교의 base를 바꾸면 닫힌다. R-02~R-05도 모두 한 곳 규정이나 계획 한 줄로 닫힌다. 재작성은 필요 없다.
