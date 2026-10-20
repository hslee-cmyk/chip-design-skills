---
title: oracle-portability -- design 이력
design: oracle-portability.design.md
date: 2026-10-16
---

# oracle-portability design 이력

> design 본문(`oracle-portability.design.md`)에 넣지 않는 경위를 둔다. 현행 규칙은 본문이 정본이다.

## H1. 버전 경위

| 판 | 커밋 | 내용 |
|---|---|---|
| v0.1 | f8b9a69 | card OP-0 초안. 승인된 계획 v0.4.2(O-1·O-2, D-1~D-9) 기준, base `6093d07`. 독립 검증·사용자 승인 전 |
| v0.2 | (이 커밋) | 사용자 결정 O-3(DV-1 (가) 확정, DV-2 별도 card, X-D1·X-D2 수용)을 반영했다. offset-trim design TR-0T의 G-15 닫힘으로 PC-10을 정의했다(입력 `output_reference`). 사용자 결정 T-39로 DC 풀이 허용오차 선언을 강제(`dc_tolerance_undeclared`)하고, 입력 환산 전파값 `dc_resolution_in_V`(§13.4)를 결과에 낸다. X-D3 해소, X-D4 신설 |
| v0.2.1 | (이 커밋) | 사용자 결정 O-4("TR-0T 승인, X-D4 권고대로 해")로 X-D4 수용을 표시했다. 매뉴얼 원문 보관·쪽 번호는 OP-0 card 범위, 영향 측정은 OP-1이다. offset-trim TR-0T가 master에 병합돼(T-40) PC-10·`dc_tolerance_undeclared`의 대조 기준을 master `offset-trim.design.md` §20으로 바꿨다. v0.2 독립 검증 결과는 아직 반영하지 않았다 |
| v0.2.2 | (이 커밋) | v0.2 독립 검증 87점(차단 B-1, 비차단 N-1~N-9)을 반영했다. B-1: X-13 test를 `E/tests/` 아래 읽기 전용 test로 두고(계획 v0.5.1 8a 예외, `oport-plan-r2` `d9f37c4`), 중복 검사도 넣었다. 나머지: N-2 양 종류별 필요 허용오차 키 집합, N-3 매뉴얼 쪽 번호를 OP-2 병합 조건으로, N-4 PC-10 부호 규약 인용 정정(offset-trim 계획 N0.1·design §0 V_in(c))과 단일 출력 기준 셋 모두 `source`, N-5 PC-3 r 출처(`--rel-resolution` 필수)와 기록 지문의 n·r, N-6 오류 표에 `oracle_condition_missing`·`descriptor_source_duplicated`, N-7 §5 조기 종결 문장을 G-13과 맞춤, N-8 `oracle_capability`를 `oracle_run capability` 하위 명령으로, N-9 Summary 판 번호·O-3·O-4·nutmeg 대 `early_window` 독립 기준(b)·T1-4 실행 중 기록 측정, B-2·B-8 '결정(O-3)' 표시. 남은 'trim-design-r1 미병합' 문구 정리 |
| v0.2.3 | (이 커밋) | 재확인 95점(차단 0)의 문구 3건을 고쳤다: §0 값 원칙 '입력 `testbench.options`' → '`simulator.options` 또는 출처 있는 어댑터 보정값', §3.1 CLI 통합 '(기본안)' → '결정(O-3)', §19.1 B-9를 '계획 v0.5.1 8a 예외에 따름'으로 표시 |
| v0.2.3 승인 | (이 커밋) | 사용자 승인(2026-10-16 "모두 권고대로", 결정 기록 O-5). 독립 검증 87 → 95점(차단 0). Status를 '승인됨'으로 바꿨다. 본문 규칙 변경 없음 |
| v0.2.4 | `cbf06d1`(브랜치 `design/oracle-op0-v024`, base `1ba9461`) | 계획 v0.6~v0.6.2(사용자 O-6 D-a·D-b·D-c, 승인 O-7)와 OP-1 측정을 반영한 개정 초안. 독립 검증·사용자 승인 전. 경위는 H3 |
| v0.2.5 | `564245f`(브랜치 `design/oracle-op0-v025`, base `9069e10` + v0.2.4 병합 `9d7ee5f`) | v0.2.4 독립 검증 결함(B-1·B-2, M-1~M-6, 경미)과 계획 v0.6.3~v0.6.4(L-1·L-2·L-3·O-8) 반영 개정 초안. 새 멈춤 DV-4·DV-5. 경위는 H4 |
| v0.2.6 | `5d4a262`(같은 브랜치, master `52945ce` 병합 `dea6549`), 후속 `57c2a0f`·`e6fc0fc`(재검증 조건·경미, 계획 v0.6.6 diff M-1·M-2), `428f87e`(계획 v0.6.6 병합 `b21b4a9` 반영: plan_version 0.6.6·인용 갱신·머리 version 정정), 이 커밋(git 추적 기준 철회 → 계획 v0.6.6 문구 '디스크의 모든 파일 − 제외 목록', X-D6, abspath 표기) | v0.2.5 검증 중간 지적 다섯·경미 일곱, 소비자 미정 칸, 계획 v0.6.5(O-9·O-10)·v0.6.6(어댑터 지문 제외 목록 방식) 반영 개정 초안. DV-4·DV-5 닫힘, 새 멈춤 없음. 독립 검증·사용자 승인 전. 경위는 H5 |
| v0.3.0 | (이 커밋, 브랜치 `design/oracle-eo1`, base master `9401e98f`) | 계획 v0.6.9(O-48) 반영: DR-1~DR-17, OP-3 입력 스키마 계약(EO-1 계약)·G-18 확장 칸·실행 결과 계약, metric 측정 절차 §21(OP-5·OP-10·OP-11). 새 멈춤 DV-6~DV-9. 독립 검증·사용자 승인 전. 경위는 H6 |
| v0.3.1 | (이 커밋, 브랜치 `design/oracle-eo1`, base `1a1e6396` = master `d6bd02b1` 병합) | 계획 v0.6.10(O-57 승인) N7.5 DR-18 반영: 사용자 결정 O-50~O-55로 DV-6~DV-9·B-34·X-D7·X-D8·v0.3.0 결정 대기 목록 닫음(§19.2 'v0.3.1 닫힘 표'). `conduction_columns` 입력 칸 삭제 → 전도 두 단계(`conduction.points[]`, `PENDING_CONDUCTION`, `sweep_rezoom`), `declared_triode` → `intended_region` {triode, off}, `measure_feedback`(ICMR·슬루 구성, 반전 포트 `.tf` 부호), `slew.step_ends_V` 삭제·방향별 슬루, 계통 offset 부호 있는 V_id*·기준 종류 셋, 동일성 비교 상대 = OP-1b 추가 기준선. 새 멈춤 DV-10(슬루 확정 끝 전달 경로)·DV-11(단일 입력 `.tf` A). 새 기본안 B-44~B-46. 옛 문장은 본문에 '(v0.3.0 기록)'으로 남김. 독립 검증·사용자 승인 전 |
| v0.3.2 | (이 커밋, 같은 브랜치, base `5d6e7073`) | v0.3.1 독립 검증(`_drafts/evidence/2026-10-20/oracle_v031_validation.md` #1~#23) 가운데 O-58 DV-10·DV-11 계획 개정에 걸리지 않는 것과 O-58 B-45 반영. 본문 '(v0.3.0 기록)' 대체 문장을 H7로 옮김. 새 멈춤 DV-12(범위 최종 metric 재계산 주체)·DV-13(계통 offset 기준점). 독립 검증·사용자 승인 전. 경위는 H7 |
| v0.3.3 | (이 커밋, 같은 브랜치, base `7a77cd5a` = master `b9af2d6f` 병합 -- 계획 v0.6.11·gain-budget v6.21 승인 O-60) | '(O-58 계획 개정 대기)' 표지 6곳 해소, DV-10·DV-12(계획 G-19 네 검사·N3.9 '최종 범위 metric'·OP-10 실행 순서, O-58 DV-10·O-59 (3)) → §11.6 `confirmed_range`, §7 `range_pointer_rejected`·§7.2 2c, §11.7 `range_final`·`range_input_fp`, §21.2·§21.6; DV-11(계획 σ 행·DEC-23 A_dc, O-58 DV-11) → §21.5; DV-13(DEC-23 '이동의 기준점', O-59 (4)) → §11.6 `dc_sweep.input_dc`, §7 `input_dc_undeclared`, §21.4 3단계(free servo 해 빼기 삭제). B-46에 v0.3.2·v0.3.3 이름 기록, §21.3 대상 출처를 O-54로 바로잡음(O-56은 술어 하나만). 새 멈춤 DV-14(\|A\| ≤ 판정 분해능)·DV-15(입력 DC 두 칸). 독립 검증 대기·사용자 승인 전 |

(v0.2.6 번호 정리: 절을 판 순서대로 H2 작성 → H3 v0.2.4 → H4 v0.2.5 → H5 v0.2.6으로 놓았다. 옛 'H6'(v0.2.5)는 H4다. design 본문 Status의 인용도 같이 고쳤다.)

## H7. v0.3.2 경위 (2026-10-20) -- 판 순서상 H6 뒤에 읽는다(편집 제약으로 여기 둠)

- 기준: design v0.3.1 `5d6e7073`, 계획 v0.6.10, 사용자 결정 O-58(B-45 확정 -- ICMR 공칭 점 차 거부·`nominal_output_shift_V` 칸 없음). DV-10·DV-11은 계획 v0.6.11 개정 대기라 본문에 '(O-58 계획 개정 대기)' 표시만 했다.
- 고친 것: 검증 #1(점 기록 `m`·`VGS`, 창 값 `provisional`, 공칭 점 꺼짐 주체 -- 재계산 주체는 멈춤 DV-12), #2, #3(OP-10 행 계단 끝 부분 제외), #4, #5, #6, #7, #8(계단 끝 부분 제외), #9, #10, #11, #12(인용 줄 위치만, 따옴표 문구 재대조는 남음), #14, #15, #16(B-45 = O-58), #17, #18, #19, #20, #21, #22, #23(gain-budget 인용 줄을 `7fe555b1`과 현 tree로 다시 잼: 스윙·소자 조건 563/564, 슬루 564/565). #13은 계획·DEC-23이 기준점을 정하지 않아 멈춤 DV-13.
- **본문에서 옮긴 대체 문장**(v0.3.0 판, 원문 그대로):
  * §11.6 `/declared_triode` 행: spec 선언 triode 소자(spec `intended_region == "triode"`, headroom-chain N3.6). 쓰는 곳(v0.3.0 검증 지적 3으로 고침 -- 두 판정의 정의가 다르다): **범위 판정**(swing·ICMR, §21.2)은 소자 조건 전체(전도·포화 둘 다)에서 뺀다(gain-budget N3.8 556행 '소자 조건 = spec 선언 triode 밖 모든 MOS가 전도이고 포화'). **합격 판정**(§21.3)은 포화 확인에서만 빼고 영역(SPICE VDS 대 VDSAT)을 기록하며(HC-O), **전도(꺼짐) 확인에는 남긴다**(DEC-90 (1) '꺼짐 판정은 선언 triode를 포함한 모든 MOS'). 형식 string 배열, 규칙 원소 ∈ `devices[].name`(아니면 `rule = declared_triode_unknown_device`).
  * §11.6 `/conduction_columns/<device>` 행: 형식 객체(닫힘) `{tol_v: {vds_grid_V: number 배열(길이 ≥ 2, 엄격 증가), rows_V: ((number \| null) 배열(길이 = 격자 길이)) 배열(행 1개 또는 2개)}, i_off: <§19.2 DV-6 결정 대기>}`, 필수(모든 `devices[]`, 선언 triode 포함). 판정 점 ε = (gm/ID)·tol_V의 tol_V 열과 I_off 열(계획 N3.9, 사용자 결정 O-46 (2)). **tol_v 직렬화 규칙**(EO-1 갱신 커밋이 지킴, 출처 = LUT 파생표 `tol_v_table(kind, w_key)`, 지표 `id_equivalent`, S-41): `vds_grid_V` = 그 표의 VDS 격자, `rows_V` = 그 소자 L의 행들(L이 앵커면 그 앵커 행 하나, 같은 bin 보간이면 양옆 앵커 두 행)의 셀 값 `id_equivalent_v`를 행 그대로(정의 없으면 null). 동작점 스칼라 `device.dc_tol_v`와 다른 양. 규칙 `conduction_columns_devices`·`conduction_columns_shape`.
  * §11.6 `/output_reference` 행: 엔진 DEC-23 기준값(선언 출력 목표 = spec `node_voltage_targets_v`, 쓰기 계획 W3 `REL_TARGET`; 차동 출력 = V(p) − V(n) = 0이라 입력 칸 불필요, 계획 G-18). **(v0.3.0 gap 지적으로 제한) 계통 offset(§21.4)이 받는 종류는 DEC-23이 적은 둘뿐이다**: 단일 출력 `net_value`와 차동. `net`·`rule_e_input_cm`은 계통 offset 요청에 오면 `reference_undeclared`(`detail.why = kind_not_in_dec23`)로 거부한다. **이 칸을 PC-10(offset-trim G-15)과 같은 칸으로 쓰는 판단은 보류(결정 대기)** -- 근거 기록 전까지 PC-10 쪽 사용은 OP-6에서 다시 정한다. (v0.2 §11.1에 있던 칸을 v0.3.0에 여기로 옮김 -- 계획 G-18이 확장 칸으로 분류)
  * §11.6 `/slew` 행: `feedback` = spec에 사용 구성(β) 선언이 있으면 `declared`(입력 회로·`feedback_passives`가 그 구성), 없으면 `unity_follower`(β = 1, 결과에 'β = 1 기본' 표기). `step_ends_V` = 계단 끝(O-28 '입력을 허용 입력 범위 끝까지 미는 방향별 계단') -- 값의 출처는 §19.2 DV-9 결정 대기. 정의 정본 = gain-budget N3.8 557행.
  * §11.6 'OP-5 병합 때 지우는 칸': `judge.off_current_A` 삭제는 계획 문언이 갈려 결정 대기였다: judge 칸도 전도 정의(옛 swing·compare의 `|ID| > off_current_A`, S-40)에만 쓰이고 새 정의가 그 자리를 대체하므로, 남기면 소비자 없는 칸이 된다(만들면 배선·소비자 없는 칸 금지).
  * §19.2 결정 대기 목록(v0.3.0 둘째 커밋): DV-6, DV-7, DV-8, DV-9, B-34(`judge.off_current_A` 삭제 문언), OP-10 선행·착수 조건, X-D7(B-29 닫힌 키 집합), X-D8(B-33 거부 기록), §21.1 2단계 ID 부호 규약, §21.2 개루프 ICMR 해석, §11.6 `output_reference`를 PC-10과 같은 칸으로 쓰는 판단, §21.5 단일 입력 회로의 `.tf` A(`unavailable` 유지 여부).
  * §19.2 알림: ~~(v0.3.0) DV-6 (가)가 채택되면~~ 엔진 LUT 보간 규칙(`E/lut/_helpers_interp.py`, `E/lut/point_query.py`)을 바꾸는 card는 오라클 I_off 읽기 사본과 그 test 기대값을 같은 변경에서 고친다(DV-6 (가) 기각으로 불필요).
  * §20 OP-3 행: **병합 조건 (b)는 §19.2 DV-7 결정 전에는 실행할 수 없다**(기준선 입력 LUT에 모델 기록 없음, S-39).
  * §20 OP-5 행 착수 조건: (v0.3.0) §19.2 DV-6 결정(I_off 열 읽기 규칙 -- 전도 판정 전 부분), DV-8 결정(계통 offset 부분). 계획 U-4의 '정의 확정' 조건은 부분 충족: gain-budget N3.8 v6.18 정의 문장은 승인됐지만(O-48) 계통 offset의 부호·크기·단일 입력(DV-8)과 I_off 조회 규칙(DV-6)이 문장에서 닫히지 않았다. 확장 칸 목록 `declared_triode`·`conduction_columns`. OP-10 행: DV-9 결정 대기.
  * §21.1 2단계: **결정 대기**(v0.3.0 gap 지적): 이 단계는 ID의 부호 규약에 기댄다. 정의 인용 출처는 엔진 `E/sizing/seal_conduction.py:6`('ID > 0 인 모든 MOS(전도)')와 DEC-90 (1)('I_off > ε·|ID|' -- 절댓값)인데 두 문장의 ID 부호 처리가 다르다. 오라클 ID는 크기 규칙 + 선언 단자 방향 부호(`signed_id`, `O/oracle_compare.py:226-232`)다.
  * §21.1 3단계 tol_V(점) = `conduction_columns.<소자>.tol_v` 읽기: 격자 g(길이 N), VDS가 [g[0], g[N−1]] 밖이거나 NaN이면 `conduction_undefined`(엔진 `check_axes`, `E/lut/axis_guard.py:8-18`), 칸 k = min(bisect_right(g, VDS) − 1, N − 2), tol_V = `rows_V`의 모든 행 r에 대해 {r[k], r[k+1]} 가운데 null 아닌 값의 최댓값, 모두 null이면 `conduction_undefined`. 엔진 `table_at`(`E/lut/_helpers_loo.py:153-163`)과 같음(S-41, test 작성자 2행 표 손 예). 4단계 I_off(점) = 열 읽기(DV-6 결정 대기).
  * §21.1 7단계 '선언 triode'(`declared_triode`, v0.3.0 검증 지적 3): 범위 판정(§21.2)에서는 소자 조건 전체(전도·포화)에서 뺀다(N3.8 556행). 합격 판정(§21.3)에서는 포화 확인에서만 빼고 전도(꺼짐) 확인에는 남긴다(DEC-90 (1)).
  * §21.2: v0.3.0의 'servo 없이 차동 0을 유지하는 개루프 벤치' ICMR 해석(swing 벤치는 현행 규칙으로 본문에 남김). 점 판정 '§21.1 소자 조건(선언 triode 밖 모든 MOS 전도 ∧ 포화, 여유 0)'. 공칭 점 차: ICMR도 y = 0 점 차를 `nominal_output_shift_V`로 기록(v0.3.1 B-45 초안 -- O-58로 칸 없음). 결과 칸 `rail_filter_end = true`, 창 기록 `{x_lo, x_hi, m_lo, m_hi, bracket_width, rounds, resolution, hit_rail}`. 판정 '알려진 원인 후보'(개루프 해석 전제): 고이득 개루프 회로에서 입력을 이상 전원으로 묶으면 공칭 출력은 servo 해와 거의 같지만, 입력 공통모드를 움직일 때 계통 offset의 공통모드 의존 × 차동 이득만큼 출력이 움직여 ICMR 창이 옛 servo 고정 방식보다 좁게 나올 수 있다 -- O-25 (2)의 결과이고 절차 결함이 아니다.
  * §21.3: 대상 = 엔진 전도 예측 소자(`predictions.devices.<n>.region` ≠ `"off"`, 칸이 없으면 전도 예측 -- 옛 C23 규칙). §21.1 전도식으로 꺼짐(I_off > ε·ID 또는 ID ≤ 0)이면 `FAIL`(옛 `off_spice` 자리), `conduction_undefined`면 `INCOMPLETE`. 포화 확인 대상(v0.3.0 검증 지적 5): spec 선언 triode 밖 SPICE ID > 0인 모든 MOS(gain-budget N6.2 T4 1193행, U-46). HC-O 입력 칸 `declared_triode`.
  * §21.4: 'DV-8'·`kind_not_in_dec23`·'PC-10 결정 대기' 문장. 1단계: `net`·`rule_e_input_cm`은 DEC-23에 없어 `reference_undeclared`(`why = kind_not_in_dec23`); 기준 칸을 PC-10과 같은 칸으로 쓰는 판단은 결정 대기.
  * §21.5: 단일 입력 회로 = 옛 MC 정의(V_id = 차동 입력 차, `O/oracle_offset_mc.py:117-119` -- 차동 쌍 없으면 `unavailable`)를 그대로 둘지 일반형으로 넓힐지 결정 대기.
  * §21.6 절차(DV-9에 걸린 부분 밖) 1·2단계: `slew.feedback = "declared"`면 입력 회로 그대로, `"unity_follower"`면 출력을 반전 입력에 잇는 이상 연결(단일 출력 회로: `ports.input_n` ← 출력, 이득 1 VCVS); 결과 `slew.beta_default = (feedback == "unity_follower")`. 계단 `Pulse(v1 = 동작점, v2 = step_ends_V.up)`·`step_ends_V.down`. 결과 `slew.{up, down}`.
  * §18.1 OP-5 정의 대조 행: §21.1 tol_V 읽기 규칙(2행 표 손 예), §21.1 깨진 변형(ε = 1, 동작점 값, 꺼진 소자 제외, 여유를 정의에, None을 통과로), §21.3 'ε < 1 손 예에서 옛 식 PASS·새 식 FAIL', 선언 triode 두 경우 단언. 결과 계약 행 `seal9_point_lut`.

## H2. 작성 경위 (2026-10-16)

- 지시: 오케스트레이터 'oracle-portability card OP-0(design) 작성'. 범위는 계획 OP-0이다(G 항목 중 OP-0 몫, 형식·스키마·PC 벤치·진단 배선·파일 분할·삭제 목록·test 목록·상위 문서 개정 문안). OP-1 측정이 필요한 칸은 '측정 대기'로 두고, 계획과 다른 결정이 필요하면 멈추고 보고한다(S-7).
- 읽은 것(base `6093d07`):
  - 오라클 8개 파일의 함수·상수 목록
  - `oracle_run.run_one`, `simulate` 결과 칸, `offset_mc_measure` 전체(표본 RNG 순서·V_os 식)
  - 입력 스키마 최상위 칸, `oracle_config.json`
  - smoke 입력 `process` 블록(pmos `lod.spice` include)
  - 엔진 선언 `sources` 목록
  - offset-trim v0.5.5 G-14(닫힘, T-35)·G-15(열림)·N6 오라클 확장 목록
- 실행: 코드 실행·ngspice 실행 없음.
- 멈춤 항목: DV-1(엔진 선언에 없는 include 파일, 계획 N3.4 단일 정본과 D-9의 충돌)과 DV-2(상위 문서 개정 미반영, 구현 card 착수 조건)를 본문 §19.2에 올렸다. DV-1은 임시안만 적고 확정하지 않았다.

## H3. v0.2.4 경위 (2026-10-16)

- 지시: 오케스트레이터 'OP-0 design 개정 v0.2.3 → v0.2.4'. 반영 대상 셋: (1) 계획 v0.6/0.6.1/0.6.2 변경 전부 (2) OP-1 측정 뒤 미뤄 둔 design 항목 (3) v0.2.3 검증자 정리 둘(§20 OP-2·OP-5 겹침, offset-trim N3.9-3 재대조). 계획과 다르게 가야 할 것은 정하지 말고 멈추고 보고(S-7), as-built·범위 결정 금지.
- 읽은 것:
  - 계획 v0.6.2 전문과 history v0.6~v0.6.2 절(`1ba9461`)
  - OP-1 산출물 `wt/_scratch_op1/results/`: `m1_native_mc.jsonl`(18행), `m2_m3_lut_meta.jsonl` 41행, `m7_gain_imag.json`, `m8_errlog.json`·`.console.txt`, `g8_check.json`, `g13_window_cost.json` `aggregate`, `m6_xd4_scan.json`, `m13_mc_replay.jsonl`, `n4_convert.jsonl`. 스크립트 `scripts/g13_window_cost.py`·`m6_xd4_scan.py`·`g8_check.py`, 검증자 초안 `n4_convert_input.py`·`g8_dialect_tokens.draft.json`
  - 다시 잰 코드 위치(base `1ba9461`): `O/oracle_compare.py:38, :228, :379, :708`, `O/oracle_swing.py:306`, `O/smoke/u6_selfchecks.py:136`, `O/legacy_adapter.py:191-192, :261-264`, `O/oracle_netlist.py:145-153`, `O/oracle_offset_mc.py:22-24, :137`, `O/oracle_input.schema.json` `process`, 모델 카드 `…nfet_01v8__tt.pm3.spice:16-30, :67`, `models/all.spice:2`, `E/lut/CONTRACT.md:887, :951`, offset-trim 계획 master v0.5.6 N3.9 466-477행
  - `O/` 코드가 `6093d07`과 같음을 `git diff --stat`으로 확인(README 2줄만 다름)
- 실행: 코드 실행·시뮬레이터 실행 없음(OP-1 산출물 읽기와 grep만).
- 판단 근거 몇 가지:
  - `1e-3`: v0.2.3 §14의 `data_rel` 대체안(B-7)은 계획 D-c가 뒤집었다(측정 170건 뒤집힘). 기본안 B-7을 철회로 표시하고 NFR-P2 예외로 옮겼다.
  - 진단 `value_rule`의 `z·1e-6/√m`: 기하 단위·병렬 배수를 소자 줄에서 전달하면(D-b) 이 배율이 두 번 들어간다. 계획 N3.6 삭제 목록(배율 삭제)대로 기술자 식에도 옮기지 않게 고쳤다.
  - 분포 값 sha256 불일치는 이미 있는 `pdk_descriptor_stale`로 낸다(같은 사실에 코드 둘을 만들지 않음).
  - `lut_reference_width_m`·`provenance`: 오라클 본체 grep 0이라 새 형식에서 지운다. `legacy_adapter`의 기준 폭 대체값이 함께 없어지므로 dump 값만 쓰고 없으면 막힘(조용한 대체 금지).
  - 상위 문서 개정 card `gb-oracle-rev`가 `b105b65`로 병합돼 있어 §1.3·§20 OP-2·§19.2 DV-2에 충족을 적었다.
- 멈춘 항목: DV-3(계획 N3.5 (ii)·N4 MC 수학 '끝까지 비트 동일'과 D-b 넷리스트 변화의 충돌). 권고 (가)는 적었지만 정하지 않았다.
- 알림(다른 문서 소유): 계획 N3.5.1 기준 커밋 문구, offset-trim N3.9 '순서 의존'의 '초안' 문구, `b105b65` 병합본 대 §17 문안 미대조.

## H4. v0.2.5 경위 (2026-10-16)

- 지시: 오케스트레이터 'OP-0 design 개정 v0.2.4 → v0.2.5'. v0.2.4(`cbf06d1`)가 master에 없어 worktree `wt/oracle-op0-v025`에서 `design/oracle-op0-v024`를 `--no-ff`로 병합(`9d7ee5f`, 충돌 없음)한 뒤 개정. 기준 계획 v0.6.4(승인). 계획과 다르게 가야 할 것은 정하지 말고 멈추고 목록으로(S-7), as-built 결정 금지.
- 반영 (A) v0.2.4 독립 검증(오케스트레이터 전달):
  - B-1 모델 묶음 비교 → 계획 X-22 역할 구분(§12.5 다시 씀: 역할 선언 출처, 옆 선언 형식 `lut_file_roles/1`, 근거 두 측정, 규칙 (i)~(iii), `lut_aux_input_mismatch`, 기술자 `lut_record_root`·`lut_file_roles`, OP-3 병합 (c))
  - B-2 §18.1 완료 조건 4에 PC-10 깨진 변형 셋과 `reference_undeclared` 거부
  - M-1 결과 칸 개명: 생산자 10곳·소비자를 다시 재고(S-23) §11.5 경로별 대응·`None` 처리 표, `method` 값(S-24)
  - M-2 실행 전 검사 순서 §7.2와 OP-3 (a) 양성 대조
  - M-3 '차이가 선언에서만' 판정 절차(§10.6: 기준선에 선언 변환 → 정규화 → 남은 차이 0)
  - M-4 삭제 모듈 소비자 §15.4(smoke 넷, conftest 장치, 엔진 test 하나 → DV-4)
  - M-5 §7.1 회복된 경고(S-30 로그 근거), pz 요청 단위 오류, 주입 로그 test
  - M-6 계획 X-20대로 기술자 `requires` 삭제, 코어 고정 요구(§10.4)
  - 경미: `geometry_unit_unsupported` 삭제(기존 코드로 합침), `mc_distribution_inline` 닫힌 키 집합, `descriptor_schema_invalid`, `pdk_descriptor_stale` detail, 4a 인스턴스 기하 = 보고 원값 대 test 계산 기대값(`instance_geometry_reported`), T1-0 D11 연기를 계획 X-23 단계 규칙으로, abstol 출처(S-28), 인용 정정(m1 12행 §12.3·§19.3, S-22, Status의 'H1 v0.2.4' → H3)
- 반영 (B) 계획 v0.6.3/v0.6.4: 생산자 0(§3.1·§11.4·§15.1·§18.2·§19.1 B-13 철회·§19.3·§20 OP-2), OP-1a(§13.2·§18.1·§20), DV-3 = O-8 (가-1)(가-2)(§13.2·§10.5·§19.2), OQ-4(§13.2), X-23(§18.1 T1-0)
- 다시 잰 것(base `9069e10`): `git grep` `ngspice_rc|ngspice_runs`, `O/oracle_simulate.py:401-402, :777-812, :1025-1067, :1105-1118, :1170-1202, :1230-1252, :1270-1320`, `O/oracle_noise.py:114-151, :294`, `O/oracle_offset_mc.py:109-196`, `O/oracle_swing.py:105, :306`, `O/smoke/*.py` import, `O/tests/conftest.py:36-51`, `E/tests/metrics/test_verified_by.py:1-65`, `A/sky130_lut_sweep.py:231-232, :680-695, :885-895`, `A/sky130_pdk_decl.json` `pdk_root`·`sources`, `E/lut/provenance.py:1-20`, `R/m1_native_mc.jsonl` 18행, `R/m13_mc_replay.jsonl`, `scripts/m13_mc_replay.py`, `R/m8_errlog.json`, 기준선 로그 `cmfb0/out/tcm_cmfb.free.cmloop.pz.log`·`mc5t0/o/t5ota.free.mc.log`, `R/m2_m3_lut_meta.jsonl`(38 슬라이스 중 32 `.bins.csv`), offset-trim 계획 N3.9 459-477행. `1ba9461..HEAD`의 `O/` 차이 0.
- 실행: 코드·시뮬레이터 실행 없음(읽기·grep·작은 JSON 집계만).
- 멈춘 항목: DV-4(엔진 test가 최상위 `oracle_*.py`를 glob, 완료 조건 8a와 충돌), DV-5(기준선에 표본별 V_os 칸 없음, (가-1)(가-2) 표본별 비교의 기준값 미정).

## H5. v0.2.6 경위 (2026-10-16)

- 지시: 오케스트레이터 'OP-0 design v0.2.5 → v0.2.6'. 같은 worktree에서 master `52945ce`(계획 v0.6.5, 사용자 O-9·O-10)를 `--no-ff`로 병합(`dea6549`, 충돌 없음)한 뒤 개정. 계획과 다르게 가야 할 것은 멈추고 목록으로.
- 반영 (A) v0.2.5 검증 중간 지적 다섯:
  1. §11.5 실행 전 반환 경로(S-31)의 사유 대응표 규칙, 옛 상태 칸 `log`·`log_errors`·`op_ok`·`skipped`·`cache`·`stability_cache`와 `RunStatus` 대응·소비자(S-32), 시뮬레이터 이름이 든 사유 문장(S-33)
  2. B-18 `lut_record_root` → 기존 정본 `A/lut_v2_location.json` `pdk_root` 참조(S-35, 엔진 무변경)
  3. 어댑터 지문 = 제외 목록 방식(§0, §8.3), 측정 도구 폴더 `calibration_tools/`(B-25), §3.2 import 방향
  4. `u6_selfchecks.py`의 conftest 소비와 conftest 옛 형식 입력 생성기·`make_lut`(S-34)를 §15.4·§18.2·§20에, u6 삭제 = O-10 승인, 삭제 card를 OP-3으로 고침
  5. §7.2 `lut_record_root` 교차 검사 = 8단계 `lut_record_root_mismatch`(값 불일치), `pdk_descriptor_stale`를 2단계 하나로
- 경미 일곱: §10.6 지시 줄 값·문법 출처와 `name_map` 의존 기록, §13.2 재구현 스크립트 표기, offset_mc 옛 rc 비교 제외(P-1) + `n_failed`, §7.1 주입 증거 단계 = B-24, B-20 '승인됨', history 번호 정리(H2를 앞으로, 옛 H6 → H4, 이 절 H5)·§19.3 머리, 엔진 쪽 낡은 인용 알림(S-36)
- 소비자 미정 칸: §6.1 신설(칸마다 소비자 또는 출력 전용). `RunStatus.cache_hit: bool`을 `cache_state` 넷 값으로 바꿈(옛 `'off(…)'` 상태, `O/oracle_simulate.py:105-110`), `mc_identity_lost` 새 코드, 시드 적용 = 5단계 능력 확인
- 반영 (B) 계획 v0.6.5: DV-4·DV-5 닫힘(§19.2), 8a 예외 둘째 행(§18.1), 기준선 표본별 V_os(§13.2), (d) 선택 대조 = `run_ngspice` 이름 교체 경로, conftest 손 넷리스트 기준 경로 `O/tests/adapters/ngspice/`
- 다시 잰 것(base `52945ce`, `9069e10..HEAD` `skills/` 차이 0): `O/oracle_noise.py:114-130`, `O/oracle_offset_mc.py:109-196`, `O/oracle_simulate.py:86-125, :1025-1060, :1084-1170, :1270-1320, :1369-1375`, `O/oracle_compare.py:374-390`, `O/oracle_run.py:40-60`, `O/tests/conftest.py`, 캐시 단언 test 넷, `A/lut_v2_location.json`, `E/lut/data_location.py:32-41, :58-83`, `git grep spice_oracle -- '*.py'`(엔진 쪽 인용)
- 실행: 코드·시뮬레이터 실행 없음.
- 멈춘 항목: 새 멈춤은 없다. 단 **계획 v0.6.6 개정 대기**(어댑터 지문 제외 목록 방식, 브랜치 `plan/oracle-v066` `c62f3bf`·`16af2cf` 미병합) -- §19.2 '개정 대기'. 같은 판 후속 커밋 `57c2a0f`(재검증 '승인 가능' 조건 1 + 경미 4, 계획 v0.6.6 diff 확인 M-1·M-2): 대기 표시, `lut_record_root` 규칙 출처 = `E/lut/CONTRACT.md` 1.8(256-261행, `os.path.abspath`)·의도된 엄격·X-D5, `n_failed` = 옛 정의(결과 없는 표본 수, rc는 `sample_status`만), §15.1·§11.5 u6 소비자 서술과 OP-3~OP-5 점검 공백, `lut_location_decl_invalid` 분리, 지문 파일 집합(git 추적·상대 POSIX 경로 정렬)·정규 JSON 규칙·`adapter_fingerprint_unavailable`(B-28).
- 개정 대기 해소: 계획 v0.6.6이 master `7edd723`으로 병합됨(사용자 X-22 승인) → worktree 병합 `b21b4a9` 뒤 `plan_version` 0.6.6, §0·§8.3·§12.4 인용 v0.6.6, §19.2 대기 줄 '해소'. 같은 커밋에서 머리 front matter가 `version: 0.2.5`·`plan_version: 0.6.4`로 남아 있던 것(v0.2.6 개정 때 Edit 실패, 미확인)을 `0.2.6`·`0.6.6`으로 고쳤다. X-D5는 사용자 확인 항목으로 그대로 둔다.
- diff 확인 '수정 필요'(중간 1, 경미 3) 반영: 오케스트레이터 결정(계획 문구 복귀)으로 B-28의 git 추적 파일 기준과 '추적 판정 불가 시 거부'를 철회하고 지문 파일 집합을 계획 v0.6.6 문구 '어댑터 패키지 아래 디스크의 모든 파일 − 닫힌 제외 목록'(순수 파일 열거)으로, 재현성 메모 §19.4 X-D6(잔여 파일 → 기록 무효·재생성, 의도된 엄격), §18.1 '기록 뿌리 해석' abspath를 env 값·default 둘 다에, H1 v0.2.6 행에 후속 커밋.

## H6. v0.3.0 경위 (2026-10-20)

- 기준: 계획 v0.6.9(master `9401e98f`, 사용자 O-48 승인). worktree `wt/design-oracle-eo1`, 브랜치 `design/oracle-eo1`. `52945ce`와 `9401e98f` 사이 `O/` 차이 0을 확인해 앞 판의 `O/` 줄 인용을 그대로 두었다.
- 지시: 계획 N7.5 design 개정 대상 DR-1~DR-17과 v0.6.9가 남긴 미결(G-18·G-19, EO-1 범위·갱신 경로, `.tf` 개루프 벤치, 합격 판정 전도 기준과 값의 출처, 손분석 입력 경로, OP-11). 우선순위: OP-3 입력 스키마 계약(EO-1 계약)을 먼저 test 작성자가 소스 없이 쓸 수 있는 수준으로, 그다음 OP-5·OP-10·OP-11.
- 다시 잰 것(S-37~S-46): 기술자 참조 파일 셋의 raw·LF sha256(Python), LUT v2 폴더 38개 파일의 meta 모양(폭 슬라이스 평탄·결합 파일 중첩, VGS 축 첫 값 0), 기준선 입력 593개의 `lut_npz`(모델 기록 없음), 스키마 밖 키, 기준 레일 전압, ngspice-46 `.tf` 차동 출력(scratchpad `oracle_design/tf_diff.cir`·`tf_ctrl.cir`), 오라클 `oracle_swing`·`oracle_compare`·`oracle_offset_mc`·`oracle_run` 줄, 엔진 `seal_conduction`·`tol_v_table`·`table_at`·`op_point`·`node_values`·`check_axes`·`offset_systematic`·`supply`.
- 바뀐 절: 머리(version 0.3.0, plan_version 0.6.9, Status), §0 용어(기술자·어댑터 지문 = LF 정규화, 새 용어 넷), §1.1(O-13 (5)~O-48), §2(S-37~S-46), §3.1·§3.2·§3.3, §5(`Tf`), §6·§6.1(`TransferResult`, `bundle_files`, `machine_dependent_refs` 등), §7(새 코드, DR-4·DR-10b), §7.2(1단계 세부, 2b단계, 8단계 교차 검사), §8.1·§8.3·§9, §10.1~§10.3(DR-6~DR-8·DR-16), §11 전부(OP-3 입력 스키마 계약 §11.0~§11.4, 변환표, G-18 확장 칸 §11.6, 실행 결과 계약 §11.7), §12.2·§12.4·§12.5·§12.7, §13.2, §14, §15.1·§15.3·§15.4, §16, §18.1·§18.2, §19.1(B-29~B-43)·§19.2(DV-6~DV-9, 알림)·§19.3·§19.4(X-26~X-33 인용, X-D7·X-D8), §20, §21 신설.
- 철회한 앞 판 결정: §14·§13.2·§15.1의 '차동 이득 실수 판정 `1e-3`은 값·동작 그대로 `core/mc_math.py`로 옮긴다(O-6 D-c)' -- 계획 v0.6.9 O-43 D1 (d)로 상수와 `.ac` 첫 점 경로를 지운다. §11.1의 `output_reference` 칸 -- G-18 확장 칸(§11.6, OP-5)으로 옮겼다. §11.4 '저장소 안 생산자는 0' -- EO-1 병합 전까지의 사실로 좁혔다. OP-2의 입력 형식 전환·conftest 입력 생성기 전환·스키마 적합 test 전환 -- OP-3으로(O-14 (4) J-1 (나)). §18.1 '기록 뿌리 해석(OP-2)' 행의 `lut_record_root_mismatch` 항목 -- OP-3 행으로(J-5 (가)).
- 멈춘 항목: DV-6(I_off 열 형식·읽기 규칙 -- 엔진 `op_point` 보간을 사본으로 다시 쓸지), DV-7(기준선 입력 LUT에 모델 기록 없음 -- OP-3 병합 조건 (b)·N4 변환 실행 불가), DV-8(`offset_sys_mv` 부호·크기·단일 입력), DV-9(슬루 계단 끝·방향 묶음·차동 β = 1). 넷 다 권고안을 적었고 고르지 않았다.
- 실행: 코드 변경 없음. ngspice 작은 넷리스트 둘(`.tf`)만 실행.
- 같은 판 둘째 커밋 `a5cc59a7`(첫 커밋 `8f98bca0` 위): 독립 검증 '수정 필요'와 design↔계획 gap(약 88%) 가운데 계획 결정과 무관한 것을 고쳤다 -- E10 두 칸 함께 바꿈과 픽스처 전제(E13·E17·E18), K-4·S-40 다시 씀(C23 전도 확인은 소자별 칸만, `judge.off_current_A`는 표시·포화 대상 선택용 문턱), 선언 triode의 범위 판정(전도·포화 모두 제외)과 합격 판정(포화만 제외) 구분, §21.3 포화 확인 대상(T4)·`region_spice` 표시, §21.2 `nominal_output_shift_V` 확인과 레일 밖 노드 필터를 판정 단계 필터로, §7.2 막힘 단계, `oracle_input_schema_invalid` detail 형식, `dc_sweep.common = null` 규칙, `record_id` 빼는 칸과 불변식, `lut_model_provenance_missing` 두 경우, §14 표 정리, `.tf` 여기 가중 = `dc_sweep.excite`, tol_v 직렬화 = 행 그대로, `output_reference` 계통 offset 종류를 DEC-23 둘로 제한, §20 OP-5 U-4 '부분 충족', B-37 acceptance 근거. 계획 개정이 필요할 수 있는 것은 고치지 않고 '결정 대기'로 표시했다(§19.2 결정 대기 목록). 검증 지적 12('§11.1 보충 (a)~(e)')는 지시 문면에 내용이 없어 손대지 않았다. 이 줄은 셋째 커밋에서 더했다.
- 같은 판 넷째 커밋: 검증 지적 12의 내용(오케스트레이터가 뒤에 보냄)을 §11.1 '칸 표 보충' (a)~(e)로 반영했다 -- 같은 kind 여러 LUT 파일 = 기록 합집합, `topology.sha256` 형식·규칙 (ii) 대조, `passives[].value` > 0·`not_measurable` 형식, `L`·`finger_w` > 0은 스키마 규칙(기준선 6개는 문자열·누락 C13 거부 test라 결과 같음), `circuit` 패턴. 기준선 593개 스캔으로 영향 0을 확인했다. S-44 문구를 같은 사실로 고쳤다.
- **옮긴 옛 Status 문장**(v0.2.6 판 머리에 있던 그대로, 본문에서 지움):
  * v0.2.6: master `52945ce`(계획 v0.6.5, 사용자 O-9·O-10)를 병합(`dea6549`)한 뒤 두 묶음을 반영했다. (A) v0.2.5 검증 중간 지적 다섯과 경미 일곱: 실행 전 반환 경로·옛 상태 칸(`log`·`log_errors`·`op_ok`·`skipped`·`cache`)의 대응과 소비자(§11.5), `lut_record_root`를 기존 정본 `A/lut_v2_location.json` 참조로(§10.2), 어댑터 지문 제외 목록 방식과 지문 밖 측정 도구 폴더(§0, §8.3), conftest 옛 형식 입력 생성기·`u6_selfchecks` 소비자(§15.4·§18.2·§20, u6 삭제는 O-10 승인), §7.2 교차 검사 단계·코드와 `pdk_descriptor_stale` 중복 정리, 새 칸마다 소비자 또는 출력 전용 선언(§6.1 신설). (B) 계획 v0.6.5: DV-4 = O-9 8a 예외 둘째, DV-5 = O-9 기준선 표본별 V_os 재계산값(§13.2·§19.2 닫힘), 어댑터 지문 범위. 새 멈춤 없음. 경위는 history H5.
  * v0.2.5(`564245f`): v0.2.4를 병합한 뒤 두 묶음을 반영했다. (A) v0.2.4 독립 검증 결함(차단 B-1·B-2, 비차단 M-1~M-6, 경미): 모델 묶음 비교의 LUT 기록 역할 구분(§12.5), 완료 조건 4의 PC-10 거부 test(§18.1), 결과 칸 개명의 경로별 대응(§11.5), 실행 전 검사 순서(§7.2), 소자 줄 차이 판정 절차(§10.6), 삭제 모듈 소비자(§15.4), 오류 대응표 보완(§7.1), MC 표본 성질 배치(§10.4) 등. (B) 계획 v0.6.3~v0.6.4 변경: 저장소 안 입력 생산자 0(§11.4), OP-1a 기준선 보관(§13.2·§20), DV-3 = O-8 (가-1)(가-2)(§13.2), 토큰 증거 단계 규칙 X-23(§18.1). 계획과 다른 결정이 필요한 곳 둘을 §19.2 DV-4·DV-5로 올렸다(멈춤, v0.2.6에서 O-9로 닫힘). 경위는 history H4.
  * v0.2.4: 계획 v0.6~v0.6.2(O-6 D-a·D-b·D-c)와 OP-1 측정 반영 초안. 멈춤 DV-3은 사용자 결정 O-8(계획 v0.6.3)로 닫혔다. 경위 history H3.
  * v0.2.3: 사용자 승인됨(2026-10-16 "모두 권고대로", 결정 기록 O-5). 독립 검증 87 → 95점(차단 0).
  * v0.2.2: v0.2 검증(87점, 차단 B-1, 비차단 N-1~N-9)을 반영했다. B-1은 계획 v0.5.1의 완료 조건 8a 예외(`oport-plan-r2` `d9f37c4`)를 따른다.
  * v0.2.1: 사용자 결정 O-4("TR-0T 승인, X-D4 권고대로 해")로 X-D4를 수용했다. offset-trim TR-0T design이 master에 병합됐다(T-40). 그래서 PC-10과 `dc_tolerance_undeclared`의 대조 기준은 master `offset-trim.design.md` §20이다.
  * v0.2 반영 1: offset-trim design TR-0T(v0.2 작성 때 `trim-design-r1`, 지금은 master 병합, T-40)가 G-15를 닫았다. 그래서 PC-10을 정의한다(§12.2, 기준은 새 입력 칸 `output_reference`로 받는다, §11.1).
  * v0.2 반영 2: 사용자 결정 T-39로 trim 잔여 수렴 분해능 = 오라클 DC 풀이 허용오차의 입력 환산 전파값이 됐다. 그래서 DC 풀이 허용오차를 반드시 선언하게 하고, 그 전파값을 결과에 낸다(§6, §8.3, §13.4).
  * v0.1 멈춤 항목 DV-1·DV-2는 사용자 결정 O-3으로 닫혔다. DV-1 (가)는 계획 v0.5(`oport-plan-r1`)에 반영됐고, DV-2 상위 문서 개정은 별도 card(`gb-oracle-rev`)다(§19.2).
  * 그 판의 Summary 첫 줄: '계획 `oracle-portability.plan.md` v0.6.5(승인 v0.4.2 + 사용자 결정 O-3·O-4·O-6·O-7·O-8·O-9·L-1·L-2·L-3과 검증 정합 개정, v0.6.5 승인 O-10)를 오라클 설계로 옮긴다. 계획의 결정은 사용자 결정 O-1~O-10, L-1~L-3, D-1~D-9이다.'
