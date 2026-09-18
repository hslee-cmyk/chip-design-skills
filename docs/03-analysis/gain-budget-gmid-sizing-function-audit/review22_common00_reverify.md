# review22 -- `00-common` design v1.1 재검증 (독립)

* 대상: `docs/02-design/features/gain-budget-gmid-sizing.00-common.design.md` v1.1(작업 트리, 522줄), `.ai/verification/_schema.json`, `.ai/approvals/_TEMPLATE.md`, `.ai/approvals/20260918-u38-jsonschema.md`
* 기준: 계획서 v5.19(작업 트리, `git diff HEAD`로 v5.19 개정 확인), history 머리 절 '`00-common` 구성안 C와 v5.19 계획 보완'과 Version History 5.19 행, 이전 검증 `review21_common00_verify.md`(C-01~C-24), 함수 레지스트리, `workspaces/run_harness.py`·`sizing_recipe.py`·`stick_diagram.py` 실제 소스
* 검증자: 독립 검증 agent. 이 문서도 review21도 쓰지 않았다. 작성자 측정(`common00_schema_reject_check.py`/`.txt`)은 증거로 쓰지 않고 참고만 했다.
* 내 측정 스크립트는 저장소 밖 scratchpad에 있다(`schema_new.py`, `schema_new2.py`, `tok.py`, `cnt.py`). 저장소에서 바꾼 파일은 이 보고서 하나다.
* 심각도: **S1** = 승인을 막는다 / **S2** = 승인 전에 고친다(구현자 둘이 다르게 갈 수 있다) / **S3** = 경미

---

## 1. C-01~C-24 닫힘 표

| ID | 판정 | 근거 |
|---|---|---|
| C-01 (S1) | **닫힘** | §10 절차 1·2: `cwd=worktree`인 별도 프로세스를 쓰고 `sys.path` 맨 앞에 worktree 경로를 둔다. import한 모듈 `__file__`과 LUT·library 경로가 worktree 안에 있는지 사전 검사하고, 아니면 `measurement_setup` 실패로 끝낸다. 선행 조건 DF-35·DF-36을 계획 N5.2에 넣었고 Phase는 4, 도구보다 먼저다. §11.4는 경로 누출을 FAIL로 둔다. 소스 확인: `run_harness.py` 42~45행이 절대 경로이고 63행 `np.load(LUTFILE)`이 import 시점에 돈다. `save_instance_json`은 `"topology_ref": topology_json_path`를 쓴다. 이 둘이 사실이므로 사전 검사가 DF-35 전의 측정을 실제로 거부한다. 남은 문제는 Phase 4에서 쓸 패치 지점이다(N-06). |
| C-02 (S1) | **닫힘** | §7.1: `SchemaRejectedError`·`FailureRecord`는 MOD2에, 기반 클래스를 포함한 N3.14 계층은 MOD4에 둔다. 레지스트리 `InfeasibleSizingError` 행(R1 절)의 목적지 `gmid_sizing_engine`과 맞는다. 지금 `InfeasibleSizingError`를 raise하는 함수 7개(`allocate_stack_headroom`, `search_gm_id_for_role`, `apply_diode_self_consistent_gm_id`, `_run_shared_current_joint_scan`, `_feed_metric_stage_budget`, `_hr_resolve_vertical_group`, `_build_theta_evaluator`)는 레지스트리상 목적지가 모두 MOD4 또는 MOD6이라 import 규칙을 어기지 않는다. 다만 MOD3에서 raise하는 경우가 생길 수 있다(N-18). |
| C-03 (S1) | **닫힘** | §14에서 CC-3·CC-7·CC-8은 `red-green`이고, 합성 입력으로 거부를 보이는 red가 적혀 있다. 계획 N3.12.3·N4.2 V2를 넓힌 곳은 없다. |
| C-04 | **닫힘** | N3.12.6 ①(v5.19)에 "merge gate의 판정 기록 로더·`V_CHECKS`·`PHASE_ORDER`·승인 기록 머리 파서"가 들어갔다. design §9.1·§13·§14 CC-1·CC-2(부트스트랩, 오케스트레이터)와 맞는다. |
| C-05 | **닫힘** | N3.14 SCHEMA_REJECTED는 `Exception` 직접 하위다. DF-37이 광범위 except 전수를 다시 raise하게 하고, §7.3은 DF-37을 인용한다. 세어 둔 개수가 AST 실측과 조금 다르다(N-11). |
| C-06 | **닫힘** | §9.4 토큰화 규칙, `from_phase`, `sub`, N6.1 `0` 행 주(v5.19), §7.1 N3.14 키 규칙이 모두 들어갔다. 내가 따로 구현해 설계의 실측 주장을 재현했다(§4 절). 그래도 남은 모호성이 있다(N-09, N-21). |
| C-07 | **부분** | N6.2 `0(문서)`는 C안(형식 + 일치 test 명세, 인용 여부는 각 문서의 검증 항목)으로 바뀌었다. **N9.1 `00-common` 행은 바뀌지 않았다**. 여전히 "용어집 최종본(N0.4)", "V 도입 표(N4.2), IC 담당 표(N4.1)"다. 고친 문장은 N6.1 `0(문서)` 행에 열 두 개로 잘못 붙어 있다(N-01). |
| C-08 | **닫힘**(C-08 케이스 한정) | 끝 앵커가 `(?![\s\S])`로 바뀌었고, basis는 `\S`, `approvals`·`test_ids`에는 `uniqueItems`가 붙었다. NaN은 로더 3이 맡는다. review21의 케이스를 다시 넣어 보지는 않았다. 대신 새 케이스 30건을 돌렸고, 여기서 새 구멍이 나왔다(N-02, N-14). |
| C-09 | **부분** | 해시마다 소비자가 생겼다(merge gate 재실행 대조, §8.1). 해시 입력은 `(test_id, 예외 타입)`으로 좁혔다. 남은 것: "예외 타입의 정규 이름"이 무엇인지(`AssertionError`인지 `builtins.AssertionError`인지), pytest 실행 결과에서 그 타입을 어떻게 꺼내는지가 없다. 해시를 쓰는 auditor와 재계산하는 merge gate가 서로 다른 값을 낼 수 있다(N-07). |
| C-10 | **닫힘** | §15 판정 주체가 독립 검증 agent가 됐다. `IC_TABLE`과 계측 도구는 code-author 소유, 그 test는 test-author 소유다(N3.11 트리·N6.3 v5.19와 일치). |
| C-11 | **닫힘** | review21이 낸 두 번째 수정안을 택했다. spec card '오라클 출처'에 사용자가 승인한 계획서 절과 커밋 해시를 적는다(§9.4, CC-3·CC-5). |
| C-12 | **부분** | (1) 래퍼·재raise 방식은 들어갔다. (2) 실패 호출 포함과 `eval_outcomes`도 들어갔다. (4) LUT는 파일 sha256으로 정했다. (6) auditor 부속 경로(N3.12.1 v5.19)와 로더 대상 한정도 들어갔다. 남은 것: (3) `spec_fingerprint`를 "등급 R0, 호출만"이라고 적었지만 레지스트리 등급은 **R2**이고, 지문이 스펙 동일성을 뜻하지도 않는다(N-04). (5) "Phase의 마지막 병합 card"는 판정 시점에 정할 수 없다(N-08). 캐시 설명도 부정확하다(N-12). |
| C-13 | **닫힘** | Phase별 진입점 표, 비교 대상 JSON 한정, 재귀 투영, `activations_out` 인자, spec card '무동작 판정 입력' 필드(N3.12.3 v5.19), 시드 1~5가 모두 들어갔다. 남은 모호성은 경미하다(N-24). |
| C-14 | **부분** | MG0 단계, `where`를 파일 종류로 한정, `spec_fn()` 반환 직후 검사는 닫혔다. 그런데 새로 넣은 배선 규칙("`assets/*.py`에서 `load_json_checked` 밖의 `json.load`/`json.loads` 0")은 `where`의 네 종류와 맞지 않고, 적은 지점 수도 틀리다(N-05). |
| C-15 | **닫힘** | N3.12.2(v5.19)에서 code-author가 게이트 변경 spec card와 승인 기록이 있을 때 `_schema.json`을 바꿀 수 있다. 다만 auditor의 쓰기 경로 glob도 `_schema.json`을 덮는다. 이 새 모순은 N-03에서 다룬다. |
| C-16 | **닫힘** | `qualifier`는 이름만 예약했다(§4). `QUALIFIERS` 상수와 '판정 함수 거부'는 뺐다. |
| C-17 | **닫힘** | N4.1 IC5(v5.19)에 `영역:` 줄을 넣었고, N9.1 `10-test-separation` 행에 반영했다. `영역: 없음(스키마)` 토큰도 정의했다(§5). IC5 대상 이름 집합의 사각지대는 N-17에서 다룬다. |
| C-18 | **닫힘** | `diff_path` 반복, 모르는 키 거부, 주석 줄 금지, design 승인은 `diff`, `,` 뒤 strip, 파서 한 곳이 모두 들어갔다. 재현성의 잔여 문제는 N-15에서 다룬다. |
| C-19 | **닫힘** | `plan_version: 5.19`이다. U-38 확정과 승인 기록 id도 반영했다(§16). |
| C-20 | **부분** | 부류 값은 셋으로 고쳤다. 그러나 §3.3 '판정 표 상수' 행의 두 소유 칸이 같은 문자열 "CC별(§14)"이다. §14는 §3.2 허용 이름 밖인 "오케스트레이터", "code-author / test-author", "사용자"를 쓴다(N-16). |
| C-21 | **닫힘** | §7은 "분류·발생·처리·exit code는 N3.14가 정본"이라고 하고 루프 규칙은 인용만 한다. 개수는 DF-37과 §7.3 두 곳에 중복돼 있다(N-11). |
| C-22 | **부분** | N9.1의 `05`·`10`·`40`·`6a` 행에는 CC 발행이 반영됐다. **`00-common` 행의 '읽을 plan 절' 열은 그대로다**(N0.4 / N2.2 / N3.12.5 / N3.12.6 / N3.14 / N4.1 / N4.2 / N6.3 / DEC). 고친 목록(N0.1 … N3.16 … N6.2)은 N6.1 행 끝에 잘못 들어갔다(N-01). |
| C-23 | **닫힘** | 시드는 1~5다. 파일럿 이름은 자리표시자로 바꿨고, `$PY` 정의(§0)가 들어갔다. |
| C-24 | **부분** | `exit_code_for`의 MRO 규칙과 §12 판정식 절은 들어갔다. CC-7·CC-8 oracle "(a) 구성으로 정답이 정해진 합성 입력"은 여전히 N0.4·N3.12.3의 (a)(물리 불변식·손계산: KVL·KCL·VGS 정합·단조성)가 아니다. 계획 (a)의 정의를 넓히거나 다른 종으로 적어야 한다. |

**집계: 닫힘 17 / 부분 7(C-07, C-09, C-12, C-14, C-20, C-22, C-24) / 안 닫힘 0**

---

## 2. 새 결함

### S2

#### N-01 (S2) v5.19 개정이 N9.1 `00-common` 행 대신 N6.1 `0(문서)` 행에 붙었다. design은 닫혔다고 적었다
* **위치**: 계획 N6.1 `0(문서)` 행, N9.1 `00-common` 행. design §0("N9.1 해당 행 v5.19"), §14 머리, §17("N6.2·N9.1 `00-common` 행"). history v5.19 절("N6.2·N9.1 `00-common` 행을 C안에 맞게(C-07, C-22)")
* **근거**: `git diff HEAD`의 N9.1 `00-common` 행은 바뀌지 않았다. N6.1 표 머리는 5열인데, 표 행을 셀로 나눠 보면 `0(문서)` 행만 **7셀**이다. 덧붙은 두 셀은 '반드시 담을 것'과 '읽을 plan 절'(N0.1 / … / N3.16 / N4.3 / N6.1 / N6.2 …)이다. 영향은 셋이다.
  1. N9.1은 여전히 `00-common`에 "용어집 최종본(N0.4)"과 "V 도입 표·IC 담당 표"를 담으라고 한다. N6.2(v5.19, 형식만)와 계획 안에서 모순이다.
  2. N9.1 '읽을 plan 절' 규칙("읽기 전에 그 절을 이 열에 추가")이 지켜지지 않았다.
  3. §9.4 일치 test는 N6.1 표를 읽는다. 셀 수를 검사하는 구현은 FAIL을 내고, 머리와 zip하는 구현은 통과한다. 구현마다 판정이 갈린다.
* **수정**: N6.1 `0(문서)` 행을 5셀로 되돌린다. 두 셀의 내용은 N9.1 `00-common` 행의 두 칸으로 옮긴다. §9.4에 "행의 셀 수 ≠ 머리 셀 수이면 FAIL(표 파손)"을 명시한다.

#### N-02 (S2) `1e400`처럼 넘치는 실수 리터럴이 스키마와 로더를 모두 통과한다
* **위치**: §8.1 로더 추가 검사 3("`json.loads(..., parse_constant=거부)`로 NaN·Infinity를 거부"), §6.2 `load_json_checked` docstring("NaN·Infinity 거부")
* **근거**(scratchpad `schema_new.py`, jsonschema 4.26.0, `Draft202012Validator` + `FormatChecker`): `"value": 1e400`과 `-1e400`은 `json.loads`에서 `inf`/`-inf`가 된다. `parse_constant`는 `NaN`·`Infinity`·`-Infinity` **리터럴**에만 불리므로 걸리지 않는다. 스키마 `type: number`도 통과한다. 설계 문구대로 구현한 로더(2·3·4·5)도 통과시킨다. 결국 판정 기록 `reproduced_numbers`와 topology·spec JSON에 무한대가 들어온다.
* **수정**: `parse_float`에서 `math.isfinite`를 검사하거나, 로드 뒤 모든 수를 재귀로 검사하도록 규칙을 "모든 수가 유한"으로 바꾼다. §6.2와 §8.1 두 곳에 같게 적는다. 공격 15 케이스에 `±1e400`을 더한다.

#### N-03 (S2) auditor 쓰기 경로 `.ai/verification/**`가 `_schema.json`을 포함한다(N3.12.1·N3.12.2 모순)
* **위치**: 계획 N3.12.2 auditor 행, N3.12.1(v5.19: "판정 기록과 그 부속 산출물 외 쓰기 불가"), N3.12.2 code-author 행(v5.19: `_schema.json`은 게이트 변경 card + 승인 기록이 있을 때). design §8.1 '변경 주체', §13
* **근거**: EL1·EL2 hook은 N3.12.2 glob으로 판정한다. 그 glob대로면 auditor가 자기 기록을 검증하는 스키마를 조건 없이 고칠 수 있다(WP-13). 한 경로에 소유자가 둘이 되고, 그중 하나는 무조건이다.
* **수정**: auditor 행을 `.ai/verification/<id>.json`, `.ai/verification/<id>/**`(`_schema.json` 제외)로 좁힌다. design §8.1에 "스키마 변경은 code-author만"과 "그 변경의 판정 기록은 base 스키마로 검증한다(바꾼 스키마로 자기 판정을 검증하지 않는다)"를 적는다.

#### N-04 (S2) `spec_fingerprint`는 등급 R2다. 호출부를 늘리지 말라는 규칙에 걸리고, 스펙 동일성도 뜻하지 않는다
* **위치**: §10 출력 JSON `spec_digest`("레지스트리 정본 `spec_fingerprint(spec)`의 반환값(등급 R0, 호출만)")
* **근거**:
  * 레지스트리 408행 `spec_fingerprint`는 `## 5. R2 -- §12 구조로 대체 예정 (새 호출부를 늘리지 않는다)` 절에 있다. R0 절이 아니다. `measure_search_perf.py`가 새 호출부가 되므로 WP-14와 레지스트리 §0 규칙 3을 어긴다.
  * 소스(`sizing_recipe.py:spec_fingerprint`)는 해상도 키 7개(`L_candidates`…`stage_power_tolerance`)만 본다. GBW·CL 목표, `vdd`, 제약값, topology는 빠진다. 레지스트리도 "LUT·vdd·제약값·topology·엔진 제외"라고 적는다. 스펙 목표가 다른 두 측정이 같은 `spec_digest`를 낸다. N6.3의 조건 "정본 spec"을 식별하지 못한다.
* **수정**: 등급 표기를 R2로 고친다. 필드 이름을 `spec_resolution_fingerprint`처럼 뜻대로 바꾸고 R2 호출 추가 승인을 받거나(WP-01), `spec_fn` 반환 dict에서 LUT 객체를 뺀 정규 JSON의 sha256 + topology 파일 sha256으로 정의한다. 새 지문 함수를 만들게 되면 레지스트리 등록과 S0 대체 계획을 함께 적는다.

#### N-05 (S2) "엔진 모듈의 모든 `json.load`/`json.loads`는 `load_json_checked`로"는 `where` 네 종류로 구현할 수 없다. 지점 수도 틀리다
* **위치**: §6.2 '배선'. §6.1 `where: "topology" | "sizing_spec" | "structure" | "harness_spec"`. N9.1 `40` 행 "직접 `json.load` 전수 대체"
* **근거**(AST 실측, `cnt.py`):
  * `sizing_recipe.py`: `json.load` 7(1542, 5388, 8268, 8315, 13202, 14459, 15263) + `json.loads` 3(13417, 14115, 14192, 모두 `json.loads(json.dumps(x))` 깊은 복사)
  * `stick_diagram.py`: `json.load` **11**(설계의 12는 grep에 걸린 주석·문자열 한 줄을 센 것) + `json.loads` 1
  * `design_report.py`: 1(instance.json). `topology_to_markdown.py`: 2. 둘 다 `assets/*.py`라 AST 검사 범위에 들고, 설계가 적은 목록에는 없다.
  * **topology 파일이 아닌 JSON**: 1542 = 회귀 기준 JSON, 8268 = `load_derived_bounds`의 `.derived.json` 사이드카, `design_report`/stick_diagram 10752 = instance.json. 이들은 `where`에 맞는 값이 없다. N3.16 끝 주의("옛 키로 저장된 instance.json은 … 로드 게이트가 거부")도 instance 종류를 요구한다.
  * 지점의 과반(sizing_recipe 12571행 뒤, stick_diagram 8992행 뒤)은 `__main__` self-test라서 TS1(Phase 1)에서 사라진다. Phase 4의 CC-5 범위가 아니다.
* **수정**: `where`에 `instance`, `derived_bounds` 등 실제 파일 종류를 더한다(표 행이 없어도 로더는 거친다). 아니면 AST 규칙을 "네 종류 파일을 여는 호출"로 한정한다. 깊은 복사 관용구는 AST 패턴으로 예외를 두거나 `copy.deepcopy`로 바꾸는 것을 CC-5 범위에 넣는다. 개수 문장은 지우거나 "TS1 뒤 CC-5 spec card가 AST로 센다"로 바꾼다.

#### N-06 (S2) §10·§11의 패치 지점이 Phase 3 전 이름뿐인데, 도구는 Phase 3 뒤(Phase 4)에 만든다
* **위치**: §10 절차 2~5("Phase 3 전 `run_harness.run`", "`run_harness.optimize_full_circuit_budget`", "`sizing_recipe._build_theta_evaluator`", "`run_harness.WORKSPACES_DIR` … DF-35 뒤에도 같은 전역"), 절차 6, §11.2 '3 전' 행
* **근거**: CC-7·CC-8은 Phase 4다(§14, §18.1). Phase 3 DoD에서 `sizing_recipe.py`가 삭제되고, 운영 경로는 `run_gmid_design_pipeline` 이하다(N0.4 '운영 경로'). 그래서 설계가 구체적으로 적은 이름은 도구를 만드는 시점에 하나도 없다. 절차 6은 "옮겨지면 패치 지점만 갱신"이라고 미룬다. 분할 뒤 MOD10이 `from theta_search import optimize_full_circuit_budget`처럼 이름을 묶어 import하면, 모듈 속성을 패치해도 가로채지 못한다. 어느 모듈의 어느 이름을 패치할지는 구현자마다 달라진다. 또 "DF-35 뒤에도 같은 전역 `WORKSPACES_DIR`"은 계획 DF-35(수정 방향 "`__file__`에서 유도")에 없는 제약을 `40` design에 거는 것이다.
* **수정**: 패치 대신 계측 인터페이스를 정한다. 예: MOD10 진입점이 `output_dir`와 `instrument`(평가 래퍼 콜백) 인자를 받는다. 이 인자를 CC-7 범위(`activations_out`과 같은 방식)에 넣는다. 패치를 유지한다면 "호출 시점에 이름을 찾는 모듈의 속성"으로 규칙을 적는다.

#### N-07 (S2) `failure_hashes`의 "예외 타입의 정규 이름"과 추출 방법이 정의되지 않았다
* **위치**: §8.1 해시 정의, §12 'red 재현' 행, §14 CC-1 "해시 재계산"
* **근거**: 해시는 auditor가 기록하고 merge gate(CC-1, 오케스트레이터 작성)가 다시 계산한다. `AssertionError`와 `builtins.AssertionError`, pytest `Failed`와 `_pytest.outcomes.Failed`, `__qualname__`과 `__name__` 중 무엇인지 정하지 않았다. pytest 결과에서 타입을 어떻게 얻는지(`reprcrash` 메시지 파싱, junitxml, 훅)도 없다. 두 주체가 다르게 구현하면 올바른 기록도 가짜로 거부된다(또는 반대).
* **수정**: `merge_gate.py`에 `red_failure_hash(test_id, exc_type) -> str` 하나를 두고 auditor 도구도 그것을 import하게 한다. 정규 이름은 `f"{t.__module__}.{t.__qualname__}"`로 정한다. 추출은 pytest 플러그인 훅(`pytest_runtest_makereport`의 `call.excinfo.type`)으로 정한다.

#### N-08 (S2) 성능 측정의 실행 단위 "Phase의 마지막으로 병합되는 동작 변경 spec card"는 판정 시점에 정할 수 없다
* **위치**: §10 '실행 단위', §12, N6.3 '성능'
* **근거**: auditor가 card를 판정할 때는 그 card가 그 Phase의 마지막인지 알 수 없다. 뒤에 card가 더 들어오면 측정이 마지막 card에 없게 된다. 7b·7c 예산 게이트(DEC-34)가 어느 `perf.json`을 읽는지(조회 규칙)가 없다. perf 측정이 있는지 확인하는 검사도 없다. 한 구현자는 모든 동작 card에서, 다른 구현자는 마지막 card에서만 측정한다.
* **수정**: Phase 종료 전용 card(예: `<date>-phase<N>-close`, 동작 변경 없음)를 두고 거기서 측정하게 하거나, 모든 동작 변경 card에서 측정하고 게이트는 병합 순서상 최신을 읽는다고 정한다. N6.2 해당 Phase DoD의 확인 방법(파일 경로 규칙)도 적는다.

#### N-09 (S2) `ICPart.sub`의 정의("칸의 괄호 안에만 나오는 Phase")가 §9.4 토큰 규칙과 만나면 잘못된 원소를 만든다. `part`/`sub`를 TS7에 어떻게 대응시키는지도 없다
* **위치**: §9.2, §9.4 "`sub=True` 원소의 Phase는 칸의 괄호 안 문자열에 들어 있어야 한다"
* **근거**(`tok.py`로 실측): §9.4 정규식의 뒤쪽 조건 `(?![0-9A-Za-z.])`는 한글을 막지 않는다. 그래서 IC11 괄호 "(DEC-60 구현, 2레일)"·"(3레일 추가)"에서 `2`·`3`이, V1 괄호 "(0.5는 …)"에서 `0.5`가 Phase 토큰으로 잡힌다. 괄호 안에만 나오는 Phase를 `sub`로 두라는 문장대로 IC_TABLE을 만들면 IC11에 Phase 2·3의 `sub` 원소가 생긴다. §9.4 검사는 부분 문자열 포함만 보므로 이것을 통과시킨다. 또 TS7 xfail(§9.2)은 IC 단위 reason 형식만 있다. `part`가 여럿인 IC(IC11)와 `sub` 원소(IC7 정지 케이스), `from_phase` 원소의 만료가 어느 test·parametrize 케이스의 xfail이 되는지 정해지지 않았다.
* **수정**: `sub`는 "(… 는 <Phase>)" 같은 특정 문구로 한정하거나 계획 N4.1에 부속 Phase 열을 둔다. 토큰 정규식의 뒤쪽 조건을 "공백·문장부호·끝"만 허용하도록 좁힌다. `part`/`sub` → test 케이스 대응 규칙을 §9.2에 적거나 `10-test-separation`에 넘긴다고 명시한다.

### S3

#### N-10 (S3) §14 CC가 N3.12.3 spec card 단위(red 하나 = 계약 하나)가 아니다
* CC-3(IC_TABLE + V·IC·Phase 일치 test + TS7 생성), CC-4(§7 전부 + N3.14 일치 + DF-37 + exit code), CC-5, CC-7, CC-8은 각각 여러 계약이다. CC-3의 V·Phase 부분은 부트스트랩 상수를 대조하므로 base에서 이미 통과하고, red가 없다. N9.2-5·N9.4는 이 단위로 목록을 만들라고 한다.
* **수정**: §14 표를 "작업 묶음"으로 부르고 "발행 문서가 N3.12.3 단위로 나눈다"를 적거나, 지금 나눈다.

#### N-11 (S3) 광범위 except 개수가 AST 실측과 다르고, 같은 수가 두 곳에 있다(N9.4)
* AST 실측: `sizing_recipe.py`의 `except …ValueError…` 핸들러 **52**(설계·DF-37은 54), `except Exception` **7**(1797·1933·7852·8006·8350·11028·12591, 설계는 9. grep이 주석·print 줄 14401·8205를 셌다). stick_diagram 23/1, run_harness 1/2, topology_library 0/1은 맞다.
* §6.2는 엔진 모듈을 `assets/*.py` 전부로 정의한다. 그런데 DF-37·§7.3 목록에는 `audit_current_forced.py:157`, `topology_to_markdown.py:191`의 `except Exception`이 없다.
* 같은 개수가 DF-37과 §7.3에 둘 다 있다.
* **수정**: §7.3은 DF-37을 인용만 한다. 개수는 AST 기준으로 하나만 두거나 "CC-4가 AST로 센다"로 바꾼다. 범위 정의를 하나로 맞춘다.

#### N-12 (S3) "`eval_count`는 캐시 미스 수"가 부정확하다
* `sizing_recipe.py:_optimize_theta_slsqp._cached_evaluate`는 성공한 결과만 저장한다. 예외가 나면 저장 전에 전파되므로 같은 x의 실패 평가는 매번 다시 불린다. grid·`presolve_warm_start`·`repair_infeasible_baseline` 경로는 캐시를 거치지 않는다.
* **수정**: "`ev["evaluate"]` 호출 수(캐시 미스와 실패 재평가 포함)"로 정의한다.

#### N-13 (S3) `pythonhashseed` 필드 정의가 자기모순이다
* §10은 이 필드를 "명령 환경의 `PYTHONHASHSEED`"라고 하면서, 자식 프로세스에는 `1`을 강제한다. 기록값이 실제 실행값이 아니다.
* **수정**: 자식에 준 값(1)을 기록한다고 정한다.

#### N-14 (S3) 로더 검사의 잔여 구멍(새 케이스 실측)
* `auditor_run.time`: 로더 5의 `fromisoformat`은 "2026-09-17 09:30:00+09:00"(공백 구분자)와 "20260917T093000+0900"(basic 형식)을 받는다. RFC3339 date-time이 아니다. `rfc3339-validator`가 설치된 환경에서는 스키마가 거부한다(이 환경은 미설치). 설치 여부에 따라 게이트 결과가 달라진다.
* 중복 키(`"checks"`에 V1 FAIL 뒤 PASS): `json.loads`가 마지막 값을 취해 양쪽 모두 통과한다. 사람이 읽는 파일과 게이트가 읽는 값이 달라진다. `object_pairs_hook`으로 거부해야 한다.
* 그 밖에 통과하는 것: basis가 U+200B(폭 없는 공백)뿐인 기록, 개행이 든 `test_id`(해시 입력 구분자와 충돌), `approvals` 원소의 없는 날짜(로더 2는 `id`만 검사).
* UTF-8 BOM으로 시작하는 올바른 기록은 `JSONDecodeError`로 거부된다. 이 환경의 PowerShell `Out-File` 기본값이 BOM이다. 인코딩 규칙(UTF-8, BOM 없음)을 적어야 한다.
* 설계 §8.1 표는 `code_commit`을 "40자리 16진"(소문자 언급 없음)이라고 하고, 스키마는 소문자만 받는다. 표기를 맞춘다.

#### N-15 (S3) diff 해시 재현성과 승인 기록 머리 값 검증
* 이 저장소 git 설정에 `diff.astextplain.textconv`와 `core.autocrlf=true`가 있고, 한글 경로가 있다. 명령에 `--no-textconv`, `--src-prefix=a/ --dst-prefix=b/`, `--diff-algorithm=myers`, `--no-renames`, `-c core.quotepath=true`가 없다. 설정이 바뀌면 해시도 바뀐다.
* `id`·`date`·`target`(64자리 16진)·`diff_base/head`(40자리)의 형식 검사, `id` = 파일 이름 규칙이 머리 규칙에 없다.

#### N-16 (S3) §3.3·§14 소유 칸이 §3.2 규칙을 형식적으로만 지킨다
* '판정 표 상수' 행은 두 칸이 똑같이 "CC별(§14)"이다. 기계로 대조하면 "같은 주체" 위반이다.
* §14는 허용 이름 밖인 "오케스트레이터", "code-author / test-author", "사용자"를 쓴다.
* '승인 기록 양식'·'스키마 초안' 행은 구현 "사용자 + 오케스트레이터"와 판정 "사용자"가 **사용자**라는 주체를 공유한다. 실제 작성자는 오케스트레이터이니 구현 소유를 "오케스트레이터"로 적고, 허용 집합에 더한다(부트스트랩 한정).
* '승인 기록 양식'의 고정 수단 "공격 8"은 승인 기록이 **없는지**를 보는 공격이다. 양식 파싱을 검증하지 않는다.

#### N-17 (S3) IC5 이름 집합이 이 설계의 새 게이트를 덮지 않는다(게이트 사각)
* IC5 test는 `check_*`/`verify_*`/`validate_*`/`audit_*`만 본다. §5·§6.2가 `영역:` 줄을 요구하는 `load_json_checked`·`reject_legacy_names`(기존 `require_*`도)는 검사 대상이 아니다.
* **수정**: 이름을 바꾸거나 IC5 대상 집합을 넓히도록 계획 개정을 요청한다.

#### N-18 (S3) CC-4가 Phase 4에서 발생 지점 없는 클래스를 만든다(WP-01). raise 위치 규칙도 없다
* N3.14상 STRUCTURE_UNRESOLVED는 "6c 이후/7b 이후", SEAL_VIOLATION·NONCONVERGENT는 6b 봉인·순환 블록이다. Phase 4에서는 발생 지점이 없을 수 있다. DF-37 red("`StructureUnresolvedError`가 exit 2로")는 주입으로만 만들 수 있다. `normalized_margin`도 Phase 4 소비자가 불분명하다.
* 구조 유도(MOD3)가 `StructureUnresolvedError`를 raise하면 N3.10(MOD3 → MOD4 import 금지)을 어긴다.
* **수정**: "raise는 MOD4 이상에서만, MOD3는 status를 돌려준다"를 적는다. 클래스별 첫 raise Phase를 표로 두거나, 소비자 없는 클래스를 그 Phase로 미룬다.

#### N-19 (S3) N9.2-4: 이 문서 도구의 실패 경로가 N3.14와 exit code에 대응되지 않는다
* `failure_class="measurement_setup"`과 무동작 FAIL은 `FAILURE_CLASSES` 밖이고 exit code가 "비0"뿐이다. §10-4는 "`FAILURE_CLASSES` 조회, 없으면 예외 타입 이름"이라 두 규칙이 섞인다. 도구 exit code를 표로 정한다.

#### N-20 (S3) EL3 5분류가 v5.19로 늘어난 경로를 분류하지 못한다
* `workspaces/run_harness.py`(code-author, DF-35·DF-37 대상)는 소스·test·도구·데이터·문서 어디에도 없다.
* `.ai/verification/_schema.json`은 '문서' 분류인데 이제 code-author의 `Role: code` 커밋이 바꾼다.
* `tests/tools/ic_table.py`는 판정 입력인데 '도구' 분류라서 소스와 한 커밋에 바뀔 수 있다(§9.4 일치 test가 막으므로 위험은 낮다).
* **수정**: `05` design의 허용 조합표에 명시하도록 N3.12.4에 한 줄을 더한다.

#### N-21 (S3) §8.1·§9.4 비교 규칙의 잔여 모호성
* 로더 6 "basis에 그 도입 Phase가 적혀 있음": 부분 문자열로 보는지 §9.4 토큰으로 보는지 정해지지 않았다("1"은 "10" 안에 있다).
* §9.4에 반대 방향 검사가 없다. 칸에 '이후 매 Phase'가 없는데 `from_phase=True`인 원소, N6.1 행마다 토큰이 정확히 하나인지, `FAILURE_CLASSES[k].exc`가 N3.14 '예외' 열의 클래스 이름과 같은지를 보지 않는다(예: SEARCH_FAILED ↔ `NonconvergentError` 오배정이 통과한다).
* exit code 칸 "2(같은 분류)"와 "--"를 어떻게 파싱하는지도 없다.

#### N-22 (S3) 계획 안의 소소한 모순(v5.19가 건드린 줄)
* N3.12.3 spec card 필드는 v5.19에서 Phase를 더하면서도 "판정 유형(`red-green` 또는 `equivalence`)"을 그대로 두어 `test-only`가 빠져 있다.
* N6.2 `0(문서)`는 부트스트랩 전에 `_schema.json`이 있기를 요구한다. 그런데 N3.12.2 오케스트레이터 경로에는 `.ai/verification/**`가 없고, N3.12.6은 작성 시점을 ①로 둔다.
* N7.2 U-38 행은 작성자 측정 `.txt`를 '실측' 근거로 인용한다(N0.1: 보고 수치는 판정 기록에서만 인용).

#### N-23 (S3) 성능 측정의 `git status` 대조와 `--out` 위치의 순서가 없다
* auditor가 측정 대상 worktree 안(`.ai/verification/<id>/perf.json`)에 출력을 쓰면, 대조 전에 썼는지 뒤에 썼는지에 따라 결과가 `failed`/`ok`로 갈린다. "대조 뒤 쓰기" 또는 "`--out`은 측정 worktree 밖"을 적는다.

#### N-24 (S3) 무동작 판정의 잔여 모호성
* IC7 test는 한 worktree 안에서 돈다. base가 없는데 "`noop_proof`와 같은 함수를 부른다"가 무엇을 비교하는지 정해지지 않았다(발동 계수 부분만인지).
* 계약 test의 판정이 code-author 도구에 기대는 구조(WP-13 긴장)라는 점을 적어야 한다.
* 발동 계수 ID 목록이 비면 조건이 공허하게 참이 된다.
* 병합본을 어느 시드로 실행하는지 정해지지 않았다.

---

## 3. 작성자≠검증자와 "두 소유 칸이 달라야 한다" 행별 점검

| 표 | 행 | 구현 소유 | 판정 기준 소유 | 판정 |
|---|---|---|---|---|
| §3.3 | 이 문서 | 사용자 + 오케스트레이터 | 독립 검증 agent | 적합 |
| §3.3 | 판정 기록 스키마 초안 | 사용자 + 오케스트레이터(①) | 독립 검증 agent, 이후 사용자 | 이름은 다르지만 '사용자'가 겹친다(N-16). 게다가 N3.12.2 auditor glob 때문에 판정 대상인 auditor가 스키마를 쓸 수 있다(N-03) |
| §3.3 | 승인 기록 양식 | 사용자 + 오케스트레이터 | 사용자(0.5) | '사용자'가 겹친다. 고정 수단 '공격 8'은 이 양식과 무관하다(N-16) |
| §3.3 | 판정 표 상수 | CC별(§14) | CC별(§14) | **문자열이 같다**. §14로 풀면 행마다 다르다(N-16) |
| §3.3 | 계측 도구 | gmid-code-author | gmid-test-author | 적합. 단 IC7 계약 test가 code-author 도구로 판정한다(N-24) |
| §14 | CC-1 | 오케스트레이터 | 사용자(공격 15 로그) | 부트스트랩 예외로는 적합. 공격 시나리오도 ①에서 오케스트레이터가 쓰므로 판정의 독립성은 사용자 확인과 독립 검증 케이스(review21·이 검증)에만 기댄다. 이름 집합 밖 표기다 |
| §14 | CC-2 | 오케스트레이터 | 사용자 | 적합. 실제 대조 test는 CC-3의 test-author가 쓴다. 불일치를 찾아도 고치려면 게이트 변경 card가 필요하다(판정 기준 소유 칸과 실제 판정 주체가 다르다) |
| §14 | CC-3~CC-8 | code-author | test-author | 적합. CC-3에서 `IC_TABLE`(xfail 만료를 정하는 판정 입력)을 code-author가 쓴다. §9.4 일치 test(test-author)와 계획 대조가 약화를 막는다. xfail을 런타임에 표에서 생성하면 code-author의 표 수정이 곧 test 기준 변경이 되므로, 일치 test를 V1 필수 실행에 두어야 한다는 점을 적어야 한다 |

---

## 4. 코드 사실 대조(지시 4)

| 설계 주장 | 실측 | 판정 |
|---|---|---|
| `except ValueError`: sizing_recipe 54, stick_diagram 23, run_harness 1 | AST 핸들러 52 / 23 / 1(grep 줄 수는 54) | 부정확(N-11) |
| `except Exception`: sizing_recipe 9, stick_diagram 1, topology_library 1, run_harness 2 | AST 7 / 1 / 1 / 2. 그 밖에 audit_current_forced 1, topology_to_markdown 1 | 부정확(N-11) |
| 직접 `json.load(`: sizing_recipe 7, stick_diagram 12 | AST `json.load` 7 / **11**. 여기에 `json.loads` 3 / 1, design_report 1, topology_to_markdown 2 | 부정확·범위 누락(N-05) |
| `spec_fingerprint(spec)` 정본, 등급 R0 | `def spec_fingerprint(spec: dict) -> str` 존재(해상도 키 7개). 레지스트리 등급은 **R2**(§5) | 등급 틀림(N-04) |
| `_optimize_theta_slsqp` 안 캐시, `eval_count` = 캐시 미스 | `_eval_cache`/`_cached_evaluate` 존재. 예외는 저장하지 않는다 | 부분(N-12) |
| `run_harness.run`은 모든 예외를 잡고 0 종료 | 511행 `except Exception as e:` print + traceback, 반환 없음, `__main__`은 `run()` 뒤 종료 | 맞음 |
| `save_instance_json`이 `topology_ref`에 절대 경로 | 8966행 `"topology_ref": topology_json_path`(호출자는 `LIBRARY_DIR` 절대 경로) | 맞음 |
| `validate_no_legacy_vs_key`는 다른 필드를 읽은 뒤 호출 | 8518행. `synthesize_l_class_thetas`(except로 감쌈)·`validate_metric_units`·`materialize_input_offset_pairs` 뒤 | 맞음 |
| `InfeasibleSizingError` 레지스트리 목적지 MOD4 | 레지스트리 330행 `gmid_sizing_engine` | 맞음 |
| block-coordinate 루프 안 `except ValueError` | 11746행 `except ValueError as _fast_e:` | 맞음 |

---

## 5. 스키마 독립 측정(지시 5)

jsonschema 4.26.0, `Draft202012Validator(schema, format_checker=FormatChecker())`. 이 환경의 FormatChecker에는 `date-time` 검사기가 없다(`rfc3339_validator` 미설치). 작성자 스크립트와 review21 C-08 표에 없는 새 기록 30건을 돌렸다. 로더 2·3·4·5는 설계 문구대로 따로 구현해 대조했다.

| 케이스 | 스키마 | 설계 문구대로의 로더 | 설계 의도와 일치? |
|---|---|---|---|
| 정상 equivalence(명령 2개, `Z` 시간대) / 정상 test-only / 정상 red-green(test 2개) | 통과 | -- | 일치(오거부 0) |
| `checks`가 배열, equivalence에 `red` 동반, test-only에 `equivalence` 동반, `outputs_hash` 63자리, `equivalence.commands` 빈 배열, `auditor_run.commands` 빈 배열, `reproduced_numbers.name` 공백뿐, id 대문자 slug, `spec_card` 역슬래시, 기록 전체 `null`, verdict `n/a`, basis 개행뿐, 기록에 `$schema` 키, `code_commit` 대문자 | 전부 거부 | -- | 일치(스키마 담당) |
| `auditor_run.time` 시간대 없음 | 통과 | 거부(5) | 일치(로더 담당) |
| `auditor_run.time` 끝 개행 | 통과 | 거부(5) | 일치 |
| `spec_card` id ≠ `id` | 통과 | (로더 1 담당) | 일치 |
| **`value: 1e400` / `-1e400`** | 통과 | **통과(inf)** | **불일치**(N-02) |
| **time 공백 구분자 / basic 형식** | 통과 | **통과** | **불일치**(N-14, 환경 의존) |
| **JSON 중복 키(V1 FAIL→PASS)** | 통과 | **통과** | **불일치**(N-14) |
| basis U+200B뿐 / 개행 든 test_id / approvals 원소의 없는 날짜 | 통과 | 통과 | 막는 규칙 없음(N-14) |
| failure_hashes 두 원소가 같음(test_id는 다름) | 통과 | 통과 | 재실행 대조(V2)가 잡는다. 설계대로 |
| UTF-8 BOM 선두의 올바른 기록 | `json.loads` 실패 | 거부 | 인코딩 규칙 없음(N-14) |

N6.2 `0(문서)` DoD의 "스키마 밖 필드를 거부함"은 **충족**한다. 올바른 기록 3종은 모두 통과했고, 스키마가 맡은 거부 케이스 14건도 모두 거부했다. 불일치는 모두 로더 쪽 정의(§8.1, §6.2)에 있다.

---

## 6. §9.4 토큰화 실측(지시 6)

설계 문장만 보고 구현했다(괄호 중첩 삭제 + 설계 정규식, `tok.py`).

* **N4.1 담당 Phase**: IC1 {6b}, IC2 {6b}, IC3 {1}, IC4 {6c}, IC5 {1}, IC6 {6c}, IC7 {6a}, IC8 {6c}, IC9 {6b}, IC10 {6b}, IC11 {4, 6a}
* **N4.2 도입**: V1~V6 {1}, V7 {2}, V8 {4}, V9 {6b}, V10 {0.5}
* **N6.1 Phase**: `0` {}, `**0(문서)**` {}, 나머지 행은 순서대로 0.5, 1, 2, 3, 4, 5, 6a, 6b, 6c, 7a, 7b, 7c = `PHASE_ORDER`
* 설계의 예시 4개와 실측 주장("IC·V 전부 비지 않음, N6.1 빈 집합 행은 정확히 둘")은 **재현된다**.
* 그러나 N6.1 `0(문서)` 행이 7셀이다(머리 5셀). 셀 수를 검사하는 구현은 이 test를 FAIL로 만든다(N-01).
* 같은 정규식을 괄호 **안**에 쓰면 `2`·`3`(IC11)과 `0.5`(V1)가 잡힌다(N-09).

---

## 7. §10·§11: 두 구현자가 다르게 갈 수 있는 곳(지시 7)

1. Phase 4의 패치 지점과 import 바인딩(N-06). 가장 크다. 같은 명령이 다른 코드를 잰다.
2. 성능을 측정하는 card의 선택과 예산 게이트의 파일 조회(N-08)
3. `spec_digest`의 뜻(N-04). 목표가 다른 스펙이 같은 값을 낸다
4. `eval_count` 정의(N-12), `pythonhashseed` 기록값(N-13)
5. `--out` 쓰기와 `git status` 대조의 순서(N-23)
6. 무동작: 병합본 실행 시드, 빈 ID 목록, IC7 호출 방식(N-24)
7. 도구 실패의 exit code(N-19)

위 1~3만 고치면 두 구현이 같은 수치와 판정을 낸다. 4~7은 한 줄 규정으로 닫힌다.

---

## 8. N9.2 필수 절과 숨은 열린 질문(지시 8)

* 1 범위 §1, 2 인터페이스 §6~§11, 3 판정식 §12, 5 역할별 산출물 §14, 6 DoD §15, 7 착수 조건 §16, 8 열린 질문 §17이 모두 있다. 4 실패 경로는 N3.14 형식(§7)은 있지만, 이 문서 도구의 실패 경로 대응이 없다(N-19).
* §17 "없음"은 사실과 다르다. 아래는 설계가 정하지 않았고 다른 문서로 넘긴다는 표시도 없는 항목이다:
  * `where`에 없는 JSON 종류(N-05)
  * Phase 4 계측 인터페이스(N-06)
  * 해시의 정규 타입 이름(N-07)
  * 성능 측정 card(N-08)
  * `part`/`sub` → xfail 대응(N-09)
  * CC의 spec card 분할(N-10)
  * 클래스별 첫 raise Phase(N-18)

  N9.2-8에 따라 각각 설계에서 닫거나, 담당 design 문서로 넘긴다고 명시해야 한다.

---

## 9. 집계와 판정

| 구분 | 건수 | ID |
|---|---|---|
| C-01~C-24 닫힘 | 17 | C-01~06, 08, 10, 11, 13, 15~19, 21, 23 |
| C-01~C-24 부분 | 7 | C-07, C-09, C-12, C-14, C-20, C-22, C-24 |
| C-01~C-24 안 닫힘 | 0 | -- |
| 새 S1 | 0 | -- |
| 새 S2 | 9 | N-01 ~ N-09 |
| 새 S3 | 15 | N-10 ~ N-24 |

**판정: 수정 후 승인.** review21의 S1 3건은 모두 닫혔고 새 S1은 없다. S2 9건은 다음처럼 모두 국소 수정으로 닫힌다.

* 계획 표 한 행 이동: N-01
* 로더 규칙 한 줄: N-02
* 경로 glob 한정: N-03
* 지문 필드 재정의: N-04
* `where` 종류 추가 또는 AST 규칙 한정: N-05
* 계측 인터페이스 명시: N-06
* 해시 함수 하나로 통일: N-07
* 측정 card 규칙: N-08
* `sub` 정의와 정규식 한정: N-09

재작성은 필요 없다. S2 수정 뒤 §17을 갱신하고 재검증한다. 이번에는 N-01·N-02·N-06 반영 여부만 보면 된다.
