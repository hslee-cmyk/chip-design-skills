---
template: plan
version: 0.4
---

# offset-trim Planning Document

> **Summary**: gm/ID 엔진(`skills/analog-gmid-design/gmid_engine/`)에 **입력 offset 전류 주입 trim**을 넣는다. 흐름은 두 단계다.
> 1. 엔진이 기존 수반(adjoint) offset 해석으로 주입 노드 쌍 후보와 순위, 추천 DAC 구성(bit 수 N, 이진 부분 m, 극성)을 계산한다. 결정적 변환 `augment_trim(topology, trim_decl)`이 그 구성으로 만든 **파생 topology**를 connectivity 표와 함께 제시한다.
> 2. 사용자가 승인(ratify)한 뒤에만 그 파생 topology를 사이징한다. 승인된 N·m은 고정값이고, 이 단계에서는 단위 전류만 경계에서 유도하며 보정 구간·잔여는 제약으로 판정한다.
>
> DAC는 차동 전류 steering 이진 가중이고, DNL이 부족하면 상위 비트를 thermometer로 둔다.
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code
> **Status**: 계획 초안 v0.4 (2026-10-15). v0.1 독립 검증(72/100, 차단 B1~B4)과 v0.2 재검증(84/100, 차단 C1·C2)을 반영했고, v0.3 재확인(92/100, 차단 0) 뒤 사용자 결정 T-5(온도 한계)를 반영했다. 사용자 승인 전이다. 근거는 사용자 결정 T-1~T-4(원문 `wt/_drafts/user_decisions.md` '## offset trim 착수 결정 (2026-10-15 사용자 "권고대로 해")')와 원문 7편(N8)이다.
> **이력**: 경위, 제안 원문 요지, 원문 검토 기록, 검증 반영 기록, 버전 이력은 [offset-trim.history.md](offset-trim.history.md)에 있다.
> **상위 계획**: [gain-budget-gmid-sizing.plan.md](gain-budget-gmid-sizing.plan.md). 이 계획은 상위 계획의 원칙(N1.4 NFR, N2 결정)을 그대로 따른다. 충돌하면 상위 계획이 이기고, 충돌은 N7에 올린다.

---

## N0. 문서 안내

* **담는 것**: 목적·범위, 확정 결정, 요구, 엔진 반영 구조와 규칙, 적용 판정 방법, 단계(card 후보)와 완료 조건, 위험, 원문 근거, 열린 결정.
* **담지 않는 것**: 경위와 검토 과정. 이것은 history에 둔다.
* **값 원칙**: 이 문서에는 수치 상수를 두지 않는다.
  * 범위 배수 k, 잔여 offset V_res, trim 온도는 사용자 spec 값이다.
  * 나머지는 엔진 해석값, LUT, PDK 선언에서 유도한다.
  * 원문 수치(N8)는 인용하지 않는다.
* **인용 규칙**: 코드는 `파일:줄`로 인용하고 기준은 base `cfe2e31`이다. 경로에서 `skills/analog-gmid-design/`은 뺐고, `E/`는 `gmid_engine/`이다.

### N0.1 용어

| 용어 | 정의 |
|---|---|
| σ_in | 엔진 `offset_in_sigma_mv`의 값이다. 모든 MOS의 게이트 오차원을 수반 해석으로 출력에 보내 합친 분산을 차동 이득 A_dm으로 입력 환산한 1σ 값이다(F-1). 2단계에서는 파생 topology에서 계산하므로 DAC 소자의 mismatch가 들어 있다 |
| V_sys, V_sys,s | V_sys는 엔진 `offset_sys_mv`의 값으로 크기만 담는다. V_sys,s는 부호 있는 계통 offset = `output_error_v` / A_dm이다(부호 규약 N3.4, `E/metrics/offset_systematic.py:7-8`) |
| z[n] | 감지 관측에 대한 수반 해의 노드 n 성분이다. 노드 n에 넣은 전류 I가 출력에 주는 값은 z[n]·I다(F-1) |
| 주입 쌍 | 입력 diff_pair 두 소자의 drain 넷 (n_p, n_n)이다(N3.2) |
| t | 주입 쌍에 차동 전류 +δ/2, −δ/2를 넣을 때 δ 한 단위의 입력 환산 전달이다. 정의는 t = (z[n_p] − z[n_n]) / (2·A_dm)이고 단위는 V/A다. 2단계 값은 파생 topology의 봉인 점에서 계산한다 |
| I_u | 단위 셀 하나의 steering 전류다 |
| I_T | steering 총전류다. I_T = (단위 셀 수)·I_u이고, I_A + I_B = I_T는 코드와 무관하다(T-3) |
| δ | 차동 출력 I_A − I_B다. 단위 셀 하나가 A에서 B로 바뀌면 δ는 2·I_u만큼 변한다. 그래서 **I_LSB = 2·I_u**다. 단위 셀 수가 홀수(2^N − 1)이므로 δ는 I_u의 홀수배이고, **δ = 0 코드는 없다** |
| I_FS | δ의 양 끝 크기다. 단위 셀이 모두 한쪽이면 \|δ\| = I_T이므로 **I_FS = I_T**다 |
| N, m | DAC bit 수와 이진 하위 비트 수다. 상위 N − m 비트는 thermometer(단위 2^m·I_u 셀 2^(N−m) − 1개)다. 순수 이진은 m = N − 1과 같은 최악 전이를 가진다. N·m은 승인 선택값이다(N3.1) |
| σ_U | 단위 셀 전류의 상대 σ다(Bertotti 2012 σ_I,Rel). F-3 경로(σ_VGS·gm/ID)로 계산한다 |
| trim_dac | trim 소자의 구조 역할이다. 신호 경로 셀·블록 역할에서 빠지고, 바이어스·잡음·용량·mismatch 기여는 남긴다 |
| 파생 topology | `augment_trim`이 원본 topology와 trim 선언에서 결정적으로 만든 topology다. 원본 topology.json은 바뀌지 않는다 |
| trim_decl | spec trim 필드(T-1, 사용자 값)와 승인 기록의 선택(주입 쌍, 극성, N, m)을 로더가 합친 선언이다(기본안 D-15) |

---

## N1. 목적·범위·요구

### N1.1 목적

지금은 랜덤 offset 사양을 입력쌍 면적(L·W)만으로 맞춘다. 이 기능은 그 대신 작은 입력쌍과 trim DAC의 조합을 엔진이 사이징할 수 있게 한다.

목표는 다음 두 조건을 만족하는 해를 (전력, 면적) front 위에서 찾는 것이다.
* trim 뒤 잔여 offset이 spec 목표 안에 든다.
* trim 보정 구간이 trim 전 offset 분포를 spec 수율 배수만큼 덮는다.

### N1.2 범위

| 포함 | 제외 |
|---|---|
| 정적 offset의 전류 주입 trim이다. 패키지 뒤 한 온도에서 코드를 한 번 정한다고 가정한다 | 코드 저장 방식(OTP·퓨즈·레지스터)과 디지털 디코더 면적이다(T-1) |
| 주입 쌍 후보 계산·순위, 추천 구성, 파생 topology와 connectivity 표 제시, `augment_trim`, 승인 흐름이다 | trim 알고리즘, 측정·자기 trim 비교기, 생산 시험 흐름이다(Staudt 2011 §II.B의 비교기 잡음 모델 포함) |
| 차동 전류 steering DAC의 단위 전류 유도, 보정 구간·잔여 판정, 단위 소자 W·L·gm/ID, 극성 규칙이다 | chopper·auto-zero 같은 동적 offset 제거다(Lu 2007, Zhou 2017 Fig.3) |
| trim 소자의 DC 바이어스·headroom·잡음·극점·mismatch 기여를 기존 해석으로 그대로 계산하는 것이다 | laser·저항 trim, 입력쌍 소스 저항 trim(Zhou 2017 Fig.2), 입력 단자 level shifter trim(Mohamed 2013)이다. 이것들은 비교 근거로만 쓴다 |
| offset spec 의미 전환이다. trim이 선언된 회로에서 σ_in은 덮어야 할 분포가 된다 | drift trim이다. CMOS에서는 offset이 drift에 비례하지 않아서 한 온도 offset trim이 drift를 보정하지 않는다(Kay 2024 §1.2, PDF p.7). 엔진에는 drift metric이 없다(F-6). 보고서에 이 한계를 적는다 |
| 9회로 library의 적용 판정과 일반성 측정이다 | held-out 회로 확장이다. 상위 U-75 뒤에 한다 |

### N1.3 기능 요구

| ID | 요구 |
|---|---|
| FR-T1 | **spec trim 선언**(T-1): 회로 spec에 trim 선언을 새로 둔다. 필드는 잔여 offset 목표 V_res, 수율 배수 k(또는 수율 목표, D-2), trim 온도 조건이다. 값과 출처는 사용자 몫이다. 선언이 없는 실행의 결과는 완료 조건 (1)의 범위에서 지금과 비트 동일하다 |
| FR-T2 | **1단계 후보표**: 주입 쌍(N3.2)마다 다음을 결과 JSON에 낸다. 후보 규칙은 구조 규칙이고 회로 이름을 쓰지 않는다.<br>• front 위 t의 범위와 부호<br>• 극성별 headroom 창<br>• 잡음 영향(N3.7)<br>• 추천 N·m(N3.4)<br>• 그 구성의 파생 topology와 connectivity 표(`assets/topology_to_markdown.py` 형식) |
| FR-T3 | **`augment_trim(topology, trim_decl)`**(T-2 서명): 결정적 순수 변환이다. 선택된 주입 쌍에 DAC 소자를 붙인 파생 topology와 출처 기록을 낸다. 원본 파일은 고치지 않는다 |
| FR-T4 | **승인 흐름**(T-2): 사용자가 파생 topology와 connectivity 표를 보고 승인한다. 그 승인 기록이 있을 때만 2단계 사이징 입력이 된다. 결속 규칙은 N3.3이다 |
| FR-T5 | **구조 역할 `trim_dac`**: S1·S1v가 trim 소자를 신호 경로 셀·블록 역할(`input`·`load`·`mirror`·`tail_source` 등)에 넣지 않는다. DC writer, 잡음원, MNA 용량 스탬프, offset 해석의 mismatch 원에는 그대로 포함한다 |
| FR-T6 | **DAC 규칙**(N3.4): 2단계에서 고정된 N·m에 대해 단위 전류 I_u를 유도하고, 보정 구간·잔여를 제약으로 판정한다(DNL은 잔여 판정 안에 들어간다). 불가능하면 1단계로 돌아가 다시 승인받는다 |
| FR-T7 | **offset spec 의미 전환**(N3.6) |
| FR-T8 | **끝 코드 DC 검사**(N3.5): 보정 구간 판정과 같은 균형 풀이로 한다 |
| FR-T9 | **보고**: 다음을 결과 JSON과 보고서에 적는다.<br>• trim metric, 후보표, 승인 기록 id<br>• 'drift·1/f는 trim 대상 아님' 문구<br>• 합격 조건(온도)<br>• 판정 입력 DC 한 점이라는 한계<br>• **단일 온도 trim 한계**(T-5): '판정과 trim 코드 결정은 27 °C·TT 한 조건이다. 다른 온도에서 잔여 offset은 drift 때문에 V_res를 넘을 수 있다. CMOS offset trim은 drift를 보정하지 않는다'(Kay 2024 §1.2 PDF p.7; Zhou 2017 p.1 e-Trim은 패키지 뒤 trim이라 패키지 응력 이동을 피함). TR-7 보고 전용 온도 검증 결과를 함께 싣는다 |

### N1.4 비기능 요구

상위 계획 N1.4의 NFR-1~NFR-6과 N2.2 작업 원칙을 그대로 적용한다. 이 기능에서는 특히 다음을 강제한다.

| ID | 요구 |
|---|---|
| NFR-T1 | **topology 무관**: 후보 규칙, 역할 유도, 설계식은 구조와 해석값만 읽는다. 회로·소자·넷 이름 리터럴은 금지다. 9회로에서 선언이 없으면 무동작임을 측정해 증거로 낸다 |
| NFR-T2 | **상수 발명 금지**: 범위 배수, DNL 배수, 잔여 여유에 경험 상수를 박지 않는다. 사용자 선언값(V_res, k)을 참조하거나 정의에서 유도한다. 원문 수치는 인용하지 않는다 |
| NFR-T3 | **graph 단일 정본**: 노드 수반 벡터 z, t, 후보표, DAC 유도값은 Circuit State Graph 필드다. 각 필드는 writer가 하나이고 입력 버전을 함께 기록한다(상위 DEC-83). 파생 topology는 S0 입력이고 실행마다 다시 만든다. 디스크 사본은 정본이 아니다(상위 NFR-2와 정합) |
| NFR-T4 | **결정성**: `augment_trim`은 같은 입력이면 비트 동일한 출력을 낸다. 이름은 정렬된 규칙으로 만들고, 원본 이름과 충돌하면 거부한다(상위 NFR-4) |
| NFR-T5 | **만들면 배선**: 후보 계산, 변환, 승인 검사, metric은 엔진 진입점의 실제 경로에 배선한다. 배선이 불가능하면 사용자 승인을 받는다 |
| NFR-T6 | **작성자≠검증자**: design 문서는 독립 검증 agent가 검증한다. test·기대값·판정 기준은 구현자가 소유하지 않는다. 판정자는 SPICE 오라클이다(코드 스윕 + Monte-Carlo) |

---

## N2. 확정 결정

| ID | 결정 | 출처 |
|---|---|---|
| T-1 | spec 필드: trim 뒤 잔여 offset 목표 V_res, 수율 배수 k(또는 수율 목표), trim 온도 조건을 spec에 새로 둔다. 값은 사용자 몫이다. 코드 저장 방식(OTP·퓨즈·레지스터)은 아날로그 sizing 범위 밖이다 | 사용자 2026-10-15 "권고대로 해" |
| T-2 | 파생 topology 승인: 엔진이 결정적 변환 `augment_trim(topology, trim_decl)`로 trim 소자를 붙인 파생 topology와 출처 기록을 만든다. 주입 노드 후보와 순위는 엔진이 수반 해석으로 계산해 제시한다. 사용자가 승인(ratify)한 뒤에만 쓴다. topology.json은 엔진이 고치지 않는다 | 같음 |
| T-3 | DAC 구조 기본안: 차동 전류 steering 이진 가중(I_A + I_B 일정)이다. DNL이 부족하면 상위 비트만 thermometer로 바꾼다 | 같음 |
| T-4 | 착수 시점: 엔진 구현은 NFR-4 card 2 → XRUN-F1 A·B·C 뒤에 한다. 계획 문서 초안과 원문 검토·보관은 지금 병렬로 한다(엔진 코드 무변경) | 같음 |
| T-5 | 온도 한계: 판정은 27 °C·TT(엔진 합격 조건과 같음)다. 보고 전용 검증으로 다음을 낸다. 샘플마다 27 °C에서 trim한 뒤 코드를 고정하고 온도를 sweep한 잔여 offset, 코너별 보정 구간, 끝 코드 headroom의 온도 의존, 엔진 σ_in 대 SPICE σ_in 일치. 결과 보고서에 단일 온도 trim 한계를 명시한다 | 사용자 2026-10-15 "1~3 권장대로"(원문 `wt/_drafts/user_decisions.md` 'NFR-4 card 2·offset trim 결정' T-5) |

---

## N3. 엔진 반영 구조

### N3.0 현황 사실(읽기 확인, base `cfe2e31`)

| ID | 사실 | 근거 |
|---|---|---|
| F-1 | `offset_analysis`는 회로의 **모든 MOS**에 대해 σ²_in = Σ_i (Z_i·gm_i·σ_VGS,i)² / A_dm²를 계산한다.<br>• Z_i = z[s_i] − z[d_i]다.<br>• z는 수반 풀이 한 번(LU 한 번)으로 얻는다.<br>• A_dm = sense·volt이고 부호를 포함한다(`gain_ss_db`의 T(0)와 같은 양).<br>• `offset_excess` = √(전체 분산 / 입력 셀 분산)이다 | `E/metrics/offset_analysis.py:6-8, :56, :71, :74, :81-84, :91` |
| F-2 | 노드별 수반 벡터 z는 밖으로 나오지 않는다. 지역 `state`에만 있고, 결과는 소자별 `z_ohm` = z[s]−z[d]뿐이다. t를 계산하려면 z를 graph 필드로 노출하는 엔진 변경이 필요하다 | `E/metrics/offset_analysis.py:95-100`, `E/metrics/aux_types.py:110-134` |
| F-3 | σ_VGS는 Pelgrom 상수식이 아니다.<br>• LUT 감도 열 DVGS_k에 PDK bin slope를 곱해 RSS하고, √(W_ref/W)로 기하 환산한다.<br>• 폭이 bin 최대를 넘으면 finger로 나누고 σ/√n으로 계산한다.<br>• slope는 graph 필드 `MismatchSource`에서 읽는다.<br>• 전류 mismatch σ(ΔI/I) = √((gm/ID_a·σ_a)² + (gm/ID_b·σ_b)²)는 `mirror_ratio`에 있다 | `E/metrics/device_sigma.py:17-33`, `E/lut/mismatch_sigma.py:5`, `E/metrics/mismatch_field.py:14-17`, `E/metrics/mirror_ratio.py:9, :36` |
| F-4 | `iv_matching_l.matching_bounds`는 **출발값 전용**이다(EP-7). 판정은 봉인 스냅샷의 `offset_in_sigma_mv`·`offset_excess`가 한다.<br>• L 하한은 `offset_in_sigma_mv <=`가 있을 때만 켜진다.<br>• `offset_excess <= E`는 부하 gm/ID 상한으로 간다.<br>• 부하 역할은 `mirror`·`diode_load`·`load`이다 | `E/search/iv_matching_l.py:5-16, :106, :120-125`, `E/search/_helpers_guard.py:15-29` |
| F-5 | 입력 셀은 graph 필드 `metric_structure`의 `input_cells`다. S1v transfer 뷰 gain 블록 가운데 (stage, key)가 가장 작은 블록의 `ROLE_INPUT` 소자다. 잡음 쪽(`noise_decl`)에도 같은 규칙의 두 번째 구현이 있다. 이 기능은 `metric_structure` 필드 하나만 읽는다 | `E/metrics/metric_structure.py:30-47`, `E/search/noise_decl.py:9` |
| F-6 | spec offset metric은 `offset_in_sigma_mv`(1σ), `offset_excess`, `offset_sys_mv`이다. **수율·3σ·drift·온도 필드는 없다.** 제약 항목 키는 `metric, op, value, view, source` + `value_from_constraint`·`value_from_file`이다. 합격 조건은 TT 27 °C 한 조건이다(상위 DEC-96 (3)) | `E/metrics/registry.py:56-58`, `E/authoring/spec_constraints.py:54-55`, `E/authoring/_spec_fields.py:25`, `E/authoring/spec_schema.py:22-33` |
| F-7 | topology 소자 키는 `name, kind, drain, gate, source`(+`bulk`)뿐이고, 그 밖의 키는 거부한다. 역할은 엔진이 유도한다. 파생 topology 기제는 없다(비어 있지 않은 `linked_topology_files`는 거부). `ideal_sources`와 `bias_inputs`는 선택 키다 | `E/authoring/devices.py:17-19`, `E/authoring/topology_schema.py:18-23`, `E/authoring/linked_files.py:21-25` |
| F-8 | `<name>.structure.json`은 승인 사실 파일이다(`topology_hash`, `rule_hash`, `facts[...approval_id]`).<br>• `topology_hash`가 현재 `topology_fp`와 다르거나 `rule_hash`가 현재 `structure_rule_fp()`와 다르면, 사실을 적용하지 않고 `structure_fact_stale`(**review_needed**)로 되돌린다. 정지하지 않는다.<br>• concept 어휘는 닫혀 있고 8개다.<br>• library에서 이 파일이 있는 회로는 current_reuse_telescopic_ota, nmcnr_amplifier다 | `E/graph/structure_load.py:14-15, :148`, `E/graph/s1v_values.py:31-33`, `assets/library/*.structure.json` |
| F-9 | `rule_fp = structure_rule_fp()`는 단계 A에서 구조 파일 로드에 쓰인다. S1·S1v 규칙 파일이 바뀌면 이 지문이 바뀐다 | `E/pipeline/stage_a.py:205-207` |
| F-10 | spec `meta.topology_fp`가 topology의 `connectivity_fp`와 다르면 `topology_fp_mismatch`로 거부한다. 소자를 더한 파생 topology는 원본과 지문이 다르다 | `E/authoring/spec_meta.py:32-34` |
| F-11 | 자기동형 궤도: 완전 차동 쌍은 두 drain 넷이 같은 궤도다. **단일 종단 출력(미러 부하)은 두 drain 넷이 다른 궤도다** | `E/tests/graph/test_automorphism_orbits.py:125-129` |
| F-12 | S1 matching group 종류 `diff_pair`(`MATCH_DIFF_PAIR`)가 있다. 차동쌍 후보 규칙은 같은 (kind, 비레일 source) 묶음에서 바이어스 형제를 빼고 남은 멤버가 정확히 2이면 derived, 3 이상이면 review_needed다 | `E/graph/s1_values.py:94`, `E/graph/matching_groups.py:20-22` |
| F-13 | 블록 AC 역할 어휘는 `input, cascode, follower, pass, mirror, load, tail_source, diode_load`다. DC 역할은 `diode_reference, bias_current_source, signal, diode_reference_composite(_cascode)`다. 모두 유도값이다 | `E/graph/s1v_values.py:86-96`, `E/graph/s1_values.py:65-69` |
| F-14 | 잡음원은 모든 MOS와 저항에 하나씩 있고 역할로 거르지 않는다. MNA 용량 스탬프도 셀 종류로 가르지 않는다 | `E/metrics/noise_sources.py:5, :45`, `E/metrics/stamp_mos.py:5-6` |
| F-15 | headroom·포화 검사: `headroom_bound`, `iv_headroom.headroom_bounds`, 봉인 7 `dc_seal_saturation`, DC 제약 행 `constraint_rows` | `E/metrics/headroom_bound.py:111`, `E/search/iv_headroom.py:152`, `E/sizing/seal_saturation.py:51`, `E/search/constraints.py:31` |
| F-16 | θ 종류는 `ln_idu, L, y, current, resistance, capacitance, ss_resistance`다. metric 레지스트리는 `_ROWS`이고, 이름은 `metric_catalog()`로 검증한다 | `E/sizing/s2_values.py:57-65`, `E/metrics/registry.py:36-63, :81`, `E/metrics/catalog.py:20` |
| F-17 | mismatch LUT는 `sky130_nfet_pfet_lut_v2_mismatch_r1.npz`(git 밖)다. 축은 L·VGS·VDS·VS이고 w_ref_m이 있다. 변수는 nmos `toxe, vth0, voff`, pmos는 여기에 `nfactor`를 더한 것이다 | `assets/lut_v2_location.json`, `E/lut/CONTRACT.md:938-948`, `assets/sky130_pdk_decl.json:454-465` |
| F-18 | 엔진 코드에 'trim'은 없다 | grep 2026-10-15 |

### N3.1 흐름(두 단계 실행, T-2)

1. **1단계(후보·추천)**: trim 선언이 있는 spec으로 원본 topology를 평가한다. 랜덤 offset 판정은 N3.6 의미로 바꿔 둔다. 주입 쌍과 극성마다 다음을 낸다(FR-T2).
   * front 위 t의 범위와 부호
   * headroom 창
   * 잡음 영향
   * 추천 N·m(N3.4 1단계 식)
   * 그 구성으로 `augment_trim`이 만든 파생 topology와 connectivity 표

   topology 파일은 바꾸지 않는다.
2. **승인**: 사용자가 파생 topology와 connectivity 표를 보고 주입 쌍, 극성, N, m을 고른다. 이것이 승인 기록이다(N3.3). 이 선택은 2단계에서 **고정값**이다.
3. **2단계(사이징)**: 로더가 spec trim 필드와 승인 선택을 합쳐 `trim_decl`을 만든다. `augment_trim`이 파생 topology를 다시 만들고, 결속 검사(N3.3)를 통과하면 정상 흐름(GB0~GB9)을 돌린다.
   * N·m은 고정이다. 단위 전류 I_u만 경계에서 유도한다(N3.4).
   * 보정 구간·잔여는 제약으로 판정한다.
4. **되돌림**: 2단계에서 고정 N·m으로 가능한 해가 없으면 사유(`trim_config_infeasible`와 위반 경계)를 보고하고 멈춘다. 다음 행동은 1단계 재실행과 재승인이다. 엔진이 N·m을 스스로 바꾸지 않는다.

### N3.2 주입 쌍 규칙(구조 규칙, 이름 없음)

* **쌍 정의**: S1 matching group 가운데 상태가 derived(멤버 정확히 2)인 `diff_pair` 그룹(F-12)에서, 두 멤버가 모두 `metric_structure.input_cells`(F-5)에 드는 것이다. 주입 쌍은 그 두 소자의 drain 넷 (n_p, n_n)이다. p/n 구분은 게이트 넷의 포트 역할(`differential_input_p/n`)로 한다.
* **이 정의를 쓰는 이유**: 자기동형 궤도로 짝을 지으면 미러 부하(단일 종단 출력) 회로에서 성립하지 않는다(F-11).
* **미러 부하에서도 차동 주입이 유효하다는 원리**: 다이오드 쪽 drain 넷에 전류 +I를 넣으면 다이오드 소자 전류가 I만큼 줄고, 미러 출력 전류도 같은 비율로 준다. 그래서 출력 넷에서 보면 −I를 넣은 것과 같은 방향의 효과가 난다. 즉 z[n_diode] ≈ −z[n_out]이다(미러 비 1, 다이오드 노드 임피던스가 출력 노드보다 훨씬 낮을 때의 근사). 따라서 쌍 차동 주입의 전달 t = (z[n_p] − z[n_n])/(2·A_dm)은 0이 되지 않는다. 엔진은 근사식을 쓰지 않고 z를 그대로 계산한다.
* **정의되지 않는 경우**: derived `diff_pair`가 입력 셀 안에 없으면 `trim_pair_undefined`를 보고하고 후보를 내지 않는다. diff_pair가 review_needed(멤버 3 이상)이거나 입력 셀 밖이어도 같다. 조용한 대체는 금지다.
* **상보 입력쌍**(입력 셀 안에 nmos·pmos `diff_pair` 두 개): 쌍마다 따로 후보를 낸다(D-7).
* **단일 입력 회로**: 차동 입력 포트가 없어 `diff_pair`가 입력 셀에 없다. 이 범위에서는 `trim_single_input_unsupported`다(D-8, X-11).
* **극성**(쌍마다 둘): nmos 싱크 셀은 주입 넷에서 하단 레일 쪽으로 전류를 뺀다. pmos 소스 셀은 상단 레일 쪽에서 넣는다. 극성마다 headroom 창을 경로 합(F-15)으로 계산한다. 창은 1단계 봉인 점 주입 넷 전압과 그 레일 사이에서 셀 출력 소자 VDsat + 스위치 VDS가 들어갈 여유다.
* **순위 키**: 기본안은 headroom 창이 비지 않은 (쌍, 극성) 가운데 \|t\| 내림차순이다. 잡음은 값으로 보고만 한다(D-5).

### N3.3 `augment_trim`, 승인 기록, 결속

* **서명**: `augment_trim(topology, trim_decl) -> (derived_topology, provenance)`(T-2 서명). 순수 함수이고 파일을 쓰지 않는다. 선택(쌍·극성·N·m)은 `trim_decl` 안에 있다(D-15).
* **붙이는 것**(T-3):
  * 주입 쌍의 두 넷에 연결된 steering 출력
  * 이진 하위 m비트 셀
  * 상위 thermometer 셀
  * 단위 셀 게이트 바이어스 연결(원천은 D-9)
  * 스위치(표현은 D-10)
* **코드 표현**(D-10 기본안): 스위치 게이트는 스위치마다 전용 넷에 둔다. 코드는 `trim_decl` 안의 'DC 값 벡터'(전용 게이트 넷마다 on/off 전압)로 표현한다. 그래서 코드는 파생 topology의 connectivity 지문 밖에 있고, 코드 상태를 바꿔도 지문은 같다. 승인 결속은 `trim_decl` 해시(N3.3 출처 기록)로 유지된다. 엔진은 N3.5의 네 코드 상태만 평가한다.
* **스키마**: 파생 topology는 원본 스키마(F-7)를 그대로 지키고 새 키를 넣지 않는다. trim 역할은 출처 기록과 승인 기록으로 S1에 전달한다.
* **출처 기록**: 원본 `connectivity_fp`, trim 선언 해시, 변환 규칙 해시, 선택, 1단계 실행 id, 생성 소자·넷 이름 목록.
* **승인 기록**: 새 파일 `<name>.trim.json`(기본안)에 둔다. 담는 것은 `approval_id`, 원본 `connectivity_fp`, 파생 `connectivity_fp`, 변환 규칙 해시, 선택이다.
* **결속**(B4, 기본안 D-13):
  1. **spec**: `meta.topology_fp`(F-10)는 원본 topology에 묶인다. trim 선언이 있는 실행에서 로더는 spec 지문을 원본 지문과 대조하고, 파생 지문은 승인 기록과 대조한다.
  2. **structure.json**(F-8): 사실은 원본 지문에 묶인 채로 두고, 파생 실행에서도 원본 소자에만 적용한다. 그 대신 엔진이 검사를 하나 더 한다. 파생 S1·S1v에서 trim 소자를 뺀 유도 결과가 원본 실행의 유도 결과와 같은지 본다. 다르면 `trim_structure_divergent`로 정지한다.
  3. **승인 기록**: 다시 만든 파생 topology의 지문, 또는 변환 규칙 해시가 승인 기록과 다르면 `trim_approval_stale`로 **정지**한다(fail-closed). 이것은 structure.json 선례(review_needed로 되돌리고 계속)와 다르다(X-13). 이유는 승인되지 않은 회로를 사이징하는 것이 되기 때문이다.
* **규칙 지문 변화**(F-9): TR-4가 S1·S1v 규칙 파일(`trim_dac` 역할 유도)을 바꾸면 `structure_rule_fp()`가 바뀐다. 그러면 trim 선언과 무관하게 current_reuse_telescopic_ota와 nmcnr_amplifier의 structure.json 사실이 review_needed로 돌아간다. 두 파일을 재승인하는 것(사실 내용은 같고 `rule_hash`만 갱신)은 사용자 승인 사항이고, TR-4 병합 조건이다(N5, N9).

### N3.4 DAC 규칙(유도, 상수 없음)

기호: σ_in, V_sys,s, t, k, V_res, σ_U(N0.1). 단위 셀 수는 2^N − 1이고 I_T = (2^N − 1)·I_u, I_LSB = 2·I_u, I_FS = I_T다.

**DNL**(Bertotti 2012 식(3), p.2): 분할 DAC의 최악 전이는 thermometer 셀 하나가 켜지고 이진 하위 셀이 모두 꺼지는 코드다. 이때 바뀌는 단위 셀 수는 2^(m+1) − 1이다. 그 전이의 DNL 분산(LSB²)은 다음과 같다.

  E[DNL²_worst] = (2^(m+1) − 1 − 1/(2^N − 1))·σ_U²

차동 steering에서 단위 셀 하나가 δ를 2·I_u(1 + ε) 바꾸므로 상대 오차 ε는 σ_U 그대로이고, 식은 LSB 단위로 같다. 순수 이진은 m = N − 1의 최악 전이와 같다(Staudt 2011 Table I, p.3의 σ_U·√(2^n−1)과 정합).

σ_DNL(m) = σ_U·√(2^(m+1) − 1 − 1/(2^N − 1))로 쓴다(LSB 단위 최악 전이 DNL의 1σ). σ_U의 기준점(어느 θ·어느 봉인 점의 단위 셀 σ인가)은 G-5에서 정한다.

**부호 규약**: `offset_sys_mv`는 크기(\|오차\|/\|A_dm\|)이고, 부호 있는 출력 오차는 `output_error_v`로 따로 싣는다(`E/metrics/offset_systematic.py:7-8`). 이 계획에서 부호 있는 계통 offset은 V_sys,s = `output_error_v` / A_dm이다. 랜덤 offset이 없는 회로에서 출력을 균형시키는 입력 차동 전압은 −V_sys,s다.

**음의 DNL은 trim에 해가 없다**: 음의 DNL은 인접 보정 간격을 좁힐 뿐이라 잔여 상한을 키우지 않는다. 잔여를 넓히는 것은 양의 DNL뿐이다(Staudt 2011 §III, PDF p.3, `paper.md` 696-712행: 꼬리는 양의 DNL이 만들고, 의도적으로 음의 DNL 쪽으로 기운 trim DAC가 좋다). 그래서 DNL 자체에 별도 한계를 두지 않고, 양의 DNL이 들어가는 잔여 판정 하나로 판정한다.

**1단계 추천**(결과 표에 내고 승인 대상):

| 항목 | 규칙 |
|---|---|
| N | 아래 I_u 하한 ≤ I_u 상한이 어떤 m에서라도 성립하는 최소 정수다. 입력점(front 점마다인가, 최악값인가)과 N·m을 정하는 순서는 G-4에서 정한다 |
| m | 그 N에서 I_u 하한 ≤ I_u 상한(상한 안에 σ_DNL(m))이 성립하는 가장 큰 m(≤ N − 1)이다. T-3의 'DNL 부족'은 '이진 비트가 많아 σ_DNL(m)이 커져서 잔여 창이 닫히는 것'으로 유도한다. 그래서 창이 열리는 데까지만 상위 비트를 thermometer로 둔다 |
| 극성 | N3.2 순위 |

**2단계 판정**(N·m 고정):

| 항목 | 규칙 | 근거 |
|---|---|---|
| I_u 유도 | 하한(보정 구간의 선형 근사): \|t\|·(2^N − 1)·I_u ≥ k·σ_in + \|V_sys,s\|. 상한(잔여): \|t\|·I_u·(1 + k·σ_DNL(m)) ≤ V_res, 곧 아래 잔여 판정의 Δ_max/2 ≤ V_res(Δ_max = \|t\|·2·I_u·(1 + k·σ_DNL)). 기본안은 하한값을 쓴다(전력 최소, 상위 NFR-5, D-16). 하한 > 상한이면 `trim_config_infeasible`(N3.1-4) | 선형 근사는 유도용이다. 판정은 아래 균형 풀이다 |
| 보정 구간 판정 | 끝 코드 두 개에서 전회로 DC를 출력 균형으로 풀어 입력 차동 전압 V_in(−end), V_in(+end)를 얻는다. 이 값은 계통 offset을 이미 품고 있다(구간 중심 ≈ −V_sys,s). 조건은 **[−k·σ_in, +k·σ_in] ⊆ [min V_in(±end), max V_in(±end)]**다(상위 DEC-74: 판정은 전회로 하나). 선형 근사에서 V_in(±end) ≈ −V_sys,s ± \|t\|·I_T이므로 이 조건은 \|t\|·I_T ≥ k·σ_in + \|V_sys,s\|, 곧 위 하한과 같다. 판정값과 선형 근사의 차는 결과 JSON에 기록한다 | Staudt 2011 §II.A(p.1-2), Mohamed 2013 식(3)(p.3) |
| 잔여 판정 | 인접 코드 사이 보정 간격의 최댓값을 Δ_max라 하자. 최적 코드를 고를 때 잔여 상한은 Δ_max/2다. 간격을 넓히는 것은 양의 DNL뿐이고, 그 상한을 k·σ_DNL(m)로 두면 Δ_max = \|t\|·I_LSB·(1 + k·σ_DNL(m))이다. 조건은 **Δ_max/2 ≤ V_res** 하나다. 제안의 \|t\|·I_LSB ≤ V_res는 DNL을 따로 묶은 경우의 보수 근사다(X-12) | Staudt 2011 §II.C·§III(p.2-3), Bertotti 2012 식(3)(4)(5)(p.2-3) |
| σ_U | 단위 셀 θ(gm/ID·L)에서 F-3 경로로 계산한다. Pelgrom 상수는 쓰지 않는다. k를 전이 DNL 배수로 쓰는 한계는 D-3이다 | F-3 |
| θ | 단위 셀 gm/ID(`ln_idu` 계열)와 L만 둔다. I_u·I_T는 유도값이다(X-3) | 상위 NFR-5, F-16 |
| 자기일관 | t, σ_in(DAC mismatch 포함), V_sys,s는 파생 topology의 봉인 점 값이다. 유도값과 판정값이 다르면 판정값이 이긴다 | 상위 DEC-74 |

**제약**: trim 선언이 있을 때만 생기고, 출처는 spec 선언을 참조한다. 보정 구간 포함과 잔여 Δ_max/2 ≤ V_res 둘이다. DNL만의 별도 제약은 두지 않는다(유도되지 않은 상수가 필요하기 때문이다, NFR-T2).

**metric**: 이름은 상위 DEC-68 규칙으로 design이 정한다(제안 이름 trim_lsb, trim_range, trim_dnl, trim_power, trim_area).
* LSB 입력 환산값
* 보정 구간(양 끝 입력 환산값)과 선형 근사와의 차
* 잔여 상한 Δ_max/2(입력 환산)
* 최악 전이 DNL의 1σ σ_DNL(m)(LSB, 보고용)
* steering 공급 전력(`power_dc_w`에 이미 포함되므로 보고용)
* DAC 소자 면적(탐색 축 면적에 포함)

각 metric은 `verified_by`(SPICE 오라클)가 생긴 뒤에만 제약으로 쓴다(상위 N3.8).

### N3.5 코드 상태와 DC 검사

* **평가하는 코드 상태는 넷이다**. 중간 코드 두 개(δ = +I_u, δ = −I_u. δ = 0 코드는 없음)와 끝 코드 두 개(δ = ±I_T)다. 봉인은 δ = +I_u에서 하고, 나머지 셋은 포화 검사만 한다(D-17).
* **전류 0 소자**: 꺼진 스위치와 끝 코드에서 꺼진 쪽 출력 소자는 전류가 0이다. DC writer·gm/ID·LUT 경로가 이것을 다룰 수 있는지는 확인되지 않았다(G-1).
* **정상 동작점**: 중간 코드 가운데 기본안은 δ = +I_u(D-17)이고, 일반 DC 봉인 1~8로 검사한다. 두 주입 넷에 steering 공통 전류(각 ≈ I_T/2)가 들어가므로 입력 셀 부하 전류 균형이 바뀐다(Lu 2007 식(10), p.2). 이 변화는 DC writer가 trim 소자를 바이어스 전류원으로 다루면 자동으로 들어간다.
* **끝 코드**: 보정 구간 판정(N3.4)과 같은 풀이다. 출력이 균형이 되도록 입력 차동 전압을 함께 푼 DC 해에서 포화 여유(봉인 7)를 검사한다. 이때 **꺼진 쪽(전류 0) steering 출력 소자와 꺼진 스위치는 포화 검사에서 뺀다**. 이유는 전류가 없는 소자의 포화 조건은 정의되지 않기 때문이다. 개루프에서 끝 코드만 걸면 출력이 레일에 붙으므로 이 방식을 쓴다(X-4).

### N3.6 offset spec 의미 전환과 기존 해석과의 관계

| 대상 | trim 선언 없음(지금) | trim 선언 있음 |
|---|---|---|
| `offset_in_sigma_mv` | 절대 제약(current_reuse)이거나 보고 | 덮을 분포의 입력이다(파생 topology 값, DAC mismatch 포함). 보고는 유지한다. 같은 spec에 이 제약이 함께 있을 때의 처리는 D-4다 |
| `offset_excess` 가드 | 구조 가드 | trim 소자는 분자에 들어가고 분모(입력 셀)는 그대로다. 처리는 D-4다 |
| `offset_sys_mv` | 상한 = 랜덤 예산 | 부호 있는 값 V_sys,s는 균형 풀이 끝 코드 전압에 이미 들어 있다. 선형 하한에서는 \|V_sys,s\|로 쓴다(N3.4). 상한 규칙은 D-4다 |
| `iv_matching_l` L 하한 | 출발값 | 끈다. 판정은 바뀌지 않는다(F-4, X-5). 새 출발값 규칙은 design이 정한다 |
| `iv_matching_l` 가드 부하 | 부하 역할 소자 | trim 소자는 `trim_dac` 역할이라 들어가지 않는다(FR-T5) |
| 잡음 metric 4종 | 모든 MOS | trim 소자 잡음이 들어간다(F-14). `noise_excess_th` 분모는 그대로다 |
| 극점·PM·GBW | 모든 MOS 용량 | 주입 넷에 cdb·cgd가 더해진다. 전회로 MNA로 판정한다 |
| headroom·스윙 | 경로 합 | 셀 출력 소자 여유가 주입 넷 경로에 더해진다(N3.2 극성, N3.5) |
| 전력·면적 축 | DC 공급 전력, `sum_area` | I_T와 DAC 면적이 자동으로 들어간다. 디지털 디코더·코드 저장 면적은 넣지 않는다 |
| drift·1/f | 없음 / 보고 | 바꾸지 않는다. 보고서에 'offset trim은 drift와 1/f를 보정하지 않음'을 적는다(Kay 2024 §1.2, PDF p.7. 1/f는 chopper가 없앤다는 대비: Zhou 2017 p.2) |

### N3.7 잡음 영향 지표(후보표용)

DAC 출력 전류 잡음 i_n이 주입 쌍에 들어가면 입력 환산 잡음은 대략 \|t\|·i_n이다. 보정 구간 경계에서 I_T ∝ 1/\|t\|이고, i_n²은 출력 소자 gm에 비례한다. 그래서 쌍 선택은 잡음과 전력·면적 사이의 교환이다. 후보표 값은 기존 잡음 해석(adjoint, LUT 잡음 데이터)으로 계산하고 γ 같은 상수 모델은 쓰지 않는다(상위 DEC-96 (3)). Lu 2007 식(9)(p.2)는 주입 소자 transconductance를 작게 둘수록 주입 오차가 줄어든다는 같은 방향의 근거다.

---

## N4. 9회로 적용 판정 방법

판정은 규칙으로 하고, 단계마다 '해당 없음'은 사유 코드로 남긴다.

1. spec에 trim 선언이 없으면 → 무동작이다(완료 조건 (1)).
2. 입력 셀 안에 derived `diff_pair`가 없으면 → 차동 입력 포트가 없는 경우는 `trim_single_input_unsupported`(D-8), 그 밖은 `trim_pair_undefined`.
3. 모든 (쌍, 극성)의 \|t\| = 0이거나 headroom 창이 비면 → `trim_injection_infeasible`. 탐색 전에 유도와 함께 보고한다.
4. 그 밖은 → 후보표를 낸다.

**적용 예상**(2026-10-15 topology 연결 읽기 기준이고 엔진 실행 결과가 아니다. 확정은 card TR-7의 측정이다. trim 선언 여부와 값은 사용자 몫, D-11):

| 회로 | 입력 | 입력 쌍 (n쪽 게이트 / p쪽 게이트) | 예상 주입 쌍 drain 넷 | 부하 형태(연결로 본 것) | 현재 offset 항목 | 예상 판정 |
|---|---|---|---|---|---|---|
| current_reuse_telescopic_ota | 차동, 상보 | pmos M1a/M1b, nmos M4a/M4b | N1a2a/N1b2b, N3a4a/N3b4b | 각 drain → 캐스코드(M2a/b, M3a/b) | `offset_in_sigma_mv <= 3.3`, `offset_sys_mv` | 후보 두 쌍(D-7). 기존 절대 제약과 공존 처리 D-4 |
| folded_cascode | 차동 | nmos M1/M2 | X/Y | fold 넷(M3·M6 / M4·M5) | `offset_excess` | 후보 |
| ngcc_3stage_ff | 차동 | pmos M1/M2 | ND/V1 | 미러 부하(M3/M4), 단일 종단 | `offset_excess` | 후보(z[diode] ≈ −z[out]) |
| nmcnr_amplifier | 차동 | pmos M102/M103 | NodeF1/NodeF2 | fold 넷(M104·M106 / M105·M107) | `offset_excess` | 후보 |
| sf_pushpull_output_opamp | 차동 | nmos M1/M2 | N1/N2 | MOS 소스·drain 연결 없음(수동소자 부하로 보임) | `offset_excess` | 후보 |
| two_stage_ota | 차동 | nmos M1/M2 | D3/O1 | 미러 부하(M3/M4), 단일 종단 | `offset_excess` | 후보 |
| two_stage_ota_sf | 차동 | nmos M1/M2 | D3/O1 | 미러 부하(M3/M4), 단일 종단 | `offset_excess` | 후보 |
| common_gate_amplifier | 단일(소스 구동) | 없음 | -- | -- | 없음 | `trim_single_input_unsupported` |
| pushpull_follower_buffer | 단일 | (M3 pmos, M4 nmos가 같은 입력 게이트) | -- | -- | 없음 | `trim_single_input_unsupported` |

* 예상 차동 입력 후보는 7회로다. 각 회로에서 derived `diff_pair`가 실제로 생기는지는 TR-2에서 측정한다. 생기지 않으면 2번 사유로 보고한다.
* 근거는 `assets/library/<회로>.topology.json`(ports, netlist)과 `<회로>.sizing_spec.json`(current_reuse :225-242, folded_cascode :49-51 등)이다.

---

## N5. 단계 분할 초안(card 후보)

**공통 착수 조건**:
* T-4 순서를 지킨다(NFR-4 card 2 → XRUN-F1 A·B·C 병합 뒤).
* design 문서 `docs/02-design/features/offset-trim.design.md`가 있고, 독립 검증과 사용자 승인을 받았다(bkit PDCA).
* 그 card가 읽는 N7 결정이 닫혀 있다.

| card | 범위 | 선행 | 읽는 결정 |
|---|---|---|---|
| TR-0 (문서) | design 문서: 필드 스키마, 함수 서명, graph 필드, 실패 코드, metric 이름, test 목록, 승인 기록·결속 형식, 판정 규칙 소유자, TR-7 샘플 수 규칙. G-1~G-8을 닫는다. 독립 검증 | 이 계획 승인 | D-1~D-17, G-1~G-8 |
| TR-1 | spec trim 선언 스키마, 로더 규칙(D-4 공존 처리), `trim_decl` 합성(D-15), spec 지문 결속(N3.3-1) | TR-0 | D-1·D-2·D-4·D-12·D-13·D-15 |
| TR-2 | 노드 수반 벡터 z의 graph 필드 노출(F-2), 주입 쌍 규칙(N3.2), t·극성 headroom·잡음, 1단계 N·m 추천, 후보표 결과 JSON. 보고만 한다 | TR-1 | D-3·D-5·D-6·D-7 |
| TR-3 | `augment_trim`, 출처 기록, 파생 topology와 connectivity 표 출력, 승인 기록 로드와 결속 검사(N3.3-3), 진입점 배선 | TR-2 | D-9·D-10·D-13 |
| TR-4 | `trim_dac` 역할 유도(S1·S1v 신호 경로 제외, DC writer 바이어스 전류원), 가드·부하 집합 제외, 파생 대 원본 구조 동일 검사(N3.3-2). **착수 조건**: 규칙 지문 변경에 따른 structure.json 2개 재승인 계획을 사용자가 승인한다. **병합 조건**: 재승인을 마친다 | TR-3 | D-13·D-14 |
| TR-5 | DAC 규칙(N3.4)의 I_u 유도, 보정 구간·잔여 제약과 metric, 코드 상태와 끝 코드 균형 풀이(N3.5), 되돌림 사유 | TR-4 | D-1·D-3·D-16·D-17 |
| TR-6 | offset spec 의미 전환(N3.6), `iv_matching_l` 변경 | TR-5 | D-4 |
| TR-7 | 9회로 일반성 측정(N4 사유표), 선언 회로 E2E, SPICE 오라클 대조(코드 스윕·Monte-Carlo 잔여 분포), T-5 온도 검증(N5.1) | TR-6, 오라클 확장(레인 P) | D-11 |

**완료 조건**(기능 전체):
1. **trim 선언이 없는 실행**에서 9회로 결과가 base와 비트 동일하다. 범위는 D-14다. 기본안은 structure.json 2개를 새 `rule_hash`로 재승인한 뒤에 잰다. 그 두 회로 결과 가운데 `rule_hash` 값 자체를 담는 필드는 비교에서 뺀다.
2. 선언 회로에서 trim 제약·metric이 `verified_by`를 가진다.
3. SPICE 오라클 코드 스윕 판정을 통과한다. 내용은 Monte-Carlo 표본마다 잔여 ≤ V_res인 코드가 있는 비율이다. 판정 규칙과 합격선은 TR-0에서 독립 검증자가 정하고 소유한다.
4. 모든 새 함수가 진입점에서 호출된다(배선 증거).
5. 상위 N6.3의 graph 단일 정본·재계산 계수·파일 분할 확인과 design 대 구현 gap 분석을 통과한다.

### N5.1 TR-7 검증 항목(T-5)

**판정**(합격·불합격): 27 °C·TT 한 조건이다. 엔진 합격 조건(상위 DEC-96 (3))과 같다.

**순서**: 아래 1번(엔진 σ_in 대 SPICE σ_in 일치)을 TR-7에서 맨 먼저 확인한다. 이것이 맞지 않으면 나머지 Monte-Carlo 결과로 엔진 판정을 해석할 수 없다.

| # | 항목 | 성격 |
|---|---|---|
| 1 | 엔진 `offset_in_sigma_mv`(파생 topology, DAC mismatch 포함) 대 SPICE Monte-Carlo σ_in 일치 | 판정 전제(첫 확인) |
| 2 | 27 °C 잔여 분포: 샘플마다 trim 절차를 흉내 낸다(측정 → 코드 선택 → 잔여). 잔여 ≤ V_res 비율을 잰다 | 판정(완료 조건 (3)) |
| 3 | 고정 코드 온도 sweep: 샘플마다 27 °C에서 고른 코드를 고정하고, 선언 온도 범위에서 잔여 offset을 잰다 | 보고 전용 |
| 4 | 코너별 보정 구간: 공정 코너마다 끝 코드 균형 풀이 구간 [V_in(−end), V_in(+end)]를 잰다 | 보고 전용 |
| 5 | 끝 코드 headroom의 온도 의존: 온도별 끝 코드에서 포화 여유를 잰다 | 보고 전용 |

**한계**(보고서에 적는다):
* 샘플 수는 k 꼬리를 확인할 수 있는 규모여야 한다. k가 클수록 필요한 샘플이 늘어나는 비용 한계가 있다. 샘플 수 규칙은 TR-0에서 독립 검증자가 정한다.
* 몬테카를로는 샘플마다 trim 절차(측정 → 코드 선택 → 잔여)를 흉내 내야 한다. 코드를 하나로 고정한 일반 MC는 trim 뒤 분포를 재지 못한다.
* 패키징 응력, 장기 drift, trim 측정 잡음은 DC 몬테카를로의 범위 밖이다(Zhou 2017 p.1: 패키지 뒤 trim이 응력 이동을 피하는 이유; Kay 2024 §1.2 p.7: CMOS drift는 offset과 비례하지 않음).
* 온도 drift는 DAC 바이어스 원천(D-9)에 직접 의존한다. t(T)와 δ(T)가 온도에 따라 함께 변하고, 그 변화의 방향과 크기는 바이어스 원천이 어떤 온도 특성의 전류를 주는지로 정해진다(G-8).

---

## N6. 검증 원칙

* 판정자는 SPICE 오라클(`tools/spice_oracle/`, 엔진 import 금지)이다. trim은 코드 스윕과 Monte-Carlo가 필요하다. 오라클 확장(코드 입력, 표본별 최적 코드 선택)은 레인 P 작업이다.
* 엔진 쪽 test는 interface card만 보고 쓴다. 기대값은 피검 함수를 불러 만들지 않는다.
* 일반성: 9회로 전수에서 사유 코드를 측정해 보고한다.

---

## N7. 열린 항목

### N7.1 사용자 결정 필요

기본안은 원칙으로 정한 것이고 사용자가 바꿀 수 있다.

| ID | 질문 | 기본안 |
|---|---|---|
| D-1 | V_res의 뜻: 잔여 offset의 최악 한계인가, 잔여 분포의 1σ인가 | 최악 한계(N3.4 잔여 판정 Δ_max/2 ≤ V_res) |
| D-2 | 수율 표현: k만 받을지, 수율 목표 Y도 받아 k로 환산할지. 환산에는 정규·양측 가정이 필요하다 | k만 받는다(분포 가정을 엔진에 넣지 않음). T-1을 좁히는 안이다(X-8) |
| D-3 | 잔여 판정 안 양의 DNL 상한 배수로 spec k를 그대로 쓸지(k·σ_DNL(m)). 한계: k는 offset 분포 한쪽 꼬리의 배수다. 양의 DNL 상한은 최악 전이 여러 개(thermometer 경계마다)에 동시에 걸리므로, 같은 k로는 '모든 전이 만족' 확률이 offset 수율과 같지 않다(전이 수만큼 낮다) | spec k를 그대로 쓰고 이 한계를 보고에 적는다. 따로 선언하는 안은 사용자 선택이다 |
| D-4 | 같은 spec에 기존 offset 제약(`offset_in_sigma_mv <=`, `offset_excess`, `offset_sys_mv` 상한)과 trim 선언이 함께 있을 때의 처리 | 로더가 `offset_in_sigma_mv <=`와 trim 선언의 공존을 거부한다(spec 수정은 사용자 몫). `offset_excess`와 `offset_sys_mv` 상한은 보고로 내린다 |
| D-5 | 후보 순위 키에 DAC 잡음 영향을 넣을지 | 넣지 않고 값만 보고한다 |
| D-6 | front 위에서 t의 부호나 크기가 크게 바뀌는 쌍의 처리 | 표시하고 거르지 않는다 |
| D-7 | 상보 입력쌍 회로에서 DAC를 쌍마다 둘지, 하나만 둘지 | 쌍마다 하나씩 둔다(제안 '상보 입력쌍은 trim 각각'). 판정이 입력 DC 한 점이라는 한계를 보고한다 |
| D-8 | 단일 입력 회로 지원 | 이번 범위에서는 정지한다(X-11) |
| D-9 | 단위 셀 게이트 바이어스 원천: 기존 바이어스 넷 미러인가, 새 `bias_inputs` 항목인가. 이 선택은 온도 drift에 직접 영향을 준다(t(T)·δ(T), N5.1·G-8). 27 °C 판정에는 드러나지 않고 TR-7 온도 sweep에서만 보인다 | 새 `bias_inputs` 항목. 기존 바이어스 기둥과 L 동치류를 바꾸지 않는다 |
| D-10 | steering 스위치 표현과 코드 표현: 트랜지스터 + 전용 게이트 넷 + `trim_decl` DC 값 벡터인가, 이상 스위치 + 선언 VDS 예산인가 | 트랜지스터. 스위치마다 전용 게이트 넷을 두고, 코드는 `trim_decl`의 DC 값 벡터(connectivity 지문 밖, 승인 결속은 `trim_decl` 해시)로 표현한다. on/off 레벨은 회로 레일 전압(`supply_nets`)이다 |
| D-11 | trim 선언을 넣을 회로와 V_res·k·온도 값 | 사용자 몫이다. 엔진 검증용은 `origin: fixture` 픽스처 spec으로 따로 둔다 |
| D-12 | trim 온도와 상위 DEC-96 (3) '합격 = TT 27 °C 한 조건'의 관계 | trim 온도 = 합격 조건 온도로 제한하고, 다르면 거부한다(X-1) |
| D-13 | 파생 topology 결속 방식(N3.3): spec·structure.json은 원본 지문에 묶고, 파생 지문은 승인 기록에만 묶는 안. 대안은 파생 topology용 spec·structure.json을 따로 두는 것이다 | 원본 결속 + 파생 대 원본 구조 동일 검사 + 승인 기록 fail-closed. 근거: 사용자 값(spec)과 회로 해석 승인(structure)을 한 곳에만 두고(단일 정본), 파생 회로만 따로 승인한다 |
| D-14 | 완료 조건 (1) '비트 동일'의 범위. TR-4의 규칙 파일 변경으로 `rule_hash`가 바뀌면 structure.json이 있는 두 회로는 재승인 전까지 결과가 달라진다 | trim 선언이 없는 실행만 대상이다. 기본안은 두 structure.json을 새 `rule_hash`로 재승인(사실 내용 동일)한 뒤 잰다. 비교에서 빼는 것은 '규칙 지문을 담는 모든 필드'다. `rule_hash`, S1 지문 `S1Key.rule_fp`(`E/graph/s1_values.py:5, :233-237`), 그것을 입력 버전으로 품은 필드 지문이 포함된다. 정확한 목록은 G-3이다 |
| D-15 | 선택(쌍·극성·N·m)의 위치: `trim_decl` 안(로더가 spec + 승인 기록을 합성)인가, 별도 인자 `selection`인가 | `trim_decl` 안. T-2 서명 `augment_trim(topology, trim_decl)`을 지킨다(X-9) |
| D-16 | 2단계 I_u를 하한(보정 구간 경계, 전력 최소)으로 둘지, 상한(잔여 경계)으로 둘지, θ로 둘지 | 하한. 상위 NFR-5와 전력 목적 축 때문이다(X-3) **→ 사용자 결정 T-7(2026-10-15 "TD-1은 θ안")로 변경: I_u는 θ 변수, 범위·잔여는 I_u 제약, 전력 최소화가 하한으로(design `offset-trim.design.md` §10.3, X-T14)** |
| D-17 | 정상 동작점으로 쓸 중간 코드: δ = +I_u인가, −I_u인가, 둘 다인가 | +I_u 하나로 봉인하고, −I_u는 끝 코드와 함께 포화 검사만 한다 |

### N7.3 TR-0 design에서 반드시 닫을 항목

사용자 결정이 아니라 design 작성·검증에서 근거와 함께 닫아야 하는 기술 항목이다. 닫히지 않으면 해당 card를 시작하지 않는다.

| ID | 항목 | 관련 card |
|---|---|---|
| G-1 | 전류 0 MOS(꺼진 스위치, 끝 코드의 꺼진 쪽 출력 소자)를 DC writer·gm/ID·LUT 경로가 다룰 수 있는가. `CELL_OFF`는 AC 셀 종류일 뿐이고(`E/graph/cells.py:124-128`), DC 쪽 전류 0 처리를 보장하지 않는다. 다룰 수 없으면 그 상태의 표현(소자 제외, 별도 포화 검사 경로)을 design이 정한다 | TR-3·TR-5 |
| G-2 | 파생 대 원본 구조 동일 검사(N3.3-2)의 비교 필드 범위. 주입 넷이 가지 끝 넷이 되면 원본 소자에 대해서도 `_sibling_rule`·`_counterparts`·column 규칙(matching group, 대응 넷) 결과가 달라질 위험이 있다. 비교 필드를 정의하고, TR-2·TR-4 전에 9회로에서 그 차이를 측정하는 단계를 둔다 | TR-2·TR-4 |
| G-3 | D-14 비교 제외 필드 목록: 규칙 지문을 담는 모든 필드(`rule_hash`, `S1Key.rule_fp` `E/graph/s1_values.py:5, :233-237`, 그것을 입력 버전으로 품은 필드 지문) | TR-4·완료 조건 (1) |
| G-4 | 1단계 N 추천의 입력점(front 점마다 따로인가, front 위 최악값인가)과 N·m을 정하는 순서(N 먼저 → m인가, (N, m) 쌍 전수인가) | TR-2 |
| G-5 | σ_U의 기준: 1단계 추천에서 어느 θ(단위 셀 gm/ID·L 상자의 어느 점)의 σ_U를 쓰는가. 2단계 판정에서는 봉인 점의 θ 값이고, thermometer 셀은 단위 셀 2^m개 복제(독립)로 본다 | TR-2·TR-5 |
| G-6 | 단일 종단 출력 회로에서 '출력 균형'(끝 코드 균형 풀이, N3.4·N3.5)의 기준. 기본 후보는 `offset_systematic`이 쓰는 선언 출력 기준 DC(spec `node_voltage_targets_v`)이고, 선언이 없으면 `reference_undeclared`로 보고한다(`E/metrics/offset_systematic.py:6, :12, :42`) | TR-5 |
| G-7 | 코드 상태 DC 값 벡터(N3.3, D-10)를 승인 해시에 넣을지, 승인된 N·m·극성에서 규칙으로 유도할지(유도하면 해시에는 규칙 지문만 들어간다) | TR-1·TR-3 |
| G-8 | 바이어스 원천(D-9)별로 t(T)·δ(T)의 온도 의존을 TR-7 온도 sweep(N5.1 3번)에 어떻게 보고할지 | TR-7 |

### N7.2 원래 취지와 다름(따로 보고)

| ID | 내용 |
|---|---|
| X-1 | T-1의 'trim 온도 조건' 필드는 두지만, 엔진 합격 조건이 TT 27 °C 하나라서 다른 온도는 평가할 수 없다. D-12 기본안은 사실상 27 °C 고정이다. 다른 온도를 지원하려면 LUT 온도 축이나 오라클 온도 옵션이라는 별도 범위가 필요하다 |
| X-3 | 제안은 θ 후보로 'I_LSB 또는 I_T·단위 gm/ID·L'을 들었다. 기본안은 I_u(따라서 I_LSB·I_T)를 θ에서 빼고 경계에서 유도한다(D-16) |
| X-4 | 제안의 '코드 양 끝 DC 동작점 검사'를 '출력 균형 입력 전압을 함께 푼 해'로 구체화했다. 꺼진 셀은 포화 검사에서 뺀다(N3.5) |
| X-5 | 제안의 'iv_matching_l 완화'는 판정을 바꾸지 않는다. `iv_matching_l`은 출발값 전용(F-4)이고, 의미 전환의 실체는 spec 제약 처리(D-4)다 |
| X-6 | 제안의 'drift·1/f는 유지'에서, 엔진에는 drift metric이 없다(F-6). '유지'는 '보정 대상 아님 + 보고 문구'로만 구현한다 |
| X-7 | 제안의 t_n = z[n]/A_dm(노드 하나)은 차동 steering에서 쌍의 차 t = (z[n_p] − z[n_n])/(2·A_dm)로 바뀐다. z 벡터 노출이라는 엔진 변경이 필요하다(F-2) |
| X-8 | D-2 기본안(k만)은 T-1 'k(또는 수율 목표)'를 좁힌다 |
| X-9 | 검증 지적: v0.1의 서명 `augment_trim(topology, trim_decl, selection)`은 T-2 서명 `(topology, trim_decl)`과 달랐다. v0.2 기본안(D-15)은 selection을 `trim_decl` 안에 넣어 T-2 서명으로 돌아왔다. 다만 `trim_decl`이 spec 값만이 아니라 승인 선택까지 담는다는 점은 T-2 원문에 없는 해석이다 |
| X-10 | 승인 대상: T-2는 '파생 topology 승인'이다. v0.1은 후보 노드를 승인하는 흐름이라 사용자가 파생 topology를 보지 않았다. v0.2는 1단계가 파생 topology와 connectivity 표를 내고 사용자가 그것을 승인한다(FR-T2·FR-T4). 원문과 일치시켰고, 기록을 위해 남긴다 |
| X-11 | D-8 기본안('단일 입력 회로는 범위 밖 정지')은 제안 '단일 입력 회로는 spec에 offset 항목이 있을 때만'을 좁힌다. 제안은 offset 항목이 있으면 단일 입력도 대상으로 본다 |
| X-12 | 제안의 LSB 식 I_LSB ≤ V_res/\|t\|와 'DNL < LSB/2'를 잔여 판정 하나 Δ_max/2 ≤ V_res(Δ_max = \|t\|·I_LSB·(1 + k·σ_DNL(m)))로 바꿨다. 최적 코드 잔여 상한의 정확한 표현이고, 양의 DNL만 잔여를 넓힌다는 근거(Staudt §III)를 따른다. 제안의 'DNL < LSB/2'는 별도 제약으로 두지 않는다 |
| X-13 | 승인 기록 결속 실패는 정지(fail-closed)다. structure.json 선례(F-8: review_needed로 되돌리고 계속)와 다르다 |
| X-14 | 제안의 범위식 I_range ≥ k·σ_in/\|t\|를 다음 두 가지로 바꿨다. (a) 균형 풀이 끝 코드 전압으로 한 포함 판정 [−k·σ_in, +k·σ_in] ⊆ [V_in(−end), V_in(+end)]. 끝 코드 전압이 계통 offset을 이미 품고 있고, 선형 근사에서는 \|t\|·I_T ≥ k·σ_in + \|V_sys,s\|와 같다(v0.2의 [V_sys ± k·σ_in] 형태는 계통 offset을 두 번 센 오류여서 v0.3에서 고쳤다). (b) 판정은 전회로 균형 풀이이고 선형식은 유도용이다. 제안의 N = ⌈log2(2·I_range/I_LSB)⌉은 1단계 추천 식으로만 남고, 2단계 N은 승인 고정값이다(B3) |
| X-15 | FR-T1 '선언이 없으면 지금과 비트 동일'은 v0.1에서 무조건이었지만, v0.2부터 완료 조건 (1)의 범위(D-14: trim 선언 없는 실행, structure.json 재승인 뒤, 규칙 지문 필드 제외)로 좁혀졌다. 규칙 파일 변경(TR-4)이 지문을 바꾸기 때문이다 |
| X-16 | v0.2에서는 'k·σ_DNL ≤ 1/2'의 1/2(유도 안 된 상수)가 T-3 'DNL 부족'의 기준이었다. v0.3에서 DNL 별도 제약을 지우고, 'DNL 부족'을 잔여 창(I_u 하한 ≤ 상한)이 닫히는 것으로 유도해 **해소**했다 |

---

## N8. 원문 근거표

* 보관 위치: `skills/analog-gmid-design/assets/technique/sources/<폴더>/`(`source.pdf`·`paper.md`). 쪽 렌더는 `python tools/pdf_to_md.py ensure`로 만든다.
* 쪽 번호는 PDF 쪽이다. 수치는 인용하지 않는다.

| R | 원문 | 웹 | 로컬 PDF | 쪽·위치 | 이 계획에서 쓰는 곳 |
|---|---|---|---|---|---|
| R1 | A. R. Mohamed, M. F. Ibrahim, F. Farag, 'Input Offset Cancellation Trimming Technique for Operational Amplifiers', SIECPC 2013 | [pure.kfupm.edu.sa](https://pure.kfupm.edu.sa/en/publications/input-offset-cancellation-trimming-technique-for-operational-ampl/) | `offset_trim__mohamed_2013/source.pdf` (원본 `G:/내 드라이브/work/Todoc/논문모음/input offset cancellation trimming technique for operational amplifier_mohamed2013.pdf`) | p.2 Fig.2·식(1)(2), p.3 Fig.4·식(3)(4)(7), p.4 Fig.9·11 | 범위 밖 대안(신호 경로 level shifter: 버퍼 이득 1 미만, 대역 제한) 비교. 주입항이 offset을 상쇄하는 구조(N3.4) |
| R2 | H. M. von Staudt, 'Trim DAC Design with Minimum DNL for Self-Trim with Self-Test Schemes', IEEE IMS3TW 2011 | [doi:10.1109/IMS3TW.2011.34](https://doi.org/10.1109/IMS3TW.2011.34) | `offset_trim__staudt_2011/source.pdf` (원본 `.../논문모음/(Bible - self trim) Trim DAC Design with Minimum DNL for Self-Trim with Self-Test Schemes__staudt2011.pdf`) | p.1-2 §II.A, p.2-3 §II.C·Table I·Fig.4, p.3-4 §III·Table II·III | 범위가 분포를 덮을 조건과 'µ = 0' 가정(X-14), 이진 주 전이 DNL, 양의 DNL 꼬리, 잔여와 DNL(N3.4) |
| R3 | Y. Zhou, A. Kay, 'Offset Correction Methods: Laser Trim, e-Trim, and Chopper', TI SBOT037A, 2017 | [ti.com/lit/SBOT037](https://www.ti.com/lit/SBOT037) | `offset_trim__zhou_2017/source.pdf` (원본 `.../논문모음/(Reference - trim) Offset Correction Methods_Laser Trim, e-Trim , and Chopper.pdf`) | p.1 laser·e-Trim, p.2 Fig.2·Fig.3·Table 1 | 패키지 뒤 내부 보정 전류원 trim(e-Trim, 'low offset voltage and drift' 제품군, p.1). chopper는 시간·온도 drift를 평균해 없애고 1/f를 제거한다(p.2). 한 온도 trim이 drift를 보정하지 못한다는 근거는 R7이다 |
| R4 | G. Bertotti et al., 'An 8 bit current steering DAC for offset compensation purposes in sensor arrays', Adv. Radio Sci. 10:201-206, 2012 | [doi:10.5194/ars-10-201-2012](https://doi.org/10.5194/ars-10-201-2012) | `offset_trim__bertotti_2012/source.pdf` (원본 `G:/내 드라이브/work/Todoc/기술문서/ADC/An 8 bit current steering DAC for offset compensation purposes in sensor arrays_ars-10-201-2012.pdf`) | p.2 §2·§3 식(2)(3), p.3 식(4)(5), p.4 Fig.3·4, p.5 Fig.5-8 | 분할 DAC 최악 DNL 분산 식(3)(N3.4 DNL), 차동 steering 셀(T-3), 단위 전류 σ의 동작 영역 의존 |
| R5 | C.-W. Lu, 'An Offset Cancellation Technique for Two-Stage CMOS Operational Amplifiers', IEEE ICICDT 2007 | 찾지 못함 | `offset_trim__lu_2007/source.pdf` (원본 `.../기술문서/ADC/(Ref) An Offset Cancellation Technique for Two-Stage CMOS OPamp.pdf`) | p.2 Fig.2·3, 식(6)-(10) | 1단 출력 넷 전류 주입, 주입 소자를 더할 때 부하 전류 균형(N3.5), 주입 오차 ∝ G_m,aux/G_m1(N3.7) |
| R6 | V. Srinivasan et al., 'A Precision CMOS Amplifier Using Floating-Gate Transistors for Offset Cancellation', IEEE JSSC 42(2), 2007 | [doi:10.1109/JSSC.2006.889365](https://doi.org/10.1109/JSSC.2006.889365) | `offset_trim__srinivasan_2007/source.pdf` (웹 다운로드) | p.1 §I·Fig.1 | current-mode DAC로 부하 전류를 조정하는 offset 보상(N3.2 주입 쌍 = 입력쌍 drain) |
| R7 | A. Kay, 'Op Amp Offset Voltage and Bias Current Limitations', TI SBOA590, 2024 | [ti.com/lit/pdf/sboa590](https://www.ti.com/lit/pdf/sboa590) | `offset_trim__kay_2024/source.pdf` (웹 다운로드) | §1.2: p.6 Figure 1-6, p.7 Figure 1-8 문단 | CMOS drift는 offset에 비례하지 않아 한 온도 trim이 drift를 보정하지 않는다(N1.2, N3.6) |

---

## N9. 위험과 대응

| 위험 | 대응 |
|---|---|
| trim 소자가 S1v에서 `load`·`tail_source`로 분류돼 offset·잡음 가드와 `iv_matching_l` 부하 집합을 오염시킨다 | `trim_dac` 역할을 먼저 둔다(TR-4). 파생 대 원본 구조 동일 검사(N3.3-2)로 막는다 |
| TR-4 규칙 파일 변경으로 `structure_rule_fp()`가 바뀌어 current_reuse_telescopic_ota·nmcnr_amplifier의 structure.json 사실이 review_needed로 돌아간다(trim 선언과 무관) | 재승인은 사용자 승인 사항이다. TR-4 착수 조건(재승인 계획 승인)과 병합 조건(재승인 완료)에 넣는다. 완료 조건 (1)의 범위는 D-14다 |
| spec `meta.topology_fp`가 파생 topology 지문과 맞지 않아 로드가 거부된다 | D-13 결속: spec은 원본 지문에 묶는다(TR-1) |
| t가 θ에 따라 변해서 승인한 쌍·N·m이 2단계에서 불가능해진다 | 1단계 표에 front 위 t 범위를 적는다. 2단계는 `trim_config_infeasible`로 멈추고, 재승인으로 되돌린다(N3.1-4). 엔진이 몰래 N·m을 바꾸지 않는다 |
| 주입 넷(fold 넷 등)의 headroom이 셀 출력 소자 VDsat + 스위치 VDS를 못 받친다 | 극성별 headroom 창으로 후보를 거른다(N3.2). 끝 코드 균형 풀이에서 포화를 검사한다(N3.5) |
| DAC 용량이 비주극점을 낮춰 PM이 떨어진다 | 전회로 MNA 판정에 자동으로 들어간다. 후보표에 주입 넷 용량 증가를 보고한다 |
| 파생 topology 디스크 사본이 원본과 어긋난다(stale) | 사본은 정본이 아니다. 실행마다 다시 만들고 승인 기록과 대조한다(NFR-T3, N3.3-3) |
| 범위·DNL 유도에 원문 관례값(±5σ, 5 %, 'DNL < LSB/2' 같은 경계 등)이 섞인다 | NFR-T2. 숫자 리터럴 lint와 design 검증 항목에 넣는다 |
| 상보 입력쌍 회로에서 한 CM 점 판정이 ICMR 전체 보정을 보장하지 않는다 | D-7 보고 문구. ICMR 여러 점 판정은 범위 밖이다 |
| 27 °C 한 온도에서 trim하므로 다른 온도에서 잔여가 V_res를 넘는다(CMOS drift는 offset과 비례하지 않음, Kay 2024 §1.2 p.7) | T-5: 판정은 27 °C·TT. 고정 코드 온도 sweep·코너별 보정 구간·끝 코드 headroom 온도 의존을 보고 전용으로 낸다(N5.1). 보고서에 단일 온도 trim 한계를 적는다(FR-T9) |
| DAC 바이어스 원천(D-9)의 온도 특성이 t(T)·δ(T)를 바꿔 보정량 자체가 온도에 따라 변한다 | D-9 설명과 G-8. TR-7 온도 sweep으로 드러낸다 |
| 엔진 σ_in이 SPICE σ_in과 맞지 않으면 MC 잔여 결과로 엔진 판정을 해석할 수 없다 | N5.1 1번을 TR-7 첫 확인으로 둔다 |
| MC 샘플 수가 k 꼬리를 확인하기에 부족하다(비용 한계) | 샘플 수 규칙을 TR-0에서 독립 검증자가 정한다. 부족하면 결과에 '꼬리 미확인'으로 적는다 |
| 패키징 응력·장기 drift·trim 측정 잡음은 DC MC로 재지 못한다 | 범위 밖으로 보고서에 적는다(N5.1 한계) |
| 기존 offset 제약과 trim 선언이 함께 있으면 한쪽이 조용히 무력화된다 | D-4 기본안: 로더 거부 |
| 전류 0 소자(꺼진 스위치·꺼진 출력)가 DC writer·LUT 경로에서 정의되지 않은 값을 낸다 | G-1을 TR-0에서 닫는다 |
| trim 소자를 붙이면 원본 소자의 matching group·대응 넷 유도가 바뀐다 | G-2 비교 필드 정의와 TR-2·TR-4 전 9회로 측정 |
| 같은 k로 양의 DNL 상한을 두면 다중 전이 때문에 실제 수율이 offset 수율보다 낮다 | D-3 한계 문구. 오라클 Monte-Carlo 판정(완료 조건 (3))이 실제 비율을 잰다 |
