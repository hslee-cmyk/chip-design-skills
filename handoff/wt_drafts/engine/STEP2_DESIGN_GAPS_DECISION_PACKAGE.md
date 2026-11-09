# 단계 ② design 보완 결정 자료 -- A' 시범 3회로(nmcnr·current_reuse·sf_pushpull)에서 나온 엔진 갈림

작성 2026-10-13(1차: nmcnr 항목 1~6). **갱신 2026-10-13(2차)**: current_reuse(파일럿)·sf_pushpull 시범을 통합하고 사용자 결정을 반영했다 -- 결정 상태 표(아래), 세 시범 통합 표(§0.3), 신규 항목 N1~N11(§7), 구현 결함과 재분류(§8), spec 문제(§9), 요약(§10), 질문(§11).
성격: **결정 자료**(엔진·test·design·spec 파일은 고치지 않았다). 회로 원리 해석은 사용자 공동분석 대상이라 결정하지 않고 선택지·근거·9회로 영향 실측만 낸다.

## 결정 상태 (2026-10-13 기준)

출처: `_drafts/user_decisions.md` 2026-10-13 항목. '(가) 그룹 바로 진행·(나) 그룹 기본안'은 원문에 그룹 구성이 적혀 있지 않아, 1차 문서 §10(옛 §7) '결정 필요 여부' 열로 다시 짰다 -- (가) = 결정이 필요 없는 구현 정정·확인 항목, (나) = 결정이 필요했던 항목 중 1차 문서가 권고를 낸 것. 이 짝짓기가 사용자 뜻과 다르면 이 표만 고치면 된다.

| 항목 | 내용 | 상태 | 근거·채택안 |
|---|---|---|---|
| Q0 | BLAS 스레드에 따른 출발 구간 차이 → ② 완료 조건에 '두 실행 조건 비트 동일' | **결정 완료**((가) 바로 진행) | 확인 항목 추가 |
| Q1-1 | 항목 1 A(41 §6.5 N9 구현) 먼저, 재측정 뒤 B·C 판단 | **결정 완료**((가) 바로 진행) | design 그대로, 구현 gap 정정 |
| Q1-2 | §6.4-1 'A_max 미상 → 비활성'을 found_db 비례 g_i 로(ii) + nmcnr·ngcc gain 제약(i) | **결정 완료** | (ii) 권고대로. (i) nmcnr `gain_ss_db >= 100`, ngcc `>= 111` -- spec 커밋 `0cbc0d2`(병합 `ec9a9f0`). **영향**: 항목 5(a)3·5(b) 의 'nmcnr 은 gain 제약이 없어 41 §5.1 활성 밖'은 이제 성립하지 않는다(두 회로 모두 gain 선언) |
| Q1-3 | knee 초기 L(LR5)을 §6 출발에도(E) | **기본안**((나)) | 1차 문서에 이 질문의 권고 문언이 없어 기본안 = **현행 유지(층 0 에만)** 로 적었다. 확인 필요(§11 Q-R1) |
| Q2-1 | 매크로 목적 정의역 = 모든 MOS 가지 전류 | **기본안**((나)) | 권고(항목 2 A(2)) |
| Q2-2 | k < 1 해석 조건 대신 개방 RHP 극점 수 P = 0 | **기본안**((나)) | 권고(항목 2 B) |
| Q3-1 | 체계 오프셋 술어 P1s → 41 §6.7 목표 행 `mirror_vds` | **결정 완료** | (A), θ 묶음 아님 |
| Q3-2 | 파일럿 바이어스 분배 쌍 P1s 제외 | **결정 완료** | 제외, '신호 경로' 조건은 design 에서 구조로 정의 |
| Q3-3 | `offset_sys` 제약 확장 | **결정 완료** | 출력 기준 DC 선언 회로에만 |
| Q4-1 | 가드 입력 전류 = 매크로·KCL 이 정한 전류만(4(d) A) | **결정 완료**((가) 바로 진행) | design 문언을 따르는 정정 |
| Q4-2 | 합 가드 → 소자별 상한 규칙 | **기본안**((나)) | 권고 D(41 §6.7 공동 선택) |
| Q5-1 | 자유 가지 전류 규칙, 5(c) 재측정 문구 | **결정 완료** | (나) gm 요구 역산 + (가) 슬루 비차단 하한, 재측정 문구 ② 완료 조건 채택 |
| Q6-1 | DEC-91 (2) 개정 | **결정 완료** | (A) W-bin 슬라이스 |
| N1~N11 | 세 시범 통합 신규 design 항목(§7) | **미결** 8 / **기본안** 3 | §11 질문 Q-N1~Q-N11, 기본안 = N6·N7·N10 |
| D1 | W_min bin 경계 반올림(§8.1) | **결정 불필요(구현 결함)** | 재현·위치 §8.1 |
| R1·R2 | β 미획득·가드 '미선언' 판독(§8.2·8.3) | **결정 불필요(재분류: 결함 아님)** | R1 = U17 ② 구현 예정, R2 = design 대로(빈칸은 N2 로) |
| S1~S3 | spec 문제(§9) | **미결(사용자 몫)** | §11 Q-S1~Q-S3 |

- 피검: master `3151392`(pilot 기록의 `980d147` 뒤 문서 병합만) `skills/analog-gmid-design/gmid_engine/`(읽기·실행만).
- 판정자: ngspice-46 sky130 tt(`C:/ngspice/Spice64/bin/ngspice_con.exe -b`).
- 작업 폴더 `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_step2_gaps/`(스크립트와 원자료 전부, 부록 A).
- 인용 약어: **41** = `docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md`, **40** = 같은 폴더 `...40-engine.design.md`, **P** = `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`, **E** = `skills/analog-gmid-design/gmid_engine/`. 줄 번호는 master `3151392` 기준.

---

## 0. 먼저 알릴 사실 (항목 밖, 모든 항목의 수치에 영향)

### 0.1 출발 구간이 BLAS 스레드 수에 따라 달라진다 (결정론 불변식 위반 의심)

같은 master·같은 입력(nmcnr)으로 출발 구간과 θ0 를 두 번 쟀다(`survey9.py`, 각 실행 안에서는 재현됨).

| 실행 조건 | 매크로 gm(NodeM2) | 매크로 PM | 자리값 전류(M104 등) | θ0 상태 | θ0 c<0 행 |
|---|---|---|---|---|---|
| BLAS 기본(시범 기록과 같음) `out_survey_blasdefault/` | 71.7 µS | −61.1° | 15.2 µA | sealed | pm −2.07, offset_excess −2.53, noise_excess −0.92 |
| `OPENBLAS_NUM_THREADS=1` `out_survey/nmcnr_amplifier.rerun.json` | 691 µS | −2.4° | 152 µA | **failed** | (평가 실패) |

- 원인 추정: 매크로가 `macro_nonconvergent`(SLSQP "Positive directional derivative") 영역에 있을 때 부동소수 합산 순서 차이가 결과를 가른다(E/search/macro_poles.py:337-361).
- 41 §6.6 불변식(1409줄) "같은 입력이면 같은 표"는 한 프로세스 안에서는 지켜지지만, 실행 환경(BLAS 스레드)까지는 덮지 못한다. 아래 항목 2 의 결함(Rm 누락)으로 매크로가 근 없는 영역에 있어서 생긴 2차 현상으로 보인다. 항목 2 를 고친 뒤 다시 잴 항목으로 남긴다(질문 Q0).
- 이 문서의 9회로 표는 `OPENBLAS_NUM_THREADS=1`(지시된 실행 조건) 값이다. 시범 기록 수치(BLAS 기본)와 다른 곳은 따로 적었다.

### 0.2 시범 가설과 이번 실측의 대응

| 시범 가설 | 이 문서 항목 | 이번 실측 결론(한 줄) |
|---|---|---|
| 1 [L] | 항목 1 | SPICE 를 소자 묶음별로 나눠 보니 PM 붕괴는 입력쌍 (gm/ID 20, L 0.15) 의 폴딩 노드 부하 때문이다. 'L 하한'이 아니라 **비주극점 노드 용량** 문제이고, 41 §6.5 N9(출력노드 아닌 극점 노드)가 as-built 매크로에 없다 |
| 2 [매크로 k] | 항목 2 | 매크로 망에서 **영점 상쇄 저항 Rm 이 빠져** 바깥 Miller 경로가 끊긴다(구현 결함). Rm 을 넣으면 매크로가 손 설계점 PM 80°(SPICE 77°)를 재현하고, 풀이는 스스로 k ≈ 3e-4 (≪ 1)를 찾는다 |
| 5 [체계 오프셋] | 항목 3 | 일반 구조 술어로 정의된다(9회로 중 5회로에서 발동). 개루프 강제 DC 가 노드를 '밀어낸' 것이 아니라 다음 단 소자 VGS 가 노드를 쓰는 구조(writer)이고, 같은 L·같은 전류밀도 조건이 출발값에 없다 |
| 3 [가드 변환] | 항목 4 | **구현 결함이 주원인**(가드 입력 전류가 매크로 전류와 W_min 자리값을 섞어 입력:부하 비가 1:35~1:6×10⁴, 손분석 실제 비 1:2:1). 음수 값은 gm/ID 경계가 아니라 예산 잔여(level)다. 그 밑에 design 빈칸 둘(자유 가지 전류의 비 r_k, 합 가드의 소자별 분해 규칙) |
| 4 [자리값 전류] | 항목 5 | 'uncovered'는 41 §6.5 `current_model`에서 생기고 41 §5 와 무관하게 생긴다. 41 §5 는 미구현이고, nmcnr 은 gain 제약이 없어 41 §5.1 활성 조건에서도 빠진다 → ② 완료만으로는 재측정 결과가 바뀌지 않는다 |
| 좁은 폭 | 항목 6 | pmos W ≤ 1 µm 에서 같은 전류밀도 ΔVGS −45~−131 mV, nmos −0~+67 mV. LUT 에 W 슬라이스가 이미 있다(엔진은 W_ref 하나만 읽음). 엔진 출발점의 nmos 39 %·pmos 21 % 가 W < 3 µm |

### 0.3 세 시범 통합 (2차 갱신)

자료: nmcnr = 이 문서 1차(§0~§6), current_reuse = `_pilot_current_reuse/pilot_record.md`·`noise_basis.md`·`engine_probe/`(엔진 master `00ae5df`), sf_pushpull = `_pilot_sf_pushpull/pilot_record.md`·`engine_probe/`(master `a5d8ccb`). 이번 갱신의 재확인 실측은 master `9255a22`(§8.1, §8.4) 와 1차 9회로 조사(`out_survey/`, master `3151392`, `OPENBLAS_NUM_THREADS=1`)를 썼다. 시범마다 엔진 master 가 다르다(중간 병합은 U17 ①-a 스냅샷·문서·spec 이라 출발 구간 식은 같다고 보지만 재측정하지 않은 곳은 '시범 시점 값'으로 적었다).

#### 공통 결론 -- 손 설계점을 엔진 θ 로 넣으면 봉인·판정이 SPICE 와 같은 방향이다 → 실패는 출발점 생성

| 회로 | 손 설계점을 엔진에 넣은 결과 | SPICE(판정자) | 엔진 자신의 출발점 |
|---|---|---|---|
| current_reuse | r2 θ → **sealed**(봉인 1~9). 행 c: pm +0.12(분해능 안 경계), offset −5.58, noise −0.95, swing·icm·area·offset_sys 통과 | PM 69.85°(목표 70, −0.15°), σos 3.34 mV(> 3.3), 잡음 757 µVrms(> 300), 나머지 PASS | centre θ0 SEAL_VIOLATION(M4a VDS −0.041 V), layer0 Halton 808 점 뒤 `start_status='failed'`(봉인 7 `no_root_in_window` M37b) |
| sf_pushpull | x3 θ → y(N20) = 0.1 칸에서만 **sealed**, gain +0.30·GBW +0.41·Rout +0.70 PASS, noise −0.76·offset −0.068 FAIL. r0 θ → gain −0.87·GBW −2.25 FAIL. 봉인점 노드가 손·SPICE 와 20~45 mV 안(N1 0.378 대 0.379) | x3: 66.93 dB·62.0 MHz·961 Ω PASS. r0: 57.69 dB·26.2 MHz FAIL | centre θ0 SEAL_VIOLATION(M9 VDS = 0, `lut_curve_undefined`), layer0 46 분 미종료(기존 기록 1,526 회 `start_lut_query_failed+probe_eval_budget`) |
| nmcnr | (손 θ 커널 평가 없음) 매크로 망에 Rm 만 넣은 진단: 손 점 PM 80.2°·UGF 854 kHz | PM 77.2°·UGF 826 kHz | θ0 sealed 이지만 pm c −2.07(BLAS 기본) / 매크로 근 없음 |

→ 세 회로 모두 **커널(DC·봉인·ss 판정)은 유효점을 표현하고 SPICE 와 같은 방향으로 판정한다**. 엔진이 못 하는 것은 그 점 근처로 가는 **출발점 생성**(출발 구간·매크로·자리값·KVL 출발)이다. 그래서 아래 가설은 거의 모두 41 §6(출발 구간)·§6.5(매크로)·§6.7(KVL 출발) 쪽이다. 예외: 잡음 판정은 엔진이 손 정의보다 엄격하다(sf r0 손 noise_x 1.99 PASS ↔ 엔진 FAIL, LUT 소자별 γ) -- 엔진 결함 아님.

#### 통합 가설 표

| # | 가설 | 증거 회로(근거) | 대응 항목 | 성격 |
|---|---|---|---|---|
| G1 | gain 제약이 있어도 이득 L 하한이 꺼져 L = L_min | nmcnr(가설 1), sf H3(전 소자 0.15 µm, `u9_value_not_certified`; 손 Lp 0.42~0.7·Ln 1.0, L 0.15 이면 R_up/2R_req ≈ 0.03) | 항목 1 D(ii) = **Q1-2 결정 완료**(sf 는 gain 선언 회로라 활성 대상) | design 빈칸 → 결정됨 |
| G2 | 비주극점(N9) 노드가 매크로에 없어 입력쌍 drain 용량·전류 분배를 못 봄 | nmcnr(in015 PM 35.7°), sf 3.3(남는 속도 한계 = N1 노드 R1a × 입력쌍 Cdd), sf H6(Cc 상자 하한) | 항목 1 A = **Q1-1 결정 완료** | 구현 gap(design 있음) |
| G3 | 매크로 망 Rm 누락·목적 정의역·UGF 없는 해 | nmcnr | 항목 2 = Q2-1·Q2-2 **기본안** | 구현 결함 + design 빈칸 |
| G4 | 미러 출력 VDS 를 기준과 같게 하는 출발 조건이 없음 | nmcnr H5(P1s), sf H4(캐스코드 미러 복사쌍 밀도 미결합: M5/M7/M11 ln_idu −23.7 대 M10/M12 −15.2) | 항목 3 = Q3 **결정 완료** + 캐스코드 확장 **N9 신규** | design 빈칸 |
| G5 | 가드 경계 음수(충돌) | nmcnr(4+4 충돌), sf H5(12+12 충돌) | 항목 4 = Q4-1 결정 완료·Q4-2 기본안 | 구현 결함 + design 빈칸 |
| G6 | 가드가 선언된 offset·noise 를 '미선언'으로 읽음 | current_reuse H3 | **R2 재분류**(§8.3): design 대로(가드 = 구조 가드 metric 전용). 절대 제약의 부하 몫 빈칸은 **N2** 로 | design 빈칸(결함 아님) |
| G7 | 자리값 전류(전류를 못 정한 소자에 Iref·W_min 전류) | nmcnr H4, current_reuse H1(**모든 가지 1.2 µA**, KCL 꼬리 = 2·I1 + I61 모순, 출력 Iq 손의 1/28) | 항목 5 = Q5 결정 완료. current_reuse 의 근본 원인은 매크로가 통째로 꺼진 것 → **N1 신규** | design 빈칸 |
| G8 | 정착 시간만 있고 GBW 목표가 없으면 매크로가 꺼짐(`gbw_target_missing`) | current_reuse H1 | **N1 신규** | design 빈칸 |
| G9 | 절대 offset 면적을 L 하한으로만 바꿔 입력 CM 창을 닫음 | current_reuse H2(M1a 2.5 µm·M4a 3.22 µm, θ0 M4a VDS −0.041) | **N2 신규** | design 빈칸 |
| G10 | CMFB 평형(오차 증폭기 균형·Voc = Voc_des·P/N 꼬리 일치) 출발 조건 없음 | current_reuse H4(layer0 점 봉인 7 M37b, Ncmfb_tail 창 [0, 0.249 V] 근 없음) | **N3 신규**(항목 3 과 같은 부류: 강제 전류 개루프 KCL 에 폐루프 DC 조건이 없음) | design 빈칸 |
| G11 | 폐루프 DC 묶음 부재: 출력 사슬 W4 변수 y 가 자유, β=1 vout = vin 미구속 → 가능 영역이 y 폭 ≈ 0.1 의 얇은 띠 | sf H1(4.2 표: y 0.1/0.2 한 칸만 봉인, centre y 0.5 는 띠 밖) | **N4 신규** | design 빈칸 + spec 해석 |
| G12 | DC 경로 θ 저항의 출발값이 전류와 무관한 상자 기하 중점 | sf H2(31.6 kΩ × 3 µA = 95 mV → M6/M9 VSD → 0, centre 실패 M9 VDS = 0; 손 R1 = ΔV_창/I = 10.8~13.7 kΩ), current_reuse(R2 `uncovered`, 손 R1 = R2 = 10 kΩ 은 spec 출처 기록의 '이득 손실 허용 최소 R' 규칙) | **N5 신규** | design 빈칸(41 §6.7-2 가 '상자 기하 중심 × KCL 전류'로 적음) |
| G13 | 출력단이 약반전이어야만 풀리는 KVL 기둥(VDSAT17 + VGS22 + VSG21 + VDSAT20 ≤ 1.8, VSB 0.9 V)의 출발 구간 없음 | sf H7(centre M22 ln_idu −13.8, 봉인 θ −16.9~−17.8) | **N6 신규**(기본안: §6.7 + N4 로 덮이는지 재측정) | design 범위 확인 |
| G14 | PM 목표가 없으면 Cc 가 상자 하한 | sf H6. **9회로 실측**: PM 미선언 3회로(sf, two_stage_ota, two_stage_ota_sf) 모두 매크로 Cc = 1.0e-13 F(상자 하한), 기록 `pm_floor_pole_at_ugf` | **N7 신규**(기본안: 새 규칙 없음 → G2 + spec PM) | spec + 구현 gap |
| G15 | 입력 CM 창(W4 `free_window`)이 VDSAT 을 빼고 KVL 순서 창만 씀 → y = 0.5 가 포화 창 밖 | current_reuse 새 후보 B(θ0 M4a VDS < 0) | **N8 신규**(sizing CONTRACT 12절 O1 '결정 대기'와 같은 사실) | design 빈칸(열린 항목) |
| G16 | L 동치류가 Vbias4 공유 소자(헤드룸 역할 M12/M21/M38)를 꼬리 M5 L 에 묶음 | current_reuse 새 후보 A(손 θ 봉인 7 최악 M21 slack 18.6 mV) -- **증거 약함**: 시작 실패의 직접 원인이라는 측정 없음 | **N10 신규**(기본안: 보류·재측정) | 회로 해석(공동분석) |
| G17 | 좁은 폭 효과 | current_reuse r0(협폭 기준 소자로 N 꼬리 +11 %·P 꼬리 −11 % → Voc 1.263 V), sf(M13~M16 gm/gds LUT 대비 −26~−32 %), nmcnr | 항목 6 = Q6 **결정 완료** | design 선택 → 결정됨 |
| G18 | W_min 소자의 W 를 exp(ln IDu) 로 되살리면 bin 하한 아래로 반올림 → `lut_mismatch_no_block` | current_reuse 부수 7 | **D1**(§8.1) | **구현 결함** |
| G19 | 선언된 되먹임에서 β 를 못 얻음(`feedback_factor_beta_unavailable`) | current_reuse H3 | **R1 재분류**(§8.2): design 41 §7.5 v1.6 에 있고 U17 ② 구현 예정 | 미구현(예정) |
| G20 | 엔진 잡음 분해능 440 µV(값의 61 %) | current_reuse `noise_basis.md` §5-1 | **N11 신규**(§7.11): 코드는 metrics CONTRACT 9.1·9.3 대로 -- 분해능 정의 문제 | design(계약) 문제 |
| G21 | spec 동시 실현 불가·PM 미정·잡음 값 | sf 3.2, sf SP-3, current_reuse 잡음 | **S1~S3**(§9) | spec 문제(사용자 몫) |

---

## 1. 항목 1 -- 동적 spec(GBW·PM)에서 L 을 정하는 경로 (시범 가설 1)

### 1(a) 현상과 증거

**엔진**(`out_survey/report.txt`, 9회로 출발 구간 선택점):

| 회로 | 선언 제약(요약) | L 하한 경로 비활성 사유 | 고른 L |
|---|---|---|---|
| nmcnr_amplifier | gbw, pm, icmr, swing, offset_excess, noise_excess, area | gain_l `constraint_not_declared`, matching_l `constraint_not_declared`, flicker_l `constraint_not_declared` | 15/15 소자 0.15 µm |
| ngcc_3stage_ff | gbw, pm, icmr, offset_excess, noise_excess, area | 위와 같음 | 16/16 소자 0.15 |
| two_stage_ota | gain, gbw, offset_excess, noise_excess, area | gain_l `u9_value_not_certified` | 7/7 소자 0.15 |
| two_stage_ota_sf | gain, rout, gbw, ... | gain_l `u9_value_not_certified` | 9/9 소자 0.15 |
| sf_pushpull_output_opamp | gain, gbw, rout, ... | gain_l `u9_value_not_certified` | 22/22 소자 0.15 |
| current_reuse_telescopic_ota | gain, pm, offset_in_sigma, noise_out_int, ... | gain_l `u9_value_not_certified`, flicker_l `feedback_factor_beta_unavailable` | 47/51 소자 0.15 (4 소자만 matching L 하한 2.5/3.22) |
| folded_cascode, common_gate_amplifier, pushpull_follower_buffer | gbw 없음 | 전부 `constraint_not_declared` | 전 소자 0.15 |

→ L 하한이 켜지는 회로는 절대 offset 제약이 있는 current_reuse 하나(4 소자)뿐이다. 나머지는 모두 LUT 최소 L.

**SPICE 분해 실험**(`spice/results_L.txt`, 시범 손 설계 계산기를 복사해 L·gm/ID 를 소자 묶음별로만 바꿈. 같은 넷리스트 생성기·같은 테스트벤치):

| 실험 | 바꾼 것 | A0 | UGF | PM | 모든 MOS 포화 |
|---|---|---|---|---|---|
| r0 (손 설계) | -- | 112.7 dB | 825.8 kHz | 77.2° | 예 |
| L015 (시범) | 전 소자 L 0.15 (W_min 규칙 때문에 전류·Cm 도 바뀜: gm1 275 µS, Cm1 53.6 pF, M102 W 130 mm, f_T ≈ 1 MHz) | 52.3 dB | 495.7 kHz | 42.4° | 예 |
| in015 | **입력쌍 L 만** 0.5→0.15 (gm/ID 20 유지, 전류·Cm 동일) | 99.9 dB | 500.2 kHz | **35.7°** | 예 |
| in015_g14 | 입력쌍 L 0.15, gm/ID 20→14 | 97.2 dB | 664.2 kHz | **82.4°** | 예 |
| st2_015 | 2단(M201·M202·M203/204) L 만 0.15 | 108.0 dB | 804.3 kHz | 77.5° | 예 |
| st3_015 | 3단(M301·M302) L 만 0.15 | 101.6 dB | 816.0 kHz | 76.6° | 예 |
| tail015 | 꼬리 M101 L 만 0.15 | 112.5 dB | 782.4 kHz | 78.2° | 예 |
| fold015 / *_fixI / L025·L05·L1_fixI | 폴딩·부하 L 변경 | -- | -- | -- | W_min 클램프·포화 깨짐으로 전류가 바뀌어 **교란됨**(결론에 쓰지 않음) |

해석(측정에서 나온 것만):
1. PM 붕괴는 **입력쌍의 (gm/ID, L) 조합 하나**로 재현된다(in015 35.7°). 같은 L 에서 gm/ID 만 14 로 낮추면 PM 82.4° 로 회복된다(in015_g14). 2·3단·꼬리의 L 을 0.15 로 내려도 PM 은 76.6~78.2° 로 유지된다. → "L 이 PM 을 정한다"는 가설 1 의 기전(단 이득 저하)은 이 데이터로 지지되지 않는다. pmos gm/ID 20 은 L 0.15 에서 곡선 꼭대기 근처라 W 가 폭증하고(L015 표: M102 W 130 mm, f_T 1 MHz) 그 drain 용량이 폴딩 노드(NodeF1/F2, 캐스코드 source)에 걸려 비주극점이 UGF 근처로 내려온다.
2. GBW(UGF)는 L 에 실제로 의존한다: in015_g14 의 SPICE M102 gm 18.9 µS 로 기대 UGF = 816 kHz × 18.9/19.9 = 775 kHz 인데 측정 664 kHz(−14 %). 손 추정 폴딩 노드 전류 분배 gm106/(gm106 + gds102 + gds104) = 14.3/(14.3 + 2.4 + 0.2) = 0.85 와 맞는다(gds102 = 18.9 µS/진성이득 ≈ 8, L 0.15). 꼬리 L 0.15(tail015)는 꼬리 전류 −5 %(1.376 vs 1.455 µA, 채널 길이 변조)로 UGF 782 kHz.
3. 엔진은 이 경우에 시범의 (20, 0.15) 점을 고르지 않는다: 출발 구간에서 M102 의 §6.3 속도 상한이 L 0.15 에서 gm/ID 17.08 로 걸린다(`_pilot_nmcnr/engine_probe/start_intervals.json` rows M102 `speed_ft_6.3`). 엔진 θ0 의 PM 실패의 주원인은 항목 2(Rm 누락)다.

**엔진 매크로가 L 효과를 보는가**(`out_macro/macro_exp2.txt`, Rm 을 1/gm3 로 강제한 진단 망 -- 항목 2 참고): 손 gm/ID·손 gm·C 에서 모든 L 을 0.15~2 µm 로 바꿔도 매크로 PM 77.5~80.3°, UGF 810~855 kHz. SPICE(in015 35.7°, UGF 500~664 kHz)와 방향이 다르다. 매크로 망 노드는 {NodeM2, NodeS2, Vout, NodeCM} 뿐이고 폴딩 노드가 없다.

**N9 대상 규모**(`out_pole/report.txt`, 전달 뷰 극점 노드 중 신호 구동이 있고 블록 출력이 아닌 노드, 입력 포트 제외): nmcnr {NodeF1, NodeF2 (전류 구동·낮음), NodeM1, NodeC, NodeTail, NodeCM}, ngcc {ND, NP, TAIL}, two_stage_ota {CS, D3, N_cc_rz}, two_stage_ota_sf {CS, D3}, sf_pushpull {N1, N2, N5, N7, N12, N13, N910, N1112, N1516, N17, N20, TAIL}, folded_cascode {X, Y (전류 구동), Vg7, Vg9, Vg10, tail}, current_reuse {N1a2a·N1b2b·N3a4a·N3b4b (전류 구동), N11a11b, ...}. 매크로가 활성인 5회로(gbw 선언) 모두에 N9 노드가 있다.

### 1(b) design 현 문언과 빈칸

- 41 §6.4-1(1306-1309줄): 이득 하한은 gain 제약과 인증 A_max 가 있어야 한다. "A_max가 미상이거나 gain 제약이 없으면 비활성(H3)". 41 §5.12.4(1179줄~)·stage B 실측대로 9회로 이득 블록 A_max 는 모두 미상(`grid_product_over_budget`) → gain 제약이 있는 4회로도 비활성(`u9_value_not_certified`). nmcnr 은 gain 제약 자체가 없다(SP-4 대기).
- 41 §6.4-2(1310줄)·§6.4-3(1331줄): 절대 offset·폐루프 잡음 제약에서만.
- 41 §6.4-6(1339줄): "L = max(1, 2, 3의 하한)". 셋 다 꺼지면 L = LUT 최소다. **GBW·PM 에서 L 을 정하는 문언은 없다.**
- 41 §6.3(1292-1302줄): 속도 gm/ID 상한은 비주극점 노드에 "낮은 등급 단자를 주는 소자"(캐스코드 M106/M107)의 f_T 만 본다. 그 노드에 **drain 용량을 거는 소자**(입력쌍 M102/M103, 싱크 M104/M105)는 대상이 아니다 → in015 의 기전이 이 절에서 빠진다(**빈칸**).
- 41 §6.5 망 구성(1350줄): "출력노드가 아닌 극점 노드(캐스코드 source 노드 등, N9): 낮은 등급 단자를 주는 소자 c의 gm_c + gmb_c를 컨덕턴스로 둔다 ... 높은 등급 노드는 붙은 drain 단자들의 gds 합". **design 에 있다.** as-built `E/search/macro_poles.py:5`("노드 = 이득 블록의 출력 넷 + 그 넷에서 수동소자만 거쳐 닿는 내부 넷")와 `_nodes`(100-124줄)는 N9 노드를 만들지 않는다. 41 §6.5 as-built 기록(1384-1394줄)에 이 축소가 적혀 있지 않다 → **기록 없는 as-built 축소(구현 gap)**.
- P LR5(552줄)·41 §5.3.7(810-843줄): knee 초기 L 은 층 0(§5, gain 모드)에서만 쓴다. P LR6(553줄): L 상한 `parasitic_pm_ss_deg`(θ 제약)는 그 제약을 선언한 회로(current_reuse)에서만.

### 1(c) 회로 원리 근거 (유도)

비주극점 노드 F(캐스코드 source)의 극점: ω_F = (gm_c + gmb_c + Σ_k gds_k) / C_F, C_F = Σ_k C_dd,k + C_ss,c. 소자 k 의 drain 용량은 전류 비례로 C_dd,k = I_k · (L_k / IDu_k(gm/ID_k, L_k)) · c_dd'(gm/ID_k, L_k) 이다(W = I·L/IDu). 41 §6.3 의 비주극점 조건 ω_F ≥ ω_GBW·tan(PM) 을 그대로 쓰면

  Σ_k I_k · L_k · c_dd'_k / IDu_k  ≤  (gm_c + gmb_c + Σ gds_k) / (ω_GBW · tan PM)

이고, 이는 **(gm/ID, L) 결합 상한**이다(gm/ID 가 곡선 꼭대기로 갈수록 IDu → 0 이라 좌변이 폭증한다 -- in015). L 하한이 아니라 상한·결합 조건이다.

GBW 쪽: 폴딩 노드의 전류 분배로 실효 gm1,eff = gm1 · gm_c/(gm_c + gmb_c + Σ gds_k). Cm1 은 θ 자유 변수라 ωu = gm1,eff/Cm1 은 Cm1·gm1 로 언제나 맞출 수 있다 → **GBW 는 L 의 하한을 강제하지 않고 전류(전력)를 L 에 대해 바꾼다**(목적 축의 trade-off). 단 gain 제약(A0)이 선언되면 §6.4-1 이 L 을 정한다.

정리: 동적 spec 에서 나오는 일반 규칙은 "비주극점 노드의 용량 예산(속도)"과 "실효 gm 에 대한 전류 분배"이고, 둘 다 41 §6.5 N9 망이 있으면 매크로 풀이 안에서 드러난다. 별도의 'GBW L 하한' 식은 원리상 정의되지 않는다(gain 제약 없이는).

### 1(d) 선택지 (모두 구조 술어·선언값만 사용)

| 안 | 규칙 | 영향 회로(실측) | 예상 결과 |
|---|---|---|---|
| **A** N9 구현 | 41 §6.5 1350줄 그대로: 전달 뷰 극점 노드 중 출력노드가 아닌 신호 노드를 매크로 노드로 넣고 컨덕턴스 = 낮은 등급 단자 소자 gm_c+gmb_c(+ 붙은 gds), 용량 = 붙은 소자 cgg/cdd(`per_amp`, 전류 비례). design 변경 없음(구현 gap 정정 + as-built 기록) | 매크로 활성 5회로 전부(N9 노드 수: nmcnr 6, ngcc 3, two_stage 3, two_stage_sf 2, sf_pushpull 12) | 매크로가 in015 기전·전류 분배를 본다. §6.1-7 의 '실행 가능한 최대 t' 탐색이 입력쌍 gm/ID 를 낮추는 쪽으로 움직인다. L 은 여전히 L_min 출발 |
| **B** 매크로 실행가능 L 사다리 | A 위에, §6.1-5 L 선택에 출처 `SRC_MACRO_L` 추가: L 동치류마다 LUT 앵커 오름차순(같은 bin 안 bisection, LR3)으로 매크로를 풀어 GBW·PM 이 실행 가능해지는 최소 L 을 하한으로 | 매크로 활성 5회로 | L_min 에서 실행 불가인 회로만 L 이 올라간다. 매크로 풀이 수 = 앵커 수 × 동치류(커널 평가 아님, 41 §5.3.6 '비용' 규칙) |
| **C** §6.3 확장 | 비주극점 노드의 C_F 예산을 '낮은 등급 단자 소자'뿐 아니라 그 노드에 drain/gate 가 닿는 모든 소자에 건다 -- 위 (c) 부등식을 소자별 (gm/ID, L) 결합 상한으로(예산 분배는 항목 4 의 합 가드 분배와 같은 규칙을 써야 한다) | gbw·pm 선언 회로의 N9 노드 소자 | 매크로를 바꾸지 않고 출발 구간만 좁힌다. 분배 규칙 결정이 추가로 필요 |
| **D** gain 경로 활성화 | (i) nmcnr 등에 gain 제약 선언(SP-4, 사용자 spec) (ii) §6.4-1 의 'A_max 미상 → 비활성'을 41 §5.3.2 L-2 와 같은 found_db 비례 g_i 로 대체 | (ii)만으로 gain 선언 4회로(two_stage, two_stage_sf, sf_pushpull, current_reuse) 활성. nmcnr·ngcc 는 (i) 필요 | 이득 L 하한이 실제로 켜진다. 동적 spec 과는 별개 경로 |
| **E** knee 출발 | P LR5 knee 초기 L 을 층 0 밖 §6 출발에도 적용(미러 동치류만) | 미러 동치류가 있는 회로 전부 | L_min 고착을 spec 과 무관하게 푼다. 근거는 LUT 한계효율(41 §5.3.7)뿐 |

### 1(e) 권고

**A 먼저(design 변경 없음, 구현 gap 정정), 그 결과를 재고 B·C 판단.** 이유: SPICE 분해에서 L 관련 실패 기전이 모두 비주극점 노드(용량·전류 분배)였고, 41 §6.5 가 이미 그 노드를 정의한다. 'GBW 에서 L 하한' 식은 원리상 정의되지 않는다(1(c)). D(ii)는 동적 spec 과 무관하지만 9회로 전부에서 §6.4-1 이 꺼져 있는 문언 문제라 따로 결정이 필요하다. nmcnr 의 gain 제약(D(i))은 사용자 spec 몫이다.

### 1(f) 구현 위치·test

- `E/search/macro_poles.py` `_Network._nodes`(100-124줄)에 N9 노드 추가(S1v `pole_nodes` 의 `impedance`·`drive` 사용, 이름 규칙 없음). 컨덕턴스 스탬프는 `system`(158줄~)에, 용량은 `iv_currents.per_amp` 재사용(새 LUT 조회 없음).
- test: (1) 3노드 toy(CS → 캐스코드 source 노드 → 출력)의 닫힌 식 극점 ω_F = gm_c/C_F 대조. (2) nmcnr 손 설계점에서 입력쌍 L 0.5 vs 0.15(gm/ID 20) 매크로 PM 이 SPICE r0 77.2° / in015 35.7° 와 같은 방향·DEC-72 오차 안. (3) 기본 호출 지문(41 §5.3.6 790-792줄) 변화는 의도된 변경으로 기준 재측정(작성자≠검증자).

---

## 2. 항목 2 -- 매크로 극점 모델의 시작값과 구조 조건 k = gm2/gm3 < 1 (시범 가설 2)

### 2(a) 현상과 증거

**결함 1 -- 영점 상쇄 저항 Rm 이 매크로 망에서 빠진다**(`out_macro/macro_exp2.txt`, `out_survey/report.txt`):
- 망 스탬프: `('zc', 'Rm', (NodeCM, Vout), ('M301',))`, `zc_fallback = {}`.
- `zc_value`(E/search/macro_poles.py:153-156)는 R = 1/Σ_c I_c·(gm/ID)_c 를 **전류 아핀 벡터** `model.mos[c]` 로 계산한다. M301 은 `model.mos` 에 없다(KCL 행 M301 = M302 + I_RL, 미지 θ 전류 둘 → `unassigned = (M108, M109, M302, RL)`). Rm 은 θ 상자도 없다(영점 상쇄 규칙이 정하는 값이라). → `zc_value` = None → `system` 이 스탬프를 건너뛴다(181-182줄).
- 결과: NodeCM 이 Cm1·Cm2 사이에 떠서(극점 0 Hz) **바깥 Miller 경로(Vout→Rm→NodeCM→Cm1→NodeM2)가 끊긴다.** 손 설계점(gm1 28.4 µS, gm2 16.8 µS, gm3 1.496 mS, Cm1 5.54 pF, Cm2 0.568 pF)에서 |H(jω_GBW)| = 31.9, PM 정의 불가(개방 RHP) -- 어떤 시작값에서도 PM 근이 없다(`macro_root_missing pm_target_not_met_within_ranges`).
- 그러나 M301 은 블록 3 의 **입력 소자**라 gm_301 = 매크로 변수 gm_b 그 자체다(41 §6.5 1366-1368 의 블록 VCCS 정의). 전류를 몰라도 R = 1/gm_b 가 정의된다.

**Rm = 1/gm3 를 넣은 진단 망**(엔진 파일 불변, `_Network.zc_value` 를 실험 스크립트에서만 대체):

| 점 | 매크로 |H(GBW)| | PM | SPICE |
|---|---|---|---|
| 손 설계점, 손 L | 1.042 | 80.2° (UGF 854 kHz) | 77.2° (UGF 826 kHz) |
| 손 gm/ID, L 전부 0.15 | 0.993 | 77.5° | (L015 는 전류가 달라 비교 불가) |
| 엔진 풀이 `macro_solve`, 손 L | -- | **70.0°, 기록 없음(성공)**, k = gm2/gm3 = 3.4e-4 | -- |
| 엔진 풀이, L 0.15 | -- | 70.0°, 성공, k = 2.0e-4 | -- |

k 스윕(손 L, gm1·gm3·Cm1 고정): Butterworth 규칙 Cm2 = k·CL/(2(1−k)) 로 두면 k = 0.01~0.5 에서 PM 76~80°, k 0.8 에서 63°, 0.95 에서 20°, 0.99 에서 −9°. Cm2 를 0.568·1 pF 로 고정하면 k ≥ 0.5 에서 개방 RHP(PM 정의 불가).

→ **망이 맞으면 풀이(전원 전류 최소, 다중 출발)가 k ≪ 1 을 스스로 찾는다.** 시범 θ0 의 "k ≥ 1 출발"은 Rm 누락으로 근이 없어서 생긴 결과이고, k < 1 을 규칙으로 따로 넣을 필요는 이 측정에서 보이지 않는다.

**결함 2 -- 목적 함수가 블록 3 전류를 세지 않는다**: Rm 을 넣은 풀이 결과 gm3 = 4.58 mA/V(손 L), 7.5 mA/V(L 0.15) -- 손 설계 1.5 mS 의 3~5 배. `_power`(E/search/macro_poles.py:270-273)는 "값이 정해진 θ 전류 원소"(`ctx.basis.free` 중 `model.affine` 에 있는 것)만 더한다. M302·RL 이 unassigned 라 M301 가지 전류가 목적에 없다 → gm3 를 키워도 비용 0 → gm3 가 커진다.

**결함 3 -- 1회차 매크로가 '성공'인데 UGF 가 없다**(`out_guard/nmcnr_amplifier.json` state 0, `OPENBLAS_NUM_THREADS=1` 에서만 관찰): gm(NodeM2) = 7.4 nS, Cm1 0.12 pF, Cm2 0.10 pF(상자 하한), 기록 없음, `ugf_hz = None`, `pm_deg = None`. 그 조건의 출발 구간 4단계 전류(입력쌍 3.1 nA)가 이 해에서 나온다. BLAS 기본에서는 같은 1회차가 gm(NodeM2) 13.1 µS(입력쌍 5.57 µA)로 정상 범위다(`out_guard_bd/summary.txt`) -- 0.1 의 실행 조건 의존과 같은 현상.

### 2(b) design 현 문언과 빈칸

- 41 §6.5 보상 수동소자(1358-1361줄): "선언값 / PM 최소값 / θ 상자 기하 중점은 첫 분할점". 영점 상쇄 저항(40 §2.4.11 `ZeroCancel`, R = 1/Σ gm_c)은 as-built 독스트링(macro_poles.py:8-9)에 있다. **구성 소자 c 가 블록 입력 소자일 때 gm_c = gm_b** 라는 문언은 없다(as-built 는 전류 경유로만 계산) -- 이건 정의상 자명해 **구현 결함**으로 분류한다(design 이 전류 경유를 요구하지 않음).
- 41 §6.5 as-built(1385-1389줄): 목적 = 전원 전류 합 최소. "정해진 θ 전류"만 세는 규칙은 as-built 독스트링(macro_poles.py:14)에 있고 design 에는 "전원 전류 합"뿐이다 → unassigned 가지가 있을 때의 목적 정의가 **빈칸**.
- 41 §6.5 실패 처리(1370-1373줄): 근이 없으면 기록하고 넘어간다. 'UGF 가 정의되지 않는 해'(결함 3)를 실패로 세는 문언이 없다 → **빈칸**(as-built 성공 판정 353-354줄은 `at_target` 값만 본다).
- 구조 조건 k < 1: design 에 없다. 41 §1.12.3(359-374줄, J-B)은 중첩 Miller 내부 루프를 보상 루프로 분류하고 안정도를 전체 PM + 개방 RHP 극점 없음(P = 0)으로만 본다.

### 2(c) 회로 원리 근거

NMCNR(시범 2.1 유도, 이상 이득단): H(s) = −(gm1/sCm1)(1 + sCm1/gm3) / [1 + s·Cm2(1−k)/gm2 + s²·CL·Cm2(1−k)/(gm2·gm3)], Rm = 1/gm3, k = gm2/gm3. 분모 2차 계수가 양수여야 하므로 Cm2(1−k) > 0 ⇔ k < 1(Routh). 이 조건은 **이 회로족(Miller 커패시터 둘이 공통 노드에서 null 저항 하나로 출력에 가는 구조)의 해석식**에서 나온다. NMC(null 저항 없음)·NGCC(feedforward)·DFCFC 는 다른 조건을 가진다 → 해석식을 규칙으로 넣으면 회로족 카탈로그가 된다(topology 무관 원칙과 충돌).

topology 무관하게 같은 사실을 쓰는 방법: 매크로 망의 pencil 고유값(이미 `pencil_roots` 로 계산, `at_target` 211-213줄이 RHP 를 감지)에서 **개방 RHP 극점 수 P = 0** 을 시작점·제약 조건으로 쓰는 것. 이는 41 §1.12.3 의 안정도 정의(P = 0)와 같은 술어이고, NMCNR 에서는 k < 1 과 동치다(Routh).

### 2(d) 선택지

| 안 | 규칙 | 영향 회로(실측) | 예상 결과 |
|---|---|---|---|
| **A** 결함 정정만 | (1) 영점 상쇄 구성 소자가 블록 입력 소자면 gm_c = gm_b. (2) 목적 = 모든 MOS 가지 전류 합: 블록 입력 소자 전류 I = gm_b/(gm/ID) 를 아핀으로 넣어 unassigned 가지에 걸린 블록도 비용을 갖게. (3) UGF 가 정의되지 않는 해는 `macro_nonconvergent` 로 | (1) zc 저항이 있는 회로: nmcnr(Rm, 현재 누락), two_stage_ota(Rz, 현재 정상 -- M6 전류 아핀 있음 130 kΩ), current_reuse(매크로 비활성) → 값이 바뀌는 회로는 nmcnr 하나. (2) unassigned 가 있는 매크로 활성 회로: nmcnr {M108, M109, M302, RL}, ngcc {M5, M6A}. (3) 1회차 매크로를 쓰는 전 회로 | nmcnr 매크로 PM 근 생김(진단 망에서 70° 성공), gm3 과대 해소 기대. two_stage 는 (1) 무변화 |
| **B** A + 개방 RHP 없는 출발점 | `feasible_start`(316-327줄)가 |H| = 1 만 보지 않고 pencil 극점의 RHP 수 0 도 요구: 아니면 뒤 블록 gm 을 같은 2배 사다리로 더 올린다(새 상수 없음) | 매크로 활성 5회로 | SLSQP 가 PM 제약 −1 평탄 영역(`_signed_pm`)에서 출발하는 경우 제거 |
| **C** A + 구조 조건 | 41 §1.12.3 보상 내부 루프마다 '루프 안쪽 블록 gm < 루프를 닫는 블록 gm' 부등식을 매크로 제약으로 | 보상 내부 루프가 있는 회로: nmcnr, ngcc(J-B 대상) | NMCNR 해석식과 일치. NGCC 에서 맞는지는 별도 유도 필요(회로족 의존 위험) |
| **D** A + 다중 출발 범위 확대 | 시작점 집합에 '각 블록 gm 상자 기하 중심' 등 추가 | 매크로 활성 5회로 | 근 영역이 좁을 때만 도움. 근본 원인(A)과 무관 |

### 2(e) 권고

**A(구현 결함 정정) + B.** 이유: 진단 망에서 Rm 하나만 넣어도 매크로가 손·SPICE 결과를 재현하고 풀이가 k ≪ 1 을 스스로 찾는다. C 는 회로족 해석식이라 topology 무관 원칙에 걸리고, B 의 'P = 0' 술어가 같은 사실을 일반형으로 덮는다. A(2) '모든 가지 전류 합'은 design 문언("전원 전류 합")을 구현이 좁힌 것을 되돌리는 것이라 design 개정은 '목적의 정의역'을 한 줄 명시하는 정도다(결정 필요: Q2-1).

### 2(f) 구현 위치·test

- `macro_poles.py` `zc_value`(153-156줄): 구성 소자가 블록 입력 소자이면 그 블록의 gm 성분을 쓴다(아핀 벡터의 단위 벡터). `_power`(270-273줄): 블록 입력 소자 전류 아핀 항 포함. `_iterate` 성공 판정(353-354줄)에 `analyse` UGF 정의 여부.
- test: (1) nmcnr 진단 망 손 설계점 PM 80.2° ± DEC-72 (SPICE 77.2°) -- oracle 은 손 유도 전달함수(시범 2.1)로 독립 작성. (2) 이상 VCCS 3블록 NMCNR toy 에서 k 스윕의 Routh 경계(k = 1)와 매크로 RHP 판정 일치. (3) two_stage_ota Rz 값 불변(130.4 kΩ) 확인.

---

## 3. 항목 3 -- 체계 오프셋 0 조건 (시범 가설 5)

### 3(a) 현상과 증거

- 시범 θ0(BLAS 기본): NodeM1 0.916 V, **NodeM2 1.648 V** → M109 VSD ≈ 0.152 V, 봉인 7 최악 M109 slack 5.8 mV(`_pilot_nmcnr/engine_probe/theta0_detail.txt`). M201 gm/ID 17.2(약반전, W ≈ 6 cm) → VSG201 = 1.8 − 1.648 = 0.152 V, VSG108 = 0.884 V.
- 엔진 DC 쓰기 계획(E/sizing/writer_plan.py 독스트링 4: "MOS 가 source 에서 gate 를 쓰면 vgs_gate"): M201 은 source = vdd(고정 F), gate = NodeM2 라 **NodeM2 의 writer 는 M201 의 VGS** 다(구조 추론, θ0 수치와 일치). 미러 출력 M109 의 전류는 KCL 기저(미러 비 1)로 강제되고 VDS 는 결과값이다.
- 손분석·SPICE: VSG201 = VSG108(같은 L 2 µm·같은 gm/ID 8) → NodeM2 = NodeM1, SPICE r0 NodeM1 0.647·NodeM2 0.513(협폭 오차 포함), 전 소자 포화.

**시범 가설의 '개루프 강제 DC 가 고임피던스 노드를 레일로 민다'의 정정**: 폐루프(β = 1) DC 에서도 NodeM2 = VDD − VSG201(I201) 로 같다. 폐루프에서 바뀌는 것은 미러 출력 전류 오차(gds109·ΔV)가 입력 차전압(= 체계 오프셋 = gds109·(VSG201 − VSG108)/gm1)으로 흡수된다는 점뿐이다. 엔진은 미러 전류를 강제하므로 그 오프셋을 오프셋으로 보지 않고 VDS 결과로만 본다. 즉 노드 위치는 개루프 탓이 아니라 **VSG201 을 정하는 (gm/ID, L) 선택에 VSG108 과의 결합이 없는 것**이 원인이다.

**구조 술어 9회로 실측**(`sysoff_scan.txt`, topology netlist 연결만):

술어 P1s: diode MOS d(gate = drain) / 미러 출력 o(같은 kind, o.gate = d.gate, o.source = d.source, o.drain ≠ d.drain) / 노드 n = o.drain 에 diode 가 없고 / n 에 gate 가 닿는 MOS g 가 d 와 같은 kind·같은 source 넷.

| 회로 | P1s 인스턴스 (d, o, n, g) |
|---|---|
| nmcnr_amplifier | (M108, M109, NodeM2, M201), (M203, M204, NodeS2, M301) -- 손분석의 두 조건과 정확히 같다 |
| two_stage_ota | (M3, M4, O1, M6) -- 교과서 조건(Allen-Holberg 체계 오프셋)과 같다 |
| two_stage_ota_sf | (M3, M4, O1, M6) |
| ngcc_3stage_ff | (M3, M4, V1, M8), (M3, M4, V1, M14) -- 한 노드에 g 둘 |
| current_reuse_telescopic_ota | (M66, M10, Vop1, M16), (M66, M19, Vom1, M26), 그리고 바이어스 분배 쪽 (M18_bg, M8, Vg15, M15), (M18_bg, M17, Vg25, M25) |
| folded_cascode, sf_pushpull, common_gate, pushpull | 없음(미러 출력이 출력 포트·꼬리이거나 미러 없음) |

같은 구조에서 g 의 source 넷이 다르거나 kind 가 다른 P2 형(조건이 KVL 등식 V(n) = V(d.drain) 으로만 쓰임)이 current_reuse 24·ngcc 1 건 있다.

### 3(b) design 현 문언과 빈칸

- 40 §3.8 표(851-866줄) `offset_sys_mv`: "봉인 DC 동작점에서 입력 차 0일 때의 출력 오차 / A_dm", 상한은 `offset_in_sigma_mv` 제약이 있는 회로만, 나머지 보고. → **판정 metric 은 있다**(구현 `E/metrics/offset_systematic.py` 존재). 단일 출력 회로는 출력 기준 DC 선언이 없으면 `reference_undeclared`(nmcnr: 입력 DC SP-2 대기).
- 41 §6.7(1413-1475줄) KVL 고리 출발 제약: 고리 등식(v2)과 고리가 정한 VDS 의 **포화 부등식**만 본다. 미러 출력 VDS 를 기준 diode VDS 와 같게 하는 **등식(또는 목표)은 없다**(빈칸).
- 41 §6.1-7(1252줄): gm/ID 는 소자마다 구간 최댓값 → g(M201)와 d(M108)를 독립으로 고른다.
- P DEC-04(205줄): S1 등식(매칭·L 동치류·공유 VGS)으로 묶인 것 외는 독립 결정변수. P1s 는 S1 matching 그룹에도 L 동치류에도 들지 않는다(M201·M108 은 서로 다른 블록).

### 3(c) 회로 원리 근거

미러 출력 o 와 기준 d 가 같은 VGS·같은 source 를 가지므로 I_o/I_d = (W_o/W_d)·(1 + λ·VDS_o)/(1 + λ·VDS_d). 체계 오차 0 ⇔ VDS_o = VDS_d. VDS_o = V(s) − V(n)(부호는 kind 기준), V(n) 은 g 가 쓴다: V(n) = V(s_g) ± VGS_g. s_g = s_d(같은 넷)이고 VDS_d = VGS_d(diode)이면 조건은 **VGS_g = VGS_d** 가 된다. VGS = f(IDu, L, VDS, VSB) 이므로 같은 kind 에서 이를 만족하는 충분조건은 (IDu_g, L_g) = (IDu_d, L_d)(VSB 는 같은 source·같은 bulk 에서 같다. VDS 의존은 2차). 이는 **gm/ID 와 L 이 같다**는 뜻이고 전류는 달라도 된다(W 비 = 전류 비). 술어는 연결만으로 정해지고 이름·회로족이 들어가지 않는다.

### 3(d) 선택지

| 안 | 규칙 | 영향 회로 | 예상 결과 |
|---|---|---|---|
| **A** 출발 결합 행 | 41 §6.7 에 행 종류 `mirror_vds` 추가: P1s 마다 VDS_o − VDS_d = 0 을 **출발 공동 선택의 목표**(위반 최소화 단계에 넣는 등식 행, 해가 없으면 StartConflict). 외층은 자유 | P1s 발동 5회로(nmcnr 2, two_stage 1, two_stage_sf 1, ngcc 2, current_reuse 4) | 출발점에서 g 의 gm/ID·L 이 d 쪽으로 끌린다. nmcnr M109 slack 이 커진다(손: 1.04 V). 외층이 다시 벌릴 수 있음 |
| **B** θ 묶음(경성) | P1s 의 g 를 d 와 같은 gm/ID·L 동치류로 묶음(θ 축 감소) | 같음 | 체계 오차 구조적으로 0. g 의 gm(다음 단 gm2)은 전류로만 조절 → nmcnr 은 손 설계와 같은 자유도. ngcc 처럼 n 에 g 가 둘이면 둘 다 묶임 -- 충돌 가능 |
| **C** metric 제약 | `offset_sys_mv` 를 offset 가드 회로에도 제약으로: 상한 = 같은 점의 `offset_in_sigma_mv`(40 §3.8 '계통 ≤ 랜덤 예산' 규칙을 offset_excess 회로로 확장) | offset_excess 선언 6회로 | 판정 쪽에서 막는다. 단일 출력 회로는 출력 기준 DC 선언(SP-2 류)이 없으면 `reference_undeclared`로 계산 불가 → nmcnr 은 지금 효과 없음 |
| **D** 폐루프 DC 모드 | 커널 DC 를 선언 귀환(β)으로 닫아 입력 차전압을 미지수로(SPICE 테스트벤치와 같은 조건) | 귀환 선언 회로 | 체계 오프셋이 metric 으로 바로 나온다. 노드 위치는 바뀌지 않는다(3(a) 정정) -- 그 자체로 M109 slack 문제는 안 푼다. 커널 변경 범위 큼 |

### 3(e) 권고

**A(출발) + C(판정, 단 출력 기준 DC 선언이 있는 회로).** 이유: 술어가 연결만으로 정의되고(3(c)), 9회로에서 손분석·교과서 조건과 정확히 같은 인스턴스를 고른다. A 는 41 §6.7 의 기존 기계(행·위반 최소·StartConflict)를 그대로 쓴다. B 는 자유도를 줄이는 경성 결정이라 회로 해석 판단(사용자)이 필요하다. D 는 노드 위치를 바꾸지 않아 이번 증상에 대한 효과가 없다. 'P1s 가 정말 신호 경로인가'(current_reuse 의 Vg15·Vg25 처럼 바이어스 분배일 수 있는 것)는 공동분석 확인 항목이다(Q3-2).

### 3(f) 구현 위치·test

- 술어: S1 단계 구조 사실(`graph` 블록 하나, S0당 1회). 행: `E/search/iv_kvl.py`(41 §6.7-7)에 행 종류 추가, `iv_kvl_choice.py` 위반 최소 단계에 포함.
- test: 술어 toy(이름 없는 3소자 미러+다음 단) 발동/비발동, 9회로 발동 표 = 위 표(기준선은 test 작성 주체가 독립 재측정), nmcnr 출발점 M109 VDS − M108 VDS 가 tol_vdsat 안.

---

## 4. 항목 4 -- offset·noise 가드가 음수 경계(−6.7e-11, −1.2e-23)를 내는 원인 (시범 가설 3)

### 4(a) 재현과 판정

재현 스크립트 `guard_repro.py`(엔진 `guard_bounds` 를 감싸 입력만 기록), 결과 `out_guard/nmcnr_amplifier.json`(OPENBLAS=1), `out_guard_bd/`(BLAS 기본).

가드 식(E/search/_helpers_guard.py:298-328): level_k = ratio·Σ_in term_in(g_in) − Σ_{j≠k} term_j(g_lo,j). level ≤ 0 이면 경계 대신 `StartConflict(name, gm_id, ((source, level),), ...)`(89줄). **시범의 −6.7e-11·−1.2e-23 은 gm/ID 값이 아니라 이 level(단위 A², A²/Hz)이다.** 즉 '음수 상한'이 아니라 '부하 최소 기여만으로도 예산을 넘었다'는 충돌 기록이다.

왜 level < 0 인가(2차 호출 `match2`/`noise2`, 두 실행 조건):

| 양 | BLAS 기본 (시범과 같은 값 재현: level −6.713e-11, −1.230e-23) | `OPENBLAS_NUM_THREADS=1` |
|---|---|---|
| 가드에 넘어간 입력 전류 `currents1` (start_intervals.py:252, 1회차 매크로) | M102/M103 **5.57 µA** | **3.12 nA**(1회차 매크로가 UGF 없는 해 -- 항목 2 결함 3) |
| 가드에 넘어간 부하 전류 | M104/M105 **197 µA**, M108/M109 **67.9 µA** -- 매크로가 정하지 못해 자리값 `refs`(121줄: max(정해진 전류 기하평균, W_min·IDu(g_lo)/L), g_lo ≈ 0.55~0.84 강반전) | 같음(197 µA / 67.9 µA) |
| offset: ratio·Σ입력 (base) 대 Σ부하 최소 | 3.4e-12 대 1.0e-10 A² | 5.4e-18 대 1.0e-10 A² |
| noise: base 대 Σ부하 최소 | 2.5e-24 대 2.1e-23 A²/Hz | 9.2e-28 대 2.1e-23 A²/Hz |

입력:부하 전류비 1 : 35(BLAS 기본) ~ 1 : 6×10⁴(OPENBLAS=1) → 어느 조건에서도 어떤 gm/ID 로도 level < 0. 손분석의 실제 비는 1 : 2 : 1(I_D1 : I104 : I108). 자리값(W_min 전류, 강반전)이 실제 비보다 한두 자릿수 크게 들어가는 것이 두 조건 공통 원인이다.

**반사실**(`out_guard/counterfactual.txt`): 같은 ctx·L·경계에서 가드 전류만 일관 비(입력 I, 접힘 싱크 2I, 미러 I)로 바꾸면 충돌 0, 경계가 나온다(offset: M104 23.36·M108 15.34, noise: M104 24.43·M108 25.13, L 0.15). 손 L(0.5/2/2)에서는 offset M104 22.76·M108 17.59, noise 는 `no_feedthrough_free_point`(LUT 잡음 B 미상 칸)로 비활성.

판정:
1. **구현 결함(주원인)**: 41 §6.4-2a(1323줄)·§7.5(1596-1599줄)는 "gm_k/gm_in은 §6.5 매크로 모델 전류 비 r_k(KCL·미러 비)"를 쓰라고 한다. as-built 는 (i) 매크로가 정하지 못한 소자의 **자리값**(W_min 전류, 41 §6.1-9 '기준 전류' -- 층 0 Chebyshev 중심용)을 전류로 섞어 넘기고(252줄), (ii) `OPENBLAS_NUM_THREADS=1` 조건에서는 1회차 매크로가 UGF 없는 퇴화 해(항목 2 결함 3)를 '성공'으로 내 입력 전류가 nA 다. 두 값의 눈금이 서로 무관해 비가 무의미해진다.
2. **구현 결함(2차)**: 가드 항이 (g, W = max(I·L/IDu(g), W_min)) 에서 잰다(iv_noise.py:61, iv_matching_l.py:154). W 가 W_min 으로 잘린 점은 그 g 의 실제 동작점이 아니다(W_min 이면 같은 전류에서 gm/ID 가 달라진다) → 낮은 g 쪽 항이 인위적으로 작아진다(`out_guard/cf2.txt`: M104 L 0.15·2.84 µA 에서 g 8 까지 W < W_min). 또 `hull`(87줄)이 곡선 끝의 고립된 낮은 마디(LUT B 계단·감도 미정의 칸)를 '최대 g' 로 집는다(cf2: M104 noise 경계 24.43 = 곡선 첫 마디의 항 7.7e-26, 이웃 1.7e-24).
3. **design 빈칸 (가)**: 부하 전류에 **매크로·KCL 이 정하지 못하는 자유 θ 가지 전류**(폴딩 가지 I_c = M108)가 들어가면 r_k 가 정의되지 않는다. 41 §6.4-2a·§7.5 는 r_k 를 '매크로 전류 비'라고만 한다. 이건 항목 5 와 같은 빈칸이다.
4. **design 빈칸 (나)**: 가드는 합 제약(Σ_k 부하 ≤ ratio·Σ 입력)인데 41 §6.4-2a·§7.5 는 '부하 gm/ID 상한'으로 바꾸라고만 하고, as-built 는 41 §6.2 의 '나머지는 최소' 규약(_helpers_guard.py 독스트링 241-244줄)으로 소자별 상한을 낸다. 이 상한은 필요조건이지 충분조건이 아니다 -- §6.1-7 이 모든 부하를 동시에 t = 1(상한) 쪽으로 고르면 합이 넘친다. 시범 θ0 의 offset_excess·noise_excess c < 0 이 이 형태다.

### 4(b) design 현 문언과 빈칸 위치

- 41 §6.4-2a(1323줄): "부하 gm/ID를 상한으로 둔다. gm_k/gm_in은 §6.5 매크로 모델 전류 비로 쓴다" -- 자유 가지 전류일 때 r_k, 합→소자별 분해 규칙 없음.
- 41 §7.5(1596-1599줄): 같은 문언.
- 41 §6.1-4(1249줄)·'4의 전류를 정하는 방법'(1264줄): 1회차 매크로 전류를 쓴다 -- 매크로가 일부 소자 전류를 못 정할 때의 처리 없음(as-built 는 자리값).

### 4(c) 회로 원리 근거

열잡음: 소자 k 의 드레인 전류 잡음 4kTγ_k·gm_k, 입력 환산은 같은 출력 노드로 가는 비율이 같다면 (γ_k·gm_k)/(γ_in·gm_in)(41 §7.5). gm_k = (gm/ID)_k·I_k 이므로 가드는 Σ_k γ_k·(gm/ID)_k·r_k ≤ (E − 1)·Σ_in γ_in·(gm/ID)_in, r_k = I_k/I_in. **전류의 절대 눈금은 약분된다** → 가드는 전류 '비'만 있으면 되고 자리값 눈금은 들어갈 자리가 없다. offset 도 (gm_k σ_VGS,k)² ∝ (gm/ID)_k²·I_k²·A²/(W_k L_k) = (gm/ID)_k²·I_k·A²·IDu_k/L_k² 라 같은 이유로 r_k 만 필요하다.

시범 손 규칙: γ 가 비슷하면 1 + Σ_k (gm/ID)_k r_k / Σ_in (gm/ID)_in ≤ E → 2·g104 + g108 ≤ g102 (r = 2, 1). 이 '합' 형태가 원형이다.

### 4(d) 선택지

| 안 | 규칙 | 영향 회로(실측) | 예상 결과 |
|---|---|---|---|
| **A** 결함 정정 | 가드 입력을 '매크로·KCL 이 정한 전류'만으로 제한하고, 정하지 못한 부하가 있으면 그 부하만 `guard_current_ratio_undefined` 로 비활성 보고(자리값 사용 금지). W 클램프 점은 그 g 의 실현점이 아니므로 제외(W ≥ W_min 인 g 만), `hull` 은 단조 구간 안에서만 | 가드 선언 7회로 중 충돌이 실제 난 2회로: nmcnr(offset 4·noise 4 충돌), sf_pushpull(offset 12·noise 12 충돌, `current_ref` 없음 → 자리값 아닌 다른 원인, 별도 확인 필요). two_stage·two_stage_sf·ngcc·folded·cg 는 충돌 0 | nmcnr: 부하 4 소자가 '비 미정 비활성'으로 바뀐다(경계는 여전히 없음 -- B 또는 항목 5 필요) |
| **B** A + 자유 가지 비 규칙 | r_k 미정 가지의 비를 원리 규칙으로 정함: 항목 5 의 선택지(슬루 비차단 I_c ≥ I_in 등)를 그대로 공유 | 자유 가지가 있는 회로(항목 5 표) | nmcnr: r = (2, 1) → 반사실대로 경계 생성 |
| **C** 합 가드의 예산 분배 | 소자별 상한 대신 합 예산을 부하 묶음에 **같은 몫**(부하 묶음 수 n_L 로 나눔; 41 §6.4-2 의 '입력 몫 = 나머지 몫' 등분 원칙과 같은 꼴, 새 상수 없음)으로 나눠 각 상한을 역산 → 동시 선택해도 합 ≤ 예산 | 가드 선언 7회로 | 상한이 '나머지 최소' 규약보다 좁아진다(충분조건). 등분이 최적은 아님 -- 외층이 재분배 |
| **D** C 대신 출발 공동 선택 | 가드 합을 41 §6.7 의 행처럼 공동 선택(위반 최소 → max-min)에 넣음 | 같음 | 분배를 고정하지 않고 위치 최대화로 고른다. 41 §6.7 기계 재사용 |

### 4(e) 권고

**판정: 주원인은 구현 결함(4(a) 1·2)이다. 그 밑에 design 빈칸 두 개(가·나).** 권고는 **A + B + D**. A 는 design 문언('매크로 전류 비')을 구현이 어긴 것을 되돌리는 것이라 결정 없이 가능하다. B 는 항목 5 결정에 따른다. 합 분해는 D(41 §6.7 공동 선택 재사용)가 분배 상수를 만들지 않아 C 보다 원칙에 가깝다. 단 C 가 더 단순하다(결정 Q4-2).

### 4(f) 구현 위치·test

- `start_intervals.py:252`(currents1 구성), `iv_noise.py:61`·`iv_matching_l.py:154`(W 클램프), `_helpers_guard.py:298-328`(hull·분해), D 면 `iv_kvl_choice.py` 행 추가.
- test: (1) 전류 눈금 불변: 같은 비·다른 절대값(×10⁻³, ×10³)에서 가드 경계 동일(현재 `out_guard/counterfactual.txt` 에서 offset 경계가 눈금에 따라 23.36 → 충돌 → 24.40 으로 흔들림 = red 재현). (2) 자리값이 가드에 들어가지 않음. (3) nmcnr 손 비 (2, 1) 에서 2·g104 + g108 ≤ g102 꼴(γ 보정 포함) 경계가 손 유도 oracle 과 일치.

---

## 5. 항목 5 -- 전류 자리값 'uncovered' 가 41 §5 미구현 때문인가 (시범 가설 4, 확인만)

### 5(a) 코드 근거

1. 'uncovered' 는 **41 §6.5 출발 구간**에서 생긴다: `iv_currents.current_model` 이 "어느 입력 소자 방정식으로도 정해지지 않은 θ 전류 원소"를 `unassigned` 로 남기고(E/search/iv_currents.py:14, 180줄), `start_intervals._state` 가 그 소자를 자리값 `refs`(121줄)로 채우며 `current_from_macro: stage_current_unavailable` 를 기록한다(364-365줄). `StartIntervals.uncovered` 는 '구간이 값을 정하지 못한 θ 성분'(419-421줄)이다.
2. 41 §5(층 0 gain 예산)는 **미구현**이다: 41 §5.10-2 의 대상 파일 `layer0_budget.py`·`layer0_inverse.py`·`l_targets.py`·`local_candidates.py`·`combo_dp.py`·`assembly.py` 가 master `E/search/` 에 없다(있는 것은 `layer0_center.py` 뿐).
3. nmcnr 은 41 §5 가 구현돼도 **활성 조건 밖**이다: 41 §5.1(651-654줄) 첫 조건 "gain 제약 `gain_ss_db >= G`가 있다". nmcnr spec 제약은 gbw·pm·icmr·swing·offset_excess·noise_excess·area 이고 gain 이 없다(`out_survey/report.txt`). 41 §5.1 의 '해당 회로 목록'(670줄: common_gate, folded_cascode)에는 nmcnr·ngcc 가 빠져 있어 문언도 실측과 다르다.
4. 41 §5 가 활성인 회로에서도 이 소자들은 B 종류(41 §5.3.3 표 723줄: "부하·미러·바이어스 … 미러 비·KCL로 전파")이고, KCL 이 정할 수 없는 자유 가지 전류에 대한 규칙은 §5.3.1 입력 "블록 전류(KCL·선언·슬루 하한)"(690줄)뿐이다. 슬루 하한은 슬루 spec 이 있어야 한다(nmcnr 없음, `ls_constraints.py` 는 `driving.slew_rate_v_per_s` 선언 때만 행).

### 5(b) 9회로 uncovered 실측 (출발 구간, OPENBLAS=1)

| 회로 | uncovered 전류 원소 | 자리값 쓴 소자 수 | 41 §5.1 활성(gain 제약) |
|---|---|---|---|
| nmcnr_amplifier | M108, M109(폴딩 가지), M302, RL(출력 가지) | 8 | 아님 |
| ngcc_3stage_ff | M5, M6A | 3 | 아님 |
| folded_cascode | M3, M4, M5, M6, MP | 13 | 아님 |
| current_reuse_telescopic_ota | M18a, M1a, M25, M36a, M36b, M40, M4a (+ Cc2, R2) | 27 | 예 |
| common_gate_amplifier | M3 | 3 | 아님 |
| pushpull_follower_buffer | M2, M3, M4 | 6 | 아님(rout 모드) |
| two_stage_ota, two_stage_ota_sf, sf_pushpull | 전류 없음(저항·y 만) | 0 | 예 |

→ 자리값이 쓰이는 6회로 중 41 §5.1 로 층 0 이 켜지는 회로는 current_reuse 하나다.

### 5(c) 결론과 재측정 항목 문구 제안

결론: 'uncovered' 는 41 §5 미구현 때문**만**은 아니다. (1) 생기는 곳은 41 §6.5 이고, (2) nmcnr 은 gain 제약이 없어 41 §5 구현 뒤에도 층 0 이 돌지 않으며, (3) 돌더라도 자유 가지 전류를 정하는 design 규칙이 슬루 하한 하나뿐이다. 따라서 "② 완료 뒤 nmcnr 재측정"이 의미를 가지려면 아래 중 하나가 함께 정해져야 한다(질문 Q5-1).

자유 가지 전류 규칙 후보(결정 대상, 회로 해석):
- (가) **슬루 비차단 하한**: 차동 입력 블록의 꼬리 전류가 한쪽으로 다 몰려도 같은 노드에 KCL 로 묶인 자유 가지가 꺼지지 않을 최소 전류 = 그 노드로 들어오는 입력 소자 전류(시범 I_c ≥ I_D1). 구조 술어: 입력 소자 drain 노드에서 KCL 로 만나는 자유 θ 가지. 슬루 spec 불필요.
- (나) **gm 요구 역산**: 그 가지 소자가 다른 블록의 입력 소자이거나 영점 상쇄·비주극점 컨덕턴스 요구가 있으면 그 gm/(gm/ID) (nmcnr M301 → M302 가지, 출력 RL 전류는 출력 DC 선언에서).
- (다) **현행 유지 + 보고**: 자리값을 쓰되 판정·가드 입력에서 제외(항목 4 A)하고 외층에 맡김.

재측정 항목 문구(제안):

> **② 완료 조건 (nmcnr 재측정)**: master 의 ② 병합본에서 nmcnr 출발 구간을 다시 재고 다음을 표로 남긴다 -- (1) `uncovered` 전류 원소 목록과 각 원소를 정한 규칙(매크로 / KCL / 자유 가지 규칙 [Q5-1 결정] / 자리값), (2) 자리값이 남은 원소가 가드·매크로 목적 입력에 쓰였는지(쓰였으면 실패), (3) 41 §5.1 활성 여부와 그 사유(gain 제약 SP-4 결정 반영), (4) θ0 의 pm·offset_excess·noise_excess 행 c 값, (5) 같은 측정을 BLAS 기본·`OPENBLAS_NUM_THREADS=1` 두 조건에서 해 출발 θ 가 비트 동일한지(0.1). (1)에 자리값이 남으면 그 원소마다 사유를 붙이고 '판정 보류'로 둔다.

---

## 6. 항목 6 -- 좁은 폭 효과의 영향 범위 (DEC-72 모델 오차 항으로 다룰 선택지)

### 6(a) ngspice 측정

넷리스트 `narrow/sweep_{n,p}_0.6.cir`(시범 `mknet.py` 와 같은 인스턴스 형식·확산 기하 ad = W·0.5 µm, pd = W + 2 µm), |VDS| = 0.6 V, VSB = 0, VGS 0~1.8 V 5 mV 간격. 기준 = W 5 µm(LUT W_ref). gm/ID 목표점(5, 8, 12, 16, 20)의 기준 VGS 에서: ΔI/I(같은 VGS), ΔVGS(같은 전류밀도), Δ(gm/ID)(같은 전류밀도). 표 `narrow/narrow_table.md`, 원자료 `narrow/narrow_result.json`.

같은 전류밀도에서의 ΔVGS(mV, gm/ID 5~20 범위의 최소~최대):

| W(µm) | nmos L 0.15 | nmos L 0.5 | nmos L 2 | pmos L 0.15 | pmos L 0.5 | pmos L 2 |
|---|---|---|---|---|---|---|
| 0.36 / 0.42(p) | −3 ~ +16 | +9 ~ +32 | +4 ~ +44 | −22 ~ −51 | −98 ~ −124 | −120 ~ −131 |
| 0.42 / 0.55(p) | +30 ~ +67 | +5 ~ +25 | 0 ~ +37 | −28 ~ −66 | −85 ~ −104 | −96 ~ −112 |
| 1.0 | +24 ~ +54 | +15 ~ +31 | +8 ~ +33 | −27 ~ −59 | −44 ~ −63 | −61 ~ −70 |
| 2.0 | +5 ~ +28 | +9 ~ +15 | +7 ~ +18 | −11 ~ −37 | −16 ~ −25 | −23 ~ −27 |
| 3.0 | +3 ~ +13 | +8 ~ +13 | +5 ~ +15 | −5 ~ −24 | −6 ~ −16 | −14 ~ −18 |

- 같은 VGS 의 전류 오차: nmos W ≤ 1 µm −5 ~ −46 %, pmos W ≤ 1 µm +11 ~ +1045 %(약반전일수록 큼 -- ΔVTH 가 지수로 들어감).
- gm/ID(같은 전류밀도) 오차는 작다: nmos −12 ~ +1 %, pmos −14 ~ +10 %. → 협폭 오차는 **소신호보다 DC(바이어스 전압·노드 전위·포화 여유·체계 오프셋)** 에 크게 들어간다.
- 시범 대조: nmos W 0.36·L 2·gm/ID 5 에서 ΔI −18.8 %(시범 SPICE M104 −19.5 %), W 0.36·L 0.5·gm/ID 12 에서 ΔVGS +15 mV.
- **LUT 에 이미 있다**: `lut_data/sky130_lut_v2/` 에 nfet 20·pfet 13 개 W 슬라이스(0.36~7 µm, 모델 bin 경계 폭, 같은 ngspice·같은 확산 기하)가 있고, 슬라이스끼리 비교한 값이 위 직접 측정과 같다(예 pfet 0.42 µm·L 0.5·gm/ID 12: ΔI +165 %, ΔVGS −99 mV, ΔVTH −102 mV). 엔진은 레이아웃 전 사이징에서 kind 마다 W_ref(5 µm) 슬라이스 하나만 읽는다(E/sizing/pre_layout_widths.py:1-24, P DEC-91 (2)).

### 6(b) 엔진이 고르는 W 와의 겹침 (9회로 출발 구간 선택점, `out_survey/report.txt`)

| kind | 소자 수 | W < 0.5 µm(= W_min 0.42) | 0.5~1 | 1~2 | 2~3 | 3~5 | ≥ 5 |
|---|---|---|---|---|---|---|---|
| nmos | 74 | 18 | 0 | 4 | 7 | 11 | 34 |
| pmos | 68 | 14 | 0 | 0 | 0 | 3 | 51 |

- W < 3 µm: nmos 29/74(39 %), pmos 14/68(21 %). W_min 에 붙은 소자: common_gate(M1, M2, M3), folded_cascode(9 소자), nmcnr(M104~M107, M301, M108, M109, M302), pushpull(6 소자), two_stage_ota_sf(M3, M4).
- 이 소자들의 오차 크기(위 표): nmos W_min·L 0.15 에서 ΔVGS +30~+67 mV, pmos W_min·L 0.15 에서 −22~−51 mV. 봉인 7 의 여유 판정 단위(LUT `tol_vdsat`)와 시범 θ0 최악 slack 5.8 mV 보다 한 자릿수 크다.
- θ0 커널 스냅샷의 `dc_w` 열은 비어 있어(시범·이번 모두) 출발점 W 만 셌다.

### 6(c) design 현 문언과 빈칸

- P DEC-91 (2)·`pre_layout_widths.py` 독스트링: "레이아웃 전 첫 사이징점은 LUT 생성 규칙의 확산 기하를 쓴다", "레이아웃 뒤 실현 폭 슬라이스로 바꾸는 것은 DEC-89 재평가 몫". → 레이아웃 전에는 협폭 오차를 의도적으로 무시한다.
- P DEC-72(271줄): 모델 오차 = (회로, metric)별 SPICE 대조 측정값, 소비처는 NFR-5 여유·gain bin·층 0 점 상한 등. **소자 수준 DC 오차(VGS·노드 전위)를 봉인 tol 에 넣는 소비처는 없다**(빈칸).
- P LR3·41 §6.4-2(1318줄): L 은 bin 안에서만 보간하고 mismatch slope 는 bin(W, L)별로 읽는다 -- W 쪽 bin 은 mismatch 에서만 쓰고 DC LUT 읽기에는 없다.

### 6(d) 선택지

| 안 | 규칙 | 영향 | 비고 |
|---|---|---|---|
| **A** W 슬라이스 선택(bin 일관) | 소자의 실현 폭 W(= I·L/IDu)가 든 모델 W-bin 의 LUT 슬라이스를 읽는다. bin 경계를 넘는 보간 없음(LR3 의 L 규칙과 같은 꼴). W 가 θ 에 의존하므로 W → 슬라이스 → IDu → W 는 커널 안 고정점(bin 이 이산이라 유한 단계에서 멈춤, 상한 = bin 수) | W < 5 µm 소자 전부(9회로 nmos 40 %, pmos 25 %) | 데이터 이미 있음. DEC-91 (2) 개정 필요. 커널·LUT memo 키에 W bin 추가 |
| **B** 레이아웃 전 W 하한 | 슬라이스 간 ΔVGS 가 그 칸 tol_V 이하인 최소 폭 W_floor(kind, L, gm/ID)를 LUT 슬라이스에서 계산해 W ≥ W_floor 를 제약으로 | 같은 소자 | 상수 없음. 그러나 측정상 nmos 는 3 µm 에서도 8~15 mV → 사실상 W ≥ 5 µm → 작은 전류 소자의 전류·면적 증가(시범 Cm1 규칙이면 전류 ~14배) |
| **C** DEC-72 소비처 추가: 소자 DC 모델 오차 | 소자마다 |ΔVGS(W, L, 점)|(슬라이스 대 W_ref, 계산값)를 봉인 7·KVL 행의 여유에 더하는 'model_error_vgs_device' -- (회로, metric) 선언값이 아니라 LUT 에서 계산한 소자별 값 | 같은 소자 | DEC-72 의 '측정된 선언값 하나' 원칙과 형태가 다름(계산값) → DEC-72 문언 개정 필요. 오차를 고치지 않고 여유로 흡수 |
| **D** 현행 유지(DEC-89 재평가) + 보고 | 레이아웃 뒤 재평가에서만 반영, 레이아웃 전 front 에 '협폭 미반영' 표시 | -- | front 가 레이아웃 뒤 뒤집힐 수 있음(시범: M107 여유 0.067 → 0.023 V) |

### 6(e) 권고

**A.** 이유: 오차가 DC 에 크게(수십~백 mV) 들어가 봉인 7·체계 오프셋·바이어스 판정을 직접 흔들고, 데이터가 이미 같은 ngspice·같은 기하로 있어 상수를 만들 필요가 없다. LR3 의 bin 일관 규칙을 W 로 넓히는 것이라 원칙이 같다. C 는 오차를 고치지 않고 여유로 덮어 설계를 과하게 만든다(NFR-5 와 충돌). B 는 면적·전력 비용이 크다. A 는 DEC-91 (2) 개정이라 사용자 결정이 필요하다(Q6-1).

### 6(f) 구현 위치·test

- `E/sizing/pre_layout_widths.py`(w_key 선택), 커널 LUT 접근(`LutAccess.w_keys` → 소자별 W bin), LUT memo 키.
- test: (1) pfet W 0.42·L 0.5·gm/ID 12 에서 엔진 VGS 가 ngspice 직접 측정(위 표)과 tol_V 안 -- oracle 은 `narrow/` 의 독립 ngspice 결과. (2) W 가 bin 경계를 넘을 때 보간이 일어나지 않음. (3) 시범 손 설계점 재평가에서 M104 전류가 SPICE(2.29 µA)와 DEC-72 안.

---

## 7. 신규 항목 N1~N11 -- current_reuse·sf_pushpull 시범 (2차 갱신)

형식은 항목 1~6 과 같다((a) 현상·증거, (b) design 문언·빈칸 위치, (c) 회로 원리 유도, (d) 선택지 -- 구조 술어·선언값만, (e) 권고, (f) 구현 위치·test). 줄 번호는 master `9255a22` 기준. 9회로 영향은 실측한 것만 수치로, 못 잰 것은 '미측정'.

### 7.1 N1 -- 정착 시간 spec 만 있고 GBW 목표가 없으면 매크로가 꺼진다 (current_reuse H1)

**(a)** current_reuse spec `compensation_targets` = {`pm_target_deg`, `settling`{total_s 40 ns, linear_s 30 ns}}, `gbw_target_hz` 없음. 매크로 `macro_inactive{gbw_target_missing}`(E/search/macro_poles.py:21) → 모든 가지가 자리값(시범 `cr_rows.txt`: I0 = 1.2 µA = Iref 전부, 꼬리 M5 = 2·I1 + I61 KCL 과 모순, 출력 Iq 손의 1/28). `settling` 은 authoring 이 파싱만 한다(E/authoring/spec_targets.py:12-13 '과도 metric 이 레지스트리에 없어 보상 목표로만 쓰이고') -- search·sizing 에서 읽는 곳 0(`grep settling E/search E/sizing` 0건). 손: ε = 1/(1 + A0·β) = 0.41 %(A0 54 dB, β 0.484) → N = ln(1/ε) = 5.49 τ → ωc = N/t_lin = 1.83e8 rad/s(루프 UGF 29.1 MHz), SPICE 루프 UGF 29.25 MHz·소신호 정착 16 ns.
**(b)** 41 §6.3·§6.5 전제 = `gbw_target_hz`. 40 R27·P DEC-90 (2): 정착은 SPICE 기록만. **정착 → 루프 대역 규칙 없음(빈칸)**. 41 §6.4-3 1/f L 하한도 f_cl = β·`gbw_target_hz`라 같은 이유로 꺼진다(§8.2).
**(c)** 1극 폐루프 선형 정착: 오차 e(t) = ε0·exp(−ωc t), ωc = β·ω_GBW. 선형 정착 시간 t_lin 안에 ε 에 닿으려면 ωc ≥ ln(1/ε)/t_lin, ω_GBW ≥ ln(1/ε)/(β·t_lin). ε 는 spec 에 없다. 선언값만으로 정할 수 있는 유일한 짝은 '동적 오차 = 정적 오차' ε = 1/(1 + A0·β)(A0 = gain 제약 값, β = §7.5 v1.6 β) -- 손이 쓴 규칙이고 상수를 만들지 않는다. 슬루 몫(total − linear)은 계단 크기 미선언이라 규칙이 없다(SR ≥ ΔV/t_slew 의 ΔV 없음).
**(d)**
| 안 | 규칙 | 9회로 영향(실측, 정적) | 비고 |
|---|---|---|---|
| A | `gbw_target_hz` 가 없고 `settling` 과 gain 제약·β 가 있으면 GBW 목표 = ln(1 + A0·β)/(2π·β·t_lin) 로 유도(출처 `derived_from_settling`) | settling 선언 1/9(current_reuse). 나머지 8회로 무동작 | β 는 U17 ② 의 §7.5 β 계산 재사용. 2극(PM 목표 있음) 정착은 1극보다 느릴 수 있음 -- 외층 판정 몫 |
| B | spec 에 정착 오차 ε 선언 필드 추가(사용자 값) | 같음 | spec 결정 필요 |
| C | 현행(매크로 꺼짐 + 보고) | -- | 자리값 전류 유지 → current_reuse 출발 불가 계속 |
**(e)** **A**. 선언값(gain·β·t_lin)만 쓰고, 이 회로의 출발 실패 1순위 원인(전 가지 자리값)을 없앤다. ε 해석('정적 = 동적')은 spec 해석이라 사용자 확인(Q-N1).
**(f)** `E/search/iv_context.py`(목표 읽기, `_KEY_GBW` 24줄)에 유도 경로, 출처 어휘. test: settling·gain·β toy 에서 닫힌 식 GBW, 셋 중 하나 빠지면 비활성 사유 유지, 9회로 중 current_reuse 만 값 변화.

### 7.2 N2 -- 절대 offset 면적을 L 하한으로만 바꾸는 규칙이 입력 CM 창을 닫는다 (current_reuse H2, R2)

**(a)** `matching_l_6.4_2` 가 입력 L 하한 M1a/b 2.5 µm·M4a/b 3.22 µm(1차 조사 `out_survey/report.txt`: L 칸 {0.15: 47, 3.221: 2, 2.5: 2}) → θ0 M4a VDS −0.041 V. 손: current-reuse 입력 CM 창 [VDSAT5 + VGS4(VSB), VDD − VSDsat6 − VSG1(VSB)] 는 sky130 pfet |VT| ≈ 1.0 V(L ≥ 0.5)라 **L = 0.15(VT 0.76)·약반전에서만** 0.21 V 로 열린다 → 손은 offset 면적을 W 로 둔다(M1 25.97/0.15, M4 10.61/0.15, SPICE σos 3.34 mV). 긴 L 은 Cin(W 484 µm × 2.5 µm)도 키워 β 를 무너뜨린다.
코드: E/search/iv_matching_l.py:84-103 `_l_lower` 는 **입력 소자 gm/ID 하한(gm/ID_lo, 강반전 끝 = IDu 최대)에서** L ≥ √(A_min·IDu/I) 를 푼다(독스트링 10줄). 그 뒤 §6.1-7 은 gm/ID 를 구간 위쪽(시범 0.88 위치)에서 고르므로 L 하한이 실제 선택점보다 과대하다.
R2(§8.3): 같은 회로에서 offset·잡음 가드는 `constraint_not_declared` -- 가드는 구조 가드 metric(`offset_excess`·`noise_excess_th`) 전용이라 design 대로다. 그런데 §6.4-2 의 입력 몫 σ_share = σ_target/√2 는 '부하 기여 ≤ 입력 기여'를 전제하는데, 절대 제약 회로에서는 그 전제를 거는 부하 경계가 없다(빈칸).
**(b)** 41 §6.4-2(1323줄): '하한' L ≥ √(A_min·IDu/I) -- 어느 gm/ID 에서 재는지 문언 없음(as-built 는 g_lo). §6.4-6: L = max(이득·matching·flicker 하한). §6.2: `icm_margin_v`·`icmr_v` 는 입력 DC 선언 회로에서만 입력 경로 예산을 만든다 -- current_reuse 는 SP-2 대기라 **입력 CM 창이 출발 구간 어디에도 없다**. §6.4-2a·§7.5 가드는 구조 가드 metric 에서만.
**(c)** 면적 조건 W·L ≥ A_min 은 (gm/ID, L) 평면의 결합 조건이다: W·L = I·L²/IDu(g, L) ≥ A_min ⇔ IDu(g, L) ≤ I·L²/A_min. IDu 는 g 가 커질수록(약반전) 작아지므로 **같은 면적을 L 을 늘려서도, g 를 올려서(W 를 늘려서)도** 얻는다. 어느 쪽인지는 다른 경계가 정한다: 입력 경로 기둥(레일 → VSDsat → VSG_p(L) → 입력 gate → VGS_n(L) → VDSAT → 레일)의 VGS 는 VT(L) 를 통해 L 에 의존하고, 입력 gate 용량 Cin = W·L·Cox' 는 β 에 들어간다. 즉 '면적 → L 하한'은 원리상 한 방향만 고른 것이다.
**(d)**
| 안 | 규칙 | 9회로 영향 | 비고 |
|---|---|---|---|
| A | 현행(g_lo 에서 L 하한) | -- | current_reuse 출발 불가 유지 |
| B | 면적 조건을 L 하한이 아닌 **gm/ID 하한**으로: L 은 다른 경계가 정하고(§6.4-6 에서 matching 제외), 그 L 에서 IDu(g, L) ≤ I·L²/A_min 인 최소 g 를 gm/ID 하한(출처 `matching_area_6.4_2`)으로 | 절대 offset 선언 1/9(current_reuse), 입력 4소자 | 손 방식과 같다. 면적이 W 로 간다 |
| C | B + **입력 CM 창 비어 있지 않음 행**: 입력 DC 미선언이어도, 입력 gate 를 지나는 레일-레일 경로(§6.2 '입력 경로 기둥')의 Σ(VGS(L) + VDSAT) ≤ ΔV_rail 을 41 §6.7 목표 행(창 폭 ≥ 0)으로 | 입력 DC 미선언 + 입력 경로 기둥이 있는 회로(9회로 중 W4 `input_common_mode` y 가 있는 7회로) -- 행이 실제로 위반되는 회로 수는 **미측정** | L 은 §6.7 변수가 아니므로 행 위반 시 충돌 기록, L 후보 거르기는 §6.4-6 에서 |
| D | (R2 빈칸) 절대 offset·잡음 회로에도 §6.4-2a·§7.5 부하 가드를 '부하 ≤ 입력'(§6.4-2 등분 전제와 같은 E² − 1 = 1)으로 건다 | 절대 제약 선언 1/9(current_reuse) | 새 상수 없음(§6.4-2 가 이미 쓰는 등분 원칙) |
**(e)** **B + C + D**. 면적 조건의 원리(결합 조건)를 그대로 쓰고, 손분석이 찾은 이 회로의 핵심 제약(입력 CM 창)을 출발 구간에 넣는다. D 는 §6.4-2 의 전제를 실제로 거는 것이라 문언 정합.
**(f)** `iv_matching_l.py` `_l_lower`→gm/ID 하한 변환, `start_intervals.py` §6.4-6 선택, C 는 `iv_kvl.py` 행 종류 추가(U17 ②의 §6.7 구현과 함께), D 는 `iv_matching_l.py:113-118`·`iv_noise.py:73-75` 가드 조건. test: 면적 조건 toy((g, L) 두 점이 같은 W·L), current_reuse 입력 L = L_min·M4a VDS > 0, 절대 제약 없는 8회로 무동작.

### 7.3 N3 -- CMFB 평형 조건이 출발에 없다 (current_reuse H4)

**(a)** 엔진: M6·M36a·M36b·M39·M40 전류가 독립 θ(시범 4.2 표), layer0 점에서 봉인 7 `no_root_in_window` M37b·노드 Ncmfb_tail 창 [0, 0.249 V]. 손: I6 + I7 = 2·I1 + I68(P 꼬리 = N 꼬리 쪽 합), I37a = I37b, Voc = Voc_des(출력 포화 창 중앙 0.876 V)를 설계로 강제, SPICE CMFB PM 77.4°·전 MOS 포화. 손 r0 에서 협폭 오차로 N 꼬리 +11 %·P 꼬리 −11 % 가 되자 CMFB 범위를 넘어 Voc 1.263 V(목표 0.896)가 됐다 -- 평형 조건이 DC 해를 지배한다는 측정.
**(b)** 40 §5(1132-1156줄): CM 루프의 정의·절단 분류(구동/소비, `cm_partition`)·판정(PM)만 있다. **DC 평형(루프가 닫혔을 때의 동작점)을 출발에 거는 문언 없음(빈칸)**. 41 §6.7 은 VGS 고리·VDS-1 만. 항목 3(P1s)은 차동 미러 VDS 조건이라 CMFB 쌍에서 발동하지 않는다(1차 `sysoff_scan.txt` current_reuse 인스턴스에 M37 없음).
**(c)** CM 루프 이득 T_cm(0) ≫ 1 이면 DC 에서 오차 증폭기 입력 차 → 0: V(감지) = V(기준), 오차 쌍 전류 I_a = I_b = I_tail,err/2. 그 결과 CM 구동 소자(M7)의 VGS 가 정해지고, 1단 출력 CM 노드의 KCL(P 쪽 공급 = N 쪽 흡수)이 성립한다. 강제 전류 개루프 KCL 에서는 이 조건이 없으므로 고임피던스 CM 노드가 레일로 간다 -- 항목 3(차동 체계 오프셋)과 같은 부류('폐루프가 만드는 DC 조건이 개루프 강제 전류에 없음')이고 대상 루프만 다르다. 술어는 40 §5 의 CM 분할 결과(감지 넷·기준 넷·소비 소자)만 쓴다(이름 없음).
**(d)**
| 안 | 규칙 | 9회로 영향(실측, 정적) | 비고 |
|---|---|---|---|
| A | CM 평형 등식을 S1 전류 기저에: 오차 쌍(gate 가 감지 넷·기준 넷인 같은 kind 쌍, 공통 source) 전류 같음 + 출력 CM 노드 DC = 기준 넷 DC(쓰기 계획 고정 노드) | 차동 출력 포트쌍 회로 1/9(current_reuse). held-out D(wulffern cnr_ota, 저항 CMFB)도 대상 -- 일반성 증거 후보 | θ 축 감소(경성). '출력 기준 DC'가 생겨 Q3-3 offset_sys 확장 조건도 만족하게 됨 |
| B | 41 §6.7 목표 행 `cm_balance`(I_a − I_b = 0, V(감지) − V(기준) = 0, 위반 최소 단계) | 같음 | §6.7 변수는 gm/ID 위치뿐이라 θ 전류(I_a, I_b)를 못 움직인다 → 전류 행은 위반만 보고 |
| C | 현행(층 0 에 맡김) | -- | 시범: layer0 808 점 뒤에도 실패 |
**(e)** **A**. 평형 등식은 T_cm ≫ 1 의 결과라 경성으로 둬도 판정(전회로 `pm_cm_ss_deg`, 봉인)이 따로 확인한다. B 는 §6.7 변수 어휘(gm/ID 위치)로 전류를 못 움직여 효과가 없다. 회로 해석(CMFB 를 평형으로 닫는 것) 승인 필요(Q-N3).
**(f)** S1 `current_basis`(전류 기저, user_decisions 2026-10-12 '3번' 규칙 옆)에 CM 평형 등식, 쓰기 계획(`E/sizing/writer_plan.py`)에 출력 CM 고정 노드. test: 저항 감지 + 오차 쌍 toy, current_reuse θ 전류 수 감소·Ncmfb_tail 창 비지 않음, 단일 출력 8회로 무동작.

### 7.4 N4 -- 폐루프 DC 묶음 부재: 출력 사슬 y 가 자유 (sf H1)

**(a)** sf θ 에 W4 변수 y(N20)(시범 master; 1차 조사 master 에서는 y(Y)) -- 손 x3 θ 가 y 0.1 한 칸에서만 sealed, y 0.5(centre) 는 M1(TAIL)/M10(N910) `no_root_in_window`(시범 4.2 표). 봉인 점 vout 0.868/0.933 ≠ 0.9. 손은 β = 1 폐루프(vout = vin_dc = 0.9)와 기둥 B(M17·M20 같은 포화 여유)로 N20 을 정한다. SPICE 테스트벤치도 vin_n 을 vout 에 DC 연결(L = 1e15 H)해 동작점을 잡는다.
**(b)** P N3.8 PM(527줄)·U-48: '되먹임 수동소자가 없으면 β = 1 루프의 PM' -- **PM 정의**이고 DC 동작점 구성은 아니다. 41 §6.7-2: W4 창 넷은 상대 전위, y 는 출발 선택에서 고르지 않는다('VDS 배분은 층 0 몫'). **'β = 1 단위 이득 구성이면 출력 DC = 입력 DC' 를 거는 문언 없음(빈칸)**. Q3-3(결정): offset_sys 제약은 '출력 기준 DC 가 선언된 회로'에만.
**(c)** 단위 이득 DC 되먹임(β = 1, 저항·도선 경로)에서 V(out) = V(in) − V_os,sys. 체계 오프셋 0 근처의 출발점은 V(out) = V(in_dc). 이 등식 하나가 출력 사슬의 W4 자유도 y 하나를 없앤다(차원 1 대 1). 용량 되먹임(current_reuse Cf)은 DC 경로가 아니라 해당 없음 -- 술어 = '선언 되먹임이 DC 경로이거나 β = 1 규약' + '입력 DC 선언'.
**(d)**
| 안 | 규칙 | 9회로 영향(실측, 정적) | 비고 |
|---|---|---|---|
| A | 출발: 단계 A 에서 V(out)(y) = V(in_dc) 인 y 를 41 §6.7-2 출발 전위 모델로 1-D 근(`bracket_root`)으로 구해 출발 y 로. 판정: β = 1 구성을 '출력 기준 DC = 입력 DC 선언'으로 읽어 Q3-3 offset_sys 제약을 켠다 | 입력 DC 선언 2/9(sf, pushpull) 중 출력 사슬 y 가 있는 회로 1(sf). 입력 DC 가 SP-2 로 정해지면 출력 사슬 y 가 있는 6회로(common_gate, folded, ngcc, nmcnr, two_stage, two_stage_sf)로 늘 수 있음(**미측정**) | 커널 불변. y 는 외층에서 자유로 남고 offset_sys 가 묶는다 |
| B | 커널 쓰기 계획에서 출력 넷을 입력 DC 고정 노드(W2)로(SPICE 테스트벤치와 같은 구성) | 같음 | y 차원 제거(경성). 커널·W 계획 변경 범위 큼 |
| C | 현행 | -- | sf 가능 영역 = y 폭 ≈ 0.1 띠 |
**(e)** **A**. 출발만 바꾸고 판정은 이미 결정된 Q3-3 기계를 쓴다. 단 'β = 1(되먹임 소자 없음) = DC 단위 이득 구성'은 spec 해석이다 -- common_gate·pushpull 처럼 연산증폭기가 아닌 회로에도 같은 규약이 적용돼 있어 사용자 확인 필요(Q-N4).
**(f)** `iv_kvl.py`(§6.7 출발 전위 모델 재사용) 또는 `start_intervals` 의 y 출발, spec 해석 규칙은 authoring. test: 소스 팔로워 β = 1 toy 의 y 닫힌 식, sf 출발 y 가 손 띠(0.1~0.2) 안, 입력 DC 미선언 회로 무동작.

### 7.5 N5 -- DC 경로 θ 저항의 출발값이 전류와 무관한 상자 중점 (sf H2, current_reuse R1/R2)

**(a)** sf R1a/b/c 출발 31.6 kΩ(상자 [1 kΩ, 1 MΩ] ln 중점) × I(R1a) 3.0 µA = 95 mV → M6/M9 VSD → 0 → centre 실패 M9 VDS = 0. 손: R1 = (N5 − N1)/I1, (N5 − N1) = VSD6 창 [VDSAT6, min(VSG6 − VDSAT5, 기둥 A 상한 − VSG5)] 의 중앙 → 10.84 kΩ(r0)·SPICE 포화 PASS. current_reuse R2 `uncovered`, R1 = R2 는 CM 감지(대칭점 DC 전류 0)라 ΔV/I 가 정의되지 않는다. 손 R1 = R2 = 10 kΩ 의 근거는 spec 출처 기록 문언('출력 임피던스 대비 gain 손실이 허용 여유 안인 최소 저항', `element_values.R1.source.record`) -- 사용자 규칙이 기록돼 있으나 엔진 규칙은 없다.
**(b)** 41 §6.7-2(1438줄): "저항 = 선언값 또는 θ 저항 상자 기하 중심 × KCL 기저 전류". P DEC-70: DC 경로 미선언 저항은 θ. **전류·창에서 R 을 정하는 규칙 없음(빈칸)** -- 41 §6.5 '보상 수동소자 값 규칙'(PM 최소값)은 보상 소자만.
**(c)** DC 경로 저항의 역할은 노드 사이 전압차 ΔV = I·R 을 만드는 것이다. 그 ΔV 가 닿는 포화 행(41 §6.7-3)의 실행 가능 구간 [ΔV_lo, ΔV_hi] 은 출발 gm/ID 에서 정해지므로 R ∈ [ΔV_lo/I, ΔV_hi/I]. 그 안의 선택은 §6.7-4 와 같은 기준(행 최소 여유 최대, max-min)이면 새 상수가 없다. DC 전류 0 인 저항(대칭 CM 감지)은 이 원리가 비고, 역할이 '출력 부하'라 gain 제약(A0 ≥ G)에서 R 하한이 나온다(R‖r_out 손실).
**(d)**
| 안 | 규칙 | 9회로 영향(실측, 정적) | 비고 |
|---|---|---|---|
| A | DC 전류가 있는 θ 저항을 41 §6.7-4 공동 선택 변수로 추가(ln R, 상자 안 위치), 같은 기준(위반 최소 → max-min → 합 최대) | DC 경로 θ 저항이 있는 회로 2/9: sf(R1a/b/c), current_reuse(R1/R2, 단 전류 0) | §6.7 변수 어휘 확장(gm/ID 위치 + ln R 위치) |
| B | 닫힌 식 R = ΔV*/I, ΔV* = R 이 닿는 포화 행이 모두 ≥ 0 인 구간의 중앙 | 같음 | 행이 하나일 때 A 와 같음. 여러 행이면 중앙 선택이 A 보다 약함 |
| C | DC 전류 0 인 θ 저항: gain 제약의 국소 출력 저항 조건(R‖r_out 이 gain 손실 허용 안)의 최소 R -- spec 출처 기록의 사용자 규칙을 엔진 규칙으로 | current_reuse R1/R2(1/9) | gain 제약·출력 노드 매크로 컨덕턴스 필요 |
| D | 현행 | -- | sf centre 실패 원인 그대로 |
**(e)** **A + C**. A 는 §6.7 기계를 그대로 쓰고 B 보다 일반적이다. C 는 사용자가 이미 적은 규칙을 엔진 경로로 옮기는 것이라 새 원리가 아니다(단 규칙 해석 확인 Q-N5).
**(f)** `iv_kvl.py`·`iv_kvl_choice.py`(U17 ②), C 는 `start_intervals` 저항 출발. test: 저항 1개 자기바이어스 toy 의 R 창 닫힌 식, sf 출발 M6/M9 VSD > VDSAT + tol, DC 경로 θ 저항 없는 7회로 무동작.

### 7.6 N6 -- 출력단 약반전 요구(기둥 B KVL)의 출발 구간 (sf H7) -- 기본안: 새 규칙 없음

**(a)** 기둥 B: VDSAT17 + VGS22 + VSG21 + VDSAT20 ≤ 1.8 V(M21·M22 VSB 0.9 V)는 출력 2소자가 약반전(ln_idu −16.9~−17.8)일 때만 풀린다. centre M22 −13.8(중반전). 손 IC = 1 이면 VGS22 0.87 + VSG21 1.04 = 1.91 > 1.8.
**(b)** 41 §6.2 기둥 가용 폭 = ΔV_rail − Σ VGS_min(diode) − Σ R·I: 팔로워 VGS(diode 아님)는 기둥 식에 없다. 41 §6.7 v2 고리(class-AB VGS 고리 VSG18 + VGS19 = VGS22 + VSG21)와 포화 행(M17·M20 VDS)이 같은 사실을 출발 선택에서 다루고, §6.7-4 는 gm/ID 를 올리는 쪽(약반전)도 허용한다(B3). 단 M17·M20 VDS 행이 y(출력 사슬 W4)에 의존하는데 y 는 §6.7 이 고르지 않는다 → N4 와 엮인다.
**(c)** 팔로워 사슬의 레일-레일 경로가 gate-source 를 지나므로 KVL 이 VGS 합을 VDD 아래로 묶는다. 이 조건은 §6.7 의 고리·포화 행으로 이미 표현된다(새 술어 불필요).
**(d)** A **(기본안)** 새 규칙 없이 U17 ② §6.7 구현 + N4 A 뒤 sf 재측정. B §6.2 기둥 식에 'gate-source 를 지나는 기둥'의 VGS 를 넣어 gm/ID 하한을 만든다(§6.7 과 중복).
**(e)** A. 재측정에서 M22·M21 출발 ln_idu 가 손 띠(−16.9~−17.8)에 들지 않을 때만 B 를 다시 묻는다. 9회로 영향: 미측정(§6.7 미구현).
**(f)** 없음(② 재측정 항목: sf 출발 θ 의 M21·M22 ln_idu, M17·M20 VDS 행).

### 7.7 N7 -- PM 목표가 없으면 Cc 가 상자 하한 (sf H6) -- 기본안: 새 규칙 없음

**(a)** **9회로 실측**(`out_survey/*.json` `macro.caps`, master `3151392`): PM 목표가 없는 3회로 모두 Cc = 1.0e-13 F(θ 상자 하한) -- sf(`pm_target_deg` SP-3), two_stage_ota(SP-3), two_stage_ota_sf(`pm_target_deg` 없음, pending 도 아님). 셋 다 기록 `pm_floor_pole_at_ugf`(41 §6.5 as-built 1394줄: PM 목표 없으면 45° 바닥). PM 목표가 있는 ngcc 는 Cm1 0.71 pF·Cm2 0.1 pF, nmcnr 1 pF·1 pF. sf 손: Cc 1.033 pF(r0), 0.40 pF(x3, PM 41°).
**(b)** 41 §6.5 '보상 수동소자 값 규칙': 선언값 없으면 'PM ≥ 목표인 최소값'. 목표가 없으면 as-built 바닥 45°. 매크로 망에 비주극점(N9) 노드가 없어서(항목 1) 작은 Cc 에서도 바닥 45° 가 쉽게 만족된다(sf 매크로 PM 48.5° at Cc 하한, 노드 {Y, vout} 둘뿐).
**(c)** Cc 를 아래에서 미는 것은 비주극점 대비 주극점 분리(PM)다. 비주극점이 망에 없거나 PM 목표가 없으면 '최소 Cc'는 상자 하한으로 간다 -- 원인은 N9 노드 부재(항목 1 A)와 spec PM 미정(S2)이고 새 규칙이 필요한 빈칸이 아니다.
**(d)** A **(기본안)** 새 규칙 없음 -- 항목 1 A(N9, 결정 완료) + S2(PM 값, 사용자) 로 해소. B PM 목표 없는 회로에서 Cc 를 GBW 조건의 C_Y,tot(손 방식)로 정함 -- 매크로 UGF 조건이 이미 같은 일을 한다(중복).
**(e)** A. 항목 1 A 구현 뒤 세 회로 Cc 재측정을 ② 완료 조건 표에 추가.
**(f)** 없음(재측정 항목).

### 7.8 N8 -- 입력 CM 창(W4 `free_window`)에 VDSAT 이 없다 (current_reuse 새 후보 B)

**(a)** current_reuse θ0 y(input_common_mode) = 0.5 → M4a VDS −0.041 V(`lut_query_failed`, tol_v 셀 VDS 축 밖). 손 창 [0.770, 0.979] 는 포화 창, 중앙 0.875.
**(b)** E/sizing/block_columns.py 독스트링 11-17줄: `free_window` 창 = 채널이 닿는 MOS 마다 VDS ≥ 0 인 KVL 순서 창, "**VDsat 항은 넣지 않는다** ... W4 의존(`dc_scc_order`)을 바꿔야 한다(계약 12절 O1 잔여, 결정 대기)". 포화 창 재계산(`_solve_input_window`, 692줄)은 y = 1/2 풀이가 성공해야 시작된다. → **design 열린 항목(O1)이 출발 실패로 드러난 것**.
**(c)** VDSAT 은 소자 gate·bulk·자기 노드에 의존해 커널 안에서는 순환이지만, 단계 A 출발 선택점에서는 소자마다 출발 gm/ID·L 이 정해져 VDSAT 을 LUT 로 바로 읽을 수 있다(순환 없음). 출발 y 를 포화 창 중앙으로 두면 커널 W4 정의를 바꾸지 않고도 첫 풀이가 포화 창 안에서 시작한다.
**(d)**
| 안 | 규칙 | 9회로 영향(실측) | 비고 |
|---|---|---|---|
| A | 커널 W4 창에 VDSAT 포함(O1 해소, `dc_scc_order` 의존 변경) | W4 input_common_mode y 가 있는 7/9(common_gate, current_reuse, folded, ngcc, nmcnr, two_stage, two_stage_sf) | 커널 결과 바뀜, 기본 호출 지문 재측정 |
| B | 출발 y 만: 단계 A 에서 출발 gm/ID·L 의 VDSAT 으로 포화 창을 계산해 그 중앙의 y 를 출발값으로(커널 불변) | 같은 7회로의 출발 y(실제로 바뀌는 회로 수 **미측정**) | O1 은 열린 채 |
| C | 현행 | -- | |
**(e)** **B**. 출발점 생성 문제에 출발 쪽 정정으로 답하고 커널 결정(O1)은 따로 둔다.
**(f)** `start_intervals`(또는 U15 placer) y 출발, `iv_headroom` VDSAT 재사용. test: 입력쌍 toy 의 포화 창 닫힌 식, current_reuse 출발 M4a VDS ≥ VDSAT + tol.

### 7.9 N9 -- 체계 오프셋 술어의 캐스코드 확장 P1c (sf H4)

**(a)** sf 거울 복사쌍의 밀도가 묶이지 않음: M5/M7/M11 ln_idu −23.7 대 M10/M12 −15.2(centre θ0), I(R1a) 3 µA 대 I(M9) 9.8 µA. 손: M5 = M10, M6 = M9 = M17 등 같은 밀도(VSG 일치). 결정된 P1s(Q3-1)는 기준이 diode 이고 미러 출력 노드에 gate 가 닿는 경우만이라 이 캐스코드형에서 발동하지 않는다.
**(b)** Q3-1 결정 문언(P1s)·41 §6.7 `mirror_vds` 행(② 반영 예정).
**(c)** 미러 쌍 (r, o)(같은 kind·gate·source) 의 VDS_r = VDS_o 는 V(r.drain) = V(o.drain). 두 drain 노드를 source 로 쓰는 MOS a, b 의 gate 가 같으면 V(n_r) = V(g) − VGS_a, V(n_o) = V(g) − VGS_b 이므로 조건은 **VGS_a = VGS_b** -- P1s 와 같은 결론((gm/ID, L) 같음, 전류는 달라도 됨). 연결만으로 정의된다(이름·회로족 없음).
**(d)** 술어 P1c: 미러 쌍 (r, o) + r.drain 을 source 로 쓰는 a, o.drain 을 source 로 쓰는 b, a.kind = b.kind, a.gate = b.gate. **9회로 실측**(`sysoff_cascode_scan.py`/`.txt`): 6 인스턴스 3회로 -- folded (M10, M9; M8, M7)(기준 diode), (M3, M4; M6, M5); nmcnr (M104, M105; M106, M107); sf (M6, M9; M5, M10), (M14, M16; M13, M15), (M11, M8; M12, M7). folded (M3, M4)·nmcnr (M104, M105)는 대칭 반쪽이라 U2 궤도 묶음이 이미 같게 하므로 행이 0 으로 무동작일 것으로 본다(**미측정**). 선택지: A P1c 를 같은 행 종류 `mirror_vds` 에 추가(Q3-2 '신호 경로' 조건 함께), B 넣지 않음.
**(e)** **A**. Q3-1 에서 결정한 원리의 같은 꼴 확장이다. 회로 해석 확인(Q-N9).
**(f)** S1 술어(항목 3 과 같은 블록), test: 캐스코드 미러 toy 발동/비발동, 9회로 발동 표 = 위 표(기준선은 test 작성 주체가 독립 재측정).

### 7.10 N10 -- L 동치류가 헤드룸 역할 소자를 꼬리 L 에 묶음 (current_reuse 새 후보 A) -- 기본안: 보류

**(a)** Vbias4 gate 공유 소자(M12/M21 병진 싱크, M38 CMFB 꼬리)가 L 동치류(주인 M5, `owner_rule` `tail_first_gain_stage`, E/graph/l_classes.py:9·28)로 묶여 L = 1 µm. 손은 이 셋을 L 0.15(N11b·Ncmfb_tail 헤드룸). 손 θ 를 엔진에 넣으면 묶음 때문에 M21 이 L = 1 이 되고 봉인 7 최악 slack 18.6 mV(손 r0 같은 여유 26 mV 와 일치) -- 봉인은 통과한다. **출발 실패의 직접 원인이라는 측정은 없다.**
**(b)** P DEC-17·DEC-04(L 동치류 멤버는 L 공유). 미러 멤버의 L 을 갈라 쓰는 손 설계(같은 gate 다른 L → 미러 비가 W 비가 아님)는 이 규칙 밖이다.
**(c)** 같은 gate·source 의 소자가 다른 L 을 가지면 같은 VGS 에서 IDu 가 L 마다 달라 전류 비가 W 비만으로 정해지지 않는다 -- 동치류 규칙은 이 정합을 위한 것이고, 헤드룸 이득은 그 대가다. 어느 쪽이 맞는지는 회로 해석이다.
**(d)** A **(기본안)** 보류: N1~N8 반영 뒤 current_reuse 출발이 이 묶음에서 막히는지 재측정. B 헤드룸 행이 위반되는 동치류 멤버만 동치류에서 떼는 규칙.
**(e)** A. 증거가 약하고 회로 해석이라 지금 design 을 바꾸지 않는다.
**(f)** 재측정 항목: current_reuse 출발점 봉인 7 최악 소자·여유.

### 7.11 N11 -- 잡음(소신호 metric) 분해능 정의: 값의 61 % (current_reuse `noise_basis.md` §5-1)

**(a)** **실측**(이번, master `9255a22`, `OPENBLAS_NUM_THREADS=1`, `_step2_gaps/noise_res/noise_res_probe.py` → `out_noise.txt`; 파일럿 r2 손 θ, 엔진 `noise_integral._final` 를 감싸 같은 식의 항을 따로 기록, 엔진 불변): 값 719.8 µVrms, 분해능 440 µV(시범 재현). 분해 -- **파라미터 항 Σ_p |∂I/∂p|·Δp = 391 µV(89 %)**, 열잡음 칸 tol 항 45 µV, flicker tol 항 3.8 µV. 파라미터 306 개(MOS 51 × {gm, gmb, gds, cgs, cgd, cgb} 중 0 아닌 것), ε_d(MOS 별 상대 불확실성) 최소/중앙/최대 = 7.8e-5 / **0.169** / 0.326. 상위 두 소자(대칭 쌍)의 gm 항이 각 14 %. 같은 Δp 를 RSS 로 합치면 97 µV(값의 13 %).
**(b)** 코드는 계약 그대로다(구현 결함 아님): metrics CONTRACT 9.1(899-907줄) **ε_d = (gm/ID)_d · tol_V,d**(tol_V = `id_equivalent` 셀, 'LUT 전류의 상대 불확실성'), Δp = ε_d·|p| 를 6 열 모두에; 9.3(933줄) **결합 규칙 = 최악 선형 Σ|∂q/∂p|·Δp**('상관을 가정하면 비 꼴 metric 에서 상쇄로 과소평가'). 구현 `E/metrics/lut_parameters.py:37-68`, `E/metrics/noise_integral.py:151-158`. 41 §7.3 '분해능'은 'metrics §9 와 같은 방식'.
**(c)** ε_d = (gm/ID)·tol_V 는 **같은 VGS 에서의 전류** 상대 오차다. 봉인 스냅샷의 소신호 값은 전류 ID(θ·KCL 로 정해짐)와 노드 전압 점에서 읽은 gm/ID·gds·C 열로 만든다 -- 노드 전압 점이 tol_V 만큼 어긋나면 gm 의 상대 오차는 |∂ln(gm/ID)/∂VGS|·tol_V 이고 (gm/ID)·tol_V 가 아니다. 약반전에서는 gm/ID 가 평탄해 앞의 값이 훨씬 작고, ε_d 가 큰 곳(gm/ID ~20)이 바로 약반전이다. 다른 열도 같은 식(그 열의 VGS 기울기 × tol_V)으로 같은 LUT 에서 얻는다(새 상수 없음). 결합: 306 항의 부호가 모두 같은 방향이라는 최악 가정은 판정을 '보류 쪽'으로 크게 민다(이번 값에서 RSS 의 4 배).
**(d)**
| 안 | 규칙 | 영향 | 비고 |
|---|---|---|---|
| A | 현행 | current_reuse 잡음 판정 c 가 spec 450/300 µV 모두 ±1 안 → 사실상 판정 보류 | -- |
| B | Δp = abs(∂ln p/∂VGS)(LUT, 그 점) × tol_V × abs(p) -- 열마다 VGS 기울기로 전파(결합은 최악 선형 유지) | 모든 ss metric 의 분해능(9회로) -- **미측정** | 같은 tol_V·같은 LUT, 새 상수 0. 보수 결합 유지 |
| C | 결합을 RSS 로(Δp 그대로) | 잡음 r2: 440 → 97 µV(실측 1점). 다른 metric·회로 **미측정** | 계약 9.3 의 '상관 과소평가' 우려는 RSS(독립 가정)에는 해당하지 않으나, 최악 보장이 없어진다 |
| D | B + C | -- | -- |
**(e)** **B 먼저**(유도 정정, 보수 결합 유지), 그 결과로 C 판단. 분해능은 NFR-5 판정 단위라 계약 변경은 사용자 결정(Q-N11). S3(잡음 spec 값)과 함께 정해야 한다(분해능이 값과 같은 크기면 어떤 spec 값도 판정되지 않는다).
**(f)** `E/metrics/lut_parameters.py`(Δp), `ss_dev` 의 `lut_rel_tol` 생성(CONTRACT 509줄), 계약 9.1·9.3. test: 단일 소자 toy 에서 Δgm = LUT 기울기 × tol_V 닫힌 식, 약반전 점에서 B < A, 9회로 분해능 표(재측정 기준선은 test 작성 주체 독립).

---

## 8. 구현 결함과 재분류 (결정 불필요)

### 8.1 D1 -- W_min 소자의 W 반올림이 mismatch bin 밖으로 (구현 결함)

- **위치**: W = ID·L/exp(ln IDu)(`E/sizing/block_widths.py:47`) → mismatch bin 판정 `bin_index`(`E/lut/_helpers_bins.py`: 경계 비교 허용 **1 ulp**) → `_block_of` 없음 → `seal_violation("lut_mismatch_no_block")`(`E/lut/mismatch_sigma.py:23-44`). `E/metrics/device_sigma.py` `_sigma` 는 W 가 bin 최대 폭을 넘을 때(finger 분할)만 처리하고 최소 폭 아래는 처리하지 않는다.
- **재현 1**(master `9255a22`, `_step2_gaps/noise_res/out_wmin.txt`): 파일럿 r2 손 θ 에서 파일럿이 넣은 우회(W × (1 + 1e-7))만 빼면 `status='failed'`, `SEAL_VIOLATION`, `lut_mismatch_no_block`, W = 3.599999999999999e-07(nmos, L 1 µm -- M37a/b 류 W_min 소자). 우회를 넣으면 `sealed`(`out_noise.txt`). 실패 레코드의 `devices=()` 로 소자 이름도 빠진다.
- **재현 2**(순수 산술, `bin_index` 직접 호출): W_min 에 놓인 소자를 ln IDu = ln(I·L/W_min) → W = I·L/exp(ln IDu) 로 왕복하면 (I, L) 무작위 10만 점 중 **37.6 %(0.36 µm)·39.9 %(0.42 µm)** 가 bin 하한 아래로 1 ulp 넘게 떨어진다(왕복 오차 ~수십 ulp).
- **발생 경로**: 엔진 출발점은 W_min·(1 + _REL)로 띄워(`E/search/start_intervals.py:133`) 피한다. 외층 W 하한 행(`E/search/constraints.py:37`, W − W_min ≥ 0)은 W = W_min 경계를 허용하므로 탐색이 경계에 닿으면 이 실패가 난다(빈도 **미측정**).
- **정정 방향**(design 변경 없음): bin 조회 전 W 를 PDK 선언 제조 격자(`manufacturing_grid_m`, `search_values.py:79`)에 맞춘다(실현 폭은 격자 위 값) -- 또는 허용오차를 왕복 오차 상계로. test: W_min 왕복 toy, 파일럿 손 θ 우회 없이 sealed.

### 8.2 R1 -- 선언된 되먹임에서 β 를 못 얻음 → 재분류: 미구현(U17 ② 예정)

- `E/search/iv_noise.py:67-70`: `noise_out_int_vrms` 선언이면 flicker L·열잡음 C_eff 를 `feedback_factor_beta_unavailable`·`c_eff_not_a_start_bound` 로 비활성 보고 -- 독스트링 9-13줄이 '출발 입력 묶음에 β 가 없다'고 적은 그대로다.
- design 41 §7.5 v1.6(1613-1617줄) 'β·C_eff 입력 배선'이 β 정의(Cf/(Cf + Cs + Cin))·C_eff·S0 필드 `graph/start: noise_inputs` 를 정했고, 40 v1.9.1 D3 가 U17 ②에서 만든다고 정했다. → **결함 아님, 예정된 미구현**.
- 주의(새 사실): ② 구현 뒤에도 1/f L 하한은 f_cl = β·`gbw_target_hz` 라 current_reuse 에서 `gbw_target_missing` 으로 꺼진다 → N1 과 묶어야 실제로 켜진다.

### 8.3 R2 -- 가드가 선언된 offset·noise 를 '미선언'으로 읽음 → 재분류: design 대로

- `E/search/iv_matching_l.py:107-118`·`iv_noise.py:73-75`: 가드는 `offset_excess`·`noise_excess_th`(구조 가드 metric)만 읽는다. current_reuse 는 절대 제약(`offset_in_sigma_mv`·`noise_out_int_vrms`)을 선언했고, 41 §6.4-2(절대 offset → matching L 하한, 실제로 4소자 활성)·§7.5(절대 잡음 → C_eff·1/f, R1)가 그 경로다. 41 §6 머리(1237줄) '절대 offset 제약이 있으면 matching L 하한, offset 구조 가드가 있으면 부하 gm/ID 상한'.
- → **결함 아님**. 남는 빈칸(절대 제약 회로의 부하 몫)은 N2 D.

### 8.4 엔진 잡음 분해능 440 µV → N11 로 이동

- 코드는 metrics CONTRACT 9.1·9.3 대로 계산한다(§7.11 (b)). 원인은 계약의 ε 정의와 최악 선형 결합이라 **결정이 필요한 design(계약) 항목**으로 옮겼다.

---

## 9. spec 문제 (사용자 몫)

### 9.1 S1 -- sf {gain ≥ 65 dB, noise_excess_th ≤ 2, 입력 DC 0.9 V} 동시 실현 불가(손분석 결론)

- 근거(sf 시범 3.2·3.3): 보정된 손 모형(Gm 손실 k = ro1/(ro1 + Z_N1), Cgb, N1 극점)으로 잡음 가드 등호 조합 18개 × L 격자 전수 → **이득 제약을 만족하는 (Lp, Ln) 없음**(최대 R_Y/R_req = 0.99, 그 점은 Lp = Ln = 4 µm·거울 극점 5 MHz). 사슬: 잡음 가드 → 부하 gm/ID 낮음 → pfet VSG 큼 → 기둥 A 가 VDS1·VSD6 를 누름 → ro1·ro9 작음 → Gm 손실·R_up 부족.
- 반대 실험: 잡음 가드만 풀면(x3: g1 16, gp = gn = 12, Cc 0.40 pF) SPICE gain 66.93 dB·GBW 62.0 MHz·Rout 961 Ω·전 MOS 포화 PASS, noise_x 3.20, PM 41°.
- 엔진 잡음 정의(LUT 소자별 γ)는 손 정의보다 엄격하다(r0 손 1.99 PASS ↔ 엔진 c −0.69 FAIL) → 충돌은 엔진 정의에서 더 강하다.
- 한계: '실현 불가'는 손 모형·이산 격자의 결론이고 SPICE·엔진 front 로 증명된 것은 아니다.
- 선택지: (가) `noise_excess_th` 를 이 회로에서 보고만으로(이 구조 가드는 design 41 §7.1 회로별 선언의 공통 규칙 '부하 잡음 ≤ 입력 잡음'이다), (나) noise_excess_th 값 완화(값은 사용자), (다) gain 완화, (라) 유지하고 엔진이 '실현 불가'를 보고하는지 ② 뒤 확인.

### 9.2 S2 -- PM 목표 미정 (sf SP-3, 그리고 같은 상태의 2회로)

- sf `pm_target_deg` = pending SP-3, two_stage_ota = pending SP-3, **two_stage_ota_sf = 목표 자체 없음**(pending 도 아님) -- 실측 3회로 모두 매크로가 바닥 45° 로 풀려 Cc = 상자 하한(N7).
- sf 손 x3 은 GBW 를 맞추려고 PM 41° 를 받아들였다 -- PM 값이 정해지면 GBW·Cc 결론이 바뀐다.

### 9.3 S3 -- current_reuse 잡음 spec (별도 결정 중)

- 근거 `_pilot_current_reuse/noise_basis.md` §4: 현 300 µVrms 는 논문 값(대역 미상). design 41 §7.1 적분 규칙(최고 극점 21.6 GHz 까지)에서 r2 757.9 µV, 재설계 c_k8m4s2 438.5 µV(282 µW, 다른 spec 전부 통과), 300 µV 는 외삽 ~520 µW.
- 후보: **C1 ≤ 450 µVrms 차동(권고)**, C2 300 µV + 대역 상한 π/2·UGF(design 41 §7.1 개정 필요), C3 300 µV 유지, C4 구조 가드로 대체.
- 엔진 분해능(N11)이 값과 같은 크기(440 µV)라 어느 값이든 N11 결정과 함께 정해야 판정이 된다. spec 문구에 '차동 출력' 명시 필요(단일 출력이면 CM 바이어스 잡음 3.35 mV 가 지배).

---

## 10. 요약 표

| 항목 | 성격 | 권고 | 상태 |
|---|---|---|---|
| 0.1 BLAS 스레드에 따른 출발 구간 차이 | 구현(결정론) -- 항목 2 결함의 2차 현상 추정 | 항목 2 정정 뒤 두 조건 비트 동일 확인을 ② 완료 조건에 | 결정 완료(Q0) |
| 1 동적 spec → L | **구현 gap**(41 §6.5 N9 기록 없는 축소) + design 빈칸 | A(N9 구현) 먼저, 재측정 뒤 B/C. D(ii) | A 결정 완료(Q1-1), D(ii)+(i) 결정 완료(Q1-2), E 기본안 = 현행(Q1-3, 확인 Q-R1) |
| 2 매크로 시작값·k < 1 | **구현 결함 3건** + design 빈칸 | A + B. 회로족 해석식(k < 1)은 규칙으로 넣지 않음 | 기본안(Q2-1·Q2-2) |
| 3 체계 오프셋 0 | **design 빈칸** | A + C | 결정 완료(Q3). 캐스코드 확장은 N9 |
| 4 가드 음수 경계 | **구현 결함(주)** + design 빈칸 2 | A + B + D | A 결정 완료(Q4-1), D 기본안(Q4-2), B 는 Q5 결정에 따름 |
| 5 uncovered 자리값 | §5 미구현만이 아님 | 재측정 문구 + 자유 가지 규칙 | 결정 완료(Q5: (나)+(가), 문구 채택). nmcnr 은 이제 gain 선언(Q1-2 (i)) |
| 6 좁은 폭 | design 선택(DEC-91 (2))의 영향 큼 | A(W-bin 슬라이스) | 결정 완료(Q6) |
| N1 정착 → GBW | design 빈칸 | A(ε = 1/(1 + A0·β) 로 GBW 유도) | **미결**(Q-N1) |
| N2 matching 면적 W/L 배정 | design 빈칸(+ 절대 제약 부하 몫) | B + C + D | **미결**(Q-N2) |
| N3 CMFB 평형 | design 빈칸 | A(S1 전류 기저 + 출력 CM 고정) | **미결**(Q-N3, 회로 해석) |
| N4 폐루프 DC 묶음 | design 빈칸 + spec 해석 | A(출발 y 근 + Q3-3 offset_sys) | **미결**(Q-N4) |
| N5 DC 경로 θ 저항 출발값 | design 빈칸(41 §6.7-2 '상자 중심') | A(§6.7 변수) + C(전류 0 저항 = 이득 손실 규칙) | **미결**(Q-N5) |
| N6 출력단 약반전 | design 범위 확인 | 새 규칙 없음, ② 뒤 재측정 | 기본안 |
| N7 PM 미정 시 Cc 하한 | spec + 구현 gap(항목 1) | 새 규칙 없음 | 기본안 |
| N8 입력 창 VDSAT | design 열린 항목(O1) | B(출발 y = 포화 창 중앙) | **미결**(Q-N8) |
| N9 캐스코드 미러 P1c | design 빈칸(Q3 확장) | A | **미결**(Q-N9, 회로 해석) |
| N10 L 동치류 헤드룸 | 회로 해석, 증거 약함 | 보류·재측정 | 기본안 |
| N11 소신호 분해능 정의 | design(계약) | B 먼저, 뒤에 C 판단 | **미결**(Q-N11) |
| D1 W_min bin 반올림 | **구현 결함** | 제조 격자 맞춤 | 결정 불필요 |
| R1 β 미획득 | 미구현(U17 ② 예정) | -- | 결정 불필요(N1 과 연동 주의) |
| R2 가드 '미선언' 판독 | design 대로 | -- | 결정 불필요(빈칸은 N2 D) |
| S1 sf spec 동시 실현 불가 | spec | (라) 확인 후 (가) | **미결**(Q-S1) |
| S2 PM 목표 미정 3회로 | spec | 값 지정 | **미결**(Q-S2) |
| S3 current_reuse 잡음 spec | spec | C1 ≤ 450 µVrms 차동 | **미결**(Q-S3) |

---

## 11. 사용자에게 물을 질문 (결정이 필요한 것만)

1차 질문 Q0~Q6 은 모두 결정 또는 기본안으로 닫혔다(머리의 결정 상태 표). 아래는 남은 것뿐이다.

- **Q-R1** (확인) Q1-3 의 기본안을 '현행 유지(knee 초기 L 은 층 0 에만)'로 적었다 -- (나) 그룹 기본안의 뜻이 이것이 맞나? → **권고: 맞다고 두고, 항목 1 A·Q1-2 (ii) 반영 뒤 L_min 고착이 남는 회로가 있을 때만 다시 묻는다.**
- **Q-N1** 정착 시간만 선언한 회로(현재 current_reuse 1개)에서 GBW 목표를 ε = 1/(1 + A0·β)('동적 오차 = 정적 오차')로 유도해 매크로를 켤까? → **권고: 예(A). 선언값(gain·β·t_lin)만 쓰고, 전 가지 자리값이라는 이 회로 출발 실패 1순위 원인을 없앤다.**
- **Q-N2** 절대 offset 면적 조건을 'L 하한'이 아니라 '그 L 에서의 gm/ID 하한'(면적을 W 로)으로 바꾸고(B), 입력 DC 미선언이어도 입력 CM 창이 비지 않는다는 행을 출발에 넣고(C), 절대 offset·잡음 회로에도 '부하 ≤ 입력' 부하 가드를 걸까(D)? → **권고: B + C + D. 면적은 (gm/ID, L) 결합 조건이라 L 한 방향만 고를 근거가 없고, 손분석이 찾은 이 회로의 핵심 제약(입력 CM 창)을 넣는다.**
- **Q-N3** (회로 해석) CMFB 루프를 DC 평형으로 닫아 '오차 쌍 전류 같음 + 출력 CM DC = 기준 넷 DC'를 S1 등식으로 둘까? → **권고: 예(A). T_cm ≫ 1 의 결과라 경성으로 둬도 판정(`pm_cm_ss_deg`·봉인)이 따로 확인하고, held-out D(저항 CMFB)가 일반성 검증 대상이 된다.**
- **Q-N4** (spec 해석) '되먹임 소자 없음 = β = 1' 규약을 DC 에도 '단위 이득 구성(출력 DC = 입력 DC)'으로 읽어, 출발 y 를 그 등식으로 정하고 offset_sys(Q3-3)를 켤까? 연산증폭기가 아닌 회로(common_gate·pushpull)는 어떻게 둘까? → **권고: 연산증폭기(차동 입력 + 단일 출력) 회로에만 예(A), 나머지는 현행. 지금 바뀌는 회로는 입력 DC 가 선언된 sf 1개.**
- **Q-N5** DC 전류가 흐르는 θ 저항을 41 §6.7 공동 선택 변수로 넣고(A), DC 전류 0 인 θ 저항(CM 감지 R1/R2)은 spec 출처 기록의 사용자 규칙('이득 손실이 허용 안인 최소 R')을 엔진 규칙으로 옮길까(C)? → **권고: A + C. 상자 중점 출발이 sf 출발 실패의 직접 원인이고, C 는 이미 적힌 사용자 규칙이다(해석이 맞는지만 확인).**
- **Q-N8** 입력 CM 창의 VDSAT 누락(sizing CONTRACT 12절 O1)은 커널을 고치지 않고 출발 y 만 단계 A 의 포화 창 중앙으로 둘까(B)? → **권고: B. 출발점 문제는 출발 쪽에서 고치고 커널 O1 은 따로 둔다.**
- **Q-N9** (회로 해석) Q3-1 의 P1s 를 캐스코드 미러형 P1c(미러 쌍 drain 을 source 로 쓰는 같은 gate 의 두 소자 → 같은 (gm/ID, L))로 넓혀 같은 `mirror_vds` 행에 넣을까? → **권고: 예(A). 같은 원리의 확장이고 9회로 실측 6 인스턴스 중 대칭 반쪽 2개는 무동작으로 예상된다(확인은 test 작성 주체).**
- **Q-N11** (계약) 소신호 metric 분해능의 Δp 를 '같은 VGS 의 전류 오차 (gm/ID)·tol_V'에서 '열마다 LUT VGS 기울기 × tol_V'로 바꿀까(B)? 결합을 최악 선형에서 RSS 로 바꿀까(C)? → **권고: B 먼저(유도 정정, 보수 결합 유지), 9회로 분해능 재측정 뒤 C 판단. 현행으로는 current_reuse 잡음 판정이 어떤 spec 값에서도 보류에 가깝다(분해능 440 µV = 값의 61 %).**
- **Q-S1** (spec) sf {gain ≥ 65 dB, noise_excess_th ≤ 2, 입력 DC 0.9 V} 는 손분석상 동시 실현 불가다. 어떻게 둘까? → **권고: (라) ② 반영 뒤 엔진이 같은 결론(front 비어 있음·실현 불가 보고)을 내는지 먼저 확인하고, 확인되면 (가) 이 회로의 noise_excess_th 를 보고만으로.**
- **Q-S2** (spec) PM 목표가 없는 3회로(sf SP-3, two_stage_ota SP-3, two_stage_ota_sf 미선언)의 PM 값은? → **권고: 세 회로 모두 값을 정해 달라 -- 미정이면 매크로가 45° 바닥으로 풀려 Cc 가 상자 하한에 붙는다(실측 3/3).**
- **Q-S3** (spec) current_reuse 잡음 spec 은? → **권고: C1 ≤ 450 µVrms(차동 출력 명시, design 41 §7.1 대역 그대로), 단 Q-N11 과 함께 결정.**

---

## 부록 A. 산출 파일 (`C:/Users/HSLEE/Documents/Todoc/fpga/wt/_step2_gaps/`)

| 파일 | 내용 |
|---|---|
| `setup_ctx.py` | 엔진 단계 A·B·search context 준비(시범 `engine_start_probe.py` 와 같은 순서) |
| `survey9.py`, `survey_report.py`, `out_survey/` | 9회로 출발 구간·매크로 망·uncovered·W 분포·θ0. `out_survey/report.txt` 요약, `out_survey_blasdefault/` BLAS 기본 비교 |
| `guard_repro.py`, `guard_counterfactual.py`, `guard_cf2.py`, `guard_gamma.py`, `out_guard/`, `out_guard_bd/` | 항목 4 재현·반사실·γ/σ 곡선 |
| `macro_exp.py`, `macro_exp2.py`, `out_macro/` | 항목 2 매크로 망 진단(Rm 누락, Rm 강제 시 손 점·k 스윕·L 스윕) |
| `polenodes.py`, `out_pole/report.txt` | 항목 1 N9 후보 노드 9회로 |
| `sysoff_scan.py`, `sysoff_scan.txt` | 항목 3 구조 술어 9회로 |
| `spice/` (`design.py` 에 L_/g_/Lcur 인자 추가 복사본, `run.sh`, `batch1.sh`, `results_L.txt`, `n_*.log/.summary.md`) | 항목 1 SPICE 분해 |
| `narrow/` (`mk.py`, `an.py`, `narrow_table.md`, `narrow_result.json`, `iv_*.txt`) | 항목 6 협폭 ngspice 측정 |
| `noise_res/noise_res_probe.py`, `noise_res/out_noise.txt`, `noise_res/out_wmin.txt` (2차) | N11 잡음 분해능 항 분해(master `9255a22`), D1 W_min bin 재현(파일럿 r2 손 θ, 우회 유무). 파일럿 probe(`_pilot_current_reuse/engine_hand_theta_probe.py`)를 재사용, 엔진 불변 |
| `sysoff_cascode_scan.py`, `sysoff_cascode_scan.txt` (2차) | N9 캐스코드 미러 술어 P1c 9회로 계수 |
| `noise_res/wmin_roundtrip.py`, `noise_res/out_wmin_roundtrip.txt` (2차) | D1 재현 2(왕복 산술 10만 점, 엔진 `bin_index` 직접 호출) |


## 부록 (2026-10-13 추가) held-out 등록에서 나온 항목 -- 사용자 "HA-1, HA-2, HB-1, HB-2 모두 권고대로 해"

### N12 -- 공급 전류 합산 레일 선언 통로 없음 (HB-1)
- 사실: `gmid_engine/metrics/dc_metrics.py`의 `supply_current_dc`는 `counted_rails`(DEC-78, 기본값 없음)가 있어야 정의된다. spec에 선언 칸이 없고 search 커널은 빈 tuple을 넘기며 `search/find_front.py`는 `not_computed`로 기록한다 -> 항상 미측정. design 40·41에 `counted_rails` 선언 위치 문장 없음(grep 0). library 9회로는 이 metric을 쓰지 않아 드러나지 않았다.
- 영향: held-out A(457.2 µA, 원문 '증폭기 전류만' p.54 -- 레일 합산으로는 바이어스 회로를 뺄 수 없음)와 B(10.4 µA, 레일 vdd·vcp·vcn)의 전류 제약을 판정에 못 씀. 둘 다 `pending_constraints`(U-75)로 둠.
- 결정 필요: (1) spec 선언 위치(예: `human.counted_rails` 넷 목록, source 필수) (2) B 레일 집합(권고: vdd+vcp+vcn, 원문 'supply current') (3) A의 '증폭기만' 정의 처리(권고 유지: 판정 밖; 대안 (나) 회로 전체 (다) 바이어스 전류 가산 (라) 소자 단위 계수 = 엔진 변경).
- 원문: A Matibag UPC 2024 https://upcommons.upc.edu/bitstreams/a99028f7-5d7f-447a-b086-c1f4effcdb1b/download (`wt/_heldout/upc_rfc.pdf` p.54, p.56 Table 17), B Wu 외 Sensors 2025 https://pmc-oa-opendata.s3.amazonaws.com/PMC12031453.1/PMC12031453.1.pdf (`wt/_heldout/erfc_sensors2025.pdf` p.12, p.15 Table 2, p.8 Fig.6).

### N13 -- held-out B CBAT θ 상자 (HB-2)
- 사실: B의 CBAT1_L·CBAT1_R·CBAT2는 `engine: true`(사용자 B-5)인데 `theta_bounds` 선언이 없어 탐색 단계에서 `theta_*_bounds_undeclared` 거부 예상. 다른 회로의 엔진 계산 보상 소자와 같은 규칙으로 정한다(규칙은 ② design에서).
- 원문: B p.8 Fig.6, p.3 본문 'coupling capacitors CBAT1 and CBAT2'.

### 결정 반영 (2026-10-14)
- Q-R1·Q-N1/2/3/4/5/8/9/11·Q-S1/S2(PM >= 70 deg)/S3·N12·N13·결정 10 전부 사용자 확정 -- 원문은 `_drafts/user_decisions.md` 2026-10-14 항목들. step 2 design 착수 조건: U17 1-b 병합, code_hash 경로 의존 수정 card.
