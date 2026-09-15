---
template: plan
version: 5.10
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
| SP1 | stage 분할 규칙(여기 뷰 + 셀 우선순위 + N3.2-4 엣지 비용) | N3.2 |
| S0/S1/S1v/S2/S2p/S3 | Circuit State Graph 층 | N3.3 |
| W0~W4 | 노드전압 writer 티어 | N3.4 |
| SC-a~SC-e | 상태 계약 | N3.5 |
| K1~K8 | stage 경계를 넘는 결합 종류 | N3.7 |
| MG0~MG3 | 스키마 이름 마이그레이션 단계(DEC-69) | N3.16 |
| MT1~MT3 | metric 티어(블록 국소 / 블록 분해 가능 / 전역) | N3.8 |
| LR1~LR9 | L 결정 규칙 | N3.9 |
| MOD1~MOD10 | 모듈(트랜지스터 이름 M1a 등과 구분) | N3.10 |
| TS0~TS7 | test 분리 단계 | N3.11 |
| EL1~EL4 | 역할 분리 강제 겹 | N3.12.4 |
| IC1~IC11 | 기지 사고 클래스와 강제 test | N4.1 |
| V1~V10 | auditor 검사 | N4.2 |
| DF-nn | 현존 결함 | N5.2 |
| I-A* / I-B* / I-G* / I-C* | 열린 이슈(옛 §10 A/B/G/C 번호 유지) | N5.3 |
| J1~J12(J12-a~h) | 회로 해석 공동분석 항목 | N7.1 |
| U-nn | 사용자 결정 착수 조건 | N7.2 |
| RC1~RC5 | gain 분해 실패의 근본 원인 | N3.1 끝 |

레지스트리 등급(R0/R1/R2/D/DUP)은 외부 문서 정의라 개명하지 않고 **"등급 R1"처럼 '등급'을 붙여** 쓴다.

**용어집**

| 용어 | 정의 |
|---|---|
| gain-budget-first | stage별 gain 예산을 **엔진이 유도해 산출**한다. 사용자는 총 gain 제약 하나만 준다. "gain이 gm을 정한다"는 뜻이 아니다 |
| 보상 먼저 | 스펙 목표 (CL, GBW, PM)(필드 이름은 부하 요소 값·`gbw_target_hz`·`pm_target_deg`, N3.16)에서 보상망이 보상 수동소자 값(극점 노드 사이에 걸린 Cc·Rz 등, 개수는 회로마다 다르다)과 gm_1..gm_N의 요구량을 정한다(판정은 봉인 후보마다, DEC-70). 보상은 ID를 직접 정하지 않는다: gm_i 요구량은 봉인 후보마다 `gm_i(θ) ≥ gm_req` 제약으로 판정하고, ID_i는 θ(전류를 정하는 결정변수 포함)에서 KCL로 정한다. 자유 축은 DEC-70의 θ다 |
| 영역(domain) | 모든 규칙·관계 엣지·metric·필드·게이트에 붙이는 표기(DEC-67). **DC**(`dc`) = 동작점: 노드전압·가지전류·VGS/VDS/VSB·KCL/KVL·헤드룸·정지전류·게이트-소스 KVL 루프·벌크 역바이어스·포화 여유. **AC구조** = connectivity만으로 하는 소신호 판정: 교류접지·셀 분류·구동 종류·stage 경계·극성·루프 분류. **소신호 AC 수치**(`ss`) = 봉인된 DC 점에서 LUT로 선형화한 gm/gmb/gds/cgg와 그로 계산한 이득·출력 저항·극점·루프 이득. **대신호**(`ls`) = 슬루·방향별 최대 출력 전류·스윙. 노드전압·전류의 정본은 DC다(DEC-31). `ss`·`ls` 값은 DC 봉인을 통과한 점에서만 계산한다. 봉인 없이 격자 전 범위에서 내는 값은 '상한'이나 '추정'으로 표기하고 판정에 쓰지 않는다. 영역 표기가 없는 계획 행은 절 머리에 선언된 영역(N3.4·N3.6 = DC)을 따르고, 절 머리 선언이 없는 N3.9 LR은 DC(L·VDS)다. design 문서와 코드 필드는 개별 표기가 필수다 |
| 소자 역할(DC·AC) | 소자 역할은 두 벌로 기록한다. **DC 역할**(뷰 무관, S1): 바이어스 전류원 / diode 기준 / 신호 소자. KCL·미러·`equal_vgs` 관계로 유도한다. 게이트-소스 KVL 루프 소속은 역할이 아니라 `kvl_branch` 엣지로 기록한다(DEC-64). **AC 역할**(뷰별, S1v): CS·CG·CD·pass 셀, load. 한 소자가 DC 역할은 바이어스 전류원이고 AC 역할은 gate로 신호를 받는 CS일 수 있다(K8) |
| G_vgs | MOS gate–source 무향 엣지와 레일을 병합한 고정 노드로 만든 DC 관계 그래프. 기본 사이클을 `equal_vgs`(평행 엣지) / 포트 차 루프 / `kvl_branch` 등식 / VDS 엣지 하나 포함 부등식으로 분류한다(DEC-64). 신호 루프 분류(N3.2-2)와 무관하며 루프 뷰를 만들지 않는다 |
| 여기 뷰 | S1v에서 만드는 신호 그래프. 두 종류뿐이다: (AC구조) **전달 뷰**(metric 선언 `(ac_excite, sense)` 하나에 하나, 선언된 여기원 밖은 교류접지)와 **루프 뷰**(S1에서 찾은 되먹임 루프 중 N3.2-2 조건을 만족하는 루프 하나에 하나, 외부 여기원 전부 교류접지, 루프 끊는 점이 입력). 셀 분류·구동 종류·stage·극점 노드 목록·블록 속성은 뷰마다 따로 기록한다(N3.2-3) |
| signal stage | (AC구조) S1v 여기 뷰에서 SP1로 유도한 stage(gain 할당은 gain 제약 metric이 선언한 전달 뷰의 것을 쓴다): {AC 역할 멤버 input, cascode, follower, pass, load / tail(DC 역할이 바이어스 전류원인 소자 중 그 뷰에서 둘 이상 셀의 공통 source 노드에 drain이 붙은 것, N3.2-6), 출력노드, 출력노드 임피던스 등급, 블록 노드 집합} |
| 셀 | 트랜지스터 하나의 소신호 역할. 신호 입력 단자와 출력 단자로 정한다: CS(gate->drain), CG(source->drain), CD(gate->source, follower), pass(source↔drain, gate가 그 뷰의 신호 경로 밖 -- 뷰 입력에서 방향 신호 그래프로 도달하지 않는 넷, 바이어스·diode 구동 넷 포함. 예: 파일럿 floating battery M9a/M9b는 gate 넷 N11b·N14a14b가 diode 구동 넷이라 pass. '바이어스'라는 말은 DC 역할에만 쓴다). 모든 트랜지스터에 같은 규칙으로 붙인다(AC구조, 뷰별). gate로 신호를 받는 소자의 출력 단자는 그 뷰의 교류접지가 아닌 채널 단자다: drain이 교류접지면 CD, source가 교류접지면 CS, 둘 다 아니면 N3.2-3 셀 판정 기준 |
| 입력 노드 구동 종류 | (AC구조, 뷰별) 그 뷰의 신호 경로에서 신호가 노드로 들어오는 단자의 종류. 신호가 신호 셀의 **drain**으로 들어오면 **전류 구동**(예: 캐스코드 source 노드), 신호 셀의 **source**(CD 출력)·**입력 포트**(이상원)·**앞 stage 출력노드**로 들어오면 **전압 구동**이다. **저항**을 거쳐 들어오면 '값 의존' 속성으로 기록한다. 구조 판정이 필요한 곳(GB2 stage 경계, K8)에서는 6a-2 J12 ratify로 정해 `structure.json`에 기록한 구동 종류를 쓰고, GB8은 값이 확정된 봉인 점에서 그 ratified 값과의 일관성만 검사한다(탐색 중 불일치는 그 후보의 실패 `structure_inconsistent`(margin = 판정 경계까지 거리)로 기록하고 탐색을 계속한다. 최종 해에서 불일치하면 STRUCTURE_UNRESOLVED로 보고하고 J12 재분석 대상으로 올린다). 예: `sf_pushpull_output_opamp` N5(R1a[N5, N1]와 M5 drain으로 신호 진입). 신호를 싣지 않는 DC 역할 소자(바이어스 전류원·diode 기준으로 gate가 그 뷰의 신호 경로 밖인 소자)의 단자는 신호 진입이 아니라 부하로만 센다(예: `pushpull_follower_buffer` A는 M3 source로 신호가 들어와 전압 구동, M5 drain은 부하). **혼재 우선 규칙**: 한 노드에 신호 셀 source(전압 진입)와 측면 주입 셀(K8, DC 역할 바이어스 전류원이면서 gate로 신호를 받는 셀)의 drain이 함께 들어오면 전압 구동으로 판정하고, drain 쪽 셀이 측면 주입이 아니면 `review_needed`(`기록만` 규칙 분기)다(예: `sf_pushpull_output_opamp` N17·N20, J12-b ratify 대상). stage 경계를 정한다(N3.2-5) |
| declared stage | topology.json에 사람이 적은 stage 정보(`compensation.stage_devices`, `gain_stages_sum.stages` 등). 대조 대상일 뿐 정본이 아니다 |
| 출력노드 | stage 안에서 신호가 마지막으로 도달해 다음 stage 입력 또는 출력 포트로 넘어가는 노드. CS·CG 사슬이면 drain 노드(고임피던스), CD·pass로 끝나면 source(또는 pass의 반대쪽 단자) 노드(저임피던스일 수 있다). 임피던스 등급은 노드 속성으로 기록한다 |
| 노드 어드미턴스 | (소신호 AC 수치, 봉인 통과 점) 노드에 붙은 소자 단자별 소신호 기여의 합: drain 단자 gds, source 단자 gm+gmb+gds(게이트가 교류접지일 때), 수동소자 어드미턴스. 캐스코드·follower 효과는 아래 블록 국소 모델이 자동으로 포함한다 |
| 블록 gain | (소신호 AC 수치) 블록 국소 소신호 모델(N3.8)로 푼 출력노드 대 입력의 전압비(dB, 이름 `gain_ss_db`). CS 한 단의 특수 케이스가 `20·log10(gm_in / G_out)`, CD 한 단의 특수 케이스가 `20·log10(gm / (gm + gmb + G_node))` |
| 블록 종류 | **이득 블록**(N3.2-5 구동 종류 규칙으로 새 gain stage를 시작한 셀 -- CS 또는 source가 전압 구동인 CG -- 부터 출력노드까지, gain 할당 대상) / **버퍼 블록**(CD로 끝나는 구간(pass는 DEC-63 예외 규칙), 할당 대상 아님 -- 출력 임피던스와 구동 전류로 평가. 한 입력 넷에서 갈라져 같은 출력노드로 합류하는 follower 사슬 묶음은 버퍼 블록 하나이며 중간 노드를 블록 노드 집합에 넣는다, `계산 규칙 있음`. 묶음은 DEC-63의 R(u) 절차로 만들고 합류 노드가 둘 이상이면 `기록만`. 버퍼 블록은 gain 목표를 받지 않지만 내층 DP 단계로 결정한다). 버퍼를 독립 블록으로 둘지는 J10 |
| 극점 노드 목록 | (AC구조) 보상(GB5)·슬루 규칙이 소비하는 노드 목록(슬루 규칙(대신호)은 뷰와 무관하게 gain 제약 metric 전달 뷰의 목록을 쓰고, 루프 뷰의 목록은 루프 안정도에만 쓴다): 해당 여기 뷰에서 교류접지 집합이 아닌 모든 노드(수동소자 사이 내부 노드 포함). 노드마다 소속 블록, 임피던스 등급, 종류(gain stage 출력노드 / 버퍼 블록 출력노드 / 캐스코드 source / diode 연결 단자가 붙은 노드 / 수동소자 내부 노드 등)를 속성으로 기록하고, 보상에서 뺄 노드는 `parasitic_pm_ss_deg` 기여 계산 결과로만 뺀다. gain 할당 단위(gain stage)와 따로 둔다(N3.2-6) |
| 블록 속성 | 블록마다 영역별로 따로 기록하는 값: `ss` = 전압 이득 `gain_ss_db`(블록 국소 모델), 출력 임피던스 `rout_ss_ohm`(같은 모델에서 출력노드 테브난 임피던스) / `ls` = 방향별 최대 출력 전류 `i_out_max_source_amp`·`i_out_max_sink_amp`(DEC-65, N3.8). 모두 봉인 통과 점에서 계산한다 |
| 결합 블록(coupling block) | signal stage 하나에 대응하는 할당 단위 |
| 결합변수 y | 두 결합 블록 이상에 걸친 관계 엣지의 상태(K1~K4) |
| 계산 블록(compute block) | 평가 커널을 나눈 계산 단위(입력·출력 선언, S2 memo 단위) |
| 순환 블록(cycle block) | 유도 DAG의 SCC. 명시적 고정점으로 푼다 |
| 교류접지 집합 | (AC구조) 레일(`supply_nets` 선언, DEC-60. 레일 넷은 DC에서는 W0 고정 전압 `supplies_v`이고 AC구조에서는 모든 뷰의 교류접지다. 그 넷을 `ac_excite`로 선언한 전달 뷰(PSRR 등)만 예외) / gate에만 붙고 구동되지 않는 넷(입력·수동소자·이상원 단자 제외) / 이상 전압원 단자 |
| 대칭 축약 | 대칭 회로의 전달 뷰를 반회로로 줄이는 계산 수단. 여기가 순수 기모드(대응 포트가 반대 부호)면 자기대응 넷을 가상접지로 두고(**기모드 축약**, 옛 이름 DM 뷰), 순수 우모드(같은 부호, 레일 여기 포함)면 대응 넷을 합친다(**우모드 축약**). 여기가 섞이거나 대칭이 불완전하면 축약하지 않는다. 축약 결과는 비축약 전체 뷰와 같아야 한다 |
| 봉인(seal) | metric 계산 전 S2 `dc` 스냅샷이 N3.6 봉인 항목(DC)을 모두 통과한 상태. S2 `ss`·`ls` 필드는 봉인 통과 스냅샷에서만 쓴다 |
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
| library 회로 | `library/*.topology.json`의 회로 전부(`_TEMPLATE` 제외, 현재 7개) = 기존 4개 회로 + `two_stage_ota_sf` / `pushpull_follower_buffer` / `sf_pushpull_output_opamp`. 구조 유도와 규칙 분기 발동표의 대상(DEC-47) |
| 기존 4개 회로 | `current_reuse_telescopic_ota`(파일럿) / `folded_cascode` / `two_stage_ota` / `nmcnr_amplifier`. declared stage·기존 기준선·equivalence 대조가 있는 회로 |
| 사이징 대상 회로 | library 회로 중 사이징 스펙이 선언된 회로. 현재 기존 4개 회로. 스펙 확정(U-25)·실행 이관 대기: `sf_pushpull_output_opamp`·`pushpull_follower_buffer`(agnd 레일, 실행 `SPECS` 이관은 DEC-60 구현 뒤), `two_stage_ota_sf`(실행 `SPECS` 이관은 사이징 착수 시). 실행 선언되면 들어온다. 사이징·metric·탐색 완료 조건의 대상 |
| 규칙 분기 | SP1·루프·보상·출력 구동·L 규칙·metric 정의·DC 루프 탐지에서 결과를 가르는 경우 하나(예: tail 없는 L 동치류 주인, CD 셀, 버퍼 묶음(단일 합류), G_vgs 사이클 v0/v1/v2·VDS-1, 방향별 전류 β/σ, 측면 주입, 전압 구동 CG stage 시작, 순수 follower, 단일 입력 여기, 주 신호 분기·합류가 있는 이득 블록 DAG). 목록 정본은 6a design이 두고 규칙을 추가할 때 함께 늘린다. 분기마다 `계산 규칙 있음 / 기록만` 속성을 둔다 |
| 검증 발동 회로 | 그 규칙 분기가 발동하고, 발동 결과가 ratified 대조표(J)와 일치하며, 그 분기가 `계산 규칙 있음` 속성인 library 회로. `기록만` 분기에는 검증 발동 회로가 없다(DEC-59) |

---

## N1. 목표·범위·요구

### N1.1 목적

gm/ID 사이징의 결정 순서를 **signal stage 유도 -> 보상 -> gain 할당(gm_id·L) ⇄ 노드전압 DC 해석 -> 전체회로 판정**으로 세운다. 설계 목표:

* (a) stage·부하·결합을 connectivity에서 유도하고, 회로 해석이 걸린 것만 사람과 확정한다.
* (b) stage gain을 출력노드 임피던스로 정의하고, 제약 판정은 전체회로 MNA gain으로 한다.
* (c) 노드전압·가지전류를 DC 정본으로 두어 KVL·vsb·매칭 불일치를 표현할 수 없게 하고, 소신호·대신호 값은 봉인된 DC 점에서만 계산한다(DEC-67). AC·대신호 결과는 DC 값을 덮어쓰지 않고 결정변수의 제약으로만 되돌아간다(DEC-70).
* (d) 계산 결과(실패 포함)를 입력 지문으로 재사용하고, 이전 결과로 시작점을 정제한다.
* (e) 코드 작성, 판정 기준 작성, 판정 실행을 서로 다른 주체가 맡고 기계적으로 강제한다.

이력: 출발 문제(2026-09-04 diode 헤드룸 rail-lock)와 v4.0~v4.49 경위는 이력 문서 §0, §1, §10.6~§10.14, Version History.

### N1.2 범위

**In scope**: N6.1의 Phase 0.5~7c 전부, library 회로 전부(측정 대상 구분은 DEC-47). 지원 범위는 회로 부류가 아니라 규칙 분기의 검증 발동으로 정한다(DEC-59).

**Out of scope**

| 항목 | 이유 |
|---|---|
| 현재 검증 발동 회로가 0인 부류 | 규칙 분기 기준으로 library에 검증 발동 회로가 없어 DEC-59 게이트가 탐색 전에 정지시키는 회로(I-G3·I-G7 해소). 현재 예: 비증폭 회로(밴드갭, constant-gm bias, 비교기, 스위치드 커패시터), gain boosting·regulated cascode(게이트가 전류 구동 노드인 CS, N3.2-9), 전류 입력 포트·트랜스임피던스 전달 뷰, 수동소자 전역 되먹임 루프(저항 되먹임, 분압 되먹임), 주 신호 분기·합류가 있는 이득 블록 DAG(feedforward), nmos·pmos 밖 kind. 분기의 계산 규칙을 정의하고 발동 회로를 library에 넣어 ratify하면 범위에 들어온다(N9.3). 계산 규칙 없이 기록만 하는 분기는 ratify만으로 들어오지 않는다 |
| PVT 코너 스윕 | LUT는 TT·기록된 온도 한 조건. 코너 메타는 기록만 한다(I-A5 범위 부분 해소) |
| 레이아웃 알고리즘 변경 | common-centroid·오일러·finger·floorplan은 MOD7로 옮기기만 한다 |
| 코드 추가가 필요한 토폴로지 추가 | 새 토폴로지는 데이터만으로 추가한다(DEC-62, N9.3). 코드가 필요하면 규칙 결함(DF)으로 다룬다 |

### N1.3 기능 요구

| ID | 요구 | 근거 결정 |
|---|---|---|
| FR-1 | signal stage는 connectivity에서 SP1로 유도한다. declared stage와 다르면 `review_needed`로 기록하고, 회로 해석은 공동분석(J)으로 `ratified`한다 | DEC-43, DEC-44 |
| FR-2 | 블록 gain은 블록 국소 소신호 모델(출력노드 정의는 소자 구성에 따른다: CS·CG는 drain, CD·pass는 source 쪽)로 정의한다. gain 제약 판정은 전체회로 MNA gain 하나로 하고, 블록 gain 합과의 잔차를 매 평가 기록한다 | DEC-05 |
| FR-3 | 보상이 먼저다: (CL, GBW, PM)에서 보상 수동소자 값을 계산하고, gm_i 요구량과 기생 pole L 상한은 θ의 제약으로 봉인 후보마다 판정한다(보상이 ID를 직접 정하지 않는다) | DEC-02, DEC-24, DEC-25, DEC-70 |
| FR-4 | gain 할당은 엔진이 유도해 `gain_budget_db`로 **출력**한다. 결합 블록 3층 할당을 쓴다. 공유 VGS는 gain 기준으로 고르고 L 동치류의 주인은 DEC-17 규칙으로 정한다 | DEC-03, DEC-45, DEC-10, DEC-17 |
| FR-5 | 노드전압이 DC 정본이다. 소자 vds/vgs/vsb는 노드전압 차이로 유도하고, writer 티어 W0~W4로 쓰며, 순환은 명시적 고정점으로 푼다. 모든 규칙·필드·metric·게이트는 영역(DC / AC구조 / `ss` / `ls`)을 표기하고 `ss`·`ls` 값은 봉인 통과 점에서만 계산한다 | DEC-31(D1), DEC-32, DEC-67, DEC-70 |
| FR-6 | 모든 소자의 V/I 관계를 상시 검증한다: 내부는 봉인 게이트(N3.6), 독립 검증은 트랜지스터 레벨 SPICE | DEC-48 |
| FR-7 | 계산 결과를 버리지 않는다: 입력 지문 기반 재사용, 실패도 margin과 함께 기록, 이전 결과로 시작점 정제 | DEC-30 |
| FR-8 | 달성 불가를 탐색 전에 보고한다: 블록별 gain 상한 합(AC 상한, 봉인 불필요, 보수적), 구조·수치 DOF | N3.1 RC3·RC4 |
| FR-9 | JSON·spec·계획 문서의 필드 이름은 명명 규칙 하나를 따르고, 개념 하나에 이름 하나·저장 위치 하나다. 옛 이름은 조용히 읽지 않고 로드 게이트가 거부한다 | DEC-68, DEC-69 |

### N1.4 비기능 요구

| ID | 요구 |
|---|---|
| NFR-1 | **버그 free 최우선.** 기존 함수 시그니처 보존은 목표가 아니다. 판단 기준은 "물리적으로 옳은가, 조용한 실패가 구조적으로 불가능한가"다 |
| NFR-2 | **효율.** 같은 계산을 호출부마다 반복하지 않는다. 캐시 키는 그 계산이 실제로 읽는 모든 가변 상태의 내용 지문이다. 캐시는 상한을 두고 초과 시 LRU로 밀어낸다(캐싱 중단 금지). **합격 기준**: 계산 블록별 memo 적중·미적중 계수와 같은 입력 해시의 재계산 횟수를 매 실행 기록한다. 같은 실행 안에서 같은 입력 해시로 같은 계산 블록을 다시 계산한 횟수는 0이어야 한다(LRU 퇴출로 인한 재계산은 퇴출 기록과 함께 별도 집계). 최적화 판단 근거는 cProfile과 중복 인자 계측 기록이다(WP-10). 계측 도구는 test-author 소유이고(WP-13), 6b DoD(평가 커널·S2 memo)와 7b DoD(3층 할당·역방향 제약)에서 판정한다. 구체 방법(캐시 키 구성, 계산 블록 분할 단위, 무효화 조건, 계측 형식)은 해당 design이 정한다 |
| NFR-3 | **기지 사고 재발 불가.** IC1~IC11(N4.1)마다 거부 케이스를 가진 강제 test가 있어야 한다 |
| NFR-4 | **결정론.** 모든 반복은 정렬된 시퀀스 위에서 한다(`set` 순회 금지). 같은 입력은 같은 산출물을 낸다 |
| NFR-5 | **스펙에 딱 맞춘 최적화, 불필요한 계산 최소화**(2026-09-15 사용자). 성능·레이아웃을 스펙보다 과하게 만들지 않는다: 최종 해에서 활성 제약의 여유는 해당 metric의 격자 분해능 이하이고, 면적은 제약을 만족하는 최소에 가깝다. 같은 결과를 내는 탐색이면 평가 수가 적은 쪽을 택한다(선택 근거는 실측). 여유 조건은 **활성 제약에만** 적용한다: 다른 제약(전력 최소점, W 한계 등)이 해를 정해 비활성인 제약의 초과는 스펙 오버가 아니며, 보고 시 제약마다 활성/비활성을 구분한다. 레이아웃을 이유로 L을 통일하지 않는다(LR8) |

---

## N2. 확정 결정·원칙

### N2.1 결정 레지스터

**무엇이 이미 정해졌는지는 이 표가 정본이다.** 현행 형태만 적는다(대체된 형태와 결정 경위는 이력 문서, 출처 줄 번호는 원자료 `rewrite_X_decisions.md`). 상태: **구현됨** / **부분**(잔여 명시) / **미구현** / **착수 조건**(N7.2의 사용자 결정) / **원칙**(구현 대상이 아닌 규칙).

| ID (별칭) | 결정 | 날짜 | 적용 | 상태 |
|---|---|---|---|---|
| DEC-01 | 목표는 gain-budget-first다. Circuit State Graph는 stage 분할과 gain 할당을 위한 기반이다 | 2026-09-04, 09-14 | 전체 | 미구현 |
| DEC-02 | 인과 방향은 보상 먼저: (CL, GBW, PM) -> (보상 수동소자 값, gm_1..gm_N 요구량), 이후 자유 축은 DEC-70의 θ. 요구량은 DC 값을 덮어쓰지 않고 봉인 후보마다 θ의 제약으로 판정한다(DEC-70) | 2026-09-07 | GB5 | 부분(Cc 유도만) |
| DEC-03 | stage별 gain 예산은 엔진이 유도해 `gain_budget_db`로 출력한다. 사람이 배분을 강제하는 유일한 경로는 `gain_budget_db_override`(출처 필수) | 2026-09-07 | GB0, GB6 | 미구현 |
| DEC-04 | **(2026-09-14 재정의, 사용자 "난 강제하고 싶지 않아")** 블록 안 소자(input·cascode·load·tail)의 gm_id·L은 S1 등식 관계(매칭, L 동치류, 공유 VGS)로 묶인 것을 제외하면 소자마다 **독립 결정변수**다. 함께 정하라는 규칙을 두지 않는다. 소자 사이의 결합은 블록 gain·헤드룸·면적·PM 같은 목적함수와 제약이 만들 뿐이다. 캐스코드 L을 role 배수로 따로 정하지 않는 것은 DEC-18·LR5가 담당한다(옛 형태 "input+cascode 동시 결정"은 철회). 입력-캐스코드 블록의 L을 같게 강제하는 규칙을 복원할지는 7b 실측으로 정한다(U-23). 회로·kind·블록 단위 단일 L을 두고 VDS를 주 변수로 삼는 방식은 채택하지 않는다: 파일럿에서 미러 L 동치류(8소자, 11소자)가 블록 5개를 가로질러 블록 단일 L이 회로 단일 L로 붕괴하고, kind가 다른 소자를 묶으면 반회로 분리가 깨져 조합 수가 줄어도 평가가 늘며(블록 단일 L 6.5초 대 독립 L 5.4초), W 한계가 L을 요구하는 소자(파일럿 stage1 pmos 입력)는 VDS로 대신할 수 없다(knee 근방 단일 L은 면적 약 3배, 70dB 초과 불가). 선측정 원자료 `docs/03-analysis/gain-budget-gmid-sizing-function-audit/review3_opt_L_vs_VDS.md`(블록 국소 모델, tt 한 코너) | 2026-09-04, 09-14, 09-15 | GB6 내층 | 미구현 |
| DEC-05 | gain 제약 판정은 전체회로 MNA gain 하나로 한다. 블록 gain(블록 국소 소신호 모델, 부하·follower·pass 포함)은 할당용 분해 값이고, 두 값의 잔차를 매 평가 기록한다 | 2026-09-14 | GB8 | 미구현(현 제약은 `gain_stages_sum`, I-B21) |
| DEC-06 | theta는 자유 탐색 변수만이다. 구조 선언은 `sizing_spec.json`의 선언/유도 필드로 옮긴다 | 2026-09-07 | GB0, MOD2 | 미구현 |
| DEC-07 | 목적함수는 전력 최소화 하나, 면적은 `area_um2` 상한 제약. 면적 예산이 선언되지 않으면 전력-면적 Pareto를 제시하고 정지한다 | 2026-09-07 | GB6, GB9 | 미구현(전력 정의 U-10, Area 정의 U-13) |
| DEC-08 | (DC) 이상 전류원 정지 전류 `value_dc_amp`(현 topology 키 `ideal_sources[].value_amp`, 문서 기록 `IBias_amp`를 흡수. 이름 변경과 저장 위치 이관은 MG3, DEC-69)가 null이면 자유 탐색, 값이 있으면 그 값을 실제 전류로 고정한다. 같은 소스를 움직이는 theta와 공존하면 로드 거부 | 2026-09-08 | GB0 | 부분(KCL 잔차 metric만 소비). 파일럿 Iref `value_dc_amp = 1.2µA`(현 키 `value_amp`)는 사용자가 원문에서 확인한 고정 대상(사이징 경로 미배선, I-B14) |
| DEC-09 | 게이트·소스를 공유하는 전류미러 멤버는 전부 VGS를 강제로 공유한다(`equal_vgs`). 파일럿 적용(ratified 대상): 18소자, tail M5/M6를 bias 미러에 묶음(설계 의도) | 2026-09-09 | GB1, K2 | 구현됨(소자 이름 리터럴 여부 DF-23) |
| DEC-10 | 공유 VGS(DC)는 gain(`ss`) 기준으로 고른다(면적 기준 아님). 후보 VGS마다 GB7 봉인을 통과한 점에서만 gain을 계산해 비교하고, 봉인 실패 후보는 margin을 기록하고 비교에서 뺀다(좌표 평가 1회 = 평가 커널 1회). gain 폭이 분해능 이하인 그룹의 기준은 U-14 | 2026-09-09 | GB6 중층 | 미구현 |
| DEC-11 | LUT 역보간 `_solve_vgs`는 목표를 품는 가장 오른쪽 구간에서만 보간한다(rightmost root). 곡선 범위 밖은 명시적 실패 | 2026-09-09 | MOD1 | 구현됨(다른 이분 역산은 DF-10) |
| DEC-12 | diode 창은 VGS를 공유하는 미러 멤버 전원의 W 한계를 함께 본다. 멤버 vds가 미정이면 그 멤버의 포화 하한(DEC-27의 VDsat)을 바닥으로 쓰고, 멤버 L/ID 미정은 명시적 실패 | 2026-09-09 | W2 | 부분(현 코드는 선언 역할별 `min_vds` 바닥. 6b에서 S1 관계 엣지 기반·DEC-27 VDsat 바닥으로 전환, DF-25) |
| DEC-13 | 적층 diode는 2변수로 함께 푼다. vsb는 DEC-61로 노드전압과 bulk 넷에서 유도하며, 두 소자의 bulk가 같을 때 아래쪽 vsb = 위쪽 vsb + 위쪽 vds가 그 특수형이다 | 2026-09-09 | W2 | 부분(DF-01) |
| DEC-14 | diode vds는 나눠줄 몫이 아니라 구간 제약 변수이고, diode gm_id는 vds의 종속값이다 | 2026-09-08 | W1, W2 | 구현됨 |
| DEC-15 | (DC) gate-source 사슬로 닫힌 KVL 루프(`kvl_branch`) 멤버는 S1 관계 엣지 `kvl_branch`로 루프 전압 기준 관계를 기록하고 DC 역할은 바꾸지 않는다. AC 역할(신호 경로 여부, 셀)은 뷰별 셀 분류(N3.2-3)가 따로 정하며 DC 루프 소속과 무관하다. 탐지 규칙은 DEC-64이고 이 행은 그 사례다. 파일럿 적용(ratified 대상, J12-c 대조): M11a/M11b/M20a/M20b(class-AB 배터리) | 2026-09-09, 09-15 | GB1 | DEC-64로 통합(현 구현은 선언 기반, 소자 이름 리터럴 여부 DF-23) |
| DEC-16 | 초기 L은 공정 knee에서 시작하고 실현가능 창으로 clamp한다 | 2026-09-07 | LR5 | 구현됨(`measure_L_knee`, `derive_role_L`) |
| DEC-17 | L 동치류의 주인: 동치류에 tail이 있으면 tail. 여기서 tail은 **DC 역할**이다(뷰 무관, S1): `kcl_group`에서 둘 이상 소자의 공통 source 노드 전류를 공급하는 바이어스 전류원. 여럿이면 gain 제약 metric 전달 뷰의 최초 gain stage에 붙은 것 우선(이 선택은 GB2 뒤에 확정하고 GB1은 후보로 기록한다. 뷰별 AC tail 표기는 대조용이다). 없으면 `kcl_group`에서 다른 멤버의 전류를 정하는 전류 출처 멤버, 그것도 없으면 이름 정렬 첫 멤버. 동치류 멤버는 L을 공유하고, 공통 L은 모든 선언 제약을 동시에 만족하도록 탐색한다. 동치류 안에서 L이 갈리면 에러 | 2026-09-10, 09-15 | GB1, LR2 | 부분(tail 주인만 구현, tail 없는 동치류 규칙은 6a. 층0 게이트의 `ValueError`는 DF-03) |
| DEC-18 | L theta는 동치류에서 일반 규칙으로 파생한다(소자·theta 이름 지정 금지). role 배수 상수(`_L_ROLE_MULTIPLIERS`)는 쓰지 않는다 | 2026-09-10 | GB1 | 구현됨 |
| DEC-19 | warm start 격자에 L 동치류 theta를 포함한다 | 2026-09-10 | GB9 | 구현됨 |
| DEC-20 | 제약 임계값은 근거가 되는 선언값 하나만 두고, 파생 임계값은 `value_from_constraint`로 참조한다 | 2026-09-10 | GB0 | 구현됨(`mirror_ratio_error_mV`) |
| DEC-21 | (DC 오차) `mismatch_sigma_mV = 5.0`은 회로 안에서 유도할 수 없는 시스템 입력이다. 출처 선언이 필요하다 | 2026-09-10 | GB0 | 착수 조건 U-17 |
| DEC-22 | 제약 임계값 도출은 bisection(임계값만 움직이며 원래 탐색 반복, 마지막 성공값, 여러 시드 전부 성공)으로 한다 | 2026-09-10 | N3.13 | 미구현 |
| DEC-23 | 입력환산 오프셋(DC 오차량을 봉인점의 gm으로 환산, 영역 `dc→ss`)은 gm 가중 RSS, 캐스코드 제외. 쌍 = offset 매칭 선언 ∩ 게이트가 ports input 넷. 이 쌍 규칙은 차동 입력쌍 분기이며(DEC-59 발동표에 기록), 입력이 대칭 쌍이 아닌 회로는 I-B22 | 2026-09-10 | GB8 | 구현됨(DF-12) |
| DEC-24 | 보상 수동소자(Cc, Rz 등) 값은 보상망이 계산해 확정한다(spec 손값은 폴백) | 2026-09-10 | GB5 | 구현됨 |
| DEC-25 | L 상한은 상수 N 없이 기생 pole의 위상 기여를 직접 계산한 `parasitic_pm_ss_deg >= pm_target_deg`로 건다(현 코드 이름 `parasitic_pm_deg`·`PM_target_deg`, MG3). 이 부등식은 봉인 통과 점마다 판정하는 θ의 제약이다(DEC-70). 격자 경계(GB4·LR5)로 쓸 때는 '봉인 전 추정 경계'로 표시한다 | 2026-09-10, 09-15 | GB5, LR6 | 구현됨(정본은 전체 주파수응답. 노드별 근사 `node_pole_estimate`는 못 세는 고임피던스 노드를 `undetermined`로 실패시킨다. 사이징 대상 회로 선측정 미완 I-A10) |
| DEC-26 | spec은 `run_harness.canonical_spec()`만 정본이다. 변형은 `derived_spec(why 필수)`로만 만든다 | 2026-09-10 | GB0, S0 | 구현됨 |
| DEC-27 | (DC) VDS 엣지를 정확히 하나 포함한 게이트-소스 KVL 루프(DEC-64의 VDS-1 사이클) 사례: 루프 전압(루프 양끝 노드 전압 차 − 루프 안 다른 소자 VGS 합)을 그 루프 소자의 gm_id 탐색 상한으로, 포화 하한은 VDsat로 둔다. VDsat는 LUT 열로 읽지 않는다(LUT에 VDsat 열이 없다) -- 6b design이 LUT의 (ID, gds, VDS) 곡선에서 유도 규칙을 정한다. 파일럿 적용(ratified 대상): class-AB 배터리 `V_bat = vdd − VGS(M15) − VGS(M16)` | 2026-09-10, 09-15 | W2 | 부분(탐지는 DEC-64로 통합.파일럿 KVL 상한 구현. 포화 하한은 현 코드가 강반전 근사 `2/(gm/ID)`, DF-25, 6b) |
| DEC-28 | 실현 불가 기준점 복구는 회로 이름 없는 일반 규칙으로만 한다 | 2026-09-10 | GB9 | 구현됨(DF-04) |
| DEC-29 | 신호 방향은 뷰 입력(전달 뷰 = 여기 포트, 루프 뷰 = 끊는 점)에서의 0-1 BFS 거리로 정의하고, 방향은 여기 뷰(S1v)마다 둔다(노드 단일 속성 금지) | 2026-09-10, 09-14 | GB2 | 미구현 |
| DEC-30 | 계산 결과(노드전압·신호방향·실패 포함)를 버리지 않고 재사용·점진 정제·전역 최적화에 쓴다 | 2026-09-14 | N3.3~N3.5 | 미구현 |
| DEC-31 (D1) | **노드전압이 DC 정본이다.** 소자 vds/vgs/vsb는 노드전압 차이로 유도한다 | 2026-09-14 | GB7, W0~W4 | 미구현 |
| DEC-32 (D2) | 순환 블록 수렴 허용오차는 LUT 보간 오차(leave-one-out)에서, 반복 상한은 그 허용오차와 구간폭·수축비에서 계산한다. LUT 격자 간격은 FD 스텝과 bisection 구간에 쓴다(식: N3.6, N3.7) | 2026-09-14 | GB7 | 미구현 |
| DEC-34 (D4) | 전역 샘플 수는 사람 선언 `wall_clock_budget_s`(7b 전에는 `SPECS[circuit]` 항목, 7b부터 `sizing_spec.json` human. 기본안은 파일럿 선언값 300 s(5분)를 모든 사이징 대상 회로에 같게 적용하고 사용자가 회로별로 바꿀 수 있다, 확정 U-26) 안에서 실측 시간으로 계산한다(식: N3.5) | 2026-09-14 | GB9 | 미구현 |
| DEC-35 (D5) | `ports`는 오케스트레이터가 connectivity로 제안 -> 표로 사용자 확인 -> 반영한다 | 2026-09-14 | 6a | 착수 조건 U-08 |
| DEC-36 (D9) | test 프레임워크는 pytest(설치된 9.0.2). 플러그인 추가 없음 | 2026-09-04 | tests | 미구현 |
| DEC-37 (D10, D11) | 결함 수정에 순서 예외는 없다(DF-03·DF-18도 Phase 4). 메인 세션(오케스트레이터)은 엔진 소스·tests를 쓰지 못한다(EL1 강제) | 2026-09-14 | Phase 4, EL1 | 미구현 |
| DEC-38 (D12) | test-author는 interface card만 입력으로 받고 소스 경로 Read가 거부된다. test의 독립성은 결과(V3, V4)로 검사한다 | 2026-09-14 | N3.12 | 미구현 |
| DEC-39 (D13) | 뮤테이션은 자체 AST 변이기로 한다(의존성 추가 없음) | 2026-09-14 | V3 | 미구현 |
| DEC-40 (D14) | 기준 약화는 매 건 사용자 승인. 승인 기록 없이 병합 불가 | 2026-09-14 | V5 | 미구현 |
| DEC-41 (D15) | 역할 분리 hook을 프로젝트 `.claude/settings.json`에 등록한다(스크립트 완성과 거부 확인 뒤) | 2026-09-14 | Phase 0.5 | 미구현 |
| DEC-42 | 코드 작성(gmid-code-author), 판정 기준 작성(gmid-test-author), 판정 실행·보고 수치(gmid-verification-auditor)를 분리하고 EL1~EL4로 강제한다 | 2026-09-14 | N3.12 | 미구현 |
| DEC-43 | stage 분할은 SP1(여기 뷰 + 셀 우선순위 + N3.2-4 엣지 비용)로 한다. 회귀 기준은 공동분석으로 `ratified`된 분할이다 | 2026-09-14 | GB2 | 미구현 |
| DEC-44 | 회로 해석이 걸린 판정(교류접지 예외, 부하 귀속, 역할)은 사람과 공동분석으로 확정하고, 엔진은 증거와 함께 `review_needed`까지만 낸다 | -- | GB1, GB2 | 원칙 |
| DEC-45 | gain 할당은 3층이다: 결합변수 y 고정 블록 DP / y 좌표강하 / DP 해에서 SLSQP 미세조정 | 2026-09-14 | GB6 | 미구현 |
| DEC-46 | 코드는 10모듈(N3.10)로, 인라인 self-test는 `tests/` pytest(N3.11)로 분리한다. stick_diagram self-test도 포함 | 2026-09-04, 09-14 | Phase 1, 3 | 미구현 |
| DEC-47 | 모든 동작 변경 Phase는 library 회로에서 측정한다: 구조 유도(SP1 셀·stage·극점 노드·루프 탐지·규칙 분기 발동표)는 library 회로 전부, 사이징·metric·탐색은 사이징 대상 회로 전부, 기존 기준선·declared stage·equivalence 대조는 기존 4개 회로(용어 N0.4) | -- | 전체 | 원칙 |
| DEC-48 | 전체회로 물리 정합성(KVL/KCL/VGS)을 파이프라인 상시 게이트로 둔다 | 2026-09-04 | GB7, GB9 | 부분(노드전압 복원·vsb 게이트) |
| DEC-49 | 새 metric의 상한 제약은 사이징 대상 회로에서 먼저 잰 뒤 정한다 | 2026-09-08 | GB8 | 원칙 |
| DEC-50 | `gain_db >= 54`(현 metric 이름, 7a부터 `gain_ss_db`)는 결함 metric(`gain_stages_sum`) 기준값이다. 7a 이후 전체회로 gain 기준으로 bisection 재도출한다 | 2026-09-03, 09-14 | 7a | 착수 조건 U-19 |
| DEC-51 | 모든 구현은 plan -> design -> do 순서를 거친다 | 2026-09-10 | 전체 | 원칙 |
| DEC-52 | `vs`는 `vsb`(소스-벌크 역바이어스 크기)이며 옛 키는 로드 거부. 크기는 DEC-61로 노드전압에서 유도한다 | 2026-09-08 | MOD2 | 구현됨 |
| DEC-53 | metric 이름과 단위는 레지스트리로 검증한다 | 2026-09-08 | MOD5 | 구현됨 |
| DEC-54 | 연속 최적화는 SLSQP를 유지한다. 시작점은 S3 아카이브와 준난수 전역 샘플에서 고른다 | 2026-09-14 | GB9 | 부분(multi-start만) |
| DEC-55 | passive connectivity와 노드를 공유하는 `budget_reference_device`는 topology에 선언한다. 파일럿 적용(ratified 대상): CL1/CL2, Cf1/Cf2 교차, Cs1/Cs2, M18b `budget_reference_device` 반영 완료 | 2026-09-10 | GB1 | 구현됨(파일럿) |
| DEC-58 | 블록은 이득 블록과 버퍼 블록으로 나눈다. 블록마다 전압 이득·출력 임피던스(`ss`)·방향별 최대 출력 전류(`ls`, 판정 규칙 DEC-65)를 기록한다. 출력 임피던스 판정은 DEC-66. `driving_spec`(슬루율·부하 전류, 부하 용량은 부하 요소 참조 -- N3.15)이 선언되면 극점 노드마다 방향별 최대 충방전 전류 ≥ 슬루율 × 그 노드의 C_total이고, 부하 전류가 선언되면 출력 포트 노드의 방향별 최대 출력 전류 ≥ 부하 전류다(N3.7 출력 구동 규칙) | 2026-09-15 | GB5, GB6, GB8 | 미구현 |
| DEC-57 | (AC구조) stage는 **전압 이득 stage**다. 모든 트랜지스터를 셀(CS/CG/CD/pass)로 같은 규칙으로 **여기 뷰마다** 분류하고(셀은 신호가 들어오는 단자로 정하므로 같은 트랜지스터가 뷰에 따라 달라진다. 예: 파일럿 M1a/M1b는 차동 전달 뷰에서 CS, CMFB 루프 뷰에서 CG), stage 경계는 셀 입력 노드의 구동 종류로 정한다. 캐스코드(전류 구동 CG)는 별도 stage가 아니다. gain 할당은 gain stage를, 보상(GB5)은 극점 노드 목록(버퍼 출력 포함)을 입력으로 쓴다(극점·보상 문헌은 출력 버퍼를 한 단으로 센다. 기존 4개 회로는 순수 follower가 없어(folded M8은 J10 판정 전까지 미정) 두 수가 같고, `two_stage_ota_sf`는 M8 follower 때문에 다르다). 소자의 DC 역할은 S1에 뷰와 무관하게 따로 기록한다(용어집 '소자 역할') | 2026-09-14 | GB2, N3.2-5 | 미구현 |
| DEC-56 | L5c 픽스처는 `r_cmfb_vocdes`를 하한 0.02로 고정하고 `stop_after_sizing=True`로 돈다(픽스처 입력이지 일반 규칙이 아니다). 이관 뒤 이 입력을 바꾸는 것은 기준 약화(DEC-40) | 2026-09-09~10 | Phase 1 | 구현됨 |
| DEC-59 | 지원 범위는 회로 부류가 아니라 **규칙 분기 발동**으로 정한다. 매 실행 규칙 분기마다 발동 회로 수와 검증 발동 회로 수를 `runs/<run_id>/rule_branch_coverage.json`에 기록한다(library 회로 전체 발동표는 regression 산출물). 검증 발동 회로가 library에 0인 분기를 타는 회로는 탐색 전에 `unsupported_rule_branch`(STRUCTURE_UNRESOLVED, 분기·소자·증거 기록)로 정지한다. 규칙 분기 목록과 발동표는 분기마다 `계산 규칙 있음 / 기록만` 속성을 둔다. `기록만` 분기(계산 규칙 없이 기록·`review_needed`만 정한 분기: 루프 분류 (4), 셀 규칙 밖 (a)(b)(c), 주 신호 분기·합류가 있는 이득 블록 DAG, 보상 규칙으로 풀리지 않는 보상 구성, 전류·트랜스임피던스 전달 뷰, nmos·pmos 밖 kind 등)는 ratify 여부와 무관하게 항상 `unsupported_rule_branch`로 정지한다. 분기를 지원하려면 그 분기의 계산 규칙을 이 계획서 또는 해당 design에 정의하고, 발동 회로를 N9.3 절차로 library에 넣어 ratify한다. 검증 발동 0인 분기가 남아 있는 동안 보고서에 그 분기의 일반성을 주장하지 않는다 | 2026-09-15 | GB0, GB2, N3.14 | 미구현(6a 기록, 6c부터 정지) |
| DEC-60 | 레일은 두 선언으로 정한다(넷 이름 집합으로 판정하지 않는다). 레일 **넷** = topology 선택 필드 `supply_nets`(넷 이름 목록, connectivity라 사용자가 쓴다, WP-07·U-16). 레일 **전압**(DC) = 사이징 스펙의 사람 선언 `supplies_v{넷: 전압}`(7b 전에는 `SPECS[circuit]` 항목, 7b부터 `sizing_spec.json` human). `supply_nets`가 없는 기존 4개 회로는 전환기 해석으로 현 코드 이름 집합(sizing_recipe `_DEFAULT_RAIL_HI`/`_DEFAULT_RAIL_LO` = vdd·VDD / gnd·GND·vss·VSS, stick_diagram `_RAIL_NETS` = vdd·gnd·vss)을 쓴다(DF-26). MG1(Phase 4) 전까지만 전환기 해석을 쓴다: `supplies_v`가 없으면 레일 둘, 가장 높은 레일 = spec `vdd`, 가장 낮은 레일 = 0 V. MG1부터 모든 사이징 대상 회로는 `supplies_v`가 필수이고 스칼라 `vdd` 폴백은 MG1과 함께 삭제한다(가장 높은 레일 전압은 `supplies_v`에서 유도하는 함수 하나). spec 넷 키 집합은 topology `supply_nets`와 같아야 하고 로드 게이트가 강제한다. `supply_nets`는 기존 4개 회로 밖의 회로에서 필수이고, `supplies_v`는 레일 넷이 셋 이상이거나(예: agnd) 음전위 레일을 쓰는 회로에서는 MG1 전에도 필수다(로드 게이트가 없는 Phase 4 전 실행 spec은 원점 이동한 스칼라 `vdd`를 허용한다). nmcnr은 sky130 재설계 전원 `supplies_v{vdd: 0.9, vss: −0.9}`를 선언한다(사용자 확정 2026-09-15, U-26). 스칼라 `vdd`만 받는 현 실행 spec은 폭 1.8 V(`vdd: 1.8`)로 원점 이동 동등이며 IC11이 보장한다. 분할 레일 실행은 이 결정의 구현 뒤다. 레일이 셋 이상인 회로의 공급전류는 레일별로 기록하고, 제약은 선언된 레일 기준으로 건다. 없으면 GB0 로드 게이트가 거부한다. 선언 확정은 U-26. 문서 목표 기록(nmcnr `_paper_target_spec`의 레일 필드, 사용자 확정 스펙 `_declared_target_spec.supplies_v`)은 출처일 뿐 레일 정본이 아니다. 코드의 metric 인자 `supply_nets`(sizing_recipe `supply_current`, 공급 전류를 셀 레일 부분집합이라는 다른 뜻)는 Phase 4에서 이름을 비운다(MG1) | 2026-09-15 | GB0, S1, W0 | 미구현(현 코드는 이름 집합, DF-19·DF-26) |
| DEC-61 | netlist 소자는 선택 필드 `bulk`(넷)를 가질 수 있다(connectivity라 사용자만 쓴다, WP-07). 선택 필드이므로 기본 규칙과 다른 벌크 연결이 있는 소자만 선언하면 되고, 없으면 nmos = `supplies_v` 중 가장 낮은 전위 넷, pmos = 가장 높은 전위 넷이다. vsb = abs(V(source) − V(bulk))이며 노드전압(W0 레일 전압 포함)에서 유도한다(레일 0 V 가정 금지). source·drain 접합의 순바이어스는 크기로 덮지 않고 봉인이 거부한다(N3.6 항목 6). nmos·pmos 밖 kind는 `기록만` 규칙 분기로 기록한다(DEC-59) | 2026-09-15 | S1 소자 `b`, W0, W2 | 미구현(DF-24) |
| DEC-62 | 새 토폴로지 추가는 데이터(topology.json connectivity·`ports`·`passive_elements`·`supply_nets`, `sizing_spec.json`(`supplies_v` 포함), `SPECS` 데이터 항목)만으로 끝나야 한다. 회로 이름으로 갈리는 코드(회로별 보상 함수, 회로별 metric, 회로 이름 분기)가 필요해지면 그 사실을 일반 규칙의 결함(DF)으로 등록하고 규칙을 고친다 | 2026-09-15 | N9.3 | 원칙 |
| DEC-63 | (AC구조 + `ss`) follower 묶음: 전압 구동 넷 u(입력 포트 또는 이득 블록 출력노드)에서 CD 셀(gate 입력, source 출력)의 입력→출력 엣지만 따라 도달하는 노드 집합 R(u)를 모은다. gate가 그 뷰의 신호 경로 밖인 pass 셀은 묶음에 넣지 않는다(pass 구간은 J10 예외, 곧 N3.7 입력 기준 규칙이 뒤 이득 블록에 흡수한다. 병렬 셀 입력으로 흡수되지 않는 pass 구간은 `기록만` 규칙 분기다, DEC-59). R(u)에서 더 이상 CD 입력으로 쓰이지 않는 노드가 하나(합류 노드 v)면 버퍼 블록 = {입력 u, 노드 집합 R(u), 출력노드 v}(`계산 규칙 있음`), 둘 이상이면 다출력 버퍼로 `기록만`. 경로에서 CS·CG 셀을 만나면 묶음이 끝나고 그 셀은 N3.2-5로 새 이득 블록을 시작한다. 버퍼 블록과 앞 이득 블록이 공유하는 넷은 u 하나다. 버퍼 블록 속성(이득·출력 임피던스)은 블록 국소 모델이 단자 스탬프로 계산하고 별도 분기를 두지 않는다. 앞 블록의 경계 부하는 다음 블록 국소 모델에서 계산한 입력 넷 어드미턴스다(cgd는 drain 노드, cgs는 source 노드, cgb는 bulk 넷에 스탬프. 팔로워 입력 어드미턴스 cgd + cgb + cgs·(1 − A_buf)가 여기서 나온다, DF-28). 버퍼 블록은 gain 목표를 받지 않지만 내층 DP 단계로 결정한다(블록 gain을 누적 bin에 더하고 비용은 전력. 이득 블록이 없는 회로는 DP 단계가 버퍼 블록뿐이고 gain 제약이 없으면 bin 없이 비용과 MT1 제약으로 탐색). 측정 기대(J12-a ratify 대상): `pushpull_follower_buffer` {vin; A, B, vout; vout}, `sf_pushpull_output_opamp` {Y; N17, N20, vout; vout}, `two_stage_ota_sf` {OUT; vout; vout}, 기존 4개 회로 0 | 2026-09-15 | GB2, GB6, N3.8 | 미구현 |
| DEC-64 | (DC) **게이트-소스 KVL 루프 탐지 규칙 하나**(DEC-15·DEC-27 통합): G_vgs(용어집)의 스패닝 트리 비트리 엣지마다 기본 사이클 하나 = KVL `Σ±VGS = ΔV(고정 노드)`. 분류(모두 `계산 규칙 있음`): (v0) 같은 (gate 넷, source 넷) 평행 엣지 = `equal_vgs`(기존) / (v1) `ports` role이 입력인 넷(외부 원이 DC를 고정하는 넷, 값 선언 여부 무관)을 둘 이상 지나는 사이클 = 포트 차 루프(출력 포트는 고정 노드가 아니라 세지 않는다. ΔV는 입력 DC 선언이 있으면 그 차, 없으면 '입력 DC 동일 가정'으로 기록하고 제약을 만들지 않으며 대칭 매칭과 중복 여부만 대조한다. 예: 파일럿 {M1a, M1b, M4a, M4b}는 입력 포트 Vip·Vim을 지나 v1, `pushpull_follower_buffer`는 입력 포트가 vin 하나라 v2) / (v2) 나머지 = `kvl_branch` **등식**(레일을 지나면 ΔV = 레일 전압차, 아니면 0. 루프 멤버 소자 중 하나의 gm_id가 종속된다(나머지 멤버 gm_id·L·노드전압으로 결정). 종속 소자 선택 우선순위: 해당 회로 J(버퍼 두 회로는 J12-f)의 ratified 선택이 있으면 그것, 없으면 결정론적 이름 정렬 첫 멤버(기본값). 후보는 다른 등식(`equal_vgs`, `gm_id_match_vgs_of`, 다른 `kvl_branch`)에 이미 종속되지 않은 멤버로 한정한다. 예: `sf_pushpull_output_opamp` 루프는 이름 정렬이면 M18, J12-f 후보는 M21/M22. 루프 가지 전류는 θ 전류 변수다(DEC-70) / (VDS-1) drain–source 엣지를 정확히 하나 포함한 사이클 = 그 VDS 노드를 W1/W2로 쓰고 포화 하한(VDsat, DF-25)이 VGS 합의 **부등식**(DEC-27이 사례). VDS 엣지 2개 이상은 스택 창(W4)이라 대상이 아니다. 루프 소속은 DC 역할이 아니라 S1 관계 엣지 `kvl_branch`(domain `dc`)로 기록하고, 멤버의 DC 역할(바이어스 전류원·신호 소자 등)과 AC 역할은 그대로 둔다(DEC-15. 출력 소자는 DC 역할 신호 소자라 DEC-65 σ로 분류된다). 신호 루프 분류(N3.2-2)와 별개이고 루프 뷰를 만들지 않는다. 선언 기반 목록(DEC-15 소자 이름)은 탐지 결과 대조로 바꾼다(DF-23). 측정 기대(J12-c ratify 대상): 파일럿 v2 4(레일 경유)·v1 1, `pushpull_follower_buffer` v2 1 {M1, M2, M3, M4}, `sf_pushpull_output_opamp` v2 1 {M18, M19, M21, M22}, 나머지 0 | 2026-09-15 | GB1, W2, N3.7 DOF | 미구현(파일럿 선언 기반 KVL 상한만 구현) |
| DEC-65 | (`ls`, 구조 판정은 AC구조) 노드 k·방향(충전/방전)별 최대 전류는 그 방향으로 전류를 댈 수 있는 셀(채널 단자가 k에 붙고 반대 단자 경로가 해당 레일로 이어짐)의 **DC 역할**로 나눠 봉인 통과 점에서 계산한다: (β) DC 바이어스 셀(gate가 교류접지) = 봉인점 ID(포화 유지 범위 안) / (σ) 신호 셀 = W·L 고정에서 LUT ID(VGS_max), VGS_max는 gate 노드의 스윙 한계(N3.8)와 k의 반대 방향 한계로 계산, 계산할 수 없으면 '상한 미상' / (κ) 측면 주입 셀(K8) = '상한 미상'. 구조 판정: 출력 포트 두 방향이 모두 σ면 push-pull, 한 방향만 σ면 class-A(측정 기대: `two_stage_ota_sf` vout = class-A, 두 push-pull 버퍼 vout = push-pull, `two_stage_ota` OUT(M6 σ / M7 β)도 같은 규칙, J12-e ratify 대상). class-AB 대 class-B는 출력 가지 정지전류(θ 전류 변수의 봉인점 값) > 0 여부(DC 동작점 값)다. 슬루율이 선언되면 β 방향은 봉인점 ID, σ 방향은 계산값으로 판정하고, '상한 미상' 방향에 슬루 선언이 걸리면 `기록만`(DEC-59 정지) | 2026-09-15 | GB6, GB8 | 미구현 |
| DEC-66 | (`ss`) 출력 임피던스 metric `rout_ss_ohm(port)` = 전체회로 MNA에서 모든 여기원을 교류접지로 두고 출력 포트에 단위 전류를 주입해 얻은 저주파 개루프 전압. 엔진은 임계값을 만들지 않고 spec에 선언된 `rout_ss_ohm` 제약만 판정한다. 블록 테브난 값은 분해값이며 MNA 값과의 잔차를 기록한다(DEC-05와 대칭). 제약으로 쓰려면 `verified_by`가 필요하다(N3.8) | 2026-09-15 | GB8 | 미구현 |
| DEC-67 | **DC/AC 영역 원칙.** 세 영역(용어집 '영역'): DC 동작점 / 소신호 AC(봉인된 DC 점에서 LUT 선형화, 구조만으로 하는 판정은 'AC구조'로 명시하고 connectivity로 한다) / 대신호. 노드전압·전류의 정본은 DC다(DEC-31). `ss`·`ls` 값은 DC 봉인(N3.6)을 통과한 점에서만 계산하고, 봉인 전에 내는 AC 값은 '상한'(INFEASIBLE 판정 전용) 또는 '추정'(시작점)으로 표기하며 판정·보고 값으로 쓰지 않는다. 모든 규칙·관계 엣지(S1 `domain` 필드)·metric·필드·게이트에 영역을 표기한다. 소자 역할은 DC 역할과 뷰별 AC 역할로 이중 기록한다. 입력 노드 구동 종류는 신호 진입 단자로 정한다(용어집). DC와 AC가 서로 기다리는 순환은 명시적 고정점으로만 둔다(DEC-70) | 2026-09-15 | 전체 | 원칙 |
| DEC-68 | **명명 규칙**(JSON·spec·계획 문서 공통, 정본 표 N3.16): 키는 소문자 snake_case(소자·넷 이름 값은 예외) / 사람이 선언하는 수치는 풀어 쓴 단위 접미사 `_v`, `_amp`, `_farad`, `_ohm`, `_hz`, `_deg`, `_db`, `_s`, `_m`(전력은 `_w`). 하네스 탐색 설정·PDK 키에 적용할지는 U-32 / 넷 이름 값은 `_net` / 모음(list·map)은 복수형, 단위는 복수형 뒤(`supplies_v`) / 영역이 모호한 값은 `_dc_v`·`_dc_amp`, AC 여기는 `ac_` 접두사(`ac_excite`), 소신호 metric은 `_ss_`(`gain_ss_db`, `rout_ss_ohm`) / `_` 접두사는 어떤 코드도 읽지 않는 문서 전용, 주석 키는 `_<필드>_comment` 하나 / 소자 목록 `devices`, 극성 어휘 `nmos`·`pmos` / 개념 하나에 이름 하나·저장 위치 하나, 다른 곳은 참조(`value_from_spec`, `value_from_constraint`, 요소 이름)로만 잇는다. metric 이름의 표시 단위 접두(`_ua`, `_mv`, `_um2`, `_pct`)는 기존 레지스트리대로 허용한다 | 2026-09-15 | GB0, MOD2, N3.15 | 원칙(적용은 DEC-69) |
| DEC-69 | **스키마 이름 마이그레이션 MG0~MG3**(N3.16): MG0 즉시(계획 문서 명칭, `_TEMPLATE` 옛 안내, topology 문서 필드 이름) / MG1 Phase 4(레일 코드) / MG2 6a 착수 전(`_` 접두사 정리, `nfet`/`pfet` → `nmos`/`pmos`, `names` → `devices`, 여기·감지 선언 모양, `ports.direction` 삭제) / MG3 7b `sizing_spec.json` 이관과 함께(나머지 spec 값 이름·요소 값). 각 단계는 옛 키 거부 로드 게이트를 같은 변경 단위에 넣고(선례 `validate_no_legacy_vs_key`, '실제로 거부한다'를 먼저 확인), 이름 변경 코드는 code-author, 옛 키 거부 red test·equivalence 비교는 test-author가 쓴다(픽스처 키 갱신은 test-author 커밋, 값은 바꾸지 않는다). 이름만 바꾼 변경은 사이징 대상 회로의 θ*·metric·instance.json 수치가 키 매핑 후 같아야 한다(다르면 동작 변경). 보상 함수 인자 이름은 7b에서 시그니처를 바꾸고 매핑표를 두지 않는다 | 2026-09-15 | Phase 4, 6a, 7b | 미구현 |
| DEC-70 | **AC·대신호 → DC 되먹임 규칙.** AC·대신호 결과는 DC 값을 직접 덮어쓰지 않고 결정변수 θ(셀별 gm_id, L 동치류 L, 결합변수 y(전류 분할 포함), W4 자유 노드전압, θ 전류 변수(아래 정의), DC 전류 경로에 있는 값 미선언 저항 값)의 **제약**으로만 되돌아간다: 보상 `gm_i(θ) ≥ gm_req(C(θ))`, 슬루 `방향별 최대 전류(θ) ≥ 슬루율 × C_k,total(θ)`, 기생 극점 `parasitic_pm_ss_deg(θ) ≥ pm_target_deg`(LR6). 셋 다 봉인 스냅샷마다 계산하는 부등식이며, 위반 후보는 버리고(margin 기록) 할당기(내층 DP / 중층 좌표강하 / 외층)가 다음 후보로 간다. 내층 DP는 목적값 순 상위 k개 해를 내고(k는 DEC-34 예산에서 계산), 커널 판정에서 위반한 해는 margin과 함께 빼고 다음 순위를 평가한다. 전부 위반하면 위반 제약을 DP 비용 bin에 추가해 한 번 다시 푼다. 판정은 봉인 스냅샷의 S2 `ss`·`ls` 필드(gm, gds, cgg, 노드 C_total, σ 방향 전류, 스윙 한계)를 읽는다. `ls` 필드는 봉인 통과 직후 한 번 LUT로 계산해 저장하고, 제약 판정과 metric은 LUT를 다시 조회하지 않으며 같은 스냅샷 값을 공유한다. **전류 변수 정의**: θ의 전류 변수 = S1 KCL 그래프에서 KCL·전류 강제 관계(미러 비율 `matching_ratio`, 값이 선언된 이상 전류원)로 정해지지 않는 가지 전류의 독립 기저(결정론적 이름 정렬). 결합변수 y의 전류 분할과 값 미선언 이상 전류원은 이 기저의 부분집합이며 중복 계수하지 않는다. 바이어스 게이트 전압으로 전류가 정해지는 가지(예: `pushpull_follower_buffer` M5/M6, `two_stage_ota` tail)도 이 기저에 포함된다. gm/ID 매개화에서 VGS = f(gm_id, L, VDS, VSB)는 ID를 포함하지 않으므로 게이트-소스 KVL 루프 등식(DEC-64)은 전류를 정하지 못하고 멤버 gm_id 하나를 종속시킨다. 따라서 반복은 (a) DC 순환 블록(N3.6 수렴·상한) (b) 탐색 층의 종료 규칙(N3.7) 두 곳뿐이다. **보상 수동소자 값**: 보상망이 유도하는 수동소자 중 DC 전류 경로에 없는 것(커패시터, 커패시터와 직렬인 저항)은 DC 동작점을 바꾸지 않으므로 봉인 스냅샷에서 계산하는 `ss` 파생값이며 반복이 없다. DC 전류 경로에 있는 값 미선언 저항은 θ에 포함한다. 판정은 한 규칙이다: DC 전도 그래프(엣지 = MOS 채널(drain–source), 저항, 이상원. 게이트와 커패시터는 엣지가 아니다)에서, 레일·포트가 아닌 노드 중 DC 엣지가 저항 하나뿐인 노드와 그 저항을 반복해서 잘라낸다(잎 가지치기). 잘려 나간 저항은 DC 전류가 흐르지 않으므로 봉인 스냅샷 파생값이고, 남은 값 미선언 저항은 θ다. 이 판정은 보상망 여부와 무관하게 값이 선언되지 않은 저항에 적용한다. 적용 예: 파일럿 Rz1·Rz2(N_cc_rz1 등의 DC 엣지가 Rz 하나뿐이라 잘림) = 파생값, 커패시터에서 이어진 직렬 저항 사슬 = 차례로 잘려 파생값, `sf_pushpull_output_opamp` R1a~R1c(자기바이어스) = θ, 파일럿 R1/R2(Voc의 DC 엣지가 R1·R2 둘) = θ(기본안: 대칭 DC점에서 전류 0이지만 구조상 DC 경로. 처리는 J ratify 대상) | 2026-09-15 | GB5, GB6, N3.5 | 미구현 |

### N2.2 작업 방식 원칙

모든 역할과 오케스트레이터에 적용한다.

| ID | 원칙 |
|---|---|
| WP-01 | 만들면 반드시 배선한다. 배선할 수 없으면 사용자 승인을 받는다 |
| WP-02 | skip·continue·예외 목록·광범위 except를 만들기 전에 (1) 대상이 실재하나 (2) 검사가 틀렸나 대상이 틀렸나 (3) 우회 없이 고칠 수 있나를 답한다. 게이트는 "통과"보다 "실제로 거부한다"를 먼저 확인한다 |
| WP-03 | 상수를 임의로 만들지 않는다. 근거 선언값 하나만 두고 식을 코드로 계산해 캐시한다. 유도를 주석에 적고 결과 숫자를 박는 것은 해결이 아니다 |
| WP-04 | 논문 값을 인용하지 않는다. 사용자가 직접 지정한 값만 확정값이다 |
| WP-05 | 해결책은 일반화한다(회로·소자·theta 이름과 매직넘버 금지). library 회로에서 측정해(대상 구분 DEC-47) 필요 없는 회로의 무동작을 증명한다. 무동작 증명은 발동 0인 분기의 정답을 보이지 않으므로 분기 검증은 검증 발동 회로로 한다(DEC-59) |
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
| **GB0 spec** | 사람 선언을 읽고 검증한다: objective, 제약값(출처 필수, 논문 출처 거부), `ports`, `value_dc_amp`, 보상 목표(`gbw_target_hz`/`pm_target_deg`, 부하 용량은 부하 요소 참조), `driving_spec`, `gain_budget_db_override`, W3 노드전압 목표, `supplies_v`. 로드 게이트: 옛 키(`vs`, DEC-69 단계별 옛 이름), 단위, 영역 표기, theta 선언 순서, `value_dc_amp`와 같은 소스를 움직이는 theta 공존, `supply_nets`·`supplies_v` 선언 또는 전환기·기본 해석(DEC-60: 기존 4개 회로 밖 회로는 `supply_nets` 필수, 레일 셋 이상·음전위 레일이면 `supplies_v` 필수, `supplies_v` 넷 키 = `supply_nets`), library 규칙 분기 발동표 로드(DEC-59) | 검증된 spec + S0 지문 | MOD2, MOD3 | 6a(의미·게이트), 7b(`sizing_spec.json` 파일) |
| **GB1 구조 유도** | 레일(`supply_nets`·`supplies_v`)·소자 bulk(DEC-60·61), 소자 DC 역할(용어집), 교류접지 집합, diode, 미러 그룹, diffpair·tail(DC 역할), L 동치류(주인 = DEC-17), vertical stack, G_vgs 사이클(DEC-64), 관계 엣지(영역 표기)를 레지스트리 정본 함수로 유도 | S1 | MOD3 | 6a |
| **GB2 stage 분할** | SP1(N3.2)로 signal stage와 피드백 엣지·극성을 유도하고 declared stage와 대조한다. 불일치는 `review_needed`. 규칙 분기 발동을 기록하고 검증 발동 0 분기는 `unsupported_rule_branch`(6c부터 정지, DEC-59). 7b부터 루프 뷰가 생긴 회로에서 루프 안정도 제약이 선언되지 않으면 GB2 출구 게이트가 STRUCTURE_UNRESOLVED(`undeclared_loop_constraint`)로 탐색 전 정지(U-24) | S1v | MOD3 | 6a |
| **GB3 결합 블록** | 블록 = signal stage. 블록 경계를 넘는 관계 엣지에서 결합변수 y(K1~K4)를 추출 | S1 | MOD3 | 6c |
| **GB4 달성가능성·DOF** | LUT 곡선 검사, 블록별 gain 상한 표(AC 상한: 봉인 불필요, 격자 전 범위라 보수적. INFEASIBLE 판정에만 쓰고 실제 판정은 봉인 후보에서만 한다), 구조 DOF와 수치 rank. 불가하면 탐색 전에 정지 | S2 memo | MOD4 | 6c |
| **GB5 보상** | spec에서 목표(GBW·PM·부하 용량)를 읽고, 봉인 후보마다 gm 요구량·보상 수동소자 값·기생 pole L 상한을 θ의 제약으로 판정한다(DEC-70, 7b부터. 6b~7a는 N3.5 전환기 경로) | S2 | MOD4 | 7b |
| **GB6 gain 할당** | 3층: 블록 DP / y 좌표강하 / SLSQP 미세조정. `gain_budget_db` 출력 | S2, S3 | MOD6 | 7b |
| **GB7 DC 해석** | 노드전압 정본, writer 티어 W0~W4, 순환 블록 고정점, 봉인 | S2 | MOD4 | 6b |
| **GB8 metric** | 전체회로 MNA gain, 블록 gain과 잔차, 감도 게이트, metric 티어 분류, 전력·면적 | S2 | MOD5 | 7a |
| **GB9 전역 탐색·검증** | 실패 캐시, 시작점 선택, 준난수 전역 샘플, 아카이브, SPICE 독립 검증 | S3 | MOD6, MOD5 | 5(캐시·θ*), 7c(나머지) |

**실행 구조**: GB0~GB4는 S0 지문마다 한 번 돈다(GB4 값은 봉인 없는 AC 상한). spec에서 정해지는 것은 보상 목표(GBW·PM·부하 용량)뿐이고, gm 요구량·슬루·기생 pole 제약(GB5)은 봉인 후보마다 계산한다(DEC-70). GB6의 각 층이 후보 하나를 평가할 때마다 평가 커널(N3.5)이 **GB7(DC 고정점) -> 봉인 -> GB5 제약 판정 -> GB8(metric)**을 실행한다(7b부터. 6b~7a는 N3.5 전환기 경로). 봉인 전에 계산한 AC 값은 상한·추정으로만 쓴다(DEC-67). 즉 표의 순서는 논리 의존이고 실행은 중첩이다. gm_id·L 선택(GB6)과 노드전압(GB7)은 한 평가 안에서 같은 순환 블록으로 함께 수렴한다.

**막으려는 실패**(원자료 `review_D_gain_decomposition_incidents.md`)

| ID | 근본 원인 | 막는 단계 |
|---|---|---|
| RC1 | stage gain을 소자 이름 목록으로 정의(부하·캐스코드·경계를 사람이 선언) | GB2, GB8 |
| RC2 | KVL/KCL 확인 없이 metric을 계산하고 기준선으로 고정 | GB7 봉인 |
| RC3 | 목표·배분·파생값의 출처 미기록 | GB0 출처 필수, GB4 |
| RC4 | 독립 참조 없이 정식화를 확정(정의상 참인 검증) | GB8 감도 게이트, GB9 SPICE, V2~V4 |
| RC5 | gain과 같은 자유도를 쓰는 결정을 국소적으로 따로 함 | GB3, GB6 |

### N3.2 stage 분할 규칙 SP1

1. **교류접지 집합**: (1) 레일(`supply_nets` 선언 넷, DEC-60) (2) gate에만 붙고 구동되지 않는 넷 -- 입력 포트·수동소자 단자·이상원 단자는 제외 (3) 이상 전압원 단자. J1의 결론(replica bias 예외)은 두 곳에 반영한다: AC구조(이 집합의 예외 목록, 루프 부호) / DC(바이어스 SCC를 GB7 순환 블록으로 등록, N3.6 고정점).
2. **여기 뷰 수집**:
   * **전달 뷰**: metrics 선언의 `(ac_excite, sense)`마다 하나(분자·분모 여기는 각각 하나). 선언된 여기원 밖의 독립원은 교류접지다. **기본 전달 뷰**: metric `(ac_excite, sense)` 선언이 없는 회로(스펙 미선언 library 회로)와 metric에 모드 선언이 없는 경우는 `ports`의 input·output 역할에서 여기를 정한다 -- 입력 포트가 둘이고 `find_structural_symmetry_candidates`가 두 포트를 대응으로 확인하면 기모드 여기 하나, 아니면 입력 포트마다 단일 여기 하나, 감지는 output 포트. metric 선언이 없는 회로의 기본 전달 뷰는 6a 구조 유도(셀·stage·극점 노드·루프 탐지·규칙 분기 발동표)에만 쓰고, 사이징 제약 판정과 gain 할당은 metric 선언(U-25) 뒤에만 한다. 전달 뷰의 여기·감지는 전압이다(전류 입력·트랜스임피던스 전달 뷰는 `기록만` 규칙 분기, DEC-59). gain 할당은 gain 제약 metric이 선언한 전달 뷰의 stage를 쓴다.
   * **루프 뷰**: (AC구조) 이 분류는 AC 되먹임 루프만 대상으로 한다. 게이트-소스 KVL 사이클(G_vgs, DEC-64)과 바이어스 SCC는 **DC 루프**다: S1에서 탐지해 GB7 순환 블록·등식으로 풀고 루프 뷰를 만들지 않는다. 자기바이어스 캐스코드처럼 DC 바이어스를 정하면서 신호 경로 밖에 있는 국소 루프는 DC 루프로도 등록한다(AC에서는 블록 국소 모델이 스탬프할 뿐 보상 변수가 아니다). 루프 탐지는 뷰마다 교류접지 집합과 그 뷰의 이상 여기원이 구동하는 넷(여기 포트)을 제거한 신호 그래프에서 하고, 방향 엣지(gate->drain, gate->source, 그리고 source 노드가 전류 구동 노드(용어집 '입력 노드 구동 종류')인 소자의 source->drain)와 수동소자 엣지만 쓴다. source->drain 엣지는 그 뷰의 셀 분류와 무관하게 노드 구동 종류로 둔다 -- 차동 전달 뷰에서 CS인 파일럿 M1a/M1b도 전류 구동 노드 Vx에서 drain으로 가는 엣지를 가져 CMFB 루프가 빠지지 않는다. 제거한 넷은 그 뷰에서 고정이므로 그 넷을 지나는 경로는 루프로 세지 않고, 그 넷과 신호 노드 사이의 수동소자는 양 끝 부하로 블록 국소 모델·MNA에 스탬프한다(예: 파일럿 Cf1[Vom, Vip]·Cf2[Vop, Vim]는 전달 뷰에서 출력노드–여기 포트 사이 부하). gate가 그 뷰의 신호 경로 밖인 pass 셀(floating battery 등)은 같은 두 노드 사이의 pass 묶음 하나로 합쳐 2단자 신호 경로로 둔다. 폐경로는 묶음을 한 방향으로 한 번 통과할 수 있고, 같은 묶음 안의 왕복(역병렬 쌍 내부 순환)만 폐경로에서 뺀다. 이 그래프의 기본 폐경로를 모두 모아 아래 순서로 분류하고, 앞 번호에 해당하면 뒤 번호는 보지 않는다((2)는 (4)보다 먼저 판정한다). (0) 한 소자 안에서 닫히는 자기 엣지(diode 연결의 gate = drain 등)는 폐경로가 아니다. (1) 교류접지·여기 포트를 지나는 경로는 위에서 제거했으므로 루프가 아니다. (2) **Miller형**: 커패시터를 포함한 수동소자만으로 이루어진 복귀 경로가 같은 뷰의 순방향 경로 위 노드(블록 출력노드 또는 내부 노드)로 돌아오는 루프 = 보상 루프로 GB5가 다룬다(`계산 규칙 있음`, 루프 뷰를 만들지 않는다. 예: 파일럿 Cc1–Rz1, `two_stage_ota_sf` Cc, nmcnr 중첩 Miller). 능동 셀 하나와 저항으로 닫히고 그 루프가 신호 경로 밖 바이어스 노드끼리만 잇는 국소 루프(자기바이어스 캐스코드, 예: `sf_pushpull_output_opamp` R1a/R1b/R1c)만 블록 국소 모델이 스탬프하는 국소 되먹임이다(`계산 규칙 있음`, 보상 변수 아님, J12 ratify). 신호 경로 노드를 잇는 저항 shunt 되먹임은 (4)다. 능동 셀 둘로 닫히고 수동소자가 없는 복합 diode 경로(`sf_pushpull_output_opamp` M6/M5, M7/M8, M13/M14)가 (2)~(4) 중 어디에 드는지는 J12-h에서 판정한다. (3) **어느 전달 뷰의 순방향 경로에도 없는 능동 셀을 하나 이상 포함하는 루프** = 루프 뷰 하나(`계산 규칙 있음`, 예: 공통모드 되먹임). (4) 나머지 -- 여기 포트가 아닌 노드로 수동소자를 거쳐 돌아오는 전역 되먹임(분압점·저항 되먹임 노드)과 순방향 능동 셀만으로 닫힌 루프(교차결합) -- 만 `기록만` 규칙 분기로 기록하고 `review_needed`(항상 DEC-59 정지). 전달 뷰 신호 경로의 노드를 하나도 지나지 않는 루프(바이어스·레플리카 되먹임)는 루프 뷰를 만들지 않고 바이어스 SCC로 기록한다(J1). 루프 뷰에서 외부 여기원은 모두 교류접지다. **끊는 점** = 루프에만 속한 CS 셀의 gate(임피던스가 무한대에 가까워 끊어도 부하가 바뀌지 않는다. 끊은 gate의 Cgg는 앞쪽 노드 부하로 남긴다). 후보가 여럿이면 복귀 경로 다음 첫 gate, 후보가 없으면 `review_needed`. 극성은 규칙 7로 확인한다. 루프 목록과 끊는 점은 회로마다 J11에서 ratify한다.
3. **셀 분류와 뷰 구성**(뷰마다 적용한다):
   * **셀 우선순위**: gate가 신호를 받으면 CS(출력 drain) 또는 CD(출력 source)다. 이때 source 쪽 신호는 소스 저항(degeneration)이지 입력이 아니다. CS·CD 판정 기준: drain이 그 뷰의 교류접지면 CD(출력 source), source가 교류접지면 CS(출력 drain), 둘 다 아니면 source 노드가 다른 신호 셀의 입력 단자나 출력 포트에 닿을 때 CD·CS 이중 출력으로 `review_needed`(`기록만`), 닿지 않으면 CS(degeneration). CG·pass 공통으로 gate가 그 뷰의 신호 경로 밖(교류접지 집합은 그 부분집합)이면 신호를 받지 않는 gate다. 신호 경로 도달성은 J1 예외를 적용한 뒤 source→drain 엣지를 모두 넣은 초집합 방향 그래프로 한 번 계산하고 그 다음 셀을 분류한다. gate가 신호 경로 밖이고 source로 신호가 들어와 drain으로 나가면 CG, gate가 그 뷰의 신호 경로 밖(뷰 입력에서 도달하지 않는 넷, 바이어스·diode 구동 넷 포함)이고 source↔drain으로 신호가 지나면 pass다(예: 파일럿 M9a/M9b·M18a/M18b). 이 우선순위 때문에 입력쌍 공통 소스를 거치는 gate->source->drain 우회로(한쪽 입력 소자에서 다른 쪽 입력 소자로 CG처럼 건너가는 경로)는 상대 소자 gate도 신호를 받는 뷰에서는 생기지 않는다.
   * **대칭 축약**(용어집): 대칭 회로에서 여기가 순수 기모드 또는 우모드인 전달 뷰는 반회로로 줄여 계산할 수 있다. 대칭 대응은 `find_structural_symmetry_candidates`로 짓고, 대응이 없는 소자는 축약 뷰에서 빼고 목록으로 보고한다. 단일출력 회로는 출력-대응 쌍을 제거한다. 축약은 계산 수단이므로 비축약 전체 뷰와 stage·셀 결과가 같아야 한다(규칙 8에서 측정).
   * **load**(AC 역할) = 그 뷰의 출력노드(또는 블록 노드)에 단자가 붙었으나 그 뷰의 신호 경로 셀이 아닌 소자·수동소자. 신호를 싣지 않는 DC 역할 소자(바이어스 전류원·diode 기준)의 단자는 여기로만 센다. 블록 속성의 출력 임피던스에 넣는다(규칙 6의 load는 이 정의다).
   * 예시(규칙이 아니라 파일럿 잠정 판독, J11에서 ratify): 차동 전달 뷰에서 M1a/M1b·M4a/M4b는 CS, M2a/M2b·M3a/M3b는 캐스코드다. CMFB 루프 뷰(끊는 점 후보 M37a gate)에서는 M37a CS -> diode 연결 노드 `Vcmfb` -> 미러 M7 -> M7 drain 전류가 `Vx`로 흘러듦 -> M1a/M1b CG(gate 교류접지) -> M2a/M2b 캐스코드 -> `Vom1`/`Vop1` -> M16/M26 CS -> Vom/Vop -> R1/R2 -> `Voc`이고, `Vy`에는 루프 신호가 들어가지 않아 nmos 반쪽(M4a/M4b, M3a/M3b)은 `Vom1`/`Vop1`의 load다. M58 전류 분할은 J1과 함께 판정한다.
4. **엣지와 비용**: gate->drain 비용 1, source->drain(캐스코드)·gate->source 비용 0, gate 넷이 diode 연결 단자(AC 1/gm 노드)인 소자의 gate->drain 비용 0(미러, AC구조). 수동소자 엣지 비용은 6a design이 정한다(측면 주입·주 신호 분기 판정(N3.7)은 이 비용에 의존하지 않는다). 예외: source 노드가 전압 구동인 CG의 source->drain은 비용 1(규칙 5). 입력 넷에서 0-1 BFS 최소 비용이 stage 번호다. 뷰의 입력(전달 뷰는 여기 포트, 루프 뷰는 끊는 점)에서 출발한다. 기존 4개 회로 실측 규칙은 기모드 축약 뷰에서 잰 R3(DM/R2)이다(원자료 `probe_stage_partition.result.md`): 축약 뷰에서는 입력쌍 공통 소스가 가상접지라 gate->source 우회로가 끊긴다. 축약 없이 같은 비용만 쓰면 우회로 때문에 입력단 stage 번호가 0으로 떨어졌다. 비축약 뷰에서는 규칙 3의 셀 우선순위가 이 우회로를 막는다 -- 셀 우선순위 적용 후에도 R3 결과(기존 4개 회로 100% 일치)가 유지되는지는 아직 측정하지 않았고 규칙 8에서 측정한다.
5. **셀과 stage 경계**(AC구조, 뷰별): 각 여기 뷰의 신호 경로에서 모든 트랜지스터를 셀(CS/CG/CD/pass)로 분류하고(규칙 3), 셀마다 입력 노드의 구동 종류(전압/전류)를 기록한다. stage 경계는 단자 이름이 아니라 **입력 노드 구동 종류 하나로** 정한다.
   * 전압 구동 입력을 받아 전류를 고임피던스 노드로 내보내는 셀(CS, source가 전압 구동인 CG) = **새 gain stage 시작**(번호 +1).
   * 전류 구동 입력을 받는 CG = 캐스코드. **같은 stage를 잇는다**(앞 셀의 출력저항을 키우는 전류 버퍼다. 같은 stage는 gain을 평가하는 단위일 뿐이고, 캐스코드의 gm_id·L은 등식 관계를 제외하면 입력 소자와 독립 결정변수다 -- DEC-04).
   * 전압 구동 입력을 받아 저임피던스 노드로 내보내는 셀(CD. pass는 DEC-63 예외 규칙) = 전압 버퍼. gain stage 번호는 올리지 않고 버퍼 구간으로 표시한다(독립 블록 여부는 J10). 버퍼 출력노드는 극점 노드 목록에 넣는다(규칙 6) -- gain 기준으로는 stage가 아니지만 극점·보상 기준으로는 한 단이다. CD 사슬과 상보 CD 합류는 DEC-63 묶음 절차로 한 버퍼 블록이 되고, 버퍼 블록 입력 넷은 앞 이득 블록 출력노드와 공유하는 유일한 넷이다.
   * 근거: 캐스코드를 별도 stage로 나누면 그 stage의 전압 이득(source 노드 -> drain)과 앞 stage의 이득(≈ −1)이 같은 전류와 같은 출력저항을 공유해 분리성이 깨지고(결합 블록 DP 성립 조건, N3.7), 보상 레지스트리의 stage 수(`compensation.stage_devices`)와도 어긋난다. 캐스코드를 입력과 같은 stage에 두는 이유는 결정을 묶기 위해서가 아니라, 출력노드 저항이 캐스코드로 정해져 블록 gain을 계산하는 단위가 같기 때문이다. 기존 4개 회로 실측: CG 셀 8개(파일럿 M9a/M9b/M18a/M18b, folded M5/M6, nmcnr M106/M107)가 **모두 전류 구동**이고 source가 전압 구동인 CG는 없다(전압 구동 CG stage 시작 분기는 검증 발동 0, DEC-59). 파일럿 선언 `gain_stages_sum`은 캐스코드 M2a/M3a를 입력 M1a/M4a와 같은 stage에 둔다(원자료 `probe_cg_cascode_stage.result.md`). 따라서 이 규칙은 기존 4개 회로에서 실측 규칙 R3(DM/R2)과 같은 결과를 내고, CG 증폭기·follower도 같은 기준으로 분류하지만 그 분기의 검증은 검증 발동 회로로 한다. 외부 기준과의 대조(원자료 `docs/03-analysis/gain-budget-gmid-sizing-function-audit/review3_stage_partition_literature.md`): 캐스코드를 입력과 같은 단으로 두는 것(telescopic·folded를 one-stage로 분류, 기능블록 분해에서 캐스코드는 load에 흡수)과 diode 미러를 같은 단에 두는 것은 문헌과 일치한다. 입력 노드 구동 종류로 경계를 정하는 것은 기능블록 분해의 "게이트 전압을 전류로 바꾸는 소자가 단의 시작"과 같은 개념이다. 여기 뷰·엣지 비용은 이 분류의 구현이며 근거는 기존 4개 회로 실측이다.
6. **stage 구성**: 출력노드 = stage 안에서 신호가 마지막으로 도달해 다음 stage 시작 셀의 입력 단자 또는 출력 포트로 넘어가는 노드. CS·CG 사슬로 끝나면 drain 노드, CD·pass로 끝나면 그 소자의 출력 단자 노드다. 임피던스 등급을 뷰별 노드 속성으로 구조로 기록한다(AC구조): 낮음 = gm 차수 컨덕턴스를 주는 단자(gate가 그 뷰에서 교류접지인 source 단자, diode 연결 소자의 drain+gate)가 붙음 / 높음 = 그 외(drain·gate·커패시터 단자만) / 값 의존 = 낮음 단자 없이 저항이 붙음(구조 판정에는 J12 ratified 값을 쓰고 GB8은 일관성 검사만 한다, 용어집 '입력 노드 구동 종류'). input = stage 시작 셀의 신호 입력 단자(CS·CD는 gate, CG는 source)가 stage 입력 넷에 붙은 소자, cascode = CG 사슬, follower = CD, pass = pass 구성 소자, load = 규칙 3의 load, tail = DC 역할이 바이어스 전류원이고 그 뷰에서 둘 이상 셀의 공통 source 노드에 drain이 붙은 소자(없으면 빈 역할. DEC-17이 쓰는 tail은 뷰 무관 DC 정의). **블록 노드 집합** = stage 입력 넷부터 출력노드까지 신호 경로 노드 ∪ 블록 셀 단자 노드 중 교류접지 집합이 아닌 노드(source degeneration 노드 포함). **극점 노드 목록** = 용어집 정의(그 여기 뷰의 교류접지 아닌 노드 전부, 속성 기록). GB5·출력 구동 규칙·`parasitic_pm_ss_deg`는 이 목록을 소비하고, gain 할당(GB6)은 gain 제약 metric이 선언한 전달 뷰의 gain stage를 소비한다. 극점 노드 목록은 여기 뷰마다 따로 만든다(루프 뷰의 안정도는 그 루프 뷰의 목록, U-24).
7. **피드백**: 뷰 입력에서의 BFS 거리(DEC-29) 기준으로 역방향 엣지(MOS·수동소자)를 피드백으로 분리한다. 극성 = 끊는 점에서 한 바퀴 도는 경로의 저주파 부호이며 셀·소자 부호의 곱으로 구조로 계산한다(CS 반전, CG·CD·pass 비반전, 저항·분압 비반전). 커패시터만 거쳐 저주파 경로가 없거나 부호가 섞이면 `review_needed`(Cc–Rz 직렬 루프는 J7).
8. **검증 기준**(구동 종류 판정은 규칙 1의 교류접지 집합이 먼저 확정돼야 한다 -- 교류접지 없이 BFS하면 레플리카 바이어스 경로 때문에 파일럿 M2a/M3a가 CG로 잡히지 않는다, J1): 정답 기준은 J 공동분석으로 `ratified`된 대조표(stage 멤버십, 출력노드, load·G_out 기여 소자, 셀 판독)다. declared stage는 불일치 보고용 입력이다 -- 기존 4개 회로에서는 input·cascode·tail 멤버십이 declared와 일치함(실측 100%, 원자료 `probe_stage_partition.result.md`)을 회귀로 유지하고, declared가 없는 신규 회로는 ratified 대조표만 쓴다. declared stage에 없는 부하(파일럿 Vom1의 M19·M18a·M18b)는 결함 선언이지 규칙의 오류가 아니다. 기존 4개 회로에는 drain이 레일에 붙은 순수 follower가 없고, source·drain 단자로 신호를 넘기는 소자는 파일럿 class-AB floating battery(M9a/M9b: Vop1↔Vg15, M18a/M18b: Vom1↔Vg25)와 folded M8(gate Vg7, source Vg10)이다(실측 원자료 `probe_common_drain.result.md`, 6a design이 기모드 축약 뷰에서 재측정). 순수 follower는 `two_stage_ota_sf`(M8), `pushpull_follower_buffer`(M1~M4), `sf_pushpull_output_opamp` 버퍼(M18/M19/M21/M22)에 있다(U-22). library 회로 전부에서 측정해 보고한다: (i) 셀 우선순위를 적용한 SP1이 기존 4개 회로의 R3 실측(declared stage 100% 일치)을 유지하는지 (ii) 대칭 회로에서 축약 뷰와 비축약 전체 뷰의 stage·셀 결과가 같은지, 대칭 쌍이 없는 회로(`pushpull_follower_buffer`)에서 비축약 결과가 ratified 대조표와 같은지 (iii) 루프 탐지 결과 -- 루프 뷰가 생긴 루프와 끊는 점(파일럿 CMFB 루프가 규칙 2의 루프 탐지 그래프에서 탐지되는지 포함), 규칙 2의 (0)~(4)·바이어스 SCC 분류, 루프가 없는 회로는 없음을 명시 (iv) 규칙 분기 발동표(DEC-59) (v) CD 셀·버퍼 묶음(DEC-63), G_vgs 사이클 분류(DEC-64), 출력 포트 방향 분류(DEC-65) -- 기존 4개 회로는 CD 0·버퍼 묶음 0이고 `kvl_branch`(v2)·포트 차 루프(v1)는 파일럿에만 나와야 한다.
9. **graph로 정하지 않는 것**: 어느 여기 모드가 스펙인가, class-AB 출력단 정지전류 규칙과 floating battery의 stage 출력노드(J3), follower를 독립 블록으로 둘지 앞 stage에 흡수할지(J10), 자유 노드 배분 기준(GB6 목적함수가 정한다), LUT 비단조 자체(GB4가 해법을 고른다). 셀 규칙 밖의 사례는 분류하지 않고 `review_needed`로 보고한다: (a) 게이트가 전류 구동 노드에 붙은 CS(gain boosting 보조증폭기, regulated cascode 등) (b) 입력 포트가 전류 입력인 CG(포트의 전압/전류 구분은 `ports` 선언, 선언이 없으면 전압) (c) CS로 시작하지만 출력노드 임피던스 등급이 낮은 블록(CS 버퍼, diode 부하 CS). 전압 이득이 1 이하인 이득 블록은 사이징 뒤 값이라 GB2가 아니라 GB8 블록 속성 기록에서 경고한다. (a)(b)(c)는 `기록만` 규칙 분기로 기록한다(항상 DEC-59 정지).

### N3.3 Circuit State Graph 층

| 층 | 내용 | 키·무효화 | 저장 |
|---|---|---|---|
| **S0 지문** | topology 정규화 JSON 해시 / LUT 파일 내용 해시 + 생성 메타(`lut_conditions_from_npz`: corner, temp) / spec 전체 해시(제약값 포함) / 유도 규칙 코드 해시(S1 유도 함수 호출 폐포의 `ast.dump`, docstring·모듈 경로 제외) / metric 정의 코드 해시 | -- | 메모리 |
| **S1 구조** | 노드 {name, terminals[(device, terminal)], is_rail(`supply_nets`, DEC-60), ac_ground_class, port_role} / 소자 {name, kind, d, g, s, b(선언 `bulk` 또는 DEC-61 기본 레일), is_diode, dc_role(용어집 '소자 역할')} / 수동소자 {name, kind, terminals}(topology 이름과 같게) / 관계 엣지 {type, domain, members, status, evidence{rule, nets}}. `domain` ∈ {`dc`, `geom`, `dc→ss`}: `equal_vgs`·`vds_eq_vgs`·`budget_ref`·`stacked_vsb`·`matching_ratio`·`kcl_group`·`kvl_branch` = dc, `same_as`·`l_class` = geom, `matching_offset` = dc→ss. 노드 `is_rail`은 DC, `ac_ground_class`는 AC구조다. 메모리 엣지 type `same_as`·`budget_ref`는 topology·spec 필드 `same_as`·`budget_reference_device`와 이 대응으로만 잇는다(N3.16). type ∈ `equal_vgs`, `vds_eq_vgs`, `same_as`, `budget_ref`, `stacked_vsb`, `matching_offset`, `matching_ratio`, `l_class`, `kcl_group`, `kvl_branch`. 개념마다 정의 하나 | topology 해시(`supply_nets` 포함) + 유도 규칙 해시 + 레일 전압 선언(`supplies_v`) 해시 | 메모리(엔진 유도, 매 실행 재생성) + `library/<name>.structure.json`(ratified 기록만, 오케스트레이터가 씀, 6a) |
| **S1v 여기 뷰** | 모드별: SCC 응축 신호 DAG, 피드백 엣지·극성, 셀(AC 역할), 노드 구동 종류(전압/전류/값 의존), 임피던스 등급, signal stage 목록, 극점 노드 목록 | S1 키 + 모드 | 메모리 |
| **S2 동작점** | 세 부분으로 나눈다(DEC-67). `dc` = 노드 DC 전압(경로별 값·충돌), 소자 op(ID, gm_id, L, W, VGS/VDS/VSB), KCL 전류와 출처, 스택 창·slack(writer 티어 W0~W4, 봉인 대상) / `ss` = gm·gmb·gds·cgg(cgs·cgb 열이 생기면 포함, DF-28), 노드 C_total·G, 소신호 metric(봉인 통과 스냅샷의 파생, 입력 `dc` 버전 카운터 기록) / `ls` = 방향별 최대 전류, 스윙 한계, 슬루 등가 용량(`ls.c_slew_farad`, 극점용 `ss.node_c_farad`와 다른 필드). `ss`·`ls`는 봉인 통과 뒤에만 쓴다. 필드마다 {writer 티어(`dc`) 또는 입력 카운터(`ss`·`ls`), 버전 카운터} | memo 키 = 계산 블록 입력의 내용 해시 | LRU(상한 N3.5) |
| **S2p 사전정보** | 직전 수렴 스냅샷. 초기값·시드로만 쓰고 결과값으로 쓰지 않는다 | 없음(힌트) | 메모리 |
| **S3 탐색 기억** | 평가 기록(θ, ok/fail, 실패 분류·소자·margin, metric, 제약 여유, 분지 id), 실행 기록(θ*, start별 결과), 유도 임계값 | S0 전체 지문 | `library/<name>.search_archive/<S0 지문>/{evals,runs}.jsonl`(append-only, 케이스마다 flush, `.gitignore` 등록). 지문이 다른 디렉터리는 읽지 않는다. Phase 5~6a 전에는 N3.5 임시 지문을 디렉터리 이름으로 쓴다 |

**status 전이**

| 전이 | 누가 | 조건 |
|---|---|---|
| (생성) -> `declared` | 사람 선언을 로드할 때 엔진 | topology/spec에 적힌 사실 |
| (생성) -> `derived` / `proposed` | 엔진 | 규칙과 connectivity 증거가 있으면 derived, 증거가 부족하면 proposed |
| `derived`/`proposed` -> `review_needed` | 엔진 | declared와 불일치, 또는 규칙이 해석 불가를 보고 |
| `review_needed` -> `ratified` | 오케스트레이터 | 공동분석 결론 + 승인 기록 id |
| `ratified` -> `review_needed` | 엔진 | S0의 topology(`supply_nets` 포함)·유도 규칙 해시 변경, 또는 레일 전압 선언(`supplies_v`, spec 지문) 변경 |

shadow 대조 보고와 그 밖의 실행 산출물은 `runs/<run_id>/`(`.gitignore` 등록)에 쓴다. 평가 경로가 읽는 상태는 `declared`, `derived`, `ratified`뿐이다. 6a(shadow)에서는 평가가 기존 declared 경로로 계속 돌고 유도 결과는 대조 보고만 한다. 유도 값을 평가가 소비하기 시작하는 6c부터 `review_needed`가 남아 있으면 GB4 전에 정지한다.

### N3.4 노드전압 writer 티어 W0~W4

모든 티어는 DC 영역이다. AC·대신호 결과는 어떤 티어에도 쓰지 않는다(DEC-70).

| 티어 | 쓰는 대상 | 출처 |
|---|---|---|
| W0 | 레일 노드 | `supply_nets`의 모든 넷. 전압은 사이징 스펙 `supplies_v{넷: 전압}`(미선언이면 DEC-60 전환기·기본 해석). vsb는 이 전압과 bulk 넷에서 유도(DEC-61) |
| W1 | 구조 항등으로 묶인 노드 변수: diode(VGS=VDS), 노드를 공유하는 `budget_ref`, `vds_match_vgs_of`(D1에서 항등식) | S1 관계 엣지 |
| W2 | 물리 종속 블록: 노드전압 ↔ gm_id ↔ W, 적층 diode(`stacked_vsb`), class-AB 배터리 KVL, 신호 CD 셀의 source 노드(`V(s) = V(g) ∓ VGS(gm_id, L, vds = abs(V(d) − V(s)), vsb = DEC-61(V(s)))`, vds·vsb가 V(s)에 종속하는 순환), `kvl_branch` 등식 노드. 두 CD 경로가 같은 합류 노드를 쓰면(push-pull 출력) 합류 노드 전압과 DEC-64 등식 하나를 한 W2 블록으로 함께 푼다(봉인 5 writer 유일). 버퍼 블록 입력 넷의 DC는 앞 이득 블록 출력노드의 writer(W4 또는 W3)가, 입력 포트면 spec의 입력 DC 선언(`input_dc_net` 등)이 쓴다 | 순환 블록 고정점 |
| W3 | 사람이 선언한 노드전압 목표 | `sizing_spec.json` human.`node_voltage_targets_v`(`diode_stack.target_net`, 출력 공통모드 DC 목표 `Voc_des` → `voc_target_dc_v` 계열을 이관, MG3) |
| W4 | 자유 노드 | GB6 중층(결합변수 y)이 창 안에서 배정 |

* 노드 하나에 writer는 하나다. "먼저 쓴 값 존중"은 없다. 두 writer가 같은 노드를 쓰면 봉인 위반이다.
* 소자 vds/vgs/vsb는 노드전압 차이의 읽기 전용 파생이다. `set_device_vds`는 W 티어 setter의 파생으로 바뀐다.
* 노드 하나에 값 하나이므로 "스택 합 ≠ 레일 전압차"는 표현할 수 없다(검사 대상이 아니다). writer 경합과 버전 불일치는 봉인이 거부한다.

### N3.5 상태 계약·평가 커널·최적화 계층

**상태 계약**(강제 test는 `tests/contracts/`, 담당 Phase 6b. SC-e는 7a metric 분류에서 소비)

| ID | 규칙 | 강제 test |
|---|---|---|
| SC-a 단일 writer | S2 `dc` 필드 × writer 티어 권한표(`ss`·`ls` 필드는 writer 티어가 없고 봉인 통과 스냅샷의 파생으로만 쓴다). **전환기 writer(6b~7a 한정)**: 보상 블록 → `dc` 전류·gm_id 필드, 출력에 '봉인 전 추정' 태그, `ss`·`ls`에는 쓰지 않는다. 7b 커널 재배열과 함께 이 권한을 삭제한다. 모든 쓰기는 타입 setter로만. 원시 대입은 grep 게이트로 금지 | 원시 대입 grep 0 + 순서 섞기 불변(IC2) |
| SC-b 버전 있는 유도 | 필드마다 쓰기 카운터. 파생 필드는 입력 카운터를 기록하고, 봉인이 불일치를 거부. 재사용 시 `setdefault`로 기존 값을 건너뛰지 않는다(V6 lint 대상) | 옛 vsb 버전으로 계산된 W를 넣은 픽스처를 봉인이 거부 |
| SC-c 순환 = 명시적 고정점 | 계산 블록 입출력 선언으로 만든 유도 DAG의 SCC를 순환 블록으로 반복. 수렴 판정·반복 상한은 N3.6, 비수렴은 NONCONVERGENT 실패(N3.14) | 수렴 픽스처 + 비수렴 픽스처 거부 |
| SC-d 내용 지문 무효화 | 지문 불일치 = 캐시 없음. 픽스처 spec은 `origin: fixture`와 자기 지문을 선언하고 정본 유도 임계값을 읽지 않는다(U-04) | 지문 변경 시 미적중 |
| SC-e reader 기록 | metric과 계산 블록은 실제로 읽은 S2 필드를 기록한다. metric 티어 분류(N3.8)와 영향 집합이 이 기록을 쓴다 | 선언 support와 실제 read가 다르면 기록이 이긴다 |

**평가 커널**: `_evaluate`를 계산 블록으로 나눈다 -- ② 전류(KCL, `value_dc_amp`) ③ L 유도 ④ 스택·순환 블록(W1/W2 + gm_id pass) ⑤ W 계산 -> **봉인**(N3.6) -> ① 보상·슬루·PM 제약 판정(DEC-70, 봉인 스냅샷 S2 `ss` 필드를 읽고 LUT를 다시 조회하지 않는다) -> ⑥ metric(`ss`·`ls`, ①과 같은 스냅샷 값을 공유). 번호는 옛 순서를 유지한 이름이고 실행 순서는 화살표 순이다. 이 순서는 7b(GB5 θ 제약과 같은 변경 단위)부터 적용한다. 6b~7a는 현 코드 경로(보상 블록이 A엔진·theta보다 먼저 gm을 정한다, `sizing_recipe.py` `_evaluate` 8697행 참고)를 전환기 경로로 두고 그 출력을 '봉인 전 추정'으로 표시한다. 블록마다 입력·출력을 선언하고, 결과는 입력 내용 해시로 S2에 memo한다. 전역 metric은 봉인 스냅샷마다 한 번 계산한다. 조인트 스캔 memo 키는 입력 θ 성분과 그 스캔이 읽는 `dc` 값으로만 짓는다(그룹 L, vds, vsb, 고정 gm_id, 전류를 정하는 θ 성분).

**S2 LRU 상한** = (DEC-34 식의 샘플 수 + 선언 `n_starts` × 평가 계수기로 실측한 SLSQP 1회 평가 수) × 계산 블록 수. 초과분은 LRU로 밀어낸다.

**최적화 계층**

* **실패 캐시**: 키 = (θ 각 성분의 `float.hex`, S0 지문). 실패는 N3.14 구조화 실패로 저장한다. 제약 함수는 상수 페널티 대신 정규화 위반량(margin)을 돌려준다. S0가 없는 Phase 5~6a 전에는 지문 자리에 임시 지문(topology 파일 내용 해시 + spec 전체 해시 + 엔진 소스 파일 해시)을 쓰고, 6a에서 S0로 바꾼다. 임시 지문 레코드는 그 뒤 읽지 않는다(SC-d).
* **시작점**: 지문이 일치하는 S3 feasible 점 상위 `n_starts`개(선언값) -> 부족하면 선언 x0. "지난 해 ± 창"은 추가 시작점으로만 쓴다(전역 bounds를 줄이지 않는다).
* **전역 샘플 수(DEC-34)**: `N = floor((wall_clock_budget_s − T_fixed) / t_eval)`(`wall_clock_budget_s`는 회로별 선언값, DEC-34). `T_fixed` = 같은 실행에서 샘플을 뺀 단계(presolve, GB0~GB5, DP, 좌표강하, SLSQP) 실측 합, `t_eval` = warm 평가 실측 중앙값. 샘플러는 `scipy.stats.qmc.Sobol`(scipy는 이미 의존). 7c 전에는 그 Phase에 존재하는 단계만으로 `T_fixed`를 실측해 같은 식으로 N을 계산하고, 판정 기록에 어느 단계를 넣었는지 적는다(6b LRU 상한, 6c DOF 표본 수가 이 N을 쓴다).
* **분지**: feasible 샘플의 θ 격자 인접 연결성분, 또는 DP 결정 벡터가 다른 해. 서로 다른 분지에서 SLSQP를 시작한다.
* 한 기준점의 수치 섭동으로 차원을 동결하지 않는다. 무효화는 구조적 쓰기 집합(SC-e 영향 집합)으로만 한다.

### N3.6 봉인 게이트와 허용오차(DEC-32)

**봉인 항목**(DC 영역, metric·제약 판정 전, 모든 평가)

| # | 항목 | 판정 |
|---|---|---|
| 1 | 노드 충돌 | 같은 노드에 도달한 경로별 값의 최대 차 ≤ tol_V |
| 2 | VGS 정합 | 모든 소자(diode 포함)에서 노드 차 VGS와 `vgs_for_gm_id(gm_id, L, vds, vsb)`의 차 ≤ tol_V |
| 3 | KCL 잔차 | 내부 노드마다 |ΣI| ≤ tol_I. `exclude_nets`는 사유가 선언된 넷만 |
| 4 | 버전 일치 | 파생 필드의 입력 카운터 = 현재 카운터(정확 일치) |
| 5 | writer 유일 | 노드마다 writer 하나 |
| 6 | 벌크 역바이어스 | 모든 소자에서 source-bulk·drain-bulk 접합이 역바이어스(nmos V(source), V(drain) ≥ V(bulk), pmos V(source), V(drain) ≤ V(bulk)). 위반 크기 > tol_V이면 거부(DEC-61) |
| 7 | 포화 여유 | ID > 0인 모든 MOS에서(뷰 무관) VDS − VDsat(DF-25 유도 규칙) ≥ −tol_V. 위반 크기 > tol_V이면 거부. 선형 영역을 의도한 소자는 topology 소자 선택 필드(기본안 `intended_region: "linear"`, 사용자 작성, 이름은 6b design 확정)로 선언한 것만 제외한다. 이 항목이 있어야 `ss` 선형화 점이 포화점이다 |
| 8 | `kvl_branch` 등식 | DEC-64 v2 등식 잔차(멤버 LUT VGS 합 − ΔV) ≤ 멤버 수 × tol_V. 봉인 1·2가 통과하면 자동 성립하므로, W2 블록이 등식을 풀지 않은 경로(선언 기반 전환기 경로)를 잡는 게이트다 |

**허용오차 식**

* `tol_V` = (kind, L 앵커, VDS)별 LUT leave-one-out 보간 오차(VGS 기준)의 최댓값. 계산 함수는 `tests/probe_interp_scheme_loo.py`의 방법을 MOD1 함수로 승격한다.
* `tol_I` = `tol_V` × 해당 순환 블록 소자 gm의 최댓값. gm은 직전 봉인 스냅샷(S2p)의 `ss` 값을 쓰고, 첫 평가는 LUT 격자 최댓값을 쓴다(봉인 전 gm으로 허용오차가 순환하지 않게).
* 반복 상한: `K_max = ceil(log2(구간폭 / tol_V))`(같은 구간을 bisection으로 풀 때의 반복 수). 고정점 반복도 같은 K_max를 상한으로 한다(그보다 느린 고정점은 bisection보다 나쁘다). 고정점 반복은 매 반복 q = 직전 변화비 `|Δk| / |Δk−1|`(추정에 필요한 최소 반복 3개)를 갱신하고, q < 1이면 수축 오차 한계 `q^(K_max − k)·|Δk| / (1 − q) > tol_V`로 남은 상한 안 도달 불가가 확정될 때, q ≥ 1이면 K_max에 닿을 때 NONCONVERGENT. 창 크기·연속 횟수 상수는 두지 않는다.
* 같은 `tol_V`를 IC1 test의 허용오차와 SPICE 비교(N3.8)의 노드전압 허용오차로 쓴다.

### N3.7 결합 블록·달성가능성·DOF·할당

**결합 종류**

| ID | 결합 | 처리 | 영역 |
|---|---|---|---|
| K1 | 블록 출력노드의 부하 소자가 다른 블록의 미러·L 동치류에 속함 | y | DC(y는 DC 결정변수, 바꾸면 GB7 봉인 필수) |
| K2 | 두 블록 이상에 걸친 `equal_vgs`(공유 VGS. 예: `sf_pushpull_output_opamp` M17~M6, M20~M14) | y | DC |
| K3 | 블록 경계를 넘는 `stacked_vsb` | y | DC |
| K4 | 두 블록이 공유하는 스택의 노드전압 | y(W4) | DC |
| K5 | 다음 블록 입력 넷 어드미턴스(CS는 Cgg, CD는 부트스트랩 포함, DEC-63)가 노드 pole을 거쳐 PM에 영향 | GB5·GB8(`parasitic_pm_ss_deg`) | `ss`(봉인점) |
| K6 | 보상 제약이 요구하는 gm | GB5 제약(DEC-70) | `ss` 제약(DC 값으로 쓰지 않음) |
| K7 | 둘 이상의 여기 뷰가 같은 소자를 쓴다 -- 한 뷰에서 정한 소자 값이 다른 뷰의 제약에 들어간다(예: 파일럿 M7은 차동 전달 뷰에서 M6와 병렬 tail이고 CMFB 루프 뷰에서 구동 소자라 M6·M7 전류 분할이 두 뷰에 함께 걸린다) | y(공유 소자의 분할·값), 뷰별 제약(U-24) | AC구조(뷰 공유) + DC(분할값) |
| K8 | 측면 주입: 셀 c의 **DC 역할이 바이어스 전류원**(KCL·미러·`equal_vgs`로 유도)이고 **AC 역할은 gate로 신호를 받는 CS**이며, c의 drain 노드 k에 신호 CD 셀의 source가 붙어 있고, c의 gate 넷이 그 CD 셀의 입력 넷에서 CD 엣지로 도달하지 않으며, k가 어떤 이득 블록의 출력노드도 아니다(connectivity와 셀 분류만으로 판정. 용어집 혼재 우선 규칙이 이 정의를 인용한다)(N3.7 달성가능성 (b), 예: `sf_pushpull_output_opamp` M17(k = N17)·M20(k = N20), J12-d ratify 대상) | 블록 DP는 사슬 유지, 해당 metric은 MT3(외층 전체회로 MNA) | AC구조(판정) + DC 역할 |

* **결합 잔차 측정(6c 첫 작업)**: 사이징 대상 회로마다 LUT 격자에서 DEC-34 식의 샘플 수만큼 준난수 표본을 뽑고, 표본마다 GB7 봉인을 돌려 통과한 점에서만 블록 gain 합과 전체회로 MNA gain의 차를 잰다(봉인 실패 점 수와 분류는 따로 보고)(파일럿은 기존 6480조합 데이터 `tests/probe_mirror_gain_ranking.py`를 표본에 더할 수 있다). 0이 아닌 블록 쌍은 해당 metric을 MT3로 표시하고, MT 분류는 회로별로 저장한다.
* **LUT 곡선 검사(로드 시)**: 곡선이 단조면 역산 허용, 비단조면 격자 전수만 허용, 단위 불일치면 로드 거부.
* **블록 gain 상한**(AC 상한, 봉인 불필요, 보수적): `A_i,max = max(블록 i의 국소 소신호 모델 gain)` over gm_id 격자 × LUT L 앵커 × W4 창의 VDS × y 가능역. 봉인 가능 점을 모두 포함하는 상위집합 위의 상계이며 INFEASIBLE 판정에만 쓴다. 탐색 전 격자 전수(GB4)로 계산해 행마다 조건(gm, ID, L, VDS)과 함께 S0 지문 memo로 둔다. 7b에서 보상 제약이 요구하는 gm으로 다시 계산할 때는 이 GB4 격자 표에서 gm 조건을 만족하는 행만 거르는 필터로 하고 LUT 격자를 다시 돌지 않는다. 필터로 표현할 수 없는 경우만 재계산하고 그 사유를 기록한다.
* **달성가능성**: 이득 블록 DAG(S1v)가 직렬 사슬이면 Σ A_i,max < 총 gain 제약일 때 INFEASIBLE_TARGET(탐색 전). 블록 사이 분기는 둘로 나누고 (a)를 먼저 판정한다(두 조건에 모두 해당하면 (a)). (a) **주 신호 분기**(두 경로가 신호 셀 사슬로 이어져 합류하고, 그 합류 노드가 전류 구동(두 신호 셀 drain 전류가 합산)이거나 블록 출력노드일 때만: feedforward 보상, 병렬 이득 경로)는 Σ dB 분해·내층 DP·잔차 정의를 쓰지 않고 `기록만` 규칙 분기로 기록한다(항상 DEC-59 정지). (b) **측면 주입**(K8 정의(결합 표): DC 역할 바이어스 전류원 + AC 역할 gate 신호 수신 CS, drain 노드에 신호 CD 셀 source가 붙고 gate 넷이 그 CD 셀 입력 넷에서 CD 엣지로 도달하지 않음. BFS 비용이나 '순방향 신호 경로' 도달성에 의존하지 않는다)는 `계산 규칙 있음`이다: 블록 DP는 사슬로 두고 그 주입을 결합 K8로 기록하며, 해당 metric은 MT3(외층 전체회로 MNA로 판정)다. 예: `sf_pushpull_output_opamp`의 M17(gate N5)·M20(gate N13). (a)의 합류 노드 조건과 (b) 기준은 기본안이며 판정은 J12-d에서 ratify한다. 같은 출력노드로 합류하는 병렬 셀(push-pull 두 CS 등)은 입력 기준으로 판정한다: 셀들의 신호 입력 단자(CS·CD는 gate, CG는 source, pass는 신호가 들어오는 쪽 단자. 교류접지에 붙은 gate는 입력으로 세지 않는다)가 블록 입력 넷이거나, 블록 입력 넷에서 pass 셀·같은 묶음의 CD 셀(DEC-63)·블록 내부 노드를 거쳐 닿는 넷이면 한 블록이다(입력 하나, 그 경로 노드는 블록 노드 집합에 넣어 국소 모델이 함께 스탬프, `계산 규칙 있음`, 비사슬 DAG 아님). 신호 입력 단자가 서로 독립인 입력(블록 내부로 이어지지 않는 서로 다른 외부 넷)을 받는 병렬 셀은 다입력 블록으로 `기록만` 규칙 분기다(항상 DEC-59 정지). 예: 파일럿 M16(gate Vop1)과 M15(gate Vg15)는 Vg15가 floating battery(M9a/M9b pass)로 Vop1과 이어진 블록 내부 노드라 한 블록이다. 캐스코드 합류도 같다: 파일럿 Vom1의 M2a/M3a, folded out의 M6, nmcnr NodeM2의 M107은 CG라 신호 입력 단자가 source(블록 내부 노드)이므로 한 블록(`계산 규칙 있음`)이다. LUT·구조만으로 상한을 계산할 수 없는 제약은 "상한 미상"으로 보고한다.
* **DOF**: 변수(W0·W1·W3이 쓰지 않는 모든 노드전압, 소자 gm_id, L 동치류 L, θ 전류 변수(DEC-70 정의: KCL·전류 강제 관계로 정해지지 않는 가지 전류의 독립 기저), DC 전류 경로에 있는 값 미선언 저항 값)와 등식(diode VGS=VDS, `equal_vgs`, `budget_ref`, `stacked_vsb`, `kvl_branch`(DEC-64 v2), KCL)으로 구조 rank를 센다(부등식은 경고). 수치 rank는 θ 표본에서의 Jacobian(`numpy.linalg.matrix_rank` 기본 허용오차, FD 스텝 = 해당 변수의 LUT 격자 간격, 표본 수 = DEC-34 식의 샘플 수 안). 결과 `DofReport{status: ok | underdetermined | overconstrained, 경쟁 목표 쌍}`. overconstrained는 INFEASIBLE_TARGET.

**3층 할당(DEC-45)**

| 층 | 명세 |
|---|---|
| 내층 블록 DP | y 고정. DP의 블록 gain·전력은 블록 국소 DC 점(블록 내부 KVL·KCL·포화를 만족하는 점)에서 계산한 **할당용 추정**이고, 제약 판정은 DP 해를 평가 커널(GB7 봉인 → 제약 판정 → GB8)로 다시 평가한 값으로 한다(추정과 판정 값의 차는 결합 잔차로 기록). 버퍼 블록도 DP 단계다(DEC-63). 상태 = (블록 순서, 누적 gain bin), 결정 = 블록 안 셀마다 독립인 (gm_id 격자점, L 동치류의 LUT 앵커)의 벡터(DEC-04). L 앵커 후보는 LR5의 동치류별 격자다. kind가 다른 소자의 L을 한 결정변수로 묶지 않는다(반회로 분리 유지). 블록 안 전수 크기 Π(셀별 격자 수)가 DEC-34 예산에서 계산한 평가 수 안이면 전수, 넘으면 강결합 셀 그룹 단위 좌표강하(같은 직렬 전류 경로를 공유하는 셀 -- 예: 입력 소자와 그 캐스코드 -- 과 `kvl_branch` 사이클 멤버(DEC-64. 등식이 종속시키는 멤버 하나의 gm_id는 W2 블록이 풀고 격자 스캔은 독립 멤버만 한다. 루프 가지 전류는 θ 전류 변수로 스캔한다)를 S1에서 구조로 유도해 한 좌표로 함께 스캔한다. 그룹은 탐색 단위일 뿐 값을 같게 만드는 결정 제약이 아니다. 종료 규칙은 중층과 같다), 비용 = 전력(U-10 정의), 면적 제약이 있으면 면적 bin 추가. gain bin 해상도 = 인접 격자점이 만드는 블록 gain 차의 최솟값(계산) |
| 중층 좌표강하 | y의 각 차원을 자기 가능역의 1-D 격자에서 순서대로 최소화. 공유 VGS는 gain 기준(DEC-10). y 좌표 평가 1회 = 평가 커널 1회(봉인 포함). 종료 = 한 바퀴에 y 불변, 또는 목적값 감소 ≤ DP 목적값 분해능. 상한 = y 격자 점 수의 합(유한 격자·비증가라 종료 보장) |
| 외층 미세조정 | DP·좌표강하 해를 시작점으로 SLSQP(`SPECS[circuit]["slsqp_kwargs"]`). MT3 제약은 이 층에서만 판정 |

검증: 사이징 대상 회로 전부에서 **전체회로 MNA를 목적·제약으로 쓰는 축소 격자 전수탐색**(다른 모델)과 대조, 최적 목적값 차 ≤ 격자 분해능.

**보상 규칙(GB5)**

* 보상 변수 = 극점 노드 목록의 두 노드 사이에 걸린 보상 수동소자 전부(개수 가변)와 gm_i. 판정은 봉인 후보마다의 θ 제약이다(DEC-70). 보상 해법은 극점·영점 식을 극점 노드 목록과 MNA에서 조립하는 규칙 하나이며 stage 수에서 `solves_for`·gm 참조를 유도한다(2단 하드코딩 금지, 회로별 보상 함수 금지, DEC-62). 이 규칙으로 풀리지 않는 보상 구성은 `기록만` 규칙 분기로 기록한다(항상 DEC-59 정지).
* `ID_source` 타입: `kcl`(KCL·미러 비율로 정해짐) / `ideal_source_ref`(값 선언 이상 전류원) / `theta_current`(θ 전류 변수, DEC-70 -- class-AB 정지전류 등 게이트-소스 KVL 루프가 있는 가지도 여기다. 그 루프는 전류가 아니라 멤버 gm_id 하나를 종속시킨다, DEC-64).
* `compensation: null`(단일단): 기본안 gm_1 요구량 `gm_1 ≥ 2π·gbw_target_hz·C_out,total`(C_out,total = 봉인점 출력노드 용량 `ss.node_c_farad` + 부하 요소 값). gm_1과 C_out,total은 서로 의존하므로 봉인 후보마다 판정하는 θ 제약으로 둔다(DEC-70). U-12 확정 전까지 기본안으로 구현하지 않는다.

**출력 구동 규칙(GB5·GB6, DEC-58, 대신호)**: 모든 값은 봉인 통과 점에서 계산한다. `driving_spec`에 슬루율이 선언되면 극점 노드 목록(gain 제약 metric 전달 뷰)의 노드 k마다 방향별(충전/방전) 최대 전류 ≥ 슬루율 × C_k,total을 GB6 할당의 θ 제약으로 건다(DEC-70). C_k,total(`ls.c_slew_farad`) = 봉인점 노드 용량 + 그 노드에 걸린 보상 커패시터(반대 노드가 따라 움직이는 Miller 커패시터는 전체 값) + 출력 포트 노드이면 부하 요소 값. 극점 계산의 노드 용량(`ss.node_c_farad`, Miller 효과 반영)과 다른 필드다. 최대 전류는 공급 셀의 DC 역할로 판정한다(DEC-65: 바이어스 셀 = 봉인점 ID, 신호 셀 = LUT ID(VGS_max), 측면 주입 셀 = 상한 미상). 따라서 Miller 보상 회로의 내부 노드 슬루와 출력노드 슬루가 함께 걸린다. `driving_spec`에 부하 피크 전류(`load_peak_amp`, 대신호)가 선언되면 출력 포트 노드의 방향별 최대 출력 전류 ≥ 그 값이고, DC 부하 전류(`load_dc_amp`)가 선언되면 출력 포트 KCL에 넣는다. 전류와 gm의 관계(같은 gm_id에서 전류가 오르면 gm도 오름)는 봉인점에서만 성립한다. 슬루율이 선언되지 않으면 KCL 전류만 쓴다. 측면 주입 셀·'상한 미상' 방향만 J3(파일럿)·J12(버퍼 두 회로) 결론을 따른다.

### N3.8 metric

* **gain**(`ss`): 제약 판정은 gain 제약 metric이 선언한 전달 뷰 `(ac_excite, sense)`의 봉인 통과 점 전체회로 MNA 전압 전달함수 하나(`gain_ss_db`). 기모드 여기는 그 한 경우이고 단일 입력 여기도 같다(N3.2-2). 전류·트랜스임피던스 단위는 `기록만` 규칙 분기다(DEC-59). 회로별 이관: 파일럿 `gain_stages_sum` -> `gain_ss_db`, folded `_metric_folded_cascode_gain_db` -> `gain_ss_db`(ports U-08 선행), nmcnr `_metric_nmcnr_gain_db` -> `gain_ss_db`(ports 선행), two_stage는 이미 MNA(계산기 type `smallsignal_gain_db`, metric 이름 `gain_db` -> `gain_ss_db`).
* **블록 국소 소신호 모델**: 블록 노드 집합(N3.2-6. 병렬 셀 입력을 잇는 pass 경로 노드를 포함한다, N3.7 달성가능성)만 미지수로 둔 절점방정식을 푼다. 블록 입력 넷은 단위 신호로 구동하고, 블록 밖 노드는 해당 여기 뷰의 교류접지 또는 다음 블록 국소 모델에서 계산한 입력 넷 어드미턴스(DEC-63: cgd는 drain 노드, cgs는 source 노드, cgb는 bulk 넷에 스탬프. CD 입력은 부트스트랩 포함, 저주파 gain에는 0이고 극점·K5·`parasitic_pm_ss_deg`에만 들어간다)로 고정한다. 스탬프 값의 출처는 둘로 필드를 나눈다: (i) GB8·제약 판정 = 봉인 통과 S2 `dc` 스냅샷의 `ss` 값 (ii) GB6 내층 = 블록 국소 DC 점의 할당용 추정. LUT에 CGS·CGB 열이 생기기 전(DF-28)에는 CGG−CGD를 g–s에 스탬프하는 근사로 표시하고 해당 metric은 `verified_by` 전까지 검증 대기다. 소자는 단자별로 gm·gmb·gds·cgg를 스탬프하므로 CS·CG·CD·pass를 따로 분기하지 않는다. 블록 gain = 출력노드 전압 / 입력 전압(dB, 저주파). 블록 경계를 가로지르는 되먹임 수동소자가 있으면 한쪽을 교류접지로 두는 근사가 되므로 그 블록 gain metric을 MT3로 분류한다.
* **gmb**: LUT에는 gmb 열이 없다. LUT VS 축(|VSB|)에서 `gmb = ∂ID/∂VSB`를 수치미분으로 유도하는 함수를 MOD1에 두고, 블록 국소 모델과 전체회로 MNA가 같은 값을 쓴다. gmb는 봉인 통과 스냅샷의 vsb(`dc`)로 계산하고 입력 카운터를 기록해, 레벨 시프트(W2 VGS)와 gmb가 같은 vsb 버전을 읽는다(SC-b)(현 MNA가 gmb를 넣지 않는 것은 7a에서 함께 고친다).
* **블록 속성**: 블록 국소 모델에서 전압 이득 `gain_ss_db`와 출력노드 테브난 임피던스(`ss`)를, DEC-65 규칙으로 방향별(공급/흡수) 최대 출력 전류(`ls`)를 봉인 통과 점에서 계산해 기록한다(S2). 이득 블록은 GB6 gain 할당의 결정 대상이고, 버퍼 블록은 gain 목표를 받지 않지만 전압 이득(1 미만)이 누적 bin에 들어가는 내층 DP 단계로 결정한다(DEC-63). 출력 임피던스 판정은 DEC-66: 전체회로 MNA에서 여기원을 교류접지로 두고 출력 포트에 전류를 주입한 저주파 개루프 값 `rout_ss_ohm`이며, 엔진은 임계값을 만들지 않고 spec에 선언된 `rout_ss_ohm` 제약만 판정한다(블록 테브난 값과의 잔차 기록). 부하 용량만 있는 회로는 저주파 gain에 Rout이 드러나지 않으므로 gain 제약으로 대신 판정하지 않는다.
* **잔차**: 잔차 = MNA gain − Σ 블록 gain. 블록 국소 모델은 블록 밖을 고정한 모델이라 전체회로 MNA와 독립이며, 전체 MNA 해를 잘라 만든 전압비의 곱으로 분해하는 정의는 금지(정의상 참).
* **감도 게이트**: 봉인 스냅샷마다 영향 집합(SC-e)에서 분해 metric이 읽지 않는 소자를 건드리는 θ 방향으로 섭동한다. 분해 값 변화 ≤ ε 이고 MNA 값 변화 > ε 이면 오류. ε = MNA 선형해 잔차 노름에서 계산한 수치 분해능.
* **metric 티어**: metric마다 `domain`(dc / ss / ls)과, `ss`이면 그 metric의 전달 뷰를 적는다. DC metric의 블록은 gain 제약 전달 뷰의 블록으로 센다. support(SC-e) ⊆ 블록 하나 -> MT1, 블록별 항의 합 -> MT2, 그 외 -> MT3. MT1·MT2는 내층·중층, MT3는 외층에서만 쓴다.
* **전력**(DC 정지 전류 기반): 정의는 U-10(후보 `sum_current` / `_metric_supply_current`). 결정 전까지 보고에 "스택 중복계상 전력"임을 명시한다. 레일이 셋 이상인 회로는 공급전류를 레일별로 기록하고 제약은 선언된 레일 기준으로 건다. 이름은 U-10 결정과 함께 정한다(후보 `supply_current_dc_ua` / `power_dc_w`, DEC-68).
* **스윙·입력 범위**(`ls`, I-A6): 노드 k 방향별 한계 = 레일에서 k까지 DC 경로 합의 최소 여유(VDS 엣지는 포화 하한(DF-25), VGS 엣지는 그 전류에서 vsb를 포함한 VGS(W2)). follower는 `V(out)max = V(g)max − VGS`, `V(out)min = 레일 + VDsat(sink)`처럼 연쇄한다. 한계에서의 전류는 부하 전류 선언값, 없으면 봉인점 정지전류. 버퍼 입력 범위(ICMR)도 같은 경로 합이다. 스펙에 선언된 경우만 제약이고 아니면 보고만 한다(U-29). DC 봉인의 포화 여유(N3.6 항목 7)와 필드를 나눈다.
* **`verified_by`**: {script, oracle_kind, max_error, metric_code_hash, date}. metric 코드 해시가 바뀌면 무효. 유효한 `verified_by`가 없는 metric은 제약으로 쓸 수 없다(적용 순서 U-11).
* **SPICE 독립 검증**: `write_spice_netlist(S1, S2, models) -> path`, `run_ngspice_op_ac(path) -> {nodes, ids, ac}`(`C:\ngspice\Spice64\bin\ngspice_con.exe -b`, 모델 경로는 LUT 생성 메타에서 읽는다). 비교량과 허용오차: 노드전압 `tol_V`, 소자 ID `tol_V × gm`, AC gain = 노드 허용오차를 소신호 감도로 전파한 값. LUT에 없는 접합용량 때문에 못 세는 노드는 제외하지 않고 별도 열로 보고한다.

### N3.9 L 결정 규칙

| ID | 규칙 |
|---|---|
| LR1 | S1 L 동치류 멤버는 L을 공유한다. 주인은 DEC-17 규칙. 종류가 다른 소자 간 VGS 매칭은 L을 공유하지 않는다 |
| LR2 | 매칭 그룹의 L은 전원 동시에 바꾼다 |
| LR3 | LUT 파일이 kind별로 가진 L 앵커 집합 밖으로 외삽하지 않는다. spec `L_candidates`는 탐색 격자이며 앵커 범위 안이어야 한다. L 밖 축(VGS·VDS·VS)도 외삽하지 않는다: 축 밖 입력은 클램프하지 않고 구조화 실패 `lut_axis_out_of_range{소자, 축, 값, 범위}`(SEAL_VIOLATION)로 처리한다(DF-27). 필요한 VS 축 상한은 상수로 두지 않고 library 회로 `supplies_v`의 최대 전위 차(현재 1.8 V, U-27)에서 유도해 LUT 생성 체크리스트 입력으로 둔다(U-27) |
| LR4 | L 증가가 항상 gain 이득은 아니다 -- 격자 전수로 판단한다 |
| LR5 | 초기 L 목표(역할은 라벨이 아니라 S1 유도 사실이다, IC4): 미러(`equal_vgs` 멤버) = kind별 knee(`measure_L_knee`, 동치류 멤버의 탐색 gm_id 가능역으로 한정한 곡선에서 계산. 현 구현은 I-A15), 바이어스 레플리카(J1 교류접지 예외 목록 소자) = `feasible_L_window` 하한, 캐스코드(전류 구동 CG 셀)·그 밖 신호 경로 셀 = knee 목표를 거부하고 theta 탐색이 정한다(`derive_role_L` 가드 유지). 모두 `feasible_L_window`로 clamp한다. **탐색 격자**: 동치류마다 초기 격자 = {knee 앵커와 인접 앵커} ∪ {`feasible_L_window` 하한 앵커}. 블록이 실현 불가(W 한계, 블록 gain 상한 < 목표)이거나 한 칸 넓힌 격자에서 목적값(면적 제약·목적이 있으면 면적 포함)이 격자 분해능 이상 개선되면 그 동치류 격자를 인접 앵커 한 칸씩 넓히고, 개선이 없거나 LR3·LR6 경계에 닿으면 멈춘다. 근거: knee 근방만 쓰면 파일럿 stage1에서 pmos 입력이 W 한계로 L 0.5µm를 요구해 50dB에서 면적 약 3배(실현은 됨), 70dB 초과 불가(원자료 `docs/03-analysis/gain-budget-gmid-sizing-function-audit/review3_lut_L_vs_VDS.results.md`) |
| LR6 | L 상한은 `parasitic_pm_ss_deg >= pm_target_deg`(봉인 통과 점마다 판정하는 θ 제약, DEC-70. 격자 경계로 쓸 때는 봉인 전 추정), 하한은 mismatch 임계값(출처 U-17)이다 |
| LR7 | gain이 부족할 때 W4 자유 노드전압 창에 여유가 있는 스택은 창 안에서 먼저 재배분한다(W1/W2 노드 제외). 창이 소진됐거나 창 폭이 같은 블록 소자의 VGS(gm_id·L)에 묶인 스택(예: 파일럿 stage1은 입력 게이트 공유로 창 폭이 입력 소자 VGS 합에 묶인다)은 VDS와 L을 같은 단계에서 평가해 블록 DP 목적값으로 고른다. VDS 재배분의 주 효과는 면적(파일럿 stage1 1~3%)보다 활성 제약 여유를 격자 분해능까지 줄이는 것이다(VDS 균등 고정 대비 목표 초과 1.7dB -> 0.1dB, NFR-5). GB6 중층에서 적용하고, 재배분 후보마다 GB7 봉인 → GB8 gain으로 판정한다(좌표 평가 1회 = 평가 커널 1회) |
| LR8 | L을 바꾸면 행 폭·n_fingers(`check_box_shape`, finger 폭 호환)를 재판정한다. 오일러 패스는 L과 무관하다. 같은 물리 행 안에서 L은 달라도 되지만 finger 폭은 같아야 하고, 매칭 그룹이면 LR2가 우선한다. branch(`vertical_stack_id`, 전기)와 row(물리 행)는 다르다: 물리 행은 (kind, body 넷)으로 먼저 나뉘므로 같은 branch 안에서 L이 달라도 된다. 행 안 L 통일은 행 폭을 줄이지 않는다(행 폭 = Σ n_fingers × (L + overhead), overhead는 L과 무관). 간격·허용 L 규칙은 PDK 선언에서 읽는다(sky130 선언: 간격 규칙이 L과 무관하고 고정 poly pitch가 없어 행 안 L 혼재는 DRC 제약이 아니다). 실측(원자료 `docs/03-analysis/gain-budget-gmid-sizing-function-audit/review3_layout_equal_L.md`): 행 안 L 혼재는 파일럿 24행 중 5행뿐이고 기존 4개 회로 중 나머지 3개는 0, 파일럿에서 W를 두고 행마다 L을 최댓값으로 통일하면 행 폭 +7~11%·box 비율 악화, W를 L 비례로 재산정하면 finger 배정 실패 또는 finger 폭 < sky130 최소폭. 레이아웃 판정 지표 = 공통 finger 폭 존재, finger 합, box 비율. 레이아웃을 이유로 L을 통일하는 경우는 매칭 그룹(LR2)과 허용 L 목록을 강제하는 공정(PDK 선언)뿐이다 |
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
  contracts/       IC1~IC11, SC-a~SC-e 계약 test
  regression/      library 회로 측정(대상 구분 DEC-47), 규칙 분기 발동표(DEC-59)
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

**spec card** `docs/02-design/specs/<id>.spec.md`, `<id>` = `YYYYMMDD-<slug>`. 필드: 의도 / 관찰 가능한 계약 / interface card / 판정 유형(`red-green` 또는 `equivalence`) / oracle 종류와 출처 / 거부해야 할 입력 / library 회로 적용 여부(DEC-47 대상 구분) / 재현할 수치 / 결정 필요 항목 / 승인 기록 링크.

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

1. 대상 제약의 선언값을 `B_ok`로 둔다. `B_fail`은 제약을 조이는 방향(op가 `>=`면 큰 쪽, `<=`면 작은 쪽)으로 `B_ok`에서 격자 분해능 × 2^j(j = 0, 1, …)만큼 떨어진 값을 차례로 시험해 처음 실패한 값이다(확장 횟수 상한 = 반복 상한 식과 같은 방식으로 계산).
2. 각 스텝은 `B = (B_ok + B_fail)/2`로 두고 그 회로의 선언 탐색 인자(`SPECS[circuit]["slsqp_kwargs"]`) 그대로 원래 탐색을 돌린다. 성공 -> `B_ok = B`, 실패 -> `B_fail = B`.
3. 종료: `abs(B_ok − B_fail)` ≤ 그 metric의 격자 분해능(spec 격자가 만드는 최소 metric 차, 계산). 부호·0 근방 값(dB, 위상)에도 같은 식이다.
4. 답은 마지막으로 성공한 `B_ok`이고, 선언 `n_starts`개의 서로 다른 시드에서 **전부 성공**해야 채택한다.
5. 선언에 `value`와 `_derived{지문, 스텝 이력, 시각}`을 기록한다. `value_from_constraint`로 이 값을 참조하는 제약은 함께 움직인다(의도된 결합).
6. 구현: `achievable_metric_bound(mode="bisect")`. 한 스텝이 전체 탐색 1회라 한 번 재서 기록하고 이후 읽기만 한다. 호출 도구는 기존 `derive_achievable_bounds.py`(TS6에서 `tests/tools/`로 이동)를 재사용한다.

### N3.14 공통 실패 규약

| 분류 | 발생 | 예외(모두 `InfeasibleSizingError` 하위) | 탐색 중 처리 | 파이프라인 exit code(서로 다른 비0 규약값, 분류 순서대로 배정) |
|---|---|---|---|---|
| STRUCTURE_UNRESOLVED | `review_needed` 잔존(6c 이후), `undetermined` 노드, `unsupported_rule_branch`(검증 발동 0 분기, 6c 이후, DEC-59), `undeclared_loop_constraint`(7b 이후, U-24) | `StructureUnresolvedError` | 탐색 시작 전 정지 | 2 |
| STRUCTURE_UNRESOLVED(최종 해) | `structure_inconsistent`가 최종 해에서도 남음(값 의존 노드 구동 종류가 ratified 값과 불일치) | `StructureUnresolvedError` | 탐색 후 최종 해 보고 정지(J12 재분석 대상) | 2(같은 분류) |
| (후보 실패 레코드 class = `structure_inconsistent`, 분류 STRUCTURE_UNRESOLVED의 하위) | 탐색 중 GB8에서 값 의존 노드 구동 종류가 ratified 값과 불일치 | 예외 없음(실패 레코드) | 실패 기록(margin = 판정 경계까지 거리), 탐색 계속 | -- |
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
| `human` | `objective`, `constraints[]{metric, op, value, source}`(`metric`은 실제 metric 이름, 예 `gain_ss_db`·`rout_ss_ohm`·`pm_ss_deg`), `ports{<넷>: {role}}`(`direction` 없음, role에서 유도), `element_values{<요소 이름>: {value_ohm | value_farad | value_dc_amp}}`(수동소자·이상원 값. 부하 용량 CL은 부하 요소의 `value_farad`), `compensation_targets{gbw_target_hz, pm_target_deg}`(부하 용량은 요소 이름으로 참조), `driving_spec`(슬루율, `load_peak_amp`, `load_dc_amp`), `wall_clock_budget_s`(DEC-34), `supplies_v`(DEC-60), `node_voltage_targets_v`, `input_dc_net`(입력 DC가 넷 이름일 때), `gain_budget_db_override`(source 필수), `cross_kind_matching`, `same_as`(M7=M6, M36b=M36a처럼 connectivity로 유도되지 않는 것만) |
| `derived` | S1·S1v에서 유도한 필드: {필드, status, evidence, rule_hash} -- stage 구성, `vertical_stack_id`, `vsb`, `vds_match_vgs_of`, 같은 종류 `gm_id_match_vgs_of`, `compensation.stage_devices`, `vds_kvl_groups`, metric 소자 역할 인자, 노드 공유 `budget_reference_device` |

* 로더 `load_sizing_spec(path)`는 미지 필드를 거부하고, `topology_hash` 불일치를 거부하고, `constraints[].source`가 없거나 논문이면 거부하고, DEC-69 단계별 옛 이름(`supplies`, `vdd` 스칼라, `value_amp`, `PM_target_deg`, `GBW`, `CL` 키, `same_as_device` 등)을 거부한다.
* 명칭: 슬루율 필드 이름은 metric 단위 레지스트리(DEC-53)의 이름-단위 규약과 DEC-68 접미사 규칙을 따라 하나로 정한다(I-C7 해소). 실제 이름은 `7b-compensation-allocation` design이 레지스트리 단위표를 인용해 적는다.
* 이관: 기존 4개 회로마다 topology.json의 `device_roles`/`sizing_roles`/`compensation`, `passive_elements[].value_ohm`·`value_farad`, `ideal_sources[].value_amp`(→ `element_values`)에서 `sizing_spec.json`을 생성하고(MG3 이름 변경을 같은 이관에서 한다), 생성본으로 같은 결과가 나오는지(equivalence) 확인한 뒤 topology.json에서 해당 필드를 제거한다. 제거는 topology.json 변경이라 사용자 확인 후 오케스트레이터가 반영한다. 옛 필드가 없는 신규 회로는 U-25 스펙 선언 뒤 `sizing_spec.json`을 새로 작성한다. 부하 요소 CL이 없는 `folded_cascode`·`nmcnr_amplifier`·`two_stage_ota`는 이 이관에서 CL 요소를 추가한다(connectivity라 사용자 확인, U-08 포트 선언 확정·영향 test와 함께, U-31).

### N3.16 명명 규칙·개념별 정본·마이그레이션(DEC-68·69)

규칙은 DEC-68이 정본이다. 아래 표는 개념마다 이름 하나·저장 위치 하나를 정한다. 코드 위치는 참고용이며 줄 번호는 design이 다시 확인한다(원자료 `docs/03-analysis/gain-budget-gmid-sizing-function-audit/review5_schema_unification.md`).

| 개념 | 정본 이름(영역) | 저장 위치 | 흡수되는 옛 이름 | 단계 |
|---|---|---|---|---|
| 레일 넷 | `supply_nets`(list) | topology | sizing_recipe `_DEFAULT_RAIL_HI/LO`, `rail_nets`, stick_diagram `_RAIL_NETS` | MG1 |
| 레일 전압 | `supplies_v`({넷: V}, DC) | sizing_spec human(7b 전 `SPECS` spec) | spec 스칼라 `vdd`(유도 함수 하나로 대체), 계획 `supplies`, metric `rail`의 `else 0.0`, nmcnr `sky130_supplies_v`·문헌 `supply_v`(→ 각 문서 기록의 `supplies_v`) | MG1(코드), MG0(문서) |
| 공급 전류 셀 레일(다른 뜻) | metric 인자 `supply_nets` 이름 삭제, 레일별 기록 | metric 선언 | sizing_recipe `supply_current`의 `spec.get("supply_nets")` | MG1 |
| 소자 벌크 | `bulk` | topology `netlist[]`(선택) | S1 `b` | -- |
| 소스-바디 전압 | `vsb`(DC, S2 `dc`) | sizing_spec derived | `vs` | MG0(`_TEMPLATE` 안내) |
| 요소 값 | `value_ohm` / `value_farad` / `value_dc_amp`(DC) | sizing_spec human `element_values` | topology `passive_elements[].value_*`, `ideal_sources[].value_amp`, 문서 `IBias_amp`·`CL_farad` | MG3 |
| 부하 용량 | 부하 요소(예 `CL`)의 `value_farad` | 위와 같음(보상·metric은 요소 이름 참조) | spec `CL`, metric 인자 `CL`, 계획 `compensation_targets.CL`, `driving_spec` 부하 용량 | MG3 |
| GBW 목표 | `gbw_target_hz` | human `compensation_targets` | `GBW`, `GBW_hz` | MG3 |
| PM 목표 / 측정 | `pm_target_deg` / metric `pm_ss_deg`(`ss`) | human / metric 선언 | `PM_target_deg`, `PM`, 문헌 `pm_deg` / metric `pm_deg` | MG3 |
| 기생 극점 PM | metric `parasitic_pm_ss_deg`(`ss`) | metric 선언 | `parasitic_pm_deg` | MG3 |
| 이득(metric 이름) | `gain_ss_db`(`ss`, 단일 정본) | metric 선언, 목표는 constraint | `gain_db`, `gain_full_circuit_db`, 문서 `dc_gain_db` | 7a(metric 통일)·MG3 |
| 이득(계산기 type) | 레지스트리 키 `smallsignal_gain_db` 유지 또는 개명(7a design) | `_METRICS_REGISTRY` | -- | 7a |
| 출력 저항 | metric `rout_ss_ohm`(`ss`, DEC-66) | metric 선언, 목표는 constraint | 문서 `rout_ohm` | 7a |
| 방향별 최대 전류 | `ls.i_out_max_source_amp` / `ls.i_out_max_sink_amp` | S2 | -- | 7b |
| AC 여기·감지 | `ac_excite{}`, `sense_p`, `sense_n`, `sense_mode`. 비 metric은 `num{같은 4키}`, `den{같은 4키}` | metric 선언 | `excite`, `excite_num/den`, `sense_num/den` | MG2 |
| 노드전압 목표 | `node_voltage_targets_v`, 출력 공통모드 `voc_target_dc_v` | human | `node_voltage_targets`, `Voc_des` | MG3 |
| 입력 DC 넷 | `input_dc_net` | human | 문서 `input_dc_v: "agnd"`, `input_common_mode` | MG0(문서)·MG3 |
| 포트 | `ports{<넷>: {role}}` | topology | `direction`(role에서 유도) | MG2 |
| 극성 어휘 | `nmos` / `pmos` | 전체 | `nfet` / `pfet`(`vth0_slope` 등) | MG2 |
| 소자 목록 | `devices` / 단일 `device` / 역할 인자 `<역할>_device` | 전체 JSON(`members`는 메모리 S1 엣지 전용) | `names`(matching_pairs), `stages` | MG2 |
| 동일 치수 | `same_as` | human | `same_as_device` | MG3 |
| 전압 예산 기준 | `budget_reference_device`(S1 엣지 `budget_ref`와 대응) | sizing_spec derived | -- | -- |
| 기계가 읽는 `_` 키 | `netlist_sections`, `known_dangling_nets`, `compensation_status`, `spec_source` | topology / spec | `_netlist_sections_structured`(텍스트판 `_netlist_sections` 삭제), `_known_dangling_nets`, `_compensation_status`, `_spec_source` | MG2 |
| 주석 키 | `_<필드>_comment`(문자열 또는 배열), 로그는 `_correction_log: [...]` 하나 | topology | `_note`, `_schema_note`, `_X_comment_N`, `_correction_log_N` | MG2 |
| 문서 목표 기록 | 논문 값 `_paper_target_spec` / 사용자 확정 스펙 `_declared_target_spec`(둘 다 human과 같은 키) | topology 문서 필드 → 7b에서 human으로 이관 | pushpull·sf_pushpull·two_stage_ota_sf의 `_paper_target_spec`, two_stage_ota `_target_spec_comment` | MG0(컨테이너 이름)·MG3 |
| PDK 상수 | 한 곳 선언(출처 규칙 번호 명시, `min_finger_w` = difftap.2, `W_bounds` 하한은 `min_finger_w`에서 유도, U-30). 키 이름 접미사는 U-32 | 공정 기록 한 곳(LUT 생성 메타와 연결) | spec_fn 4개 복사본(`L_min`, `W_bounds`, `min_finger_w` 등) | Phase 4(선언), 이름은 U-32 |
| 제약 metric 표시 단위 | `mismatch_sigma_mv`, `mirror_ratio_error_mv` | metric 선언·spec | `mismatch_sigma_mV`, `mirror_ratio_error_mV` | MG3 |
| 보상 함수 인자 | snake_case·접미사 이름(시그니처 변경, 매핑표 없음) | `topology_library.py` | `GBW`, `CL`, `PM_target_deg` 등 | MG3 |

| 단계 | 내용 | 담당 | 배치 |
|---|---|---|---|
| MG0 | 계획 문서 명칭(이 개정), `_TEMPLATE`의 옛 `vs` 안내와 matching_pairs `kind` 예시 정정, topology 문서 필드 이름(`_paper_target_spec` → `_declared_target_spec`(사용자 확정 스펙 세 회로), 문서 `input_dc_v` → `input_dc_net`, nmcnr `sky130_supplies_v` → `_declared_target_spec.supplies_v`, 문헌 `supply_v` → `_paper_target_spec.supplies_v`) | 오케스트레이터(topology·템플릿은 사용자 확인 U-16) | 즉시 |
| MG1 | 레일: topology `supply_nets`, spec `supplies_v`, `vdd` 유도 함수, 이름 집합 제거, metric 인자 `supply_nets`/`rail_nets` 정리. 옛 키 거부 게이트 + IC11 | code-author / test-author | Phase 4(DF-19·24·26과 같은 변경 단위) |
| MG2 | `_` 접두사 정리, 주석 키 통합, `nfet`/`pfet` → `nmos`/`pmos`, `names` → `devices`, 여기·감지 선언 모양, `ports.direction` 삭제. 각각 옛 키 거부 게이트 | code-author / test-author | 6a 착수 전(S0 해시 입력 키가 6a에서 굳는다. 뒤로 미루면 ratified 기록이 전부 `review_needed`로 넘어간다) |
| MG3 | spec 값 이름, 요소 값·`element_values`, `same_as`, 보상 함수 시그니처, 하네스 탐색 설정·PDK 키 접미사(U-32 결정 시), 문서 목표 기록의 human 스키마화, CL 요소 추가(U-31) | code-author / test-author, 오케스트레이터(topology 필드 제거·추가) | 7b(`sizing_spec.json` 이관과 한 번에) |

* 문자열 값 안의 이름(`value_from_spec: "PM_target_deg"` 등)은 키 검색에 걸리지 않으므로 test-author가 값 문자열까지 옛 이름 0인지 따로 검사한다.
* 옛 키로 저장된 워크스페이스 산출물(instance.json, 보고서)은 재생성하거나 로드 게이트가 거부한다(방침은 해당 단계 design).

---

## N4. 원칙과 강제 검사

### N4.1 기지 사고 클래스 IC1~IC11

사고1~24(`known-incidents.md`)를 클래스로 묶고, 클래스마다 **거부 케이스를 가진 강제 test**를 둔다. 담당 Phase까지는 xfail(TS7)이다.

| ID | 실패 클래스 | 구조적 방지 | 강제 test(`tests/contracts/`) | 담당 Phase |
|---|---|---|---|---|
| IC1 | 물리 제약 미검증 상수 | 모든 전압·전류는 W 티어 또는 선언을 거친다 | `test_vgs_consistency_all_devices`: 모든 소자 VGS 정합 ≤ tol_V(N3.6) | 6b |
| IC2 | 암묵적 순서 의존 | SC-a 단일 writer, NFR-4 결정론 | `test_order_shuffle_invariance`: 소자 dict 순서·그룹 순서·set 순회를 섞어 2회 실행, 이산 필드 완전 일치, 노드전압 ≤ tol_V, 전류 ≤ tol_I, 그 밖의 연속 필드 ≤ tol_V 섭동의 감도 전파값 | 6b |
| IC3 | 조용한 소실·덮어쓰기 | 이름 전역 유일, 저장 필드 목록 단일 정의, pass마다 커버리지 재검증 | `test_coverage_and_field_completeness`: `check_stick_diagram_coverage` + instance.json 소자·필수 필드 누락 0 + 이름 충돌 0 | 1 |
| IC4 | role 라벨 과신 | 물리·connectivity 판정이 항상 우선 | `test_role_label_removal_invariance`: `headroom_role`/`gm_id_role`/`L_role` 전부 제거해도 결과 동일 | 6c |
| IC5 | 게이트 사각 | 게이트 docstring에 "검사하지 않는 것" 절 필수 | `test_gate_docstring_declares_blind_spots`: `check_*`/`verify_*`/`validate_*`/`audit_*` 전수 정적 검사 | 1 |
| IC6 | underdetermined를 반복으로 밀어붙임 | GB4 DOF 진단 | `test_dof_catches_incident19_fixture`: 사고19 픽스처(스택 vds 미지수 2 / 등식 1)를 overconstrained·underdetermined로 판정 | 6c |
| IC7 | 단일 회로·단일 부류로만 검증 | 동작 변경 Phase는 library 회로 측정(DEC-47), 규칙 분기 발동표(DEC-59) | `test_all_library_topologies_run`(regression): library 회로 실행(대상 구분 DEC-47) + 필요 없는 기능 발동 계수 0 + 규칙 분기 발동표 생성 + 검증 발동 0 분기를 타는 픽스처(library topology 로드·변형)에서 `unsupported_rule_branch` 정지 | 6a 이후 매 Phase(정지 케이스는 6c) |
| IC8 | 증거 없는 자동 병합 | 증거 없는 유도는 `proposed`/`review_needed` | `test_unevidenced_derivation_stops_before_search`: 증거 없는 픽스처에서 STRUCTURE_UNRESOLVED | 6c |
| IC9 | 중복 복붙 | 레지스트리 정본 하나, 타입 setter만 | `test_no_raw_duplicated_writes`: 원시 대입·중복 상수 grep 0 | 6b |
| IC10 | 캐시 키가 가변 상태를 놓침 | SC-d 내용 지문, SC-e reader 기록 | `test_cache_key_covers_mutable_state`: `ctx.sized`만 바꾸고 같은 metric 호출 시 옛 값 미반환 | 6b |
| IC11 | 레일 기준 전위 가정(레일 0 V, 레일 이름 집합) | 전압 차는 노드전압과 레일 선언(DEC-60)에서만 유도 | `test_rail_origin_shift_invariance`: 같은 회로를 원점만 옮긴 두 레일 선언으로 돌려 소자 VGS·VDS·VSB·gm_id·W·metric(dc·ss·ls 전부, 여기·감지 넷 선언은 그대로)이 허용오차(전압 tol_V, 그 밖은 tol_V 섭동의 감도 전파값) 안에서 같음(DF-24·DF-26 검출). Phase 4 대상은 레일 둘인 기존 회로(예: `two_stage_ota` (vdd 1.8, gnd 0 V) 대 (vdd 0.9, gnd −0.9 V)). agnd 3레일 신규 회로((vdd 1.8 / vss 0 / agnd 0.9 V) 대 (+0.9 / −0.9 / 0 V))는 `supply_nets`가 생긴 뒤(6a, U-26 (b)) 대상에 추가 | 4(DEC-60 구현, 2레일), 6a(3레일 추가) |

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
| V9 | 물리 불변식 | 사이징 대상 회로 결과가 봉인 항목(N3.6), IC1, `matching_offset` 멤버의 (W/L, gm_id) 일치와 `matching_ratio` 멤버의 (W/L 비 = 선언 비율, gm_id 일치)(gm_id 허용오차 = LUT gm_id 격자 간격, W/L 허용오차 = 같은 ID에서 그 gm_id 허용오차가 만드는 IDu의 상대 차)를 통과 | contracts test | 6b |
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
| DF-16 | 목적함수 `power_uA`(`sum_current`)가 직렬 스택 전류를 중복 계상한다 | 기존 4개 회로 objective | 7a | I-A3, U-10, 보고 시 명시. 목적함수 전력 정의가 GB8 전력 정의와 같은 결정이라 7a로 옮긴다 |
| DF-17 | stick_diagram self-test Test 16의 FAIL 출력이 기준선에 박제돼 있다 | stick_diagram self-test | 1(TS0) | U-01 |
| DF-18 | `run_harness.run`이 실패해도 exit 0이고 θ*를 출력만 한다 | `workspaces/run_harness.py` | 4(N3.14 exit code, θ* 기록) | 보고 시 명시 |
| DF-19 | 레일 넷 집합이 모듈마다 다르다(대소문자) | stick_diagram `_RAIL_NETS`, sizing_recipe `_DEFAULT_RAIL_HI`/`_DEFAULT_RAIL_LO` 레일 판정 | 4(DEC-60 `supply_nets`·`supplies_v` 선언으로 교체, MG1, DF-26과 같은 변경 단위, U-26) | |
| DF-20 | 운영 경로의 근거 없는 폴백 상수(vds 0.6/0.2, margin 0.05, W_bounds·gm_id 격자 리터럴) | `resolve_feed_vds` 계열 | 4 | WP-03 |
| DF-21 | 실행 불가·무의미 probe 3개 | `probe_mirror_common_L_wiring`, `probe_node_voltage_audit`, `probe_vs_semantics` | 2(TS6) | U-02 |
| DF-22 | 지문 불일치 노트 리스트 `_RESOLVE_STALE_NOTES`를 읽는 코드가 없다 | `resolve_constraint_references` | 4 | DF-08과 함께 |
| DF-23 | 결정 레지스터의 파일럿 적용 사실(DEC-09·15·27·55의 소자 이름)이 엔진 코드에 소자 이름 리터럴로 박혀 동작을 정하는지 확인되지 않았다(확인 필요). 박혀 있으면 일반 규칙 대신 이름이 동작을 정한다 | 엔진 소스 전수(topology.json에서 읽은 값이 아닌 소자 이름 문자열 리터럴) | 2(전수 목록·레지스트리 기록), 4(일반 규칙으로 교체) | WP-05, DEC-62 |
| DF-24 | vsb 유도가 bulk를 nmos = 0 V, pmos = `vdd` 인자로 가정한다(nmos는 소스 전압 `v`를 그대로, pmos는 `vdd − v`). 현 하네스는 가장 낮은 레일을 0 V로 둔 단일 기준이라(nmcnr spec `vdd: 1.8`, `run_harness.py` `_spec_nmcnr_amplifier`) 현재 경로에서는 맞지만, `supplies_v`에 음전위 레일을 선언하면 레일 기준 없이 `v`를 돌려주는 nmos 분기가 틀어진다 | `derive_vsb_from_nodes`(sizing_recipe.py 3957행 참고)와 호출부 `reconcile_vsb_from_nodes` 등 | 4(red: 음전위 레일을 `supplies_v`에 둔 픽스처) | DEC-61, DF-01, U-26 |
| DF-25 | 포화 하한이 강반전 근사 `2/(gm/ID)`다(약반전 VDsat와 다르다). LUT npz에는 VDsat 열이 없어(ID·GM·GDS·CGG·CGD·SID_1F, 축 L·VGS·VDS·VS) 교체 식은 6b design이 LUT의 (ID, gds, VDS) 곡선에서 정한다 | `lut_vdsat_headroom`, `_default_cascode_headroom`(`2/gm_id + margin`), DEC-27 구현부 | 6b(유도 규칙 정의와 교체) | DEC-12, DEC-27, WP-03 |
| DF-26 | 레일 판정이 넷 이름 집합 하드코딩이다(sizing_recipe `_DEFAULT_RAIL_HI`/`_DEFAULT_RAIL_LO`, stick_diagram `_RAIL_NETS`). 신규 회로 `sf_pushpull_output_opamp`·`pushpull_follower_buffer`의 중간 전위 레일 `agnd`(DC에서는 W0 레일, AC구조에서는 교류접지)를 레일로 읽지 못한다 | sizing_recipe.py 3882~3883, stick_diagram.py 3147 참고 | 4(DEC-60 구현, DF-19와 같은 변경 단위) | DEC-60, DF-19, IC11, U-26 |
| DF-27 | LUT 표본 VS 축이 0~0.8 V(5점)라 push-pull 출력 follower의 vsb(agnd 출력 기준 약 0.9 V 가능)를 덮지 못할 수 있고, L 밖 축(VGS·VDS·VS)의 축 밖 입력 처리 규칙이 없다(클램프·외삽 여부 미정) | `sky130_nfet_pfet_lut_sample.npz`, `GmIdLUT` 보간부 | 4(red: VS 축 밖 픽스처를 `lut_axis_out_of_range`로 거부, LR3) | DEC-61, U-27 |
| DF-28 | LUT에 CGS·CGB 열이 없어(CGG·CGD만) CD 입력 용량 부트스트랩과 follower 영점을 스탬프할 수 없다. LUT 생성 체크리스트는 두 열을 probe한다 | LUT npz, MNA·블록 국소 모델 스탬프부 | 7a(열 추가 전에는 CGG−CGD 근사 표시, 열 생성은 U-27) | DEC-63, U-27 |

### N5.3 열린 이슈

옛 §10 항목 중 아직 열린 것만 둔다(닫힌 것은 이력 문서 "[판정] §10 닫힌 이슈"). DF와 같은 결함인 I-A3(DF-16), I-A4(DF-05), I-B7(DF-02), I-B9(DF-01)은 N5.2에만 둔다. v5.0에서 I-G3, I-G7, I-G8, I-C3, I-C5, I-C7, I-C9, I-A9는 본문 명세로 닫았다(부록 A). I-A10, I-A11, I-B22, I-C10, I-C11은 v5.0에서 새로 연 항목이다.

| ID | 남은 것 | 담당 |
|---|---|---|
| I-A2 | 면적 정의(트랜지스터 W·L, 레이아웃 면적, 수동소자 면적의 관계) | 7b, U-13 |
| I-A5 | LUT 생성 메타를 읽는 `lut_conditions_from_npz`가 운영 경로에서 불리지 않는다 | 6a(S0에 배선) |
| I-A6 | ICMR·출력 swing metric(`ls`)과 제약 슬롯이 없다 | 7a(metric, N3.8 스윙·입력 범위), 7b(슬롯은 `human.constraints`의 metric, 선언 시만 제약 U-29). 헤드룸(DC)은 봉인 항목 7(포화 여유)이 맡고 스윙 한계를 헤드룸 하한으로 이중 부과하지 않는다 |
| I-A7 | 일반 순환 블록 수렴 판정 | 6b(N3.6) |
| I-A10 | `parasitic_pm_ss_deg >= pm_target_deg`(현 이름 `parasitic_pm_deg >= PM_target_deg`) 제약이 사이징 대상 회로 선측정 없이 걸려 있다(folded는 `omega_c`를 노출하지 않아 측정 불가) | 7a(gain metric 이관 때 `omega_c` 노출), DEC-49 |
| I-A12 | `stick_diagram.PROCESS_GEOMETRY["finger_pitch_overhead_m"]`가 0.0이다(sky130 poly pitch 규칙 미확보) -- 행 폭을 과소평가한다. PDK 선언값에서 유도하도록 바꾸는 것은 공유 엔진 변경이라 승인 대상 | 7b(MOD8) |
| I-A13 | 레이아웃 엔진에 dummy·LDE(LOD/WPE/PSE) 반영이 없다. 매칭 interdigitation 행에 L이 섞일 때의 좌우 대칭 검사도 없다 | 7b(MOD8), 승인 대상 |
| I-A15 | `measure_L_knee`가 knee를 gm_id 격자 전체 중앙값에서 잰다(선택 근거 없음). LR5는 동치류 멤버의 탐색 gm_id 가능역으로 한정한 곡선을 쓴다 | 7b(LR5 구현) |
| I-A11 | 크로스오버 주파수 해석 차이(선언식 36.6MHz 대 전체 응답 실측 30.50MHz)의 원인 미확인 | 7a |
| I-B2 | stage-local/전역 게이트 구현 없음 | 7a(MT 분류) |
| I-B3 | 블록 사이징 함수 시그니처 | 7b(N3.7 내층 DP 입력 = 블록, W4 창, y) |
| I-B5, I-B6 | DOF 진단 구현 없음(VDS·KVL 축, 부등식 오계수) | 6c(N3.7) |
| I-B8 | KCL 잔차 제약 없음 | 6b(봉인 항목 3) |
| I-B11 | IC 강제 test 0개 | 1~7c(TS7) |
| I-B12 | `set` 순회 잔존(sizing_recipe 1곳, stick_diagram 5곳) | 6b(NFR-4, IC2) |
| I-B13 | gm_id·vds 확정 출처 태그가 일부 경로에만 있다 | 6b(SC-a) |
| I-B14 | 사이징 경로가 `value_dc_amp`(현 키 `value_amp`)를 읽지 않는다 | 7b(DEC-08) |
| I-B21 | 선언된 gain 제약이 미러 부하를 못 본다 | 7a(DEC-05, J6), 보고 시 명시 |
| I-B22 | 입력환산 오프셋의 다중 diff pair(cascade 입력환산, CMFB 오차증폭기)와 입력이 대칭 쌍이 아닌 회로(단일 입력, 비대칭 오차증폭기) 처리. 후보: 선언 매칭 그룹마다 ΔVth를 전달 뷰 입력으로 환산한 MNA 감도의 RSS | 7a(DEC-23) |
| I-G1 | 단일단 회로의 gm 출처 | 7b, U-12 |
| I-G2 | 3단 보상의 stage 수 종속 일반화, nmcnr passive 누락 | 7b, J9 |
| I-G4 | class-AB 정지전류 `ID_source` 타입 | 7b(N3.7), J3 |
| I-G5 | 폴딩 노드 역할 | 6a(SP1 역할 분류), J5 |
| I-G6 | stage 분할 구현 | 6a(SP1) |
| I-C6 | 읽히지 않는 스키마 필드(`closed_loop_accuracy_db`, `stage_gm_ref`, `vdd_kvl`) | 7b(v5 스키마에 두지 않음 -- 로더가 미지 필드로 거부) |
| I-C10 | `stack_headroom_slack_v` metric의 담당·제약 여부가 없다 | 6b, U-20 |
| I-C11 | `two_stage_ota` stage1_out 분리와 `nmcnr` stage2_diode_ref 이월 -- 해소 전에는 두 회로에서 유도 기능을 돌릴 수 없다 | U-09 |

### N5.4 탐색 결과를 보고할 때 반드시 명시할 것

수정 전까지: I-B21(gain 제약이 미러 부하를 못 봄), DF-16(전력 중복 계상), DF-03(게이트 예외로 탐색 중단 가능), DF-18(실패해도 exit 0). U-11이 SPICE 대조를 7c로 두면 7a~7c 사이 gain metric의 `verified_by` 검증 대기도 명시한다. 규칙 분기 발동표에서 검증 발동 0인 분기(그 분기의 일반성을 주장하지 않는다, DEC-59). 봉인 전에 계산한 AC 상한·추정 값은 판정 값과 구분해 표기한다(DEC-67). CGS·CGB 근사 스탬프를 쓴 metric(DF-28).

---

## N6. 로드맵

### N6.1 순서표(유일한 순서 정본)

모든 Phase의 공통 착수 조건: **해당 design 문서의 사용자 승인**(DEC-51). 이전 Phase DoD PASS.

| Phase | 범위 | 판정 유형 | 추가 착수 조건 | design 문서 |
|---|---|---|---|---|
| 0 | 함수 재사용 레지스트리 | -- | -- | ✅ 완료 |
| **0.5** | 역할 분리 인프라(N3.12.6), 공격 시나리오·과거 사례 재생 5건(N4.3) | 부트스트랩 | U-15(hook 필드가 없을 때), U-16. MG0(`_TEMPLATE`·topology 문서 필드는 U-16 확인 후 오케스트레이터, 계획 명칭은 v5.10) | `05-role-separation` |
| 1 | TS0, TS1, TS2, TS3, TS5, TS7 선언. IC3(필드 완전성·이름 충돌 검사 신설)·IC5(게이트 docstring '검사하지 않는 것' 절 추가) 활성 | TS0·IC3·IC5 red-green, TS1 equivalence, TS2·TS3·TS5 test-only | U-01 | `10-test-separation` |
| 2 | TS6, 레지스트리 등급 D 삭제(배선을 고른 항목은 Phase 4로), 레지스트리 §2에서 "행동 보존 통합 가능"인 DUP 통합, DF-23 전수 목록 | equivalence(TS6은 test-only, 운영 도구 이동은 code·test 두 커밋) | U-02 | `20-dead-code-dup` |
| 3 | 10모듈 이동(N3.10), shim, 추적 파일 호출부 갱신 후 `sizing_recipe.py` 삭제 | equivalence | U-03 | `30-module-split` |
| 4 | TS4, DF-01~15·18~20·22~24·26·27, MG1 레일 이름 변경(DEC-69), U-27 LUT 재생성, PDK 상수 한 곳 선언(U-30), Phase 2에서 배선을 고른 함수 배선, `fallback_events` 계측(V8), 기존 4개 회로 실행 가능성(I-C11), IC11 활성 | red-green | U-04, U-05, U-09, U-26, U-27 | `40-defect-fixes` |
| 5 | 실패 캐시, 시작점 선택(S3 레코드 v1: θ*·start별 결과·실패), margin 반환 | red-green | -- | `50-failure-cache` |
| 6a | 착수 전 MG2(DEC-69, 옛 키 거부 게이트 포함). GB0(의미·로드 게이트, 영역 표기), S0(LUT 메타 배선 포함), GB1(소자 DC 역할, G_vgs 사이클 DEC-64, 엣지 `domain`), GB2 shadow(소자 구성 분류 CS/CG/CD/pass, 구동 종류, 버퍼 묶음 DEC-63, 출력 방향 구조 분류 DEC-65 포함, library 회로 전부), 규칙 분기 발동표(DEC-59, 기록만). IC7 활성, IC11 3레일 케이스 추가. 6a-1 유도·대조표, 6a-2 공동분석·ratify, `structure.json`, 레지스트리 §2 ★ DUP(diode·미러 그룹·diffpair/tail)를 U-06 결론의 정본으로 통합하고 옛 함수 삭제 | red-green | U-08, U-17, U-26(신규 회로 `supply_nets`). 6a-2는 U-06(J1·J2·J3-ac·J4~J7, J9 ports, J10, J11, J12·J12-a~h, 구조 정본) | `6a-structure-stage` |
| 6b | GB7: W 티어, 순환 블록, 봉인, SC-a~SC-e, 평가 커널 계산 블록과 S2 memo, NFR-4 결정론, DF-25(VDsat 유도 규칙과 포화 하한 교체), 봉인 항목 7(포화 여유)·8(`kvl_branch` 등식), S2 `dc`/`ss`/`ls` 분리, CD source 노드 W2, 평가 커널 계산 블록 분할(보상 블록은 현 순서를 유지하고 출력을 봉인 전 추정으로 표시, 재배열은 7b), 중복 계산 계측(NFR-2). IC1·IC2·IC9·IC10 활성 | red-green | U-06(J8), U-20, U-26(`wall_clock_budget_s`) | `6b-node-voltage-seal` |
| 6c | 결합 잔차 측정, GB3, GB4(LUT 곡선 검사, 블록 gain 상한, DOF), `review_needed` 잔존·`unsupported_rule_branch` 시 정지. IC4·IC6·IC8 활성 | red-green | -- | `6c-coupling-achievability` |
| 7a | GB8: gain metric 통일(`gain_ss_db`), 출력 임피던스 metric `rout_ss_ohm`(DEC-66), 스윙·입력 범위 metric, DF-28(CGS·CGB 스탬프), 블록 국소 소신호 모델과 gmb 유도(MNA에도 gmb 반영), 잔차, 감도 게이트, MT 분류, 전력 정의, metric DUP 3쌍(gain/PM/CMRR) 통합, `verified_by`(U-11 결과에 따라 SPICE AC gain 대조 포함), bisection 도구와 임계값 재도출 | red-green | U-07, U-10, U-11, U-19, J6 승인 기록(6a-2 확정) | `7a-gain-metric` |
| 7b | GB5 보상 규칙(DEC-70 θ 제약)과 평가 커널 재배열(봉인 뒤 보상·슬루·PM 판정), GB6 3층 할당(버퍼 블록 DP 단계 포함), 방향별 최대 전류(DEC-65), `sizing_spec.json` v5(기존 4개 회로 이관, 신규 회로는 U-25 뒤 작성)와 MG3 이름 변경·CL 요소 추가(U-31), 루프 안정도 제약 게이트(U-24), `value_dc_amp` 소비, 면적·Pareto, MOD8 수렴 루프(LR9) | red-green | U-12, U-13, U-14, U-21, U-24, U-06(J3-dc 정지전류, J9 passive), U-31, U-32 | `7b-compensation-allocation` |
| 7c | GB9: S3 전체, Sobol 전역 샘플, 분지, SPICE `.op` 전체 대조. IC 전원 PASS | red-green | -- | `7c-archive-spice` |

### N6.2 Phase별 완료 조건

| Phase | 완료 조건(측정 명령은 design 문서에 고정) |
|---|---|
| 0.5 | N4.3 공격 11건 거부 로그 + 사례 5건 적발, hook 입력 필드 실측 기록, 에이전트 정의 `check_agents.py` PASS, 설치 후 RTL agent 무동작, MG0: `_TEMPLATE` 옛 `vs` 안내 0·사용자 확정 스펙 세 회로의 `_paper_target_spec` 컨테이너명 0 |
| 1 | TS0 판정 기록 / TS1 seed 1~5 stdout 전후 동일 / TS2 기본·셔플 순서 PASS / TS3 판정 문자열 0 / TS5 기준선 참조 0 / 소스에 인라인 self-test 0 / IC3·IC5 PASS, 나머지 IC xfail 선언(담당 Phase 명시) / 사례 caa970b 적발 |
| 2 | 승인된 D 목록 처리, DUP마다 옛 함수 대 정본 차등 test(실행 가능한 library 회로 입력 전수 출력 동일) PASS 후 옛 함수 삭제, 레지스트리 갱신, probe 엔진 식 재구현 0, DF-23 소자 이름 리터럴 전수 목록 |
| 3 | MOD1~MOD10 존재, import 계층 위반 0(`import_layering.py`), 이동 커밋마다 AST 해시 동일, `sizing_recipe.py` 삭제, 레지스트리 이관 목적지 열 = 실제 위치 |
| 4 | DF마다 red-green, V8 도입(정본 실행 `fallback_events` 0), 사이징 대상 회로 실행과 전후 비교표, IC11 2레일 케이스 PASS, MG1 옛 키(계획 `supplies`, spec 스칼라 `vdd` 선언, metric 인자 `supply_nets`) 거부 test PASS, DF-27 VS 축 밖 픽스처 거부, U-27 재생성 LUT의 옛 격자점 값 대조 기록(다르면 원인 보고, 기준선 변경은 DEC-40 승인), U-30 PDK 상수 교체 전후 self-test·사이징 대상 회로 비교표(`min_finger_w` = difftap.2 출처 기록, 바뀌는 기준선·기대값은 DEC-40 승인) |
| 5 | 평가 입구 계수기로 동일 θ 재평가 0, θ* 기록이 다음 실행 시작점에 쓰임, 사이징 대상 회로 착지 전후표 |
| 6a | 기존 4개 회로 input·cascode·tail 멤버십이 declared와 일치, library 회로 전부(신규 세 회로 포함, 스펙 미선언 회로는 N3.2-2 기본 전달 뷰)의 출력노드·load·G_out 기여 소자·셀 판독·극점 노드·루프 탐지 결과가 ratified 대조표와 일치(대칭 쌍 없는 `pushpull_follower_buffer`의 비축약 결과 포함), 규칙 분기 발동표(분기별 발동·검증 발동 회로 수)와 shadow 대조 보고가 매 실행 생성, J 결론의 승인 기록, IC7 PASS(정지 케이스는 6c), IC11 3레일 케이스 PASS, MG2 옛 키 거부 test PASS, CD 셀·버퍼 묶음(DEC-63)·G_vgs 사이클 분류(DEC-64)·출력 방향 분류(DEC-65)·구동 종류(혼재 우선 규칙·값 의존 속성 포함)가 library 회로에서 ratified 대조표와 일치(기존 4개 회로 CD 0·버퍼 묶음 0·`kvl_branch`는 파일럿만), S1 관계 엣지 전부에 `domain`, 파일럿 M9a/M9b/M18a/M18b = pass·M2a/M3a = CG 판독이 ratified 대조표와 일치 |
| 6b | 봉인 위반 0(사이징 대상 회로), IC1·IC2·IC9·IC10 PASS, SC 거부 케이스 PASS, 사례 76.48 적발, 평가 오버헤드 전후, CD source 노드 W2 고정점 수렴 픽스처, `kvl_branch` 등식 위반·포화 여유 위반 픽스처 거부, 봉인 전 `ss`·`ls` 필드 쓰기 픽스처 거부(SC-a 전환기 writer 외 봉인 전 쓰기 거부), NFR-2 계측(같은 실행 같은 입력 해시 재계산 0, LRU 퇴출분 별도 집계, 계측 도구는 test-author 소유) |
| 6c | 결합 잔차 표(사이징 대상 회로), 블록·y 목록(library 회로, 스펙 미선언 회로는 기본 전달 뷰의 stage 목록), 검증 발동 0 분기 픽스처에서 탐색 전 `unsupported_rule_branch`, 달성 불가 픽스처(oracle (a): 목표 gain > 블록 이론 상한 합을 test가 다른 방법으로 계산)에서 탐색 전 INFEASIBLE_TARGET, IC4·IC6·IC8 PASS |
| 7a | gain 제약이 `gain_ss_db`로 판정, B21 재현 픽스처(6480조합 중 `gain_stages_sum` 변화 0이고 MNA 변화 최대인 두 점)에서 감도 게이트 FAIL, 평가 기록에 MNA-블록 잔차 필드(사이징 대상 회로), gain metric `verified_by` 유효(U-11이 SPICE를 7c로 두면 '검증 대기' 표시 + N5.4 명시), 임계값 재도출 기록, 버퍼 블록 국소 모델 이득·출력 임피던스가 test 쪽 독립 폐형식(gmb 포함)과 일치, `rout_ss_ohm` `verified_by`(없으면 검증 대기 표시), DF-28 근사 표시 |
| 7b | `gain_budget_db` 출력, 3층 할당이 다른 모델 전수탐색과 격자 분해능 안 일치, `sizing_spec.json` 이관 기존 4개 회로 equivalence, derived 필드마다 status·evidence·rule_hash, `driving_spec`이 있는 회로에서 극점 노드별 방향별 최대 전류 ≥ 슬루율 × C_k,total(부하 전류 선언 시 출력 포트 조건 포함), 입력-캐스코드 블록이 있는 사이징 대상 회로에서 그룹 좌표강하 결과가 블록 전수 결과와 격자 분해능 안 일치, 루프 뷰가 있는 회로의 루프 안정도 제약 미선언 픽스처에서 GB2 출구 게이트가 탐색 전 정지, 버퍼 대조 test 두 가지 -- (i) `sf_pushpull_output_opamp` 안 버퍼(M17~M22)를 버퍼 입력 Y 외 모든 외부 넷(전류원 게이트 N5·N13 포함)을 AC에서는 교류접지로 두고 DC에서는 N5·N13을 단독 `pushpull_follower_buffer` 봉인 해의 VPB1·VNB1 노드전압(W3 목표)으로, Y DC = agnd로 고정한 경계 조건에서(반대 방향 대조: 내장 해의 N5·N13 DC를 단독 회로 W3 목표로), 같은 버퍼 스펙의 단독 `pushpull_follower_buffer`와 사이징 결과·극점·출력 구동 규칙 판정이 같음(블록 국소 모델 검증) (ii) 전체 회로 사이징(J12-d에서 M17·M20이 K8로 ratify되면 K8·MT3로 계산해 정지하지 않는다. (a) 주 신호 분기로 ratify되면 (ii)는 `unsupported_rule_branch` 정지를 기록한다, N3.7)에서의 차이는 동일성 판정 없이 보고(N5·N13 바이어스 넷 신호 결합 크기, K2(N5·N13 `equal_vgs`)와 K8 주입을 분리 보고), U-23 실측표 제출, 커널 실행 순서(봉인 뒤 제약 판정) 검사, NFR-2 계측(3층 할당·역방향 제약 판정에서 같은 입력 해시 재계산 0, GB4 격자 표 필터 재사용과 필터 불가 재계산 사유 기록), 방향별 최대 전류 구조 판정(DEC-65)이 ratified 대조표와 일치, MG3 옛 키 거부 test PASS, wall-clock ≤ 선언 `wall_clock_budget_s`(파일럿 300 s. U-13에서 면적 예산을 선언하지 않으면 파일럿 판정은 Pareto 제시·정지와 사용자가 고른 점의 재실행으로) |
| 7c | SPICE 비교가 N3.8 허용오차 안, 같은 지문 재실행에서 아카이브 적중 > 0이고 θ* 목적값이 첫 실행 이하, IC1~IC11 전원 PASS, wall-clock ≤ 선언 `wall_clock_budget_s`(파일럿 300 s) |

### N6.3 공통 완료 조건

* auditor 판정 기록 PASS(N4.2 도입 표 기준), merge gate(EL4) 통과, 동작 변경 spec card마다 거부해야 할 입력의 test 존재.
* library 회로: 동작 변경 Phase(4 이후)는 DEC-47 대상 구분대로 측정하고 필요 없는 회로의 무동작을 증명한다. 동작 보존 Phase(1~3)는 실행 가능한 회로 전부에서 equivalence(I-C11 해소 전 two_stage·nmcnr, 스펙 미선언 신규 회로는 로드·구조 단계까지).
* 성능: Phase 4부터 매 Phase 보고 -- 조건 = 정본 spec, `SPECS[circuit]["slsqp_kwargs"]`, 파일럿 탐색 1회의 전체 wall-clock과 평가 시간 중앙값, 기계 정보. wall-clock 예산 게이트(DEC-34)는 7b·7c.

---

## N7. 공동분석과 사용자 결정

### N7.1 공동분석 J(회로 해석)

오케스트레이터가 connectivity 증거와 대조표를 제시하고 사용자가 확정한다. 결론은 승인 기록으로 남기고 `ratified`로 반영한다.

| ID | 항목 | 소비 Phase |
|---|---|---|
| J1 | replica bias(M57/M58/M63/M64)를 교류접지 예외로 끊을지(끊으면 CMFB 루프 부호가 부궤환으로 확정) | 6a |
| J2 | (AC구조) gate 넷이 diode 연결 단자인 소자의 gate->drain을 같은 stage(미러)로 볼지(nmcnr M201->M203/M204 경계) | 6a |
| J3 | (J3-ac, 6a: pass 묶음·stage1 출력노드·병렬 CS 한 블록 / J3-dc, 7b: `kvl_branch` 등식(DEC-64 탐지 결과 대조)·정지전류(θ 전류 변수)·루프 종속 gm_id 소자·방향별 최대 전류(`ls`, DEC-65)) class-AB M9a/M9b/M18a/M18b/M8/M17의 역할. floating battery(M9a/M9b: Vop1↔Vg15, M18a/M18b: Vom1↔Vg25)가 pass 구성으로 신호를 넘길 때 stage1 출력노드: 기본안은 Vop1(캐스코드 사슬 끝)이다(근거: N3.7 입력 기준 규칙과 J10 기본안 예외로 pass 구간 Vop1→Vg15가 뒤 블록 노드 집합에 들어가므로, Vg15로 두면 두 블록의 노드 집합이 겹친다). 출력노드와 정지전류 규칙은 6a-2 공동분석 ratify 대상이다: pass 묶음 내부 왕복은 루프로 세지 않고(N3.2-2), 같은 출력노드로 합류하는 병렬 CS(M15/M16)는 M15 gate Vg15가 pass(M9a/M9b)로 Vop1과 이어진 블록 내부 노드라 한 블록 안의 병렬 셀이다(N3.7 입력 기준 규칙) | 6a, 7b |
| J4 | M7(gate Vcmfb)을 tail로 볼지 CMFB 구동소자로 볼지 | 6a |
| J5 | 5T 미러부하·NMCNR 폴딩 미러를 기모드 축약에서 다루는 법(축약 뷰가 출력노드를 잃는 경우 -- 비축약 전달 뷰를 쓸지 포함) | 6a |
| J6 | 출력노드 부하 귀속: 파일럿 M18a/M19/M18b를 stage1 부하(G_out)로, nmcnr M104/M106을 해당 stage 부하로 넣을지 | 6a(ratify), 7a(gain metric이 소비) |
| J7 | Cc–Rz 직렬 루프 극성 판정 | 6a(극성 ratify), 7b(보상 규칙이 소비) |
| J8 | `fold_group`, `shared_gm_id_groups`, 노드를 공유하지 않는 `budget_reference_device` 4건(M61, M68, M38, two_stage M4), `voltage_divider`/`floating_current_source`/`bias_replica` 의도(단서: vsb 오류 소자 M38/M60/M61/M68이 모두 `budget_reference_device` 보유) | 6b |
| J9 | folded·nmcnr `ports`, nmcnr·two_stage `passive_elements` 누락분 | 6a(ports), 7b(passive) |
| J10 | follower(CD) 또는 pass로 끝나는 경로를 독립 블록으로 둘지 앞 stage 블록에 흡수할지(AC구조 결정: 블록 경계와 극점 노드 목록. 레벨 시프트·헤드룸(DC)은 블록 경계와 무관하게 GB7이 CD source 노드 W2로 계산한다). folded M8(gate Vg7 -> source Vg10) 판정 포함. 기본안: 독립 버퍼 블록(극점·보상 문헌이 출력 버퍼를 한 단으로 센다, DEC-57), 경계 절차는 DEC-63. 단 병렬 셀 입력을 잇는 pass 구간은 뒤 블록에 흡수한다(N3.7 입력 기준 규칙, 이 예외도 기본안이며 6a-2에서 ratify). 6a-2에서 ratify | 6a |
| J11 | 루프 뷰: 회로마다 루프 탐지 결과(루프 목록, 루프에만 속한 셀), 끊는 점, 루프 뷰의 셀 판독표·stage 경계·극점 노드를 대조표로 ratify. 파일럿 대조 내용: CMFB 루프(N3.2-3 예시 판독), M58 전류 분할(J1과 함께), M7 이중 역할(J4와 함께) | 6a |
| J12 | 신규 library 회로의 ratified 대조표와 symmetry 판정(항목마다 영역 표시): `sf_pushpull_output_opamp`(입력 차동쌍 M1/M2(AC구조), 저항 자기바이어스 캐스코드 미러 3조 R1a/R1b/R1c(DC 루프 + 국소 되먹임), 고임피던스 노드 Y의 Cc–agnd(Miller 아님, 보상 분류, AC), 출력 캐스코드 M9/M10·M15/M16, 버퍼 M17~M22가 `pushpull_follower_buffer`와 같은 구조인지(AC구조), IBias 이상 전류원(DC), 레일 vdd/vss/agnd(DC)), `two_stage_ota_sf`(M1~M7 대칭 후보, M8 follower 버퍼 블록(AC구조), Cc Miller 루프의 보상 분류(AC), M1/M2 body effect(DC vsb + `ss` gmb)), `pushpull_follower_buffer`(대칭 쌍 없음, 단일 입력 전달 뷰, 팔로워 2단 연쇄 셀·버퍼 블록(AC구조), 두 경로가 합류하는 vout, 정지전류 `kvl_branch` 루프 VGS4 + VSG3 = VGS1 + VSG2(DC), 부하 CL vout–agnd) | 6a(구조), 7b(정지전류) |
| J12-a | (AC구조) 버퍼 블록 경계 3건(DEC-63 측정 기대값): `pushpull_follower_buffer` {vin; A, B, vout}, `sf_pushpull_output_opamp` {Y; N17, N20, vout}, `two_stage_ota_sf` {OUT; vout}와 앞 이득 블록 출력노드(OUT, Y)와의 경계 | 6a |
| J12-b | (AC구조) A·B·N17·N20의 구동 종류 = 전압 구동(용어집 혼재 우선 규칙 기본안), 값 의존 노드(`sf_pushpull_output_opamp` N5 등)의 구동 종류(`structure.json`에 기록)와 M5/M6(단독 버퍼)·M17/M20(내장 버퍼)의 load 귀속 | 6a |
| J12-c | (DC) G_vgs 사이클 판독·분류(DEC-64): 두 push-pull 루프의 멤버·부호(`VGS4 + VSG3 = VGS1 + VSG2` 형태), 파일럿 레일 경유 4사이클이 J3 정지전류 루프와 같은지(DEC-15 M11a/M11b/M20a/M20b 대조), 파일럿 포트 차 루프 {M1a, M1b, M4a, M4b}(v1)를 제약에서 뺄지 | 6a |
| J12-d | (AC구조 + DC 역할) M17/M20이 K8 측면 주입인지 (a) 주 신호 분기인지(기본안 K8, 합류 노드 조건은 N3.7). 원문 "bias currents through M18 and M19 vary with the signal"의 해석 | 6a |
| J12-e | (AC구조 판정, `ls` 값) 출력 방향 분류(DEC-65): `two_stage_ota_sf` vout = class-A(흡수 바이어스 제한), `two_stage_ota` OUT = class-A(M6 σ / M7 β), 두 push-pull vout = push-pull, 파일럿 Vop/Vom = push-pull CS(J3와 함께) | 6a |
| J12-f | (DC) 루프 종속 gm_id 소자 선택(후보 M1/M2, M21/M22, 전류는 θ)과 합류 노드 KCL `I_M1 = I_M2`(출력 DC 부하 전류 없음 전제)의 성립 | 6a |
| J12-g | (AC) `two_stage_ota_sf`: Cc가 O1–OUT이라 follower M8은 Miller 루프 밖이고 vout이 별도 극점 노드인지(GB5 입력) | 6a |
| J12-h | (AC구조, 미검증 관찰) `sf_pushpull_output_opamp` M6(g = N5, d = N56)·M5(s = N56, d = N5) 복합 diode: 방향 신호 그래프에서 능동 셀 둘·수동소자 없이 닫히는 폐경로라 루프 분류 (2) 예시("능동 셀 하나와 저항")와 맞지 않아 (4)로 떨어질 수 있다. M7/M8·M13/M14도 같은 형태. J11 대조표에서 확인 | 6a |

### N7.2 사용자 결정 U

기본안은 원칙에서 나온 제안이며, 확정 전에는 구현하지 않는다.

| ID | 결정 | 기본안 | 필요 시점 |
|---|---|---|---|
| U-01 | stick_diagram Test 16의 의도(test가 틀렸나 대상이 틀렸나) | 오케스트레이터가 원인 대조표 제시 | Phase 1 |
| U-02 | 레지스트리 등급 D 목록과 probe 삭제 11개의 항목별 삭제/배선 | 제안표 일괄 승인 | Phase 2 |
| U-03 | 추적되지 않는 `workspaces/` 스크래치 스크립트가 `sizing_recipe.py` 삭제로 깨지는 것을 허용할지 | 허용(추적 파일만 갱신). 근거: WP-01의 배선 대상은 저장소에 추적되는 파일 | Phase 3 |
| U-04 | 픽스처와 정본 spec의 구분 | spec에 `origin: canonical | fixture` 필수, 픽스처는 유도 임계값을 읽지 않음 | Phase 4 |
| U-05 | 비단조 곡선에서 이분 역산의 처리 | 단조 구간별 근을 모두 돌려주고 호출자가 선택 규칙을 명시(DEC-11 확장) | Phase 4 |
| U-06 | J1~J12 공동분석 + 구조 개념 정본(diode 이웃 포함 여부, 미러 그룹 키, diffpair/tail 유도) | 대조표로 항목별 확정 | 6a-2(J1·J2·J3-ac·J4~J7, J9 ports, J10, J11, J12·J12-a~h, 구조 정본) / 6b(J8) / 7b(J3-dc 정지전류, J9 passive) |
| U-07 | 전력 정의 변경으로 바뀌는 기대값들을 한 승인으로 묶어도 되는지 | 변경 목록을 첨부한 한 승인 | 7a |
| U-08 | folded·nmcnr·two_stage `ports`(two_stage 출력 포함) | connectivity 제안표 확인 | 6a |
| U-09 | two_stage stage1_out 분리·nmcnr stage2_diode_ref 이월을 언제 풀지 | Phase 4에서 DF와 함께. 근거: 기존 4개 회로 측정(N6.3)이 Phase 4부터 동작 변경 판정에 필요 | Phase 4 |
| U-10 | 목적함수 전력 정의(`sum_current` / `_metric_supply_current`, DC) | 사이징 대상 회로 비교표 제시. 스택 중복 계상 배율이 가지마다 다른 회로(예: `two_stage_ota_sf` 입력 가지(공유 tail 포함) 대 출력 가지)와 배율이 균일해 최적점이 바뀌지 않는 회로(`pushpull_follower_buffer`)를 구분해 넣는다 | 7a |
| U-11 | `verified_by` 적용 순서 | SPICE AC gain 대조를 7a로 당겨 gain 제약에 적용 | 7a |
| U-12 | 단일단(보상 없음) 회로의 gm 출처 | `gm_1 ≥ 2π·gbw_target_hz·C_out,total`(봉인 후보마다 θ 제약, DEC-70, N3.7. C_out,total = 봉인점 출력노드 용량 + 부하 요소 값. GBW는 개루프 양이라 되먹임 인자와 무관) | 7b |
| U-13 | 면적 정의와 파일럿 면적 예산 | 예산 미선언 시 DEC-07대로 Pareto 제시 후 정지 | 7b |
| U-14 | gain 폭이 분해능 이하인 공유 VGS 그룹(pmos:Vcmfb)의 선택 기준 | 전력 기준으로 고르고 기록 | 7b |
| U-15 | hook 입력에 역할 필드(`agent_type`)가 없을 때의 역할 판정 방식. **실측 후 결정(2026-09-14 사용자)**: 부트스트랩 ② 실측 기록(PreToolUse·PostToolUse·SubagentStop 각각에서 `agent_type`·`agent_id`·`cwd` 존재 여부, 세 역할 + 메인 세션)을 제시하고 고른다. 필드가 있으면 이 결정은 필요 없다 | 선택지: A. 호출자 `cwd`가 속한 worktree(`../wt/<id>-<role>`)로 판정(EL1 약화분은 EL3·EL4와 Bash `git -C`·다른 worktree 경로 거부로 보완) / B. 역할마다 별도 Claude 세션·설정 / C. EL1은 메인 세션 규칙만, 역할 구분은 EL3·EL4 | 0.5(실측 직후) |
| U-16 | topology.json 메타데이터(role·ports·passive) 반영 주체. **확정(2026-09-14 사용자 "A로 해")**: 오케스트레이터가 사용자 확인 후 반영 | 조건: 사용자가 확인한 표의 항목만 반영, connectivity(넷리스트·passive·이상원 넷)는 WP-08대로 모았다가 일괄 반영하고 net 표 재출력으로 대조 / 승인 기록 `.ai/approvals/<id>.md` + 커밋 `Role: doc`, EL4는 승인 기록 없는 topology diff를 거부 / topology 변경은 S0 지문을 바꿔 `ratified`를 `review_needed`로 되돌림 / topology 변경으로 바뀌는 test 기대값은 V5 승인 대상. 근거: WP-07, WP-08, DEC-35 | 확정 |
| U-17 | `mismatch_sigma_mV = 5.0`의 출처(시스템 레벨 요구) | 사용자가 출처를 선언 | 6a |
| U-18 | 기준 약화 개별 승인 | 매 건 승인 기록 | 상시 |
| U-19 | `gain_db >= 54`(현 이름, 7a부터 `gain_ss_db`)를 전체회로 gain 기준 bisection으로 재도출해 교체할지 | 재도출값 제시 후 승인 | 7a |
| U-20 | `stack_headroom_slack_v`를 봉인 항목으로 흡수할지 metric 제약으로 남길지(I-C10) | 봉인 항목 1·5가 같은 사실을 보므로 metric 삭제 | 6b |
| U-21 | 선언 L theta(`L_cascode`, `L_stage2out_*`)를 L 동치류 theta로 대체하고 삭제할지 | DEC-18에 따라 삭제 | 7b |
| U-22 | 순수 follower(drain이 레일, source가 출력)가 있는 회로를 library에 추가해 CD 규칙을 실제 회로로 측정할지 | **확정(2026-09-15, 사용자 확정 넷 표로 추가)**: `two_stage_ota_sf`(M8), `pushpull_follower_buffer`(M1~M4). 6a에서 CD 분류·버퍼 블록·J10을 이 회로로 측정한다 | 확정 |
| U-23 | 입력-캐스코드 블록의 L을 같게 맞추도록 강제하는 규칙을 복원할지(DEC-04) | 실측 후 결정. 캐스코드가 있는 회로(파일럿, folded, nmcnr)에서 (A) 독립 L과 (B) 입력-캐스코드 L 동일 강제를 같은 spec·탐색 인자로 돌려 비교: 평가 수(불필요한 반복), 목적값(전력), 활성 제약 여유(스펙 오버 여부, NFR-5), 면적, 레이아웃(행 안 L 종류 수, finger 배정 성공 여부, finger 합·box 비율 -- 입력과 캐스코드가 같은 물리 행인 회로는 파일럿뿐이므로 레이아웃 비교는 파일럿에서만 판정하고 나머지 회로는 평가 수·목적값·제약 여유만 비교). 비교군에 (C) LR5 격자 확장 규칙을 쓴 A와 (D) VDS 균등 고정 A를 함께 둔다. 조건: 목표 gain은 블록 gain 상한 이하에서 4점 이상, W 한계 경계 gm_id와 한 칸 아래를 포함, 제약마다 활성/비활성 구분, 지표에 tail 포화 여유·`parasitic_pm_ss_deg`·미러 전류비 오차 포함. B가 finger 배정에 실패하면 기각. B가 평가 수를 줄이면서 목적값·제약 여유·면적이 A와 격자 분해능 안에서 같거나 나으면 B를 제안, 아니면 A 유지. 선측정(블록 국소 모델, tt 한 코너, tail 포화·gmb 미포함): 파일럿 stage1에서 B는 A 대비 면적 +2.8~5.9% | 7b(실측 직후) |
| U-24 | 루프 뷰의 안정도·대역폭을 제약으로 선언할지와 그 값(예: 루프 PM 하한, 주 전달 경로 대비 대역폭). 파일럿 옛 `N_cmfb_bw` 휴리스틱 같은 근거 없는 배수는 쓰지 않는다 | 6a~7a: 루프 뷰의 루프 이득·극점을 metric으로 보고만 하고 제약으로 걸지 않는다(보고 시 명시). 7b부터: 루프 뷰가 있는 회로에서 루프 안정도 제약이 선언되지 않으면 GB2 출구 게이트가 탐색 전에 정지한다 | 7b 착수 전 |
| U-25 | 신규 library 회로의 사이징 스펙 | **확정(2026-09-15 사용자, topology 문서 필드 `_declared_target_spec`(현 파일 이름 `_paper_target_spec`, MG0에서 변경)에 기록 -- 문서 전용)**: `sf_pushpull_output_opamp` = `supplies_v` vdd 1.8 / vss 0 / agnd 0.9 V, IBias `value_dc_amp` 50 µA, CL 1 pF, Av(`gain_ss_db`) ≥ 65 dB, GB ≥ 60 MHz, Rout(`rout_ss_ohm`, 소신호 저주파 개루프, DEC-66) ≤ 1 kΩ, R1·Cc는 유도. `pushpull_follower_buffer` = 같은 레일, vin DC = agnd(`input_dc_net`), CL 1 pF(vout–agnd), Rout(`rout_ss_ohm`) ≤ 1 kΩ, 목적 최소 전력, 버퍼 대역폭은 보고만(사이징 대상에서 빼지 않는다). `two_stage_ota_sf` = two_stage_ota 스펙 정본(`run_harness._spec_two_stage_ota`)과 `two_stage_ota.topology.json` sizing_roles의 제약·목적을 참조로 상속하고, 추가는 CL 3 pF(정본 값)를 팔로워 출력 vout에, Rout(`rout_ss_ohm`) ≤ 1 kΩ(Allen L26 버퍼 기준, 도면 p.26-5에는 값 없음) 두 가지. 상속한 gain metric의 감지 노드는 vout(팔로워 감쇠 포함). 잔여 결정 없음. `sf_pushpull_output_opamp` 전체 회로 사이징의 M17·M20 측면 주입은 K8(N3.7)로 계산하며 J12에서 ratify한다 | 실행 `SPECS` 이관: agnd 레일 두 회로는 DEC-60 구현 뒤, `two_stage_ota_sf`는 사이징 착수 시. 이관 전에는 구조 유도(6a)에만 넣는다 |
| U-26 | 레일·예산 선언 확정: (a) 기존 4개 회로의 `supply_nets`·`supplies_v{넷: 전압}`(nmcnr은 **확정(2026-09-15 사용자 "1.8로 고쳐", "+-0.9로 고치고")**: sky130 재설계 전원 `supplies_v{vdd: 0.9, vss: −0.9}`. 옛 `vdd` 2.0은 논문 공정(AMS 0.8 µm) ±1 V를 폭으로 옮긴 미검증 추정이라 폐기. 실행 spec은 스칼라 `vdd: 1.8`로 원점 이동 동등(IC11), 분할 레일 실행은 DEC-60 구현 뒤) (b) 신규 회로의 `supply_nets`(connectivity, 사용자 작성) (c) 사이징 대상 회로의 `wall_clock_budget_s` | (a) connectivity의 레일 넷과 `SPECS[circuit]["vdd"]`로 제안표를 만들어 사용자 확인, 확정 전에는 DEC-60 전환기·기본 해석 (b) 신규 회로 넷 표에서 제안(`sf_pushpull_output_opamp`·`pushpull_follower_buffer` = vdd·vss·agnd, `two_stage_ota_sf` = vdd·gnd) (c) 파일럿 선언값 300 s(5분)를 모든 사이징 대상 회로에 같게 적용하고 사용자가 회로별로 바꿀 수 있다 | (a) Phase 4 (b) 6a(IC11 3레일 케이스 입력) (c) 6b |
| U-27 | LUT 재생성: VS 축 0~1.8 V, CGS·CGB 열 추가 | **확정(2026-09-15 사용자 "권고대로")**: 진행. 현 표본 `sky130_nfet_pfet_lut_sample.npz`는 VS 축 0~0.8 V 5점이고 CGS·CGB 열이 없다(실측). 담당 Phase 4(`40-defect-fixes`, DF-27과 같은 design). 선행 조건: (1) DF-27 축 커버리지 게이트 red test가 옛 표본 LUT에서 VS 축 밖 입력을 거부함을 먼저 확인 (2) LUT 생성 도구(`sky130_lut_sweep.py`)·ngspice·모델 경로(LUT 생성 메타) 확인 (3) 재생성 LUT의 옛 격자점 값을 옛 표본과 대조(다르면 원인 보고, 바뀌는 기준선은 DEC-40 승인) (4) 새 LUT 해시로 S0·실패 캐시 지문이 바뀜을 기록. CGS·CGB 열의 소비(스탬프)는 7a(DF-28). VS 축 상한 = library 회로 `supplies_v` 최대 전위차에서 유도한 1.8 V(LR3 유도와 일치, 2026-09-15 확정) | Phase 4 |
| U-28 | follower 벌크 선언 | **확정(2026-09-15)**: 기본 규칙(DEC-61: nmos = 가장 낮은 전위 레일, pmos = 가장 높은 전위 레일)으로 충분하고, `bulk`는 기본과 다른 연결이 필요할 때만 선언한다(connectivity라 사용자 작성) | 확정 |
| U-29 | 출력 스윙·버퍼 입력 범위 제약 | **확정(2026-09-15)**: 스펙에 선언된 경우만 제약으로 걸고, 아니면 N3.8 스윙·입력 범위 metric을 보고만 한다(I-A6) | 확정 |
| U-30 | `two_stage_ota`만 `min_finger_w = 0.1e-6`(나머지 세 회로 1e-6)인 것이 의도인지 | **닫힘(2026-09-15 사용자 "2번은 phase4에서 해.", 2026-09-15 대화)**: 의도가 아닌 오류다. sky130 공식 periphery rules: difftap.2 최소 채널 폭 0.420 µm(표준셀 밖), difftap.2b 0.360 µm(표준셀 안), poly.1a 0.150 µm, poly.1b lvtn pfet L ≥ 0.350 µm. 로컬 bins.csv(nfet W ≥ 0.36, pfet W ≥ 0.42)는 모델 유효 범위이지 DRC가 아니다. 나머지 회로 1 µm·`W_bounds` 하한 1 µm는 근거가 없다. Phase 4 항목: PDK 상수를 한 곳에 출처 규칙 번호와 함께 선언, `min_finger_w` = difftap.2, `W_bounds` 하한은 `min_finger_w`에서 유도, 교체 전후 self-test·사이징 비교. 출처 기록 `skills/analog-gmid-design/references/lut-generation-checklist.md`(288행 참고) | Phase 4 |
| U-31 | 부하 요소 CL 추가(`folded_cascode`·`nmcnr_amplifier`·`two_stage_ota`) | **닫힘(2026-09-15)**: 7b에서 수동소자 값을 `element_values`로 이관할 때 U-08 포트 선언 확정·영향 test와 함께 추가한다(connectivity라 사용자 확인). 값: `two_stage_ota` = CL 3 pF@OUT(실행 spec `CL: 3e-12`) / `folded_cascode` = CL 1 pF 스펙 확정(사용자 "CL은 load cap이잖아. 1pF이면 그냥 스펙으로 봐도 돼."), 실행 spec 반영도 7b / `nmcnr_amplifier` = 실행 spec `CL: 1e-10`, 출력 넷 `Vout`은 추정(`ports` 미선언, U-08에서 확정) | 7b |
| U-32 | 명명 규칙의 단위 접미사를 하네스 탐색 설정 키(`L_candidates`, `VDS_candidates`, `min_vds_by_role` 등)와 PDK 상수 키에도 적용할지 | 사용자 결정 대상(DEC-68 확정 범위는 사람이 선언하는 값). 기본안 없음 -- 7b 착수 전에 선택지(사람 선언 값만 / 탐색 설정·PDK 키까지)와 변경 비용을 제시한다 | 7b 착수 전 |

---

## N8. 위험과 대응

| 위험 | 대응 |
|---|---|
| stage 분할의 회로 해석 오판 | 6a는 shadow로 대조만, `review_needed` 잔존 시 6c에서 정지, J 공동분석으로 ratify |
| 3층 할당 비수렴·국소해 | 종료 규칙과 유한 격자 상한(N3.7), 분지별 시작, 다른 모델 전수탐색 대조 |
| 노드전압 정본 전환(6b)이 착지를 바꿈 | 봉인 위반이 없던 소자의 값만 옛 경로와 동등 단언하고, 달라진 소자는 writer 티어와 함께 기록, 사이징 대상 회로 전후표 |
| hook 입력에 역할 필드가 없음 | 0.5 첫 단계에서 실측, 대체 판정 U-15 |
| hook 오탐이 RTL agent·일반 작업을 막음 | 판정 범위를 gmid 역할과 경로표로 한정, 공격 시나리오 11 |
| 분리로 못 막는 은폐(자기참조 oracle, 거짓 기준값, 폴백) | V3·V4·V5·V6·V8·V9 |
| 파일 이동 중 회귀 | test 분리 먼저, 이동 전용 커밋, AST 해시 동일 증명 |
| 배분값·목표값을 지어냄(사고4) | `gain_budget_db`는 출력, 제약값 출처 필수 |
| 전체회로 MNA 반복으로 wall-clock 예산 초과 | `build_ac_network` 1회 조립, 봉인 스냅샷당 전역 metric 1회, S2 memo |
| SPICE 모델·ngspice 환경 부재 | SPICE를 처음 쓰는 Phase(U-11에 따라 7a 또는 7c)의 design 첫 단계에서 모델 경로(LUT 생성 메타)와 실행을 확인 |
| S3 아카이브 디스크 증가 | append-only, 크기를 매 실행 보고 |
| 사이징↔레이아웃 반복 중 소자 소실(사고16) | MOD8 루프 매 반복 커버리지 재검증(LR9), 이름 전역 유일(IC3) |
| 스키마 이름 변경이 동작을 바꾸거나 옛 이름이 조용히 남음 | 단계마다 옛 키 거부 게이트(DEC-69), 키 매핑 후 수치 동일 equivalence, 값 문자열 안 옛 이름 검사, MG2를 6a 전에 끝내 S0 해시 입력을 먼저 고정 |
| LUT 재생성(U-27)이 기존 기준선을 바꿈 | 옛 격자점 대조, 바뀐 기준선은 DEC-40 승인, 지문 변경 기록 |

---

## N9. design 문서 작성 지침

### N9.1 문서 목록

경로: `docs/02-design/features/gain-budget-gmid-sizing.<번호>-<slug>.design.md`

| 문서 | 반드시 담을 것 |
|---|---|
| `00-common` | 용어집 최종본(N0.4), 영역 표기 규약(DEC-67), 명명 규칙과 옛 키 거부 게이트 공통 형식(DEC-68·69), 실패 규약 클래스·필드(N3.14), 판정 기록·승인 기록 JSON/MD 스키마(N3.12.5), V 도입 표(N4.2), IC 담당 표(N4.1), 성능 측정 명령(N6.3), 무동작 판정 방법 |
| `05-role-separation` | 쓰기 경로표를 glob 목록으로(N3.12.2), hook 입력 실측 절차와 U-15 분기, 설치 명령과 순서(N3.12.6), 트레일러·경로 분류 규칙(소스/test/도구/데이터/문서), V3·V4·V5·V6·V7 알고리즘, interface card 생성기, spec card·dispute 양식, worktree 명령 시퀀스(N3.12.3), EL2 무시 목록, 공격 11 + 사례 5 재생 절차와 기대 메시지, agent 정의 3개 |
| `10-test-separation` | TS0 원인 대조, TS1 추출 스크립트와 두 커밋 순서, seed별 stdout 비교 명령, TS2 섹션→test 매핑표와 fixture 목록, 셔플 옵션 구현, TS3 AST 검사, TS5 퇴역 절차, TS7 xfail 선언 목록(IC별 담당 Phase) |
| `20-dead-code-dup` | U-02 제안표(항목, 호출부 0 증거, 삭제 영향, 배선 시 소비자), DUP별 차등 test 설계, TS6 승격·삭제·이동 목록 |
| `30-module-split` | 레지스트리 목적지 열에서 생성한 함수→모듈 이관표, 계산된 import 그래프, `import_layering.py` 규칙, AST 해시 증명 명령, shim 재수출 목록 생성법, 추적 파일 호출부 목록 |
| `40-defect-fixes` | DF별 red 형태(행동 test / lint)와 수정 범위, N3.14 실패 클래스 도입, tol_V 함수 선도입, U-04·U-05 반영, `fallback_events` 스키마와 계측 지점 전수, exit code, I-C11 해소 설계, `supply_nets`·`supplies_v` 기반 레일 판정(DF-19·DF-26)·vsb(DF-24)·IC11, MG1(`vdd` 유도 함수, metric 인자 `supply_nets` 정리, 옛 키 거부), DF-27 축 커버리지 게이트, U-27 LUT 재생성 절차·대조, U-30 PDK 상수 한 곳 선언(규칙 번호 출처·`W_bounds` 하한 유도)과 교체 전후 비교 |
| `50-failure-cache` | 실패 캐시 키·저장, margin 정규화식, 시작점 선택 규칙, S3 레코드 v1 스키마와 위치, 계수기 |
| `6a-structure-stage` | S0 해시 구성, S1 스키마(N3.3), 교류접지 3분류, 여기 뷰 2종(전달·루프) 수집, 셀 우선순위, 대칭 축약과 비축약 대조, SP1 알고리즘(0-1 BFS), 루프 탐지·끊는 점 규칙, J11 대조표, 소자 구성 분류와 출력노드·임피던스 등급 판정, 모드 수집, 피드백 극성, status 전이 구현, `structure.json` 형식, shadow 대조 보고 형식, J 대조표 양식, ports 제안표, 규칙 분기 목록(정본)과 발동표 형식·`unsupported_rule_branch` 판정, `supply_nets`·`supplies_v`·`bulk` 로드(DEC-60·61), 루프 분류 (0)~(4)·바이어스 SCC, J12(J12-a~h) 대조표, MG2 이름 변경과 옛 키 거부, 소자 DC 역할 유도, 구동 종류(혼재 우선 규칙·값 의존 속성), S1 엣지 `domain`, G_vgs 사이클 탐지·분류(DEC-64), 버퍼 묶음 R(u)(DEC-63), 출력 방향 구조 분류(DEC-65), 수동소자 엣지 비용 |
| `6b-node-voltage-seal` | S2 필드 스키마, SC-a 권한표(필드 × W0~W4), W3 소스 필드, 계산 블록 입출력 선언과 유도 DAG, tol_V·tol_I·반복 상한 구현, 봉인 항목 구현, 버전 카운터, LRU 상한 계산, IC2 섞기 대상, 동등 단언 범위, J8 결론 반영, U-20 반영, I-A6 헤드룸 하한 여부 판정, VDsat 유도 규칙(DF-25, LUT (ID, gds, VDS) 곡선), 봉인 항목 7·8, S2 `dc`/`ss`/`ls` 스키마, CD source W2 블록, 평가 커널 계산 블록 분할(보상 블록 순서 유지는 7b 재배열 전까지), 중복 계산 방지 구체안(캐시 키 구성, 계산 블록 분할 단위, 무효화 조건, 계측 형식) |
| `6c-coupling-achievability` | 결합 잔차 측정 절차, 블록·y 추출 규칙(K1~K4), LUT 곡선 검사→해법 매핑, 블록 gain 상한 계산, DOF 변수·등식 표와 수치 rank, `DofReport`, 달성 불가 픽스처와 oracle |
| `7a-gain-metric` | 회로별 gain metric 이관표, 블록 국소 소신호 모델(경계 조건·스탬프)과 gmb 유도 식, 블록 속성(`rout_ss_ohm` DEC-66, 경계 부하 = 다음 블록 입력 넷 어드미턴스 DEC-63) 계산, 스윙·입력 범위 metric, DF-28 CGS·CGB 스탬프와 근사 표시, 잔차 계산, 감도 게이트 섭동 방향·ε 계산, MT 분류 규칙, 전력 정의(U-10) 반영, `verified_by`와 SPICE AC gain 대조(U-11), bisection 모드(N3.13)와 U-19 |
| `7b-compensation-allocation` | `sizing_spec.json` v5 스키마·로더·이관·topology.json 필드 제거 절차, GB5 규칙(단일단 U-12, 3단, class-AB J3), 내층 DP 상태·bin 해상도, 중층 좌표강하 종료, 외층 인자, 면적·Pareto(U-13), U-14, `value_dc_amp` 소비, MOD8 수렴 루프, 다른 모델 대조 test, U-21 반영, 슬루율 필드 명칭(DEC-53 규약 인용), 출력 구동 규칙(DEC-58)과 극점 노드별 C_k,total·방향별 최대 전류 계산(DEC-65 β/σ/κ), DEC-70 θ 제약과 평가 커널 재배열, 보상 수동소자의 DC 전류 경로 판정, 중복 계산 방지 구체안(캐시 키 구성, 계산 블록 분할 단위, 무효화 조건, 계측 형식, GB4 격자 표 필터 재사용), MG3 이름 변경·CL 요소 추가(U-31), U-32 결정 반영, 루프 안정도 제약 게이트(U-24), `wall_clock_budget_s`, 강결합 셀 그룹 유도 규칙, U-23 실측 설계(비교 조건·회로·지표), 단독 버퍼 대 opamp 내장 버퍼(M17~M22) 대조 test 설계(경계 조건 동일성 (i), 전체 회로 차이 보고 (ii)) |
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

topology.json(connectivity, `ports`, `passive_elements`, `supply_nets`, 필요 시 소자 `bulk` -- 사용자 확인, WP-07·WP-08·U-16) -> GB1·GB2 유도, 규칙 분기 발동표, 공동분석(ratified 대조표) -> `sizing_spec.json` human 섹션(`supplies_v` 포함, 선언되면 사이징 대상 회로) -> `SPECS` 데이터 항목 -> regression에 회로 추가 후 기존 회로 무동작 증명. 코드 추가가 필요하면 멈추고 DF로 등록한다(DEC-62).

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
| §7.4 | DEC-02·DEC-03·DEC-04(2026-09-14 재정의), N3.1 |
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
| 표 A A01~A74 | A01→DEC-01, A02→DEC-04(2026-09-14 재정의: 동시 결정 철회), A03→DEC-02, A04·A05→DEC-03, A06→DEC-05, A07→DEC-06, A08·A09→DEC-07, A10→NFR-1, A11→WP-02, A12→NFR-2, A13→NFR-3, A14→DEC-48, A15→DEC-08, A16→WP-04, A17→DEC-09, A18→DEC-10, A19→DEC-11, A20→DEC-12, A21→DEC-13, A22→DEC-14, A23→DEC-15, A24→DEC-56, A25→DEC-16, A26→LR1~LR9, A27·A29→DEC-17, A28·A30→DEC-18, A31→DEC-19, A32→DEC-20, A33→DEC-21, A34→DEC-22, A35→DEC-23, A36→DEC-24, A37·A38→DEC-55, A39→DEC-25, A40→DEC-31, A41→DEC-26, A42→DEC-27, A43→DEC-28, A44→DEC-29, A45·A62→DEC-01, A46→DEC-30, A47·A48→DEC-46, A49→WP-14, A50→DEC-42, A51→DEC-32, A52→N6.1, A53→DEC-34, A54→DEC-35, A55→U-10, A56→U-02, A57→U-06, A58→DEC-36, A59→DEC-37, A60→DEC-37~40, A61→DEC-41, A63→N3.1 RC, A64→DEC-50, A65→DEC-51, A66→U-09, A67→이력, A68→DEC-54, A69→DEC-52, A70→DEC-18·DEC-19(knee 출발은 LR5), A71→DEC-53, A72→DEC-05·J6, A73→DEC-49, A74→DEC-47 |
| D1~D15 | D1→DEC-31, D2→DEC-32, D3→N6.1, D4→DEC-34, D5→DEC-35, D6→U-10, D7→U-02, D8→U-06, D9→DEC-36, D10·D11→DEC-37, D12→DEC-38, D13→DEC-39, D14→DEC-40, D15→DEC-41 |
| 표 B B01~B21 | B01~B18→WP-01~WP-18, B19→해당 없음, B20→DEC-51, B21→WP-20 |
| 이슈 A/B/G/C (§10) | 열림은 I-A* / I-B* / I-G* / I-C*(N5.3). v5.0에서 닫음: I-G3·I-G7(N1.2), I-G8(N9.3), I-C3(DEC-47), I-C5(WP-14), I-C7(N3.15), I-C9(원표 이력), I-A9(N3.8). DF로 통합: I-A3→DF-16, I-A4→DF-05, I-B7→DF-02, I-B9→DF-01. 신설: I-A10(folded `omega_c` 선측정), I-A11(크로스오버 해석 차이), I-A12(pitch overhead 0), I-A13(dummy·LDE 미반영), I-B22(다중 diff pair 오프셋), I-C10(옛 §10.5a-8, U-20), I-C11(옛 A66, U-09), I-A14(two_stage_ota 입력 극성, v5.9 안에서 닫힘 -- 이력 5.9), I-A15(knee gm_id 구간) |
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
| 결함 #1~#21 | DF-01~DF-21(DF-22~DF-28 신설) |
| (옛 번호 없음) | 신설: DEC-59~DEC-70, FR-9, IC11, K7, K8, MG0~MG3(N3.16), 봉인 항목 7·8, J12(J12-a~h), U-25~U-32. |
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
