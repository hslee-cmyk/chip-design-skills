---
template: plan
version: 0.1
---

# offset-trim Planning Document

> **Summary**: gm/ID 엔진(`skills/analog-gmid-design/gmid_engine/`)에 **입력 offset 전류 주입 trim**을 넣는다. 엔진은 기존 수반(adjoint) offset 해석으로 주입 노드 후보와 순위를 계산해 제시하고, 결정적 변환 `augment_trim(topology, trim_decl)`으로 trim DAC 소자를 붙인 **파생 topology**를 만든다. 사용자가 그 파생 topology를 승인(ratify)한 뒤에만 사이징한다. DAC는 차동 전류 steering 이진 가중 구조이고, 범위·LSB·bit 수·단위 소자 크기는 spec 선언값(V_res, k)과 엔진 해석값(σ_in, 주입 전달 t)에서 유도한다.
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code
> **Status**: 계획 초안 v0.1 (2026-10-15). 사용자 승인 전이다. 근거는 사용자 결정 T-1~T-4(원문 `wt/_drafts/user_decisions.md` '## offset trim 착수 결정 (2026-10-15 사용자 "권고대로 해")')와 원문 7편(N8)이다.
> **이력**: 경위, 제안 원문 요지, 원문 검토 기록, 버전 이력은 [offset-trim.history.md](offset-trim.history.md)에 둔다.
> **상위 계획**: [gain-budget-gmid-sizing.plan.md](gain-budget-gmid-sizing.plan.md). 이 계획은 그 계획의 원칙(N1.4 NFR, N2 결정)을 그대로 따른다. 충돌하면 상위 계획이 이기고, 충돌은 N7에 올린다.

---

## N0. 문서 안내

* **담는 것**: 목적·범위, 확정 결정, 요구, 엔진 반영 구조와 규칙, 적용 판정 방법, 단계(card 후보)와 완료 조건, 위험, 원문 근거, 열린 결정.
* **담지 않는 것**: 경위와 원문 검토 과정. 이것은 history에 둔다.
* **값 원칙**: 이 문서에는 수치 상수를 두지 않는다. 범위 배수 k, 잔여 offset V_res, trim 온도는 사용자 spec 값이다. 나머지는 엔진 해석값과 LUT, PDK 선언에서 유도한다. 원문 수치(N8)는 인용하지 않는다.
* **인용 규칙**: 코드는 `파일:줄`로 인용하고 base `cfe2e31` 기준이다. 경로는 `skills/analog-gmid-design/`을 뺀 상대 경로이고, `E/`는 `gmid_engine/`이다.

### N0.1 용어

| 용어 | 정의 |
|---|---|
| σ_in | 엔진 `offset_in_sigma_mv`의 값이다. 모든 MOS의 게이트 오차원을 수반 해석으로 출력에 보내 합친 분산을 차동 이득 A_dm으로 입력 환산한 1σ 값이다. 이것이 trim 전 랜덤 offset이다(N3.0 F-1) |
| V_sys | 엔진 `offset_sys_mv`의 값이다. 봉인 DC 동작점의 계통 offset이다(N3.0 F-1) |
| z[n] | 감지 관측에 대한 수반 해의 노드 n 성분이다. 노드 n에 넣은 전류 I가 출력에 주는 값은 z[n]·I다(N3.0 F-1) |
| t_pair | 노드 쌍 (n_p, n_n)에 차동 전류 +δ/−δ를 넣을 때 입력 환산 전달이다. 정의는 t_pair = (z[n_p] − z[n_n]) / A_dm이고 단위는 V/A다 |
| I_FS | DAC 차동 출력 δ의 양쪽 끝 크기다(δ ∈ [−I_FS, +I_FS]) |
| I_LSB | 코드 한 칸의 δ 변화다 |
| I_T | steering 총전류다. I_A + I_B = I_T이고 코드와 무관하다(T-3) |
| trim_dac | trim 소자에 주는 구조 역할이다. 신호 경로 셀·블록 역할에서 빠지고, 바이어스·잡음·용량·mismatch 기여는 남긴다 |
| 파생 topology | `augment_trim`이 원본 topology와 trim 선언에서 결정적으로 만든 topology다. 원본 topology.json 파일은 바뀌지 않는다 |

---

## N1. 목적·범위·요구

### N1.1 목적

랜덤 offset 사양을 입력쌍 면적(L·W)만으로 맞추는 대신, 작은 입력쌍과 trim DAC 조합을 엔진이 사이징할 수 있게 한다. trim 뒤 잔여 offset이 spec 목표 안에 들고, trim 범위가 trim 전 offset 분포를 spec 수율 배수만큼 덮는 해를 (전력, 면적) front 위에서 찾는 것이 목적이다.

### N1.2 범위

| 포함 | 제외 |
|---|---|
| 정적 offset의 전류 주입 trim이다. 패키지 뒤 한 온도에서 코드를 한 번 정한다고 가정한다 | 코드 저장 방식(OTP·퓨즈·레지스터)과 디지털 디코더 면적이다(T-1) |
| 주입 노드 후보 계산·순위·제시와 `augment_trim` 변환, 승인 흐름이다 | trim 알고리즘, 측정·자기 trim 비교기, 생산 시험 흐름이다(Staudt 2011 §II.B의 비교기 잡음 모델 포함) |
| 차동 전류 steering DAC의 범위·LSB·bit 수·분할(이진/상위 thermometer)과 단위 소자 W·L·gm/ID다 | chopper·auto-zero 같은 동적 offset 제거다(Lu 2007, Zhou 2017 Fig.3) |
| trim 소자의 DC 바이어스·headroom·잡음·극점·mismatch 기여를 기존 해석으로 그대로 계산하는 것이다 | laser·저항 trim, 입력쌍 소스 저항 trim(Zhou 2017 Fig.2), 입력 단자 level shifter trim(Mohamed 2013)이다. 비교 근거로만 쓴다 |
| offset spec 의미 전환이다. trim이 선언된 회로에서 σ_in은 덮어야 할 분포가 된다 | drift trim이다. CMOS에서는 한 온도 offset trim이 drift를 보정하지 않는다(Kay 2024 §1.2, PDF p.7). 엔진에 drift metric은 없다(N3.0 F-6). 보고서에 이 한계를 적는다 |
| 9회로 library의 적용 판정과 일반성 측정이다 | held-out 회로 확장이다. 상위 계획 U-75 뒤에 한다 |

### N1.3 기능 요구

| ID | 요구 |
|---|---|
| FR-T1 | **spec trim 선언**(T-1): 회로 spec에 trim 선언을 새로 둔다. 필드는 잔여 offset 목표 V_res, 수율 배수 k(또는 수율 목표, N7 D-2), trim 온도 조건이다. 값과 출처는 사용자 몫이다. 선언이 없으면 엔진 동작은 지금과 비트 동일이다 |
| FR-T2 | **주입 노드 후보·순위**: 입력 셀 drain 쪽 차동 노드 쌍마다 t_pair, 그 쌍의 headroom 여유, 잡음 영향을 계산해 순위표로 낸다. 후보를 정하는 규칙은 구조 규칙이고 회로 이름을 쓰지 않는다(N3.2). 결과 JSON에 기록한다 |
| FR-T3 | **`augment_trim(topology, trim_decl)`**: 결정적 순수 변환이다. 선택된 노드 쌍에 DAC 소자를 붙인 파생 topology와 출처 기록을 낸다. 출처 기록에는 원본 topology 해시, trim 선언 해시, 변환 규칙 해시, 선택 근거(순위표 행)를 넣는다. 원본 파일은 고치지 않는다(T-2) |
| FR-T4 | **승인 흐름**(T-2): 파생 topology는 사용자 승인 기록이 있을 때만 사이징 입력이 된다. 승인 기록의 해시와 그 실행에서 다시 만든 파생 topology 해시가 다르면 fail-closed로 정지한다 |
| FR-T5 | **구조 역할 `trim_dac`**: S1·S1v가 trim 소자를 신호 경로 셀·블록 역할(`input`·`load`·`mirror`·`tail_source` 등)에 넣지 않는다. DC writer, 잡음원, MNA 용량 스탬프, offset 해석의 mismatch 원에는 그대로 포함한다 |
| FR-T6 | **DAC 설계 규칙**(N3.4): 범위·LSB·bit 수·분할·단위 소자를 유도하고 제약과 metric으로 판정한다 |
| FR-T7 | **offset spec 의미 전환**(N3.6): trim이 선언된 회로에서는 랜덤 offset 판정이 'σ_in ≤ spec'에서 'trim 범위 ≥ 덮을 분포' 그리고 '잔여 ≤ V_res'로 바뀐다. 출발값 규칙 `iv_matching_l`도 같이 바뀐다 |
| FR-T8 | **코드 양 끝 DC 검사**: DAC 코드의 양 끝에서 모든 소자의 포화 여유를 검사한다(N3.5) |
| FR-T9 | **보고**: trim metric, 순위표, 승인 기록 id, 'drift·1/f는 trim 대상 아님' 문구, 합격 조건(온도)을 결과 JSON과 보고서에 적는다 |

### N1.4 비기능 요구

상위 계획 N1.4의 NFR-1~NFR-6과 N2.2 작업 원칙을 그대로 적용한다. 이 기능에서 특히 다음을 강제한다.

| ID | 요구 |
|---|---|
| NFR-T1 | **topology 무관**: 후보 규칙, 역할 유도, 설계식은 구조와 해석값만 읽는다. 회로·소자·넷 이름 리터럴은 금지다(상위 구조 test 규칙 E). 9회로에서 선언이 없으면 무동작임을 측정해 일반성의 증거로 낸다 |
| NFR-T2 | **상수 발명 금지**: 범위 배수, DNL 여유, LSB 여유에 경험 상수를 박지 않는다. 사용자 선언값(V_res, k)을 참조하거나(`value_from_constraint` 계열) 정의에서 유도한다. 원문 수치는 인용하지 않는다(N8) |
| NFR-T3 | **graph 단일 정본**: 노드 수반 벡터 z, t_pair, 후보표, DAC 유도값은 Circuit State Graph 필드다. 각 필드는 writer가 하나이고 입력 버전을 함께 기록한다(상위 DEC-83). 파생 topology는 S0 입력이며, 실행마다 원본과 선언에서 다시 만든다(디스크 사본을 재사용하지 않음, 상위 NFR-2 실행 사이 재사용 폐지와 정합) |
| NFR-T4 | **결정성**: `augment_trim`은 같은 입력이면 비트 동일한 출력을 낸다. 소자·넷 이름 생성은 정렬된 규칙을 따르고, 원본 이름과 충돌하면 거부한다(상위 NFR-4) |
| NFR-T5 | **만들면 배선**: 후보 계산, 변환, 승인 검사, metric은 엔진 진입점의 실제 경로에 배선한다. test만 통과하고 배선되지 않은 함수는 완료가 아니다. 배선이 불가능하면 사용자 승인을 받는다 |
| NFR-T6 | **작성자≠검증자**: design 문서는 독립 검증 agent가 검증한다. test·기대값·판정 기준은 구현자가 소유하지 않는다. 판정자는 SPICE 오라클이다(코드 스윕 + Monte-Carlo, N6) |

---

## N2. 확정 결정

| ID | 결정 | 출처 |
|---|---|---|
| T-1 | spec 필드: trim 뒤 잔여 offset 목표 V_res, 수율 배수 k(또는 수율 목표), trim 온도 조건을 spec에 새로 둔다. 값은 사용자 몫이다. 코드 저장 방식(OTP·퓨즈·레지스터)은 아날로그 sizing 범위 밖이다 | 사용자 2026-10-15 "권고대로 해" |
| T-2 | 파생 topology 승인: 엔진이 결정적 변환 `augment_trim(topology, trim_decl)`로 trim 소자를 붙인 파생 topology와 출처 기록을 만든다. 주입 노드 후보와 순위는 엔진이 수반 해석으로 계산해 제시한다. 사용자가 승인(ratify)한 뒤에만 쓴다. topology.json은 엔진이 고치지 않는다 | 같음 |
| T-3 | DAC 구조 기본안: 차동 전류 steering 이진 가중(I_A + I_B 일정)이다. DNL이 부족하면 상위 비트만 thermometer로 바꾼다 | 같음 |
| T-4 | 착수 시점: 엔진 구현은 NFR-4 card 2 → XRUN-F1 A·B·C 뒤에 한다. 계획 문서 초안과 원문 검토·보관은 지금 병렬로 한다(엔진 코드 무변경) | 같음 |

---

## N3. 엔진 반영 구조

### N3.0 현황 사실(읽기 확인, base `cfe2e31`)

| ID | 사실 | 근거 |
|---|---|---|
| F-1 | `offset_analysis(ss, view, sigmas, input_cells, ...)`는 회로의 **모든 MOS**에 대해 σ²_in = Σ_i (Z_i·gm_i·σ_VGS,i)² / A_dm²를 계산한다. Z_i = z[s_i] − z[d_i]이고, z는 수반 풀이 한 번(LU 한 번)으로 얻는다. A_dm = sense·volt(부호 포함, `gain_ss_db`의 T(0)와 같은 양)이다. `offset_excess` = √(전체 / 입력 셀 분산)이다 | `E/metrics/offset_analysis.py:6-8, :56, :71, :74, :81-84, :91` |
| F-2 | **노드별 수반 벡터 z는 밖으로 나오지 않는다.** 지역 `state`(:100)에만 있고, 결과는 소자별 `z_ohm` = z[s]−z[d]뿐이다. 따라서 t_pair를 계산하려면 z를 graph 필드로 노출하는 엔진 변경이 필요하다 | `E/metrics/offset_analysis.py:95-100`, `E/metrics/aux_types.py:110-134` |
| F-3 | σ_VGS는 Pelgrom 상수식이 아니다. LUT 감도 열 DVGS_k에 PDK bin slope를 곱해 RSS하고, √(W_ref/W)로 기하 환산한 값이다(`device_sigmas` → `mismatch_sigma_vgs`). 폭이 bin 최대를 넘으면 finger로 나누고 σ/√n으로 계산한다. PDK slope는 `MismatchSource`(graph 필드, writer `mismatch_source`, S0당 한 번)에 있다. 전류 mismatch σ(ΔI/I) = √((gm/ID_a·σ_a)² + (gm/ID_b·σ_b)²)는 `mirror_ratio`에 이미 있다 | `E/metrics/device_sigma.py:17-33`, `E/lut/mismatch_sigma.py:5`, `E/metrics/mismatch_field.py:14-17`, `E/metrics/mirror_ratio.py:9, :36` |
| F-4 | `iv_matching_l.matching_bounds`는 **출발값 전용**이다(EP-7). 판정은 봉인 스냅샷의 `offset_in_sigma_mv`·`offset_excess`가 한다. L 하한은 `offset_in_sigma_mv <=` 제약이 있을 때만 켜지고(σ_share = σ_target/√2), `offset_excess <= E`는 부하 gm/ID 상한(Σ_load/Σ_in ≤ E²−1)으로 간다. 부하 역할은 `mirror`·`diode_load`·`load`이다 | `E/search/iv_matching_l.py:5-16, :106, :120-125`, `E/search/_helpers_guard.py:15-29` |
| F-5 | 입력 셀은 S1v transfer 뷰 gain 블록 가운데 (stage, key)가 가장 작은 블록의 `ROLE_INPUT` 소자다. 잡음 해석도 같은 규칙을 쓴다. 블록에는 `outputs`·`nodes`가 있다. **'drain 쪽 차동 노드 쌍' 자료구조는 없다.** 쓸 수 있는 구조는 `automorphism_orbits`, `virtual_ground`, matching group(`diff_pair`·`mirror`·`branch_symmetric`)이다 | `E/metrics/metric_structure.py:30-47`, `E/search/noise_decl.py:9`, `E/graph/s1v_values.py:305-323`, `E/graph/automorphism_orbits.py`, `E/graph/s1_values.py:93-98` |
| F-6 | spec offset metric은 `offset_in_sigma_mv`(1σ), `offset_excess`(비), `offset_sys_mv`이다. **수율·3σ·drift·온도 필드는 없다.** 제약 항목 키는 `metric, op, value, view, source` + `value_from_constraint`·`value_from_file`이다. 합격 조건은 TT 27 °C 한 조건이다(상위 DEC-96 (3)) | `E/metrics/registry.py:56-58`, `E/authoring/spec_constraints.py:54-55`, `E/authoring/_spec_fields.py:25`, `E/authoring/spec_schema.py:22-33` |
| F-7 | topology 소자 항목 키는 `name, kind, drain, gate, source`(+`bulk`)뿐이다. 그 밖의 키는 `element_unknown_key`로 거부한다. 역할은 엔진이 유도하고 topology에 선언하지 않는다. 파생·augment topology 기제는 없다(비어 있지 않은 `linked_topology_files`는 거부). 이상원(`ideal_sources`)과 `bias_inputs`는 선택 키로 있다 | `E/authoring/devices.py:17-19`, `E/authoring/topology_schema.py:18-23`, `E/authoring/linked_files.py:21-25` |
| F-8 | 승인 기록의 선례는 `<name>.structure.json`이다(`{topology_hash, rule_hash, facts[{concept, subject, value, status:"ratified", evidence, approval_id}]}`). 해시가 다르면 `structure_fact_stale`이 된다. concept 어휘는 닫혀 있고 8개다 | `E/graph/structure_load.py:1-17`, `E/graph/s1v_values.py:31-33` |
| F-9 | 블록 AC 역할 어휘: `input, cascode, follower, pass, mirror, load, tail_source, diode_load`. DC 역할: `diode_reference, bias_current_source, signal, diode_reference_composite(_cascode)`. 모두 유도값이다 | `E/graph/s1v_values.py:86-96`, `E/graph/s1_values.py:65-69` |
| F-10 | 잡음원은 모든 MOS와 저항에 하나씩 있다. 역할로 거르지 않으므로 바이어스 소자도 기여한다. MNA 용량 스탬프(cgs·cgd·cgb·cdb·csb)도 셀 종류로 가르지 않는다 | `E/metrics/noise_sources.py:5, :45`, `E/metrics/stamp_mos.py:5-6`, `E/metrics/ss_circuit.py` |
| F-11 | headroom·포화 검사: `headroom_bound`, `iv_headroom.headroom_bounds`, 봉인 7 `dc_seal_saturation`(VDS − VDsat ≥ tol), DC 제약 행 `constraint_rows` | `E/metrics/headroom_bound.py:111`, `E/search/iv_headroom.py:152`, `E/sizing/seal_saturation.py:51`, `E/search/constraints.py:31` |
| F-12 | θ 종류: `ln_idu, L, y, current, resistance, capacitance, ss_resistance`. metric 레지스트리는 `E/metrics/registry.py` `_ROWS`이고 이름은 `metric_catalog()`로 검증한다 | `E/sizing/s2_values.py:57-65`, `E/metrics/registry.py:36-63, :81`, `E/metrics/catalog.py:20` |
| F-13 | mismatch LUT는 `sky130_nfet_pfet_lut_v2_mismatch_r1.npz`(git 밖)이다. 축은 L·VGS·VDS·VS이고 w_ref_m을 가진다. 변수는 nmos `toxe, vth0, voff`, pmos는 여기에 `nfactor`가 더해진다 | `assets/lut_v2_location.json`, `E/lut/CONTRACT.md:938-948`, `assets/sky130_pdk_decl.json:454-465` |
| F-14 | 엔진 코드에 'trim'은 없다 | grep 2026-10-15 |

### N3.1 흐름(두 단계 실행, T-2)

1. **1단계(후보)**: trim 선언이 있는 spec으로 원본 topology를 평가한다. 랜덤 offset 판정은 N3.6 의미로 바꿔 둔다. 결과로 front 점(또는 시작점)마다 후보 노드 쌍의 t_pair, headroom 여유, 잡음 영향, 예상 DAC 크기(N3.4 식)를 담은 순위표를 낸다. topology는 바꾸지 않는다.
2. **승인**: 사용자가 노드 쌍과 DAC 구조(T-3 기본안 또는 변경)를 고른다. 승인 기록(N3.3)을 남긴다.
3. **2단계(사이징)**: `augment_trim`이 파생 topology를 다시 만들고, 해시를 승인 기록과 대조한다. 다르면 정지한다. 같으면 파생 topology를 S0 입력으로 정상 흐름(GB0~GB9)을 돌린다. trim 제약과 metric(N3.4)은 이 단계에서 판정한다.

1단계 순위표는 θ에 의존한다(z와 A_dm이 사이징에 따라 바뀐다). 순위표에는 front 위 t_pair의 범위(최소·최대)와 부호 일관성을 함께 적는다. 부호가 front 위에서 바뀌는 쌍은 후보에서 표시만 하고 거르지 않는다(N7 D-6).

### N3.2 주입 노드 후보 규칙(구조 규칙, 이름 없음)

* 후보 노드 = F-5 입력 셀(첫 gain 블록 `ROLE_INPUT` 소자)의 drain 넷이다. 고정 넷(교류접지·레일·뷰 구동 넷)은 뺀다.
* 쌍 = 그 후보 넷들 가운데 topology 정준형 자기동형 궤도(`automorphism_orbits`)가 같은 두 넷이다. 차동 포트 p/n은 같은 색이라 서로 바뀔 수 있다(`E/graph/automorphism_orbits.py:1-8`). 궤도 안의 후보 넷이 정확히 둘이 아니면(짝이 없거나 셋 이상이면) `trim_pair_undefined`로 보고하고 후보를 내지 않는다. 조용한 대체는 금지다.
* 순위 지표(쌍마다): |t_pair|, 두 넷의 headroom 여유(F-11의 경로 합으로 DAC 출력 소자가 포화를 유지할 수 있는 전압 창), DAC 잡음의 입력 환산 영향(N3.7). 기본 순위 키는 headroom이 가능한 쌍 가운데 |t_pair| 내림차순이다. 잡음 항을 키에 넣을지는 N7 D-5다.
* 상보 입력쌍(입력 셀이 nmos·pmos 두 쌍인 회로)은 쌍마다 따로 후보를 낸다. DAC를 하나로 할지 둘로 할지는 N7 D-7이다.
* 단일 입력 회로(차동 입력 포트 없음)는 쌍 규칙이 정의되지 않는다. 선언이 있으면 `trim_single_input_unsupported`로 정지한다. 지원 확장은 N7 D-8이다.

### N3.3 `augment_trim`과 승인 기록

* 서명: `augment_trim(topology, trim_decl, selection) -> (derived_topology, provenance)`. 순수 함수이고 파일을 쓰지 않는다.
* 붙이는 것(T-3 기본안): 선택 쌍 (n_p, n_n)마다 차동 steering 출력 두 개, 이진 가중 단위 전류원 셀, 상위 thermometer 비트(분할 m은 N3.4에서 유도), 단위 셀 게이트 바이어스 연결이다. 바이어스 원천(기존 바이어스 넷 미러 대 새 `bias_inputs` 항목)은 N7 D-9다. 스위치의 표현 수준(트랜지스터 대 이상 스위치)은 N7 D-10이다.
* 파생 topology는 원본 스키마(F-7)를 그대로 지킨다. 새 키를 넣지 않는다. trim 역할은 topology가 아니라 출처 기록과 승인 기록으로 S1에 전달한다.
* 출처 기록: `{원본 topology_hash, trim_decl_hash, rule_hash, selection(쌍·순위표 행·1단계 실행 id), 생성 소자 이름 목록}`.
* 승인 기록: structure.json 선례(F-8)를 따른다. 새 파일 `<name>.trim.json`을 쓸지, structure.json의 concept 어휘에 `trim_dac`·`trim_injection_pair`를 더할지는 design에서 정한다. 어느 쪽이든 `approval_id`, `topology_hash`(원본), `derived_topology_hash`, `rule_hash`를 담고, 해시가 다르면 fail-closed다.

### N3.4 DAC 설계 규칙(유도, 상수 없음)

기호: σ_in, V_sys(봉인 점의 엔진 값), t = t_pair(파생 topology의 봉인 점에서 다시 계산), k·V_res(spec), σ_U = 단위 셀 전류의 상대 σ(F-3의 σ_VGS와 gm/ID에서 `mirror_ratio`와 같은 식으로 유도).

| 항목 | 규칙 | 근거 |
|---|---|---|
| 덮을 분포 | V_cover = k·σ_in + \|V_sys\|. 계통 항을 넣은 것은 제안 식에 없던 보강이다(N7 X-2) | Staudt 2011 §II.A(범위가 미보정 분포를 덮어야 함, p.1-2) |
| 범위 | \|t\|·I_FS ≥ V_cover | 같음, Mohamed 2013 식(3) 구조(주입으로 더한 항이 offset을 상쇄, p.3) |
| LSB | \|t\|·I_LSB ≤ V_res. 이때 잔여는 양자화 ±LSB/2와 DNL 한계 LSB/2의 합으로 V_res 안에 든다(V_res의 뜻은 N7 D-1) | Staudt 2011 §II.A·§II.C(p.2-3) |
| bit 수 | 2^N ≥ 2·I_FS / I_LSB를 만족하는 최소 정수 N | 정의 |
| DNL | 이진 가중 주 전이의 DNL σ = σ_U·I_LSB·√(2^m_b − 1)(m_b = 이진 부분 bit 수), thermometer 전이는 σ_U·I_LSB다. 조건은 (DNL 배수)·σ_DNL ≤ I_LSB/2이다. 배수는 N7 D-3이다 | Staudt 2011 Table I(p.3), Bertotti 2012 식(3)(p.2) |
| 분할 | 조건을 만족하는 가장 큰 m_b를 이진 부분으로 하고, 나머지 상위 비트는 thermometer로 둔다(T-3) | Bertotti 2012 §2·식(3)(p.2) |
| 단위 소자 | 단위 전류원의 gm/ID·L(θ)과 I_LSB에서 W를 정한다. σ_U는 F-3 경로로 계산한다(Pelgrom 상수 하드코딩 금지) | Bertotti 2012 식(4)(5)(p.3), F-3 |
| θ | 기본안: 단위 셀 gm/ID(`ln_idu` 계열)와 L만 θ에 둔다. I_LSB와 I_FS는 위 경계에서 유도한다. LSB 경계는 활성 제약이라 상위 NFR-5('스펙에 딱 맞춤')와 정합한다. 제안은 I_LSB도 θ 후보로 들었다(N7 X-3) | 상위 NFR-5, F-12 |
| t의 자기일관 | DAC 소자가 주입 노드의 gds·용량을 바꾸므로 t는 파생 topology의 봉인 점에서 계산한 값을 쓴다. 유도값과 판정값이 다르면 판정값(전회로)이 이긴다 | 상위 DEC-74(판정은 외층 전회로 하나) |

**제약**(trim 선언이 있을 때만 생긴다. 출처는 spec 선언을 참조한다): 범위 제약 `|t|·I_FS ≥ V_cover`, LSB 제약 `|t|·I_LSB ≤ V_res`, DNL 제약(위 식).
**metric**(이름은 상위 DEC-68 접미사 규칙으로 design이 정한다. 제안 이름: trim_lsb, trim_range, trim_dnl, trim_power, trim_area): LSB의 입력 환산값, 범위의 입력 환산값, 주 전이 DNL(LSB 단위), steering 총전류에 의한 공급 전력(전력 축 `power_dc_w`에 이미 포함되므로 별도 행은 보고용), 단위 셀 면적 합(탐색 축 면적에 포함). 각 metric은 `verified_by`(SPICE 오라클)가 생긴 뒤에만 제약으로 쓴다(상위 N3.8).

### N3.5 코드 양 끝 DC 검사

* 정상 동작점(코드 중간, δ = 0)은 일반 DC 봉인 1~8로 검사한다. 이때 steering 공통 전류 I_T/2가 두 주입 노드에 들어가므로, 입력 셀 부하 전류 균형이 바뀐다(Lu 2007 식(10), p.2). 이 변화는 DC writer가 trim 소자를 바이어스 전류원으로 다루면 자동으로 들어간다.
* 끝 코드(δ = ±I_FS) 검사 기본안: 그 코드가 보정하는 입력 offset(∓t·I_FS)을 입력 차동 전압으로 함께 건 점에서 출력이 균형인 DC 해를 풀고, 모든 소자의 포화 여유(봉인 7)를 검사한다. 근거는 다음과 같다. 개루프에서 끝 코드만 걸면 출력이 레일로 가므로 의미 있는 검사가 아니다. 실제 칩에서 끝 코드는 그만한 offset이 있을 때만 쓰인다. 이 해석은 제안의 '코드 양 끝 DC 동작점 검사'를 구체화한 것이다(N7 X-4).

### N3.6 offset spec 의미 전환과 기존 해석과의 관계

| 대상 | trim 선언 없음(지금) | trim 선언 있음 |
|---|---|---|
| `offset_in_sigma_mv` | 절대 제약(파일럿)이거나 보고 | 덮을 분포 V_cover의 입력이다. 보고는 유지한다. 같은 spec에 `offset_in_sigma_mv <=` 제약이 함께 있으면 어떻게 할지(거부, 무시, 공존)는 N7 D-4다 |
| `offset_excess` 가드 | 구조 가드 | trim 소자는 분자(전체 분산)에 들어간다. 분모(입력 셀)는 그대로다. 가드를 유지할지는 N7 D-4다 |
| `offset_sys_mv` | 상한 = 랜덤 예산 | V_cover에 더한다. 상한 규칙은 N7 D-4다 |
| `iv_matching_l` L 하한 | `offset_in_sigma_mv <=`가 있으면 켜짐(출발값) | 끈다(출발값 전용이므로 판정은 바뀌지 않는다, F-4). 대신 LSB·범위 경계에서 입력쌍 출발값 규칙을 새로 둘지는 design이 정한다 |
| `iv_matching_l` 가드 부하 | 부하 역할 소자 | trim 소자는 `trim_dac` 역할이라 부하 집합에 들어가지 않는다(FR-T5) |
| 잡음 metric 4종 | 모든 MOS | trim 소자 잡음이 들어간다(F-10). `noise_excess_th`의 분모(입력 소자)는 그대로다 |
| 극점·PM·GBW | 모든 MOS 용량 | 주입 노드에 cdb·cgd가 더해진다. 판정은 전회로 MNA라 별도 규칙이 없다 |
| headroom·스윙 | 경로 합 | DAC 출력 소자 VDS 여유가 주입 노드의 경로에 더해진다. 후보 순위(N3.2)와 끝 코드 검사(N3.5)에서 쓴다 |
| 전력·면적 축 | DC 공급 전력, `sum_area` | I_T와 DAC 소자 면적이 자동으로 들어간다. 디지털 디코더·코드 저장 면적은 넣지 않는다(N1.2) |
| drift·1/f | 없음 / 보고 | 바꾸지 않는다. 보고서에 'offset trim은 drift와 1/f를 보정하지 않음'을 적는다(Kay 2024 §1.2, PDF p.7; Zhou 2017 Table 1, p.2) |

### N3.7 잡음 영향 지표(후보 순위용)

DAC 출력 전류 잡음 i_n이 주입 노드 쌍에 들어가면 입력 환산 잡음은 |t|·i_n이다. I_FS ∝ 1/|t|(범위 경계)이고 i_n²은 출력 소자 gm에 비례하므로, 노드 선택은 잡음과 전력·면적 사이의 교환이다. 후보표에는 이 값을 기존 잡음 해석(adjoint)으로 계산해 적는다. 상수 모델(γ 등)은 쓰지 않고 LUT 잡음 데이터만 쓴다(상위 DEC-96 (3)).

---

## N4. 9회로 적용 판정 방법

판정은 회로 이름이 아니라 규칙으로 한다. 단계마다 '해당 없음'은 사유 코드로 남긴다.

1. spec에 trim 선언(FR-T1)이 없으면 → 무동작이다. 결과는 지금과 비트 동일해야 한다.
2. transfer 뷰에 차동 입력 포트쌍이 없으면 → `trim_single_input_unsupported`(N7 D-8 전까지).
3. 첫 gain 블록 입력 셀이 없거나, 그 drain 넷이 자기동형 궤도로 정확히 둘씩 짝지어지지 않으면 → `trim_pair_undefined`.
4. 모든 후보 쌍의 |t_pair| = 0이거나 headroom 창이 비면 → `trim_injection_infeasible`. 이때 탐색 전에 유도와 함께 보고한다.
5. 그 밖의 경우 → 후보표를 낸다.

현재 사실(F-5·F-6, 2026-10-15 읽기 확인. 적용 여부는 이 규칙으로 card TR-7에서 **측정**한다. 이 표로 미리 정하지 않는다):

| 회로 | 입력 | 입력 게이트 소자 | 현재 offset 항목 |
|---|---|---|---|
| common_gate_amplifier | 단일(소스 구동) | 없음 | 없음 |
| current_reuse_telescopic_ota | 차동, 상보 | M1a/M1b pmos, M4a/M4b nmos | `offset_in_sigma_mv <= 3.3`, `offset_sys_mv` |
| folded_cascode | 차동 | M1/M2 nmos | `offset_excess` |
| ngcc_3stage_ff | 차동 | M1/M2 pmos | `offset_excess` |
| nmcnr_amplifier | 차동 | M102/M103 pmos | `offset_excess` |
| pushpull_follower_buffer | 단일 | M3 pmos, M4 nmos | 없음 |
| sf_pushpull_output_opamp | 차동 | M1/M2 nmos | `offset_excess` |
| two_stage_ota | 차동 | M1/M2 nmos | `offset_excess` |
| two_stage_ota_sf | 차동 | M1/M2 nmos | `offset_excess` |

근거: 각 `assets/library/<회로>.sizing_spec.json`(current_reuse :225-242, folded_cascode :49-51 등)과 `<회로>.topology.json`이다. 9회로 spec 가운데 trim 선언을 넣을 회로와 그 값은 사용자 몫이다(T-1, N7 D-11).

---

## N5. 단계 분할 초안(card 후보)

공통 착수 조건: T-4 순서(NFR-4 card 2 → XRUN-F1 A·B·C 병합 뒤)를 지킨다. design 문서 `docs/02-design/features/offset-trim.design.md`가 있고 독립 검증과 사용자 승인을 받아야 한다(bkit PDCA: 계획 → design → 구현 → gap 분석). N7 '사용자 결정 필요' 가운데 그 card가 읽는 항목이 닫혀 있어야 한다.

| card | 범위 | 선행 | 읽는 결정 |
|---|---|---|---|
| TR-0 (문서) | design 문서: 필드 스키마, 함수 서명, graph 필드, 실패 코드, metric 이름(DEC-68), test 목록, 승인 기록 형식. 독립 검증 | 이 계획 승인 | D-1~D-11 |
| TR-1 | spec trim 선언 스키마·로더 거부 규칙. 선언이 없으면 9회로 결과 비트 동일 | TR-0 | D-1·D-2·D-4 |
| TR-2 | 노드 수반 벡터 z의 graph 필드 노출(F-2), t_pair, 후보 규칙(N3.2), 순위표 결과 JSON(1단계). 보고만 한다 | TR-1 | D-5·D-6·D-7 |
| TR-3 | `augment_trim`, 출처 기록, 승인 기록 로드, 해시 대조 fail-closed, 진입점 배선 | TR-2 | D-9·D-10 |
| TR-4 | `trim_dac` 역할 유도(S1·S1v 신호 경로 제외, DC writer 바이어스 전류원), 가드·부하 집합 제외 | TR-3 | -- |
| TR-5 | DAC 설계 규칙(N3.4), 제약·metric 레지스트리, 끝 코드 DC 검사(N3.5) | TR-4 | D-3·X-2·X-3·X-4 |
| TR-6 | offset spec 의미 전환(N3.6), `iv_matching_l` 변경 | TR-5 | D-4 |
| TR-7 | 9회로 일반성 측정(N4 판정 사유표), 선언 회로 E2E, SPICE 오라클 대조(코드 스윕·Monte-Carlo 잔여 offset 분포) | TR-6, 오라클 확장(레인 P) | D-11 |

**완료 조건**(기능 전체): (1) 선언이 없는 9회로 결과가 base와 비트 동일하다. (2) 선언 회로에서 trim 제약·metric이 `verified_by`를 가진다. (3) SPICE 오라클의 코드 스윕에서 각 Monte-Carlo 표본마다 잔여 ≤ V_res인 코드가 존재하는 비율이 spec 수율 배수에 대응하는 값 이상이다(판정 규칙은 TR-0이 정하고, 독립 검증자가 소유한다). (4) 모든 새 함수가 진입점에서 호출된다(배선 증거). (5) 상위 N6.3 graph 단일 정본·재계산 계수·파일 분할 확인과 design 대 구현 gap 분석을 통과한다.

---

## N6. 검증 원칙

* 판정자는 SPICE 오라클(`tools/spice_oracle/`, 엔진 import 금지)이다. trim은 코드 스윕과 Monte-Carlo가 필요하다. 오라클 확장(코드 입력, MC 표본별 최적 코드 선택)은 레인 P 작업이다.
* 엔진 쪽 test는 interface card만 보고 쓴다(작성자≠검증자). 기대값은 피검 함수를 불러 만들지 않는다.
* 일반성: 9회로 전수에서 사유 코드를 측정해 보고한다. 필요 없는 회로에서 무동작임을 보이는 것이 증거다.

---

## N7. 열린 항목

### N7.1 사용자 결정 필요

| ID | 질문 | 기본안(원칙으로 정한 것, 사용자 변경 가능) |
|---|---|---|
| D-1 | V_res의 뜻: 잔여 offset의 최악 한계(\|V_res\|)인가, 잔여 분포의 1σ인가 | 최악 한계. 그러면 LSB 경계 \|t\|·I_LSB ≤ V_res가 양자화 + DNL 한계를 덮는다(N3.4) |
| D-2 | 수율 표현: 배수 k만 받을지, 수율 목표 Y도 받아 k로 환산할지. 환산하려면 정규 분포·양측 가정이 필요하다 | k만 받는다. 분포 가정을 엔진에 넣지 않는다 |
| D-3 | DNL 조건의 배수: spec k를 그대로 쓸지, 별도 선언을 둘지 | spec k를 그대로 쓴다(수율 선언 하나, 새 상수 없음) |
| D-4 | 같은 spec에 기존 offset 제약(`offset_in_sigma_mv <=`, `offset_excess`, `offset_sys_mv` 상한)과 trim 선언이 함께 있을 때의 처리 | 로더가 `offset_in_sigma_mv <=`와 trim 선언의 공존을 거부한다(spec 수정은 사용자 몫). `offset_excess` 가드와 `offset_sys_mv`는 보고로 내린다. 근거: 의미가 다른 두 판정을 동시에 걸면 조용히 한쪽이 무력해진다 |
| D-5 | 후보 순위 키에 DAC 잡음 영향(N3.7)을 넣을지 | 넣지 않는다. 순위 키는 headroom이 가능한 쌍의 \|t\| 내림차순이고, 잡음은 표에 값으로 보고만 한다 |
| D-6 | front 위에서 t의 부호나 크기가 크게 바뀌는 쌍의 처리 | 표시하고 거르지 않는다. 승인은 사용자 몫이다 |
| D-7 | 상보 입력쌍(current_reuse_telescopic_ota) 회로에서 DAC를 쌍마다 둘 둘지, 하나만 둘지. 입력 CM에 따라 지배 쌍이 바뀌면 한 코드로 양쪽을 다 보정할 수 없다 | 쌍마다 하나씩 둔다(제안 '상보 입력쌍은 trim 각각'). 다만 엔진 판정은 선언 입력 DC 한 점에서만 한다는 한계를 보고한다 |
| D-8 | 단일 입력 회로 지원(제안 '단일 입력 회로는 spec에 offset 항목이 있을 때만') | 이번 범위에서는 정지(`trim_single_input_unsupported`)한다. 차동 쌍 규칙(T-3 steering)이 정의되지 않기 때문이다. 현재 단일 입력 2회로에는 offset 항목이 없다(N4) |
| D-9 | DAC 단위 셀 게이트 바이어스의 원천: 회로 기존 바이어스 넷에서 미러할지, 새 `bias_inputs` 항목을 둘지 | 새 `bias_inputs` 항목(선언 원천)을 둔다. 기존 바이어스 기둥의 전류·L 동치류를 바꾸지 않기 위해서다 |
| D-10 | steering 스위치 표현: 트랜지스터로 둘지, 이상 스위치(+선언 VDS 예산)로 둘지 | 트랜지스터로 둔다. 잡음·용량·headroom 기여를 남긴다는 제안 원칙을 따른다. 엔진은 한 코드 상태(중간 코드, 끝 코드)만 평가한다 |
| D-11 | 9회로 가운데 trim 선언을 넣을 회로와 V_res·k·온도 값 | 사용자 몫이다(T-1). 엔진 검증용 픽스처 spec은 `origin: fixture`로 따로 둔다 |
| D-12 | trim 온도 조건(T-1)과 상위 DEC-96 (3) '합격 = TT 27 °C 한 조건'의 관계: 27 °C가 아닌 trim 온도를 선언하면 엔진이 평가할 수 없다 | 이번 범위는 trim 온도 = 합격 조건 온도로 제한하고, 다르면 거부한다. 원래 취지와 다를 수 있다(X-1) |

### N7.2 원래 취지와 다름(따로 보고)

| ID | 내용 |
|---|---|
| X-1 | T-1의 'trim 온도 조건' 필드는 두지만, 엔진 합격 조건이 TT 27 °C 하나(상위 DEC-96 (3))라서 다른 온도는 평가할 수 없다. 기본안(D-12)은 사실상 그 필드를 27 °C로 고정하는 제약이다. 다른 온도를 지원하려면 LUT 온도 축이나 오라클 온도 옵션이라는 별도 범위가 필요하다 |
| X-2 | 제안 범위식은 I_range ≥ k·σ_in/\|t\|였다. 계획은 계통 offset을 더해 V_cover = k·σ_in + \|V_sys\|로 했다. 계통 offset이 코드 중간점을 옮기므로 덮어야 할 분포의 중심이 0이 아니기 때문이다(Staudt 2011 §II.A의 'µ = 0' 가정이 깨지는 경우) |
| X-3 | 제안은 θ 후보로 'I_LSB 또는 I_T·단위 gm/ID·L'을 들었다. 기본안은 I_LSB와 I_FS를 θ에서 빼고 경계에서 유도한다(NFR-5). I_LSB를 θ로 두면 LSB 경계가 활성이 아닌 해가 front에 남는다 |
| X-4 | 제안의 '코드 양 끝 DC 동작점 검사'를 '그 코드가 보정하는 입력 offset을 함께 건 균형점'의 검사로 구체화했다(N3.5). 개루프 끝 코드 단독 검사는 출력이 레일에 붙어 정의되지 않기 때문이다 |
| X-5 | 제안의 'iv_matching_l 완화'는 실제로는 판정을 바꾸지 않는다. `iv_matching_l`은 출발값 전용(F-4)이고 판정은 spec 제약이 한다. 의미 전환의 실체는 spec 제약 처리(D-4)다 |
| X-6 | 제안의 'drift·1/f는 유지'에서 엔진에는 drift metric이 없다(F-6). '유지'는 '보정 대상 아님 + 보고 문구'로만 구현된다. drift 계산을 새로 넣지 않는다 |
| X-7 | 제안의 t_n = z[n]/A_dm은 노드 하나의 정의다. T-3 차동 steering에서는 쌍의 차 (z[n_p] − z[n_n])/A_dm(t_pair)를 쓴다. 노드 z 벡터는 지금 노출되지 않아(F-2) graph 필드를 새로 만드는 엔진 변경이 필요하다 |

---

## N8. 원문 근거표

보관 위치: `skills/analog-gmid-design/assets/technique/sources/<폴더>/`(`source.pdf`·`paper.md`, 쪽 렌더는 `python tools/pdf_to_md.py ensure`로 만든다). 쪽 번호는 PDF 쪽이다. 수치는 인용하지 않는다.

| R | 원문 | 웹 | 로컬 PDF | 쪽·위치 | 이 계획에서 쓰는 곳 |
|---|---|---|---|---|---|
| R1 | A. R. Mohamed, M. F. Ibrahim, F. Farag, 'Input Offset Cancellation Trimming Technique for Operational Amplifiers', SIECPC 2013 | [pure.kfupm.edu.sa](https://pure.kfupm.edu.sa/en/publications/input-offset-cancellation-trimming-technique-for-operational-ampl/) | `offset_trim__mohamed_2013/source.pdf` (원본 `G:/내 드라이브/work/Todoc/논문모음/input offset cancellation trimming technique for operational amplifier_mohamed2013.pdf`) | p.2 Fig.2·식(1)(2), p.3 Fig.4·식(3)(4)(7), p.4 Fig.9·11 | 범위 밖 대안(신호 경로 level shifter: 버퍼 이득 < 1, 대역 제한) 비교. 주입항이 offset을 상쇄한다는 구조(N3.4 범위) |
| R2 | H. M. von Staudt, 'Trim DAC Design with Minimum DNL for Self-Trim with Self-Test Schemes', IEEE IMS3TW 2011 | [doi:10.1109/IMS3TW.2011.34](https://doi.org/10.1109/IMS3TW.2011.34) | `offset_trim__staudt_2011/source.pdf` (원본 `.../논문모음/(Bible - self trim) Trim DAC Design with Minimum DNL for Self-Trim with Self-Test Schemes__staudt2011.pdf`) | p.1-2 §II.A, p.3 §II.C·Table I·Fig.4, p.3-4 §III·Table II·III | 범위가 분포를 덮을 조건, 주 전이 DNL σ_U·√(2^n−1) 대 thermometer σ_U, 양의 DNL 꼬리, 범위 손실과 bit 추가(N3.4, X-2) |
| R3 | Y. Zhou, A. Kay, 'Offset Correction Methods: Laser Trim, e-Trim, and Chopper', TI SBOT037A, 2017 | [ti.com/lit/SBOT037](https://www.ti.com/lit/SBOT037) | `offset_trim__zhou_2017/source.pdf` (원본 `.../논문모음/(Reference - trim) Offset Correction Methods_Laser Trim, e-Trim , and Chopper.pdf`) | p.1 laser·e-Trim, p.2 Fig.2·Table 1 | 패키지 뒤 내부 보정 전류원 trim의 존재(N1.1), drift·1/f 제거는 chopper만(N3.6) |
| R4 | G. Bertotti et al., 'An 8 bit current steering DAC for offset compensation purposes in sensor arrays', Adv. Radio Sci. 10:201-206, 2012 | [doi:10.5194/ars-10-201-2012](https://doi.org/10.5194/ars-10-201-2012) | `offset_trim__bertotti_2012/source.pdf` (원본 `G:/내 드라이브/work/Todoc/기술문서/ADC/An 8 bit current steering DAC for offset compensation purposes in sensor arrays_ars-10-201-2012.pdf`) | p.2 §2·식(2)(3), p.3 식(4)(5), p.4 Fig.3·4, p.5 Fig.5-8 | 차동 steering 셀(T-3), 분할 DNL·INL 분산, 단위 전류 σ의 동작 영역 의존(N3.4) |
| R5 | C.-W. Lu, 'An Offset Cancellation Technique for Two-Stage CMOS Operational Amplifiers', IEEE ICICDT 2007 | 찾지 못함 | `offset_trim__lu_2007/source.pdf` (원본 `.../기술문서/ADC/(Ref) An Offset Cancellation Technique for Two-Stage CMOS OPamp.pdf`) | p.2 Fig.2·3, 식(6)-(10) | 1단 출력 노드 전류 주입 구조, 주입 소자를 더할 때 부하 전류 균형(N3.5), 주입 오차 ∝ G_m,aux/G_m1(N3.7) |
| R6 | V. Srinivasan et al., 'A Precision CMOS Amplifier Using Floating-Gate Transistors for Offset Cancellation', IEEE JSSC 42(2), 2007 | [doi:10.1109/JSSC.2006.889365](https://doi.org/10.1109/JSSC.2006.889365) | `offset_trim__srinivasan_2007/source.pdf` (웹 다운로드) | p.1 §I·Fig.1 | current-mode DAC로 부하 전류를 조정하는 offset 보상(N3.2 주입 노드 = 입력 셀 drain 쪽) |
| R7 | A. Kay, 'Op Amp Offset Voltage and Bias Current Limitations', TI SBOA590, 2024 | [ti.com/lit/pdf/sboa590](https://www.ti.com/lit/pdf/sboa590) | `offset_trim__kay_2024/source.pdf` (웹 다운로드) | §1.2: p.6 Figure 1-6, p.7 Figure 1-8 문단 | CMOS drift는 offset에 비례하지 않아 한 온도 trim이 drift를 보정하지 않음(N1.2, N3.6) |

---

## N9. 위험과 대응

| 위험 | 대응 |
|---|---|
| trim 소자가 S1v에서 `load`·`tail_source`로 분류돼 offset·잡음 가드와 `iv_matching_l` 부하 집합을 오염시킨다 | FR-T5 `trim_dac` 역할을 먼저 둔다(TR-4). 9회로 S1v 결과가 trim 소자를 뺀 원본과 같은지 test한다 |
| t가 θ에 따라 변해서 1단계에서 승인한 쌍이 2단계 front에서 나빠진다 | 순위표에 front 위 t 범위를 적는다(N3.1). 2단계에서 판정은 전회로 값으로 한다 |
| 주입 노드(예: fold 노드처럼 낮은 전압 노드)의 headroom이 DAC 출력 소자 VDsat + 스위치 VDS를 못 받친다 | 후보 순위 단계에서 headroom 창을 거른다(N3.2). 끝 코드 검사(N3.5)를 한다 |
| DAC 용량이 비주극점을 낮춰 PM이 떨어진다 | 전회로 MNA 판정에 자동으로 들어간다. 순위표에 주입 노드 용량 증가를 보고 항목으로 둔다 |
| 파생 topology 디스크 사본이 원본과 어긋난다(stale) | 사본을 정본으로 쓰지 않는다. 실행마다 다시 만들고 해시를 승인 기록과 대조한다(NFR-T3, FR-T4) |
| 범위·LSB 유도에 원문 관례값(±5σ, 5 % 등)이 섞인다 | NFR-T2. 구조 test(숫자 리터럴 lint)와 design 검증 항목에 넣는다 |
| 상보 입력쌍 회로에서 한 CM 점 판정이 실제 ICMR 전체 보정을 보장하지 않는다 | D-7의 보고 문구. ICMR 여러 점 판정은 범위 밖으로 둔다 |
| 기존 offset 제약과 trim 선언이 함께 있을 때 한쪽이 조용히 무력화된다 | D-4 기본안: 로더 거부 |
