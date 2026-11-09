# 계획 v6.34.1 재검증 (plan/v6341: be056f61·d1b4c788·ec9f6db3, base master 821c9bf2)

- 2026-10-22, 읽기 전용 검증 agent. 쓴 파일은 이 파일 하나다.
- 확인한 것
  - 커밋별 diff(`git -C … show`)
  - `ec9f6db3`의 plan 전문
  - 엔진 integ-it12 `6afe4758`를 직접 열었다: `metrics/ss_metrics.py`, `metrics/metrics_aux.py`, `metrics/ss_types.py`, `metrics/records.py`, `metrics/ss_circuit.py`, `core/immutability.py`, `sizing/seal.py`, `sizing/seal_conduction.py`, `metrics/ss_evaluate.py`

## 점수: 88 / 100

- 필수(G) 0, 권고(S) 1, 참고(N) 6.
- 셋째 커밋의 사실 인용과 작성자의 충돌 점검 다섯 항목은 독립적으로 다시 확인해도 맞다.
- 원칙 점검도 통과한다: graph 단일 정본, 새 code 이름 0, '원래 취지와 다름(범위 확대)' 표시.
- 감점은 두 가지다.
  - fail-closed 범위가 DC/AC 분리와 어긋날 수 있다. 용량 값만 없어도 DC 양(ICMR)이 정의 불능이 된다(S-1).
  - (10)(c)의 측정 대상 문구가 조금 모호하다(N-1).

## 1. 사실 확인 (6afe4758 직접 확인)

| 주장 | 결과 |
|---|---|
| 조립 사본 ① `metrics/ss_metrics.py:379-394` | 맞다. `metrics_ss` 블록(377행 데코레이터) 안 379~393행이 열을 읽고, 394행이 `ss_circuit(...)`을 호출한다. |
| 조립 사본 ② `metrics/metrics_aux.py:92-105` | 맞다. `_ss_of` 함수 안 같은 열·같은 정준 순서 식, 105행이 `ss_circuit(...)`을 호출한다. `metrics_aux`(159행)가 이 함수를 부른다. |
| 비test 엔진 소스의 `ss_circuit(` 호출 | 위 두 곳뿐이다(grep). 사본은 실제로 둘이다. |
| `SsCircuit`이 graph 필드 값이 될 수 있다 | 맞다. `ss_types.py:40` frozen dataclass이고, 칸은 tuple과 `SmallSignalCircuit`(frozen, tuple 칸)이다. 원소 `MosSmallSignal`·`Resistor`·`Capacitor`도 frozen이고 int·float·str 칸이다. `core/immutability.py` 허용 규칙(스칼라·tuple·frozenset·frozen dataclass 재귀)을 모두 만족한다. |
| 두 블록의 `passive_value_undeclared` 처리 | 맞다. `ss_metrics.py:401-403`(`ss.missing` → `_undefined(r, CODE_PASSIVE_MISSING, …)`), `metrics_aux.py:164-166`(`_fail(…)`)이다. 둘 다 category `definitional`이고, 상수 `CODE_PASSIVE_MISSING = "passive_value_undeclared"`가 두 모듈(`ss_metrics.py:71`·`metrics_aux.py:52`)에 따로 정의돼 있다(N-4). |
| `SsCircuit.missing`에 용량도 들어간다 | 맞다. `ss_circuit.py:46-49`가 저항·커패시터 모두 값이 없으면 `missing`에 넣는다. 이 사실이 S-1의 근거다. |

## 2. 근본원칙 점검

| 원칙 | 판정 | 근거 |
|---|---|---|
| graph 규칙 1 (writer 하나, 둘째 생산자 금지) | 통과 | writer 블록 하나, 두 사본 삭제, `ss_nodal`도 조립하지 않음. (10)(c)가 grep으로 단언한다. |
| 규칙 2 (재사용 = graph reuse·S3 graft) | 통과 | 봉인 뒤 ss 층 블록이라 S3 graft로 재사용한다. 새 cache·memo는 없다. |
| 규칙 3 (같은 정의는 필드 하나) | 통과 | 같은 열·같은 식으로 만드는 같은 양을 필드 하나로 합친다. |
| 규칙 4 (참조 전달) | 통과 | READS로 읽는다. extras 사본은 없다. |
| 규칙 5 (스냅샷 파생) | 통과 | 아래 3절 (i) |
| 규칙 6·7 | 통과 | 정본 자리를 정한 뒤 계획을 먼저 고쳤고, 충돌 점검을 기록했다. |
| fail-closed | 통과, 단 범위 문제 | `missing`이면 `ss_nodal`은 정의 불능, `icm_config`는 `passive_value_undeclared`로 fail-open을 막는다. 다만 범위가 넓다(S-1). |
| 새 code 이름 0 | 통과 | 기존 어휘 `passive_value_undeclared`만 쓴다. |
| DEC-103 계산 틀 | 통과 | 계산 틀은 바뀌지 않는다(회로 객체 출처만 바뀜). |
| 원래 취지와 다름 표시 | 통과 | Status, N3.3, N3.8, N6.6 범위 1, (10)(c), H1에 모두 '범위 확대, 사용자 승인 대상'이 있다. |

## 3. 작성자 충돌 점검 다섯 항목 -- 독립 재확인

- **(i) keep과 S3 graft**: 맞다.
  - N3.3(456행)에서 keep은 base writer ∪ 봉인 4 호출 목록(커널 블록 ∪ 봉인 항목 블록)이다. 나머지 writer 필드는 파생 때 지우고, 다시 불리면 같은 입력 버전 값이 S3 색인 graft로 돌아온다.
  - 같은 행의 '실패 평가의 부분 스냅샷' 문장도 'ss writer는 파생 keep 밖이라 파생 때 지워지므로'라고 적었다.
  - 새 ss 층 writer도 이 문언 그대로 처리된다. 충돌 없음.
- **(ii) 봉인 4**: 맞다. 봉인 4는 커널 스냅샷의 writer coverage이고(`seal.py` 머리 2), ss 층은 `ss_evaluate`가 `SealedSnapshot`을 받은 뒤에만 돈다(`ss_evaluate.py:83`). 대상 밖이다.
- **(iii) G-10 계수**: 맞다.
  - 계획 본문을 grep해 보니 ss 층 블록 수를 박은 reuse·graft 계수 문언이 없다.
  - (11)(c)는 'ss 재평가가 S3 graft로 computes 증분 0'이라 새 블록이 생겨도 성립한다.
  - 다만 1521행 '착수 실측: search tests 가운데 ss 블록 `reuse` 계수를 단언하는 test'와 design·test 쪽 정확 계수는 블록이 하나 늘면 바뀐다. design 후속 목록에 넣을 것(N-3).
- **(iv) graph 밖 목록(셋)**: 맞다. LUT memo, S3 기록·2단계 판정 기록, 그리고 셋째 항목뿐이고 소신호 회로는 없다.
- **(v) N3.8 기존 조립 자리 셋**: 맞다. `offset_analysis:69`·`offset_systematic:46`·`block_residual:73`은 `metrics_aux` 안에서 `ss`를 받는다. `ss` 출처가 `graph.ss_circuit`로 바뀔 뿐이고, 그 셋이 `graph.ss_nodal`을 READS로 읽는다는 문언과 충돌하지 않는다.

## 4. 완료 조건 (10)(c) 새 단언 -- 판정할 수 있다(조건부)

- 단언: writer 1곳, READS 단언 셋, '비test 엔진 소스에서 `SsCircuit`을 만드는 자리 = 그 writer 하나', G-10 재계산 0, missing toy → `ss_nodal` 정의 불능·`icm_config` `passive_value_undeclared`.
- 측정 대상 '만드는 자리'가 두 가지로 읽힌다(N-1).
  - `SsCircuit(` 생성자는 지금도 `ss_circuit.py:60` 순수 함수 안 한 곳뿐이다.
  - `ss_circuit(` 호출 자리는 지금 두 곳이다.
  - grep 패턴을 '`ss_circuit(` 호출 자리 = writer 블록 하나, `SsCircuit(` 생성 = `ss_circuit` 함수 하나'로 적어야 판정이 갈리지 않는다.
- '`ss_nodal` 정의 불능(노달 계 없음)'의 관측 꼴(필드 값 None / 항목 없음 / Undefined)은 design 몫이다. red 판정이 가능하도록 design에서 정해야 한다(N-5).

## 5. 앞 두 커밋 정정 -- 유지, 모순 없음

- **(12)(a)**: 셋째 커밋에도 남아 있다.
  - 'tol 미정 갈래 = 측정 구성 쪽 대상 없음 -- tol_V 미정 행은 undefined로 판정되어 봉인되지 않는다(`DcEvaluation(sealed=None)`; 거부와 undefined는 다른 상태)'
  - 근거 세 줄을 코드로 확인했다: `seal_conduction.py:43-46`의 eps None, `seal.py` 머리 4 'undefined → sealed=None', `ss_evaluate.py:83` SealedSnapshot만 받음.
  - '봉인 9가 거부'는 Status의 정정 경위 인용과 1945행(ID ≤ 0 fail, 다른 사안)에만 남았다.
  - 같은 이유 문장이 두 번 이어지는 중복이 있다(바이너리 치환의 흔적, N-6).
- **(8)(a)**: 유지된다. oracle 입력은 다음과 같다.
  - `node.dc_v`, `device.dc_op` VGS·VDS·VSB·L·w_key, `device.dc_tol_v`
  - VDsat·tol_VDsat = test가 LUT 원시 `vdsat`·`tol_vdsat_table`을 직접 부름
  - 허용치 = `dc_tol_v` 손계산, cfg `tol_v` 사용 금지
- 셋째 커밋과의 관계: (8)(a)는 `conductance_matrix`를 부르지 않는 손 조립이다. 새 `graph.ss_circuit`을 oracle 입력으로 읽으라는 문언도 없어 독립성이 유지된다.

## 6. 발견 사항

### G: 0건

### S (승인 전 반영 권고)

- **S-1 `SsCircuit.missing` fail-closed 범위 -- 용량만 없어도 DC 양(ICMR 측정 구성)이 정의 불능**
  - 위치: N3.8 '엔진 쪽 계산 자리'의 fail-closed 문장, N6.6 범위 1, 완료 조건 (10)(c)
  - 근거
    - `missing`에는 값 없는 커패시터도 들어간다(`ss_circuit.py:46-49`).
    - `graph.ss_nodal` G는 용량을 넣지 않는다. `conductance_matrix`가 용량을 넣지 않고(DC 극한 개방), 측정 구성 창·T_p도 DC 양이다.
    - 그런데 v6.34.1 문언은 `missing`이 비지 않기만 하면 `ss_nodal` 정의 불능, `icm_config` `passive_value_undeclared`로 둔다.
    - 그래서 보상 커패시터처럼 DC에 영향이 없는 소자의 값이 없을 때도 ICMR이 정의 불능이 된다. AC 쪽 결측이 DC 판정을 막는 결합이다(DC/AC 분리 근본원칙, '물리 정합 최우선').
    - 반대로 저항이 빠지면 G가 틀리므로 fail-closed가 맞다.
  - 수정 제안
    - '`missing` 가운데 DC 전도 소자(저항 -- 용량 제외)가 있으면 `ss_nodal` 정의 불능·`icm_config` `passive_value_undeclared`'로 좁힌다.
    - 용량만 없으면 노달 계를 세우고, AC metric(`metrics_ss`)만 기존대로 정의 불능으로 둔다.
    - 판정 자료는 `SsCircuit`의 기존 칸(`resistors`·`capacitors`는 스탬프된 이름)과 S1 `device.kind`(READS)다. 새 칸·새 code는 없다.
    - (10)(c) toy를 둘로 나눈다: 저항 결측(→ 정의 불능), 용량만 결측(→ 노달 계 있음, 창 정의됨, 정의 불능이면 red).
  - 원칙 점검: DC/AC 분리, 물리 정합, fail-closed(DC에 영향 있는 결측만 막음), graph 단일 정본(새 필드·생산자 없음), 새 code 0 → 맞음
  - 판정 주체: fail-closed 범위를 넓게 둘지는 작성자 기본안이고 원칙상으로는 좁히는 쪽이다. 넓게 유지하면 그 이유를 적어야 한다.
  - 미확인: 운영 9+4 회로에서 용량만 결측인 봉인점이 실제로 나오는지. `ss_evaluate.py` 머리 27행은 '결정 대기 등'이면 생긴다고 적었다.

### N (참고)

- **N-1** (10)(c) grep 대상을 명시한다: '`ss_circuit(` 호출 자리 = `graph.ss_circuit` writer 블록 하나, `SsCircuit(` 생성 = `ss_circuit` 함수 하나(tests 제외)'. → 맞음(판정 가능성)
- **N-2** 이름 충돌 주의: 새 필드 `graph.ss_circuit`, 기존 순수 함수 `ss_circuit`(`metrics/ss_circuit.py`), 계획 문구 'metrics `ss_circuit.py` 계열'이 겹친다. writer 블록·상수 이름은 design에서 기존 함수·모듈·test glob과 충돌하지 않게 정한다(card 규칙: 새 이름은 test glob 충돌 grep). → 맞음
- **N-3** design 41과 test에서 ss 층 블록 수에 기댄 정확 계수(1521행 착수 실측이 가리키는 ss 블록 reuse 계수 test, design L11 계수)는 블록 하나가 늘면 바뀐다. design 개정 목록과 card 재동결에 넣는다. 계획 문언은 고칠 필요 없다. → 맞음(G-10)
- **N-4** `CODE_PASSIVE_MISSING`이 두 모듈에 같은 값으로 따로 정의돼 있다. 새 writer가 생기면 이 code를 한 자리(writer 모듈 또는 공용 상수)에서 import하도록 같은 변경에서 정리할 것을 권한다. 사본 상수 금지 취지다. → 맞음(단일 정의 자리, 선택 사항)
- **N-5** '`ss_nodal` 정의 불능'의 graph 필드 꼴(None·항목 없음·Undefined)과 그때 `metrics_aux` 기존 세 자리(이미 `ss.missing`이면 조기 반환)의 동작을 design에서 명시한다. → 맞음(fail-closed 관측 가능성)
- **N-6** (12)(a) '-- tol_V 미정 행은 undefined로 판정되어 그 점은 봉인되지 않는다(…)'가 바로 앞 근거 문장과 내용이 중복된다. 둘째 커밋 바이너리 치환의 흔적이다. 한 문장으로 줄일 것을 권한다(의미 변화 없음). → 맞음

## 7. 미확인

1. 운영 13회로 봉인점에서 `SsCircuit.missing` 발생 여부와 그 종류(저항/용량) -- S-1의 실제 영향.
2. design 41 v1.13.x에서 고칠 자리 전수 목록(writer 블록 이름·층, `ss_nodal` READS, 실패 꼴, 계수).
