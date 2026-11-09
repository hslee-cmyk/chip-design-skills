# spec card 초안 -- library spec 반영: Q-S2(PM >= 70도 3회로)·Q-S3(current_reuse 잡음 <= 450 µVrms 차동)

작성 2026-10-14. 읽기 전용 실측: 저장소 master `af10c9b`(`C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills`). 수정·커밋·실행 안 함.
아래 줄 번호는 모두 af10c9b 기준. 'S' = `skills/analog-gmid-design/`, 'E' = `S/gmid_engine/`, 'L' = `S/assets/library/`.
'추정'이라고 쓴 것은 실행하지 않고 코드만 읽고 낸 판단이다.

---

## 1. 결정 원문 (원문 그대로 인용)

| 출처 | 원문 |
|---|---|
| `wt/_drafts/user_decisions.md:367` | `- 2026-10-14 step-2 Q-S: 사용자 "Q-S는 모두 권고대로, Q-S2는 70도 이상". Q-S1 (라) 2 반영 뒤 엔진이 sf 동시 실현 불가(front 비어 있음)를 내는지 먼저 확인, 확인되면 (가) sf noise_excess_th 보고만. Q-S2 PM 목표 pm_ss_deg >= 70 deg: sf(SP-3), two_stage_ota(SP-3), two_stage_ota_sf(미선언). Q-S3 current_reuse 잡음 C1 <= 450 uVrms 차동 출력(41 7.1 대역), Q-N11 B와 함께. spec 파일 반영 시점: U17 1-b 병합 뒤(1-b 판정 기준선 보호), step 2 착수 전 별도 커밋.` |
| `wt/_drafts/engine/STEP2_DESIGN_GAPS_DECISION_PACKAGE.md:732-733` | `### 결정 반영 (2026-10-14)` / `- Q-R1·Q-N1/2/3/4/5/8/9/11·Q-S1/S2(PM >= 70 deg)/S3·N12·N13·결정 10 전부 사용자 확정 -- 원문은 `_drafts/user_decisions.md` 2026-10-14 항목들. ...` |
| 같은 파일 `:698`(질문 Q-S2) | `**Q-S2** (spec) PM 목표가 없는 3회로(sf SP-3, two_stage_ota SP-3, two_stage_ota_sf 미선언)의 PM 값은? → **권고: 세 회로 모두 값을 정해 달라 -- 미정이면 매크로가 45° 바닥으로 풀려 Cc 가 상자 하한에 붙는다(실측 3/3).**` |
| 같은 파일 `:699`(질문 Q-S3) | `**Q-S3** (spec) current_reuse 잡음 spec 은? → **권고: C1 ≤ 450 µVrms(차동 출력 명시, design 41 §7.1 대역 그대로), 단 Q-N11 과 함께 결정.**` |
| 같은 파일 `:645-649`(§9.3 S3 근거) | `후보: **C1 ≤ 450 µVrms 차동(권고)**, ...` / `spec 문구에 '차동 출력' 명시 필요(단일 출력이면 CM 바이어스 잡음 3.35 mV 가 지배).` |

참고 메모(pm_ss_deg ≥ 70 sf·two_stage_ota·two_stage_ota_sf / current_reuse C1 ≤ 450 µVrms differential)는 원문과 **일치**한다.

**대상 회로 이름**: 'sf' = `sf_pushpull_output_opamp`(근거: 같은 결정 패키지 §9.1·§9.2 가 sf {gain ≥ 65 dB, noise_excess_th ≤ 2, 입력 DC 0.9 V}로 적고, 이 값들은 `L/sf_pushpull_output_opamp.sizing_spec.json:96-98·151-153` 와 같다. `two_stage_ota_sf` 는 결정문에 따로 나온다). 파일은 `*.spec.json` 이 아니라 `L/<회로>.sizing_spec.json` 이다.

## 2. 현재 spec 값 (af10c9b)

| 파일 | 키(줄) | 현재 값 |
|---|---|---|
| `L/sf_pushpull_output_opamp.sizing_spec.json` | `pending_constraints[0]` (171-176) | `{"metric": "pm_ss_deg", "decision": "SP-3"}` |
| 〃 | `compensation_targets.pm_target_deg` (184-186) | `{"pending": "SP-3"}` |
| 〃 | `constraints` (93-170) | pm_ss_deg 없음(gain 65, gbw 60e6, rout 1000, offset_excess √2, icm_margin 0, noise_excess_th 2, area 2e-8) |
| `L/two_stage_ota.sizing_spec.json` | `pending_constraints[0]` (111-116) | `{"metric": "pm_ss_deg", "decision": "SP-3"}` |
| 〃 | `compensation_targets.pm_target_deg` (124-126) | `{"pending": "SP-3"}` |
| 〃 | `constraints` (59-110) | pm_ss_deg 없음 |
| `L/two_stage_ota_sf.sizing_spec.json` | `pending_constraints[0]` (112-117) | `{"metric": "pm_ss_deg", "decision": "SP-3"}` -- **결정문 '미선언'과 다름: 제약 표지는 있다** |
| 〃 | `compensation_targets` (118-125) | `gbw_target_hz` 만(`value_from_file two_stage_ota#gbw_target_hz`), **`pm_target_deg` 키 자체가 없음**(결정문 '미선언'은 이 칸을 가리킨다) |
| `L/current_reuse_telescopic_ota.sizing_spec.json` | `constraints[]` noise (267-278) | `{"metric": "noise_out_int_vrms", "op": "<=", "value": 0.0003, source{kind user_spec, record "...결정 Q11 -- 파일럿 폐루프 적분 출력 잡음 <= 300 uVrms(...)", decided 2026-10-08, origin "paper", citation "Xie & Chen 논문 Table I 적분 출력 잡음 300 uVrms"}}` -- view 키 없음 |
| 〃 | `constraints[]` pm (163-172) | `pm_ss_deg >= 70`(이미 있음, 2026-10-07 결정) -- 이번 범위 밖, 문안 본보기 |
| 〃 | `compensation_targets.pm_target_deg` (302-307) | `{"value_from_constraint": "pm_ss_deg", source{kind reference}}` -- 3회로 문안 본보기 |

## 3. metric catalog 존재·정의

| metric | 레지스트리(`E/metrics/registry.py`) | 단위·영역·뷰 | 판정 |
|---|---|---|---|
| `pm_ss_deg` | 43줄 `("pm_ss_deg", "deg", "ss", "loop", None, LoopAnalysis, "phase_margin_deg")` | deg, ss, loop | 있음. 뷰는 적지 않는다(`E/authoring/spec_constraints.py:19-20` -- feedback·ports 에서 유도). 3회로 모두 `feedback.elements = []` 이므로 β = 1 포트 루프(`spec_views.py:98`). |
| `noise_out_int_vrms` | 54줄 `("noise_out_int_vrms", "v", "ss", "transfer", None, NoiseAnalysis, "out_int_vrms")` | **V**(µV 아님 -- 450 µVrms = `4.5e-4`), ss, transfer | 있음 |

**'차동(differential)' 표현**: 새 metric·단위 **불필요**. 잡음 제약에 view 를 적지 않으면 기본 포트 뷰가 쓰이고(`spec_constraints.py:15-18`, `_view` 205줄),
기본 포트 뷰의 감지는 출력 포트가 role `differential_output_p/_n` 쌍이면 `SenseDecl(Vop, Vom, "differential")` 이다(`E/authoring/spec_views.py:81-83`).
current_reuse ports = Vip(differential_input_p)·Vim(differential_input_n)·**Vop(differential_output_p)·Vom(differential_output_n)**(topology.json `ports`).
잡음 계산은 그 감지 행을 그대로 쓴다(`E/metrics/ss_metrics.py:291-296` `_noise_sense` port → view.sense, 330-332 `ledger.sense(entry, sense)`, `E/metrics/noise_integral.py:5` '출력 = 전달 뷰의 감지').
즉 **현재 엔진의 이 제약은 이미 v(Vop) − v(Vom) 차동 적분 잡음**이다(pilot `noise_basis.md:65` 차동 757.9 µV 가 엔진 값과 같은 정의). 명시 선언 모양(`{ac_excite, sense_p, sense_n, sense_mode: "differential"}`)도 계약에 있다(`spec_constraints.py:17-18`).

→ **엔진 변경 필요 없음**(값 변경 + 출처 문구 + 선택적 명시 view 만).

## 4. 영향

### 4.1 S0 키·지문
- spec 지문: `spec_fp` = 섹션 지문들의 지문(`E/authoring/spec_model.py:13`, `SECTION_GROUPS` 307-320 -- `constraints_fp` = constraints + pending_constraints, `compensation_fp` = compensation_targets).
  S0 키 입력 `_s0_inputs` 에 `spec_fp` 가 들어간다(`E/pipeline/stage_a.py:200-205`), 입력 파일 sha 는 `_s0_sources`(212-) 의 키 메타.
- 바뀌는 S0 키: 4회로(sf_pushpull, two_stage_ota, two_stage_ota_sf, current_reuse) -- 새 S0 스냅샷 1회 계산. 나머지 5회로 키 불변.
- 현재 파일 sha256(af10c9b 작업트리 바이트): sf `504e96f7…9de6`, two_stage_ota `9d3ec0f5…862b`, two_stage_ota_sf `a5c82d9e…ce33`, current_reuse `d63a8037…a9dd`.
  저장소 안에서 이 sha 를 리터럴로 박은 곳은 없다(gmid_engine·tools·assets·docs grep 0건).
- two_stage_ota_sf 는 `value_from_file two_stage_ota#…` 로 two_stage_ota 파일을 참조하므로 two_stage_ota 변경만으로도 해석 결과가 따라간다(참조 대상은 gbw 뿐이라 이번 PM 값과는 무관).

### 4.2 test 기대값 (grep 실측, 고칠 주체 = test 작성자)

| test | 위치 | 지금 | 바뀐 뒤(손 집계) |
|---|---|---|---|
| `E/tests/integration/test_spec_library_load.py` `TABLE` | 75-85 | sf (7,7,6), two_stage_ota (5,5,7), two_stage_ota_sf (6,6,6), current_reuse (13,12,11) | sf **(8,8,5)**, two_stage_ota **(6,6,6)**, two_stage_ota_sf **(7,7,6)**, current_reuse (13,12,11) 불변. pending 열은 `{"pending": X}` 객체 수(`_markers`) -- pending_constraints 항목은 세지 않는다 |
| 〃 `ID_TOTALS`·`ID_TOTAL_SUM` | 95-97 | `"SP-3": 2`, 합 60 | SP-3 키 삭제(0), 합 **58** |
| 〃 `UNITY_LOOP` | 370-373 | ngcc·nmcnr 2개 | + `sf_pushpull_output_opamp: ((("vin_n",-0.5),("vin_p",0.5)), SenseDecl("vout",None,"single_ended"))`, `two_stage_ota: (… , SenseDecl("OUT",None,"single_ended"))`, `two_stage_ota_sf: (… , SenseDecl("vout",None,"single_ended"))` (ports role 손 읽기: 3회로 모두 vin_p/vin_n 차동 입력 + 단일 출력 1개) |
| 〃 `test_other_circuits_have_no_loop_view` | 464-467 | 'pm_ss_deg 제약이 없는 6회로' | 대상 3회로로 줄어든다(common_gate, folded, pushpull) -- docstring '6회로' 수정 |
| 〃 `DESIGN_U5_ROWS` 파일럿 행 | 536-541 | `("noise_out_int_vrms", "<=", 300e-6)` + 주석 529 '300 µVrms = 300e-6 V' | `450e-6`. 출처 날짜 대조(`KEEP_OLD_SOURCE` 근처, 548-)가 결정일 2026-10-08 을 보는지 확인 -- 새 행은 2026-10-14 |
| 〃 `test_ci10_*`(파일럿 pm) | 383-436 | 파일럿 pm 뷰 | 영향 없음(파일럿 pm 불변) |
| `E/tests/integration/test_j_rules_library.py` docstring 표 + `test_stage_a_with_library_spec` | 25-33, 150-160 | '나머지 6회로 \| 없음 \| ok' | 3회로가 'pm_ss_deg unity' 행으로 옮겨간다. 단계 A status 는 **추정 ok 유지**(two_stage·two_stage_sf 는 루프 역할 없음, sf 는 composite_diode_internal 만 -- ngcc·nmcnr 처럼 정지를 푸는 쪽 변화이지 새 정지 원인이 아님). 재측정 필요 |
| `E/tests/integration/test_s0_layer_9circuits.py` `test_stage_reports_unchanged_from_base`·`test_s0_field_values_unchanged_from_base` | 343-385, 기준선 `fixtures/u17_1b_s0_baseline.json` | base a5d8ccb 기준선 | **4회로 기준선 재측정 필요(추정)**: 3회로는 단계 A `views`(pm 루프 뷰 추가) sha 와 S0 `graph/start` macro·records·rungs·start.row 지문(PM 목표 45° 바닥 → 70°)이 바뀐다. current_reuse 는 잡음 값을 단계 A·출발 구간이 읽지 않으므로(`E/search/iv_noise.py:67` 은 metric 존재만 본다) 보고서·S0 필드 값은 **추정 불변**, S0 키만 바뀜 |
| `E/tests/integration/test_blas_thread_determinism.py` `test_single_thread_start_fp_matches_base` | CIRCUIT = two_stage_ota(30), 같은 기준선 | 기준선 | two_stage_ota 출발 지문 변경 → 같은 기준선 재측정에 묶임(추정) |
| `E/tests/search/test_iv_matching_l.py` | 38-100 `real_case("two_stage_ota")` | 출발 구간 실경로 | 대부분 상대 비교(OFFSET vs OFFSET_TIGHT)라 영향 낮음, 절대값 단언이 있으면 바뀔 수 있음(추정, 실행 확인 필요) |
| `E/tests/generality/test_spec_generators.py` | 108-122 `constraints[0]` 를 고쳐 씀 | gain 제약 | **새 pm 제약을 constraints 맨 앞에 넣지 말 것**(끝 또는 gbw 뒤에 추가하면 영향 없음) |
| `E/tests/authoring/test_spec_load.py:61` | 합성 `pm_target_deg pending SP-3` | library 무관 | 영향 없음 |

### 4.3 단계 A/B 결과 영향 (실행 안 함, 전부 추정)
- 3회로 PM: 출발 목표 `_target`(`E/search/iv_context.py:35-40`)은 compensation_targets 값 → 없으면 `pm_ss_deg >= v` 제약 값 순으로 읽는다. 지금은 pending 이라 None → 매크로가 `PM_FLOOR_DEG`(45°) 바닥 + 기록 `pm_floor_pole_at_ugf`(`E/search/macro_poles.py:19-20, 234-235`). 바뀌면 70° 목표 → 비주극점을 UGF 위로 더 밀어 Cc·2단 gm·전류 출발값이 바뀌고 `pm_floor_pole_at_ugf` 기록이 사라진다(결정 패키지 §9.2 'Cc = 상자 하한' 현상 해소 기대).
- sf: 손 x3 은 PM 41° 로 GBW 60 MHz 를 맞췄다(§9.2). 70° 는 같은 GBW 에 더 큰 전류·Cc 를 요구 → Q-S1(sf 동시 실현 불가) 경향이 **더 강해질 수 있다**(추정). Q-S1 확인은 결정대로 step 2 반영 뒤.
- current_reuse 잡음: 판정 c = (450 − v)/분해능. r2 v ≈ 719.8~757.9 µV, 분해능 440 µV(`noise_basis.md:19`) → c ≈ −0.61 ~ −0.70(현 300 기준 −0.95). 판정은 여전히 ±1 안이라 Q-N11 B(분해능 정의) 반영 전에는 보류에 가깝다.
- 단계 B·외층 판정 대상 제약 수: 3회로 각 +1(pm_ss_deg 판정 추가).

### 4.4 design·계획·계약 문서의 해당 수치 언급

| 문서 | 줄 | 지금 문구 | 갱신 |
|---|---|---|---|
| `docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md` §9 Q5 표 | 1373 | two_stage_ota '아직 없는 값: PM(SP-3)' | PM ≥ 70(2026-10-14 Q-S2) |
| 〃 | 1374 | two_stage_ota_sf '아직 없는 값: PM' | 〃 |
| 〃 | 1377 | sf_pushpull '아직 없는 값: PM(SP-3)' | 〃 |
| 〃 | 1372 | 파일럿 '이번에 올리는 것: 잡음 ≤ 300 µVrms' | ≤ 450 µVrms 차동(2026-10-14 Q-S3) |
| 〃 Q11 결정 표 | 1366 | `noise_out_int_vrms ≤ 300 µVrms` | 결정 기록이므로 원문 보존 + '2026-10-14 Q-S3 로 450 µVrms 차동' 각주(이력은 history) |
| `docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md` §7.1 회로별 선언 | 1500 | `noise_out_int_vrms <= 300e-6`, 출처 논문 Xie & Chen Table I | `<= 450e-6`, 감지 = 차동 출력 v(Vop)−v(Vom)(기본 포트 뷰), 출처 user_spec 2026-10-14 Q-S3, 근거 `noise_basis.md` §4(c) C1 |
| 〃 C-2 결정 인용 | 1209 | "... 300 uV 는 OTA 소자 잡음 적분 ..." | 결정 원문 인용이라 보존 |
| `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` DEC-96 | 296 | 파일럿 `noise_out_int_vrms <= 300 µVrms` | 450 µVrms 차동, 경위는 history |
| `E/authoring/SPEC_CONTRACT.md` 5절 표 | 236-246 | sf 6(6)·two_stage 5(5)/7·two_stage_sf 6(6)/6 … (**이미 낡음**: test TABLE 은 sf 7, ngcc 7, nmcnr 8) | 실측 표로 갱신(sf 8(8)/5, two_stage 6(6)/6, two_stage_sf 7(7)/6, ngcc 7(7), nmcnr 8(8)) |
| 〃 U5 문단 | 252, 259 | 파일럿 `noise_out_int_vrms <= 3e-4`, '남은 표지 총 60' | 450e-6, 총 58 |
| 〃 | 263 | 'SP-3 2'(U5 전 기록) | 기록 문단이라 보존 |

## 5. 출처

| 수치 | 근거 | 원문 논문 |
|---|---|---|
| pm_ss_deg ≥ 70 (sf·two_stage_ota·two_stage_ota_sf) | 사용자 결정 2026-10-14 Q-S2(`user_decisions.md:367`). 파일럿 PM 70(2026-10-07 항목 2, `user_decisions.md:131`)과 같은 값 | **없음** -- 논문 값이 아니라 사용자 지정 값. (회로 출처: sf = P.E. Allen Lecture 26 Page 26-6, 웹 aicdesign.org/wp-content/uploads/2018/08/lecture26-140625.pdf -- 로컬 PDF 없음; two_stage_ota = Maloberti p.28-33 -- 로컬 PDF·링크 없음; two_stage_ota_sf = Allen Lecture 26 Page 26-5 -- 로컬 PDF 없음. 이 문헌들의 PM 값은 이번 결정의 근거가 아님) |
| noise_out_int_vrms ≤ 450 µVrms 차동 (current_reuse) | 사용자 결정 2026-10-14 Q-S3(`user_decisions.md:367`), 근거 `wt/_pilot_current_reuse/noise_basis.md` §4(c) 표 C1(156줄: 재설계점 c_k8m4s2 SPICE 438.5 µV @ 282 µW, 다른 spec 전부 통과, 여유 2.6 %), §2 71줄(단일 출력이면 3.37 mV -- '차동' 명시 근거), 적분 대역 = design 41 §7.1 | 옛 값 300 µVrms 의 출처 Xie & Chen, "A 126uW Current-Reuse Telescopic OTA with Class-AB Output Stage"(UT Austin) Table I -- **로컬 PDF 없음**(fpga 폴더 전체 *.pdf 검색 0건, `_heldout/CANDIDATES.md` 에 없음), **웹 링크 기록 없음**(topology.json `source` 에 URL 없음). 450 은 논문 값이 아니다 |

## 6. card 초안

### 6.1 id·범위
- id(제안): `spec-qs2qs3` -- library spec 3+1 파일 값 반영 + 그 값을 단언하는 test 기대값 + 계약/design/plan 수치 문구. **엔진 코드 변경 없음.**
- 포함: Q-S2(3회로 PM ≥ 70), Q-S3(current_reuse 잡음 450 µVrms 차동).
- 제외: Q-S1(sf noise_excess_th 보고만 -- 결정상 step 2 반영 뒤 엔진 확인이 먼저), Q-N11 B(분해능 정의 -- step 2 엔진 card), SP-2·기타 pending.
- 시점: 결정 '1-b 병합 뒤, step 2 착수 전 별도 커밋'. 1-b 병합(eadb729)·결정 10(af10c9b) 완료 → 지금 착수 가능.

### 6.2 변경 파일
1. `L/sf_pushpull_output_opamp.sizing_spec.json`
   - `constraints` 끝(area_search_m2 뒤)에 추가:
     `{"metric": "pm_ss_deg", "op": ">=", "value": 70, "source": {"kind": "user_spec", "record": "user_decisions.md 2026-10-14 step-2 Q-S \"Q-S는 모두 권고대로, Q-S2는 70도 이상\" -- Q-S2 PM 목표 pm_ss_deg >= 70 deg (SP-3 해소)", "decided": "2026-10-14"}}` (view 키 없음)
   - `pending_constraints` 의 SP-3 항목 삭제(목록이 비면 키 삭제 -- `HUMAN_OPTIONAL`, `E/authoring/spec_schema.py:29`).
   - `compensation_targets.pm_target_deg` = `{"value_from_constraint": "pm_ss_deg", "source": {"kind": "reference"}}`(파일럿 302-307 과 같은 모양).
2. `L/two_stage_ota.sizing_spec.json` -- 1 과 같은 세 변경.
3. `L/two_stage_ota_sf.sizing_spec.json` -- 같은 제약 추가(값 70 리터럴, 아래 U-2 기본안), pending_constraints SP-3 삭제, `compensation_targets.pm_target_deg` **새 키** 추가(value_from_constraint).
4. `L/current_reuse_telescopic_ota.sizing_spec.json` noise 제약(267-278):
   `"value": 0.00045`, source = `{"kind": "user_spec", "record": "user_decisions.md 2026-10-14 step-2 Q-S \"Q-S는 모두 권고대로\" -- Q-S3 C1: 폐루프 적분 출력 잡음 <= 450 uVrms, 차동 출력 v(Vop)-v(Vom)(기본 포트 뷰 감지), 적분 대역 design 41 §7.1 그대로. 근거 _pilot_current_reuse/noise_basis.md §4(c). 옛 값 300 uVrms(Xie & Chen Table I, 2026-10-08 Q11)를 대체", "decided": "2026-10-14"}` -- `origin: paper`·`citation` 삭제(논문 값 아님). view 는 기본안대로 적지 않는다(U-1).
5. test(작성자 = test author, 기대값은 위 4.2 손 집계·사용자 결정 문장에서): `test_spec_library_load.py`(TABLE·ID_TOTALS·UNITY_LOOP·no_loop_view docstring·DESIGN_U5_ROWS·주석), `test_j_rules_library.py`(표·파라미터), 그리고 `fixtures/u17_1b_s0_baseline.json` 의 해당 회로 키 재측정(U-3 승인 조건).
6. 문서: `E/authoring/SPEC_CONTRACT.md` 5절, design 40 §9 표(1372-1377), design 41 §7.1(1500), plan DEC-96(296) -- 규칙·수치만, 경위는 history(H 문서).

### 6.3 interface card (test 작성자용 공개 계약 -- 소스 열람 없이 쓸 수 있는 것만)
- 로더: `gmid_engine.authoring.load_sizing_spec(spec_path, topology_doc, metric_catalog)` → `SizingSpecDoc`. 제약은 `doc.constraints`(각 `metric`, `op`, `value`, `view`, `judged`), 결정 대기 제약은 `doc.pending_constraints`((metric, decision) tuple), 결정 대기 표지는 `doc.pending`(각 `.decision`), 보상 목표는 `doc.compensation_targets`((key, decl) -- decl.value 는 참조 해석 뒤 값).
- 바뀐 뒤 기대(oracle (d) 사용자 결정 문장):
  - sf_pushpull_output_opamp·two_stage_ota·two_stage_ota_sf: `pm_ss_deg >= 70` 제약 정확히 1개, judged True, view.mode == "loop", view.beta == "unity", view.weights == ((입력 n 포트, −0.5), (입력 p 포트, +0.5)), view.sense == SenseDecl(<단일 출력 포트>, None, "single_ended"), view.cuts 비어 있음. `pending_constraints` 에 pm_ss_deg 없음. `compensation_targets` 의 `pm_target_deg` 값 70. 어느 표지에도 "SP-3" 없음.
  - current_reuse_telescopic_ota: `noise_out_int_vrms <= 4.5e-4`(단위 V) 정확히 1개, judged True, source.kind user_spec·decided "2026-10-14", origin 없음. view.mode == "port", **view.sense == SenseDecl("Vop", "Vom", "differential")**(차동 명시의 실행 증거). 다른 제약 불변.
  - library 전체: "SP-3" 표지 0, 표지 합 58.
- 실 LUT 를 쓰는 test(단계 A/B·S0 기준선)는 실행 결과로 기대값을 만들지 않는다 -- 기준선 재측정은 test 작성자가 엔진 밖 스크립트로(옛 `wt/_scratch_u17_1b_tests/baseline.py` 방식) 재고 그 스크립트 경로를 픽스처 주석에 남긴다.

### 6.4 완료 조건
1. 4파일 로드 0 hit, 두 번 로드 `spec_fp` 동일.
2. 6.3 기대가 모두 test 로 고정되고 통과(차동 sense 단언 포함).
3. 전 test 통과(`OPENBLAS_NUM_THREADS=1` 판정 환경). 재측정한 기준선 키는 4회로 것만 바뀌고 나머지 5회로 기준선 바이트 불변(diff 로 확인).
4. 단계 A 재측정 보고(독립 판정 기록): 3회로 `pm_floor_pole_at_ugf` 기록 사라짐·macro PM 목표 70, 단계 A status 변화 유무, current_reuse S0 필드 값 지문 불변 여부(추정 검증).
5. 문서 4곳 수치 갱신, 이력은 history 에만. `grep -rn "SP-3[^0-9]" L/` 0건, `grep -rn "300e-6\|0.0003" L/ E/tests` 0건(의도된 기록 문단 제외 목록 명시).
6. graph 정본 확인: 새 함수·상수 없음(spec·test·문서만) -- G-8 lint·소유표 변화 없음 확인.

### 6.5 사용자 확인 항목 (기본안 있음 -- 이의 없으면 기본안으로 진행)
- **U-1** 잡음 '차동 출력' 명시 방법: 기본안 = 제약에 view 를 적지 않고(엔진 기본 포트 뷰가 이미 차동 v(Vop)−v(Vom)) 출처 문구에 '차동'을 적고, test 가 sense_mode == differential 을 단언. 대안 = 명시 view `{ac_excite:{Vip:0.5, Vim:-0.5}, sense_p:"Vop", sense_n:"Vom", sense_mode:"differential"}`(mode 가 port → transfer 로 바뀌어 다른 소비자 영향 재측정 필요). → 기본안으로 해도 되나?
- **U-2** two_stage_ota_sf 의 PM 값: 기본안 = 자기 파일에 70 리터럴(user_spec, 결정문이 회로마다 70 으로 지정). 대안 = gbw 처럼 `value_from_file two_stage_ota#pm_ss_deg` 참조. → 리터럴로 해도 되나?
- **U-3** S0 기준선(`fixtures/u17_1b_s0_baseline.json`) 4회로 키 재측정: 의도된 입력(spec) 변경에 따른 기준선 교체이지 기준 완화는 아니지만, 계획 §14(작성자 ≠ 검증자, 기준 변경)에 걸리므로 승인 요청. 조건 = 4회로 키만, 나머지 5회로 바이트 불변, 측정 스크립트는 엔진 밖·test 작성자 소유. → 승인하나?
- (확인만) Q-S3 'Q-N11 B와 함께': 기본안 = spec 값은 지금 별도 커밋으로 넣고(결정의 반영 시점 문장), 판정 의미는 Q-N11 B(step 2 엔진 card) 반영 뒤 생긴다고 보고에 적는다.
