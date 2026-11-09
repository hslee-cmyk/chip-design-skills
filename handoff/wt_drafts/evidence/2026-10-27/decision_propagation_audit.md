# 승인 결정 전파 감사 -- 계획·design·코드 (2026-10-27)

감사자: 독립 감사 agent(파일 수정 없음, 이 파일만 작성). 계기: Q1-2 (ii)·Q6-1 (A) 미전파가 CMP-1 시범 front 0의 원인(`wt/_drafts/evidence/2026-10-27/cmp1_verify_alternatives.md` C2 ★·D0).

기준:
- 결정 원문 `wt/_drafts/user_decisions.md`(1143줄), 결정 꾸러미 `wt/_drafts/engine/STEP2_DESIGN_GAPS_DECISION_PACKAGE.md`(733줄, 이하 PKG).
- 계획 = chip-design-skills master `1fefcab1`(v6.38.1, O-162): `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(이하 P) + history + headroom-chain·oracle-portability·graph-consumption·offset-strategy·offset-trim plan.
- design = `docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md`(D40)·`.41-gain-budget.design.md`(D41)·`.42-gap-checklist.design.md`(D42).
- 코드 = `wt/integ-it12` @ `ebad06c1`, `E` = `skills/analog-gmid-design/gmid_engine`. spec data = `skills/analog-gmid-design/assets/{library,heldout}`.
- 방법: 결정 키워드·개념 grep(P·history·D40~42·다른 계획), `git -C <repo> log --all -S`(docs·엔진 양쪽), 코드 file:line 직접 읽기. 줄 번호는 위 커밋 기준.
- 분류 어휘: **반영됨** / **계획 미반영** / **계획 반영·design/코드 미반영·card 없음** / **이후 결정으로 대체됨** / **판정 불가**. 섞인 결정은 부분마다 따로 적었다.

## 0. 요약표

★ = 엔진 동작(출발점·front·판정 결과)을 바꾸는 미반영.

| 결정 | 날짜 | 분류 | 옛 문언 자리(계획·design·코드) | 영향 | card 후보 |
|---|---|---|---|---|---|
| ★ Q1-2 (ii) 이득 L 하한 found_db 비례 g_i | 10-13 | 계획 미반영(**확인됨** -- CMP-1 재확인) | D41:1569, E/search/iv_context.py:49-51, iv_gain_l.py:99-101 | 이득 L 하한 비활성 → L = L_min 고착 → gain 제약 회로 front 0(CMP-1 two_stage 실측) | LA-1(L 역산 DEC-71 (4)(b)) |
| ★ Q6-1 (A) DEC-91 (2) W-bin 슬라이스 | 10-13 | 계획 미반영(**확인됨**) | P:290 DEC-91 (2), D41:964, E/sizing/pre_layout_widths.py:14-22 | 좁은 폭 소자 전류 −29~−67 %, 계통 offset +20 mV(CMP-1 C4·C5) | LA-1 또는 LI-1(새 범위) |
| Q1-2 (i) nmcnr·ngcc gain 제약 | 10-13 | 반영됨(spec data: nmcnr ≥ 100, ngcc ≥ 111) | -- | -- | -- |
| Q0 BLAS 두 조건 비트 동일 | 10-13 | 이후 결정으로 대체됨(NFR-4 BLAS 결정성, user_decisions:385-392 → P NFR-4) | -- | -- | -- |
| ★ Q1-1 매크로 망에 비출력 극점 노드(41 §6.5 N9) | 10-13 | 계획 반영(P DEC-104 R3 '망 정의는 design')·design 반영(D41:1610)·**코드 미반영·card 명시 없음** | E/search/macro_poles.py:3-4(망 = 블록 출력 + 수동소자 도달 넷) | 입력쌍 drain 용량·전류 분배를 못 봄 → nmcnr PM 35.7°, sf Cc 상자 하한(PKG G2·N7) | LA-1(매크로 블록 = R3 writer, 범위 13 B85와 같은 파일) |
| Q1-3 / Q-R1 knee 초기 L 층 0에만 | 10-14 | 반영됨(현행 유지) -- 단 재질의 조건('Q1-2 (ii) 반영 뒤 L_min 고착 남으면 다시 묻는다')이 Q1-2 미반영으로 평가된 적 없음 | -- | Q1-2 반영 뒤 재측정 필요 | LA-1 변화표 |
| Q2-1 매크로 목적 = 모든 MOS 가지 전류 | 10-13 | 이후 결정으로 흡수(DEC-104 R3, O-151 U5·U6 user_decisions:1063, O-157 S8) -- 코드 미반영 | E/search/macro_poles.py:270-273 `_power`(정해진 θ 전류만), :153-156 `zc_value`(전류 경유 gm_c) | nmcnr gm3 3~5배 과대, Rm 스탬프 누락 → PM 근 없음(PKG 2(a)) | LA-1(범위 13 B85·U5·U6) |
| ★ Q2-2 매크로 출발점에 개방 RHP 극점 수 P = 0 | 10-13 | 계획 미반영 | D41 §6.5:1623-1633(조건 없음), macro_poles.py:316-328 `feasible_start`(|H| = 1만) | SLSQP가 PM 평탄 −1 영역에서 출발(nmcnr·ngcc) | LA-1 |
| Q3-1 체계 오프셋 술어 P1s → §6.7 `mirror_vds` 행 | 10-13 | ★ 계획 미반영 | D41 §6.7-3:1699-1702(행 종류에 없음), E/search: §6.7 블록 자체 없음(`s0_fields.py:8` 'kvl_* 는 U17 ②') | nmcnr NodeM2 레일 근처(M109 VSD 0.15 V, 봉인 7 여유 5.8 mV) | LA-1(R6 블록 = §6.7 7a, P:1882) |
| Q3-2 바이어스 분배 쌍 P1s 제외('신호 경로' 조건) | 10-13 | 계획 미반영(Q3-1 종속) | 같음 | Q3-1과 함께 | LA-1 |
| Q3-3 offset_sys 확장 = 출력 기준 DC 선언 회로에만 | 10-13 | 반영됨(DEC-23 (나′) V_ref 선언 기준·`reference_undeclared` 정의 불능, O-53 B3·O-118·U-107) | -- | -- | DE-1 (c)(구현) |
| Q4-1 가드 입력 전류 = 매크로·KCL이 정한 전류만 | 10-13 | 부분 대체(자리값 삭제 = O-151 U5·U6) + **나머지(W 클램프 점 제외·hull 단조 구간) 계획 미반영·card 없음** | E/search/start_intervals.py:286(가드에 `refs` 자리값), iv_noise.py:61·iv_matching_l.py:136-(W = max(·, W_min)), _helpers_guard.py:86 `hull` | 가드 경계 음수 → 충돌(nmcnr 4+4, sf 12+12) | TB-1(R7 가드 필드 writer) |
| ★ Q4-2 합 가드 → §6.7 공동 선택(D) | 10-13 | 계획 미반영(P DEC-104 (3)(b) R7 = 'B 소자별 gm/ID 가드 구간'만) | P:303 (3)(b), D41:1583 §6.4-2a, _helpers_guard.py(나머지 최소 규약) | 부하 동시 상한 선택 시 합 초과(nmcnr θ0 offset·noise c < 0) | TB-1·LA-1(R6) |
| ★ Q5-1 (가) 슬루 비차단 하한(입력 소자 drain 노드 자유 가지 ≥ 입력 전류) | 10-13 | 계획 미반영(O-151 U5·U6이 같은 양의 하한 목록을 'W_min·R8·R10'으로 정하면서 (가)를 빠뜨림 -- 명시 대체 아님) | P:303 R3 하한 목록, D41:1640 '남는 θ 전류는 상자 기하 중심', start_intervals.py:124-129 | nmcnr 폴딩 가지 M108/M109가 W_min 하한에 놓임 → 가드 비 무의미·슬루 시 가지 꺼짐 | LA-1(U5·U6)·SB-1(하한 행) |
| Q5-1 (나) gm 요구 역산 | 10-13 | 이후 결정으로 흡수(DEC-104 R3 '필요 gm과 θ 전류를 같은 매크로 풀이가 KCL 기저로') -- 코드 미반영 | iv_currents.py:149-151·:181(미지 둘 이상 행 건너뜀, P:1837 B85) | folded 매크로 gm이 θ 전류로 안 감(O-140 D8) | LA-1 범위 13 |
| Q5-1 재측정 문구(② 완료 조건) | 10-13 | 계획 미반영(D40 §10.5 U17 ② 완료 조건:2033-2041에 없음) | -- | 측정 항목 누락(동작 무관) | U17 ②·LA-1 변화표 |
| D1 W_min 왕복 반올림이 mismatch bin 밖(1 ulp) | 10-13 | 결정 불필요(구현 결함) -- **미수정·card 없음** | E/lut/_helpers_bins.py:6-14(1 ulp), E/sizing/block_widths.py:47 | 외층이 W = W_min 경계에 닿으면 `lut_mismatch_no_block` 봉인 실패(빈도 미측정) | 새 결함 card(또는 LA-1 범위) |
| Q-N1 (A) 정착 → GBW 목표 유도 ε = 1/(1+A0β) | 10-14 | 이후 결정으로 대체됨(O-133 static 오차 spec·gain 삭제 user_decisions:927, O-139 ω_c ≥ ln(1/ε)/t_s 출발 목표 :962) -- 대체 규칙도 코드 미반영 | macro_poles.py:22 '`gbw_target_missing` → 매크로 안 돎', iv_context.py:25 | current_reuse 매크로 꺼짐 → 전 가지 자리값(B81 원인 후보) | LA-1(O-139 'S 분류·출발 목표') |
| ★ Q-N2 B 면적 조건 → gm/ID 하한(L 하한 아님) | 10-14 | 계획 미반영 | P:681 LR6 '하한은 mismatch 임계값'(L 하한), D41:1581, E/search/iv_matching_l.py:84-103 `_l_lower`(g_lo에서) | current_reuse 입력 L 2.5/3.22 µm → 입력 CM 창 닫힘(M4a VDS −0.041 V) | LA-1(LR6)·offset-strategy G-S2 |
| Q-N2 C 입력 CM 창 비어 있지 않음 행 | 10-14 | 이후 결정으로 흡수(DEC-104 (0) R-1′ 모든 KVL 고리 + R5′, O-127·O-142) | -- | -- | TB-1·HC-1 |
| ★ Q-N2 D 절대 offset·잡음 회로에도 부하 가드 | 10-14 | 계획 미반영 | P:303 (3)(b)·D41:1583(구조 가드 metric 회로만), iv_matching_l.py:107-118, iv_noise.py:73-75 | 절대 제약 회로(current_reuse)의 σ_share = σ/√2 전제가 걸리지 않음 | TB-1(R7 가드 필드) |
| ★ Q-N3 (A) CMFB DC 평형 등식을 S1 전류 기저에 | 10-14 | 계획 미반영 | D40 §5(CM 루프 정의·PM만), D41 §6.7(VGS·VDS 행만), E/graph current_basis·E/sizing/writer_plan.py | current_reuse Ncmfb_tail 창 빔·봉인 7 실패(B81 current_reuse 봉인점 없음과 같은 회로) | TB-1(θ 기저 S0 필드)·LA-1 |
| Q-N4 (가) 출발 y = V(out)=V(in_dc) 근 + β=1을 출력 기준으로 읽어 offset_sys 켬 | 10-14 | 이후 결정으로 대체됨 -- 출발: O-142 R5′ (2)(미선언 W4 = 동작 조건, 창 안 max-min, user_decisions:983); 판정: O-53 B3(단일 출력 기준 미선언 = `reference_undeclared`, 추론 금지, :673) | -- | sf 출력 기준은 spec 선언(입력 추종 종류)이 있어야 판정됨 -- spec data에 없음(관찰) | SF-1(spec 선언) |
| Q-N5 A θ 저항을 §6.7 공동 선택 변수로 / C 전류 0 저항 = gain 손실 최소 R | 10-14 | 이후 결정으로 대체됨(A: O-127 (iii) V_R 결정 변수·O-142 R5′ (2); C: O-157 S6 '전류 0 DC 저항은 spec 상자 안 θ 독립 성분', :1104) | -- | -- | LA-1 |
| Q-N6·Q-N7·Q-N10 기본안(새 규칙 없음·재측정) | 10-14 | 반영 불필요(재측정 항목) -- 단 재측정 항목이 ② 완료 조건에 등록 안 됨; N7 원인(PM 미정)은 Q-S2로 해소 | -- | 없음 | LA-1 변화표 |
| Q-N8 B 출발 y = 포화 창 중앙(VDSAT 포함) | 10-14 | 이후 결정으로 대체됨(O-142 R5′ (2) 포화 행·writer_root 행 창 안 max-min) | E/sizing/block_columns.py:11-17 `free_window`(VDsat 없음, O1 열린 항목) | -- | LA-1(R6) |
| Q-N9 (A) 캐스코드 술어 P1c → `mirror_vds` | 10-14 | ★ 계획 미반영(Q3-1과 같음) | D41 §6.7-3 | sf 거울 복사쌍 밀도 불일치(ln_idu −23.7 대 −15.2) | LA-1(R6) |
| ★ Q-N11 B 잡음·ss metric 분해능 Δp = |∂ln p/∂VGS|·tol_V·|p| | 10-14 | 계획 미반영(metrics CONTRACT 9.1 미개정) | E/metrics/ss_linearize.py:11·:74 `lut_rel_tol = gm_id·tol_v`, lut_parameters.py:8 | current_reuse 잡음 분해능 440 µV(값의 61 %) → 잡음 판정 사실상 보류; 모든 ss metric 분해능 과대 | card 없음(새 card 필요) |
| Q-S1 (라) sf 동시 실현 불가 확인 뒤 (가) | 10-14 | 판정 불가 -- (라) 확인 미완(sf는 B81로 봉인점 자체가 없어 '잡음 때문에 front 빔' 판정 못 함), spec `noise_excess_th <= 2` 유지는 결정대로 | -- | -- | LA-1 뒤 재측정 |
| Q-S2 PM ≥ 70 (sf·two_stage·two_stage_sf) | 10-14 | 반영됨(spec data·D40:1776-1780) | -- | -- | -- |
| Q-S3 current_reuse 잡음 ≤ 450 µVrms | 10-14 | 반영됨(spec data 0.00045·D41:1759) | -- | -- | -- |
| ★ N12 `counted_rails` spec 선언·held-out B·D 공급 전류 판정 | 10-14 | 계획 미반영(P:654·:1974는 백로그 언급만) | heldout erfc·cnr `pending_constraints supply_current_dc U-75`, E/search/find_front.py(`not_computed`) | held-out B(10.4 µA)·D(92 µA) 공급 전류 제약이 판정에 안 들어감 | SF-1 |
| ★ N13 held-out B CBAT θ 상자 = 엔진 보상 소자 공통 규칙 | 10-14 | 계획 미반영(규칙 없음, spec에 상자 없음) | heldout/erfc_ota.sizing_spec.json(CBAT engine, theta_bounds 없음) | held-out B 탐색 전 `theta_*_bounds_undeclared` 거부 예상(PKG N13) | SF-1 |
| 결정 10 code_hash 경로 의존 | 10-14 | 반영됨(D40 v1.9.3) | -- | -- | -- |
| A' (3)·①②③ | 10-13 | 반영됨(P DEC-98, D40 §10.5) | -- | -- | -- |
| SYNTHESIS Q1~Q12 | 10-07 | 반영됨(history:930-943 → DEC-87~93) | -- | -- | -- |
| 10-08 design v1.2 Q1~Q11, Q3·Q4 | 10-08 | 반영됨(DEC-78 Q6, U-58 Q10, U-55 Q3·Q4, DEC-21·DEC-23) | -- | -- | -- |
| O-1~O-162 N2.1 행 | 10-16~10-27 | 반영됨(gain-budget 관련 O-번호는 P N2.1 또는 다른 계획에 있음). 계획 전체 grep 0인 O-12·O-17·O-39·O-42·O-77·O-84·O-93·O-99·O-102~O-105는 design 승인·card dispute·승인 범위 결정이라 design·card 몫(§4) | -- | -- | -- |

미반영 요약(엔진 동작을 바꾸는 것, 확인됨 2건 포함 14건): Q1-2 (ii), Q6-1 (A), Q1-1(코드), Q2-2, Q3-1·Q3-2·Q-N9(`mirror_vds`), Q4-2, Q5-1 (가), Q-N2 B, Q-N2 D, Q-N3, Q-N11, N12, N13. 동작 무관 미반영: Q4-1 잔여(W 클램프·hull), D1(결함 미수정), Q5-1·Q-N6/7/10 재측정 항목 미등록.

공통 원인(관찰): PKG(2026-10-13 2차 갱신·10-14 결정 반영 절)의 결정은 '단계 ② design 보완' 항목으로 정리됐으나, design 41 §6 개정·계획 N2.1 행·U17 ② 완료 조건(D40:2033-2041) 어디에도 옮겨지지 않았다(`git -C chip-design-skills log --all -S"STEP2_DESIGN_GAPS"`·`-S"mirror_vds"`·`-S"Q6-1"`·`-S"Q1-2"` 모두 0건, 엔진 저장소 `-S"mirror_vds"`·`-S"guard_current_ratio_undefined"` 0건). 그 뒤 O-번호 체계(10-16~)가 같은 양을 일부 다시 결정(DEC-104 R3·R5′·R7, O-53, O-139)하면서 PKG 결정을 인용하지 않아, 대체된 것과 빠진 것이 섞였다.


## 1. 묶음 A -- 단계 ② 결정 꾸러미 2026-10-13 (원문 user_decisions:300-316, PKG 결정 상태 표 :10-29)

원문: 307-311 "Q3, Q5, Q6는 모두 권고대로 해", 313 "Q1-2는 (ii) 권고대로, (i)는 추가", 315 "nmcnr은 승인, ngcc는 논문값 참조". PKG 표는 Q0·Q1-1·Q4-1을 '(가) 바로 진행', Q1-3·Q2-1·Q2-2·Q4-2를 '(나) 기본안'으로 적었고 2026-10-14 '결정 반영' 절(PKG:725-726)이 Q-R1·Q-N·Q-S·N12·N13까지 '전부 사용자 확정'으로 닫았다. 따라서 '기본안' 항목도 승인 결정으로 셈한다.

공통 사실(직접 확인):
- `git -C chip-design-skills log --all --oneline -S"STEP2_DESIGN_GAPS" -- docs` 0, `-S"mirror_vds"` 0, `-S"Q6-1"` 0, `-S"Q1-2"` 0, `-S"P1s"` 0, `-S"W-bin"` 0, `-S"found_db 비례 g_i"` 0.
- `git -C wt/integ-it12 log --all -S"mirror_vds"` 0, `-S"guard_current_ratio_undefined"` 0.
- D40 §11 '② search 상태·층 0' 행(D40:2093)과 'U17 단계 ② 완료 조건'(D40:2033-2041)에 PKG 항목이 없다(DEC-98 A' 판정만).
- D41 §6 상태 문장 '**상태**: MISS. as-built는 spec과 무관한 LUT 포락선 상자 중점'(D41:1671)은 그대로다.

### A-1. Q1-2 (ii) -- 확인됨(CMP-1 재확인 C2 ★·D0, 다시 재지 않음)
- 원문 user_decisions:313. 옛 문언 D41:1569 "A_max가 미상이거나 gain 제약이 없으면 비활성이다(H3)". 코드 E/search/iv_context.py:49-51, iv_gain_l.py:99-101.
- card 후보: LA-1(범위 1 '목표 이득의 gm/gds → 같은 bin 안 L' 역산, 첫 회차 예산 = found_db 비례 L-2와 같은 g_i -- 같은 양을 출발 구간 §6.4-1에도 쓰는 것). 계획 N2.1 행 신설 필요.

### A-2. Q6-1 (A) -- 확인됨(CMP-1 재확인 C4·D0)
- 원문 user_decisions:310. 옛 문언 P:290 DEC-91 (2) "레이아웃 전 첫 사이징점은 LUT 생성 규칙의 확산 기하를 쓴다", D41:964, 코드 E/sizing/pre_layout_widths.py:14-22(kind마다 `w_ref_m` 슬라이스 하나).
- card 후보: LA-1(층 0 W 파생 '커널 W 계산 블록과 같은 함수'가 슬라이스를 고름) 또는 LI-1(layout 입력 정본화, N6.12). DEC-89 (1) W_need(fw) 정의와 같은 꼴(LR3 bin 안)이라 정본 자리는 DEC-91 (2) 개정 + DEC-89 인용.

### A-3. Q0 -- 이후 결정으로 대체됨
- PKG:12 '② 완료 조건에 두 실행 조건 비트 동일'. 2026-10-15 'NFR-4 BLAS 결정성'(user_decisions:385-392) 1안(엔진 BLAS 스레드 1 고정·환경 지문 S0 키)이 같은 문제를 다른 방식으로 닫았고 P NFR-4(:188)·D40 v1.9.4에 반영됨.

### A-4. Q1-1 -- 계획·design 있음, 코드 미반영, card 명시 없음
- PKG:13 '항목 1 A(41 §6.5 N9 구현) 먼저'. design 문언은 이미 있다: D41:1610 "출력노드가 아닌 극점 노드(캐스코드 source 노드 등, N9): 낮은 등급 단자를 주는 소자 c의 gm_c + gmb_c를 컨덕턴스로". P DEC-104 R3(:303)은 '망 정의는 design', 망 밖 극점 θ 전류는 '극점 미포함' 기록.
- 코드: E/search/macro_poles.py:3-4 모듈 머리 "**망**(전달 뷰): 노드 = 이득 블록의 출력 넷 + 그 넷에서 수동소자(커패시터·저항)만 거쳐 닿는 내부 넷" -- N9 노드 없음.
- 영향(PKG G2·N7 실측): nmcnr in015 PM 35.7°, sf 매크로 PM 48.5°가 Cc 하한에서 만족(망 노드 {Y, vout} 둘뿐) → Cc 상자 하한. 비주극점 노드를 못 보는 출발 전류 분배.
- card 후보: LA-1(DEC-104 R3 writer = 매크로 블록, 범위 13 B85가 같은 파일군 `iv_currents`·`macro_poles`). LA-1 범위 문언에 'D41 §6.5 N9 노드 구현'이 없어 명시 필요.

### A-5. Q1-3 / Q-R1 -- 반영됨(현행 유지), 재질의 조건 미평가
- 원문 user_decisions:371 "Q1-3 기본안 = 현행 유지(knee 초기 L은 층 0에만)… 항목 1 A·Q1-2 (ii) 반영 뒤 L_min 고착이 남는 회로가 있을 때만 다시 묻는다". 현행이 결정이므로 문서 변경은 필요 없다. 그러나 전제(항목 1 A·Q1-2 (ii))가 반영되지 않아 재질의 조건을 잴 수 없었다. CMP-1 two_stage·folded의 `l_chosen = 1.5e-7` 전 소자(cmp1_verify_alternatives C2 ④)는 Q1-2 미반영의 결과라 이 조건의 근거로 쓰면 안 된다(결함을 근거로 쓰지 않음).

### A-6. Q2-1 -- 이후 결정으로 흡수, 코드 미반영
- PKG 2(e) A(1) 영점 상쇄 구성 소자가 블록 입력 소자면 gm_c = gm_b, A(2) 목적 = 모든 MOS 가지 전류(블록 입력 전류 아핀 포함), A(3) UGF 없는 해 = `macro_nonconvergent`.
- 계획: P DEC-104 R3(v6.38.1 O-151 U5·U6, user_decisions:1063; O-157 S8 보충) "필요 gm과 θ 전류는 같은 매크로 풀이가 KCL 기저 행(`dc_current_basis`)을 통해 함께 정한다 -- 한 KCL 행에 미지 θ 전류가 둘 이상 남으면 남는 자유도는 같은 '전원 전류 최소'의 변수다 … 상자 중심·기하 평균 자리값은 쓰지 않는다". A(2)의 취지(미정 가지도 목적에 든다)를 더 일반형으로 덮는다. A(1)·A(3)은 '정의상 자명한 구현 결함'(PKG 2(b))이라 계획 문언이 따로 필요 없다.
- 코드(미반영): macro_poles.py:153-156 `zc_value` = Σ I_c·(gm/ID)_c(전류 아핀 없는 소자는 빠짐 → Rm 스탬프 생략), :270-273 `_power` = `ctx.basis.free` 중 `model.affine`에 있는 원소만.
- 영향(PKG 2(a)): nmcnr Rm 누락으로 NodeCM 부유 → PM 근 없음, Rm 넣은 뒤에도 gm3 3~5배 과대.
- card 후보: LA-1(범위 13 B85 + U5·U6 'LA-1 변화표 확인', O-155 M-4 'LA-1 범위에 U5·U6 명시').

### A-7. Q2-2 -- 계획 미반영
- PKG 2(e) B: `feasible_start`가 |H| = 1만 보지 않고 pencil 극점 RHP 수 0도 요구, 아니면 뒤 블록 gm 2배 사다리.
- 계획·design: P:489·D41:379의 'P = 0'은 **최종 안정도 판정**(J-B)이고 매크로 **출발점** 조건이 아니다. D41 §6.5 '풀이 순서와 실패 처리'(:1623-1633)·as-built(:1644-1649)에 없음.
- 코드: macro_poles.py:316-328 `feasible_start`(|H(jω_GBW)| = 1 근만, RHP 검사 없음).
- 영향: SLSQP가 `_signed_pm` −1 평탄 영역에서 출발(PKG 2(d) B, 매크로 활성 5회로). nmcnr 시범 θ0 'k ≥ 1 출발'.
- card 후보: LA-1(매크로 블록).

### A-8. Q3-1·Q3-2 -- 계획 미반영
- 원문 user_decisions:308 "체계 오프셋 술어 P1s … 41 §6.7 출발 공동 선택의 목표 행 `mirror_vds`(VDS_o − VDS_d = 0, 위반 최소 단계, 해 없으면 StartConflict)로(A), θ 묶음(B) 아님. Q3-2 파일럿 바이어스 분배 쌍 … 제외 -- '신호 경로' 조건은 design에서 정의".
- 계획: P DEC-104 R5′(:303) 고리 = R-1′ 제약 그래프 변·순환 + writer_root 행. 미러 VDS 같음 행은 KVL 고리가 아니므로 R-1′에 들지 않는다. O-118 (나′) 성분 (1)이 계통 offset을 **판정** 쪽에서 재지만 **출발** 행은 아니다.
- design: D41 §6.7-3(:1699-1702) 행 종류 = `loop_lo`·`loop_hi`·`saturation`·`writer_root`뿐.
- 코드: §6.7 블록 자체가 없다(E/search/s0_fields.py:8 "`kvl_model`·`kvl_rows`·KVL 기록 … 은 U17 ②"; `iv_kvl.py` 없음).
- 영향(PKG 3(a)): nmcnr NodeM2 = VDD − VSG201 → M109 VSD ≈ 0.152 V, 봉인 7 최악 여유 5.8 mV; 출발점이 체계 오프셋 0 근처에 오지 않음.
- card 후보: LA-1의 R6 블록 구현(P:1882 'R6 블록(출발 단계 §6.7 7a 확장, 층 0 공용)… 이 card(U17 ② §6.7과 같은 통합 병합)가 구현') -- R6 행 목록에 `mirror_vds`를 넣는 계획 개정 필요. 술어(S1 구조 사실) 자리는 TB-1 분류 필드 옆.

### A-9. Q3-3 -- 반영됨
- 원문 user_decisions:308 "offset_sys 제약 확장은 출력 기준 DC가 선언된 회로에만".
- 계획: P DEC-23 (나′) V_ref = '출력 기준의 정의 자리'의 선언 기준, O-53 B3 "단일 출력에 선언이 없으면 `reference_undeclared` 정의 불능(fail-closed, 기준을 추론하지 않는다)", U-107 기준 도달 불가. 같은 취지가 더 엄밀하게 들어 있다. 구현 = card DE-1 (c).

### A-10. Q4-1 -- 부분 대체, 잔여 미반영
- PKG 4(d) A: 가드 입력 = 매크로·KCL이 정한 전류만(자리값 금지), W 클램프 점(W = W_min으로 잘린 g) 제외, `hull`은 단조 구간 안에서만.
- 대체된 부분: 자리값(`refs`) 자체를 없애는 결정 O-151 U5·U6(P DEC-104 R3 '상자 중심·기하 평균 자리값은 쓰지 않는다').
- 미반영 부분: W 클램프 점 제외·hull 단조 구간 규칙은 계획·design에 없다(D41 §6.4-2a:1583, §7.5). 코드: E/search/start_intervals.py:286 `currents1 = {… first.refs.get(n)}`(자리값을 가드에 넘김), iv_noise.py:61 `w = max(current * L / IDu, ctx.w_min_m)`, iv_matching_l.py:63(같은 꼴, 주석 'W 하한 제약 S-18'), _helpers_guard.py:86 `hull(...)`.
- 영향(PKG 4(a)): nmcnr 입력:부하 전류비 1:35~1:6×10⁴ → 가드 경계 음수(offset 4·noise 4 충돌), sf 12+12 충돌.
- card 후보: TB-1(R7 가드 필드 writer = '기존 가드 계산을 이 필드에 씀') -- 옮기면서 정정하거나, 정정 없이 옮기면 결함이 정본 필드로 들어간다.

### A-11. Q4-2 -- 계획 미반영
- PKG 4(e) D: 합 가드(Σ부하 ≤ ratio·Σ입력)를 41 §6.7 공동 선택(위반 최소 → max-min)에 넣는다(소자별 상한은 필요조건일 뿐).
- 계획: P DEC-104 (3)(b) "R7 matching·잡음 가드 필드(B 소자별 gm/ID 가드 구간 -- design 41 §6.4-2a·§7.5 가드의 정본)", R7 (가) '가드 구간과의 교집합' -- 소자별 구간만 있고 합 조건 행이 없다. D41:1583도 '부하 gm/ID를 상한으로'.
- 영향: §6.1-7·R7이 여러 부하를 동시에 구간 위쪽으로 고르면 합이 넘침(nmcnr θ0 offset_excess·noise_excess c < 0, PKG 4(a) 4).
- card 후보: TB-1(가드 필드 형식에 합 행 포함)·LA-1(R6 K-1 공동 선택이 합 행을 읽음).

### A-12. Q5-1 -- (나) 흡수·(가) 미반영·재측정 문구 미반영
- 원문 user_decisions:309 "(나) gm 요구 역산 … + (가) 슬루 비차단 하한(입력 소자 drain 노드에서 KCL로 만나는 자유 가지 전류 ≥ 그 노드로 들어오는 입력 소자 전류)을 함께. 5(c) 재측정 문구를 ② 완료 조건으로 채택".
- (나): P DEC-104 R3('필요 gm과 θ 전류는 같은 매크로 풀이가 KCL 기저로', '그 전류가 gm을 정하는 소자의 노드 극점이 매크로 망 안에') -- 흡수. 코드 미반영(iv_currents.py:149-151·:181 미지 둘 이상 행 건너뜀, P:1837 범위 13 B85).
- (가): P DEC-104 R3 "교류 요구가 닿지 않는 θ 전류(순수 바이어스 가지)는 그 최소화에서 하한 행들(W ≥ W_min의 전류, R8·R10)의 최대에 놓인다"(O-151 U5·U6, 2026-10-26). 하한 행 목록에 (가)가 없다. R10은 선언 슬루율이 있을 때만 정의되는 동적 요구라 (가)(슬루 spec 불필요한 KCL 비차단 조건)와 다른 양이다. O-122(엔진 슬루 손계산 경계 삭제)는 슬루 **판정**·**SR 경계** 행을 지운 것이라 (가)를 명시적으로 대체하지 않았다 -- 그러나 O-151이 (가)를 인용하지 않고 같은 양의 하한을 정했으므로 '대체 의도였는지'는 사용자 확인 대상.
- 옛 문언: D41:1640 "남는 θ 전류는 상자 기하 중심이다"(R3로 낡음), 코드 start_intervals.py:124-129 `refs`.
- 영향(PKG 5(b)): 자리값 쓰는 6회로(nmcnr 8소자, folded 13, current_reuse 27 등) -- R3 적용 뒤에는 W_min 하한에 놓여 폴딩 가지 전류 < 입력 전류인 점이 출발점이 될 수 있다(nmcnr 손: I_c ≥ I_D1).
- 재측정 문구(PKG 5(c) 표 (1)~(5)): D40 §10.5 'U17 단계 ② 완료 조건'(:2033-2041)에 없음.
- card 후보: LA-1(U5·U6) 또는 SB-1(R8·R10 하한 행 구현 card -- 하한 행 목록에 추가).

### A-13. D1 W_min 반올림 -- 결함 미수정, card 없음
- PKG 8.1. 코드 E/lut/_helpers_bins.py:6-14 경계 비교 허용 1 ulp 그대로, 왕복 오차 수십 ulp(10만 점 중 37.6~39.9 %가 bin 밖, PKG 재현 2). 엔진 출발점은 start_intervals.py:140 `w_min_m * (1 + _REL)`로 피하지만 외층 W 하한 행은 W = W_min 경계를 허용.
- 영향: 탐색이 W_min 경계에 닿으면 `lut_mismatch_no_block` 봉인 실패(빈도 미측정). 결정 불필요 항목이라 계획 미반영은 정상이나 결함 기록(DF/backlog)도 없다(P DF 표 grep 0).
- card 후보: 새 결함 card 또는 backlog 등록.

## 2. 묶음 B -- 2026-10-14 단계 ② Q-N·Q-S·Q-R1·N12·N13 (원문 user_decisions:366-373, PKG §7·§9·부록 N12·N13)

원문: 366 "Q-N은 Q-N4만 제외하고 권고대로 해" → Q-N1 A, Q-N2 B+C+D, Q-N3 A, Q-N5 A+C, Q-N8 B, Q-N9 A, Q-N11 B 먼저 후 C(Q-N6·N7·N10은 기본안); 369 Q-N4 (가); 367 Q-S; 368 N13; 373 N12. 주의: 계획 P:2340-2349의 'Q-N1~Q-N10'(U-77~U-86)은 **다른 결정**(2026-10-15 NFR-4 세부)이라 이름 grep 적중은 이 묶음과 무관하다.

### B-1. Q-N1 (A) 정착 → GBW 목표 -- 이후 결정으로 대체됨
- PKG 7.1 (d) A: `gbw_target_hz`가 없고 settling·gain·β가 있으면 GBW = ln(1 + A0·β)/(2π·β·t_lin)(ε = 1/(1+A0β) '동적 = 정적').
- 대체: O-133(user_decisions:927, current_reuse `gain_ss_db >= 54` 삭제, 원천 spec = static 오차 0.1 %, 손계산 출발값 1/(β·ε)), O-139(:962-970, 엔진 = 루프 대역폭 하한 ω_c ≥ ln(1/ε)/t_s '추정', 용도 = S 분류(매크로 활성)와 출발 목표만, gbw_target_hz 사본 금지). P:645 정착 측정 정의. 같은 목적(정착 spec만 있는 회로에서 매크로를 켬)을 다른 식으로 결정했다.
- 코드(대체 규칙도 미반영): macro_poles.py:22 "GBW 목표 없음: 매크로 모델을 돌리지 않는다(`macro_inactive`, 사유 `gbw_target_missing`)", iv_context.py:25 `_KEY_GBW`만 읽음.
- card 후보: LA-1(O-139 'S 분류·출발 목표', O-141 (7) 'current_reuse는 O-139 대역폭 하한으로 S 분류가 켜지는지 먼저 확인').

### B-2. Q-N2 -- B·D 계획 미반영, C 흡수
- B(면적 조건 → gm/ID 하한, L은 다른 경계가 정함): P:681 LR6 "하한은 mismatch 임계값이다(2026-10-08 Q3: 절대 offset 제약 `offset_in_sigma_mv`가 있는…)" -- L 하한 그대로. D41:1581 "**L ≥ √(A_min·IDu/I)**". offset-strategy plan:212·:304·:619는 'L 하한 규칙 정본은 gain-budget LR6'이라 인용만. LA-1 범위 1 "LR6 경계 안 -- … 하한 mismatch 임계값". 코드 E/search/iv_matching_l.py:84-103 `_l_lower`(gm/ID_lo 강반전 끝에서 L을 풂).
  - 영향(PKG 7.2 (a)): current_reuse 입력 L 2.5·3.22 µm → θ0 M4a VDS −0.041 V(입력 CM 창 [VDSAT5 + VGS4, VDD − VSDsat6 − VSG1]이 L = 0.15·약반전에서만 열림), 긴 L이 Cin을 키워 β 붕괴. 손은 면적을 W로(M1 25.97/0.15, SPICE σos 3.34 mV).
- C(입력 CM 창 비어 있지 않음 행): 흡수 -- P DEC-104 (0) "θ의 독립 성분은 모든 KVL 고리(MOS 채널·게이트–소스·저항 엣지)에서 종속 성분을 제거한 기저 … 고리 = R-1′ 제약 그래프", R5′ 포화 행. 입력 경로 레일-레일 고리의 포화 행이 같은 사실을 덮는다(O-127·O-142). 구현 = TB-1(R-1′ S0 필드)·HC-1·LA-1(R6).
- D(절대 offset·잡음 회로에도 부하 가드 '부하 ≤ 입력'): P DEC-104 (3)(b) R7 가드 = 'design 41 §6.4-2a·§7.5 가드의 정본' -- 그 design 문언(D41:1583 "`offset_excess <= √2` 회로")은 구조 가드 metric 회로만. 코드 iv_matching_l.py:107-118·iv_noise.py:73-75 가드 조건이 `offset_excess`·`noise_excess_th` 선언에서만. → 계획 미반영.
  - 영향: 절대 제약 회로(current_reuse)에서 §6.4-2의 σ_share = σ_target/√2 전제(부하 ≤ 입력)를 거는 경계가 없음(PKG 8.3 R2 → N2 D).
- card 후보: B = LA-1(LR6 개정, 범위 1)·offset-strategy G-S2(같은 출발값 자리); D = TB-1(R7 가드 필드).

### B-3. Q-N3 (A) CMFB DC 평형 -- 계획 미반영
- PKG 7.3 (d) A: CM 평형 등식을 S1 전류 기저에 -- 오차 쌍(gate가 감지 넷·기준 넷인 같은 kind 쌍, 공통 source) 전류 같음 + 출력 CM 노드 DC = 기준 넷 DC(쓰기 계획 고정 노드).
- 계획·design: '평형' grep P·D40·D41 모두 0. D40 §5(CM 루프 정의·절단 분류·PM)·P:668(`pm_cm_ss_deg`)는 소신호 판정뿐. O-115(ICMR servo '차동 출력은 DM 고정·CM은 CMFB')는 측정 구성이고 출발 동작점 규칙이 아니다.
- 코드: E/graph current_basis(user_decisions 2026-10-12 '3번' 규칙)·E/sizing/writer_plan.py에 CM 평형 행 없음(grep 'cmfb' 적중은 spec_views·view_analysis·layout·current_symmetry·ss_constraints뿐).
- 영향(PKG 7.3 (a)): current_reuse M6·M36a·M36b·M39·M40 전류가 독립 θ → layer0 808점 뒤에도 봉인 7 `no_root_in_window`(M37b, Ncmfb_tail 창 [0, 0.249 V]). B81(current_reuse 봉인점 없음)·LA-1 완료 조건의 current_reuse '따로 보고'와 같은 회로 -- 원인 후보로 계획에 등록돼 있지 않다. held-out D(cnr_ota, 저항 CMFB)도 대상.
- card 후보: TB-1(θ 기저 S0 필드 -- 평형 등식은 θ 축 감소 = 기저 정의)·LA-1(current_reuse 원인 분석). P:1882·O-142의 'current_reuse 해결 선행 = LA-1 design'에 이 결정을 넣어야 한다.

### B-4. Q-N4 (가) -- 이후 결정으로 대체됨(출발·판정 둘 다)
- 원문 :369 "단계 A에서 V(out)(y) = V(in_dc)인 y를 41 6.7-2 출발 전위 모델 1-D 근으로 구해 출발 y로, 판정은 Q3-3 offset_sys 제약을 켬".
- 출발: O-142 R5′ (2)(user_decisions:983-990; P DEC-104 R5′ (2)) "미선언 W4와 정의 고리 없는 V_R = 동작 조건, 모든 포화 행·writer_root 행을 함께 만족하는 창 안에서 고름"(max-min, O-151 N-2) -- 같은 좌표(출력 사슬 y)를 다른 규칙으로 정함.
- 판정: O-53 B3(user_decisions:673; P DEC-23 '출력 기준의 정의 자리') "단일 출력에 선언이 없으면 `reference_undeclared` 정의 불능(fail-closed, 기준을 추론하지 않는다)", 선언 종류에 '(입력 추종) 출력이 입력 공통모드를 따름'. Q-N4의 'β = 1을 출력 기준 = 입력 DC로 읽음'(추론)은 이 규칙과 반대라 대체로 본다.
- 관찰(결정 아님): sf_pushpull_output_opamp spec에 출력 기준 선언(입력 추종 종류)이 없다(`grep output_reference` 0) -- Q-N4가 노린 offset_sys 판정을 sf에서 켜려면 SF-1 spec 선언이 필요하다. 사용자 확인 대상.

### B-5. Q-N5 A+C -- 이후 결정으로 대체됨
- A(DC 전류 있는 θ 저항을 §6.7 공동 선택 변수로): O-127 (iii)(:881-888) "값 미선언 DC 경로 저항은 강하 V_R 이 결정 변수, R = V_R/I_R 파생", O-142 R5′ (2) V_R = 동작 조건 max-min. P DEC-104 (0)·R5′.
- C(DC 전류 0 저항 = gain 손실 허용 안 최소 R): O-157 S6(:1104-) "θ점 DC 전류 0인 DC 경로 저항(current_reuse R1·R2)은 R을 θ 독립 성분(spec 상자 안)으로(O-127 (iii) 적용 범위 축소)" -- 다른 규칙으로 대체. spec element_values R1 출처 문언('최소 저항')은 2026-10-07 원문 기록으로 남아 있다(정본 아님 -- 관찰).

### B-6. Q-N6·Q-N7·Q-N10 -- 반영 불필요(재측정 항목), 재측정 등록 없음
- 셋 다 '새 규칙 없음, ② 뒤 재측정'. 재측정 항목(N6: sf M21·M22 ln_idu·M17/M20 VDS 행, N7: 세 회로 Cc, N10: current_reuse 봉인 7 최악 소자)이 D40 §10.5 U17 ② 완료 조건에 없다. N7 원인 중 'PM 목표 없음'은 Q-S2(PM ≥ 70)로 해소, 'N9 노드 부재'는 Q1-1 미구현으로 남음.

### B-7. Q-N8 B -- 이후 결정으로 대체됨
- 출발 y = 출발 gm/ID·L의 VDSAT으로 낸 포화 창 중앙. 대체 = O-142 R5′ (2)(포화 행 = `sat_threshold` 정본, 창 안 max-min). 커널 쪽 O1(`free_window` VDsat 없음, E/sizing/block_columns.py:11-17)은 열린 채 -- O-151 M3 '커널이 종속 W4를 노드 전압 목표로 받음'(LA-1)이 관련.

### B-8. Q-N9 (A) P1c -- 계획 미반영(A-8과 같은 자리)
- 원문 :366(Q-N9 예(A), P1c). PKG 7.9 실측 6 인스턴스 3회로(folded 2·nmcnr 1·sf 3). 영향: sf 거울 복사쌍 밀도 불일치(M5/M7/M11 ln_idu −23.7 대 M10/M12 −15.2), R1a 3 µA 대 M9 9.8 µA. card 후보: LA-1(R6 행 목록).

### B-9. Q-N11 B -- 계획 미반영, card 없음
- PKG 7.11 (d) B: Δp = |∂ln p/∂VGS|·tol_V·|p|(열마다 LUT VGS 기울기), 결합은 최악 선형 유지; 그 결과로 C(RSS) 판단.
- 계획·design: grep 0. metrics CONTRACT 9.1(ε_d = (gm/ID)·tol_V)·9.3 그대로.
- 코드: E/metrics/ss_linearize.py:11 "`lut_rel_tol` = `dc_op.gm_id · dc_tol_v`", :74, lut_parameters.py:8 "Δp = ε_d·|p|".
- 영향: current_reuse 잡음 분해능 440 µV = 값(720 µV)의 61 % → spec 450 µV 판정 c가 ±1 안(사실상 보류). 같은 Δp가 모든 ss metric 분해능(NFR-5 판정 단위·DEC-72 bin 폭 w_g = max(b_gain, …))에 들어가므로 9회로 gain bin 폭·층 0 '추정' 표기에도 닿는다(9회로 영향 미측정).
- card 후보: 없음 -- 새 card(metrics 분해능 정의, LA-1 gain bin 폭 b_gain 선행) 필요. 계약 변경이라 기준 변경 승인 절차 대상.

### B-10. Q-S1·Q-S2·Q-S3
- Q-S1 (라)→(가): 판정 불가. (라) '② 반영 뒤 엔진이 sf 동시 실현 불가(front 빔)를 내는지 확인'은 아직 측정되지 않았고, sf는 B81(봉인점 없음)이라 '잡음 가드 때문에 front 빔'을 가를 수 없다. spec `noise_excess_th <= 2` 유지는 결정 그대로.
- Q-S2: 반영됨 -- sf·two_stage·two_stage_sf spec `pm_ss_deg >= 70`(출처 기록 '2026-10-14 step-2 Q-S'), D40:1776-1780.
- Q-S3: 반영됨 -- current_reuse spec `noise_out_int_vrms <= 0.00045`, D41:1759, D40:1769 각주.

### B-11. Q-R1 -- A-5 참조.

### B-12. N12 counted_rails -- 계획 미반영
- 원문 :373 "(1) spec에 레일 목록 하나(counted_rails, user_spec 출처 record·decided 필수, 기본값 없음 DEC-78 유지) … 로더 검사 … supply_current_dc 제약이 있는데 선언 없으면 실행 전 보류로 멈춤. (2) 판정: D VDD_1V8 <= 92 uA, B vdd+vcp+vcn <= 10.4 uA …".
- 계획: P:654(metric 표 'counted_rails 둘 이상이면 정의 정정 필요, N6.17 백로그'), :1974(PW-1 백로그 '발동 0') -- 선언 자리·로더 검사·held-out 판정 결정이 없다. D40·D41 grep 0.
- data·코드: heldout erfc_ota·cnr_ota spec `pending_constraints: supply_current_dc U-75`(결정 (2)의 판정 제약 미등록), E/metrics/dc_metrics.py `counted_rails` 소비자는 있으나 spec 선언 통로 없음(PKG N12 사실: 커널이 빈 tuple, find_front `not_computed`).
- 영향: held-out B·D 공급 전류 제약이 U17 ② held-out 판정에서 빠짐(엔진 front가 전류 제약 없이 나옴).
- card 후보: SF-1(spec 선언 형식 정리·library spec data, N6.28) -- held-out data는 별도 커밋.

### B-13. N13 CBAT θ 상자 -- 계획 미반영
- 원문 :368 "CBAT1_L·CBAT1_R·CBAT2(engine: true)의 theta 상자는 다른 회로의 엔진 계산 보상 소자와 같은 규칙으로 정하고, 규칙은 step 2 design에서 정한다(회로별 상자 값 선언 안 함)".
- 계획·design: 규칙 없음(grep 0). 2026-10-08 '[0.1 pF, 10 pF]'(user_decisions 단락 '10번도 네 판단에 동의해')은 library 회로별 `theta_bounds` data로만 들어가 있다(two_stage_ota spec `theta_bounds`).
- data: heldout/erfc_ota.sizing_spec.json CBAT 3개 engine, `theta_bounds` 없음.
- 영향: held-out B 탐색 전 `theta_*_bounds_undeclared` 거부 예상(PKG N13 '예상' -- 실행 확인은 안 함).
- card 후보: SF-1(공통 규칙 = spec 형식) 또는 LA-1. 원칙 점검: '회로별 값 선언 안 함'이므로 규칙을 엔진(보상 소자 공통 상자 정의)에 두는 것이 결정 취지.

## 3. 묶음 C -- 그 밖 Q-번호·번호 없는 엔진 결정 (빠른 확인)

| 결정 | 원문 | 분류 | 근거 |
|---|---|---|---|
| SYNTHESIS Q1~Q12(reference 검토) | 2026-10-07 "B는 추천대로 해" | 반영됨 | history:930-943이 Q마다 DEC-87~DEC-93·LY·N3 자리로 옮김 |
| 10-08 design v1.2 Q1~Q11 | "Q1~Q11 모두 네 의견대로" | 반영됨 | Q6 전력 = DEC-78(P:277), Q10 = U-58(P:2321), Q2·Q3·Q4 = DEC-21·DEC-23·U-55(P:2318), Q11 잡음 = D41 §7 |
| 10-08 Q3·Q4 matching·스윙 | "q3,q4는 네 제안대로" | 반영됨(이후 일부 대체: 스윙·ICMR은 O-25·O-115·O-154) | U-55, D41 §6.2·§6.4-2 |
| 10-13 A' (3)·①②③ | "1은 권고, 2도 권고, 3도 권고대로"·"①, ②, ③ 권고대로" | 반영됨 | P DEC-98(:297), D40 §10.5(:2008-2041), D42 D-AP1 |
| 10-13 d/s 비트 동일 범위 (라) | 같은 원문 (1) | 반영됨 | history:1290, D40:1613, D42 D-SYg |
| 10-13 ② '가설 1·2·5를 design 보완 항목으로 올려 결정받는다' | user_decisions:305 | 결정은 받음(PKG), **반영 단계 누락** | §1·§2 전체 |
| 10-14 결정 10 code_hash | "10도 권고대로" | 반영됨 | D40 v1.9.3(:28) |
| 10-14 U17 ①-b 3~9, U-68 | "3~9 모두 권고대로" 등 | 반영됨 | D40 v1.9.2·v1.9.3, history:1294-1298 |
| 10-15 NFR-4 BLAS, Q-N1~Q-N10(U-77~U-86) | "1안·3안…", "기본안대로 진행해" | 반영됨 | P NFR-4(:188), U-77~U-86(P:2340-2349) |
| 10-15/16 XRUN-F1·offset trim TD·offset-strategy DS·SPICE 온도 루프 | 각 원문 | 반영됨(각 계획) | XRUN-F1: gb 17·hc 10·os 19 적중, DS-U: offset-strategy 32, 온도: oracle 8·offset 8·trim 7 적중 |
| held-out A~D 판독·spec(HA·HB·D-x·U1~U9·C-1~C-3) | 10-13·10-14 | 반영됨(data) -- 단 HB-1→N12, HB-2→N13은 §2 B-12·B-13 미반영 | assets/heldout/*.sizing_spec.json |

## 4. 묶음 D -- O-번호 결정 N2.1 행 빠른 확인

방법: O-1~O-162마다 `O-n` 뒤에 숫자가 오지 않는 패턴으로 P와 다른 계획 5개(headroom-chain·oracle-portability·graph-consumption·offset-strategy·offset-trim)·history를 셌다.

- P N2.1 표의 O 행(`| O-n` 꼴)은 gain-budget 범위 결정에만 있다(예 P:309-318 O-33~O-46, :343 O-118, :348 O-124, :368 O-151, :374 O-157). 행이 없는 O-번호 대부분은 본문·card 근거로 인용되거나(gbplan 적중 ≥ 1) 다른 계획 몫이다(O-2~O-10 oracle-portability 등).
- 계획 전체 적중 0인 O-번호와 판단:
  - O-12(oracle OP-0 design 승인), O-42(design 40 v1.11.2 승인), O-77(offset-strategy design 승인), O-99·O-104·O-105(design 40·41 승인·정오) -- design 승인 기록이라 계획 행 불필요. 반영됨.
  - O-17(card B 규칙 M-c 해석·`computed_blocks` 삭제), O-39(ly_device 쪼개기) -- design 40 §2.4.5·layout 필드 결정(history 적중 2·1). design 몫, 반영됨.
  - O-84(IT-1 dispute, 코드 변경 0), O-93(IT-2a 승인 범위 확장) -- card·승인 기록 몫. 반영됨.
  - O-102·O-103(IT-2b 커널 y 끝점 봉인 7 거부 수락, 백로그 B70) -- 결정 문언 'design 4.7-8 (8) 추가'라 design 몫. 엔진 동작은 '구현 유지'라 미반영 영향 없음. B70은 백로그 정본(계획 밖)에서 확인 대상.
- 판정: O-번호 결정에서 '계획 미반영'으로 분류할 것은 찾지 못했다. 단 O-151 U5·U6(DEC-104 R3 하한 행 목록)은 PKG Q5-1 (가)를 인용하지 않고 같은 양을 정했다(§1 A-12).

## 5. 엔진 동작을 바꾸는 미반영 -- 반영 자리와 card 후보 정리

| # | 결정 | 반영할 계획 자리(제안) | card 후보(N6) | 비고 |
|---|---|---|---|---|
| 1 | Q1-2 (ii)(확인됨) | N2.1 새 행 + design 41 §6.4-1 개정 | LA-1 | CMP-1 front 0 직접 원인 |
| 2 | Q6-1 (A)(확인됨) | DEC-91 (2) 개정 | LA-1 또는 LI-1 | CMP-1 −29~−67 % 전류 오차 |
| 3 | Q1-1 N9 매크로 노드 | DEC-104 R3 '망 정의' + LA-1 범위 문언 | LA-1(범위 13 옆) | design 문언은 있음 |
| 4 | Q2-2 매크로 출발 P = 0 | DEC-104 R3 또는 DEC-92 (2) | LA-1 | |
| 5 | Q3-1·Q3-2·Q-N9 `mirror_vds`(P1s·P1c) | DEC-104 R5′/R6 행 목록 | LA-1(R6 블록)·TB-1(술어 S0 필드) | 체계 offset 출발 조건 |
| 6 | Q4-2 합 가드 공동 선택 | DEC-104 (3)(b) R7 형식 | TB-1·LA-1 | |
| 7 | Q5-1 (가) 슬루 비차단 하한 | DEC-104 R3 하한 행 목록 | LA-1(U5·U6) 또는 SB-1 | O-151이 대체 의도였는지 사용자 확인 |
| 8 | Q-N2 B 면적 → gm/ID 하한 | LR6 | LA-1·offset-strategy G-S2 | current_reuse 입력 CM 창 |
| 9 | Q-N2 D 절대 제약 회로 부하 가드 | DEC-104 (3)(b) | TB-1 | |
| 10 | Q-N3 CMFB DC 평형 | DEC-104 (0) θ 기저 / DEC-70 | TB-1·LA-1 | current_reuse B81 원인 후보 |
| 11 | Q-N11 분해능 Δp | NFR-5·metrics CONTRACT 9.1 | 없음(새 card) | 기준 변경 승인 대상 |
| 12 | N12 counted_rails | DEC-78·N3.15 spec 형식 | SF-1 | held-out B·D |
| 13 | N13 CBAT θ 상자 규칙 | DEC-24/DEC-92 보상 소자 상자 | SF-1 또는 LA-1 | held-out B |

동작 무관 미반영: Q4-1 잔여(W 클램프·hull 단조, TB-1 가드 필드 옮길 때 같이), D1(W_min 1 ulp, card·backlog 없음), Q5-1·Q-N6/7/10 재측정 항목(U17 ② 완료 조건 미등록).

원칙 점검(graph 단일 정본 규칙, 프로젝트 CLAUDE.md): 위 card 후보는 모두 기존 정본 자리(DEC-104 R3 매크로 블록·R6 블록·R7 가드 필드·LR6·DEC-91)에 넣는 꼴이고 새 cache·사본·둘째 생산자를 만들지 않는다. 단 #5 `mirror_vds`는 R-1′ 고리가 아닌 행이라, R6 블록 행 목록에 넣을 때 O-158 (A′)('R-1′ 아닌 행을 사다리에') 선례와 같은 '원래 취지와 다름' 표지가 필요할 수 있다(계획 개정 때 판단). #7은 O-151 U5·U6과 충돌 여부를 사용자에게 먼저 물어야 한다(대체였으면 '대체됨'으로 바뀐다).

## 6. 정정(이 파일 안)

- §0 요약표 Q4-1 행의 `iv_matching_l.py:136-`는 `iv_matching_l.py:63`(W = max(·, W_min), 주석 'W 하한 제약 S-18')이 맞다(§1 A-10은 정정본).
