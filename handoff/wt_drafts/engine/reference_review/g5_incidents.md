# reference 검토 g5 -- known-incidents.md · consistency-map.md 대조 (2026-10-07)

- 범위: `skills/analog-gmid-design/references/known-incidents.md`(627행, 사고 1~24 전부 정독), `references/consistency-map.md`(1167행, 원칙 맵·마커 규약·고유 검증 항목·변경 이력 1차~48차 전부 정독).
- 대조 대상: `_drafts/user_decisions.md`(2026-10-07), `_drafts/engine/` NEW_ENGINE_DESIGN_REQUIREMENTS(REQ, 끝 '확정 사항'), ROADMAP(R), design_gb7_dc_canonical(G7), design_mod3_s1_graph(DS1), design_mod3_structure_u2_u5(DU), design_mod6_search_front(M6), design_mod7_layout(DM), PENDING_USER_DECISIONS(PUD), 계획서 v6.0 N4.1 IC1~IC11(P), master `gmid_engine/{authoring,graph,layout}/CONTRACT.md`, `tools/spice_oracle/README.md`.
- 실측(읽기만, 저장소 변경 없음): library 9회로 JSON에서 (a) 같은 kind·같은 비레일 source·서로 다른 gate 묶음 (b) 같은 kind·같은 비레일 gate·서로 다른 source 묶음을 Python으로 셌다(스크립트는 `$TEMP`에만). 결과는 G5-03·G5-04 근거.
- 표기: **[추측]** = 실측·원문 근거 없는 추론. 심각도 높음 = 합격 시험·정확도에 직접 영향.

---

## 1. 사고별 재발 방지 장치 유무 (사고 1~24)

상태: **있음** = 새 엔진 설계·계약·test에 구조적 장치가 있다 / **부분** = 일부만 / **없음**.

| 사고 | 교훈(한 줄) | 새 엔진 장치 | 위치 | 상태 | 관련 발견 |
|---|---|---|---|---|---|
| 1 | 함수 출력을 손으로 축약·재구성 금지 | 레이아웃 패턴 함수 본문 복사 + AST 해시 3자 대조, 결과는 graph 필드 | DM L10·2.1, layout CONTRACT 1절 | 있음(엔진) / 부분(리포트 MOD9 미설계) | G5-18 |
| 2 | 원문 도면 → 소자 표 먼저, 가정은 ⚠ 표시 | connectivity는 사용자만 수정, 정정 대기열 Q1~Q5, spec 값 출처 필수(F5) | user_decisions 131~143, DS1 8.1 | 부분(소스 대비 소자 수 대조 없음) | G5-22 |
| 3 | 검증된 시각화 코드(report_template) 재사용 | 없음 -- MOD9 `html.py` 신규, 8섹션·재사용 규칙 언급 없음 | REQ 3.1 report 행 | 없음 | G5-18 |
| 4 | 값이 논문에 없다고 스킵 금지, 모든 소자 값 확정 | R1·R2 엔진 계산(사용자 결정), GB5 보상 규칙, Rz=1/gm | user_decisions 143, R K7 | 부분(전 원소 값 완전성 게이트 없음) | G5-11 |
| 5 | 연결부를 끝까지 추적(사람이 메우는 지점 0, 재현, 최선) | 진입점 E2E(T1), 결정론 test(IC2), front | R 1.2 T1·T9, REQ 1.5 | 있음 | -- |
| 6 | self-test가 실제 회로 이름을 쓰면 load_topology로 역할·연결 먼저 assert | 엔진 소스 이름 리터럴 금지(`test_no_name_literals`). test 픽스처 쪽 규칙 없음 | REQ 1.4, DM 6 T1~T4(파일럿 이름 사용) | 부분 | G5-17 |
| 7 | 공유 엔진 계산 로직은 설계 논의·명시 승인 뒤 변경 | 확정 6 "사용자 승인은 회로 해석 항목만" | REQ 확정 사항 6, user_decisions 128 | **충돌** | G5-14 |
| 8 | 물리적 같은 노드 ≠ 기능적 그룹, matching base + 검증된 상속만 | 행 그룹 = "기둥 + matching 그룹에서 유도"(규칙 미정의). 차동쌍 규칙이 같은 노드 3소자를 못 가름 | DM 3단계 1, DU 3.2 | 부분/위험 | G5-03, G5-06 |
| 9 | 구조적 파트너의 role 선언 대칭 재검증 | role 태그 미사용(유도만), 대칭 사상 `graph.symmetry` | DU 4.1 | 부분(대칭 파트너 역할 동일성 test 없음) | G5-21 |
| 10 | diode-connected는 Vgs=Vds 자기일관 해석(connectivity로 판정) | W1 writer = diode drain 노드 bisection, `is_diode`=g==d | G7 2.3·3.4, graph CONTRACT 4.1 | 있음 | (G5-20 봉인 7 tol) |
| 11 | 게이트가 못 보는 조건을 '통과'로 믿지 말 것, kind 혼합 행 금지, 전기축≠레이아웃축 | 행 그룹을 (kind, body)로 먼저 분리, 복사 `build_graph`. IC5(docstring '검사하지 않는 것') 미이식 | DM 3단계 1 | 부분 | G5-09, G5-06 |
| 12 | N-way 매칭 그룹을 2-tuple로 쪼개 덮어쓰기 금지 | 그룹 레코드 단위 판정, T4(7소자 미러 1레코드) | DM 6 T4 | 있음 | -- |
| 13 | 선언 순서=처리 순서 암묵 계약 금지 | 쓰기 계획 Tarjan SCC 위상 순서, 결정론 test | G7 3.1-4 | 있음 | -- |
| 14 | 계산 필드 저장 누락(.update) 금지, 런타임 실측 | 불변 스냅샷·필드별 writer·입력 버전, 봉인 4 | G7 2.1·3.6, 확정 1·5 | 있음 | -- |
| 15 | 헤드룸 축(vsid)과 레이아웃 행 축 혼동 금지 | 행 그룹 유도가 "MOD3 기둥"(=KVL 축)에서 출발 | DM 3단계 1 | **위험** | G5-06 |
| 16 | 반복마다 이름 전역 유일 + repair 이후 커버리지 재검증 | 행 이름 = 그룹 id 기반, MOD8 매 반복 + 끝 coverage | DM 1(`_layout_result_to_rows` 미복사), 2 표, 5 | 있음 | -- |
| 17 | 새 메커니즘은 library 전 회로로 실행 검증 | 9회로 통합 test + 합성 topology metamorphic | DU 5.3, R T9 | 있음 | -- |
| 18 | 대칭은 복사가 아니라 connectivity로 유도, 2소자 공유 넷만 자동, 3+ review_needed | 유도만, `matching_offset` 3+ → review_needed, v1 '입력 DC 동일 가정' 기록 | DU 3.2, G7 3.1 | 있음(단 G5-03 부작용) | G5-03 |
| 19 | underdetermined 상호참조 검산(독립방정식 수) | W4 y 자유변수·DOF 표. IC6 강제 test는 GB4 축소로 빠짐 | G7 3.1-5, R 0.2(GB4 DOF 범위 밖) | 부분 | G5-08 |
| 20 | (a) diode/게이트 미러 인식 (b) 승격 1개씩 (c) 3-way hub 오판정·전류 0/음수 검출 | (a) gs_groups (b) BFS 1엣지씩 (c) 분기 노드 차수≥3. **전류 부호·0 검출 없음** | DU 1.2·3.2, G7 3.6 | 부분 | G5-02, G5-01 |
| 21 | DC 먼저·AC 위에서, 방향 = 신호경로 순서(보상이 정한 gm 소자는 건드리지 않음) | 커널 순서 ②③④⑤→봉인→ss→GB5. 종속 소자 선택은 diode 우선 + **이름 정렬** | G7 3.2·10 U1, DU J12-f | 부분 | G5-07 |
| 22 | 그룹 단일패스 대신 fixed-point worklist, 진전 판정 = 채워진 값 수 | Tarjan SCC + Gauss-Seidel + q 규칙·K_max | G7 3.4 | 있음 | -- |
| 23 | 일반 함수의 물리 기본값은 KVL/KCL 소속 확인 없이 위험, 무의미한 동작점(VDS 0.01) 경계 | 상수 리터럴 lint, VDS는 노드 차 파생. 봉인 7 허용 −tol_V(수백 mV 가능), 복사 floorplan 리터럴 예외 | REQ 1.3, G7 3.6, DM 2.2 | 부분 | G5-20, G5-12 |
| 24 | 중복 제거 ≠ 물리적 정확성, 단일 소스 값도 독립 오라클로 | 오라클 기대값(LUT npz·손계산·SPICE), 작성자≠검증자 | R 0.4, G7 8 | 있음 | (G5-16 문서 포인터) |

---

## 2. consistency-map 정합 규칙 대조 (원칙 맵 + 변경 이력에서 나온 규칙)

| 규칙(consistency-map 행) | 새 엔진 | 상태 | 관련 발견 |
|---|---|---|---|
| 21 함수 우선순위(harness→원소→새 코드) | 옛 harness 대신 새 진입점 `run_gmid_design_pipeline`, 레이아웃은 옛 함수 복사 | 원칙은 유지되나 **SKILL/맵이 옛 harness를 가리킴** | G5-15 |
| 29·16차/25차 coverage(이름 집합) + sizing_overrides 누락 | `coverage.py` 복사 + T8 Σnf·fw 보존 | 있음 | -- |
| 30 매칭 후보는 sub-block 구분 없이 전체 목록에 | S1 전역 유도 | 있음 | -- |
| 31 단일 전체 감사(소스 대비 총 소자 수 선언 포함) | 봉인 1~8 전체, coverage. 소자 수 매니페스트 없음 | 부분 | G5-22 |
| 33 floorplan 빈 공간 없는 2D packing, row-split 시 sizing/SPICE 되먹임 | `pack_floorplan_grouped` 복사, W 바뀌면 MOD8 | 있음(입력 일부 손실) | G5-13 |
| 34 행 재구성 시 pair 종류별 matching-safety(interdig/CC) 별도 검증, 손 재배열은 `check_walk_sequence` | `audit_row_split` 미복사, 행 접기·행 분할·floorplan 뒤 재판정 없음 | **없음** | G5-05 |
| 37 layout은 topology JSON에 담지 않음(사이징 결과) | 레이아웃 = graph `ly.*` 필드, topology = connectivity만(F5) | 있음 | -- |
| 37 `symmetry`(matching kind)를 topology에 데이터로 | 새 로더는 `symmetry` 무시, 유도만 | 의도적 변경(사용자 결정, 태그 미사용) | G5-03·04(유도 규칙 보강 필요) |
| 39 current_mirror = gate+source 그룹, diff_pair 역할 필터, 캐스코드 대칭쌍은 복합소자 상속 | gs_groups(gate+source) 있음. diff_pair 역할 필터 없음, 캐스코드 대칭쌍 그룹 없음 | 부분 | G5-03, G5-04 |
| 고유 검증(61~70) 'out of scope' 금지 | 결과 JSON에 소자·수동·이상원 값. 완전성 게이트 없음 | 부분 | G5-11 |
| 4·24차 넷 이름 대소문자 충돌 | 원소 이름 casefold만(authoring 3.8), 넷은 레일만(oracle C4) | **없음** | G5-10 |
| 7·8차 diffusion-safe split ≠ matching-safe split | `find_diffusion_safe_split_points` 복사, matching 재판정 없음 | 부분 | G5-05 |
| 8차 기능 그룹을 원자 유닛으로 packing | spine_groups = (kind, body)만 | 부분 | G5-13 |
| 9차 신호선 근접 배치(net_weights) | 어댑터 표에 net_weights 없음 | 없음 | G5-13 |
| 12차 box-shape PASS ≠ Euler 실현 | 행 접기(`apply_explicit_row_split`) 뒤 Euler 재판정 문장 없음 | 부분 | G5-05 |
| 13차 matching kind별 필수 게이트(mirror=3b, diff=3c), set 순회 비결정성 | 사용자 규칙(diff=CC 필수)·`canonical_row` | 있음(판정 장치는 G5-05) | G5-05 |
| 14·16차 branch_symmetric(게이트만 공유) = 행 swap 분배로 CC, 3c 필수 | 그룹 자체가 유도되지 않음 | **없음** | G5-04 |
| 15차 box = 행 폭 유사(하드), bbox 종횡비는 소프트 | `box_verdict` 행 폭 비 + "elongation"(정의 모호) | 부분 [추측: elongation이 종횡비면 15차 위반] | G5-05 비고 |
| 23차 `linked_topology_files` 병합(전체 구조 강제) | 비어 있지 않으면 거부(DEC-76) | 의도적 미이식 -- 부분 파일만 보는 사고(3차)는 거부로 재발 0 | -- |
| 32·36차 잔차 지표 결함(길이 1 행·격리쌍)·crossover 우선 정렬 | 복사본에 포함, 정렬 키에 isolated_pairs·crossover | 있음 | -- |
| 44·46차 다운스트림 소비자(workspaces) 확인, import≠call | 옛 엔진 동결, 새 엔진은 도달성 test(`test_reachable_from_entry`) | 있음 | -- |
| 47·48차 원문 재판독(가상 소자·반쪽 누락·극성·well 태그 오독) | 정정 대기열·사용자 확인 | 부분(엔진 대조 장치 없음) | G5-22 |

---

## 3. 발견 상세

### G5-01 [높음] SPICE 합격의 포화 검사가 'ID > 0 소자'만 본다 -- 꺼진 소자가 합격을 통과한다
- reference: known-incidents.md:440 "`I(M1)=0`이라는 물리적으로 틀린 값을 산출", 450 "'마지막 검증 패스'(bounds 중앙값 재평가로 전류 0/음수를 자동 검출)"; 266 "게이트가 그 조건을 볼 수 없어서 그냥 통과한 것".
- 새 엔진: `tools/spice_oracle/README.md` '합격 정의' 2 "ID > 0(`off_current_A` 가 있으면 ID > 그 값)인 모든 MOS 가 포화", C8; user_decisions.md:129 "SPICE 합격 = free 모드 스펙 만족 + **전 MOS 포화**".
- 유형: 결정 재검토(구현이 결정보다 좁음) + 빠짐. free 모드에서 바이어스가 무너져 소자가 꺼지면(ID≈0 또는 역방향) 포화 검사 대상에서 빠지고, 선언 제약이 없는 회로(folded·nmcnr·common_gate 등, R 1.3 '제약 0건')는 합격할 수 있다. `off_current_A`는 선택 인자라 기본은 ID>0 하나면 '전도'다.
- 보강안: (1) `oracle_compare.py` 합격 조건에 '엔진이 전도로 예측한 MOS(= `predictions.devices[].region != off`, 엔진은 `intended_region` 선언 없으면 전부 전도)가 SPICE에서도 전도'를 추가. (2) 전도 판정 문턱은 상수 대신 엔진이 소자마다 내는 값으로: 예 `off_current_A[dev]` = LUT에서 그 소자 (W, L, VDS, VSB)의 VGS=0 누설 ID(LUT 계산, 상수 아님)로 입력 스키마 필수화. (3) '꺼진 소자 = FAIL'을 C8에 명시하고 거부 픽스처 test(꺼진 소자 1개 회로) 추가.
- 누가: 합격 정의 문언 변경이라 **사용자 결정 필요**(결정 8 "전 MOS 포화"의 해석 확인). 문턱 식은 엔진 내부.

### G5-02 [높음] 엔진 봉인에 가지 전류 부호·0 검사가 없다 (사고 20 (c) 클래스)
- reference: known-incidents.md:440~441 "`m_cascode()`가 3-way hub ... `I(M1)=0`이라는 물리적으로 틀린 값", 449~450 "마지막 검증 패스 ... 전류 0/음수를 자동 검출".
- 새 엔진: G7 3.6 봉인 표(1 노드 충돌 ~ 8 kvl_branch) -- 전류 방향·크기 항목 없음. 봉인 7은 "ID > 0인 MOS"만 포화 검사(G7 3.6 #7)라 KCL로 0·음수가 된 소자는 검사에서도 빠진다. ② `block_currents`(G7 3.2-1)는 θ 전류 기저 bounds (0, …](M6 4.1)만 양수이고 KCL 차감으로 나오는 가지(예: 폴딩 노드 I_cascode = I_src − I_in)는 부호 보장이 없다.
- 유형: 빠짐(알고리즘). 합격(T3 봉인·T4 SPICE)에 직접 영향.
- 보강안: `sizing/seal/item9_branch_direction.py`(계산 블록 1 = 파일 1) 신설: 모든 MOS `device_id`가 kind별 전도 방향이고 |ID| ≥ tol_I(그 SCC) -- 위반은 `SealViolationError(item=9)`, margin = ID/tol_I(연속). M6 5절 제약 표에 '봉인 9 전류 방향'을 봉인 6·7처럼 연속 제약으로 노출(SLSQP가 경계로 밀 수 있게). 픽스처: 폴딩 가지에서 I_in > I_src인 θ → 거부(손계산).
- 누가: 엔진 내부.

### G5-03 [높음] 차동쌍 유도 규칙이 파일럿의 두 입력쌍을 차동쌍으로 못 잡는다 (사고 8과 같은 '물리적 같은 노드' 오판)
- reference: known-incidents.md:154~157 "`Vx`(stage-1 tail/diff-pair 공유 노드)에 `M58`(bias-gen 하우스키핑 소자, source=Vx)이 얹혀있다는 이유만으로"; 159~160 "'물리적 사실'과 '기능적 판단'을 구분 못 하는 자동추론 공통 패턴"; consistency-map.md:39 "우연히 같은 source+W를 갖던 diff_pair에 role 필터 추가"; consistency-map.md:160~161 "M4a/M4b -- Vy net을 M5와도 공유해 hub_merge로 분류됨".
- 새 엔진: DU 3.2 "**matching_offset**(차동쌍 후보): 같은 kind, 같은 비레일 source 넷, gate 가 서로 다른 MOS 가 정확히 2개면 derived, 3개 이상이면 review_needed", J-U4-b(DU 250행).
- 실측(library JSON): current_reuse `('pmos','Vx')` = M1a(Vip)·M1b(Vim)·**M58(Vbias2)**, `('nmos','Vy')` = M4a(Vip)·M4b(Vim)·**M63(Vbias3)** → 두 입력쌍 모두 3소자라 review_needed. 나머지 7회로는 정확히 2개라 통과.
- 영향: 사용자 규칙 "differential pair = common-centroid 필수"(user_decisions 120·122)가 파일럿 입력쌍에 적용되지 않고(matching group role이 diff_pair가 아님), 레이아웃 판정 축 면적(E4 (나))과 offset이 바뀐다. U2 ratify로 사람이 메우면 사고 5 '사람이 메우는 연결부'가 남는다.
- 보강안(일반 규칙, topology 무관): `graph/rel_matching.py`에서 같은 (kind, 비레일 source) 묶음의 멤버 중 gate가 '모든 뷰에서 교류접지'이거나 dc_role이 `bias_current_source`/diode 구동인 소자를 먼저 제외(사고 8 '병렬 소비자 배제'), 남은 멤버의 gate가 기본 전달 뷰의 신호 넷(여기 입력 포트 또는 `graph.symmetry` 대응쌍)인 소자가 정확히 2이면 derived. 이 경우 U3(dc_role)·U5(뷰)를 rel_matching보다 먼저 계산하도록 블록 순서 조정(DU 4.0 호출 순서). 회귀 test: 파일럿 Vx·Vy → diff_pair derived 2건, M58·M63는 제외 사유 기록; 합성 metamorphic(tail 노드에 바이어스 소자 1개 추가해도 diff_pair 유지).
- 누가: 규칙은 엔진 내부, 결과(제외 판정)는 U2 회로 해석 확인 대상.

### G5-04 [중간] 캐스코드 대칭쌍(gate만 공유, source 다름)이 matching group으로 유도되지 않는다
- reference: consistency-map.md:1004~1008 "M5/M6·M7/M8은 gate만 공유하고 source/drain은 서로 완전히 다르다('캐스코드 대칭쌍')", 978~980 "swap-대칭으로 분배 ... 실측 dx=0.00/dy=0.20 ... `branch_symmetric`은 이제 `diff_pair`처럼 3c가 필수 게이트", 39 "캐스코드 대칭쌍은 `find_stacked_matching_candidates()`(복합소자 상속)로 별도 커버", 163~165 "core_signal_cell의 전류거울 캐스코드 쌍(M2a/M2b, M3a/M3b)이 interdigitation FAIL".
- 새 엔진: DU 3.2 matching_ratio = "gate 가 레일이 아닌 `gs_groups` 묶음"(같은 gate **그리고 같은 source**), matching_offset = 같은 source. DM L8 matching 그룹 = 이 유도 출력.
- 실측: gate 공유·source 다른 묶음 = current_reuse M2a/M2b(+M58, M57), M3a/M3b(+M64, M63), folded M5/M6·M7/M8, nmcnr M106/M107, sf M5/M10·M7/M12·M13/M15 등 → 새 엔진에서 matching 대상이 아니다.
- 보강안: `graph/matching_groups.py`에 role `branch_symmetric` 추가 -- `graph.symmetry`(DU 4.1) 대응쌍이면서 gate 넷을 공유하고 source가 다른 같은 kind 쌍. 레이아웃 규칙: 공유 hub가 없어 interdigitation 불가(14차 실측)이므로 패턴 = 행 swap 분배 common-centroid(16차, 각 멤버를 두 행에 nf를 나눠 대칭 배치), 3c 필수. 복사 패턴 함수는 hub-leaf 전제라 쓸 수 없으니 `layout/pattern_branch_symmetric.py`(새 코드, 16차 규칙) + 손계산 test(dx=0, dy 기록).
- 누가: 엔진 내부(reference 확정 규칙). 대칭 사상 미해결 회로(J5)는 U2 확인.

### G5-05 [중간] 최종 행·floorplan 위의 matching-safety 감사와 행 접기 뒤 Euler 재판정이 없다
- reference: consistency-map.md:34 "box-shape를 위해 functional group을 여러 물리 행으로 새로 지을 때, matching-safety(interdigitation/common-centroid)까지 pair 종류에 맞게 별도 검증 -- Euler-validity/box-shape만으로는 ... 못 잡는다"; 1059~1061 "`check_box_shape()`는 finger 수 합만 비교해 Euler-realizability를 전혀 보장하지 않는다"; 1092~1096 "diffusion-safe 분할점이 있지만 matching-critical 행이라 그 지점에서 자르면 `verify_mirror_symmetry()`가 깨짐"; 166~168 "box-shape PASS·Euler-valid였지만 matching-safety는 전혀 확인된 적 없었던 상태".
- 새 엔진: DM 1 "복사하지 않는 SD 함수 ... `audit_row_split`(7004) ... (L8 위반)" -- 감사 기능 대체물 없음. DM 3단계 3 "행 안 그룹 배치들의 finger_w가 다르면 그 행을 finger_w별로 나눈다", 5단계 "`apply_explicit_row_split` n_rows = 2, 3, ...를 시도 ... 행 접기는 총 W 불변"(재판정 문장 없음), 6단계 floorplan.
- 유형: 빠짐. 패턴 함수의 residual은 '패턴 함수가 만든 행' 기준이고, 뒤 단계(finger_w별 행 분할·접기·floorplan 배치)가 그 대칭을 깨도 아무도 다시 재지 않는다.
- 보강안: `layout/matching_audit.py`(진입점 1, 필드 `ly.match[gid]`) -- 최종 `ly.rows`·`ly.floorplan` 좌표에서 그룹마다 3b(행 안 finger 인접: 멤버 쌍이 같은 행에서 이웃하는가)·3c(멤버별 finger 무게중심 dx·dy)를 계산, role별 필수 판정(diff_pair·branch_symmetric = 3c, mirror = 3b 또는 3c 중 선택한 패턴의 것), `audit_row_split`의 판정 정의를 선언 축 없이 그룹 레코드로 재작성. `rows.py` 5단계는 접은 행마다 `row_euler` 재실행 + `matching_audit` 재판정, 개선이 matching을 깨면 그 접기를 거부. MOD8 매 반복과 `run_layout` 끝에서 실행(사고 16의 '수리 뒤 재검증'). 부수: `box_verdict`의 'elongation'이 bbox 종횡비면 15차("box는 직사각형 포함, 종횡비는 소프트") 위반이므로 정의를 행 폭 비 하나로 고정 [추측].
- 누가: 엔진 내부.

### G5-06 [중간] 레이아웃 행 그룹 유도 규칙이 정의되지 않았고 '기둥'(KVL 축)에서 출발한다
- reference: known-incidents.md:162~166 "`matching_pairs`(선언된 것만)를 base union으로 ... 직렬로 얹힌 같은 kind 소자만 재귀적으로 union ... `M58`처럼 '같은 노드를 소스로 공유하는 형제(병렬 소비자)'는 ... 배제"; 266~270 "`vertical_stack_id`(전기적, KVL 헤드룸 축)와 물리 레이아웃 행(오일러 패스/대칭 배치 축)은 ... 항상 별도로 파생해야 하는 서로 다른 두 축"; 325~329 사고 15.
- 새 엔진: DM 3단계 1 "행 그룹: `row_groups`(MOD3 기둥 + matching 그룹에서 유도, (kind, body 넷)으로 먼저 분리 -- LR8)", REQ 3.3 `"row_groups": [... ]  // 기둥·matching group에서 유도`. MOD3 기둥은 레일 쌍 사이 노드-단순 경로 전부(DU 1.2-5, 파일럿 41개)라 소자가 여러 기둥에 겹쳐 들어가고, 겹친 기둥에서 서로소 행을 만드는 규칙이 없다.
- 위험: 파일럿 Vx 기둥(M6/M7 → Vx → M1a/M1b, M58 → …)에서 M58이 신호 소자와 한 행으로 묶이면 사고 8(공통 finger_w 없음)이 재현된다. finger_w별 행 분할(3단계 3)이 크래시는 막지만 행 구성이 전류 규모가 다른 소자를 섞는 것은 그대로다.
- 보강안: `graph/row_groups.py`(MOD3, 구조 유도 출력) 신설 -- (1) base = matching 그룹(G5-03·04 보강 후) (2) 같은 kind·같은 body에서 base 멤버와 **내부 2단자 넷**(DU kcl_group segment 경계, 분기 노드 아님)으로 직렬 연결된 소자만 재귀 편입 (3) 분기 노드(차수 ≥ 3)를 소스로 공유하는 형제는 편입하지 않음 (4) 남은 소자는 단독 행 그룹. 기둥은 헤드룸 축으로만 쓰고 행 신원으로 쓰지 않는다. test: 파일럿 Vx·Vy에서 M58·M63이 입력쌍 행 그룹에 없음, 합성 metamorphic(형제 소비자 추가 시 기존 그룹 불변).
- 누가: 엔진 내부.

### G5-07 [중간] 종속 gm_id 소자 선택이 '이름 정렬'에 의존 -- 사고 21의 신호경로 방향 원칙 미반영
- reference: known-incidents.md:464~466 "맞춰야 할 건 M301이 아니라 M204의 vds"; 478~482 "**`compensation.stage_devices` 배열의 신호경로 순서**(앞 stage=load, 뒷 stage=gm)가 방향을 정하는 진짜 기준이다 -- 태그만으로는 ... 구분 못 한다".
- 새 엔진: G7 10 U1 "diode 멤버가 writer(gm_id 독립), 나머지 종속. diode 없으면 이름 정렬 첫 멤버", U4·DU J12-f "kvl_branch 종속 멤버 ... 이름 정렬 첫 멤버", G7 3.1-2 BFS "같은 단계는 소자 이름 정렬".
- 유형: 잘못(원칙 위반 소지). 이름 tie-break 결과는 θ 매개화(어느 소자의 반전 좌표가 독립인가)·bounds·SLSQP 경로를 바꿔 front 연속값이 이름에 따라 달라질 수 있다. DU 5.3 metamorphic은 '개수'만 비교하므로 이 의존을 못 잡는다(대원칙 "topology에 종속된 엔진 금지" 측정 구멍).
- 보강안: 종속 선택 규칙을 구조 우선순위로: (1) diode (2) GB5 보상 규칙이 gm을 요구하는 소자·S1v stage 순서상 뒤 stage(AC 정본 gm) 소자는 독립 유지 (3) 대칭 사상 궤도 대표(대칭쌍은 같은 쪽 규칙) (4) 그래도 동률일 때만 이름. metamorphic test에 '이름 전단사 후 front 정규화 해시(이름 사상 적용) 동일'을 추가.
- 누가: G7 U1·U4는 이미 사용자 승인 항목 -- **사용자 결정 필요**(기본안을 위 구조 규칙으로 바꾸자는 제안).

### G5-08 [중간] 사고 19(underdetermined) 강제 test IC6이 새 설계에서 사라졌다
- reference: known-incidents.md:409~411 "`M2x.vds + M3x.vds = 상수` 방정식 하나에 미지수가 둘이라 상호참조 자체가 근본적으로 underdetermined"; 계획 P N4.1 IC6 `test_dof_catches_incident19_fixture`.
- 새 엔진: R 0.2 "GB4는 축소 ... DOF·수치 rank는 범위 밖", REQ·G7·M6 test 목록에 IC6 없음. 대신 G7 3.1-5 DOF 표·W4 y가 구조적으로 처리.
- 보강안: IC6을 GB7 `writer_plan`으로 재지정 -- 사고 19 픽스처(이름 없는 4소자 기둥, 미지수 2/등식 1)에서 DOF 표가 W4 y 정확히 1개를 내고, 과결정 픽스처(같은 노드에 W3 선언 + diode 등식)에서 종속 gm_id 또는 `StructureUnresolvedError`를 낸다. `tests/contracts/test_ic6_dof.py`.
- 누가: 엔진 내부.

### G5-09 [중간] IC5(게이트 사각, 사고 11) -- 새 엔진 게이트들이 '검사하지 않는 것'을 선언하지 않는다
- reference: known-incidents.md:266~269 "검증 함수가 실제로 무엇을 체크하는지(무엇을 체크 **안** 하는지)를 코드로 직접 확인하지 않은 채 '통과했다'를 결론의 근거로 삼지 말 것"; consistency-map.md:1059~1061(box ≠ Euler), 1094~1096(diffusion-safe ≠ matching-safe), 846~848(coverage는 이름만).
- 새 엔진: REQ 1절 구조 test 목록·G7 8.4·DM 6에 IC5 대응 없음. 복사한 `check_stick_diagram_coverage`는 이름 집합만, `box_verdict`는 행 폭만, 봉인 7은 ID>0만(G5-01·02) 본다.
- 보강안: `tests/structure/test_gate_blind_spots.py` -- `check_*`·`seal/item*`·`*_verdict`·`audit_*` 진입점 docstring에 '검사하지 않는 것:' 절과 `영역:` 줄 필수(계획 IC5 그대로), 복사 함수는 해시 때문에 docstring을 못 바꾸므로 `_copy_manifest.py`에 같은 정보를 행별로 둔다.
- 누가: 엔진 내부.

### G5-10 [중간] 넷 이름 대소문자 충돌 검사가 없다
- reference: consistency-map.md:1133~1136 "Stage-1을 만든 스크립트가 net 이름을 `Vbias1/VDD`(대문자)로, ... `vbias1/vdd`(소문자)로 -- 같은 물리 net을 다르게 이름 붙인 탓에 ... 미러 그룹에서 빠져"; 851~858 24차 "새 topology-JSON 파이프라인엔 아예 없었다".
- 새 엔진: authoring CONTRACT 3.8 `name_case_collision` = 원소(소자·수동·이상원) 이름만; oracle README C4 "대소문자만 다른 두 넷"은 레일 쪽 막힘만. 넷 전체 casefold 검사 없음.
- 보강안: `authoring/name_uniqueness.py`(또는 `_terminal_nets.py` 소비 파일)에 rule `net_case_collision` 추가 -- 모든 단자 넷 ∪ supply_nets ∪ 포트 넷에서 casefold 같고 글자 다른 묶음마다 hit. 자동 통일 없이 거부(24차와 같음). test: `Vbias1`/`vbias1` 픽스처 거부, 9회로 오거부 0.
- 누가: 엔진 내부.

### G5-11 [중간] 모든 원소의 값 확정 완전성 게이트가 없다 (사고 4, §1.5)
- reference: known-incidents.md:58~60 "모든 소자(능동+수동)의 값을 확정 ... 값이 없다고 스킵하지 않는다"; consistency-map.md:61~70 "'out of scope'/'범위 밖'으로 표기된 능동·수동 소자 값 ... FAIL".
- 새 엔진: R 1.1 출력 목록(수동소자 값, 이상원 값)과 T1 "결과 JSON에 1.1 출력 전부"는 있으나 원소 단위 판정 문장이 없다. authoring은 `value_*: null`(미선언)을 통과시키고(3.6), F5는 값 정본 = spec.
- 보강안: (1) S0 단계 `graph`(또는 `search/theta_schema`)에서 값 출처표 작성: 원소마다 {declared, spec, GB5 rule, θ 변수(DC 미선언 저항·R1·R2 등)} 중 정확히 하나, 없으면 탐색 전 `StructureUnresolvedError(unsupported_rule_branch, rule_branch="element_value_unresolved")`. (2) `tests/contracts/test_result_values_every_element.py`: 9회로 결과 JSON에서 MOS(W·L·nf·finger_w)·수동·이상원 값 null 0, 출처 필드 존재.
- 누가: 엔진 내부.

### G5-12 [중간] 복사한 floorplan 리터럴이 이제 판정 축(레이아웃 면적)을 좌우한다 (사고 23·24 클래스)
- reference: known-incidents.md:563~565 "일반화된 함수의 물리적 의미 있는 기본값 ... 확인 없이는 안전하지 않다"; 624~626 "중복 제거와 물리적 정확성은 서로 다른 축".
- 새 엔진: DM 2.2 "(b) 본문 내부 탐색 상한(`max_iters`, 두 `_MAX_*`, steps)은 결과 판정이 아니라 탐색 폭이라 복사본 그대로", layout CONTRACT 1.1 리터럴 표 `pack_floorplan` 0.3, 0.5, 2.0, 2.2, 40 / `_pack_by_subkind` 같음 / `evaluate_row_split_candidates` 0.6, 100. user_decisions 132 "12번은 (나)" -- front 점마다 floorplan 외곽 면적 A_L로 비지배 재필터.
- 유형: 잘못(전제 변화). DM 2.2의 '판정이 아니라 탐색 폭' 분류는 E4 (나) 결정 이전 전제다. 이제 A_L이 front 판정 축이고 동률 폭이 격자 한 칸(M6 6.4)이라, packing 내부 종횡비 목표·후보 문턱 리터럴이 판정 결과를 바꿀 수 있다.
- 보강안: (1) 호출 측 인자로 넘길 수 있는 리터럴(목표 종횡비·gap·steps)은 유도값을 넘긴다(종횡비는 사람 선언 또는 '판정 축 최소화'에서 유도) (2) 넘길 수 없는 본문 리터럴은 `tests/layout/test_floorplan_literal_sensitivity.py`로 무해성 실측: 리터럴을 ±한 격자 단계 바꿔도 9회로 A_L 변화 ≤ ΔA_tie임을 기록, 넘으면 (3) 해시를 깨는 본문 수정을 승인받는다.
- 누가: (1)(2) 엔진 내부, (3)은 복사 원칙(사용자 "기존 함수 이용") 예외라 **사용자 결정 필요**.

### G5-13 [낮음] floorplan 입력에서 기능 그룹·신호 근접 가중이 빠졌다
- reference: consistency-map.md:1097~1101 "`pack_floorplan()`이 기능 그룹(Stage-1/bias-gen/CMFB)을 전혀 모른 채 ... CMFB의 한 행을 Stage-1 사이에 끼워 넣은 사고"; 1082~1089 "`net_weights` ... 가중 거리 tie-break".
- 새 엔진: DM 2 표 "`spine_groups` = 행 그룹의 (kind, body 넷)(LR8), `mirror_pairs` = matching 그룹" -- 기능 그룹·`net_weights` 언급 없음.
- 보강안: `layout/floorplan.py` 어댑터가 `Structure`의 stage·블록(DU/REQ `stages.py`·`composite_blocks.py`)을 기능 그룹으로, S1 바이어스 넷(gate 공유 넷)을 `net_weights`로 넘긴다. 판정 축 면적(G5-12)과 함께 9회로 전후 A_L 기록.
- 누가: 엔진 내부.

### G5-14 [중간 · 결정 재검토] '사용자 승인은 회로 해석 항목만'이 사고 7 규칙과 어긋난다
- reference: known-incidents.md:142~145 "`stick_diagram.py`/`sizing_recipe.py`의 함수 로직을 바꾸는 작업은 항상 설계를 먼저 논의하고 명시적 승인을 받은 뒤에만 코드를 고친다"; 138~141 "한 번 바뀌면 ... 4개 토폴로지 전부의 사이징 결과가 동시에 바뀐다".
- 새 엔진: REQ 확정 사항 6 "E7 MOD 별 짧은 design, 사용자 승인은 회로 해석 항목만", user_decisions.md:128.
- 근거·판단: 새로 짓는 단계에서는 design 문서가 승인 단위라 충돌이 작다. 그러나 MOD가 구현·9회로 합격 뒤에는 core·sizing·metrics·search 계산 블록 변경이 사고 7과 같은 '전 회로 동시 변경'이다. 결정을 뒤집지 않고 범위만 보강하는 제안.
- 보강안(제안): "구현 완료된 공유 계산 블록의 알고리즘 변경은 9회로 전후 결과 차(노드전압·front·SPICE verdict)를 붙여 보고하고, verdict가 바뀌면 사용자 확인" 한 줄을 확정 사항 6에 추가.
- 누가: **사용자 결정 필요**.

### G5-15 [중간] SKILL.md·consistency-map·function-selection-map이 옛 harness를 정본으로 지시한다
- reference: consistency-map.md:21 "함수 우선순위 대원칙(harness → 원소 함수 → ...)", 275~279 harness = `run_sizing_pipeline`/`optimize_multistage`/`run_full_circuit_audit`/`audit_row_split`/`run_topology_pipeline`; 37행 `run_topology_pipeline()`/`save_instance_json()`.
- 새 엔진: user_decisions 119 "현재 엔진은 참고용 ... 계획서 내용으로 재설계", 정본 진입점 `run_gmid_design_pipeline`(REQ 3.2). 원칙 맵에 새 대원칙(graph 단일 정본·필드=캐시, 파일 규칙 A~D, topology 무종속, 상수 금지, SPICE 합격 정의, 레이아웃 규칙 (c)) 행이 없다. 변경 이력은 48차(2026-07-30)에서 멈춰 사고 8~24·2026-10-07 결정이 반영되지 않았다.
- 유형: reference 오류(오래됨) + 충돌. 사고 1·44차 클래스: 다음 agent가 skill 문서를 따라 옛 harness를 부르면 새 엔진이 '쓴 척만' 된다.
- 보강안: consistency-map 원칙 맵에 새 엔진 대원칙 7행 추가(반영 위치 = REQ 절·계약 파일·structure test 이름), 옛 harness 행에 `legacy (참고·대조 기준선)` 표기, SKILL '함수 우선순위 대원칙'의 harness를 새 진입점으로 바꾸는 개정안. known-incidents 각 사고 끝에 '새 엔진 대응: IC·test 이름' 줄(1절 표 그대로).
- 누가: 문서 반영은 엔진 내부, SKILL.md 원칙 문장 교체는 **사용자 결정 필요**.

### G5-16 [낮음 · reference 오류] known-incidents의 오래된 포인터·권고
- known-incidents.md:3 "절대 원칙 4개는 각각 아래 사고에서 도출" -- SKILL.md 65~73행 절대 원칙은 5개(5번 = 사고 5).
- 125~126 "실제 구현 예시: `sizing_recipe.py`의 `telescopic_class_ab` self-test(Phase 2에서 삭제 ...)" -- 예시가 삭제되어 따라 할 대상이 없다.
- 240~243·620~622 "`docs/01-plan/.../plan.md`(... §3 헤드룸 해석기 재설계)", "계획 §3 `_resolve_device_headroom()`" -- 계획 v6.0에 해당 절·함수 없음(grep 0). 새 엔진은 G7 W1 diode writer(3.4)로 대체.
- 501~502 "`vds_match_vgs_of`/`gm_id_match_vgs_of` 두 primitive를 재사용/일반화할 것" -- 새 엔진은 노드전압 단일 writer + 비트리 VGS 정합(G7 3.3)으로 이 둘을 일반화했으므로 권고 문언이 낡음.
- 414~417 사고 19 해결 "정확히 반씩 나눈다" -- 새 엔진은 W4 y를 탐색 변수로 둔다(G7 3.4). 균등 분배는 당시 휴리스틱이지 규칙이 아님을 명시해야 새 설계가 '사고 19 해법 위반'으로 오인되지 않는다.
- 보강안: 각 항목에 '새 엔진(2026-10-07) 대응' 주석 추가, 머리말 개수 정정.
- 누가: 엔진 내부(문서).

### G5-17 [낮음] 사고 6 클래스 -- test 픽스처가 실제 library 소자 이름을 쓴다
- reference: known-incidents.md:119~124 "실제 `library/*.topology.json`에 존재하는 특정 소자 이름 ... 참조하면 ... `load_topology(그 실제 파일)`을 호출해 ... assert로 먼저 검증".
- 새 엔진: DM 6 T1(M3a·M3b·M4a·M4b·M5), T2(M4a·M4b diff_pair), T3(M11b/M20b → M37a/M37b), T4(M18_bg 그룹); G7 10 U1(M3/M4) 등.
- 보강안: `tests/conftest.py`에 `library_device(circuit, name, expect_kind, expect_pins)` helper -- 실제 이름을 쓰는 test는 이 helper로 kind·연결·역할 가정(G5-03 유도 결과)을 먼저 assert. '수식 검증'과 '역할 배정 검증'을 다른 test 함수로 분리.
- 누가: 엔진 내부.

### G5-18 [낮음] 리포트 단계(MOD9)에 사고 1·3과 design-report-spec 규칙이 없다
- reference: known-incidents.md:43~45 "`report_template.html`은 ... 재사용해야 하는 검증된 구현체 ... `renderSchematic()`/`renderStack()` 본문은 한 줄도 새로 쓰지 않는다"; consistency-map.md:28·33 "8섹션 규격 ... §8 floorplan 필수", 32 "시각 검증 의무".
- 새 엔진: REQ 3.1 `report` 행 `html.py`(1) "결과 JSON·front 표·옛 instance.json 어댑터·HTML"만, design 문서 없음.
- 보강안: MOD9 짧은 design에 (1) `legacy/report_template.html`의 JS 렌더러를 레이아웃 패턴 함수와 같은 방식(본문 복사 + 해시)으로 가져옴 (2) 8섹션 존재·소자 커버리지 계약 test (3) 시각 확인 절차. 합격 시험 밖이라 낮음.
- 누가: 엔진 내부.

### G5-19 [낮음] 새 엔진 문서 사이 충돌 2건
- PUD.md:349 DF-14 "MOD7 matching 함수 재사용 방식 | 복사가 아니라 import 재사용" ↔ DM L10 "패턴 함수는 legacy import가 아니라 본문 복사 + 함수별 AST 해시 대조", layout CONTRACT(복사 구현 완료).
- PUD.md:370 "R D4 ... 판정 축 재필터는 보고만" ↔ user_decisions.md:132 "12번은 (나) ... (가) 보고만 해석 철회", M6 6.4.
- 보강안: PUD를 현행(복사+해시, 재필터 범위 안)으로 정정. consistency-map 방식대로 '반영 위치' 동시 갱신.
- 누가: 엔진 내부(문서).

### G5-20 [중간] 봉인 7 포화 여유가 −tol_V이고 gm/ID 역산 tol_V가 수백 mV면 선형 영역 소자가 봉인을 통과한다 (사고 23 교훈)
- reference: known-incidents.md:560~563 "'여유가 있다'와 'VDS 값 자체가 물리적으로 무의미하다(0.01V, 사실상 triode)'는 다른 문제 ... 그 동작점 자체가 무의미한지부터 확인할 것".
- 새 엔진: G7 3.6 #7 "VDS − VDsat ≥ −tol_V"; M6 4.2 "gm/ID 역산 지표 tol_V는 셀 p50/p90/max = nmos 222/286/402 mV, pmos 224/371/445 mV". D-1 (라)(ln ID/W, id_equivalent p50 3.7 mV)는 결정 대기.
- 유형: 잘못(허용오차 배정). D-1이 (가)로 남으면 엔진 봉인은 VDS가 VDsat보다 수백 mV 낮은 소자를 '포화'로 내보내고, SPICE free 합격(포화 여유)에서 떨어진다. (다른 g 검토와 겹칠 수 있음.)
- 보강안: 봉인 7 허용을 '그 VDS를 만든 조회 종류'의 tol이 아니라 VDsat 자체의 LUT 오차(`lut/vdsat.py` LOO)로 분리하거나, D-1 (라) 채택 시 id_equivalent 셀 tol로. 어느 쪽이든 봉인 7 기준 = SPICE 포화 여유 기준과 같은 정의(엔진·오라클 같은 정의 원칙, 결정 9).
- 누가: D-1이 **사용자 결정 필요**, 봉인 7 tol 분리는 엔진 내부.

### G5-21 [낮음] 대칭 파트너의 유도 결과 동일성 test가 없다 (사고 9·18)
- reference: known-incidents.md:200~202 "구조적 파트너가 있는지 먼저 확인하고, 있으면 둘이 같은 role을 받는지(또는 정당하게 다르다면 그 이유)를 항상 함께 검증"; 393~395 "connectivity로 강제되는 대수적 사실인지 검증 안 된 가정인지 먼저 구분".
- 새 엔진: DU 4.1 `graph.symmetry`(넷·소자 대응), DU 5.3 metamorphic(이름·순서·극성·복제·직렬) -- 대칭 대응쌍끼리 dc_role·셀·stage·matching·row 그룹 소속 비교 test 없음.
- 보강안: `tests/integration/test_symmetric_partner_consistency.py` -- `graph.symmetry`의 소자 대응쌍마다 dc_role·셀 종류·stage·matching 그룹 role·row 그룹 크기가 같고, 다르면 그 쌍이 `review_needed`로 기록되어 있는지. 값(노드전압 등) 동일은 요구하지 않는다(사고 18).
- 누가: 엔진 내부.

### G5-22 [낮음] 원문 대비 소자 수 대조(소스 매니페스트) 장치가 없다
- reference: consistency-map.md:31 "사이징 전 소스 대비 총 소자 수 선언", 100~113 47차(가상 소자 9개·Vop측 12개 누락·극성 오류, 41→51), 1124~1126 5차 "(c) 사이징 전 '소스 대비 총 소자 수'를 세는 이른 게이트 부재".
- 새 엔진: topology connectivity는 사용자 소관(정정 대기열), 엔진 로더에 원문 대조 항목 없음.
- 보강안(제안): topology 선택 키 `source_manifest{figure, device_count, passive_count}`(사람 선언) + 로더가 netlist 수와 대조해 다르면 거부. 또는 기존 메모리 절차(topology_to_markdown 표 출력·사람 재확인)를 SKILL DoD에 유지.
- 누가: 스키마 추가는 **사용자 결정 필요**.

---

## 4. 요약표 (심각도별 개수)

| 심각도 | 개수 | ID |
|---|---|---|
| 높음 | 3 | G5-01, G5-02, G5-03 |
| 중간 | 12 | G5-04, G5-05, G5-06, G5-07, G5-08, G5-09, G5-10, G5-11, G5-12, G5-14, G5-15, G5-20 |
| 낮음 | 7 | G5-13, G5-16, G5-17, G5-18, G5-19, G5-21, G5-22 |
| 합계 | 22 | 사용자 결정 필요 포함: G5-01, G5-07, G5-12(일부), G5-14, G5-15(일부), G5-20(D-1), G5-22 |

유형 분포: 빠짐 11, 잘못 4, 충돌 3, reference 오류 2, 결정 재검토 2(G5-01 구현-결정 차, G5-14).

대원칙과 충돌하는 reference 권고(그대로 따르면 안 되는 것):
- known-incidents 사고 19 '균등 분배'·사고 21 `vds_match_vgs_of` 재사용 권고 -- 필드=캐시·노드전압 단일 writer 구조로 대체됨(G5-16).
- consistency-map 23차 `linked_topology_files` 병합 -- DEC-76(발동 0 분기 미구현)과 충돌, 거부로 대체(재발 위험 없음).
- consistency-map 37행 `symmetry`를 topology 데이터로 -- 사용자 결정(태그 미사용·구조 유도)과 충돌, 유도 규칙 보강(G5-03·04)으로 대체.
- 복사한 floorplan 리터럴(사고 24 클래스)은 상수 금지 원칙과 충돌 -- 현재 manifest 예외로 묶여 있으나 판정 축이 된 뒤에는 근거 필요(G5-12).

## 5. 상위 5개 권고

1. **SPICE 합격에서 꺼진 소자를 막는다(G5-01)** -- 엔진이 전도로 예측한 MOS가 SPICE에서 꺼지면 FAIL, 전도 문턱은 LUT 누설에서 계산. 합격 정의 문언은 사용자 확인.
2. **봉인 9 '가지 전류 방향·크기' 신설(G5-02)** -- 모든 MOS `device_id`가 kind 방향이고 |ID| ≥ tol_I, 연속 margin으로 SLSQP 제약에 노출(사고 20 (c)).
3. **차동쌍 유도에서 바이어스 형제 소자를 먼저 제외(G5-03)** -- 파일럿 Vx(M58)·Vy(M63) 때문에 두 입력쌍이 review_needed가 되는 것을 구조 규칙(gate 교류접지·dc_role·입력 포트/대칭 대응)으로 해소, 사용자 규칙 '차동쌍 CC 필수'가 파일럿에 실제로 적용되게.
4. **레이아웃 최종 matching 감사 + 행 그룹 유도 규칙 명시(G5-05·G5-06·G5-04)** -- `matching_audit.py`(3b/3c, 접기·floorplan 뒤 재판정, 접은 행 Euler 재확인), `graph/row_groups.py`(matching base + 내부 2단자 넷 직렬 상속, 형제 소비자 배제, 기둥은 행 신원 아님), 캐스코드 대칭쌍 `branch_symmetric` 그룹과 swap 분배 CC.
5. **사고 대응 test 공백 메우기(G5-08·G5-09·G5-10·G5-11)** -- IC6을 GB7 DOF 표로 재지정, IC5 게이트 사각 docstring test, 넷 이름 casefold 충돌 거부, 전 원소 값 출처·null 0 계약 test.
