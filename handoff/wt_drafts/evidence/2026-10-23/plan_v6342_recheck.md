# 계획 v6.34.2 재검증 (plan/v6342 `de200594`, 부모 `50cf0a19`)

- 2026-10-23, 읽기 전용 검증 agent. 쓴 파일은 이 파일 하나다.
- 확인한 것
  - `de200594`의 plan·history 전문
  - design 41 v1.13.0 742·812행, design 40 v1.13.0 555행(같은 커밋에서 읽음)
  - integ-it12 `09c3dce2`의 tests를 `git -C … grep`과 `show`로 확인

## 점수: 93 / 100 -- 새 G·S 없음

## 1. 앞 지적의 해소

| 지적 | 판정 | 근거 |
|---|---|---|
| S-1 | 해소 | N3.8 (i)과 N6.6 IT-2d (2)는 이제 '`metrics_aux`는 다시 판정하지 않고 `graph.ss_nodal`이 `Undefined`인지와 `SsCircuit.missing` ≠ ∅만 READS로 읽는다'로 적혀 있다. 결측 판정의 생산자는 `ss_nodal` 하나이고, (13)(c)에 '`metrics_aux` 호출 0'과 READS 단언이 있다. 새 필드는 0이다. |
| S-2 | 해소(표시 방식) | 작성자 해석을 유지하면서 '원래 취지와 다름(작음), 사용자 확인 대상'을 붙였다. N3.8, IT-2d (2), (13)(a), H1에 있다. 앞 검증의 대안 (나)에 해당한다. 해석의 근거로 든 'O-112 권고의 예시가 `block_residual`·슬루'는 권고 원문이 user_decisions에 없어 확인하지 못했다. |
| N-1 | 해소 | 대조 실행을 '같은 θ·같은 봉인점에서 커패시터 값만 선언'으로 하고 비교를 비트 동일로 적었다. |
| N-2 | 해소 | AST 대상을 결측 판정 함수와 그것이 부르는 함수로 한정했다. 기존 metric 이름 분기는 대상 밖이다. |
| N-3 | 해소 | metric 이름으로 단언하고, VB-1이 먼저 병합되면 `offset_sys_mv`는 red 대상에서 뺀다. |
| N-4·N-5 | 해소 | IT-2d '변경 종류'에 `ff_gm_ratio` 표기와 변화표 원인 칸 분리가 들어갔다. |
| N-6 | 대체로 해소, 누락 1 | 아래 4절 |

## 2. 작성자가 좁힌 곳 -- 맞다(graph 규칙 1 부합)

- `ss_circuit`과 `ss_nodal`이 술어를 부르는 목적이 다르다.
  - `ss_circuit`(design 41:812 (ⅳ), 40:555 `ss_circuit.is_dc_conducting_passive(kind)`)은 소자 하나의 kind를 보고 저항 스탬프와 용량 스탬프를 가른다. 산출은 `SsCircuit`의 구조(`resistors`·`capacitors`)다.
  - `ss_nodal`은 `missing` 집합 전체를 보고 'DC 전도 소자의 결측이 있는가'를 판정한다. 산출은 `graph.ss_nodal`의 `NodalSystem` 또는 `Undefined`다.
- 두 산출은 다른 값이다. 같은 판정값(결측 판정)의 생산자는 `ss_nodal` 하나다.
- 술어는 kind 문자열에 대한 정의 함수다. graph 계산값이 아니라 정의 한 자리(`def` 1곳)이므로 두 자리에서 불러도 규칙 1을 어기지 않는다.
- (13)(c) '호출 자리 = `ss_circuit`·`ss_nodal` 둘뿐'은 design 41:812 (ⅳ) '부르는 자리 = `ss_circuit`·`ss_nodal`'과 같다.

## 3. READS 사실 -- 맞다

- design 41:742: '세 함수는 `metrics_aux` 블록 안에서 불린다 … `metrics_aux` READS에 `("graph", "ss_nodal")`를 더한다'.
- design 41:812 (c): '`icm_config`·`metrics_aux` READS에 `("graph", "ss_nodal")`'.
- design 40:555: `graph.ss_nodal` 값 타입이 `NodalSystem | Undefined`이고, 저항 결측이면 `Undefined("ss_nodal", "passive_value_undeclared", …)`이다. 같은 줄에 `graph.ss_circuit` 읽는 쪽이 `metrics_ss`·`metrics_aux`·`ss_nodal`로 적혀 있다.
- 따라서 IT-2d가 READS를 더할 일은 없다.

## 4. N-6 grep 재확인

- 계획에 적힌 것은 모두 맞다.
  - `tests/metrics/test_registry.py:44-51`
  - `tests/authoring/conftest.py:105-112`(소비 `test_pending_metrics.py:64`·`:131-135`, `test_catalog.py:47-49`)
  - `tests/metrics/test_catalog.py:52-55`
- **누락 두 곳**(N-a): `tests/metrics/test_pending_metrics.py`의 두 test가 영역 리터럴을 직접 단언하는데 영향 목록에 없다. metric 이름이 parametrize 목록에 있어 이름과 영역이 같은 줄에 없기 때문에 grep에서 빠진 것으로 보인다.
  - `:76-79` `test_large_signal_metrics_have_no_view`: `swing_out_v`·`icmr_v`·`icm_margin_v`의 영역 `"ls"`
  - `:82-86` `test_offset_metrics_transfer_view`: offset 셋의 영역 `"ss"`
  - 둘 다 relabel로 깨진다.
- 참고: `test_pending_metrics.py:149`(`MetricSignature("db", "ss")`)는 읽기 전용 확인용 대입이라 영향이 없다.

## 5. 새 원칙 위반

없음. 점검한 항목은 graph 정본(생산자 하나, 새 필드 0), fail-closed, DC/AC, 새 code 0, 계획 먼저다.

## N (참고)

- **N-a** IT-2d 영향 목록에 `tests/metrics/test_pending_metrics.py:76-79`·`:82-86`을 더한다. → 맞음
- **N-b** N3.8 (i)의 '`graph.ss_nodal`이 `Undefined`인지'를 '`Undefined`이고 code가 `passive_value_undeclared`인지'로 적으면, 나중에 `ss_nodal`의 다른 정의 불능 사유(예: 특이)가 생겨도 DC metric에 결측 code를 잘못 붙이지 않는다. 다른 사유라면 그 사유를 전파한다. 지금 design 40:555의 `Undefined`는 그 하나뿐이라 현재 결함은 아니다. → 맞음(fail-closed, code 정확성)
