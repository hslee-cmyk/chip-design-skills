# 재검증 4 (마지막 확인): design `7ff10ccd` + 계획 `7f1900a2` (2026-10-22)

읽기 전용으로 확인했고, git은 `git -C`만 썼다. 엔진 근거는 `wt/integ-it12` `6afe4758`에서 확인했다.

## 점수: 95 / 100

새로 생긴 G·S는 **없음**.

## 1. 앞 지적 해소 (모두 해소)

recheck3 지적:
- **S-A**: writer 상수 셋을 `sizing.__all__`에 넣었다(41:760·797, 40:1881).
- **S-B**: 용량만 결측인 경우의 문언을 사실대로 고쳤다. DC 판정 자리는 서지만 metric은 모두 정의 불능(B77)이고, '원래 취지와 다름(작음)'으로 표시했다. toy (ⅱ)는 `NodalSystem`과 cfg 존재까지만 단언한다(41:739·812).
- **N-A**: 소유표에 값 타입 `NodalSystem | Undefined`과 소비자 처리를 적었다(41:797, 40:555).
- **N-B**: `test_ss_metrics.py:35-36`을 test 영향 목록에 넣었다.
- **N-C**: 저항 술어를 하나로 모았고, 저항·용량이 함께 결측인 toy (ⅲ)과 grep 단언 (ⅳ)를 더했다.

gap 분석(`design_v1130_vs_plan_v6341_gap.md`) 지적:
- **S-1**: S-B와 같은 건이다. 해소.
- **N-1**: L12 (a)의 전제를 `k_max` toy에만 건다. 해소.
- **N-2**: U-101 이동 범위를 '위임 범위 안, 원래 취지와 다름 아님'으로 적었다. 해소.
- **N-3**: grep에서 `def` 줄을 뺀다. 해소.
- **N-4**: detail 키를 `"elements"`로 바꿨다. 엔진의 `ss_metrics.py:403`·`metrics_aux.py:165`와 같은 키다. 해소.
- **N-5**: 술어 하나로 모았다. 해소.
- **N-6**: 4.7-8 (9′)에 실패 블록 이름 변화를 적었다. 해소.
- N-7(B75)은 백로그로 유지한다.

## 2. 새 술어 `is_dc_conducting_passive`

- **import 방향과 층**:
  - `DC_CONDUCTING_PASSIVE_KINDS = ("resistor",)`(`authoring/dc_edges.py:11`)는 `authoring.__all__`에 공개돼 있다(`__init__.py:6·108`).
  - metrics(5)가 authoring(2)를 import하는 것은 아래층 방향이다.
  - 선례가 있다: graph의 `composite_diode`·`loops`·`view_analysis` 등 다섯 곳이 같은 상수를 같은 방식으로 import한다.
  - `ss_circuit.py`는 metrics 층 1에 그대로 남는다(패키지 import는 패키지 안 층에 영향이 없다).
  - **맞음.**
- **동작 동일**:
  - `LOOP_CUT_KINDS = ("resistor", "capacitor")`(`records.py:185`)이므로 `LOOP_CUT_KINDS[0] == "resistor"`다.
  - `ss_circuit` 안의 그 비교는 이미 `kind in LOOP_CUT_KINDS` 갈래 안에 있다. 그래서 `kind in ("resistor",)`로 바꿔도 결과가 같다.
  - 나중에 authoring 상수가 늘어나도 그 갈래 조건에 막혀 용량 판정은 바뀌지 않는다.
  - **같음.**
- **이름 충돌**: `is_dc_conducting_passive`를 엔진 전체(tests 포함)에서 grep한 결과 0건이다.
- **구조 규칙 A**:
  - `ss_circuit.py`의 공개 정의는 `ss_circuit`·`is_dc_conducting_passive`·`ss_circuit_field` 셋이다.
  - 술어는 `ss_circuit`이 참조하고, `ss_circuit`은 `ss_circuit_field`가 참조한다. 그래서 진입점은 등록 블록 하나다.
  - `ss_nodal`이 술어를 같은 패키지에서 import하는 것은 규칙 B(`_` 이름 아님)에 맞다.
  - **맞음.**
- **정본**: 상수 정본은 authoring 하나이고, 술어는 그 위의 한 줄짜리라 둘째 정의가 아니다.
  - (참고, 지적 아님) 레지스트리 §2에 술어 행을 넣으면 graph 쪽의 인라인 `in DC_CONDUCTING_PASSIVE_KINDS`와 관계가 분명해진다.

## 3. 계획·design 문언 대조

계획 `7f1900a2`의 601·1518·1528과 design 41:739·812, 40:555, 42:229는 같은 뜻이다. 넷 모두 같은 표현을 쓴다.
- 용량만 결측이면 DC 판정 자리(노달 계·측정 구성)는 선다.
- 그 점의 metric은 `metrics_aux`·`metrics_ss`가 결측 전체를 막아 모두 정의 불능이다(B77 범위 밖).
- 이것은 원래 취지와 다르다(작음).
- toy (ⅱ)는 `NodalSystem`과 cfg 존재까지만 단언하고, metric 결과는 단언하지 않는다.

어긋나는 곳은 없다.

## 4. 새 원칙 위반

**없음.**
- graph 단일 정본: 새 필드·cache·사본이 없다. 술어는 정본 상수 위의 함수 하나다.
- fail-closed: 저항 결측 갈래는 그대로다.
- DC/AC 분리: 판정 자리는 맞고, metric 수준의 제약은 B77로 사실대로 표시했다.
- 새 code: 0.
- 구조 규칙 A·B·C와 층: 맞다.

## 미확인

- 계획 history H1 'v6.34.1 다섯째 커밋' 행 본문.
