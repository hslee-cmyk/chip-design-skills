# O-59 계획 개정 재검증 (2026-10-20)

검증자: 독립 agent(작성자 아님), 읽기 전용(`git -C`·show·diff만 사용).
대상: gb `plan/gb-v621` `bb545b92` → `124e5063`(c1df0737·124e5063), oracle `plan/oracle-v0611` `ade94756` → `13a26fee`.
행 번호는 각 head 판 기준이다. 코드는 master `2e707d5d` 기준이다.

## 판정: **수정 필요**

결함은 Major 2건이다.
- (R1) 스냅샷 파생 규칙의 남길 writer 집합에 S1 writer가 빠져 있다. 코드 사실과 맞지 않는다.
- (R2) gb 429·579에 옛 '탐색·판정 창 `node.dc_window`(선언 제약 판정)' 문언이 남아 있다. 이것은 앞 검증 때 제가 grep으로 자리를 보고도 놓친 것이다.

나머지(앞 검증 F1~F8, 감사 F1, O-59 (1)(3)(4))는 원칙대로 닫혔다.

## 1. 앞 검증 F1~F8·감사 F1 닫힘 여부

| # | 판정 | 근거(head) |
|---|---|---|
| F1 | 닫힘 | gb 1477 θ 프레임 탐색 창 / 측정 구성 판정 창(커널 ICMR 선언 제약)으로 분리 |
| F2 | 닫힘 | gb 1572 "ICMR(측정 구성) 끝은 IT-2 봉인 뒤 블록이 쓰고 이 card는 정의 기준을 더한다; 경계 행 감도는 같은 함수 하나". 1573 (ii)·(ii′) 분리 |
| F3 | 닫힘 | gb 566 '커널 metric(DE-1 전 한정)' |
| F4 | 닫힘 | gb 497 봉인 7행 '동작 변경(N4 0번·N6.3), 맡는 card = EO-1'. 1894 경계 toy red(옛 기준이면 통과) |
| F5 | 닫힘 | gb 566 `sat_threshold` 정본 인용, 훑기 점 = 그 점 VDS·VSB 셀(O-46 (2)), '둘째 진입점 없음' |
| F6 | 닫힘 | gb 1589 σ 두 red(차동 비트 동일, 단일 입력 값 없음 → 값) |
| F7 | 닫힘 | gb 566 같은 연립 결과를 두 필드가 공유(재계산 0) |
| F8 | 닫힘 | gb 566 G5 열거에 tol_VDsat 추가 |
| 감사 F1 | 닫힘(원칙 충족) | gb 566 봉인점 컨덕턴스 계·인수분해 = **ss 층 graph 필드 하나, writer 하나**(가칭 `nodal_factor`). 새 봉인 뒤 블록과 기존 세 자리(`offset_analysis.py:69`·`offset_systematic.py:46`·`block_residual.py:73`, master에서 세 자리 모두 `nodal_factor(conductance_matrix(ss.circuit, size), fixed)` 확인)는 READS. 재사용 = graph reuse·S3 graft만이고 graph 밖 캐시는 금지. 세 자리 이전 = IT-2 범위('같은 변경에서 둘째·셋째 생산자 제거'). 1477 범위 1, 1486 완료 조건(writer 1곳 `git grep`·G-10). 옛 '캐시 공유' 문언은 319·566에서 '정정됨'이라는 인용으로만 남음 |

감사 F1에서 design에 넘길 점(Info): 인수분해 객체가 graph 필드 값이 되면 READS 투영 지문(`compute_block.py:129-132` `Projection.from_snapshot`·`fp_of`)이 그 값을 다룰 수 있어야 한다. 입력 버전으로 지문을 낼지, 값으로 낼지는 design 몫이다. 계획 결함은 아니다.

## 2. O-59 (1)~(4) 반영

| 항목 | 자리 | 판정 |
|---|---|---|
| (1) S-1 문언 정정 | gb 318·319 결정표, 566, 1477, 1486 | 결정 뜻대로 반영. '옛 문언은 graph 밖 캐시라 위반' 근거가 본문에 있음 |
| (2) 스냅샷 파생 규칙 | gb 421(N3.3), 494(봉인 4행), 1480(범위 4), 1486 (11) | 표기 '**원래 취지와 다름, 승인 O-59 (2)**' 있음. 무효화 기준 변경과 reuse→graft 집계 명시. 옛 기본안 철회 경위는 근거 문서 인용. **내용 결함 R1** |
| (3) DV-12 | or 122, 417('최종 범위 metric' -- 정의 자리 하나), 432, 492, 584 | 반영됨. '원래 취지와 다름(경미) -- 승인됨 O-59' 표기 있음. 잠정 대 `status = final`, 엔진 쪽 값 식·제약 비교 사본 금지, fail-closed |
| (4) DV-13 | gb 223 DEC-23 '이동의 기준점', 1575 DE-1 (c) 착수 실측; or 432 인용 | 반영됨. V_id,0 = Σe·V_in,decl/Σe², 선언 없으면 정의 불능, 봉인점 입력 ≠ spec 선언이면 멈춤 |

## 3. 스냅샷 파생 규칙과 기존 graph 규칙·코드 사실

코드 사실은 맞다.
- `kernel_run.py:72-75`: parent가 있으면 `snapshot = parent.snapshot`에서 출발한다. 검사는 `PLAN_WRITERS`의 `block_version` 일치뿐이다(:73).
- `seal_versions.py`: 봉인 4는 `calls`에 든 블록과 그 블록이 쓴 필드만 검사한다. calls 밖 writer 필드는 검사하지 않으니 규칙이 메우려는 공백이 실재한다.
- `compute_block.py:139-147`: `snapshot.block_version(name) == version`이면 reuse, 아니면 S3 donor graft다. 그래서 eager 제거 뒤 같은 입력이면 graft로 돌아오고 computes 증분 0이 성립한다.

NFR-2·DEC-83과의 관계: child를 새 스냅샷으로 만들며 필드를 빼는 것이라 불변 스냅샷·구조 공유와 모순되지 않는다. 필드 = 캐시 정본도 유지되고 새 캐시도 없다.

**R1 (Major)**: 남길 writer 집합 = '`PLAN_WRITERS` ∪ 그 평가의 호출 블록'(gb 421·494·1480)에 S1 writer가 없다.
- 실측: `PLAN_WRITERS`(`E/sizing/kernel_context.py:49-50`)는 레일·대칭·전류 기저·쓰기 계획·SCC 순서·커널 필드·θ 스키마 일곱 개다.
- 그런데 커널 base는 `base = lift_s1(s1graph)`(`kernel_context.py:81`)에서 출발한다. 따라서 S1 구조 필드(writer = `S1_WRITERS`, `E/graph/s1_values.py:194`)를 담는다.
- 탐색 쪽 지문도 이미 두 집합의 합집합 `_CONTEXT_WRITERS = S1_WRITERS ∪ PLAN_WRITERS`(`E/search/search_context.py:44`)를 쓴다.
- 결과: 문언 그대로 구현하면 (a) eager 파생이 커널이 읽는 S1 필드를 지우고, (b) 봉인 4 단언이 모든 평가에서 FAIL한다. 이 결함은 fail-closed라 조용히 틀리지는 않지만 엔진이 서지 않는다.
- 확신도는 중상이다. `lift_s1`이 S1 필드의 writer 귀속을 바꾸는지는 열어 보지 않았다.
- 최소 수정: 세 자리의 집합을 "커널 컨텍스트 base의 writer(`S1_WRITERS` ∪ `PLAN_WRITERS` -- `search_context._CONTEXT_WRITERS`와 같은 집합, 사본이 아니라 그 정의 참조) ∪ 그 평가의 호출 블록"으로 고친다. 1480 착수 실측에 'base의 writer 집합 실측'을 더한다.
- 원칙 점검: 정본 하나(기존 집합 정의 참조), fail-closed 유지, 새 규칙 없음(같은 규칙의 집합 정정). 모두 충족한다.

Minor(R3): 1486 (11)(a)는 "커널 밖 writer 필드가 child에 없음"만 잰다. R1 수정 뒤에는 S1·계획 필드가 child에 **남음**도 같은 red에 넣어야 한다. 그래야 지우는 쪽만 맞고 지나치게 지우는 결함을 잡는다.

## 4. 새 diff가 만든 모순·상수·사본·graph 밖 캐시

- 새 상수 없음. 사본 없음(경계 행 함수 하나, 지목 정의 자리 하나, 값 식은 오라클에만). graph 밖 캐시는 오히려 제거됐다.
- **R2 (Major, 남은 옛 문언)**: S-1 뒤 정의와 모순되는 옛 문언 두 자리.
  - gb 429(S2 동작점 필드 목록): "세 필드: … 커널 탐색·판정 창 `node.dc_window`(+tol_VDsat, `sat_threshold`, 커널 탐색·선언 제약 판정)". 측정 구성 판정 창이 없다.
  - gb 579(DC/AC 표 `icmr_v` 행): "탐색·판정 창 `node.dc_window`(+tol, 선언 제약 판정)". 측정 구성 판정 창이 없다.
  - 최소 수정: 두 자리를 N3.8 '창 필드'의 네 필드(θ 프레임 탐색 창 / 측정 구성 판정 창 / 정의 창 / 다듬은 정의 창)로 맞추거나 N3.8 '창 필드' 인용 한 구절로 줄인다.
  - 앞 검증에서 428·578 위치를 grep으로 보고도 결함으로 올리지 않은 것은 제 누락이다.
- Info: or 432는 gb를 옛 해시 `plan/gb-v619` `81fc49a7` 223행으로 인용한다(이번 diff 이전부터 있던 것). gb 병합 뒤 해시 맞춤 때 함께 고친다.

## 5. gb↔oracle 정합

- 확정 범위 지목: 정의 자리는 or 417 하나다. 생산자는 엔진 쪽 2단계(or 492, OP-10 통합 병합 엔진 커밋)다. gb에는 'final/provisional' 어휘가 없다.
  - gb에서 오라클 범위 값을 읽는 자리: DEC-98 front 대조·보고, DE-1 (d) 슬루·O-51(gb 567·1576), DE-1 후속 정정 표 oracle 행.
  - 이 자리들이 '확정 기록(`status = final`)만 읽는다'를 인용하지 않는다(Minor, R4 -- 후속 정정 행).
  - 모순은 아니다. 다만 gb 소비자가 잠정 값을 읽지 않는다는 fail-closed 규칙이 gb 쪽에 없다.
- DEC-23 기준점: gb 223이 정의하고 or 432가 인용만 한다. 차동 동일 DC 선언이면 0, 선언 없으면 정의 불능. 양쪽이 같다.
- T-1·σ 인용: 앞 검증 상태 그대로 정합.

## 6. 다른 계획 후속 정정 행 (갱신)

| 계획 | 자리 | 정정 |
|---|---|---|
| gain-budget(자기) | 429·579 | R2 |
| gain-budget(자기) | DEC-98 front 대조, 567·1576(O-51), DE-1 후속 정정 표 oracle 행 | 오라클 범위 값은 확정 기록(`status = final`)만 읽는다(or N3.9 '최종 범위 metric' 인용) -- R4 |
| headroom-chain | plan 331·584 '탐색·판정 창 `node.dc_window`'; 59 필드 목록 | 'θ 프레임 탐색 창'으로 정정, 측정 구성 판정 창 추가(앞 검증 그대로) |
| headroom-chain | HC-S `sat_threshold` 소비자 | 측정 구성 판정 창, T-1 triode 반대쪽 여유(gb 566이 이제 이 정본을 인용하므로 HC-S 쪽에 소비자 등록 필요) |
| graph-consumption | 소비 표 | 새 graph 필드 둘을 등록한다: 측정 구성 판정 창(소비자 = 커널 ICMR 제약), ss 층 `nodal_factor`(소비자 = 봉인 뒤 블록·세 자리). 347 V_id* 행에 DEC-23 기준점 V_id,0 인용 |
| offset-trim | 148·311·330(DEC-23 V_id* 인용) | 기준점 V_id,0(O-59 (4)) 인용 추가. 온도 조건 V_id*(T)도 같은 기준점인지 확인 |
| oracle-portability | 18·122·432 gb 인용 | gb 병합 뒤 해시 맞춤(432의 옛 `81fc49a7` 포함) |
| (search test) | ss 블록 `reuse` 계수 단언 test | O-59 (2)로 graft로 집계가 바뀐다. 1480 착수 실측에 이미 있음(계획 정정 아님, card 몫) |

## 7. 확인하지 못한 것

- `lift_s1`의 필드 writer 귀속(R1 확신도를 높이려면 확인 필요).
- 인수분해 객체를 graph 필드 값으로 둘 때의 지문 방식(design 몫).
- graph-consumption·offset-trim 계획 본문 정독.
- or G-19 기존 다른 행(126·127·131·402·406·654·689·690)과 '확정 범위 지목' 문언의 전수 정합.
- history 두 파일 신규 행의 문언.
