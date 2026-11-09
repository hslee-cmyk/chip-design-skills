# 사용자 결정 대기 통합 (PENDING_USER_DECISIONS) -- 2026-10-07

- 목적: 지금까지 문서 9개에 흩어진 '사용자 결정 대기' 항목을 한 번의 세션에서 답할 수 있게 하나로 모은다. 같은 결정은 하나로 합치고 출처를 모두 적었다.
- 읽은 출처(모두 `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/` 아래, 약어):
  - **DP** = `engine/decision_package_specs.md`(스펙 36칸 #1~#36, 묶음 A~D, 3.1절 합격 정의 7건, 4절 J 묶음)
  - **R** = `engine/ROADMAP.md`(4절 D1~D18, 3절 주차, 정정절 1~8)
  - **NR** = `engine/NEW_ENGINE_DESIGN_REQUIREMENTS.md`(6절 E1~E7, 확정 사항 절)
  - **S6a** = `engine/6a_structure_prep.md`('착수 전 결정 필요' 1~5)
  - **NM** = `engine/nmcnr_diag.md`(5절 Q1~Q3)
  - **IC11** = `engine/ic11_two_stage_diag.md`(4절 F2 방향, M1/M2 VDS, CS 노드)
  - **PA** = `engine/power_area_min_study.md`(5절 D1~D10)
  - **SH** = `engine/spice_harness_report.md`(4단계 4·5·8)
  - **LC** = `engine/lut_coverage_study.md`(6절 추천안)
  - **M3** = `engine/design_mod3_s1_graph.md`(8절 사용자 승인 항목 8.1 J9·8.2 DEC-61, 7절 ⑦ [결정])
  - **G7** = `engine/design_gb7_dc_canonical.md`(10절 사용자 승인 항목 U1~U9; 이 문서에서는 G7-U1처럼 적는다)
  - **UD** = `user_decisions.md`(2026-10-07 항목까지 = 중복 제거 기준)
  - **P 행** = 계획서 `chip-design-skills/docs/01-plan/features/gain-budget-gmid-sizing.plan.md` 행 번호(6df4bd7).
- 정리 규칙(사용자 원칙 "결정은 원칙으로 기본안부터, 묻는 건 사용자 몫(spec·회로해석·승인)만"):
  - 이미 답한 것은 넣지 않았다(8절 목록).
  - 오케스트레이터가 원칙·기존 기록으로 정할 수 있는 것은 질문에서 빼고 **7절 '기본안 확정 가능'**으로 모았다(근거 함께).
  - 스펙 값·회로 해석은 Claude가 값을 정하지 않았다. 기본안 칸에는 **근거 방식**만 적었다.
- 주차 = R 3절 표(1주 U1, 3주 끝 U2 공동분석, 6주 U3 결과 검토). '필요 시점'은 그 결정이 없으면 멈추는 작업 단위(R 2절 ID)와 그 주.
- 질문 ID: **SP** 스펙 값 / **AC** SPICE 합격 정의 / **CI** 회로 해석 공동분석 / **PA** 전력·면적 / **ET** 기타 / **DF** 기본안 확정 가능(질문 아님).

---

## 0. 1주차에 꼭 필요한 것 (요약)

1주 작업(R 3절: K1 LUT, D0·D1 설계, N1 로더, P1 SPICE 오라클, P3 LUT 재생성, P5 test 기반, D5 스펙 형식)과 2주 초 P4(회로 스펙)·D3(metric 명세)·N2(9회로 S1 그래프)가 아래 없이는 멈춘다.

| ID | 한 줄 | 막히는 것 |
|---|---|---|
| SP-1 | 4회로(two_stage·current_reuse·folded·common_gate) 전원을 `supplies_v{vdd 1.8, gnd 0}`로 확정 | N1 로드 게이트가 `supplies_v` 없는 회로를 거부(NR C11, E1 승인) -> 9회로 로드 불가 |
| SP-3 | PM 하한 -- 파일럿 70°는 확정 표시만 | P4 파일럿 spec, 마일스톤 1 PM 판정 |
| SP-5 | 파일럿 정착 목표(t_lln·t_settle, 논문 값) 채택 여부 | P4 파일럿 spec(GBW 대신 정착에서 omega_c 유도) |
| SP-6 | 파일럿 부하·되먹임 용량(C_Ltot 1 pF, Cf/Cs 500 fF, 논문 값) 채택 여부 | P4 파일럿 spec, M1 PM·GBW |
| AC-1 | SPICE 합격 임계·포화 여유·노드 허용오차·처리 순서 | P1 오라클 tol 파일, T4 판정 |
| AC-2 | PM 측정 정의(어느 루프) | P1 `.ac` PM 측정, D3 metric 명세(2주) |
| CI-12 | [J9] `passive_elements` 키 없는 3회로(nmcnr·two_stage·folded): 키 없으면 거부 + 사용자가 선언 작성(CL 포함) vs 통과+review_needed | MOD2/MOD3 passive 게이트가 지금 3회로를 거부 -> S1 그래프(N2) 생성 불가 |
| CI-14 | [DEC-61] 9회로 bulk 선언 0 -> 기본 규칙(nmos 최저·pmos 최고 레일) 적용 확인, source 등에 묶은 소자는 사용자가 `bulk` 작성 | S1 `Device.b`, 6b `stacked_vsb`·gmb 입력 -- S1 지문에 선언 bulk가 들어가 나중에 바꾸면 S1 재유도 |

**1주차 필수 = 8건.** (SP-2 입력 DC는 G7-U2 기본안(W4 자유 변수)이 있어 1주가 아니라 GB7(K2, 3~4주) 전에 필요하다.) SP-3·SP-5·SP-6은 규칙(방식) 질문이라 한 번 답하면 다른 회로 칸에도 적용된다. 다른 회로 칸의 값은 늦어도 5주(two_stage·folded·nmcnr, Z2~Z4)·6주(나머지 5회로, Z5~Z9) 시작 전이면 되지만, R은 U1에 한 번에 받는 것을 기본으로 한다.

---

## 1. 묶음 (1) 스펙 값 -- 7문항 (DP 36칸 중 면적 9칸을 뺀 27칸)

공통 기본 규칙(DF-1, 질문 아님): **사용자가 값을 준 칸만 제약(`user_spec`)**, 값이 없는 metric은 '보고만', 그 회로는 선언 스펙과 T1~T4·T6·T8만 판정(R D1 기본안, U-35 P 1112 -- 자기 결과 역산값 금지). 따라서 아래 질문에서 "값 없음"도 유효한 답이다.

공통 근거 출처 표기: H = `workspaces/run_harness.py`(지금은 `legacy/workspaces/`), T = 회로 topology.json(DP 1절 행 번호).

### SP-1. 전원 `supplies_v` 표기·값 확정 (4칸)
- 질문: two_stage_ota·current_reuse·folded_cascode(지금 스칼라 vdd 1.8, 확정 기록 없음)와 common_gate_amplifier(빈칸)의 전원을 `supplies_v{vdd: 1.8, gnd: 0}`로 확정하는가?
- 왜 필요: 새 로더 GB0는 `supplies_v` 필수이고 스칼라 vdd 폴백이 없다(NR C11, E1 승인). 없으면 N1 '9회로 로드' 완료 조건이 막힌다.
- 선택지: (a) 4회로 모두 1.8/0 (b) 회로별 다른 값 지정.
- Claude 기본안 근거 방식: 같은 공정 정격(sky130 1.8 V core)·LUT VDS/VGS 특성화 범위(0~1.8 V)·이미 확정된 ngcc 1.8/0과 일관되게 표기만 바꾼다. 값은 사용자 확인.
- 출처: DP #1·#5·#11·#31, DP 묶음 B, U-26 (a), NR C11·C18.
- 필요 시점: **1주(N1)**.

### SP-2. 입력 DC(공통모드) 정하는 방식 (6칸 + IC11 CS 노드)
- 질문: 입력 DC가 빈 6회로(two_stage #2, current_reuse #6, folded #12, nmcnr #18, ngcc #24, common_gate #32)의 입력 DC를 (a) 회로별 값으로 줄지 (b) connectivity 헤드룸에서 ICMR을 유도해 그 중앙으로 둘지 (c) spec에 없으면 W4 자유 변수(창 안)로 두고 결과에 '요구 입력 공통모드'로 보고할지 (d) 선언 필수(없으면 정지)? 그리고 two_stage의 CS 노드 전압(tail VDS)을 tail 하한에서 둘지 입력 공통모드에서 유도할지(IC11)?
- 왜 필요: SPICE free 모드 테스트벤치에 입력 DC가 있어야 하고(SH 3.1), 노드전압 정본(K2)은 입력 노드 전압을 고정 입력으로 받는다. 옛 엔진은 folded 입력을 레일 밖 −0.85 V로 예측했다(선언 필요성 근거).
- Claude 기본안 근거 방식: 입력쌍 극성·tail 최소 VDS·미러 부하 VGS에서 ICMR 범위 유도 -> 중앙. current_reuse는 PMOS·NMOS 입력쌍 헤드룸의 교집합, nmcnr은 분할 레일 ±0.9 V의 0 V와 ICMR 유도값을 함께 제시, ngcc는 확정 ICMR(≥ 0.6 V) 범위 안, common_gate는 vin DC = M2 source = M1 drain이라 M1 VDS(sat) 하한과 M2·M3 헤드룸(T `_reference_relations`)에서 유도. 3레일 회로의 agnd(전원 중간) 선례와 비교 표시. 값은 정하지 않음. 정책 기본안은 G7-U2 (c)(= G7 문서의 (a) W4 자유 변수): 값을 주지 않은 회로는 엔진이 창 안에서 정하고 보고한다(근거 G7 10절 U2, 3절 쓰기 티어 W4).
- 출처: DP #2·#6·#12·#18·#24·#32, DP 묶음 C, IC11 4절 F2 끝 "CS 노드 전압", SH 4단계 3, **G7-U2**.
- 필요 시점: 정책(c/d)은 GB7(K2, 3~4주) 전 = U2(3주 끝)까지. 값을 줄 회로는 P4(2주)~늦어도 5주, common_gate 6주.

### SP-3. PM 하한 (4칸)
- 질문: PM 하한을 two_stage(#3 빈칸, 설계 의도 ≈70°), folded(#15 빈칸), sf_pushpull(#28 빈칸)에 둘지·얼마로, current_reuse(#9) 70°를 확정 표시하는지? two_stage의 GBW·PM을 '보상 목표'에서 '제약'으로 올리는지(R D1)?
- 왜 필요: T5 SPICE 성능 판정 대상, GB5 보상 규칙(K7)의 목표.
- Claude 기본안 근거 방식: 프로젝트 확정 선례(nmcnr·current_reuse 70°, ngcc 63.4°) + 구조 하한(2단 Miller 60°)에 여유, two_stage는 T276 설계 의도(Z/NDP가 인코딩한 PM)와 대조. sf_pushpull은 Cc–agnd 보상(GB5 규칙 뒤 측정 가능).
- 출처: DP #3·#9·#15·#28, DP 묶음 D, R D1.
- 필요 시점: **파일럿 확정 표시 1주**, 나머지 5주(K7) 전.

### SP-4. gain 하한 (4칸 + 재도출 2건)
- 질문: folded(#13), nmcnr(#20, 논문 >100 dB는 참고), ngcc(#25), common_gate(#34)의 gain 하한을 (a) 지금 값으로 줄지 (b) "SPICE 실측 달성값 − 마진"으로 정할지(마진 값은 사용자) (c) 보고만? two_stage 57 dB·current_reuse 54 dB를 7a SPICE 대조로 재도출(U-19)하는지?
- 왜 필요: T5 판정, GB4 축소(K6)의 INFEASIBLE_TARGET 검사 입력.
- Claude 기본안 근거 방식: current_reuse 54 dB 선례(실측 달성점 − 안전 마진, 사용자 승인) 방식, 3단 구조 이득 상한(엔진 실측)과 대조, common_gate는 Av = gm2·(rds2∥rds3) 상한(LUT gm/gds) − 마진, folded는 같은 단수 문헌 typical을 참고로만.
- 출처: DP #13·#20·#25·#34, R D1, U-19 P 1096, U-35 P 1112.
- 필요 시점: 2주(P4)~늦어도 5주(Z2~Z4), common_gate·ngcc 6주.

### SP-5. GBW·정착 목표 (3칸 + R D1)
- 질문: current_reuse 정착 목표(#8, 논문 t_lln 30 ns·t_settle 40 ns)를 채택하는지, folded(#14)·common_gate(#35) GBW를 둘지·얼마로? two_stage 7 MHz(확정)를 제약으로 올리는지(SP-3과 같이)?
- 왜 필요: current_reuse는 GBW가 없고 omega_c를 정착 시간에서 유도한다(H 190·204). 단일단 회로는 U-12(gm1 ≥ 2π·GBW·C_out) 규칙이 GBW 목표를 요구한다.
- Claude 기본안 근거 방식: 정착 배분식(t_s = t_slew + t_lln)이 배선돼 있으므로 정착 목표를 시스템 요구로 받거나, 논문 값을 sky130 전원·부하로 스케일(SR ∝ I/C, 전원 폭 비)한 값을 참고로 제시. 단일단은 확정 CL과 U-12 규칙에서 같은 전력 수준 GBW 스윕 무릎점(two_stage 7 MHz 선례 방식).
- 출처: DP #8·#14·#35, R D1, U-12 P 1089.
- 필요 시점: **파일럿 1주**, folded 5주, common_gate 6주.

### SP-6. 부하 (3칸)
- 질문: (a) current_reuse 부하·되먹임 용량(#7, 논문 Table I: C_Ltot 1 pF, Cf/Cs 500 fF)을 채택하는가 (b) nmcnr 저항 부하 25 kΩ(#19, 논문 측정 조건)을 넣는가, 순수 용량 부하(100 pF)만인가 (c) common_gate CL(#33, 빈칸)은?
- 왜 필요: 부하는 GBW·PM·SR의 기준 조건. 파일럿은 실행 spec에 이미 논문 값이 쓰이고 있다(확정 기록 없음).
- Claude 기본안 근거 방식: 부하·되먹임 용량은 공정 무관 topology 수준 값이라 논문 값을 참고로 제시하고 채택 여부만 묻는다(ngcc·nmcnr에서 사용자가 논문 CL을 채택한 선례). common_gate는 같은 class 단일단 확정 CL(folded 1 pF)과 일관.
- 출처: DP #7·#19·#33.
- 필요 시점: **파일럿 1주**, nmcnr 5주, common_gate 6주.

### SP-7. 그 밖의 성능 제약: CMRR/PSRR·슬루 (3칸)
- 질문: folded CMRR/PSRR(#17, U-35로 삭제됨)를 다시 선언할지, nmcnr PSRR(#23, 논문 92.61/106.44 dB@1 kHz)·슬루(#21, 논문 SR 0.36/0.31 V/µs)를 제약으로 둘지(주파수점 포함)?
- 왜 필요: 선언하면 T5 판정 대상, 안 하면 DF-1로 보고만.
- Claude 기본안 근거 방식: 선언 시 current_reuse 확정값(CMRR·PSRR 60 dB)과 일관 또는 7a 실측 − 마진. 슬루는 논문 SR을 sky130 전원 폭(2.0 -> 1.8 V)·CL 동일(100 pF)·전류 수준으로 스케일한 참고값, 또는 U-29 유추로 보고만.
- 출처: DP #17·#21·#23.
- 필요 시점: 5주(Z2~Z4) 전.

---

## 2. 묶음 (2) SPICE 합격 정의 -- 3문항

DP 3.1절 7건 중 #2(비교 W)·#4의 gain 부분·#6(수동소자 면적 출처)은 원칙으로 정해져 7절 DF로 뺐고, #3(Iref)은 CI-17, #7(시간 예산)은 4절 PA-2로 옮겼다.

### AC-1. 합격 임계·포화 여유·노드 허용오차·처리 순서
- **해소(사용자 확정 2026-10-07 8번 수정안)**: 합격 = free 모드 스펙 만족 + 전 MOS 포화(VDS−VDsat ≥ 0), 노드·소자·성능 차이는 기록, forced 모드만 경고. 아래 원문은 이력.
- 질문: SPICE 합격을 (i) 스펙 판정 = SPICE 측정값이 사용자 스펙 값 그대로 만족 (ii) 포화 = ID > 0 인 모든 MOS가 VDS − VDsat ≥ 포화 여유(기본 0) (iii) 노드전압 비교 허용오차 = tol_V(LUT leave-one-out 보간 오차에서 계산, 상수 아님), 소자별 ID·gm·gds 차는 기록만(DEC-72) (iv) 순서 = SPICE 1점으로 모델 오차 측정 -> 그만큼 제약을 조여 1회 재풀이 -> 선택 점 판정(NFR-5)으로 정의하는가?
- 왜 필요: P1 오라클의 tol 파일과 T4·T5 판정 문장이 이것으로 정해진다. 지금 하네스는 "N/A(tol 미설정)"만 낸다(SH 2단계).
- 선택지: (a) 기본안 그대로 (b) 포화 여유를 양수 값으로 지정 (c) metric별 허용오차 값을 따로 지정.
- Claude 기본안 근거: DEC-72 P 266(모델 오차는 기록, 임계 아님), NFR-5 P 185(여유 = max(격자 분해능, 모델 오차)), P 442(tol_V), 사용자 2026-10-07 "상수는 배제하고 PDK로 오차를 계산"(W 허용오차에서 같은 원칙). 최소화는 해를 활성 제약 경계로 밀므로 오차 측정이 최소화보다 먼저여야 한다(PA 3절).
- 함께 답할 것 (v) **G7-U5** W4 고임피던스 노드(고이득 출력노드 등)의 SPICE free 대조 판정 방식: 기본안 = DC 되먹임 하네스 상태에서 tol_V 비교 + forced 모드 KCL 잔차 ≤ tol_I 병행(근거 G7 10절 U5, SH 4단계 8). (vi) '전 소자 포화' 예외 소자 목록은 CI-18(G7-U9)에서 받는다.
- 출처: DP 3.1 #1, R D6·T4, PA D7, SH 4단계 8, G7-U5.
- 필요 시점: **1주(P1 tol 파일)**.

### AC-2. PM 측정 정의(루프)
- 질문: PM을 엔진·SPICE 오라클이 같은 정의로 재며, 선언된 되먹임 수동소자(예: 파일럿 Cf/Cs)가 있으면 그 β 루프의 PM, 없으면 β = 1(단위 이득 되먹임) 루프의 PM으로 정의하는가?
- 왜 필요: 옛 하네스는 개루프 A 기준 PM(180 − 위상차)을 쟀고, 정의 없이 비교하면 파일럿에서 79° 대 18° 같은 차가 정의 문제인지 결함인지 가를 수 없다. D3(7a metric 명세, 2주)와 P1 `.ac` 측정이 이 정의를 쓴다.
- 선택지: (a) 기본안 (b) 모든 회로 β = 1 (c) 회로별 지정.
- Claude 기본안 근거: R D15 기본안, I-B21 P 972. 파일럿에서 어떤 노드가 β 루프를 이루는지는 회로 해석이라 CI-10으로 분리.
- 출처: DP 3.1 #4(PM 부분), R D15, SH 4단계 8.
- 필요 시점: **1주(P1), 늦어도 2주(D3)**.

### AC-3. SPICE를 돌리는 front 점
- 질문: 합격 시험에서 SPICE 판정(T4·T5)을 요구하는 front 점을 (a) 양 끝점 + 예산 점 (b) front 전 점 (c) 예산 점만 중 무엇으로 하는가?
- 왜 필요: T7 판정 범위와 마일스톤 1 완료 조건 (d).
- Claude 기본안 근거: (a) -- 끝점이 활성 제약 경계(오차에 가장 민감), ngspice 1회는 초 단위라 비용 문제는 아님(PA 3절). (b)는 비용상 가능하나 ε점 수가 시간 예산(PA-2)에 묶여 있다.
- 출처: DP 3.1 #5, R D5·T7, PA D6.
- 필요 시점: 4주(마일스톤 1).

---

## 3. 묶음 (3) 회로 해석 공동분석 -- 18문항 (U2, 3주 끝 한 세션; CI-12·CI-14만 1주)

회로 해석은 Claude가 결론을 내지 않는다(메모리 원칙). 6a 구현(N3~N9)이 낸 **J 대조표**(회로별 유도 결과 + 갈리는 읽기의 수치)를 보고 사용자가 ratify한다. 진행 순서는 계획 판정 순서(P 1045): J2·J5·J13 -> J11 -> J3-ac·J4·J10 -> J12-a~i -> J6·J7, 그 뒤 J8(6b)·J9 passive(7b). J1은 확정(2026-09-17, 파일럿 2건·나머지 무동작).

회로별 connectivity 표(topology_to_markdown.py 생성, 2026-10-07; 세션에 함께 띄운다), 경로 앞부분 = `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/engine/decision_package_connectivity/`:

| 회로 | 파일 | 걸린 CI |
|---|---|---|
| common_gate_amplifier | `common_gate_amplifier.connectivity.md` | CI-3·4·8 (가장 가벼움) |
| current_reuse_telescopic_ota (파일럿) | `current_reuse_telescopic_ota.connectivity.md` | CI-2·3·4·5·7(c·e)·9·10·11·15·17 (가장 무거움) |
| folded_cascode | `folded_cascode.connectivity.md` | CI-3·4·6·11·12·15·16 |
| ngcc_3stage_ff | `ngcc_3stage_ff.connectivity.md` | CI-2·3·4·7·13 |
| nmcnr_amplifier | `nmcnr_amplifier.connectivity.md` | CI-1·2·3·4·9·11·12 |
| pushpull_follower_buffer | `pushpull_follower_buffer.connectivity.md` | CI-3·4·6·7 |
| sf_pushpull_output_opamp | `sf_pushpull_output_opamp.connectivity.md` | CI-3·4·6·7·13 |
| two_stage_ota | `two_stage_ota.connectivity.md` | CI-2·3·4·7(e)·11·12 |
| two_stage_ota_sf | `two_stage_ota_sf.connectivity.md` | CI-2·3·4·6·7 |

공통 기본안 근거 방식(모든 CI): connectivity 사실(gate·drain·source 넷 공유, KCL·KVL)로 유도한 구조를 대조표로 제시하고, 갈리는 읽기가 있으면 두 읽기의 수치를 함께 적는다(P 1162 "결정 전까지 대조표는 갈리는 읽기의 수치를 함께 적는다"). 회로 이름·소자 이름을 규칙에 넣지 않는다(일반화 원칙).

### CI-1. nmcnr 2단 diode 미러 (J2 + nmcnr Q1~Q3)
- 질문: (Q1·J2) M203(G=D=NodeC)은 M201의 부하이자 M204 미러의 레퍼런스인가, diode gate->drain이 같은 stage(미러)인가? (Q2) M201 VDS = vdd − VGS(M203)인 종속 관계인가(2소자 직렬 기둥)? (Q3) M204(D = NodeS2 = M301 gate)는 포화여야 하는가? -- Q3는 CI-18(선형 영역 의도 소자)과 함께 답한다.
- 왜 필요: 옛 엔진은 이 기둥에서 'stage2_diode_ref' infeasible로 멈췄다(compensation이 M201 VDS를 diode 창과 무관하게 고정). 새 엔진은 기둥 KVL과 diode 창을 GB1·GB7에서 다루며, nmcnr_diag 2~3절 수치를 test 픽스처로 쓴다(R 0.5) -- 이 해석이 픽스처 기대값의 근거다.
- 출처: DP 4.1 J2, NM 5절 Q1~Q3, R 3절 U2·4절 끝, IC11 2절(nmcnr 몫).
- 필요 시점: U2(3주 끝). K2 nmcnr 확장(K5, 6주)·Z4(5주) 전.

### CI-2. 5T 미러 부하·폴딩 미러 축약 + `equal_vgs` 그룹의 독립 gm_id 소자 (J5 + IC11 F2 + G7-U1)
- 질문: (J5) 5T 미러 부하(two_stage, two_stage_ota_sf, ngcc)와 NMCNR 폴딩 미러를 기모드 축약에서 어떻게 볼지? (IC11 F2) two_stage M3(diode)/M4 쌍에서 diode VGS를 정하는 등식은 (Ha) 파트너 M4의 gm_id가 권위 / (Hb) systematic offset 0 조건 VSG(M3) = VSG(M6) / (nmcnr 선례) diode 창에서 받고 파트너가 역산 -- 중 무엇이 설계 의도인가? 즉 systematic offset 0을 요구하는지, M3/M4를 강반전 matching으로 둘지? (IC11) offset 매칭 차동쌍 M1/M2의 VDS가 서로 달라도 되는가? (G7-U1, 같은 질문의 일반형) `equal_vgs` 그룹(같은 gate·source 넷)에서 어느 소자의 gm_id를 독립(writer)으로 두고 나머지를 종속으로 둘지 -- two_stage M3/M4, current_reuse Vbias2 {M2a, M2b, M58, M57}·Vbias3 묶음 {M3a, M3b, M64, M63}.
- 기본안(G7 문서 그대로): diode 멤버가 writer(gm_id 독립), 나머지 종속, diode가 없으면 이름 정렬 첫 멤버. 근거: G7 10절 U1(쓰기 계획 트리의 writer 소자 선택), IC11 F2-nmcnr 선례(diode 창 -> 파트너 역산). 이 기본안은 F2-Ha가 아니라 nmcnr 선례 쪽이므로 systematic offset 0(F2-Hb)을 요구하면 다른 답이 된다.
- 왜 필요: 같은 gate·source 넷 쌍의 VGS 동일은 connectivity 사실이라 새 엔진(K2 노드전압 정본)이 구조적으로 강제한다. 남는 것은 그 공유 전압을 무엇이 정하느냐(W3 목표 대 유도)이고 이것이 회로 해석이다. 옛 실측: Ha gain 61.40 dB·VSD 차 0.31 V, Hb 61.20 dB·면적 785 µm², F1만이면 VGS 불일치가 조용히 통과(받으면 안 되는 해).
- 출처: DP 4.1 J5, IC11 3절 원인 C·4절 F2, S6a 5절 관찰 4, G7-U1.
- 필요 시점: U2(3주 끝) -- GB7(K2, 3~4주)이 writer 선택에 쓴다.

### CI-3. 가지·기둥 유도와 기둥↔블록 매핑 (J13, 9회로)
- 질문: 9회로 각각 6a가 유도한 가지·기둥(레일 쌍별, 3레일 pushpull·sf_pushpull의 레일 쌍 포함)과 기둥↔블록 매핑이 설계 의도와 맞는가? 옛 `vertical_stack_id`와 다른 곳은 어느 쪽이 맞는가? (G7-U8) 이상 전류원 가지의 전압을 W4 자유 변수로 두는가 -- 기본안 W4(근거 G7 10절 U8, DEC-71 (1) 이상원 가지 표시).
- 왜 필요: K2 노드전압 정본(GB7)이 기둥 KVL을 입력으로 쓴다. T2(역할 태그 없이 같은 멤버십) 불일치는 `review_needed`로 여기서 ratify.
- 출처: DP 4.1 J13, R N4·T2, S6a R5·R18, G7-U8.
- 필요 시점: U2(3주 끝), K2 끝(4주) 전.

### CI-4. 루프 뷰 (J11, 9회로)
- 질문: 9회로 루프 목록·(0)~(4) 분류·끊는 점·극성이 맞는가? 파일럿 CMFB·M58·M7 루프는 J1 결과를 입력으로.
- 왜 필요: PM 루프(AC-2)와 GB5 보상 규칙(K7)의 입력. 옛 기대 36/18/1/0 대 재측정 23/13/1/1이라 정의 확정 뒤 재측정 값을 ratify해야 한다(P 342).
- 출처: DP 4.1 J11, S6a R14, R N6.
- 필요 시점: U2(3주 끝), K7(5주) 전.

### CI-5. 파일럿 class-AB pass 묶음·stage1 출력·병렬 CS와 M7 (J3-ac + J4)
- 질문: (J3-ac) current_reuse M9a/M9b/M18a/M18b/M8/M17의 class-AB pass 묶음·stage1 출력노드·병렬 CS 해석이 맞는가? (J4) M7(gate Vcmfb)은 tail인가 CMFB 구동인가?
- 왜 필요: 파일럿 DC 정본(K2 순환 블록 CMFB·bias SCC)과 마일스톤 1(4주).
- 출처: DP 4.1 J3-ac·J4, S6a R9·R16. (J3-dc는 7b 몫, 이번엔 미리 보기만.)
- 필요 시점: U2(3주 끝) -- 마일스톤 1(4주) 직전이라 늦출 수 없음.

### CI-6. follower/pass 경로 독립 블록 대 흡수 (J10)
- 질문: two_stage_ota_sf(M8)·pushpull·sf_pushpull·folded(M8)의 follower/pass 경로를 독립 블록으로 볼지 앞 단에 흡수할지?
- 왜 필요: stage·극점 노드(R12)와 버퍼 묶음(R15) 결과가 갈린다.
- 출처: DP 4.1 J10.
- 필요 시점: U2(3주 끝).

### CI-7. 신규 4회로 대조표 (J12 본문 + J12-a~h)
- 질문(하위 8개, 한 표로 ratify): J12 본문(ngcc gmf1 가지·Vout 합류·Cm DC 고립·미러 후보), J12-a 버퍼 블록 경계 3건, J12-b A·B·N17·N20 구동 종류·버퍼 load 귀속, J12-c G_vgs 사이클(push-pull KVL 루프; pushpull·sf_pushpull·current_reuse), J12-d sf_pushpull M17/M20 K8 측면 주입 대 복합 블록(결과에 따라 ngcc와 함께 DEC-81 발동), J12-e 출력 방향 class-A/push-pull(5회로), J12-f 루프 종속 gm_id 소자·합류 KCL(M1/M2, M21/M22) + **G7-U4** `kvl_branch` 종속 멤버 선택(sf_pushpull {M18, M19, M21, M22}, pushpull {M1~M4}, 파일럿 v2 4개; 기본안 = DEC-64 기본 이름 정렬 첫 멤버, 근거 G7 10절 U4), J12-g two_stage_ota_sf Cc O1–OUT와 follower가 Miller 루프 밖인지, J12-h sf_pushpull M5/M6 복합 diode 루프(M7/M8·M13/M14 포함).
- 왜 필요: K5(9회로 확장 DC: 3레일·`kvl_branch`·K8 측면 주입, 6주), N7(버퍼 묶음·출력 방향·복합 블록, 5주)의 기대값.
- 출처: DP 4.1 J12·J12-a~h, S6a R4·R15·R16·R17, R N7·K5, G7-U4.
- 필요 시점: U2(3주 끝), 늦어도 5주(N7).

### CI-8. common_gate 대조표 (J12-i)
- 질문: 전압 구동 CG에서 stage 시작을 어디로 보는지, CG 셀 1개 판정이 맞는가?
- 왜 필요: common_gate의 셀·stage(R9·R12) 기대값. 다른 J12와 독립.
- 출처: DP 4.1 J12-i, S6a R9.
- 필요 시점: U2(3주 끝).

### CI-9. 출력노드 부하 귀속과 Cc–Rz 직렬 루프 극성 (J6 + J7)
- 질문: (J6) current_reuse M18a/M19/M18b, nmcnr M104/M106 출력노드 부하 귀속은? (J7) current_reuse Cc1–Rz, nmcnr Cm1/Cm2–Rm 직렬 루프의 극성은?
- 왜 필요: 극점 노드·GB5 보상 규칙(K7) 입력, 7a PM.
- 출처: DP 4.1 J6·J7.
- 필요 시점: U2(3주 끝), K7(5주) 전.

### CI-10. 파일럿 PM 루프 β의 해석 (R D15 "파일럿 β 해석은 U2")
- 질문: AC-2 정의를 파일럿에 적용할 때 Cf/Cs가 이루는 되먹임 루프(β)를 어느 노드로 끊고 어떤 β로 보는가?
- 왜 필요: 마일스톤 1(4주)의 PM 판정. 옛 강제 바이어스 SPICE에서 단 합 대비 6.6 dB, MNA 대비 12.1 dB 차가 있었다(R D15 근거).
- 출처: R D15, DP 3.1 #4, SH 4단계 8.
- 필요 시점: U1에서 답하면 좋고, 늦어도 U2(3주 끝).

### CI-11. fold_group·shared_gm_id_groups·budget_reference_device 의도 (J8, 6b)
- 질문: 새 엔진은 이 태그를 읽지 않는다. 6a 출력(분기 노드·`kcl_group`·공유 가지)이 옛 태그의 의도를 대신하는지, 특히 노드를 공유하지 않는 budget_reference 4건(current_reuse M61/M68/M38, two_stage M4)과 folded·nmcnr fold_group이 무엇을 뜻했는지?
- 왜 필요: K2(노드전압 정본, 2~4주)의 전류 합류 등식 대조. 메모리 원칙(fold_group 해석은 혼자 판단 금지, 세션42 오판 반복).
- 출처: DP 4.1 J8, S6a 3절 `fold_group`·`budget_reference_device` 행.
- 필요 시점: U2(3주 끝).

### CI-12. [J9] `passive_elements` 키 없는 3회로 + 출력 CL 추가 (J9 passive + R D12) -- 1주 필수
- 질문: nmcnr_amplifier·two_stage_ota·folded_cascode는 `passive_elements` 키가 없다. (a) 게이트는 키가 없으면 거부하고(`[]`는 '없음'의 명시 선언으로 받음) 사용자가 세 파일에 선언을 쓴다 / (b) 키가 없으면 통과시키고 S1에 `passives_declared=False`를 기록, 루프·교류접지 소비자(R6·R14)가 `review_needed`로 정지 -- 중 무엇인가? (a)라면 각 회로의 선언 내용:
  - nmcnr: topology 주석 `_compensation_network_comment`의 Cm1(NodeM2–NodeCM), Cm2(NodeS2–NodeCM), Rm(NodeCM–Vout), CL(Vout–vss, 100 pF)을 그대로 옮기는가("only ONE null resistor", 2026-07-31 사용자 정정; NodeCM은 netlist에 없는 넷).
  - two_stage_ota: 후보 Cc(O1–OUT)·CL(OUT–gnd, 3 pF) -- **추측**(two_stage_ota_sf의 같은 이름 넷과 Miller 표준형에서 유추)이라 도면 확인 필요.
  - folded_cascode: 도면에 보상·부하 소자가 없으면 `[]`, 출력 CL 1 pF(U-31 확정 spec)를 connectivity로 넣을지(R D12).
  - nmcnr 저항 부하 25 kΩ(SP-6 (b))를 넣는다면 같은 묶음으로.
- 왜 필요: MOD2/MOD3 passive 게이트가 지금 3회로를 거부한다 -> 9회로 S1 그래프(N2)가 안 선다. 키 없음을 `[]`로 읽으면 '수동소자 없음'이라는 회로 사실을 엔진이 지어내 교류접지 (2)·루프 분류가 경고 없이 달라진다(WP-02). 계획 J9는 7b 소비로 적었지만 S1 게이트 때문에 승인 시점이 당겨졌다(M3 8.1). connectivity는 사용자만 쓴다.
- Claude 기본안: (a) -- 근거 WP-02(회로 사실을 지어내지 않음), (b)는 3회로의 6a 대조가 늦어짐. 선언 값은 U-31 spec 값·topology 주석에서 옮기되 도면 확인은 사용자. 반영은 메모리 원칙대로 정정 대기열에 쌓았다가 "한꺼번에 반영" 지시 뒤 일괄 + connectivity 표 재출력.
- 출처: M3 8.1, R D12, DP 4.1 J9, U-31 P 1108.
- 필요 시점: **1주(S1 게이트, N2 착수 전)**.

### CI-13. J 항목이 없는 DC 역할 그룹 (6a 열린 항목 ⑮, J 신설)
- 질문: 3단 회로의 2단·feedforward 쌍(ngcc), sf_pushpull의 한 그룹, J12-b 목록에 없는 sf 대기 노드의 DC 역할을 새 J 항목으로 ratify한다.
- 왜 필요: 계획이 ⑮만 'AI 제안 -> 사람 확정(J 신설)'로 분류했다(P 1162 WP-21). 나머지 ①~⑭는 코드로 정한다(DF-11).
- 출처: P 1162 ⑮, R 4절 끝(열린 항목 ①~⑮), S6a 6절 U15.
- 필요 시점: U2(3주 끝).

### CI-14. [DEC-61 사실 확인] bulk 선언 0개 -> 기본 레일 규칙 적용 -- 1주 필수
- 질문: 9회로 모두 `bulk` 선언이 0개다. 기본 규칙(nmos -> `supplies_v` 최저 전위 레일, pmos -> 최고 전위 레일; 3레일 회로는 agnd에 붙지 않음)을 전 소자에 적용해도 되는가? 도면에서 bulk를 source 등 다른 넷에 묶은 소자가 있으면 그 소자에 `bulk` 필드를 써 달라.
  - source가 레일이 아니어서 기본 규칙이면 vsb ≠ 0이 되는 소자(확인 대상): pushpull M1~M4(follower), sf_pushpull M1·M2·M5·M7·M10·M12·M13·M15·M18·M19·M21·M22, two_stage_ota_sf M1·M2·M8(follower), current_reuse 23개(M1a/M1b·M4a/M4b 입력쌍, 캐스코드, M57/M58/M63/M64 등), folded 6·nmcnr 4·ngcc 2·two_stage 2·common_gate 1개.
- 왜 필요: S1 `Device.b`와 6b W2 `stacked_vsb`·`ss` gmb의 입력이고, 선언 bulk는 S1 지문에 들어가 나중에 바꾸면 S1부터 다시 유도된다. bulk는 connectivity라 사용자만 쓴다(DEC-61, WP-07).
- Claude 기본안: 선언을 추가하지 않고 기본 규칙 적용(J12의 "two_stage_ota_sf M1/M2 body effect" 서술과 일치). 레일 이름으로 대신 정하지 않는다(DEC-60). `supplies_v`가 없는 회로는 SP-1 확정(·spec 로더) 전까지 `b = undetermined`.
- 출처: M3 8.2, DEC-61 P 255, LC 5절(vsb 범위 밖 사례).
- 필요 시점: **1주(S1 생성)**.

### CI-15. W3 노드 목표 목록 (`node_voltage_targets_v`, G7-U3)
- 질문: 출력 공통모드 등 '목표 전압을 갖는 노드(W3)'를 무엇으로 둘지? 대상: current_reuse Voc_des·Vom1/Vop1, folded out.
- 왜 필요: GB7 쓰기 티어에서 W3(목표)와 W4(자유)가 갈리고, SPICE free 대조(AC-1 (v))의 판정 대상이 바뀐다.
- 기본안(G7 문서 그대로): 선언된 것만 W3, 나머지 W4. 근거: G7 10절 U3, 3절 쓰기 티어.
- 출처: G7-U3, SH 4단계 3(Voc_des 게이트 넷 요구 전압 차 0.55 V).
- 필요 시점: U2(3주 끝), GB7(K2, 3~4주) 전.

### CI-16. folded M1·M2 극성·단자 확인 (UD-17a, G7-U6) -- connectivity
- 질문: folded_cascode 입력쌍 M1·M2의 kind(극성)와 단자 연결이 도면과 맞는가? 옛 엔진에서 PMOS 게이트가 −1.04 V여야 하는 비물리 바이어스·vsb 1.6 V가 나왔고, 극성 선언 오류가 의심됐다(UD-17a).
- 왜 필요: connectivity라 사용자만 고친다. GB7 노드전압 정본과 folded 기둥 픽스처(R 1.3 '옛 −0.85 V를 픽스처로')의 전제다. S1 지문에 들어가므로 일찍 고칠수록 재유도가 적다.
- 기본안: 없음(G7 10절 U6 "-- connectivity, 사용자만 수정"). 고칠 내용이 있으면 메모리 원칙대로 정정 대기열 -> "한꺼번에 반영" 지시 뒤 일괄 + connectivity 표 재출력. 대조용: `folded_cascode.connectivity.md`.
- 출처: G7-U6, LC 5절(folded M1·M2 행), UD-17a(`prep_ud17_f26_f27.md`).
- 필요 시점: 늦어도 U2(3주 끝, GB7 전). N2 S1 생성(2주) 전에 답하면 재유도가 없다.

### CI-17. 값 선언 이상 전류원과 θ의 관계 (파일럿 Iref, G7-U7 = SH Iref 항목)
- 질문: 값이 선언된 이상 전류원(current_reuse `Iref.value_amp` 1.2 µA, 2026-09-08 사용자 확정)은 선언값으로 고정하고 엔진이 소비하는가, 그리고 같은 전류원에 θ(옛 `r_biasgen` 계열)가 함께 있으면 로드에서 거부하는가?
- 왜 필요: 옛 엔진은 M18_bg에 0.1993 µA를 써서 topology 값으로 SPICE를 돌리면 bias 가지 전류가 5~6배 달랐다(SH 4단계 4). 마일스톤 1(4주)의 파일럿 바이어스.
- 기본안(G7 문서 그대로): 선언값 고정, θ와 공존 시 로드 거부. null이면 엔진이 정해 출력. 근거: G7 10절 U7, DEC-08 P 203, I-B14 P 971.
- 출처: G7-U7, SH 4단계 4, DP 3.1 #3, R D14.
- 필요 시점: U2(3주 끝), GB7 전. (U1에서 확인만 받아도 된다.)

### CI-18. 선형 영역 의도 소자 선언 (`intended_region`, G7-U9) + nmcnr Q3
- 질문: 의도적으로 선형 영역에서 동작하는 소자가 있는 회로가 있는가? 있으면 `intended_region` 목록으로 선언한다. nmcnr M204(D = NodeS2 = M301 gate)가 포화여야 하는가(NM Q3)도 여기서 답한다.
- 왜 필요: 봉인 7(포화 검사)과 SPICE T4 '전 소자 포화' 판정(AC-1 (ii))의 예외 목록.
- 기본안(G7 문서 그대로): 선언 0(전 소자 포화 검사). 근거: G7 10절 U9, 봉인 항목 7(P 428~435).
- 출처: G7-U9, NM 5절 Q3, AC-1.
- 필요 시점: U2(3주 끝), GB7 봉인 전.

---

## 4. 묶음 (4) 전력·면적 -- 2문항

### PA-1. 면적 예산(U-13)과 전력 예산 선언 (9칸 + nmcnr 전력)
- 질문: 9회로 각각 면적 예산을 선언할지·값(DP 면적 9칸 #4·#10·#16·#22·#26·#27·#29·#30·#36), nmcnr 논문 전력 400 µW(#22, AMS 0.8 µm·±1 V)를 전력 예산으로 둘지?
- 왜 필요: 예산이 있으면 그 예산을 ε으로 고정한 전력 최소 점 하나가 합격 대상 '예산 점'이 된다(T6·T7). 없으면 front를 내고 정지(자동 선택 금지).
- 선택지: (a) 미선언 -> front 제시 후 정지, U3(6주)에서 사용자가 front 점 선택 (b) 회로별 예산 값 지정(front 무릎점을 근거로 보고 정해도 됨).
- Claude 기본안 근거 방식: (a) -- DEC-77 P 271, U-13 P 1090. 전력은 목적(최소화)이라 예산 없이 둘 수 있고, 면적·전력 논문 값은 공정 종속이라 미채택이 이미 기록돼 있다(DP #22). 예산을 정한다면 front의 무릎점 근거.
- 출처: DP #4 외 8칸·묶음 A, R D7·T6, PA D1, U-13.
- 필요 시점: 7b 착수(K8, 5주) 전. (a)를 고르면 실제 점 선택은 U3(6주).

### PA-2. front 계산 시간 예산 (`wall_clock_budget_s`)
- 질문: 풀이 1회 300 s(DEC-34, 파일럿)를 전 회로 공통으로 쓰는가, 그리고 front 전체 시간 예산은 얼마인가?
- 왜 필요: ε점 수 = front 예산 / 실측 1회 풀이 시간(새 상수 없음). 파일럿 1회 ≈146 s(3 start)라 300 s면 끝점 2개뿐이다(PA 4절). 보상 단 gm/ID를 θ로 둘지의 자동 판정(DF-6)도 이 예산을 기준으로 한다.
- 선택지: (a) 300 s 유지(끝점 2개 + 예산 점) (b) front 예산을 회로당 N 초로 늘림.
- Claude 기본안 근거: 시간 예산은 사람 선언(DEC-34 P 228)이라 값은 사용자. 기본은 (a) 유지 후 4주 마일스톤 실측 시간을 보고 재질의.
- 출처: DP 3.1 #7, R D9, PA D4, U-26 (c).
- 필요 시점: 4주(마일스톤 1 front 양 끝), 늦어도 5주(K8).

---

## 5. 묶음 (5) 기타 -- 2문항 (지금 답하지 않아도 됨)

### ET-1. 새 엔진 브랜치의 메인 저장소 반영 방식
- 질문: clone `gmid-light`의 새 엔진 작업(R 0.1: 브랜치 `engine-v2`)을 메인 저장소 master에 언제·어떻게 반영하는가(gate 반영 방식)?
- 왜 필요: UD 2026-10-07 "병합 방식(gate 반영)은 Phase 3 끝난 뒤 사용자 결정" -- Phase 3은 멈췄고(D17) 새 엔진이 그 자리를 대신한다.
- Claude 기본안 근거: 마일스톤 1(4주) 통과 뒤 한 번 반영하고, 범위 합격(6주) 뒤 최종 반영. gate는 E1에서 '폐기 표시'됐으므로 가벼운 절차(PROCEDURE '남기는 것') 기준.
- 출처: UD 2026-10-07(phase3-light 항목), R 0.1, NR 확정 6(E1).
- 필요 시점: 4주 이후.

### ET-2. 옛 엔진·옛 test 퇴역
- 질문: 새 엔진이 9회로에 합격하면 `legacy/`의 옛 엔진·옛 test를 삭제할지, 대조 기준선으로 계속 둘지?
- 왜 필요: R D17 "퇴역은 9회로 합격 뒤 별도 결정". 삭제는 사용자 승인 사항.
- 출처: R D17·0.1, 메모리(목표 재확인: test는 버려도 됨).
- 필요 시점: 6주(U3) 이후.

---

## 6. 질문 수 집계

| 묶음 | 질문 수 | 그중 1주차 필수 |
|---|---|---|
| (1) 스펙 값 | 7 (SP-1~SP-7) | 4 (SP-1, 그리고 SP-3·5·6의 파일럿 칸) |
| (2) SPICE 합격 정의 | 3 (AC-1~AC-3) | 2 (AC-1·AC-2) |
| (3) 회로 해석 공동분석 | 18 (CI-1~CI-18) | 2 (CI-12·CI-14) |
| (4) 전력·면적 | 2 (PA-1·PA-2) | 0 |
| (5) 기타 | 2 (ET-1·ET-2) | 0 |
| **합** | **32** | **8** |

(1주차 필수 8건 = SP-1·SP-3·SP-5·SP-6·AC-1·AC-2·CI-12·CI-14. 0절 표와 같다. G7-U1~U9는 GB7(K2) 주차 = 3~4주라 U2(3주 끝)로 두었다.)

G7 10절 U1~U9 배치: U1 -> CI-2, U2 -> SP-2, U3 -> CI-15, U4 -> CI-7, U5 -> AC-1 (v), U6 -> CI-16, U7 -> CI-17, U8 -> CI-3, U9 -> CI-18. 기본안은 G7 문서의 것을 그대로 썼다.

---

## 7. 기본안 확정 가능 (질문에서 뺀 것) -- 오케스트레이터가 원칙·기존 기록으로 정한다

이 항목들은 사용자 몫(spec 값·회로 해석·삭제/공유 설정 승인)이 아니어서 근거와 함께 기본안으로 확정한다. 이의가 있으면 그 ID만 말하면 된다.

| ID | 결정 | 확정 기본안 | 근거 | 원 출처 |
|---|---|---|---|---|
| DF-1 | 값이 빈 스펙 칸 처리 | 사용자가 값을 준 칸만 제약, 나머지 metric은 보고만 | 스펙은 사용자 몫, U-35 P 1112(자기 결과 역산값 삭제), U-29 P 1106 선례 | R D1 기본안, DP 2절 메모 |
| DF-2 | gain 비교 metric | 전회로 MNA gain(엔진 `gain_ss_db`)을 SPICE `.ac` 전회로 응답과 비교 | SPICE가 재는 것은 전회로 응답 하나뿐 -- 엔진·오라클이 같은 정의여야 비교가 성립(I-B21 P 972) | DP 3.1 #4(gain), R D15, SH 4단계 8 |
| DF-3 | SPICE 비교 기준 W | 최종 레이아웃 기하(`w=finger_w m=n_fingers`)로 넷리스트를 만든다. 사용자 레이아웃 규칙상 총 W는 tol_V×(gm/ID) 허용오차 안에서만 보존되므로 엔진 W와 같은 값이 아니다(허용오차 안의 차가 남고, finger_w 슬라이스가 바뀌면 같은 gm/ID에서 전류밀도도 달라진다). 허용오차를 벗어나면 비교 기준 문제가 아니라 레이아웃 결함. 레이아웃 뒤 재검증·합격 SPICE 기하는 Q4(reference_review SYNTHESIS 2절) 대기 | 사용자 2026-10-07 레이아웃 규칙(총 W 보존·W_request·PDK 격자 하한), LC 6절 4(nf 대신 m) | DP 3.1 #2, SH 4단계 5 |
| DF-4 | (CI-17로 옮김) | 파일럿 Iref 정본은 G7-U7과 같은 결정이라 회로 해석 묶음의 확인 질문으로 옮겼다 | coordinator 지시(G7-U7 = SH Iref) | -- |
| DF-5 | 수동소자 단위 면적 출처(U-36) | `core/pdk_decl.py` 한 곳에서 sky130 PDK 문서의 MIM 커패시터·저항 단위 면적을 출처와 함께 읽는다. PDK 파일에 값이 없을 때만 사용자에게 묻는다 | E1 승인(NR C20: tlef 격자 + 규칙 문서 값 + 수동소자 단위 면적을 한 곳에서), 사용자 "상수 배제, PDK로 계산" | DP 3.1 #6, R D8, PA D3, U-36 P 1113 |
| DF-6 | 보상 단 gm/ID를 결정변수로 | 계획 DEC-04(소자마다 독립 θ)대로 θ에 포함. 실측 풀이 시간이 PA-2 예산을 넘을 때만 보상 단을 GB5 규칙값으로 고정하고 그 사실을 결과에 기록 | DEC-04 P 200(계획 확정 규칙), 퇴화 front 수용(PA D5)은 옛 엔진 θ 구조 전제라 새 엔진에 해당 없음 | R D10, PA D5 |
| DF-7 | 전력 표기 | 축은 공급 전류(A) 유지, 보고에 전력(W = V·I) 병기 | DEC-78 P 272, DEC-68 metric 이름 | PA D8 |
| DF-8 | 옛 엔진 결과와의 차이 처리 | 기준선 변경 승인 대상이 아니라 R 2.6 대조 기록 | 사용자 2026-10-07 "옛 엔진은 참고용" | R D11 |
| DF-9 | 로더가 읽지 않는 역할 태그 범위 | R 1.1 목록(`device_roles`, `vertical_stack_id`, `fold_group`, `headroom_role`, `shared_gm_id_groups`, `budget_reference_device`, 손선언 θ·stage). spec·constraints·ports·supply_nets·passive 값·ideal source 값은 입력 | P 1023, IC4 P 824, 사용자 범위 (나) "태그 없이 connectivity로" | R D13 |
| DF-10 | GB6 층 0 범위 | 최소형(기둥 KVL 시작점 조립)으로 시작, 확정은 새 커널 cProfile 뒤 | E1 승인에 포함된 NR C7(D18을 '새 커널 cProfile 뒤 확정'으로 조건부화), U-33 P 1110 | R D18 |
| DF-11 | 6a 열린 항목 ①~⑭ (S6a 결정 1~4 포함: 수동소자 엣지 비용=⑬ 관련, 대칭 반쪽 공유 넷=⑩, 병렬 소자 기둥 계수 62 대 41=⑦, 규칙 5·9(c) 적용 순서=⑧) | ⑦은 정본 = 따로 세기 62(DEC-71 (3)), 합쳐 세기 41 병기(M3 7절 [결정]). 나머지는 6a design(D1)이 알고리즘으로 정하고 구현·test로 고정. 갈리는 읽기의 수치는 J 대조표에 함께 적어 U2에서 사용자가 결과를 본다. ⑭(DEC-81 Phase 불일치)는 '6a는 묶음 판정을 기록만, 규칙은 같은 design에' 한 줄 결정 | 계획 P 1162 WP-21 분류: ①~⑤⑦~⑬ = **코드**, ⑥ = 코드 수치로 갱신, ⑭ = 한 줄 결정, ⑮만 사람 확정(CI-13) | S6a '착수 전 결정 필요' 1~4, R 4절 끝 |
| DF-12 | LUT 재생성(U-27) 착수 | 1주에 백그라운드로 시작(VS 0~1.8, CGS·CGB·SID_1F, 기계 약 22 h). 결과 전에는 VS 축 밖 조회 거부 | U-27 P 1104(계획 확정), LC 6절 5(VGS 100 mV급 오차), 협폭 DC 슬라이스는 E5 승인 | R P3, LC 6절 |
| DF-13 | matching 패턴 표 원문 대조 | `COMMON_CENTROID_PATTERNS`(PDF p.19)·`INTERDIGITATION_PATTERNS` '*' 표시(PDF p.15)를 저장소 안 원문 PDF와 1회 대조. 원문 PDF를 못 찾을 때만 사용자에게 출처를 묻는다 | 사용자 지시(기존 함수 재사용), 코드 주석의 재확인 권고 | R 정정 6 |
| DF-14 | MOD7 matching 함수 재사용 방식 | legacy import가 아니라 본문 복사 + 함수별 AST 해시 대조(`interdigitate_layout`·`common_centroid_layout`; 계획 LY4·design_mod7 L10, layout CONTRACT 복사 구현 완료. 옛 'import 재사용' 기본안은 정정) | 사용자 2026-10-07 "기존 함수를 이용해", R 정정 6 | NR 5.2 D-e |

**소멸(옛 엔진 동결로 더 묻지 않음)** -- 근거: 사용자 2026-10-07 새 엔진 재설계·R D17 답, R 0.5 "옛 엔진 국소 패치 기본안에서 뺌":

| ID | 항목 | 원 출처 |
|---|---|---|
| X-1 | `reserved_vds_for_other_stack_members` diode 예약을 lo로 바꿀지, 수정안 A(기둥 diode 창 콜백) | NM 6절 |
| X-2 | IC11 F1(compensation VDS 강등)·F1b | IC11 4절 |
| X-3 | 4회로 objective·기준선 변경 승인(DEC-40) | PA D9 |
| X-4 | `_metric_supply_current` 레일 극성(B26-2 D1)과의 순서 -- 새 엔진은 레일을 선언에서 읽고 공급 전류는 SPICE 레일 전압원 전류로 검증 | PA D10 |

**기본안 확정 가능 13건(DF-1~DF-14 중 DF-4 제외) + 소멸 4건 = 질문에서 뺀 17건.** G7 문서가 스스로 기본안으로 확정한 비해석 결정(W1 > W2 우선순위, G_vgs BFS 순서, y 창 정규화, SCC 필드 단위, tol_I 귀속, 봉인 순방향 재계산; G7 10절 끝)은 처음부터 질문 대상이 아니어서 세지 않았다.

---

## 8. 이미 답한 것 (중복 제거 기준, 넣지 않음)

| 항목 | 답 | 기록 |
|---|---|---|
| R D16 새 엔진 위치·이름 (= S6a 결정 5) | `skills/analog-gmid-design/gmid_engine/`, 파일 = 기능별 분할 | UD 2026-10-07 재설계·파일 구성 규칙 A~D |
| R D17 옛 엔진 작업 중단(Phase 3 이동) | 중단 | UD 2026-10-07 |
| R D4 면적 판정 축·MOD8 범위 (= PA D2, NR E4) | W_request 루프 범위 포함, 판정 축 재필터도 범위 안(front 점마다 MOD7 floorplan 외곽 면적, 동률 = 격자 한 칸; 옛 '보고만' 해석 철회) | UD 2026-10-07 12번 (나) |
| R D2 finger 폭 = W_ref 고정 (= LC 추천 1) | 철회(레이아웃이 matching을 고려해 finger_w·nf 선택, 총 W 보존) | UD 2026-10-07 레이아웃 규칙, R 정정 5 |
| R D3 협폭 DC 슬라이스 (= LC 추천 2) | finger_w 후보 = PDK 특성화 폭 슬라이스, 보간 금지 | UD 2026-10-07 E5 |
| NR E1 계획서 개정 24건 | 일괄 승인(gate 절 폐기 표시) | UD 2026-10-07 |
| NR E2 memo LRU 퇴출 | LUT memo에만, 실행 내 같은 키 재계산 0 | UD 2026-10-07 |
| NR E3 디스크 캐시 | S1 스냅샷·LUT 파생 표(지문 키) + 실패 캐시 | UD 2026-10-07 |
| NR E5 finger_w 후보 | PDK 특성화 폭 슬라이스 | UD 2026-10-07 |
| NR E7 design 승인 단위 | MOD별 짧은 design, 사용자 승인은 회로 해석 항목만(D0 인터페이스 별도 승인 불필요) | UD 2026-10-07 |
| 상태 구조(Circuit State Graph 단일 정본) | 확정 | UD 2026-10-07, NR 확정 사항 1~6 |
| 레이아웃 규칙 (c) 전부, 차동쌍 완화 순서, W 허용오차 식 | 채택 | UD 2026-10-07 |
| gate 잔여물 정리·gate 경량화 | 정리 완료, E1에서 gate 절 폐기 표시 | UD 2026-10-07 |
| 범위·기간 | 9회로 전부, 구조 유도 포함, 전력·면적 최소화 포함, 약 1달(합리적이면 2달) | UD 2026-10-07 |
| J1 바이어스 종속 넷 교류접지 예외 | 확정 | 2026-09-17 |
| J9 ports | 완료(U-08 9/9) -- passive는 CI-12 | DP 4.1 |


## 추가 (2026-10-07, design_mod1_lut_mod5_mna.md O2)

### CI-19. 되먹임 루프가 있는 회로의 PM 측정 대상: 루프 이득 T 인가 전달함수 H 인가
- AC-2(PM 루프 정의)·CI-10(파일럿 β 해석)과 함께 U2(3주 끝)에 묻는다. 6a 루프 분류(J11)와 함께 정한다. 출처: design_mod1_lut_mod5_mna.md 남은 결정 O2.
- 나머지 O1(tol_V 는 L 축만, VDS·VS 방향 LOO 는 보고만)·O3(전력 목적 = DEC-78 문언, power_dc_w 는 기록)·O4(첫 사이징점 finger_w 는 MOD4·MOD8 design) 는 기본안 확정 가능.


## 추가 (2026-10-07) -- 구조 유도 U2~U5 공동분석 J 항목 (design_mod3_structure_u2_u5.md 6절, 3주차 묶음)

J13-a 종류가 다른 병렬 합침(nmcnr RL ∥ M301) / J13-b 잎 가지치기 순서 / J13-c 3레일 레일 쌍 / J13-d 이상 전류원 가지 전압 자유 변수 / J13-e vertical_stack_id 대조 위치 / J-U3-a 교류접지 판정 / J-U3-b 역할 상속 / J-U3-c 미분류 DC 역할 묶음 4개 / J-U4-a 미러 L 동치류 / J-U4-b 차동쌍 후보 규칙 / J12-c v1·VDS-1 목록 / J12-f kvl_branch 종속 멤버 / J5 기본 전달 뷰. 기본안은 문서 6절 표.

## 추가 -- spec 형식 관련 신규 사용자 결정
- 파일럿 R1·R2(CMFB 감지 저항) 값 출처: 값도, 엔진 계산 기록도 없음.
- F5 요소 값 정본 = spec(topology 는 connectivity 만) -- 기본안 채택, 사용자 이의 없으면 유지.


## 추가 (2026-10-07) -- spec 로더 구현에서 나온 항목
- SP-10: 파일럿 current_reuse 의 CL1·CL2 가 각각 C_Ltot 1 pF 인지(차동 출력 양쪽 각각 1 pF) 아니면 합계 1 pF(각 0.5 pF)인지 -- 사용자 확정 '파일럿 부하 C_Ltot 1 pF' 의 해석.
- (해소) AC-1 포화 여유 = 0(8번 확정), CI-19 비파일럿 8회로 feedback = β=1(PM 정의 확정), SP-9 보상 소자 값 = 엔진 계산(nmcnr·two_stage 확정과 같은 원칙).
