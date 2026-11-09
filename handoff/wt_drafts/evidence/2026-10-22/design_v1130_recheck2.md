# design v1.13.0 셋째·넷째 커밋과 계획 v6.34.1 R2 재검증 (2026-10-22)

## 대상과 조건

- design: `wt/design-v634` 커밋 `63853954`(셋째)와 `fa3d0a27`(넷째). 앞 판은 `34970ea8`.
- 계획: `wt/plan-v6341` 커밋 `d1b4c788`.
- 줄 수는 바뀌지 않았다: 40 = 2125, 41 = 1992, 42 = 361.
- 엔진 대조 기준: `wt/integ-it12` `6afe4758`.
- 읽기 전용으로 진행했고, git은 `git -C`로만 실행했다.

## 점수: 86 / 100

S-R1과 R1~R5는 실제로 해소됐다. 넷째 커밋으로 조립 코드의 사본 둘이 하나(`ss_circuit_of`)로 모였고, 층 배치와 구조 규칙 A도 맞다.

감점 사유는 셋이다.

- `ss_nodal`이 수동소자 값 누락(`SsCircuit.missing`)을 처리하지 않아 fail-open 구멍이 있다(S-1).
- 같은 `SsCircuit`이 평가 한 번에 블록 셋에서 각각 다시 만들어진다. graph 단일 정본 규칙 1에 걸린다(S-2).
- 넷째 커밋으로 범위가 넓어졌는데, 이를 계획보다 design에 먼저 적었다(S-3).

---

## 1. 앞 재검증 지적의 해소

| 지적 | 반영 위치 | 판정 |
|---|---|---|
| S-R1 L10 (j) 식 변경 감지 | 41:812 (j): 스탬프 값 식 안의 수치 `BinOp`만 센다(문자열 피연산자 제외). 손 기대(MOS 2, 저항 1)와 다르면 red | **해소**. 식만 바꾼 경우를 잡는다: 항을 더하면 계수 3 ≠ 2로 red, 식을 helper로 빼내면 계수가 줄어 red. 연산자만 바꾸면(+ → −) 계수가 같고 c_s도 그대로라서 통과하는 것이 맞다. 남은 문구 문제는 N-1 |
| R1 '연산 수 > 0' | 41:812 | 해소 |
| R2 'undefined → 봉인되지 않음' | design 41:17·688·737·814, 계획 d1b4c788 Status·(12)(a) | 해소. 아래 3절에서 문언까지 같음을 확인했다 |
| R3 metrics CONTRACT `StampSet` 행 | 41:797 | 해소 |
| R4 metrics 층 | 41:797 | 해소. 2절 (2)에서 확인 |
| R5 죽은 갈래 test 없음 | 41:688·737·814 | 해소 |
| N-3 확인 기록 | 41:760: 오케스트레이터 판단 (가), 재수출은 실사용이 아님, 백로그 B76 | 해소 |

## 2. 넷째 커밋 (`ss_circuit_of`)

### (1) 사본 둘 삭제

엔진에서 확인한 사실:
- `ss_metrics.py:379-394`의 `metrics_ss` 인라인 조립과 `metrics_aux.py:92-105`의 `_ss_of`가 같은 줄로 되어 있다.
- `ss_circuit(` 호출은 이 두 곳에만 있다(test 제외).

design은 둘을 지우고 `ss_circuit_of` 하나만 둔다(41:739, L10 (l)의 `git grep` 단언: 호출 자리 하나, `def _ss_of` 0). **맞다.**

### (2) `ss_nodal` 층 3

`_module_map.py:120-132`의 metrics 층은 다음과 같다:
- 층 0: `aux_types` 등
- 층 1: `ss_circuit` 등
- 층 2: `_helpers_nodal`·`_helpers_view` 등
- 층 3: `offset_analysis` 등
- 층 5: `metrics_aux`
- 층 6: `ss_metrics`
- 층 7: `ss_evaluate`

`ss_nodal`이 import하는 가장 높은 층은 층 2이므로 `ss_nodal`은 층 3이다. 41:741의 고정 집합에 `_helpers_view.view_system`을 써도 층 2라 결과가 같다.

다른 조건도 맞다:
- `icm_config`도 층 3이지만 둘은 서로 import하지 않는다.
- `ss_evaluate`(층 7), `metrics_aux`(층 5), `ss_metrics`(층 6)는 모두 앞 층을 import한다.

**맞다.**

### (3) 진입점 `ss_circuit` → `ss_circuit_of` (규칙 A, README 39행)

규칙 A는 같은 파일의 다른 최상위 문장이 이름으로 참조하지 않는 공개 정의를 진입점으로 센다.
- `ss_circuit_of`가 `ss_circuit`을 부르므로 `ss_circuit`은 진입점에서 빠진다.
- 진입점 개념은 `ss_circuit_of` 하나가 된다.
- `_unsupported`는 비공개이고, `BRANCH_SS_ELEMENT`는 대입이라 세지 않는다.

`ss_circuit`은 그대로 공개로 남는다(`metrics/__init__.py:160`, `test_ss_circuit.py:41`). 규칙 A는 공개를 금지하지 않으므로 **맞다.** 모듈 지도의 `ss_circuit.py` 행(`_module_map.py:773`)과 CONTRACT 12.0 표를 고칠 자리도 41:797에 적혀 있다.

### (4) 반환을 `SsCircuit` 하나로

- `ss_values`(`device.ss_dev`)와 `device_orbit`(`device.dc_colour`)은 계산값이 아니라 READS 열을 dict로 바꾼 것뿐이다.
- 호출부가 각자 읽어도 둘째 생산자가 아니다.
- `ss_nodal`에 쓰지 않는 반환값을 만들지 않는 것도 '만들면 배선' 원칙에 맞다.

**맞다.**

### (5) 동치 test oracle (L10 (l))

- 기대값은 test 작성자가 손으로 적은 정준 순서다. 피검 함수 출력으로 만들지 않으므로 **독립적이다.**
- 다만 `metrics_ss`·`metrics_aux` 안의 회로는 밖에서 직접 볼 수 없다. 관측은 다음 둘뿐이다(N-2):
  - `NodalSystem.nodes`(그리고 `ss_circuit_of` 반환)를 기대값과 비교한다.
  - 두 블록의 결과가 base와 비트 단위로 같은지(변성 관계)를 본다.

## 3. 계획 (12)(a) 문언 대조

| 계획 d1b4c788 (12)(a) | design |
|---|---|
| tol_V 미정 행은 undefined로 판정되어 그 점은 봉인되지 않는다(`DcEvaluation(sealed=None)`; 거부(fail)와 undefined는 엔진에서 다른 상태다) | 688 '미정 행이 undefined라서 봉인되지 않아(`sealed=None` -- 엔진에서 undefined는 fail(거부)과 다른 상태)', 737 '…봉인되지 않아(`sealed=None`) … 대상 없음, test 없음', 814 '…봉인되지 않아(`sealed=None` -- fail과 다른 상태) … 죽은 갈래라 cfg test 없음' |

뜻이 같다. '커널 A6 b `unsettled` 단언 유지'도 양쪽이 같다.

## 4. graph 단일 정본 규칙 1~7 점검

1. **writer 하나·둘째 생산자 금지 → S-2.**
   - `SsCircuit`은 graph 필드가 아니다.
   - 평가 한 번에 `ss_nodal`, `metrics_aux`, `metrics_ss` 셋이 같은 스냅샷에서 각자 `ss_circuit_of`를 불러 같은 값을 세 번 만든다.
   - 코드 정의는 하나로 모였지만 값의 생산자는 셋이다. 그중 `ss_nodal` 자리는 IT-2c가 새로 더한다(옛 사본 둘은 그 전부터 있던 부채).
2. **cache**: 새 cache·memo·사본은 없다(통과).
3. **같은 정의 한 필드**: 새 필드가 없다(통과).
4. **참조 전달**: 해당 없음.
5. **스냅샷 파생**: `ss_nodal`은 봉인 뒤 writer이고 keep 밖이다(41:753). 바뀐 것은 없다.
6. **정본 자리 없으면 멈춤**: S-2가 해당하며 원칙 충돌로 올린다.
7. **검증 단계 점검**: 이 문서가 그 점검이다.

## 5. design ↔ 계획 gap

- 계획 v6.34.1의 결정과 완료 조건((0)~(12), (8)(a) oracle, (12)(a), U-101 닫힘)은 design에 다르지 않게 들어 있다.
- 넷째 커밋의 범위 확대(IT-2c가 `ss_metrics.py`·`metrics_aux.py`의 조립부 정리까지 맡음)는 계획에 없다. 계획 N6.6의 IT-2c 범위·소비자 표에도 없다.
- design이 '원래 취지와 다름(작음)'으로 표시하기는 했다(41:17·834). 그래도 S-3이다.

---

## 6. 지적

### G

없다.

### S

**S-1. `ss_nodal`의 수동소자 값 누락 처리가 없다 (fail-open).**
- 위치: 41:739(`graph.ss_nodal`), 4.7-3b.
- 근거:
  - `SsCircuit.missing`이 비어 있지 않으면 값 없는 수동소자가 스탬프되지 않아 회로가 불완전하다(`ss_types.py:41-53` docstring '불완전, metric은 정의 불가').
  - `metrics_aux`는 이미 이 경우 모든 요청을 `CODE_PASSIVE_MISSING`으로 실패시킨다(`metrics_aux.py:164-165`).
  - 그러나 design의 `ss_nodal`은 이 갈래를 정하지 않았다. 그대로 두면 저항이 빠진 G로 `NodalSystem`을 쓰게 된다. 그러면 `icm_config`가 그 G로 T_p, KCL 창, 선언 되먹임 망을 재서 `"measured"`로 쓴다(조용한 오답).
  - 첫 커밋부터 있던 공백이다. 앞 두 번의 검증에서 놓쳤다.
- 수정안:
  - `ss_nodal`은 회로가 불완전하면 그 사실을 `NodalSystem`에 담는다. 예: 칸 `missing`, 그리고 그때 `factor`는 None.
  - `icm_config`는 그 경우 `config` None과 정의 불능 code를 쓴다. code는 기존 `CODE_PASSIVE_MISSING`과 같은 어휘를 재사용하고, 새 code는 만들지 않는다.
  - `NodalSystem.__canonical__`에도 그 칸을 넣는다.
  - test는 '값 없는 수동소자 toy → cfg 항목 없음·세 metric 정의 불능'을 단언한다.
- 원칙: fail-closed, 조용한 대체 금지. 같은 사실을 생산자 하나(`ss_nodal`)가 담고 소비자들은 읽기만 한다.

**S-2. 같은 `SsCircuit`을 블록 셋이 각자 다시 만든다 (graph 규칙 1). 원칙 충돌로 올린다.**
- 위치: 41:739, 40:1884.
- 근거:
  - 계산값은 graph 필드로 두고 다른 곳은 READS로 읽어야 한다(CLAUDE.md graph 규칙 1).
  - 넷째 커밋은 코드 사본은 없앴지만, 평가 한 번에 같은 값을 만드는 자리를 둘에서 셋으로 늘린다.
  - 비용은 O(N)으로 작다. 그래도 규칙은 비용이 아니라 생산자 수를 본다.
- 선택지:
  - (가) **권고.** 봉인 뒤 맨 먼저 도는 `ss_nodal`(또는 새 블록 하나)이 `graph.ss_circuit`(값 `SsCircuit`, frozen dataclass라 `fp_of`로 지문을 낼 수 있음)을 쓰고, `metrics_aux`·`metrics_ss`·`icm_config`는 READS로 읽는다. `SsCircuit.missing`도 그 필드에 실려 S-1이 함께 풀린다.
  - (나) 지금처럼 함수 하나에 호출 셋을 둔다. 이 경우 '같은 값 재계산'을 승인 예외로 계획 N3.3에 올려 사용자 결정을 받아야 한다.
- 이유: (가)는 READS 변경을 동반하는 범위 확대라 계획부터 고쳐야 한다(규칙 6, '계획과 다르면 계획부터').

**S-3. 넷째 커밋의 범위 확대가 계획보다 먼저 design에 들어갔다.**
- 근거:
  - 계획 N6.6의 IT-2c 범위와 소비자 표에는 `ss_metrics.py`·`metrics_aux.py` 조립부 정리가 없다.
  - design은 이를 '원래 취지와 다름(작음)'으로 표시해 design 승인에 묶었다. 메모리 규칙 '계획과 다르면 계획부터 고친다 -- design에 다른 점을 묶어 승인받지 말 것'에 어긋난다.
- 수정안:
  - 계획 v6.34.1에 셋째 커밋으로 IT-2c 범위 한 줄을 더하고, 검증과 승인을 받는다. S-2의 결정을 함께 반영한다.
  - 그 뒤 design 문언을 맞춘다.

### N

- **N-1.** 41:812 (j)의 'AST 계수 ≠ `g_ops`의 연산 수이면 red'는 비교 기준이 모호하다.
  - MOS는 `total = gm + gmb + gds`를 한 번 계산해(AST 2) 두 항목에 각각 c_s = 2로 매긴다. 그래서 `g_ops`의 합(4)과 비교하면 늘 red다.
  - 수정안: 'AST 계수 = 손 기대(MOS 2, 저항 1)'와 '`g_ops` 항목값 = 손 기대(항목별)' 두 단언으로 나눈다. AST 계수와 `g_ops`를 직접 비교하려면 '`g_ops`의 최댓값'으로 명시한다.
- **N-2.** L10 (l)의 '세 블록이 쓰는 회로가 기대와 같음'을 무엇으로 관측하는지 명시해야 한다. `NodalSystem.nodes`와 `ss_circuit_of` 반환을 직접 비교하고, `metrics_ss`·`metrics_aux`는 base 대비 결과 비트 동일로 확인한다. 내부 회로를 꺼내는 주입은 R2 범위 밖이다.
- **N-3.** `ss_circuit_of`가 각 호출 블록의 투영에서 읽는 열 열 개는 `metrics_ss`·`metrics_aux`·`ss_nodal` 세 블록 모두의 READS에 있어야 한다.
  - `metrics_aux`의 READS에는 모두 있다(`metrics_aux.py:42-46`).
  - `metrics_ss`의 READS는 이번에 재지 않았다(**미확인**). 41:797에 '세 블록 READS ⊇ 조립 열' 단언을 하나 더할 것을 권고한다.

## 7. 원칙 적합 요약

- 상수 발명 금지, 회로 이름 code 금지, 구조 규칙 A·B·C, 모듈 지도 층: 적합.
- 작성자 ≠ 검증자(L10 (j)·(l)의 oracle 독립): 적합. 문구 정리는 N-1·N-2.
- fail-closed: S-1이 남았다.
- graph 단일 정본: S-2가 남았다.
- 계획 먼저: S-3이 남았다.

## 8. 미확인

- `metrics_ss`의 READS 목록 전체(N-3).
- `icm_config`가 실제로 `_helpers_view`·`_helpers_nodal` 밖의 metrics 파일을 import하는지(층 3 판정은 design 문언 기준).
- 계획 history H1 'v6.34.1 둘째 커밋' 행 본문.
