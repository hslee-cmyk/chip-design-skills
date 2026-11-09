# reference 검토 종합 -- G1~G6 132건을 주제로 묶음 (2026-10-07)

- 입력: 같은 폴더 `g1_gmid_lut.md`(22) · `g2_layout.md`(20) · `g3_workflow_spice.md`(24) · `g4_topology.md`(21) · `g5_incidents.md`(22) · `g6_report.md`(23) = 132건. 저장소는 고치지 않았다. 이 문서는 종합만 하고, 수치는 각 g 문서가 적은 값과 출처를 그대로 옮겼다(새로 잰 값은 없음).
- 분류: **(E)** 엔진 내부라 오케스트레이터가 정함 / **(U)** 사용자 결정 필요(회로 해석·스펙·방법론 선택·합격 정의 문구) / **(D)** 문서 정정(계획서·설계 초안·reference). 한 주제가 둘 이상이면 함께 적었다.
- 우선순위: P1 = 합격 시험(T1~T9)이나 SPICE 판정에 직접 영향, P2 = 정확도·front 품질에 영향, P3 = 보고·test·문서.
- 끝에 (U) 질문 목록 12개(이미 대기 중인 질문 포함), (E) 작업 묶음(브랜치별), (D) 정정 목록, ID→주제 색인이 있다.

---

## 1. 주제 목록 (우선순위 순)

### T01 [P1] 계획서 합격 문구가 오늘 결정과 반대 -- 노드전압을 합격 조건으로 남김
- 포함: G6-01, G3-05
- 문제: P N6.2 T4(1087행)·마일스톤 1(1078행), ROADMAP T4(102행)·마일스톤 (b)(284행), G7 8.3 '판정 2(노드)', PUD AC-1 (iii)(v)가 "노드전압이 S2 `dc`와 tol_V 안"을 합격 조건으로 둔다.
- 근거: UD 129행(8번 수정안) "SPICE 합격 = free 모드 스펙 만족 + 전 MOS 포화, 노드전압 등은 기록", P 458행(N3.6 정정본)·오라클 README 합격 정의·SF `node_compare_rule = record_only`는 이미 기록만. reference(spice-verification §1 20~22행, DRS 402행)도 노드 차는 진단 신호이고 합격 축은 스펙이다.
- 보강안: 위 문장들을 "포화만 판정, 노드전압 차는 T8 기록 + forced 경고"로 정정하고 노드 대조는 진단 표(T09의 `diagnosis`)로 옮긴다. PUD AC-1 (iii)(v)는 '해소됨(UD 8)'.
- 담당: 계획서 N6.2·ROADMAP·G7·PUD.
- 분류: **(D)**. 결정은 이미 사용자가 했다. 그대로 두면 단위 11 판정자가 스펙을 만족하는 해를 FAIL로 판정한다.

### T02 [P1] VDsat 정의가 엔진·LUT 계약·SPICE 판정에서 갈리고, 봉인 7 허용이 SPICE보다 느슨하다
- 포함: G1-03, G3-01, G5-20 (D-1과 연결: T13)
- 문제: 합격은 BSIM `@m[vdsat]`으로 판정하는데(오라클 C8, `oracle_netlist.py` 34행) 엔진 봉인 7은 `lut.vdsat`(DF-25 '6b design이 정함', 미정)을 쓰고, LUTC 8절은 "vdsat: 소비자 없음 → 만들지 않음"이다. 봉인 7은 `VDS − VDsat ≥ −tol_V`라 VDsat보다 tol_V만큼 낮은 VDS도 통과한다.
- 근거: gm/ID 역산 지표 tol_V 셀 p50 222 mV(nmos)/224 mV(pmos), max 402/445 mV(M6 4.2·LUTC 5절). 이 지표로 봉인하면 수백 mV 선형 영역 소자가 '포화'로 나간다. reference: GM §2.7·§9.3(2/(gm/ID)는 short-channel 과대, 약반전에서는 과소), sky130 §6·§7.4(op-info vdsat은 검증된 적 없음).
- 보강안: (1) LUT `VDSAT` 열(RG D6, op 값이라 비용 약 0) 채택 → MOD1 `lut/vdsat.py` = 그 열의 (VGS, VDS, VS) 보간(L 앵커 한 장)으로 오라클과 같은 양. (2) 봉인 7 기준을 오라클 `saturation_rule`과 같은 방향으로: `VDS − VDsat ≥ +tol`(엔진이 SPICE보다 보수), tol은 VDsat 열 LOO 또는 id_equivalent 셀값. (3) 열이 생기기 전에는 봉인 7을 '정의 미확정'으로 표시하고 2/(gm/ID)를 몰래 쓰지 않는다. (4) 단일 소자로 `@m[vdsat]`과 gds 꺾임 VDsat의 차를 한 번 재서 기록. (5) LUTC 8절 '소비자 없음'을 G7 소비로 정정.
- 담당: MOD1 `lut/vdsat.py`, GB7 `sizing/seal` 7, LUTC.
- 분류: **(U)** VDSAT 열 채택(Q1)과 봉인 7 부호·tol 지표(Q3), **(E)** 구현, **(D)** LUTC 8절.

### T03 [P1] 꺼진 소자가 SPICE 합격을 통과하고, 엔진 봉인에 가지 전류 부호·0 검사가 없다
- 포함: G5-01, G5-02
- 문제: 오라클 합격 조건 2는 "ID > 0(또는 `off_current_A` 초과)인 MOS가 포화"라 꺼진 소자는 검사 대상에서 빠진다. 엔진 봉인 7도 ID > 0인 MOS만 보고, KCL 차감으로 나오는 가지(폴딩 노드 I_cascode = I_src − I_in)는 부호 보장이 없다.
- 근거: known-incidents 사고 20 (c) "I(M1)=0", "마지막 검증 패스로 전류 0/음수 자동 검출". 선언 제약 0건 회로(folded·nmcnr·common_gate, R 1.3)는 바이어스가 무너져도 합격할 수 있다.
- 보강안: (1) 오라클: 엔진이 전도로 예측한 MOS가 SPICE에서 꺼지면 FAIL. 전도 문턱 = 엔진이 소자마다 LUT의 VGS=0 누설 ID로 계산해 `off_current_A[dev]`로 필수 입력(상수 아님). 꺼진 소자 거부 픽스처. (2) 엔진: `sizing/seal/item9_branch_direction.py` 신설 -- 모든 MOS `device_id`가 kind 전도 방향이고 |ID| ≥ tol_I(SCC), margin = ID/tol_I를 M6 제약 표에 연속 제약으로 노출. 픽스처: 폴딩 가지 I_in > I_src → 거부.
- 담당: `tools/spice_oracle`(C8), GB7 봉인, MOD6 제약 표.
- 분류: (1) **(U)** '전 MOS 포화' 해석 확인(Q5), (2) **(E)**.

### T04 [P1] 레이아웃 뒤 전기 재검증 -- 무엇을 보존하고, 언제 다시 평가하며, SPICE는 어떤 기하로 도나
- 포함: G2-01, G2-02, G2-03, G3-03, G3-08, G6-03 (사용자가 묶은 '레이아웃 재검증'의 전기 쪽 절반. 기하 감사는 T12)
- 문제: (a) LY1이 '총 W 보존'인데 슬라이스 fw가 바뀌면 같은 gm/ID에서 전류밀도 J가 달라져 W를 보존하면 ID가 틀어진다. (b) MOD8 재평가는 W_request가 있을 때만 돈다 -- tol_V×gm/ID 안의 실현 오차는 재평가 없이 freeze된다. (c) LY2가 diode 소자를 재평가에서 뺀다. (d) SPICE 넷리스트가 sizing W인지 MOD8 수렴 기하인지, 엔진 `predictions`가 어느 W에서 계산된 값인지 문서에 없다.
- 근거: LCS 표 A J(fw)/J(5 µm) = −28 %~+170 %(nfet). TV 4절 "W 보존 판정이 거의 아무것도 거부하지 않는다". 오라클은 실현 기하 `w=finger_w m=n_fingers`로 넷리스트를 만든다. 옛 엔진 layout W로 PM 79° → 18°(SH 3.1). diode는 ID는 맞아도 VGS(=노드전압)가 바뀌어 그 gate를 받는 미러·캐스코드 VDS 창(봉인 7)이 바뀐다. reference SE §5·§10 "모든 W·finger_w 조정 뒤 체크리스트 재실행", DRS 402행 "스냅 전/후 수치 차이와 원인 명시".
- 보강안: (1) 보존량 = (ID, gm/ID, L), 실현 W = `W_need(fw) = ID/J_slice(kind, fw, gm/ID, L, VDS, VSB)`(`ly.fw_cand` 키에서 1회 계산, 매칭 멤버는 같은 fw). (2) MOD7 결과가 나오면 W_request 유무와 관계없이 실현 기하를 S2 `layout`에 쓰고 평가 커널 1회 + 봉인 1~8 재실행(바뀐 폭 키 필드만 miss) 후 freeze. MOD8 진입 조건 = "폭 키가 사이징 스냅샷과 다름 또는 W_request 존재". (3) diode 예외 문구 = "ID 재보정 불필요, 노드전압·봉인은 재실행". (4) 합격 SPICE 기하 = MOD8 수렴 스냅샷(finger_w, nf, 행 확산 기하), sizing 직후 기하는 진단 실행(`--tag sizing`)만. (5) metric마다 3열(엔진@sizing W / 엔진@실현 W / SPICE@실현 W), DEC-72 모델 오차 파일에는 2열−3열만. 오라클 `provenance.prediction_w = "realized"`. (6) LY1 tol은 후보 순위 기준으로만 남김.
- 담당: MOD8 `convergence/loop.py`, MOD7 `layout/finger_candidates.py`, 오라클 입력 스키마, 결과 JSON.
- 분류: **(U)** LY1·LY2 문언과 합격 기하(Q4), **(E)** 구현, **(D)** ROADMAP 93·53행(철회된 'W 정본'), PUD DF-3 "엔진 W와 같은 값", REQ 3.3 `self_biased_diode` 주석, P T7 문구.

### T05 [P1] W 허용오차·tol_V 지표 -- 어떤 지표인지 미지정, 측정 정의가 과대, 보간이 정확해지면 창이 빔
- 포함: G1-06, G1-07, G3-04, G3-07, G3-22
- 문제: (a) UD·M7·REQ·ROADMAP은 "상한 = tol_V × gm/ID"라고만 하고 지표를 지정하지 않는다(LUTC 171행만 `id_equivalent`). (b) LOO는 격자 간격 2배 LUT 오차라 칸 중앙 실제 오차보다 선형 약 4배, Hermite 약 16배 크다. (c) T08(Hermite)을 채택하면 id_equivalent p50 2.6 µV → gm/ID 20에서 finger_w_crit ≈ 48 µm라 모든 실용 폭에서 하한(격자/(2·fw)) > 상한이 된다. 이때의 규칙이 없다. (d) 오라클 forced 경고 허용오차가 스칼라 하나(`ID_rel`)라 '소자별 LUT 계산 허용오차'(UD 8)를 표현 못 한다. (e) M15 2.7·TV는 아직 L 축 LOO(결정 11 이전) 정의.
- 근거: `gm_id_inverse` 지표면 gm/ID 15에서 ΔW/W 상한 ≈ 330 %, `id_equivalent`(p50 3.7 mV)면 ≈ 5.5 %(G3-04). LC 7.3 "이상치는 SPICE로 직접 재확인".
- 보강안: (1) 지표 = `id_equivalent` 셀값으로 문언 명시, `LayoutInput.tol_v`를 (metric, 셀 조회 함수)로 타입화, T11에 `gm_id_inverse` 입력 거부 경우. (2) 실효 허용오차 = max(상한, 하한), 하한이 큰 소자는 '격자 지배' 기록, W 보존 의미 = '보간 정합'(폭 슬라이스 모델 오차 미포함)으로 문서화. (3) LOO를 운영 보간과 같은 방법으로 재고 차수 p(선형 2, Hermite 4)로 2^p 환산(Richardson), 셀 표본 칸 중앙을 ngspice로 재는 검증 test. 환산을 안 하면 '보수 배수 약 2^p'를 결과 JSON에 표시. (4) 오라클 스키마 `predictions.devices[].tol{ID_rel, gm_rel}`(엔진이 셀 tol에서 계산), 스칼라 폴백 금지. (5) M15 2.7·O1·TV 머리에 'LUTC 5절 r2로 대체' 표시.
- 담당: MOD1 `tolerance.py`, MOD7 `LayoutInput`, 오라클 스키마, 계획 N3.6 문구.
- 분류: **(U)** tol_V 환산·SPICE 표본 검증(Q2), 지표 문언·빈 창 규칙(Q4), **(E)** 구현·오라클 스키마, **(D)** M15 2.7·TV.

### T06 [P1] GB5 보상 -- 계산 방법이 정의되지 않았고, 근사식으로 채우면 틀린다
- 포함: G4-01, G4-02, G4-13 (reference 정정 G1-10·G3-13·G4-15·G4-16은 D 목록)
- 문제: 계획은 "극점·영점 식을 극점 노드 목록과 MNA에서 조립하는 규칙 하나"(P 496)뿐이고 `gm_req`·보상 수동소자 값 계산법은 어디에도 없다(M6 155행은 쓰기만, RM D4 design 없음). 영점 상쇄 저항 Rz·Rm의 기준 소자를 고르는 규칙도 없다(엔진은 `nulling_reference_device`를 읽지 않음). MNA에서 극점·영점을 뽑는 블록도 없다.
- 근거: TFD 3절 실측 -- NMCNR Eq10/11 근사는 PM 60~90° 전 구간에서 GBW를 2.5~21배 틀리고(PM_target 61°에서 21.4배), PM 오차 방향도 R→∞ 극한과 유한 R에서 반대. nmcnr(GBW 816 kHz, CL 100 pF∥25 kΩ, PM 70°)·ngcc(feedforward)·파일럿 Rz1·Rz2·two_stage Rz가 직접 걸린다.
- 보강안: (1) 보상 수동소자 값을 θ 연속 성분(GB6 외층 SLSQP 변수)으로 두고 GBW·PM은 봉인 `ss` 전회로 MNA의 `ugf_ss_hz`·`pm_ss_deg`로 판정(DEC-74 위치와 같음). `gm_req`가 필요하면 "다른 θ 고정 시 MNA 제약을 만족하는 최소 gm_i"를 같은 스냅샷 MNA에서 1-D 근 찾기. feedforward 영점은 정확 MNA가 자동 포함. (2) 근사 극점·영점 식은 층 0 시작점 생성기로만, 근사 대 MNA 차를 `comp_approx_gap`으로 기록. (3) Rz 규칙: (a) 구조 규칙 R = 1/Σ_{c∈S} gm_c(S = 저항 끝 넷을 출력으로 갖고 루프 반대쪽에서 신호를 받는 CS 셀, 2단 Miller와 NMCNR Structure 4가 같은 규칙으로 나오는지 손계산 대조), (b) R도 θ 변수. S 결과는 J7 ratify. (4) `metrics/poles_zeros.py`: (G, C) 일반화 고유값, 조립 fp 키, ω 무관. (5) TFD 닫힌식·NGCC Table 4는 회로별 함수로 이식하지 않고 이상 VCCS 손계산 test 오라클로만(논문 값은 설계 입력 아님).
- 담당: MOD5 `metrics/compensation.py`·`poles_zeros.py`, D4 design(신규), MOD6 θ 스키마.
- 분류: **(U)** 방법론(Q7), **(E)** 구현, J7 ratify는 사용자.

### T07 [P1] 접합 용량(CJD·CJS)과 확산 기하가 엔진·SPICE에서 서로 다르다
- 포함: G1-02, G3-02, G2-16, G6-10, G1-12
- 문제: 엔진 MNA 스탬프에 cdb·csb가 없다(M15 3.3, '별도 열로 보고'). 오라클은 `diffusion`이 선택이고, 선언하면 `m=n_fingers`로 finger마다 독립 확산(공유 없음)을 넣어 실제 Euler 행 공유 확산 대비 접합 C를 최대 약 2배로 잡는다. 결과: 선언하면 엔진이 PM·GBW를 낙관, 안 하면 둘 다 비현실적으로 일치. 용량 자체도 W = 5 µm 한 슬라이스를 W 비례로 늘린 근사(협폭 ±9 %).
- 근거: W = 5 µm에서 Cdd 4.34 fF 대 Cgd 1.20 fF(LCS 표 M·sky130 §7.1). GM §4.2·부록 "기생 CJD를 C에 더해 3~4회 반복 수렴, CJD 때문에 약반전 쪽 최적점이 moderate로 돌아옴" -- 이 항이 없으면 전력 최소화가 약반전·큰 W로 밀린다. 크기는 미측정([추측] 표시 유지).
- 보강안: (1) MOD5 `ss_linearize`가 d–b·s–b에 cdb·csb 스탬프. 값 출처 (a) LUT CDD·CSS 열 − CGD·CGS(RG D6) 또는 (b) `core.pdk_decl`의 PDK 접합 파라미터(CJ·CJSW·MJ·MJSW·PB) + 봉인점 역바이어스 + 확산 기하. (2) 확산 기하는 한 곳에서: MOD7 `ly.row`에서 소자별 내부 공유·끝 확산 통계 `ly.diffusion[dev]` → 엔진 `ss`와 오라클 소자별 `ad/as/pd/ps` override(m 유지, LCS 표 E 때문에 nf 인스턴스 금지)에 같은 값. 레이아웃 전 첫 사이징점은 LUT 생성 규칙(ad=as=W·0.5 µm 등)을 기본으로. `ad_per_w_m`도 PDK 규칙 근거 선언(현재 '0.5·W 관례'는 근거 아님). (3) 층 0 기생 고정점·GB5 `C_out,total`·슬루 `C_k,total`이 이 필드를 읽게, MOD8에서 nf가 바뀌면 무효화. (4) 합격 실행에서 오라클 `process.diffusion` 필수(없으면 BLOCKED). (5) 폭별 용량은 RG D4(전 폭 AC, 약 12 h)와 같은 실행에서.
- 담당: MOD5 MNA, MOD1 `cap_query`, MOD7, 오라클 C3, `core/pdk_decl.py`.
- 분류: **(U)** 합격 포함 여부·기하 규칙·값 출처(Q6), 열·D4(Q1), **(E)** 스탬프·배선.

### T08 [P2] LUT 보간과 도함수 -- 저장 도함수 Hermite, gmb 열, 역산 일관성
- 포함: G1-01, G1-05, G1-15(판정: 엔진이 옳음), G1-16(보고 열 부분), G1-14(I0 보고 부분)
- 문제: MOD1은 VGS·VDS·VS 3축 다중선형 보간이고 VGS 간격 37.5 mV로 LC 권고(25 mV 이하, 저장 gm을 기울기로 쓰는 cubic-Hermite)와 다르다. op_point의 gm/ID와 역산의 gm/ID가 다른 곡면에서 나오고(LUTC 155행 스스로 인정), gm ≠ d(보간 ID)/dVGS, 격자선 C0 꺾임이 SLSQP·FD를 방해한다. gmb는 VS 0.2 V 칸 할선(계단).
- 근거(G1 실측): VGS 축 ln ID→VGS 환산 nmos p50 1.25 → 0.0026 mV, p99 3.83 → 0.042 mV, 칸 중앙 gm/ID p99 2.1 % → 0.021 %. VDS 축 GDS/ID 기울기로 p99 69.9 → 6.85 mV. Fritsch–Carlson 위반 nmos 0/126,361, pmos 0/104,125. gmb 이웃 칸 할선 상대차 p99 16.6 %(n)/20.6 %(p). 재생성 비용 0.
- 보강안: (1) `_helpers_interp` 축별 방법 표: VGS = 2점 cubic-Hermite(y = lnID, 기울기 GM/ID, gm/ID는 그 다항식 미분으로 정의), VDS = Hermite(GDS/ID), VS = 선형(GMBS 열 생기면 기울기 −GMBS/ID), lnGDS의 VGS 방향은 선형. (2) LUTC 6절 `multilinear_interp` AST 해시 고정 → '옛 함수 = 기대값 비교 참조', 동치 test는 격자점에서만. (3) 역산(`vgs_for_gm_id`, `vgs_for_current_density`)은 같은 Hermite 칸 안 bisection(상한 K_max). (4) 로드 시 칸마다 FC 검사, 위반 칸은 실패 기록. (5) gmb = GMBS 열 보간(× W/w_m), 열 전까지는 3점 2차식을 '임시'로 표시. (6) 역표는 순방향과 같은 곡면에서만(엔진 방식 유지, reference 정정은 D). (7) `curve_report` 진단 열: 강반전 log-log 기울기 d ln IDu/d ln(gm/ID)(−2~−1), 약반전 최대 gm/ID. (8) I0(kind, w_key, L, VDS) 파생 표(LC 7.4 1단계: 두 점근선 교점)와 ln IC 보고.
- 담당: MOD1 `lut/` (`_helpers_interp`, `op_point`, `gmb`, `curve_report`, `tolerance`), LUTC r2 개정.
- 분류: **(U)** Hermite 채택은 이미 대기 질문(Q2), GMBS 열(Q1), **(E)** 나머지.

### T09 [P1] SPICE 오라클 -- 측정 항목 부족, topology 동일성 미검사, 진단 분해 장치 없음
- 포함: G6-02, G3-10, G4-12, G3-06, G3-14, G4-11
- 문제: (a) `measure` enum이 `dc_gain_db, ugf_hz, pm_deg, f3db_hz, supply_current_A` 5개뿐이라 파일럿 spec의 CMRR·PSRR(`ratio_ss_db >= 60` 두 뷰)·slew·settling은 영구 INCOMPLETE → T5 "선언된 성능 제약 전부" 불가. 정착 목표(t_lln 30 ns·t_settle 40 ns, UD 3)는 채택됐지만 판정 장치가 없다(SF F11). (b) 오라클은 엔진·어댑터가 만든 JSON만 보고 topology JSON과 연결을 대조하지 않는다(OR C1~C14에 없음). (c) 단독 소자(LUT↔SPICE) 모드가 없어 K3 완료 조건을 판정할 장치가 없다(`iso` grep 0건). (d) free FAIL 원인 분류(경계조건/구조/엔진 DC 비정합)가 수동이다(Z1 절차 없음).
- 근거: DRS 402행 "gain/GBW/slew-rate/matching/전류 등이 원 스펙 만족". TBD 0.5단계·NMCNR 잘못된 조립 사고(노드 하나 오연결 → '노치' 오결론). spice-verification §1·§2 분해 절차.
- 보강안: (1) measure 추가: `cmrr_db`·`psrr_db`(MOD5 레지스트리 뷰 num/den과 같은 여기 정의, .ac 2회 -- PM과 같은 'U-48식 같은 정의'), `slew_rate_v_per_s`·`settle_s`(.tran, 선언 β 루프, 오차 대역은 spec 값), 필요 시 `swing_v`. 엔진 레지스트리 항목마다 `oracle_measure` 필드 → spec 로드 시 `spice_unverifiable[]`를 실행 전에 출력. (2) C15: `--topology` 필수, 오라클 netlist를 다시 파싱해 (이름, 종류, 단자 넷 튜플) 집합을 topology(netlist + passive + 이상원)와 비교, 테스트벤치 원소는 접두사로 제외, 다르면 BLOCKED + 차이 목록. 결과 JSON `connectivity_fp` 대조. 오라클은 엔진 import 없이 최소 파서(C1 유지). (3) `--bias iso`: 소자별 단독 인스턴스를 엔진 예측 VGS·VDS·VSB에 고정, ID·gm·gds 비교, 허용 = 셀 `id_equivalent × gm/ID`. (4) `oracle_compare.diagnosis`: forced KCL 잔차 대 Σtol_I로 '경계조건 쪽'/'엔진 DC 비정합' 분류, 게이트 공유 넷별 등가 ΔVGS = ΔID/gm 최대 차. (5) Z1 도구: `--omit`/`--short`(제거법), `--ideal`(엔진 `ss`의 VCCS+gds+C 등가, 계획된 MNA 오라클 재사용), `pm_crosscheck_deg`(폐루프 step 오버슈트 또는 peaking 역산, 기록만). 결과는 (netlist sha256, 모델 fp, 명령) 디스크 캐시.
- 담당: `tools/spice_oracle`(README 계약 C15~, `oracle_netlist.py`, `oracle_compare.py`), MOD5 레지스트리, spec 로더.
- 분류: **(U)** 어느 제약을 합격 판정에 넣을지(Q5), **(E)** 측정·C15·iso·diagnosis·Z1 도구.

### T10 [P1] GB4 achievability 상한이 상한이 아닐 수 있다 -- 거짓 INFEASIBLE
- 포함: G1-04, G1-08, G3-12
- 문제: M15 3.5 문구("소자별 gm/gds 최대를 넣은 상한")대로 구현하면 부하 소자의 gds/ID가 최소가 되지 않아 계산값이 실제 달성 gain보다 작아진다(P N3.7 477행 '결합 최댓값'과도 충돌). 블록 국소 모델이 블록 노드의 저컨덕턴스 소자를 빠뜨려도 상한이 낮아진다. 극값이 LUT 격자 끝(L 4 µm 앵커 등)에서 나오면 INFEASIBLE이 물리 한계가 아니라 LUT 범위 한계다.
- 근거: GM §13.7 "gm/gds 최대화 ≠ ro 최대화(M202: ro 129,938 Ω 대 실제 최대 250,266 Ω)". spice-verification §3 국소 근사의 49 dB·부호 반대 오차(M10/M19 누락). RG K3: pfet 8→20 µm에서 고유이득 미포화.
- 보강안: (1) 상한 = 완화 문제 최댓값: 분자(gm) 소자는 격자 가능역 최대 gm/ID, 분모(gds) 소자는 최소 gds/ID를 독립으로(같은 소자가 양쪽이면 각 항에 따로) -- 기여 위치는 국소 모델 스탬프에서 유도, role 라벨 미사용. 극값을 낸 격자 조건을 소자마다 행 표에 기록. (2) 국소 모델 소자 집합 = 블록 노드에 단자가 닿는 S1 소자 전부(이름·역할로 거르지 않음)로 계약 명시. (3) test `test_gb4_bound_dominates_mna`: 9회로 탐색 중 봉인 통과 스냅샷마다 전회로 MNA 블록 이득 ≤ 상한, 임의 격자 표본(`dof_rank_sample_count`) 국소 gain ≤ 상한. (4) 행마다 '격자 끝 극값' 플래그 → 그 블록 때문이면 `INFEASIBLE_TARGET` 대신 'LUT 범위 한계 가능'(다음 앵커 후보 = RG K1) 사유로 정지(숨기지 않음, WP-01), LC 7.7 '레버 하나만 확장해 재확인' 문구.
- 담당: MOD5 `achievability.py`, M15 3.5 문구.
- 분류: **(E)**, **(D)** M15 3.5. L 상한(8/20 µm)은 Q1.

### T11 [P2] matching 그룹 유도 -- 차동쌍 오판, 캐스코드 대칭쌍 누락, 분류·status 정책 없음
- 포함: G5-03, G4-03, G5-04, G2-07, G6-06, G4-04, G4-20, G4-05, G6-11, G2-12 (사용자가 묶은 'matching 유도' 주제 + 관련)
- 문제: (a) 차동쌍 규칙(같은 비레일 source·다른 gate 정확히 2개)이 파일럿 두 입력쌍을 못 잡는다 -- Vx에 M58, Vy에 M63(바이어스 소자)이 얹혀 3소자 → review_needed(G5 실측). (b) 같은 gate·다른 source인 캐스코드 대칭쌍(파일럿 M2a/M2b·M3a/M3b, folded M5/M6·M7/M8, nmcnr M106/M107, sf M5/M10·M7/M12·M13/M15 등)이 어떤 matching 그룹에도 안 든다 -- AGI §6.3이 이미 찾아 고친 공백의 재발. (c) gs_groups 미러 규칙은 (c)형 바이어스 분배(작은 diode → 다른 블록 큰 소비 소자)와 (d)형 피드백 공유 gate까지 '진짜 미러'로 넣는다. (d) diode 2개 쌍이 차동쌍으로 잡힐 수 있다[추측: 9회로 발동 미측정]. (e) status(derived/proposed/review_needed)를 레이아웃이 어떻게 쓰는지 정책 없음. (f) 레이아웃 규칙: 캐스코드쌍은 공유 hub가 없어 interdigitation이 그래프상 불가 → '둘 중 하나'가 사실상 CC뿐인데 규칙 문장이 이를 담지 않고, 미러는 reference상 interdigitation 필수. (g) 완화된 차동쌍은 DRS 기준으로 합격 아님. (h) 매칭 멤버의 L 동일성을 레이아웃이 확인하지 않는다.
- 근거: known-incidents 사고 8('물리적 같은 노드 ≠ 기능 그룹'), consistency-map 14·16·39차(branch_symmetric 3c 필수, swap 분배 dx 0.00/dy 0.20), FSM 134행, DRS §1.5-4 후보 5패턴, AGI §6.3 실측(M2a/M2b·M3a/M3b 재현, M57/M58 비유입).
- 보강안: (1) 차동쌍: 같은 (kind, 비레일 source) 멤버 중 gate가 모든 뷰 교류접지이거나 dc_role이 bias_current_source/diode 구동인 소자를 먼저 제외, 남은 멤버 중 gate가 신호 넷(입력 포트 또는 `graph.symmetry` 대응)인 소자가 정확히 2이면 derived, 두 멤버 `is_diode == False`. U3(dc_role)·U5(뷰)를 rel_matching보다 먼저 계산(DU 4.0 순서 조정). 의사차동(레일 source + 대칭 입력 gate)은 9회로 발동 0이면 review_needed 기록만(DEC-76). (2) stack 전파 규칙(role `branch_symmetric`/`cascode_pair`): seed = 확정 matching 쌍, 채널 stack 엣지(같은 kind, X.s == Y.d 비레일)를 따라 바로 위 같은 kind·같은 gate 쌍을 고정점까지 등록, 증거 `{base_pair, shared_gate}`. (3) 레코드 `role ∈ {diff_pair, mirror, branch_symmetric, bias_distribution, feedback_shared}` + `evidence{rule, nets}` + status. 레이아웃에는 diff_pair·mirror·branch_symmetric의 derived·ratified만, 나머지는 `matching_dispositions[]`에 근거와 함께. (4) MOD7 hub 없는 쌍 배치: `layout/pattern_branch_symmetric.py`(두 행 swap-대칭 분배, dx/dy residual, 손계산 test), 복사 `mirror_symmetric_trail` 재사용. (5) `pattern_select`가 그룹 멤버 L 동일성 확인 → 다르면 `matching_L_mismatch` 기록(L 통일은 LR2 소관). (6) 완화 차동쌍은 결과 맨 앞 review_needed + dx·dy(pitch 단위) + 근본 원인. (7) metamorphic test: tail에 바이어스 소자 1개 추가해도 diff_pair 유지, T2 telescopic 캐스코드쌍 2개, seed 없는 같은 gate 쌍(M57/M58형) 0개.
- 담당: MOD3 `graph/rel_matching.py`·`matching_groups.py`, MOD7 `pattern_select.py`·새 패턴 파일, LY4·LY5.
- 분류: **(U)** 회로 해석(캐스코드쌍 matching 인정, 분류 규칙, 레이아웃 규칙 보강, 완화 표시 -- Q8) + 9회로 결과 J-U4 ratify, **(E)** 유도 알고리즘·패턴·test.

### T12 [P2] 레이아웃 최종 matching 감사·행 접기 뒤 재판정 없음
- 포함: G6-04, G6-05, G5-05, G4-06, G2-13, G2-08 (사용자가 묶은 '레이아웃 재검증·matching 감사'의 기하 쪽)
- 문제: MOD7 순서가 패턴 → finger → Euler → box(FAIL이면 `apply_explicit_row_split` 자동) → floorplan이고, 접기·finger_w별 행 분할·crossover·floorplan 뒤 Euler·matching을 다시 재지 않는다. `apply_explicit_row_split`은 원본 docstring상 "매칭 파트너가 없는 단독 소자용, 호출자가 명시 선언할 때만"이고 소자마다 `divmod`로 나눠 interdigitation/CC 순서를 보존하지 않는다. `check_mirror_symmetry`·`audit_row_split` 대체물이 없고 `LayoutResult`에서 dx·dy가 빠졌다. Euler 막힘 때 W를 보존하는 패리티 전환 없이 곧바로 crossover로 간다.
- 근거: DRS PRE-FLIGHT 2·13·14·19·20, §1.7 3.5(종류별 필수 게이트), consistency-map 7·8·12·34차, SE §3 설계 레버 (a) "finger 수 조정으로 parity 전환 우선".
- 보강안: (1) `layout/match_audit.py`(진입점 1, 필드 `ly.match[gid]`, 입력 = 최종 `ly.row` 지문 + 그룹 레코드): 3b(복사 `count_isolated_pairs`), 3c(복사 `common_centroid_residual`로 dx·dy), 대칭(`check_mirror_symmetry` 복사 + 해시 대조), role별 필수 게이트, 결과 JSON에 3b·3c·dx·dy·ok·`axis_symmetric`. 3c 허용은 멤버 finger 수 홀짝 양자화에서 유도하고 리터럴 0.5와 같음을 test로 고정. (2) 행 접기는 matching 그룹이 없는 행에만, matching 행은 패턴 함수로 n_rows=k 재구성. 접거나 재구성한 뒤 `row_euler` + `match_audit` 재실행, matching이 나빠지면 거부, 채택은 전체 floorplan 결과로(PRE-FLIGHT 17). 접는 지점은 `find_diffusion_safe_split_points` 안전 지점만. MOD8 매 반복과 `run_layout` 끝에서 실행. (3) `row_euler`가 막힌 행이면 `ly.fw_cand` 후보에서 홀수 차수 노드를 줄이는 (fw, nf) 조합을 공식으로 먼저 찾고 없을 때만 crossover(탐색 상한 = 행 소자 수 × 후보 수). (4) test: 매칭 2멤버 행 + box FAIL 픽스처에서 접은 결과 3c가 나빠지면 미채택.
- 담당: MOD7 `layout/rows.py`·`box_shape.py`·`row_euler.py`·새 `match_audit.py`, 복사 목록·해시 manifest.
- 분류: **(E)**. '자동 접기 범위'(비매칭 행만 자동, 매칭 행은 재구성)는 DRS·SD docstring의 '설계자 판단'과 DM7 자동 적용이 달라 **(U)** 확인 1회(Q8).

### T13 [P1 대기] 쓰기 소자 독립 좌표 D-1과 포화 봉인 지표
- 포함: G1-14, G5-20(D-1 부분)
- 문제: D-1 (가) gm_id 유지면 봉인 2·7 허용이 gm_id_inverse 지표(p50 222 mV)라 무력하고, 정점 근처 조건수가 발산한다(M6 4.2).
- 근거: reference가 (라)를 지지한다 -- GM §2.3·§4.3(Jespers qF), LC 7.3·7.4(Murmann IC 축)는 전류밀도·반전 지수를 독립 변수로 쓴다. 단서: IDu = IC × I0이고 I0는 짧은 L에서 이동도 열화로 L에 의존하므로 "ℓ이 바뀌어도 같은 r이면 반전 수준 유지"는 긴 L에서만 근사[추측: 크기 미측정].
- 보강안: (라) 채택 + I0 파생 표와 ln IC 보고(T08 (8)), 봉인 7 tol 분리(T02).
- 담당: MOD6 θ 스키마, MOD1 `vgs_for_current_density`, DEC-04·DEC-70 문언.
- 분류: **(U)** 이미 대기 중인 D-1(Q3).

### T14 [P2] DC 역할 유도와 종속 소자 선택이 일반적이지 않다
- 포함: G4-14, G5-07
- 문제: (a) 바이어스 판정이 'diode 멤버 gs 묶음' 또는 'gate가 모든 뷰 교류접지 + source 레일'뿐이라, diode 없이 미러 출력만이 구동하는 bias 넷의 gate를 받는 단독 전류원은 `review_needed`도 아닌 `signal`로 조용히 떨어진다(파일럿 Vbias4는 diode M66이 있어 지금은 발동 0, 9회로 전수 미확인). (b) 종속 gm_id 소자 선택이 diode 없으면 '이름 정렬 첫 멤버'(G7 U1·U4, DU J12-f, BFS 같은 단계 이름 정렬)라 θ 매개화·bounds·SLSQP 경로가 이름에 의존할 수 있다. DU 5.3 metamorphic은 개수만 비교해 이를 못 잡는다.
- 근거: AGI §11.2 "드라이버 게이트 클래스를 재귀(고정점)로 확인해 BIAS 전파". known-incidents 사고 21 "신호경로 순서가 방향을 정하는 진짜 기준".
- 보강안: (1) `dc_roles.py` 규칙 (3′): 뷰 생성 전 1회 'DC 바이어스 넷' 고정점(입력 포트 전부 여기 도달성 밖 + 채널 구동 소자가 전부 diode_reference/bias_current_source) → gate가 그 넷이고 source가 레일이면 bias_current_source, 고정점 밖 미분류는 review_needed. '미러 사슬 bias 넷(diode 없음)' 픽스처, 9회로 수치(28/46/68) 재측정, 바뀌면 J-U3. (2) 종속 선택 우선순위: diode > GB5가 gm을 요구하는 소자·뒤 stage 소자는 독립 유지 > 대칭 궤도 대표 > 이름. metamorphic에 '이름 전단사 후 front 정규화 해시(이름 사상 적용) 동일' 추가.
- 담당: MOD3 `dc_roles.py`, GB7 `writer_plan`, MOD6.
- 분류: (1) **(E)** + 결과 J-U3 ratify, (2) **(U)** G7 U1·U4가 사용자 승인 항목이라 기본안 교체 확인(Q10).

### T15 [P2] MOD2 입력 게이트 -- 추출 오류를 조용히 흡수
- 포함: G4-08, G4-09, G5-10, G4-19, G5-22, G4-21
- 문제: (a) gate 전용 넷이 선언 없이 외부 바이어스(교류접지)로 자동 분류된다 -- 6회로에 미선언 gate 전용 넷: common_gate {VNBias1, VNBias2, VPBias1}, folded {bias3}, ngcc {VBP, VBN}, nmcnr {VB1~VB5}, pushpull {VPB1, VNB1}, two_stage·two_stage_sf {bias}(G4 실측). 오독 넷(사고 5형)도 그대로 사이징된다. (b) 넷 이름 대소문자 충돌 검사가 원소 이름에만 있어 엔진은 받고 오라클 C4는 막는다. (c) 저작 단계 검토 보고(넷 기준·소자 기준 표, 대칭 미해결 목록)가 새 엔진에 없다. (d) 원문 대비 소자 수 대조 장치가 없다. (e) bulk 기본 규칙이 follower 소자(two_stage_sf M8, pushpull M1~M4, sf M18~M22)에 조용히 적용된다.
- 근거: TEC 사고 4·5, TEC 85~87·102·104행, consistency-map 24차·47차(가상 소자 9개·Vop측 12개 누락, 41→51), AGI §11.1(대소문자 불일치 = 조용한 오분류).
- 보강안: (1) topology에 `bias_inputs`(또는 `ports` role) 선언 + MOD2 게이트: 미선언 gate 전용 넷 `SchemaRejectedError(gate_only_undeclared)`, 선언했는데 gate 전용이 아니면 거부. 비차단 `authoring_anomalies`(dangling 넷, 대칭 미해결). 오라클 C6(`bias_voltages`)과 입력 맞춤. (2) `net_case_collision`: MOS d/g/s/bulk, 2단자 terminals, `supply_nets`, `ports` 전체 casefold, 자동 통일 없이 거부, 9회로 오거부 0 test. (3) MOD9 `report/topology_review.py`: 넷·소자 표 + 이상 보고 + 대칭 미해결을 Markdown·stdout으로, 정정 대기열 일괄 반영 때마다 출력. (4) 선택 키 `source_manifest{figure, device_count, passive_count}` + 로더 대조. (5) S1D 8.2 확인 요청을 소자별 질문으로 좁힘.
- 담당: MOD2 `authoring/`, MOD9, topology 파일(사용자).
- 분류: **(E)** 게이트·검사·보고, **(U)** 6회로 선언 추가·manifest 키·body 답(Q9).

### T16 [P2] 레이아웃 면적 판정 축 -- box 비 선언, dummy·tap, 복사 리터럴, 박스 개선 수단
- 포함: G2-10, G6-13, G2-05, G2-09, G5-12, G2-14, G6-14, G6-16, G2-20
- 문제: (a) DM7은 box 허용 비를 spec 필수 선언으로 요구(없으면 로드 거부)하는데 spec 형식에 그 필드가 없다 -- 그대로 구현하면 9회로 전부 거부. reference 1.5·2.0·60 %·0.5는 상수 금지와 충돌. (b) 박스 개선 수단이 행 접기뿐이고 reference의 주 수단인 행별 finger_w 재선택(Case A)이 없다. (c) 판정 축 면적(front 비지배 재필터, 동률 폭 격자 한 칸)에 well·tap·guard ring·행 끝 dummy가 빠져 행 수가 다른 front 점 순위를 뒤집을 수 있다[추측: 크기 미측정]. (d) 복사한 floorplan 리터럴(0.3, 0.5, 2.0, 2.2, 40 / 0.6, 100)은 '탐색 폭'으로 예외 처리됐지만 12번 (나) 결정 뒤에는 판정 결과를 바꿀 수 있다. `_common_centroid_residual`의 0.5는 판정 기준이다. (e) floorplan 필드가 bbox 면적 하나로 줄었고 후보·탈락 사유·box FAIL 필요 행 수 기록이 없다. (f) 비차동 그룹 정렬 키 1순위가 method라 7멤버 미러가 7행 회전을 고르게 된다 -- 사용자 문언 "box·면적·residual"과 순서가 다르다.
- 근거: SE §8.1·§8.2·§8.5, §10 1240행(well/substrate 공간 확보), DRS §1 표 4·8, PRE-FLIGHT 23, known-incidents 사고 23·24, DSF grep(box 필드 0건).
- 보강안: (1) box 판정을 'floorplan 외곽 면적 + packing 밀도 보고'로, 박스 개선 목적함수 = 판정 축 면적, 행 폭 비는 기록만(spec 항목 불필요). 하드 게이트로 남기려면 DSF `layout_criteria{box_row_width_ratio_max:{value, source}}`. (2) 행별 허용 후보(`ly.fw_cand`) 보관 → 목표 행 폭 T를 후보 폭 합집합에서 차례로, 행마다 T에 가장 가까운 (fw, nf, 접기 수), Case B(공통 fw)는 같은 루프의 특수 경우. (3) `core/pdk_decl.py`에 tap 폭·nwell 간격·nwell 여유·poly 끝 dummy 폭을 규칙 번호와 함께 선언, `floorplan.py`가 행 끝 dummy 2개 + 그룹 경계 tap + body 다른 그룹 사이 well 간격, front 표 '포함 항목' 열. (4) 넘길 수 있는 리터럴은 유도값으로, 못 넘기는 본문 리터럴은 `test_floorplan_literal_sensitivity.py`로 ±한 격자 단계 A_L 변화 ≤ ΔA_tie 기록, 넘으면 본문 수정 승인. 3c 허용은 T12 (1)처럼 유도. (5) `ly.floorplan = {bbox_w, bbox_h, A_L, aspect_ratio, packing_density, placements, groups, row_split_candidates[...]}`, `ly.group[gid].candidates[...]`, `ly.box.attempts`(접기 수별 면적)·`fail_analysis{rows_needed_for_ratio}`. (6) 비차동 그룹 정렬 키 = (crossover_count, 판정 축 면적 기여, residual), method는 기록.
- 담당: MOD7 `box_shape.py`·`rows.py`·`floorplan.py`·`pattern_select.py`, `core/pdk_decl.py`, DSF.
- 분류: **(U)** box 하드 게이트 여부·dummy/tap 포함·리터럴 본문 수정(Q8), **(E)** 나머지.

### T17 [P2] 행 그룹 유도·hub 병합·floorplan 입력 의미
- 포함: G5-06, G2-06, G4-07, G6-17, G6-07, G5-13
- 문제: (a) 행 그룹이 "MOD3 기둥 + matching 그룹에서 유도"로만 적혀 있고, 기둥(KVL 헤드룸 축, 파일럿 41개, 소자 중복)에서 서로소 행을 만드는 규칙이 없다 -- 파일럿 Vx 기둥에서 M58이 신호 소자와 한 행이 되면 사고 8 재현. (b) stage를 넘는 hub 병합 탐지(`find_hub_merge_candidates`)가 복사 목록에도 '복사하지 않는 함수' 목록에도 없다(조용한 누락). (c) floorplan 호출이 `spine_groups` = (kind, body), `mirror_pairs` = matching 그룹으로 의미를 바꿔 넘긴다 -- 원래 spine = 기능 블록, sub_kinds = 폴러리티 후보, mirror_pairs = 좌우 대칭 행 쌍. `net_weights`는 안 넘긴다. A_L이 여기서 나온다.
- 근거: known-incidents 사고 8·15, SE §4·§4.1·§10, FSM 68·155행, DRS §1.7-1·PRE-FLIGHT 15·16·17, consistency-map 8·9차.
- 보강안: (1) `graph/row_groups.py`(MOD3): base = matching 그룹(T11 이후), 같은 kind·body에서 base 멤버와 내부 2단자 넷(분기 노드 아님)으로 직렬 연결된 소자만 재귀 편입, 분기 노드(차수 ≥ 3)를 source로 공유하는 형제는 제외, 나머지는 단독. 기둥은 헤드룸 축으로만. test: 파일럿 M58·M63이 입력쌍 행 그룹에 없음, 형제 소비자 추가 시 기존 그룹 불변. (2) `layout/hub_merge.py`: (kind, body, hub 넷, hub 역할 source/drain)으로 후보, 역할 반대 제외, leaf ≥ 3 패리티 공식(`check_multi_leaf_hub_parity` 복사·해시), 레일 공유만이면 `false_positive_shared_supply_rail`, 병합안·비병합안을 판정 축 면적으로 비교해 `merge_decisions[{devices, net, merged, reason}]` 기록. (3) `floorplan.py`: spine_groups = MOD3 블록(stages·composite_blocks·루프)별 행 묶음, sub_kinds = (kind, body) 후보, mirror_pairs = 차동 두 가지를 따라 대응되는 좌우 행 쌍, net_weights = 그룹 사이 공유 gate·drain 넷 수, width_tolerance는 복사 기본값. 두 블록 픽스처에서 블록 행이 섞이지 않는 test, 9회로 전후 A_L 기록.
- 담당: MOD3(row_groups), MOD7(`rows.py`·`hub_merge.py`·`floorplan.py`).
- 분류: **(E)**. 병합 거부 정책(노이즈 결합 우려로 거부할지)만 **(U)**(Q8, 기본안 기록만).

### T18 [P2] W_request 경로가 끝까지 정의되지 않았다
- 포함: G2-04, G2-11
- 문제: (a) `W_adjustable=false`(= 활성 제약 소자)이면 차동쌍이 LY5 (ii)(W_request)를 시도도 않고 완화로 간다 -- 사용자 결정 "둘 다 불가능할 때만"과 어긋나고, `W_adjustable`의 계산 주체·규칙도 없다. (b) finger_quantization W_request가 거부되면 갈 곳이 없고 `W_new` 계산 규칙도 없다.
- 근거: SE §5 FAIL 사다리 (i) 다른 branch (ii) gm/ID 재선택 (iii) diffusion break.
- 보강안: (1) `W_adjustable`을 계약에서 빼고 모든 W_request를 MOD8 재평가가 판정(꼭 두면 spec·ratify로 W 고정된 소자만 false, MOD4가 유도). T5 픽스처에 '활성 제약 차동쌍 + MOD8 수용 → relaxed=false'. (2) 사다리: W_new = 실현 격자 {nf·fw}(T04면 W_need(fw))에서 W 위·아래 두 값 요청 → 둘 다 거부면 MOD8이 그 소자를 '실현 격자 값 집합 제약'으로 θ 재탐색 → 실패면 `removed{reason: layout_unrealizable, device}`. 반복 상한 K_max.
- 담당: MOD7·MOD8, NR 288행·M7 159행 문구.
- 분류: **(E)**, **(D)** NR·M7 문구.

### T19 [P2] 준정적(NQS) 검사 부재
- 포함: G1-09, G3-09, G4-10
- 문제: P·M15·ORC·초안 어디에도 f_nqs/fT 검사가 없고(grep 0), MNA와 ngspice BSIM4(NQS 기본 꺼짐)는 둘 다 준정적이라 서로 못 잡는다.
- 근거: GM §2.6·§4.5, FSM 37행 `check_quasi_static`. sky130 §8 IGS 예제는 '4행 모두 True'라 적었지만 재계산하면 소자 f_T 773 MHz·23.5 MHz인 3·4행은 False, NGCC 1단 PMOS f_T 1.69 MHz < GB 10 MHz(G3 실측).
- 보강안: MOD5 `metrics/nqs.py`(변형군): 신호 경로 소자마다 f_T,dev = gm/(2π·cgg)(봉인 `ss`, 추가 조회 0), `nqs_ratio` = ugf_ss_hz / min f_T 기록. 0.1은 reference 경험 상수(WP-03)라 박지 않음 -- spec 선언(출처 필수)일 때만 제약, 아니면 보고만. 대안: SPICE 대조에서 '비율 대비 모델 오차'를 실측해 유도.
- 담당: MOD5 레지스트리.
- 분류: **(E)** 보고 metric, **(U)** 제약화 여부·임계 출처(Q11), reference 표 정정은 D.

### T20 [P3] 미스매치 -- 면적 최소화에 반대 압력이 없다
- 포함: G1-11, G3-11
- 문제: `mismatch_sigma_mv <= 5.0`은 파일럿에만 있고 `pending_spice`(판정 안 함). 목적 축이 전력·면적이라 front 끝점이 미러·차동쌍 W·L을 최소로 밀어도 막을 장치가 없다(GM §13.5 옛 엔진 사고와 같은 형태). 합격(공칭 SPICE)에는 영향 없음.
- 근거: GM §7.1·§6.6·§13.5, LC 8.2 PDK mismatch 상수. reference 오류: SKILL 169행이 차동쌍을 미러와 같은 줄(moderate~strong)에 둠 -- 입력환산 오프셋은 gm/ID가 클수록 줄어든다(G3-11).
- 보강안: MOD5 보고용 `mismatch_sigma_v`: S1 유도 매칭 그룹마다 Pelgrom 두 항(A_VT, A_β), 계수는 PDK mismatch 파일(`__mismatch.corner.spice` slope 파라미터), 봉인점 W·L·gm/ID로 입력 환산(DEC-23), 모든 회로·front 점 기록. SPICE Monte Carlo 소수 표본으로 1회 대조(U-17 '7a 재도출'). 제약은 spec 선언 시만.
- 담당: MOD5.
- 분류: **(E)** 보고 metric, **(U)** 제약값(U-17, Q11), SKILL 169행 정정은 D.

### T21 [P3] 사고 대응 test·계약 공백
- 포함: G5-08, G5-09, G5-11, G5-17, G5-21, G3-21, G2-15, G6-21
- 문제와 보강안(모두 엔진 내부):
  - G5-08 IC6(사고 19 underdetermined)이 GB4 축소로 사라짐 → `tests/contracts/test_ic6_dof.py`: 이름 없는 4소자 기둥(미지수 2/등식 1)에서 DOF 표가 W4 y 정확히 1개, 과결정 픽스처는 종속 gm_id 또는 `StructureUnresolvedError`.
  - G5-09 IC5(사고 11 게이트 사각) → `test_gate_blind_spots.py`: `check_*`·`seal/item*`·`*_verdict`·`audit_*` docstring에 '검사하지 않는 것:'·`영역:` 필수, 복사 함수는 `_copy_manifest.py`에 같은 정보.
  - G5-11 원소 값 완전성(사고 4) → S0에서 원소마다 값 출처 {declared, spec, GB5 rule, θ 변수} 정확히 하나, 없으면 `element_value_unresolved`로 탐색 전 정지 + `test_result_values_every_element.py`(9회로 null 0).
  - G5-17 test 픽스처가 실제 library 이름 사용(사고 6) → `conftest.py` `library_device(circuit, name, expect_kind, expect_pins)`로 연결·역할 가정을 먼저 assert, 수식 검증과 역할 검증 분리.
  - G5-21 대칭 파트너 유도 결과 동일성(사고 9·18) → `test_symmetric_partner_consistency.py`(dc_role·셀·stage·matching role·row 그룹 크기, 다르면 review_needed 기록 확인, 값 동일은 요구 안 함).
  - G3-21 옛 이득 이중 곱 버그 재발 방지 → `test_gain.py` 단일 CS + 이상 전류원 부하 `gain_ss_db` = 20·log10(gm_gds).
  - G2-15·G6-21 출판 정답을 외부 오라클로 → SE §6.1 Maloberti 4행 시퀀스·홀수 노드, §7 2단 OTA 3 stack, DRS PRE-FLIGHT 26의 12개 행 시퀀스(test 작성자가 원문에서 독립 전사, 함수 오라클로만).
- 담당: tests/, MOD0 S0, GB7.
- 분류: **(E)**.

### T22 [P3] 보고(MOD9)·결과 기록 -- 설계 문서가 없다
- 포함: G6-08, G6-09, G6-12, G6-15, G6-18, G6-19, G6-20, G3-23, G3-24, G5-18, G1-19
- 문제: MOD9 design 문서가 없어 DRS 8섹션·§7 레이아웃 가이드·회로도 좌표 출처·시각 검증·커버리지 입력 독립성이 어디에도 배정되지 않았다. 참고 구현 `design_report.py`는 섹션을 조용히 생략하고 `renderSchematic`을 표로 대체해 규격 위반. 최적성 증거(KKT 잔차·활성 제약·시작점 수)·front 선택 근거 필드·spec 3층(선언/파생/엔진 계산) 분리도 없다. 슬루율 미선언 회로는 슬루 보고가 없다. metric 이름 `supply_current_dc`(DSF) 대 `supply_current_dc_a`(DM6) 불일치.
- 보강안: `design_mod9_report.md` 신설 -- (1) 결과 JSON 8섹션 키 필수, 못 낸 섹션은 `{"status": "not_run", "reason"}`. (2) 섹션 ↔ graph 필드 대응표(§3 = S2 dc·ss, §5 = `ly.row`, §6 = T04 3열 표 + oracle compare, §8 = `ly.floorplan`). (3) HTML = 결과 JSON의 순수 함수, JSON을 `<script id="REPORT">`에 바이트 그대로(sha256 동일 test). (4) `report_completeness` 게이트: 4중 집합(S1 MOS = `device_op` 키 = `ly.row` = floorplan 블록), 수동소자 = 결과 JSON = `layout_guide.passives`, MOD3 블록별 소자 수 표(사용자 대조용). (5) `report/layout_guide.py`(critical_nodes는 최종 해 1회 MNA 감도 dPM/dC, power_branches·sensitive_nets·compensation·placement·not_verified, EM 숫자 생성 금지). (6) 회로도 좌표: S1 자동 배치(x = 기둥 순서, y = 적층 순서, 직교 배선) 또는 topology 선택 필드. (7) `legacy/report_template.html` JS 렌더러는 본문 복사 + 해시. (8) headless 렌더 DOM 검사(SVG 존재·`<pre>` 0·라벨 겹침 0) + 스크린샷 확인 1회. (9) `optimality{slsqp_status, kkt_residual, active_constraints, n_starts, start_spread, lb_rounds}`, `runs.front[].selection{rule, budget_ref, reason}`, `spec{declared(sha256+원문), derived[...], engine_computed[...]}`, metric 이름은 레지스트리 정본 하나. (10) 극점 노드마다 방향별 I_max/C_k,total 슬루 보고(`ls` 필드 재사용).
- 담당: MOD9(신규 design), MOD6 결과 기록, spec 로더.
- 분류: **(U)** HTML 8섹션·가이드를 DEC-85 '엔진 완성' 범위에 넣을지, 회로도 좌표 출처, 시각 검증 절차(Q11), **(E)** 스키마·게이트·필드, **(D)** DSF·DM6 metric 이름, P 513행(D-6).

### T23 [P3] 범위 밖으로 확정된 것 -- PVT·잡음·왜곡
- 포함: G1-21, G3-15, G3-16, G1-20
- 문제: LUT·합격은 TT 27 °C 하나(P 164행), 잡음은 7b 이후(P 163행)인데 SKILL DoD에는 잡음·왜곡이 있고 reference는 PVT 코너 흔들림을 경고한다.
- 보강안: (1) 결과 JSON·보고서에 '합격 = TT 27 °C 한 조건', '잡음·왜곡 미검증' 명시. (2) spec 로더가 잡음·왜곡 metric 선언을 만나면 `unsupported_metric`으로 정지(조용히 무시 금지). (3) 오라클 옵션으로 같은 넷리스트를 ss/ff·온도 끝점에서 '기록만'(모델 include `{corner}`만 교체). (4) 잡음 metric을 설계할 때 γ 식이 아니라 LUT 잡음 열(두 주파수, RG D5)을 보간한다고 계획 잡음 항목에 한 줄.
- 담당: spec 로더, 오라클, 계획 잡음 항목.
- 분류: **(U)** 9회로 잡음 스펙 유무·코너 기록 옵션(Q11), **(E)** 정지 규칙·문구, **(D)** 계획 한 줄.

### T24 [P3] 사용자 승인 범위 -- 구현 뒤 공유 계산 블록 변경
- 포함: G5-14
- 문제: 확정 사항 6 "사용자 승인은 회로 해석 항목만"은 구현·9회로 합격 뒤 core·sizing·metrics·search 블록 변경이 '전 회로 동시 변경'이 된다는 사고 7 규칙과 어긋난다.
- 보강안: "구현 완료된 공유 계산 블록의 알고리즘 변경은 9회로 전후 결과 차(노드전압·front·SPICE verdict)를 붙여 보고, verdict가 바뀌면 사용자 확인"을 확정 사항 6에 추가(뒤집지 않고 범위만 보강).
- 분류: **(U)**(Q12).

### T25 [P3] 새 엔진 문서끼리의 충돌·낡은 문장
- 포함: G2-19, G5-19, G3-22(문서 부분), G6-20(P 513행 부분) -- T01·T04·T05·T10·T18의 (D) 부분과 함께 4절 목록으로
- 분류: **(D)**.

### T26 [P3] reference 자체 오류·낡음
- 포함: G1-10, G1-13, G1-15, G1-16, G1-17, G1-18, G1-22, G2-03(reference 문장), G2-17, G2-18, G3-08(reference 문장), G3-09(sky130 §8 표), G3-11(SKILL 169행), G3-13, G3-17, G3-18, G3-19, G3-20, G4-15, G4-16, G4-17, G4-18, G5-15, G5-16, G6-22, G6-23, G1-03(GM §2.7 보완)
- 문제: 회로별 보상 함수·옛 harness를 정본으로 지시(대원칙 3과 충돌 -- 다음 작업자가 회로별 함수를 다시 만들 경로), 식 오류(Miller Cm 1/2 누락 -- GB5 손계산 oracle에 옮기면 Cm 2배), 체크리스트 오류(gm/ID 단조 감소, ID/W ∝ (gm/ID)² → 실제 ⁻²), 실측과 다른 예제 수치, 낡은 경로·행 번호·상태 문구 등. 상세는 4절 D-R 표.
- 분류: **(D)**, 단 reference 파일을 고칠지·옛 판을 `legacy/`로 옮길지·SKILL.md 원칙 문장을 바꿀지는 **(U)** 한 항목(Q12).

---

## 2. (U) 사용자 질문 목록 -- 한 번에 답할 수 있게 12개로 압축

이미 대기 중인 질문(VGS Hermite 보간, L 처리 (다), D-1 ln(ID/W), D-2 L 탐색, D-3 시간 예산, D-4 격자 한 칸, LUT 재생성 승인, SP-10 파일럿 CL1·CL2)을 같은 결정끼리 합쳤다. 각 질문은 "추천대로"라고만 답해도 되게 썼다.

### Q1. LUT 재생성(U-27) 승인과 이번 실행에 넣을 열 [대기: LUT 재생성 승인 / 신규: G1-03·05·08·12·18(b)·20, G3-01·02]
- **[결정됨 -- L 처리 (나), 사용자 2026-10-07 "나로 하자."]** L은 같은 PDK 모델 bin 안의 두 LUT L 점 사이에서만 선형 보간한다(bin 경계를 넘는 보간 거부, L = bin 선택 + bin 안 연속, bin 지도는 모델 파일 `lmin`/`lmax` 파싱, tol_V에 bin 안 L 방향 LOO 추가). 그래서 **(a) 'L 앵커 S2 30점'은 철회**되고 L 격자는 18점(옛 12 + bin 경계 0.18·2·8·20 + 불연속 경계 반대쪽 끝점 0.185·0.255 µm)이다 -- 계획 LR3·N3.6·U-27 개정(worktree `plan-rev3` 커밋 `86115b1`), 상세 `../lut_regen_plan.md` 0·1.2a·2절. (b)~(h)는 이 결정과 별개로 아직 대기다.
- **[결정됨 (2026-10-07)]** 사용자 "B는 추천대로 해." -- (b)~(g) 예, (h) 나중(Q6 값 출처 = PDK 식). 반영: 계획 N7.2 U-27(열 묶음), N3.8 gmb(GMBS), N5.2 DF-25(VDSAT), N1.2 잡음 행(열 개명). worktree `plan-rev4` 커밋 `defdc24`.
- 질문: U-27 재생성을 승인하고 아래를 이번 실행에 포함할까요?
  - (a) L 앵커 S2 30점(RG D1) (b) L 상한 20 µm(D2) (c) 추가 열 VDSAT·GMBS(D6 권고) (d) 드레인·소스 여기 용량 CDD·CSS(D6 선택) (e) 잡음 열을 `SVG2_1HZ`(V²/Hz)·`SVG2_HF`로 개명(D5) (f) 공유 생성기 `assets/sky130_lut_sweep.py` 수정(D7, `destroy all` 등) (g) 앵커 집합 kind 공통(D8) (h) 전 폭 AC·잡음(D4, 약 12 h)은 지금 / 나중.
- 추천: (a)~(g) 모두 예, (h)는 Q6 답이 '값 출처 = LUT 열'이면 같은 실행, 'PDK 식'이면 나중.
- 근거: VDSAT은 오라클 합격 판정과 같은 정의라 봉인 7을 SPICE와 맞출 유일한 길(T02). GMBS가 없으면 gmb가 칸 경계에서 p99 16~21 % 튄다(T08). CDD·CSS는 접합 용량 값 출처 후보(T07). pfet은 8→20 µm에서 0.88 dB 미포화라 L 상한 8이면 INFEASIBLE이 LUT 범위 한계로 날 수 있다(T10). op 열은 비용 거의 0, D7 없이는 S2가 약 48 h.

### Q2. VGS(·VDS) 축 cubic-Hermite 보간과 tol_V 측정 정의 [대기: VGS Hermite 보간 / 신규: G1-01·06]
- **[결정됨 (2026-10-07)]** (i) 예, (ii) (A). 반영: 계획 N2.1 **DEC-87**, N3.6 tol_V(보간 방법과 2^p 환산), N3.7 LUT 곡선 검사(FC), N6.1 단위 1.
- 질문 (i): MOD1 VGS 축을 저장 도함수 cubic-Hermite(y = lnID, 기울기 = GM/ID, gm/ID는 그 다항식 미분으로 정의)로, VDS 축도 GDS/ID 기울기 Hermite로 바꿀까요? 이에 따라 LUTC r2 6절의 `multilinear_interp` AST 해시 고정을 '옛 함수 = 기대값 비교 참조'로 개정합니다.
- 질문 (ii): tol_V LOO를 운영 보간과 같은 방법으로 다시 재고, (A) 차수 p로 2^p 환산(Richardson)한 값을 셀 tol로 쓰고 ngspice 칸 중앙 표본 test로 검증 / (B) 지금 정의(LOO 그대로)를 유지하고 결과에 '보수 배수 약 2^p'만 표시.
- 추천: (i) 예, (ii) (A).
- 근거: G1 실측 VGS 축 오차 p50 1.25 mV → 2.6 µV, 칸 중앙 gm/ID p99 2.1 % → 0.02 %, 단조성 위반 0, 재생성 비용 0. op_point·역산·gm이 한 곡면이 되어 봉인 2 잔차와 SLSQP 꺾임이 사라진다. LOO는 간격 2배 LUT의 오차라 선형 4배·Hermite 16배 과대 -- 봉인·K_max·tol_I·W 보존이 모두 그만큼 느슨하다. (i)을 채택하면 지금 tol 표는 무효라 (ii)는 필수.

### Q3. 쓰기 소자 독립 좌표(D-1)와 봉인 7 포화 기준 [대기: D-1 ln(ID/W) / 신규: G1-14, G5-20, G3-01]
- **[결정됨 (2026-10-07)]** (i) (라) ln(ID/W), (ii) (C) `VDS − VDsat ≥ +tol_VDsat`(VDSAT 열 LOO). 반영: 계획 **DEC-88**, DEC-04·DEC-70 문언, N3.6 봉인 2(ID 환산 지표)·봉인 7, N5.2 DF-25.
- 질문 (i) D-1: (가) gm_id 유지 (나) 혼합 (다) VGS (라) ln(ID/W).
- 질문 (ii) 봉인 7: (A) 현행 `VDS − VDsat ≥ −tol_V` (B) 오라클과 같은 `VDS − VDsat ≥ 0` (C) `VDS − VDsat ≥ +tol`(엔진이 SPICE보다 보수). tol은 VDsat 열 LOO(Q1 VDSAT 채택 시) 또는 id_equivalent 셀값. 오라클 `saturation_rule = vds_ge_vdsat`(여유 0, SF 164행 '확인' 대기)은 그대로.
- 추천: (i) (라), (ii) (C).
- 근거: (가)면 봉인 허용이 gm_id_inverse 지표 p50 222 mV·max 445 mV라 VDsat보다 수백 mV 낮은 소자가 봉인을 통과하고 SPICE free 합격에서 떨어진다. reference GM(Jespers qF)·LC(Murmann IC)가 모두 전류밀도·반전 지수를 독립 변수로 쓴다(G1-14). (C)는 엔진 통과 해가 SPICE 비포화 FAIL이 되는 경로를 막는다. 단서: 같은 r이면 반전 수준 유지는 긴 L에서만 근사라 I0·ln IC를 보고로 덧붙인다(엔진 내부).

### Q4. 레이아웃 뒤 무엇을 보존·재검증하고, SPICE 합격은 어떤 기하로 도나 [신규: G2-01·02·03, G3-03·04·08, G6-03, G1-07]
- **[결정됨 (2026-10-07)]** (i) (나), (ii)~(v) 예. 반영: 계획 **DEC-89**, DEC-84 문언, N3.17 **LY1·LY2·LY7 개정 + LY8 신설**, N6.2 단위 9·T4·T7·T8. 주의: 사용자 원 규칙 '총 W 보존'(DEC-84)을 대체한다.
- 질문 (i) LY1 보존 대상: (가) 현행 '총 W 보존' / (나) '(ID, gm/ID, L) 보존, 실현 W = 슬라이스 fw에서 계산한 W_need(fw) = ID/J_slice'.
- 질문 (ii) MOD7 결과가 나오면 W_request 유무와 관계없이 실현 기하로 평가 커널 1회 + 봉인 1~8을 다시 돌린 뒤 freeze하고, LY1 tol은 후보 순위 기준으로만 쓸까요?
- 질문 (iii) LY2 diode 예외를 "ID 재보정만 불필요, 노드전압·봉인은 재계산"으로 바꿀까요?
- 질문 (iv) W 허용오차 상한의 tol_V 지표 = `id_equivalent` 셀값으로 명시하고, 하한(격자/(2·fw))이 상한보다 크면 실효 = max(상한, 하한) + '격자 지배' 기록으로 할까요?
- 질문 (v) SPICE 합격 넷리스트 기하 = MOD8 수렴 스냅샷의 (finger_w, nf, 행 확산 기하), sizing 직후 기하는 진단 실행만, metric 표는 엔진@sizing W / 엔진@실현 W / SPICE 3열이고 모델 오차 파일에는 2열−3열만 -- 이렇게 고정할까요?
- 추천: (i) (나), (ii)~(v) 예.
- 근거: 같은 gm/ID에서 J(fw)/J(5 µm) = −28 %~+170 %(LCS 표 A)라 W를 보존하면 ID가 틀어진다. tol_V×gm/ID는 gm/ID 12에서 38 %(셀 중앙)~227 %(최대)라 "거의 아무것도 거부하지 않고"(TV 4절) 재평가 없이 freeze된다. SPICE는 실현 기하로 돈다 -- 옛 엔진에서 layout W로 PM 79° → 18°. diode는 ID가 맞아도 VGS가 바뀌어 그 gate를 받는 미러·캐스코드의 포화 여유가 바뀐다. `gm_id_inverse` 지표면 상한이 330 %라 W 보존이 무력하다. Q2 Hermite를 채택하면 id_equivalent가 µV급이 되어 창이 거의 모든 폭에서 비므로 (iv)의 max 규칙이 필요하다.

### Q5. SPICE 합격 정의 보강 -- 꺼진 소자, 오라클이 못 재는 제약 [신규: G5-01, G6-02, G3-10]
- **[결정됨 (2026-10-07)]** (i) 예, (ii) CMRR·PSRR (A), 슬루·정착 (B). 반영: 계획 **DEC-90**, N3.6 SPICE 대조, N6.2 T4·T5, N6.1 단위 2(`spice_unverifiable[]`).
- 질문 (i): '전 MOS 포화'를 "엔진이 전도로 예측한 MOS가 SPICE에서 꺼지면 FAIL(전도 문턱 = 엔진이 소자마다 LUT VGS=0 누설로 계산)"까지 포함하는 뜻으로 확정할까요?
- 질문 (ii): 파일럿 spec의 CMRR·PSRR(≥ 60 dB), slew, 정착(t_lln 30 ns·t_settle 40 ns)을 어떻게 다룰까요? (A) 오라클 측정 추가 + 합격 판정 포함 (B) 측정은 추가하되 기록만 (C) T5를 '오라클 측정이 있는 제약 전부'로 좁힘.
- 추천: (i) 예. (ii) CMRR·PSRR은 (A)(엔진 뷰와 같은 여기 정의로 .ac 2회, 비용 작음), slew·정착은 (B)(β 루프·.tran 정의가 추가로 필요하고 SF F11과 일관). 그 사이 엔진은 spec 로드 때 `spice_unverifiable[]`를 미리 낸다.
- 근거: 지금은 ID > 0인 MOS만 포화를 보므로 바이어스가 무너져 꺼진 소자는 검사에서 빠지고, 선언 제약 0건 회로(folded·nmcnr·common_gate)는 그대로 합격할 수 있다(사고 20 (c)). 오라클 measure 5개로는 파일럿 T5가 늘 INCOMPLETE다.

### Q6. 접합 용량을 합격 실행에 넣을지, 확산 기하·값 출처 [신규: G1-02, G3-02, G2-16, G6-10, G1-12]
- **[결정됨 (2026-10-07)]** (i) 예, (ii) (나), (iii) (b) 정본 + (a) 대조 test. 반영: 계획 **DEC-91**, N3.8(국소 모델 스탬프·SPICE 독립 검증), N3.16 PDK 상수 행, N3.17 LY8, N6.1 단위 5.
- 질문 (i): 합격 실행에서 엔진·SPICE 모두 접합 용량을 넣고 오라클 `diffusion`을 필수(없으면 BLOCKED)로 할까요?
- 질문 (ii) 확산 기하: (가) finger마다 독립(현 오라클 `m=n_fingers`) / (나) Euler 행 공유 확산(MOD7 `ly.diffusion` 통계로 소자별 ad/as/pd/ps, m 유지). 레이아웃 전 첫 사이징점은 LUT 생성 규칙.
- 질문 (iii) 값 출처: (a) LUT CDD·CSS 열 − CGD·CGS (b) PDK 모델카드 접합 파라미터 + 역바이어스 + 확산 기하.
- 추천: (i) 예, (ii) (나), (iii) (b)를 정본, (a)는 Q1에서 열을 받으면 대조 test로.
- 근거: W = 5 µm에서 Cdd 4.34 fF 대 Cgd 1.20 fF라 고임피던스 노드 극점에서 같은 크기. 지금 diffusion을 선언하면 SPICE만 접합 C를 가져 엔진 PM·GBW가 낙관, 안 하면 둘 다 비현실적으로 일치. (가)는 공유 확산을 무시해 최대 약 2배 과대. LUT 열은 생성 때 고정 기하(ad = W·0.5 µm)라 공유 확산을 반영 못 해 (b)가 맞다. 전력 최소화가 약반전·큰 W로 밀리는 것을 되돌리는 항(GM §4.2)이 이것이다. `ad_per_w_m`·확산 연장 길이는 PDK 규칙에서 근거를 선언해야 한다.

### Q7. GB5 보상 방법론 [신규: G4-01·02·13]
- **[결정됨 (2026-10-07)]** (i) (나), (ii) (a) 기본 + (b) 폴백. 반영: 계획 **DEC-92**, N3.7 보상 규칙(GB5), DEC-02·DEC-24·DEC-70 문언, N6.1 단위 7. 회로별 S는 J7 ratify.
- 질문 (i): (가) 극점·영점 근사식을 조립해 gm_req·보상소자 값을 정함 / (나) 보상 수동소자 값을 θ 연속 변수로 두고 GBW·PM을 봉인 `ss` 전회로 MNA로 판정, 근사식은 시작점과 `comp_approx_gap` 기록에만.
- 질문 (ii) 영점 상쇄 저항: (a) 구조 규칙 R = 1/Σgm(저항 끝 넷을 출력으로 갖고 루프 반대쪽에서 신호를 받는 CS 셀 집합, 회로별 결과는 J7 ratify) / (b) R도 θ 변수.
- 추천: (i) (나), (ii) (a) 기본 + (b) 폴백.
- 근거: reference TFD 3절 실측 -- NMCNR Eq10/11 근사는 PM 60~90° 전 구간에서 GBW를 2.5~21배 틀리고 PM 오차 방향도 바뀐다. nmcnr·ngcc·파일럿(Rz1·Rz2)·two_stage(Rz) 합격이 직접 걸린다. (나)는 판정 위치(DEC-74)와 같아 새 닫힌식이 필요 없고 ngcc feedforward 영점도 자동 포함. 엔진이 `nulling_reference_device`를 읽지 않으므로 (ii)가 없으면 Rz·Rm 값이 정해지지 않는다.

### Q8. 레이아웃 matching·면적 규칙 (회로 해석 포함) [신규: G2-06·07·09·10, G4-03·05, G5-03·04·12, G6-04·06·11·13]
- **[결정됨 (2026-10-07)]** (i)~(v) 예, (vi) (나), (vii) 예, (viii) 예(기록만), (ix) 예(실측 뒤 재질의). 반영: 계획 **DEC-93**, N3.17 **LY4·LY5 보강 + LY9·LY10·LY11 신설**, DEC-79(면적 포함 항목), N7.1 **J14 신설**(옛 J-U4 -- 9회로 결과 ratify는 남음).
- 질문 (i): 캐스코드 대칭쌍(같은 gate, source 다름, 확정 쌍 위로 stack된 쌍)을 matching 그룹 `branch_symmetric`으로 인정할까요?
- 질문 (ii): 레이아웃 규칙 LY4·LY5에 두 줄 추가 -- branch_symmetric은 행 swap 분배 common-centroid만 허용(interdigitation은 공유 노드가 없어 불가), 실패 시 차동쌍과 같은 완화 순서 / 전류거울은 정렬 키 첫째 = 'interdigitation 성립'.
- 질문 (iii): matching 분류 -- 같은 gate라도 diode와 다른 블록의 소비 소자(`bias_distribution`), 루프 신호 gate 공유(`feedback_shared`)는 레이아웃 matching에서 빼고 근거와 함께 기록, 차동쌍 유도에서 바이어스 형제 소자(파일럿 Vx의 M58, Vy의 M63)를 먼저 제외 -- 이 규칙으로 하고 9회로 결과는 J-U4 대조표로 확인받을까요?
- 질문 (iv): LY5로 완화된 차동쌍을 결과 맨 앞 `review_needed` + dx·dy로 표시할까요?
- 질문 (v): box 개선 행 접기 -- matching 그룹이 없는 행만 자동으로 접고, matching 행은 패턴 함수로 행 수를 다시 짓는다(접은 뒤 Euler·matching 재판정).
- 질문 (vi): box 판정 -- (가) spec에 `box_row_width_ratio_max` 선언 필수(없으면 로드 거부: 지금 9회로 전부 거부됨) / (나) 하드 게이트 없이 floorplan 외곽 면적(판정 축)을 목적으로, 행 폭 비는 기록만.
- 질문 (vii): 판정 축 면적에 행 끝 dummy·tap·well 간격을 넣을까요(PDK 규칙 번호와 함께 선언, front 표에 '포함 항목' 열)?
- 질문 (viii): stage를 넘는 hub 병합 -- 면적 비교로 채택하고 노이즈 결합 우려 거부는 기록만 할까요?
- 질문 (ix): 복사한 floorplan 본문 리터럴이 A_L을 격자 한 칸 이상 바꾸는 것으로 실측되면, 그때 본문 수정(해시 깨짐) 승인을 다시 요청해도 될까요?
- 추천: (i)~(v) 예, (vi) (나), (vii) 예, (viii) 예(기록만), (ix) 예(실측 뒤 재질의).
- 근거: AGI §6.3이 같은 공백을 이미 찾아 stack 전파로 고쳤고(M2a/M2b·M3a/M3b 재현, M57/M58 비유입), consistency-map 14·16차 실측은 branch_symmetric swap 분배 dx 0.00/dy 0.20, interdigitation 불가. 파일럿 두 입력쌍이 지금 규칙으로는 3소자라 review_needed가 되어 '차동쌍 CC 필수'가 파일럿에 적용되지 않는다. `apply_explicit_row_split`은 원본 docstring상 매칭 파트너 없는 소자용이고 interdigitation/CC 순서를 보존하지 않는다. box 비 1.5·2.0은 상수이고 목적(floorplan 효율)은 이미 판정 축 면적(12번 (나))이 맡는다. dummy·tap은 행 수 비례 고정비라 front 순위를 뒤집을 수 있다.

### Q9. topology·spec 파일 선언 (사용자 소유 파일) [대기: SP-10 / 신규: G4-08·21, G5-22]
- **[결정됨 (2026-10-07)]** (i) 예(6회로 선언은 topology 정정 대기열 -- "한꺼번에 반영" 지시 대기), (iii) 예, (iv) SP-10 해소 = CL1·CL2 **각각 1 pF**(합계 2 pF). **(ii) follower body는 사용자 답 대기**. 반영: 계획 **DEC-94**, N6.1 단위 2.
- 질문 (i): topology에 gate 전용 외부 바이어스 넷 선언(`bias_inputs` 또는 `ports` role)을 두고 미선언은 거부하는 게이트를 넣을까요? 그렇다면 6회로 선언을 정정 대기열에 넣습니다: common_gate {VNBias1, VNBias2, VPBias1}, folded {bias3}, ngcc {VBP, VBN}, nmcnr {VB1~VB5}, pushpull {VPB1, VNB1}, two_stage·two_stage_sf {bias}.
- 질문 (ii): follower 소자의 body가 도면에서 어느 넷인지 소자별로 답해 주세요 -- two_stage_sf M8, pushpull M1~M4, sf M18~M22 각각 A(극값 레일, 현 기본 규칙) / B(자기 source).
- 질문 (iii): topology에 선택 키 `source_manifest{figure, device_count, passive_count}`(사람 선언)를 두고 로더가 netlist 수와 대조하게 할까요?
- 질문 (iv) SP-10: 파일럿 current_reuse의 CL1·CL2가 각각 1 pF(차동 출력 양쪽 각각)인지, 합계 1 pF(각 0.5 pF)인지.
- 추천: (i) 예, (ii) 답 필요(회로 해석이라 추천 없음), (iii) 예, (iv) 추천 없음(사용자 확정 '파일럿 부하 C_Ltot 1 pF'의 해석).
- 근거: 지금은 오독된 넷(TEC 사고 5형)도 '외부 바이어스'로 조용히 흡수되어 사이징이 진행된다. follower의 gmb·VSB는 출력 레벨·이득에 직접 닿는다(사고 4: body 태그를 연결로 오독). consistency-map 47차에서 가상 소자 9개·반쪽 12소자 누락이 소자 수 대조 부재로 늦게 발견됐다.

### Q10. 탐색 방법 묶음 [대기: D-2, D-3, D-4, L 처리 (다) / 신규: G5-07]
- **[결정됨 (2026-10-07)]** (i) 기본안(bin 결정에 맞춰 'bin 벡터' 처리로 읽음), (ii) 보류(cProfile 뒤 재질의), (iii) 예, (iv) L 결정 (나)로 종결, (v) 예. 반영: 계획 **DEC-95**, N3.9 **LR10 신설**, DEC-64(종속 소자 우선순위), DEC-79(ΔA_tie 식), N7.2 U-47.
- 질문 (i) D-2 외층 L 이산: 기본안 L-a(시작점 고정) + L-c(ℓ 분지 multi-start) + front 점에만 L-b 1회.
- 질문 (ii) D-3 시간 예산: 300 s를 front 전체에 쓸지 -- 새 커널 cProfile(U-49) 뒤 재질의로 보류해도 될까요?
- 질문 (iii) D-4 면적 동률 폭 ΔA_tie = MANUFACTURINGGRID × max(두 점 bbox 변)이 '격자 한 칸'의 뜻이 맞나요?
- 질문 (iv) 'L 처리 (다)': 대기 중인 원 질문 그대로(이 검토 입력에는 문언이 없어 새 근거만 덧붙임 -- reference는 L 이산·bin 경계 보간 금지를 지지한다(G1-13: pfet 0.175 → 0.18 µm에서 ID 중앙 9.4 %·최대 49 %·VTH 19 mV 점프), L 상한은 Q1 (b)).
  - **[결정됨 2026-10-07: (나) bin 안 선형 보간 -- Q1 머리 참조]** 그리고 위 G1-13 수치는 **bin 불연속이 아니었다**: ngspice-46은 0.175와 0.18 µm에 같은 아래 bin [0.15, 0.18]을 쓴다(경계값은 lmax = L인 bin). 진짜 전환점 점프는 VGS 환산 2 mV 아래다(`../lut_regen_plan.md` 1.2a). 외층 L은 이제 bin 고정 연속이므로 (i) D-2 'L 이산' 기본안(L-a·L-c·L-b)도 이 결정에 맞게 다시 써야 한다.
- 질문 (v) 종속 gm_id 소자 선택(G7 U1·U4): diode가 없을 때 '이름 정렬 첫 멤버'를 구조 우선순위(diode > GB5가 gm을 요구하는 소자·뒤 stage 소자는 독립 유지 > 대칭 궤도 대표 > 이름)로 바꾸고 '이름 전단사 후 front 동일' metamorphic test를 둘까요?
- 추천: (i) 기본안, (ii) 보류, (iii) 예, (iv) 원 질문의 기본안 유지(reference가 반대 근거를 주지 않음), (v) 예.
- 근거: 이름 tie-break는 θ 매개화·bounds·SLSQP 경로를 이름에 따라 바꿀 수 있어 대원칙 'topology 종속 금지'의 측정 구멍(사고 21: 방향은 신호경로 순서가 정한다). (iii)은 Q8 (vii)로 A_L 구성이 바뀌어도 식은 그대로다.

### Q11. 범위와 추가 제약 -- 준정적·미스매치·PVT·잡음·보고서 [신규: G1-09·11·21, G3-09·11·15·16, G4-10, G6-08·09·12·18]
- **[결정됨 (2026-10-07)]** (i) 예, (ii) 예, (iii) 기본안 + 사용자 답 "9회로 중 잡음·왜곡 스펙은 없어."(합격 = TT 27 °C), (iv) 예 + 좌표 (a). 반영: 계획 **DEC-96**, DEC-85, N1.2(잡음·PVT 행), N3.8(준정적·미스매치·잡음 항목), N7.2 U-17.
- 질문 (i) 준정적: `nqs_ratio`(UGF / 신호 경로 소자 최소 f_T)를 모든 회로에 보고만 하고, 제약은 spec에 임계값(출처 필수)이 선언될 때만 걸까요?
- 질문 (ii) 미스매치: Pelgrom σ(PDK mismatch 파일 계수)를 매칭 그룹마다 모든 front 점에 보고하고, 제약은 spec 선언 시만(U-17 값은 그대로 대기) -- 이렇게 할까요?
- 질문 (iii) PVT·잡음: 합격은 TT 27 °C 유지, ss/ff·온도 끝점 '기록만' 오라클 옵션은 마일스톤 뒤. 9회로 spec 중 잡음·왜곡 스펙이 있는 회로가 있나요(있으면 `unsupported_metric` 정지 대상)?
- 질문 (iv) 보고서: DRS 8섹션을 결과 JSON 키(못 낸 섹션은 `not_run`)로는 엔진 완성(DEC-85) 범위에 넣고, HTML 렌더·§7 레이아웃 가이드·시각 검증 절차는 마일스톤 뒤로 미룰까요? 회로도 좌표 출처는 (a) S1 자동 배치 (b) topology 선택 필드 `schematic` (c) 연결 표만 중 무엇으로 할까요?
- 추천: (i) 예, (ii) 예, (iii) 기본안 + 잡음 스펙 유무 답 필요, (iv) 예 + 좌표 (a).
- 근거: MNA와 BSIM4 기본은 둘 다 준정적이라 서로 못 잡고, sky130 §8 예제의 '준정적 True'도 재계산하면 3·4행이 False(f_T 773 MHz·23.5 MHz). 0.1·5 mV는 상수라 박지 않는다. 면적 최소화가 매칭 소자 W·L을 최소로 미는 것을 막을 장치가 지금 없다(GM §13.5 옛 사고). topology 종속 금지 원칙상 엔진이 회로별 좌표를 가질 수 없어 (a)가 원칙과 맞다.

### Q12. 문서·거버넌스 [신규: G5-14·15, G3-13, G4-15, D-R 목록 전체]
- **[결정됨 (2026-10-07)]** (i)~(iv) 예. 반영: 계획 N6.1 레인 P(reference 정정·재작성·legacy 이동·SKILL.md 원칙 문장 교체), N2.1 **DEC-51 범위 보강**((iv)), `NEW_ENGINE_DESIGN_REQUIREMENTS.md` 확정 사항 6.
- 질문 (i): 4절 D-R 표의 reference 정정(29행, 식 오류·체크리스트 오류·예제 수치·낡은 경로)을 한 card로 묶어 고쳐도 될까요?
- 질문 (ii): function-selection-map·topology-fn-derivation-guide를 새 엔진 판으로 다시 쓰고(TFD는 'GB5 검증 오라클 목록'으로), 옛 판을 `legacy/`로 옮길까요? (reference 이동·삭제라 승인 필요)
- 질문 (iii): SKILL.md·consistency-map의 원칙 문장을 교체할까요 -- 함수 우선순위의 옛 harness(`run_sizing_pipeline` 등) → 새 진입점 `run_gmid_design_pipeline`, `topology_library.py` 회로별 보상 함수 → GB5 일반 규칙, 원칙 맵에 새 대원칙 7행 추가.
- 질문 (iv): 확정 사항 6에 "구현 완료된 공유 계산 블록의 알고리즘 변경은 9회로 전후 결과 차를 붙여 보고하고, SPICE verdict가 바뀌면 사용자 확인"을 추가할까요?
- 추천: (i)~(iv) 모두 예.
- 근거: SKILL.md가 이 reference들을 먼저 읽게 하므로(FSM 12행) 고치지 않으면 다음 AI가 회로별 보상 함수·옛 harness를 다시 만든다(대원칙 3 충돌, 사고 1·44차 클래스). Miller Cm 식(GM §6.4 식 8.15)의 1/2 누락을 GB5 손계산 oracle로 옮기면 Cm이 2배가 된다. (iv)는 사고 7 규칙(공유 엔진 계산 로직 변경은 승인 뒤)과 확정 사항 6의 범위 차를 메운다.

---

## 3. (E) 작업 묶음 -- 모듈·브랜치별

(U) 답이 필요한 부분은 [Qn 뒤]로 표시했다. 나머지는 답과 무관하게 착수 가능하다.

### E-1 ng-u2 (구조 유도, MOD3)에 넣을 것
- 차동쌍 유도에서 바이어스 형제 제외 + 두 멤버 is_diode false, U3·U5를 rel_matching보다 먼저(T11 (1), G5-03·G4-04). [결과는 J-U4 ratify]
- stack 전파 규칙 `branch_symmetric`(seed = 확정 쌍, 채널 stack 고정점, evidence)(T11 (2), G4-03·G5-04·G2-07). [레이아웃 사용은 Q8 뒤, 유도·기록은 지금]
- matching 레코드 role·evidence·status 필드와 레이아웃 전달 정책(derived·ratified만)(T11 (3), G6-06·G4-20). [bias_distribution·feedback_shared 분류 규칙은 Q8 (iii) 뒤]
- `dc_roles.py` 규칙 (3′) 바이어스 넷 재귀 전파 + review_needed 폴백 + 9회로 수치 재측정(T14 (1), G4-14).
- `graph/row_groups.py` 신설(matching base + 내부 2단자 넷 직렬 상속, 형제 배제)(T17 (1), G5-06).
- metamorphic 추가: tail 바이어스 소자 추가 불변, telescopic 캐스코드쌍 2개, M57/M58형 0개, 미러 사슬 bias 넷, 이름 전단사 front 동일(T11 (7), T14, G5-07 [test 부분은 Q10 (v) 뒤]).
- `test_symmetric_partner_consistency.py`(G5-21).

### E-2 ng-mna (MOD5)에 넣을 것
- cdb·csb 스탬프 자리와 필드 배선(층 0 기생 고정점·GB5 C_out,total·슬루 C_k·nf 무효화)(T07 (1)(3)). [값 출처는 Q6 뒤 -- 스탬프·필드 인터페이스는 지금]
- `metrics/poles_zeros.py`(일반화 고유값, 조립 fp 키)(T06 (4), G4-13).
- GB4 `achievability.py` 완화 극값 상한 + 국소 모델 소자 집합 = 블록 노드 단자 소자 전부 + 격자 끝 플래그·'LUT 범위 한계' 사유 + `test_gb4_bound_dominates_mna`(T10, G1-04·08·G3-12).
- 보고 metric: `nqs_ratio`(T19), `mismatch_sigma_v`(T20), 슬루 I_max/C_k 보고(G1-19). [제약화는 Q11 뒤]
- `test_gain.py` 이중 곱 재발 방지(G3-21).
- 레지스트리 항목에 `oracle_measure` 필드(T09 (1)).

### E-3 ng-rows (레이아웃 행 구성, MOD7)에 넣을 것
- `match_audit.py`(3b·3c·dx/dy·`check_mirror_symmetry` 복사·role별 필수 게이트, 3c 허용 유도)(T12 (1), G6-05·G5-05·G2-13).
- 행 접기 뒤 `row_euler` + `match_audit` 재실행·악화 시 거부·diffusion-safe 지점만(T12 (2), G6-04·G4-06). [자동 접기 범위는 Q8 (v) 뒤 -- 재판정 자체는 지금]
- Euler 막힘 시 W 보존 패리티 전환 후보 우선(T12 (3), G2-08).
- 박스 개선 Case A(행별 fw 후보·목표 행 폭)(T16 (2), G2-05), 비차동 정렬 키 순서(G2-20), 매칭 L 동일성 확인(G2-12).
- `hub_merge.py`와 `merge_decisions` 기록(T17 (2), G2-06·G4-07·G6-17). [거부 정책은 Q8 (viii)]
- floorplan 입력 의미 정정(spine = 블록, sub_kinds, mirror_pairs, net_weights)(T17 (3), G6-07·G5-13).
- 기록 필드: `ly.floorplan` 확장, `ly.group.candidates`, `ly.box.attempts`·`fail_analysis`(T16 (5), G6-14·G6-16·G2-14), `ly.diffusion` 통계(T07 (2), G2-16·G6-10).
- box 판정을 면적 기준으로·dummy/tap/well 반영(T16 (1)(3), G2-10·G6-13·G2-09). [Q8 (vi)(vii) 뒤]
- `test_floorplan_literal_sensitivity.py`(G5-12 (1)(2)).
- 출판 정답 오라클 test(SE §6.1·§7, DRS PRE-FLIGHT 26)(G2-15·G6-21).

### E-4 ng-spec (spec 로더)에 넣을 것
- spec 로드 시 `spice_unverifiable[]` 사전 출력(T09 (1), G6-02).
- 잡음·왜곡 metric 선언 → `unsupported_metric` 정지(T23, G3-16).
- 결과 JSON `spec{declared, derived, engine_computed}` 3층(G6-19), metric 이름 레지스트리 정본으로 통일(G6-20).
- 원소 값 출처표·`element_value_unresolved` 탐색 전 정지(G5-11) -- S0 쪽이면 ng-spec, graph 쪽이면 ng-u2(파일 위치는 오케스트레이터 판단).
- [Q8 (vi)에서 (가)를 고르면] DSF `layout_criteria` 필드, [Q11에서 임계 선언을 허용하면] nqs·mismatch 임계 키.

### E-5 새 작업 (진행 중 브랜치에 맞지 않음)
- **MOD1 보간·tol 개정(LUTC r3/r4)** [Q2·Q1 뒤]: 축별 Hermite·FC 검사·같은 칸 역산·AST 고정 → 참조 비교, `tolerance.py` 같은 방법 LOO + 2^p 환산 + ngspice 칸 중앙 표본 test, `vdsat.py`(VDSAT 열), gmb = GMBS 열(열 전까지 임시 3점식 표시), `curve_report` 진단 열, I0·ln IC 파생 표(T08, T05 (3), T02 (1)).
- **GB7 봉인 보강**: 봉인 9 가지 전류 방향·크기 + 연속 margin 제약 노출(T03 (2), G5-02, 지금 착수 가능), 봉인 7 기준 교체 [Q3 뒤], IC6 DOF test(G5-08), IC5 게이트 사각 docstring test(G5-09).
- **MOD8 수렴 루프**: 실현 기하 재평가·진입 조건·diode 재계산·3열 기록 [Q4 뒤](T04), `W_adjustable` 제거·finger_quantization 거부 사다리(T18, 지금 착수 가능).
- **spice_oracle 계약 확장(C15~)**: topology 동일성 C15·`--bias iso`·소자별 tol 스키마·`diagnosis`·`--omit/--short/--ideal`·`pm_crosscheck_deg`(T09, T05 (4), 지금 착수 가능), cmrr/psrr/slew/settle measure [Q5 (ii) 뒤], 꺼진 소자 FAIL·`off_current_A` 필수 [Q5 (i) 뒤], `diffusion` 필수·소자별 ad/as override [Q6 뒤], ss/ff 기록 옵션 [Q11 (iii)].
- **D4 보상 design + `metrics/compensation.py`** [Q7 뒤](T06).
- **MOD2 입력 게이트**: `net_case_collision`(T15 (2), 지금), `authoring_anomalies`(dangling·대칭 미해결, 지금), `bias_inputs` 게이트 [Q9 (i) 뒤], `source_manifest` 대조 [Q9 (iii) 뒤].
- **MOD9 design 문서 신설** [Q11 (iv) 뒤]: 8섹션 스키마·`report_completeness`·`layout_guide`·`topology_review`·HTML 복사 렌더러·DOM 검사(T22, T15 (3)).
- **MOD6 결과 기록**: `optimality{...}`·`runs.front[].selection`(G3-23·G6-20, 지금), 종속 소자 tie-break 교체 [Q10 (v) 뒤].
- **tests 공통**: `conftest.library_device` helper(G5-17).

---

## 4. (D) 문서 정정 목록

### D-P 새 엔진 문서(계획서·설계 초안·계약) -- 결정이 이미 있거나 사실 정정이라 오케스트레이터가 할 수 있는 것
| # | 위치 | 정정 | 출처 ID |
|---|---|---|---|
| 1 | P N6.2 T4(1087행), 마일스톤 1(1078행) | "노드전압 tol_V 안" 삭제 → "포화 판정, 노드전압 차는 T8 기록" | G6-01 |
| 2 | ROADMAP T4(102행)·마일스톤 (b)(284행), G7 8.3 판정 2, PUD AC-1 (iii)(v) | 같은 정정, AC-1은 '해소됨(UD 8)' | G3-05 |
| 3 | ROADMAP 1절 93행 'W 정본·레이아웃 어댑터는 W를 바꾸지 않음', 53행 '레이아웃은 합격 밖' | UD 레이아웃 규칙으로 정정(합격 기하는 Q4 답 반영) | G3-03 |
| 4 | LUTC 8절 246행 "vdsat: 소비자 없음" | G7 봉인 7·창이 소비자 -- 정정 | G1-03 |
| 5 | M15 3.5(213행) GB4 "소자별 gm/gds 최대" | 완화 극값 정의로 정정(P N3.7 477행과 일치) | G1-04 |
| 6 | M15 2.7·O1, TV 머리 | 'L 축 LOO는 LUTC 5절 r2(VGS·VDS·VS 축)로 대체' 표시 | G3-22 |
| 7 | PUD DF-3(338행) "총 W는 엔진 W와 같은 값" | 사실 아님 -- 정정 | G2-02 |
| 8 | PUD DF-14(349행) "import 재사용" | LY4·M7 L10(본문 복사 + AST 해시)으로 정정, 이력은 history | G2-19, G5-19 |
| 9 | PUD 370행 "R D4 판정 축 재필터는 보고만" | UD 132행 12번 (나)로 정정 | G5-19 |
| 10 | P N3.8 513행 "판정 축 재필터는 보류", DSF 98행·DM6 metric 이름 | DEC-79·D-6 정정, metric 이름 하나로 | G6-20 |
| 11 | M7 58행 '복사하지 않는 함수' 목록 | `find_hub_merge_candidates`를 채택하지 않는다면 사유 기록(채택 시 복사 목록으로) | G4-07 |
| 12 | NR 288행·M7 159행 `W_adjustable` | 계약에서 제거(또는 spec·ratify 고정 소자만) | G2-04 |
| 13 | REQ 3.3 `self_biased_diode` 주석, ROADMAP 323행 | Q4 (iii) 답에 따라 "ID 재보정만 불필요" | G3-08, G2-03 |
| 14 | P T7(1090행) | "MOD8 수렴 레이아웃 W로 SPICE" 명시(Q4 (v) 뒤) | G6-03 |
| 15 | LUTC 6절 AST 복사 고정 | Q2 (i) 채택 시 '참조 비교'로 개정 | G1-01 |
| 16 | 계획 잡음 항목 | "잡음 metric은 γ 식이 아니라 LUT 잡음 열(두 주파수) 보간" 한 줄 | G1-20 |

### D-R reference 자체 오류·낡음 -- 고칠지는 사용자 결정(Q12) 하나로
| # | reference | 오류·낡음 | 정정안 | 출처 ID |
|---|---|---|---|---|
| 1 | GM §6.4(436~439) 식 8.15 | Miller Cm 근의 공식에 1/2 누락(같은 절 예제 1.41 pF와도 모순) | Cm = (NDP/(2Z))·[C1+C2+√((C1+C2)²+4C1C2Z/NDP)] + 유도 한 줄 | G1-10 |
| 2 | GM §2.7 | 2/(gm/ID) VDsat은 short-channel 과대만 적음 | 약반전에서는 과소(2nUT ≈ 60~80 mV < 수 UT) 추가 | G1-03 |
| 3 | GM §2.3(131) | 'i=1 (q=1)'은 같은 점이 아님(q=1이면 i=2) | 정정 | G1-17 |
| 4 | GM §4.4(314) | W = ID/IDu (L 빠짐) | W = L·ID/IDu | G1-17 |
| 5 | GM 핵심 방정식 색인(600~602) | 절 번호 틀림(HD3 §11.1, Rm §10.4) | 정정 | G1-17 |
| 6 | GM §13 머리 | role 라벨 처방(대원칙과 충돌) | '옛 엔진 기록, 교훈 3개만 유효' 표시 | G1-22 |
| 7 | LC 5(79~82) | gm/ID 단조 감소(정점 오른쪽만), ID/W ∝ (gm/ID)²(실제 ⁻², 속도포화면 ⁻¹) | 두 문구 정정 | G1-16 |
| 8 | LC 7.2 L 행(118) | 'L 선형 보간'은 bin 경계에서 틀림 | [결정됨 2026-10-07 (나)] 'L 선형, 불균등 격자 그대로'를 **같은 bin 안으로 한정**(bin 경계 넘는 보간 금지, LR3). 원 처방 '보간 금지'는 대체됨 | G1-13 |
| 9 | LC 7.2(121~123) | 오프라인 역LUT 권고 | '역표는 순방향과 같은 곡면에서만' | G1-15 |
| 10 | LC 7 머리(98)·GM §3.5(243) | `SemiEmpiricalGmIdLUT`가 Hermite 구현 예시라고 함(실제는 4축 선형) | 정정 | G1-18 |
| 11 | LC 8.1(280)·8.2(288) | SID_1F '구현 대기'·단위 없음(실제 V/√Hz), W_bounds Phase 4 | RG D5 이름·단위, VDSAT·GMBS·CGS·CGB·CDD 열을 필수 필드 표에, 상태 갱신 | G1-18 |
| 12 | SE §8.3(984~985) | "diode는 SPICE가 알아서 보정" -- 노드전압 예측엔 해당 없음 | 주석 정정 | G2-03, G3-08 |
| 13 | SE §8.2~§8.4 | 연속 finger_w 탐색·19.6 µm 사례·'수십 µm 안전' | E5 이후 슬라이스, 안전 상한 = bin wmax와 슬라이스 최대 폭 | G2-17 |
| 14 | SE 967행·§9(1058~1073)·§2.5.2 CC 표 | check_box_shape 인자 모순, 낡은 경로, PDF p.19 3·4열 누락 | 3건 정정 | G2-18 |
| 15 | sky130 §8 IGS 표 | '준정적 4행 모두 True' -- 3·4행 False | 표·문장 정정 | G3-09 |
| 16 | SKILL 169행 | 차동쌍을 미러와 같은 'moderate~strong' 줄에 둠 | 미러/전류원 대 차동쌍(오프셋은 gm/ID 클수록 감소) 분리 | G3-11 |
| 17 | SKILL §1.5·§4·141~157·214행, sky130 §11 | 회로별 topology_fn·`topology_library.py` 지시 | GB5 일반 규칙 정본, 닫힌형 결과는 손계산 오라클 test로 | G3-13 |
| 18 | SKILL 187~190·sky130 §4 64행 | gm/ID 상한 29.93/32.20 상수(비포화 점, PMOS 실제 32.60) | '`curve_report`가 조건마다 계산' | G3-17 |
| 19 | sky130 §2·§3 | L 4점·55분, 함정 5개 누락(`nf` 대신 `m`, `destroy all`, VS 상한, stderr 혼입, vbs 부호) | 갱신 | G3-18 |
| 20 | sky130 §5(74~81) | W ≈ 24660 µm 재현 안 됨(7191 µm) | 사용 ID 명시·재계산 | G3-19 |
| 21 | spice-verification 90~94, sky130 §13.1·529~530 | 낡은 경로·행 번호, Figure 번호 자기 모순, 미결 TODO | 함수 이름 기준·번호 통일 | G3-20 |
| 22 | FSM 44~59·160·166, TFD 1~7·194 | 회로별 보상 함수·allowlist 추가 지시 | TFD = 'GB5 검증 오라클 목록', FSM 새 판, 옛 판 legacy(Q12 (ii)) | G4-15 |
| 23 | TFD 63~75·183, FSM 52 | Miller '완전 결정(자유도 없음)'·Z=10·NDP=4·C1=0.1CL·mu_ratio 3.9775 | Z·NDP는 PM 자유도, 상수에 '새 엔진 사용 금지' | G4-16 |
| 24 | AGI 3~9·158~161·489~501·509~518 | '미커밋' 상태, 이름 힌트·레일 이름 집합 폴백 | '새 엔진과의 관계' 절 | G4-17 |
| 25 | TBD 16~19 | "10~20 % 오차는 넘어감" | 질적 불일치 → 8단계 진단, 양적 차 → 모델 오차(DEC-72) | G4-18 |
| 26 | consistency-map 21·275~279·37행, 변경 이력 48차에서 멈춤 | 옛 harness 정본 지시, 새 대원칙 없음 | 원칙 맵 7행 추가, harness 행 legacy 표기, 사고마다 '새 엔진 대응' 줄 | G5-15 |
| 27 | known-incidents 3·125~126·240~243·501~502·414~417·620~622 | 원칙 개수(4 → 5), 삭제된 예시, 없는 계획 절, 낡은 primitive 권고, '반씩 나눔'이 규칙처럼 읽힘 | '새 엔진 대응' 주석 | G5-16 |
| 28 | DRS 6·188·230~235·243·311·397·412·571, 92·308 | `assets/` → `legacy/` 경로, 이동된 함수, 새 엔진이 복사하지 않은 함수를 필수 근거로 지정 | 경로 정정 + '옛 함수 → 새 엔진 대응' 표 | G6-22 |
| 29 | DRS 498~500·380·596·606~610·400 | 내부 모순 5곳 | 문구 정정 | G6-23 |

---

## 5. ID → 주제 색인 (132건 전부)

| ID | 주제 | ID | 주제 | ID | 주제 |
|---|---|---|---|---|---|
| G1-01 | T08 | G2-01 | T04 | G3-01 | T02 |
| G1-02 | T07 | G2-02 | T04 | G3-02 | T07 |
| G1-03 | T02 | G2-03 | T04·D-R | G3-03 | T04 |
| G1-04 | T10 | G2-04 | T18 | G3-04 | T05 |
| G1-05 | T08 | G2-05 | T16 | G3-05 | T01 |
| G1-06 | T05 | G2-06 | T17 | G3-06 | T09 |
| G1-07 | T05 | G2-07 | T11 | G3-07 | T05 |
| G1-08 | T10 | G2-08 | T12 | G3-08 | T04·D-R |
| G1-09 | T19 | G2-09 | T16 | G3-09 | T19·D-R |
| G1-10 | D-R | G2-10 | T16 | G3-10 | T09 |
| G1-11 | T20 | G2-11 | T18 | G3-11 | T20·D-R |
| G1-12 | T07 | G2-12 | T11 | G3-12 | T10 |
| G1-13 | D-R | G2-13 | T12 | G3-13 | D-R |
| G1-14 | T13 | G2-14 | T16 | G3-14 | T09 |
| G1-15 | T08·D-R | G2-15 | T21 | G3-15 | T23 |
| G1-16 | T08·D-R | G2-16 | T07 | G3-16 | T23 |
| G1-17 | D-R | G2-17 | D-R | G3-17 | D-R |
| G1-18 | D-R | G2-18 | D-R | G3-18 | D-R |
| G1-19 | T22 | G2-19 | T25 | G3-19 | D-R |
| G1-20 | T23 | G2-20 | T16 | G3-20 | D-R |
| G1-21 | T23 | | | G3-21 | T21 |
| G1-22 | D-R | | | G3-22 | T05·T25 |
| | | | | G3-23 | T22 |
| | | | | G3-24 | T22 |

| ID | 주제 | ID | 주제 | ID | 주제 |
|---|---|---|---|---|---|
| G4-01 | T06 | G5-01 | T03 | G6-01 | T01 |
| G4-02 | T06 | G5-02 | T03 | G6-02 | T09 |
| G4-03 | T11 | G5-03 | T11 | G6-03 | T04 |
| G4-04 | T11 | G5-04 | T11 | G6-04 | T12 |
| G4-05 | T11 | G5-05 | T12 | G6-05 | T12 |
| G4-06 | T12 | G5-06 | T17 | G6-06 | T11 |
| G4-07 | T17 | G5-07 | T14 | G6-07 | T17 |
| G4-08 | T15 | G5-08 | T21 | G6-08 | T22 |
| G4-09 | T15 | G5-09 | T21 | G6-09 | T22 |
| G4-10 | T19 | G5-10 | T15 | G6-10 | T07 |
| G4-11 | T09 | G5-11 | T21 | G6-11 | T11 |
| G4-12 | T09 | G5-12 | T16 | G6-12 | T22 |
| G4-13 | T06 | G5-13 | T17 | G6-13 | T16 |
| G4-14 | T14 | G5-14 | T24 | G6-14 | T16 |
| G4-15 | D-R | G5-15 | D-R | G6-15 | T22 |
| G4-16 | D-R | G5-16 | D-R | G6-16 | T16 |
| G4-17 | D-R | G5-17 | T21 | G6-17 | T17 |
| G4-18 | D-R | G5-18 | T22 | G6-18 | T22 |
| G4-19 | T15 | G5-19 | T25 | G6-19 | T22 |
| G4-20 | T11 | G5-20 | T02·T13 | G6-20 | T22·T25 |
| G4-21 | T15 | G5-21 | T21 | G6-21 | T21 |
| | | G5-22 | T15 | G6-22 | D-R |
| | | | | G6-23 | D-R |

합계: G1 22 + G2 20 + G3 24 + G4 21 + G5 22 + G6 23 = 132.
