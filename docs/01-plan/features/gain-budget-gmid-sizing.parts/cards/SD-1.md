### N6.21 card SD-1 -- spec/topology data: O-73 1단계 외부 망 표지·O-74 공급 구성(사용자 결정 O-73·O-74, DEC-100·DEC-101)

**성격**: 데이터 card(엔진 코드 변경 0). **동작 변경으로 등록한다**(N4 0번·N6.3 변화표) -- 보고 면적·GB4 면적 하한·layout 산출물·S0 기준선·spec 지문이 바뀐다. 면적 고정 항은 GB4 면적 하한과 출발 구간 면적 추정에도 들어가므로(DEC-100 (4) 소비자) **탐색 궤적과 front가 바뀔 수 있고**, 면적 제약(`area_search_m2` 상한) 경계 근처 점의 합격 여부도 바뀔 수 있다 -- 변화표로 잰다. 해석 값(DC·AC·과도)은 바뀌지 않는다: current_reuse의 네 소자는 topology에 남고, rfc_ota는 out–gnd 총용량이 2.75 pF로 같다(DEC-100 (2)(3)).

**표 SD-T1 -- 회로별 공급 구성(O-74 (2), 선언된 사실과 출처)**. 원문 쪽은 `assets/library/sources/*/paper.md`의 `## p.N` 머리, 원문 링크·로컬 PDF는 `supply_config_audit_13.md` §2:

| 회로 | 원문 구성 | 근거 | 이식 rail(현재) | SD-1 할 일 |
|---|---|---|---|---|
| common_gate_amplifier | single | Allen Lecture 20 p.20-2 `VOUT(min) ≈ VDS1(sat)+VDS2(sat)`, p.20-7 "negative power supply (ground in this case)" | vdd/gnd 1.8/0 | `supplies_v.source`에 구성·인용 |
| current_reuse_telescopic_ota | single 1.8 V | Xie & Chen 2019 p.1 "1.8V power supply", p.4 | vdd/gnd 1.8/0 | 구성·인용 |
| folded_cascode | single(사용자 확정 O-74 (2) '5번') | Maloberti 2004 p.30·p.33 VDD/GND 라벨(folded 쪽 p.34~38 텍스트에는 라벨 없음) | vdd/gnd 1.8/0 | 구성·인용(사용자 확인 기록) |
| ngcc_3stage_ff | single 1.2 V | Lee 2007 p.5 "Power supply voltage was set to 1.2V", p.6 | vdd/gnd 1.8/0(사용자 2026-09-16) | 구성·인용 |
| nmcnr_amplifier | **dual ±1 V**(사용자 확정 '4번') | Leung 1999 PDF p.4(저널 p.602) "supply voltage of +/-1V", Table 1 "+/- 1 V" | vdd/vss/agnd 1.8/0/0.9 | `supplies_v.source`에 원문 ±1 V 인용 추가. 입력 DC 기준 = agnd(DEC-101 (2)) -- **값은 SP-2 결정 때 적용, 지금은 `{"pending": "SP-2"}` 유지** |
| pushpull_follower_buffer | **dual**(사용자 확정 '1번' -- 원문 텍스트는 상충: p.26-4 "negative output voltages", VSS 라벨 없음) | Allen Lecture 26 p.26-4 + 사용자 확인 O-74 (2) | vdd/vss/agnd 1.8/0/0.9, CL·input_dc → agnd | 현 구성 유효, dual 근거 인용 추가 |
| sf_pushpull_output_opamp | **dual**(사용자 확정 '2번') | Allen Lecture 26 p.26-6 Fig. 7.1-1 VDD·VSS 라벨 + 사용자 확인 O-74 (2) | vdd/vss/agnd 1.8/0/0.9, Cc·CL·input_dc → agnd | 현 구성 유효, dual 근거 인용 추가 |
| two_stage_ota | single(사용자 확정 '5번') | Maloberti 2004 p.30·p.33 VDD/GND 라벨 | vdd/gnd 1.8/0 | 구성·인용 |
| two_stage_ota_sf | single | Allen Lecture 26 p.26-5 "(I5 + I7 + I9)VDD" | vdd/gnd 1.8/0 | 구성·인용 |
| cnr_ota | single 1.8 V | wulffern/cnr_ota_sky130nm @8c839f7 README "VSS Input Ground", "AVDD 1.7/1.8/1.9 V"; sim `VSS VSS 0 dc 0` | VDD_1V8/VSS 1.8/0 | 구성 문언(인용은 이미 있음) |
| erfc_ota | single 1.8 V | Wu 2025 p.1 "power supply of 1.8 V", p.12 | vdd/gnd/vcp/vcn(vcp·vcn = 원문 Fig.6 바이어스 전압, 중간 rail 아님) | 구성 문언 |
| r2r_opamp | **single**(사용자 확정 '3번') | Hogervorst 1994 p.8 Table I "Vsupply = 3.3 V" | VDD/VSS 1.8/0, RL·CL → VSS 유지 | `r2r_opamp.spec_source.md` 'RL의 다른 끝 = VSS로 둔 이유'(41~44행)의 근거 '엔진이 이상 전압원을 받지 않아 중간 끝을 만들 수 없다'를 '원래 topology에 중간 rail 없음(single, 사용자 확인 O-74 (2))'으로 정정(옛 근거는 사실도 아니다 -- 중간 끝은 `supply_nets` rail로 만들 수 있다, DEC-101 (2)) |
| rfc_ota | single 1.8 V | Matibag 2024 p.11 "Supply voltage: 1.8V" | vdd/gnd 1.8/0 | 구성 문언(인용은 이미 있음) |

**표 SD-T2 -- 데이터 변경**:

| # | 대상 | 변경 | 근거 | 결과 |
|---|---|---|---|---|
| D1 | `assets/library/current_reuse_telescopic_ota.sizing_spec.json` `human.element_values` Cf1·Cf2·Cs1·Cs2 | `"measurement_load": true` 추가(값·출처 그대로), `human.feedback.elements = [Cf1, Cf2]` 유지 | O-73, O-74 (3); 원문 Table I p.1 "Values for C1, C2, and CL: 500fF, 500fF, 1pF", Eq.(4) p.4 | 면적 고정 항 −2 pF ≈ −1.0e-9 m²(≈ −1000 µm², MIM 면적 밀도(PDK 선언) -- `external_network_inventory_13.md` §3), 보고 면적·GB4 면적 하한·layout(Cf/Cs 4개 미생성) 변경, spec 지문 변경, topology 불변 |
| D2 | `assets/library/rfc_ota.topology.json` `passive_elements`·`source_manifest` | 커패시터 `Cstab` 하나 추가(DUT 보상 C 0.5 pF, 연결 out–gnd -- CL과 병렬). 연결은 추론이다(p.35는 연결을 적지 않고 '부하에 더해 총 2.75 pF'라고만 적음) -- 이름·연결 사용자 확인(O-76 (3)); 반영 뒤 연결 표 재출력. **topology 연결 변경 -- 사용자 승인(O-74 (3))**. `source_manifest.passive_count` 2 → 3(검사 `E/authoring/source_manifest.py:7·34-35`), `source_manifest.figure`에 'p.35' 추가 | 원문 p.35(paper.md 1884~1890행) "500fF were added for a total of 2.75pF, to make the Recycling structure stable" | `connectivity_fp`·spec `meta.topology_hash` 변경, `rfc_ota.topology.md` 재생성 |
| D3 | `assets/library/rfc_ota.sizing_spec.json` `human.element_values` | CL = 2.25 pF `measurement_load`(출처 원문 p.11 요구 부하), `Cstab` = 0.5 pF(값 고정, `user_spec` + `origin: paper` + citation p.35, `measurement_load` 아님 -- DUT) | O-74 (3) | 면적 +0.5 pF ≈ +250 µm²(고정 항), out–gnd 총용량 2.75 pF 불변 -- 해석 값 불변 |
| D4 | 13회로 전부(사용자 확정 O-76 (2)) `human.supplies_v.source.record` | 원문 구성(single/dual)과 원문 인용(문서·쪽)을 `record` 문장에(표 SD-T1). nmcnr = 원문 ±1 V(p.602) 인용, pushpull·sf = dual 근거 인용. `origin`·`citation`은 선언 값의 출처 그대로(새 키 없음) | DEC-101 (1) | 값 불변, spec 지문 불변(`SpecSource` 지문 = `kind`만 -- `E/authoring/spec_model.py:5`, `E/authoring/SPEC_CONTRACT.md:204`) |
| D5 | `assets/library/r2r_opamp.spec_source.md` | 표 SD-T1 r2r 행 문장 정정(연결·값 불변) | O-74 (2) | 문서만 |

**착수 실측(순서 0)**: SD-M1 닫힘 -- `supplies_fp`의 `source`는 `kind`만 지문에 들어가므로(`E/authoring/spec_model.py:5`, `E/authoring/SPEC_CONTRACT.md:204`) D4는 지문을 바꾸지 않는다; SD-M2 닫힘 -- rfc_ota `source_manifest.passive_count: 2`(`rfc_ota.topology.json:15`)는 D2에서 함께 갱신; SD-M3 `r2r_opamp.topology.json` `RL._comment`에도 같은 낡은 근거가 있는데(`supply_config_audit_13.md` §2.12), 주석 정정이 `connectivity_fp`를 바꾸지 않을 때만 함께 고치고 아니면 spec_source만 고친다 **(미확인)**.

**표 SD-T3 -- 바뀌는 test·기준선(작성 = test 작성자, 판정 = 검증자; 작성자 ≠ 검증자)**:

| 자리 | 변화 | 처리 |
|---|---|---|
| `E/tests/integration/test_spec_library_load.py:96` `MEASUREMENT_LOADS["current_reuse_telescopic_ota"] = {"CL1", "CL2"}` | 기대 집합에 Cf1·Cf2·Cs1·Cs2 추가 | test 작성자 갱신(기대 출처 = O-74 (3)) |
| `test_spec_library_load.py:364-371` CI-10 기대(`CI10_FEEDBACK = ("Cf1","Cf2")`, `CI10_NOT_FEEDBACK = ("Cs1","Cs2")`) | 불변(`feedback.elements` 유지) | 확인만 |
| `E/tests/integration/test_j_rules_library.py:32` 'pm_ss_deg β(Cf1·Cf2)' | 불변(β 루프 유지) | 확인만 |
| `E/tests/integration/test_stage_b_library.py:218`(spec `measurement_load`를 읽어 면적 기대를 만듦) | spec 표지를 읽어 기대를 만들므로 자동으로 따라감(210~222행) | 확인만 |
| S0 기준선·결과 JSON(current_reuse 면적·GB4 하한·layout 소자 수, rfc_ota 면적·layout, 지문) | 변화 | 기준선 갱신은 동작 변경 승인 뒤(N6.3 변화표) |
| rfc_ota(옛 heldout, O-181 뒤 library) 엔진 test | `git grep rfc_ota -- gmid_engine/tests` 0건 -- 해당 없음 | -- |
| 오라클 smoke 산출물 `tools/spice_oracle/smoke/current_reuse_telescopic_ota.*`(`cf_external_impact.md` R4) | 기록물(판정 입력 아님), rfc 넷리스트에 소자 하나 추가 | 재생성 |
| `cf_external_impact.md` T1~T4 | Cf·Cs가 topology에 남으므로 T1·T2·T3·T4 모두 해당 없음(그 표는 topology 삭제 전제) | -- |

**IT-1·IT-2와의 관계**: SD-1은 `human.input_dc`를 바꾸지 않으므로 IT-1 범위(입력 DC 미선언 회로의 `input_tie` 제거)와 IT-0 대상 집합이 그대로다. nmcnr은 SP-2가 정해질 때(DEC-101 (2)로 기본값 = `{"net": "agnd"}`) 비로소 입력 DC 선언 회로가 된다 -- **지금이 아니다**. 그때 nmcnr은 IT-1의 미선언 집합에서 빠져 O-72 (3)의 입력 DC 선언 회로 갈래(as-built 입력 창 없음)로 옮겨가므로, SP-2 결정 card가 IT-1·IT-2 기준선의 nmcnr 행을 동작 변경으로 다시 잰다.

**IT-0 기록**: 발동 회로·수치는 history H1 'v6.25 둘째 커밋' 행, `()` 갈래 정렬은 N6.6 끝 '`feedback.elements = []`의 측정 구성 갈래'.

**IT-2 완료 조건 (10)(a) 문언**: 확정(사용자 결정 O-76 (2)) -- N6.6 (10)(a)에 반영했다(정적 검사 = 호출 구문만, 동적 호출 0회).

**실현 가능성 표(규칙 → 코드 근거)**:

| 규칙 | 기존 기계(file:line) | 상태 |
|---|---|---|
| 외부 소자 표지 = `measurement_load` | `E/authoring/spec_elements.py:9·37·66-71·84·95`(커패시터·저항만, true만) | 확인 |
| 표지 → 면적 제외 | `E/search/area_decl.py:42-47`, 호출 `E/pipeline/stage_b.py:167`·`E/search/search_context.py:180` | 확인 |
| 표지 → layout 제외 | `E/layout/passives.py:20`(`area_decl.excluded`), `E/layout/contract_input.py:169` | 확인 |
| 해석은 표지를 읽지 않음 | `git grep measurement_load` 엔진 소스 = authoring·search·layout·pipeline·metrics `records.py:299`(문서 문자열) | 확인 |
| 표지 + `feedback.elements` 함께 | `_feedback` `spec_elements.py:118-138`에 상호 배제 검사 없음 | 확인 |
| 이상 전류원 표지 불가 | `spec_elements.py:69-71`(`LOAD_KINDS`) | 확인 |
| 중간 rail = `supply_nets` + `supplies_v` | `E/graph/s1_structure.py:56`(`node.is_rail`), `E/authoring/spec_supplies.py`(넷 집합 = `supply_nets`) | 확인 |
| 이상 전압원 없음 | `E/graph/s1_values.py:29` `SUPPORTED_SOURCE_KINDS = ("current_source",)` | 확인 |
| 입력 DC 기준 = rail 넷 | `E/authoring/spec_input_dc.py`(`{"net": <레일>}`, `input_dc_net_not_rail`) | 확인 |
| 공급 구성 선언 자리 = `supplies_v.source` | `E/authoring/spec_sources.py` `SOURCE_KEYS`·`CITED_ORIGINS` | 확인(구성은 `record` 문장 -- 기계 키 없음) |
| 바이어스 기준 → 중간 rail | 원문 텍스트에 바이어스 기준 rail이 안 나옴(`supply_config_audit_13.md` §4) | **미확인** -- 회로별 적용은 원문 확인 뒤 |
| `supplies_v.source` 문구는 지문 밖 | `E/authoring/spec_model.py:5`, `E/authoring/SPEC_CONTRACT.md:204`(`SpecSource` 지문 = `kind`만) | 확인(SD-M1 닫힘) |
| rfc 개수 선언 갱신 | `rfc_ota.topology.json:15` `passive_count: 2`, 검사 `E/authoring/source_manifest.py:7·34-35` | 확인(SD-M2 닫힘) |
| 표지 → GB4 하한·출발 구간 면적 | `E/metrics/achievability.py:246-251`, `E/search/_helpers_area.py` → `start_intervals.py:43`·`iv_area.py:27` | 확인 |
| 응용 topology(2단계) 자리 | 스키마·writer 없음 | **미확인 -- 정본 자리 없음, AP-1 착수 전 계획 개정(S-7)** |

**graph 단일 정본 점검**:

| 항목 | 정본 자리 | 생산자 수 | 새 cache·사본 | 소비자 |
|---|---|---|---|---|
| 외부 소자 표지 | spec `element_values.<원소>.measurement_load`(기존) | 선언 1 → graph `passive_area_decl` writer 1 | 없음 | `passive_area_decl` → GB4 하한·평가·layout(기존) |
| `feedback.elements`와 표지 공존 | 두 선언, 정의 축이 다름(β 루프 대 면적·layout) | 각 1 | 없음 | 루프 뷰·잡음 / 면적·layout |
| 공급 구성(single/dual) | `supplies_v.source.record`(기록 전용, 계산값 아님) | 1 | 없음 | 엔진 소비자 없음 = **출력 전용 선언**(사람·감사용) |
| 중간 rail | topology `supply_nets` → S1 `node.is_rail`(writer `s1_structure`) | 1 | 없음 | S1 이후 기존 소비자 |
| rfc 보상 C | topology 원소 + spec 값(값 정본 spec, F5) | 1 | 없음 | 소신호 회로·면적·layout(기존) |
| 응용 topology | **없음** -- 만들지 않는다 | -- | -- | AP-1 계획 개정 뒤 |

**완료 조건**: (1) SD-T2 D1~D5 반영, spec 로드 통과(`element_value_declaration` 위반 0) (2) rfc_ota 연결 표 재출력·사용자 확인 기록 (3) 변화표(N6.3) -- current_reuse·rfc_ota 면적·GB4 하한·layout 소자 수·면적 제약 판정이 바뀐 점, SD-M1 결과에 따른 지문 변화 (4) 같은 θ 점(S0 기준선 점)을 다시 평가하면 해석 값(이득·PM·잡음·ICMR·스윙 등)의 변화가 0임을 두 회로에서 측정(DEC-100 (2)의 증거 -- 탐색 궤적·front 변화는 (3) 변화표 몫) (5) SD-T3 test 갱신은 test 작성자, 판정은 검증자 (6) **원점 이동 data 기록**(IC11 test는 엔진 변경 권한이 있는 card SF-1 완료 (5)로 옮김; SD-1은 data card라 test가 드러낸 엔진 결함을 고칠 수 없다): nmcnr 원점 이동 data 변경(있으면)의 기록만.

