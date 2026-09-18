# review23 -- `00-common` design v1.2 세 번째 독립 검증

* 대상: `docs/02-design/features/gain-budget-gmid-sizing.00-common.design.md` v1.2(작업 트리, 577줄), `.ai/verification/_schema.json`, `.ai/approvals/_TEMPLATE.md`, `.ai/approvals/20260918-u38-jsonschema.md`
* 기준: 계획서 v5.19(작업 트리, `git diff HEAD -- docs/01-plan`), history 머리 절 '`00-common` 구성안 C와 v5.19 계획 보완'과 Version History 5.19 행, review21(C-01~C-24), review22(닫힘 표 + N-01~N-24), 함수 레지스트리, `workspaces/run_harness.py`, `skills/analog-gmid-design/assets/*.py`
* 검증자: 독립 검증 agent. 이 설계도 review21·review22도 쓰지 않았다. 작성자 스크립트(`common00_schema_reject_check.py`/`.txt`)는 참고만 했고 증거로 쓰지 않았다.
* 내 측정 스크립트는 저장소 밖 scratchpad에 있다: `review23/schema23.py`(+`.txt`), `review23/exc23.py`(+`.txt`), `tok3.py`(+`.txt`), `ast_json.py`(+`.txt`), `specscan.py`(+`.txt`). 저장소에서 바꾼 파일은 이 보고서 하나다.
* 심각도: **S1** = 승인을 막는다(틀림·모순·구현 불가) / **S2** = 승인 전에 고친다(구현자 둘이 다르게 가거나 한쪽 읽기가 게이트를 망가뜨린다) / **S3** = 경미

---

## 1. 닫힘 표

### 1.1 review22에서 부분이던 C 항목

| ID | 판정 | 근거 |
|---|---|---|
| C-07 | **닫힘** | `git diff HEAD`로 확인했다. N9.1 `00-common` 행이 "용어→코드 이름 대응(N0.4와 합쳐 용어집 최종본)", "V 도입 표·IC 담당 표의 형식과 계획서 일치 test 명세"로 바뀌었다. N6.1 `0(문서)` 행은 5셀로 돌아왔다(`tok3.py` 셀 수 검사: N6.1 파손 행 0). N6.2 `0(문서)`도 C안 문구다. |
| C-09 | **닫힘** | 정규 이름은 `f"{__module__}.{__qualname__}"`, 추출은 `pytest_runtest_makereport`의 `call.excinfo.type`, 함수는 `merge_gate.py` 하나다(§8.1). 소비자는 merge gate의 V2 재실행이다. 단, 수집 단계 ImportError 등 이 훅으로 잡히지 않는 red가 남았다. 이것은 새 결함 M-07로 다룬다. |
| C-12 | **닫힘** | `spec_fingerprint`(등급 R2)는 쓰지 않고 도구 자체 `spec_digest`를 정의했다. 레지스트리 408행이 R2 절이라는 것도 확인했다. 실행 단위는 동작 변경 card마다이고, 예산 게이트는 first-parent 최신 `perf.json`을 읽는다. `eval_count` 정의도 고쳤다. 남은 모호성은 M-22로 다룬다. |
| C-14 | **닫힘** | `JSON_KINDS` 7종, `stage`에 MG0, 깊은 복사 관용구 처리, TS1 뒤 재계수가 들어갔다. 적힌 AST 개수는 내 재측정과 일치한다(§4). N3.16 행을 `LegacyName`으로 옮기는 규칙이 비어 있는 것은 새 결함 M-09로 다룬다. |
| C-20 | **닫힘** | §3.3·§14의 소유 칸이 모두 §3.2 허용 값이고, 두 칸이 같은 행은 없다(§3 표). 양식 자체의 머리 불일치는 M-16으로 다룬다. |
| C-22 | **부분** | N9.1 `00-common` '읽을 plan 절'에 N0.1·N3.10·N3.11·N3.12 전체·N3.16·N4.3·N6.1·N6.2가 들어갔다. 그러나 설계가 쓰는 **N5.2**(DF-35·36·37을 §7.1·§7.3·§10에서 인용), N1.4(NFR-4, §11.4), N2.1(DEC-34·47·51)은 여전히 없다. `40-defect-fixes` 행에도 CC-7이 구현할 N6.3과 MOD10 인자의 근거 N3.10이 없다(M-17). |
| C-24 | **닫힘** | N0.4 oracle (a)에 '구성으로 정답이 정해진 합성 입력'이 들어갔다. N3.12.3의 oracle 선택 기준 문장은 고치지 않았다(M-18, S3). |

**C 집계: 닫힘 6 / 부분 1(C-22) / 안 닫힘 0**

### 1.2 review22 N-01~N-24

| ID | 판정 | 근거 |
|---|---|---|
| N-01 (S2) | **닫힘** | N6.1 행 복구(5셀), N9.1 행 개정, §9.4에 "셀 수 ≠ 머리 셀 수이면 FAIL"을 넣었다. 세 대상 표(N4.1·N4.2·N6.1)의 파손 행은 0이다(§6). |
| N-02 (S2) | **닫힘** | 로더 3이 "모든 수를 재귀로 훑어 `math.isfinite`"로 바뀌었고 §6.2와 같다. 다만 문구대로 구현하면 401자리 정수에서 거부가 아니라 `OverflowError`가 난다(M-12, S3). |
| N-03 (S2) | **닫힘** | auditor 경로가 `.ai/verification/<id>.json`, `<id>/**`(`_schema.json` 제외)로 좁혀졌다. §8.1에 "base 스키마로 검증" 규칙이 들어갔다. |
| N-04 (S2) | **닫힘** | §10 `spec_digest`는 자체 정의이고 `spec_fingerprint`는 R2라 쓰지 않는다고 적었다. 레지스트리와 일치한다. |
| N-05 (S2) | **닫힘** | `JSON_KINDS`가 실제 종류를 덮는다(topology·derived_bounds·instance·regression_baseline 등). AST 개수 7/3·11/1·1·2는 내 재측정과 같다. 깊은 복사는 `copy.deepcopy`로 바꾼다. |
| N-06 (S2) | **부분** | 패치를 버리고 `instrument` 인터페이스를 정했다. 그러나 무엇을 감싸는지가 현 코드 구조에서 하나로 정해지지 않는다. 평가 커널 빌더 호출 지점이 6개이고, `optimize_full_circuit_budget`이 레지스트리 기준으로는 MOD6·MOD8로 갈린다(M-10). |
| N-07 (S2) | **부분** | 정규 이름·훅·함수 하나는 정했다. 그러나 N3.12.3이 허용하는 "신규 함수의 ImportError red"(CC-3이 명시)는 대개 수집 단계 오류라 `call.when == "call"` 훅이 보지 못한다. node id 기준 경로와 플러그인 출력 경로도 없다(M-07). |
| N-08 (S2) | **닫힘** | 모든 동작 변경 card에서 측정하고, 게이트는 first-parent 최신을 읽는다. 다만 Phase 4 앞쪽 card에서는 도구가 아직 없다(M-11). |
| N-09 (S2) | **닫힘** | 정규식 뒤쪽을 "공백·문장부호·끝"으로 좁혔다. 설계 문장만으로 구현해 보니 IC11 괄호 안은 {}, V1 괄호 안도 {}였다(§6). `sub`·`part`·`from_phase` → xfail 대응을 §9.2에 적었다. |
| N-10 (S3) | **닫힘** | §14를 "작업 묶음"으로 부르고, 발행 문서가 N3.12.3 단위로 나눈다고 적었다. |
| N-11 (S3) | **닫힘** | DF-37 개수가 AST 기준이다. 내 재측정도 같다(`exc23.txt`: sizing_recipe ValueError 52 / Exception 7, stick 23/1, harness 1/2, topology_library·audit_current_forced·topology_to_markdown Exception 각 1). §7.3은 DF-37을 인용만 한다. |
| N-12 (S3) | **닫힘** | `eval_count`를 "평가 함수 호출 수(캐시 미스·실패 재평가 포함)"로 정의했다. |
| N-13 (S3) | **닫힘** | `pythonhashseed`는 자식에 준 값(1)이다. |
| N-14 (S3) | **닫힘** | 중복 키(`object_pairs_hook`), BOM, RFC 3339 정규식, `Z*`/`Cc`/`Cf` basis 검사, `approvals` 날짜, 소문자 표기가 모두 들어갔다. 새 잔여 구멍은 M-12·M-13에서 다룬다. |
| N-15 (S3) | **부분** | 옵션 고정과 머리 값 형식이 들어갔다. 그러나 두 가지가 남았다. (1) `diff.context`·`diff.interHunkContext` 설정이 해시를 바꾼다(실측, M-15). (2) `_TEMPLATE.md`에 적힌 명령이 설계 §8.2와 다른 옛 명령이다(M-02). |
| N-16 (S3) | **닫힘** | '공격 8'이 '공격 15'로 바뀌었다. 소유 칸도 허용 값이다. |
| N-17 (S3) | **닫힘** | N4.1 IC5 이름 집합에 `reject_*`·`require_*`·`load_*_checked`를 더했다. |
| N-18 (S3) | **닫힘** | raise 위치 규칙(MOD4 이상, MOD3은 status 반환)과 합성 raise → exit code red가 들어갔다. 기반 클래스를 **잡는** 지점 18곳은 새 결함 M-04로 다룬다. |
| N-19 (S3) | **닫힘** | 도구 exit code 표(0 / N3.14 값 / 8 / 9 / 10)와 `tool_*` 실패 분류가 들어갔다. |
| N-20 (S3) | **부분** | EL3 분류에 판정 입력 파일 셋을 넣었다. 그런데 기존 glob과 겹쳐 5분류가 분할이 아니게 됐다(M-05). |
| N-21 (S3) | **부분** | 반대 방향 검사(`from_phase` 동치, N6.1 원소 정확히 하나, `exc` 이름)와 exit code 파싱을 넣었다. 그러나 로더 10의 "basis를 토큰화했을 때 도입 Phase 토큰이 있다"가 괄호 밖 집합인지 합집합인지 정해지지 않았다. N4.2가 정한 양식이 괄호 안에 도입 Phase를 적는 형태라 결과가 갈린다(M-03). |
| N-22 (S3) | **닫힘** | N3.12.3 판정 유형에 `test-only`가 들어갔고, 오케스트레이터 경로에 `_schema.json`(부트스트랩 ①)을 넣었으며, U-38이 review21·22를 인용한다. 같은 판에서 새로 생긴 N6.1 U-38 누락은 M-18에서 다룬다. |
| N-23 (S3) | **닫힘** | "대조가 끝난 뒤 `--out`에 쓴다", `--out`은 worktree 밖이어야 한다는 규칙이 들어갔다. |
| N-24 (S3) | **닫힘** | IC7은 발동 계수 부분만 쓴다. WP-13 긴장과 빈 ID 목록 FAIL을 명시했고, 비교는 시드 1이다. |

**N 집계: 닫힘 19 / 부분 5(N-06, N-07, N-15, N-20, N-21) / 안 닫힘 0**

---

## 2. 새 결함

### S2

#### M-01 (S2) 공격 15의 범위가 "로더 추가 검사 §8.1 1~6"으로 남아, 로더 규칙 7~10의 거부 증명이 계획서 밖이 됐다
* **위치**: 계획 N4.3 공격 15 행("로더 추가 검사(`00-common` §8.1 1~6)"), 설계 §8.1 로더 규칙 1~10, §14 CC-1("§8.1 로더 규칙 1~10")
* **근거**: v1.2의 로더 규칙은 10개다. 번호도 다시 매겨졌다. 옛 2(날짜)가 지금 6이고, 옛 4(길이)가 지금 7이다. 계획 N4.3이 "1~6"을 그대로 두어 정본인 계획이 7(길이 일치), 8(RFC 3339), 9(보이지 않는 근거), 10(N/A 도입 Phase)을 공격 15 범위에서 뺐다. N6.2 0.5 DoD는 공격 15의 거부 로그를 요구하므로, 이 넷은 0.5에서 "실제로 거부한다"를 보일 의무가 없다(WP-02). 작성자 스크립트도 옛 번호("로더 3" = NaN, "로더 2" = 날짜, "로더 4" = 길이)를 쓴다.
* **수정**: N4.3 공격 15를 "`00-common` §8.1 로더 규칙 전부"로 바꾼다(번호를 적지 않는다). CC-1 케이스 목록에 규칙 7~10의 거부 케이스를 명시한다.

#### M-02 (S2) `_TEMPLATE.md`에 적힌 diff 해시 명령과 형식이 설계 §8.2와 다르다(정본 둘)
* **위치**: `.ai/approvals/_TEMPLATE.md` 주석("target = `git diff --no-color --no-ext-diff --full-index --binary …`", 자리표시자 "64자리 16진", "40자리 16진"), 설계 §8.2(고정 옵션 명령, "소문자 16진")
* **근거**: 설계 §8.2는 N-15를 반영해 `-c core.quotepath=true -c core.autocrlf=false … --no-textconv --no-renames --diff-algorithm=myers --src-prefix=a/ --dst-prefix=b/`를 정했다. 양식은 옛 명령을 그대로 안내한다. 오케스트레이터는 승인 기록을 쓸 때 양식을 복사한다. 이 저장소에는 `diff.astextplain.textconv`와 `autocrlf=true`가 설정돼 있고 한글 경로도 있다. 양식 명령으로 만든 `target`은 V5가 설계 명령으로 다시 계산한 값과 다를 수 있다. 그러면 올바른 승인이 거부되거나, V5 구현자가 양식 주석을 정본으로 읽는다. 양식은 §3.3에서 부류 `코드`(V5 판정 입력)인데 설계와 어긋난 채 "지금 만드는 파일"로 남아 있다.
* **수정**: 양식 주석의 명령과 형식을 §8.2와 같게 고치거나, 명령을 지우고 "§8.2 명령"만 가리킨다. §15 DoD의 `test -f`에 "양식 머리와 주석이 §8.2와 일치"를 더한다.

#### M-03 (S2) 로더 10 "basis를 토큰화했을 때 도입 Phase 토큰이 있다"가 어느 집합인지 없다. N4.2 양식과 부딪친다
* **위치**: 설계 §8.1 로더 규칙 10, §9.4 `plan_phase_tokens`(괄호 밖/안 두 집합 반환), 계획 N4.2 머리("`N/A(사유, 도입 Phase)`로 판정 기록에 적는다")
* **근거**(`schema23.py`, 설계 문구대로 구현, spec card Phase = 4, V9 도입 6b):
  * C10: basis `N/A(Phase 4 변경, 도입 6b)`(N4.2 양식 그대로). 괄호 밖 집합으로 판정하면 **거부**된다. §9.4의 다른 대조가 모두 괄호 밖 집합을 쓰므로 이 읽기가 자연스럽다.
  * C11: 같은 기록을 합집합으로 판정하면 통과한다. 구현에 따라 N4.2가 정한 양식이 전부 거부되거나 전부 통과한다. Phase 1~6a에서 N/A가 붙는 모든 병합이 이 판정을 지난다.
  * C12: `도입 Phase는 6b부터`는 뜻이 맞지만 거부된다(뒤가 한글이라 토큰이 아니다).
  * C13: `도입 6c 전이다. 6b`는 도입을 틀리게 적었는데 통과한다(토큰 존재만 본다).
* **수정**: basis 형식을 기계 형식으로 정한다. 예: "`N/A` 판정의 basis는 `도입 <Phase>:`로 시작한다"(첫 토큰을 대조). 아니면 "괄호 안팎 합집합에 도입 Phase가 있고, 다른 Phase 토큰은 없다"로 정한다. N4.2 양식 문구와 같은 형태로 적는다.

#### M-04 (S2) 탐색 루프가 기반 클래스 `InfeasibleSizingError`를 잡는 곳이 18개인데, DF-37·CC-4 어느 범위에도 없다
* **위치**: 계획 N3.14 v5.19 문장("탐색 루프는 … 기반 클래스 `InfeasibleSizingError`를 잡지 않는다"), DF-37(대상 = `except …ValueError…`·`except Exception`), 설계 §7.3("개수와 범위는 DF-37"), §14 CC-4
* **근거**(`exc23.py` AST): `sizing_recipe.py`의 `except InfeasibleSizingError` 핸들러는 18개이고 모두 운영 코드다(`__main__` 0). 위치는 `_feed_metric_stage_budget` 6717, `check` 7294, `_hr_resolve_vertical_group` 8113, `_evaluate` 9274, `optimize_full_circuit_budget` 9768(grid 루프), `derive_theta_dependency_graph` 10356·10368·10373, `extract_linear_feasibility_constraints` 10481, `search_stage_budget_L_warm_start` 10904, `_probe` 11025, `presolve_warm_start` 11305·11319, `_objective_fn` 11508, `_fn` 11518, `_optimize_theta_slsqp` 11574·11610, `_callback` 11596이다. DF-37은 이름이 `ValueError`·`Exception`인 핸들러만 세므로 이 18곳이 빠진다. Phase 4에 `StructureUnresolvedError`·`InfeasibleTargetError`·`SearchFailedError`가 기반 클래스의 하위로 생기면, 이 핸들러들이 '탐색 시작 전 정지'여야 할 클래스를 후보 실패로 삼킨다. §7.1의 `CANDIDATE_FAILURE_CLASSES`는 소비자가 이 지점들인데, 교체할 주체가 정해져 있지 않다(WP-01).
* **수정**: DF-37 대상에 "`except InfeasibleSizingError`(기반 클래스) 핸들러 → `except CANDIDATE_FAILURE_CLASSES`로 교체"를 더한다(AST 계수는 CC-4 card). 설계 §7.3에 한 줄로 인용하고, CC-4 내용에 넣는다.

#### M-05 (S2) v5.19 EL3 경로 분류가 분할이 아니다(한 경로가 두 분류)
* **위치**: 계획 N3.12.4 EL3("소스(…, 그리고 판정 입력이 되는 `workspaces/run_harness.py`·`.ai/verification/_schema.json`·`assets/tests/tools/ic_table.py`) / … / 도구(`assets/tests/tools/**`, `tools/**`) / … / 문서(`docs/**`, `.ai/**`)")
* **근거**: `ic_table.py`는 소스이면서 도구(`assets/tests/tools/**`)다. `_schema.json`은 소스이면서 문서(`.ai/**`)다. 우선순위 규칙이 없다. 허용 조합표(`Role:` × 분류)는 분류가 함수라는 전제로 만든다. 예를 들어 `_schema.json`을 바꾸는 `Role: doc` 커밋은 문서로 읽으면 통과하고 소스로 읽으면 차단된다. 또 v5.19가 세운 기준("판정 입력이 되는 파일은 소스")대로라면 `V_CHECKS`·`PHASE_ORDER`를 담은 `tools/gates/merge_gate.py`도 소스여야 하는데 도구로 남아 있다. 기준이 일관되지 않다.
* **수정**: "명시한 파일 > glob" 우선순위를 적거나, 판정 입력 파일을 별도 분류(6번째)로 둔다. `05-role-separation` 허용 조합표가 이 규칙에서 생성된다고 적는다.

#### M-06 (S2) merge gate 자기검사(공격 16)가 어느 판의 gate 코드·상수·계획서를 대조하는지 없다. 읽기에 따라 교착되거나 공격이 무의미해진다
* **위치**: 설계 §9.4 '어디서 도는가'("merge gate가 시작할 때 자기검사 … 불일치면 판정하지 않고 거부"), 계획 N4.3 공격 16
* **근거**: 두 읽기 모두 문제가 있다.
  * (가) base의 gate 코드·상수·계획서를 쓰는 경우: 오케스트레이터가 N4.2 `도입`이나 N6.1을 고치는 계획 개정을 base에 커밋하면, 그 뒤 모든 병합이 "판정하지 않고 거부"된다. `V_CHECKS`를 고칠 게이트 변경 card(code-author, N3.12.2)의 병합도 같은 gate에서 거부되므로 교착에 빠진다. 계획서는 판이 자주 바뀐다(v5.10~v5.19).
  * (나) 병합본(branch) 쪽을 쓰는 경우: 공격 16의 합성 커밋은 거부되지만, 같은 커밋이 자기검사 코드나 계획서를 함께 고치면 통과한다. 이때 공격 16이 증명하는 것이 없다.
* **수정**: 명시한다. 예: "gate 코드는 base 판, 대조하는 상수와 계획서는 병합본 판. 계획서 N4.1·N4.2·N6.1을 바꾸는 오케스트레이터 커밋과 상수를 바꾸는 게이트 변경 card는 같은 병합 단위로 들어온다." 공격 16에는 (가)의 교착 시나리오(계획만 바뀐 base)도 오거부 0 쪽 케이스로 넣는다.

#### M-07 (S2) red 해시의 입력을 N3.12.3이 허용하는 red 전부에서 만들 수 없다(수집 단계 ImportError·setup 실패·node id 기준)
* **위치**: 설계 §8.1 해시 정의("`call.when == "call"`이고 `call.excinfo`가 있을 때의 `call.excinfo.type`"), §14 CC-3("red는 ImportError 허용"), 계획 N3.12.3 순서 3("ImportError만의 실패는 신규 함수일 때만 인정")
* **근거**:
  * 신규 모듈·함수를 test 파일 머리에서 import하면 ImportError는 **수집 단계**에서 난다. 이때 test 함수 node가 생기지 않아 `pytest_runtest_makereport`가 불리지 않는다. `red.test_ids`에 넣을 id도 없고 해시도 없다. CC-3(`IC_TABLE` 신규 모듈)이 바로 이 경우다.
  * fixture 오류는 `when == "setup"`이라 해시가 없다.
  * `test_ids`가 pytest node id라면 rootdir(`assets/`에서 실행하느냐 저장소 루트에서 실행하느냐)에 따라 문자열이 달라진다. 실행 위치를 정하지 않았다.
  * auditor가 기록할 때 플러그인이 (id, 타입)을 어디로 내보내는지(파일·환경변수)도 없다.
  * 해시는 예외 타입만 보므로 N3.12.3의 "assertion 실패여야 한다(ImportError는 신규 함수만)"를 merge gate가 강제하지 못한다.
* **수정**: 수집 오류는 `pytest_collectreport`의 모듈 node id와 예외 타입으로 해시한다(또는 "신규 심볼 import는 test 함수 안에서"를 test 규칙으로 둔다). setup 단계 포함 여부를 정하고, 실행 cwd·rootdir(`-c`/`--rootdir`)과 플러그인 출력 경로를 고정한다. 허용 예외 타입 집합(`builtins.AssertionError`, `_pytest.outcomes.Failed`, 신규 함수의 `builtins.ImportError`/`ModuleNotFoundError`)을 merge gate 규칙으로 둔다.

#### M-08 (S2) TS7 xfail 만료의 입력 "현재 Phase(spec card `Phase`)"를 pytest 실행이 얻는 경로가 없다
* **위치**: 설계 §9.2 xfail 대응("현재 Phase(spec card `Phase`)가 `phase` 이상이면 xfail을 두지 않는다")
* **근거**: xfail 생성은 test 실행 시점(conftest)에 일어난다. 그런데 pytest는 어느 spec card의 병합본인지 모른다. V1(auditor, audit worktree), 개발 중 로컬 실행, TS2 셔플 실행이 같은 test를 서로 다른 '현재 Phase'로 볼 수 있다. 입력 경로(환경변수, 저장소 안 파일, spec card 경로 인자)를 구현자마다 달리 정하게 된다. 만료가 판정 입력(N3.12.3 "만료되면 FAIL")이므로 결과가 갈린다.
* **수정**: 예: "`pytest --gmid-phase <Phase>` 옵션. 없으면 수집 오류(기본값 없음). V1은 spec card `Phase`를 넘긴다"를 §9.2에 적고 CC-3 범위에 넣는다.

#### M-09 (S2) N3.16 → `LEGACY_NAMES`(및 test-author 기대 목록) 옮기기 규칙이 없다
* **위치**: 설계 §6.1 `LegacyName`(`stage: "MG0"|"MG1"|"MG2"|"MG3"(N3.16 '단계' 열)`, `where`, `scope`), §6.3("기대 목록은 test-author가 계획서 N3.16에서 직접 옮긴다"), §6.1("표에 행이 있다 = 그 이름 변경이 끝났다")
* **근거**:
  * N3.16 '단계' 열에는 네 값 밖의 값이 있다: `--`, `MG1(코드), MG0(문서)`, `7a(metric 통일)·MG3`, `7a`, `7b`, `MG0(문서)·MG3`, `MG0(컨테이너 이름)·MG3`, `Phase 4(선언), 이름은 U-32`.
  * '흡수되는 옛 이름' 열에는 JSON 이름이 아닌 것이 있다. 코드 식별자(`_DEFAULT_RAIL_HI/LO`, `_RAIL_NETS`), 서술("spec_fn 4개 복사본", "계획 문구 '격자 분해능'이 대신하던 자리, 문헌값 인용")이 그렇다. `_paper_target_spec`은 같은 행에서 정본 이름이면서 옛 이름이다.
  * '저장 위치' 열("전체", "S2", "metric 선언", "human")을 `where`(JSON_KINDS)·`scope`(JSON pointer)로 바꾸는 규칙이 없다. `scope` 세그먼트 `*`가 리스트 원소(`netlist[]`)도 뜻하는지도 없다.
  * "행이 있다 = 끝났다"이므로 CC-5 시점의 기대 목록은 "MG0 `vs` + MG1 행"뿐이어야 한다. 그런데 §6.3에는 단계 필터가 없다. test-author는 N3.16 전체를 옮기고 red가 영원히 FAIL하거나, 아니면 임의로 고른다.
* **수정**: §6.3에 옮기기 규칙을 표로 둔다(단계 열 → `stage`, 저장 위치 → `where`/`scope`, 코드 식별자 행 제외 = AST lint 대상, 서술 행 제외). 기대 목록은 "spec card Phase까지 끝난 단계의 행"으로 한정한다. N3.16의 `_paper_target_spec` 이중 역할은 계획 개정으로 푼다(흡수 대상을 '5회로의 사용자 확정 스펙을 담던 `_paper_target_spec` 컨테이너'로 한정).

#### M-10 (S2) 계측 인터페이스가 감싸는 지점이 하나로 정해지지 않는다
* **위치**: 설계 §10 절차 1("엔진은 최상위 탐색 호출과 평가 커널 빌더가 돌려준 평가 함수를 이 둘로 감싼다"), 절차 6(`eval_count`에 "캐시를 거치지 않는 경로의 호출도 포함"), §13 계측 인터페이스 행
* **근거**(AST, `sizing_recipe.py` 운영 코드):
  * `_build_theta_evaluator`를 부르는 함수는 6개다: `diagnose_sizing_roles_gap` 9576, `optimize_full_circuit_budget` 9693, `derive_theta_dependency_graph` 10275, `extract_linear_feasibility_constraints` 10469, `search_stage_budget_L_warm_start` 10691, `presolve_warm_start` 11200(`ev or _build_theta_evaluator(...)` 재빌드).
  * `instrument`는 MOD10 인자인데, 이것이 MOD8 → MOD6의 각 빌더 호출까지 어떻게 닿는지(인자 전파인지 문맥 변수인지)와 어느 호출까지 감싸는지가 없다. 최상위 빌더 하나만 감싸면 재빌드 경로의 평가가 빠지고, 절차 6의 정의와 어긋난다.
  * "최상위 탐색 호출"도 모호하다. 레지스트리는 `optimize_full_circuit_budget`의 목적지를 `sizing_layout_convergence`(MOD8, 레이아웃·row_split)로 적는데, N3.10은 MOD6에 "탐색부"를 둔다. wall-clock이 레이아웃 수렴 루프를 포함하는지 구현자마다 달라진다. N6.3 "파일럿 탐색 1회의 전체 wall-clock"도 이것을 가르지 못한다.
* **수정**: (1) `wrap_search`는 MOD6 탐색 진입 함수(이름은 `30-module-split` 이관표) 한 곳이고 레이아웃 수렴은 포함한다/안 한다를 적는다. (2) `wrap_evaluate`는 MOD6의 평가 커널 빌더 **안**(반환 직전)에서 적용해 모든 호출 지점이 자동으로 감싸지게 하고, `instrument`를 빌더까지 전달하는 방법을 하나로 정한다. (3) 레지스트리·N3.10의 목적지 불일치를 30 design 착수 조건으로 넘긴다고 명시한다.

#### M-11 (S2) "Phase 4부터 동작 변경 spec card마다" 측정·무동작 증명을 요구하는데, 도구는 Phase 4 중간에 생긴다
* **위치**: 설계 §10 실행 단위("Phase 4부터 동작 변경 spec card마다"), §11.1("동작 변경 Phase(4 이후)의 spec card마다 적용한다(N6.3)"), §18.1 순서(DF-35·36 → CC-4·5·7·8), 계획 N3.11 TS4 "4(첫 작업)"
* **근거**: TS4와 Phase 4 앞쪽 DF card, 그리고 DF-35·DF-36·CC-7·CC-8 card 자신은 도구나 `activations_out`이 병합되기 전이다. 그래서 이 card들은 §10·§11을 지킬 수 없다. 구현자는 건너뛰거나(WP-02 위반) 병합을 막는다(Phase 4 교착). 또 N6.3 원문은 "필요 없는 회로의 무동작을 증명한다"(Phase 단위)인데, 설계가 card 단위로 강화하면서 시작점을 정하지 않았다. 여기에 더해, base·병합본 실행이 예외로 끝날 때(I-C11 해소 전 회로, SEARCH_FAILED) 무동작 판정이 무엇인지도 없다. 산출물이 없으면 해시가 같아 PASS인지, FAIL인지, 예외 분류 비교인지가 갈린다.
* **수정**: "적용 시작 = CC-7(성능)·CC-8(무동작) 병합 뒤 card. 그 전 Phase 4 card의 무동작 증명은 CC-8 병합 직후 base = Phase 4 시작 커밋으로 일괄 수행"처럼 정한다. 예외 종료는 "양쪽이 같은 N3.14 분류로 끝나면 분류 비교, 아니면 FAIL"처럼 판정식에 넣는다(§12).

### S3

#### M-12 (S3) 로더 규칙 문구대로 구현했을 때 남는 구멍(새 케이스)
* **근거**(`schema23.txt`, jsonschema 4.26.0 `Draft202012Validator` + `FormatChecker`, 로더 1~10은 설계 문구대로 따로 구현):
  * C1: `test_ids`에 C1 제어문자 U+0085가 있으면 스키마와 로더 모두 통과한다. §8.1 표는 "제어 문자 없는"인데 스키마 패턴은 C0·DEL만 막는다.
  * C2: `test_ids`에 짝 없는 서로게이트(`"\ud800"`)가 있으면 스키마와 로더 모두 통과하고, 그 뒤 `red_failure_hash`가 `UnicodeEncodeError`로 죽는다(거부 메시지가 아니다).
  * C3: `value`가 401자리 정수 리터럴이면 로더 3의 `math.isfinite`에서 `OverflowError`가 난다. 거부가 아니라 예외다(`float("1e400")`과 다른 경로).
  * C4: `equivalence.commands = ["\u200b"]`는 통과한다. merge gate가 재실행할 명령이 사실상 비어 있다.
  * C5: basis가 U+3164(한글 채움 문자, 범주 Lo)뿐이면 규칙 9를 통과한다(보이지 않는 근거).
  * C15: `test_ids = [" "]`도 통과한다.
  * C16: UTF-16LE BOM 파일(Windows PowerShell 5.1 `Out-File`의 기본 인코딩)은 규칙 1(UTF-8 BOM만 명시)에 걸리지 않는다. `UnicodeDecodeError`로 끝나 BOM 명시 메시지가 나오지 않는다.
  * C17: spec card `Phase`가 `PHASE_ORDER` 밖(`0(문서)` 등)일 때의 처리가 없다. 구현에 따라 `ValueError`로 죽거나 거부한다.
* **수정**: 로더 규칙에 "모든 문자열: UTF-8로 인코딩 가능, 범주 Cc(C0·C1)·Cs 없음", "수는 `float(x)`로 변환 가능하고 유한(`OverflowError`도 거부)", "`commands`·`name`·`worktree`·`test_ids`에도 규칙 9를 적용", "BOM은 UTF-8·UTF-16·UTF-32 모두 명시 거부", "spec card `Phase ∉ PHASE_ORDER`이면 거부"를 더한다. 공격 15 케이스에 C1~C5·C15·C16·C17을 넣는다.

#### M-13 (S3) 로더 8은 "RFC 3339"라고 하지만 RFC 3339가 허용하는 값을 거부한다
* C6: 소문자 `t`/`z`(RFC 3339 5.6 NOTE가 허용)는 로더 8 정규식에서 거부된다. C7: 윤초 `23:59:60Z`는 `fromisoformat`에서 거부된다. C9: 소수 9자리는 통과한다. auditor 도구가 `datetime.isoformat()`만 쓰면 실무 영향은 없다. 하지만 `format: date-time` 검사기(rfc3339-validator)를 설치하면 스키마 판정과 로더 판정이 갈린다.
* **수정**: "RFC 3339의 부분집합: 대문자 `T`/`Z`, 윤초 불허"라고 적는다.

#### M-14 (S3) 참조 무결성과 로더 대상 범위
* C14: `approvals`에 존재하지 않는 승인 기록 id가 있어도 로더 1~10을 모두 통과한다. 파일 존재 검사는 어느 규칙에도 없다.
* 로더 5 "로더가 읽는 판정 기록은 `.ai/verification/` 바로 아래 id 형식 `.json`뿐"은 **전부 훑는다**로도 읽힌다. 그러면 스키마를 바꾸는 게이트 변경 뒤 옛 기록이 새 스키마에 걸려 모든 병합이 거부된다. 이번 병합의 기록 하나만 읽는지 정해야 한다.
* auditor 쓰기 glob `.ai/verification/<id>.json`은 `<id>`가 아무 id라서, auditor가 다른 변경의 과거 판정 기록을 고칠 수 있다(EL1은 경로만 본다).
* **수정**: "승인 id마다 `.ai/approvals/<id>.md`가 존재하고 머리 파싱 통과", "merge gate는 이번 변경의 `<id>.json`만 로드", auditor 경로는 "자기 변경 id만"(code-author의 disputes 규칙과 같은 방식)으로 적는다.

#### M-15 (S3) diff 해시가 아직 git 설정에 흔들리고, 승인 기록 파서의 경계가 없다
* **실측**(git 2.52, 이 저장소, HEAD~3..HEAD, 계획·history 두 경로, 설계 §8.2 명령 그대로): 기본값 해시 `fd4ca810…`. `-c diff.context=5`를 주면 `548d62c4…`, `-c diff.interHunkContext=20`을 주면 `f3f9b70b…`로 바뀐다. `diff.indentHeuristic=false`에서는 같았다. "옵션을 모두 고정한다"는 사실이 아니다.
* `.ai/approvals/`를 훑는 V5가 `_TEMPLATE.md`(id `YYYYMMDD-<slug>`)를 만나면 거부할지 제외할지가 없다(§8.1은 `_schema.json` 제외를 적었다).
* `autocrlf=true`인 worktree에서는 승인 기록이 CRLF로 체크아웃된다. `---\r`를 머리 경계로 인정하는지가 없다.
* **수정**: 명령에 `-U3 --inter-hunk-context=0`을 더하고 `GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL=<빈 파일>`로 실행한다고 적는다. 파서 대상에서 `_`로 시작하는 파일을 제외하고, 줄 끝은 `\r?\n`으로 정한다.

#### M-16 (S3) §3.3이 §3.2 양식을 "그대로" 쓰지 않고, WP-21 분류에 빠진 항목이 있다
* §3.2는 "아래 열 그대로"라면서 열을 `판정 근거(§3.1 순서 번호와 이유)`, `산출 spec card 또는 승인 기록`으로 정했다. §3.3 머리는 `판정 근거`, `산출`이다. 다른 design 문서가 어느 쪽을 따를지 갈린다.
* §13이 만든다고 한 판정 입력 중 `parse_approval_header`, `red_failure_hash`, 판정 기록 로더, `plan_phase_tokens`(CC-1·CC-2)와, 엔진 쪽 `instrument`·`activations_out` 인자(CC-7·CC-8)는 §3.3에 행이 없다. WP-21은 항목마다 분류를 요구한다.
* **수정**: §3.3 머리를 §3.2와 같게 하고 행을 더한다(부트스트랩 항목은 `오케스트레이터`/`사용자`).

#### M-17 (S3) N9.1 '읽을 plan 절'의 잔여 누락(C-22 잔여)
* `00-common` 행: N5.2(DF-35·36·37), N1.4(NFR-4), N2.1(DEC-34·47·51)이 없다. N7.2 U-38도 이 문서가 읽는다(§16).
* `40-defect-fixes` 행: CC-7이 구현할 N6.3 성능 조건과, CC-7·CC-8이 바꿀 MOD10 시그니처의 근거 N3.10이 없다.
* `05-role-separation` 행: "N6.1·N6.2 Phase 0.5"뿐인데 CC-2 자기검사는 N6.1 Phase 열 전체와 N4.2 전체를 읽는다.
* **수정**: 각 행에 더한다(N9.1: "읽기 전에 그 절을 이 열에 추가").

#### M-18 (S3) v5.19가 남긴 계획·history 안의 작은 불일치
* history는 "U-38을 Phase 0.5 착수 조건으로 올렸다"라고 하고 N7.2도 필요 시점이 Phase 0.5인데, **N6.1 0.5 행 '추가 착수 조건'에는 U-38이 없다**(U-15·U-16만 있다). N6.1은 "유일한 순서 정본"이다.
* N0.4 oracle (a)는 넓혔는데, N3.12.3 선택 기준 "물리 불변식(KVL·KCL·VGS 정합·단조성)으로 표현되면 (a)"는 그대로다.
* history의 수치가 서로 맞지 않는다: "`except ValueError` 78곳"(DF-37 AST 합계는 76), 같은 절 안에서 "거부 30/30"과 "거부 케이스 24건". 둘 다 작성자 측정이다.
* **수정**: N6.1 0.5 행에 U-38(확정)을 적는다. N3.12.3 선택 기준에 합성 입력을 한 줄 넣는다. history 수치는 DF-37·독립 검증 기록을 인용하도록 고친다.

#### M-19 (S3) §9.4 "머리 줄로 표를 찾고"의 머리가 정해지지 않았다
* 열 이름으로 찾으면 `Phase` 열이 N3.11(TS 표)·N6.1·N6.2 세 표에 있다(`tok3.txt`). 머리 줄 전체 문자열로 찾는지, 절 제목 + 열 이름으로 찾는지를 정해야 한다.
* 참고(v5.19가 만든 것은 아니다): 셀 수 검사를 계획 전체에 돌리면 N3.6(429행), N3.12.4 EL3(616행, `Role: code|test|audit|doc`의 파이프, v5.19가 고친 행), N3.15(674행), N7.2 U-04(985행)가 GFM 기준으로 파손돼 있다. §9.4 대상 표는 아니지만, EL3 행은 `05` design이 허용 조합표를 만들 때 읽는다.
* **수정**: "절 제목(`### N4.1`, `### N4.2`, `### N6.1`, `### N3.14`) 아래 첫 표"로 정한다. EL3 행의 파이프는 `\|`로 이스케이프한다.

#### M-20 (S3) 같은 값 집합이 두 곳에 있거나, 만들고 쓰지 않는 필드가 있다
* §5: IC5 test가 Phase 1에서 §4의 영역 값 집합을 옮겨 둔다. 6a에서 `DOMAINS`가 생긴 뒤 둘을 대조하는 검사가 §9.4에 없다(정본 둘, N9.4 취지 위반).
* §9.1 `VCheck.tool`: 소비자가 없다(§9.4 대조에도, 로더에도 쓰지 않는다. WP-01).
* **수정**: CC-6에 "IC5 허용 문자열 = `DOMAINS`" 대조 test를 넣는다. `tool`은 지우거나 소비자(자기검사 대상)를 적는다.

#### M-21 (S3) CC-1·CC-5의 입력이 저장소 밖에 있거나 비어 있다
* CC-1 oracle "review22 새 케이스 30건": 그 케이스는 review22 보고서에 묶음 요약으로만 있고, 원본은 세션 scratchpad(`schema_new.py`, `schema_new2.py`)에 있어 저장소에서 재현할 수 없다. 30건 중에는 설계 의도가 **통과**인 것(`failure_hashes` 중복 등)도 섞여 있다.
* CC-5 "깊은 복사 관용구 `json.loads(json.dumps(x))`를 `copy.deepcopy`로": AST 실측 4개(sizing_recipe 13417·14115·14192, stick_diagram 12643)가 전부 `__main__` self-test 안이라 TS1(Phase 1) 뒤에는 대상이 0개다.
* **수정**: 공격 15 케이스 목록은 `tools/gates/redteam/`에 데이터로 두고 기대(거부/통과)를 케이스마다 적는다. CC-5 문구는 "TS1 뒤 AST 계수가 0이면 해당 없음"으로 바꾼다.

#### M-22 (S3) §10·§11의 잔여 모호성
* `spec_digest`는 `spec_fn()` 반환값이다. 그런데 하네스 `run()`은 실행 전에 spec에 `floorplan_target`·`max_layout_retry_rounds`를 `setdefault`한다(`run_harness.py:run`). 도구가 하네스 `run()`을 부르는지 MOD10을 직접 부르는지(§10-1과 §11.2 표가 다르게 읽힌다)에 따라 실제로 돈 spec이 달라진다.
* MOD10 시그니처 `run_gmid_design_pipeline(spec, *, output_dir, instrument, activations_out)`에는 탐색 설정(`grid_points_per_theta`, `search_method`, `slsqp_kwargs`)이 없다. 지금 이 값들은 `SPECS[circuit]` cfg에 있고 spec에는 없다(`specscan.txt`: 파일럿 cfg 키 = grid_points_per_theta·report_dir·search_method·slsqp_kwargs·spec_fn·topology_file).
* `spec_digest`의 "LUT 객체면 그 npz의 sha256": `SemiEmpiricalGmIdLUT` 객체는 원본 파일 경로를 갖지 않는다(배열로 생성). 도구가 어떤 파일로 대응시키는지 없다(실측: 비직렬화 값은 `lut_by_kind.nmos/pmos`, `lut` 세 개).
* `wrap_search` 밖에서 나는 예외(로드 게이트 `SchemaRejectedError`, 레이아웃 단계)의 `status`·`failure_class`가 없다.
* 무동작의 경로 누출 검사: 원시 바이트에서 찾는지 파싱한 문자열에서 찾는지가 없다. JSON 이스케이프(`\\`), 구분자, 드라이브 문자 대소문자 변형을 어떻게 다루는지도 없다. 원시 바이트에서 찾으면 역슬래시 이스케이프 때문에 놓친다.
* **수정**: 한 줄씩 규정한다(도구는 하네스 `run()`을 부르고 digest는 실제 전달 spec, MOD10 인자에 탐색 설정 추가 또는 spec 편입, LUT 파일 = 하네스가 연 경로, 게이트 밖 예외는 `exit_code_for`, 누출 검사는 파싱한 모든 문자열에서 `os.path.normcase`로 비교).

#### M-23 (S3) 숨은 열린 질문(§17 "없음"과 다르다)
* U-38은 "프로젝트 의존성"으로 승인됐다. 그런데 저장소 어디에도 의존성 선언이 없다(requirements·pyproject 없음, `grep` 0). `jsonschema` 4.26.0은 사용자 site-packages에 우연히 있다. 선언 위치와 버전 고정(WP-20 최소 릴리스 나이)을 누가 언제 하는지가 없다.
* §16의 승인 기록 `diff_path`는 이 설계 문서 하나다. v5.19 계획 개정(새 DF·공격·경로표)과 두 양식은 어떤 승인 기록 해시에도 들지 않는다.
* M-06(자기검사 판), M-07(수집 단계 red), M-08(현재 Phase 입력), M-09(N3.16 옮기기 규칙), M-10(감싸는 지점), M-11(적용 시작점)은 설계가 정하지 않았고 넘긴 곳도 적지 않았다.
* **수정**: 각각 설계에서 닫거나, 담당 design(`05`·`10`·`40`·`30`)을 명시해 §17에 적는다.

---

## 3. WP-13 점검: §3.3·§14의 행별 소유 칸

§3.2 규칙: 허용 값은 6개(`오케스트레이터`/`gmid-code-author`/`gmid-test-author`/`gmid-verification-auditor`/`사용자`/`독립 검증 agent`)이고, 한 칸에 한 값이며, 두 칸은 달라야 한다.

| 표 | 행 | 구현 소유 | 판정 기준 소유 | 허용 값 | 두 칸 상이 | 비고 |
|---|---|---|---|---|---|---|
| §3.3 | 이 문서 | 오케스트레이터 | 독립 검증 agent | 적합 | 적합 | 최종 판정은 사용자(DEC-51). 고정 수단 칸에 적혀 있다 |
| §3.3 | 판정 기록 스키마 초안 | 오케스트레이터 | 사용자 | 적합 | 적합 | 부트스트랩 규칙(§3.2)과 일치. EL3 분류 겹침은 M-05 |
| §3.3 | 승인 기록 양식 | 오케스트레이터 | 사용자 | 적합 | 적합 | 양식이 §8.2와 어긋난다(M-02) |
| §3.3 | merge gate 상수 | 오케스트레이터 | 사용자 | 적합 | 적합 | 자기검사의 판이 미정이다(M-06) |
| §3.3 | IC 담당 표 | gmid-code-author | gmid-test-author | 적합 | 적합 | code-author의 표 수정이 곧 xfail 범위 변경이다. V5 test diff에는 잡히지 않고 §9.4 일치 test만 막는다 |
| §3.3 | 실패 규약 코드 | gmid-code-author | gmid-test-author | 적합 | 적합 | -- |
| §3.3 | 옛 키 게이트 | gmid-code-author | gmid-test-author | 적합 | 적합 | 기대 목록을 옮기는 규칙이 없다(M-09) |
| §3.3 | 영역 토큰 | gmid-code-author | gmid-test-author | 적합 | 적합 | 값 집합이 두 곳에 있다(M-20) |
| §3.3 | 계측 도구 | gmid-code-author | gmid-test-author | 적합 | 적합 | -- |
| §3.3 | margin 정규화 | gmid-code-author | gmid-test-author | 적합 | 적합 | -- |
| §3.3 | (없음) 로더·`parse_approval_header`·`red_failure_hash`·`plan_phase_tokens`·`instrument`/`activations_out` | -- | -- | **행 없음** | -- | M-16 |
| §14 | CC-1 | 오케스트레이터 | 사용자 | 적합 | 적합 | 케이스 원본이 저장소 밖(M-21) |
| §14 | CC-2 | 오케스트레이터 | 사용자 | 적합 | 적합 | -- |
| §14 | CC-3~CC-9 | gmid-code-author | gmid-test-author | 적합 | 적합 | -- |

**결론**: 형식 위반은 없다(두 칸이 같은 행 0, 허용 밖 값 0). 결함은 행이 빠진 것(M-16)과 머리 열 이름 불일치(M-16)다.

---

## 4. 코드 사실 대조(지시 4)

| 설계 주장 | 실측(AST·소스) | 판정 |
|---|---|---|
| §6.2 `json.load`/`json.loads`: sizing_recipe 7·3, stick_diagram 11·1, design_report 1, topology_to_markdown 2 | `ast_json.txt`: 7·3 / 11·1 / 1 / 2. `from json import` 0 | 맞음 |
| 그중 인라인 self-test 안의 것은 TS1에서 사라진다 | sizing_recipe `__main__`(12571~): load 3·loads 3. stick(8992~): load 8·loads 1. topology_to_markdown(187~): 1. 운영에 남는 것: sizing_recipe 1542·5388·8268·8315, stick 3958·4722·8590, design_report 111, topology_to_markdown 82 | 맞음. 깊은 복사 4개는 전부 `__main__` 안이다(M-21) |
| `JSON_KINDS` 근거: topology, `.derived.json`, instance.json, 회귀 기준 JSON | 1542 = `reference_json_path`(회귀 기준), 8268 = `derived_bounds_path` 사이드카, design_report 111 = instance.json, 나머지 = topology | 맞음 |
| DF-37 핸들러 수 | `exc23.txt`: ValueError 52/23/1, Exception 7/1/1/1/1/2 | 맞음. 다만 `except InfeasibleSizingError` 18곳이 빠졌다(M-04) |
| `spec_fingerprint` 등급 R2, 해상도 키만 | 레지스트리 408행 `## 5. R2` 절. 소스 8151: `_SPEC_RESOLUTION_KEYS` 7개 | 맞음 |
| `validate_no_legacy_vs_key`는 `_build_theta_evaluator`에서 다른 필드를 읽은 뒤 호출 | 정의 5790, 호출 8518 한 곳 | 맞음 |
| `InfeasibleSizingError(ValueError)` 기존 클래스, 레지스트리 목적지 MOD4 | 6984 `class InfeasibleSizingError(ValueError)`. 레지스트리 330 `gmid_sizing_engine` | 맞음 |
| 하네스 `run()`이 모든 예외를 삼키고 0으로 끝난다(DF-37) | 511 `except Exception as e:` print·traceback. `__main__`은 `run()` 뒤 종료. 단 알 수 없는 circuit_key는 `try` 밖 `raise`라 exit 1 | 대체로 맞음 |
| `save_instance_json`이 `topology_ref`에 절대 경로(DF-36) | stick 8966 `"topology_ref": topology_json_path`. 호출자는 `os.path.join(LIBRARY_DIR, …)`(절대 경로) | 맞음 |
| 하네스 경로가 메인 체크아웃 절대 경로이고 LUT를 import 시점에 읽는다(DF-35) | 35행 `sys.path.insert(0, r"C:\…\assets")`, 41~44행 절대 경로 상수, 63행 `np.load(LUTFILE)` | 맞음 |
| `spec_fn()` 반환값의 직렬화 불가 값은 LUT 객체뿐 | `specscan.txt`: 4회로 모두 `lut_by_kind.nmos/pmos`, `lut`(`SemiEmpiricalGmIdLUT`)뿐. 대체하면 `sort_keys` 직렬화 성공 | 맞음(대응 파일 규칙은 M-22) |
| 평가 커널 빌더를 감싸면 평가가 모두 덮인다(§10-1의 전제) | `_build_theta_evaluator` 호출 함수 6개 | 감싸는 지점이 미정이다(M-10) |

---

## 5. 스키마·로더 독립 측정(지시 5)

jsonschema 4.26.0, `Draft202012Validator(schema, format_checker=FormatChecker())`, `check_schema` 통과. 이 환경의 `FormatChecker`에는 `date-time` 검사기가 없다(`rfc3339_validator` 미설치). 로더 1~10은 설계 §8.1 문구대로 따로 구현했다. 작성자 스크립트, review21 C-08, review22(`schema_new*.py` 포함)에 없는 새 기록 17건과 대조 1건을 돌렸다(`review23/schema23.txt`).

| # | 케이스 | 스키마 | 로더(문구대로) | 설계 의도 | 스키마/로더 분담과 일치? |
|---|---|---|---|---|---|
| C0 | 정상 red-green | 통과 | 통과 | 통과 | 일치 |
| C1 | test_id에 U+0085 | 통과 | 통과 | 거부("제어 문자 없는") | **불일치**(M-12) |
| C2 | test_id 짝 없는 서로게이트 | 통과 | 통과 → 해시에서 `UnicodeEncodeError` | 거부 | **불일치**(M-12) |
| C3 | value 401자리 정수 | 통과 | **`OverflowError`**(거부 아님) | 거부(규칙 3) | **불일치**(M-12) |
| C4 | commands = [U+200B] | 통과 | 통과 | 거부가 합당 | 규칙 없음(M-12) |
| C5 | basis = U+3164 | 통과 | 통과 | 거부(규칙 9 취지) | **불일치**(M-12) |
| C6 | time 소문자 t/z | 통과 | 거부(8 정규식) | RFC 3339 적합 | 과잉 거부(M-13) |
| C7 | time 윤초 | 통과 | 거부(8 fromisoformat) | RFC 3339 적합 | 과잉 거부(M-13) |
| C8 | time 아랍-인도 숫자 | 통과 | 거부(8 fromisoformat) | 거부 | 일치 |
| C9 | time 소수 9자리 | 통과 | 통과 | 통과 | 일치 |
| C10 | N/A basis `N/A(Phase 4 변경, 도입 6b)`, 괄호 밖 집합 | 통과 | **거부**(10) | 통과(N4.2 양식) | **구현에 따라 갈림**(M-03) |
| C11 | 같은 기록, 합집합 | 통과 | 통과 | 통과 | 〃 |
| C12 | N/A basis `도입 Phase는 6b부터` | 통과 | 거부(10) | 통과가 합당 | 과잉 거부(M-03) |
| C13 | N/A basis `도입 6c 전이다. 6b` | 통과 | 통과 | 거부가 합당 | 과소 거부(M-03) |
| C14 | approvals에 없는 승인 id | 통과 | 통과 | 거부가 합당 | 규칙 없음(M-14) |
| C15 | test_id `" "` | 통과 | 통과 | 거부가 합당 | 규칙 없음(M-12) |
| C16 | UTF-16LE BOM 파일 | 파싱 예외 | `UnicodeDecodeError`(BOM 메시지 없음) | 거부 + BOM 명시 | 부분(M-12) |
| C17 | spec card Phase `0(문서)` + N/A | 통과 | 구현 의존(내 구현은 거부) | 거부 | 규칙 없음(M-12) |

N6.2 `0(문서)` DoD "스키마 밖 필드를 거부함"은 **충족**한다. 올바른 기록은 통과하고, 새 케이스에서도 스키마가 맡은 필드 형식 판정에 과오가 없다. 불일치는 모두 로더 규칙(§8.1)의 문구와 범위에 있다.

---

## 6. §9.4 `plan_phase_tokens` 독립 구현 결과(지시 6)

설계 문장만 보고 구현했다(`tok3.py`). 괄호 `\([^()]*\)`를 반복해 지우고, 설계 정규식을 괄호 밖과 안에 따로 적용했다. 표는 "`|`로 시작하는 줄 + 구분선"으로 찾았고, 셀은 이스케이프되지 않은 `|`로 나눴다.

* **N4.1 담당 Phase**: IC1 {6b}, IC2 {6b}, IC3 {1}, IC4 {6c}, IC5 {1}, IC6 {6c}, IC7 밖 {6a}·안 {6c}, IC8 {6c}, IC9 {6b}, IC10 {6b}, IC11 밖 {4, 6a}·안 {}
* **N4.2 도입**: V1 {1}(안 {} -- `0.5는`은 토큰이 아니다), V2~V6 {1}, V7 {2}, V8 {4}, V9 {6b}, V10 {0.5}
* **N6.1 Phase**: `0` {}, `**0(문서)**` {}, 나머지 12행이 차례로 0.5, 1, 2, 3, 4, 5, 6a, 6b, 6c, 7a, 7b, 7c = `PHASE_ORDER`
* **셀 수 검사**: N4.1·N4.2·N6.1 세 표의 파손 행은 0이다.
* **설계 주장과의 대조**: "IC1~IC11·V1~V10 괄호 밖 집합 전부 비지 않음, 괄호 안 토큰은 IC7 {6c} 하나뿐, N6.1 빈 집합 행은 정확히 `0`·`0(문서)` 둘"을 **그대로 재현했다**.
* **diff가 건드린 표 전체의 셀 수**: N0.4 용어집, N3.10, N3.11, N3.12.1, N3.12.2, N3.14, N4.1, N4.3, N5.2, N6.1, N6.2, N9.1은 정상이다. N3.12.4는 EL3 행이 6셀(머리 3셀)이다. 원인은 코드 스팬 안 파이프이고 HEAD에도 있던 것이다. N7.2는 U-04 행이 5셀이다(기존). N3.6과 N3.15도 기존 파손이다(M-19). 공격 수 "16건"·"0.5 대상 14건(1~12·15·16)"·"6a 2건(13·14)"은 계획 N4.3·N6.2·N9.1 `05` 행, 설계, history에서 모두 일치한다.

---

## 7. §10·§11·§8.2: 두 구현자가 다르게 갈 곳과 계측 인터페이스의 실현성(지시 7)

1. **감싸는 지점**(M-10): 빌더 호출 지점 6곳에 `instrument`를 어떻게 전하는지, 레이아웃 수렴을 wall-clock에 넣는지. 현재 `optimize_full_circuit_budget`은 θ 탐색과 레이아웃 재시도를 한 함수에서 한다. 레지스트리는 목적지를 MOD8로, N3.10은 "탐색부"를 MOD6로 둔다. **실현성**: 빌더 안에서 감싸고 `instrument`를 빌더 인자(또는 한 문맥 변수)로 전하면 가능하다. 다만 30 design의 이관표가 그 인자를 반영해야 하므로 CC-7만으로는 닫히지 않는다.
2. **적용 시작점과 예외 종료 판정**(M-11).
3. **도구가 부르는 진입점과 digest 대상 spec**, MOD10 시그니처의 탐색 설정(M-22).
4. **red 해시**: 수집 단계 오류, rootdir, 출력 경로(M-07).
5. **diff 해시**: `diff.context`/`interHunkContext` 설정 의존, 양식 명령 불일치(M-15, M-02).
6. **승인 기록 파서**: `_TEMPLATE.md` 제외, CRLF(M-15).
7. **경로 누출 검사**의 비교 방식(M-22).

1·2·4만 고치면 두 구현이 같은 수치와 판정을 낸다. 나머지는 한 줄 규정으로 닫힌다.

---

## 8. N9.2 필수 절과 숨은 열린 질문(지시 8)

* 1 범위 §1, 2 인터페이스 §6~§11, 3 판정식 §12, 4 실패 경로 §7 + §10 도구 exit code, 5 역할별 산출물 §14, 6 DoD §15, 7 착수 조건 §16, 8 열린 질문 §17이 **모두 있다**.
* §15 "공통 정의가 한 곳에 모임"을 대응시켜 봤다. N9.1 `00-common` 행 9항목(분류 양식 §3, 용어→코드 §4, 영역 §5, 명명·옛 키 §6, 실패 규약 §7, 두 스키마 §8, V/IC 형식 §9, 성능 명령 §10, 무동작 §11)이 **전부 대응한다**.
* §15 "`_TEMPLATE.md`가 있음"은 존재 조건만 충족한다. 내용이 §8.2와 어긋난다(M-02).
* §17 "없음"은 사실과 다르다. 정하지 않았고 넘긴 곳도 적지 않은 항목은 다음과 같다: 자기검사 판(M-06), 수집 단계 red(M-07), 현재 Phase 입력(M-08), N3.16 옮기기 규칙(M-09), 감싸는 지점(M-10), 적용 시작점·예외 종료(M-11), 기반 클래스 catch 교체 범위(M-04), `jsonschema` 의존성 선언 위치, v5.19 계획 개정과 양식의 승인 범위(M-23).

---

## 9. 집계와 판정

| 구분 | 건수 | ID |
|---|---|---|
| review22 부분 C 항목: 닫힘 | 6 | C-07, C-09, C-12, C-14, C-20, C-24 |
| review22 부분 C 항목: 부분 | 1 | C-22 |
| N-01~N-24: 닫힘 | 19 | N-01~05, 08~14, 16~19, 22~24 |
| N-01~N-24: 부분 | 5 | N-06, N-07, N-15, N-20, N-21 |
| N-01~N-24: 안 닫힘 | 0 | -- |
| 새 S1 | 0 | -- |
| 새 S2 | 11 | M-01 ~ M-11 |
| 새 S3 | 12 | M-12 ~ M-23 |

**판정: 수정 후 승인.**

review22의 S2 9건 중 N-01~N-05, N-08, N-09는 닫혔다. N-06과 N-07은 형식은 들어갔지만 실현 단계의 빈칸이 남았다(M-10, M-07). 새 S2 11건은 모두 국소 규정으로 닫힌다. 계획서에 닿는 것과 설계에 닿는 것은 다음과 같다.

* 계획 한 줄: M-01(공격 15 범위), M-04(DF-37에 기반 클래스 catch), M-05(EL3 우선순위)
* 양식 한 곳: M-02
* 로더·게이트 규정: M-03(N/A basis 형식), M-06(자기검사 판), M-07(red 해시 입력)
* 설계 규정: M-08(현재 Phase 입력), M-09(N3.16 옮기기 표), M-10(감싸는 지점), M-11(적용 시작점)

재작성은 필요 없다. 다음 재검증에서는 M-01~M-11 반영 여부와 §17 갱신만 보면 된다.
