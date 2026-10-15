---
template: design
version: 0.2
plan: ../../01-plan/features/offset-trim.plan.md
plan_version: 0.4
---

# offset-trim Design Document (card TR-0)

> **Summary**: 승인된 계획 `offset-trim.plan.md` v0.4(사용자 결정 T-1~T-6)를 엔진 `gmid_engine` 설계로 옮긴다. 계획 N7.3의 TR-0 닫을 항목 G-1~G-8과 TR-7 샘플 수 규칙을 닫고(§3, §17), 결정적 변환 `augment_trim`, `trim_decl`·승인 기록·결속, 1단계 후보·추천, 2단계 θ·유도·코드 상태·균형 풀이·제약·metric, 구조 역할 `trim_dac`, graph 필드 소유, 결과 JSON, 파일 분할, card 범위와 test 초안, 9회로 적용 판정을 정한다.
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code (design 작성자 역할)
> **Status**: design 초안 v0.2 (2026-10-15). v0.1 독립 검증 66/100의 차단 B1·B3·B4와 비차단 N1~N13을 반영했다. 같은 날 사용자 결정 T-7~T-13(TD-1 θ안 등)을 반영해 B2는 소멸, B5는 시험 회로(T-9)로 정리했다. 열린 사용자 값은 TD-3이다(TD-6은 T-14로 닫힘, §18.1). 재검증 82점의 차단 B6(I_u θ 키)과 M1~M6을 반영했고 TD-10·X-T15는 사용자 결정 T-15·T-16으로 닫혔다. 경위는 [offset-trim.design.history.md](offset-trim.design.history.md). 재검증·사용자 승인 전이다. 사용자 결정이 더 필요한 곳과 원래 취지와 다른 판단은 정하지 않고 §18에 모았다.
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
| T-7 | I_u를 θ 변수로. 범위·잔여 조건은 I_u 제약, 전력 최소화가 하한으로. 평가당 커널 1회(계획 D-16·X-3 변경) | §10.2·§10.3, X-T14 |
| T-8 | 예산 충돌 소멸, X-16·X-17 변경 없음 | §10.3 |
| T-9 | 2단계 검증용 시험 회로·spec을 따로(사용자 승인 전 쓰지 않음, library spec 무변경) | §16.1, §15 |
| T-10 | 꺼진 스위치 진성 용량 = LUT VGS 음수 축 추가(별도 card) | §3.1, TR-L |
| T-11 | structure.json 2개 재승인은 TR-4 착수 전 | §11 절차 |
| T-12 | TR-7 식 S + 검증자 조건 3개 채택 | §17 |
| T-13 | connectivity 표 도구를 새 엔진 로더로 이식 | TR-T |
| T-14 | 보고 전용 온도 sweep 범위 −40 ~ 80 °C | §17 |
| T-15 | TR-2 병합은 U16 뒤(TR-M·TR-1·TR-L 먼저 가능) | §15 |
| T-16 | X-T15 해석 확인: 재승인 결정은 TR-4 착수 전, `rule_hash` 갱신은 TR-4 병합 때 | §11 |

원문: `wt/_drafts/user_decisions.md` '## offset trim design 결정 (2026-10-15 사용자 "TD-1은 θ안, TD-8은 다로 해, TD2~TD7은 제안대로")'.

D-1(V_res = 최악 한계), D-2(k만), D-3(DNL 배수 = k), D-4(공존 거부), D-5(잡음은 보고만), D-6(t 변동 표시만), D-7(상보 쌍마다 DAC), D-8(단일 입력 정지), D-9(새 `bias_inputs` 항목), D-10(트랜지스터 스위치·전용 게이트 넷·`trim_decl` DC 값 벡터, on/off = 레일 전압), D-11(선언 회로·값은 사용자), D-12(trim 온도 = 합격 온도, 다르면 거부), D-13(원본 결속 + 구조 동일 검사 + 승인 fail-closed), D-14(비트 동일 범위), D-15(선택은 `trim_decl` 안), D-16(I_u 하한), D-17(+I_u 봉인).

### 1.2 원칙과 이 문서의 강제 장치

| 원칙 | 강제 장치 |
|---|---|
| topology 무관(NFR-T1, EP-1) | 주입 쌍은 S1 matching group·`metric_structure`·포트 역할로만 고른다(§9.1). 생성 이름은 고정 접두 + 정렬 번호(§7.2). 구조 규칙 E(회로 이름 리터럴)·D(숫자 리터럴)가 새 파일에도 걸린다. 9회로에서 선언 없음 = 무동작을 측정한다(TR-7) |
| 상수 발명 금지(NFR-T2, EP-4) | 모든 문턱은 spec(V_res·k), LUT(VDSAT·tol·축·온도), PDK(W_min), 엔진 분해능에서 유도(§10, §17). 반복 상한(균형 풀이 newton)은 `k_max`(`E/sizing/k_max.py`)로 |
| graph 단일 정본(NFR-T3, DEC-83) | 새 값은 모두 graph 필드이고 writer 하나(§12.1). 파생 topology는 S0 입력이고 실행마다 다시 만든다. 디스크 사본(§13)은 출력이다 |
| 계산값 재사용(40 §2.4.9 판정 1) | 새 계산은 모두 계산 블록이다(`Projection` 하나만 읽음, `donors`·`counters` 필수). 실행 안 같은 입력 재계산 0은 XRUN-F1 블록 결과 색인이 보장한다(§12.3) |
| 결정성(NFR-T4, NFR-4) | 변환·이름·코드 벡터·셀 순서는 정렬 규칙의 함수. I_u는 θ 성분이라 평가가 θ만의 함수(§10.3) |
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
| E-10 | 감쇠 Newton `newton_solve(nodes, values, evaluate, tolerance, width, devices=())`가 있다(LU, 역추적, 반복 상한 `k_max`, 실패 사유 `newton_*`, `devices`는 실패 기록에 붙일 소자 이름) | `E/sizing/scc_newton.py:1-17, :33` |
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
| KCL 기저 | 코드 상태가 주는 off 집합의 스위치 전류는 고정값 0인 기저 항이다(값 선언 이상원과 같은 `fixed` 경로). 전류 원뿔 행에서 빠진다('전도 MOS' = off 집합 밖). 셀 전류는 w_c × I(`trim<d>_c0_src`)(I_u = 가중치 1 셀 전류원의 θ 전류, §10.2)다 | E-1·E-2를 깨지 않고 0 전류를 표현하는 길은 전도 집합에서 빼는 것뿐이다 |
| 쓰기 계획 | off 소자는 어느 노드도 쓰지 않는다. 셀 공통 넷 X_c는 켜진 스위치가 쓴다 | 노드 writer 유일(봉인 5) |
| W·동작점(`dc_widths`) | off 소자는 LUT를 조회하지 않는다. W = 짝 스위치(같은 셀의 다른 쪽, 이 코드에서 켜짐)의 W, L = 짝의 L, ID = 0, `DeviceOp`에 off 표지. 짝 동일은 §7 생성 규칙이 보장하는 물리 사실이다(같은 셀 두 스위치는 같은 W·L로 그린다) | E-3 |
| 봉인 | 소자 전류·LUT 순방향 조회·관계를 보는 항목은 off 소자를 행으로 만들지 않는다: 봉인 1(노드 충돌 -- off 소자가 함의하는 관계 값 제외), 2(VGS 정합 -- 순방향 LUT), 3(KCL 잔차 -- off 전류는 정의상 0이라 항에서 뺀다), 7(포화), 8(`kvl_branch`), 9(전도 -- 이미 ID ≤ 0을 뺀다, E-4). 봉인 6(벌크 역바이어스)은 노드 전압만 보므로 off 소자도 그대로 검사한다. 봉인 4·5는 블록·writer 검사라 그대로다 | 정의되지 않는 조건을 판정하지 않는다(계획 N3.5). 봉인 번호는 `E/sizing/seal.py:7-8`과 각 `seal_*.py` 머리 |
| 소신호(`ss_dev`) | gm = gmb = gds = 0(전류 0의 채널), 접합 용량 cdb·csb = PDK 식(E-6, VGS 무관). **진성 용량 cgs·cgd·cgb는 지금 LUT VGS 축 밖이라, LUT에 VGS 음수 축을 추가해(사용자 결정 T-10, card TR-L) 그 축에서 조회한다.** TR-L 전에는 TR-5a를 시작하지 않는다 | E-5·E-6 |
| 잡음원 | off 소자는 채널 잡음원을 만들지 않는다(전류 0). LUT 잡음 조회를 하지 않는다 | 물리적으로 0이고 조회가 축 밖이다 |
| offset 수반 | off 소자의 σ_VGS는 조회하지 않고 기여 항을 0으로 둔다(항 = Z·gm·σ, gm = 0이라 σ 값과 무관하게 정확히 0). `sigma_missing` 검사는 off 표지 소자를 빼고 한다 | E-11 식 |
| 포화 검사(코드 상태 −1, ±end) | §10.5 균형 풀이 해에서 off 소자를 빼고 포화 여유를 잰다 | 계획 N3.5 |
| 켜진 스위치 영역 | 켜진 스위치는 gate가 on 레일이라 대개 triode다. 그래서 `trim_decl.dacs[*].triode_devices`(스위치 전부)를 봉인 7의 선형 영역 집합에 합친다. **경로**(검증 B4): `E/sizing/dc_inputs.py:37-38`이 spec `intended_region`에서 `linear_devices`를 만드는 자리에서 `trim_decl` triode 목록과 합집합(이름 정렬)을 만든다 -- `DcInputs.linear_devices` 하나가 정본이고 소비 경로(`kernel_run.py:82·88` → `seal_dc` → `dc_seal_saturation`, `metrics_aux`의 `linear_devices`)는 바뀌지 않는다. spec 선언과 trim 목록이 같은 소자를 담는 경우는 없다(trim 소자는 사용자 topology 원소가 아니고 spec `intended_region_device` 검사가 topology 밖 이름을 거부). `spec_regions.py`는 고치지 않는다(사용자 선언 어휘 그대로). 셀 전류원은 포화를 요구한다 | E-7. on 레벨 = 레일(D-10) |
| 스위치 게이트 DC 레벨(검증 B4) | 봉인 코드 상태의 스위치 게이트 넷 전압(on/off 레벨, §7.4)은 고정 노드다. **규칙**: `kernel_fields`(writer `kernel_context`, `E/sizing/kernel_fields.py`)가 extras로 봉인 상태의 `gate_levels`를 받아 `graph/kernel: fixed_values`에 합친다(쓰기 열은 그대로 `fixed_values` 하나 -- 새 열 없음). W3 목표·입력 DC와 같은 넷이 겹치면 `trim_fixed_net_conflict`(`ValueError` 아님, `SchemaRejectedError` -- 설정 충돌). 다른 코드 상태의 레벨은 `trim_code_states`가 `balance_solve` 고정 넷으로 직접 쓴다(§10.5, `fixed_values`에 넣지 않는다). DAC 바이어스 넷은 고정하지 않는다(셀 전류원 writer가 쓴다) | E-8 |

**바뀌는 엔진 지점**(TR-5a): `sizing/current_basis.py`(off 고정 0·셀 열 j ≥ 1을 w_j × c0 열로 치환), `sizing/theta_check.py`·`block_currents.py`(원뿔 = off 밖), 쓰기 계획, `block_widths.py`(off 경로), 봉인 3·7·8, `metrics` 소신호·잡음원·`device_sigmas`. off 집합은 블록 extras(코드 상태 = `trim_decl`의 값)로 들어가므로 입력 버전에 포함된다.

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
| 새 필드 N | **선언 없는 실행의 정의(검증 N3, 하나로 통일)**: 새 계산 블록(§12.1의 새 writer 전부)은 **아예 불리지 않는다** -- 스냅샷에 그 필드가 쓰이지 않고 `perf.blocks`에 그 행이 생기지 않으며 결과 JSON에 `trim` 키가 없다. 예외는 기존 writer에 열을 더한 둘뿐이다: `metrics_aux`의 `graph/metrics: offset_adjoint`(값 None), `kernel_fields`의 `fixed_values`(extras 없으면 기존 값 그대로 -- 값 부류라 비트 동일 비교 대상) | `offset_adjoint` 열 하나만 비교 집합 밖이고 **값 None을 단언**한다. 새 블록 행·`trim` 키·새 필드는 '없음'을 단언한다 |
| 시간 T | 40 §2.4.13 (2) T 부류 | 뺀다(기존 규칙) |
| 값 V | 그 밖의 모든 칸(노드 전압·소자 동작점·metric 값·제약 행·front·ε 기록·`perf` 계수·S3 줄 값 칸·단계 A·B 보고서의 값 칸) | **비트 동일** |

지문 부류를 뺀 뒤 값 부류가 비트 동일이면 완료 조건 (1) 통과다. 값 부류에서 한 칸이라도 다르면 FAIL이고 필드별 비교로 넘어가지 않는다. F2·F3를 빼는 것은 계획 D-14 문언('규칙 지문을 담는 모든 필드')보다 넓다 → §18.2 X-T5.

### 3.4 G-4 1단계 N 추천의 입력점과 순서

* **입력점: front 점마다 따로 계산한 뒤 front 위에서 함께 가능한 구성으로 모은다.**
  - 점 p마다 (t_p, σ_in,p, V_sys,s,p)로 가능 여부 가능_p(N, m)(§9.4)를 정한다.
  - 근거: 승인된 N·m은 2단계에서 front 전체에 고정값이다(N3.1-3). front 한 점에서만 가능한 구성은 다른 점에서 `trim_config_infeasible`가 된다. 점별 값은 표로 함께 낸다(D-6: 거르지 않고 표시).
* **집계 규칙(검증 N2 반영)**:
  1. 점마다 N_p = 가능_p(N, m)인 m이 있는 최소 N. 그런 N이 없으면(§9.4 종료 조건) 그 점은 '추천 불가 점'으로 목록에 내고 집계에서 뺀다.
  2. m_max,p(N) = 가능_p(N, m)인 가장 큰 m(0 ≤ m ≤ N − 1). **가능한 m이 하나도 없으면 m_max,p(N)은 정의되지 않는다**(값 없음, 0이 아니다).
  3. 추천 N = max_p N_p부터 1씩 올리며, 집계 대상 모든 점에서 m_max,p(N)이 정의되는 첫 N. 그 사이에 어떤 점이 그 N 이상 모든 N에서 불가능해지면(§9.4 종료 조건 = 그 N에서 W_u ≥ W_min 마디 없음) 그 점을 추천 불가 점으로 옮기고 다시 본다.
  4. 추천 m = min_p m_max,p(추천 N).
  5. 남는 점이 없으면 `trim_config_unrecommendable`.
* **순서: N 먼저, 그다음 m.** (N, m) 쌍 전수가 아니다(계획 N3.4 규칙: N = 어떤 m에서라도 성립하는 최소 정수, m = 그 N에서 성립하는 가장 큰 m).
  - m에 대해서는 같은 N·같은 σ_U에서 σ_DNL(m)이 m에 대해 증가하므로 가장 큰 가능한 m을 위에서부터 찾는다.
  - **N에 대한 단조성은 주장하지 않는다**(v0.1 문장 삭제): σ_U 최솟값을 고르는 마디 집합이 W_min 조건으로 N마다 달라져 가능 여부가 N에 대해 단조라는 보장이 없다. 그래서 위 3이 N을 하나씩 올리고, 종료는 §9.4의 W_min 조건으로만 한다.
  - test는 (N, m) 쌍 전수(N은 종료 조건까지) 결과에서 같은 규칙(가능한 최소 N, 그 N의 최대 m)을 뽑은 값과 대조한다(§15 TR-2).

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
| 분해(검증 N8) | 잔여 R(T) = V_os(T) + s·t(T)·δ(T)를 표본·온도마다 다음 세 몫으로 쓴다(δ₂₇ = 27 °C의 고정 코드 δ, t₂₇ = 27 °C t). (i) 원본 offset drift 몫 = **R(T) − s·δ₂₇·t(T)**(측정 잔여에서 '27 °C DAC 전류가 그 온도의 전달로 준 보정'을 뺀 값 -- 별도 재측정 없이 측정값에서 계산) 의 27 °C 대비 변화 (ii) DAC 전류 drift 몫 = s·(δ(T) − δ₂₇)·t(T) (iii) 전달 drift 몫 = s·δ₂₇·(t(T) − t₂₇). **닫힘 잔차** = (R(T) − R₂₇) − [(i) + (ii) + (iii)]를 함께 낸다. 정의상 0에 가까워야 하고, 크면 t(T)·δ(T) 측정(소신호 선형 근사)과 실제 DC 잔여가 어긋난다는 표지다(문턱은 두지 않고 값만 보고) |
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
  run_stage_b → build_search_context(파생) → find_front: 평가마다 kernel.evaluate(θ에 I_u 포함, 커널 1회)
     → trim_kernel.trim_point_blocks: 코드 상태 균형 풀이 → trim 값·제약·metric (§10.3a)
  불가능 → trim_config_infeasible 보고, 1단계로(엔진이 N·m을 바꾸지 않음)                   (N3.1-4)
```

* 단계 선택은 진입 인자로만 한다: spec에 `offset_trim` 섹션이 있고 `trim_approval_path`가 없으면 1단계, 있으면 2단계다. 섹션이 없는데 승인 경로가 오면 `trim_approval_without_decl`(`SchemaRejectedError`).
* 선언이 없으면 새 블록은 하나도 불리지 않는다(§3.3 N 부류 정의 -- 스냅샷 필드·`perf.blocks` 행·결과 `trim` 키 모두 없음).

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
N = 1, 2, … 순서로: 가능한 m이 있는 첫 N(= N_p). m_max(N) = 그 N에서 가능한 가장 큰 m(m = N−1부터 내려감), 없으면 정의 안 됨
종료: 어떤 N에서 W_u ≥ W_min 인 마디가 하나도 없으면 그 N과 이후 N은 불가능(I_lb(N)가 N에 대해 감소하고 W_u = I_lb·L/IDu가
      같은 마디에서 I_lb에 비례하므로 W_min 조건만은 N에 대해 단조) → 점 하나면 trim_config_unrecommendable, 집계는 §3.4
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

2단계 단계 A는 원본 S0와 파생 S0(봉인 코드 상태 = seal_plus)를 만든다. 원본 S0는 구조 동일 검사(§3.2)와 스키마 확장 검사(§10.2)에만 쓴다(S0 수준, 실행에 한 번). 둘 다 실행 수명이고 같은 블록 결과 색인·`RunCounters`를 쓴다(40 §2.4.5 '수명'). 원본 S0의 블록 입력은 1단계와 같은 topology라도 실행이 다르므로 다시 계산한다(실행 사이 재사용 없음, 40 §2.4.3).

**평가마다 원본 회로를 평가하지 않는다**: I_u가 θ(T-7)라 θ마다 원본 회로를 평가할 이유가 없다. 원본 회로 값이 필요한 곳은 S0 수준 비교(구조·스키마)뿐이다. '원본 대비 DAC가 더한 분산' 보고는 1단계 결과로 대신하고 2단계에서 다시 재지 않는다(이 비교는 서로 다른 θ 점의 값 비교다 -- X-T16).

**색인 상한**(검증 N4): 40 §2.4.5 식 'Σ 분할 수 × (E_total + 1)'의 +1은 S0 수준 계산 한 번이다. 2단계 trim 실행은 S0를 두 벌 계산하므로 같은 블록이 S0 수준에서 서로 다른 입력으로 두 번 계산된다. 그래서 trim 2단계 실행의 상한은 **Σ 분할 수 × (E_total + 2)**이다. `perf.block_index_bound`는 이 식으로 낸다(card C의 등록 시 fail-closed 검사도 이 식). 1단계·선언 없는 실행은 기존 식 그대로다.

### 10.2 θ와 정의역(사용자 결정 T-7, 검증 B1)

* 원본 성분: 원본 θ 스키마 성분 그대로(키 동일). **스키마 확장 성질**: 파생 스키마 ⊇ 원본 스키마이고 공통 키의 뜻이 같아야 한다. 단계 A가 두 스키마를 대조하고 어기면 `trim_schema_not_extension`(`StructureUnresolvedError`)으로 정지한다(TR-M이 미리 잰다).
* trim 성분(DAC마다 다섯):
  - **단위 전류 I_u**(검증 B6): θ 전류 키는 **가중치 1 셀 전류원 `trim<d>_c0_src`의 전류**다(회로 원소 이름이라 as-built 경로 -- `block_currents.py:28`의 `basis.free` 대조, `search_domain.py:62` `_current_bounds`의 `classes[key]` = MOS, 자기 행 θ_I > 0 하한 -- 를 그대로 탄다). 나머지 셀 j의 전류는 KCL 기저에서 w_j × I(`trim<d>_c0_src`)로 묶는다: `sizing/current_basis.py`가 `trim_decl`의 셀 가중치를 extras로 받아 기약 행사다리꼴 **전에** 셀 전류 열 j ≥ 1을 w_j·(c0 열)로 치환한다. 그래서 trim 셀 전류 열은 c0 하나만 남고 자유 열이 된다(주입 넷으로 들어가는 새 가지라 원본 자유 열은 그대로 -- 스키마 확장 성질, TR-M이 잰다). m = 0이면 c0은 thermometer 셀 하나(가중치 2^0 = 1)다. 켜진 스위치 전류 = 그 셀 전류(직렬), 꺼진 스위치 = 0(§3.1).
  - 셀 전류원 묶음의 ln IDu 하나·L 하나: gate·source 공유라 LR1 L 동치류와 equal_vgs로 이미 하나로 묶인다(writer 하나, 나머지 순방향).
  - 켜진 스위치 묶음의 ln IDu 하나·L 하나: 게이트 넷이 서로 달라 구조 규칙으로 묶이지 않으므로 `trim_decl`의 셀 표에서 '스위치 묶음'을 선언 묶음으로 넘긴다(`search/trim_ties.py`, 묶음 확장은 기존 궤도 묶음 `tie_expand`와 같은 형식). 계획 N3.4 θ 행 '단위 셀 gm/ID·L만'을 셀의 두 소자 종류로 읽은 것이다(§18.2 X-T2).
  - 켜진 스위치 ln IDu 상자 가운데 gate = on 레일 고정에서 실현할 수 없는 부분의 비율을 TR-M·TR-5a에서 잰다(검증 N12). 실현 불가 점은 평가에서 쓰기 계획 근 없음(기존 후보 실패)이 된다.
* θ 상자: ln IDu는 kind별 LUT 포락선, L은 PDK 칸(E-18). I_u(= c0 전류) 상자는 as-built `_current_bounds`의 MOS 원소 규칙(셀 kind `current_box`)에 **w 계수 교집합**을 더한다: 상자 = ∩_j (셀 kind 상자 / w_j)(가중치가 가장 큰 셀이 상한을 정한다). 비면 `tied_current_box_empty`(기존 사유)로 거부한다. 이것이 `search_domain.py`의 새 작업이다.

**정의역**: 봉인 코드(δ = +I_u)에서 주입 넷 KCL에 DAC 전류 s·I_A, s·I_B(I_A = 2^(N−1)·I_u, I_B = (2^(N−1) − 1)·I_u)가 들어가 원본 MOS 전류의 기저 식에 I_u 항이 생긴다. I_u가 θ 전류 성분이므로 이 항도 θ의 선형 항이다. 그래서 정의역 = as-built 그대로 'θ 전류 원뿔(모든 전도 MOS 행 > 0)'이고 θ만의 선형 부등식이다. 셀 전류원 행 = w_c·I_u > 0, 켜진 스위치 행도 같고, 꺼진 스위치는 행이 없다(§3.1).

| 원뿔을 쓰는 자리 | 처리 |
|---|---|
| `sizing/theta_check.py:48-53`, `block_currents.py:32-34` | 변경 없음(원뿔 행에 off 스위치가 없는 것만 §3.1) |
| search 자리 `cone_rows.py:21`, `layer0_center.py:155-191·549`, `fd_jacobian.py:49`, `gate_run.py:41` | 변경 없음: 원뿔 행의 항 원천이 원소 `trim<d>_c0_src`(θ 전류 키)라 기존 코드가 그대로 다룬다 |
| `search_domain.py:62-64` `_current_bounds`·묶음 구성(`:144-173`) | **변경**: c0 상자의 w 계수 교집합(위), trim 스위치 묶음을 궤도 묶음과 합침(아래 '묶음과 기존 tie 기제') |
| 원뿔 밖 | as-built 그대로: search가 커널 전에 `STATUS_OUTSIDE_DOMAIN`(커널 0)으로 거른다. 커널 안 `check_theta` `ValueError`는 search가 걸렀으므로 생기지 않는다(생기면 결함) |

**묶음과 기존 tie 기제**(검증 B6, grep 2026-10-15: `search/orbit_ties.py:28-51`, `search/current_symmetry.py:1-25·129`, `search/search_domain.py:144-173`, `search/tie_expand.py:9`):
* 셀 전류: 묶음은 KCL 기저 안(위 치환)에서 끝나므로 θ 전류 묶음(`current_symmetry`의 `ties`·`negated`·`zeros`)과 겹치지 않는다. 셀 j ≥ 1 전류는 자유 열이 아니라 대칭 연립의 변수가 아니다. 같은 가중치 thermometer 셀 전류원끼리 자기동형 궤도가 같아도 전류는 이미 같은 식(w·c0)이라 대칭 관계가 새 묶음을 만들지 않는다.
* ln IDu·L: 파생 topology는 A·B 대칭이라 `orbit_ties`가 같은 셀의 `_swa`·`_swb`와 같은 가중치 thermometer 셀끼리의 스위치·전류원을 궤도로 이미 묶는다(같은 kind·같은 궤도). 가중치가 다른 이진 셀은 궤도가 달라 묶이지 않으므로 `trim_ties`(스위치 묶음, 셀 전류원은 LR1·equal_vgs로 이미 하나)가 필요하다. **합치는 규칙**: `search_domain`이 `orbit_ties` 결과와 `trim_ties`를 같은 성분 위 합집합-찾기로 합쳐 묶음 하나로 만들고, 대표 = 묶음 안 구조 색 `dc_colour` 최소(기존 대표 규칙 그대로). 궤도를 넘는 ln IDu·L 묶음은 지금 없던 경우인데, 묶음 안 상자가 모두 같은 kind의 LUT 포락선·같은 PDK 칸이라 `tied_orbit_bounds_differ`가 생기지 않는다(다르면 그 사유로 거부 -- 기존 검사 재사용). 봉인 상태에서 꺼진 스위치는 ln IDu 성분이 없으므로 묶음에 들어오지 않는다.
* `untie_orbits`(spec)는 trim 소자 이름을 받을 수 없다(사용자 topology 원소가 아니므로 `untie_element_unknown`) -- trim 묶음은 풀지 않는다.


### 10.3 I_u의 결정(사용자 결정 T-7, T-8)

* I_u는 탐색 변수다. 보정 구간 조건 `trim_range`(§10.6)가 I_u의 **하한 제약**, 잔여 조건 `trim_residual`이 I_u의 **상한 제약**으로 작용한다(Δ_max/2 = \|t\|·I_u·(1 + k·σ_DNL)가 I_u에 비례).
* 목적 축(전력, 면적)은 둘 다 I_u에 대해 증가한다(전력: I_T·레일 폭, 면적: 같은 ln IDu에서 W ∝ I). 그래서 front 점은 보정 구간 하한 쪽으로 밀린다. 계획 D-16 '하한(전력 최소)'의 효과를 제약 + 목적으로 얻는다.
* `i_lower_amp`(§10.4)는 판정 점에서 잰 하한 (k·σ_in + \|V_sys0\|)/(\|t\|·(2^N − 1))이고 보고만 한다. V_sys0 = V_sys,s(seal) − s·t·I_u(봉인 점 V_sys,s에 든 DAC 자신의 δ = +I_u 몫, 입력 환산 반 LSB를 뺀 δ = 0 기준 계통 offset, §0 V_in(c) = −(V_sys0 + s·t·δ(c))에서 c = seal을 넣은 것 -- 검증 N1의 정의는 그대로 쓴다).
* **평가 단위·예산**(T-8): θ 하나 = 커널 평가 1회(`perf.kernel_calls` 1 증가, `E/search/kernel.py:114` 그대로). 그래서 card C 예산 규칙(E_total = E_B + N_T + R, X-16·X-17, `search_ceiling`·`search_stop`·FD 묶음 상계 = 열 수 × 2)이 **변경 없이** 적용되고 검증 B2의 예산 충돌은 사라진다. as-built 불변식 '`kernel_calls` == 고유 키 수'(`E/search/find_front.py:15`)도 그대로다. `perf.trim_kernel_passes` 칸은 만들지 않는다.

### 10.3a 커널과 trim 블록의 호출 방향(검증 B3)

* 평가 진입은 지금처럼 `kernel.evaluate`(`E/search/kernel.py:91`) 하나다. search 호출자(층 0, 외층, FD, 감도 게이트, 시작점)는 바뀌지 않는다(NFR-4 관찰 지점 계약 유지).
* `kernel.evaluate` 본체가 봉인·metric 뒤 trim 선언 실행에서만 `trim_kernel.trim_point_blocks(snapshot, ...)`(`E/search/trim_kernel.py`, search 층)를 부른다. 이 함수는 `trim_code_states`(sizing)·`trim_dac_values`(metrics) 블록을 부르고 제약 행 함수 `trim_constraint_rows`가 읽을 필드를 채운다. `trim_kernel.py`는 `kernel.py`를 import하지 않는다 → 순환·재귀 없음. 방향: `kernel.evaluate` → `trim_kernel.trim_point_blocks` → sizing·metrics 블록.
* 1단계 후보: `run_trim_candidates`(pipeline, `E/pipeline/trim_stage1.py`)가 `find_front`(search) 결과를 받아 front 점마다 `trim_candidates` 블록(metrics)을 부른다. **방향 pipeline → search·metrics**. `find_front`는 trim을 모른다.

### 10.4 판정 점의 trim 값 `trim_dac_values`(S2 블록)

판정 점 스냅샷에서 계산해 `graph/trim: dac`(DAC마다 `TrimDacValues`)에 쓴다.

| 칸 | 정의 |
|---|---|
| `i_unit_amp`, `i_total_amp`, `i_lsb_amp` | I_u(그 점의 θ 성분 값), I_T = (2^N − 1)·I_u, I_LSB = 2·I_u |
| `i_lower_amp` | 그 점에서 잰 하한 (k·σ_in + \|V_sys0\|)/(\|t\|(2^N − 1)), 보고만(§10.3). 판정은 제약 `trim_range` |
| `t_v_per_amp`, `effective_sign` | §9.2와 같은 정의(파생 회로 봉인 점) |
| `sigma_unit_rel` | σ_U(G-5 2단계) |
| `sigma_dnl_lsb` | σ_DNL(m) |
| `lsb_in_v` | \|t\|·I_LSB |
| `range_linear_v` | (−V_sys,s − \|t\|·I_T, −V_sys,s + \|t\|·I_T) |
| `residual_bound_v` | Δ_max/2 = \|t\|·I_u·(1 + k·σ_DNL(m)) |
| `thermo_sigma_ratio` | §3.5 일치 확인 비 |

### 10.5 코드 상태 균형 풀이 `trim_code_states`(S2 블록, 분할 = 코드 상태)

봉인 점 스냅샷에서 상태 `minus`, `end_plus`, `end_minus`마다(분할 key = 상태 이름, 40 §2.4.4 분할 -- 상태끼리 서로 읽지 않으므로 독립 분할):

* **풀이 `balance_solve`**(`sizing/fixed_geometry_dc.py`, 순수 함수): **고정 기하 DC**. 모든 켜진 MOS의 W·L = 봉인 점 값(off 소자 제외 -- 그 상태의 off 집합).
  - 고정 넷: 레일, gate 전용 넷(봉인 점 전압, 스위치 게이트는 그 상태의 on/off 레벨), 입력 포트 = 입력 공통모드(봉인 점 입력 DC) ± V_id/2, 값 선언 이상 전류원.
  - 미지수: 나머지 넷 전압 + V_id.
  - 방정식: 미지 넷마다 KCL(순방향 LUT 전류 IDu·W/L의 합 = 0) + 출력 균형 1개(§3.6: 차동 V(out_p) − V(out_n) = 0, 단일 V(out) = 기준).
  - 풀이: `newton_solve(nodes, values, evaluate, tolerance, width, devices=켜진 MOS 이름 tuple)`(E-10). 야코비안 = LUT gm·gds·gmb(순방향 조회 한 번에 함께). 시작점 = 봉인 점 전압 + V_id 선형 예측 −(V_sys,s + s·t·δ(c)). 허용오차: 넷 KCL 잔차 ≤ 그 넷에 닿은 소자 tol_I 합(봉인 3과 같은 양), 노드 걸음 ≤ 그 넷 tol_V. 폭 = 레일 전위 폭. 상수 없음.
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
| `trim_power_w` | w | dc | I_T·(V(R_max) − V(R_min))(검증 N9: steering 총전류는 코드와 무관하게 두 극단 레일 사이를 흐른다 -- 주입 넷을 거쳐 원본 회로 쪽 레일로 돌아가는 몫도 결국 두 레일 사이 전류다) | 보고(`power_dc_w`에 이미 포함). 한계: 레일이 셋 이상인 회로(nmcnr처럼 중간 레일이 있음)에서 DAC 전류가 주입 넷을 거쳐 중간 레일로 돌아가면 실제 전력은 이 값보다 작다 -- 정확한 값은 `power_dc_w`의 레일별 공급 전류다 |
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
* **규칙 지문**: `s1_trim_roles.py`는 S1 규칙 파일(`S1_RULE_FILES`)에, S1v 쪽 변경 파일은 이미 `S1V_RULE_FILES`에 있다. 그래서 `structure_rule_fp()`가 바뀌고 structure.json 2개(current_reuse_telescopic_ota, nmcnr_amplifier)가 stale이 된다(계획 N3.3·N9).
* **재승인 절차**(사용자 결정 T-11: 재승인은 TR-4 착수 전):
  1. TR-4 착수 전: 오케스트레이터가 두 파일의 사실 목록(concept·subject·value·approval_id)과 '사실 내용은 바꾸지 않고 `rule_hash`만 새 `structure_rule_fp()`로 갱신, approval_id 그대로'라는 재승인 안을 사용자에게 올리고 승인을 받는다. 이 승인이 TR-4 착수 조건이다. override 사실(current_reuse `ac_ground_exception` Vbias2, nmcnr `l_owner`)도 이 승인으로 다시 확인받는다(40 §3.2-3 'override 사실은 사용자가 다시 확인').
  2. TR-4 구현 안: 새 `rule_hash` 값은 규칙 파일이 바뀐 코드에서만 계산되므로(40 §3.2-3 '작성 순서: 사실 파일은 코드 병합 뒤에 쓴다'), 같은 TR-4 병합에서 오케스트레이터가 새 코드의 유도 결과가 confirm 사실과 전부 같음을 보인 대조 기록을 남기고 `rule_hash`만 고쳐 쓴다.
  3. 병합 조건: 두 파일 단계 A에서 `structure_fact_stale` 0, 갱신 전과 같은 적용 사실(Vbias2 판정·`l_owner_name_order` review 없음) 확인. 다르면 갱신하지 않고 사용자에게 다시 올린다.

---

## 12. graph 필드·계산 블록·재사용 정합

### 12.1 필드 소유표(새 필드 전부)

| 필드(kind/key: field) | 값 형식 | writer(계산 블록, 파일) | 층 | 선언 없을 때 |
|---|---|---|---|---|
| `device: trim_role` | `TrimRole` \| None | `s1_trim_roles`(`graph/s1_trim_roles.py`) | S0 | 블록 안 불림(필드 없음) |
| `graph/trim: pairs` | `TrimPair` tuple | `trim_pairs`(`metrics/trim_pairs.py`) | S0 | 블록 안 불림(필드 없음) |
| `graph/trim: structure_diff` | `TrimStructureDiff` | `compare_trim_structure` 호출 결과를 단계 A가 보고서에 싣는다 -- graph 필드 아님(두 S0의 비교 출력, 판정은 정지) | -- | -- |
| `graph/metrics: offset_adjoint` | (view id, A_dm, ((넷, z), …)) \| None | `metrics_aux`(기존 writer, 쓰기 열 추가) | S2 | None |
| `graph/trim: candidates` | `TrimCandidate` tuple | `trim_candidates`(`metrics/trim_candidates.py`) | S2(1단계 front 점) | 블록 안 불림(필드 없음) |
| `graph/trim: dac` | `TrimDacValues` tuple | `trim_dac_values`(`metrics/trim_dac_values.py`) | S2(2단계 판정 점) | 블록 안 불림(필드 없음) |
| `graph/trim: code_states` | `CodeStateSolution` tuple(분할 = 상태) | `trim_code_states`(`sizing/trim_code_states.py`) | S2 | 블록 안 불림(필드 없음) |
| `graph/trim: range` | `TrimRange` | `trim_dac_values`가 code_states를 읽어 같이 쓴다 | S2 | 블록 안 불림(필드 없음) |
| `graph/kernel: trim_ties` | 스위치 묶음 | 새 블록 `trim_ties`(`search/trim_ties.py` 진입점 `trim_theta_ties`를 블록으로) -- v0.1의 '`kernel_fields` 열 추가'는 선언 없는 실행에 빈 필드가 생겨 N3 정의와 어긋나 바꿨다 | S0 | 블록 안 불림(필드 없음) |
| `graph/kernel: fixed_values`(기존 필드, 값 확장) | 기존 (넷, V) + 봉인 상태 스위치 게이트 레벨 | `kernel_fields`(기존 writer, 같은 열, extras `gate_levels` 추가) | S0 | 기존 값 그대로(extras 없음) |
| 제약 행 trim 3종 | 기존 제약 행 형식 | 기존 search 제약 블록(행 생성 함수 `trim_constraint_rows` 추가) | S2 | 행 생성 함수 안 불림(행 없음) |

* `offset_adjoint`는 `offset_analysis`가 이미 계산한 z(E-11)를 그대로 담는다(같은 LU, 재계산 없음). `OffsetAnalysis` 값 형식은 바꾸지 않는다(바꾸면 선언 없는 실행의 `metrics_aux` 값이 바뀌어 §3.3 V 부류를 깬다).
* 출처 기록 `TrimProvenance`와 `TrimDecl`은 S0 입력(graph 밖, spec과 같은 지위)이다. 둘의 지문이 쓰는 블록의 입력 버전에 들어간다.
* front 위 집계(G-4 추천 N·m, 순위)는 front 점 스냅샷 필드를 읽어 만드는 **출력**이고 graph 필드가 아니다(설계 값의 새 정본을 만들지 않는다).

### 12.2 계산 블록 규칙

* 새 블록은 모두 `compute_block`이고 `Projection` 하나만 읽는다. I_u는 θ 성분이라 투영(θ extras) 안에 있다 -- 블록이 parent·이전 회차 값을 읽지 않는다(40 §2.4.4 '이식이 비트 동일인 전제').
* `trim_code_states`의 newton 시작점은 봉인 점 스냅샷(투영 안)의 함수다.
* `metrics_aux`는 `offset_adjoint` 열을 늘 쓰지만 값을 채우는 것은 trim 선언(extras 플래그)이 있을 때만이고, 없으면 None이다(§3.3 N 부류의 유일한 예외 열).

### 12.3 실행 안 재사용(XRUN-F1 정합)

* 원본 S0·파생 S0의 블록은 각자 한 번 계산된다(`computes` = 1, 판정 1).
* θ 하나 = 커널 평가 1회라 평가 캐시·블록 결과 색인 규칙이 as-built 그대로 적용된다. FD 열에서 trim 성분 하나만 움직이면 원본 성분만 읽는 S0 수준 블록은 색인 적중이다.
* `test_g10_no_recompute_9circuits`에 trim 선언 픽스처 회로를 하나 더해 판정 1·5를 단언한다(TR-5).

### 12.4 XRUN-F1·NFR-4 card 2와의 정합 점검

| 항목 | 정합 |
|---|---|
| 블록 호출 `donors`·`counters` 필수(40 §2.4.4) | 새 블록 전부 같은 호출 경로 |
| 블록 결과 색인 수명 = 실행(단계 A부터) | 원본·파생 S0 블록 포함, 실행 하나 |
| E_total(40 §2.4.9), `search_ceiling`·`search_stop`(card C) | 변경 없음: θ 하나 = 커널 1회(§10.3, 사용자 결정 T-8) |
| 결정적 도메인 실패 등록·재연(X-9) | `trim_balance_*`·newton 실패는 `InfeasibleSizingError` 하위로 만들어 등록 대상 |
| `ThetaCoords`(card A) | trim θ 성분도 같은 정본으로 좌표 변환(새 사본 금지) |
| BLAS 고정·`env_fp`(NFR-4 card 2) | 새 선형 풀이(newton LU)는 scipy `lu_factor`(실수, 엔진 크기) -- 40 §2.4.13 표 '실수 lu' 묶음에 자리를 더한다(TR-5에서 표 갱신) |
| 관찰 지점 계약(J-3·J-7·J-16) | `find_front`·`layer0_center`의 모듈 전역 호출 방식 유지. `kernel.evaluate`가 `trim_kernel`을 콜백으로 부르는 한 방향이고(§10.3a) 호출자 쪽 이름·호출 방식은 바꾸지 않는다 |
| 결과 JSON 형식 변경 | §13 새 칸만 더한다. 기존 칸의 뜻은 그대로 |

---

## 13. 결과 JSON 칸

| 위치 | 칸 | 내용 |
|---|---|---|
| 단계 A 보고서 | `trim` | `{mode: "stage1"\|"stage2", spec: TrimSpec 값, pairs, temperature: {declared_c, lut_temp_c, lut_corner}, demoted_constraints, structure_diff(2단계), approval: {approval_id, path, binding_checks[]}, provenance(2단계)}` |
| `find_front` 결과(runs 줄) | `trim.stage1` | front 점마다 후보표(§9.2), 순위(§9.3), 추천 (N, m)과 점별 (N_p, m_p), `t_varies` 표지, 추천 불가 점, 출력 파일 경로·sha256(파생 topology·md·승인 초안), 사유 코드 |
| 〃 | `trim.stage2` | front 점마다 `trim/dac`·`trim/range`·`code_states` 요약, 그 점의 I_u(θ 성분)·`i_lower_amp`, 불가능이면 `trim_config_infeasible`과 위반 경계(하한 > 상한의 두 값) |
| 〃 | `trim.reports` | §10.8 보고 문구 목록, D-3 한계, 단일 온도 한계(FR-T9) |

선언 없는 실행에서는 `trim` 키 자체가 없다(I_u는 θ라 S3 줄 θ 칸에 이미 있다)(§3.3 N 부류 -- '없음' 단언).

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
| `search/trim_ties.py` | `trim_theta_ties`(블록, writes `graph/kernel: trim_ties`, 선언 실행에서만 `build_search_context`가 부른다) | search | TR-5a |
| `search/trim_kernel.py` | `trim_point_blocks(snapshot, ...)`(`kernel.evaluate` 본체가 부른다, `kernel.py`를 import하지 않는다 -- §10.3a) | search | TR-5b |
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
| `sizing/current_basis.py`(off 고정 0·셀 전류 항), `block_currents.py`, 쓰기 계획(`writer_plan.py`), `block_widths.py`, 봉인 1·2·3·7·8 파일 | TR-5a | 부분 |
| `sizing/kernel_fields.py`(extras `gate_levels` → `fixed_values` 합침, 충돌 거부 -- B4) | TR-5a | 부분 |
| `sizing/dc_inputs.py:37-38`(`linear_devices` = spec triode ∪ `trim_decl` triode 목록 -- B4) | TR-5a | 부분 |
| B1·B6 정의역(T-7 θ안): `sizing/current_basis.py`(extras 셀 가중치, 기약 행사다리꼴 전 셀 열 j ≥ 1 → w_j × `trim<d>_c0_src` 열 치환), `search/search_domain.py`(`_current_bounds` c0 상자 w 계수 교집합 `:62-64`, 묶음 구성 `:144-173`에서 `orbit_ties` 결과와 `trim_ties` 합집합-찾기 합침). `search/orbit_ties.py`·`current_symmetry.py`·`tie_expand.py`·search 원뿔 네 자리·`theta_check.py`는 변경 없음 | TR-5a | 부분 |
| `sizing/theta_schema.py`(trim 성분) | TR-5a | 부분 |
| `metrics/ss_linearize.py`·`noise_sources.py`·`device_sigma.py`(off 소자) | TR-5a | 부분 |
| `metrics/registry.py`·`verified_by.py`·`catalog.py`(trim metric) | TR-5b | 부분 |
| `search/kernel.py`(본체에서 `trim_point_blocks` 호출만), `search/find_front.py`(결과 칸) | TR-5b | 부분 |
| 색인 상한 +2(검증 M5): `search/s3_index.py`(card C 등록 검사의 상한 식이 S0 벌 수를 인자로 받음 -- 2단계 trim 실행 2, 그 밖 1), `search/search_context.py`(그 값을 단계 A 결과의 S0 벌 수에서 넘김), `search/find_front.py`(`perf.block_index_bound` 같은 식) | TR-5b | 부분 |
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
| `trim_point_blocks` | `kernel.evaluate`(`E/search/kernel.py`) 본체가 trim 선언 실행에서만 부른다(§10.3a) |
| `trim_dac_values`·`trim_code_states`·`balance_solve`·`trim_constraint_rows` | `trim_kernel`의 판정 점 처리 / search 제약 블록 |
| `run_trim_candidates` | 1단계 진입: 파이프라인(지금은 `pipeline/trim_stage1.py` 진입을 부르는 실행 스크립트·test, U16 뒤 `run_gmid_design_pipeline`)이 `find_front` 결과를 넘겨 부른다. 방향 pipeline → search·metrics, `find_front`는 trim을 모른다(검증 B3) |

---

## 15. card 범위·완료 조건·test 초안

공통: 순서 = design 승인 → test(interface card만 보고) → code → 독립 판정. 각 card 완료 조건에 (a) 배선 증거(§14.4 행의 호출 grep + 실행 경로 test), (b) 상위 N6.3 graph 정본·재계산 계수·파일 분할 확인, (c) design 대 구현 gap 분석을 넣는다. test 기대값은 피검 함수를 부르지 않는다.

| card | 범위 | 선행 | 완료 조건 | test 초안(독립 oracle) |
|---|---|---|---|---|
| **TR-M** 측정(엔진 코드 무변경) | G-2 표(§3.2)와 G-1 측정 항목(§3.1)·스키마 확장 성질(§10.2)을 9회로 후보 7회로 × 쌍 × 극성에서 잰다. 파생 topology는 측정 스크립트가 §7 규칙을 **독립 구현**해 만든다(구성 둘: 이진·thermometer 셀을 모두 갖는 최소 구성 N = 2, m = 1과, thermometer 셀이 여럿인 구성 N = 3, m = 1 -- 검증 N10). 결과 기록 `.ai/verification/trim/tr_m.json`. 켜진 스위치 ln IDu θ 상자의 실현 불가 비율(§10.2, 검증 N12)도 잰다. **방법(엔진 무변경, 재검증 M4)**: 스크립트가 LUT npz를 직접 읽는다. 원본 회로 1단계 front 점(또는 TR-M 시점의 원본 탐색 front 점)의 주입 넷 전압 V(n)을 그대로 두고, gate = on 레일(극성별)·source = 셀 공통 넷이 V(n) − VDS(sink) 범위를 움직일 때 LUT 격자의 (L, VDS, VSB) 마디마다 VGS = V_on − V_X가 축 안이고 그 마디 ln IDu가 kind 상자 안인지 센다. 비율 = 상자 격자 마디 가운데 어떤 V_X로도 닿지 않는 마디 수 / 전체 마디 수, 회로·쌍·극성별. **작성자 조건(검증 N11)**: 이 스크립트의 작성자는 TR-3 `augment_trim` 구현자와 다른 agent여야 한다(같은 규칙의 독립 구현이 TR-3 test oracle이 되기 때문) | design 승인 | 비교 행 차이 목록, DC 역할·셀 분류(trim 소자), KCL 기저 풀림 여부, 원본 θ 키 보존 여부가 회로별로 있다. 차이가 있으면 TR-4 design 보완 전 사용자 보고 | 스크립트 자체가 TR-3 `augment_trim` test의 독립 oracle이 된다(같은 규칙의 다른 구현) |
| **TR-1** spec·승인·합성 | §5 전부, §6, §8.1·§8.2, 승인 로더, 온도 대조 | TR-0 승인, T-4 순서 | 섹션 검사·거부 사유 전수, D-4 공존 처리, 온도 대조 거부가 실제로 거부함, 선언 없는 spec 로드 결과 비트 동일 | 형식 위반 픽스처마다 사유 코드 / `offset_in_sigma_mv`와 공존 거부 / `offset_excess` 강등 / 온도 ≠ LUT `temp_c` 거부(LUT 메타를 test가 직접 읽음) / 셀 표·코드 벡터: test가 손으로 쓴 N = 3, m = 1·N = 2, m = 0 표와 대조(§7.4 검산식) / `trim_rule_fp` 파일 바이트 변경 시 변함 |
| **TR-2** z·쌍·후보·추천(보고만) | §9.1~§9.4, `offset_adjoint` 쓰기, 결과 JSON `trim.stage1` 표(파생 topology 제외) | TR-1, TR-M. **병합 조건: U16(파이프라인 배선) 병합 뒤**(사용자 결정 T-15 -- `run_trim_candidates`를 제품 경로에서 부르기 위해. 착수·test 작성은 먼저 해도 된다) | 7회로 후보표, 사유 코드 9회로(§16), 선언 없는 실행 무동작(§3.3) | t: 작은 손 회로(저항 + 이상 전류원 + 선형 MOS 소신호)에서 손으로 푼 z와 대조 / `dnl_sigma`: 단위 셀 전수 합으로 독립 계산한 최악 전이 분산과 대조 / `recommend_trim_config`: (N, m) 쌍 전수 결과와 순서 규칙 결과 일치, W_min 종료 / 쌍 규칙: matching group 손 픽스처 |
| **TR-3** 변환·출처·결속·출력 | §7, §8.3(1~5), §9.5, `topology_from_data` | TR-2 | 파생 topology가 로드 게이트 통과, 결정성(두 번 비트 동일), 이름 충돌 거부, 승인 stale 다섯 경로 각각 정지, 1단계 출력 파일 | TR-M 독립 구현과 소자·넷·`bias_inputs` 비교 / 입력 dict 순서 섞기 → 같은 출력 / 결속 경로마다 지문 하나만 바꾼 픽스처 → 해당 detail로 정지 |
| **TR-4** 역할·구조 검사 | §11, §3.2 검사(§8.3-6), structure.json 재승인 | TR-3, **착수 조건: structure.json 2개(current_reuse_telescopic_ota, nmcnr_amplifier) 재승인 완료**(사용자 결정 T-11, 절차 §11) | 9회로에서 trim 소자 셀 종류 `off`·블록 역할 없음, 구조 검사 통과(TR-M 차이 0 회로), 차이 주입 픽스처에서 정지. **병합 조건: structure.json 2개 재승인 완료** | 손 회로: trim 소자가 신호 도달에서 빠짐 / 부하 역할 집합에 trim 소자 없음 / 원본 matching group에 trim 소자를 섞은 픽스처 → `trim_structure_divergent` |
| **TR-5a** 전류 0 소자·trim 전류 | §3.1 sizing·metrics 경로(꺼진 스위치 진성 용량은 TR-L의 VGS 음수 축 LUT로), I_u θ 성분과 셀 전류 묶음, 스위치 묶음, 스키마 확장 검사 | TR-4, **TR-L**(T-10) | 봉인 상태 파생 회로가 봉인 1~9 통과(시험 회로, T-9), off 소자 DC·잡음·σ LUT 조회 0(조회 계측), off 소자 진성 용량은 VGS 음수 축 조회, 선언 없는 실행 비트 동일 | off 소자: W = 짝 W, 소신호 gm = 0, 잡음원 없음, σ 항 0, 진성 용량 = TR-L 축의 LUT 값(test가 LUT 배열을 직접 읽어 대조) / 원뿔: off 스위치 행 없음, I_u 항이 원본 MOS 행에 θ 선형으로 들어감 / KCL: 손으로 푼 셀 전류 = w_c·I_u |
| **TR-5b** DAC 값·제약·metric | §10.3, §10.3a, §10.4, §10.6, §10.7 | TR-5a, **시험 회로 승인**(T-9, §16.1) | **시험 회로**에서 2단계 front 생성, θ 하나 = 커널 1회(`kernel_calls` == 고유 키 수), 판정 1·5(재계산 0), card C 예산 규칙 그대로 동작, 결과 JSON `trim.stage2`, front 점에서 `trim_range` 활성(전력·면적이 I_u를 하한으로 미는지) 보고 | 제약 행 c 부호: 손 계산 / I_u 상자 = w_c로 나눈 셀 상자 ∩ 원천 행 상자(손 계산) / `trim_point_blocks`는 선언 없는 실행에서 불리지 않음 |
| **TR-5c** 코드 상태 균형 풀이 | §10.5 | TR-5b | **시험 회로**에서 세 상태 풀이 수렴, 포화 행에서 off·triode 제외, 실패 사유 | 오라클: 같은 고정 기하에서 SPICE `.op` + 입력 차 sweep으로 V_in 대조(오라클 측 독립, 허용폭 = 노드 tol 전파) / 선형 예측과의 차 보고 |
| **TR-6** 의미 전환 | §10.8 | TR-5c | `iv_matching_l` 하한 꺼짐(선언 시), 보고 문구, 선언 없는 실행 비트 동일 | 선언 유무 두 spec에서 출발값 차이가 L 하한 행에만 있음 |
| **TR-7** 검증 | §17 전부(식 S + 검증자 조건 셋, T-12), 9회로 일반성(§16), 오라클 확장(레인 P: 코드 입력·표본별 코드 선택·온도), `verified_by` 붙이기 | TR-6, 오라클 확장, **시험 회로 승인**(T-9), 온도 sweep 범위 −40 ~ 80 °C(T-14, 닫힘) | 2단계 판정(§17-1·2)은 **시험 회로**에서 통과, 9회로는 일반성(사유 코드·선언 없음 무동작), 완료 조건 (1)~(5)(계획 N5) | §17 |
| **TR-L** LUT VGS 음수 축(사용자 결정 T-10) | LUT 생성 규칙 변경: 꺼진 스위치 VGS 범위(음수, 크기 = 레일 전위 폭까지 -- 레일 선언에서 유도)를 VGS 축에 더해 진성 용량(cgg·cgd·cgs·cgb) 열을 만든다. 기존 VGS ≥ 0 격자·값은 비트 동일, 새 버전 파일(`lut_v2_location.json` 새 항목·sha256), `lut/CONTRACT.md` 축 절, 축 검사(`axis_guard`)는 새 축 범위로. 엔진 조회는 off 소자 용량에만 쓴다 | TR-0 승인(TR-1과 병렬) | 기존 축 값 비트 동일(재생성 대조), 새 축에서 ngspice `.op` 진성 용량 대조, 생성 규칙 문서 | 생성기와 독립인 ngspice 직접 조회로 표본 대조 |
| **TR-T** connectivity 표 도구 이식(사용자 결정 T-13) | `assets/topology_to_markdown.py`가 옛 엔진 로더(`legacy/stick_diagram.py`) 대신 새 엔진 로더(`load_topology`, 파생 topology는 `topology_from_data`)를 쓰게 옮긴다. 표 형식(넷 기준 표·dangling·gate 전용 넷 표지)은 그대로 | TR-3(`topology_from_data`) | library 9회로 표가 이식 전과 같은 내용, 파생 topology 표 생성, `legacy` import 0 | 이식 전 도구 출력(기존 `*.topology.md`)과 대조 |

계획 N5의 TR-5를 셋(a·b·c)으로 나누고, TR-M(측정 단계 G-2의 자리), TR-L(사용자 결정 T-10), TR-T(사용자 결정 T-13)를 더했다. 시험 회로·spec 승인(§16.1)은 card가 아니라 사용자 승인 절차다.

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

* 선언이 없는 9회로는 모두 무동작(§3.3 N 부류: 새 블록 호출 0, `offset_adjoint` = None)이고 이것을 TR-7이 측정한다.
* 단일 출력 6회로가 추천까지 가려면 출력 넷 `node_voltage_targets_v`가 필요하다(§3.6, TD-3).
* 그래서 지금 2단계를 바로 돌릴 수 있는 library 회로가 없다(current_reuse는 공존 거부). 2단계 검증은 별도 시험 회로로 한다(사용자 결정 T-9, §16.1). library 회로 spec은 건드리지 않는다.

### 16.1 2단계 검증용 시험 회로·spec(사용자 결정 T-9)

이 design은 회로를 정하지 않는다. 요구 조건과 승인 절차만 정한다.

| 요구 조건 | 근거 |
|---|---|
| 차동 입력(입력 셀 안 derived `diff_pair` 하나 이상) | §9.1 쌍 규칙, D-8 |
| 차동 출력이거나, 단일 출력이면 그 출력 넷의 `node_voltage_targets_v` 기준 DC 선언 | §3.6 G-6 |
| spec에 `offset_in_sigma_mv` 판정 제약이 없다 | §5.2 D-4 공존 거부 |
| spec에 `offset_trim` 선언(V_res·k·온도, 온도 = LUT `temp_c`)이 있다 | §5 |
| spec `meta.origin` = `fixture`, topology·spec 파일은 library 밖 시험 위치(`assets/library/`에 두지 않는다) | 40 §3.1 spec `origin`, T-9 'library spec 무변경' |
| 주입 넷 headroom 창이 비지 않는 (쌍, 극성)이 하나 이상(1단계 후보표로 확인) | §9.2 |
| spec 목적(`objective`)에 전력 또는 면적 축이 포함된다(I_u를 하한으로 미는 것이 목적 최소화이므로) | T-7 전제, §10.3 |

**승인 절차**: (1) 오케스트레이터가 요구 조건을 만족하는 topology·spec 초안과 connectivity 표를 만든다 -- 초안은 쓰이지 않는다 (2) 사용자가 topology(connectivity)와 spec 값을 승인한다(topology·spec은 사용자 몫) (3) 승인 뒤 1단계 → 승인 기록(§8) → 2단계. TR-5b·5c·7의 2단계 완료 조건은 이 시험 회로 기준이다(§15).
* 계획 N4 표의 '후보'와 다른 점: 단일 출력 회로는 후보표까지만 나온다(§18.2 X-T6).

---

## 17. TR-7 검증 규칙(샘플 수 포함)

**소유**: 이 절의 판정 규칙과 합격선은 design 작성자가 초안을 쓰고 **독립 검증자(design-validator, 이후 TR-7 auditor)가 확정·소유**한다(계획 N5·N6, NFR-T6). 검증자가 바꾸면 그 판이 정본이다. 오라클 구현(레인 P)은 엔진을 import하지 않는다.

**순서**(N5.1): 1 → 2 → 3·4·5. 1이 실패하면 2 이후는 해석하지 않고 보고만 한다.

| # | 항목 | 규칙 | 성격 |
|---|---|---|---|
| 1 | σ_in 일치 | 파생 topology 판정 점(코드 seal_plus, trim 없는 MC)에서 SPICE MC 표본 n개의 입력 환산 offset 표준편차 σ̂. 합격: \|σ_eng − σ̂\| ≤ k·σ̂/√(2(n − 1)) + 엔진 분해능(`offset_analysis` resolution). k = spec 배수(새 신뢰 상수 없음) | 판정 전제 |
| 2 | 27 °C 잔여 | 표본마다 trim 절차 흉내: seal_plus에서 offset 측정 → 모든 코드 c의 잔여를 오라클 DC로 재고 \|잔여\| 최소 코드 선택 → 잔여. **표본 선택 창(검증 N6·재검증 M3)**: 중심 = **공칭 offset V_nom** = 소자 mismatch 0인 같은 파생 회로를 **seal_plus 코드**에 두고 오라클 공칭 DC로 잰 입력 환산 offset(0이 아니다). 표본의 trim 전 offset도, 결정적 끝 표본도 모두 같은 seal_plus 코드 기준으로 잰다, 창 = [V_nom − k·σ̂, V_nom + k·σ̂]. **합격: trim 전 offset이 창 안인 표본 전부가 잔여 ≤ V_res(실패 0)**. 창 밖 표본 수와 그 잔여는 보고만. 더해 **결정적 끝 표본 둘**: 소자 공칭 + 입력에 직렬 이상 전압 ±k·σ_eng를 넣은 회로(seal_plus 코드에서 잰 trim 전 offset = V_nom ± k·σ_eng, 창의 두 끝)에서 같은 절차 → 잔여 ≤ V_res | 판정(완료 조건 (3)) |
| 3 | 고정 코드 온도 sweep | 2의 표본·코드를 고정하고 온도 점마다 잔여. 온도 점 = 사용자 결정 T-14의 보고 전용 범위 −40 ~ 80 °C의 두 끝점과 판정 온도(LUT `temp_c`). 범위 값은 사용자 값이고 판정에 쓰지 않는다(T-5). §3.8 분해 표 | 보고 |
| 4 | 코너별 보정 구간 | PDK 선언 코너마다 공칭 소자의 end_plus·end_minus 균형 V_in | 보고 |
| 5 | 끝 코드 headroom 온도 의존 | 3의 온도 점마다 끝 코드 포화 여유(off 소자 제외) | 보고 |

**샘플 수 규칙**:
* n = 1 + ⌈2·k⁴·σ_eng² / LSB_in²⌉ … (식 S)
* 유도: σ 추정의 표준오차 σ/√(2(n − 1))의 k배가, 보정 구간 요구량 k·σ를 반 LSB(LSB_in/2) 이상 옮기지 않을 σ 오차 LSB_in/(2k)보다 작아야 한다: k·σ/√(2(n − 1)) ≤ LSB_in/(2k). 모든 양은 spec(k)·엔진(σ_eng, LSB_in = \|t\|·I_LSB)에서 온다. k가 이 식에서 두 번(신뢰 배수, 구간 배수) 쓰이는 점은 X-T13.
* 같은 n개 표본을 1과 2에 같이 쓴다.

**비용 표(검증 N7, 실행 전에 낸다)**:

| 항목 | 오라클 DC 풀이 수 |
|---|---|
| 1 σ 일치 | n(표본마다 seal_plus offset 1회 -- 2의 첫 측정과 같은 풀이를 쓴다) |
| 2 잔여 | n·2^N(표본마다 코드 전수) + 결정적 끝 표본 2·(1 + 2^N) |
| 3 온도 sweep | n·(온도 점 수) |
| 4 코너 구간 | (코너 수)·2 |
| 5 headroom 온도 | (온도 점 수)·2 |
| 합 | 위 합. 한 풀이 시간은 오라클이 공칭 1회를 재서 곱한다 |

**판정 불능 규칙(기준 약화 금지)**: 합 시간이 TR-7 실행 한도를 넘으면 n·창·코드 전수를 줄이지 않는다. 결과는 '판정 불능(표본 부족)'이고 비용 표와 함께 사용자에게 올린다(한도를 늘릴지 결정). 일부 표본만 돈 결과로 합격을 선언하지 않는다.

**검증자 조건 셋(사용자 결정 T-12로 채택)**: (1) 표본 선택 창 중심 = 공칭 offset(§17-2) (2) 비용 표를 실행 전에 먼저 보고한다 (3) 실행 한도 초과·표본 부족은 '판정 불능(표본 부족)'이고 n·창·합격선을 줄이지 않는다(기준 약화 금지). n은 실행 전에 식 S로 고정하고 실행 중 바꾸지 않는다. 독립 검증자가 이 규칙의 판정 실행·소유를 맡는다.

* 한계 문구(보고서): 'MC는 분포 내부를 확인한다. k 꼬리(구간 끝)는 결정적 끝 표본으로만 확인한다. 수율 확률은 주장하지 않는다(D-2: 분포 가정 없음)'.

**9회로 일반성**: §16 표의 사유 코드를 9회로 전수로 재고, 선언 없는 실행의 무동작(§3.3 N 부류 정의: 새 블록 호출 0·새 필드·`trim` 키 없음, `offset_adjoint` = None)을 보인다.

---

## 18. 결정 필요·원래 취지와 다름

### 18.1 결정 상태

**닫힘**(사용자 결정 2026-10-15 "TD-1은 θ안, TD-8은 다로 해, TD2~TD7은 제안대로", 원문 `wt/_drafts/user_decisions.md` 'offset trim design 결정'):

| ID | 결정 | 반영 |
|---|---|---|
| TD-1 → T-7 | I_u = θ 변수(θ안) | §10.2·§10.3, X-T14 |
| TD-9 → T-8 | 예산 충돌 소멸, card C 규칙 변경 없음 | §10.3 |
| TD-8 → T-9 | 2단계 검증용 시험 회로·spec 별도(초안은 사용자 승인 전 쓰지 않음) | §16.1, §15 |
| TD-2 → T-10 | LUT VGS 음수 축 추가 | §3.1, TR-L |
| TD-4 → T-11 | structure.json 2개 재승인은 TR-4 착수 전 | §11 절차 |
| TD-5 → T-12 | 식 S + 검증자 조건 셋 | §17 |
| TD-7 → T-13 | 표 도구를 새 엔진 로더로 이식 | TR-T |
| TD-10 → T-15 | `run_trim_candidates` 제품 경로 배선: (다) TR-2 병합을 U16 뒤로. TR-M·TR-1·TR-L은 먼저 진행 가능(2026-10-15 사용자 "TD-10은 다") | §15 TR-2 행 |
| X-T15 → T-16 | structure.json 재승인 결정은 TR-4 착수 전, `rule_hash` 파일 갱신은 TR-4 병합 때(사용자 확인) | §11 절차 |
| TD-6 → T-14 | 보고 전용 온도 sweep 범위 = −40 ~ 80 °C(2026-10-15 사용자 "TD-6은 -40~80") | §17-3·5, TR-7 |

**열림**(사용자 값):

| ID | 질문 | 막는 것 |
|---|---|---|
| TD-3 | 단일 출력 6회로의 출력 기준 DC 값(`node_voltage_targets_v`, CI-15) -- 오케스트레이터가 회로별 선택지를 제안하고 사용자가 고른다(T-14 원문) | 그 회로들의 추천·2단계(값이 정해질 때까지 후보표까지만) |
| (절차) | 시험 회로 topology·spec 승인(§16.1) | TR-5b·5c·7의 2단계 완료 조건 |

### 18.2 원래 취지와 다름(따로 보고)

| ID | 내용 |
|---|---|
| X-T1 | (닫힘) v0.2의 'TD-1 (나)는 D-16/X-3과 다르다'는 사용자 결정 T-7로 (나)가 채택되어 X-T14로 옮겼다 |
| X-T2 | 계획 θ 행 '단위 셀 gm/ID·L만'을 셀의 두 소자 종류(전류원, 스위치)의 ln IDu·L로 읽어 DAC마다 ln IDu·L 성분 넷(+ T-7의 I_u 하나 = 다섯)이다(§10.2). 스위치 크기를 θ 밖 규칙으로 정하는 안은 상수(폭 비 등)를 발명해야 해서 택하지 않았다 |
| X-T3 | (삭제) 평가마다 원본 topology pass 0 -- T-7 뒤 필요 없어 없앴다(§10.1). 원본 S0는 구조·스키마 비교에만 쓴다 |
| X-T4 | G-1 표현: 구조(S1·S1v)는 모든 스위치를 가진 파생 topology 하나로 만들고 코드 상태는 sizing 층의 off 집합으로만 표현한다. 계획은 '소자 제외, 별도 포화 검사 경로' 중 택하라고만 했다 |
| X-T5 | 완료 조건 (1) 비교 제외(G-3)가 계획 D-14 문언('규칙 지문')보다 넓다: 블록 코드 해시에서 온 입력 버전·스냅샷 지문·코드 지문(F2~F4)도 뺀다. 코드가 바뀌는 card에서 이 칸들은 필연적으로 바뀌기 때문이다. 값 부류는 비트 동일 그대로라 기준 약화는 아니라고 보지만, 판정 기준 변경이라 보고한다 |
| X-T6 | 계획 N4 표의 단일 출력 6회로 '후보'는 G-6 fail-closed 때문에 후보표까지만 나오고 추천·2단계는 TD-3 전까지 막힌다 |
| X-T7 | (닫힘) connectivity 표: 1단계는 assets 도구를 하위 프로세스로 부르고, 도구는 TR-T에서 새 엔진 로더로 옮긴다(사용자 결정 T-13) |
| X-T8 | 켜진 스위치를 `trim_decl`이 triode 의도 영역으로 더한다(§3.1). 지금 `intended_region`은 사용자 spec에만 있는 선언인데, trim 소자 한정으로 엔진 출처 선언이 생긴다(trim 소자는 사용자 topology 원소가 아니므로 사용자 선언 자리가 없다) |
| X-T9 | card 분할: 계획 TR-5를 TR-5a·b·c로 나누고 TR-M(측정)을 더했다. TR-L·TR-T는 사용자 결정 T-10·T-13에서 온 card다 |
| X-T10 | TR-7 표본 수 식(§17)은 '반 LSB' 기준을 쓴다. 반(1/2)은 '최적 코드 선택의 잔여 = 간격/2'(계획 N3.4 잔여 판정)와 같은 정의에서 왔으나, 검증 기준으로 쓰는 것은 이 design의 선택이다(TD-5) |
| X-T11 | 승인 결속에 `spec_trim_fp`(spec `offset_trim` 섹션 지문)를 넣었다(§8.3-4). 계획 N3.3 결속은 원본·파생 지문과 변환 규칙 해시뿐이라 이 design이 계획보다 엄격하다: V_res·k·온도가 바뀌면 추천 (N, m)이 달라지므로 재승인을 요구한다 |
| X-T12 | (해소) K_trim 상한 문제는 T-7로 고정점·K_trim 자체가 없어져 대상이 사라졌다 |
| X-T13 | §17 식 S에서 spec k를 두 번 쓴다: (1) 보정 구간 배수(계획 정의) (2) σ 추정 오차의 신뢰 배수. (2)는 '새 신뢰 상수를 만들지 않기 위해' 같은 선언값을 재사용한 design 선택이다. 별도 신뢰 배수를 spec에 두는 안은 사용자·검증자 몫(TD-5) |
| X-T14 | **I_u = θ 변수**(§10.2·§10.3): 계획 D-16(I_u = 하한값)·X-3(I_u를 θ에서 뺀다)과 다르다. **사용자 결정 T-7로 승인됨**. 하한은 제약 `trim_range` + 전력·면적 최소화로 얻는다. 계획 D-16 행은 같은 브랜치에서 T-7로 한 줄 정정했다 |
| X-T15 | structure.json 재승인(T-11 'TR-4 착수 전'): 새 `rule_hash` 값은 TR-4 코드에서만 계산되므로, 착수 전에는 재승인 **결정**을 받고 파일의 `rule_hash` 갱신은 TR-4 병합에서 한다(§11 절차, 40 §3.2-3 작성 순서). 결정 문언과 시점 해석이 다를 수 있어 보고한다 -- **사용자 확인됨(T-16)** |
| X-T16 | 2단계는 원본 회로를 다시 평가하지 않으므로(§10.1) '원본 대비 DAC가 더한 offset 분산' 보고는 1단계 front 점(원본 회로, 그 θ)과 2단계 front 점(파생 회로, 다른 θ)의 값 비교다. 같은 θ의 쌍 비교가 아니라는 문구를 보고에 함께 싣는다 |

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
