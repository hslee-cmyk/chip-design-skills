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
| v0.3.3 (둘째 커밋) | (이 커밋, 같은 브랜치, base `79e5e5f4`) | design-validator v0.3.3 '수정 필요' 반영: B1 기록 파일 이름 `<stem>.<kind>.<rid16>`·같은 `<out_dir>` 호출자 의무, B2 검사 (4) 면제 좁힘(계획 417행 두 단계 같은 규칙), M1 `range_input_fp` = 실효 입력 지문(CLI·adapter_fp·descriptor_fp 포함), M2 `range_request`·재훑기 끝 기록 형식·원 범위 기록 정의, M3 §18.1 test, M4 §20 OP-5·OP-10 행, M5 §21.1 7단계 T-1 인용, M6 범위 최종 판정 = `range_final` 하나, M7 §11.6 표 행·글머리 분리, L1 frontmatter·§1.1 O-58~O-60, L2 §3.1 `range_confirm.py`, L3 `end_cause` `stage2_pending` 삭제, L4 measure 이름, L5 `range_final.lo/hi` 출력 전용, L6 옛 Status → H8, L7·#23 gain-budget v6.21 566·567행 재인용, L8 §21.4 '위 2번의 해'. #20·#22는 이미 해소(재측정: '전도 열' 0건, §4.2 행에 다섯 벤치 있음). DV-15에 검증자 판단 기록(결정 대기 유지). DV-14·DV-15 멈춤 유지 |
| v0.3.3 (셋째 커밋) | (이 커밋, 같은 브랜치, base `1352c5af`) | design↔계획 gap(약 90%) 가운데 design 몫 반영: (1) §19.2 알림에 U-6 EO-1 계약 변경 목록(파일 이름·같은 `<out_dir>`·`run_request`·`range_final`·`confirmed_range`·`input_dc`·끝 기록 칸 삭제), (2) §19.4 X-R1(파일 이름 꼴)·X-R2(`range_input_fp` 구성) -- 사용자 보고 대상, (3) `range_request`/`range` → `run_request`/`primary`(일반 합격 판정 실행 이름 어긋남), (4) 사본 정리: 끝 기록 `x_pass`·`x_fail`·`m_pass`·`m_fail`·`resolution_r`와 `range_final.*.lo/hi` 삭제 -- 정본 = `conduction.points[]`(point_id 지목), r은 §18.3 식으로 재계산, (5) §11.6 G-18 소자 식별 확인 문장, (6) §21.1·§21.2 인용 판을 gain-budget v6.21 master 566행으로 통일. 새 멈춤 DV-16(2단계 끝의 이탈 소자 정보 위치 -- 계획 결정 대기) |
| v0.3.4 | (이 커밋, 같은 브랜치, base `83727b8e` = master `7675f71b` 병합 -- 계획 v0.6.13·gain-budget v6.23 승인 O-65) | 계획 DR-19·DR-20(사용자 결정 O-61 P7·P8, O-62 (2) P10·(3) P11, O-63 (1)(2))로 DV-14·DV-15·DV-16 닫음. DV-14: `.tf` A 한 측정을 최상위 `a_dc` 기록으로(옛 `offset_mc.a_dc_tf` 등 이동), 갈래(\|A\| ≤ 판정 분해능, 사유 `a_dc_below_resolution`)·`.tf` 실패(`tf_failed`)·`.dc` 수렴 실패(`sim_convergence_failed`) 사유 분리, σ·V_id*는 `a_dc_undefined`로 참조, 갈래 먼저·V_id* 벤치에 둘째 A 측정 없음, '정의 경계 불일치'(§21.4·§21.5·§7). DV-15: `swing_icmr.input_dc_V`·`input_dc_pending` OP-5에서 삭제, V_icm = `dc_sweep.input_dc` 사영 또는 공칭 점 좌표(§11.1·§11.5·§11.6·§21.2). DV-16: `confirmed_range` 정의 불능 끝 `{undefined: true, record_id}`(`reason` 삭제), 검사 (1)만 정의 불능 끝에, `range_final.source` 정의 불능 꼴 = 같은 꼴, `end_cause`에 2단계 갈래 없음, 2단계 이탈 소자·사유 정본 = 엔진 `stage2_judgment`(인용만)(§7·§11.6·§11.7). X-R1·X-R2 승인 표시와 `range_input_fp`↔`input_sha256` 축 차이(§11.7·§19.4). §18.1 test (a)~(c), §19.5 graph 단일 정본 자체 점검 표 신설. 남은 멈춤 0 |
| v0.3.5 | (이 커밋, 같은 브랜치, base `d35f1907`) | v0.3.4 design-validator(M1~M6·N1~N4)와 design↔계획 gap(`_drafts/evidence/2026-10-21/oracle_design_v034_plan_gap.md`, 88.9%) 반영: M1 A 판정 분해능 V/V 식은 기존 정의에서 나오지 않아 새 멈춤 DV-17(A = 0은 진행; §21.2 반전 입력 전달 크기 판정도 같은 멈춤); M2 `a_dc`·`offset_sys` 기록 자리 = sim 단계 `sim.a_dc`·`sim.offset_sys`, compare는 `sim_ref`(sha256) 참조, 옛 `summary.u6` 사본 삭제(OP-3, X-R5); M3 결과 칸 `offset_mc.a_dc_signed` → `sim.a_dc.value` 대응 행·U-6 (j) 정정; M4 사유 집합·순서(실행 전 거부 / 정의 쪽 / 갈래 / 수치), `reference_undeclared`는 실행 전 거부로; M5·M6·N2 test(갈래 시 `.dc` 요청 0, 여기 방향 `tf_bench` 1, 있는 조건); N1 `/a_dc` 포인터; N3 PC-10 (e); N4 X-R3~X-R5 사용자 확인 항목; gap #27 OQ-10 (나) 동치 불성립 → 멈춤 DV-18; #34 §20 OP-5 행; #35 §1.1 O-56; §21.4 제목 v6.23 |
| v0.3.6 | (이 커밋, 같은 브랜치, base `b0dc62ff` = master `f4d89a23` 병합 -- 계획 v0.6.14·gain-budget v6.24 승인 O-70) | 계획 N7.5 DR-21·DR-22(사용자 결정 O-67~O-71): DV-17 닫힘(전달 판정 분해능 \|A\|·W_rail ≤ δV_out, δV_out = vntol + reltol·\|공칭 V\|·차동 δ_p + δ_n, 함수 하나, 문턱 값 칸 없음, `rail_width_zero`), DV-18 닫힘(`icm_margin_v` = 포트별 식, V_icm 사영·OQ-10 (나) 문단 삭제, `input_dc` 소비자 = V_id,0 하나, ICMR 점 `m` → `v_in`), S-OS2 차동 모드 DC 닫힘 벤치(`tb:icm` + `Vcvs` ±½, 출력별 반전 입력 `.tf`), §7 `feedback_config_undeclared` 슬루만·`measure_feedback_undeclared` 입력 칸 없음만, X-R3~X-R5 승인 표시·X-35, U-6 (l)~(n); DR-22 슬루 계단 자리·입력 망 규칙, t = 0 시작 동작점(닫힘 `.op` → `Tran.ic`, 능력 `tran_ic_bias_only`), 손 회로 test; 착수 실측 current_reuse 입력 망 없음(슬루 정의 불능 -- 사용자 보고); §19.6 실현 가능성 표(사용자 규칙); 새 멈춤 DV-19(단일 출력 + 용량만 선언)·DV-20('미확인' ngspice `.ic` 원문 쪽). 옛 V_icm 사영·동치 문단(v0.3.4·v0.3.5 §21.2 'metric 값')은 이 판에서 본문에서 지움 -- 원문은 git `3e4ee765` |
| v0.3.7 | (이 커밋, 같은 브랜치, base `158cffab`) | v0.3.6 design-validator(`_drafts/evidence/2026-10-21/oracle_design_v036_validation.md`, 80/100 조건부) 필수 2~6만 반영(사용자 결정 O-78 (3)): 필수 2 `icmr_v` = 포트 창 교집합의 폭 min_p hi_p − max_p lo_p(gain-budget 1490행·엔진 as-built `E/metrics/ls_swing.py:20`과 같은 뜻, 빈 교집합 = 음수 폭), m(`icmr_coord`)은 끝 확정 좌표로만 -- 옛 문장 `icmr_v` = "hi − lo(레일로 자름; hi·lo = 끝 점의 `icmr_coord(v_in, c)`)"는 본문에서 지움(원문 git `158cffab` §21.2 'metric 값'); 필수 3 DC 닫힘 `tb:icm` DC = cm0 + y·c_s, c(in_a) = c(in_b) 조건, 비대칭 c → 새 코드 `closure_common_asymmetric`(근거: 계획 닫힘 행 (i)(ii)·'여기 직교 성분', 스키마 Σ excite·common = 0과 같이 읽으면 여기 방향 = 닫힘 차동 방향); 필수 4 §18.1 (d) 옛 '짝 부호를 뒤집은 변형은 수렴 실패 또는 다른 창 → red'를 오프셋 손 회로 d_out 부호 test(d-1)·구조 단언 sign(T)·sign(닫힘) < 0(d-2)로 바꿈, F-1 'CMFB 없으면 `.dc` 미수렴' → '어느 쪽이든 fail-closed'; 필수 5 인용 정정(829→`/rails`, 833→`feedback_passives`, §4.1→§5 `Tf`·`OpSweep`·`Tran`, F-1 묶음에서 `:445` 뺌, F-4에 `:765`; 이 판에서 §7에 한 행을 더해 §11.1 줄이 1씩 밀려 835·839-840행으로 적음); 필수 6 §11.6 `measure_feedback`에 `human.feedback.elements: []` → `unity_follower`(`E/authoring/spec_elements.py:19-20`), 13회로 재측정(비지 않은 것 current_reuse 하나); nice-to-fix 셋(C10 `.ic` = 같은 `Tran.ic`·`tran_ic_bias_only`, `measure_feedback_undeclared`↔`feedback_config_undeclared` 이름 대응, F-1 판정 근거 = `.tf` 부호); §19.6 F-7~F-9·v0.3.7 graph 점검표; §19.2 '1b·DV-19: O-78로 계획 v0.6.15 대기' 한 줄. 필수 1·7(§21.6 1b)·DV-19 내용은 손대지 않음(O-78 (1)(2) 계획 먼저) |
| v0.3.7 (둘째 커밋) | (이 커밋, 같은 브랜치, base `f5b72b9d`) | v0.3.7 design-validator(`_drafts/evidence/2026-10-21/oracle_design_v037_validation.md`, 86/100 조건부) 반영: 필수 A §11.7 묵은 문장 둘(`icmr_coord` 소비자 = r·검사 (4)뿐, `range_final` 끝 값 = swing `m`/ICMR `v_in`); 필수 B §21.2 (c) 근거 (2) 정정 -- 옛 문장 "c에서 Vcvs 이득을 유도하면 … 훑기 방향이 차동 성분을 섞어 '차동 모드만 닫고 공통모드를 훑는' 정의 문장과 다른 측정이 되고"는 틀렸다(닫힘에서 차동 성분은 자유 변수가 아니라 같은 해 곡선, 매개만 다름) → 근거 = O-78 (3) 승인 + (1) 계획 문언 + (3) 스키마 직교 동치, (2)는 '정의 밖이라 막음'; N2 `closure_common_asymmetric` 인용에서 gb 576 S-OS1 문언 빼고 O-78 (3)·N3.14; N1 `icmr_v` 포트 집합 = 엔진 design 41 v1.12.4(master `ab916aba`) 780·784·811행(L8 (a), gap G4) 인용(grep 일치 -- DV 아님); N3 (d-2) `.tf` 네 값으로 만든 A_d 부호; N4 lo_p·hi_p = 두 끝 기록 min·max; N5 (d-3) ½(V_a+V_b) = cm0 + 2y; N6 거부 시점 = 시뮬레이터 호출 전, `excite` 두 포트 이름, `detail = {ports}`; N7 DC 닫힘 포트 ±½d_out·레일 밖 필터; N8 F-1 음수 margin = 값 FAIL; C10 `.ic` 문장 정정(§20 OP-3 범위, 1b가 AP-1로 가면 C10이 유일 소비자, 최종 귀속은 v0.3.8 DR-23); r(m 좌표) 백로그 메모(vntol 항만 \|c_s\|배); §19.2 v0.3.7 상태 문구; §19.6 graph 점검표 둘째 커밋 행. §21.6 1b·DV-19 본문은 손대지 않음 |
| v0.3.8 | (이 커밋, 같은 브랜치; base = master `93a9ff82` 병합 `9554b60a` -- 계획 v0.6.15·gain-budget v6.26 승인 O-80) | 계획 v0.6.15 DR-23 반영, 사용자 결정 O-78 (1)(2)·O-79·O-80 R2. **(1) 1b 미룸**: §21.6 1b 시작 동작점 경로와 1단계 입력 망 계단 갈래를 OP-10에서 빼 gain-budget card AP-1 몫으로 표시(§19.2 알림), OP-10에서는 기존 `feedback_config_undeclared`의 새 `why` 값 `start_op_deferred`·`input_network_step_deferred`(옛 `no_input_network` 대체); AP-1에서 시작점 = ICMR 공칭 점 기록 `v_in` 참조(둘째 `.op` 생산자 금지, v0.3.6 검증 필수 1). `Tran.ic`·`tran_ic_bias_only`는 소비자 C10이 있어 OP-3 소유 확정(§4.2·§5·§8.3·§18.1 'OP-3 C10 `.ic`'·§20 OP-3 행 -- v0.3.7 검증 보고 5 권고). OP-10 시작 동작점 손 회로 test 삭제 → '측정 구성 거부' (i)~(iv). §19.5 1b 행 writer 없음, §19.6 F-4·F-5 AP-1 표시, F-10~F-12 더함, v0.3.8 graph 점검표. **(2) DV-19 닫힘**: §21.2 2단계 (e) = 정의 불능(정의 = gain-budget v6.26 N3.8 인용), 사유 `icmr_feedback_dc_absent`(엔진 대응 `icm_config_feedback_no_dc` -- design 41 v1.12.5 `88bc5f2f`, 승인 대기, §19.2 알림), 단일 입력 (d) 먼저; §18.1 'OP-5 (e)' 행. **(3) DV-20 = C10 몫으로 줄임**. 새 멈춤 없음. 옛 문장은 아래 H9 |
| v0.3.8 (둘째 커밋) | (이 커밋, 같은 브랜치, base `ced5a45c`) | v0.3.8 design-validator(`_drafts/evidence/2026-10-21/oracle_design_v038_validation.md`, 84/100 조건부) 반영. **M1** C10 `.ic`(`Tran.ic`·`tran_ic_bias_only`·§4.2 `stab_benches`) 귀속 OP-3 → **OP-4**(계획 OP-4 행 500행 'C10 규칙 코어화 … `stability_op_netlist` 삭제'·N4 OP-4 행 467행 'C10 판정 불변' grep 재확인; 만드는 card = 쓰는 card): §4.2·§5·§8.3·§18.1 행 이름 'OP-4 C10 `.ic`'·§19.2 DV-20·v0.3.8 상태·§19.3·F-10·graph 표·§20 OP-3(경계 한 줄)·OP-4(이전 범위)·OP-10·§21.6 1b·Status. **M2** §7 (b) 범위는 그대로, §19.2에 '원래 취지와 다름(경미) X-R6'(범위가 계획 문언보다 넓음 + current_reuse 사유 `no_input_network` → `input_network_step_deferred`, 결과 같음, 사용자 확인). **N1** §19.2 'DC 성분 분류: O-81 (2) 경로 기준 일반화 -- 계획 v6.27 대기' 포인터(분류 자체는 안 바꿈). **N2** §19.2 ICMR·슬루 사유 대응표(엔진 design 41 v1.12.5 `88bc5f2f` 승인 대기, 입도 차이). **N3** F-4·F-5 옛 본문과 §20 OP-10 v0.3.6 '범위 더함' 문장을 H9로. **N4** (b)(c) 함께 해당 시 `detail.also`. 새 멈춤 없음 |
| v0.3.9 | (이 커밋, 같은 브랜치; base = master `8c2357bc` 병합 `44aa3932` -- 계획 v0.6.16·gain-budget v6.27 승인 O-83) | 계획 v0.6.16 DR-24 반영, 사용자 결정 O-81 (2)·O-82. §21.2 2단계 새 (0) DC 되먹임 판정(정의 = gain-budget v6.27 N3.8 '선언 되먹임의 DC 되먹임 판정 -- 정의 하나' 인용, 오라클 구현 = `/passives`·`/feedback_passives`·`/devices`·`/sources`·`/rails`·`/ports`·`/bias_voltages`의 방향 의존 그래프 BFS, 끝점 = C14 절단 규칙 넷, 시뮬레이터 호출 전, 결과는 갈래로만); (a)(c)(e)·§7 `feedback_config_undeclared` (c)·`icmr_feedback_dc_absent` 뜻·§11.6 `/measure_feedback` 차동 문장·§21.6 1b·F-11·점검표 '구성 판정' 행을 그 판정으로; `Inductor` 문언 삭제; 새 사유 `dc_feedback_judgment_undefined`; 대응표 갱신(+ 이상 전압원·DV-21 행); 1619행 포인터 닫힘 + v0.3.9 상태; §18.1 'OP-5 (0)' 판정 toy 행(R 출력–in−, Cf+Rb, R in−–레일만, T망, Rf∥Cf, 이상 전압원·전류원), 'OP-5 (e)' (ii) 문언; §19.6 F-13·F-14·v0.3.9 graph 표; §20 OP-5. 새 멈춤 DV-21(차동 두 출력 판정이 갈림). 옛 문장 H9 |
| v0.3.9 (둘째 커밋) | (이 커밋, 같은 브랜치, base `32af6e6c`) | v0.3.9 design-validator(`_drafts/evidence/2026-10-21/oracle_design_v039_validation.md`, 85/100 조건부) 반영. **M1** 종류 문언 세 곳: §7 `measure_feedback_undeclared` 행('단일 출력 + 용량만 선언' → 'DC 되먹임 없는 선언((0) 판정)'), §21.6 1단계('단일 출력 + 용량만 선언' 같은 정정), §20 OP-5 행 옛 '남은 막음 = **DV-19**(§21.2 2단계 (e) 단일 출력 + 용량만 선언만)'(DV-19 닫힘과 모순) → 닫힘 표시. **M2** §20 OP-5 착수 조건: DV-21 전에는 그 갈래 구현 안 함(N3.14); §19.2 DV-21 닫는 경로 = gb N3.8 한 문장(제안 문언, 사용자 결정 대기, 사유 이름은 그 뒤). **N1** §18.1 OP-5 (0) toy 공통 DUT 조건(입력은 MOS gate에만), (vi) R 분압, (vii) 공통 게이트 입력 '있음'(O-83 N4), (viii) 전류원 toy에 선언 Cf, (ix) bias 규칙; OP-5 (e) (i)(iii)(iv) 조건. **N2** `/bias_voltages` 게이트 전용 미검사 확인(스키마 100-104, 넷리스트 466-480, topology 대조 1233-1245) → 판정 전제 규칙 `dc_feedback_judgment_undefined` `why = bias_not_gate_only`, 계약 전체 확대는 백로그. **N3** 차동 출력 '하나라도'는 반대쪽 절단 넷 포함. **N4** 1053·1453·1454행 'DC 성분'·'용량만' → 판정·'DC 전도 원소'. **N5** bulk(gmb) 엣지 일반화 백로그(bulk 제외 유지). 새 멈춤 없음 |
| v0.3.10 | (이 커밋, 같은 브랜치; base = master `e87092b3` 병합 `810794a9` -- 계획 v0.6.17·gain-budget v6.28 승인 O-86) | 계획 v0.6.17 DR-25 반영, 사용자 결정 O-85 (1)(3)·O-86. **(1) DV-21 닫힘**: §21.2 2단계 (0) '차동 출력의 결합'(gain-budget v6.28 N3.8 '차동 출력' 인용), 갈리면 `dc_feedback_judgment_undefined` `why = differential_split`(`detail.present`·`absent` = 넷 이름); §20 OP-5 착수 막음 해소(옛 문장 "**착수 조건(v0.3.9 둘째 커밋, 검증 M2)**: DV-21이 닫히기 전에는 OP-5에서 '차동 출력 두 출력 판정이 갈리는 경우'의 갈래를 **구현하지 않는다** -- 사유 이름 없는 fail-closed를 코드에 남기지 않기 위해서다(gain-budget N3.14 공통 실패 규약 = 정의 불능 + 사유 기록). 나머지(단일 출력 판정, 두 출력 판정이 같은 차동 출력)는 착수 가능. DV-21을 닫는 경로 = §19.2 DV-21 행."); (0) 옛 문장 "차동 출력에서 두 출력의 판정이 갈리는 경우는 계획이 정하지 않는다 -- 멈춤 DV-21(§19.2); 그 갈래는 DV-21이 닫히기 전에는 OP-5에서 구현하지 않는다"; §18.1 OP-5 (0) 옛 끝 문장 "차동 출력 두 출력 판정이 갈리는 꼴 → 측정 진행 안 함(DV-21, 사유 이름 미정이라 사유 문자열은 단언하지 않음)" → 차동 결합 toy (x)(xi)(의사 차동, 비대칭 선언 Rf(o_a–in_b)·Cf(o_b–in_a); (x) 출력이 DC로 이어지지 않아 갈림 → 정의 불능, (xi) CMFB 저항 Rc1·Rc2가 출력을 이어 둘 다 '있음' → (a)). **(2) 지원 밖 원소 정렬**: `why = voltage_source` → `element_unsupported`(gain-budget v6.28 N3.8 '지원 밖 원소' 인용, 옛 인용 '이상 전압원 = 지원 밖' 대체; 오라클에서 판정에 닿는 지원 밖 kind는 `/sources` voltage 하나). `bias_not_gate_only` 그대로(DR-25 (3)). 대응표(엔진 `icm_config_feedback_element_unsupported`·DV-21 짝 이름 = design 41 v1.12.7 몫, 미작성·승인 대기), §19.2 v0.3.10 상태, §19.6 F-15·F-16·graph 표, §1.1, Status. 열린 멈춤 없음 |
| v0.3.10 (둘째 커밋) | (이 커밋, 같은 브랜치, base `72aad57c`) | v0.3.10 design-validator(`_drafts/evidence/2026-10-21/oracle_design_v0310_validation.md`, 91/100, 필수 0) nice-to-fix 반영. **N1** v6.28 문언 정렬: §21.2 (0) 옛 "판정 정의 불능(이상 전압원)이면" → 원인 셋; §7 `dc_feedback_judgment_undefined` 머리 옛 "정의 = gain-budget v6.27 N3.8 … '이상 전압원 = 지원 밖, 정의 불능'" → v6.28 '지원 밖 원소'·'차동 출력'; F-14 옛 "이상 전압원 → … | 정의 문단 '이상 전압원 = 지원 밖, 정의 불능'(gain-budget 587행)" → '지원 밖 원소'(589행); §18.1 OP-10 (ii) 옛 "차동 출력 + 용량만 선언" → 'DC 되먹임 없는 선언'. **N2** `bias_not_gate_only` 범주 = 입력 계약 전제 위반, OP-3 이관 때 같은 변경에서 그 why 삭제. **N3** 대응표 MOS kind 경계 행(엔진 nmos·pmos 대 오라클 기술자 kinds, 갈리면 '정의 경계 불일치'). **N4** §19.2 알림: 출력을 건너는 경로 toy (x)(xi)를 design 41 test로. **N5** DV-1~DV-9 행에 닫힘·결정 번호(O-3·O-8·O-9·O-50·O-51) 표시. **N6** §18.1 (x)(xi)를 별도 행 'OP-5 (0) 차동 결합'으로 나눔. 새 멈춤 없음 |
| v0.3.10 (셋째 커밋) | (이 커밋, 같은 브랜치, base `cd823a67`) | 사용자 결정 O-87(`_drafts/user_decisions.md` O-87 행). (2) §19.2 X-R6 표제 옛 '원래 취지와 다름(경미) -- 사용자 확인 필요 X-R6' → '승인됨 (O-87 (2))', 대기 목록에서 뺌. (1) U-1: §19.2 대응표 '차동 출력 두 출력 판정이 갈림' 행 -- 옛 엔진 칸 "이름 = design 41 v1.12.7 몫(…); v1.12.7 미작성이라 **미확인**, **승인 대기**" → 예약 이름 `icm_config_feedback_outputs_split`(엔진 S-OS2 일반형 card 구현), 그 전까지 엔진은 선언 있는 차동 출력 전부 `icm_config_differential_output_structure`, 같은 회로에서 갈리면 '정의 경계 불일치'. 오라클 쪽 판정·사유 변경 없음 |
| v0.3.10 (넷째 커밋) | (이 커밋, 같은 브랜치, base `509d2227`) | 사용자 결정 O-89 (2)(근거 `_drafts/evidence/2026-10-21/adopted_fix_audit.md` A19): `detail.also` 삭제 -- 소비자 0(test 행·대응표가 읽지 않음, 만들면 배선). 옛 §7 문장 "(v0.3.8 둘째 커밋, 검증 N4) `detail.why`는 처음 걸린 갈래 하나이고, (b)와 (c)가 함께 해당하면(사례 current_reuse) `detail.also = ["start_op_deferred"]`로 둘째 갈래도 적는다(같은 검사 하나가 쓰는 판정 기록 -- 값 사본 아님)." → 기록 = `why = input_network_step_deferred` 하나. §18.1 OP-10 (i) 옛 "용량만 선언된 차동 출력이므로 `detail.also = ["start_op_deferred"]` -- 둘째 커밋 N4", F-11 옛 "current_reuse는 (b) + `detail.also = ["start_op_deferred"]`(둘째 커밋 N4; …)", graph 표 옛 행 "`detail.also` | 같은 구성 검사 하나 | 거부 기록·검증자 | 판정 기록(함께 걸린 갈래 이름)이고 값 사본 아님 | 준수"를 정정. Status |

(v0.2.6 번호 정리: 절을 판 순서대로 H2 작성 → H3 v0.2.4 → H4 v0.2.5 → H5 v0.2.6으로 놓았다. 옛 'H6'(v0.2.5)는 H4다. design 본문 Status의 인용도 같이 고쳤다.)

## H9. v0.3.8에서 본문에서 옮긴 문장(계획 v0.6.15 DR-23)

* **§21.6 1b 옛 본문**(v0.3.6, DR-22): "1b. (v0.3.6, DR-22) **`.tran` 시작 동작점**(t = 0 해): 선언 되먹임에 DC 성분이 있으면 과도 벤치 자신의 바이어스 해 그대로. **용량만 선언된 차동 출력**이면 t = 0 해를 §21.2 2단계 (c) **차동 모드 DC 닫힘**(같은 벤치 소자 꼴, 정의 = gain-budget N3.8 576·577행 인용, 식은 계획 ICMR 행 한 곳)으로 정한다: (i) 닫힘 `.op` 한 점(§21.2 ICMR 벤치, y = 계단 시작 v1에 해당하는 0) → 입력 포트 in_a·in_b의 전압 V0(in_a)·V0(in_b) (ii) 과도 벤치(선언 구성 전체, 닫힘 원소 `tb:icm`·`tb:dmc:*` 없음)에 그 두 노드의 **바이어스 전용 초기 조건**을 건다 -- `Tran.ic = ((in_a, V0(in_a)), (in_b, V0(in_b)))`, 어댑터는 시뮬레이터의 '바이어스 해에서만 묶고 t > 0에 푸는' 초기 조건(ngspice: `uic` 없는 `.ic`)으로 쓴다. 닫힘 벤치와 과도 벤치의 바이어스 해는 같은 KCL이다(`.op`에서 용량은 열려 있고, 닫힘은 두 입력 전압으로만 회로에 닿으므로 그 두 전압을 묶으면 나머지 노드 해가 같다). t > 0에서는 묶임이 풀리고 넷리스트에 닫힘 원소가 없으므로 닫힘이 계단 응답에 남지 않는다(§18.1 OP-10 행 손 회로 test). reset 위상과 같은 꼴(계획 문언). IR·요청 확장: `Tran`에 `ic: tuple[(net, V)] = ()`, 어댑터 능력 `tran_ic_bias_only: bool`(§8.3에 더함; 없으면 그 회로의 슬루는 `adapter_capability_missing`). 실현 가능성 = §19.6 F-4(ngspice 쪽 원문 쪽 번호는 '미확인' -- 멈춤 DV-20)." -- AP-1에서 다시 쓸 때 (i)은 ICMR 공칭 점 기록 `v_in` 참조로 바꾼다(둘째 `.op` 생산자 금지).
* **§21.6 1단계 옛 계단 자리 문장**(v0.3.6): "선언 구성이 모든 입력 포트에 닿으면 선언 원소 가운데 **입력 망 원소**(한 단자가 입력 포트이고 다른 단자가 출력·레일·접지·다른 입력 포트가 아닌 원소)의 그 다른 단자에 원을 둔다 -- 없으면 `feedback_config_undeclared`(`why = no_input_network`; …)". v0.3.6 검증 필수 7: 그 노드가 용량에만 닿으면 `.op`에서 DC로 떠서 행렬이 특이해지고, 다른 소자가 구동하는 노드면 이상 전압원이 그 구동을 덮어쓴다 -- AP-1 착수 때 대표 회로(current_reuse 응용 회로 Cs 하판)로 실측.
* **§18.1 OP-10 옛 '시작 동작점 손 회로'**(v0.3.6, DR-22): 용량만 선언된 차동 출력(선형 이상 차동 OTA gm·ro + CMFB + 입력 망 Cin + 되먹임 Cf + 부하 CL)에서 (i) 과도 넷리스트 닫힘 원소 0개, `Tran.ic` = 입력 포트 둘 (ii) t = 0 해 = 닫힘 `.op` 해 (iii) 닫힘이 계단 응답에 남지 않음(`tb:dmc` 유지 변형·`uic` 변형 red) (iv) 입력 망 없는 선언 → `no_input_network` (v) 차동 출력 + 미선언 → `differential_undeclared` (vi) `tran_ic_bias_only` 없는 stub → `adapter_capability_missing`. (v)는 v0.3.8 '측정 구성 거부' (iii)으로, (iv)는 (i)로 남고, (vi)는 §18.1 'OP-3 C10 `.ic`' (ii)로 옮김; (i)~(iii)은 AP-1 몫.
* **§21.2 2단계 (e) 옛 문장**(v0.3.6): "(e) 단일 출력 + DC 성분 없는 선언(용량만): 계획이 정하지 않음 -- 멈춤 DV-19(§19.2); 그 측정은 진행하지 않는다(fail-closed; 사유 이름은 DV-19가 닫힐 때 정한다 -- 지금 지어 넣지 않음)."

**v0.3.9에서 옮긴 것**(계획 v0.6.16 DR-24 -- 소자 종류 분류 → 경로 판정):
* §21.2 2단계 (a) 옛 표제: "**(a) 선언 되먹임에 DC 성분이 있음**(`declared`이고 `feedback_passives`에 `Resistor`·`Inductor`가 하나라도 있음)".
* §21.2 2단계 (c) 옛 괄호: "(미선언 또는 DC 성분 없는 선언 -- 사례 current_reuse Cf1·Cf2)"; (e) 옛 표제 "**(e) 단일 출력 + DC 성분 없는 선언**(용량만; …)".
* §7 `feedback_config_undeclared` (c) 옛 괄호: "차동 출력 + DC 성분 없는(용량만) 선언(§21.2 2단계 (c)와 같은 분류 -- `feedback_passives`에 `Resistor`·`Inductor` 없음)".
* §11.6 `/measure_feedback` 옛 차동 문장: "ICMR = 선언 되먹임의 DC 성분(`feedback_passives` 가운데 IR `Resistor`·`Inductor` 원소)이 있으면 `declared` 그대로, DC 성분이 없거나(`Capacitor`만) `unity_follower`(미선언)이면 차동 모드 DC 닫힘".
* §21.6 1b 옛 문언: "선언 되먹임에 DC 성분이 있으면(또는 단일 출력 + `unity_follower`) 과도 벤치 자신의 바이어스 해 그대로".
* §19.2 v0.3.8 둘째 커밋 포인터: "**DC 성분 분류**: O-81 (2) 경로 기준 일반화 -- 계획 v6.27 대기. (v0.3.8 둘째 커밋, 검증 N1 포인터만; §21.2 2단계의 지금 분류(`Resistor`·`Inductor` 유무)는 바꾸지 않음. 참고: 오라클 입력 `/passives` kind는 `resistor`·`capacitor`뿐이라 `Inductor` 갈래는 지금 도달하지 않는다 -- 엔진 `DC_CONDUCTING_PASSIVE_KINDS`와 표기 차이는 v6.27 반영 때 함께 정리)".
* §19.6 graph 점검표 v0.3.8 행 이름: "구성 분류 'DC 성분 없음'(`Resistor`·`Inductor` 없음) | §21.2 2단계 분류 하나(ICMR (c)(e)·슬루 (c)가 같은 분류를 읽음)"; F-11 근거 "IR 원소 종류(§4.1 `Capacitor`·`Resistor`·`Inductor`)".
* §18.1 'OP-5 (e)' (ii) 옛 문언: "같은 선언에 `Resistor` 하나를 더한 변형 → 거부 안 됨(2단계 (a))".

**v0.3.8 둘째 커밋에서 옮긴 것**(검증 M1·N3):
* **§20 OP-3 행 첫 커밋 문장**(M1로 틀림 -- C10은 계획 OP-4): "**(v0.3.8, 계획 v0.6.15 DR-23 (1) -- 소유 확정) C10 초기 조건의 이전**: §5 `Tran.ic`·§8.3 `tran_ic_bias_only`(ngspice 어댑터 선언 = 참)·§4.2 `stab_benches`가 그 칸을 씀, §18.1 'OP-3 C10 `.ic`' 행; DV-20(원문 쪽)은 이 선언의 근거 칸". 같은 판 §4.2 행 v0.3.7 문장 'C10을 이 칸·능력으로 옮기는 것은 **OP-3 몫**이다'(v0.3.7 검증 보고 5 권고)도 같은 이유로 틀림 -- 본문에는 정정 표시와 함께 남김.
* **§19.6 F-4 옛 행 본문**(v0.3.6~v0.3.7): 설계 선택 "슬루 t = 0 = 닫힘 `.op` → 과도 벤치 `Tran.ic`(바이어스 전용, ngspice `uic` 없는 `.ic`)(§21.6 1b; DR-22 '어느 기법인지는 design')"; 근거 "`.ic` 무-`uic` 사용 = `O/oracle_netlist.py:596-598`, `:625`, `:720`, `:765`; IR·요청에 `Tran.ic` 없음 → 이 판이 더함(§5; C10도 같은 칸·같은 능력), 능력 `tran_ic_bias_only` 새 키(§8.3); 매뉴얼 원문 쪽 = 미확인(R6 대기)"; 단위 노드 전압 V; 추론 "닫힘 벤치와 과도 벤치는 `.op`에서 용량이 열려 같은 KCL이고, 닫힘은 두 입력 전압으로만 닿으므로 그 둘을 묶으면 해가 같다; t > 0 넷리스트에 닫힘 원소가 없어 흔적 없음. current_reuse는 입력 망이 없어 이 경로에 오지 않음(F-5)"; 경로 "닫힘 `Op` → V0(in_a), V0(in_b) → `Tran.ic` → 어댑터 `.ic` → `.tran` → dV/dt"; 판정 "미확인 1건 -- DV-20 멈춤(원문 쪽 + §18.1 OP-10 손 회로 test 통과가 관문)".
* **§19.6 F-5 옛 행 본문**(v0.3.6~v0.3.7): 설계 선택 "계단 자리 = 구성이 닿지 않은 입력 포트, 없으면 입력 망 원소의 다른 단자, 없으면 `no_input_network`(§21.6 1단계; DR-22 '입력 망은 선언 몫')"; 근거 "`feedback_passives`(§11.1 839-840행)·IR 원소 단자(§4.1); current_reuse 실측 `A/library/current_reuse_telescopic_ota.sizing_spec.json:141-142`, topology `passive_elements` Cf1·Cf2·Cs1·Cs2"; 추론 "current_reuse: Cf가 두 입력 포트에 닿고 Cs는 입력–접지라 입력 망 원소 아님 → 계단 자리 없음 → 정의 불능(사용자 보고)"; 경로 "spec 선언 → `feedback_passives` → 원소 단자 분류 → 원 자리"; 판정 "확인됨(결과 = current_reuse 슬루 정의 불능 -- 보고)".
* **§20 OP-10 행 v0.3.6 문장**: "(v0.3.6, DR-22) 범위 더함: §21.6 1단계 계단 자리·입력 망 규칙, 1b 시작 동작점(차동 모드 DC 닫힘 `.op` → `Tran.ic`), §8.3 `tran_ic_bias_only`, §4.1 `Tran.ic`, §7 `feedback_config_undeclared`(슬루만), §18.1 OP-10 시작 동작점 손 회로. 남은 막음 = DV-20('미확인' 원문 쪽 + 손 회로 test 통과)이 1b만."

## H8. v0.3.0~v0.3.3 판 Status 문장(v0.3.3 둘째 커밋에서 본문에서 옮김, 검증 L6; v0.3.3 문장은 v0.3.4에서 옮김)

* v0.3.3: **design v0.3.3 -- 개정 초안, 독립 검증 대기·사용자 승인 전**(2026-10-20; 승인된 계획 v0.6.11(O-60)·gain-budget v6.21 DEC-23과 사용자 결정 O-58·O-59로 DV-10·DV-11·DV-12·DV-13 닫음 -- §11.6 `confirmed_range`·`dc_sweep.input_dc`, §7 `range_pointer_rejected`·`input_dc_undeclared`·§7.2 2c, §11.7 `range_final`, §21.4 3단계, §21.5, §21.6; 새 멈춤 DV-14(작은 \|A\|)·DV-15(입력 DC 두 칸) -- history 판 표 v0.3.3; 둘째 커밋 = design-validator v0.3.3 '수정 필요' 반영; 셋째 커밋 = design↔계획 gap 반영 -- U-6 알림, §19.4 X-R1·X-R2, `run_request`, 끝 기록 사본 삭제, G-18 소자 식별 확인, 인용 판 v6.21, 새 멈춤 DV-16).
* v0.3.2: **design v0.3.2 -- 개정 초안, 독립 검증·사용자 승인 전**(2026-10-20; v0.3.1 독립 검증 #1~#23 반영, O-58 B-45 반영, DV-10·DV-11은 O-58 계획 v0.6.11 개정 대기, 새 멈춤 DV-12·DV-13 -- history H7).
* v0.3.1: 계획 v0.6.10(사용자 O-57 병합 승인, master `d6bd02b1`)의 N7.5 **DR-18**과 사용자 결정 O-50~O-55(O-56은 엔진 쪽 가리킴만)를 반영해 v0.3.0 멈춤 DV-6~DV-9·B-34·X-D7·X-D8과 결정 대기 목록을 닫았다(§19.2 'v0.3.1 닫힘 표'). 바뀐 곳: §11.6 G-18 확장 칸(`conduction_columns` 삭제, `intended_region`·`measure_feedback`·`sweep_rezoom` 칸, `slew.step_ends_V` 삭제), §11.7 결과 칸(점별 op 값·1단계 판정·`PENDING_CONDUCTION`), §21.1~§21.4·§21.6 절차(전도 두 단계, 선언 영역, ICMR 측정 구성, 부호 있는 V_id*, 방향별 슬루). 남은 멈춤은 §19.2 끝 'v0.3.1 남은 멈춤'.
* v0.3.0: **design v0.3.0 -- 개정 초안**(2026-10-20). 계획 v0.6.9(master `9401e98f`, 사용자 O-48)의 N7.5 design 개정 대상 DR-1~DR-17과 v0.6.9가 남긴 미결(G-18·G-19, EO-1 범위·갱신 경로, `.tf` 개루프 벤치, 합격 판정 전도 기준 = 봉인 9 식과 값의 출처, 손분석 입력 경로, OP-11)을 반영했다. 우선순위대로 OP-3 입력 스키마 계약(§11)을 먼저 test 작성자가 소스 없이 쓸 수 있는 수준(칸 이름·형식·필수·거부 조건·예시)으로 확정하고, 그다음 OP-5·OP-10·OP-11(§11.6, §21)을 정했다. **멈춘 항목 넷**(§19.2): DV-6 I_off 열의 읽기 규칙, DV-7 기준선 입력 LUT에 모델 기록 없음(OP-3 병합 조건 (b) 실행 불가), DV-8 `offset_sys_mv` 부호 규약, DV-9 슬루 계단 끝 '허용 입력 범위'의 출처. 이전 판(v0.2.6까지)의 상태 문장은 history H6으로 옮겼다.

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

---

## v0.4.0 -- 계획 v0.6.25·DR-26~DR-28 반영, 옛 문언 보존 (2026-11-03, 브랜치 `design/op0`, 기준 master `c8ecc4e7`)

결정·근거: 계획 v0.6.18~v0.6.25, 상위 사용자 결정 O-115·O-116·O-118~O-122·O-157·O-178·O-180·O-182 Q-S9·O-197·O-202·O-204·O-205·O-210·O-211·O-212·O-215·O-219~O-224. 낡음 표지를 단 줄 수 = 73(줄 번호 47,48,77,88,89,93,101,102,105,201,202,561,838,839,876,1010,1088,1337,1485,1488,1491,1517,1518,1578,1580,1581,1585,1620,1629,1633,1646,1648,1651,1652,1653,1654,1655,1659,1661,1665,1667,1680,1685,1686,1687,1688,1696,1703,1705,1706,1759,1774,1775,1796,1797,1799,1802,1803,1805,1812,1813,1817,1818,1819,1823,1829,1830,1831,1832,1836,1837,1839,1850). 아래는 바꾼 자리의 옛 원문이다.

### 옛 문언: 1959행

> 2. `power_dc_w` = Σ_{기준 아닌 레일} V·I. 레일별 `power.per_rail = {net: {V, I, P}}`도 싣는다. 기준 레일은 0 V(OP-3 입력 규칙 `reference_rail_voltage`가 보장)라 항에 넣지 않는다 -- 엔진 `E/metrics/supply.py:69`(모든 레일 합)와 같은 값.

### 옛 문언: 1964행

> 6. 비교: measure `power_dc_w`(§11.6) 행 -- 엔진 예측(`predictions.metrics`) 대 오라클 값, 판정 폭 `judge.tolerances.power_dc_w_rel`이 없으면 'N/A(tol 미설정)'. 모델 오차 기록(`derived.model_error_power_dc_w`, DEC-72)과 엔진 `verified_by` 연결 변경은 gain-budget PW-1a 몫(계획 U-5).

### 옛 문언: §21.6 머리

> **(v0.3.1) 정의·절차 갱신**(정본 = gain-budget v6.20 N3.8 슬루율 측정 정의(`7fe555b1` 564행 = 현 tree 565행)·metric 표, 계획 N3.9 슬루 행·G-19·OP-10 행 인용): **metric = 방향별 둘** `slew_rise_v_per_s`·`slew_fall_v_per_s`(각각 spec과 비교; spec이 `slew_rate_v_per_s` 하나만 선언하면 두 방향 모두에 적용; 집계 칸 없음 -- v0.3.0 DV-9 (가) '최솟값' 기각). **되먹임 구성** = §11.6 `measure_feedback`(§21.2 ICMR과 같은 칸·같은 반전 입력 포트 규칙; 차동 출력 + 미선언 = `feedback_config_undeclared`). **계단 끝 = 같은 입력의 오라클 ICMR 확정 끝**(§21.2를 2단계까지 확정한 `icmr` 창의 lo·hi -- O-51; 엔진 창·`step_ends_V` 입력 칸 없음). **순서**: ICMR 측정(1단계 훑기 → 2단계 전도 판정 → 끝 확정, `sweep_rezoom` 왕복 포함) → 슬루 요청(같은 입력 + 확정 ICMR 결과 기록을 근거로) → `.tran`. **확정 끝의 전달**(v0.3.3, DV-10 닫힘 -- 계획 G-19·OP-10 '실행 순서'·N3.9 슬루 행, 사용자 결정 O-58 DV-10·O-59 (3)): 실행 순서 = ICMR 측정(오라클 1단계 훑기) → 엔진 쪽 2단계(끝 확정, `sweep_rezoom` 왕복 포함, 지목 생산) → 확정 실행(같은 입력 + `confirmed_range`, §11.6) 하나에서 범위 확정 기록(`range_final`, §11.7)과 슬루 `.tran`을 함께 낸다(2단계 왕복 하나 더, 범위 확정과 같은 왕복). 슬루는 `confirmed_range.icmr`의 끝 지목(네 검사 통과 뒤)만 읽고 전압은 오라클 자기 기록에서 읽는다(전압 값 입력 칸 없음, 엔진 창 받지 않음). 그 끝이 정의 불능이면 **그 방향 슬루도 정의 불능**(`slew_step_end_undefined`, 다른 값으로 대신하지 않음). 엔진 손계산 계단(엔진 ICMR 창, DE-1 (d))과의 차를 포함한 슬루 차 = 모델 오차(DEC-72).

### 옛 문언: §21.6 정의 인용

> **정의 인용**(v0.3.3 둘째 커밋 재인용, 검증 L7·#23 -- 정본 = gain-budget v6.21 N3.8 '슬루율 측정 정의', master `b9af2d6f` tree 567행): "metric은 방향별 둘 -- `slew_rise_v_per_s`(출력 상승)·`slew_fall_v_per_s`(출력 하강)", "계단 = 동작점에서 ICMR 끝까지 미는 방향별 계단 -- 방향 = 출력을 그 방향으로 움직이는 쪽의 ICMR 끝", "SPICE 측정(정의 정확값)의 계단 끝 = 오라클이 잰 ICMR 확정 끝(오라클 확정 기록 `status = final`만 읽음, 잠정 값 읽지 않음)", "차동 출력 회로에 되먹임 구성 선언이 없으면 정의 불능". 아래는 옛 v6.19 557행 문구(기록 -- 위 v6.21 문구가 이김): gain-budget N3.8 557행 "**슬루율 측정 정의**(정의 SPICE 해석 `.tran`, O-33 (6) …): 계단 크기·방향 = O-28 끝(입력을 허용 입력 범위 끝까지 미는 방향별 계단), 측정 노드 = 슬루 정의 노드(DEC-65 노드 k), dV/dt = 측정 구간 안 최대 |dV/dt|, 되먹임 구성 = spec에 사용 구성(β) 선언이 있으면 그 구성, 없으면 단위 이득 follower(β = 1, 교과서 표준)이고 결과에 'β = 1 기본'을 표기한다(사용자 결정 O-34 (2))".

### 옛 문언: 1944행

> **절차**(v0.3.2 재작성; v0.3.3 계단 끝 전달 경로 = `confirmed_range`, DV-10 닫힘):

### 옛 문언: 1945행

> 1. 벤치(`slew_bench`; v0.3.6 다시 씀 -- 계획 v0.6.14 N3.9 슬루 행 '시작 동작점', 사용자 결정 O-69 (1) OQ-11 (다), DR-22): **과도 구간 되먹임 = 선언 구성 전체**(`declared`면 입력 회로·`feedback_passives` 그대로 -- 용량 포함, O-34 (2)); 단일 출력 + `unity_follower` = 출력을 반전 입력 포트(§21.2 규칙)에 잇는 이득 1 `Vcvs`; 단일 입력 = 회로 그대로; **차동 출력 + `unity_follower` = `feedback_config_undeclared`(`why = differential_undeclared`, 정의 불능 유지)**; 반전 포트 판정 실패 = `inverting_port_undetermined`. 입력 넷의 servo·choke는 넣지 않는다. 결과에 `slew.beta_default = (measure_feedback.kind == "unity_follower")`. **계단 자리**(v0.3.8 줄임 -- 계획 v0.6.15 DR-23 (1)·OP-10 행): 구성이 닿지 않은 입력 포트(선언 원소의 단자에 없는 입력 포트)가 있으면 그 포트의 원. 선언 구성이 모든 입력 포트에 닿으면 계단 자리(입력 망 원소의 다른 단자)는 gain-budget card AP-1 몫이라 OP-10에서는 `feedback_config_undeclared`(`why = input_network_step_deferred`)로 정의 불능이다(입력 포트에 원을 걸면 그 포트의 되먹임이 사라지므로 걸지 않음 -- 입력 망은 선언 몫, O-69 (1)). 옛 '입력 망 원소의 다른 단자에 원' 갈래와 `no_input_network`는 history v0.3.8. **착수 실측 결과**(DR-22, §19.3; v0.3.8 재측정 §19.6 F-11): current_reuse 선언 = {Cf1(Vom–Vip), Cf2(Vop–Vim)}가 두 입력 포트에 닿음 → `input_network_step_deferred`(정의 불능 그대로, 사유 문자열만 옛 `no_input_network`에서 바뀜). **단일 출력 + DC 되먹임 없는 선언**(§21.2 2단계 (0) 판정; v0.3.9 둘째 커밋 문언 -- 검증 M1-b, 옛 '용량만 선언'): 같은 입력의 ICMR이 `icmr_feedback_dc_absent`(§21.2 2단계 (e))라 확정 끝이 없어 2단계 `slew_step_end_undefined`로 끝난다(따로 사유를 두지 않음).

### 옛 문언: 1946행

> 1b. **`.tran` 시작 동작점**(t = 0 해; v0.3.8 다시 씀 -- 계획 v0.6.15 N3.9 슬루 행 '시작 동작점 경로의 구현 자리'·OP-10 행·DR-23 (1), 사용자 결정 O-78 (1)): 선언 되먹임에 DC 되먹임이 있으면(v0.3.9 -- §21.2 2단계 (0) 경로 판정 하나, 계획 v0.6.16 DR-24 (2); 옛 'DC 성분' 문언은 history v0.3.9)(또는 단일 출력 + `unity_follower`) 과도 벤치 자신의 바이어스 해 그대로. **용량만 선언된 차동 출력**의 t = 0 시작 동작점 경로(정의 = 계획 N3.9 슬루 행 '시작 동작점'이 인용하는 gain-budget N3.8 DC 닫힘)는 **OP-10에서 만들지 않는다** -- gain-budget card AP-1(N6.22) 몫이고, 그때까지 그 슬루는 `feedback_config_undeclared`(`why = start_op_deferred`, 1단계 구성 검사, 시뮬레이터 호출 0)로 정의 불능이다. AP-1에서 만들 때 t = 0 시작점은 같은 입력의 ICMR 공칭 점 기록 `v_in`(§11.7, y = 0 점; 슬루는 ICMR 확정 뒤에만 돌므로 그 기록은 늘 있음)을 참조로 읽는다 -- 시작점용 닫힘 `.op`(둘째 생산자)를 두지 않는다(검증 필수 1, graph 규칙 1·2·4). 옛 v0.3.6 1b 본문(닫힘 `.op` → `Tran.ic`, 손 회로 test)은 history v0.3.8. `Tran.ic`·`tran_ic_bias_only`는 이 경로 몫이 아니라 OP-4 C10 몫으로 남는다(§4.2, §8.3; 둘째 커밋 M1 정정).

### 옛 문언: §21.6 2단계

> 2. 계단: 1단계의 계단 자리(구성이 닿지 않은 입력 포트의 원 -- v0.3.8, 입력 망 원소 갈래는 AP-1 몫)에 `Pulse(v1 = 동작점, v2 = 확정 ICMR 끝)`을 끝(`lo`·`hi`)마다 따로 실행한다(방향 둘). (v0.3.3) 방향 = 출력을 그 방향으로 움직이는 쪽의 ICMR 끝(gain-budget v6.21 567행 -- 상승 metric은 출력을 올리는 쪽 끝). v2 = 같은 확정 실행 `range_final.icmr`(`status = final` -- gain-budget v6.21 567행 '오라클 확정 기록 `status = final`만 읽음, 잠정 값 읽지 않음')의 그 끝 `source` 지목 점 기록의 훑기 좌표 x(= y)로 정해지는 원 값 v0(n) + x·c(n)(§21.2 3단계와 같은 식, 오라클 자기 기록에서 읽음), v1 = 동작점(y = 0). 지목이 정의 불능이거나 `confirmed_range.icmr`가 없으면 그 방향 슬루는 `slew_step_end_undefined`(다른 값으로 대신하지 않음).

### 옛 문언: §21.6 4단계

> 4. dV/dt: 측정 노드 `slew.node`의 시간열에서 계단 시작 뒤 연속 출력 점 쌍의 |ΔV/Δt| 최댓값(방향별). 결과 `slew.{rise, fall}`(출력 방향 기준 -- 각각 measure `slew_rise_v_per_s`·`slew_fall_v_per_s`, §11.6; 어느 끝 계단이 출력 상승인지는 구성에 따라 다르므로 측정 노드 시간열의 변화 부호로 정한다) = {`max_dv_dt_v_per_s`, `t_at`, `max_step_s`, `step_end`(`lo` \| `hi`)}.

### 옛 문언: 1950행

> 5. 거부: `slew_undeclared`(§11.6 칸 없음), 수렴 실패·시간 상한 → `sim_convergence_failed`·`sim_timeout`(측정 단위 `failed`).

### 옛 문언: 1917행

>    * **판정**(계획 N4-2 '정의를 바꾼 칸', (vi)): 갈래가 발동한 회로의 `offset_sys_mv`는 0번 '동작 변경' 기준. 엔진과 오라클 가운데 **한쪽만** 갈래가 발동한 점은 값 오차(DEC-72 모델 오차)가 아니라 **'정의 경계 불일치'**로 검증자 원인 변화표에 적는다(범주 이름·정의 = 계획 N3.9 `offset_sys_mv` 행 (vi), gain-budget DEC-23이 같은 범주를 인용). 오라클 쪽 입력은 `sim.a_dc.status`·`sim.a_dc.reason`이고, 엔진 쪽 갈래 판정은 엔진 기록(card DE-1 (c) 자리)에서 검증자가 읽는다 -- 오라클은 엔진 판정을 받지 않는다.

### 옛 문언: 1918행

> 5. 비교: measure `offset_sys_mv`(§11.6), 판정 폭 `judge.tolerances.offset_sys_mv_abs`가 있을 때만. 엔진 1차값(ΔW 1차 감도, O-46 (1)·O-47) 대 오라클 정확값의 차 = 모델 오차(DEC-72). 오라클이 재는 점은 판정 W의 설계점이라 엔진 front 판정 점과 같다(계획 N3.9 계통 offset 행 '정합한다').

### 옛 문언: §21.3 전체

> ### 21.3 합격 판정의 전도 기준(OP-5, `core/compare.py` + `core/conduction.py`)
> 
> * 대상(v0.3.2 정정; v0.3.3 출처 대조 -- 대상 '모든 MOS × 선언 영역' = 계획 N3.9 '선언 영역'의 범위 조건 정본 '모든 MOS가 선언된 영역에 머문다'(사용자 결정 O-54, 동작점 대조 포함 -- 정의 정본 gain-budget N3.8 소자 조건); '술어 하나' = O-56 원문 'intended_region 술어 하나를 모든 소비자가 읽음, 둘째 거르기 없음'(`wt/_drafts/user_decisions.md` O-56 행). O-56은 같은 행에서 '판정 부분(공용 전도 판정 함수 하나)은 넓히지 않음'이라 하므로 판정 대상의 근거는 O-56이 아니라 O-54다 -- v0.3.2 인용 'O-56 술어 하나'만으로는 대상 근거가 모자랐음): **모든 MOS**를 선언 영역 `intended_region` 하나로 가른다 -- 선언 없음·triode = 전도 요구, off = off 유지 요구(§21.1 7단계). 엔진 예측 칸 `predictions.devices.<n>.region`은 대상 선택에 쓰지 않는다(엔진 예측 기록과 `region_spice` 대조 표시용 -- 둘째 off 출처를 만들지 않음). 판정 점 = free `.op` 해. (옛 C23 대상 규칙은 history H7)
> * (v0.3.1, 사용자 결정 O-50 G5·O-55 U1·U2, 계획 N3.9 '합격 판정') **두 단계**: 1단계(오라클) FAIL = ID ≤ 0(`off_reverse`), 포화 확인 실패, 제약 FAIL -- 그러면 최종 FAIL. 1단계에 FAIL이 없고 `stage2_pending` 소자가 있으면 `summary.verdict = "PENDING_CONDUCTION"`(§11.7, 오라클은 PASS를 내지 않음). 최종 판정은 엔진 쪽 2단계(공용 전도 판정 함수): I_off > ε·ID → FAIL, 판정 불능 → INCOMPLETE. **원인 구분**(U1): 선언 소자(`intended_region`)의 동작점 불일치 = `intended_region_mismatch` 선언 오류 → **판정 불능(INCOMPLETE) 집계**(FAIL 아님); 선언 없는 소자의 비포화 = 설계 실패 FAIL. 판정 우선순위는 §11.7 '반환 코드'.
> * **포화 확인 대상**(v0.3.1 확정 -- 사용자 결정 O-50 O2·O-55 V7, X-31 정정): **선언 없는**(`intended_region` 키 없음) **SPICE ID > 0(선언 방향)인 모든 MOS**; 선언 소자(triode·off)는 위 선언 영역 대조로 본다. 조건은 VDS − VDSAT ≥ `sat_margin_V`(판정 여유)다. 옛 코드의 대상 선택 'SPICE ID > 문턱 `thr`'(`O/oracle_compare.py:390-391`, 문턱 = 소자별 `off_current_A` 또는 `judge.off_current_A`)은 이 정의로 바꾼다(정의를 바꾼 칸 -- OP-5에서 두 문턱 칸이 지워지므로 대상 선택에 문턱이 남지 않는다). 선언 소자 영역 기록은 headroom-chain HC-O(같은 입력 칸 `intended_region`, 순서는 계획 N5.2 -- 나중 card가 앞 card의 test를 깨지 않음이 병합 조건).
> * **`region_spice` 표시 규칙**(v0.3.0 검증 지적 5; v0.3.1: 오라클 표시는 1단계까지 -- ID ≤ 0이면 `"off"`, ID > 0이면 아래 sat/triode에 2단계 대기 표시 `"pending"`을 덧붙이고, I_off > ε·ID의 `"off"`는 2단계 결과에만 있다): `"off"` = §21.1 전도식이 거짓(ID ≤ 0 또는 I_off > ε·ID), `"undefined"` = `conduction_undefined`, 그 밖은 옛 그대로 VDS − VDSAT ≥ `sat_margin_V`면 `"sat"`, 아니면 `"triode"`(여유가 없으면 `None`). 옛 '|ID| < 문턱이면 off'(`:279-281`)를 대체한다. 표시는 판정 입력이 아니다(판정은 위 두 확인).
> * 결과: `summary.conduction_definition = "seal9_two_stage"`(§11.7, v0.3.1), 소자 행에 1단계 칸(`stage1`)과 `conduction.points[]`(2단계 입력). 옛 행 칸 `off_current_A_pred`·`conduction_threshold_A`(`O/oracle_compare.py:301`)는 지운다(정의를 바꾼 칸).
> * 판정 기준: 정의를 바꾼 칸(X-33). 원래 취지와 다름(합격 기준이 엄격해짐)은 사용자 승인됨(O-45 U2).
> 

### 옛 문언: §21.2 정의 인용

> **정의 인용**(v0.3.3 둘째 커밋 재인용, 검증 L7·#23 -- 정본 = gain-budget v6.21 N3.8 '스윙·입력 범위', master `b9af2d6f` tree 566행): "출력 스윙 = 입력 공통모드를 동작점에 고정하고 차동 입력을 DC로 훑을 때 출력이 움직이는 범위 가운데 모든 MOS가 선언된 영역에 머무는 구간이다", "ICMR = 차동 입력 0(또는 동작점 차)으로 두고 입력 공통모드를 DC로 훑을 때 출력은 회로가 정하는 대로 따르는 상태에서 모든 MOS가 선언된 영역에 머무는 범위다(출력 고정 안 함, Allen 관례; 소자 조건 = DC 범위 조건, O-54)", 측정 구성 = 같은 행 'ICMR 측정 구성'(O-50 G4·O-58 S-3). 아래는 옛 v6.19 556행 문구(기록 -- 범위 조건은 위 v6.21 문구가 이김): gain-budget N3.8 556행(v6.19) -- "출력 스윙 = 입력 공통모드를 동작점에 고정하고 차동 입력을 DC로 훑을 때 출력이 움직이는 범위 가운데 전 소자(spec 선언 triode 제외) 포화 유지 구간", "ICMR = 차동 입력 0(또는 동작점 차)으로 두고 입력 공통모드를 DC로 훑을 때 출력은 회로가 정하는 대로 따르는 상태의 전 소자 포화 유지 범위(출력 고정 안 함, Allen 관례)", "끝이 정해지지 않으면(끝 풀이가 같은 x에서 성공한 해가 없으면) 그 끝을 읽는 metric은 정의 불능", "일반형: 전달 뷰 여기 방향으로 입력 포트를 훑는다", "단일 입력 회로의 ICMR = 출력이 회로대로 따라가는 상태에서 입력 포트를 DC로 훑을 때 소자 조건이 유지되는 입력 범위(차동이 없으면 공통모드 = 입력 자체)", "수렴하지 않은 점은 정의 불능이다 -- 창을 그 점에서 자르지 않는다".

### 옛 문언: §21.2 벤치 2단계

> 2. (v0.3.1, **ICMR 측정 구성** -- 사용자 결정 O-50 G4·O-53 A-1·A-2; v0.3.6 다시 씀 -- 계획 v0.6.14 N3.9 ICMR 행 '구성의 경계와 DC 닫힘'·'반전 입력 포트 식별'·'전달 판정 분해능', 사용자 결정 O-67 (1)·O-68 (2), X-35 승인, DR-21; 정의 = gain-budget v6.24 N3.8 'ICMR 측정 구성'(병합 `59ecc88e` 576행) 인용; ICMR의 옛 개루프 벤치 해석은 history H6·H7, swing은 이 단계 끝 'swing 벤치') ICMR 벤치 = 측정 구성(§11.6 `measure_feedback` + IR 원소 종류):
>    * **(0) DC 되먹임 판정**(v0.3.9, 계획 v0.6.16 N3.9 ICMR 행 'DC 되먹임 판정'·DR-24 (1), 사용자 결정 O-81 (2)·O-82; 정의 = gain-budget v6.27 N3.8 '선언 되먹임의 DC 되먹임 판정 -- 정의 하나' 문단 하나 -- 이 문서는 인용하고, 아래는 오라클이 같은 정의를 자기 입력만으로 따로 구현하는 자리(NFR-P3, 엔진 판정을 입력으로 받지 않음)): 아래 (a)·(c)·(e)와 §21.6 1단계 (c)의 'DC 되먹임 있음/없음'은 모두 이 판정 하나를 읽는다(코어 `swing_math.dc_feedback_judgment` 하나 -- 이름은 이 design; 슬루 쪽 둘째 구현 없음). **언제**: `measure_feedback.kind = declared`이고 입력 포트가 둘 이상일 때만(입력 하나면 (d)가 먼저라 부르지 않음 -- O-80 R2), §7.2 10단계 C14 막힘 검사 뒤, **어떤 시뮬레이터 호출보다 먼저**(입력 칸만 읽음; `.tf`·동작점·T_p 안 씀). **그래프**(방향 의존 그래프, 마디 = 넷): `/passives`(§11.1) `kind = resistor` → 두 단자 사이 양방향 엣지(`capacitor`는 엣지 아님 -- DC에서 열림); `/devices` → drain↔source 양방향, gate→drain·gate→source 한 방향(bulk는 엣지 아님 -- 정의 문단의 엣지 목록에 없음); `/sources` `kind = "current"` → 엣지 아님. **지원 밖 원소**(v0.3.10 정렬 -- 계획 v0.6.17 DR-25 (2), 사용자 결정 O-85 (3); 정의 = gain-budget v6.28 N3.8 같은 문단 '지원 밖 원소' 규칙 인용, 옛 인용 '이상 전압원 = 지원 밖' 대체): 오라클 입력에서 지원 밖 원소 = `/sources`의 `kind = "voltage"`(엔진 지원 이상원 = 전류원 하나와 같은 경계)이고, 하나라도 있으면 판정 **정의 불능**(`detail.why = element_unsupported`). 그 밖의 kind는 입력에서 이미 막힌다 -- `/passives` kind는 닫힌 열거(resistor·capacitor, §11.1 840행) 밖이면 스키마 거부, `/devices` kind는 기술자 `kinds` 키가 아니면 `descriptor_kind_undeclared`(§7) -- 그래서 판정 단계에 도달하는 지원 밖 kind는 `/sources` voltage 하나다(오라클은 kind 목록으로 다시 판정하는 둘째 검사를 두지 않고, 이 한 갈래만 본다). **끝점** = 선언 절단 넷 = `/feedback_passives` 원소의 `/passives` 단자 ∩ 입력 포트 넷(`/ports`의 `input_p`·`input_n`·`input`) -- 이 집합은 §7.2 10단계 C14 검사와 **같은 규칙 하나**(지금 `O/oracle_netlist.py:234-253` `loop_break_nets` -- 소자마다 입력 포트 단자 정확히 하나, 아니면 막힘)의 넷 목록을 읽는다(둘째 절단 규칙 없음). **경유 금지**(정의 문단 '고정 전위 넷'): `/rails`의 넷, 끝점이 아닌 입력 포트 넷(측정 구성이 구동), `/bias_voltages`의 넷(게이트 전용 이상 전압 넷 -- 들어오는 엣지가 없어 원래 중간 마디가 될 수 없음; 같은 뜻을 명시)은 중간 마디가 되지 않는다(끝점은 예외). (v0.3.9 둘째 커밋, 검증 N2) **게이트 전용 조건은 지금 검사되지 않는다**(확인: 스키마 `O/oracle_input.schema.json:100-104`은 칸 형식과 설명문만, 넷리스트 생성 `O/oracle_netlist.py:466-480`는 구동되는 넷의 선언을 조용히 건너뜀, topology 대조 `:1233-1245`는 topology가 있을 때만) -- 그래서 판정의 전제로 **규칙**을 둔다: 판정이 필요한 요청에서 `/bias_voltages` 넷이 MOS gate 말고 다른 단자(`/passives` 단자, `/devices` drain·source, `/sources` 단자, `/ports` 넷, `/rails` 넷)에 물리면 판정 정의 불능 `dc_feedback_judgment_undefined`(`detail.why = bias_not_gate_only`, `detail.nets`) -- 고정 전위로 다룰 근거(게이트 전용)가 깨지면 경유 금지 집합이 정해지지 않으므로 fail-closed. 입력 계약 전체(§11.2 1d)로 넓히는 것은 OP-3 범위 변경이라 이 판에서 하지 않는다(백로그, §19.2 알림). **판정**: 출력 넷(`/ports`의 `output` 또는 `output_p`·`output_n` 각각)에서 BFS로 끝점 가운데 하나라도 도달하면 그 출력은 'DC 되먹임 있음', 아니면 '없음'(정의 문단 '선언 절단 넷까지 도달하는 경로가 있다'). 단일 출력 = 그 출력의 판정. (v0.3.9 둘째 커밋, 검증 N3) 차동 출력에서 '끝점 가운데 하나라도'는 **반대쪽 절단 넷도 센다** -- 출력 o_a에서 o_b 쪽 반전 입력(절단 넷)에 닿아도 o_a는 '있음'이다(정의 문단의 끝점 = 선언 절단 넷 집합 전체, 출력과 절단 넷의 짝을 묻지 않음; 짝 식별은 `.tf` 몫이고 이 판정은 `.tf`를 쓰지 않음). **차동 출력의 결합**(v0.3.10, DV-21 닫힘 -- 계획 v0.6.17 DR-25 (1), 사용자 결정 O-85 (1)·O-86 N3; 정의 = gain-budget v6.28 N3.8 같은 문단 '**차동 출력**' 규칙 인용, 규칙을 다시 적지 않음): 두 출력의 판정이 같으면 그 판정을 (a)(c)와 슬루 (c)가 읽고, 갈리면 판정 정의 불능 → `dc_feedback_judgment_undefined`(`detail.why = differential_split`, `detail.present`·`detail.absent` = 출력 넷 이름만). (v0.3.9 둘째 커밋의 'DV-21 전에는 OP-5에서 구현하지 않음'은 풀림 -- history v0.3.10.) 판정 정의 불능(v0.3.10 둘째 커밋 일반화, 검증 N1 -- 원인 셋: 지원 밖 원소 `element_unsupported`, 차동 두 출력 판정 갈림 `differential_split`, 입력 전제 위반 `bias_not_gate_only`)이면 그 ICMR·슬루는 `dc_feedback_judgment_undefined`(§7). 판정 결과는 새 기록 칸이 아니다 -- 결과는 고른 갈래(벤치 넷리스트의 닫힘 원소 `tb:icm`·`tb:dmc:*` 유무, 또는 거부 사유)로만 남고, 검증자는 엔진 `config`와 그 갈래를 맞대어 갈리면 '정의 경계 불일치'(O-63 (2))로 변화표에 적는다. 비용: 입력당 BFS 한 번 O(넷 수), cache 없음.
>    * **(a) 선언 되먹임에 DC 되먹임 있음**(v0.3.9 -- (0) 판정 '있음'; 옛 문언 '`feedback_passives`에 `Resistor`·`Inductor`가 하나라도 있음'은 history v0.3.9): 입력 회로 그대로(β망 포함 -- `.dc`에서 용량은 열려 있어 DC 성분만 남음, 덧붙임 없음).
>    * **(b) 단일 출력 + 미선언**(`unity_follower`): 출력을 **반전 입력 포트**에 잇는 이상 연결(이득 1 `Vcvs`)을 더한다.
>    * **(c) 차동 출력 + (미선언 또는 DC 되먹임 없는 선언 -- (0) 판정 '없음'(두 출력 모두), v0.3.9; 사례 current_reuse Cf1·Cf2)**: **차동 모드만 닫는 DC 닫힘**(in_a − in_b) = (V(o_a) − V(o_b)) -- in_a = 출력 o_a의 반전 입력(T(in_a → o_a) < 0), in_b = 출력 o_b의 반전 입력; 계획 문언 (in+ − in−) = −(Vop − Von)과 같은 식을 짝 부호로 쓴 것. **벤치 소자 꼴**(design, DR-21): 공통모드 원 `tb:icm`(`VSource`, `n_cm` → 0, DC = cm0 + y·c_s, cm0 = ½(v0(in_a) + v0(in_b)) -- 공칭 free 해, c_s = c(in_a) = c(in_b) -- 아래 '공통모드 가중 조건') 하나와 `Vcvs` 둘 -- `tb:dmc:a`(p = in_a, n = `n_cm`, 제어 (o_a, o_b), 이득 +½), `tb:dmc:b`(p = in_b, n = `n_cm`, 제어 (o_a, o_b), 이득 −½). 그래서 V(in_a) − V(in_b) = V(o_a) − V(o_b), ½(V(in_a) + V(in_b)) = cm0 + y·c_s(입력 공통모드 = 훑기 변수, O-68 (2); 각 포트가 3단계 규칙과 같이 y·c(n)만큼 함께 움직임 -- c = (1, 1)이면 옛 식 cm0 + y와 같음). **공통모드 가중 조건**(v0.3.7, 검증 필수 3·사용자 결정 O-78 (3)): 이 닫힘은 c(in_a) = c(in_b) ≠ 0일 때만 쓴다 -- 그때 4단계 좌표 m = Σc·V/Σc² = ½(V(in_a) + V(in_b))/c_s라 벤치의 ½ 가중과 c 가중이 같은 방향의 같은 양(배율만 다름)이다. c(in_a) ≠ c(in_b)(한쪽 0 포함)이면 **`closure_common_asymmetric`**(§7, ICMR 정의 불능, fail-closed). (v0.3.7 둘째 커밋, 검증 N6 -- 거부 시점 통일) 검사는 in_a·in_b 짝(`.tf` 식별) 전에 `dc_sweep.excite`의 두 입력 포트 이름으로 c 두 값을 비교해 **어떤 시뮬레이터 호출보다 먼저** 한다(대칭 조건은 짝 순서와 무관); `detail`은 그 두 `excite` 포트 이름이다. 근거(v0.3.7 둘째 커밋 다시 씀, 검증 필수 B·N2): **사용자 결정 O-78 (3)**('공통모드 가중 c 유도·비대칭 fail-closed' 가운데 fail-closed 선택의 승인)과 아래 (1)·(3); (1) 계획 문언 -- 닫힘 행 (i)이 차동 방향을 (in+ − in−) = (1, −1)로 정하고 (ii)가 '입력 공통모드 = x', 계획 N3.9 ICMR 행이 '훑는 것은 여기 직교 성분(공통모드)'이라 공통모드 방향은 (1, −1)에 직교하는 (1, 1)뿐이다; 비대칭 c는 이 직교에 맞지 않아 두 행이 정하는 구성이 아니다 (2) 물리(v0.3.7 둘째 커밋 정정 -- 옛 문장 '훑기 방향이 차동 성분을 섞어 다른 측정이 된다'는 틀렸다, history v0.3.7 둘째 커밋) -- c에서 Vcvs 이득을 유도해도(g_a = c_b/(c_a + c_b), g_b = −c_a/(c_a + c_b)) 차동 행 V(in_a) − V(in_b) = V(o_a) − V(o_b)는 그대로이고, 닫힘에서 차동 성분은 자유 변수가 아니라 회로가 정한다. 그래서 해 집합은 같은 1차원 곡선이고 그 곡선의 매개(m 눈금·격자 간격)만 다르며, `icmr_v`·`icm_margin_v`는 포트 전압 `v_in`으로 내므로 끝점과 metric 값도 c 가중과 무관하다. 곧 비대칭 c를 막는 이유는 물리적 측정 차이가 아니라 **정의 밖**이라는 것이다 -- 그 일반화(비대칭 c의 이득 유도)는 계획에 없으므로 눈금만 다른 같은 곡선이어도 지어 넣지 않는다(as-built 결정 금지 -- 그런 회로가 생기면 계획부터). (3) 기존 §11.6 `/dc_sweep` 교차 규칙 Σ_n excite_n·common_n = 0(`dc_sweep_not_orthogonal`)과 함께 읽으면 c(in_a) = c(in_b) ⇔ excite(in_a) = −excite(in_b), 곧 이 조건은 '여기 방향 = 닫힘의 차동 방향 (1, −1)'과 같은 뜻이다 -- 대칭 여기(사례 `excite = {inp: 0.5, inn: -0.5}`)이면 스키마가 이미 대칭 c만 받으므로 이 갈래는 비대칭 여기 선언에서만 발동한다. 지금 library 차동 입력 회로의 `dc_sweep` 값은 EO-1 생산자가 아직 없어 **미확인**(이 조건은 그 값과 무관하게 fail-closed); 출력 공통모드는 회로의 CMFB가 정한다(벤치가 출력 공통모드를 묶지 않음). 두 입력 포트는 구성에 묶이지 않은 훑기 포트이고 `icm_margin_v` 대상 = 그 둘(O-68 (2)). 엔진의 닫힘 행 계산(Schur 2×2)을 받지 않는다(NFR-P3). 실현 가능성 = §19.6 F-1.
>    * **(d) 단일 입력 회로**: 회로 그대로(덧붙임 없음, O-52 확인 1).
>    * **(e) 단일 출력 + DC 되먹임 없는 선언**(v0.3.9 -- (0) 판정 '없음'; 옛 표제 'DC 성분 없는 선언(용량만)'은 history v0.3.9 -- 예 Cf(출력–in−) + Rb(in−–레일)도 여기; v0.3.8 DV-19 닫힘 -- 계획 v0.6.15 N3.9 ICMR 행·DR-23 (2), 사용자 결정 O-78 (2)·O-79·O-80 R2): **정의 불능**(fail-closed) -- 정의 자리는 gain-budget v6.26 N3.8 'ICMR 측정 구성'의 그 문장 하나이고 이 문서는 인용만 한다. 사유 `icmr_feedback_dc_absent`(§7), 거부는 어떤 시뮬레이터 호출보다 먼저. **갈래 순서**: 입력이 하나인 회로는 (d)가 먼저다(같은 N3.8 문장 'O-80 R2') -- (e)는 입력 포트가 둘 이상일 때만. 해당 회로 0개(§19.6 F-12). 옛 멈춤 문장은 history v0.3.8.
>    * **반전 입력 포트**: `inverting_input` 선언이 있으면 그것; 없으면 오라클이 §21.5 개루프 `tf_bench(port=p)`를 입력 포트마다, 출력마다(단일 출력 `NodeV(out)`, 차동 출력은 `NodeV(o_a)`·`NodeV(o_b)` 각각) 돌려 동작점 DC 전달 T(p → o)의 부호가 음수인 포트를 고른다(엔진 값을 받지 않음, 포트 role 이름은 근거 아님). 음수 후보 0개·2개 이상, 후보 전달이 **전달 판정 분해능**으로 판정 불능(§21.5 4단계 (4)와 같은 판정 함수 하나 -- 출력 식은 그 `NodeV`), 차동 출력에서 두 출력의 반전 입력이 같은 포트, 레일 폭 0이면 `inverting_port_undetermined`(ICMR 정의 불능, 사유 기록). (v0.3.5 DV-17 멈춤은 v0.3.6에서 닫힘 -- §21.5 4단계 (4).)
>    * 훑는 것 = 구성이 묶지 않은 입력 포트(follower면 비반전 입력, DC 닫힘이면 `tb:icm` 하나로 두 입력이 함께)를 같은 y로(O-53 A-2 -- 구성이 묶은 포트에는 적용 안 함). 엔진 쪽 ICMR(IT-2·DE-1)도 같은 구성(정의 하나).
>    * **swing 벤치**(v0.3.0 규칙, swing의 현행 규칙) = 본 회로 IR + 레일 + 바이어스 + 입력 넷마다 이상 전압원 `tb:sweep:<n>`(DC = v0(n)). 입력 넷의 servo·choke·결합 C·AC 원·Middlebrook 원은 넣지 않는다 -- 출력을 고정하는 원소가 없다(계획 G-18 'servo 없이 차동 0 유지하는 테스트벤치 원소'). 본 회로의 β 되먹임망(`feedback_passives`)은 회로 원소라 그대로 둔다.

### 옛 문언: §21.2 3단계

> 3. 점(`Excitation`의 DC 덮어쓰기, v0.3.2 정정 -- O-53 A-2): swing은 모든 입력 넷 n ∈ `excite`에 `tb:sweep:<n>` = v0(n) + x·excite(n). ICMR은 **훑기 넷 집합 S = 구성이 묶지 않은 입력 포트**(`declared`·단일 입력 = c(n) ≠ 0인 모든 입력 넷, `unity_follower` = 반전 입력 포트를 뺀 넷 -- 차동 2입력이면 비반전 입력 하나)에만 원 `tb:sweep:<n>` = v0(n) + y·c(n)을 두고, 묶인 포트(follower의 반전 입력)에는 원을 두지 않는다(출력 연결이 정함). (v0.3.6) DC 닫힘(2단계 (c))이면 `tb:sweep:<n>`을 두지 않고 `tb:icm` 하나의 DC = cm0 + y·c_s를 덮어쓴다((v0.3.7) c_s = c(in_a) = c(in_b), 비대칭이면 `closure_common_asymmetric` -- 2단계 (c) '공통모드 가중 조건')(두 입력이 `Vcvs`로 그 원에 걸림). c = `dc_sweep.common`, `null`이면 c = excite(단일 입력). x·y의 범위 = 모든 입력 넷이 [레일 최저, 레일 최고] 안에 머무는 구간. 격자 간격 = V_T = kT/q(그 실행 온도, 옛 격자 간격 -- 소신호 선형화의 물리 척도, `thermal_voltage`), 공칭 0을 포함한다.

### 옛 문언: §21.2 4단계

> 4. 측정 좌표: swing = 출력(단일 V(out), 차동 V(output_p) − V(output_n)). ICMR m = Σ_n c(n)·V_n / Σ_n c(n)²(v0.3.2: V_n = 그 점에서 풀린 전압, 합은 c의 모든 넷 -- 묶인 포트 포함; follower에서는 훑기 좌표 y와 m이 다르므로 끝 확정 분해능 r은 m으로 잰다((v0.3.7) ICMR metric 값 `icmr_v`·`icm_margin_v`는 m이 아니라 포트 전압 `v_in[p]`로 낸다 -- 아래 'metric 값'); (v0.3.6) ICMR 점 기록은 `m` 대신 원값 `v_in`을 싣고 m은 `swing_math.icmr_coord(v_in, c)` 한 함수가 이 식으로 계산, §11.7. 차동 c = (1, 1)이면 (V_p + V_n)/2 = 옛 '실제 입력 공통모드', 단일 입력이면 V_in).

### 옛 문언: §21.2 점 판정

> **점 판정**: (v0.3.1, 사용자 결정 O-54, 정본 = gain-budget v6.21 N3.8 소자 조건 master `b9af2d6f` 566행 인용(옛 v6.20 563행)) §21.1 1단계 선언 영역 조건(모든 MOS가 선언 영역에 머무름, 여유 0) -- 전도 쪽 이탈은 2단계가 정한다. 공칭에서 바깥으로 1단계 첫 이탈 점까지 가고 그 끝 괄호를 좁히며 모든 점의 op 값을 `conduction.points[]`에 낸다. 2단계는 그 점들에서 첫 전도 쪽 이탈 점을 찾고, **창 끝 = 두 단계 끝 가운데 공칭에 가까운 쪽**(2단계는 창을 줄이기만 함). 전도로 정해진 끝의 괄호가 아래 분해능 r보다 넓으면 2단계가 `sweep_rezoom`(§11.6) 입력으로 다시 요청하고, 같은 r·같은 `ZOOM_ROUNDS` 상한(오라클 결과 `rounds_left`만 전달)을 적용; 상한 안에 확정 안 되면 `sweep_end_unresolved`. 공칭 점에서 선언 소자 불일치 = `intended_region_mismatch`, 선언 없는 소자가 공칭 점에서 꺼짐 = 정의 불능(아래 metric 값 규칙) -- (v0.3.2) 1단계 `off_reverse`(ID ≤ 0)면 오라클이 `sweep_end_unresolved`(`why = nominal_not_conducting`)로 내고, ID > 0에서 I_off > ε·ID로 꺼짐이면 2단계(엔진 쪽)가 정의 불능으로 정한다(계획 N3.9 '범위 판정' 끝 문장, 2단계만 I_off를 가짐). **레일 밖 노드 필터**(v0.3.0 gap 지적으로 고침 -- 정의 밖의 **판정 단계 필터**로 둔다): 회로 노드 전압이 [레일 최저 − reltol·폭, 레일 최고 + reltol·폭] 밖인 점은 통과로 세지 않는다(옛 `sat_violation` 레일 규칙, `O/oracle_swing.py:123-130`). 물리 근거(P-1): 레일 사이에서만 전원이 공급되는 회로에서 레일 밖 노드 전압은 이상 전류원·이상 전압원이 만든 해이고 실제 소자로 얻을 수 없다 -- 정의의 '포화 유지 구간'은 물리 해 위에서만 뜻이 있다. 허용 폭 reltol·폭은 그 실행의 해 정확도(새 상수 없음). 이 필터로 끝이 정해진 경우는 끝 기록에 `end_cause = rail_filter`(§11.7)로 따로 적어 소자 조건으로 정해진 끝과 구분한다(검증자 원인 변화표가 읽음). 그 점에서 한 소자라도 `conduction_undefined`이면 그 점이 정의 불능이고, 측정 전체를 `conduction_undefined`로 거부한다(엔진 '판정 불가'와 같음).

### 옛 문언: §21.2 공칭 점

> **공칭 점 차 확인 -- swing만**(v0.3.0 검증 지적 6; 기본안 B-45 = 사용자 결정 O-58 B-45): swing 개루프 훑기 벤치의 x = 0 점 출력과 1단계 servo 해 출력의 차를 `nominal_output_shift_V`로 기록한다(입력을 servo 해 전압의 인쇄 값으로 구동하므로 생기는 차, §21.5 `.tf` 벤치 기록과 같은 성질). 그 차의 크기가 아래 끝 확정 분해능 r(출력 좌표, 같은 식)을 넘으면 개루프 벤치가 servo 해와 같은 동작점에 있다고 볼 수 없으므로 그 swing 측정을 `sweep_end_unresolved`(`detail.why = nominal_shift`)로 거부한다(fail-closed, 새 상수 없음). `nominal_output_shift_V`는 swing 결과에만 있는 칸이고 검증자 원인 변화표가 읽는다. **ICMR에는 공칭 점 차 거부도 `nominal_output_shift_V` 칸도 없다**(O-58 B-45): ICMR 범위 측정의 공칭 점 = 측정 구성 벤치(§11.6 `measure_feedback`)의 y = 0 해이고, 그 구성은 servo 해와 다른 회로(되먹임 구성)라 servo 해와의 차는 측정 결함이 아니다(엔진 ICMR도 같은 구성 -- 계획 N3.9 ICMR 행).

### 옛 문언: §21.2 끝 풀이

> **끝 풀이**: 공칭에서 바깥으로 첫 실패 점까지 가고, 괄호 [마지막 통과, 첫 실패]를 `ZOOM_POINTS`+1 등분으로 최대 `ZOOM_ROUNDS`회 좁힌다(NFR-P2 예외 상수 그대로, §14). **끝 확정** = 괄호 양 끝 점의 측정 좌표 차 ≤ r, r = reltol·max(|m_a|, |m_b|) + vntol(§18.3 전압 분해능 식, 그 실행 `Resolution`, 새 상수 없음). 끝 값 = 마지막 통과 점의 측정 좌표((v0.3.7) ICMR은 끝 = 그 점의 기록이고, metric은 그 기록의 `v_in`에서 'metric 값' 식으로 낸다 -- m은 끝 확정에만). (v0.3.7 둘째 커밋, **백로그 메모만** -- 검증 보고 5) r은 m 좌표라 포트 전압 단위와 다르다: 대칭 c에서 m = V/c_s이면 reltol 항은 상쇄되고 포트 전압 괄호 = reltol·\|V\| + \|c_s\|·vntol이라 **vntol 항만** \|c_s\|배가 된다(vntol 크기 -- 판정 영향 무시할 만함). r 식은 엔진 2단계 재훑기·검사 (4)와 공유하는 교차 계약이라 이 판에서 바꾸지 않고, metric 단위(포트 V)와 맞출 때 엔진 card와 함께 바꾼다. 확정 전에 반복 상한·시간 상한에 닿으면 `sweep_end_unresolved` -- 그 metric은 정의 불능이고 외삽 값을 내지 않는다(옛 코드는 상한에 닿아도 마지막 통과 값을 냈다). 범위 축 끝(입력이 레일)까지 모두 통과하면 그 끝은 레일 끝이다(옛 `hit_rail` 그대로). 어느 점이든 수렴하지 않으면 `sweep_point_unconverged`로 측정 전체를 거부한다.

### 옛 문언: §21.2 metric 값

> **metric 값**(값 식은 옛 그대로 -- 설계 40 §3.8-8, gain-budget DEC-96 (2) 정본): `swing_out_v` = 단일 2·min(V_hi − V_o0, V_o0 − V_lo), 차동 2·min(D_hi, −D_lo), V_o0·D 기준 = 공칭 점(x = 0)의 측정 출력. **`icmr_v`**(v0.3.7 다시 씀, 검증 필수 2·사용자 결정 O-78 (3); 정본 = gain-budget N6.6 IT-2 '범위' 2 'metric 읽기'(v6.24 1490행) "`icmr_v` = 포트 창 교집합의 폭(as-built 뜻 유지)" 인용) = **min_p hi_p − max_p lo_p** -- p·lo_p·hi_p는 아래 `icm_margin_v`와 같은 포트·같은 기록(측정 구성이 묶지 않은 입력 포트, 확정 끝 점 기록의 `v_in[p]`, 단위 = 포트 전압 V); 교집합이 비면 음수 폭 그대로(엔진 as-built `E/metrics/ls_swing.py:20` "입력 포트 넷들의 창 [max lo, min hi] 폭(빈 창은 음수 폭 그대로)"과 같은 뜻). **포트 집합**(v0.3.7 둘째 커밋, 검증 N1 -- design 해석이 아니라 엔진 정의 인용): 세 metric(`icm_margin_v`·`icmr_v`·`required_input_cm_v`)의 포트 집합은 같고 묶인 포트를 뺀다 -- 엔진 design 41 v1.12.4(master `ab916aba`, `docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md`) 780행 "`ports` = **측정 구성이 묶지 않은 입력 포트**마다(v1.12.4 gap G4 …) … **세 metric의 포트 집합은 같다**"·784행 "`icmr_v` = 포트 창 교집합 폭 = min_p hi_p − max_p lo_p(빈 교집합은 음수 폭 그대로, as-built 뜻)"·811행 L8 (a) "커널·front 세 metric의 포트 집합 = 묶이지 않은 입력 포트뿐(`tied_ports`의 반전 입력을 포함해 … red -- v1.12.4 gap G4)"(grep 확인; 이 worktree의 design 41은 v1.12.3이라 master 판을 인용). **창 끝 방향**(v0.3.7 둘째 커밋, 검증 N4): lo_p = min(두 확정 끝 기록의 `v_in[p]`), hi_p = max(같은 둘) -- c(p) < 0(스키마는 값 ≠ 0만 요구)이면 lo 끝 기록에서 그 포트가 최대가 되므로 기록 이름이 아니라 전압 크기로 정한다(엔진 design 41의 '다듬은 창 = 두 끝 전압 [min, max]'(v1.12 독립 검증 C1)과 같은 꼴); `icm_margin_v`도 같은 lo_p·hi_p. 레일: 직접 훑는 포트(`tb:sweep:<n>`)는 범위 규칙(3단계 '모든 입력 넷이 [레일 최저, 레일 최고] 안')으로 레일 안에 있고, (검증 N7) DC 닫힘 포트는 n_cm에서 ±½·d_out만큼 다를 수 있어 그 규칙만으로는 레일 안이 보장되지 않는다 -- 그런 점은 '점 판정'의 레일 밖 노드 필터(`rail_filter`)가 통과로 세지 않는다. 단일 입력·follower(묶지 않은 포트 하나)이면 그 포트의 hi_p − lo_p. 옛 m 좌표 정의 'hi − lo(hi·lo = 끝 점의 `icmr_coord(v_in, c)`)'는 **지운다** -- 엔진 정의(포트 창 교집합)와 같은 이름에 정의 둘이었다(graph 규칙 3; 반례 c = (2, 2)이면 포트 폭 2Δy 대 m 폭 Δy, DC 닫힘에서 두 포트 창이 어긋나면 교집합 < m 폭; 옛 문장 history v0.3.7). m(`icmr_coord`)은 이제 **끝 확정 좌표**(아래 '끝 풀이'의 r)로만 쓰고 metric 값에 들어가지 않는다. **`icm_margin_v`**(v0.3.6 다시 씀, **DV-18 닫힘** -- 계획 v0.6.14 N3.9 ICMR 행 '`icm_margin_v` 정의', 사용자 결정 O-67 (2), DR-21; 정본 = gain-budget N6.6 IT-2 '범위' 2 'metric 읽기'(v6.24 병합 `59ecc88e` 1490행) 인용) = **min_p min(V_p − lo_p, hi_p − V_p)** -- p = 측정 구성이 묶지 않은 입력 포트(follower의 반전 입력 제외, DC 닫힘이면 입력 포트 둘, 단일 입력이면 그 포트), 단위 = 포트 전압(V), V_p = 공칭 점(x = 0)의 SPICE 포트 전압(공칭 점 기록 `v_in[p]` -- 오라클이 푼 넷리스트 자신의 값, 선언 사본 아님, O-46 (2)), lo_p·hi_p = 확정 끝 점(확정 범위 지목의 `lo`·`hi` 점) 기록의 `v_in[p]`((v0.3.7 둘째 커밋, 검증 N4) 두 값의 min·max -- 위 `icmr_v` '창 끝 방향'). v0.3.4·v0.3.5의 V_icm 사영 Σc·V_in,decl/Σc²와 '선언 없으면 공칭 점 m' 갈래, OQ-10 (나) 동치 조건 문단은 **지운다**(같은 이름 두 정의 해소, graph 규칙 3; 옛 문장 history v0.3.6). `dc_sweep.input_dc`는 이 metric에 쓰지 않는다(§11.6). 정의를 바꾼 칸(포트 계수 1·묶인 포트 없음·기준점 = 동작점 밖 회로)이라 판정은 계획 N4-2 '정의를 바꾼 칸'. 공칭 점이 이미 포화 조건을 어기면 −(최대 포화 부족량)(옛 그대로). 공칭 점이 포화가 아니라 **전도**에서만 어기면 부족량이 정의되지 않으므로 `sweep_end_unresolved`(`detail.why = nominal_not_conducting`). (v0.3.2) 오라클이 내는 이 값들은 2단계 전 값이라 `status = provisional`이다(§11.7 '잠정 표시'). (v0.3.3, DV-12 닫힘; v0.3.6) 최종 값은 확정 실행이 지목 점 기록(swing은 `m`, ICMR은 `v_in`)을 **이 식 그대로** 넣어 `range_final`(§11.7)로 낸다 -- 값 식 정본은 이 한 곳(`range_final`의 `icm_margin_v`도 같은 포트별 식).

### 옛 문언: §21.2 결과 칸

> **결과 칸**(v0.3.2: 스키마 정본은 §11.7 '범위 끝 기록' 하나 -- 옛 `{x_lo, x_hi, m_lo, m_hi, bracket_width, rounds, resolution, hit_rail}`은 그 끝 기록으로 대체, `hit_rail` = `end_cause = rail`), 실행 수 `sim_runs`(옛 `ngspice_runs`, §11.5).

### 옛 문언: §21.2 판정

> **판정**: 정의를 바꾼 칸(X-29·X-32, O-34 규칙). 기준선 값과의 차는 검증자 원인 변화표에 칸마다 적는다. (v0.3.1) ICMR 해석 결정 대기는 **닫힘**(사용자 결정 O-50 G4 -- 측정 구성 = 선언 되먹임, 없으면 β = 1 follower). 원인 변화표의 ICMR 원인 후보 = 측정 구성 전환(옛 servo 출력 고정 → 구성 벤치)과 범위 조건 전환(O-54).

### 옛 문언: §21.2 깨진 변형

> **깨진 변형**(완료 조건 10): 출력을 고정한 ICMR(옛 servo 방식), 차동 전제로 단일 입력을 `unavailable`로 내는 경로, 끝 풀이 실패를 외삽·마지막 통과 값으로 넘기는 경로, 수렴하지 않은 점을 '포화 아님'으로 세어 창을 자르는 경로.

### 옛 문언: §21.1 전체

> ### 21.1 판정 점의 전도·포화(OP-5, `core/conduction.py`)
> 
> **정의 인용**(v0.3.3 셋째 커밋 인용 판 통일: 소자 조건 정본 = gain-budget v6.21 N3.8 '스윙·입력 범위' 안 '소자 조건', master `b9af2d6f` 566행; 옛 인용 v6.20 `7fe555b1` 563행 = 그때 tree 564행 '모든 MOS가 선언 영역에 머무름'(O-54) -- 아래 v6.19 556행 문구의 '선언 triode 밖' 부분은 그것으로 대체, 문구 재대조는 남음): gain-budget N3.8 556행(v6.19) "**소자 조건** = spec 선언 triode 밖 모든 MOS가 전도(봉인 9 전도 정의 I_off ≤ ε·ID와 같은 정의)이고 포화(VDS ≥ VDSAT)다 -- 소자가 꺼지는 점도 범위의 끝이다", "I_off·ε 모두 그 점 값이다"; DEC-90 (1) 289행 "SPICE 점에서 I_off > ε·|ID|이면 꺼짐, ε = (gm/ID)·tol_V. I_off·gm/ID·tol_V는 모두 그 판정 점(SPICE op 점) 자신의 값이다 … gm/ID = SPICE op 값, I_off = 그 SPICE op 점의 VDS·VSB에서 VGS = 0 누설 LUT 조회(판정 기하의 W), tol_V = 같은 점 VDS에서 읽은 LUT tol_V 셀"(사용자 결정 O-45 U2·O-46 (2)).
> 
> **절차**(판정 점 = 합격 판정의 free `.op` 해 또는 훑기 점의 해):
> 1. 어댑터 `OpTable`에서 소자마다 ID·gm·VDS·VSB·VGS·VDSAT(크기 규칙 정규화 값)를 읽는다. 하나라도 `None`이면 그 소자는 그 점에서 `conduction_undefined`(값 없음을 통과로 세지 않는다 -- 옛 `sat_violation` 규칙과 같음).
> **(v0.3.1) 전도 판정 두 단계**(사용자 결정 O-50 G5·G3, O-55 U2 -- 계획 N3.9 '전도 판정 위치 -- 두 단계'를 인용, 정의는 그대로이고 바뀌는 것은 계산 위치뿐): 오라클(1단계, 엔진 import 없음)은 아래 1·2·6·7단계만 하고 결과 `conduction.points[]`(§11.7)에 점별 SPICE op 값을 낸다. **I_off·tol_V와 I_off ≤ ε·ID 판정(옛 3~5단계)은 오라클이 하지 않는다** -- 엔진 정본 LUT 함수(공용 전도 판정 함수 하나, 엔진 봉인 7·9가 바로 부르는 것)가 2단계로 그 SPICE op 점에서 계산한다(엔진 쪽 OP-5 통합 병합 커밋, U-6; 사본 없음 -- 옛 DV-6 (가) 사본 안 기각). 값이 정의되지 않는 점·소자는 2단계에서 판정 불능(fail-closed). **온도 점**(사용자 결정 O-53 B2, 계획 N3.9 '온도 점 전도 판정'): 온도 조건 요청의 모든 점에서 gm/ID = 그 온도의 SPICE op 값, **I_off = 그 온도의 SPICE 값** -- 코어가 소자 개별 풀이 벤치(`core/build_benches.ioff_bench`: 그 소자 하나, 같은 VDS·VSB, VGS = 0, 그 온도의 `Op`)를 만들고 어댑터가 쓴다, 결과 `i_off_spice_A`; tol_V = T_j LUT 셀(2단계가 계산, 결과에 출처 `T_j_lut_cell` 표기). 그 요청 안 모든 점에 이 규칙 하나. 공칭 판정(LUT I_off)과 T_j 온도 요청(SPICE I_off)의 I_off 출처 차는 모델 오차(DEC-72) 기록이다. 그 판정을 쓰는 OP-6·offset-trim card는 이 절차를 부른다(구현하지 않음).
> 
> 2. **(v0.3.1 닫힘 -- 사용자 결정 O-50 G3)** 전도의 부호 조건 = **선언 단자 방향 ID > 0**. ID ≤ 0이면 꺼짐 확정(`stage1 = off_reverse`, 역방향 전도도 꺼짐 -- I_off ≥ 0이라 I_off ≤ ε·ID가 참이 될 수 없다). ID > 0이면 `stage1 = stage2_pending`(통과로 세지 않음). gain-budget DEC-90 (1)의 \|ID\| 문언과 엔진 봉인 9 'ID ≤ 0 판정 제외'를 같은 정의로 맞추는 것은 gain-budget v6.20·엔진 card 몫이다.3~4. (v0.3.1 삭제 -- tol_V·I_off 계산은 2단계 엔진 정본 LUT 함수로 위임, O-50 G5·DV-6 닫힘; 온도 점은 위 B2의 SPICE 소자 개별 풀이. 옛 열 읽기 규칙은 history H7)
> 5. **전도**(2단계가 판정, 정의 기록) ⟺ I_off ≤ ε·ID, ε = (gm/ID)·tol_V. 정확 부등식(새 허용 폭 없음). 결과 행 = 엔진 봉인 9 행과 같은 모양(`i_off_A`, `tol_v_V`, `eps`, `conduction_margin` = I_off/(ε·ID), > 1이면 꺼짐 -- `E/sizing/seal_conduction.py:11`).
> 6. **포화**(범위 정의) ⟺ VDS ≥ VDSAT, 여유 0(사용자 결정 O-33 (8)). 판정 여유 `judge.sat_margin_V`는 범위 정의에 넣지 않는다(계획 X-31). 합격 판정의 포화 확인은 옛 그대로 VDS − VDSAT ≥ `sat_margin_V`(판정 단계).
> 7. **(v0.3.1) 선언 영역**(`intended_region`, §11.6, 사용자 결정 O-53 B1·O-54·O-55 U1): 소자마다 선언 영역 가운데 1단계가 정할 수 있는 부분 -- 선언 없음: ID > 0 ∧ VDS ≥ VDSAT(전도는 2단계 대기); triode: ID > 0 ∧ VDS < VDSAT(전도는 2단계 대기; 경계 여유 = gain-budget N3.8 triode 경계 여유 한 정의(VDSAT − VDS − tol_VDsat ≥ 0)를 **2단계가 적용** -- 계획 N3.9 '범위 판정' 417행·'선언 영역', 사용자 결정 O-58 T-1; 오라클은 원값 VDS·VDSAT만 내고 여유·tol_VDsat를 적용하지 않음); off: ID ≤ 0이면 off 유지 확정, ID > 0이면 2단계(I_off > ε·ID면 off 유지). 동작점에서 선언 소자가 어긋나면 `intended_region_mismatch`(판정 불능 집계), 훑기 점에서 어긋나면 그 점이 범위 끝(§21.2). 함수는 판정 종류(`accept` / `sweep`)를 인자로 받아 이 둘을 가른다.
> **깨진 변형**(완료 조건 10, 먼저 실패를 보임): ε가 빠진 식 `ID > I_off`(ε = 1), 판정 점 대신 동작점(봉인점)의 I_off·tol_V로 판정, 꺼진 소자를 조건에서 빼 꺼지는 점을 범위 끝으로 보지 않음, 여유를 포화 정의에 넣음, tol_V `None`을 통과로 셈. (v0.3.1 추가) 오라클 결과만으로 PASS(`stage2_pending`을 통과로 셈), \|ID\|로 역방향 전도를 전도로 셈(G3), 오라클 안에 LUT 보간 사본(G5), 동작점의 선언 소자 불일치를 FAIL로 셈(U1 -- 판정 불능이어야 함), 훑기 중 선언 영역 이탈을 측정 거부로 셈(O-54 -- 범위 끝이어야 함).
> 

### 옛 문언: 1845행

> * **엔진·오라클 차**: 판정 실패가 아니라 모델 오차 기록이다(상위 DEC-72, D-6). 합격 판정은 지금처럼 오라클 값으로 한다(계획 N3.9).

### 옛 문언: 1844행

> * **변경 종류**(계획 N4 0번 표 그대로): OP-5 -- noise 칸·MC 수학((가-1)) = 정의 그대로(동일성) / 네이티브 MC 표본열, `icmr_v`·`icm_margin_v`·`swing_out_v`, 새 칸(`offset_sys_mv`, 단일 입력 swing·ICMR), A 출처와 σ, 합격 판정 전도 기준 = 정의를 바꾼 칸(동작 변경 기준). OP-10 -- 슬루 = 새 측정. OP-11 -- `rail_current_A`·`supply_current_A` = 정의 그대로, `power_dc_w` = 새 칸. 모든 card에서 결정성(두 번 실행 비트 동일).

### 옛 문언: 1824행

> | OP-5 | (v0.3.9, 계획 v0.6.16 DR-24) §21.2 2단계 (0) DC 되먹임 판정(`swing_math.dc_feedback_judgment`, 슬루 OP-10도 같은 함수를 읽음 -- 만드는 card = OP-5), §7 `dc_feedback_judgment_undefined`, §18.1 'OP-5 (0)' 행 더함. (v0.3.10, 계획 v0.6.17 DR-25 (1)) DV-21 닫힘 -- v0.3.9 둘째 커밋의 착수 조건('DV-21 전에는 그 갈래 구현 안 함', 옛 문장 history v0.3.10)은 풀렸다: 갈리면 `dc_feedback_judgment_undefined`(`why = differential_split`)를 이 card가 만든다, §18.1 OP-5 (0) (x)(xi). (v0.3.8, DR-23 (2)) §21.2 2단계 (e) `icmr_feedback_dc_absent`(§7)·§18.1 'OP-5 (e)' 행 더함; §10.4·§10.5와 기술자 파일의 `mc`·`diagnostic` 칸(sky130 값, 사용자 확인), §12.7 손 모델 픽스처 정본(만듦), §13, §11.5 결과 칸 OP-5 행, §15.1 OP-5 행(v0.3.0: `.ac` 첫 점·`1e-3` 삭제, swing servo 목표 훑기·ICMR 출력 고정 삭제, ε = 1 전도 판정 삭제), §15.4 OP-5 행, §18.1 4a. **(v0.3.0, 계획 v0.6.9 N3.9·DR-17)**: §11.6 G-18 확장 칸(v0.3.2 정정: `intended_region`(HC-O가 먼저면 재사용), `dc_sweep`, `measure_feedback`, `sweep_rezoom`, `output_reference`, measure `offset_sys_mv`)과 입력 칸 `off_current_A` 둘 삭제, 결과 칸 `conduction.points[]`·범위 끝 기록·`PENDING_CONDUCTION`(§11.7), §21.1 판정 점 전도·포화, §21.2 swing·ICMR, §21.3 합격 판정 전도 기준, §21.4 계통 offset, §21.5 `.tf` A, §18.1 '10 정의 대조' OP-5 행. **같은 통합 병합에 엔진 커밋 셋(`Role: code`, 계획 N3.9 '배선' (i)~(iii), O-55 U2, U-6)**: (i) EO-1 생산자 갱신(확장 칸 생산, `off_current_A` 생산 부분 삭제) (ii) 2단계 호출 자리(공용 전도 판정 함수)와 끝 괄호 재요청(`sweep_rezoom`) (iii) graph-consumption `dc_off_current` 출력 전용 선언 | OP-4, **gain-budget EO-1 병합**(생산자 갱신 대상, 계획 OP-5 선행) | (충족) OP-1 (i) 결과 = 소자별 독립(S-12). (충족, v0.2.5) DV-3 = 사용자 결정 O-8(§13.2). (충족, v0.2.6) DV-5 = O-9. OP-1a 병합(기준선 표본별 V_os 재계산값). (v0.3.2) **착수 조건**: DV-6·DV-8 닫힘(O-50 G5·G1·O-53 B3), gain-budget v6.20 정의 문장 병합(O-57, 계획 U-4 충족). 남은 막음: (v0.3.3) DV-11·DV-12·DV-13 닫힘(O-58 DV-11, O-59 (3)·(4), 계획 v0.6.11·gain-budget v6.21 DEC-23); 남은 막음 = (v0.3.4) DV-14·DV-15 닫힘(O-61 P7·P8, 계획 v0.6.12·v0.6.13); (v0.3.5) DV-17·DV-18 → (v0.3.6) **닫힘**(계획 v0.6.14 DR-21); 남은 막음 = DV-19(v0.3.6 당시) → (v0.3.8) **닫힘**(계획 v0.6.15 DR-23 (2), `icmr_feedback_dc_absent`; v0.3.9 둘째 커밋 정정 -- 검증 M1-c, 옛 '남은 막음 = DV-19(… 용량만 선언만)'은 이 행 앞머리 'DV-21'과 모순이라 고침). (v0.3.6 범위 더함) §21.2 차동 모드 DC 닫힘 벤치·출력별 반전 입력 `.tf`, `icm_margin_v` 포트별 식·ICMR 점 `v_in`, §21.5 전달 판정 분해능 함수·`rail_width_zero`, §7 `feedback_config_undeclared`(슬루만)·`inverting_port_undetermined` detail, §18.1 (b)(d). (v0.3.2 당시: DV-11(§21.5 단일 입력), DV-12(범위 최종 metric 재계산 주체), DV-13(계통 offset 기준점).) **(v0.3.3 범위 재작성, 검증 M4)** 이 card 범위에 더한다: §11.6 `confirmed_range`·`dc_sweep.input_dc`, §7 `range_pointer_rejected`·`input_dc_undeclared`·§7.2 2c, §11.7 `range_final`·`run_request`·`range_input_fp`·기록 파일 이름·같은 `<out_dir>` 호출자 의무, §3.1 `core/range_confirm.py`, §21.4 3단계 값 식, §21.5 단일 입력 A, §18.1 `core/test_range_confirm.py`. 같은 통합 병합의 엔진 커밋(U-6)에 EO-1 생산자의 `input_dc` 생산과 2단계 호출 자리의 `confirmed_range` 지목 생산·확정 실행 호출이 든다. **(v0.3.4·v0.3.5 범위 더함)** §21.5 `sim.a_dc` 기록(여기 방향 `.tf` 한 측정, 있는 조건)·사유 집합(`sweep_direction_undeclared`·`nominal_unconverged`·`tf_failed`·`a_dc_below_resolution`), §21.4 `sim.offset_sys`·사유 순서·갈래 발동 시 `.dc` 미요청, §7 `a_dc_undefined`·`range_pointer_rejected` 정의 불능 끝(검사 (1)만)·sim.json 대조, §11.1 `swing_icmr.input_dc_V`·`input_dc_pending` 삭제·§11.5 변환 행·결과 칸 `a_dc_signed` → `sim.a_dc.value` 행, §11.6 `confirmed_range` 정의 불능 꼴, §11.7 `range_final.source` 정의 불능 꼴·`end_cause` 1단계만·`sim_ref`, §21.2 V_icm, §18.1 '10 정의 대조 -- OP-5' (a)(b)(c). (OP-3 범위에는 `summary.u6` 삭제·`sim_ref`가 든다 -- X-R5 확인 뒤.) (옛 착수 조건 문장은 history H7) |

### 옛 문언: 1823행

> | OP-4 | **(v0.3.8 둘째 커밋, 계획 v0.6.15 DR-23 (1)·계획 OP-4 행 500행·N4 OP-4 행 467행, 검증 M1) C10 초기 조건의 이전 -- 만들고 같은 card에서 배선**: §4.2 `stab_benches` 행, §5 `Tran`의 `ic` 칸, §8.3 `tran_ic_bias_only`(ngspice 어댑터 선언 = 참)를 이 card가 만들고 C10이 쓴다(choke 노드·kick 출력 노드 `.ic`), §18.1 'OP-4 C10 `.ic`' 행; DV-20(원문 쪽)은 그 선언의 근거 칸(이 card를 막는 범위 = 근거 칸만). §8.4(G-13 확정), §8.5, §7.1 pz·과도 몫, §11.5 결과 칸 OP-4 행(실행 전 반환 경로 포함), §14 반복 상한 다섯, §15.1 OP-4 행, §15.4 OP-4 행(측정 도구 `calibration_tools/`로), §18.2 캐시 test 넷째, u6 pz 점검 재작성 | OP-3 | G-13 측정(S-19 있음) + (가) 시간 상한 사례 수(§19.3) |

### 옛 문언: 1826행

> | OP-7 | §16 | OP-3, XRUN-F1 C | (충족) OP-1 (iii) = S-15. 경계 재측정, cap·mismatch 세트 판 기록 확인 |

### 옛 문언: 1828행

> | OP-10 (v0.3.0 신설 반영; v0.3.1 선행·착수 조건 닫힘 -- O-50 O3·O-51; 남았던 DV-10은 v0.3.3에서 닫힘 -- O-58 DV-10·O-59 (3)) | §21.6 슬루, §11.6 `slew` 칸, §5 `Tran` 계단 벤치, §8.3 능력 `tran_large_signal`, §15.1 C25 행, §18.1 '10 정의 대조' OP-10 행 | OP-4, OP-5, **EO-1**(v0.3.1, O-50 O3), gain-budget v6.20 N3.8 슬루 정의 문장(565행) | (v0.3.1) **착수 조건**(계획 OP-10 행): (i) gain-budget v6.20 N3.8 개정 병합(O-57로 병합됨) (ii) OP-5 ICMR 절차 병합(계단 끝 출처, O-51); 그리고 §19.2 DV-10(확정 끝 전달 경로) 결정. EO-1 생산자 갱신(`slew`·`measure_feedback` 칸) 커밋을 같은 통합 병합에(U-6). (v0.3.3 재작성, 검증 M4: DV-10 닫힘 -- O-58 DV-10·O-59 (3)) 슬루는 OP-5 확정 실행(`confirmed_range` → `range_final`)과 **같은 실행**에서 돈다 -- 선행에 OP-5 `range_confirm`(§3.1)이 든다; 계단 끝 = 같은 실행 `range_final.icmr`의 그 끝 `source` 지목(§21.6 2단계), 실행 순서 = ICMR → 엔진 쪽 2단계 → 확정 실행(계획 OP-10 '실행 순서'), 지목 생산·확정 실행 호출 = 이 card 통합 병합의 엔진 커밋(U-6) **(v0.3.8, 계획 v0.6.15 OP-10 행·DR-23 (1), 사용자 결정 O-78 (1) -- 범위 줄임; v0.3.6 DR-22 '범위 더함' 옛 문장은 history v0.3.8 둘째 커밋(H9))** v0.3.6에 더했던 1b 시작 동작점, 1단계 입력 망 계단 갈래, 시작 동작점 손 회로 test는 **이 card 범위가 아니다**(gain-budget card AP-1 몫, §19.2 알림); `Tran.ic`·`tran_ic_bias_only`는 OP-4 소유(C10; 둘째 커밋 M1 정정, 옛 'OP-3')라 이 card는 쓰지 않는다. 이 card에 남는 것: §21.6 1단계 구성 검사(`feedback_config_undeclared` `why` ∈ `differential_undeclared`·`input_network_step_deferred`·`start_op_deferred`), §18.1 OP-10 '측정 구성 거부' (i)~(iv). DV-20은 이 card를 막지 않는다(C10 몫). |

### 옛 문언: 1822행

> | OP-3 | §3, §4, §5, §6(`instance_geometry_reported`·요청 단위 오류·`bundle_files`·`machine_dependent_refs` 포함), §7(§7.1 op·ac 몫, §7.2), §8.1~8.3, §9, §10.6(소자 줄 작성·미선언 거부), **(v0.3.0) §11 전부 -- OP-3 입력 스키마 `spice_oracle_input/2`(§11.1~§11.3, EO-1 계약 §11.4), 옛 형식 거부, 옛 입력 읽기 전환, 기술자 로더의 `oracle_run` 배선, 실행 결과 계약(§11.7), `O/oracle_input.schema.json` 다시 씀**, §11.5 결과 칸 OP-3 행, §12.5(역할 구분, sha256 정의, 기록 뿌리 교차 검사 함수·test), §15.1 OP-3 행, §15.4 OP-3 행(cm_loop 스크립트, `u6_selfchecks.py` 삭제(O-10), conftest 입력 생성기 새 형식(v0.3.0 OP-2에서 옮김), `make_lut` 기록, 손 넷리스트 기준 `O/tests/adapters/ngspice/`로), §18.1 '8a 예외 둘째'(엔진 test glob 한 줄, 엔진 test 작성자)·'OP-3 입력 계약' 행, §18.2 캐시 test 앞 셋, smoke 고정 자료 '스키마 적합' test → '옛 형식이라 거부' test. **(v0.3.8 둘째 커밋, 검증 M1 -- OP-3/OP-4 경계)** 위 §4·§5·§8.1~8.3 가운데 **C10 과도 몫**(§4.2 `stab_benches` 행, §5 `Tran`의 `ic` 칸, §8.3 `tran_ic_bias_only`)은 OP-4 몫이다(계획 OP-4 행·N4 OP-4 행) -- OP-3은 그 칸·능력을 만들지 않는다(첫 커밋의 'C10 초기 조건 이전' 문장은 history v0.3.8 둘째 커밋) | OP-2(따로 검토, 함께 병합), (v0.3.2) OP-1b(병합 조건 (b)의 비교 상대) | **착수 조건**(v0.2.5): §19.2 DV-4 결정 -- (v0.2.6) 충족(O-9). (v0.3.0, 계획 OP-3 행) 옆 선언 근거 (a) 생성기 판 찾기가 폭 슬라이스 32개에서 가능한지 먼저 확인(§12.5, 계획 N9), 기존 슬라이스 meta 모양 실측(**충족** -- S-38: 폭 슬라이스 평탄, 결합 파일 중첩, §11.2 2b가 두 모양을 읽음). (v0.3.2) 병합 조건 (b)의 비교 상대 = **OP-1b 추가 기준선**(DV-7 닫힘, 사용자 결정 O-50 O1′ -- 기준선 입력 593개는 D-7 거부 `lut_model_provenance_missing`이 기대 결과, 코어 이관 동일성은 모델 기록 있는 LUT v2 슬라이스 입력으로; 선행에 OP-1b). **병합 조건**(P OP-3): (a) 기하 규칙 미선언 기술자의 실제 거부 test + 검사 순서·양성 대조 (b) 첫 조합 선언값의 공칭 op·ac 결과 N4-2 기준선 동일(검증자), 소자 줄 차이는 기록만·§10.6 절차로 선언 기인 한정 (c) (v0.2.5, 계획 v0.6.3) 기존 LUT 역할 옆 선언 + 그 선언으로 (i)~(iii) 통과 + 역할 지운 변형·보조 입력 sha256 바꾼 변형 실제 거부(§18.1 'OP-3 병합' 세 행). smoke 고정 자료 '넷리스트 재생성 일치' test 삭제 + `criteria_weakened`(§18.2) |

### 옛 문언: 1821행

> | OP-2 | (v0.3.0 다시 씀, DR-10i -- 사용자 결정 O-14 (4) J-1 (나), 계획 X-28) **기술자·기술자 스키마·기술자 읽기 코드만**: §10.1, §10.2·§10.3 가운데 `mc`·`diagnostic` 칸을 **뺀** 기술자 전부(기하 단위·병렬 배수 선언 칸, `lut_record_root` 참조 포함, P G-5, sha256 칸 = LF 정규화 DR-6~DR-8), 코어 기술자 로더(스키마 검사, 참조 sha256 대조 -- 규칙 (i)(ii), 원본 중복 검사 -- 규칙 (iii), 위치 선언 해석, §18.1 '기록 뿌리 해석' 행). **입력 형식 전환은 하지 않는다**(§11은 OP-3): 옛 형식 입력과 옛 모듈 경로는 OP-2 병합 뒤에도 그대로 돌고, 기술자 로더는 아직 실행 경로에 배선되지 않는다 -- **OP-2·OP-3은 따로 검토하고 함께 병합**한다(만들면 배선을 병합 단위로 지킴). 기록 뿌리 교차 검사(`lut_record_root_mismatch`)도 OP-3(J-5 (가)) | OP-0, OP-1 | (충족, `b105b65`) 상위 문서 개정 card `gb-oracle-rev` 병합. **병합 조건**: ngspice 매뉴얼 원문 보관과 기본 허용오차 쪽 번호(R6) 채움(X-D4), (v0.2.5) abstol 값·쪽 포함(S-28) |

### 옛 문언: 1454행

> | (v0.3.0) 10 정의 대조 -- OP-5 | `core/test_conduction.py`, `core/test_swing_icmr_def.py`, `core/test_offset_sys.py`(기준 종류 셋 + 차동 기본, §21.4; v0.3.3 값 식 3단계 = V_id* − V_id,0(선언 입력 DC 기준) -- free servo 해를 빼는 변형 실패, `dc_sweep.input_dc` 없음 → `input_dc_undeclared`, 차동 같은 DC 선언 → V_id,0 = 0), `core/test_range_confirm.py`(v0.3.3: 네 검사 깨진 변형 넷 → `range_pointer_rejected` `check`별 red(재훑기 기록 합친 열의 (2)·(4) 포함, (4) 면제는 `pass_point_id` ∧ `end_cause` ∈ {rail, rail_filter, stage1}일 때만), `range_input_fp`가 CLI 덮어쓰기·adapter_fp·descriptor_fp 변화에 따라 바뀜, 다른 `<out_dir>` → `record`, `range_final` 값 = §21.2 식(엔진 쪽 사본 grep 0), 잠정 실행 verdict에 범위 제약 없음, 기록 파일 이름 `<stem>.<kind>.<rid16>` 덮어쓰기 없음, `confirmed_range`+`sweep_rezoom` 동시 → E5), `adapters/ngspice/test_tf_gain.py`(v0.3.3: 단일 입력 A가 값, 차동 비트 동일) + 검증자 정의 대조표 | test 작성자(정의 문장에서 기대값), 검증자(대조표·원인 변화표) | 계획 완료 조건 10(v0.3.2 재작성 -- §21.1 깨진 변형·§11.7 기준): §21.1 1단계(ID ≤ 0 → `off_reverse`, \|ID\|로 역방향 전도를 전도로 세는 변형 실패(G3); ID > 0 → `stage2_pending`, 통과로 세지 않음; 값 하나 없음 → `stage1 = undefined`·`conduction_undefined`; 오라클 안 LUT 보간 사본 grep 0(G5); 온도 조건 요청에서 `ioff_bench`가 소자마다 돌고 `i_off_spice_A`·`tol_v_source = "T_j_lut_cell"`이 실림(B2, G3 ID ≤ 0 소자 포함); 7단계 선언 영역 세 경우(선언 없음·triode·off)), 2단계 쪽 깨진 변형(ε = 1, 동작점 값, 여유를 정의에)은 엔진 쪽 2단계 test 몫(OP-5 통합 병합 엔진 커밋), §21.2 손 회로(단일 입력 회로의 ICMR이 `unavailable`이 아니라 값이 나옴, 출력 고정 ICMR 변형은 다른 값, 수렴 실패 점 하나 → `sweep_point_unconverged`, 반복 상한 도달 → `sweep_end_unresolved`; (v0.3.2) 훑기 중 선언 영역 이탈 = 범위 끝·`departed` 기록(측정 거부로 세는 변형 실패, O-54), 훑기 이탈이 범위 축 끝이면 `end_cause = rail`, `sweep_rezoom` 1회 훑기·`rounds_left − 1`·`rounds_left = 0` → `sweep_end_unresolved`, `measure_feedback` 구성 벤치와 반전 포트 포트별 `.tf` 부호 판정(후보 0·2개 이상 → `inverting_port_undetermined`), swing만 공칭 점 차 거부·ICMR 결과에 `nominal_output_shift_V` 칸 없음(B-45)), §21.3 합격 판정(오라클 결과만으로 PASS 없음 -- 대기 소자 → `PENDING_CONDUCTION`; 동작점 선언 불일치 → `intended_region_mismatch` → `INCOMPLETE`, FAIL로 세는 변형 실패(U1); 선언 없는 소자 비포화 → FAIL), §21.5 `.tf`(개루프 손 회로 A = gm·R, servo 닫힌 변형은 다른 값, `.ac` 첫 점·`1e-3` grep 0), (옛 '선언 triode 두 경우 단언'은 v0.3.1 `intended_region`으로 대체 -- 위 7단계 항목). **(v0.3.4, DV-14·DV-15·DV-16 닫힘 -- 계획 DR-19·DR-20, 기대값은 정의 문장에서 test 작성자가 씀)** (a) `adapters/ngspice/test_tf_gain.py`·`core/test_offset_sys.py` **A_dc 갈래 손 회로**(DR-20 P11; v0.3.5 검증 M5·M6·N2 반영): A = 0 손 회로(입력이 출력에 닿지 않는 VCCS -- 그 출력 고정 `.dc`가 수렴함은 test가 같은 벤치 요청으로 따로 보임)에서 `sim.a_dc = {status: undefined, reason: a_dc_below_resolution}`, `offset_mc.status = unavailable`·사유 `a_dc_undefined`(`detail.a_dc_ref = "/a_dc"`), `sim.offset_sys.reason = a_dc_undefined`이고 **값 칸 없음**(`.dc` 해로 값을 내는 변형 red), **주 경로의 `.dc` 출력 고정 요청 수 = 0**(어댑터 요청 기록; 갈래 발동인데 `.dc`를 부르는 변형 red -- M5); (v0.3.6, DV-17 닫힘) 0이 아닌 작은 A 손 회로: \|A\|·W_rail ≤ δV_out(δV_out = vntol + reltol·\|공칭 V(o)\|, test가 정의 문장에서 계산)이면 `a_dc_below_resolution`, 바로 위(\|A\|·W_rail > δV_out)면 값(양성 대조); 차동 출력 손 회로에서 δV_out = δ_p + δ_n(한 노드만 쓰는 변형 red); \|V\|를 개루프 벤치 `.op` 값으로 쓰는 변형 red; 레일 폭 0 입력 → `rail_width_zero`; `sim.a_dc`에 문턱·δV_out 값 칸 없음; `.tf` 실패 주입 → `reason = tf_failed`(갈래와 다른 이름); 공칭 free 실행 미수렴 주입 → `nominal_unconverged`; `dc_sweep` 없음 → `sweep_direction_undeclared`(σ·offset_sys 모두 그 사유 먼저); `input_dc` 없음 → `offset_sys.reason = input_dc_undeclared`(`.tf`는 정상); `.dc` 수렴 실패 주입(A 정상) → `sim_convergence_failed`(사유가 서로 다름); 단일 출력 기준 미선언 → 실행 전 `reference_undeclared` 거부(시뮬레이터 호출 0); 한 실행에서 **여기 방향 `tf_bench`(port 없음) 요청 수 = 1**(σ·V_id* 둘 다 요청해도 -- 둘째 측정 변형 red), 반전 입력 식별의 포트별 `tf_bench(port=p)`는 따로 센다(M6); `offset_mc`·`offset_sys` 기록에 A 값 칸 없음, compare JSON에 `sim.a_dc`·`sim.offset_sys` 사본 없음(`sim_ref`만); **있는 조건**(N2): forced·iso bias 실행, `offset_mc`·`offset_sys_mv`·PC-10 요청 없는 free 실행에는 `sim.a_dc` 칸 없음·`tf_bench` 요청 0 (b) `core/test_swing_icmr_def.py` **`icm_margin_v` 포트별 식**(v0.3.6, DV-18 닫힘, DR-21): 기대값 = 정의 문장 min_p min(V_p − lo_p, hi_p − V_p)(test 작성자가 손 회로 포트 전압에서 계산) -- c = (1, 1) `declared` 손 회로, **반례 둘**: c = (2, 2)(사영 식이면 값이 1/2 -- 사영 변형 red), β = 1 follower(묶인 반전 입력은 대상 아님 -- 넣는 변형 red); 입력에 `dc_sweep.input_dc`를 바꿔도 `icm_margin_v`가 변하지 않음; `swing_icmr.input_dc_V`·`input_dc_pending` 입력 → E5; ICMR 점 기록에 `m` 칸 없음(`v_in`만, m은 `icmr_coord` 한 함수). **(d) S-OS2 DC 닫힘**(DR-21): DC 되먹임 없는 차동 되먹임 손 회로(v0.3.9 둘째 커밋 문언 -- §21.2 2단계 (0) 판정 '없음' 두 출력 모두; 이상 차동 VCCS(입력 넷은 제어 단자에만 -- 들어오는 엣지 없음) + CMFB + DC 전도 원소 없는 선언 Cf -- current_reuse 꼴)에서 ICMR 벤치 넷리스트에 `tb:icm` 1개·`tb:dmc:a`·`tb:dmc:b` 2개(이득 ±½, 제어 = 출력 짝)가 있고, 각 훑기 점에서 V(in_a) − V(in_b) = V(o_a) − V(o_b)와 ½(V(in_a) + V(in_b)) = cm0 + y·c_s가 §18.3 분해능 안; **(v0.3.7, 검증 필수 4) 판별 가능한 닫힘 부호 test** -- 옛 '짝 부호를 뒤집은 변형(양되먹임)은 수렴 실패 또는 다른 창 → red'는 지운다(DC `.op`는 평형점의 안정성을 가리지 않아 대칭 손 회로에서는 두 부호가 같은 해 d = 0을 낸다): (d-1) **오프셋 손 회로**: 같은 손 회로의 한 입력에 이상 전압원 V_os(test 픽스처 값, 0 아님)를 직렬로 넣고 유한 차동 이득 A_d = d(V(o_a) − V(o_b))/d(V(in_a) − V(in_b)) < 0(\|A_d\| > 1, 손 회로 gm·R)에서, 공칭 점(y = 0)의 출력 차 d_out의 기대값 = 정의(닫힘 V(in_a) − V(in_b) = d_out, 회로 d_out = A_d·(V(in_a) − V(in_b) + V_os))에서 test 작성자가 푼 A_d·V_os/(1 − A_d) -- 부호 = sign(A_d·V_os), 크기 < \|V_os\|; 짝을 뒤집은 변형(닫힘 V(in_a) − V(in_b) = −d_out, 또는 in_a·in_b 짝 바꿈)은 d_out = A_d·V_os/(1 + A_d)로 **부호가 반대**이고 크기 > \|V_os\|라 red (d-2) **구조 단언**(v0.3.7 둘째 커밋 고침, 검증 N3 -- 단일 끝 T(in_a → o_a) 대신 차동 이득): 이미 잰 포트별 `.tf` 네 값 T(p → o)(p ∈ {in_a, in_b}, o ∈ {o_a, o_b})로 A_d = [T(in_a → o_a) − T(in_a → o_b)] − [T(in_b → o_a) − T(in_b → o_b)]의 ½배(d(V(o_a) − V(o_b))/d(V(in_a) − V(in_b)), 두 입력에 ±½ 차동을 건 선형 중첩 -- 새 `.tf` 요청 없음)를 만들고 sign(A_d) · sign(닫힘 계수) < 0(닫힘 계수 = d(V(in_a) − V(in_b))/d(V(o_a) − V(o_b)) = (+½) − (−½) = +1, 넷리스트 `tb:dmc:*` 이득에서 읽음)을 단언 -- 루프 이득 부호가 음수(음되먹임)임을 비대칭 회로에서도 값과 무관하게 단언, `tb:dmc` 이득 부호를 바꾼 변형 red (d-3) c = (2, 2) DC 닫힘에서 ½(V(in_a) + V(in_b)) = cm0 + 2y(구성상 정확 -- v0.3.7 둘째 커밋 고침, 검증 N5: 두 포트 각각은 닫힘 차 ½·Δd_out만큼 어긋나므로 포트마다 y·2를 단언하지 않음, `tb:icm` DC = cm0 + 2y), c = (1, 2) 입력 → `closure_common_asymmetric`(시뮬레이터 호출 0 -- `.tf` 포함), (d-4) `icmr_v` = 포트 창 교집합 폭(v0.3.7, 필수 2): 기대값 = 정의 문장 min_p hi_p − max_p lo_p(test 작성자가 손 회로 포트 전압에서 계산) -- c = (2, 2) `declared` 손 회로에서 m 폭(hi − lo of `icmr_coord`)을 내는 변형 red(값 1/2), 두 포트 창이 어긋나는 DC 닫힘 손 회로(V_os 있음)에서 교집합 폭 < 각 포트 폭이고 m 폭을 내는 변형 red, 빈 교집합 → 음수 폭 그대로(0으로 자르는 변형 red); 차동 출력 + 미선언도 같은 닫힘(옛 `feedback_config_undeclared` ICMR 갈래 → 값이 나옴), 출력 공통모드를 벤치가 묶지 않음(넷리스트에 출력 CM 원 없음), 포트별 `tf_bench(port, NodeV(o))` 4회로 짝을 정함(두 출력의 반전 입력이 같으면 `inverting_port_undetermined`); (c) `core/test_range_confirm.py` **정의 불능 끝**(DR-20 P10): `{undefined: true, record_id}` 지목에서 `record_id`가 없는 기록·다른 `range_input_fp`의 기록·그 metric의 범위 결과가 아닌 기록을 가리키는 변형 → 각각 `range_pointer_rejected`(`check = record`, `point_id: null`); 검사 (1)을 통과한 정의 불능 끝은 (2)~(4)를 하지 않음(점 검사 함수 호출 0); `{undefined: true, reason: …}`(옛 꼴)·`reason` 키를 더한 지목 → E5(`confirmed_range_shape`); 통과한 정의 불능 끝의 `range_final.source.<end>` = 입력 지목과 같은 `{undefined: true, record_id}`(`null` 아님)이고 그 끝을 읽는 metric은 정의 불능; ICMR 정의 불능 끝 → 그 방향 슬루 `slew_step_end_undefined`(OP-10 행); `O/` 안 `confirmed_range`·`range_final`의 `departed`·`reason` 값 칸 `git grep` 0건(gain-budget N6.20 완료 조건 (iii)의 오라클 쪽), `end_cause` 값 ∈ {`rail`, `rail_filter`, `stage1`}만; (v0.3.5, 검증 M2) compare JSON의 `sim_ref.sha256`과 다른 sim.json(또는 없음) → 검사 (1) `record` 거부, OP-3 판부터 compare JSON에 `summary.u6` 사본 없음(보고서는 `sim_ref`로 읽음 -- X-R5 확인 뒤) |

### 옛 문언: 1455행

> | (v0.3.8) 10 정의 대조 -- OP-5 (e) | `core/test_swing_icmr_def.py`(시뮬레이터 호출 0, stub 어댑터) | test 작성자(정의 = gain-budget v6.26 N3.8 문장에서 기대값) | 계획 v0.6.15 DR-23 (2)·O-80 R2: (i) 단일 출력 + 두 입력(MOS gate에만 물림 -- v0.3.9 둘째 커밋 DUT 조건, 검증 N1) + `measure_feedback.kind = declared`·`feedback_passives` = Cf(출력–in−)만(DC 전도 원소 없음 → (0) '없음') → ICMR `icmr_feedback_dc_absent`(`detail.output` = 그 출력 넷), 시뮬레이터 호출 0 (ii) 같은 선언에 출력–반전 입력 `resistor` 하나를 더한 변형(Rf∥Cf) → 거부 안 됨(2단계 (a); v0.3.9 -- 옛 '`Resistor` 하나를 더한' 문언은 저항 위치를 정하지 않아 경로 판정에서 모호, 아래 'OP-5 (0)' 행) (iii) 단일 입력(`dc_sweep.excite` 키 1개) + 단일 출력 + DC 전도 원소 없는 선언 Cf → 거부 안 됨(2단계 (d) 먼저, 회로 그대로, 판정 미호출) -- 갈래 순서를 (e) 먼저로 바꾼 변형 red (iv) 차동 출력 + 두 출력 모두 'DC 되먹임 없음'(입력은 MOS gate에만) → 이 코드 아님(2단계 (c)) |

### 옛 문언: 1354행

> * 정본은 LUT 생성 실행에 묶은 선언 하나다. 묶는 대상(기본 방향, P G-14)은 (LUT가 쓴 모델 파일 sha256 묶음, 생성 시뮬레이터 판)이다.

### 옛 문언: 1358행

>   {"schema": "lut_bin_rule/1", "model_files_sha256": [...], "simulator": {"name", "version"},

### 옛 문언: 1364행

> * 엔진 읽기: OP-7 엔진 card가 `E/lut/` 쪽에서 이 파일을 읽는다(엔진 변경, D-4 승인됨(O-1)). 오라클 능력 기록·오라클 코드 지문은 읽지 않는다.

### 옛 문언: 1355행

> * (v0.3.0, DR-10g, 계획 N3.4 'sha256 정의') **묶음 값의 정의**: 새 선언(검증자 옆 선언·OP-8 새 LUT meta)이 적는 `model_files_sha256` 묶음은 LF 정규화 값이다(규칙 (i) -- 모델 파일은 텍스트). 엔진이 세트 meta의 옛 raw 기록과 이 선언을 대조할 때는 규칙 (ii)(LF 또는 raw로 맞으면 같은 파일, raw만이면 기계 의존)를 쓴다 -- 엔진 쪽 구현은 OP-7 엔진 card와 gain-budget SH-1의 정의(같은 규칙, 계획 N3.7 U-1 (b))를 따른다. 정의가 다른 두 기록값을 서로 견주지 않는다(규칙 (iii)).

### 옛 문언: §11.7 반환 코드

> * **반환 코드**(옛 그대로 + v0.3.2 `PENDING_CONDUCTION`): 0 = 모든 bias 판정 `PASS`/`INCOMPLETE`/`PENDING_CONDUCTION`, 1 = `FAIL`, 2 = `BLOCKED` 또는 **거부**(§7·§11.2의 코드). **오라클 판정 우선순위**(v0.3.2, 계획 N3.9 '합격 판정' -- 1단계 FAIL이면 최종 FAIL, 오라클 결과만으로 PASS 금지): `FAIL`(1단계 FAIL 하나라도) > `PENDING_CONDUCTION`(1단계 FAIL 없음 ∧ `stage2_pending` 소자 있음 -- 같은 결과에 판정 불능 사유가 있으면 `summary.verdict_reason`에 함께 싣는다) > `INCOMPLETE`(대기 소자 없음 ∧ 판정 불능 사유 있음) > `PASS`. **최종 판정**(엔진 쪽 2단계): 2단계 꺼짐 하나라도 → `FAIL` > 2단계 판정 불능 또는 오라클 판정 불능 사유 → `INCOMPLETE` > `PASS`.

### 옛 문언: 1073행

>   * `input_sha256` = 입력 파일 raw sha256(출력 전용, 판정 기록과 입력의 대응 확인용). (v0.3.4) 아래 `range_input_fp`와 축이 다르다(그 항목 끝).

### 옛 문언: §11.7 conduction_definition

>   * `summary.conduction_definition` ∈ {`"threshold_eps1"` -- OP-3 판(OP-5 전): SPICE ID > `off_current_A` 문턱(S-40, DEC-90 (1) 옛 Q5 식), `"seal9_two_stage"` -- OP-5 뒤: 판정 점 봉인 9 식을 두 단계로(§21.1·§21.3, v0.3.1에서 옛 이름 `seal9_point_lut`를 바꿈 -- 사용자 결정 O-50 G5)}. 소비자 = EO-1 판정 기록 '꺼짐 정의 판'(gain-budget N6.20, K-5).

### 옛 문언: §11.7 points·범위 끝 기록

>   * (v0.3.1, OP-5 뒤, 계획 N3.9 '두 단계' 1단계 출력·G-18 '결과 칸') **`conduction.points[]`** = 판정 점마다 `{point_id, kind: "accept" \| "sweep", metric?, x?, temp_c?, m?, v_in?, devices: {<name>: {VDS, VSB, VGS, ID, gm_id, VDSAT, stage1}}}`(v0.3.2: `x` = 훑기 좌표, `m` = 그 점의 측정 좌표(§21.2 4단계 -- follower 구성에서는 x ≠ m; (v0.3.6) **swing 점에만** -- 출력 좌표 원값), `v_in` = (v0.3.6, DV-18 닫힘 -- `icm_margin_v` 포트별 식의 입력) **ICMR 점의** 풀린 입력 포트 전압 `{<입력 넷>: V}`(같은 `OpSweep` 해의 `NodeV` 원값; ICMR 점에는 `m` 칸을 두지 않고 ICMR 측정 좌표 m은 `swing_math.icmr_coord(v_in, c)` 한 함수가 §21.2 4단계 식으로 계산 -- 소비자 = 끝 확정 r·검사 (4)뿐, m 사본 없음; (v0.3.7 둘째 커밋, 검증 필수 A) ICMR metric `icmr_v`·`icm_margin_v`는 m을 읽지 않고 끝 점 기록의 `v_in[p]`로 낸다(§21.2 'metric 값')), `VGS` = 그 점 VGS(off 선언 소자의 'off 유지' 경계 입력, 계획 N3.9 '배선' O-55 V5)). `ID`는 선언 단자 방향 부호(`signed_id`), `stage1` ∈ {`off_reverse`(ID ≤ 0 -- 꺼짐 확정, G3), `stage2_pending`(ID > 0 -- I_off ≤ ε·ID는 2단계), `undefined`(값 없음)}. 온도 조건 요청(§21.1 B2)이면 소자에 `i_off_spice_A`(소자 개별 풀이 값)와 `tol_v_source = "T_j_lut_cell"` 표기가 더해진다. **범위 끝 기록**(v0.3.2: 정본 스키마 하나 -- §21.2 '결과 칸'은 이것을 인용): `sim.swing_icmr.{swing, icmr}` = `{status: "provisional" \| "undefined", lo, hi}`, 끝마다(`lo`·`hi`) `{pass_point_id, fail_point_id, rounds_cap, rounds_left, end_cause: "rail" \| "rail_filter" \| "stage1", departed: [{device, declared, actual}]}`(v0.3.3 셋째 커밋, 정본 하나 -- graph 단일 정본 규칙 1·3: 끝 괄호의 x·m은 `pass_point_id`·`fail_point_id`가 가리키는 `conduction.points[]` 점의 `x`·`m`이 정본이고 끝 기록에 사본을 두지 않는다(옛 `x_pass`·`x_fail`·`m_pass`·`m_fail` 칸 삭제); 끝 확정 분해능 r(옛 `resolution_r`)은 저장하지 않고 소비자(2단계·검사 (4))가 두 점의 m으로 §18.3 식(§21.2 '끝 풀이')을 다시 잰다. `departed` = **1단계**가 그 끝에서 판정한 이탈(어느 소자가 어느 선언 영역을 벗어났는지 -- 계획 G-18 O-54; writer = 오라클 1단계 하나, 꼴 = gain-budget N6.20 (3) '1단계 `departed`와 같은 꼴'). (v0.3.4, DV-16 닫힘 -- 계획 N3.9 '범위 판정' v0.6.13 '2단계 끝의 이탈 소자·정의 불능 사유', 사용자 결정 O-62 (2) P10) **2단계가 정한 끝(전도 쪽 이탈)의 이탈 소자·정의 불능 사유는 오라클 기록에 두지 않는다** -- 정본은 엔진 2단계 판정 기록 `stage2_judgment` 하나(정의·writer·결합 키 (`oracle_record_id`, `metric`, `end`) = gain-budget v6.23 N6.20 '2단계 판정 기록', 인용만; 값은 공용 전도 판정 함수의 소자별 반환에서만). 오라클은 그 기록을 저장·복사·검사하지 않고, 검증자 원인 변화표의 2단계 끝 원인 칸은 그 기록을 위 결합 키로 이 끝 기록과 잇는다. **`end_cause`에 2단계 갈래를 두지 않는다**(계획 DR-20이 design에 맡긴 결정): `end_cause`는 오라클 1단계가 정한 끝의 원인만 담는 칸이고(값 ∈ {`rail`, `rail_filter`, `stage1`}), 2단계 끝의 원인은 엔진 기록에만 있다 -- 2단계 값을 두면 엔진 판정의 사본이 되고(graph 단일 정본 규칙 1·2), 오라클은 2단계 끝을 정하지 않으므로 writer도 없다; `rail_filter` = 레일 밖 노드 필터로 정해진 끝(옛 `rail_filter_end = true`); v0.3.3 둘째 커밋(검증 L3): 옛 `end_cause` 값 `stage2_pending`은 정의가 없어 지움 -- 오라클은 2단계 끝을 정하지 않고 모든 1단계 끝은 `status = provisional`로 2단계를 기다린다 -- 둘 다 검증자 원인 변화표가 읽음). **잠정 표시**(v0.3.2, 계획 R 표 739행 '2단계가 빠진 실행이 확정된 범위 끝으로 읽힌다' 대응): 오라클이 내는 창·`swing_out_v`·`icmr_v`·`icm_margin_v`는 2단계 전 값이라 `status = "provisional"`이고 확정 끝·제약 판정으로 읽지 않는다. (v0.3.3, DV-12 닫힘 -- 계획 N3.9 '범위 판정' 끝 '최종 범위 metric', 사용자 결정 O-59 (3)) **확정 기록**: 2단계가 끝을 확정한 뒤 같은 입력 + `confirmed_range`(§11.6)로 오라클을 한 번 더 부르면(요청마다 확정 왕복 1회 -- 원래 취지와 다름(경미), 승인됨 O-59), 오라클은 네 검사(§7.2 2c) 뒤 compare JSON 최상위 `range_final` = `{status: "final", swing?: R, icmr?: R}`를 낸다. R = `{source: {lo: {record_id, point_id} \| {undefined: true, record_id}, hi: …}, value, constraint}` -- (v0.3.3 셋째 커밋, 정본 하나) 끝 좌표 칸은 두지 않는다: 끝 값 = `source` 지목 점의 `conduction.points[]` 기록 -- swing은 그 점의 `m`, ICMR은 그 점의 `v_in`(v0.3.7 둘째 커밋 정정, 검증 필수 A: ICMR 점에는 v0.3.6부터 `m` 칸이 없다; 값 식은 §21.2 'metric 값' 하나)(지목 기록이 정본, 소비자는 지목으로 읽음 -- 둘째 커밋의 출력 전용 `lo`·`hi` 칸도 사본이라 삭제); (v0.3.4, DV-16 닫힘 -- 계획 DR-20이 design에 맡긴 결정) 지목이 정의 불능인 끝은 v0.3.3의 `null` 대신 **입력 지목과 같은 꼴 `{undefined: true, record_id}`**(검사 (1)을 통과한 그 지목 -- `source`는 입력 지목의 참조 그대로이고 값 칸이 아님; `null`이면 그 끝을 판정한 기록의 참조가 끊겨 검증자가 엔진 `stage2_judgment`와 결합 키로 이을 수 없다), 그 끝을 읽는 metric은 정의 불능(v0.3.3 규칙 그대로). `departed`·`reason` 값 칸은 두지 않는다(gain-budget N6.20 (6), 완료 조건 (iii) `git grep` 0건), `value` = §21.2 'metric 값' 식 그대로(같은 코어 함수 -- 엔진 쪽에 값 식·제약 비교의 사본 없음; 공칭 점 V_o0·포트 전압 V_p(`v_in`)는 원 범위 기록에서 읽음), `constraint` = 그 metric의 선언 제약 판정. `source.*.record_id`가 원 `record_id` 참조다. 확정 실행의 range metric 행(`swing_out_v`·`icmr_v`·`icm_margin_v`)과 그 제약 판정은 `range_final`에서만 오고, 잠정 기록의 값은 확정으로 읽지 않는다(fail-closed). **`range_input_fp`**(v0.3.3, 검사 (1)의 '같은 입력 지문'; 둘째 커밋에서 실효 입력 지문으로 -- 검증 M1) = 정규 JSON(§0 직렬화 규칙) `{input: 입력 JSON − {confirmed_range, sweep_rezoom, provenance}, cli: 진입점 CLI가 덮어쓴 실효 칸 값(이 기록의 bias 하나, simulator·sim-exe 해석 결과, judge 파일 sha256, sat-margin-v, timeout-s, topology sha256·require-topology, omit·short), adapter_fp, descriptor_fp}`의 sha256 -- 결과를 정하는 실효 입력 하나의 지문이다(out_dir·tag·cache-dir처럼 결과를 바꾸지 않는 값은 빼고, `fingerprints` 칸은 이 계산의 입력으로 읽을 뿐 사본을 두지 않음). 모든 compare JSON에 싣는다(출력 전용; 원 범위·재훑기·확정 실행이 같은 값이어야 검사 (1) 통과). (v0.3.4, X-R2 승인 O-61 -- design-validator 지적 반영, graph 단일 정본 규칙 3 '정의가 다른 칸은 다른 축을 적는다') **`input_sha256`과 다른 양이다**: `input_sha256` = 입력 **파일 바이트**(raw)의 지문(축 = 파일 대응 -- 이 기록이 어느 입력 파일에서 났는가; `confirmed_range`·`sweep_rezoom`·`provenance`를 포함하고 CLI·어댑터·기술자는 포함하지 않음, 정규화 없음), `range_input_fp` = **결과를 정하는 실효 입력**의 지문(축 = 측정 동일성 -- 같은 측정의 원 범위·재훑기·확정 실행인가; 실행 종류 칸·`provenance`를 빼고 CLI 실효 값·`adapter_fp`·`descriptor_fp`를 더함, 정규 JSON). 그래서 원 범위·재훑기·확정 실행은 `input_sha256`이 서로 다르고(실행 종류 칸이 다름) `range_input_fp`는 같다 -- 한쪽을 다른 쪽에서 유도하거나 대신 쓰지 않는다(writer 각 하나, 둘 다 출력 전용). **`run_request`**(v0.3.3 둘째 커밋, 검증 M2; 셋째 커밋에서 이름 정리 -- 옛 `range_request`·`range`는 범위 요청이 없는 일반 합격 판정 실행에도 붙어 어긋났음; 출력 전용) = `{kind: "primary" \| "rezoom" \| "confirm", sweep_rezoom?: <입력 칸 그대로>}` -- `primary` = `sweep_rezoom`·`confirmed_range` 둘 다 없는 실행(일반 합격 판정 실행; 범위 요청이 있으면 1단계 훑기 포함), `rezoom` = `sweep_rezoom`이 있는 실행, `confirm` = `confirmed_range`가 있는 실행(둘 다 있으면 E5, `rule = run_request_conflict`). **원 범위 기록** = 같은 `range_input_fp`이고 `run_request.kind = primary`이고 그 metric의 범위 결과가 있는 기록(검사 (2)·(3)·(4)의 기준). **재훑기 끝 기록 형식**: `rezoom` 기록의 `sim.swing_icmr.<metric>`에는 요청된 끝 하나만 `{status: "provisional", <end>: 같은 끝 기록 형식}`으로 싣는다(다른 끝 키 없음; `pass_point_id`·`fail_point_id` 점의 x는 요청 괄호 안, `rounds_left` = 요청 값 − 1, 점은 그 기록 `conduction.points[]`). **기록 파일 이름**(검증 B1, OP-5 병합부터): `<stem>.<kind>.<rid16>.compare.json`(`.compare.md`·`.sim.json`·넷리스트도 같은 줄기), `kind` = `run_request.kind`, `rid16` = `record_id` 앞 16자 -- 같은 `<out_dir>`에서 원 범위·재훑기·확정 실행이 서로 덮어쓰지 않는다(OP-3 판 이름 `<stem>.compare.json`은 OP-5 병합 전까지 그대로). **호출자 의무**(EO-1 판정 배선, 검증 B1): 한 요청(같은 `range_input_fp`)의 모든 실행(원 범위 → 재훑기 → 확정)은 **같은 `<out_dir>`**에 쓴다 -- 다른 폴더면 확정 실행의 검사 (1)이 `record`로 거부한다(fail-closed). 소비자 = 엔진 쪽 2단계 호출 자리(공용 전도 판정 함수를 부름)와 끝 괄호 재요청(`rounds_cap`·`rounds_left`만 읽음) -- 둘 다 OP-5 통합 병합의 엔진 커밋(`Role: code`, 계획 N3.9 '배선' (ii), 사용자 결정 O-55 U2).

### 옛 문언: §11.7 PENDING

>   * (v0.3.1) **`summary.verdict = "PENDING_CONDUCTION"`**(기본안 B-44): 1단계에 FAIL이 없고 `stage2_pending` 소자가 있으면 오라클은 PASS를 내지 않고 이 값을 낸다(계획 N3.9 '합격 판정' -- 오라클 결과만으로 PASS 금지, fail-closed). 반환 코드 = 0(INCOMPLETE와 같은 자리, FAIL 아님). 최종 판정(PASS / FAIL / INCOMPLETE)은 엔진 쪽 2단계가 낸다. 우선순위는 위 '반환 코드' 항목.

### 옛 문언: §11.7 EO-1 읽는 칸

> * EO-1이 읽는 칸 목록(이 밖의 칸은 EO-1 계약이 아니다): 반환 코드, 거부 기록 `code`·`detail`·`stage`, free `compare.json`의 `summary.verdict`·`summary.verdict_reason`·`record_id`·`summary.conduction_definition`·`fingerprints`. (v0.3.1) OP-5 통합 병합부터 엔진 쪽 2단계가 `conduction.points[]`와 범위 끝 기록을 더 읽는다(위 소비자). (v0.3.5) 같은 병합부터 `sim_ref`로 같은 줄기 sim.json의 `sim.a_dc`·`sim.offset_sys`·`sim.offset_mc`·`sim.swing_icmr`를 읽는다(compare에 사본 없음). (v0.3.3) 같은 병합부터 확정 실행의 `range_final`을 읽고(범위 metric 최종 값·제약 판정), **범위 metric의 최종 판정은 `range_final` 하나다**(검증 M6): 원 범위·재훑기 실행의 범위 제약 판정은 잠정이라 그 실행의 `summary.verdict`·`verdict_reason`에 넣지 않고(범위 제약 행은 `provisional` 표시만), 확정 실행의 `summary.verdict`가 `range_final.*.constraint`를 담는다; OP-10 통합 병합부터 같은 확정 실행의 `slew`를 읽는다(지목 생산 = 그 병합의 엔진 커밋, 계획 OP-10 행 U-6).

### 옛 문언: §11.6 지우는 칸

> * **OP-5 병합 때 지우는 칸**(계획 OP-5 '옛 입력 칸 삭제', K-6): `predictions.devices.<n>.off_current_A`(옛 동작점 스칼라, 엔진 `device.dc_off_current` 직렬화)와 `judge.off_current_A`. 두 칸 모두 판정 점 LUT 조회(§21.1)가 대체해 판정에 쓰지 않는다(사용자 결정 O-46 (2)). (v0.3.1) **두 칸 모두 OP-5에서 지운다 -- B-34 닫힘, 사용자 결정 O-50 O2**(계획 N3.9 '옛 입력 칸', X-31): 지운 칸을 넣은 입력은 E5로 거부. 판정에는 §21.1 두 단계(엔진 정본 LUT 함수의 I_off)가 대신한다. 엔진 쪽 `device.dc_off_current` 필드는 graph-consumption 계획이 출력 전용으로 선언한다(계획 OP-5 행 '배선' (iii)). (v0.3.0 기록 문장은 history H7)

### 옛 문언: 1051행

> | `/intended_region` | (v0.3.1, 사용자 결정 O-53 B1 -- 옛 `/declared_triode`를 넓힌 **같은 정본 칸 하나**, 계획 G-18 B1) OP-5와 headroom-chain HC-O 가운데 **먼저 병합하는 쪽**(나중 card는 같은 칸을 쓴다; offset-trim augment_trim이 코드 상태마다 결정적으로 만든 값도 이 칸으로 온다) | 객체(닫힘) `{<device name>: "triode" \| "off"}`(포화 = 키 없음 기본) | 예(빈 객체 허용, 기본안 B-36 그대로) | spec `intended_region`(계획 N3.9 '선언 영역'). 판정 의미(정본 = gain-budget v6.20 N3.8 소자 조건, 사용자 결정 O-54·O-55 U1 -- 이 문서는 인용): **범위 판정**(§21.2)은 모든 MOS가 선언 영역(없음 = 포화: 전도 ∧ VDS ≥ VDSAT, triode: 전도 ∧ VDS < VDSAT, off: 전도 아님)에 머무는 구간이고 훑기 중 이탈 점이 범위 끝(측정 거부 아님). **동작점**(합격 판정 점·범위 측정 공칭 점)에서 **선언 소자**의 실제 영역이 선언과 어긋나면 `intended_region_mismatch`로 그 판정을 **판정 불능**(`INCOMPLETE`, 사유 = 선언 오류; FAIL 아님)으로 집계하고, 선언 없는 소자의 비포화는 설계 실패(합격 판정 FAIL, §21.3). 영역 판정은 §21.1 두 단계 전도식을 쓴다 | 키 ∈ `devices[].name`(아니면 `rule = intended_region_unknown_device`), 값 ∈ {`triode`, `off`}(아니면 E5) |

### 옛 문언: §11.6 /confirmed_range

> | `/confirmed_range` | (v0.3.3, 계획 N3.9 '범위 판정' 끝 '최종 범위 metric'(지목의 정의 자리)·G-19 네 검사·OP-10 '실행 순서', 사용자 결정 O-58 DV-10·O-59 (3) DV-12) OP-5(범위 metric 확정이 먼저 씀, OP-10 슬루가 같은 칸의 `icmr`를 읽음 -- 같은 왕복) | 객체(닫힘) `{swing?: {lo: P, hi: P}, icmr?: {lo: P, hi: P}}`, P = `{record_id: string(sha256 hex 64자), point_id: string}` \| `{undefined: true, record_id: string(sha256 hex 64자)}`(v0.3.4, DV-16 닫힘 -- 계획 N3.9 '범위 판정' 끝 '최종 범위 metric'·G-19, 사용자 결정 O-62 (2): 정의 불능 끝도 그 끝을 판정한 원 범위·재훑기 기록의 `record_id`를 갖는다. v0.3.3의 `reason` 칸(2단계 사유의 사본)은 **삭제** -- 2단계 끝의 정의 불능 사유와 이탈 소자(`departed`)의 정본은 엔진 `stage2_judgment` 하나(정의·writer = gain-budget v6.23 N6.20 '2단계 판정 기록' (2)·(5)·(6), 결합 키 (`oracle_record_id`, `metric`, `end`) -- 인용만); 이 칸과 §11.7 `range_final`에는 `departed`·`reason` 값 칸이 없다. 지목의 끝 = 그 기록 끝 항목의 (`oracle_record_id`, `point_id` \| 정의 불능)의 투영이고(꼴 소유 = 계획 N3.9, 끝 항목 꼴 소유 = gain-budget N6.20 (3)·(4)), 오라클은 엔진 기록을 읽지도 가리키지도 않는다) | 아니오(엔진 쪽 2단계가 끝을 확정한 뒤의 **확정 실행**에서만) | **확정 범위 지목**: 2단계가 끝마다 같은 입력의 오라클 기록(원 범위 기록 또는 `sweep_rezoom` 재훑기 기록)의 `record_id`와 그 기록 `conduction.points[]`의 판정 점 `point_id`를 가리킨다(정의 불능 끝은 `record_id`만). **전압 값은 받지 않는다**(계획 G-19 '계단 끝 전압 값을 받는 입력 칸은 두지 않음' -- 전압은 오라클이 자기 기록에서 읽음, 엔진 창을 받지 않음). 오라클은 §7.2 2c에서 네 검사를 하고(`range_pointer_rejected`), 통과하면 확정 기록(§11.7 `range_final`)을 낸다. 이 칸이 있는 실행은 범위 훑기를 다시 하지 않는다 | 키 ≥ 1, 끝 키 = 정확히 `lo`·`hi`, `point_id`는 비어 있지 않음, P의 키 집합 = 정확히 {`record_id`, `point_id`} 또는 {`undefined`, `record_id`}이고 `undefined`는 `true`만(v0.3.4 -- `reason` 등 다른 키가 있으면 거부)(아니면 `rule = confirmed_range_shape`) |

### 옛 문언: 1054행

> | `/measure_feedback` | (v0.3.1, 사용자 결정 O-50 G4·G2·O-52 확인 1·O-53 A-1, 계획 G-18 'ICMR 측정 구성 -- 그 선언을 받는 입력 칸'·G-19 'β 선언을 읽는 입력 칸') OP-5(ICMR이 먼저 씀, OP-10 슬루가 같은 칸을 씀 -- 정의 하나) | 객체(닫힘) `{kind: "declared" \| "unity_follower", inverting_input?: <net>}` | ICMR·슬루 요청 때(없으면 `measure_feedback_undeclared`) | `declared` = spec 되먹임 구성(β) 선언이 있어 입력 회로·`feedback_passives`가 그 구성. `unity_follower` = 선언 없음(β = 1 기본, 결과에 'β = 1 기본' 표기). **(v0.3.7, 검증 필수 6·사용자 결정 O-78 (3)) EO-1 생산자 매핑**: spec `human.feedback.elements: []`(빈 list)는 `kind = unity_follower`로 옮긴다(`feedback_passives`는 비움) -- 엔진 정의 `E/authoring/spec_elements.py:19-20` "빈 list = 되먹임 수동소자 없음 = β=1 루프"(UD 9번)와 같은 뜻이고, `unity_follower`의 정의(β = 1)와 같다. 비지 않은 list는 `declared`(그 원소 = `feedback_passives`). 이 매핑이 없으면 library 단일 출력 회로가 모두 `declared` + 빈 선언(절단 넷 없음 → §21.2 2단계 (0) 'DC 되먹임 없음'; v0.3.9 둘째 커밋 문언, 옛 'DC 성분 없음') = §21.2 2단계 (e)로 떨어진다(검증 필수 6) -- (e) 해당 회로 0개(O-78 (2))는 이 매핑을 전제로 한다(계획 v0.6.15 N3.9 ICMR 행 '`human.feedback.elements: []`의 뜻'과 같음). `{pending}` 꼴의 매핑은 이 판이 정하지 않는다(K-2·K-6: 확장 칸 생산자는 그 card 통합 병합에서 갱신). `inverting_input` = spec이 반전 입력 포트를 선언했을 때만(O-53 A-1); 없으면 오라클이 `.tf` 부호로 정한다(§21.2, 엔진 값을 받지 않음, 포트 role 이름은 근거로 쓰지 않음). **단일 입력 회로**(`dc_sweep.excite` 키 1개)는 회로 그대로가 구성이라 `kind` 값과 무관하게 덧붙이는 연결이 없다(O-52 확인 1). (v0.3.6, DR-21·DR-22 -- 계획 N3.9 ICMR 행 '구성의 경계와 DC 닫힘'·슬루 행 '시작 동작점', 사용자 결정 O-67 (1)·O-68 (2)·O-69 (1), X-35) **차동 출력**: ICMR = 선언 되먹임에 DC 되먹임이 있으면(v0.3.9 -- §21.2 2단계 (0) 경로 판정, 계획 v0.6.16 DR-24; 옛 'IR `Resistor`·`Inductor` 원소' 종류 판정은 history v0.3.9) `declared` 그대로, 없거나 `unity_follower`(미선언)이면 **차동 모드 DC 닫힘**(§21.2 2단계); 슬루 = 선언 구성 전체(용량 포함), `unity_follower`면 `feedback_config_undeclared`(슬루만 정의 불능); (v0.3.8, DR-23 (1)) DC 되먹임 없는 선언(v0.3.9 같은 판정)의 슬루 = `feedback_config_undeclared`(`why = start_op_deferred`, t = 0 시작 동작점 경로는 gain-budget card AP-1 몫). (v0.3.8, DR-23 (2); v0.3.9 '없음' = 경로 판정) **단일 출력 + DC 되먹임 없는 선언**의 ICMR = `icmr_feedback_dc_absent`(§21.2 2단계 (e)), 단일 입력이면 (d)가 먼저. 구성 종류는 이 칸과 IR 원소 종류에서 오라클이 정하고 새 입력 칸을 두지 않는다 | `inverting_input` ∈ `excite` 키(아니면 `rule = measure_feedback_port`) |

### 옛 문언: §11.6 /sweep_rezoom

> | `/sweep_rezoom` | (v0.3.1, 계획 N3.9 '범위 판정'·G-18 '훑기 구간 입력 칸') OP-5 | 객체(닫힘) `{metric: "swing" \| "icmr", end: "lo" \| "hi", x_pass: number, x_fail: number, rounds_left: integer ≥ 0}` | 아니오(2단계가 끝 괄호를 다시 좁힐 때만) | 2단계(엔진 쪽 끝 괄호 재요청)가 전도로 정해진 끝의 괄호 [마지막 통과, 첫 전도 쪽 이탈](훑기 좌표 x)를 다시 훑게 하는 요청. `rounds_left`는 직전 오라클 결과의 그 끝 `rounds_left`를 **그대로** 돌려준 값(상한 정본 = 오라클 `ZOOM_ROUNDS` 한 곳, 2단계는 사본을 두지 않음 -- 계획 v0.6.10 셋째 커밋 B-1). 오라클은 이 구간을 `ZOOM_POINTS`+1 등분으로 1회 훑고 `rounds_left − 1`을 싣는다; `rounds_left = 0`이면 `sweep_end_unresolved` | `x_pass`·`x_fail`가 같은 입력의 공칭 쪽 순서와 맞음, `rounds_left` ≤ `ZOOM_ROUNDS`(아니면 `rule = sweep_rezoom_bounds`) |

### 옛 문언: §11.6 /slew

> | `/slew` | OP-10 | (v0.3.1) 객체(닫힘) `{node: string}` -- 되먹임 구성은 `/measure_feedback`(ICMR과 같은 칸), **계단 끝 입력 칸 `step_ends_V`는 삭제**(사용자 결정 O-51: 계단 끝 = 같은 입력의 오라클 ICMR 확정 끝, §21.6; 엔진 창을 받지 않음, 계획 G-19) | 슬루 측정 요청 때(없으면 `slew_undeclared`) | 계획 G-19, 정의 정본 = gain-budget v6.20 N3.8 '슬루율 측정 정의'(`7fe555b1` 564행 = 현 tree 565행, 사용자 결정 O-34 (2)·O-50 G2). `node` = 슬루 정의 노드(DEC-65 노드 k). 되먹임 구성·β = 1 기본 표기는 `/measure_feedback`. 계단 끝 = 같은 입력의 확정 ICMR 끝(O-51) -- (v0.3.3) 그 끝은 `/confirmed_range`의 `icmr` 지목으로만 받는다(같은 확정 실행, §21.6; 계획 G-19·사용자 결정 O-58 DV-10·O-59 (3)). (옛 `feedback`·`step_ends_V` 설명은 history H7) | `node` ∈ 회로 넷(`rule = slew_node_unknown`) |

### 옛 문언: 881행

> | 1d | 스키마로 쓸 수 없는 교차 칸 규칙(이 판에서 새로 생긴 칸에만 둔다 -- 옛 의미 검사는 아래 '막힘'으로 그대로): `lut_kind_coverage`(모든 `devices[].kind`가 어떤 `lut_files[].kinds`의 키이고, 모든 `kinds` 키가 어떤 `devices[].kind`임), `reference_rail_voltage`(기준 레일이 하나일 때 그 전압 = 0). 1c를 통과한 입력에만 돌고, 1d 위반도 전부 모아 같은 정렬로 낸다 | `oracle_input_schema_invalid`(`rule` = 규칙 이름, `pointer` = 그 규칙이 가리키는 칸) | 코어 `input_check` |

### 옛 문언: 966행

>   * **K-6 OP-5 병합 때 바뀌는 것**: `predictions.devices.<n>.off_current_A`·`judge.off_current_A` 칸이 스키마에서 지워지고(넣으면 E5와 같이 거부), §11.6 확장 칸이 생긴다. EO-1 생산자의 그 부분 삭제·추가는 같은 통합 병합의 엔진 커밋이다(계획 OP-5 행).

### 옛 문언: §7.2 2c

> | 2c | (v0.3.3, 계획 G-19 네 검사) 입력에 `confirmed_range`(§11.6)가 있으면 끝 지목마다 오라클 자기 기록 읽기(`<out_dir>`의 compare JSON, `record_id` 재측정) → 검사 (1)~(4) 순서. (v0.3.4) 정의 불능 끝은 (1)만(§7 `range_pointer_rejected`) | `range_pointer_rejected` |

### 옛 문언: 487행

> | (규칙 이름 -- 코드 아님) | (v0.3.2, B-46 정정) `intended_region_unknown_device`·`measure_feedback_port`·`sweep_rezoom_bounds`는 `oracle_input_schema_invalid`의 `detail[].rule` 값이다(§11.2 1d, §11.6 교차 규칙 열) -- 별도 오류 코드가 아니다 | 코어 `input_check` |

### 옛 문언: 477행

> | `measure_feedback_undeclared` | (v0.3.1, OP-5·OP-10) ICMR·슬루 요청인데 입력 `measure_feedback`(§11.6)이 없음(측정 단위). (v0.3.6, DR-21 -- 갈래 정리) 이 코드는 **입력 칸 없음** 하나만 뜻한다(ICMR·슬루 공통). 구성이 정의되지 않는 경우는 아래 `feedback_config_undeclared`(슬루만) -- ICMR에는 그 갈래가 없다(차동 모드 DC 닫힘, §21.2 2단계). (v0.3.8; v0.3.9 둘째 커밋 문언 -- 검증 M1-a) ICMR의 단일 출력 + DC 되먹임 없는 선언(§21.2 2단계 (0) 판정) 경우는 `icmr_feedback_dc_absent`(§21.2 2단계 (e))다. (v0.3.7, 검증 nice-to-fix -- 이름 대응) 계획 DR-22 문언 '`measure_feedback_undeclared` 슬루 갈래 = 미선언 차동 출력'은 이 design에서 `feedback_config_undeclared`(`detail.why = differential_undeclared`)가 맡는다 -- 이 코드(`measure_feedback_undeclared`)는 입력 칸 없음만 뜻하므로 같은 경우에 코드가 둘 생기지 않는다 | 코어 |

### 옛 문언: 479행

> | `closure_common_asymmetric` | (v0.3.7, OP-5, 검증 필수 3·사용자 결정 O-78 (3) 승인(비대칭 c fail-closed); 실패 규약 = gain-budget N3.14 '공통 실패 규약'(정의 불능 + 사유 기록) 적용, 코드 이름은 이 design이 붙임 -- (v0.3.7 둘째 커밋, 검증 N2) 옛 인용 'gain-budget 576행 그 구성은 정의 불능(… code 이름은 design)'은 S-OS1 문장이라 이 경우와 무관해 뺐다) 차동 모드 DC 닫힘(§21.2 2단계 (c))이 필요한 ICMR 요청인데 `dc_sweep.common`의 두 입력 포트 계수가 같지 않음(한쪽 0 포함) → ICMR 정의 불능. 거부 시점 = **어떤 시뮬레이터 호출보다 먼저**(`.tf` 짝 식별 전 -- 두 `excite` 포트 이름으로 비교, v0.3.7 둘째 커밋 통일). `detail` = `{ports: [<excite 포트 이름 둘>]}`(넷 이름만 -- 계수 값 사본 없음, 입력 `dc_sweep.common`이 정본). 근거·계획 문언은 §21.2 2단계 (c) '공통모드 가중 조건' | 코어 `swing_math` |

### 옛 문언: 480행

> | `icmr_feedback_dc_absent` | (v0.3.8, OP-5, DV-19 닫힘 -- 계획 v0.6.15 N3.9 ICMR 행·DR-23 (2), 사용자 결정 O-78 (2)·O-79·O-80 R2; 정의 = gain-budget v6.26 N3.8 'ICMR 측정 구성'의 '단일 출력 + DC 성분 없는(용량만) 선언 되먹임' 문장 하나 -- 이 문서는 인용만, 사유 이름은 이 design이 붙임; **v0.3.9 뜻 갱신** -- 계획 v0.6.16 DR-24·gain-budget v6.27 N3.8 표제 '단일 출력 + DC 되먹임 없는 선언 되먹임', '없음' = '선언 되먹임의 DC 되먹임 판정 -- 정의 하나'의 경로 판정(§21.2 2단계 (0)), 소자 종류 판정 아님(O-81 (2)·O-82)) ICMR 요청이 §21.2 2단계 (e)에 해당 → ICMR 정의 불능(fail-closed). 입력이 하나인 회로는 이 코드가 아니다(§21.2 2단계 (d)가 먼저). 거부 시점 = 어떤 시뮬레이터 호출보다 먼저(입력 `measure_feedback`·`feedback_passives` IR 원소 종류·`dc_sweep.excite` 키 수만 읽음). `detail` = `{output: <출력 넷 이름>}`(넷 이름만 -- 원소 목록 사본 없음, 입력 `feedback_passives`가 정본). **엔진 쪽 대응 이름**: `icm_config_feedback_no_dc`(design 41 v1.12.5 `88bc5f2f` 734행 4.7-3b (1)·744행 code 목록; 경로 판정을 담을 v1.12.6은 v0.3.9 작성 때 브랜치 `design/it2c-o79` 머리 `2e60f9c7`에 아직 없음 = **미확인**; **승인 대기**) -- 같은 경우의 엔진 사유이고 이름이 다른 것은 오라클 어휘(§7)를 따른 것; 대응은 design 41 승인 뒤 확정(§19.2 알림) | 코어 `swing_math` |

### 옛 문언: 481행

> | `dc_feedback_judgment_undefined` | (v0.3.9, OP-5·OP-10, 계획 v0.6.16 N3.9 ICMR 행 'DC 되먹임 판정'·DR-24, 사용자 결정 O-82; 정의 = gain-budget v6.28 N3.8 '선언 되먹임의 DC 되먹임 판정 -- 정의 하나'의 '지원 밖 원소'·'차동 출력' 규칙(v0.3.10 둘째 커밋 머리 정렬, 검증 N1 -- 옛 v6.27 '이상 전압원 = 지원 밖' 인용 대체). **범주**(검증 N2): `element_unsupported`·`differential_split` = 판정 정의 불능(gb 정의 문단의 갈래); `bias_not_gate_only` = **입력 계약 전제 위반**(판정 정의가 아니라 오라클 입력 `/bias_voltages`의 '게이트 전용' 전제가 깨짐 -- 지금은 판정을 부를 때만 검사하므로 이 code 아래 둠). 그 검사가 OP-3 입력 계약(§11.2 1d 교차 규칙)으로 옮겨 가면 같은 변경에서 이 `why` 값을 지운다(같은 검사 두 자리 금지)) §21.2 2단계 (0) 판정이 필요한 ICMR·슬루 요청인데 (v0.3.10 -- 계획 v0.6.17 DR-25 (1)(2), 사용자 결정 O-85 (1)(3); 정의 = gain-budget v6.28 N3.8 같은 문단 '지원 밖 원소'·'차동 출력' 규칙 인용) 지원 밖 원소가 있음 = 입력 `/sources`에 `kind = "voltage"`(`detail.why = element_unsupported`, `detail.sources` = 원 이름만; 옛 why 이름 `voltage_source`(v0.3.9)는 history v0.3.10), 또는 차동 출력의 두 출력 판정이 갈림(`detail.why = differential_split`, `detail.present`·`detail.absent` = 출력 넷 이름만 -- DV-21 닫힘), 또는 (v0.3.9 둘째 커밋, 검증 N2) `/bias_voltages` 넷이 게이트 전용이 아님(`detail.why = bias_not_gate_only`, `detail.nets` = 넷 이름만) → 그 측정 정의 불능(fail-closed). 거부 시점 = 어떤 시뮬레이터 호출보다 먼저. 엔진 쪽은 그 전에 S1 `s1_dc_conduction`이 `source_kind_unsupported`로 멈춘다(gain-budget v6.27 N3.8 같은 문단 인용) -- 대응표 §19.2 | 코어 `swing_math` |

### 옛 문언: 482행

> | `inverting_port_undetermined` | (v0.3.1, O-53 A-1; v0.3.6 DV-17 닫힘·차동 출력 짝 -- 계획 N3.9 '전달 판정 분해능'·ICMR 행 '반전 입력 포트 식별') 반전 입력 포트 `.tf` 부호 판정 실패: 출력(차동 출력이면 출력 노드마다)에 대해 음수 후보 0개·2개 이상, 후보 전달이 전달 판정 분해능으로 판정 불능(§21.5 4단계 (4)의 같은 판정 함수), 차동 출력에서 두 출력의 반전 입력이 같은 포트, 레일 폭 0. `detail` = `{why, candidates: {<출력 식>: {<port>: A}}}`(v0.3.6: 옛 `resolution` 칸은 지움 -- 판정 문턱 δV_out/레일 폭은 입력(`Resolution`·레일 선언·공칭 `.op`)에서 다시 잴 수 있는 값이라 저장하지 않음, 새 값 칸 금지 DR-21). ICMR을 내지 않는다(v0.3.6: 옛 '같은 구성을 쓰는 슬루도 내지 않음'은 지움 -- 슬루는 선언 구성 전체, §21.6) | 코어 `swing_math` |

### 옛 문언: 483행

> | `slew_step_end_undefined` | (v0.3.1, OP-10, O-51) 그 방향 계단 끝(같은 입력의 확정 ICMR 끝)이 정의 불능 → 그 방향 슬루 정의 불능. (v0.3.3) 끝은 입력 `confirmed_range.icmr`(§11.6)의 그 끝 지목으로만 받는다 -- 지목이 정의 불능이거나 `confirmed_range.icmr`가 없으면 이 코드(`detail.why` ∈ `pointer_undefined`, `no_confirmed_range`; 계획 G-19 'ICMR 끝 정의 불능이면 그 방향 슬루 정의 불능', 사용자 결정 O-58 DV-10) | 코어 `slew_math` |

### 옛 문언: 484행

> | `range_pointer_rejected` | (v0.3.3, OP-5·OP-10, 계획 G-19 네 검사·N3.9 '범위 판정' 끝 '최종 범위 metric', 사용자 결정 O-58 DV-10·O-59 (3)) 입력 `confirmed_range`(§11.6)의 끝 지목 하나가 오라클 자기 기록과 어긋남 → **거부**(§7.2 2c, 거부 기록 §11.7, 반환 코드 2; 끝 하나라도 어긋나면 실행 전체 거부 -- 부분 확정 없음, fail-closed). `detail` = `{metric: "swing" \| "icmr", end: "lo" \| "hi", record_id, point_id, check}`. `check` = 계획 G-19 검사 번호와 같은 순서: `record`((1) `<out_dir>`의 오라클 compare JSON 가운데 본문을 다시 재어 `record_id`가 같은 기록이 없음, 또는 그 기록의 `range_input_fp`(§11.7)가 이 입력과 다름, 또는 그 기록이 그 metric의 범위 결과·재훑기 결과가 아님), `stage1_pass`((2) `point_id`가 그 기록 `conduction.points[]`에 없음, 또는 공칭부터 지목 점까지 -- 원 범위 기록과 재훑기 기록의 점을 x 순서로 합친 열 -- 1단계 통과가 아닌 점이 있음), `within_stage1`((3) 지목 점의 x가 원 범위 기록 그 끝 `pass_point_id` 점의 x보다 바깥), `bracket`((4) 끝 확정 규칙 -- 계획 N3.9 '범위 판정' 417행 '끝 확정 규칙은 두 단계 전체에 같게 적용': **면제**는 지목 점 = 그 끝 원 범위 기록의 `pass_point_id`이고 그 끝 `end_cause` ∈ {`rail`, `rail_filter`, `stage1`}일 때만(1단계가 이미 확정한 끝을 2단계가 줄이지 않은 경우); 그 밖에는 원 범위 기록과 재훑기 기록의 점을 x 순서로 합친 열에서 지목 점의 바깥 이웃 점과의 측정 좌표 m 차 ≤ r(r = 두 점의 m으로 §18.3 식을 다시 잼, §21.2 '끝 풀이' -- 저장값 없음)이어야 하고, 아니면 이 검사 실패). 새 상수 없음. (v0.3.4, DV-16 닫힘 -- 계획 G-19 '정의 불능 끝에는 검사 (1)을 그대로, (2)~(4)는 점 지목 끝에만', 사용자 결정 O-62 (2)) **정의 불능 끝**(`{undefined: true, record_id}`, §11.6)에는 `record` 검사만 한다 -- 기준은 점 지목 끝과 같다(그 `record_id`의 기록이 `<out_dir>`에 있고 `range_input_fp`가 같고 그 metric의 범위 결과 또는 같은 끝의 재훑기 결과임); `stage1_pass`·`within_stage1`·`bracket`은 점 지목 끝에만. 정의 불능 끝의 `detail` = `{metric, end, record_id, point_id: null, check: "record"}`. (v0.3.5, 검증 M2) 검사 (1)의 '기록'은 compare JSON과 그 `sim_ref`(§11.7)가 가리키는 같은 줄기 `.sim.json`이다 -- sim.json이 없거나 정규 JSON sha256이 `sim_ref.sha256`과 다르면 `record`(범위 끝 기록 `sim.swing_icmr`는 sim.json에 있음). 어느 검사도 사유를 읽지 않는다(지목에 사유 칸이 없음 -- 사유는 엔진 `stage2_judgment`에만, gain-budget N6.20 '2단계 판정 기록') | 코어 `range_confirm` |

### 옛 문언: 476행

> | `intended_region_mismatch` | (v0.3.1, OP-5, 사용자 결정 O-53 B1·O-55 U1) 동작점(합격 판정 점·범위 측정 공칭 점)에서 선언 소자(`intended_region`)의 1단계 영역이 선언과 어긋남 = 선언 오류. 합격 판정이면 판정 불능(`INCOMPLETE`) 집계(FAIL 아님), 범위 판정이면 그 측정 정의 불능. `detail` = `[{device, declared, actual}]` | 코어 `conduction` |

### 옛 문언: 233행

>     conduction.py          (v0.3.0) 판정 점 전도·포화 판정(봉인 9 식, tol_V·I_off 열 읽기, §21.1) -- OP-5

### 옛 문언: §3.1 range_confirm

>     range_confirm.py       (v0.3.3) 확정 범위 지목 네 검사(§7.2 2c)·`range_final` 조립(값 식은 swing_math 호출, 사본 없음)·`range_input_fp`(§11.7) -- OP-5

### 옛 문언: 머리 version

> version: 0.3.10 / plan_version: 0.6.17

### 옛 문언: 10행

> > **Summary**: 계획 `oracle-portability.plan.md` v0.6.17(승인 O-86, master `e87092b3`(계획 병합 plan/o85)); 이전 기준 v0.6.16 = O-83 `dae968ec`(병합 기준 master `8c2357bc`); 그 전 기준 v0.6.15 = O-80 `93a9ff82`(계획 병합 plan/o78), 그 전 기준 v0.6.14 = O-70 (2) `f4d89a23`(계획 병합 `1b4a8536`), v0.6.13 = O-65 `7675f71b`, v0.6.11 = O-60 `b9af2d6f`, v0.6.10 = O-57 `d6bd02b1`)을 오라클 설계로 옮긴다. 계획의 결정은 사용자 결정 O-1~O-71 가운데 이 기능에 닿는 것(§1.1), L-1~L-3, D-1~D-9이다. 이 문서가 정하는 것은 다음과 같다.

### 옛 문언: 머리 Status (v0.3.10 판 전체)

> > **Status**: **design v0.3.10 -- 개정 초안, 독립 검증 대기·사용자 승인 전**(2026-10-21; 넷째 커밋 = 사용자 결정 O-89 (2): `detail.also` 삭제(소비자 0), (b)(c) 함께 해당 시 기록 = `why = input_network_step_deferred` 하나; 셋째 커밋 = 사용자 결정 O-87: (2) X-R6 승인됨, (1) U-1 대응표 `differential_split` 행 -- 엔진 짝 = 예약 이름 `icm_config_feedback_outputs_split`(엔진 S-OS2 일반형 card), 그 전까지 엔진 `icm_config_differential_output_structure`, 갈리면 '정의 경계 불일치'; 둘째 커밋 = v0.3.10 검증(`_drafts/evidence/2026-10-21/oracle_design_v0310_validation.md`, 91/100, 필수 0) N1~N6: v6.28 문언 정렬(1865·481·F-14·1458), `bias_not_gate_only` 범주 = 입력 계약 전제(OP-3 이관 때 같은 변경에서 삭제), MOS kind 경계 대응 행, 출력을 건너는 경로 toy를 design 41에 알림, DV-1~DV-9 상태 표시, (x)(xi) toy 행 나눔; v0.3.10 = 계획 v0.6.17(승인 O-86, master `e87092b3`) DR-25 반영, 사용자 결정 O-85 (1)(3) -- DV-21 닫힘(차동 출력 두 출력 판정이 같을 때만, 갈리면 `dc_feedback_judgment_undefined` `why = differential_split`, gain-budget v6.28 N3.8 인용), 지원 밖 원소 사유 정렬(`why = voltage_source` → `element_unsupported`), §20 OP-5 막음 해소, §18.1 차동 결합 toy (x)(xi), 대응표·§19.6 F-15·F-16·graph 표; `bias_not_gate_only` 그대로; 열린 멈춤 없음; 이력 history v0.3.10; v0.3.9 문장: v0.3.9 둘째 커밋 = v0.3.9 검증(`_drafts/evidence/2026-10-21/oracle_design_v039_validation.md`, 85/100) M1(종류 문언 세 곳·OP-5 행 DV-19 모순)·M2(DV-21 = OP-5 그 갈래 구현 착수 조건, 닫는 경로 = gb N3.8 한 문장 -- 사용자 결정 대기)·N1~N5(toy DUT 조건·공통 게이트·R 분압, `/bias_voltages` 게이트 전용 규칙, 반대쪽 절단 넷, 'DC 전도 원소' 문언, bulk 백로그); v0.3.9 = 계획 v0.6.16(승인 O-83, master `dae968ec`) DR-24 반영, 사용자 결정 O-81 (2)·O-82 -- §21.2 2단계 'DC 성분' 소자 종류 분류를 gain-budget v6.27 N3.8 '선언 되먹임의 DC 되먹임 판정 -- 정의 하나' 인용 + 오라클 자기 구현(방향 의존 그래프, 시뮬레이터 호출 전, §21.2 2단계 (0))으로 바꿈, (a)(c)(e)·1b·§7·§11.6·점검표가 그 판정 하나를 읽음, `Inductor` 문언 삭제, 새 사유 `dc_feedback_judgment_undefined`(이상 전압원), 대응표·§18.1 'OP-5 (0)' 판정 toy 행·§19.6 F-13·F-14·graph 표, 1619행 포인터 닫힘, 새 멈춤 **DV-21**(차동 두 출력 판정이 갈리는 경우); 이력 history v0.3.9; v0.3.8 문장: v0.3.8 = 계획 v0.6.15(승인 O-80, master `93a9ff82`) DR-23 반영, 사용자 결정 O-78 (1)(2)·O-79·O-80 -- §21.6 1b(용량만 선언된 차동 출력 슬루의 t = 0 시작 동작점)와 1단계 입력 망 계단 갈래를 OP-10에서 빼고 gain-budget card AP-1 몫으로 표시(그때까지 `feedback_config_undeclared` `why = start_op_deferred`·`input_network_step_deferred`), `Tran.ic`·`tran_ic_bias_only`는 C10 소비자로 OP-4 소유(둘째 커밋 정정 -- 첫 커밋 'OP-3'은 계획 OP-4 행과 어긋남, v0.3.8 검증 M1; 둘째 커밋은 M1·M2·N1~N4도 반영), DV-19 닫힘(새 코드 `icmr_feedback_dc_absent`, 정의 = gain-budget v6.26 N3.8 인용, 단일 입력 먼저 -- R2), DV-20을 C10 몫으로 줄임; 이력 history v0.3.8 행; v0.3.7 문장: v0.3.7 = v0.3.6 design-validator 보고(`_drafts/evidence/2026-10-21/oracle_design_v036_validation.md`) 필수 2~6 반영, 사용자 결정 O-78 (3) -- `icmr_v` = 포트 창 교집합의 폭(정의 하나, m 좌표 hi − lo 삭제), DC 닫힘의 c 대칭 조건과 비대칭 c fail-closed(`closure_common_asymmetric`), 판별 가능한 닫힘 부호 test, 인용 위치 정정, `human.feedback.elements: []` → `unity_follower` 명시, graph 점검표 §19.6; 둘째 커밋 = v0.3.7 검증(`_drafts/evidence/2026-10-21/oracle_design_v037_validation.md`, 86/100) 필수 A·B와 N1~N8·C10 문장·r 백로그 메모(history v0.3.7 둘째 커밋 행); 필수 1·7(§21.6 1b)·DV-19는 O-78 (1)(2)로 계획 v0.6.15 대기라 손대지 않음; v0.3.6 문장: v0.3.6 = 계획 v0.6.14(승인 O-70 (2), 병합 `1b4a8536`) N7.5 DR-21·DR-22 반영 -- DV-17·DV-18 닫음, S-OS2 차동 모드 DC 닫힘 벤치, `icm_margin_v` 포트별 식, X-R3~X-R5 승인 표시, 슬루 t = 0 시작 동작점 벤치, 착수 실측(current_reuse 입력 망 없음 -- 사용자 보고), 설계 선택별 실현 가능성 표 §19.6(사용자 규칙 2026-10-21); 새 멈춤 DV-19·DV-20; v0.3.5 문장: v0.3.5 = v0.3.4 design-validator M1~M6·N1~N4와 design↔계획 gap(`_drafts/evidence/2026-10-21/oracle_design_v034_plan_gap.md`) 반영 -- `sim.a_dc`·`sim.offset_sys` 기록 자리(sim 단계, compare는 `sim_ref` 참조), 사유 집합·순서, 새 멈춤 DV-17(A 판정 분해능 식)·DV-18(OQ-10 (나) V_icm 동치 불성립), 사용자 확인 X-R3~X-R5; v0.3.4 문장: 승인된 계획 v0.6.13(O-65 -- DR-19·DR-20)·gain-budget v6.23(DEC-23 'A_dc 정의 불능 갈래'·N3.8 판정 분해능·N6.20 '2단계 판정 기록')과 사용자 결정 O-61~O-63으로 DV-14·DV-15·DV-16 닫음 -- §21.5 `a_dc` 기록(`.tf` A 한 측정, 갈래 먼저, 사유 셋), §21.4 4단계, §11.1 `swing_icmr` 두 칸 삭제·§21.2 V_icm, §11.6 `confirmed_range` 정의 불능 끝 `{undefined: true, record_id}`, §7 검사 (1) 범위, §11.7 `range_final.source`·`end_cause`, §19.4 X-R1·X-R2 승인 표시와 지문 축 차이; v0.3.4 당시 남은 멈춤 0 -- history 판 표 v0.3.4·v0.3.5). v0.3.0~v0.3.3 판의 Status 문장은 history H8로 옮겼다.

---

## v0.4.1 -- 검증 M1~M9 반영 (2026-11-03, 브랜치 `design/op0`)

재판정: (1) M8 고칠 문언의 `role == 'circuit'`은 library topology에 그 키가 없어(netlist·passive_elements·ideal_sources 전부 None) IR 용어(`tb:`·`measurement_load` 제외)로 바꿈, 측정 결과는 재현 (2) M3에 없던 ε 눈금 정정: v0.4.0 ε = r은 옛 `S·f ≤ r²·cum`과 달라 동일성을 깸 → ε = r² (3) M3 비트 동일 갈래는 옛 확장 입력을 덮지 못함 → PG-5, 평탄 구간 거부 위험 → F-24. M5는 단일 입력과 겹치지 않게 입력 포트 둘 이상으로 좁힘, M4는 `slew_rate_v_per_s` 단일 선언 갈래를 더함.

### 옛 문언: M1 test

> | (v0.4.0) 10 정의 대조 -- OP-5 servo ICMR | `core/test_swing_icmr_def.py` | test 작성자 | 손 회로 차동·단일 입력: V_cm 좌표 세 metric 값, servo 부호 = `.tf`(role 이름을 뒤바꾼 변형도 같은 값), 고정 오차 초과 변형 → `icmr_output_lock_violated`, 입력 셋 → `icmr_input_ports_unsupported`, 선택 상대 항 칸 → E5 거부 |

### 옛 문언: M2

> free bias 실행이고 `offset_mc`·`offset_sys_mv`·PC-10 가운데 하나라도 요청됐을 때만 한 번(여기 방향 `tf_bench`(port 없음) 1회 -- 반전 입력 식별용 포트별 `tf_bench(port=p)`는 §21.2의 별도 측정); forced·iso bias, 셋 다 요청 없음,

### 옛 문언: M2 정본 목록

> §21.0~§21.3·§21.6·§21.7 일부

### 옛 문언: M3 부등식

> 바로 앞 구간 기울기 ≥ n̂(꼬리에서 완만해지지 않음)이고 n̂ > 1이어야 한다.

### 옛 문언: M3 갈래

> f_hi는 T(f_hi) ≤ ε·I(f_hi)(ε = `noise.rel_resolution`)를 푼 닫힌 식 f_hi = f0·(S(f0)·f0/((n̂ − 1)·ε·I))^(1/(n̂ − 1))로 직접 정하고,

### 옛 문언: M3 test

> | (v0.4.0) OP-B1 상한 | `core/test_bounds_derived.py` | test 작성자 | 상한 도달 toy마다 fail-closed 사유, 네 이름 + `NYQUIST_K_MAX` `git grep` 0, N4 비교(상한에 닿지 않은 입력 비트 동일) |

### 옛 문언: M4·M5 4단계

> 추종 판정 = 이상 폐루프 목표(계단 × 1/β) 양 끝 검사(상위 N3.8), 어기면 그 방향 정의 불능.

### 옛 문언: M4~M6 test

> | (v0.4.0) 10 정의 대조 -- OP-10 DR-27 | `core/test_slew_def.py` | test 작성자 | 해석해 슬루 회로: 20~80 % 기울기, 피드스루 가장자리 변형이 값을 바꾸지 않음, 계단 = 같은 덱 범위, 범위 정의 불능 → `follower_range_undefined`, 선언 step 범위 밖 → `slew_step_out_of_range`, 무릎 보고 칸 |

### 옛 문언: M5·M6

> **단일 출력 + DC 되먹임 없는 선언**(0단계 판정; v0.3.9 둘째 커밋 문언 -- 검증 M1-b, 옛 '용량만 선언'): 같은 입력의 ICMR이 `icmr_feedback_dc_absent`(§21.6 0단계 (e))라 확정 끝이 없어 2단계 `slew_step_end_undefined`로 끝난다(따로 사유를 두지 않음).

### 옛 문언: M6 §7

> (c) (v0.3.8, DR-23 (1)) 차동 출력 + DC 되먹임 없는 선언(

### 옛 문언: M5 §7

> 검사 순서 (a) → (b) → (c), 모두 어떤 시뮬레이터 호출보다 먼저

### 옛 문언: M7

> 같은 입력 `sim.swing_icmr.swing` 끝 기록(§11.7, 둘째 `.dc` 없음, 값 사본 없음) -- 밖이면

### 옛 문언: M7 test

> | (v0.4.0) 10 정의 대조 -- OP-5 DR-28 | `core/test_offset_sys.py` | test 작성자 | §21.4 toy, `.dc` 요청 0 단언, 엔진 U-107 toy와 같은 판정 |

### 옛 문언: M8

> 코어 `conduction.kcl_zero_current_devices(ir)`가 회로 IR 연결에서 집합을 독립 유도한다(엔진 값을 쓰지 않음).

### 옛 문언: M8 test

> | (v0.4.0) 10 정의 대조 -- OP-5 판정 한 단계 | `core/test_conduction.py` | test 작성자 | §21.1 깨진 변형 전부 |

### 옛 문언: M9 §8.1

> work_dir: str, timeout_s: float|None, cache_dir: str|None) -> ResultBundle

### 옛 문언: M9 §9

> 모델 묶음 sha256 정렬 목록 ∥ 실행 인자). 같은 키는

### 옛 문언: M9 §11.7

> `fingerprints = {adapter_fp, descriptor_fp, capability_record_id}`(계획 FR-P9.

### 옛 문언: M9 §16

> 찾으면 어댑터 실행 설정 `RunConfig.compat = 선언 compat`으로 실행하고,

### 옛 문언: M9 완료

> `_helpers_bins.py` 변경 0(`git diff`).

### 옛 문언: M4 §7

> | `bin_rule_undeclared` | (v0.4.0, OP-7, §16)

### 옛 문언: version

> version: 0.4.0

### 옛 문언: Status

> > **Status**: **design v0.4.0 -- 개정 초안, 독립 검증·design↔계획 gap·사용자 승인 대기**

---

## v0.4.2 -- 재판정 R1·R2, oracle Minor 둘, 계획 v0.6.26 (2026-11-03, 브랜치 `design/op0`, master `c0b41eee` 병합)

### 옛 문언: R1 규칙

> 입력 회로 원소(`tb:` 테스트벤치 원소와 `measurement_load` 제외)로 그래프를 만든다.

### 옛 문언: R1 측정 표지

> 계획 Q-S9와 일치).

### 옛 문언: R1 test

> | (v0.4.0) 10 정의 대조 -- OP-5 판정 한 단계 | `core/test_conduction.py` | test 작성자 | §21.1 깨진 변형 전부; 다리 규칙 toy: 직렬 MOS 다리 → 집합에 듦, 고리 안 MOS → 안 듦, `off` 소자와 직렬 → 듦 |

### 옛 문언: R2 §18.3

> **격자 밀도**: 연속 두 적분 차 ≤ ε까지 격자를 2배,

### 옛 문언: R2 §7

> (v0.4.0, OP-5, OP-B1) 연속 두 적분 차 > 분해능인 채 유도 상한 도달

### 옛 문언: R2 test

> | (v0.4.0) OP-B1 상한 | `core/test_bounds_derived.py` | test 작성자 | 상한 도달 toy마다 fail-closed 사유, 네 이름 + `NYQUIST_K_MAX` `git grep` 0, N4 비교(상한에 닿지 않은 입력 비트 동일); noise: 완만해지는 꼬리 → 거부, 한 극 꼬리 → 통과, T ≤ ε·I 입력 → f_hi 불변 |

### 옛 문언: Minor ref

> **`sim.offset_sys.ref_minus_servo_ref_V`** = V_ref − s0(§21.2 ICMR servo 목표) 기록 하나(판정에 쓰지 않음, 새 문턱 없음; 소비자 = 검증자 원인 변화표, 출력 전용 선언).

### 옛 문언: Minor x=0

> ICMR의 x = 0 점 정확도는 위 U-103 점별 확인이 맡는다

### 옛 문언: plan_version

> plan_version: 0.6.25

### 옛 문언: version

> version: 0.4.1

### 옛 문언: Summary

> 계획 `oracle-portability.plan.md` v0.6.25(승인 = 상위 gain-budget v6.38.6 사용자 결정 O-216, plan/v6386 HEAD `e71aa597`; 대조 기준 master `c8ecc4e7`); 이전 기준 v0.6.17

### 옛 문언: Status

> > **Status**: **design v0.4.1 -- 검증 `wt/_drafts/evidence/2026-11-03/design_b56_validation.md` M1~M9 반영, 재검증·design↔계획 gap·사용자 승인 대기**(위임 A-21·A-22; 재판정 3건 = history v0.4.1). v0.4.0: **개정 초안**

### 옛 문언: Status PG

> §19.2 'v0.4.0 계획 공백' PG-1~PG-4.

### 옛 문언: PG-1

> * **PG-1 OP-3 판 합격 판정 대 EO-1(중요)**: 공통 선행 순서 = OP-3 → EO-1이고 OP-5는 그 밖이다. 그래서 EO-1 판정 실행은 OP-3 판 `threshold_eps1`(소자별 `off_current_A` 문턱, 칸 없으면 `INCOMPLETE`)로 돈다. 그런데 상위 O-205로 엔진 `device.dc_off_current`가 삭제되고 EO-1 생산자는 낼 값이 없다. 계획은 칸 삭제를 OP-5 몫으로만 적었다. 선택지(사용자·계획 몫): (a) 판정 한 단계(§21.1·§21.3)와 칸 삭제를 OP-3 또는 EO-1 앞 새 card로 앞당김 (b) EO-1 판정 범위를 OP-5 뒤로 (c) 필드 삭제를 OP-5 뒤로. 작성자 판단: (a)가 원칙(O-205·fail-closed)에 맞으나 계획 변경이다.

### 옛 문언: PG-3

> * **PG-3 OP-7 표지·선행**: d_questions §5.2 'EO-1 행 표지 한 줄'은 첫 단계 계획 개정 몫이다. 옛 design 선행 'XRUN-F1 C'는 계획 OP-7 행에 없어 §20에서 뺐다(계획이 이김).

### 옛 문언: PG-4

> * **PG-4 낡은 계획 문구**: OP-0 행 'plan_version 0.6.22'·'offset-trim v0.6.2'(현행 0.6.25·0.6.4), N3.9 ICMR 행 '끝 = 확정 끝 점(N3.9 범위 판정 확정 범위 지목)', N3.5.1 기준 커밋, N7.5 DR-26 끝의 슬루 '차동 모드 닫힘'. 의미 변화 없음, 다음 계획 개정 때.

### 옛 문언: K-6

> (v0.4.0 **계획 공백 PG-1**, §19.2: OP-3 판 입력의 이 칸들과 공통 선행 안 EO-1의 관계)

### 옛 문언: §20 OP-3

> 합격 판정은 PG-1 표지 그대로 `threshold_eps1`.

### 옛 문언: §20 OP-5

> 엔진 커밋 = 생산자 갱신뿐.

### 옛 문언: §20 OP-7

> | OP-7 | §16(v0.4.0), §7.2 8b, §8.3 끝 `compat_modes`, §18.1 v0.4.0 행 | OP-3 | 계단 없음. EO-1 판정 앞(§16 'EO-1 순서' -- 거부 규칙의 귀결). 경계 재측정 = 검증자, WB-1이 reader. 옛 선행 'XRUN-F1 C'는 계획에 없어 뺌(PG-3) |

### 옛 문언: §16 조각

> 측정 스크립트는 `oracle_run`을 지나지 않고 어댑터 실행 설정에 호환 모드를 직접 준다.

### 옛 문언: §20.1

> ### 20.1 card별 범위 대응표(v0.4.0, 계획 N5.1 v0.6.25 대 이 문서)

### 옛 문언: §20.1 행

> | OP-0 | `plan_version`, 독립 검증, 승인 | 머리(0.6.25), 검증·승인 대기 |

### 옛 문언: §11.7 EO-1

> (판정은 오라클이 끝냄 -- 엔진 쪽 2단계 호출 자리·재요청·`stage2_judgment` 없음, 상위 N6.20 EO-1, 소비자 0)

## v0.4.3 -- card OP-7 선언 조각·OP-1b 멈춤 항목 반영, 계획 v0.6.27 (2026-11-04, 브랜치 `docs/cards1104d`)

근거: card `20261104-op7a`·`20261104-op1b` S-1~S-5, 상위 위임 A-53(SPICE 범위 해석)·A-54. 독립 판정 전.

### 옛 문언

> * 형식(기본안): `<lut 폴더>/bin_rule.json` =
>
> "rule": "lower" | "upper", "evidence": {"points": [{"L", "W", "chosen_bin"}], "measured_by", "date"}}
>
> 기존 LUT = 옆 선언 `<lut 폴더>/bin_rule.json`(이 card, 검증자가 **지금 공유 LUT의 L 축 bin 경계 앵커 점 전부**에서
>
> 측정에 쓴 모드를 `evidence`에 씀)
>
> (A-13 -- 측정 방법 미확인, 재측정이 안 되면 선언을 쓰지 않고 멈추고 보고)
>
> 남은 것 = 옆 선언 기록 조각의 측정 방법 미확인(A-13 -- 아래 §16, 재측정이 안 되면 선언을 쓰지 않고 멈추고 보고).
>
> 옆 선언 조각은 어댑터가 생기기 전이라 측정 방법 미확인(재측정이 안 되면 멈추고 보고).

## v0.4.4 -- 독립 판정 card 묶음 d 반영 (2026-11-04, 브랜치 `docs/cards1104d`)

근거: `wt/_drafts/evidence/2026-11-04/cards_d_validation.md` M1(S-29·§12.5·§16 '32' 표지, 값은 그대로 두고 정정 한 줄), M2(§11.5 `exe`), M4(§16 조건), m12·m14, 위임 A-56.

### 옛 문언

> | `process.ngspice_exe` | `simulator.exe` | 옮긴 뒤 삭제 |

## v0.4.5 -- 재판정 반영 (2026-11-04, 브랜치 `docs/cards1104d`)

근거: `wt/_drafts/evidence/2026-11-04/cards_d_validation.md` '재판정' R1·R2·r6, 위임 A-57. `model_includes` 줄은 판정 문언 `:220-228` 대신 이 브랜치 실측 `:220-228`으로 적었다.

### 옛 문언

> 폭·병렬 배수·확산 기하·코너·온도·포함 파일·바이어스 부호 규약·`ID` 단위를 그 세트 기록에서 읽고, 칸이 없거나 뜻을 못 정하면 그 점은 판별하지 않는다.
>
> noise·mismatch는 `cap_npz_sha256`으로 그 세트에 묶인다.

## v0.4.6 -- §16 선언 미적용 시점 (2026-11-04, 브랜치 `design/wb1`)

근거: 상위 판정 `wt/_drafts/evidence/2026-11-04/design_b3_validation.md` V3, 상위 위임 A-62 D2. **원래 취지와 다름**: 옛 문언보다 엄함. 계획 v0.6.28 D-4와 같이 고침.

### 옛 문언

> 그래서 같은 모델로 일부 세트만 다시 만들어도 선언이 그대로 맞고, 모델이나 판이 다른 세트에는 적용되지 않아 경계 위 L이 거부된다(`bin_tie_undeclared`, P D-4).
