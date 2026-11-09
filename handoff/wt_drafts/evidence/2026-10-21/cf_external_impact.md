# Cf1·Cf2(및 Cs1·Cs2) 외부 되먹임망 제거 영향 분석 -- current_reuse_telescopic_ota

- 작성: 2026-10-21, 읽기 전용 분석(결정 없음). 기준 master `0de6a34a`.
- 사용자 진술(2026-10-21, 회로 사실 -- 사용자 영역): "Cf1/Cf2는 회로 외부에서 구성되는 feedback loop이야. 즉, 회로를 설계할때는 이 Cf cap은 제거하고 하는 것이 맞다"
- 경로 약어: `S` = `chip-design-skills/skills/analog-gmid-design`, `E` = `S/gmid_engine`, `O` = `S/tools/spice_oracle`, `P/gb` = `chip-design-skills/docs/01-plan/features/gain-budget-gmid-sizing.plan.md`, `UD` = `wt/_drafts/user_decisions.md`.

## 1. Cs1·Cs2도 같은 외부 SC 망인가 -- 근거(양쪽)

| 근거 | 내용 | 방향 |
|---|---|---|
| 논문 Table I (`S/assets/library/sources/current_reuse_telescopic_ota__xie_chen_2019/paper.md:74-77`, source.pdf p.1) | "Values for C1, C2, and CL: 500fF, 500fF, 1pF" -- **C1(=Cf)·C2(=Cs)·CL이 한 행**에 '설계 사양/테스트 조건'으로 나열됨 | Cs도(그리고 CL도) Cf와 같은 외부 테스트 조건 |
| 논문 III 식 (3)(4) (`paper.md:404-418`, p.4) | gm1 = ωc·Cc/β, β = Cf/(Cf+Cs+Cgg1), "Cf = Cs = 500fF, β ≈ 0.48" | Cs는 β 분모(외부 SC 망의 일부) |
| 논문 II 본문 (`paper.md:128-135`) | "Figure 1 shows the schematic design of the designed OTA" -- 본문이 기술하는 OTA 구조는 1단 current-reuse + 2단 class-AB(+Cc, CMFB). Cf/Cs는 III절 β 식에서만 등장 | Cf/Cs가 OTA 회로 본체가 아님을 시사(그림 1 안 포함 여부는 이미지 재확인 필요 -- 이 분석은 이미지 판독 안 함) |
| 논문 IV.F / Fig.19 (`UD:245` C-2 판독) | Table I 잡음 300 µV/272 µV = Cadence **폐루프 testbench**(C1=C2=500 fF 용량 귀환, CL=1 pF)의 .noise, 스위치 없음 | Cf·Cs·CL 모두 testbench 소자 |
| topology.json 주석 (`S/assets/library/current_reuse_telescopic_ota.topology.json` passive_elements Cf1/Cf2/Cs1/Cs2, 2026-09-10 사용자 승인) | Cf = "스위치드커패시터 피드백망", Cs = "스위치드커패시터 샘플링 커패시터 ... 개루프 AC 측정에서는 양단이 다 고정이라 기여가 0" | 두 쪽 모두 SC 망 소자로 기록 |
| CI-10 (`UD:159`, 2026-10-08) | "Cs1·Cs2 는 입력-gnd 샘플링 커패시터로 β = Cf/(Cf+Cs+Cin) 분모의 입력 부하이지 feedback 아님" | Cs는 **되먹임은 아니나** 같은 β 망의 입력 부하로 결정됨 |
| 반대 근거 | 원문 어디에도 "Cs는 OTA 내부 소자"라는 문장은 찾지 못함. Cs가 OTA 안에 남아야 할 근거 0건 | -- |

판독 요약(확신도 중간~높음, 그림 1 이미지 미확인): Cs1·Cs2는 Cf1·Cf2와 같은 외부 SC 망(β 망)의 일부다. CL1·CL2도 Table I의 같은 행에 있는 테스트 부하다 -- 다만 CL은 이미 spec에서 `measurement_load: true`(설계 대상 아님)로 표시돼 있다(§3 선례).

## 2. Cf/Cs에 의존하는 자리 전수

### 2.1 회로·spec 자산

| # | 자리 (file:line) | 지금 내용 | Cf 제거 시 | Cf+Cs 제거 시 |
|---|---|---|---|---|
| A1 | topology.json `passive_elements` Cf1[Vom,Vip]·Cf2[Vop,Vim]·Cs1[Vip,gnd]·Cs2[Vim,gnd] (`value_from_spec` Cf/Cs) | connectivity 사실 | 두 소자 삭제 -- **connectivity 변경 = 사용자 전용**(memory 'topology.json이 유일한 토폴로지 소스'). `connectivity_fp` 바뀜 → S0 재빌드·기준선 변화 | 네 소자 삭제, 같음 |
| A2 | topology.md `:47-48,51,53,57,124-127` | 넷 표에 Cf/Cs 단자 | 재생성(`topology_to_markdown.py`) | 같음 |
| A3 | sizing_spec `human.element_values.Cf1/Cf2` (`:92` 부근), `Cs1/Cs2` (`:112` 부근) -- user_spec 500 fF, 출처 Table I | 값 선언 | Cf 항목은 topology에 없는 소자라 거부될 것(요소 검사 `E/authoring/spec_elements.py:140-173`) → 삭제 필요 | Cs 항목도 삭제 |
| A4 | sizing_spec `human.feedback.elements = [Cf1, Cf2]` (`:141-142`, CI-10 출처) | β 루프 선언 | **로드 거부** `feedback_element_unknown`(`E/authoring/spec_elements.py:134`) → 값을 바꿔야 함: `[]`(β = 1) 또는 `{"pending": ID}` 또는 새 외부망 선언(현재 스키마 없음) | 같음 |
| A5 | constraint `offset_in_sigma_mv <= 3.3` (spec `:226`, 출처 Q3 (2)) | 3.3 mV 유도 근거 = "논문 β ≈ 0.48(Cf = Cs = 500 fF)" | 값은 입력 환산이라 계산 의미는 유지. **출처 문장이 외부 β에 기대어 있음** -- 유지 여부는 사용자 판단 | 같음 |
| A6 | constraint `noise_out_int_vrms <= 450 µVrms` (spec constraints[10], 출처 2026-10-14 Q-S3; DEC-96 (3) `P/gb:296`; design 41 `:1830, :1883`) | **폐루프** 출력 잡음(Cf로 닫고 Cs 입력 부하, 논문 Table I 조건) | feedback `[]`면 엔진은 `open` 모드(입력 단락, 개루프 출력 잡음 -- `E/metrics/noise_plan.py:9-10, :40-41`), 오라클은 `unavailable`(`O/oracle_noise.py:259-261`). **같은 450 µV 숫자가 다른 정의의 양에 붙게 됨** → 제약 정의/값 재결정 필요 | 같음 |
| A7 | constraint `pm_ss_deg >= 70` (spec constraints[1]) + U-48 (`P/gb:567, :2016`) | 선언 β 루프의 PM(절단 Vip·Vim, Cf 부하 포함) | feedback `[]` → β = 1 루프 뷰 = 포트 뷰(`E/authoring/spec_views.py:95-98`, SPEC_CONTRACT `:277-278` "[] → loop unity, 차동 출력 sense (Vop, Vom)"). 출력 부하에서 Cf 직렬 부하(≈ Cf·(Cs+Cin)/(Cf+Cs+Cin) ≈ 0.26 pF/쪽)가 빠지고 β가 0.48 → 1. 70°의 원래 근거(β 루프용 기본안 2026-10-07)와 다른 루프 | 같음(Cs는 β = 1 포트 뷰에서 구동 입력에 달려 기여 0) |
| A8 | constraint `area_search_m2 <= 4e-8` (constraints[12], 결정 11 "Cl을 빼는 것에 동의") + `E/search/area_decl.py:6-7` | 면적 제외 = `measurement_load`인 소자뿐(지금 CL1·CL2) → **Cf1·Cf2·Cs1·Cs2(합 2 pF)가 지금 회로 면적에 들어가 있음** | Cf 면적 1 pF가 빠짐 | Cs 면적 1 pF도 빠짐 |
| A9 | `compensation_targets.settling` (t_lln 30 ns, 논문 III.A) | 논문은 ωc(β 루프 UGF)로 유도 | 엔진 소비자 없음(`E/authoring/spec_targets.py:13` "보상 목표로만 쓰이고 합격 판정 대상이 아니다", search·sizing grep 0건) → 즉시 영향 없음. 단 의미는 외부 β 전제 | 같음 |
| A10 | `CL1/CL2` `measurement_load: true` (spec element_values, `_CL_comment`) | Table I 같은 행의 테스트 부하를 회로 안 소자 + 표지로 둔 **선례** | 변화 없음(질문 Q2) | 같음 |
| A11 | offset-strategy F-1 fixture (design `docs/02-design/features/offset-strategy.design.md:556, :617-624`) | library topology **사본**(같은 `connectivity_fp`), 아직 파일 없음(`S/assets/fixture/offset_strategy/` 부재) | library가 바뀌면 사본도 같이(아직 미생성이라 지금 수정 대상 없음) | 같음 |

### 2.2 엔진 소비자 (모두 회로 이름 없는 일반 규칙 -- 선언만 바뀌면 코드 변경 없이 따라감)

| # | 자리 | 되먹임 선언을 어떻게 쓰나 | feedback `[]`(β = 1)일 때 |
|---|---|---|---|
| E1 | `E/authoring/spec_elements.py:118-138` `_feedback`, `:19-22` 절단 규칙 | 선언 소자 존재·입력 포트 단자 1개 검사 | 통과(빈 list = "되먹임 수동소자 없음 = β=1 루프, UD 9번" `:19-20`) |
| E2 | `E/authoring/spec_load.py:104-112, :148` | feedback → `constraint_declaration` 루프 뷰 유도 | β = 1 루프 뷰 |
| E3 | `E/authoring/spec_views.py:90-110` `_loop_view` | 선언 → cuts·weights / 빈 list → `BETA_UNITY` 포트 뷰 | 차동 포트 뷰(Vop, Vom) |
| E4 | `E/metrics/loop_analysis.py:13-14`, `E/metrics/loop_cut.py:12`, `E/metrics/records.py:194` | 선언 소자 입력 쪽 단자에서 절단, Middlebrook 식 | 빈 list면 포트 전달 `Factor` 하나(T = A) |
| E5 | `E/search/noise_decl.py:3-8, :35-43` (writer `noise_decl`, graph 필드 `noise_input_cells`) → `NoiseDecl.feedback` | 잡음 폐루프 모드 + **ICMR 측정 구성 extras의 출처**(UD O-69 비고 C-3 (b′): `NoiseDecl.feedback`을 `icm_config` extras로) | `()` → 잡음 open 모드, icm_config는 "선언 없음/DC 성분 없음" 갈래 |
| E6 | `E/metrics/noise_plan.py:36-55` | closed(자유 입력 넷) / open / undefined | `open` |
| E7 | `E/metrics/ls_fields.py:6-8` `c_slew_farad` | 노드에 닿은 **모든 회로 용량 소자** 합(부하·보상 포함) | Cf가 빠지면 출력 노드 슬루 용량에서 Cf 0.5 pF/쪽 제거(현재는 Cf 전체 값이 출력 노드에 더해짐 -- Cf 반대 끝 Vip는 구동 고정이 아님에도 크기 합) |
| E8 | 소신호 회로 `E/metrics/ss_circuit.py:33-35` (`passive_values`) | topology 수동소자 전부 MNA에 스탬프 | Cf/Cs 스탬프 사라짐 → gain·UGF·PM·CMRR/PSRR·pm_cm(CMFB 루프 부하) 전부 값 변화 |
| E9 | `E/search/area_decl.py:6-7` | §2.1 A8 | 면적 감소 |

### 2.3 오라클

| # | 자리 | 내용 | 제거 시 |
|---|---|---|---|
| R1 | `O/oracle_netlist.py:235-252` (β 루프 절단 넷), `:366`, `:1061-1062`, `:1287` | `feedback_passives`가 있으면 루프 넷리스트(`.loop.cir`) | 없으면 루프 넷리스트 안 씀 → PM은 β = 1 정의(`O/oracle_simulate.py:44`) |
| R2 | `O/oracle_noise.py:15, :253-261` | 폐루프 잡음은 `feedback_passives` 필요 | `unavailable`("폐루프 되먹임 요소 미선언") -- A6과 연동 |
| R3 | `O/legacy_adapter.py:461-462` (`legacy_c12_input_net_passives`), README `:195-196` | 옛 기준선 규칙 = 입력 넷 수동소자 전부({Cf1,Cf2,Cs1,Cs2}) | Cf만 빼고 Cs를 남기면 옛 규칙이 **Cs만을 되먹임으로 고름**(입력-gnd 소자로 β 루프를 만드는 오류). legacy는 F-LT8 삭제 대상(`P/gb:1284, :1311`) |
| R4 | 오라클 smoke 산출물 `O/smoke/current_reuse_telescopic_ota.*.{cir,compare.md,oracle_input.json}` | Cp_Cf1/Cp_Cs1 포함 과거 실행 기록 | 기록물(재생성 대상), 판정 입력 아님 |
| R5 | oracle 계획 OP-10 (`docs/01-plan/features/oracle-portability.plan.md:502`), DR-22 (`:714`), X-35 (`:644`) | "용량만 선언된 차동 출력(current_reuse Cf1·Cf2)의 `.tran` 시작 동작점" 범위 | library에 그 갈래의 실례가 0이 됨 -- 규칙은 남지만 발동 회로 없음(OP-10 검증 실례 재선정 필요 여부) |

### 2.4 계획·design·결정 문언

| # | 자리 | 지금 문언 | 제거 시 |
|---|---|---|---|
| D1 | `P/gb:254` DEC-55 | "파일럿 적용: CL1/CL2, Cf1/Cf2 교차, Cs1/Cs2" | 사례 문구 정정 |
| D2 | `P/gb:405` N3.2 루프 뷰 예 | "파일럿 Cf1[Vom, Vip]·Cf2[Vop, Vim]는 전달 뷰에서 출력노드–여기 포트 사이 부하" | 예시 정정(규칙 불변) |
| D3 | `P/gb:567` PM, `:2016` U-48 | 선언 되먹임이 있으면 β 루프, 없으면 β = 1 | 규칙 그대로 적용 -- current_reuse가 β = 1 갈래로 이동 |
| D4 | `P/gb:576` ICMR 측정 구성(O-50 G4, O-67 (1), O-68 (2)) | "DC 성분이 없거나(용량만 -- 예 library current_reuse Cf1·Cf2) 선언이 없으면 **차동 모드만 닫는다**" | **결과 불변**: DC 망에서 용량은 원래 열림이라 Cf 유무와 무관하게 같은 DM 닫힘((in+ − in−) = −(Vop − Von), 입력 CM = x, 출력 CM = CMFB). 예시 문구만 정정 |
| D5 | `P/gb:577` 슬루(O-34 (2), O-50 G2, O-69 (1)) | 선언 구성 있으면 그 구성, 없으면 β = 1 follower; **차동 출력 미선언 = 정의 불능**; 용량만 선언된 차동 출력의 t = 0 `.op` = N3.8 DM 닫힘 인용(current_reuse 예) | feedback `[]`이 '미선언'인지 'β = 1 선언'인지 문언에 없음(Q4). 어느 쪽이든 current_reuse 슬루 = **정의 불능**(입력 망이 정해지지 않음 -- `:577` 근거 정정 문장). spec에 slew 제약이 없어 판정 영향은 없고 보고만 '정의 불능' |
| D6 | `P/gb:296` DEC-96 (3), design 41 `:1409`(C-2), `:1830`, `:1865`, `:1883` | 파일럿 `noise_out_int_vrms` = 선언 feedback {Cf1, Cf2}로 닫은 폐루프, Cs 입력 부하, CL 부하 | 정의 성립 불가(A6) -- 계획 개정 필요 |
| D7 | `P/gb:2038` U-70, design 40 `:1473` | 잡음 N_in 계수 "반쪽 귀환 대칭(Cf1 = Cf2)" | 예시 문구(규칙은 일반) |
| D8 | `UD:159` CI-10 | 파일럿 feedback = {Cf1, Cf2}, Cs 입력 부하 | 사용자 새 진술과 충돌 -- CI-10 대체 결정 필요 |
| D9 | `UD:245` C-2 | 잡음 300 µV는 폐루프 testbench(C1=C2=500 fF) 조건 | 회로 밖 조건임을 사용자가 이번에 확인한 셈 -- 판정 조건을 어디에 둘지 미정 |
| D10 | `UD:654` O-34 (2), `UD:670` O-50 G2·G4, `UD:688` O-67 (1), `UD:689` O-68 (2), `UD:690` O-69 (1) | 위 D4·D5 규칙의 원 결정. O-67 (1)·O-69 (1)은 current_reuse Cf1·Cf2를 실례로 인용 | 규칙 자체는 일반형이라 유지 가능, 실례 문구만 낡음 |
| D11 | `UD:687` O-66 Q1, `wt/_drafts/evidence/2026-10-21/de1_output_structure_13.md:44-45, :71, :89` | current_reuse Vom/Vop = KVL 고정(R1/R2 → Voc → CMFB 사슬). 핀 목록에 Cf1/Cf2 | **분류 불변**(DC writer 사슬은 R·MOS로만, 용량 무관). 표의 핀 칸만 낡음 |
| D12 | `UD:691-693` O-70~O-72 | 판정 분해능 δV_out(IT-2c 착수 실측에 current_reuse 봉인점 포함, O-71 '미확인') | 정의 불변. 실측 대상 회로의 넷리스트가 바뀌므로 IT-2c 착수 실측은 바뀐 topology 위에서 |
| D13 | `E/authoring/SPEC_CONTRACT.md:264-265, :277-278` | CI-10 해소 문장, {Cf1,Cf2}/{Cf1..Cs2}/[] 세 경우 실측 | 계약 문장 정정 |

### 2.5 test·기준선

| # | 자리 | 의존 | 제거 시 |
|---|---|---|---|
| T1 | `E/tests/integration/test_spec_library_load.py:364-371` `CI10_FEEDBACK=("Cf1","Cf2")`, `CI10_NOT_FEEDBACK=("Cs1","Cs2")` | CI-10 기대값 | 깨짐(기대값 출처 = 사용자 결정 -- 새 결정으로 test 작성자가 갱신) |
| T2 | `E/tests/integration/test_j_rules_library.py:32, :168` | "pm_ss_deg β(Cf1·Cf2)" | 깨짐/갱신 |
| T3 | `E/tests/search/test_noise_decl.py:75-77` | 이름 tuple ("Cf2","Cf1")·("Cs1","Cs2")를 extras로 넘김 | `noise_decl`은 이름을 그대로 담기만 해 단언은 통과 가능성 있음(미실행 -- 확인 안 함) |
| T4 | `E/tests/graph/test_orbit_matching_crosstab.py:78` | 파일럿 Cs2 접지 끝을 vdd로 바꾸는 합성 변형 | Cs 제거 시 이 변형 자리 소멸 → 다른 비대칭 주입 자리 필요 |
| T5 | S0 기준선·test 기대·`connectivity_fp` | library topology 지문 | 동작 변경(N4 0번·N6.3 변화표) |

## 3. 외부 루프 정보(β·부하)를 어디에 둘 것인가 -- 현재 계획이 말하는 것

- **지금 정본 자리**: (i) 외부 되먹임은 spec `human.feedback.elements`(소스 kind `user_spec`만, `E/authoring/spec_sources.py:39`)가 **topology 수동소자 이름**을 가리키는 꼴뿐이다(`E/authoring/spec_elements.py:3-24`). (ii) β 값 자체를 담는 필드는 없다 -- β는 선언 소자로 루프를 끊어 MNA로 잰다(`P/gb:567`, loop_analysis). (iii) 부하는 topology 수동소자 + spec `element_values.<소자>.measurement_load: true`(`E/authoring/spec_elements.py:9, :37, :84-95`) -- '설계 대상이 아닌 측정 부하'라는 표지가 이미 있고 면적에서만 뺀다(`E/search/area_decl.py:6`). (iv) DEC-55(`P/gb:254`): passive connectivity는 topology에 선언.
- **'회로 밖 소자'를 topology 밖에서 선언하는 스키마·graph 필드는 없다.** 외부망 선언을 새로 만들면 새 spec 섹션 + 그것을 읽어 소신호 회로·루프 뷰·잡음 계·과도 벤치에 붙이는 writer 하나가 필요하다 → graph 단일 정본 규칙 6(`fpga/CLAUDE.md` "정본 자리가 없으면 멈추고 보고, 계획부터 고친다(S-7)")에 해당 -- **계획 개정 사안**.
- **기존 선례로 표현하는 길**: CL1/CL2가 Table I 같은 행의 테스트 부하인데 topology 소자 + `measurement_load`로 남아 있다. 같은 꼴로 Cf/Cs를 topology에 두고 "외부(테스트벤치) 소자" 표지를 다는 길이 있으나, 지금 `measurement_load`의 뜻은 면적 제외 하나뿐이고 **"설계 회로 netlist에서 제거"**(사용자 진술)와는 다르다. 사용자 진술 문자 그대로(설계 netlist에서 제거)를 따르면 topology에서 빠지고, 그러면 β 루프 PM·폐루프 잡음·슬루 구성은 선언할 자리가 없다.
- graph 규칙 3 관점: '설계 회로의 개루프 양'(예 β = 1 PM, 개루프 잡음)과 '외부 β 망을 단 폐루프 양'(β 루프 PM, 폐루프 잡음)은 **측정 구성 축이 다른 별개 정의**다 -- 같은 metric 이름(`pm_ss_deg`, `noise_out_int_vrms`)에 둘을 섞으면 안 되고, 둘 다 필요하면 정의 축(측정 구성)을 문서에 적고 필드를 나눠야 한다.

## 4. Cf 제거 뒤 current_reuse(차동 출력, 되먹임 선언 없음)에 지금 계획 규칙이 주는 값

| 항목 | 지금 규칙 | 결과 | 표준 OTA 특성화 관례 | 계획 개정 필요? |
|---|---|---|---|---|
| ICMR | `P/gb:576` O-68 (2): DC 성분 없음 **또는 선언 없음** → 차동 모드만 닫음, 입력 CM = x 훑기, 출력 CM = CMFB | **지금과 동일**(DC에서 Cf는 원래 열림) | 단위 이득 follower 구성에서 입력 CM 훑기. 완전차동이면 Vop→Vim·Vom→Vip 직결은 입력 CM = 출력 CM(CMFB가 고정)이라 CM을 훑을 수 없어, 실무는 DM만 닫는 이상 망(저항/이상 VCVS)으로 입력 CM을 따로 건다 -- O-68 (2)와 같은 꼴 | 아니오(예시 문구만) |
| 슬루 | `P/gb:577` O-50 G2·O-69 (1): 차동 출력 미선언 = 정의 불능(근거: 계단 입력 망은 선언 몫) | **정의 불능**(spec에 slew 제약 없음 → 보고만 '정의 불능', 판정 영향 0) | 단위 이득(β = 1) 또는 응용 β 구성에서 큰 계단, CL 부하. 완전차동은 저항/용량 β 망 또는 이상 DM 망을 테스트벤치로 둠 | 슬루를 재고 싶으면 예(입력 망 정의 -- 외부망 선언 또는 'DM β = 1 테스트벤치' 규칙). `[]`가 '미선언'인지 'β = 1 선언'인지 문언 정리 필요 |
| PM β | `P/gb:567` U-48: 선언 없으면 β = 1. 엔진 `spec_views.py:95-98` 빈 list → 포트 뷰(β = 1), 오라클 루프 넷리스트 없음 → β = 1 | **β = 1 PM**(차동 포트 Vop−Vom). 70° 하한이 그대로 걸림 | 단위 이득 PM = 최악 조건(β 최대)이 관례. 응용 β(0.48)는 더 여유 | 규칙 개정은 불요. **제약 값 70°의 근거(β 루프 전제)는 재결정 대상**(Q5) |
| 잡음 | `E/metrics/noise_plan.py:40-41` 빈 tuple → open(입력 단락 출력 잡음); 오라클 폐루프 unavailable | 450 µV 제약이 개루프 출력 잡음에 붙음(정의 불일치) | 입력 환산 잡음(PSD·적분) 또는 응용 β 폐루프 잡음 | **예**(DEC-96 (3)·design 41 §7 파일럿 정의) |
| GBW/UGF | 보고 metric(제약 없음) | 출력 부하에서 Cf 몫 빠져 UGF 상승 | 개루프 UGF(CL만) | 아니오 |
| 면적 | `area_decl.py:6` | Cf(·Cs) 면적이 빠짐 | 외부 소자는 OTA 면적 밖 | 아니오(오히려 정합) |

## 5. 사용자 회로 지식이 필요한 질문

- **Q1 (Cs 범위)**: Cs1·Cs2도 Cf와 같은 외부 SC 망(β 분모)으로 보고 함께 제거하는가? 근거 §1(Table I 같은 행, β 식, Fig.19 testbench). Cf만 빼고 Cs를 남기면 입력-gnd 용량만 남는데, 개루프·β = 1 측정에서 기여가 0이고 면적만 1 pF 늘며 옛 legacy 규칙이 Cs를 되먹임으로 오인한다(R3).
- **Q2 (CL)**: CL1·CL2도 Table I 같은 행의 테스트 부하다. 지금처럼 '회로 안 소자 + measurement_load'(PM·UGF·슬루에 부하로 들어감)로 유지하는가?
- **Q3 (외부 β 정보 보존 여부)**: 응용 β(≈ 0.48, Cf = Cs = 500 fF)로 정한 사양(β 루프 PM, 폐루프 잡음 450 µV, 정착 t_lln 30 ns, offset 3.3 mV 유도 근거)을 계속 판정에 쓸 것인가? 쓴다면 외부망을 담을 정본 자리가 없으므로 계획부터 개정(새 spec 섹션 + writer 하나, S-7)이 필요하고, 안 쓴다면 이 사양들을 개루프/β = 1/입력 환산 정의로 다시 정해야 한다.
- **Q4 (빈 선언의 뜻)**: `human.feedback.elements = []`(엔진 규칙상 'β = 1 루프')를 슬루·ICMR 규칙의 '선언 없음'과 같은 것으로 볼 것인가? 지금 문언(`P/gb:576-577`)은 '선언 없음'과 '빈 선언'을 구분하지 않는다.
- **Q5 (PM 하한)**: β = 1 PM에도 70°를 그대로 거는가(2026-10-07 기본안은 β 루프 전제)?
- **Q6 (잡음 제약)**: `noise_out_int_vrms <= 450 µV`(폐루프, 논문 testbench 조건)를 입력 환산 잡음 제약으로 바꾸는가, 외부망 선언으로 폐루프 정의를 유지하는가?
- **Q7 (topology 수정 주체)**: topology.json connectivity 삭제는 사용자 전용 규칙이다 -- 사용자가 직접 지우는가, 일괄 반영 지시('한꺼번에 반영해')를 줄 것인가? (memory: topology 정정은 대기열 후 일괄 반영)
- **Q8 (그림 1 확인)**: 논문 Fig.1(OTA 회로도)에 C1·C2가 그려져 있는지 -- 이 분석은 이미지를 판독하지 않았다(memory: 회로도 이미지 판독 부정확 규칙).

## 6. 확인 안 한 것

- test 실행 결과(T3 통과 여부 등) -- 읽기 전용이라 실행 안 함.
- Cf 제거 뒤 PM·UGF·잡음의 실제 수치 변화 -- 미측정.
- 논문 Fig.1 이미지 판독.
