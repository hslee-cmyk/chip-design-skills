---
template: plan
version: 5.2
---

# gain-budget-gmid-sizing Planning Document

> **Summary**: `analog-gmid-design` skill의 gm/ID 사이징 엔진을 **gain-budget-first**로 재설계한다. connectivity에서 signal stage를 유도하고, 보상망이 gm을 정한 뒤, stage 출력노드의 실제 부하까지 포함한 gain을 결합 블록 단위로 할당하고, 노드전압을 DC 정본으로 두어 헤드룸을 자기일관되게 푼다. 그 기반으로 계산 결과를 버리지 않는 **Circuit State Graph**, 책임별 10모듈과 명시적 pytest, 코드 작성자와 검증자의 기계적 분리를 만든다.
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code · **Date**: 2026-09-04, v5.0 재구성 2026-09-14
> **Status**: Plan 확정본. 다음 단계는 N9의 design 문서 작성(첫 대상 Phase 0.5).
> **이력**: 결정 경위·과거 구현 기록·원설계 본문·v4.49 이전 계획서 전문은 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md). 이 문서의 옛 절 번호(§0~§15)는 부록 A로 찾는다.

---

## N0. 문서 안내

### N0.1 이 문서가 담는 것

* 담는 것: **확정 결정, 요구, 목표 구조, 규칙, 순서, 완료 조건, 열린 항목**. 모든 항목은 한 곳에만 있다.
* 담지 않는 것: 경위, 발견 과정, 사례 서술, 검토 방법, 과거 수치. 필요하면 "이력:" 앵커나 분석 원자료를 따라간다.
* 인용 규칙: 이 문서 안은 **절 번호 + 항목 ID**로 인용한다(줄 번호 금지). 코드는 `파일:함수명`으로 인용하고 줄 번호는 참고로만 쓴다. 탐색·test 결과 수치를 보고할 때는 auditor 판정 기록(N3.12.5)에서만 인용한다(설계 입력인 사실 수치는 예외).

### N0.2 읽는 순서

| 독자 | 순서 |
|---|---|
| design 문서 작성 agent | N0.4 용어 -> N2 결정 -> N6 해당 Phase -> N3 해당 구조 -> N4 해당 규칙 -> N9 해당 문서 지침 -> N7 착수 조건 |
| 구현 agent(code/test) | 해당 design 문서 -> spec card -> 레지스트리(N0.3) -> N4 |
| auditor | N4.2 검사표 -> N3.12.3 흐름·판정 규칙 -> N3.5 계약 test 열 -> N6 해당 Phase DoD |
| 새 세션 | N6.1 순서표 -> N7 -> N5.4 |

### N0.3 관련 문서

| 문서 | 용도 |
|---|---|
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md` | 경위·원설계·과거 구현 기록·v4.49 이전 계획서 전문 |
| `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` | 함수 재사용 레지스트리(개념별 정본표, 등급 R0/R1/R2/D/DUP). **새 함수를 쓰기 전에 반드시 본다** |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/` | 동결 원자료: agent1~7(함수·계획 대조·은폐 이력), review_A/B/D(원설계 재평가·gain 분해 사고), probe_stage_partition(4회로 stage 분할 실측), rewrite_X/Y(결정·이슈 판정) |
| `~/.claude/agent-kit/methodology.md` §7 | anti-tautology·anti-circularity 원칙(N3.12이 이식) |
| `skills/analog-gmid-design/references/known-incidents.md` | 사고1~24(N4.1 IC의 출처) |
| `skills/analog-gmid-design/references/gm-id-methodology.md` §13 | 엔진 운영에서 나온 방법론 발견(미러 다리 판정 신호 등) |
| `docs/01-plan/features/analog-topology-json-library.plan.md` | topology.json은 connectivity 전용이라는 원래 의도(WP-07 근거) |
| `.ai/context.md` 세션44~48 | 세션별 경위(WP-15 확인 대상) |

### N0.4 용어와 ID 체계

**ID 접두어**(IC·SC·V·GB·RC·TS·W·MT·EL·DF·I-*는 옛 번호와 같다(신설 번호는 부록 A.2에 '신설'로 표기). DEC·WP·U는 새 번호이며 부록 A.2로 찾는다)

| ID | 뜻 | 정의 절 |
|---|---|---|
| DEC-nn | 확정 결정(옛 D1~D15는 별칭 `D1`로 병기) | N2.1 |
| WP-nn | 작업 방식 원칙 | N2.2 |
| FR-n / NFR-n | 기능·비기능 요구 | N1.3, N1.4 |
| GB0~GB9 | gain-budget-first 흐름 단계 | N3.1 |
| SP1 | stage 분할 규칙(DM 뷰 + N3.2-4 엣지 비용) | N3.2 |
| S0/S1/S1v/S2/S2p/S3 | Circuit State Graph 층 | N3.3 |
| W0~W4 | 노드전압 writer 티어 | N3.4 |
| SC-a~SC-e | 상태 계약 | N3.5 |
| K1~K6 | stage 경계를 넘는 결합 종류 | N3.7 |
| MT1~MT3 | metric 티어(블록 국소 / 블록 분해 가능 / 전역) | N3.8 |
| LR1~LR9 | L 결정 규칙 | N3.9 |
| MOD1~MOD10 | 모듈(트랜지스터 이름 M1a 등과 구분) | N3.10 |
| TS0~TS7 | test 분리 단계 | N3.11 |
| EL1~EL4 | 역할 분리 강제 겹 | N3.12.4 |
| IC1~IC10 | 기지 사고 클래스와 강제 test | N4.1 |
| V1~V10 | auditor 검사 | N4.2 |
| DF-nn | 현존 결함 | N5.2 |
| I-A* / I-B* / I-G* / I-C* | 열린 이슈(옛 §10 A/B/G/C 번호 유지) | N5.3 |
| J1~J10 | 회로 해석 공동분석 항목 | N7.1 |
| U-nn | 사용자 결정 착수 조건 | N7.2 |
| RC1~RC5 | gain 분해 실패의 근본 원인 | N3.1 끝 |

레지스트리 등급(R0/R1/R2/D/DUP)은 외부 문서 정의라 개명하지 않고 **"등급 R1"처럼 '등급'을 붙여** 쓴다.

**용어집**

| 용어 | 정의 |
|---|---|
| gain-budget-first | stage별 gain 예산을 **엔진이 유도해 산출**한다. 사용자는 총 gain 제약 하나만 준다. "gain이 gm을 정한다"는 뜻이 아니다 |
| 보상 먼저 | 스펙 (CL, GBW, PM)에서 보상망이 (Cc, Rz, gm_1..gm_N)을 한 번에 정한다. 그 뒤 자유 축은 gm_id_i, L(동치류 단위), W4 자유 노드전압이다 |
| signal stage | S1v 차동모드 뷰에서 SP1로 유도한 stage: {input, cascode, follower, pass, load, tail, 출력노드, 출력노드 임피던스 등급, 블록 노드 집합} |
| 셀 | 트랜지스터 하나의 소신호 역할. 신호 입력 단자와 출력 단자로 정한다: CS(gate->drain), CG(source->drain), CD(gate->source, follower), pass(source↔drain, 게이트는 바이어스 -- class-AB floating battery 등). 모든 트랜지스터에 같은 규칙으로 붙인다 |
| 입력 노드 구동 종류 | 셀 입력 노드가 **전압 구동**(입력 포트, 앞 stage의 출력노드, follower 출력)인지 **전류 구동**(다른 소자 drain 전류가 흘러드는 저임피던스 내부 노드, 캐스코드 source)인지. stage 경계를 정한다(N3.2-5) |
| declared stage | topology.json에 사람이 적은 stage 정보(`compensation.stage_devices`, `gain_stages_sum.stages` 등). 대조 대상일 뿐 정본이 아니다 |
| 출력노드 | stage 안에서 신호가 마지막으로 도달해 다음 stage 입력 또는 출력 포트로 넘어가는 노드. CS·CG 사슬이면 drain 노드(고임피던스), CD·pass로 끝나면 source(또는 pass의 반대쪽 단자) 노드(저임피던스일 수 있다). 임피던스 등급은 노드 속성으로 기록한다 |
| 노드 어드미턴스 | 노드에 붙은 소자 단자별 소신호 기여의 합: drain 단자 gds, source 단자 gm+gmb+gds(게이트가 교류접지일 때), 수동소자 어드미턴스. 캐스코드·follower 효과는 아래 블록 국소 모델이 자동으로 포함한다 |
| 블록 gain | 블록 국소 소신호 모델(N3.8)로 푼 출력노드 대 입력의 전압비(dB). CS 한 단의 특수 케이스가 `20·log10(gm_in / G_out)`, CD 한 단의 특수 케이스가 `20·log10(gm / (gm + gmb + G_node))` |
| 결합 블록(coupling block) | signal stage 하나에 대응하는 할당 단위 |
| 결합변수 y | 두 결합 블록 이상에 걸친 관계 엣지의 상태(K1~K4) |
| 계산 블록(compute block) | 평가 커널을 나눈 계산 단위(입력·출력 선언, S2 memo 단위) |
| 순환 블록(cycle block) | 유도 DAG의 SCC. 명시적 고정점으로 푼다 |
| 교류접지 집합 | 레일 / gate에만 붙고 구동되지 않는 넷(입력·수동소자·이상원 단자 제외) / 이상 전압원 단자 |
| DM 뷰 | 대칭 넷 대응으로 만든 차동모드 반회로. 자기대응 넷은 가상접지 |
| 봉인(seal) | metric 계산 전 S2 스냅샷이 N3.6 봉인 항목을 모두 통과한 상태 |
| shadow 모드 | 새 유도 결과를 기존 경로와 대조해 보고만 하고 동작은 바꾸지 않는 실행 모드 |
| status | 유도 사실의 상태. `declared`(사람 선언) / `derived`(엔진 유도) / `proposed`(증거 부족 제안) / `review_needed`(선언과 불일치 또는 해석 필요) / `ratified`(공동분석으로 사용자 확정) |
| 무동작 증명 | 그 기능이 필요 없는 회로에서 기능의 발동 계수가 0이고 그 회로의 산출물이 Phase 전후 동일함 |
| 오케스트레이터 | 메인 세션. 라우팅·계획/설계/기록 문서·spec card만 쓴다(DEC-37) |
| spec card | 변경 1건의 계약(N3.12.3). design 문서는 Phase 설계, spec card는 그 설계를 구현하는 변경 1건 |
| interface card | 기계적으로 뽑은 시그니처·docstring 첫 단락 + spec card의 신규 시그니처. test-author의 유일한 구현 정보 |
| 판정 기록 | auditor만 쓰는 `.ai/verification/<id>.json`(N3.12.5) |
| 승인 기록 | 사용자 승인 원문을 오케스트레이터가 옮긴 `.ai/approvals/<id>.md`(N3.12.5) |
| oracle 4종 | (a) 물리 불변식·손계산 (b) 다른 방법의 참조구현 (c) known-good 기준(SPICE, 결함 도입 전 커밋) (d) spec card에 사용자가 적은 값 |
| 기준 약화 | assert 삭제, 비교 완화, 허용오차 확대, skip/xfail 추가, 기대값 리터럴 변경, 픽스처 입력 리터럴 변경, 격자 확대, assert를 조건문·try 아래로 이동 |
| 운영 경로 | Phase 3 전: `workspaces/run_harness.py` -> `optimize_full_circuit_budget` -> `_evaluate`. Phase 3 후: `run_gmid_design_pipeline` 이하. 문자열 레지스트리(`_METRICS_REGISTRY`, `_COMPENSATION_REGISTRY`, topology.json `"function"`)로 도달하는 것 포함 |
| 4개 회로 | `current_reuse_telescopic_ota`(파일럿) / `folded_cascode` / `two_stage_ota` / `nmcnr_amplifier` |

---

## N1. 목표·범위·요구

### N1.1 목적

gm/ID 사이징의 결정 순서를 **signal stage 유도 -> 보상 -> gain 할당(gm_id·L) ⇄ 노드전압 DC 해석 -> 전체회로 판정**으로 세운다. 설계 목표:

* (a) stage·부하·결합을 connectivity에서 유도하고, 회로 해석이 걸린 것만 사람과 확정한다.
* (b) stage gain을 출력노드 임피던스로 정의하고, 제약 판정은 전체회로 MNA gain으로 한다.
* (c) 노드전압을 DC 정본으로 두어 KVL·vsb·매칭 불일치를 표현할 수 없게 한다.
* (d) 계산 결과(실패 포함)를 입력 지문으로 재사용하고, 이전 결과로 시작점을 정제한다.
* (e) 코드 작성, 판정 기준 작성, 판정 실행을 서로 다른 주체가 맡고 기계적으로 강제한다.

이력: 출발 문제(2026-09-04 diode 헤드룸 rail-lock)와 v4.0~v4.49 경위는 이력 문서 §0, §1, §10.6~§10.14, Version History.

### N1.2 범위

**In scope**: N6.1의 Phase 0.5~7c 전부, 4개 회로 전부.

**Out of scope**

| 항목 | 이유 |
|---|---|
| 비증폭 회로(밴드갭, constant-gm bias, 비교기, 스위치드 커패시터) | 대상은 차동 입력 전압증폭기 계열(I-G7 해소) |
| gain-boosted cascode | 부스트 증폭기 재귀 스키마가 없다(I-G3 해소) |
| PVT 코너 스윕 | LUT는 TT·기록된 온도 한 조건. 코너 메타는 기록만 한다(I-A5 범위 부분 해소) |
| 레이아웃 알고리즘 변경 | common-centroid·오일러·finger·floorplan은 MOD7로 옮기기만 한다 |
| 4개 회로 외 토폴로지 추가 | 추가 비용 문서화(I-G8)만 N9에 포함 |

### N1.3 기능 요구

| ID | 요구 | 근거 결정 |
|---|---|---|
| FR-1 | signal stage는 connectivity에서 SP1로 유도한다. declared stage와 다르면 `review_needed`로 기록하고, 회로 해석은 공동분석(J)으로 `ratified`한다 | DEC-43, DEC-44 |
| FR-2 | 블록 gain은 블록 국소 소신호 모델(출력노드 정의는 소자 구성에 따른다: CS·CG는 drain, CD·pass는 source 쪽)로 정의한다. gain 제약 판정은 전체회로 MNA gain 하나로 하고, 블록 gain 합과의 잔차를 매 평가 기록한다 | DEC-05 |
| FR-3 | 보상이 먼저다: (CL, GBW, PM)에서 (Cc, Rz, gm_i)를 풀고 기생 pole로 L 상한을 정한다 | DEC-02, DEC-24, DEC-25 |
| FR-4 | gain 할당은 엔진이 유도해 `gain_budget_db`로 **출력**한다. 결합 블록 3층 할당을 쓴다. 공유 VGS는 gain 기준으로 고르고 tail이 L 동치류의 주인이다 | DEC-03, DEC-45, DEC-10, DEC-17 |
| FR-5 | 노드전압이 DC 정본이다. 소자 vds/vgs/vsb는 노드전압 차이로 유도하고, writer 티어 W0~W4로 쓰며, 순환은 명시적 고정점으로 푼다 | DEC-31(D1), DEC-32 |
| FR-6 | 모든 소자의 V/I 관계를 상시 검증한다: 내부는 봉인 게이트(N3.6), 독립 검증은 트랜지스터 레벨 SPICE | DEC-48 |
| FR-7 | 계산 결과를 버리지 않는다: 입력 지문 기반 재사용, 실패도 margin과 함께 기록, 이전 결과로 시작점 정제 | DEC-30 |
| FR-8 | 달성 불가를 탐색 전에 보고한다: 블록별 gain 상한 합, 구조·수치 DOF | N3.1 RC3·RC4 |

### N1.4 비기능 요구

| ID | 요구 |
|---|---|
| NFR-1 | **버그 free 최우선.** 기존 함수 시그니처 보존은 목표가 아니다. 판단 기준은 "물리적으로 옳은가, 조용한 실패가 구조적으로 불가능한가"다 |
| NFR-2 | **효율.** 같은 계산을 호출부마다 반복하지 않는다. 캐시 키는 그 계산이 실제로 읽는 모든 가변 상태의 내용 지문이다. 캐시는 상한을 두고 초과 시 LRU로 밀어낸다(캐싱 중단 금지) |
| NFR-3 | **기지 사고 재발 불가.** IC1~IC10(N4.1)마다 거부 케이스를 가진 강제 test가 있어야 한다 |
| NFR-4 | **결정론.** 모든 반복은 정렬된 시퀀스 위에서 한다(`set` 순회 금지). 같은 입력은 같은 산출물을 낸다 |

---

## N2. 확정 결정·원칙

### N2.1 결정 레지스터

**무엇이 이미 정해졌는지는 이 표가 정본이다.** 현행 형태만 적는다(대체된 형태와 결정 경위는 이력 문서, 출처 줄 번호는 원자료 `rewrite_X_decisions.md`). 상태: **구현됨** / **부분**(잔여 명시) / **미구현** / **착수 조건**(N7.2의 사용자 결정) / **원칙**(구현 대상이 아닌 규칙).

| ID (별칭) | 결정 | 날짜 | 적용 | 상태 |
|---|---|---|---|---|
| DEC-01 | 목표는 gain-budget-first다. Circuit State Graph는 stage 분할과 gain 할당을 위한 기반이다 | 2026-09-04, 09-14 | 전체 | 미구현 |
| DEC-02 | 인과 방향은 보상 먼저: (CL, GBW, PM) -> (Cc, Rz, gm_1..gm_N), 이후 gm_id_i·L·자유 노드전압이 자유 축 | 2026-09-07 | GB5 | 부분(Cc 유도만) |
| DEC-03 | stage별 gain 예산은 엔진이 유도해 `gain_budget_db`로 출력한다. 사람이 배분을 강제하는 유일한 경로는 `gain_budget_db_override`(출처 필수) | 2026-09-07 | GB0, GB6 | 미구현 |
| DEC-04 | 결합 블록 안의 소자(input·cascode·load·tail)는 gm_id·L을 함께 결정한다. 캐스코드 L을 role 휴리스틱으로 따로 정하지 않는다 | 2026-09-04 | GB6 내층 | 미구현 |
| DEC-05 | gain 제약 판정은 전체회로 MNA gain 하나로 한다. 블록 gain(블록 국소 소신호 모델, 부하·follower·pass 포함)은 할당용 분해 값이고, 두 값의 잔차를 매 평가 기록한다 | 2026-09-14 | GB8 | 미구현(현 제약은 `gain_stages_sum`, I-B21) |
| DEC-06 | theta는 자유 탐색 변수만이다. 구조 선언은 `sizing_spec.json`의 선언/유도 필드로 옮긴다 | 2026-09-07 | GB0, MOD2 | 미구현 |
| DEC-07 | 목적함수는 전력 최소화 하나, 면적은 `area_um2` 상한 제약. 면적 예산이 선언되지 않으면 전력-면적 Pareto를 제시하고 정지한다 | 2026-09-07 | GB6, GB9 | 미구현(전력 정의 U-10, Area 정의 U-13) |
| DEC-08 | `ideal_sources.value_amp`가 null이면 자유 탐색, 값이 있으면 그 값을 실제 전류로 고정한다. 같은 소스를 움직이는 theta와 공존하면 로드 거부 | 2026-09-08 | GB0 | 부분(KCL 잔차 metric만 소비). 파일럿 Iref `value_amp = 1.2µA`는 사용자가 원문에서 확인한 고정 대상(사이징 경로 미배선, I-B14) |
| DEC-09 | 게이트·소스를 공유하는 전류미러 18소자(파일럿)는 전부 VGS를 강제로 공유한다. tail M5/M6를 bias 미러에 묶는 것이 설계 의도다 | 2026-09-09 | GB1, K2 | 구현됨 |
| DEC-10 | 공유 VGS는 gain 기준으로 고른다(면적 기준 아님). gain 폭이 분해능 이하인 그룹의 기준은 U-14 | 2026-09-09 | GB6 중층 | 미구현 |
| DEC-11 | LUT 역보간 `_solve_vgs`는 목표를 품는 가장 오른쪽 구간에서만 보간한다(rightmost root). 곡선 범위 밖은 명시적 실패 | 2026-09-09 | MOD1 | 구현됨(다른 이분 역산은 DF-10) |
| DEC-12 | diode 창은 VGS를 공유하는 미러 멤버 전원의 W 한계를 함께 본다. 멤버 vds가 미정이면 역할별 `min_vds`를 바닥으로 쓰고, 멤버 L/ID 미정은 명시적 실패 | 2026-09-09 | W2 | 구현됨(선언 기반 -> S1 관계 엣지 기반으로 전환, 6b) |
| DEC-13 | 적층 diode는 2변수로 함께 푼다. 아래쪽 vsb = 위쪽 vsb + 위쪽 vds | 2026-09-09 | W2 | 부분(DF-01) |
| DEC-14 | diode vds는 나눠줄 몫이 아니라 구간 제약 변수이고, diode gm_id는 vds의 종속값이다 | 2026-09-08 | W1, W2 | 구현됨 |
| DEC-15 | M11a/M11b/M20a/M20b는 class-AB 배터리 전압 기준 소자다(신호경로 미러 아님) | 2026-09-09 | GB1 | 구현됨 |
| DEC-16 | 초기 L은 공정 knee에서 시작하고 실현가능 창으로 clamp한다 | 2026-09-07 | LR5 | 구현됨(`measure_L_knee`, `derive_role_L`) |
| DEC-17 | gain stage의 tail이 L 동치류의 주인이다(최초 입력단 tail 우선). 동치류 멤버는 L을 공유하고, 공통 L은 모든 선언 제약을 동시에 만족하도록 탐색한다. 동치류 안에서 L이 갈리면 에러 | 2026-09-10 | GB1, LR2 | 구현됨(층0 게이트의 `ValueError`는 DF-03) |
| DEC-18 | L theta는 동치류에서 일반 규칙으로 파생한다(소자·theta 이름 지정 금지). role 배수 상수(`_L_ROLE_MULTIPLIERS`)는 쓰지 않는다 | 2026-09-10 | GB1 | 구현됨 |
| DEC-19 | warm start 격자에 L 동치류 theta를 포함한다 | 2026-09-10 | GB9 | 구현됨 |
| DEC-20 | 제약 임계값은 근거가 되는 선언값 하나만 두고, 파생 임계값은 `value_from_constraint`로 참조한다 | 2026-09-10 | GB0 | 구현됨(`mirror_ratio_error_mV`) |
| DEC-21 | `mismatch_sigma_mV = 5.0`은 회로 안에서 유도할 수 없는 시스템 입력이다. 출처 선언이 필요하다 | 2026-09-10 | GB0 | 착수 조건 U-17 |
| DEC-22 | 제약 임계값 도출은 bisection(임계값만 움직이며 원래 탐색 반복, 마지막 성공값, 여러 시드 전부 성공)으로 한다 | 2026-09-10 | N3.13 | 미구현 |
| DEC-23 | 입력환산 오프셋은 gm 가중 RSS, 캐스코드 제외. 쌍 = offset 매칭 선언 ∩ 게이트가 ports input 넷 | 2026-09-10 | GB8 | 구현됨(DF-12) |
| DEC-24 | Cc와 Rz는 보상망이 계산해 확정한다(spec 손값은 폴백) | 2026-09-10 | GB5 | 구현됨 |
| DEC-25 | L 상한은 상수 N 없이 기생 pole의 위상 기여를 직접 계산한 `parasitic_pm_deg >= PM_target_deg`로 건다 | 2026-09-10 | GB5, LR6 | 구현됨(정본은 전체 주파수응답. 노드별 근사 `node_pole_estimate`는 못 세는 고임피던스 노드를 `undetermined`로 실패시킨다. 4개 회로 선측정 미완 I-A10) |
| DEC-26 | spec은 `run_harness.canonical_spec()`만 정본이다. 변형은 `derived_spec(why 필수)`로만 만든다 | 2026-09-10 | GB0, S0 | 구현됨 |
| DEC-27 | class-AB 배터리 전압 `V_bat = vdd − VGS(M15) − VGS(M16)` KVL을 gm_id 탐색 상한으로, 포화 하한은 `2/(gm/ID)`로 둔다 | 2026-09-10 | W2 | 구현됨 |
| DEC-28 | 실현 불가 기준점 복구는 회로 이름 없는 일반 규칙으로만 한다 | 2026-09-10 | GB9 | 구현됨(DF-04) |
| DEC-29 | 신호 전파는 input 포트에서 output 포트 방향으로만 해석하고, 방향은 여기 모드별 뷰(S1v)에 둔다(노드 단일 속성 금지) | 2026-09-10, 09-14 | GB2 | 미구현 |
| DEC-30 | 계산 결과(노드전압·신호방향·실패 포함)를 버리지 않고 재사용·점진 정제·전역 최적화에 쓴다 | 2026-09-14 | N3.3~N3.5 | 미구현 |
| DEC-31 (D1) | **노드전압이 DC 정본이다.** 소자 vds/vgs/vsb는 노드전압 차이로 유도한다 | 2026-09-14 | GB7, W0~W4 | 미구현 |
| DEC-32 (D2) | 순환 블록 수렴 허용오차는 LUT 보간 오차(leave-one-out)에서, 반복 상한은 그 허용오차와 구간폭·수축비에서 계산한다. LUT 격자 간격은 FD 스텝과 bisection 구간에 쓴다(식: N3.6, N3.7) | 2026-09-14 | GB7 | 미구현 |
| DEC-34 (D4) | 전역 샘플 수는 파일럿 wall-clock 5분 안에서 실측 시간으로 계산한다(식: N3.5) | 2026-09-14 | GB9 | 미구현 |
| DEC-35 (D5) | `ports`는 오케스트레이터가 connectivity로 제안 -> 표로 사용자 확인 -> 반영한다 | 2026-09-14 | 6a | 착수 조건 U-08 |
| DEC-36 (D9) | test 프레임워크는 pytest(설치된 9.0.2). 플러그인 추가 없음 | 2026-09-04 | tests | 미구현 |
| DEC-37 (D10, D11) | 결함 수정에 순서 예외는 없다(DF-03·DF-18도 Phase 4). 메인 세션(오케스트레이터)은 엔진 소스·tests를 쓰지 못한다(EL1 강제) | 2026-09-14 | Phase 4, EL1 | 미구현 |
| DEC-38 (D12) | test-author는 interface card만 입력으로 받고 소스 경로 Read가 거부된다. test의 독립성은 결과(V3, V4)로 검사한다 | 2026-09-14 | N3.12 | 미구현 |
| DEC-39 (D13) | 뮤테이션은 자체 AST 변이기로 한다(의존성 추가 없음) | 2026-09-14 | V3 | 미구현 |
| DEC-40 (D14) | 기준 약화는 매 건 사용자 승인. 승인 기록 없이 병합 불가 | 2026-09-14 | V5 | 미구현 |
| DEC-41 (D15) | 역할 분리 hook을 프로젝트 `.claude/settings.json`에 등록한다(스크립트 완성과 거부 확인 뒤) | 2026-09-14 | Phase 0.5 | 미구현 |
| DEC-42 | 코드 작성(gmid-code-author), 판정 기준 작성(gmid-test-author), 판정 실행·보고 수치(gmid-verification-auditor)를 분리하고 EL1~EL4로 강제한다 | 2026-09-14 | N3.12 | 미구현 |
| DEC-43 | stage 분할은 SP1(DM 뷰 + N3.2-4 엣지 비용)로 한다. 회귀 기준은 공동분석으로 `ratified`된 분할이다 | 2026-09-14 | GB2 | 미구현 |
| DEC-44 | 회로 해석이 걸린 판정(교류접지 예외, 부하 귀속, 역할)은 사람과 공동분석으로 확정하고, 엔진은 증거와 함께 `review_needed`까지만 낸다 | -- | GB1, GB2 | 원칙 |
| DEC-45 | gain 할당은 3층이다: 결합변수 y 고정 블록 DP / y 좌표강하 / DP 해에서 SLSQP 미세조정 | 2026-09-14 | GB6 | 미구현 |
| DEC-46 | 코드는 10모듈(N3.10)로, 인라인 self-test는 `tests/` pytest(N3.11)로 분리한다. stick_diagram self-test도 포함 | 2026-09-04, 09-14 | Phase 1, 3 | 미구현 |
| DEC-47 | 모든 동작 변경 Phase는 4개 회로 전부에서 측정한다 | -- | 전체 | 원칙 |
| DEC-48 | 전체회로 물리 정합성(KVL/KCL/VGS)을 파이프라인 상시 게이트로 둔다 | 2026-09-04 | GB7, GB9 | 부분(노드전압 복원·vsb 게이트) |
| DEC-49 | 새 metric의 상한 제약은 4개 회로에서 먼저 잰 뒤 정한다 | 2026-09-08 | GB8 | 원칙 |
| DEC-50 | `gain_db >= 54`는 결함 metric(`gain_stages_sum`) 기준값이다. 7a 이후 전체회로 gain 기준으로 bisection 재도출한다 | 2026-09-03, 09-14 | 7a | 착수 조건 U-19 |
| DEC-51 | 모든 구현은 plan -> design -> do 순서를 거친다 | 2026-09-10 | 전체 | 원칙 |
| DEC-52 | `vs`는 `vsb`(소스-벌크 역바이어스 크기)이며 옛 키는 로드 거부 | 2026-09-08 | MOD2 | 구현됨 |
| DEC-53 | metric 이름과 단위는 레지스트리로 검증한다 | 2026-09-08 | MOD5 | 구현됨 |
| DEC-54 | 연속 최적화는 SLSQP를 유지한다. 시작점은 S3 아카이브와 준난수 전역 샘플에서 고른다 | 2026-09-14 | GB9 | 부분(multi-start만) |
| DEC-55 | passive connectivity(CL1/CL2, Cf1/Cf2 교차, Cs1/Cs2)와 M18b `budget_reference_device`는 파일럿 topology에 반영돼 있다 | 2026-09-10 | GB1 | 구현됨 |
| DEC-57 | stage는 **전압 이득 stage**다. 모든 트랜지스터를 셀(CS/CG/CD/pass)로 같은 규칙으로 분류하고, stage 경계는 셀 입력 노드의 구동 종류로 정한다. 캐스코드(전류 구동 CG)는 별도 stage가 아니다 | 2026-09-14 | GB2, N3.2-5 | 미구현 |
| DEC-56 | L5c 픽스처는 `r_cmfb_vocdes`를 하한 0.02로 고정하고 `stop_after_sizing=True`로 돈다. 이관 뒤 이 입력을 바꾸는 것은 기준 약화(DEC-40) | 2026-09-09~10 | Phase 1 | 구현됨 |

### N2.2 작업 방식 원칙

모든 역할과 오케스트레이터에 적용한다.

| ID | 원칙 |
|---|---|
| WP-01 | 만들면 반드시 배선한다. 배선할 수 없으면 사용자 승인을 받는다 |
| WP-02 | skip·continue·예외 목록·광범위 except를 만들기 전에 (1) 대상이 실재하나 (2) 검사가 틀렸나 대상이 틀렸나 (3) 우회 없이 고칠 수 있나를 답한다. 게이트는 "통과"보다 "실제로 거부한다"를 먼저 확인한다 |
| WP-03 | 상수를 임의로 만들지 않는다. 근거 선언값 하나만 두고 식을 코드로 계산해 캐시한다. 유도를 주석에 적고 결과 숫자를 박는 것은 해결이 아니다 |
| WP-04 | 논문 값을 인용하지 않는다. 사용자가 직접 지정한 값만 확정값이다 |
| WP-05 | 해결책은 일반화한다(회로·소자·theta 이름과 매직넘버 금지). 4개 회로에서 측정해 필요 없는 회로의 무동작을 증명한다 |
| WP-06 | 회로 위상 해석은 항상 사용자와 공동분석한다. 공유 엔진의 동작 변경은 승인 후에 한다 |
| WP-07 | topology.json이 유일한 토폴로지 소스다. connectivity는 사용자만 수정하고, role·matching 메타데이터는 분석해 갱신할 수 있다. test 픽스처는 `library/*.topology.json`에서 로드·변형만 하고 손으로 넷리스트를 새로 치지 않는다 |
| WP-08 | connectivity 정정은 모았다가 "한꺼번에 반영" 지시 때 일괄 반영하고 net 표를 다시 출력한다 |
| WP-09 | 회로도 이미지 판독은 `topology_to_markdown.py` net 표로 재검증한다 |
| WP-10 | 반복문 안의 계산은 쓰는 순간 캐시하고(상한 필수), 최적화 근거는 cProfile과 중복 인자 계측으로 만든다 |
| WP-11 | 조사 스크립트는 결과를 파일에 케이스마다 append한다 |
| WP-12 | 장시간 실행은 harness의 background 실행으로 한다(수동 `&`/nohup 금지) |
| WP-13 | 코드를 쓴 주체는 그 코드의 test·기대값·기준선·판정·보고 수치를 소유하지 않는다(N3.12) |
| WP-14 | 새 함수를 쓰기 전에 레지스트리 개념별 정본표와 호출부를 확인한다. 등급 R0는 호출만, 등급 R1은 그 함수를 고치고, DUP는 정본만 쓴다. 대체하면 같은 변경 단위에서 옛 함수를 삭제하고 레지스트리를 갱신한다 |
| WP-15 | 만들기 전에 이 문서 N2·N5, `.ai/context.md`, `def` grep을 확인한다. context 사용량 70%에서 분석 결과를 기록한다 |
| WP-16 | 결정은 기존 원칙·기록으로 기본안을 먼저 확정한다. 사용자 몫(spec, 회로 해석, 삭제·공유 설정 승인)만 해당 Phase의 착수 조건으로 남긴다 |
| WP-17 | 상상으로 채우지 않는다. 원문과 실제 실행 출력을 확인한 뒤 판단한다 |
| WP-18 | 현 엔진을 고치는 동안(Phase 1~5)은 L/gm_id의 권위 출처 4종(compensation / replica / metric_stage_budget / gm_target_convention)을 모두 확인한 뒤 값을 채운다. 6b부터는 SC-a 권한표가 이를 대체한다 |
| WP-19 | 새 함수는 목적지 모듈(N3.10)에 쓰고, test는 `tests/`의 test 함수로 쓴다(인라인 self-test 금지) |
| WP-20 | 패키지 최소 릴리스 나이 정책을 낮추지 않는다. 의존성 추가는 사용자 승인 |

---

## N3. 목표 아키텍처

### N3.1 흐름 GB0~GB9

| 단계 | 하는 일 | 산출물(저장 층) | 모듈 | 구현 Phase |
|---|---|---|---|---|
| **GB0 spec** | 사람 선언을 읽고 검증한다: objective, 제약값(출처 필수, 논문 출처 거부), `ports`, `value_amp`, 보상 목표(CL/GBW/PM), `driving_spec`, `gain_budget_db_override`, W3 노드전압 목표. 로드 게이트: 옛 키(`vs`), 단위, theta 선언 순서, `value_amp`와 같은 소스를 움직이는 theta 공존 | 검증된 spec + S0 지문 | MOD2, MOD3 | 6a(의미·게이트), 7b(`sizing_spec.json` 파일) |
| **GB1 구조 유도** | 교류접지 집합, diode, 미러 그룹, diffpair·tail, L 동치류(주인 = tail), vertical stack, 관계 엣지를 레지스트리 정본 함수로 유도 | S1 | MOD3 | 6a |
| **GB2 stage 분할** | SP1(N3.2)로 signal stage와 피드백 엣지·극성을 유도하고 declared stage와 대조한다. 불일치는 `review_needed` | S1v | MOD3 | 6a |
| **GB3 결합 블록** | 블록 = signal stage. 블록 경계를 넘는 관계 엣지에서 결합변수 y(K1~K4)를 추출 | S1 | MOD3 | 6c |
| **GB4 달성가능성·DOF** | LUT 곡선 검사, 블록별 gain 상한 표, 구조 DOF와 수치 rank. 불가하면 탐색 전에 정지 | S2 memo | MOD4 | 6c |
| **GB5 보상** | (CL, GBW, PM) -> (Cc, Rz, gm_i). 기생 pole로 L 상한 | S2 | MOD4 | 7b |
| **GB6 gain 할당** | 3층: 블록 DP / y 좌표강하 / SLSQP 미세조정. `gain_budget_db` 출력 | S2, S3 | MOD6 | 7b |
| **GB7 DC 해석** | 노드전압 정본, writer 티어 W0~W4, 순환 블록 고정점, 봉인 | S2 | MOD4 | 6b |
| **GB8 metric** | 전체회로 MNA gain, 블록 gain과 잔차, 감도 게이트, metric 티어 분류, 전력·면적 | S2 | MOD5 | 7a |
| **GB9 전역 탐색·검증** | 실패 캐시, 시작점 선택, 준난수 전역 샘플, 아카이브, SPICE 독립 검증 | S3 | MOD6, MOD5 | 5(캐시·θ*), 7c(나머지) |

**실행 구조**: GB0~GB4는 S0 지문마다 한 번, GB5는 spec마다 한 번 돈다. GB6의 각 층이 후보 하나를 평가할 때마다 평가 커널(N3.5)이 **GB7(DC 고정점) -> 봉인 -> GB8(metric)**을 실행한다. 즉 표의 순서는 논리 의존이고 실행은 중첩이다. gm_id·L 선택(GB6)과 노드전압(GB7)은 한 평가 안에서 같은 순환 블록으로 함께 수렴한다.

**막으려는 실패**(원자료 `review_D_gain_decomposition_incidents.md`)

| ID | 근본 원인 | 막는 단계 |
|---|---|---|
| RC1 | stage gain을 소자 이름 목록으로 정의(부하·캐스코드·경계를 사람이 선언) | GB2, GB8 |
| RC2 | KVL/KCL 확인 없이 metric을 계산하고 기준선으로 고정 | GB7 봉인 |
| RC3 | 목표·배분·파생값의 출처 미기록 | GB0 출처 필수, GB4 |
| RC4 | 독립 참조 없이 정식화를 확정(정의상 참인 검증) | GB8 감도 게이트, GB9 SPICE, V2~V4 |
| RC5 | gain과 같은 자유도를 쓰는 결정을 국소적으로 따로 함 | GB3, GB6 |

### N3.2 stage 분할 규칙 SP1

1. **교류접지 집합**: (1) 레일 (2) gate에만 붙고 구동되지 않는 넷 -- 입력 포트·수동소자 단자·이상원 단자는 제외 (3) 이상 전압원 단자. J1의 결론(replica bias 예외)은 이 집합의 예외 목록으로 반영한다.
2. **여기 모드**: metrics 선언의 `(excite, sense)` 집합에서 모드를 모은다. 모드 선언이 없는 회로는 차동모드(DM)만 만든다.
3. **DM 뷰**: `find_structural_symmetry_candidates`의 대칭 대응으로 넷을 짝짓는다. 자기대응 넷은 가상접지로 둔다. 대응이 없는 소자는 DM 뷰에서 빼고 목록으로 보고한다. 단일출력 회로는 출력-대응 쌍을 제거한다.
4. **엣지와 비용**: gate->drain 비용 1, source->drain(캐스코드)·gate->source 비용 0, diode 노드 게이트의 gate->drain 비용 0(미러). 예외: source 노드가 전압 구동인 CG의 source->drain은 비용 1(규칙 5). 입력 넷에서 0-1 BFS 최소 비용이 stage 번호다. DM 뷰에서는 입력쌍 공통 소스가 자기대응 넷(가상접지)이라 gate->source 우회로가 끊긴다. 이 조합이 4개 회로에서 실측한 규칙이다(원자료 `probe_stage_partition.result.md`의 R3(DM/R2)). DM 뷰가 아닌 전체 회로에 같은 비용을 쓰면 우회로 때문에 입력단 stage 번호가 0으로 떨어지므로 SP1은 DM 뷰에서만 쓴다.
5. **셀과 stage 경계**: DM 뷰의 신호 경로에서 모든 트랜지스터를 셀(CS/CG/CD/pass)로 분류하고, 셀마다 입력 노드의 구동 종류(전압/전류)를 기록한다. stage 경계는 단자 이름이 아니라 **입력 노드 구동 종류 하나로** 정한다.
   * 전압 구동 입력을 받아 전류를 고임피던스 노드로 내보내는 셀(CS, source가 전압 구동인 CG) = **새 gain stage 시작**(번호 +1).
   * 전류 구동 입력을 받는 CG = 캐스코드. **같은 stage를 잇는다**(앞 셀의 출력저항을 키우는 전류 버퍼이며, 입력 소자와 L·gm_id를 함께 정한다 -- DEC-04).
   * 전압 구동 입력을 받아 저임피던스 노드로 내보내는 셀(CD, pass) = 전압 버퍼. gain stage 번호는 올리지 않고 버퍼 구간으로 표시한다(독립 블록 여부는 J10).
   * 근거: 캐스코드를 별도 stage로 나누면 그 stage의 전압 이득(source 노드 -> drain)과 앞 stage의 이득(≈ −1)이 같은 전류와 같은 출력저항을 공유해 분리성이 깨지고(결합 블록 DP 성립 조건, N3.7), 입력+캐스코드 동시 결정(DEC-04)과 보상 레지스트리의 stage 수(`compensation.stage_devices`)와도 어긋난다. 4개 회로 실측: CG 셀 8개(파일럿 M9a/M9b/M18a/M18b, folded M5/M6, nmcnr M106/M107)가 **모두 전류 구동**이고 source가 전압 구동인 CG는 없다. 파일럿 선언 `gain_stages_sum`은 캐스코드 M2a/M3a를 입력 M1a/M4a와 같은 stage에 둔다(원자료 `probe_cg_cascode_stage.result.md`). 따라서 이 규칙은 4개 회로에서 실측 규칙 R3(DM/R2)과 같은 결과를 내고, CG 증폭기·follower까지 같은 기준으로 처리한다.
6. **stage 구성**: 출력노드 = stage 안에서 신호가 마지막으로 도달해 다음 stage 입력(다음 CS의 gate) 또는 출력 포트로 넘어가는 노드. CS·CG 사슬로 끝나면 drain 노드, CD·pass로 끝나면 그 소자의 출력 단자 노드다. 임피던스 등급(높음 = drain만 붙음 / 낮음 = 출력 source가 붙음)을 노드 속성으로 기록한다. input = gate가 stage 입력 넷에 붙은 소자, cascode = CG 사슬, follower = CD, pass = pass 구성 소자, load = 드레인이 출력노드(또는 중간 고임피던스 노드)에 붙고 게이트가 바이어스·미러 넷인 소자, tail = 드레인이 입력쌍 공통 소스 노드에 붙은 소자. **블록 노드 집합** = stage 입력 넷부터 출력노드까지 신호 경로에 있는 노드 전부.
7. **피드백**: 수동소자 엣지와 역방향 MOS 엣지를 피드백으로 분리한다. 극성 = MOS만 거치는 복귀 경로의 저주파 부호. 부호가 섞이면 `review_needed`(Cc–Rz 직렬 루프는 J7).
8. **검증 기준**(구동 종류 판정은 규칙 1의 교류접지 집합이 먼저 확정돼야 한다 -- 교류접지 없이 BFS하면 레플리카 바이어스 경로 때문에 파일럿 M2a/M3a가 CG로 잡히지 않는다, J1): input·cascode·tail 멤버십은 declared stage와 대조한다(4개 회로 실측 100% 일치, 원자료 `probe_stage_partition.result.md`). 출력노드와 load·G_out 기여 소자는 J5·J6 공동분석으로 `ratified`된 대조표와 대조한다. declared stage에 없는 부하(파일럿 Vom1의 M19·M18a·M18b)는 결함 선언이지 규칙의 오류가 아니다. 4개 회로에 drain이 레일에 붙은 순수 follower는 없고, source·drain 단자로 신호를 넘기는 소자는 파일럿 class-AB floating battery(M9a/M9b: Vop1↔Vg15, M18a/M18b: Vom1↔Vg25)와 folded M8(gate Vg7, source Vg10)이다(실측 원자료 `probe_common_drain.result.md`, 6a design이 DM 뷰에서 재측정). 따라서 CD 분류의 4개 회로 검증은 "분류 발동 소자 = 이 목록"까지이고, 순수 follower 회로 추가 여부는 U-22다.
9. **graph로 정하지 않는 것**: 어느 여기 모드가 스펙인가, class-AB 출력단 gm 합산 방식과 floating battery의 stage 출력 노드(J3), follower를 독립 블록으로 둘지 앞 stage에 흡수할지(J10), 자유 노드 배분 기준(GB6 목적함수가 정한다), LUT 비단조 자체(GB4가 해법을 고른다).

### N3.3 Circuit State Graph 층

| 층 | 내용 | 키·무효화 | 저장 |
|---|---|---|---|
| **S0 지문** | topology 정규화 JSON 해시 / LUT 파일 내용 해시 + 생성 메타(`lut_conditions_from_npz`: corner, temp) / spec 전체 해시(제약값 포함) / 유도 규칙 코드 해시(S1 유도 함수 호출 폐포의 `ast.dump`, docstring·모듈 경로 제외) / metric 정의 코드 해시 | -- | 메모리 |
| **S1 구조** | 노드 {name, terminals[(device, terminal)], is_rail, ac_ground_class, port_role} / 소자 {name, kind, d, g, s, b, is_diode} / 수동소자 {name, type, nodes} / 관계 엣지 {type, members, status, evidence{rule, nets}}. type ∈ `equal_vgs`, `vds_eq_vgs`, `same_as`, `budget_ref`, `stacked_vsb`, `matching_offset`, `matching_ratio`, `l_class`, `kcl_group`, `kvl_branch`. 개념마다 정의 하나 | topology 해시 + 유도 규칙 해시 | 메모리(엔진 유도, 매 실행 재생성) + `library/<name>.structure.json`(ratified 기록만, 오케스트레이터가 씀, 6a) |
| **S1v 여기 뷰** | 모드별: SCC 응축 신호 DAG, 피드백 엣지·극성, signal stage 목록 | S1 키 + 모드 | 메모리 |
| **S2 동작점** | 노드 DC 전압(경로별 값·충돌), 소자 op(ID, gm_id, L, W, gm, gds, cgg), KCL 전류와 출처, 스택 창·slack, 노드 cap/G, metric. 필드마다 {writer 티어, 버전 카운터} | memo 키 = 계산 블록 입력의 내용 해시 | LRU(상한 N3.5) |
| **S2p 사전정보** | 직전 수렴 스냅샷. 초기값·시드로만 쓰고 결과값으로 쓰지 않는다 | 없음(힌트) | 메모리 |
| **S3 탐색 기억** | 평가 기록(θ, ok/fail, 실패 분류·소자·margin, metric, 제약 여유, 분지 id), 실행 기록(θ*, start별 결과), 유도 임계값 | S0 전체 지문 | `library/<name>.search_archive/<S0 지문>/{evals,runs}.jsonl`(append-only, 케이스마다 flush, `.gitignore` 등록). 지문이 다른 디렉터리는 읽지 않는다. Phase 5~6a 전에는 N3.5 임시 지문을 디렉터리 이름으로 쓴다 |

**status 전이**

| 전이 | 누가 | 조건 |
|---|---|---|
| (생성) -> `declared` | 사람 선언을 로드할 때 엔진 | topology/spec에 적힌 사실 |
| (생성) -> `derived` / `proposed` | 엔진 | 규칙과 connectivity 증거가 있으면 derived, 증거가 부족하면 proposed |
| `derived`/`proposed` -> `review_needed` | 엔진 | declared와 불일치, 또는 규칙이 해석 불가를 보고 |
| `review_needed` -> `ratified` | 오케스트레이터 | 공동분석 결론 + 승인 기록 id |
| `ratified` -> `review_needed` | 엔진 | S0의 topology·유도 규칙 해시 변경 |

shadow 대조 보고와 그 밖의 실행 산출물은 `runs/<run_id>/`(`.gitignore` 등록)에 쓴다. 평가 경로가 읽는 상태는 `declared`, `derived`, `ratified`뿐이다. 6a(shadow)에서는 평가가 기존 declared 경로로 계속 돌고 유도 결과는 대조 보고만 한다. 유도 값을 평가가 소비하기 시작하는 6c부터 `review_needed`가 남아 있으면 GB4 전에 정지한다.

### N3.4 노드전압 writer 티어 W0~W4

| 티어 | 쓰는 대상 | 출처 |
|---|---|---|
| W0 | 레일 노드 | spec `vdd`, gnd |
| W1 | 구조 항등으로 묶인 노드 변수: diode(VGS=VDS), 노드를 공유하는 `budget_ref`, `vds_match_vgs_of`(D1에서 항등식) | S1 관계 엣지 |
| W2 | 물리 종속 블록: 노드전압 ↔ gm_id ↔ W, 적층 diode(`stacked_vsb`), class-AB 배터리 KVL | 순환 블록 고정점 |
| W3 | 사람이 선언한 노드전압 목표 | `sizing_spec.json` human.node_voltage_targets(`diode_stack.target_net`, `Voc_des` 계열을 이관) |
| W4 | 자유 노드 | GB6 중층(결합변수 y)이 창 안에서 배정 |

* 노드 하나에 writer는 하나다. "먼저 쓴 값 존중"은 없다. 두 writer가 같은 노드를 쓰면 봉인 위반이다.
* 소자 vds/vgs/vsb는 노드전압 차이의 읽기 전용 파생이다. `set_device_vds`는 W 티어 setter의 파생으로 바뀐다.
* 노드 하나에 값 하나이므로 "스택 합 ≠ vdd"는 표현할 수 없다(검사 대상이 아니다). writer 경합과 버전 불일치는 봉인이 거부한다.

### N3.5 상태 계약·평가 커널·최적화 계층

**상태 계약**(강제 test는 `tests/contracts/`, 담당 Phase 6b. SC-e는 7a metric 분류에서 소비)

| ID | 규칙 | 강제 test |
|---|---|---|
| SC-a 단일 writer | S2 필드 × writer 티어 권한표. 모든 쓰기는 타입 setter로만. 원시 대입은 grep 게이트로 금지 | 원시 대입 grep 0 + 순서 섞기 불변(IC2) |
| SC-b 버전 있는 유도 | 필드마다 쓰기 카운터. 파생 필드는 입력 카운터를 기록하고, 봉인이 불일치를 거부. 재사용 시 `setdefault`로 기존 값을 건너뛰지 않는다(V6 lint 대상) | 옛 vsb 버전으로 계산된 W를 넣은 픽스처를 봉인이 거부 |
| SC-c 순환 = 명시적 고정점 | 계산 블록 입출력 선언으로 만든 유도 DAG의 SCC를 순환 블록으로 반복. 수렴 판정·반복 상한은 N3.6, 비수렴은 NONCONVERGENT 실패(N3.14) | 수렴 픽스처 + 비수렴 픽스처 거부 |
| SC-d 내용 지문 무효화 | 지문 불일치 = 캐시 없음. 픽스처 spec은 `origin: fixture`와 자기 지문을 선언하고 정본 유도 임계값을 읽지 않는다(U-04) | 지문 변경 시 미적중 |
| SC-e reader 기록 | metric과 계산 블록은 실제로 읽은 S2 필드를 기록한다. metric 티어 분류(N3.8)와 영향 집합이 이 기록을 쓴다 | 선언 support와 실제 read가 다르면 기록이 이긴다 |

**평가 커널**: `_evaluate`를 계산 블록으로 나눈다 -- ① 보상 ② 전류(KCL, `value_amp`) ③ L 유도 ④ 스택·순환 블록(W1/W2 + gm_id pass) ⑤ W 계산 ⑥ metric. 블록마다 입력·출력을 선언하고, 결과는 입력 내용 해시로 S2에 memo한다. 전역 metric은 봉인 스냅샷마다 한 번 계산한다. 조인트 스캔 memo 키는 (그룹 L, vds, vsb, gm_total, 고정 gm_id).

**S2 LRU 상한** = (DEC-34 식의 샘플 수 + 선언 `n_starts` × 평가 계수기로 실측한 SLSQP 1회 평가 수) × 계산 블록 수. 초과분은 LRU로 밀어낸다.

**최적화 계층**

* **실패 캐시**: 키 = (θ 각 성분의 `float.hex`, S0 지문). 실패는 N3.14 구조화 실패로 저장한다. 제약 함수는 상수 페널티 대신 정규화 위반량(margin)을 돌려준다. S0가 없는 Phase 5~6a 전에는 지문 자리에 임시 지문(topology 파일 내용 해시 + spec 전체 해시 + 엔진 소스 파일 해시)을 쓰고, 6a에서 S0로 바꾼다. 임시 지문 레코드는 그 뒤 읽지 않는다(SC-d).
* **시작점**: 지문이 일치하는 S3 feasible 점 상위 `n_starts`개(선언값) -> 부족하면 선언 x0. "지난 해 ± 창"은 추가 시작점으로만 쓴다(전역 bounds를 줄이지 않는다).
* **전역 샘플 수(DEC-34)**: `N = floor((300 s − T_fixed) / t_eval)`. `T_fixed` = 같은 실행에서 샘플을 뺀 단계(presolve, GB0~GB5, DP, 좌표강하, SLSQP) 실측 합, `t_eval` = warm 평가 실측 중앙값. 샘플러는 `scipy.stats.qmc.Sobol`(scipy는 이미 의존). 7c 전에는 그 Phase에 존재하는 단계만으로 `T_fixed`를 실측해 같은 식으로 N을 계산하고, 판정 기록에 어느 단계를 넣었는지 적는다(6b LRU 상한, 6c DOF 표본 수가 이 N을 쓴다).
* **분지**: feasible 샘플의 θ 격자 인접 연결성분, 또는 DP 결정 벡터가 다른 해. 서로 다른 분지에서 SLSQP를 시작한다.
* 한 기준점의 수치 섭동으로 차원을 동결하지 않는다. 무효화는 구조적 쓰기 집합(SC-e 영향 집합)으로만 한다.

### N3.6 봉인 게이트와 허용오차(DEC-32)

**봉인 항목**(metric 계산 전, 모든 평가)

| # | 항목 | 판정 |
|---|---|---|
| 1 | 노드 충돌 | 같은 노드에 도달한 경로별 값의 최대 차 ≤ tol_V |
| 2 | VGS 정합 | 모든 소자(diode 포함)에서 노드 차 VGS와 `vgs_for_gm_id(gm_id, L, vds, vsb)`의 차 ≤ tol_V |
| 3 | KCL 잔차 | 내부 노드마다 |ΣI| ≤ tol_I. `exclude_nets`는 사유가 선언된 넷만 |
| 4 | 버전 일치 | 파생 필드의 입력 카운터 = 현재 카운터(정확 일치) |
| 5 | writer 유일 | 노드마다 writer 하나 |

**허용오차 식**

* `tol_V` = (kind, L 앵커, VDS)별 LUT leave-one-out 보간 오차(VGS 기준)의 최댓값. 계산 함수는 `tests/probe_interp_scheme_loo.py`의 방법을 MOD1 함수로 승격한다.
* `tol_I` = `tol_V` × 해당 순환 블록 소자 gm의 최댓값.
* 반복 상한: bisection이면 `ceil(log2(구간폭 / tol_V))`. 고정점 반복이면 수축 사상의 오차 한계 `|x_k − x*| ≤ q^k·|Δ0| / (1 − q)`로 `q^k·|Δ0| / (1 − q) ≤ tol_V`가 되는 최소 k를 상한으로 한다. q = 최근 두 연속 변화비의 최댓값이며 매 반복 갱신한다. q ≥ 1인 반복에서는 상한을 갱신하지 않고 직전 상한을 유지하며, q ≥ 1이 두 번 연속 관측되면 NONCONVERGENT(한 번은 초기 과도로 본다).
* 같은 `tol_V`를 IC1 test의 허용오차와 SPICE 비교(N3.8)의 노드전압 허용오차로 쓴다.

### N3.7 결합 블록·달성가능성·DOF·할당

**결합 종류**

| ID | 결합 | 처리 |
|---|---|---|
| K1 | 블록 출력노드의 부하 소자가 다른 블록의 미러·L 동치류에 속함 | y |
| K2 | 두 블록 이상에 걸친 `equal_vgs`(공유 VGS) | y |
| K3 | 블록 경계를 넘는 `stacked_vsb` | y |
| K4 | 두 블록이 공유하는 스택의 노드전압 | y(W4) |
| K5 | 다음 stage 입력 Cgg가 노드 pole을 거쳐 PM에 영향 | GB5·GB8(`parasitic_pm_deg`) |
| K6 | 보상이 고정한 gm | GB5 입력 |

* **결합 잔차 측정(6c 첫 작업)**: 기존 6480조합 데이터(`tests/probe_mirror_gain_ranking.py`)로 블록 gain 합과 전체회로 MNA gain의 차를 잰다. 0이 아닌 블록 쌍은 해당 metric을 MT3로 표시한다.
* **LUT 곡선 검사(로드 시)**: 곡선이 단조면 역산 허용, 비단조면 격자 전수만 허용, 단위 불일치면 로드 거부.
* **블록 gain 상한**: `A_i,max = max(블록 i의 국소 소신호 모델 gain)` over gm_id 격자 × LUT L 앵커 × W4 창의 VDS × y 가능역. 격자 전수, S2 memo. 7b에서 GB5가 고정한 gm으로 다시 계산한다.
* **달성가능성**: Σ A_i,max < 총 gain 제약이면 INFEASIBLE_TARGET(탐색 전). LUT·구조만으로 상한을 계산할 수 없는 제약은 "상한 미상"으로 보고한다.
* **DOF**: 변수(스택 내부 노드전압 k−1, 소자 gm_id, L 동치류 L)와 등식(diode VGS=VDS, `equal_vgs`, `budget_ref`, `stacked_vsb`, KCL)으로 구조 rank를 센다(부등식은 경고). 수치 rank는 θ 표본에서의 Jacobian(`numpy.linalg.matrix_rank` 기본 허용오차, FD 스텝 = 해당 변수의 LUT 격자 간격, 표본 수 = DEC-34 식의 샘플 수 안). 결과 `DofReport{status: ok | underdetermined | overconstrained, 경쟁 목표 쌍}`. overconstrained는 INFEASIBLE_TARGET.

**3층 할당(DEC-45)**

| 층 | 명세 |
|---|---|
| 내층 블록 DP | y 고정. 상태 = (블록 순서, 누적 gain bin), 결정 = (gm_id 격자점, L 동치류의 LUT 앵커), 비용 = 전력(U-10 정의), 면적 제약이 있으면 면적 bin 추가. gain bin 해상도 = 인접 격자점이 만드는 블록 gain 차의 최솟값(계산) |
| 중층 좌표강하 | y의 각 차원을 자기 가능역의 1-D 격자에서 순서대로 최소화. 공유 VGS는 gain 기준(DEC-10). 종료 = 한 바퀴에 y 불변, 또는 목적값 감소 ≤ DP 목적값 분해능. 상한 = y 격자 점 수의 합(유한 격자·비증가라 종료 보장) |
| 외층 미세조정 | DP·좌표강하 해를 시작점으로 SLSQP(`SPECS[circuit]["slsqp_kwargs"]`). MT3 제약은 이 층에서만 판정 |

검증: 파일럿과 한 개 회로에서 **전체회로 MNA를 목적·제약으로 쓰는 축소 격자 전수탐색**(다른 모델)과 대조, 최적 목적값 차 ≤ 격자 분해능.

**보상 규칙(GB5)**

* 보상 레지스트리 함수가 stage 수에서 `solves_for`·gm 참조를 유도한다(2단 하드코딩 금지).
* `ID_source` 타입: `kcl` / `ideal_source_ref` / `kvl_battery_loop`(class-AB 정지전류).
* `compensation: null`(단일단): 기본안 `gm_1 = 2π·GBW·CL`(U-12 확정 전까지 기본안으로 구현하지 않는다).

### N3.8 metric

* **gain**: 제약 판정은 `smallsignal_gain_db`(전체회로 MNA, DM 모드) 하나. 회로별 이관: 파일럿 `gain_stages_sum` -> `smallsignal_gain_db`, folded `_metric_folded_cascode_gain_db` -> `smallsignal_gain_db`(ports U-08 선행), nmcnr `_metric_nmcnr_gain_db` -> `smallsignal_gain_db`(ports 선행), two_stage는 이미 MNA.
* **블록 국소 소신호 모델**: 블록 노드 집합(N3.2-6)만 미지수로 둔 절점방정식을 푼다. 블록 입력 넷은 단위 신호로 구동하고, 블록 밖 노드는 DM 뷰의 교류접지 또는 다음 블록 입력의 부하 어드미턴스(다음 CS 게이트 용량 등)로 고정한다. 소자는 단자별로 gm·gmb·gds·cgg를 스탬프하므로 CS·CG·CD·pass를 따로 분기하지 않는다. 블록 gain = 출력노드 전압 / 입력 전압(dB, 저주파).
* **gmb**: LUT에는 gmb 열이 없다. LUT VS 축(|VSB|)에서 `gmb = ∂ID/∂VSB`를 수치미분으로 유도하는 함수를 MOD1에 두고, 블록 국소 모델과 전체회로 MNA가 같은 값을 쓴다(현 MNA가 gmb를 넣지 않는 것은 7a에서 함께 고친다).
* **잔차**: 잔차 = MNA gain − Σ 블록 gain. 블록 국소 모델은 블록 밖을 고정한 모델이라 전체회로 MNA와 독립이며, 전체 MNA 해를 잘라 만든 전압비의 곱으로 분해하는 정의는 금지(정의상 참).
* **감도 게이트**: 봉인 스냅샷마다 영향 집합(SC-e)에서 분해 metric이 읽지 않는 소자를 건드리는 θ 방향으로 섭동한다. 분해 값 변화 ≤ ε 이고 MNA 값 변화 > ε 이면 오류. ε = MNA 선형해 잔차 노름에서 계산한 수치 분해능.
* **metric 티어**: support(SC-e) ⊆ 블록 하나 -> MT1, 블록별 항의 합 -> MT2, 그 외 -> MT3. MT1·MT2는 내층·중층, MT3는 외층에서만 쓴다.
* **전력**: 정의는 U-10(후보 `sum_current` / `_metric_supply_current`). 결정 전까지 보고에 "스택 중복계상 전력"임을 명시한다.
* **`verified_by`**: {script, oracle_kind, max_error, metric_code_hash, date}. metric 코드 해시가 바뀌면 무효. 유효한 `verified_by`가 없는 metric은 제약으로 쓸 수 없다(적용 순서 U-11).
* **SPICE 독립 검증**: `write_spice_netlist(S1, S2, models) -> path`, `run_ngspice_op_ac(path) -> {nodes, ids, ac}`(`C:\ngspice\Spice64\bin\ngspice_con.exe -b`, 모델 경로는 LUT 생성 메타에서 읽는다). 비교량과 허용오차: 노드전압 `tol_V`, 소자 ID `tol_V × gm`, AC gain = 노드 허용오차를 소신호 감도로 전파한 값. LUT에 없는 접합용량 때문에 못 세는 노드는 제외하지 않고 별도 열로 보고한다.

### N3.9 L 결정 규칙

| ID | 규칙 |
|---|---|
| LR1 | S1 L 동치류 멤버는 L을 공유한다. 주인은 gain stage tail(DEC-17). 종류가 다른 소자 간 VGS 매칭은 L을 공유하지 않는다 |
| LR2 | 매칭 그룹의 L은 전원 동시에 바꾼다 |
| LR3 | LUT 실측 L 앵커(12개) 밖으로 외삽하지 않는다. spec `L_candidates`는 탐색 격자이며 앵커 범위 안이어야 한다 |
| LR4 | L 증가가 항상 gain 이득은 아니다 -- 격자 전수로 판단한다 |
| LR5 | 초기 L 목표: mirror = kind별 knee(`measure_L_knee`, 격자 전체 중앙값), bias_replica = `feasible_L_window` 하한, cascode·signal = knee 목표를 거부하고 theta 탐색이 정한다(`derive_role_L` 가드 유지). 모두 `feasible_L_window`로 clamp한다 |
| LR6 | L 상한은 `parasitic_pm_deg >= PM_target_deg`, 하한은 mismatch 임계값(출처 U-17)이다 |
| LR7 | gain이 부족하면 L을 올리기 전에 W4 자유 노드전압을 재배분한다(W1/W2 노드 제외). GB6 중층에서 적용 |
| LR8 | L을 바꾸면 행 폭·n_fingers(`check_box_shape`, finger 폭 호환)를 재판정한다. 오일러 패스는 L과 무관하다. 같은 물리 행 안에서 L은 달라도 되지만 finger 폭은 같아야 하고, 매칭 그룹이면 LR2가 우선한다. branch(`vertical_stack_id`, 전기)와 row(물리 행)는 다르다: PMOS/NMOS는 kind별 행으로 먼저 나뉘므로 같은 branch 안에서 L이 달라도 된다 |
| LR9 | L 변경은 사이징↔레이아웃 수렴 루프(MOD8) 안에서만 하고 매 반복 `check_stick_diagram_coverage`를 다시 돈다. 현 엔진에는 루프가 없다(루프는 7b에서 MOD8에 구현) |

### N3.10 모듈 구조

규칙: **import는 번호가 작은 모듈 쪽으로만**, 순환 0, 파일당 한 책임. 함수별 목적지는 레지스트리의 "이관 목적지" 열이 정본이고, Phase 3 design 문서가 그 열에서 이관표와 실제 의존 그래프를 생성한다.

| ID | 파일 | 책임 | 대표 대상 |
|---|---|---|---|
| MOD1 | `gmid_lut.py` | LUT 인터페이스·보간·역산·곡선 검사·보간 오차 | `GmIdLUT`, `SemiEmpiricalGmIdLUT`, `_multilinear_interp`, `_solve_vgs`, `lut_conditions_from_npz`, gmb 유도(`∂ID/∂VSB`) |
| MOD2 | `topology_authoring.py` | topology·spec 로딩, 스키마·단위·참조·선언 순서 게이트, 구조 제안 | `load_topology`, `validate_metric_units`, `validate_no_legacy_vs_key`, `require_declared_spec_source`, `validate_theta_declaration_order` |
| MOD3 | `circuit_state_graph.py` | S0 지문, S1 구조 유도(개념당 정본), S1v, 결합 블록 | `is_diode_connected`, `true_current_mirror_groups`, `l_sharing_classes`, `l_class_owners`, `vgs_alias_map`, `_kcl_and_matching_edges`, `trace_*_branches`, `propagate_topology_forced_currents`, `spec_fingerprint` |
| MOD4 | `gmid_sizing_engine.py` | 소자 사이징, DC 해석(W 티어·순환 블록·봉인), 달성가능성·DOF, 보상 레지스트리, theta feed | `size_transistor`, `feasible_gm_ids`, `measure_L_knee`, `_hr_*`, `solve_diode_connected_vds`, `solve_stacked_diode_pair`, `apply_theta_feed`, `topology_library.py` 보상식 |
| MOD5 | `circuit_metrics.py` | metric 레지스트리, 소신호 MNA, 사후검증 metric, SPICE 대조 | `compute_metric`, `_METRICS_REGISTRY`, `build_ac_network`, `_full_circuit_response`, `estimate_mismatch_sigma` |
| MOD6 | `theta_search.py` | 평가 커널 조립, 3층 할당, 실패 캐시, 시작점, 전역 샘플, S3 | `_build_theta_evaluator`, `optimize_full_circuit_budget` 탐색부, `search_stage_budget_L_warm_start`, `presolve_warm_start`, `_optimize_theta_slsqp`, `repair_infeasible_baseline` |
| MOD7 | `stick_diagram.py` | 레이아웃만(구조 유도 함수는 MOD2·MOD3로 나간다) | 레지스트리 등급 R0 레이아웃 함수 |
| MOD8 | `sizing_layout_convergence.py` | 사이징↔레이아웃 수렴 루프 | `run_topology_pipeline_with_finger_fixup`, `revalidate_finger_override`, `resolve_stack_layout` |
| MOD9 | `instance_report_builder.py` | instance.json과 HTML 보고 | `save_instance_json` 계열, `design_report.render_html_report`(재사용, 누락 절만 추가) |
| MOD10 | `gmid_design_pipeline.py` | 유일 최상위 진입점 `run_gmid_design_pipeline(spec)` | spec을 인자로 받는다(`workspaces/`를 import하지 않는다) |

* LUT 생성(`sky130_lut_sweep.py`)과 `topology_to_markdown.py`는 도구로 남는다. `canonical_spec()`/`SPECS`는 `workspaces/run_harness.py`에 남고 MOD10에 인자로 넘긴다.
* **이동 규칙**: 모듈 하나당 이동 전용 커밋. 무변경 증명 = 이동 전후 함수별 `ast.dump`(docstring 제외) 해시 동일 + import 줄만 차이. 해시가 같은 함수는 V3 대상에서 뺀다.
* **shim**: `sizing_recipe.py`는 이관 중 명시 재수출 목록(인벤토리에서 생성, `_` 접두 심볼 포함, `import *` 금지)만 가진다. 저장소에 추적되는 파일 중 `sizing_recipe`를 import하는 파일을 전부 갱신하면 shim을 삭제한다(추적 안 되는 workspaces 스크래치는 U-03).
* 등급 D 함수는 옮기기 전에 처리한다(Phase 2). 배선을 고른 함수는 동작 변경이라 Phase 4에서 배선한다.

### N3.11 test 구조

```
skills/analog-gmid-design/assets/tests/
  conftest.py      real_lut(세션, 저장소 npz 경로 고정 + 지문 기록), toy_lut, library_dir, topology 팩토리
                   (library/*.topology.json 로드·변형만), grids, --shuffle-seed 옵션(pytest_collection_modifyitems 자체 구현)
  unit/test_mod1_gmid_lut.py ... unit/test_mod9_instance_report_builder.py
  integration/     파일럿 전체회로(L5c), 레이아웃 파이프라인(엔진 import하는 레이아웃 test), end-to-end
  contracts/       IC1~IC10, SC-a~SC-e 계약 test
  regression/      4개 회로 측정
  oracles/         test-author 소유 독립 참조구현
  legacy/          TS1 이관본(TS2 완료 시 삭제)
  tools/           정본 데이터를 갱신하는 운영 도구(code-author 소유, pytest 수집 제외)
  probes/          일회성 진단(pytest 수집 제외)
```

| 단계 | 내용 | 완료 판정 | Phase |
|---|---|---|---|
| TS0 | stick_diagram Test 16 `FAIL(예상과 다름)`의 의도 판정(U-01) -> test 또는 대상 수정 | 판정 기록 + 기준선 재생성(DEC-40 승인) | 1 |
| TS1 | 두 `if __name__ == "__main__"` 블록을 추출 스크립트(`tools/migrate/extract_selftest.py`)로 `tests/legacy/`에 본문 그대로 이관. test 커밋(legacy 추가) -> auditor 동등성 -> code 커밋(소스 블록 삭제) -> auditor 재확인. `import *` 대신 명시 import, library 경로 인자화. 추출 스크립트는 code-author가 작성하고 test-author가 Bash로 실행해 출력을 커밋한다(스크립트 실행은 Read 도구 거부 대상이 아니며, 산출물이 본문 그대로임은 auditor의 stdout 동등성으로 판정). 추출 스크립트는 선행 변경 `<id>-extract-tool`(code-author 작성, red-green: test-author가 합성 입력 파일의 추출 결과를 단정하는 test)로 먼저 병합하고, TS1 변경의 base는 그 병합 커밋이다 | `PYTHONHASHSEED` 1~5 각각에서 이관 전·후 stdout 바이트 동일 | 1 |
| TS2 | 섹션 하나 = test 함수 하나. 전역 `lut` -> fixture, 섹션 사슬 -> 명시 fixture, 거부 케이스 -> `pytest.raises`, `_drl_case` -> parametrize | 기본 순서와 `--shuffle-seed` 1~5 모두 통과 | 1 |
| TS3 | print·PASS 문자열 판정을 assert로 바꾸고 판정 없는 데모는 삭제 | `tests/**`(probes·tools 제외)에서 print·logging 인자 안의 PASS/FAIL 토큰 0(AST 검사) | 1 |
| TS5 | stdout 기준선 퇴역: `tests/baseline/` 삭제, README를 pytest 실행법으로 교체 | 기준선 참조 0 | 1(TS3 직후) |
| TS4 | 자기참조 기대값 제거(피검 식으로 기대값을 만든 test를 oracle 4종으로 교체) | 해당 결함 test가 base에서 FAIL(DF-09 등) | 4(첫 작업) |
| TS6 | probe 정리: 승격(후보 `probe_gm_id_monotonicity`, `probe_physical_consistency`, `probe_parasitic_pm_all_circuits`, `probe_role_L_derivation`, `probe_lut_L_interpolation`, `probe_revalidation_scope`, `probe_prevention_wiring`) / 삭제(U-02) / probes 이동 / 운영 도구 `derive_achievable_bounds.py`는 `tests/tools/`로 이동. probe 안의 엔진 로직 복제(IDu 식, 미러 그룹, 노드전압 전파 등)는 엔진 정본 호출로 교체. 운영 도구 이동은 code 커밋(`tests/tools/`에 추가) 뒤 test 커밋(원본 삭제)의 두 커밋으로 하고, 이 부분은 순서 4·5를 생략하지 않는다 | probe의 엔진 식 재구현 0 | 2 |
| TS7 | 계약 test: Phase 1에서 xfail(reason에 담당 Phase·만료 = 그 Phase DoD)로 선언, 담당 Phase에서 활성화(N4.1 표) | 담당 Phase DoD에서 PASS | 1~7c |

* `slow` 표식: `--durations` 실측으로 기본 실행 시간을 크게 차지하는 test에 붙이고 실측표를 판정 기록에 첨부한다. 기본 실행은 `-m "not slow"`, 병합 전 판정(V1)은 전체.

### N3.12 역할 분리

#### N3.12.1 권한

| 권한 | 주체 | 할 수 없는 것 |
|---|---|---|
| 의도(spec card, 계획·설계 문서, 승인 기록 전사) | 사용자 + 오케스트레이터 | 엔진 소스·tests 쓰기(EL1) |
| 구현(엔진 소스, 운영 도구, 레지스트리) | `gmid-code-author` | tests·기대값·기준선·픽스처 쓰기 |
| 판정 기준(tests, oracles, 픽스처, 공격 시나리오) | `gmid-test-author` | 소스 쓰기, 피검 함수로 기대값 만들기 |
| 판정 실행과 보고 수치 | `gmid-verification-auditor` | 판정 기록 외 쓰기, 작성자 보고를 증거로 받기 |

#### N3.12.2 쓰기 경로표

| 주체 | 쓸 수 있는 경로 |
|---|---|
| gmid-code-author | `skills/analog-gmid-design/assets/*.py`, `skills/analog-gmid-design/assets/tests/tools/**`, `tools/migrate/**`, `workspaces/run_harness.py`, `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`, `docs/02-design/disputes/<id>.md`(자기 변경 id만). 게이트 변경 spec card와 승인 기록이 있을 때만 `tools/gates/*.py`, `hooks/role_*.py` |
| gmid-test-author | `skills/analog-gmid-design/assets/tests/**`(`tests/tools/**` 제외). 게이트 변경 spec card와 승인 기록이 있을 때만 `tools/gates/redteam/**` |
| gmid-verification-auditor | `.ai/verification/**` |
| 오케스트레이터 | `docs/01-plan/**`, `docs/02-design/**`(disputes는 `_TEMPLATE.md`만), `docs/03-analysis/**`(레지스트리 제외), `.ai/context.md`, `.ai/approvals/**`, 사용자 확인과 승인 기록이 있는 `skills/analog-gmid-design/assets/library/*.topology.json`(U-16 확정), `skills/analog-gmid-design/assets/library/*.structure.json`(status 전이 기록만) |
| 사용자만 | `.githooks/**`, `.claude/**`, `.gitignore`, `install.py`, 부트스트랩 이후의 `agents/gmid-*.md` |

hook 판정 범위: `agent_type`이 `gmid-*`인 호출, 또는 `agent_type`이 없고 대상 경로가 위 표의 경로와 겹치는 호출만 판정한다. 그 밖(RTL agent 등)은 즉시 통과시킨다. 경로 판정은 대상 경로를 해당 worktree 루트 기준 상대 경로로 바꾼 뒤 한다. '사용자만' 경로는 Claude 세션의 도구 호출로 쓸 수 없다(EL1 거부) -- 사용자가 세션 밖에서 편집하거나, 부트스트랩 ④ 단계(hook 설치 전)에 오케스트레이터가 승인 기록과 함께 한 번 쓴다.

#### N3.12.3 변경 한 건의 흐름

**spec card** `docs/02-design/specs/<id>.spec.md`, `<id>` = `YYYYMMDD-<slug>`. 필드: 의도 / 관찰 가능한 계약 / interface card / 판정 유형(`red-green` 또는 `equivalence`) / oracle 종류와 출처 / 거부해야 할 입력 / 4개 회로 적용 여부 / 재현할 수치 / 결정 필요 항목 / 승인 기록 링크.

| 순서 | 주체 | 동작 |
|---|---|---|
| 1 | 오케스트레이터 | spec card 작성, `git worktree add ../wt/<id>-test -b role/test/<id> <base>`, interface card 생성(`tools/gates/interface_card.py`) |
| 2 | test-author | test 작성, 커밋(`Role: test`) |
| 3 | auditor | freeze: test 커밋 해시 기록. red-green이면 base에서 assertion 실패 확인(ImportError만의 실패는 신규 함수일 때만 인정), equivalence면 base에서 통과 확인 |
| 4 | 오케스트레이터 | `git worktree add ../wt/<id>-code -b role/code/<id> <test 커밋>` |
| 5 | code-author | 구현, 커밋(`Role: code`). test가 틀렸다고 보면 고치지 않고 `docs/02-design/disputes/<id>.md`에 근거를 쓰고 멈춘다 -> 1로 |
| 6 | 오케스트레이터 -> auditor | 오케스트레이터가 `git worktree add ../wt/<id>-audit <test 커밋>` 후 code 브랜치를 `--no-ff`로 병합한 상태를 만든다. auditor가 그곳에서 병합본을 검증(N4.2)하고 판정 기록을 쓴다 |
| 7 | 오케스트레이터 | merge gate(EL4) 통과 시에만 audit worktree의 병합 커밋을 base 브랜치로 fast-forward한다. 병합 커밋 트레일러는 `Role: doc`이고, EL4는 병합 커밋 대신 두 부모 쪽 커밋들의 트레일러·경로를 검사한다 |

* 판정 유형: 동작을 바꾸는 변경은 `red-green`(새·바뀐 test가 base에서 FAIL, 병합본에서 PASS). 동작을 보존하는 변경(TS1, Phase 2 통합, Phase 3 이동)은 `equivalence`(test 커밋이 그대로이고 base와 병합본 모두 통과, 추가로 TS1은 stdout 동일, Phase 3은 AST 해시 동일).
* test 전용 변경(판정 유형 `test-only`: TS2·TS3·TS5, TS6의 probe 승격·삭제): 순서 4·5를 생략한다. 증거 = 변경 전 test 집합이 base에서 통과시킨 섹션을 변경 후 test가 모두 PASS함(섹션->test 매핑표는 `10-test-separation` design).
* oracle은 4종만(N0.4). 피검 함수 호출이나 피검 식 복사, 현재 출력 붙여넣기로 기대값을 만들지 않는다.
* 판정은 PASS / FAIL / XFAIL 세 값. XFAIL은 reason에 담당 Phase와 만료(그 Phase DoD)를 적고, 만료되면 FAIL. "참고" 출력과 소비자 없는 경고 리스트는 금지.
* 기준 약화는 test-author 커밋이라도 승인 기록이 있어야 병합된다(DEC-40, V5).

#### N3.12.4 기계적 강제 EL1~EL4

| ID | 장치 | 막는 것 |
|---|---|---|
| EL1 | PreToolUse hook `hooks/role_guard.py`(Edit/Write/NotebookEdit/Bash). 쓰기 경로표 밖 쓰기를 거부하고 사유를 돌려준다. Bash에서 `--no-verify`, `git commit -n`, `core.hooksPath`, `git push`, `git reset --hard`, `git checkout -- <tests 경로>`, 경로표 밖으로의 리다이렉트를 거부 | 역할 밖 편집, 게이트 무력화 |
| EL2 | PostToolUse(Bash) + SubagentStop hook `hooks/role_diff_guard.py`. worktree `git status --porcelain`을 경로표와 대조해 위반이 있으면 exit 2로 완료를 거부. 무시 목록 = `.gitignore` 대상(`library/*.search_archive/`, 실행 산출물 `runs/`를 `.gitignore`에 등록) + `__pycache__/`, `.pytest_cache/`(무시 목록 변경은 사용자만) | 쓰는 방법과 무관한 역할 밖 변경 |
| EL3 | `.githooks/pre-commit`에 `tools/gates/role_commit_gate.py` 추가. staged 경로가 경로표와 겹치면 `Role: code|test|audit|doc` 트레일러 필수. 소스와 `tests/**`(`tests/tools/**` 제외)를 한 커밋에서 바꾸면 차단, code 커밋이 `tests/**`(`tests/tools/**` 제외)·기준선·conftest를 바꾸면 차단. python이 없으면 기존 agent 검사와 역할 검사 모두 차단(skip 금지) | 코드와 기준 동시 변경 |
| EL4 | `tools/gates/merge_gate.py <base>..<branch>`. 모든 커밋의 트레일러·경로·브랜치 역할 일치를 사후 재검사하고(topology.json diff는 승인 기록 필수, U-16), 판정 기록 존재 + test 커밋 해시가 freeze 해시와 같음 + 판정 유형별 증거 + auditor PASS를 확인. 하나라도 없으면 거부 | 앞 겹을 모두 우회한 커밋 |

한계: 경로 기반 Read 거부는 Read 도구만 막고 Bash 읽기는 못 막는다(Windows에는 파일시스템 sandbox가 없다). test-author의 소스 열람은 V3·V4가 결과로 잡는다.

#### N3.12.5 기록 양식

* **판정 기록** `.ai/verification/<id>.json`: `id`, `spec_card`, `evidence_type`(red-green / equivalence / test-only), `base_commit`, `test_commit`, `red{test_ids, failure_hashes}` 또는 `equivalence{commands, outputs_hash}`, `code_commit`, `checks{V1..V10: PASS|FAIL|N/A + 근거}`, `reproduced_numbers[{name, value, command}]`, `approvals[]`, `auditor_run{time, worktree, commands}`.
* **승인 기록** `.ai/approvals/<id>.md`: 사용자 원문 인용, 날짜, 대상(diff 해시 또는 결정 ID), 범위. 오케스트레이터만 쓴다. V5는 diff 해시 일치로 판정한다.
* **dispute** `docs/02-design/disputes/<id>.md`: 문제의 test, 근거(oracle 또는 사용자 원문), 요청.
* **interface card**: 기존 함수는 AST 시그니처 + docstring 첫 단락, 신규 함수는 spec card의 시그니처 절.
* **보고 수치**: spec card "재현할 수치" 절의 항목만 auditor가 명령과 함께 재실행해 판정 기록에 적는다. 최종 보고는 판정 기록의 값만 인용한다.

#### N3.12.6 부트스트랩과 산출물

부트스트랩 순서(Phase 0.5): ① 오케스트레이터가 agent 정의 3개, hook·게이트 스크립트, 양식 초안을 작성하고 `.gitignore`에 `library/*.search_archive/`, `runs/`를 등록(이 단계에 한한 예외, 사용자 승인) ② 더미 hook이 stdin을 파일에 기록하게 해 세 역할과 메인 세션에서 hook 입력 필드를 실측 ③ 공격 시나리오·과거 사례 재생(N4.3)을 실행해 로그를 사용자에게 제시하고 승인 기록 ④ `python install.py --only agents --project .`, `python install.py --only hooks --project .`로 설치(DEC-41), `.githooks/pre-commit` 갱신 ⑤ 이후 게이트 변경을 포함한 모든 변경은 N3.12.3 흐름으로.

| 산출물 | 경로 |
|---|---|
| agent 정의 | `agents/gmid-code-author.md`, `agents/gmid-test-author.md`, `agents/gmid-verification-auditor.md`(`agent-quality/check_agents.py` 통과, frontmatter `isolation`은 쓰지 않는다 -- worktree는 N3.12.3에서 오케스트레이터가 만든다) |
| hook | `hooks/role_guard.py`, `hooks/role_diff_guard.py` |
| 게이트·검사 도구 | `tools/gates/{role_commit_gate, merge_gate, mutate_changed, test_lint, weakening_diff, source_lint, reachability, interface_card, import_layering}.py` |
| 공격 시나리오·재생 | `tools/gates/redteam/` |
| 양식 | `docs/02-design/specs/_TEMPLATE.spec.md`, `docs/02-design/disputes/_TEMPLATE.md`, `.ai/verification/_schema.json`, `.ai/approvals/_TEMPLATE.md` |

### N3.13 임계값 도출(bisection, DEC-22)

1. 대상 제약의 선언값을 `B_hi`로 둔다. `B_lo`는 절반씩 내리며 탐색이 실패할 때까지 확장한다(확장 횟수 상한 = 반복 상한 식과 같은 방식으로 계산).
2. 각 스텝은 `B = (B_lo + B_hi)/2`로 두고 그 회로의 선언 탐색 인자(`SPECS[circuit]["slsqp_kwargs"]`) 그대로 원래 탐색을 돌린다. 성공 -> `B_hi = B`, 실패 -> `B_lo = B`.
3. 종료: `(B_hi − B_lo) / B_hi` ≤ 그 metric의 격자 분해능(spec 격자가 만드는 최소 metric 차, 계산).
4. 답은 마지막으로 성공한 `B_hi`이고, 선언 `n_starts`개의 서로 다른 시드에서 **전부 성공**해야 채택한다.
5. 선언에 `value`와 `_derived{지문, 스텝 이력, 시각}`을 기록한다. `value_from_constraint`로 이 값을 참조하는 제약은 함께 움직인다(의도된 결합).
6. 구현: `achievable_metric_bound(mode="bisect")`. 한 스텝이 전체 탐색 1회라 한 번 재서 기록하고 이후 읽기만 한다. 호출 도구는 기존 `derive_achievable_bounds.py`(TS6에서 `tests/tools/`로 이동)를 재사용한다.

### N3.14 공통 실패 규약

| 분류 | 발생 | 예외(모두 `InfeasibleSizingError` 하위) | 탐색 중 처리 | 파이프라인 exit code(서로 다른 비0 규약값, 분류 순서대로 배정) |
|---|---|---|---|---|
| STRUCTURE_UNRESOLVED | `review_needed` 잔존(6c 이후), `undetermined` 노드 | `StructureUnresolvedError` | 탐색 시작 전 정지 | 2 |
| INFEASIBLE_TARGET | GB4 달성 불가, DOF overconstrained | `InfeasibleTargetError` | 탐색 시작 전 정지 | 3 |
| NONCONVERGENT | 순환 블록 반복 상한 도달 | `NonconvergentError`(잔차 포함) | 실패 기록(margin = 잔차) | 4 |
| SEAL_VIOLATION | 봉인 항목 위반 | `SealViolationError`(항목·소자·크기) | 실패 기록(margin = 위반 크기) | 5 |
| SEARCH_FAILED | 모든 시작점에서 feasible 없음 | `SearchFailedError` | -- | 6 |
| 예상 밖 예외 | 그 외 | 원래 예외 | 전파(삼키지 않음) | 1 |

모든 실패 레코드: {class, devices, margin, detail}. 광범위 except로 이 규약을 우회하지 않는다(V6).

### N3.15 `sizing_spec.json` (7b)

| 섹션 | 필드 |
|---|---|
| `meta` | `schema_version`(5), `topology_hash`, `origin`(`canonical` / `fixture`) |
| `human` | `objective`, `constraints[]{metric, op, value, source}`, `ports`, `value_amp`, `compensation_targets{CL, GBW, PM}`, `driving_spec`, `node_voltage_targets`, `gain_budget_db_override`(source 필수), `cross_kind_matching`, `same_as`(M7=M6, M36b=M36a처럼 connectivity로 유도되지 않는 것만) |
| `derived` | S1·S1v에서 유도한 필드: {필드, status, evidence, rule_hash} -- stage 구성, `vertical_stack_id`, `vsb`, `vds_match_vgs_of`, 같은 종류 `gm_id_match_vgs_of`, `compensation.stage_devices`, `vds_kvl_groups`, metric 소자 역할 인자, 노드 공유 `budget_reference_device` |

* 로더 `load_sizing_spec(path)`는 미지 필드를 거부하고, `topology_hash` 불일치를 거부하고, `constraints[].source`가 없거나 논문이면 거부한다.
* 명칭: 슬루율 필드 이름은 metric 단위 레지스트리(DEC-53)의 이름-단위 규약을 따라 하나로 정한다(I-C7 해소). 실제 이름은 `7b-compensation-allocation` design이 레지스트리 단위표를 인용해 적는다.
* 이관: 4개 회로마다 topology.json의 `device_roles`/`sizing_roles`/`compensation`에서 `sizing_spec.json`을 생성하고, 생성본으로 같은 결과가 나오는지(equivalence) 확인한 뒤 topology.json에서 해당 필드를 제거한다. 제거는 topology.json 변경이라 사용자 확인 후 오케스트레이터가 반영한다.

---

## N4. 원칙과 강제 검사

### N4.1 기지 사고 클래스 IC1~IC10

사고1~24(`known-incidents.md`)를 클래스로 묶고, 클래스마다 **거부 케이스를 가진 강제 test**를 둔다. 담당 Phase까지는 xfail(TS7)이다.

| ID | 실패 클래스 | 구조적 방지 | 강제 test(`tests/contracts/`) | 담당 Phase |
|---|---|---|---|---|
| IC1 | 물리 제약 미검증 상수 | 모든 전압·전류는 W 티어 또는 선언을 거친다 | `test_vgs_consistency_all_devices`: 모든 소자 VGS 정합 ≤ tol_V(N3.6) | 6b |
| IC2 | 암묵적 순서 의존 | SC-a 단일 writer, NFR-4 결정론 | `test_order_shuffle_invariance`: 소자 dict 순서·그룹 순서·set 순회를 섞어 2회 실행, 이산 필드 완전 일치, 노드전압 ≤ tol_V, 전류 ≤ tol_I, 그 밖의 연속 필드 ≤ tol_V 섭동의 감도 전파값 | 6b |
| IC3 | 조용한 소실·덮어쓰기 | 이름 전역 유일, 저장 필드 목록 단일 정의, pass마다 커버리지 재검증 | `test_coverage_and_field_completeness`: `check_stick_diagram_coverage` + instance.json 소자·필수 필드 누락 0 + 이름 충돌 0 | 1 |
| IC4 | role 라벨 과신 | 물리·connectivity 판정이 항상 우선 | `test_role_label_removal_invariance`: `headroom_role`/`gm_id_role`/`L_role` 전부 제거해도 결과 동일 | 6c |
| IC5 | 게이트 사각 | 게이트 docstring에 "검사하지 않는 것" 절 필수 | `test_gate_docstring_declares_blind_spots`: `check_*`/`verify_*`/`validate_*`/`audit_*` 전수 정적 검사 | 1 |
| IC6 | underdetermined를 반복으로 밀어붙임 | GB4 DOF 진단 | `test_dof_catches_incident19_fixture`: 사고19 픽스처(스택 vds 미지수 2 / 등식 1)를 overconstrained·underdetermined로 판정 | 6c |
| IC7 | 단일 회로로만 검증 | 동작 변경 Phase는 4개 회로 측정 | `test_all_four_topologies_run`(regression): 4개 회로 실행 + 필요 없는 기능 발동 계수 0 | 4 이후 매 Phase |
| IC8 | 증거 없는 자동 병합 | 증거 없는 유도는 `proposed`/`review_needed` | `test_unevidenced_derivation_stops_before_search`: 증거 없는 픽스처에서 STRUCTURE_UNRESOLVED | 6c |
| IC9 | 중복 복붙 | 레지스트리 정본 하나, 타입 setter만 | `test_no_raw_duplicated_writes`: 원시 대입·중복 상수 grep 0 | 6b |
| IC10 | 캐시 키가 가변 상태를 놓침 | SC-d 내용 지문, SC-e reader 기록 | `test_cache_key_covers_mutable_state`: `ctx.sized`만 바꾸고 같은 metric 호출 시 옛 값 미반환 | 6b |

### N4.2 auditor 검사 V1~V10

'도입'은 병합 판정에 적용되는 Phase다. 도구는 모두 Phase 0.5에서 완성되고, 0.5의 공격 시나리오·사례 재생에서 거부 동작을 증명한다. 도입 전 Phase에서는 PASS가 아니라 `N/A(사유, 도입 Phase)`로 판정 기록에 적는다.

| ID | 검사 | 판정 규칙 | 도구 | 도입 |
|---|---|---|---|---|
| V1 | 전체 test 실행 | 병합본 깨끗한 worktree에서 slow 포함 전체. `-k`·`--deselect`·`-x` 금지 | pytest | 1(0.5는 redteam 스크립트) |
| V2 | 판정 유형별 증거 | red-green: 새·바뀐 test가 base에서 assertion FAIL, 병합본 PASS. equivalence: test 커밋 불변 + base·병합본 모두 PASS + 유형별 동등 증명(TS1 stdout, Phase 3 AST 해시). test-only: 섹션->test 매핑표의 모든 섹션이 변경 후 test에서 PASS | base/병합본 실행 비교 | 1 |
| V3 | 뮤테이션 | 대상 = diff가 닿은 def 중 AST 해시가 바뀐 것. 연산자 = 비교 뒤집기 / 산술 교체 / 상수 변경(정수는 ±1, 실수는 표기된 마지막 자릿수 한 단위 ±) / 문장 삭제 / 조기 return / except 본문 삭제. 변이마다 그 함수를 호출하는 test만 실행(인벤토리). 살아남은 변이가 있으면 FAIL. 등가 변이 면제는 승인 기록으로만. 변이는 worktree 밖 임시 복사본에서 수행하고 worktree는 바꾸지 않는다 | `tools/gates/mutate_changed.py` | 1 |
| V4 | 자기참조 lint | (1) 기대값 변수가 피검 함수(interface card 심볼) 호출로 만들어짐 (2) 피검 함수 본문 식과 AST 동형(이름을 위치 인덱스로 치환한 `ast.dump`의 BinOp/Call 부분트리 해시 일치) (3) assert가 if·try 안에만 있음 (4) assert 0개 (5) print·logging으로만 판정 | `tools/gates/test_lint.py` | 1 |
| V5 | 기준 약화 | test diff에서 N0.4 "기준 약화" 8패턴 중 하나라도 있으면 해당 diff 해시의 승인 기록 필수 | `tools/gates/weakening_diff.py` | 1 |
| V6 | 소스 lint | 새 광범위 except, 새 skip/continue 분기, 허용 집합 {0, 1, −1, 산술식의 2, 인덱스} 밖 숫자 리터럴 중 `# derive: <함수명>` 태그(그 함수 존재 검사)가 없는 것, 읽는 코드 없는 경고 리스트, `id(...)` 캐시 키, 상한 없는 캐시 | `tools/gates/source_lint.py` | 1 |
| V7 | 배선 | 새 def가 운영 경로에서 도달하는지(루트 목록은 설정 파일, Phase 3 전·후 두 벌). 도달 못 하면 레지스트리 등급 D 기록 + 승인 기록 | `tools/gates/reachability.py` | 2 |
| V8 | 폴백 발동 0 | 정본 spec 실행 결과의 `fallback_events`{site, kind, device, detail}가 비어 있음 | 엔진 계측 | 4 |
| V9 | 물리 불변식 | 4개 회로 결과가 봉인 항목(N3.6), IC1, `matching_offset`/`matching_ratio` 관계 엣지 멤버의 (W/L, gm_id) 일치(gm_id 허용오차 = LUT gm_id 격자 간격, W/L 허용오차 = 같은 ID에서 그 gm_id 허용오차가 만드는 IDu의 상대 차)를 통과 | contracts test | 6b |
| V10 | 보고 수치 재현 | spec card "재현할 수치"를 명령과 함께 재실행해 판정 기록에 적음 | auditor | 0.5 |

### N4.3 게이트 거부 증명(Phase 0.5)

**공격 시나리오**(전부 거부 로그가 나와야 완료)

| # | 공격 | 기대 |
|---|---|---|
| 1 | code-author가 tests 경로를 Edit | EL1 거부 |
| 2 | code-author가 Bash로 tests 파일 생성 | EL2가 완료 거부 |
| 3 | 한 커밋에 소스+tests | EL3 차단 |
| 4 | `git commit --no-verify` | EL1 거부 |
| 5 | EL1~EL3 없이 만든 커밋을 병합 | EL4 거부 |
| 6 | 기대값을 피검 함수로 만든 test | V4 FAIL |
| 7 | assert를 `if result is not None:` 아래로 | V4 FAIL |
| 8 | 허용오차 확대 | V5 FAIL(승인 기록 없음) |
| 9 | `except Exception: return` 추가 | V6 FAIL |
| 10 | 메인 세션이 엔진 소스 Edit | EL1 거부 |
| 11 | RTL agent가 임의 파일 Edit | hook 출력 없음 + exit 0(무동작) |

**과거 사례 재생**: 해당 diff만 담은 합성 커밋을 현재 base에 적용해 기대 검사가 거부하는지 확인한다(원자료 `agent7_self_concealment.md`).

| 사례 | 커밋 | 기대 거부 | 재생 Phase |
|---|---|---|---|
| 면적 식 α 상쇄(자기참조 기대값) | e329283 | V4 | 0.5 |
| stick_diagram Test 16 FAIL 박제 | e5fbf92 | V4(print 판정) | 0.5 |
| assert를 조건문 아래로 | 3250baa | V4 | 0.5 |
| NameError를 광범위 except로 삼킨 게이트 | 1b9b4ea | V6 | 0.5 |
| 격자 확대로 제약 통과 | 2e1944a | V5 | 0.5 |
| 재검증 누락을 기대값으로 박제 | caa970b | V2(red 부재) | 1 |
| KVL 위반 동작점의 76.48dB 기준값 | 5dc4679 | V9 | 6b |

---

## N5. 결함과 열린 이슈

### N5.1 현황(2026-09-14)

* `sizing_recipe.py` 15,270줄(인라인 self-test 2,700줄), `stick_diagram.py` 12,936줄(3,946줄). `def test_` 0개.
* §N3의 새 구조(GB0~GB9, S0~S3, W 티어, 봉인, 10모듈, 역할 분리)는 구현되지 않았다. 파일럿은 기존 경로(L -> VDS -> gm_id)로 수렴한다.
* 함수별 판정은 레지스트리, 계획 대 구현 대조는 원자료 `agent6_plan_vs_code.md`.

### N5.2 현존 결함 DF

모든 결함은 수정 전에 base에서 실패하는 test 또는 lint(V6)를 먼저 둔다.

| ID | 결함 | 위치(함수) | 수정 Phase | 비고 |
|---|---|---|---|---|
| DF-01 | vsb를 노드전압으로 다시 고치면서 W·gm·gds는 옛 vsb 값으로 남는다(버전 혼재). 원인 코드 `setdefault("vsb", ref_vds)`가 남아 있다 | `reconcile_vsb_from_nodes`, `_hr_resolve_vertical_group` | 4(재계산), 6b(구조 제거) | I-B9 |
| DF-02 | 노드전압 경로 충돌(conflicts)을 엔진이 읽지 않는다 | `propagate_node_voltages` 호출부 | 4(충돌 시 SEAL_VIOLATION, tol_V 함수 선도입), 6b | I-B7 |
| DF-03 | vsb·L 동치류 게이트가 `ValueError`를 던져 탐색 전체가 멈춘다 | `_evaluate` 게이트 | 4(N3.14 실패로 교체) | 보고 시 명시 |
| DF-04 | 복구 함수가 소자명을 부분문자열로 찾는다("M1"이 "M11a"에 걸림) | `repair_infeasible_baseline` | 4 | |
| DF-05 | 미러비 오차 쌍을 그룹의 첫 두 소자만 본다 | `_mirror_ratio_error_pairs` | 4 | I-A4 |
| DF-06 | 광범위 except가 필드 원천을 조용히 버린다 | `node_pole_estimate`, `_mna_stamp_capacitance`, `synthesize_l_class_thetas` 호출부, `knee_L_for_kind` 호출부 | 4 | |
| DF-07 | 캐시 상한 도달 시 LRU가 아니라 캐싱을 멈춘다 | LUT `_query` 캐시, `_FEASIBLE_L_WINDOW_CACHE` | 4 | NFR-2 |
| DF-08 | spec 지문 불일치를 노트만 남기고 유도 임계값을 계속 쓴다 | `resolve_constraint_references` | 4 | U-04 |
| DF-09 | `estimate_area_budget` 블렌딩 식이 α를 상쇄한다(`(2−α)A`) | `estimate_area_budget` | 4(TS4 red) | |
| DF-10 | 이분 역산이 단조성을 검사하지 않는다 | `solve_id_for_target_gm`, `_invert_gm_id_for_current` | 4 | U-05, DEC-11 선례 |
| DF-11 | 적층 diode 해석이 LUT 실패 시 `idu_up = 1.0`을 대입한다 | `solve_stacked_diode_pair` | 4 | |
| DF-12 | 입력환산 오프셋이 gm 없는 소자를 조용히 뺀다 | `_metric_input_referred_offset` | 4 | |
| DF-13 | `id(lut)` 키 캐시와 상한 없는 캐시 | `diode_vds_cached`, `diode_vds_window`, `_KNEE_L_CACHE`, `_gm_id_curve_cache`, `_solve_vgs_cache`, `_idu_scan_cache` | 4 | SC-d |
| DF-14 | `except Exception`이 호출 실패를 폴백으로 바꾼다 | `lut_vdsat_headroom`, `stack_kvl_vgs_limit._known_vds`, `_hr_resolve_vertical_group`(2곳), `repair_infeasible_baseline._probe` | 4 | V8 계측 대상 |
| DF-15 | Rz 캐시 키가 소자명뿐이고 `_dc_replace`가 캐시 dict를 새 ctx와 공유할 수 있다(실행 재현 전) | `_resolve_nulling_resistor_ohm`, `revalidate_finger_override` | 4(재현 test 먼저) | |
| DF-16 | 목적함수 `power_uA`(`sum_current`)가 직렬 스택 전류를 중복 계상한다 | 4개 회로 objective | 7a | I-A3, U-10, 보고 시 명시. 목적함수 전력 정의가 GB8 전력 정의와 같은 결정이라 7a로 옮긴다 |
| DF-17 | stick_diagram self-test Test 16의 FAIL 출력이 기준선에 박제돼 있다 | stick_diagram self-test | 1(TS0) | U-01 |
| DF-18 | `run_harness.run`이 실패해도 exit 0이고 θ*를 출력만 한다 | `workspaces/run_harness.py` | 4(N3.14 exit code, θ* 기록) | 보고 시 명시 |
| DF-19 | 레일 넷 집합이 모듈마다 다르다(대소문자) | stick_diagram `_RAIL_NETS`, sizing_recipe 레일 판정 | 4 | |
| DF-20 | 운영 경로의 근거 없는 폴백 상수(vds 0.6/0.2, margin 0.05, W_bounds·gm_id 격자 리터럴) | `resolve_feed_vds` 계열 | 4 | WP-03 |
| DF-21 | 실행 불가·무의미 probe 3개 | `probe_mirror_common_L_wiring`, `probe_node_voltage_audit`, `probe_vs_semantics` | 2(TS6) | U-02 |
| DF-22 | 지문 불일치 노트 리스트 `_RESOLVE_STALE_NOTES`를 읽는 코드가 없다 | `resolve_constraint_references` | 4 | DF-08과 함께 |

### N5.3 열린 이슈

옛 §10 항목 중 아직 열린 것만 둔다(닫힌 것은 이력 문서 "[판정] §10 닫힌 이슈"). DF와 같은 결함인 I-A3(DF-16), I-A4(DF-05), I-B7(DF-02), I-B9(DF-01)은 N5.2에만 둔다. v5.0에서 I-G3, I-G7, I-G8, I-C3, I-C5, I-C7, I-C9, I-A9는 본문 명세로 닫았다(부록 A). I-A10, I-A11, I-B22, I-C10, I-C11은 v5.0에서 새로 연 항목이다.

| ID | 남은 것 | 담당 |
|---|---|---|
| I-A2 | 면적 정의(트랜지스터 W·L, 레이아웃 면적, 수동소자 면적의 관계) | 7b, U-13 |
| I-A5 | LUT 생성 메타를 읽는 `lut_conditions_from_npz`가 운영 경로에서 불리지 않는다 | 6a(S0에 배선) |
| I-A6 | ICMR·출력 swing 제약 슬롯이 없다 | 7b(슬롯은 `human.constraints`의 metric). 헤드룸 하한으로도 쓰는지는 6b design이 W4 창과 함께 판정 |
| I-A7 | 일반 순환 블록 수렴 판정 | 6b(N3.6) |
| I-A10 | `parasitic_pm_deg >= PM_target_deg` 제약이 4개 회로 선측정 없이 걸려 있다(folded는 `omega_c`를 노출하지 않아 측정 불가) | 7a(gain metric 이관 때 `omega_c` 노출), DEC-49 |
| I-A11 | 크로스오버 주파수 해석 차이(선언식 36.6MHz 대 전체 응답 실측 30.50MHz)의 원인 미확인 | 7a |
| I-B2 | stage-local/전역 게이트 구현 없음 | 7a(MT 분류) |
| I-B3 | 블록 사이징 함수 시그니처 | 7b(N3.7 내층 DP 입력 = 블록, W4 창, y) |
| I-B5, I-B6 | DOF 진단 구현 없음(VDS·KVL 축, 부등식 오계수) | 6c(N3.7) |
| I-B8 | KCL 잔차 제약 없음 | 6b(봉인 항목 3) |
| I-B11 | IC 강제 test 0개 | 1~7c(TS7) |
| I-B12 | `set` 순회 잔존(sizing_recipe 1곳, stick_diagram 5곳) | 6b(NFR-4, IC2) |
| I-B13 | gm_id·vds 확정 출처 태그가 일부 경로에만 있다 | 6b(SC-a) |
| I-B14 | 사이징 경로가 `value_amp`를 읽지 않는다 | 7b(DEC-08) |
| I-B21 | 선언된 gain 제약이 미러 부하를 못 본다 | 7a(DEC-05, J6), 보고 시 명시 |
| I-B22 | 입력환산 오프셋의 다중 diff pair(cascade 입력환산, CMFB 오차증폭기) 처리 | 7a(DEC-23) |
| I-G1 | 단일단 회로의 gm 출처 | 7b, U-12 |
| I-G2 | 3단 보상의 stage 수 종속 일반화, nmcnr passive 누락 | 7b, J9 |
| I-G4 | class-AB 정지전류 `ID_source` 타입 | 7b(N3.7), J3 |
| I-G5 | 폴딩 노드 역할 | 6a(SP1 역할 분류), J5 |
| I-G6 | stage 분할 구현 | 6a(SP1) |
| I-C6 | 읽히지 않는 스키마 필드(`closed_loop_accuracy_db`, `stage_gm_ref`, `vdd_kvl`) | 7b(v5 스키마에 두지 않음 -- 로더가 미지 필드로 거부) |
| I-C10 | `stack_headroom_slack_v` metric의 담당·제약 여부가 없다 | 6b, U-20 |
| I-C11 | `two_stage_ota` stage1_out 분리와 `nmcnr` stage2_diode_ref 이월 -- 해소 전에는 두 회로에서 유도 기능을 돌릴 수 없다 | U-09 |

### N5.4 탐색 결과를 보고할 때 반드시 명시할 것

수정 전까지: I-B21(gain 제약이 미러 부하를 못 봄), DF-16(전력 중복 계상), DF-03(게이트 예외로 탐색 중단 가능), DF-18(실패해도 exit 0). U-11이 SPICE 대조를 7c로 두면 7a~7c 사이 gain metric의 `verified_by` 검증 대기도 명시한다.

---

## N6. 로드맵

### N6.1 순서표(유일한 순서 정본)

모든 Phase의 공통 착수 조건: **해당 design 문서의 사용자 승인**(DEC-51). 이전 Phase DoD PASS.

| Phase | 범위 | 판정 유형 | 추가 착수 조건 | design 문서 |
|---|---|---|---|---|
| 0 | 함수 재사용 레지스트리 | -- | -- | ✅ 완료 |
| **0.5** | 역할 분리 인프라(N3.12.6), 공격 시나리오·과거 사례 재생 5건(N4.3) | 부트스트랩 | U-15(hook 필드가 없을 때), U-16 | `05-role-separation` |
| 1 | TS0, TS1, TS2, TS3, TS5, TS7 선언. IC3(필드 완전성·이름 충돌 검사 신설)·IC5(게이트 docstring '검사하지 않는 것' 절 추가) 활성 | TS0·IC3·IC5 red-green, TS1 equivalence, TS2·TS3·TS5 test-only | U-01 | `10-test-separation` |
| 2 | TS6, 레지스트리 등급 D 삭제(배선을 고른 항목은 Phase 4로), 레지스트리 §2에서 "행동 보존 통합 가능"인 DUP 통합 | equivalence(TS6은 test-only, 운영 도구 이동은 code·test 두 커밋) | U-02 | `20-dead-code-dup` |
| 3 | 10모듈 이동(N3.10), shim, 추적 파일 호출부 갱신 후 `sizing_recipe.py` 삭제 | equivalence | U-03 | `30-module-split` |
| 4 | TS4, DF-01~15·18~20·22, Phase 2에서 배선을 고른 함수 배선, `fallback_events` 계측(V8), 4개 회로 실행 가능성(I-C11), IC7 활성 | red-green | U-04, U-05, U-09 | `40-defect-fixes` |
| 5 | 실패 캐시, 시작점 선택(S3 레코드 v1: θ*·start별 결과·실패), margin 반환 | red-green | -- | `50-failure-cache` |
| 6a | GB0(의미·로드 게이트), S0(LUT 메타 배선 포함), GB1, GB2 shadow(소자 구성 분류 CS/CG/CD/pass 포함). 6a-1 유도·대조표, 6a-2 공동분석·ratify, `structure.json`, 레지스트리 §2 ★ DUP(diode·미러 그룹·diffpair/tail)를 U-06 결론의 정본으로 통합하고 옛 함수 삭제 | red-green | U-08, U-17. 6a-2는 U-06(J1~J7, J9 ports, J10, 구조 정본) | `6a-structure-stage` |
| 6b | GB7: W 티어, 순환 블록, 봉인, SC-a~SC-e, 평가 커널 계산 블록과 S2 memo, NFR-4 결정론. IC1·IC2·IC9·IC10 활성 | red-green | U-06(J8), U-20 | `6b-node-voltage-seal` |
| 6c | 결합 잔차 측정, GB3, GB4(LUT 곡선 검사, 블록 gain 상한, DOF), `review_needed` 잔존 시 정지. IC4·IC6·IC8 활성 | red-green | -- | `6c-coupling-achievability` |
| 7a | GB8: gain metric 통일, 블록 국소 소신호 모델과 gmb 유도(MNA에도 gmb 반영), 잔차, 감도 게이트, MT 분류, 전력 정의, metric DUP 3쌍(gain/PM/CMRR) 통합, `verified_by`(U-11 결과에 따라 SPICE AC gain 대조 포함), bisection 도구와 임계값 재도출 | red-green | U-07, U-10, U-11, U-19, J6 승인 기록(6a-2 확정) | `7a-gain-metric` |
| 7b | GB5 보상 규칙, GB6 3층 할당, `sizing_spec.json` v5와 4회로 이관, `value_amp` 소비, 면적·Pareto, MOD8 수렴 루프(LR9) | red-green | U-12, U-13, U-14, U-21, U-06(J3 정지전류, J9 passive) | `7b-compensation-allocation` |
| 7c | GB9: S3 전체, Sobol 전역 샘플, 분지, SPICE `.op` 전체 대조. IC 전원 PASS | red-green | -- | `7c-archive-spice` |

### N6.2 Phase별 완료 조건

| Phase | 완료 조건(측정 명령은 design 문서에 고정) |
|---|---|
| 0.5 | N4.3 공격 11건 거부 로그 + 사례 5건 적발, hook 입력 필드 실측 기록, 에이전트 정의 `check_agents.py` PASS, 설치 후 RTL agent 무동작 |
| 1 | TS0 판정 기록 / TS1 seed 1~5 stdout 전후 동일 / TS2 기본·셔플 순서 PASS / TS3 판정 문자열 0 / TS5 기준선 참조 0 / 소스에 인라인 self-test 0 / IC3·IC5 PASS, 나머지 IC xfail 선언(담당 Phase 명시) / 사례 caa970b 적발 |
| 2 | 승인된 D 목록 처리, DUP마다 옛 함수 대 정본 차등 test(4개 회로 입력 전수 출력 동일) PASS 후 옛 함수 삭제, 레지스트리 갱신, probe 엔진 식 재구현 0 |
| 3 | MOD1~MOD10 존재, import 계층 위반 0(`import_layering.py`), 이동 커밋마다 AST 해시 동일, `sizing_recipe.py` 삭제, 레지스트리 이관 목적지 열 = 실제 위치 |
| 4 | DF마다 red-green, V8 도입(정본 실행 `fallback_events` 0), 4개 회로 실행과 전후 비교표 |
| 5 | 평가 입구 계수기로 동일 θ 재평가 0, θ* 기록이 다음 실행 시작점에 쓰임, 4개 회로 착지 전후표 |
| 6a | 4개 회로 input·cascode·tail 멤버십이 declared와 일치, 출력노드·load·G_out 기여 소자가 ratified 대조표와 일치, shadow 대조 보고가 매 실행 생성, J 결론의 승인 기록 |
| 6b | 봉인 위반 0(4개 회로), IC1·IC2·IC9·IC10 PASS, SC 거부 케이스 PASS, 사례 76.48 적발, 평가 오버헤드 전후 |
| 6c | 결합 잔차 표, 블록·y 목록(4개 회로), 달성 불가 픽스처(oracle (a): 목표 gain > 블록 이론 상한 합을 test가 다른 방법으로 계산)에서 탐색 전 INFEASIBLE_TARGET, IC4·IC6·IC8 PASS |
| 7a | gain 제약이 `smallsignal_gain_db`로 판정, B21 재현 픽스처(6480조합 중 `gain_stages_sum` 변화 0이고 MNA 변화 최대인 두 점)에서 감도 게이트 FAIL, 평가 기록에 MNA-블록 잔차 필드(4개 회로), gain metric `verified_by` 유효(U-11이 SPICE를 7c로 두면 '검증 대기' 표시 + N5.4 명시), 임계값 재도출 기록 |
| 7b | `gain_budget_db` 출력, 3층 할당이 다른 모델 전수탐색과 격자 분해능 안 일치, `sizing_spec.json` 이관 4개 회로 equivalence, derived 필드마다 status·evidence·rule_hash, 파일럿 wall-clock ≤ 5분(U-13에서 면적 예산을 선언하지 않으면 파일럿 판정은 Pareto 제시·정지와 사용자가 고른 점의 재실행으로) |
| 7c | SPICE 비교가 N3.8 허용오차 안, 같은 지문 재실행에서 아카이브 적중 > 0이고 θ* 목적값이 첫 실행 이하, IC1~IC10 전원 PASS, 파일럿 wall-clock ≤ 5분 |

### N6.3 공통 완료 조건

* auditor 판정 기록 PASS(N4.2 도입 표 기준), merge gate(EL4) 통과, 동작 변경 spec card마다 거부해야 할 입력의 test 존재.
* 4개 회로: 동작 변경 Phase(4 이후)는 4개 회로 측정과 무동작 증명. 동작 보존 Phase(1~3)는 실행 가능한 회로 전부에서 equivalence(I-C11 해소 전 two_stage·nmcnr은 로드·구조 단계까지).
* 성능: Phase 4부터 매 Phase 보고 -- 조건 = 정본 spec, `SPECS[circuit]["slsqp_kwargs"]`, 파일럿 탐색 1회의 전체 wall-clock과 평가 시간 중앙값, 기계 정보. 5분 게이트는 7b·7c.

---

## N7. 공동분석과 사용자 결정

### N7.1 공동분석 J(회로 해석)

오케스트레이터가 connectivity 증거와 대조표를 제시하고 사용자가 확정한다. 결론은 승인 기록으로 남기고 `ratified`로 반영한다.

| ID | 항목 | 소비 Phase |
|---|---|---|
| J1 | replica bias(M57/M58/M63/M64)를 교류접지 예외로 끊을지(끊으면 CMFB 루프 부호가 부궤환으로 확정) | 6a |
| J2 | diode 노드 게이트의 gate->drain을 같은 stage(미러)로 볼지(nmcnr M201->M203/M204 경계) | 6a |
| J3 | class-AB M9a/M9b/M18a/M18b/M8/M17의 역할. floating battery(M9a/M9b: Vop1↔Vg15, M18a/M18b: Vom1↔Vg25)가 pass 구성으로 신호를 넘길 때 stage 출력노드를 Vop1(캐스코드 사슬 끝)로 볼지 Vg15(출력단 게이트)로 볼지, 정지전류 규칙 | 6a, 7b |
| J4 | M7(gate Vcmfb)을 tail로 볼지 CMFB 구동소자로 볼지 | 6a |
| J5 | 5T 미러부하·NMCNR 폴딩 미러를 DM 반회로에서 다루는 법(DM 뷰가 출력노드를 잃는 경우) | 6a |
| J6 | 출력노드 부하 귀속: 파일럿 M18a/M19/M18b를 stage1 부하(G_out)로, nmcnr M104/M106을 해당 stage 부하로 넣을지 | 6a(ratify), 7a(gain metric이 소비) |
| J7 | Cc–Rz 직렬 루프 극성 판정 | 6a(극성 ratify), 7b(보상 규칙이 소비) |
| J8 | `fold_group`, `shared_gm_id_groups`, 노드를 공유하지 않는 `budget_reference_device` 4건(M61, M68, M38, two_stage M4), `voltage_divider`/`floating_current_source`/`bias_replica` 의도(단서: vsb 오류 소자 M38/M60/M61/M68이 모두 `budget_reference_device` 보유) | 6b |
| J9 | folded·nmcnr `ports`, nmcnr·two_stage `passive_elements` 누락분 | 6a(ports), 7b(passive) |
| J10 | follower(CD) 또는 pass로 끝나는 경로를 독립 블록으로 둘지 앞 stage 블록에 흡수할지(이득 1 미만이라 배분 대상은 아니지만 레벨 시프트·저임피던스 극점·헤드룸에 영향). folded M8(gate Vg7 -> source Vg10) 판정 포함 | 6a |

### N7.2 사용자 결정 U

기본안은 원칙에서 나온 제안이며, 확정 전에는 구현하지 않는다.

| ID | 결정 | 기본안 | 필요 시점 |
|---|---|---|---|
| U-01 | stick_diagram Test 16의 의도(test가 틀렸나 대상이 틀렸나) | 오케스트레이터가 원인 대조표 제시 | Phase 1 |
| U-02 | 레지스트리 등급 D 목록과 probe 삭제 11개의 항목별 삭제/배선 | 제안표 일괄 승인 | Phase 2 |
| U-03 | 추적되지 않는 `workspaces/` 스크래치 스크립트가 `sizing_recipe.py` 삭제로 깨지는 것을 허용할지 | 허용(추적 파일만 갱신). 근거: WP-01의 배선 대상은 저장소에 추적되는 파일 | Phase 3 |
| U-04 | 픽스처와 정본 spec의 구분 | spec에 `origin: canonical | fixture` 필수, 픽스처는 유도 임계값을 읽지 않음 | Phase 4 |
| U-05 | 비단조 곡선에서 이분 역산의 처리 | 단조 구간별 근을 모두 돌려주고 호출자가 선택 규칙을 명시(DEC-11 확장) | Phase 4 |
| U-06 | J1~J10 공동분석 + 구조 개념 정본(diode 이웃 포함 여부, 미러 그룹 키, diffpair/tail 유도) | 대조표로 항목별 확정 | 6a-2(J1~J7, J9 ports, J10, 구조 정본) / 6b(J8) / 7b(J3 정지전류, J9 passive) |
| U-07 | 전력 정의 변경으로 바뀌는 기대값들을 한 승인으로 묶어도 되는지 | 변경 목록을 첨부한 한 승인 | 7a |
| U-08 | folded·nmcnr·two_stage `ports`(two_stage 출력 포함) | connectivity 제안표 확인 | 6a |
| U-09 | two_stage stage1_out 분리·nmcnr stage2_diode_ref 이월을 언제 풀지 | Phase 4에서 DF와 함께. 근거: 4개 회로 측정(N6.3)이 Phase 4부터 동작 변경 판정에 필요 | Phase 4 |
| U-10 | 목적함수 전력 정의(`sum_current` / `_metric_supply_current`) | 4개 회로 비교표 제시 | 7a |
| U-11 | `verified_by` 적용 순서 | SPICE AC gain 대조를 7a로 당겨 gain 제약에 적용 | 7a |
| U-12 | 단일단(보상 없음) 회로의 gm 출처 | `gm_1 = 2π·GBW·CL` | 7b |
| U-13 | 면적 정의와 파일럿 면적 예산 | 예산 미선언 시 DEC-07대로 Pareto 제시 후 정지 | 7b |
| U-14 | gain 폭이 분해능 이하인 공유 VGS 그룹(pmos:Vcmfb)의 선택 기준 | 전력 기준으로 고르고 기록 | 7b |
| U-15 | hook 입력에 역할 필드(`agent_type`)가 없을 때의 역할 판정 방식. **실측 후 결정(2026-09-14 사용자)**: 부트스트랩 ② 실측 기록(PreToolUse·PostToolUse·SubagentStop 각각에서 `agent_type`·`agent_id`·`cwd` 존재 여부, 세 역할 + 메인 세션)을 제시하고 고른다. 필드가 있으면 이 결정은 필요 없다 | 선택지: A. 호출자 `cwd`가 속한 worktree(`../wt/<id>-<role>`)로 판정(EL1 약화분은 EL3·EL4와 Bash `git -C`·다른 worktree 경로 거부로 보완) / B. 역할마다 별도 Claude 세션·설정 / C. EL1은 메인 세션 규칙만, 역할 구분은 EL3·EL4 | 0.5(실측 직후) |
| U-16 | topology.json 메타데이터(role·ports·passive) 반영 주체. **확정(2026-09-14 사용자 "A로 해")**: 오케스트레이터가 사용자 확인 후 반영 | 조건: 사용자가 확인한 표의 항목만 반영, connectivity(넷리스트·passive·이상원 넷)는 WP-08대로 모았다가 일괄 반영하고 net 표 재출력으로 대조 / 승인 기록 `.ai/approvals/<id>.md` + 커밋 `Role: doc`, EL4는 승인 기록 없는 topology diff를 거부 / topology 변경은 S0 지문을 바꿔 `ratified`를 `review_needed`로 되돌림 / topology 변경으로 바뀌는 test 기대값은 V5 승인 대상. 근거: WP-07, WP-08, DEC-35 | 확정 |
| U-17 | `mismatch_sigma_mV = 5.0`의 출처(시스템 레벨 요구) | 사용자가 출처를 선언 | 6a |
| U-18 | 기준 약화 개별 승인 | 매 건 승인 기록 | 상시 |
| U-19 | `gain_db >= 54`를 전체회로 gain 기준 bisection으로 재도출해 교체할지 | 재도출값 제시 후 승인 | 7a |
| U-20 | `stack_headroom_slack_v`를 봉인 항목으로 흡수할지 metric 제약으로 남길지(I-C10) | 봉인 항목 1·5가 같은 사실을 보므로 metric 삭제 | 6b |
| U-21 | 선언 L theta(`L_cascode`, `L_stage2out_*`)를 L 동치류 theta로 대체하고 삭제할지 | DEC-18에 따라 삭제 | 7b |
| U-22 | 순수 follower(drain이 레일, source가 출력)가 있는 회로를 library에 추가해 CD 규칙을 실제 회로로 측정할지 | 추가하지 않고 4개 회로의 분류 발동 목록 일치만 증명(WP-07상 픽스처 손타이핑 금지) | 6a |

---

## N8. 위험과 대응

| 위험 | 대응 |
|---|---|
| stage 분할의 회로 해석 오판 | 6a는 shadow로 대조만, `review_needed` 잔존 시 6c에서 정지, J 공동분석으로 ratify |
| 3층 할당 비수렴·국소해 | 종료 규칙과 유한 격자 상한(N3.7), 분지별 시작, 다른 모델 전수탐색 대조 |
| 노드전압 정본 전환(6b)이 착지를 바꿈 | 봉인 위반이 없던 소자의 값만 옛 경로와 동등 단언하고, 달라진 소자는 writer 티어와 함께 기록, 4개 회로 전후표 |
| hook 입력에 역할 필드가 없음 | 0.5 첫 단계에서 실측, 대체 판정 U-15 |
| hook 오탐이 RTL agent·일반 작업을 막음 | 판정 범위를 gmid 역할과 경로표로 한정, 공격 시나리오 11 |
| 분리로 못 막는 은폐(자기참조 oracle, 거짓 기준값, 폴백) | V3·V4·V5·V6·V8·V9 |
| 파일 이동 중 회귀 | test 분리 먼저, 이동 전용 커밋, AST 해시 동일 증명 |
| 배분값·목표값을 지어냄(사고4) | `gain_budget_db`는 출력, 제약값 출처 필수 |
| 전체회로 MNA 반복으로 5분 초과 | `build_ac_network` 1회 조립, 봉인 스냅샷당 전역 metric 1회, S2 memo |
| SPICE 모델·ngspice 환경 부재 | SPICE를 처음 쓰는 Phase(U-11에 따라 7a 또는 7c)의 design 첫 단계에서 모델 경로(LUT 생성 메타)와 실행을 확인 |
| S3 아카이브 디스크 증가 | append-only, 크기를 매 실행 보고 |
| 사이징↔레이아웃 반복 중 소자 소실(사고16) | MOD8 루프 매 반복 커버리지 재검증(LR9), 이름 전역 유일(IC3) |

---

## N9. design 문서 작성 지침

### N9.1 문서 목록

경로: `docs/02-design/features/gain-budget-gmid-sizing.<번호>-<slug>.design.md`

| 문서 | 반드시 담을 것 |
|---|---|
| `00-common` | 용어집 최종본(N0.4), 실패 규약 클래스·필드(N3.14), 판정 기록·승인 기록 JSON/MD 스키마(N3.12.5), V 도입 표(N4.2), IC 담당 표(N4.1), 성능 측정 명령(N6.3), 무동작 판정 방법 |
| `05-role-separation` | 쓰기 경로표를 glob 목록으로(N3.12.2), hook 입력 실측 절차와 U-15 분기, 설치 명령과 순서(N3.12.6), 트레일러·경로 분류 규칙(소스/test/도구/데이터/문서), V3·V4·V5·V6·V7 알고리즘, interface card 생성기, spec card·dispute 양식, worktree 명령 시퀀스(N3.12.3), EL2 무시 목록, 공격 11 + 사례 5 재생 절차와 기대 메시지, agent 정의 3개 |
| `10-test-separation` | TS0 원인 대조, TS1 추출 스크립트와 두 커밋 순서, seed별 stdout 비교 명령, TS2 섹션→test 매핑표와 fixture 목록, 셔플 옵션 구현, TS3 AST 검사, TS5 퇴역 절차, TS7 xfail 선언 목록(IC별 담당 Phase) |
| `20-dead-code-dup` | U-02 제안표(항목, 호출부 0 증거, 삭제 영향, 배선 시 소비자), DUP별 차등 test 설계, TS6 승격·삭제·이동 목록 |
| `30-module-split` | 레지스트리 목적지 열에서 생성한 함수→모듈 이관표, 계산된 import 그래프, `import_layering.py` 규칙, AST 해시 증명 명령, shim 재수출 목록 생성법, 추적 파일 호출부 목록 |
| `40-defect-fixes` | DF별 red 형태(행동 test / lint)와 수정 범위, N3.14 실패 클래스 도입, tol_V 함수 선도입, U-04·U-05 반영, `fallback_events` 스키마와 계측 지점 전수, exit code, I-C11 해소 설계 |
| `50-failure-cache` | 실패 캐시 키·저장, margin 정규화식, 시작점 선택 규칙, S3 레코드 v1 스키마와 위치, 계수기 |
| `6a-structure-stage` | S0 해시 구성, S1 스키마(N3.3), 교류접지 3분류, DM 뷰 구성과 SP1 알고리즘(0-1 BFS), 소자 구성 분류와 출력노드·임피던스 등급 판정, 모드 수집, 피드백 극성, status 전이 구현, `structure.json` 형식, shadow 대조 보고 형식, J 대조표 양식, ports 제안표 |
| `6b-node-voltage-seal` | S2 필드 스키마, SC-a 권한표(필드 × W0~W4), W3 소스 필드, 계산 블록 입출력 선언과 유도 DAG, tol_V·tol_I·반복 상한 구현, 봉인 항목 구현, 버전 카운터, LRU 상한 계산, IC2 섞기 대상, 동등 단언 범위, J8 결론 반영, U-20 반영, I-A6 헤드룸 하한 여부 판정 |
| `6c-coupling-achievability` | 결합 잔차 측정 절차, 블록·y 추출 규칙(K1~K4), LUT 곡선 검사→해법 매핑, 블록 gain 상한 계산, DOF 변수·등식 표와 수치 rank, `DofReport`, 달성 불가 픽스처와 oracle |
| `7a-gain-metric` | 회로별 gain metric 이관표, 블록 국소 소신호 모델(경계 조건·스탬프)과 gmb 유도 식, 잔차 계산, 감도 게이트 섭동 방향·ε 계산, MT 분류 규칙, 전력 정의(U-10) 반영, `verified_by`와 SPICE AC gain 대조(U-11), bisection 모드(N3.13)와 U-19 |
| `7b-compensation-allocation` | `sizing_spec.json` v5 스키마·로더·이관·topology.json 필드 제거 절차, GB5 규칙(단일단 U-12, 3단, class-AB J3), 내층 DP 상태·bin 해상도, 중층 좌표강하 종료, 외층 인자, 면적·Pareto(U-13), U-14, `value_amp` 소비, MOD8 수렴 루프, 다른 모델 대조 test, U-21 반영, 슬루율 필드 명칭(DEC-53 규약 인용) |
| `7c-archive-spice` | S3 저장 형식·보고, DEC-34 샘플 수 구현, 분지 판정, SPICE 넷리스트 생성·실행 인터페이스와 모델 경로 확인, 비교량·허용오차 계산 |

### N9.2 모든 design 문서의 필수 절

1. 범위: 이 계획서의 어느 절·ID를 구현하는가
2. 인터페이스: 함수 시그니처, 데이터 스키마, 파일 경로, 호출 위치
3. 판정식: 모든 임계값의 계산식과 입력(숫자를 박지 않는다, WP-03)
4. 실패 경로: N3.14 클래스와 exit code
5. 역할별 산출물: spec card 목록(판정 유형, oracle 종류 포함)
6. DoD 측정 명령: N6.2 조건을 실행 가능한 명령으로
7. 착수 조건 확인: 관련 U·J의 승인 기록 id
8. 열린 질문: 없어야 한다. 남으면 이 계획서 N7에 추가를 요청하고 그 항목을 구현하지 않는다

### N9.3 새 토폴로지 추가 절차(I-G8)

topology.json(connectivity, `ports`, `passive_elements`) -> GB1·GB2 유도와 공동분석 -> `sizing_spec.json` human 섹션 -> 보상 레지스트리 함수(stage 수 일반 규칙으로 부족할 때만) -> `SPECS` 항목 -> regression에 회로 추가 후 기존 회로 무동작 증명.

---

## 부록 A. 옛 번호 대응표

코드 주석·`.ai/context.md`·메모리·레지스트리의 옛 참조는 이 표로 찾는다(원문은 이력 문서의 같은 절 번호).

### A.1 절

| 옛 절 | 새 위치 |
|---|---|
| §0, §0.1~§0.5 (v4.47 이전 "이어받을 지점") | 이력 `## 0. 이어받을 지점`(첫 번째 출현) |
| §0.1 / §0.2 / §0.3 (v4.49) | N5.1 / N6.1 / N0.2 |
| §1.1 / §1.2 / §1.3 / §1.4 | N1.1 / 이력 / N0.3 / 이력 §1.4 |
| §2.1 / §2.2 | N6.1 / N1.2 |
| §3.1 / §3.2 / §3.3 / §3.4 | N1.3 / N1.4·WP-02 / N4.1 / N2 |
| §4 / §5 | N6.2·N6.3 / N8 |
| §6 | 이력 §6 |
| §7.0 | 판정은 N3·N2에 반영, 표 원문은 이력 |
| §7.1 / §7.2 / §7.3 | N3.15 / N3.7 / N3.4 (원문 이력 §7.1~§7.3) |
| §7.4 | DEC-02·DEC-03·DEC-04, N3.1 |
| §7.5 / §7.6 / §7.8 / §7.9 | N3.6·N3.8 / N3.8 / N3.7 / N3.7 (원문 이력) |
| §7.7 / §7.10 / §7.11 | N3.9, DEC-16, DEC-25 (원문 이력 "v5.0 교체 원문") |
| §8, §8.4, §8.5, §8.8 | N3.10, N3.10 MOD8, N3.10 MOD9, N3.11 (원문 이력 §8) |
| §9 | 이력 §9 |
| §10.2~§10.5 | N5.3(열림) / 이력 "[판정] §10 닫힌 이슈"(닫힘) |
| §10.1, §10.6~§10.14 | 이력 같은 번호(본문이 있는 첫 번째 출현) |
| §10.15 | N3.13 |
| §11 | 이력 §11 |
| §12.1~§12.4 | 이력("v5.0 교체 원문"), 원자료 |
| §12.5.1 / §12.5.2 / §12.5.3 / §12.5.4 | N3.3 / N3.5 / N3.5 / N3.5 |
| §12.6 / §12.7 / §12.8 | N5.2 / 이력 §12.7 / N2.1 |
| §13.1 / §13.2 / §13.3 | N5.1 / WP-14 / N5.2 |
| §13.4 / §13.5 / §13.6 / §13.7 / §13.8 | N3.10 / N3.11 / N6.1 / 이력 §13.7 / N2.1·N7.2 |
| §14.1 | 이력("v5.0 교체 원문"), 원자료 agent7 |
| §14.2~§14.4 / §14.5 / §14.6 / §14.7 / §14.8 / §14.9 | N3.12 / N4.2 / N4.3 / N3.12.6 / N6.1 / N2.1 |
| §15.1~§15.2 | N3.1 RC, 원자료 |
| §15.3 / §15.4 / §15.5 / §15.6 / §15.7 / §15.8 | N3.2 / N3·N3.15 / N3.1 / DEC-05·N3.8 / N7.1 / N6.1 |

코드 주석 `sizing_recipe.py`의 "계획 §10.3 A8"은 A 계열이 §10.2에 있으므로 "§10.2 A8"(닫힘, 이력)로 읽는다.

### A.2 ID

| 옛 ID | 새 ID |
|---|---|
| 표 A A01~A74 | A01→DEC-01, A02→DEC-04, A03→DEC-02, A04·A05→DEC-03, A06→DEC-05, A07→DEC-06, A08·A09→DEC-07, A10→NFR-1, A11→WP-02, A12→NFR-2, A13→NFR-3, A14→DEC-48, A15→DEC-08, A16→WP-04, A17→DEC-09, A18→DEC-10, A19→DEC-11, A20→DEC-12, A21→DEC-13, A22→DEC-14, A23→DEC-15, A24→DEC-56, A25→DEC-16, A26→LR1~LR9, A27·A29→DEC-17, A28·A30→DEC-18, A31→DEC-19, A32→DEC-20, A33→DEC-21, A34→DEC-22, A35→DEC-23, A36→DEC-24, A37·A38→DEC-55, A39→DEC-25, A40→DEC-31, A41→DEC-26, A42→DEC-27, A43→DEC-28, A44→DEC-29, A45·A62→DEC-01, A46→DEC-30, A47·A48→DEC-46, A49→WP-14, A50→DEC-42, A51→DEC-32, A52→N6.1, A53→DEC-34, A54→DEC-35, A55→U-10, A56→U-02, A57→U-06, A58→DEC-36, A59→DEC-37, A60→DEC-37~40, A61→DEC-41, A63→N3.1 RC, A64→DEC-50, A65→DEC-51, A66→U-09, A67→이력, A68→DEC-54, A69→DEC-52, A70→DEC-18·DEC-19(knee 출발은 LR5), A71→DEC-53, A72→DEC-05·J6, A73→DEC-49, A74→DEC-47 |
| D1~D15 | D1→DEC-31, D2→DEC-32, D3→N6.1, D4→DEC-34, D5→DEC-35, D6→U-10, D7→U-02, D8→U-06, D9→DEC-36, D10·D11→DEC-37, D12→DEC-38, D13→DEC-39, D14→DEC-40, D15→DEC-41 |
| 표 B B01~B21 | B01~B18→WP-01~WP-18, B19→해당 없음, B20→DEC-51, B21→WP-20 |
| 이슈 A/B/G/C (§10) | 열림은 I-A* / I-B* / I-G* / I-C*(N5.3). v5.0에서 닫음: I-G3·I-G7(N1.2), I-G8(N9.3), I-C3(DEC-47), I-C5(WP-14), I-C7(N3.15), I-C9(원표 이력), I-A9(N3.8). DF로 통합: I-A3→DF-16, I-A4→DF-05, I-B7→DF-02, I-B9→DF-01. 신설: I-A10(folded `omega_c` 선측정), I-A11(크로스오버 해석 차이), I-B22(다중 diff pair 오프셋), I-C10(옛 §10.5a-8, U-20), I-C11(옛 A66, U-09) |
| 사고 클래스 C1~C10 | IC1~IC10 |
| 상태 계약 C-a~C-d | SC-a~SC-d(SC-e 신설) |
| auditor 검사 A1~A10(§14.5) | V1~V10 |
| 흐름 G0~G9(§15.5) | GB0~GB9 |
| 근본 원인 R1~R5(§15.2) | RC1~RC5 |
| 보완책 P1~P10(§15.5) | RC 대응(N3.1)과 해당 GB·V |
| L 변경 규칙 R1~R8, R4b(§7.7) | R1→LR1, R2→LR2, R3→LR3, R4→LR4, R4b→LR7, R5·R6·R7→LR8, R8→LR9 |
| test 분리 T0~T7(§13.5) | TS0~TS7 |
| writer 티어 T0~T4(§15.4) | W0~W4 |
| metric 티어 T1~T3(§7.6) | MT1~MT3 |
| 은폐 유형 T1~T11(§14.1) | 원자료 `agent7_self_concealment.md` |
| 강제 겹 L1~L4(§14.4) | EL1~EL4 |
| 결함 #1~#21 | DF-01~DF-21(DF-22 신설) |
| Phase 6·7(§13.6) | 6a~7c(N6.1) |
| D8(구조 정본) | U-06 |

## 부록 B. 이력 문서 색인

| 찾는 것 | 이력 문서 위치(제목) |
|---|---|
| 2026-09-08 이어받을 지점 | `## 0. 이어받을 지점`(첫 번째 출현) |
| 원설계 스키마·알고리즘·헤드룸·검증기·CMRR 결합·DOF·자원배분 | `### 7.1` ~ `### 7.9`(첫 번째 출현, v5.0 전문 블록 이전) |
| 3단계 파일 구조·self-test 분리 원방침 | `## 8.` |
| v4.0~v4.42 구현 기록 | `### 10.6` ~ `### 10.14`(본문이 있는 첫 번째 출현) |
| CircuitGraph 초안 | `## 11.` |
| v4.49 재작성으로 교체된 앞부분·§4·§5·§10 원문 | `## 재작성으로 교체된 원문 (v4.49, 2026-09-14)` |
| §10 닫힌 이슈 판정 | `### [판정] §10 닫힌 이슈` |
| v4.49 계획서 전문(검토 경위 §12.1~12.4, §13.1, §14.1, §15.1~15.2, §7.0 판정표, §7.7/§7.10/§7.11 원문 포함) | `## v5.0 재구성으로 교체된 계획서 전문 (v4.49)` |
| 버전별 변경 | `## Version History` |
