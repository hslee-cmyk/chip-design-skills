---
template: design
version: 0.1
plan: ../../01-plan/features/offset-trim.plan.md
plan_version: 0.4
---

# offset-trim Design Document (card TR-0)

> **Summary**: 승인된 계획 `offset-trim.plan.md` v0.4(사용자 결정 T-1~T-6)를 엔진 `gmid_engine` 설계로 옮긴다. 계획 N7.3의 TR-0 닫을 항목 G-1~G-8과 TR-7 샘플 수 규칙을 닫고(§3, §17), 결정적 변환 `augment_trim`, `trim_decl`·승인 기록·결속, 1단계 후보·추천, 2단계 θ·유도·코드 상태·균형 풀이·제약·metric, 구조 역할 `trim_dac`, graph 필드 소유, 결과 JSON, 파일 분할, card 범위와 test 초안, 9회로 적용 판정을 정한다.
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code (design 작성자 역할)
> **Status**: design 초안 v0.1 (2026-10-15). 독립 검증·사용자 승인 전이다. 사용자 결정이 더 필요한 곳과 원래 취지와 다른 판단은 정하지 않고 §18에 모았다.
> **기준**: 엔진 인용은 `944020f`(worktree `wt/trim-design`)의 `파일:줄`이다. `E/` = `skills/analog-gmid-design/gmid_engine/`. 엔진 design 인용은 `40 §x`(`gain-budget-gmid-sizing.40-engine.design.md`), `41 §x`.
> **전제(T-4)**: 엔진 구현은 NFR-4 card 2 → XRUN-F1 card A·B·C 병합 뒤다. 이 문서는 그 병합 뒤 구조(40 §2.4.4~§2.4.14: `donors`·`counters` 필수 블록 호출, 블록 결과 색인, `RunCounters`, E_total, `search_ceiling`·`search_stop`, BLAS 고정, `ThetaCoords`)를 전제로 쓰고 충돌하지 않게 했다(§12.4).

---

## 0. 문서 안내

* **담는 것**: 결정을 엔진 구조로 옮긴 규칙, 함수 서명, graph 필드, 실패 코드, metric 이름, 파일 분할, card와 test 초안, 검증 규칙.
* **담지 않는 것**: 경위와 검토 과정(계획 history와 이후 이 design의 history 몫), 수치 상수. 수치는 사용자 spec 값(V_res·k·온도), 엔진 해석값, LUT, PDK 선언에서만 온다(계획 N0 값 원칙, NFR-T2).
* **용어**: 계획 N0.1 그대로(σ_in, V_sys,s, z[n], t, I_u, I_T, δ, I_FS, N, m, σ_U, trim_dac, 파생 topology, trim_decl). 이 문서가 더하는 용어는 아래다.

| 용어 | 정의 |
|---|---|
| 셀(cell) | 단위 전류원 한 개와 steering 스위치 두 개(A쪽, B쪽)의 묶음. 가중치 w_c = 그 셀의 단위 셀 수 |
| 셀 전류원 | 셀의 전류원 MOS. drain = 셀 공통 넷 X_c, gate = DAC 바이어스 넷, source = 극성 레일 |
| 스위치 | 셀 공통 넷 X_c와 주입 넷(A = n_p, B = n_n) 사이의 MOS. gate = 스위치 전용 넷 |
| 코드 c | A쪽으로 보내는 단위 셀 수, 0 ≤ c ≤ 2^N − 1. δ(c) = I_u·(2c − (2^N − 1)) |
| 코드 상태 | 평가하는 네 코드: 봉인 +1(c = 2^(N−1), δ = +I_u), −1(c = 2^(N−1) − 1, δ = −I_u), +end(c = 2^N − 1, δ = +I_T), −end(c = 0, δ = −I_T)(계획 N3.5, D-17) |
| 꺼진 소자(off 소자) | 그 코드 상태에서 전류가 0인 스위치(gate가 off 레벨). 셀 전류원은 어느 코드에서도 꺼지지 않는다(전류는 늘 A나 B로 간다) |
| 극성 부호 s | 싱크(nmos) −1, 소스(pmos) +1. 주입 넷으로 들어가는 DAC 전류 = s·I_A(또는 s·I_B) |
| pass 0 | 2단계 평가에서 같은 θ의 원본 topology 성분으로 원본 회로를 평가하는 것(§10.3 I_u 출발값) |

---

## 1. 입력·원칙·선행 전제

### 1.1 확정 결정(인용)

| ID | 내용(요지) | 이 문서 반영 |
|---|---|---|
| T-1 | spec 필드 V_res, k(또는 수율 목표), trim 온도. 코드 저장 방식 범위 밖 | §5 |
| T-2 | `augment_trim(topology, trim_decl)` 결정적 변환, 엔진이 후보·순위 제시, 사용자 승인 뒤에만 사용, topology.json 무변경 | §6~§9 |
| T-3 | 차동 전류 steering 이진 가중, DNL 부족이면 상위 비트 thermometer | §7, §9.4 |
| T-4 | 엔진 구현은 NFR-4 card 2 → XRUN-F1 A·B·C 뒤 | 머리·§15 |
| T-5 | 판정 27 °C·TT(= 엔진 합격 조건), 온도 의존은 보고 전용 | §5.3, §17 |
| T-6 | 계획 v0.4 승인: D-1~D-17 기본안 전부, X-1·X-3~X-16 수용 | 아래 표 |

D-1(V_res = 최악 한계), D-2(k만), D-3(DNL 배수 = k), D-4(공존 거부), D-5(잡음은 보고만), D-6(t 변동 표시만), D-7(상보 쌍마다 DAC), D-8(단일 입력 정지), D-9(새 `bias_inputs` 항목), D-10(트랜지스터 스위치·전용 게이트 넷·`trim_decl` DC 값 벡터, on/off = 레일 전압), D-11(선언 회로·값은 사용자), D-12(trim 온도 = 합격 온도, 다르면 거부), D-13(원본 결속 + 구조 동일 검사 + 승인 fail-closed), D-14(비트 동일 범위), D-15(선택은 `trim_decl` 안), D-16(I_u 하한), D-17(+I_u 봉인).

### 1.2 원칙과 이 문서의 강제 장치

| 원칙 | 강제 장치 |
|---|---|
| topology 무관(NFR-T1, EP-1) | 주입 쌍은 S1 matching group·`metric_structure`·포트 역할로만 고른다(§9.1). 생성 이름은 고정 접두 + 정렬 번호(§7.2). 구조 규칙 E(회로 이름 리터럴)·D(숫자 리터럴)가 새 파일에도 걸린다. 9회로에서 선언 없음 = 무동작을 측정한다(TR-7) |
| 상수 발명 금지(NFR-T2, EP-4) | 모든 문턱은 spec(V_res·k), LUT(VDSAT·tol·축·온도), PDK(W_min), 엔진 분해능에서 유도(§10, §17). 반복 상한은 `k_max`(`E/sizing/k_max.py`)로 |
| graph 단일 정본(NFR-T3, DEC-83) | 새 값은 모두 graph 필드이고 writer 하나(§12.1). 파생 topology는 S0 입력이고 실행마다 다시 만든다. 디스크 사본(§13)은 출력이다 |
| 계산값 재사용(40 §2.4.9 판정 1) | 새 계산은 모두 계산 블록이다(`Projection` 하나만 읽음, `donors`·`counters` 필수). 실행 안 같은 입력 재계산 0은 XRUN-F1 블록 결과 색인이 보장한다(§12.3) |
| 결정성(NFR-T4, NFR-4) | 변환·이름·코드 벡터·셀 순서는 정렬 규칙의 함수. pass 0·반복의 출발값은 θ만의 함수(§10.3) |
| fail-closed | 결속 불일치 `trim_approval_stale` 정지, 구조 불일치 `trim_structure_divergent` 정지, 공존 거부, 이름 충돌 거부, 기준 없음 정지(§3.6), LUT 축 밖은 클램프 없이 실패(§3.1) |
| 만들면 배선(NFR-T5) | 모든 새 함수는 §14.4 배선표의 진입점 경로에서 불린다. card 완료 조건에 배선 증거를 넣는다(§15) |
| topology.json 사용자 전용 | 엔진은 원본 topology 파일을 읽기만 한다. 파생 topology는 메모리 값이고, 파일은 출력 폴더에만 쓴다 |
| 작성자 ≠ 검증자(NFR-T6) | test·기대값은 interface card만 보고 쓰고 피검 함수를 부르지 않는다. TR-7 판정 규칙의 소유자는 독립 검증자다(§17) |

---

## 2. 엔진 실측 사실(이 design의 근거, `944020f`)

계획 N3.0 F-1~F-18에 더해 이 design이 새로 잰 사실이다.

| ID | 사실 | 근거 |
|---|---|---|
| E-1 | KCL 기저는 DC 원소 전체 전류를 미지수로 푼다. KCL상 전류가 늘 0인 MOS는 `StructureUnresolvedError`(`mos_zero_current_structural`) | `E/sizing/current_basis.py:1-17, :133` |
| E-2 | θ 정의역 = 전류 원뿔: **모든 전도 MOS** 전류 > 0(유리수 정확). 0이면 `check_theta`가 `ValueError`로 거부(평가 실패가 아니라 정의역 밖). `dc_currents`도 같은 검사 | `E/sizing/theta_check.py:48-53`, `E/sizing/block_currents.py:32-34`, `E/sizing/theta_schema.py:30-31` |
| E-3 | W = ID·L/exp(ln IDu). ID = 0이면 W = 0. ln IDu = ln(ID·L/W)는 ID = 0에서 정의되지 않는다 | `E/sizing/block_widths.py:47`, 머리 :4-9 |
| E-4 | 봉인 9(전도 여유)는 ID > 0 소자만 본다. ID ≤ 0 소자는 `dc_off_current`·`dc_conduction_floor`에 없다. VGS = 0 LUT 조회는 지원된다 | `E/sizing/seal_conduction.py:8-13, :26-30` |
| E-5 | LUT v2 축: VGS 49점 0~1.8 V, VDS 49점 0~1.8 V, VS 10점 0~1.8 V(크기 축). `terminal_voltages`는 kind 부호를 곱한 크기를 쓰므로 꺼진 스위치(gate가 off 레일, source가 셀 공통 넷)의 VGS는 음수다. 축 밖은 클램프·외삽 없이 `lut_axis_out_of_range` | 실측 2026-10-15 `sky130_fd_pr__nfet_01v8__tt__W0p3600um_dc.npz` 축 배열, `E/sizing/_helpers_lut.py:23-26`, `E/lut/axis_guard.py:1-21` |
| E-6 | 접합 용량 Cdb·Csb는 PDK 모델 카드 + 확산 기하 + 역바이어스 식이고 VGS에 의존하지 않는다. 진성 용량(cgs·cgd·cgb)은 LUT `caps`(VGS 축) | `E/metrics/junction_cap.py:1-22`, `E/lut/CONTRACT.md:463` |
| E-7 | 의도 영역 선언 `intended_region`(어휘 `triode`)의 소자는 봉인 7(포화)에서 빠진다. 선언은 spec(사용자)에만 있다 | `E/authoring/spec_regions.py:6, :16-17` |
| E-8 | 넷 전압 고정은 커널 필드 `graph/kernel: fixed_values` = W3 노드 목표 + 입력 DC다. 이상 전압원은 지원 밖(기록만) | `E/sizing/kernel_fields.py:8, :21, :55`, `E/graph/s1_values.py:29` |
| E-9 | gate 전용 넷은 `bias_inputs`에 선언해야 하고(없으면 `gate_only_undeclared`), `bias_inputs`는 `connectivity_fp`에 들어가지 않는다 | `E/authoring/bias_inputs.py:1-13, :23-30` |
| E-10 | 감쇠 Newton `newton_solve(nodes, values, evaluate, tolerance, width)`가 있다(LU, 역추적, 반복 상한 `k_max`, 실패 사유 `newton_*`) | `E/sizing/scc_newton.py:1-17, :33` |
| E-11 | `offset_analysis`의 노드 수반 벡터 z는 지역 변수다(:71). 결과에는 소자별 Z_i(`z_ohm`)만 남는다(:81, :100) | `E/metrics/offset_analysis.py:71, :81, :100`, `E/metrics/aux_types.py:110-121` |
| E-12 | `offset_systematic` 단일 출력의 기준은 spec `node_voltage_targets_v`의 출력 넷 값, 없으면 `reference_undeclared` | `E/metrics/offset_systematic.py:6, :28, :42` |
| E-13 | library 9회로 spec의 `node_voltage_targets_v`는 모두 `{"pending": "CI-15"}`. 차동 출력 회로는 current_reuse_telescopic_ota 하나다(그 밖의 차동 입력 6회로는 단일 출력) | `assets/library/*.sizing_spec.json`, `*.topology.json` `ports` (2026-10-15 읽기) |
| E-14 | `load_topology(path)`는 경로만 받는다(메모리 dict 진입 없음). `TopologyDoc.from_declarations`가 `connectivity_fp`를 계산한다 | `E/authoring/topology_load.py:51`, `E/authoring/topology_model.py:99-126` |
| E-15 | LUT 슬라이스·provenance에 측정 조건 `corner`·`temp_c`가 있고 묶음 안에서 같아야 한다 | `E/lut/lut_set.py:6, :338, :397`, `E/lut/provenance.py:40-47` |
| E-16 | `assets/topology_to_markdown.py`는 경로를 받는 도구이고 옛 엔진 로더(`legacy/stick_diagram.py`)를 쓴다 | `assets/topology_to_markdown.py:27-30, :80` |
| E-17 | spec 선택 섹션은 `HUMAN_OPTIONAL`에 이름을 더해 둔다(스키마 버전 그대로) | `E/authoring/spec_schema.py:26-32` |
| E-18 | `ln_idu` θ 상자는 kind별 LUT 포락선, `current` θ 상자는 kind별 `current_box`, L은 `l_cells`(PDK bin). 선언 없이도 정해진다 | `E/search/search_domain.py:10-21` |

---

## 3. TR-0 닫을 항목 G-1~G-8

### 3.1 G-1 전류 0 MOS

**결론: as-built 엔진은 전류 0 MOS를 DC 전도 소자로 다룰 수 없다.** 근거 셋이 독립적이다.
1. θ 정의역이 모든 전도 MOS 전류 > 0을 요구한다(E-2). 꺼진 스위치를 전도 소자로 두면 그 행은 원뿔 밖이라 어떤 θ도 평가되지 않는다.
2. W = ID·L/exp(ln IDu)가 ID = 0에서 0이 되고 ln IDu가 정의되지 않는다(E-3). 꺼진 스위치의 폭은 계산 결과가 될 수 없다.
3. 꺼진 스위치의 VGS는 음수인데 LUT VGS 축은 0~1.8 V이고 축 밖은 실패다(E-5). 그래서 gm/ID·소신호 파라미터·진성 용량·잡음·mismatch σ의 LUT 조회가 모두 실패한다. `CELL_OFF`(`E/graph/cells.py:124-128`)는 AC 셀 분류일 뿐 이 셋 중 어느 것도 바꾸지 않는다.

꺼지지 않는 쪽은 문제가 없다. 셀 전류원은 늘 전류가 있고(어느 코드든 A나 B로 흐른다), 켜진 스위치도 전류가 있다. 끝 코드에서 '꺼진 쪽 출력 소자'는 셀 전류원이 아니라 꺼진 쪽 **스위치**다(이 설계의 셀 구조에서 셀 전류원은 공유되고 스위치만 꺼진다).

**표현(design 결정, 계획 N3.5 '소자 제외, 별도 포화 검사 경로'의 구체화)**:

| 층 | 꺼진 소자의 처리 | 근거 |
|---|---|---|
| S1·S1v(구조) | 파생 topology 전체(모든 스위치)를 그대로 쓴다. 코드 상태는 구조에 들어가지 않는다 | 구조는 코드와 무관해야 한다: A·B 대칭을 지켜 자기동형 궤도·matching 유도가 코드로 흔들리지 않는다(G-2) |
| KCL 기저 | 코드 상태가 주는 off 집합의 스위치 전류는 고정값 0인 기저 항이다(값 선언 이상원과 같은 `fixed` 경로). 전류 원뿔 행에서 빠진다('전도 MOS' = off 집합 밖). 셀 전류는 `trim_unit` 항(§10.3) × w_c로 고정된다 | E-1·E-2를 깨지 않고 0 전류를 표현하는 길은 전도 집합에서 빼는 것뿐이다 |
| 쓰기 계획 | off 소자는 어느 노드도 쓰지 않는다. 셀 공통 넷 X_c는 켜진 스위치가 쓴다 | 노드 writer 유일(봉인 5) |
| W·동작점(`dc_widths`) | off 소자는 LUT를 조회하지 않는다. W = 짝 스위치(같은 셀의 다른 쪽, 이 코드에서 켜짐)의 W, L = 짝의 L, ID = 0, `DeviceOp`에 off 표지. 짝 동일은 §7 생성 규칙이 보장하는 물리 사실이다(같은 셀 두 스위치는 같은 W·L로 그린다) | E-3 |
| 봉인 | 소자 전류·LUT 순방향 조회·관계를 보는 항목은 off 소자를 행으로 만들지 않는다: 봉인 1(노드 충돌 -- off 소자가 함의하는 관계 값 제외), 2(VGS 정합 -- 순방향 LUT), 3(KCL 잔차 -- off 전류는 정의상 0이라 항에서 뺀다), 7(포화), 8(`kvl_branch`), 9(전도 -- 이미 ID ≤ 0을 뺀다, E-4). 봉인 6(벌크 역바이어스)은 노드 전압만 보므로 off 소자도 그대로 검사한다. 봉인 4·5는 블록·writer 검사라 그대로다 | 정의되지 않는 조건을 판정하지 않는다(계획 N3.5). 봉인 번호는 `E/sizing/seal.py:7-8`과 각 `seal_*.py` 머리 |
| 소신호(`ss_dev`) | gm = gmb = gds = 0(전류 0의 채널), 접합 용량 cdb·csb = PDK 식(E-6, VGS 무관). **진성 용량 cgs·cgd·cgb는 LUT VGS 축 밖이라 정의되지 않는다** -- 처리는 사용자 결정 TD-2(§18.1) | E-5·E-6 |
| 잡음원 | off 소자는 채널 잡음원을 만들지 않는다(전류 0). LUT 잡음 조회를 하지 않는다 | 물리적으로 0이고 조회가 축 밖이다 |
| offset 수반 | off 소자의 σ_VGS는 조회하지 않고 기여 항을 0으로 둔다(항 = Z·gm·σ, gm = 0이라 σ 값과 무관하게 정확히 0). `sigma_missing` 검사는 off 표지 소자를 빼고 한다 | E-11 식 |
| 포화 검사(코드 상태 −1, ±end) | §10.5 균형 풀이 해에서 off 소자를 빼고 포화 여유를 잰다 | 계획 N3.5 |
| 켜진 스위치 영역 | 켜진 스위치는 gate가 on 레일이라 대개 triode다. 그래서 trim 선언이 스위치를 `intended_region` triode로 더한다(§6.3 합성, 사용자 spec이 아니라 `trim_decl` 출처). 셀 전류원은 포화를 요구한다 | E-7. on 레벨 = 레일(D-10) |

**바뀌는 엔진 지점**(TR-5a): `sizing/current_basis.py`(off 고정 0·`trim_unit` 항), `sizing/theta_check.py`·`block_currents.py`(원뿔 = off 밖), 쓰기 계획, `block_widths.py`(off 경로), 봉인 3·7·8, `metrics` 소신호·잡음원·`device_sigmas`. off 집합은 블록 extras(코드 상태 = `trim_decl`의 값)로 들어가므로 입력 버전에 포함된다.

**측정 확인**(TR-M, §15): 파생 topology의 봉인 상태에서 off 집합을 뺀 KCL 기저가 `mos_zero_current_structural` 없이 풀리는지, 원본 θ 성분이 보존되는지(§10.2 스키마 확장 성질)를 9회로 후보 7회로에서 잰다.

### 3.2 G-2 파생 대 원본 구조 동일 검사의 범위

**검사 함수**: `compare_trim_structure(original, derived, trim_devices) -> TrimStructureDiff`(graph, §14). 원본 실행과 파생 실행의 S1·S1v 필드를 **원본 원소로 제한한 투영**끼리 비교한다. 차이가 하나라도 있으면 `trim_structure_divergent`(`StructureUnresolvedError`, 정지)이고 차이 목록을 결과 JSON에 싣는다.

| 구분 | 필드(S1·S1v) | 비교 방법 |
|---|---|---|
| **비교**(같아야 함) | `device: dc_role`(원본 소자) | 소자마다 정확히 같음 |
| | `equal_vgs`·kcl 묶음(gs 묶음) | 원본 원소만 남긴 묶음 집합이 같음. trim 소자와 원본 소자가 한 묶음에 섞이면 차이 |
| | G_vgs 사이클 분류 | 원본 원소만으로 된 사이클의 분류가 같음 |
| | matching group | 멤버가 모두 원본인 그룹의 (kind, 멤버, status)가 같음. 원본과 trim 소자가 섞인 그룹이 새로 생기면 차이 |
| | L 동치류와 주인 | 원본 멤버만 남긴 동치류와 주인이 같음 |
| | 자기동형 궤도·d/s 부호 | 궤도 분할을 원본 원소로 제한한 것이 같음 |
| | S1v 뷰별: 구동 종류(원본 넷), 셀 종류(원본 소자), 블록(stage, key, 출력 넷, 원본 멤버와 AC 역할), 복합 블록, 루프(원본 원소만), 극점 노드, 끊는 점 | 원본 투영이 같음 |
| | `metric_structure`의 `input_cells`, `noise_input_cells` | 같음 |
| | 결과 `findings`·`review_needed`·`applied_facts` | 파생 쪽에 원본 원소만 관련된 새 항목이 없음 |
| **비교 안 함**(보고만) | 가지·기둥(`columns`) | 새 레일 경로(셀 경로)가 생기는 것이 의도된 변화다. 원본 기둥 집합이 파생 기둥 집합의 '원본 원소 투영'에 모두 있는지만 보고한다 |
| | 구조 색(`dc_colour`), 정준 순서 | 원소 수가 바뀌면 순위가 바뀐다. 이름 무관 값이라 비교 의미가 없다 |
| | trim 소자 자신의 모든 필드 | §11 역할 규칙의 test 몫 |

**위험 지점**(계획 G-2): 주입 넷 차수가 늘어 `_sibling_rule`·`_counterparts`·column 규칙이 원본 소자의 matching·대응 넷을 바꿀 수 있다. 위 표의 matching·궤도·뷰 행이 그것을 잡는다.

**측정 단계**: card **TR-M**(§15)이 TR-2 착수 전에 9회로 후보 7회로 × 쌍 × 극성에서 독립 구현 파생 topology로 위 표를 잰다. 결과가 '비교 행 차이 0'이면 TR-4는 §11 규칙만 넣는다. 차이가 있으면 차이마다 원인(trim 소자가 신호 도달·셀 분류에 들어감, 묶음 섞임 등)을 기록하고 §11 규칙으로 막히는지 TR-4 design 보완에서 정한다. 막을 수 없는 차이는 사용자 보고(회로 해석 사항이라 혼자 정하지 않는다).

### 3.3 G-3 완료 조건 (1)(D-14)의 비교 제외 필드

비교는 '선언 없는 실행, structure.json 2개 재승인 뒤, base(TR-1 직전 master) 대 TR-6 병합본'이고 같은 실행 환경이다. 코드가 바뀌므로 40 §2.4.13 (2)의 '같은 코드' 1차 검사는 쓸 수 없다. 그래서 비교 대상을 **값 부류**로 정하고 **지문 부류**를 뺀다.

| 부류 | 필드 | 처리 |
|---|---|---|
| 지문 F1: 규칙 지문 | structure.json `rule_hash`, `structure_rule_fp()`·`s1v_rule_fp()` 값, `S1Key.rule_fp`(`E/graph/s1_values.py:233-238`, `E/graph/s1_key.py:23`) | 뺀다 |
| 지문 F2: 블록 코드 해시에서 온 입력 버전 | `FieldValue.input_version`, 스냅샷 `block_versions`, 스냅샷 `fp`, S3 evals `snapshot_fp`, `context_fp`(S1 블록·커널 계획 블록 입력 버전 지문, `E/search/search_context.py:211`) | 뺀다(`ComputeBlock.code_hash`가 바뀐 블록 파일마다 바뀐다) |
| 지문 F3: 코드·실행 지문 | `code_fp`·`engine_code_fp`, `run_id`(`E/search/find_front.py:138`), S1 지문 묶음 `S1Key` 자체 | 뺀다 |
| 지문 F4: 위 지문을 담은 키 | S3 줄의 `s0`(= `context_fp`), 평가 키 `EvalKey`의 지문 칸 | 뺀다 |
| 새 필드 N | 이 기능이 더하는 필드(§12.1 표 전부)와 결과 JSON 새 칸(§13) | base에 없으므로 비교 집합 밖. 대신 **선언 없는 실행에서 값이 비어 있음(None 또는 빈 tuple)을 단언**한다 |
| 시간 T | 40 §2.4.13 (2) T 부류 | 뺀다(기존 규칙) |
| 값 V | 그 밖의 모든 칸(노드 전압·소자 동작점·metric 값·제약 행·front·ε 기록·`perf` 계수·S3 줄 값 칸·단계 A·B 보고서의 값 칸) | **비트 동일** |

지문 부류를 뺀 뒤 값 부류가 비트 동일이면 완료 조건 (1) 통과다. 값 부류에서 한 칸이라도 다르면 FAIL이고 필드별 비교로 넘어가지 않는다. F2·F3를 빼는 것은 계획 D-14 문언('규칙 지문을 담는 모든 필드')보다 넓다 → §18.2 X-T5.

### 3.4 G-4 1단계 N 추천의 입력점과 순서

* **입력점: front 점마다 따로 계산한 뒤 front 위 최악으로 모은다.**
  - 점 p마다 (t_p, σ_in,p, V_sys,s,p)로 그 점에서 가능한 (N_p, m_p)를 정한다(§9.4).
  - 추천 N = max_p N_p, 추천 m = min_p m_max,p(N)(그 N에서 모든 점이 가능한 가장 큰 m).
  - 근거: 승인된 N·m은 2단계에서 front 전체에 고정값이다(N3.1-3). front 한 점에서만 가능한 구성은 다른 점에서 `trim_config_infeasible`가 된다. 점별 값은 표로 함께 낸다(D-6: 거르지 않고 표시).
  - 추천 불가 점(§9.4 종료 조건)은 목록으로 내고 집계에서 뺀다. 남는 점이 없으면 `trim_config_unrecommendable`.
* **순서: N 먼저, 그다음 m.** (N, m) 쌍 전수가 아니다.
  - 계획 N3.4 규칙 그대로다(N = 어떤 m에서라도 성립하는 최소 정수, m = 그 N에서 성립하는 가장 큰 m).
  - 성립 여부는 m에 대해 단조다(σ_DNL(m)이 m에 대해 증가). N에 대해서도 단조다(I_lb(N)가 감소). 그래서 순서대로 찾은 답이 쌍 전수의 답과 같다. test가 쌍 전수 결과와 대조한다(§15 TR-2).

### 3.5 G-5 σ_U의 기준점

* **1단계(추천)**: 셀 θ 상자(셀 전류원 kind의 `ln_idu` LUT 포락선 × PDK L 칸, E-18)의 **LUT 격자 마디** 가운데, I_u = I_lb(N)에서 W_u = I_u·L/IDu ≥ W_min(PDK `min_finger_w_m`)인 마디들의 σ_U **최솟값**을 쓴다. 그 마디들의 최댓값도 함께 보고한다.
  - 근거: 추천은 '2단계 탐색이 상자 안 어떤 θ로든 닿을 수 있는 최소 N'이어야 한다(존재 판정). 상자 안 최악점을 쓰면 실제로 필요한 것보다 큰 N을 권한다.
  - σ_U = (gm/ID)·σ_VGS(W_u, L)는 F-3 경로(LUT 감도 × PDK slope RSS, √(W_ref/W), finger 분할)로 계산한다. Pelgrom 상수는 쓰지 않는다.
  - 출발점·보고용 계산이다(EP-7). 판정이 아니다.
* **2단계(판정)**: 봉인 점에서 가중치 1인 셀(m ≥ 1이면 이진 LSB 셀, m = 0이면 thermometer 셀 하나 = 가중치 2^0)의 전류원의 (gm/ID, σ_VGS(W, L))로 σ_U를 계산한다.
  - thermometer 셀은 단위 셀 2^m개의 독립 복제로 본다. 엔진의 소자별 σ(폭 비례 √ 축척)가 같은 뜻이다. 두 값의 비 σ_cell,rel·√(2^m)/σ_U를 보고해 일치를 확인한다(finger 분할이 다르면 차가 드러난다).
  - 셀 전류원끼리 ln IDu·L이 같으므로(§10.2 묶음) 가중치별 σ_rel은 √w 축척만 다르다.

### 3.6 G-6 단일 종단 '출력 균형'의 기준

* **차동 출력**(감지 쌍): 균형 = V(out_p) − V(out_n) = 0. 기준 선언이 필요 없다.
* **단일 출력**: 균형 = V(out) = `offset_systematic`이 쓰는 선언 출력 기준 DC(spec `node_voltage_targets_v`의 그 출력 넷 값, E-12). **선언이 없으면 `trim_reference_undeclared`로 보고하고 그 회로의 균형 풀이·N 추천·2단계를 하지 않는다**(fail-closed). V_sys,s도 같은 기준을 쓰므로 1단계 추천 입력(|V_sys,s|)도 없다.
  - 1단계 후보표의 t·headroom·잡음은 기준과 무관하므로 그대로 낸다.
* **영향**(E-13): 지금 library의 차동 입력 7회로 가운데 단일 출력 6회로는 `node_voltage_targets_v`가 결정 대기(CI-15)라 추천·2단계까지 가지 못한다. 기준 값은 사용자 몫이다(§18.1 TD-3).

### 3.7 G-7 코드 상태 DC 값 벡터와 승인 해시

* **결론: 벡터는 승인된 (쌍, 극성, N, m)에서 규칙으로 유도하고, 승인 기록에는 벡터가 아니라 규칙 지문 `trim_rule_fp`만 넣는다.**
* 근거:
  - 벡터는 선택과 변환 규칙의 결정적 함수다. 기록에 함께 두면 같은 사실이 두 곳에 있다(단일 정본 위반). 둘이 어긋날 때 어느 쪽이 정본인지 규칙이 또 필요하다.
  - 규칙 파일이 바뀌면 `trim_rule_fp`가 바뀌어 승인이 stale(정지)이 된다. 벡터 규칙 변경이 승인 없이 지나가지 않는다.
* `trim_decl`(메모리 값)은 합성 때 유도한 벡터를 담는다(D-10 '코드는 trim_decl 안 DC 값 벡터'). `trim_decl` 지문은 출처 기록에 들어간다.

### 3.8 G-8 바이어스 원천별 t(T)·δ(T) 온도 의존 보고

D-9로 셀 바이어스 원천은 새 `bias_inputs` 넷 하나(외부 gate 전압)다. TR-7 온도 sweep(N5.1 3번, 보고 전용)은 다음을 낸다.

| 항목 | 내용 |
|---|---|
| 바이어스 모델 | 오라클에서 DAC 바이어스 넷 = 27 °C 봉인 전압의 이상 전압원(온도 무관). 이것이 D-9 원천의 정의다 |
| 표본·온도별 값 | t(T)(오라클 소신호로 잰 주입 쌍 전달), I_u(T)(LSB 셀 전류), δ_code(T) = 고정 코드의 δ, 잔여 V_res,meas(T) |
| 분해 | 잔여 변화 = (i) 원본 offset drift(DAC를 27 °C δ로 고정한 이상 전류원으로 바꾼 재측정) + (ii) DAC 전류 drift 몫(δ(T) − δ(27 °C))·t(T) + (iii) 전달 drift 몫 δ(27 °C)·(t(T) − t(27 °C)). 세 몫과 합을 표로 낸다 |
| 참고 괄호 | 같은 sweep을 바이어스 넷 대신 셀 전류를 이상 전류원 I_u(27 °C)로 고정해 한 번 더 잰다(DAC 전류 온도 계수 0인 경우). 설계 대상이 아니라 D-9 원천의 온도 몫을 드러내는 기준이다 |
| 한계 문구 | '바이어스 원천의 온도 특성은 27 °C 판정에 드러나지 않는다. 위 (ii)가 그 몫이다'(계획 N5.1 한계, N9) |

---

## 4. 흐름과 진입점

```
[1단계]  spec(offset_trim 선언) + 원본 topology
  run_stage_a(..., trim_approval_path=None) → S0(원본) + graph/trim: pairs         (§9.1)
  run_stage_b → build_search_context → find_front                                (offset 제약 의미 전환 §10.8)
  run_trim_candidates(front)  → front 점마다 trim_candidates 블록(t·headroom·잡음·(N_p,m_p)) (§9.2~9.4)
                              → 추천 (N, m)·극성, 쌍·극성마다 augment_trim → 파생 topology 파일 + connectivity 표 (§9.5)
[승인]   사용자: 파생 topology·표를 보고 <circuit>.trim.json 작성(쌍·극성·N·m, approval_id)      (§8)
[2단계]  run_stage_a(..., trim_approval_path=<circuit>.trim.json)
  bind_trim: spec trim 섹션 + 승인 → trim_decl → augment_trim → 결속 검사(지문·규칙)      (§8.3)
  S0(원본)과 S0(파생, 봉인 코드 상태) → compare_trim_structure                            (§3.2)
  run_stage_b → build_search_context(파생) → find_front: 평가마다 trim_evaluate              (§10)
     pass 0(원본) → I_u 유도 반복(파생) → 코드 상태 균형 풀이 → trim 제약·metric
  불가능 → trim_config_infeasible 보고, 1단계로(엔진이 N·m을 바꾸지 않음)                   (N3.1-4)
```

* 단계 선택은 진입 인자로만 한다: spec에 `offset_trim` 섹션이 있고 `trim_approval_path`가 없으면 1단계, 있으면 2단계다. 섹션이 없는데 승인 경로가 오면 `trim_approval_without_decl`(`SchemaRejectedError`).
* 선언이 없으면 새 경로는 하나도 돌지 않는다(새 필드는 빈 값, §3.3 N 부류).

---

## 5. spec 필드 `offset_trim` (TR-1)

### 5.1 스키마

`human.offset_trim`(선택 섹션, `HUMAN_OPTIONAL`에 더함, E-17. 스키마 버전 그대로):

```json
"offset_trim": {
  "residual_offset_v":   {"value": <V>,  "source": {<user_spec 출처>}},
  "coverage_multiple":   {"value": <k>,  "source": {<user_spec 출처>}},
  "trim_temperature_c":  {"value": <°C>, "source": {<user_spec 출처>}}
}
```

| 키 | 뜻 | 형식 검사(위반 사유) |
|---|---|---|
| `residual_offset_v` | V_res. trim 뒤 잔여 offset의 **최악 한계**(D-1), 입력 환산, V | 유한 양수(`offset_trim_value`) |
| `coverage_multiple` | k. 보정 구간이 덮을 trim 전 분포 폭의 σ_in 배수(D-2: 수율 목표 Y는 받지 않음) | 유한 양수(`offset_trim_value`) |
| `trim_temperature_c` | trim과 판정 온도(T-1) | 유한 수(`offset_trim_value`). 값 대조는 §5.3 |

* 출처 `source`는 `spec_sources` 규칙 그대로(`user_spec`만 허용 -- 섹션별 허용 kind에 `offset_trim` = (`user_spec`,)을 더한다). 결정 대기 `{"pending": <ID>}`는 섹션 전체 자리에만 받는다(값 하나만 대기는 `type`).
* 키 이름은 DEC-68(단위 접미 `_v`·`_c`, 무차원 배수는 접미 없음)이다. `_c`는 기존 어휘에 없는 온도 단위 접미라 N3.16 정본 표에 행을 더한다(TR-1).
* 받는 키 밖은 `_spec_fields.key_hits`(옛 이름·회로 전용 키 구분 그대로).

### 5.2 로더 규칙(D-4 공존)

| 상황 | 처리 |
|---|---|
| `offset_trim`과 판정 제약 `offset_in_sigma_mv <=`가 함께 있음 | 로더 거부 `offset_trim_conflicts_sigma_constraint`(`SchemaRejectedError`, detail = 그 제약 위치). spec 수정은 사용자 몫 |
| `offset_trim`과 `offset_excess <=` | 제약을 **보고로 내린다**: 로더가 그 행을 `SizingSpecDoc`의 판정 제약에서 빼고 `trim_demoted_constraints`(새 칸, (metric, op, value, 위치) tuple)에 담는다. metric은 보고 요청으로 계속 계산한다 |
| `offset_trim`과 `offset_sys_mv <=` | 같은 방식으로 보고로 내린다 |
| `offset_trim` 섹션이 결정 대기 | trim 선언 없음과 같다(1단계도 돌지 않는다). 대기 표지는 기존 수집 경로로 보고 |

검사 함수는 `trim_constraint_conflicts(trim, constraints)`(별도 파일, 규칙 A)이고 `load_sizing_spec`이 섹션 검사 뒤 부른다.

### 5.3 온도 대조(D-12, T-5)

* 대조 기준 = 그 실행 LUT 묶음의 측정 조건 `temp_c`(E-15)다. 숫자 27을 코드에 두지 않는다.
* 로더는 LUT를 모르므로 대조는 `run_stage_a`가 LUT를 받은 직후 한다: `trim_temperature_c` ≠ LUT `temp_c`이면 `trim_temperature_mismatch`(`SchemaRejectedError`, detail = 두 값). 비교는 float 정확 일치다(둘 다 선언값). spec에는 코너 필드가 없으므로 코너는 대조하지 않고 LUT `corner`를 그대로 보고한다(판정 코너 = LUT 코너가 엔진 합격 조건이다).
* 결과 보고에 '판정과 코드 결정은 이 한 조건이다' 문구(FR-T9)와 그 조건 값(LUT provenance)을 싣는다.

### 5.4 spec 지문 결속(N3.3-1, D-13)

`meta.topology_fp`는 원본 topology `connectivity_fp`와 대조한다(as-built `spec_meta.py` 그대로). 2단계에서도 spec은 원본 topology 경로와 함께 로드한다. 파생 지문은 승인 기록하고만 대조한다(§8.3).

---

## 6. `trim_decl` 스키마와 합성 (TR-1)

### 6.1 값 형식(`authoring/trim_values.py`, frozen dataclass)

```python
TrimSpec(residual_offset_v, coverage_multiple, trim_temperature_c, source_fp)      # 섹션 값 + 출처 지문
TrimSelection(pair: tuple[str, str],    # (n_p 넷, n_n 넷) -- 주입 쌍 drain 넷, p/n은 게이트 포트 역할로 정함
              polarity: str,            # "sink" | "source"
              n_bits: int, m_bits: int) # 1 ≤ N, 0 ≤ m ≤ N − 1
TrimCell(index: int, weight: int, source_device: str, switch_a: str, switch_b: str,
         common_net: str, gate_a_net: str, gate_b_net: str)
CodeState(name: str,                    # "seal_plus" | "minus" | "end_plus" | "end_minus"
          code: int,                    # c
          delta_units: int,             # 2c − (2^N − 1)
          gate_levels: tuple[(넷, V), ...],   # 스위치 게이트 넷 DC 값 벡터(넷 이름순)
          off_devices: tuple[str, ...])       # 꺼진 스위치(이름순)
TrimDac(index: int,                     # DAC 번호(쌍 정렬 순서, §7.2)
        selection: TrimSelection, rail_net: str, on_rail_net: str, off_rail_net: str,
        bias_net: str, cells: tuple[TrimCell, ...], states: tuple[CodeState, ...],
        triode_devices: tuple[str, ...])   # 스위치 전부(§3.1 켜진 스위치 영역)
TrimDecl(spec: TrimSpec, dacs: tuple[TrimDac, ...], approval_id: str | None,
         rule_fp: str, decl_fp: str)       # decl_fp = 위 모든 칸의 core fp_of
```

* 상보 입력쌍(D-7)은 `dacs`가 둘이다. 승인 기록도 선택 둘을 담는다.
* `TrimDecl`은 graph 필드가 아니라 S0 입력 값(spec과 같은 지위)이다. 블록에는 extras로 넘어가 입력 버전에 들어간다.

### 6.2 선택의 출처

| 단계 | 선택 출처 | `approval_id` |
|---|---|---|
| 1단계 | 후보표의 (쌍, 극성)과 추천 (N, m)(§9.5) | None |
| 2단계 | 승인 기록 `<circuit>.trim.json`(§8) | 승인 기록 값 |

### 6.3 합성 `compose_trim_decl(spec_trim, selections, topology, supplies, approval_id)`

1. 레일: `supplies`(spec `supplies_v`)에서 최저 전압 레일 넷 R_min, 최고 R_max(이름이 아니라 전압으로. 같은 전압 레일이 둘이면 `trim_rail_ambiguous` 거부).
2. 극성 레일: sink → `rail_net` = R_min(셀 전류원 source), 스위치 on 레벨 = V(R_max), off = V(R_min). source → `rail_net` = R_max, on = V(R_min), off = V(R_max).
3. 셀 목록(§7.3), 생성 이름(§7.2), 코드 상태 넷(§7.4)을 규칙으로 만든다.
4. 선택 검사: `pair`가 topology 넷이고 서로 다르며, N ≥ 1, 0 ≤ m ≤ N − 1, 극성 어휘 안. 위반은 `trim_selection_invalid`.
5. `rule_fp` = `trim_rule_fp()`(§8.2), `decl_fp` = `fp_of(모든 칸)`.

---

## 7. `augment_trim(topology, trim_decl)` 변환 규칙 (TR-3)

### 7.1 서명과 성질

```python
def augment_trim(topology: TopologyDoc, trim_decl: TrimDecl) -> tuple[TopologyDoc, TrimProvenance]
```

* 순수 함수다. 파일을 읽지도 쓰지도 않는다. 같은 입력이면 비트 동일한 출력(NFR-T4).
* 출력 topology는 원본 스키마(F-7)를 지킨다. 새 키를 넣지 않는다. 원본 원소·넷·포트·레일·`ideal_sources`는 그대로 두고 `devices`에 trim 소자를, `bias_inputs`에 DAC 바이어스 넷과 스위치 게이트 넷을 더한다(E-9: gate 전용 넷 선언 필수, `connectivity_fp` 밖).
* 출력은 메모리 dict를 만들어 새 진입 `topology_from_data(data, where)`(§14)로 **같은 로드 게이트를 모두 통과**시켜 `TopologyDoc`으로 만든다. 게이트 거부는 그대로 올린다(파생 topology도 원본과 같은 검사를 받는다).
* `TrimProvenance` = (원본 `connectivity_fp`, 파생 `connectivity_fp`, `decl_fp`, `rule_fp`, 선택, 1단계 실행 id(있으면), 생성 소자 이름 tuple, 생성 넷 이름 tuple, 셀 표(`TrimCell` tuple)).

### 7.2 이름 규칙

* DAC 번호 d: 선택의 정렬 순서(쌍 (n_p, n_n) 문자열 정렬)로 0부터.
* 셀 번호 j: 이진 셀 j = 0..m−1(가중치 2^j), 그 뒤 thermometer 셀 j = m .. m + 2^(N−m) − 2(가중치 2^m).
* 소자: `trim<d>_c<j>_src`(셀 전류원), `trim<d>_c<j>_swa`(A쪽 스위치), `trim<d>_c<j>_swb`(B쪽 스위치).
* 넷: `trim<d>_c<j>_x`(셀 공통 넷), `trim<d>_c<j>_ga`·`trim<d>_c<j>_gb`(스위치 게이트), `trim<d>_bias`(DAC 바이어스 넷).
* 충돌: 생성 이름이 원본 원소·넷 이름과 대소문자 무시로 같으면 `trim_name_collision`(`SchemaRejectedError`, 충돌 이름 목록). 이름을 바꿔 피하지 않는다(결정성).
* 접두 `trim`은 고정 문자열이고 회로 이름이 아니다(규칙 E 대상 아님). 숫자는 정렬 번호만 쓴다.

### 7.3 소자 생성(극성 규칙)

셀 j마다 kind = 극성 kind(sink → nmos, source → pmos):

| 소자 | drain | gate | source | bulk |
|---|---|---|---|---|
| `_src` | `_x` | `trim<d>_bias` | `rail_net` | 키 생략(엔진 bulk 기본 규칙 `graph/bulk_default.py`) |
| `_swa` | n_p | `_ga` | `_x` | 생략 |
| `_swb` | n_n | `_gb` | `_x` | 생략 |

* d/s 표기는 물리 전류 방향 선언이다(DEC-97 (4)): sink는 주입 넷 → 스위치 → X → 전류원 → R_min, source는 R_max → 전류원 → X → 스위치 → 주입 넷. pmos는 위 표에서 drain·source 의미가 kind 부호로 뒤집히는 as-built 규약 그대로다(`terminal_voltages`).
* 가중치는 소자 키가 아니다(F-7: `m` 키 없음). 가중치 w_c는 출처 기록의 셀 표에만 있고, 셀 전류 = w_c·I_u로 엔진이 W를 정한다(같은 ln IDu → W ∝ w_c). 오라클 netlist도 같은 W를 받는다.

### 7.4 코드 상태 벡터

코드 c에서 셀 j의 방향: 이진 셀 j < m은 c의 j번째 비트가 1이면 A, 0이면 B. thermometer 셀 j ≥ m은 h = j − m + 1(1부터)이 h ≤ (c >> m)이면 A, 아니면 B. A로 가는 셀의 `_swa` gate = on 레벨, `_swb` gate = off 레벨이고 B는 반대다. off 집합 = off 레벨 게이트를 받은 스위치.

검산: A쪽 단위 수 = (c mod 2^m) + (c >> m)·2^m = c. 네 상태는 §0 표의 c다.

---

## 8. 승인 기록과 결속 (TR-1 로드, TR-3 검사)

### 8.1 형식 `<circuit>.trim.json`(topology와 같은 폴더, 사용자가 쓴다)

```json
{
  "schema_version": "1",
  "approval_id": "<문자열, 사용자 결정 기록 id>",
  "decided": "YYYY-MM-DD",
  "record": "<사용자 결정 원문 위치>",
  "original_connectivity_fp": "<원본 topology connectivity_fp>",
  "derived_connectivity_fp": "<승인한 파생 topology connectivity_fp>",
  "trim_rule_fp": "<승인 당시 trim_rule_fp()>",
  "spec_trim_fp": "<승인 당시 spec offset_trim 섹션 지문>",
  "stage1_run_id": "<후보를 낸 1단계 실행 id>",
  "selections": [{"pair": ["<n_p 넷>", "<n_n 넷>"], "polarity": "sink|source", "n_bits": N, "m_bits": m}]
}
```

* 닫힌 키 어휘. 밖의 키는 `trim_approval_unknown_key`, 형식 위반은 `trim_approval_type`(`SchemaRejectedError`, gate `trim_approval`).
* 코드 벡터는 넣지 않는다(G-7).
* 1단계 출력이 이 파일의 초안(값이 채워진 JSON, `approval_id`·`decided`·`record` 빈칸)을 출력 폴더에 쓴다(§13). 사용자가 검토 뒤 채워 topology 폴더에 둔다.

### 8.2 규칙 지문 `trim_rule_fp()`

`authoring/trim_rule_fp.py`. 대상 파일 = `trim_augment.py`, `trim_decl.py`(합성·셀·코드 규칙), `trim_values.py`의 (basename, LF 정규화 바이트 sha256)을 이름순으로 묶은 `fp_of`(`E/graph/s1v_key.py`와 같은 방식). 대상 목록 상수는 그 파일 안에 둔다.

### 8.3 결속 검사(2단계 진입, `bind_trim`)

순서대로 하고 하나라도 어기면 정지(fail-closed, X-13):

| # | 검사 | 실패 |
|---|---|---|
| 1 | spec `meta.topology_fp` = 원본 `connectivity_fp` | 기존 `topology_fp_mismatch` |
| 2 | 승인 `original_connectivity_fp` = 원본 `connectivity_fp` | `trim_approval_stale`(detail `original_fp`) |
| 3 | 승인 `trim_rule_fp` = 현재 `trim_rule_fp()` | `trim_approval_stale`(detail `rule_fp`) |
| 4 | 승인 `spec_trim_fp` = 현재 spec `offset_trim` 지문 | `trim_approval_stale`(detail `spec_trim`) -- V_res·k가 바뀌면 추천이 달라지므로 재승인 |
| 5 | `augment_trim`으로 다시 만든 파생 `connectivity_fp` = 승인 `derived_connectivity_fp` | `trim_approval_stale`(detail `derived_fp`) |
| 6 | 파생 S1·S1v 구조 동일 검사(§3.2) | `trim_structure_divergent` |

`trim_approval_stale`은 core `SchemaRejectedError`(exit 7, gate `trim_approval`)다. structure.json의 stale(review_needed로 되돌리고 계속)과 다른 점은 계획 X-13 그대로다.

**structure.json**: 사실은 원본 지문에 묶인 채 원본 소자에만 적용한다(D-13). 파생 실행의 `load_structure_facts`에는 원본 `connectivity_fp`를 넘기고(파생 지문이 아니라), 적용 대상 이름이 trim 소자면 거부한다(trim 소자는 사실 대상이 아니다).

---

## 9. 1단계: 후보·추천·출력 (TR-2, TR-3)

### 9.1 주입 쌍 `trim_pairs`(S0 블록)

계획 N3.2 규칙을 그대로 구현한다.
* 쌍 = S1 matching group 가운데 종류 `diff_pair`·status derived(멤버 정확히 2)이고 두 멤버가 모두 `metric_structure.input_cells`에 드는 것. n_p = 게이트 포트 역할 `differential_input_p`인 멤버의 drain 넷, n_n = `differential_input_n` 쪽.
  - 게이트가 포트가 아니면(입력 버퍼 뒤 차동쌍) 포트 역할을 신호 도달로 거슬러 정하지 않고 `trim_pair_polarity_unresolved`로 보고한다(조용한 대체 금지).
* 쌍이 없을 때: 차동 입력 포트가 없으면 `trim_single_input_unsupported`, 있으면 `trim_pair_undefined`(detail: review_needed diff_pair, 입력 셀 밖 diff_pair 목록).
* 출력 필드 `graph/trim: pairs` = `TrimPair(n_p, n_n, devices, kind, matching_group_id)` tuple(쌍 정렬 순서). 선언이 없으면 ().

### 9.2 front 점별 후보 `trim_candidates`(S2 블록, front 점 스냅샷마다)

입력: 그 점의 `graph/metrics: offset_adjoint`(§12.2), `metrics_aux`의 `OffsetAnalysis`(σ_in, A_dm)·`OffsetSystematic`(`output_error_v`), 노드 DC 전압, `graph/trim: pairs`, spec trim 값, LUT.

쌍 P·극성 s마다:

| 칸 | 계산 |
|---|---|
| `t_v_per_amp` | t = (z[n_p] − z[n_n])/(2·A_dm). 부호 그대로 |
| `effective_sign` | s·sign(t)(코드 증가가 입력 환산 offset을 어느 쪽으로 옮기는가) |
| `headroom_window_v` | sink: V(n) − V(R_min), source: V(R_max) − V(n)를 두 넷 중 작은 쪽으로 |
| `headroom_floor_v` | 셀 전류원 kind의 θ 상자에서 LUT VDSAT + tol_vdsat의 최솟값(VDS = 창 값, VSB = 0). 스위치 VDS 하한은 0(triode 허용) |
| `headroom_ok` | 창 > 바닥 |
| `noise_in_v_per_rthz` | 입력 환산 DAC 잡음 = √(z[n_p]²·S_I,A + z[n_n]²·S_I,B)/\|A_dm\|. S_I = 셀 전류원 kind의 LUT 잡음(열잡음 평탄값, 1/f 코너 `noise_planes`)을 G-5 1단계 기준점에서 I_T/2 전류로 조회. γ 같은 상수 모델 없음(DEC-96 (3)). 보고만(D-5) |
| `injection_cap_f` | 그 넷의 기존 MNA 용량 합(보고, 계획 N9 'DAC 용량' 위험의 참고값) |
| `recommendation` | §9.4의 (N_p, m_p, I_lb, σ_U 최소·최대) 또는 사유 |

* 기준 없음(§3.6)이면 `recommendation` = `trim_reference_undeclared`이고 나머지 칸은 낸다.
* \|t\| = 0이거나 `headroom_ok`가 거짓인 (쌍, 극성)은 순위에서 빠진다. 모든 (쌍, 극성)이 빠지면 `trim_injection_infeasible`(N4-3).

### 9.3 순위(D-5, D-6)

front 점마다 `headroom_ok`인 (쌍, 극성)을 \|t\| 내림차순(같으면 쌍 정렬 → 극성 sink, source 순)으로 둔다. front 전체 순위는 (쌍, 극성)별 min_p \|t_p\| 내림차순이다(최악 점 기준, G-4와 같은 원칙). t의 부호가 front 위에서 바뀌거나 \|t\|의 최대/최소 비가 1보다 큰 쌍은 `t_varies` 표지를 붙이고 거르지 않는다(D-6). 비의 문턱은 두지 않는다(값을 보고).

### 9.4 (N, m) 추천 `recommend_trim_config` (순수 함수)

입력: \|t\|, σ_in, \|V_sys,s\|, k, V_res, σ_U 조회 함수(G-5 1단계), W_min.

```
I_lb(N) = (k·σ_in + |V_sys,s|) / (|t|·(2^N − 1))
σ_DNL(m; N, σ_U) = σ_U·√(2^(m+1) − 1 − 1/(2^N − 1))          (Bertotti 2012 식(3))
가능(N, m) ⇔ 셀 θ 상자 격자 마디 가운데 W_u(마디, I_lb(N)) ≥ W_min 인 마디가 있고,
             그 마디들의 최소 σ_U로 |t|·I_lb(N)·(1 + k·σ_DNL(m; N, σ_U)) ≤ V_res
N = 1, 2, … 순서로: 가능한 m이 있는 첫 N. m = 그 N에서 가능한 가장 큰 m(m = N−1부터 내려감)
종료: 어떤 N에서 W_u ≥ W_min 인 마디가 하나도 없으면(I_lb가 N에 대해 감소하므로 이후 N도 없다) → trim_config_unrecommendable
```

* 숫자 상수 없음. N 상한은 W_min 조건이 만든다.
* 결과: (N, m, I_lb, I_T = (2^N − 1)·I_lb, σ_U 최소·최대, 선형 보정 구간 −V_sys,s ± \|t\|·I_T).

### 9.5 1단계 출력과 파생 topology

`run_trim_candidates`(pipeline)가 front 집계(G-4)로 (쌍, 극성)마다 추천 (N, m)을 정하고, 그 선택으로 `compose_trim_decl`(approval_id None) → `augment_trim`을 불러 다음을 출력 폴더에 쓴다.
* `<circuit>.trim_d<순위>.topology.json`(파생 topology. 출력이며 정본이 아니다)
* `<circuit>.trim_d<순위>.topology.md`(connectivity 표). 만드는 방법: `assets/topology_to_markdown.py`를 하위 프로세스(`sys.executable`)로 실행한다(E-16. 엔진이 assets를 import하지 않는다). 실패하면 그 행에 사유를 싣고 정지하지 않는다(표는 사람 검토용 출력이다). 도구가 옛 엔진 로더에 기대는 위험은 §18.2 X-T7
* `<circuit>.trim_d<순위>.approval_draft.json`(§8.1 초안)
* 결과 JSON `trim.stage1`(§13)

상보 입력쌍(D-7)이면 두 쌍의 추천을 한 파생 topology(DAC 둘)로도 낸다.

---

## 10. 2단계: θ·유도·코드 상태·제약·metric (TR-5, TR-6)

### 10.1 S0 두 개

2단계 단계 A는 원본 S0와 파생 S0(봉인 코드 상태 = seal_plus)를 만든다. 원본 S0는 구조 동일 검사(§3.2)와 pass 0(§10.3)에 쓴다. 둘 다 실행 수명이고 같은 블록 결과 색인·`RunCounters`를 쓴다(40 §2.4.5 '수명'). 원본 S0의 블록 입력은 1단계와 같은 topology라도 실행이 다르므로 다시 계산한다(실행 사이 재사용 없음, 40 §2.4.3).

### 10.2 θ

* 원본 성분: 원본 θ 스키마 성분 그대로(키 동일). **스키마 확장 성질**: 파생 스키마 ⊇ 원본 스키마이고 공통 키의 뜻이 같아야 한다. 단계 A가 두 스키마를 대조하고 어기면 `trim_schema_not_extension`(`StructureUnresolvedError`)으로 정지한다(TR-M이 미리 잰다).
* trim 성분(DAC마다): 셀 전류원 묶음의 ln IDu 하나·L 하나, 켜진 스위치 묶음의 ln IDu 하나·L 하나.
  - 셀 전류원은 gate·source 공유라 LR1 L 동치류와 equal_vgs로 이미 하나로 묶인다(writer 하나, 나머지 순방향).
  - 스위치는 게이트 넷이 서로 달라 구조 규칙으로 묶이지 않는다. 그래서 `trim_decl`의 셀 표에서 '스위치 묶음'을 선언 묶음으로 넘겨, 쓰기 스위치들의 ln IDu와 L을 θ 하나로 묶는다(`search/trim_ties.py`, 묶음 확장은 기존 궤도 묶음 `tie_expand`와 같은 형식).
  - 계획 N3.4 θ 행 '단위 셀 gm/ID·L만'을 셀의 두 소자 종류로 읽은 것이다(§18.2 X-T2).
* I_u·I_T는 θ가 아니다(D-16, X-3). 셀 전류는 KCL 기저의 `trim_unit` 항 × w_c다. `trim_unit` 값은 평가마다 §10.3이 정해 커널 extras로 준다(θ 스키마 구조는 S0에 고정, 값만 평가마다).
* θ 상자: ln IDu는 kind별 LUT 포락선, L은 PDK 칸(E-18). 선언이 필요 없다.

### 10.3 I_u 유도(D-16 하한, 자기일관)

평가 하나(θ 하나)는 `trim_evaluate(sctx, theta)`(search)가 다음 순서로 한다.

1. **pass 0**: 원본 컨텍스트에서 θ의 원본 성분으로 `evaluate` → 원본 봉인 점의 t₀, σ₀, V_sys,s,0. I_u⁽⁰⁾ = (k·σ₀ + \|V_sys,s,0\|)/(\|t₀\|·(2^N − 1)). 출발값이 θ만의 함수라 결정적이다.
   - pass 0이 실패(후보 실패)하면 그 평가는 같은 사유의 후보 실패다.
2. **반복** i = 0, 1, …: 파생 컨텍스트에서 (θ, I_u⁽ⁱ⁾)로 커널 평가 → 봉인 점의 t, σ_in(DAC mismatch 포함), V_sys,s → I_u⁽ⁱ⁺¹⁾ = (k·σ_in + \|V_sys,s\|)/(\|t\|·(2^N − 1)).
   - 수렴: \|ln I_u⁽ⁱ⁺¹⁾ − ln I_u⁽ⁱ⁾\| ≤ ln(1 + ε_I), ε_I = 그 평가에서 LSB 셀 전류원의 상대 전류 분해능 (gm/ID)·tol_V(봉인 3이 쓰는 tol_I/I와 같은 양). 수렴하면 판정 점 = 마지막으로 평가한 점(I_u⁽ⁱ⁾)이다.
   - 반복 상한 K_trim = `k_max(width, tol)`, width = 셀 전류원 kind `current_box`의 ln(I_max/I_off), tol = 그 상자 안 LUT 격자 마디의 ln(1 + min (gm/ID)·tol_V). 둘 다 S0 값이라 평가 전에 정해진다.
   - 상한에 닿으면 `trim_iu_unconverged`(`InfeasibleSizingError` 하위 = 결정적 도메인 실패, 색인에 실패 기록으로 등록 -- X-9).
3. 판정은 마지막 평가의 봉인 점에서 한다(DEC-74: 유도값과 판정값이 다르면 판정값이 이긴다).

**E_total 계산**(XRUN-F1 X-8 '모든 커널 평가를 E_total에'): pass 0과 반복 하나하나가 커널 평가다(`perf.kernel_calls`에 센다). 평가 시작 전에 남은 탐색 예산 ≥ 1 + K_trim(묶음 상계, FD 묶음 규칙 40 §2.4.14 (5) C (5)와 같은 방식)인지 `search_ceiling`으로 확인하고, 아니면 평가 0으로 정지 사유 `eval_budget`이다. 색인 상한 식(40 §2.4.5)은 커널 평가 수 E_total에 대해 그대로 성립한다(반복마다 커널 평가로 세므로).

**같은 입력 재계산**: 반복의 각 회차는 extras `trim_unit` 값이 달라 입력 버전이 다르다. 같은 θ의 같은 I_u가 다시 오면(다른 lineage의 FD 시험점 등) 블록 결과 색인이 이식한다. 그래서 판정 1(재계산 0)은 그대로 성립한다.

비용·대안은 §18.1 TD-1(원래 취지와 다름 후보)에 따로 둔다.

### 10.4 판정 점의 trim 값 `trim_dac_values`(S2 블록)

판정 점 스냅샷에서 계산해 `graph/trim: dac`(DAC마다 `TrimDacValues`)에 쓴다.

| 칸 | 정의 |
|---|---|
| `i_unit_amp`, `i_total_amp`, `i_lsb_amp` | I_u(판정 점 값), I_T = (2^N − 1)·I_u, I_LSB = 2·I_u |
| `i_lower_amp` | 판정 점 값으로 다시 잰 하한 (k·σ_in + \|V_sys,s\|)/(\|t\|(2^N − 1)) |
| `t_v_per_amp`, `effective_sign` | §9.2와 같은 정의(파생 회로 봉인 점) |
| `sigma_unit_rel` | σ_U(G-5 2단계) |
| `sigma_dnl_lsb` | σ_DNL(m) |
| `lsb_in_v` | \|t\|·I_LSB |
| `range_linear_v` | (−V_sys,s − \|t\|·I_T, −V_sys,s + \|t\|·I_T) |
| `residual_bound_v` | Δ_max/2 = \|t\|·I_u·(1 + k·σ_DNL(m)) |
| `thermo_sigma_ratio` | §3.5 일치 확인 비 |
| `iterations` | §10.3 반복 수와 회차별 I_u |

### 10.5 코드 상태 균형 풀이 `trim_code_states`(S2 블록, 분할 = 코드 상태)

봉인 점 스냅샷에서 상태 `minus`, `end_plus`, `end_minus`마다(분할 key = 상태 이름, 40 §2.4.4 분할 -- 상태끼리 서로 읽지 않으므로 독립 분할):

* **풀이 `balance_solve`**(`sizing/fixed_geometry_dc.py`, 순수 함수): **고정 기하 DC**. 모든 켜진 MOS의 W·L = 봉인 점 값(off 소자 제외 -- 그 상태의 off 집합).
  - 고정 넷: 레일, gate 전용 넷(봉인 점 전압, 스위치 게이트는 그 상태의 on/off 레벨), 입력 포트 = 입력 공통모드(봉인 점 입력 DC) ± V_id/2, 값 선언 이상 전류원.
  - 미지수: 나머지 넷 전압 + V_id.
  - 방정식: 미지 넷마다 KCL(순방향 LUT 전류 IDu·W/L의 합 = 0) + 출력 균형 1개(§3.6: 차동 V(out_p) − V(out_n) = 0, 단일 V(out) = 기준).
  - 풀이: `newton_solve`(E-10). 야코비안 = LUT gm·gds·gmb(순방향 조회 한 번에 함께). 시작점 = 봉인 점 전압 + V_id 선형 예측 −(V_sys,s + s·t·δ(c)). 허용오차: 넷 KCL 잔차 ≤ 그 넷에 닿은 소자 tol_I 합(봉인 3과 같은 양), 노드 걸음 ≤ 그 넷 tol_V. 폭 = 레일 전위 폭. 상수 없음.
  - W3 노드 목표(`fixed_values`의 목표 넷)는 고정하지 않는다(목표는 사이징 입력이지 회로 소자가 아니다). 그 넷이 풀이에서 결정되지 않으면(특이) `trim_balance_singular`.
  - 켜진 소자가 풀이 중 VGS < 0이 되면 LUT 축 밖 → `trim_balance_outside_lut`(클램프 없음).
* **포화 검사**: 해에서 off 소자와 triode 선언 소자(§3.1 스위치)를 빼고 봉인 7과 같은 식(VDS ≥ VDSAT + tol_vdsat)으로 행을 만든다.
* **쓰는 값** `graph/trim: code_states` = 상태마다 `CodeStateSolution(name, v_in_v, node_v, saturation_rows, newton_detail)`.
* 실패(`trim_balance_*`, newton 사유)는 결정적 도메인 실패라 그 평가의 후보 실패다.

### 10.6 trim 제약(선언이 있을 때만, 출처 = spec `offset_trim`)

| 이름(행) | 정의 | 판정 |
|---|---|---|
| `trim_range` | lo = min(V_in(end_minus), V_in(end_plus)), hi = max(…). margin = min(hi − k·σ_in, −k·σ_in − lo) | margin ≥ 0. 행 c = margin / 분해능(분해능 = 두 끝 V_in의 newton 노드 오차 추정 + k·`offset_analysis` 분해능) |
| `trim_residual` | `residual_bound_v` | ≤ V_res(spec `residual_offset_v`, `value_from_spec`). 분해능 = \|t\|·I_u·k·(σ_DNL 분해능) + I_u·(t 분해능) |
| `trim_states_saturation` | 세 상태의 포화 행 | 기존 봉인 7 행과 같은 margin 규칙 |

* '0 이상'·'V_res 이하'는 정의에서 나오는 문턱이고 새 상수가 아니다.
* 계획 N3.4: metric이 `verified_by`(SPICE 오라클)를 가진 뒤에만 판정 제약이다. TR-5 병합 때는 오라클 측정이 없으므로 metric 서명 `oracle_measure` = None이고 spec 로더의 `spice_unverifiable` 목록에 실행 전 출력된다(DEC-90 (3)). 판정 경로는 그대로 동작한다(제약 행 계산·front 판정). TR-7이 오라클 측정을 붙여 `verified_by` = `spice_oracle`로 바꾼다. 이 처리는 기존 `spice_unverifiable` 규칙 그대로다.

### 10.7 metric(레지스트리 `_ROWS`, DEC-68 명명)

| 이름 | 단위 | 영역 | 결과 형식·필드 | 쓰임 |
|---|---|---|---|---|
| `trim_lsb_mv` | mv | ss | `TrimDacValues.lsb_in_v` | 보고 |
| `trim_range_margin_mv` | mv | dc | `TrimRange.margin_v` | 제약 `trim_range` |
| `trim_range_lo_mv`·`trim_range_hi_mv` | mv | dc | `TrimRange` | 보고 |
| `trim_range_linear_gap_mv` | mv | dc | 판정 구간 − 선형 구간(양 끝 중 큰 차) | 보고(N3.4) |
| `trim_residual_mv` | mv | ss | `residual_bound_v` | 제약 `trim_residual` |
| `trim_dnl_sigma_lsb` | lsb | ss | `sigma_dnl_lsb` | 보고 |
| `trim_power_w` | w | dc | DAC 소자 공급 전류 × 레일 전압 | 보고(`power_dc_w`에 이미 포함) |
| `trim_area_m2` | m2 | geom | trim 소자 Σ W·L(같은 면적 식) | 보고(`area_search_m2`에 이미 포함) |

* `lsb`는 새 단위 어휘다(N3.16 정본 표에 행 추가, TR-5). mv 접두는 기존 offset metric과 같다(DEC-68 표시 단위 허용).
* 이 metric들은 trim 선언 없는 spec에서 요청하면 `trim_undeclared`(정의 불가)다.

### 10.8 offset spec 의미 전환(TR-6, 계획 N3.6)

| 대상 | 처리 |
|---|---|
| `offset_in_sigma_mv` | 공존 거부(§5.2). 값은 보고와 trim 제약 입력 |
| `offset_excess`·`offset_sys_mv` 상한 | 보고로 내림(§5.2) |
| `iv_matching_l` L 하한(출발값) | 선언이 있으면 끈다. 새 출발값 규칙: 입력쌍 L 출발값은 `offset_in_sigma_mv` 하한 없이 다른 출발 규칙(gain·잡음)이 정한 값 그대로. 판정은 바뀌지 않는다(F-4, X-5) |
| `iv_matching_l` 가드 부하 집합 | `trim_role`이 있는 소자는 부하 역할 집합에서 뺀다(§11) |
| 잡음·극점·headroom·전력·면적 | 바꾸지 않는다(trim 소자가 기존 해석에 자동으로 들어간다. off 소자 처리는 §3.1) |
| 보고 문구 | 'offset trim은 drift와 1/f를 보정하지 않음', '판정·코드 결정은 LUT 측정 조건(<temp_c>, <corner>) 한 조건', '판정 입력 DC 한 점', 상보 쌍이면 'ICMR 전체 보정 미보장'(D-7), D-3 한계(같은 k의 다중 전이) |

---

## 11. 구조 역할 `trim_dac` (TR-4)

* **필드**: `device: trim_role` = `TrimRole(dac, cell, function, weight)`(function ∈ {`cell_source`, `switch_a`, `switch_b`}) 또는 None. writer = 새 S1 블록 `s1_trim_roles`(`graph/s1_trim_roles.py`). 입력 = `TrimProvenance`의 셀 표(extras). 역할은 유도가 아니라 출처 기록에서 오는 선언이다(계획 N3.3 스키마 행). S1 키(`facts_fp`와 같은 자리)에 출처 지문을 넣는다.
* **S1v**: `trim_role`이 있는 소자는 신호 도달(`signal_reach`)의 채널 엣지에서 빠진다(신호가 주입 넷에서 스위치를 거쳐 X로 번지지 않는다). 그 결과 trim 소자의 셀 종류는 `off`, 블록 AC 역할 어휘(`input`·`load`·`mirror`·`tail_source`·…)에 들지 않는다. 블록·stage·루프·극점 노드 유도에 쓰이지 않는다.
* **그대로 남는 것**(FR-T5): DC writer·KCL(§3.1), MNA 용량 스탬프, 잡음원(켜진 소자), offset 해석 mismatch 원, 전력·면적.
* **가드 집합**: `offset_excess` 분모(입력 셀)는 그대로라 trim 소자가 분자에만 든다(계획 N3.6). `iv_matching_l`·`_helpers_guard`의 부하 역할 집합은 AC 역할에서 오므로 위 S1v 규칙으로 자동 제외된다. test가 확인한다.
* **규칙 지문**: `s1_trim_roles.py`는 S1 규칙 파일(`S1_RULE_FILES`)에, S1v 쪽 변경 파일은 이미 `S1V_RULE_FILES`에 있다. 그래서 `structure_rule_fp()`가 바뀌고 structure.json 2개가 stale이 된다(계획 N3.3·N9). **TR-4 착수 조건 = 재승인 계획 사용자 승인, 병합 조건 = 재승인 완료**(사실 내용 동일, `rule_hash`만 갱신, 40 §3.2-3 '규칙 파일이 나중에 바뀌면' 절차).

---

## 12. graph 필드·계산 블록·재사용 정합

### 12.1 필드 소유표(새 필드 전부)

| 필드(kind/key: field) | 값 형식 | writer(계산 블록, 파일) | 층 | 선언 없을 때 |
|---|---|---|---|---|
| `device: trim_role` | `TrimRole` \| None | `s1_trim_roles`(`graph/s1_trim_roles.py`) | S0 | 모두 None |
| `graph/trim: pairs` | `TrimPair` tuple | `trim_pairs`(`metrics/trim_pairs.py`) | S0 | () |
| `graph/trim: structure_diff` | `TrimStructureDiff` | `compare_trim_structure` 호출 결과를 단계 A가 보고서에 싣는다 -- graph 필드 아님(두 S0의 비교 출력, 판정은 정지) | -- | -- |
| `graph/metrics: offset_adjoint` | (view id, A_dm, ((넷, z), …)) \| None | `metrics_aux`(기존 writer, 쓰기 열 추가) | S2 | None |
| `graph/trim: candidates` | `TrimCandidate` tuple | `trim_candidates`(`metrics/trim_candidates.py`) | S2(1단계 front 점) | () |
| `graph/trim: dac` | `TrimDacValues` tuple | `trim_dac_values`(`metrics/trim_dac_values.py`) | S2(2단계 판정 점) | () |
| `graph/trim: code_states` | `CodeStateSolution` tuple(분할 = 상태) | `trim_code_states`(`sizing/trim_code_states.py`) | S2 | () |
| `graph/trim: range` | `TrimRange` | `trim_dac_values`가 code_states를 읽어 같이 쓴다 | S2 | None |
| `graph/kernel: trim_ties` | 스위치 묶음 | `kernel_fields`(기존 writer, 쓰기 열 추가) | S0 | () |
| 제약 행 trim 3종 | 기존 제약 행 형식 | 기존 search 제약 블록(행 생성 함수 `trim_constraint_rows` 추가) | S2 | 행 없음 |

* `offset_adjoint`는 `offset_analysis`가 이미 계산한 z(E-11)를 그대로 담는다(같은 LU, 재계산 없음). `OffsetAnalysis` 값 형식은 바꾸지 않는다(바꾸면 선언 없는 실행의 `metrics_aux` 값이 바뀌어 §3.3 V 부류를 깬다).
* 출처 기록 `TrimProvenance`와 `TrimDecl`은 S0 입력(graph 밖, spec과 같은 지위)이다. 둘의 지문이 쓰는 블록의 입력 버전에 들어간다.
* front 위 집계(G-4 추천 N·m, 순위)는 front 점 스냅샷 필드를 읽어 만드는 **출력**이고 graph 필드가 아니다(설계 값의 새 정본을 만들지 않는다).

### 12.2 계산 블록 규칙

* 새 블록은 모두 `compute_block`이고 `Projection` 하나만 읽는다. 반복의 출발값(§10.3)은 블록 밖 `trim_evaluate`가 extras로 넘긴다 -- 블록이 parent·이전 회차 값을 읽지 않는다(40 §2.4.4 '이식이 비트 동일인 전제').
* `trim_code_states`의 newton 시작점은 봉인 점 스냅샷(투영 안)의 함수다.
* `metrics_aux`가 `offset_adjoint`를 쓰는 것은 trim 선언(extras 플래그)이 있을 때만이다.

### 12.3 실행 안 재사용(XRUN-F1 정합)

* 원본 S0·파생 S0의 블록은 각자 한 번 계산된다(`computes` = 1, 판정 1).
* pass 0의 커널 평가는 원본 컨텍스트 평가라 같은 원본 θ가 다른 파생 θ에서 다시 오면(trim 성분만 다른 θ) 평가 캐시·블록 색인이 재사용한다. 이것이 pass 0의 비용을 줄인다.
* FD 열에서 trim 성분 하나만 움직이면 원본 성분 블록 입력은 같다 → pass 0 전체가 색인 적중이다.
* `test_g10_no_recompute_9circuits`에 trim 선언 픽스처 회로를 하나 더해 판정 1·5를 단언한다(TR-5).

### 12.4 XRUN-F1·NFR-4 card 2와의 정합 점검

| 항목 | 정합 |
|---|---|
| 블록 호출 `donors`·`counters` 필수(40 §2.4.4) | 새 블록 전부 같은 호출 경로 |
| 블록 결과 색인 수명 = 실행(단계 A부터) | 원본·파생 S0 블록 포함, 실행 하나 |
| E_total(40 §2.4.9), `search_ceiling`·`search_stop`(card C) | §10.3 묶음 상계 1 + K_trim, 단일 확인 지점 그대로 |
| 결정적 도메인 실패 등록·재연(X-9) | `trim_iu_unconverged`·`trim_balance_*`는 `InfeasibleSizingError` 하위로 만들어 등록 대상 |
| `ThetaCoords`(card A) | trim θ 성분도 같은 정본으로 좌표 변환(새 사본 금지) |
| BLAS 고정·`env_fp`(NFR-4 card 2) | 새 선형 풀이(newton LU)는 scipy `lu_factor`(실수, 엔진 크기) -- 40 §2.4.13 표 '실수 lu' 묶음에 자리를 더한다(TR-5에서 표 갱신) |
| 관찰 지점 계약(J-3·J-7·J-16) | `find_front`·`layer0_center`의 모듈 전역 호출 방식 유지. `trim_evaluate`는 `kernel.evaluate`를 감싸는 새 파일이고 그 둘을 바꾸지 않는다 |
| 결과 JSON 형식 변경 | §13 새 칸만 더한다. 기존 칸의 뜻은 그대로 |

---

## 13. 결과 JSON 칸

| 위치 | 칸 | 내용 |
|---|---|---|
| 단계 A 보고서 | `trim` | `{mode: "none"\|"stage1"\|"stage2", spec: TrimSpec 값, pairs, temperature: {declared_c, lut_temp_c, lut_corner}, demoted_constraints, structure_diff(2단계), approval: {approval_id, path, binding_checks[]}, provenance(2단계)}` |
| `find_front` 결과(runs 줄) | `trim.stage1` | front 점마다 후보표(§9.2), 순위(§9.3), 추천 (N, m)과 점별 (N_p, m_p), `t_varies` 표지, 추천 불가 점, 출력 파일 경로·sha256(파생 topology·md·승인 초안), 사유 코드 |
| 〃 | `trim.stage2` | front 점마다 `trim/dac`·`trim/range`·`code_states` 요약, I_u 반복 기록, 불가능이면 `trim_config_infeasible`과 위반 경계(하한 > 상한의 두 값) |
| 〃 | `trim.reports` | §10.8 보고 문구 목록, D-3 한계, 단일 온도 한계(FR-T9) |
| `perf` | `trim_kernel_passes` | pass 0·반복 커널 평가 수(합은 `kernel_calls`에 이미 포함, 내역) |
| S3 evals 줄 | `trim_iu_amp` | 그 평가의 판정 I_u(없으면 null) |

선언 없는 실행에서는 `trim`이 `{mode: "none"}`이고 나머지 새 칸은 없다(§3.3 N 부류 단언 대상).

---

## 14. 파일 분할

### 14.1 새 파일(규칙 A: 파일당 진입점 하나)

| 파일(`E/`) | 진입점 | 층 | card |
|---|---|---|---|
| `authoring/spec_trim.py` | `trim_declaration(raw)` | authoring | TR-1 |
| `authoring/spec_trim_conflicts.py` | `trim_constraint_conflicts(trim, constraints)` | authoring | TR-1 |
| `authoring/trim_values.py` | (값 형식 선언 모듈: `TrimSpec`·`TrimSelection`·`TrimCell`·`CodeState`·`TrimDac`·`TrimDecl`·`TrimProvenance`) | authoring | TR-1 |
| `authoring/trim_approval.py` | `load_trim_approval(path)` | authoring | TR-1 |
| `authoring/trim_decl.py` | `compose_trim_decl(spec_trim, selections, topology, supplies, approval_id)` | authoring | TR-1 |
| `authoring/trim_rule_fp.py` | `trim_rule_fp()` | authoring | TR-1 |
| `authoring/topology_data.py` | `topology_from_data(data, where)`(`load_topology`가 JSON 읽기 뒤 이것을 부른다 -- 게이트 순서 한 벌) | authoring | TR-3 |
| `authoring/trim_augment.py` | `augment_trim(topology, trim_decl)` | authoring | TR-3 |
| `graph/s1_trim_roles.py` | `s1_trim_roles`(블록) | graph | TR-4 |
| `graph/trim_structure_compare.py` | `compare_trim_structure(original, derived, trim_devices)` | graph | TR-4 |
| `sizing/fixed_geometry_dc.py` | `balance_solve(...)` | sizing | TR-5c |
| `sizing/trim_code_states.py` | `trim_code_states`(블록) | sizing | TR-5c |
| `metrics/trim_pairs.py` | `trim_pairs`(블록) | metrics | TR-2 |
| `metrics/trim_candidates.py` | `trim_candidates`(블록) | metrics | TR-2 |
| `metrics/trim_dnl.py` | `dnl_sigma(sigma_unit, n_bits, m_bits)` | metrics | TR-2 |
| `metrics/trim_recommend.py` | `recommend_trim_config(...)` | metrics | TR-2 |
| `metrics/trim_dac_values.py` | `trim_dac_values`(블록) | metrics | TR-5b |
| `metrics/trim_types.py` | (값 형식: `TrimPair`·`TrimCandidate`·`TrimDacValues`·`TrimRange`) | metrics | TR-2 |
| `search/trim_ties.py` | `trim_theta_ties(...)` | search | TR-5a |
| `search/trim_kernel.py` | `trim_evaluate(sctx, theta)` | search | TR-5b |
| `search/trim_constraints.py` | `trim_constraint_rows(...)` | search | TR-5b |
| `pipeline/trim_binding.py` | `bind_trim(...)` | pipeline | TR-3 |
| `pipeline/trim_stage1.py` | `run_trim_candidates(...)` | pipeline | TR-2(표)·TR-3(파생 출력) |

값 형식은 writer 층에 둔다: `TrimRole`은 graph가 쓰는 필드 값이라 `graph/s1_values.py`, `CodeStateSolution`은 sizing이 쓰므로 `sizing/s2_values.py`에 둔다(층 순서상 metrics 값 모듈에 두면 graph·sizing이 import할 수 없다).

### 14.2 고치는 파일(범위)

| 파일 | card | 범위 |
|---|---|---|
| `authoring/spec_schema.py`, `spec_load.py`, `spec_model.py`(`SizingSpecDoc` 칸 `offset_trim`·`trim_demoted_constraints`), `spec_sources.py`(허용 kind) | TR-1 | 부분 |
| `authoring/topology_load.py` | TR-3 | 부분(데이터 단계 분리) |
| `pipeline/stage_a.py`(`trim_approval_path` 인자, 온도 대조, 두 S0, 구조 검사, 보고서 `trim`) | TR-1·TR-3·TR-4 | 부분 |
| `metrics/offset_analysis.py`(z를 반환값 밖 두 번째 결과로 넘김 -- 형식 `OffsetAnalysis`는 그대로), `metrics/metrics_aux.py`(쓰기 열 `offset_adjoint`) | TR-2 | 부분 |
| `graph/signal_reach.py`·`cells.py`·`s1v_build.py`(trim 소자 제외), `graph/s1_build.py`(블록 추가·S1 키), `graph/s1_values.py`(`TrimRole`, 규칙 파일 목록) | TR-4 | 부분 |
| `sizing/current_basis.py`, `theta_check.py`, `block_currents.py`, 쓰기 계획(`writer_plan.py`), `block_widths.py`, 봉인 1·2·3·7·8 파일, `kernel_fields.py`, `theta_schema.py`, `dc_inputs.py`(`trim_unit` 값) | TR-5a | 부분 |
| `metrics/ss_linearize.py`·`noise_sources.py`·`device_sigma.py`(off 소자) | TR-5a | 부분 |
| `metrics/registry.py`·`verified_by.py`·`catalog.py`(trim metric) | TR-5b | 부분 |
| `search/kernel.py`(trim 평가 분기 호출만), `search/search_context.py`(원본 컨텍스트 참조), `search/find_front.py`(결과 칸) | TR-5b | 부분 |
| `search/iv_matching_l.py`, `search/_helpers_guard.py` | TR-6 | 부분 |
| CONTRACT(`authoring`·`graph`·`sizing`·`metrics`·`search`·`pipeline`), `_module_map.py`, 함수 레지스트리 §2, N3.16 명명 표 | 각 card | 갱신 |

### 14.3 층 순서·모듈 지도·test

* 층: `authoring`(spec·승인·합성·변환) < `graph`(역할·구조 비교) < `sizing`(코드 상태 풀이) < `metrics`(후보·DAC 값) < `search`(평가·제약) < `pipeline`(단계 진입·출력). 역방향 import 없음(규칙 C).
* `_module_map.py`: 새 파일마다 `ModuleEntry(경로, "entry", 진입점, 설명, (계획 근거))`. 값 형식 모듈은 기존 값 모듈과 같은 종류.
* test 1:1(규칙 H): 새 파일마다 `E/tests/<패키지>/test_<파일>.py`. 9회로 실행 test는 `E/tests/integration/`.
* 함수 레지스트리(`docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`) §2에 개념 행 추가: 'trim 주입 쌍', '파생 topology 변환', '고정 기하 DC 균형 풀이', 'trim DNL σ', 'trim N·m 추천'. 2026-10-15 grep: 엔진에 `trim` 0건(F-18), 고정 기하 DC 풀이 개념 없음(`newton_solve`는 SCC 잔차 풀이 -- `balance_solve`가 그것을 재사용한다).

### 14.4 배선표(만들면 배선)

| 새 함수 | 호출 경로 |
|---|---|
| `trim_declaration`·`trim_constraint_conflicts` | `load_sizing_spec` |
| `load_trim_approval`·`compose_trim_decl`·`augment_trim`·`bind_trim` | `run_stage_a`(2단계) / `run_trim_candidates`(1단계 compose·augment) |
| `topology_from_data` | `load_topology`, `augment_trim` |
| `trim_rule_fp` | `compose_trim_decl`, `bind_trim` |
| `s1_trim_roles` | `build_s1` |
| `compare_trim_structure` | `run_stage_a`(2단계) |
| `trim_pairs` | 단계 A S0 블록 열 |
| `trim_candidates`·`dnl_sigma`·`recommend_trim_config` | `run_trim_candidates`(front 점마다) / `trim_dac_values`(`dnl_sigma`) |
| `trim_theta_ties` | `build_search_context`(도메인 묶음) |
| `trim_evaluate` | `kernel.evaluate`(trim 선언 실행에서 평가 진입) |
| `trim_dac_values`·`trim_code_states`·`balance_solve`·`trim_constraint_rows` | `trim_evaluate` 판정 점 / 제약 블록 |
| `run_trim_candidates` | `find_front` 뒤 1단계 진입(파이프라인 U16 전까지는 `find_front`가 결과 칸을 쓰는 지점에서 부른다) |

---

## 15. card 범위·완료 조건·test 초안

공통: 순서 = design 승인 → test(interface card만 보고) → code → 독립 판정. 각 card 완료 조건에 (a) 배선 증거(§14.4 행의 호출 grep + 실행 경로 test), (b) 상위 N6.3 graph 정본·재계산 계수·파일 분할 확인, (c) design 대 구현 gap 분석을 넣는다. test 기대값은 피검 함수를 부르지 않는다.

| card | 범위 | 선행 | 완료 조건 | test 초안(독립 oracle) |
|---|---|---|---|---|
| **TR-M** 측정(엔진 코드 무변경) | G-2 표(§3.2)와 G-1 측정 항목(§3.1)·스키마 확장 성질(§10.2)을 9회로 후보 7회로 × 쌍 × 극성에서 잰다. 파생 topology는 측정 스크립트가 §7 규칙을 **독립 구현**해 만든다(구성: 이진·thermometer 셀을 모두 갖는 최소 구성 N = 2, m = 1). 결과 기록 `.ai/verification/trim/tr_m.json` | design 승인 | 비교 행 차이 목록, DC 역할·셀 분류(trim 소자), KCL 기저 풀림 여부, 원본 θ 키 보존 여부가 회로별로 있다. 차이가 있으면 TR-4 design 보완 전 사용자 보고 | 스크립트 자체가 TR-3 `augment_trim` test의 독립 oracle이 된다(같은 규칙의 다른 구현) |
| **TR-1** spec·승인·합성 | §5 전부, §6, §8.1·§8.2, 승인 로더, 온도 대조 | TR-0 승인, T-4 순서 | 섹션 검사·거부 사유 전수, D-4 공존 처리, 온도 대조 거부가 실제로 거부함, 선언 없는 spec 로드 결과 비트 동일 | 형식 위반 픽스처마다 사유 코드 / `offset_in_sigma_mv`와 공존 거부 / `offset_excess` 강등 / 온도 ≠ LUT `temp_c` 거부(LUT 메타를 test가 직접 읽음) / 셀 표·코드 벡터: test가 손으로 쓴 N = 3, m = 1·N = 2, m = 0 표와 대조(§7.4 검산식) / `trim_rule_fp` 파일 바이트 변경 시 변함 |
| **TR-2** z·쌍·후보·추천(보고만) | §9.1~§9.4, `offset_adjoint` 쓰기, 결과 JSON `trim.stage1` 표(파생 topology 제외) | TR-1, TR-M | 7회로 후보표, 사유 코드 9회로(§16), 선언 없는 실행 무동작(§3.3) | t: 작은 손 회로(저항 + 이상 전류원 + 선형 MOS 소신호)에서 손으로 푼 z와 대조 / `dnl_sigma`: 단위 셀 전수 합으로 독립 계산한 최악 전이 분산과 대조 / `recommend_trim_config`: (N, m) 쌍 전수 결과와 순서 규칙 결과 일치, W_min 종료 / 쌍 규칙: matching group 손 픽스처 |
| **TR-3** 변환·출처·결속·출력 | §7, §8.3(1~5), §9.5, `topology_from_data` | TR-2 | 파생 topology가 로드 게이트 통과, 결정성(두 번 비트 동일), 이름 충돌 거부, 승인 stale 다섯 경로 각각 정지, 1단계 출력 파일 | TR-M 독립 구현과 소자·넷·`bias_inputs` 비교 / 입력 dict 순서 섞기 → 같은 출력 / 결속 경로마다 지문 하나만 바꾼 픽스처 → 해당 detail로 정지 |
| **TR-4** 역할·구조 검사 | §11, §3.2 검사(§8.3-6), structure.json 재승인 | TR-3, **착수 조건: 재승인 계획 사용자 승인** | 9회로에서 trim 소자 셀 종류 `off`·블록 역할 없음, 구조 검사 통과(TR-M 차이 0 회로), 차이 주입 픽스처에서 정지. **병합 조건: structure.json 2개 재승인 완료** | 손 회로: trim 소자가 신호 도달에서 빠짐 / 부하 역할 집합에 trim 소자 없음 / 원본 matching group에 trim 소자를 섞은 픽스처 → `trim_structure_divergent` |
| **TR-5a** 전류 0 소자·trim 전류 | §3.1 sizing·metrics 경로, `trim_unit` 기저 항, 스위치 묶음, 스키마 확장 검사 | TR-4, TD-2 결정 | 봉인 상태 파생 회로가 봉인 1~9 통과(픽스처 회로), off 소자 LUT 조회 0(조회 계측), 선언 없는 실행 비트 동일 | off 소자: W = 짝 W, 소신호 gm = 0, 잡음원 없음, σ 항 0 / 원뿔: off 스위치 행 없음 / KCL: 손으로 푼 셀 전류 = w_c·I_u |
| **TR-5b** I_u 유도·DAC 값·제약·metric | §10.3, §10.4, §10.6, §10.7, E_total 계상 | TR-5a, TD-1 결정 | 픽스처 회로 2단계 front 생성, 반복 수렴 기록, 묶음 상계 확인, 판정 1·5(재계산 0), 결과 JSON `trim.stage2` | 반복: 해석해가 있는 toy(σ_in이 I_u에 선형)에서 고정점 = 닫힌 식 / 예산: 남은 예산 = 1 + K_trim이면 평가, −1이면 평가 0 / 제약 행 c 부호: 손 계산 |
| **TR-5c** 코드 상태 균형 풀이 | §10.5 | TR-5b | 세 상태 풀이 수렴(픽스처), 포화 행에서 off·triode 제외, 실패 사유 | 오라클: 같은 고정 기하에서 SPICE `.op` + 입력 차 sweep으로 V_in 대조(오라클 측 독립, 허용폭 = 노드 tol 전파) / 선형 예측과의 차 보고 |
| **TR-6** 의미 전환 | §10.8 | TR-5c | `iv_matching_l` 하한 꺼짐(선언 시), 보고 문구, 선언 없는 실행 비트 동일 | 선언 유무 두 spec에서 출발값 차이가 L 하한 행에만 있음 |
| **TR-7** 검증 | §17 전부, 9회로 일반성(§16), 오라클 확장(레인 P: 코드 입력·표본별 코드 선택·온도), `verified_by` 붙이기 | TR-6, 오라클 확장 | §17 판정 통과, 완료 조건 (1)~(5)(계획 N5) | §17 |

계획 N5의 TR-5를 셋(a·b·c)으로, 그리고 TR-M을 더했다(측정 단계 G-2의 자리). card 수만 늘고 범위는 같다.

---

## 16. 9회로 적용 판정(예상, 확정은 TR-2·TR-7 측정)

| 회로 | 입력 | 출력 | 예상 판정 | 막는 것 |
|---|---|---|---|---|
| current_reuse_telescopic_ota | 차동, 상보 | 차동 | 후보 두 쌍(D-7), 추천 가능 | 기존 `offset_in_sigma_mv <= 3.3`과 공존 → 선언 시 로더 거부(D-4, spec 수정은 사용자) |
| folded_cascode | 차동 | 단일 | 후보표 | 추천·2단계: `trim_reference_undeclared`(CI-15) |
| ngcc_3stage_ff | 차동 | 단일 | 후보표 | 같음 |
| nmcnr_amplifier | 차동 | 단일 | 후보표 | 같음. 레일 셋(최저·최고 전압 레일로 극성 레일) |
| sf_pushpull_output_opamp | 차동 | 단일 | 후보표 | 같음 |
| two_stage_ota | 차동 | 단일 | 후보표 | 같음 |
| two_stage_ota_sf | 차동 | 단일 | 후보표 | 같음 |
| common_gate_amplifier | 단일 | 단일 | `trim_single_input_unsupported` | D-8 |
| pushpull_follower_buffer | 단일 | 단일 | `trim_single_input_unsupported` | D-8 |

* 선언이 없는 9회로는 모두 무동작(§3.3 N 부류 빈 값)이고 이것을 TR-7이 측정한다.
* 단일 출력 6회로가 추천까지 가려면 출력 넷 `node_voltage_targets_v`가 필요하다(§3.6, TD-3).
* 계획 N4 표의 '후보'와 다른 점: 단일 출력 회로는 후보표까지만 나온다(§18.2 X-T6).

---

## 17. TR-7 검증 규칙(샘플 수 포함)

**소유**: 이 절의 판정 규칙과 합격선은 design 작성자가 초안을 쓰고 **독립 검증자(design-validator, 이후 TR-7 auditor)가 확정·소유**한다(계획 N5·N6, NFR-T6). 검증자가 바꾸면 그 판이 정본이다. 오라클 구현(레인 P)은 엔진을 import하지 않는다.

**순서**(N5.1): 1 → 2 → 3·4·5. 1이 실패하면 2 이후는 해석하지 않고 보고만 한다.

| # | 항목 | 규칙 | 성격 |
|---|---|---|---|
| 1 | σ_in 일치 | 파생 topology 판정 점(코드 seal_plus, trim 없는 MC)에서 SPICE MC 표본 n개의 입력 환산 offset 표준편차 σ̂. 합격: \|σ_eng − σ̂\| ≤ k·σ̂/√(2(n − 1)) + 엔진 분해능(`offset_analysis` resolution). k = spec 배수(새 신뢰 상수 없음) | 판정 전제 |
| 2 | 27 °C 잔여 | 표본마다 trim 절차 흉내: seal_plus에서 offset 측정 → 모든 코드 c의 잔여를 오라클 DC로 재고 \|잔여\| 최소 코드 선택 → 잔여. **합격: 'trim 전 offset이 [−k·σ̂, +k·σ̂] 안인 표본' 전부가 잔여 ≤ V_res(실패 0)**. 구간 밖 표본 수와 그 잔여는 보고만. 더해 **결정적 끝 표본 둘**: 소자 공칭(mismatch 0) + 입력에 직렬 이상 전압 ±k·σ_eng를 넣은 회로에서 같은 절차 → 잔여 ≤ V_res(구간 끝을 직접 확인 -- MC가 꼬리에 닿지 않는 문제를 대신한다) | 판정(완료 조건 (3)) |
| 3 | 고정 코드 온도 sweep | 2의 표본·코드를 고정하고 온도 점마다 잔여. 온도 점 = LUT·PDK가 선언한 온도 범위의 끝점과 판정 온도(새 온도 상수 없음 -- 범위 선언이 없으면 사용자에게 범위를 묻는다, TD-6). §3.8 분해 표 | 보고 |
| 4 | 코너별 보정 구간 | PDK 선언 코너마다 공칭 소자의 end_plus·end_minus 균형 V_in | 보고 |
| 5 | 끝 코드 headroom 온도 의존 | 3의 온도 점마다 끝 코드 포화 여유(off 소자 제외) | 보고 |

**샘플 수 규칙**:
* n = 1 + ⌈k²·(2·k·σ_eng / LSB_in)² / 2⌉ … (식 S)
* 유도: σ 추정의 표준오차 σ/√(2(n − 1))에 k배를 한 값이 '보정 구간 요구량 k·σ를 반 LSB(LSB_in/2) 이상 옮기지 않을 σ 오차'(LSB_in/(2k))보다 작아야 한다: k·σ/√(2(n − 1)) ≤ LSB_in/(2k). 모든 양은 spec(k)·엔진(σ_eng, LSB_in = \|t\|·I_LSB)에서 온다.
* 같은 n개 표본을 1과 2에 같이 쓴다(표본마다 trim 절차를 하므로 추가 비용 없음).
* 한계 문구(보고서): 'MC는 분포 내부를 확인한다. k 꼬리(구간 끝)는 결정적 끝 표본으로만 확인한다. 수율 확률은 주장하지 않는다(D-2: 분포 가정 없음)'. 비용이 실행 한도를 넘으면 n을 줄이지 않고 '판정 불능(표본 부족)'으로 보고한다(기준 약화 금지).
* 이 식의 양식(반 LSB 기준)은 검증자 확정 대상이다(§18.1 TD-5).

**9회로 일반성**: §16 표의 사유 코드를 9회로 전수로 재고, 선언 없는 실행의 무동작(새 필드 빈 값, §3.3 비교)을 보인다.

---

## 18. 결정 필요·원래 취지와 다름

### 18.1 사용자 결정 필요(이 design이 정하지 않음)

| ID | 질문 | 선택지·근거 | 막는 card |
|---|---|---|---|
| TD-1 | **I_u 결정 방식**(원래 취지와 다름 후보). 계획 D-16(하한)·X-3(θ에서 뺌)을 지키는 기본 설계(§10.3)는 평가마다 pass 0 + 고정점 반복이 필요해 커널 평가가 θ 하나에 2 + 반복 수다(예산 E_total을 그만큼 먹는다) | (가) 기본 설계 그대로(계획 결정 충실, 비용 큼). (나) I_u를 θ 성분으로 두고 보정 구간을 제약으로 판정 -- 전력·면적 최소화가 I_u를 하한으로 민다(면적도 I_u에 대해 증가). 커널 평가 1회, 반복·pass 0 없음, 결정성 자연. **D-16 선택지 'θ로 둘지'를 사용자가 고르지 않았으므로 (나)는 원래 취지와 다르다** | TR-5b |
| TD-2 | **꺼진 스위치의 진성 용량**: VGS < 0이 LUT 축 밖(E-5)이라 cgs·cgd·cgb가 정의되지 않는다 | (가) 접합 용량만 넣고 진성 용량 누락을 결과에 기록, 판정은 오라클(PM·극점이 낙관 쪽으로 틀릴 수 있다 -- 근사라 원칙 'LUT가 출처'와 다름) (나) LUT 재생성으로 VGS 음수 축 추가(레인 LUT, 비용·일정) (다) VGS = 0에서 조회(클램프 -- DF-27 위반이라 권하지 않음). 권고 (나), 그 전까지 TR-5a 대기 | TR-5a |
| TD-3 | 단일 출력 6회로의 출력 기준 DC(`node_voltage_targets_v`, CI-15) | 값은 사용자 몫. 선언 전에는 그 회로들이 후보표까지만 간다(§3.6) | 해당 회로 2단계 |
| TD-4 | TR-4의 structure.json 2개 재승인 계획 | 계획 N3.3·N9 그대로(사실 내용 동일, `rule_hash`만 갱신) | TR-4 착수 |
| TD-5 | TR-7 규칙(§17) 확정 | 소유자 = 독립 검증자. 사용자 결정이 아니라 검증자 확정 사항이지만 판정 기준이므로 보고 | TR-7 |
| TD-6 | 온도 sweep 범위(§17-3) | LUT·PDK에 온도 범위 선언이 없으면 범위 값은 사용자 몫(T-5는 '선언 온도 범위'를 말하나 spec 필드는 trim 온도 하나뿐) | TR-7 보고 |
| TD-7 | 1단계 connectivity 표 도구가 옛 엔진 로더에 기댄다(E-16) | (가) 지금 도구 그대로 하위 프로세스 (나) 도구를 새 엔진 로더로 옮기는 별도 card. legacy 삭제 전에 (나)가 필요하다 | TR-3 출력 |

### 18.2 원래 취지와 다름(따로 보고)

| ID | 내용 |
|---|---|
| X-T1 | TD-1 (나)는 D-16/X-3과 다르다(위). 기본 설계는 (가)다 |
| X-T2 | 계획 θ 행 '단위 셀 gm/ID·L만'을 셀의 두 소자 종류(전류원, 스위치)의 ln IDu·L로 읽어 DAC마다 θ 성분 넷이다(§10.2). 스위치 크기를 θ 밖 규칙으로 정하는 안은 상수(폭 비 등)를 발명해야 해서 택하지 않았다 |
| X-T3 | 2단계 평가마다 원본 topology pass 0을 한다(§10.3). 계획에 없던 단계이고, I_u 출발값을 θ만의 함수로 만들기 위해서다(결정성) |
| X-T4 | G-1 표현: 구조(S1·S1v)는 모든 스위치를 가진 파생 topology 하나로 만들고 코드 상태는 sizing 층의 off 집합으로만 표현한다. 계획은 '소자 제외, 별도 포화 검사 경로' 중 택하라고만 했다 |
| X-T5 | 완료 조건 (1) 비교 제외(G-3)가 계획 D-14 문언('규칙 지문')보다 넓다: 블록 코드 해시에서 온 입력 버전·스냅샷 지문·코드 지문(F2~F4)도 뺀다. 코드가 바뀌는 card에서 이 칸들은 필연적으로 바뀌기 때문이다. 값 부류는 비트 동일 그대로라 기준 약화는 아니라고 보지만, 판정 기준 변경이라 보고한다 |
| X-T6 | 계획 N4 표의 단일 출력 6회로 '후보'는 G-6 fail-closed 때문에 후보표까지만 나오고 추천·2단계는 TD-3 전까지 막힌다 |
| X-T7 | 1단계 connectivity 표를 엔진이 직접 만들지 않고 assets 도구를 하위 프로세스로 부른다(TD-7). 표 형식의 정본이 도구 하나라서다 |
| X-T8 | 켜진 스위치를 `trim_decl`이 triode 의도 영역으로 더한다(§3.1). 지금 `intended_region`은 사용자 spec에만 있는 선언인데, trim 소자 한정으로 엔진 출처 선언이 생긴다(trim 소자는 사용자 topology 원소가 아니므로 사용자 선언 자리가 없다) |
| X-T9 | card 분할: 계획 TR-5를 TR-5a·b·c로 나누고 측정 card TR-M을 더했다 |
| X-T10 | TR-7 표본 수 식(§17)은 '반 LSB' 기준을 쓴다. 반(1/2)은 '최적 코드 선택의 잔여 = 간격/2'(계획 N3.4 잔여 판정)와 같은 정의에서 왔으나, 검증 기준으로 쓰는 것은 이 design의 선택이다(TD-5) |

---

## 19. 원문 근거

보관 위치와 쪽은 계획 N8 표(R1~R7)와 `skills/analog-gmid-design/assets/technique/sources/README.md` 그대로다. 이 design이 직접 쓰는 곳:

| R | 원문 | 쓰는 곳 |
|---|---|---|
| R4 | Bertotti et al. 2012, Adv. Radio Sci. 10:201-206 ([doi:10.5194/ars-10-201-2012](https://doi.org/10.5194/ars-10-201-2012)), 로컬 `assets/technique/sources/offset_trim__bertotti_2012/source.pdf` p.2 식(3), p.3 식(4)(5), p.4 Fig.3 | §9.4 σ_DNL 식, §7.3 차동 steering 셀, §3.5 σ_U |
| R2 | von Staudt 2011, IEEE IMS3TW ([doi:10.1109/IMS3TW.2011.34](https://doi.org/10.1109/IMS3TW.2011.34)), `offset_trim__staudt_2011/source.pdf` p.1-2 §II.A, p.2-3 §II.C·Table I, p.3-4 §III | §10.6 보정 구간 포함·잔여 Δ_max/2, 양의 DNL |
| R5 | Lu 2007, IEEE ICICDT, `offset_trim__lu_2007/source.pdf` p.2 식(9)(10) | §9.2 잡음 지표 방향, §10.5 공통 steering 전류의 부하 균형 |
| R1 | Mohamed 2013, SIECPC ([pure.kfupm.edu.sa](https://pure.kfupm.edu.sa/en/publications/input-offset-cancellation-trimming-technique-for-operational-ampl/)), `offset_trim__mohamed_2013/source.pdf` p.3 식(3) | §10.6 범위 조건 |
| R7 | Kay 2024, TI SBOA590 ([ti.com/lit/pdf/sboa590](https://www.ti.com/lit/pdf/sboa590)), `offset_trim__kay_2024/source.pdf` §1.2 p.7 | §10.8 보고 문구, §17 온도 한계 |
| R3 | Zhou·Kay 2017, TI SBOT037A ([ti.com/lit/SBOT037](https://www.ti.com/lit/SBOT037)), `offset_trim__zhou_2017/source.pdf` p.1·p.2 | §10.8 1/f·drift 문구 |
| R6 | Srinivasan et al. 2007, IEEE JSSC 42(2) ([doi:10.1109/JSSC.2006.889365](https://doi.org/10.1109/JSSC.2006.889365)), `offset_trim__srinivasan_2007/source.pdf` p.1 Fig.1 | §9.1 주입 쌍 = 입력쌍 drain |

원문 수치는 인용하지 않는다(계획 N0).
