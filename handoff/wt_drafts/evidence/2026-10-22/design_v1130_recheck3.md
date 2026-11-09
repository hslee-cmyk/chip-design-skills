# design v1.13.0 다섯째 커밋 + 계획 v6.34.1 넷째 커밋 재검증 3 (2026-10-22)

- 대상 design: `wt/design-v634` 커밋 `128dfc41`(부모 `fa3d0a27`). 줄 수는 그대로다(40 = 2125, 41 = 1992, 42 = 361).
- 대상 계획: `wt/plan-v6341` 커밋 `37d6b7e8`(부모 `ec9f6db3`).
- 엔진 근거: `wt/integ-it12` `6afe4758`의 코드를 직접 열어 확인했다.
- 작업은 읽기 전용이고, git은 `git -C`만 썼다.

## 점수: 88 / 100

recheck2의 S·N과 계획 재검증에서 design으로 넘긴 N-2~N-5는 모두 해소됐다. `graph.ss_circuit` 신설은 graph 원칙에 맞고, 엔진 사실관계 대조에서도 문제가 없었다. 남은 것은 S 둘과 N 셋이다.
- S-A: metrics 블록이 import할 writer 상수가 `sizing.__all__`에 없다.
- S-B: '용량만 결측이면 AC metric만 정의 불능'이라는 문언이 실제 동작과 다르다(B77 때문에 DC metric도 정의 불능).

## 1. 앞 지적 해소

| 지적 | 반영 | 판정 |
|---|---|---|
| recheck2 S-1 결측 fail-open | 41:739. 저항이 결측이면 `graph.ss_nodal` = `Undefined`이고, `icm_config`는 config None과 `passive_value_undeclared`. 용량만 결측이면 노달 계를 세운다 | 해소(문언 문제는 S-B) |
| recheck2 S-2 값 생산자 셋 | 41:739. writer 블록 하나가 `graph.ss_circuit`을 쓰고, `metrics_ss`·`metrics_aux`·`ss_nodal`은 READS로 읽는다 | 해소 |
| recheck2 S-3 계획 먼저 | 계획 `ec9f6db3`·`37d6b7e8`이 먼저 섰고, design은 그 문언을 따른다. '원래 취지와 다름(범위 확대), 사용자 승인 대상' 표시 있음 | 해소 |
| recheck2 N-1 | 41:812 (j-ⅰ) AST 계수 = 손 기대, (j-ⅱ) 항목별 `g_ops` = 손 기대 | 해소 |
| recheck2 N-2 | 41:812 (l-ⅰ) `graph.ss_circuit` 직접 비교, (l-ⅱ) base 대비 `value_fp` 비트 동일 | 해소 |
| recheck2 N-3 | 41:812 (l-ⅲ) READS 단언 | 해소 |
| 계획 재검증 N-2 이름 충돌 | 41:739에 0건이라 적음 | 해소(2.2에서 실측 확인) |
| 계획 재검증 N-3 G-10 | 41:739, L11 (c) | 해소(2.5) |
| 계획 재검증 N-4 `CODE_PASSIVE_MISSING` 한 자리 | 41:739·797 | 해소(2.3) |
| 계획 재검증 N-5 정의 불능 꼴 | 41:739(`Undefined` 값, `metrics_aux`의 조기 반환) | 해소(2.4) |

## 2. 새 결정 확인 (엔진 코드 직접 확인)

### 2.1 블록·writer·등록·호출 순서
- 블록 `ss_circuit_field`가 writer 이름 `ss_circuit`으로 `SS_WRITES`에 등록된다.
- `ss_evaluate.py:101`이 `ss_dev`, `:104`가 `metrics_ss`(조건 없이 늘 호출)다. 새 블록을 그 사이에 넣으므로 순서가 맞고, 늘 실행된다.
- 예외는 `:113-115`의 `CANDIDATE_FAILURE_CLASSES`가 그대로 잡아 부분 스냅샷을 붙인다. **맞음.**

### 2.2 이름 충돌
`ss_circuit_field`, `SS_CIRCUIT_WRITER`, `("graph", "ss_circuit")`을 엔진 전체(tests 포함)에서 grep한 결과 0건이다. 문자열 `"ss_circuit"`은 두 곳에만 있고, 둘 다 기존 함수 이름이다(writer 이름이 아님).
- `metrics/__init__.py:337` `__all__`의 함수 이름
- `_module_map.py:773` 진입점 이름

writer 이름과 함수 이름이 같은 문자열이지만 쓰이는 이름공간이 다르다. design 40 표는 `ss_nodal`(writer = 필드 이름)을 선례로 든다. **충돌 0을 확인했다.**

### 2.3 저항 판정 상수와 `CODE_PASSIVE_MISSING`
- `ss_circuit.py`는 `resistor_kind = LOOP_CUT_KINDS[0]`로 저항과 용량을 가른다. 결측 목록 `missing`은 `kind in LOOP_CUT_KINDS`인 수동소자에서만 나온다. 그래서 `ss_nodal`이 같은 `LOOP_CUT_KINDS[0]`로 고르면 같은 상수, 같은 규칙이다. **맞음.**
  - (N) 술어 '저항인가'가 두 자리(`ss_circuit` 함수, `ss_nodal`)에 따로 쓰인다. 상수는 하나지만 판정식은 둘이다. 값 칸을 늘리지 않으려면 지금 꼴이 최소안이다. 다른 길은 `SsCircuit.missing`을 kind별로 나누는 것인데, 이는 타입을 바꾸므로 수용한다.
- `CODE_PASSIVE_MISSING = "passive_value_undeclared"`는 지금 `metrics_aux.py:52`와 `ss_metrics.py:71` 두 곳에 같은 값으로 있다. tests에는 이 상수나 문자열을 직접 쓰는 곳이 없다(grep 0). 그래서 `ss_circuit.py` 한 자리로 옮겨도 test 영향이 없다.
- import 층: `ss_metrics`(6)·`metrics_aux`(5)·`ss_nodal`(3)·`icm_config`(3)가 `ss_circuit`(1)을 import하므로 아래층 방향이다. **맞음.**

### 2.4 정의 불능의 꼴
- `Undefined`(`mna_types.py:41-53`)는 이렇게 되어 있다.
  - frozen dataclass이고, category는 `UNDEFINED_CATEGORIES`로 검사한다(`"definitional"`이 그 안에 있다).
  - detail은 정렬된 tuple이다.
  - `fp_of`의 dataclass 규칙으로 지문을 낼 수 있다.
  - 새 타입도, 새 칸도, 새 code도 없다. **기존 타입만 쓴다.**
- `NodalSystem.__canonical__`은 `Undefined` 갈래에서는 쓰이지 않는다(값 타입이 다르다). 지문은 타입 이름까지 포함하므로 두 갈래가 섞일 수 없다. **맞음.**
- `icm_config`는 config None과 `IcmConfig.undefined`로 기존 M7 경로를 탄다. **맞음.**
- (N) `graph.ss_nodal`의 값 타입이 `NodalSystem | Undefined` 합이 된다. metrics CONTRACT 소유표 행에 이 합을 적고, 읽는 쪽 셋의 처리를 한 줄로 적어 둘 것.
  - `icm_config`는 갈래로 처리한다.
  - `metrics_aux`는 조기 반환으로 이 값에 닿지 않는다.
  - 세 자리 이전 함수는 받으면 같은 code를 낸다.

### 2.5 G-10 계수
- DC 계수(`size_and_seal`, 같은 θ parent 재평가에서 reuse 12·graft 1)는 ss 블록을 포함하지 않으므로 그대로다.
- ss 단계는 `test_ss_evaluate.py:717-728`이 블록마다 (0, 1, 0)과 `all computes == 0`을 단언한다. 새 블록 `ss_circuit`도 child 파생 때 지워졌다가 같은 입력 버전이면 graft된다. 따라서 그 test는 계속 통과하고, graft 수는 1만큼 는다. **맞음.**

### 2.6 `StructureUnresolvedError` 발생 블록 이름이 바뀌는 영향
- 지원 밖 원소 정지(`ss_element_kind`)를 단언하는 test는 순수 함수 test(`test_ss_circuit.py:118`)뿐이고, 블록 이름은 보지 않는다.
- `test_ss_metrics.py:664`의 정지는 `ds_self_swap_zero_current`다. 다른 단계라 이 변경과 무관하다.
- `StructureUnresolvedError`는 `register_failure` 대상이 아니다. 대상은 `InfeasibleSizingError`·`SchemaRejectedError`뿐이다(`compute_block.py:160-161`). 그래서 재연 색인도 바뀌지 않는다.
- 엔진 소스에서 실패 블록 이름을 읽는 소비자는 grep 범위(`core/failure_partial.py`·`search/*`)에 없었다. **영향 없음.** 그 밖은 미확인이다.
- (N) 다만 `test_ss_metrics.py:35-36`은 블록 `metrics_ss`를 스냅샷에 직접 부른다. 바뀐 뒤에는 `graph.ss_circuit`이 먼저 있어야 하므로, 그 파일의 픽스처 갱신이 test 작성 주체 몫이 된다. design 4.7-6의 test 영향 목록(`test_s2_values.py`만 있음)에 이 파일을 더할 것.

## 3. 원칙 점검

- **graph 규칙 1~7**: 통과.
  - `graph.ss_circuit`은 writer 하나다.
  - 조립 사본 둘은 지우고 `ss_circuit(` 호출 하나·`SsCircuit(` 생성 하나만 남긴다(L10 (c) grep 단언).
  - 새 cache는 없다. 스냅샷 파생 keep 밖이고 S3 graft로 복귀한다.
  - 정의 불능은 필드 값 하나에 남는다.
  - `ss_values`·`device_orbit`은 READS 열 읽기다.
- **fail-closed**: 저항 결측은 노달 계와 측정 구성 모두 정의 불능이다. 통과.
- **DC/AC 분리**: 판정 자리(`ss_nodal`)는 맞다. 다만 metric 수준에서 실제로 분리되지 않는다(S-B).
- **새 code 0**: 통과(`passive_value_undeclared`는 기존 값).
- **구조 규칙**:
  - A: `ss_circuit.py`에서 `ss_circuit_field`가 `ss_circuit`을 참조하므로 진입점은 등록 블록 하나다. 블록은 파일당 최대 하나다.
  - B: `_` 이름 import 없음.
  - C: `ss_circuit.py`가 `gmid_engine.sizing`에서 `SS_CIRCUIT_WRITER`를 import해야 하는데 `__all__`에 넣는 일이 빠졌다(S-A).
  - 층: `ss_circuit` 1, `ss_nodal`·`icm_config` 3, `metrics_aux` 5, `ss_metrics` 6, `ss_evaluate` 7. 맞음.
- **oracle 독립**: 통과.
  - L10 (j-ⅰ)(j-ⅱ)는 손 기대다.
  - (l-ⅰ)은 손 회로와 직접 비교하고, (l-ⅱ)는 base 대비 비트 동일이다.
  - 결측 toy 둘은 기대 code와 상태를 손으로 정한다.

## 4. 계획 37d6b7e8 문언

- 셋 다 앞 커밋들과 모순이 없다.
  - S-1(DC 전도 소자 결측만 fail-closed)
  - N-1(grep 대상 `ss_circuit(`·`SsCircuit(`)
  - N-6((12)(a) 중복 문장을 하나로 합침. 뜻이 같다)
- 계획 1518 "용량만 결측이면 노달 계·측정 구성은 서고 AC metric만 정의 불능"은 S-B와 같은 문제를 안고 있다.
- 사실 근거 `ss_circuit.py:46-49`(missing에 저항과 커패시터가 함께 든다)는 엔진 코드와 맞다.

## 5. 지적

### G
없음.

### S
- **S-A. writer 상수를 `sizing.__all__`에 공개해야 한다 (규칙 C, 착수 장애)**
  - 위치: 41:739·760·797(4.7-6 `__all__` 목록).
  - 근거: metrics 블록은 writer 상수를 `from gmid_engine.sizing import …`로 받는다. 선례는 `metrics_aux.py:24` `METRICS_AUX_WRITER`이고, `sizing/__init__.py:186·189·238`처럼 writer 상수마다 `__all__`에 있다. 그런데 design의 `__all__` 목록은 `Circuit`·`saturation_window`·`INPUT_STATUS_*` 셋뿐이다. 새 writer 상수 셋이 빠졌다.
    - `SS_CIRCUIT_WRITER`: 이번 커밋에서 새로 생긴 것
    - `SS_NODAL_WRITER`·`ICM_CONFIG_WRITER`: 첫 커밋부터 빠져 있었고, 앞 검증들에서 내가 놓쳤다
  - 이대로면 구현자가 규칙 C에 걸려 멈추거나, 문자열 사본을 쓰게 된다.
  - 수정안: 4.7-4·4.7-6의 `__all__` 목록에 세 상수를 더한다.
  - 원칙: 정본 상수 하나, 규칙 C.
- **S-B. '용량만 결측 → AC metric만 정의 불능'이 실제로는 성립하지 않는다**
  - 위치: 41:739, 812 L10 (c)(ⅱ). 계획 601·1518도 같은 문언이다.
  - 근거:
    - `metrics_aux`는 `ss.missing`이 비어 있지 않으면 묶음 전체를 정의 불능으로 낸다(`metrics_aux.py:164-165`). design도 이를 B77로 범위 밖에 둔다.
    - 그런데 ICMR 세 metric(DC 양)도 IT-2d 뒤 `metrics_aux`가 낸다.
    - 그래서 용량만 결측인 점에서는 `node.dc_window_cfg`가 서도, 그 유일한 metric 소비자가 버린다. 결과적으로 세 metric도 정의 불능이다.
    - 문언("AC metric만")과 동작이 다르다. cfg 항목은 그 점에서 소비자가 없는 값이 된다.
  - 수정안(원칙 순):
    - (가) 문언을 사실대로 고친다. "DC 판정 자리(`ss_nodal`·`icm_config`)는 서지만, 그 점의 metric은 `metrics_aux` 기존 조기 반환(B77)으로 모두 정의 불능이다. B77이 고쳐질 때 DC metric이 살아난다." toy (ⅱ)의 단언은 `graph.ss_nodal`·cfg 존재까지로 한정한다. '원래 취지와 다름(작음)'으로 표시한다. 계획 문언도 같은 정정이 필요하다.
    - (나) 대안: B77을 이 card로 당겨 `metrics_aux` 조기 반환을 AC 의존 metric으로 좁힌다. 범위 확대이므로 계획 먼저.
  - 권고는 (가)다. 사실 정정이라 범위가 그대로다.
  - 원칙: 문언과 실측의 일치, '만들면 배선'(소비자 없는 값을 명시).

### N
- **N-A.** `graph.ss_nodal` 값 타입이 `NodalSystem | Undefined`라는 것과, 읽는 쪽 셋의 처리를 metrics CONTRACT 소유표 행에 적는다(2.4).
- **N-B.** `test_ss_metrics.py:35-36`의 블록 직접 호출 픽스처가 `graph.ss_circuit`을 먼저 써야 한다. 이를 4.7-6 test 영향 목록에 더한다(2.6).
- **N-C.** '저항인가' 술어가 두 자리(`ss_circuit` 함수, `ss_nodal`)에 따로 있다. 상수는 하나이므로 수용하되, L10 (c) 결측 toy가 두 자리의 일치를 함께 보이도록 한다. 예: 저항과 용량이 함께 결측인 toy를 하나 더해, 저항 갈래가 먼저 잡히는지 본다(2.3).

## 6. 미확인
- 실패 블록 이름을 읽는 소비자: `core/failure_partial.py`·`search/*` 밖(예: report·pipeline)은 grep하지 않았다.
- 계획 history H1 'v6.34.1 셋째·넷째 커밋' 행 본문.
