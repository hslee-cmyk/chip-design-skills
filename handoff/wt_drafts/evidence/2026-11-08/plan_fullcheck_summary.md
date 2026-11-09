# 계획 전수 모순 점검 종합 (gain-budget ec1aad3a = v6.39.6 넷째 커밋 + 하위 계획 master 475e0b54)

사용자 지시 2026-11-08 "지금 진행전에 계획을 전수로 모순점검해". 점검자 6(작성자 아님), 구간 보고서:
`plan_fullcheck_n0n2.md`(Major 2/minor 9), `plan_fullcheck_n3.md`(2/13 + 불확실 1), `plan_fullcheck_n4n5n7n9.md`(3/12), `plan_fullcheck_n6a.md`(2/8), `plan_fullcheck_n6b.md`(2/15), `plan_fullcheck_cross.md`(4/9). 중복 정리 뒤 아래.

## A. 사용자 결정이 필요한 것

| # | 항목 | 출처 | 지금 상태 | 선택지 (권고) |
|---|---|---|---|---|
| D1 | 입력 방향의 정본 (Q-DI3, P-4) | n0n2 m-7, n3 m3 | P-4 = role에서 유도·direction 거부, 엔진은 direction 필수, O-264와 충돌 | (가) direction 정본·role은 p/n 극성 규약만 **(권고)** / (나) P-4 유지 |
| D2 | '찾아 둔 대칭'의 정본 필드 (Q-FS2) + N3.2 :545 대칭 축약의 옛 함수(`find_structural_symmetry_candidates`, legacy) | n3 M1, n6b m-11 | 대칭 생산자 셋(궤도·matching_groups·옛 함수) | (가) DEC-97 궤도 / (나) matching_groups 대칭 묶음 -- :545도 같은 필드로 |
| D3 | Q-W1 '재풀이 자리' + DEC-105 (2) '승인 전 유효 규칙' | n4n5 M1 | O-257(DEC-108 (5)(6))이 '탐색 = 연속 W, 재풀이 = 실현 평가만'으로 닫았는데 Q-W1이 열린 결정, DEC-105 (2)가 옛 '매 평가 재풀이'를 현행처럼 가리킴 | O-257로 닫힘 확인 → Q-W1 행 삭제·DEC-105 (2) 대체 표지 **(권고)** |
| D4 | spec card·interface card 흐름(N3.12.3) | n4n5 M2 | N9·N0.4 '폐기(커밋 1개 단위)', N6 card들·agent 정의는 card 흐름을 현행으로 씀(실제 작업도 card 흐름) | card 흐름을 현행으로(DEC-86 개정) **(권고)** / 폐기 유지(N6·agent 정의 정정) |
| D5 | DEC-106 (1a)가 diff_pair를 status 무관(review_needed 포함)으로 읽음 대 N3.3 :590 'review_needed면 GB4 전 정지' | n3 U1 | 어느 쪽인지 문언 없음 | review_needed 정지는 평가 경로(소자 matching)만, 차동 입력 판정은 측정 구성이라 status 무관(정의 축 명시) / 판정도 정지 |
| D6 | DEC-93 '모든 뷰 교류접지'를 S1 `ac_ground_class`로 재해석(v6.39.6) | n0n2 m-2, n3 m11 | 바이어스 종속 넷 (4)가 빠짐, 표지 없음, 영향 0 추정(미실측) | 재해석 승인 + '원래 취지와 다름' 표지 / 원래 뜻 유지(무순환 근거를 다른 꼴로) |
| D7 | O-264 문언 '같은 source 넷'을 '이상 전압원이 구동하지 않는 source 넷'으로 좁힘 | n4n5 m4 | 위임 처리(A-212), 결과 0/13 | 승인 / 원문 유지 |
| D8 | 오라클 쪽 차동 입력쌍 판정 자리 | cross M1·m2 | oracle-portability :455가 role로 판정, NFR-P3(엔진 계산 안 받음)과 관계 미정 | 엔진 필드를 측정 구성 선언으로 EO-1이 넘김 / 오라클이 같은 구조 규칙을 따로 판정(정의 하나·생산자 둘 -- 규칙 3 검토 필요) |
| D9 | (나중) 소스 퇴화 쌍·계측 증폭기형도 차동 입력으로 받을지 | n6b, n4n5 | O-264 문언상 정의 불능 정지(fail-closed) | LA-1 재점검 때 |

## B. 문언 정합 묶음 (결정 변경 없음 -- 묶어서 승인 요청)

1. O-266 잔존: N6.43 FS-1 재개 착수 조건 (7)·N6.48 DI-1 착수 조건 (5) 삭제 → O-267(원칙 19·20 재확인)로; N2.1 O-226 행에 한계 표지, O-229·O-266·O-267 행 추가, N6.1 :1469 위임 밖 목록에 '계획 문언 개정 = 사용자 승인'.
2. 같은 물리 정의 두 집합: DEC-106 (1a) '이상 구동 넷' 대 N3.6 '측정 구성 원 넷' → 하나로(정의 READS), 이상 전압원 단자 갈래·toy (c‴)는 E-27(단계 A 정지)와 맞춤.
3. SF-1 범위 3 병합 짝: :2467·:1952 → '첫 소비자 LA-1(표 #3)'.
4. 입력 DC 선언 이름: N3.15·N3.16 `input_dc_net` → `input_dc` {net, value, engine, pending}, 옛 이름 흡수 열.
5. DEC-104 R9 :304 `rel_kvl_branch` READS → 쓰기 계획 출력 READS(graph-consumption U-G1·U-G3 정합).
6. 하위 계획 role 문언: oracle-portability :455, headroom-chain N0.1 :71, offset-trim N4 :653·:670·N3.2 :256, graph-consumption :15·:148·:369·:399 → DEC-106 (1a) 필드 READS·p/n은 role 극성; DI-1 소비자에 offset-trim 추가, `legacy_adapter.py`는 LT-1 삭제 대상이라 DI-1에서 뺌.
7. v6.39.6 덜 옮긴 곳: LA-1 선행 사슬(:2155·:1358·:1359)·N6.1 :1369·:1416·:1417에 FS-1·FP-1·DI-1·SF-1 범위 9, FS-1 착수 (2) L 조건 실측을 새 짝 정의로, FS-1 (e)·(6) 시점 조건을 DI-1 완료로, IT-1 role 문언에 DI-1 대체 표지, 재작성 표 빈 곳 2(같은 DC 마디 정본 필드 생산자, Q-FS2 (나) 엔진 자리), DI-1 toy (c)(f) 정의 불능 조건에 '입력 DC 미선언', E-29 소유 상호 인용, `matching_offset` 현행 문언(:573·V9·DT-1)과 graph-consumption :500 순서.
8. 병합된 card 상태 표지(원칙 25): IT-1·IT-2a~e·EO-1 범위 4·WB-1·LM-1d/e·HC-S·JC-1·OP-7 행 '착수 전/미병합' 문언.
9. 그 밖 minor(낡은 접두·없는 절 인용·ID 표·Σ W·L 면적 축·닫힌 Q/U 행 잔존·폐기 V-검사 인용·DE-1 OP-10 선행·offset-trim N4 13 대 9회로·하위 판 번호 등) -- 구간 보고서 목록대로.

## C. 불확실(실측·design 확인 필요, 결정 전 사실 확인)
- 무순환: DI 필드 → 기본 전달 뷰 → `dc_role` → matching_groups 경로가 순환인지(n6b m-9).
- trim 포트가 입력 방향 포트로 분류되면 합성 회로가 정의 불능 정지(cross m6) -- offset-trim 되돌린 보기 목록.
- LA-1a 출발 L 변경이 FS-1 짝 조건 ③에 주는 영향 셈 자리(n6b m-6), LA-1a R7 가드 slope bin이 출발 w_f 필드를 READS하는지(m-13).
