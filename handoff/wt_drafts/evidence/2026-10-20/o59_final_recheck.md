# O-59 마지막 좁은 재확인 (2026-10-20)

검증자: 독립 agent(작성자 아님). 읽기 전용이었고 `git -C`·show·diff만 썼다.
대상:
- gb `124e5063` → `61ee9eab`
- oracle `13a26fee`(변경 없음)
- headroom `a44387cd`, graph-consumption `813a31ed`, offset-trim `738c25c3`(셋 모두 master `2e707d5d` 대비)

## 판정: **수정 필요 (한 자리)**

graph-consumption v0.13 N3.9 '스냅샷 파생 규칙과 필드 수명'(plan 500행)은 R1 정정 **전** writer 집합(`PLAN_WRITERS`)을 풀어 옮겨 적었다. gb 61ee9eab 정의와 어긋나는 사본이다(G1, Major). 이 한 자리를 고치면 다섯 브랜치 모두 병합할 수 있다. 나머지는 닫혔다.

## 1. R1·R2·R4 닫힘 (gb 61ee9eab)

| 항목 | 판정 | 근거 |
|---|---|---|
| R1 | 닫힘 | 421·494 남길 writer = `_CONTEXT_WRITERS`(`S1_WRITERS` ∪ `PLAN_WRITERS`, 정본 `E/search/search_context.py:44` 인용, 사본 목록 금지) ∪ 호출 블록. 1480 착수 실측에 `lift_s1`(`kernel_context.py:81`, 정의 `E/sizing/s2_lift.py:17`)의 writer 귀속 확인 추가. 1486 (11)(a)에 'S1·계획 필드는 child에 남음(지우면 red)' 추가. 실측: `s2_lift.py:17` = `def lift_s1`, :18이 `S1_WRITERS` 덮음을 검사함. '취지 변경 아님(집합 정밀화)' 표기는 맞음(O-59 (2) 뜻 그대로) |
| R2 | 닫힘 | 429·579 모두 'N3.8 창 필드의 네 필드 인용'으로 줄임(정의 한 자리) |
| R4 | 닫힘 | 567(슬루 ICMR 끝), 1477(front), 1575(DE-1 슬루 방향 전류), 1670에 '확정 기록 `status = final`만 읽음, 잠정 값 읽지 않음 -- oracle N3.9 인용' |
| O-59 번호 | 닫힘 | gb 안 'O-59 (3)'은 DV-12만 가리킴(DV-13 = (4)로 정정 223·1575; 318에 'DV-12 = oracle 몫'). oracle 433·492의 'O-59 (3)'은 DV-12 뜻이라 맞음 |

**1670행 위치**: 내용(oracle 행: `oracle_swing.py` ICMR servo, 슬루 `.tran`, `offset_sys_mv`)은 계획이 'DE-1 후속 정정 표 oracle 행'(317 O-51 행 인용)이라 부르는 그 표가 맞다. 그런데 표가 놓인 곳은 `### N6.12 card LI-1` 머리(1650) 아래 1662 '관련 계획 후속 정정(v6.18 …)'이다. N6.8 DE-1(1550~1613) 안이 아니다. 이번 diff가 만든 문제는 아니고 master부터 있던 배치다(Info, I1). 그 표에 'DE-1 후속 정정 표' 머리를 달거나 N6.8로 옮기면 인용이 찾아진다. 이 문제는 병합을 막지 않는다.

## 2. 세 후속 정정의 인용 정합

| 계획 | 판정 | 확인 |
|---|---|---|
| headroom v0.7.8 | 정합 | 네 창 필드(59)는 '정의는 상위 한 자리, 인용만'. `sat_threshold` 소비자 등록(331): 측정 구성 판정 창 포화 경계 행 + `triode` 경계 판정 여유 VDsat − VDS − tol_VDsat ≥ 0, 훑기 점 셀(O-46 (2)), 봉인 7 같은 기준. 행·필드 생산은 상위 IT-2·DE-1이고 이 계획은 소비자 등록만(사본 금지). 이름 정정 331·584. T-1은 gb N3.8 문언과 같음 |
| graph-consumption v0.13 | **G1 하나 제외 정합** | 347 V_id,0 = DEC-23 인용, 칸·필드 없음. 새 필드 행 둘(측정 구성 판정 창, ss 층 `nodal_factor`): writer 하나, READS 네 자리, 세 자리 이전 = IT-2, graph 밖 캐시·모듈 memo 금지, ss graft 집계. gb 566·1477·1486과 같음. **500행은 G1** |
| offset-trim v0.6.1 | 정합 | 148·311·330 V_id,0 = DEC-23 '이동의 기준점' 인용만 |

**G1 (Major)**: graph-consumption plan 500행에 세 군데가 옛 문언 그대로다.
- "parent → child 파생 때 `PLAN_WRITERS`와 그 평가가 부르는 블록의 필드만 남고"
- "봉인 4가 '모든 필드의 writer ∈ 호출 블록 ∪ `PLAN_WRITERS`'를 단언"
- "(또는 writer가 `PLAN_WRITERS`인지)"

gb 61ee9eab 421·494(`_CONTEXT_WRITERS` ∪ 호출 블록)와 다르다. 이 문언대로 소비 확인을 하면 S1 필드 reader를 거부 대상으로 잘못 분류한다. 원인은 '인용만'이라면서 규칙을 풀어 적은 데 있다(사본).

최소 수정: 세 구절의 `PLAN_WRITERS`를 `_CONTEXT_WRITERS`(`S1_WRITERS` ∪ `PLAN_WRITERS`, gb N3.3 인용)로 바꾼다. 더 나은 방법은 규칙 본문을 지우고 "gb N3.3 '스냅샷 파생 규칙'이 남기는 필드" 인용만 두는 것이다.

## 3. offset-trim V_id*(T) 기준점 = 같은 V_id,0: 원칙에 맞음

V_id,0은 DEC-23에서 spec 입력 DC 선언의 여기 방향 좌표다. 선언 값이라 온도 조건과 무관하다. V_id*(T)는 같은 `offset_sys_mv` `.dc`를 온도 조건에서 돌린 양이다(O-53 B3). 그래서 같은 정의, 같은 기준점이 단일 정본 귀결이다. 새 규칙이나 상수도 없다. 'servo 해는 기준점이 아니다'도 DEC-23과 같다. '오케스트레이터 해석, 새 결정 아님' 표기는 적절하다.

예외가 될 수 있는 경우가 하나 있다. spec이 온도별 입력 DC를 선언할 수 있다면 기준점도 온도별 선언값이어야 한다. 지금 spec에 그런 칸이 있는지는 확인하지 않았다. 있으면 같은 DEC-23 식을 그 점 선언값에 적용하면 되므로 규칙은 바뀌지 않는다.

## 4. gc 소비자 문언

gc 측정 구성 판정 창 행의 '커널 ICMR 선언 제약 판정과 커널 metric(커널 metric은 상위 DE-1 전 한정 -- N6.6 범위 2)'은 gb N3.8 566 '커널 ICMR 선언 제약 판정·커널 metric(커널 metric은 DE-1 전 한정 -- N6.6 범위 2)'과 같다. 일치한다.

## 5. 새 모순·상수·사본·graph 밖 캐시

- 새 상수 없음. graph 밖 캐시 없음(gc가 모듈 memo 금지를 명시).
- 사본: G1 하나(옛 정의를 풀어 적은 사본).
- 모순: G1 외 없음.

## 6. 병합 순서와 해시 맞춤

순서 gb → oracle → hc/gc/ot는 맞다. 정의 소유가 gb이고, oracle은 gb를 인용하며, 셋은 둘 다를 인용한다. hc/gc/ot 사이에는 서로 인용이 없어 순서가 무관하다. G1은 gc 병합 전에 고친다.

병합 뒤 해시 맞춤 목록('병합 뒤 맞춤' 표기 자리):
- oracle-portability: 18·122(gb 인용), 416·421·432·434(gb N3.8·DEC-23 인용). **432의 옛 `plan/gb-v619` `81fc49a7` 223행 인용**도 같이 고친다
- headroom-chain: 24·59·83·331(gb v6.21 인용), history 0.7.8 행
- graph-consumption: 15·347·새 필드 두 행·500(gb v6.21·oracle v0.6.11 인용), history 0.13 행
- offset-trim: 17·148·311·330(gb DEC-23 인용), history 0.6.1 행
- gain-budget: oracle N3.9 '범위 판정' 인용 자리(567·1477·1575·1670)와 headroom HC-S 인용(566). oracle·hc 병합 뒤 맞춤

## 확인하지 못한 것

- gb·hc·gc·ot history 신규 행 문언 전수.
- spec에 온도별 입력 DC 선언 칸이 있는지(3절 예외).
- gc N3.2a 기존 행들과 새 두 행의 표 형식 정합(열 수 등).
