# 낱말 diff 독립 확인 (285ec820 -> fc874bd6)

## @@ -12 +12 @@ plan_version: 6.38.3
- 지운 낱말 2073 / 더한 낱말 1930 / 공통 비 0.949
- [replace] 지움(3자, moved_text 원문 존재=True): «다섯째»
  더함: «커밋 여섯 = v1.15.1·v1.15.2 검증 지적 반영과 계획 v6.38.2·v6.38.3 반영(§3.11 신설·§3.1-1·§3.5·§3.6·§5·§10.5·§10.7 등), 일곱째»
- [replace] 지움(17자, moved_text 원문 존재=True): «v1.15.2 검증(81/100»
  더함: «손계산 원칙 단순화(측정·경위 서술을 evidence로»
- [replace] 지움(140자, moved_text 원문 존재=True): «`wt/_drafts/evidence/2026-10-29/design_v1152_validation.md`)·gap(93.3 %)의 오케스트레이터 재판정(`design_v1152_rejudge.md`) §2 반영: M-1 DUT 전력 근거 정정(정의는»
  더함: «끝 '변경 이력' 절);»
- [replace] 지움(252자, moved_text 원문 존재=True): «대기 P7), M-2 S 일반형 결합 용량 조건·fail-closed, M-4 측정(Rʳ = ∅ 9/9, 소자 안 고정점 회차·순환 발견 -- P5 대기), m-1~m-8, 신호 넷 술어 `bias_fixed_net` 하나로, `layer0_center` 출발 경로 자기모순 정리(P4 대기), D42 집계 212/154·ID 중복, §9 toy 자리, O-165 보존 문장 둘, CM 판별 밖 갈래, 사유 코드 소비자; 계획 v6.38.4 P1~P7»
  더함: «P1~P8»
- [delete] 지움(568자, moved_text 원문 존재=True): «첫째 커밋 = v1.15.1 검증(76/100 -- `wt/_drafts/evidence/2026-10-28/design_v1151_validation.md`)·gap(79.6 % -- 같은 폴더 `design_v1151_plan_gap.md`) 지적 반영: C-1 종속 키 수렴 = 키 벡터 전체 + 노드 풀이 재사용은 블록 안 local(§3.7-A 2-5 -- 원래 취지와 다름 4 철회), M-1 `finger_below_min`·W_min 제약 행의 역할(§3.7-A 5), M-2 측정 원자료 evidence 이관·재현 명령·보충 측정(§3.7-A 9), M-3 출발 단계 결과 자리·tol 표 구성 시점·`reachable_slices` L 인자(§3.7-A 5·7·8), M-4 되먹임 읽기의 정의·키 제외 비교(§3.7-A 2·6·11), m-1 `dc_finger` 빈 열 계약, m-2 B_r 계수 규칙, m-3 실현 기하 참조 전달, m-5 근거 문구, m-7 표 열 수; 계획 v6.38.2·v6.38.3 반영(§3.11 신설 등)과 class-AB S 판정(§3.5)은 둘째·셋째 커밋 --»
- [replace] 지움(23자, moved_text 원문 존재=True): «§5.12.7. 옛 판 Status 아래)»
  더함: «§5.12.7; 판별 경위 원문 = `wt/_drafts/evidence/2026-10-29/design_v1152/simplify/moved_text.md` S9)»

## @@ -1033 +1033 @@ RT를 고쳐도 색인은 필요하다(서로 다른 θ 비트는 다른 입력
- 지운 낱말 287 / 더한 낱말 50 / 공통 비 0.166
- [replace] 지움(9자, moved_text 원문 존재=True): «전력**(**계획»
  더함: «전력** -- **계획»
- [replace] 지움(11자, moved_text 원문 존재=True): «대기(P7)** --»
  더함: «대기(P7)**:»
- [replace] 지움(64자, moved_text 원문 존재=True): «정한다; 이 design은 후보의 물리 사실과 toy만 둔다. v1.15.1~v1.15.2 첫 초안 '레일 단자 합»
  더함: «정한다(후보»
- [delete] 지움(114자, moved_text 원문 존재=True): «Tellegen 소산'은 틀려 철회 -- 검증 M-1): (i) **물리 사실**(Tellegen -- 한 망의 **모든** 단자에서 Σ V·I = 그 망의 소산, 같은 기준 전위): DUT 단자 = 공급»
- [replace] 지움(43자, moved_text 원문 존재=True): «+ 출력 포트(입력 DC 전류 0). 그래서 레일 단자만 더한 합 P_rail»
  더함: «합(기준 0 V) / DUT 소산(모든 단자); 물리 사실·toy 수치»
- [replace] 지움(96자, moved_text 원문 존재=True): «Σ_k (V_k − V_0)·I_k,DUT는 DUT 소산 P_diss에 출력 포트 전력 (V_out − V_0)·I_out을 더한 값이고(항등식 P_rail − P_diss»
  더함: «`wt/_drafts/evidence/2026-10-29/design_v1152/m1_power/README.md`, 옛 상세»
- [replace] 지움(986자, moved_text 원문 존재=True): «(V_out − V_0)·I_out), 출력 DC 전류가 0이 아니면 기준 전위 V_0에 따라 바뀐다; P_diss(모든 DUT 단자)는 기준과 무관하다; 측정 부하까지 포함한 모든 공급원 전력 = P_diss + P_RL. (ii) **후보**(계획 P7 비교 대상): (가) P_rail, V_0 = 넷리스트 0 V 노드(spec 레일 절대값의 기준) 명시 (나) P_diss(모든 DUT 단자 -- 기준 무관). (iii) **수치**(`wt/_drafts/evidence/2026-10-29/design_v1152/m1_power ... DC와 무관, push-pull toy에서 Δ(가) = V_DD·ΔI_DD(손계산); 후보 (나) -- class-A toy에서 (나) = (가) − V_out·I_out(출력 DC에 따라 변함), 기준 전위를 옮겨도 불변; 두 후보 공통 -- 항등식 (가) − (나) = V_out·I_out. 계획 결정 뒤 그 후보의 toy만 SF-1 완료 조건에 둔다.»
  더함: «`wt/_drafts/evidence/2026-10-29/design_v1152/simplify/moved_text.md` S3).»
- [replace] 지움(13자, moved_text 원문 존재=True): «자리와 단자 기준은 계획»
  더함: «자리는»
- [replace] 지움(14자, moved_text 원문 존재=True): «정한다(새 상수·칸 0).»
  더함: «정한다.»

## @@ -1041 +1041 @@ RT를 고쳐도 색인은 필요하다(서로 다른 θ 비트는 다른 입력
- 지운 낱말 146 / 더한 낱말 106 / 공통 비 0.643
- [replace] 지움(18자, moved_text 원문 존재=True): «저항**(구조 규칙 셀 집합 S가»
  더함: «저항**(S가»
- [replace] 지움(79자, moved_text 원문 존재=True): «변수(우반면 영점 z = 1/(C_c(1/G_m(∞) − R)), G_m(∞) = Σ_{c∈S} gm_c -- §3.5 'S 일반형 판정').»
  더함: «변수.»
- [replace] 지움(120자, moved_text 원문 존재=True): «실측 성립(U-134 -- 출발값·좌반면 상쇄값이 도통 θ에서 모두 상자 안, `wt/_drafts/evidence/2026-10-28/u134_measure/`). 상자 상한(library 최대 약 6e25 Ω)은»
  더함: «U-134 (가) 성립 실측·상자 폭(상한 =»
- [replace] 지움(22자, moved_text 원문 존재=True): «수학적 포락이지 물리 상한이 아니다 --»
  더함: «포락,»
- [replace] 지움(57자, moved_text 원문 존재=True): «제약(저항 값 × PDK 저항 단위 면적, library 9/9 `area_search_m2` 선언)과»
  더함: «제약과»
- [replace] 지움(27자, moved_text 원문 존재=True): «GBW·PM 판정(O-172·감사 A11; 상자를»
  더함: «판정; 상자는 좁히지 않음 --»
- [replace] 지움(19자, moved_text 원문 존재=True): «결정 -- 이 판은 좁히지 않음).»
  더함: «결정)은 계획 U-134 행과 `wt/_drafts/evidence/2026-10-28/u134_measure/`(옛 상세 문장 = `wt/_drafts/evidence/2026-10-29/design_v1152/simplify/moved_text.md` S2).»

## @@ -1200,16 +1200 @@ RT를 고쳐도 색인은 필요하다(서로 다른 θ 비트는 다른 입력
- 지운 낱말 1121 / 더한 낱말 201 / 공통 비 0.103
- [replace] 지움(20자, moved_text 원문 존재=True): «집합과 일반형 판정**(v1.15.2»
  더함: «집합**(DEC-92 (3) 그대로»
- [replace] 지움(178자, moved_text 원문 존재=True): «계획 DEC-92 (3) v6.38.3 '한계'가 design에 맡긴 판정 'S 셀 집합에 AC로 같은 출력 노드를 구동하는 소자를 넣을지', 사용자 결정 O-172 (a)·감사 A10; 결과 = **넣지 않는다, 지금 연결 정의가 일반형이다 -- 규칙 변경 0**): - **S 정의**(DEC-92 (3) 그대로):»
  더함: «손계산 꼴; v1.15.2 단순화):»
- [replace] 지움(22자, moved_text 원문 존재=True): «끝(구동 쪽 끝 A, 출력 쪽 끝 B)에»
  더함: «끝에»
- [replace] 지움(30자, moved_text 원문 존재=True): «MOS(gate = A, drain = B)의 합집합;»
  더함: «MOS의 합집합이고,»
- [replace] 지움(53자, moved_text 원문 존재=True): «- **물리 결정자**(절점식): R이 없애려는 것은 보상 가지의 feedforward가 만드는»
  더함: «출발값 R_S = 1/Σ_{c∈S} gm_c은 교과서·원문의 손계산 꼴(2단 nulling resistor R_z = 1/gm -- 교과서 로컬 PDF 없음·쪽 미확인; nmcnr 원문 Leung 1999 p.2 Structure 4 'R_m = 1/g_m3' -- `assets/library/sources/nmcnr_amplifier__leung_1999/source.pdf`)이다. 다른 구조(결합 경로·T 망 등)에서 영점을 정확히 지우는 R과의 차는 출발점 품질에만 들고, R은 θ로 탐색되며 PM·영점은 봉인 `ss` MNA가 판정한다(DEC-74; 남는 차는 DEC-72 model_error 기록). 'AC로 같은 출력 노드를 구동하는 소자'(class-AB 부유 전류원 출력단)를 S에 넣는 안은 기각한다(그 안의 R은»
- [delete] 지움(137자, moved_text 원문 존재=True): «영점이다. A→B 전달의 영점은 능동망의 단락 전달 어드미턴스 y_21,act(s)(B를 교류 접지하고 A에 v_A를 걸 때 B로 드는 전류/v_A)와 보상 가지 어드미턴스 Y_c(s) = sC_c/(1 + sRC_c)가 같아지는 s다(정확식).»
- [replace] 지움(163자, moved_text 원문 존재=True): «무한대로 보내는 R(R_null)은 s → ∞의 균형으로 정해진다: **R_null = 1/G_m(∞), G_m(∞) = lim_{s→∞} y_21,act = Σ_{c: drain = B} gm_c·h_c(∞)**, h_c(∞) = A에서 소자 c의 gate 넷으로의 고주파 전압비(용량 분압»
  더함: «남김»
- [replace] 지움(455자, moved_text 원문 존재=True): «gate가 A면 1). gate가 A가 아닌 중간 넷 G의 h(∞) = C_AG/(C_AG + C_G)(C_AG = A–G 결합 용량, C_G = G의 그 밖 용량 -- 게이트·접합, 0이 아님)이다(검증 독립 기호 유도 `wt/_drafts/evidence/2026-10-29/design_v1152_validation/indep_zero/` -- C_AG가 있으면 R_null = 1/(gm16 + gm15·C_AG/(C_AG + C_G)), 수치 문턱 6/6 일치). **조건**: 중간 gate 넷이 A와 용량으로 결합하지 않으면(C_AG = 0) h(∞) = 0이고 G_m(∞)은 gate가 A에, drain이 B에 직접 닿은 소자만의 합 -- 위 연결 정의와 같다. **조건 밖의 판별·처리 = 계획 v6.38.4 대기(P2)**(검증 2 MJ-1 -- 최종 문언은 계획 정정 문언과 함께 정함; 아래는»
  더함: «절점식 근거·실측 `wt/_drafts/evidence/2026-10-29/design_v1152/class_ab_s/`).»
- [replace] 지움(28자, moved_text 원문 존재=True): «꼴 초안): 물리 결정자는 소자 종류가 아니라 A와»
  더함: «조건: A(구동 쪽 끝)와»
- [replace] 지움(9자, moved_text 원문 존재=True): «사이의 **고주파»
  더함: «사이에 고주파»
- [replace] 지움(222자, moved_text 원문 존재=True): «경로 C_AG**다 -- 선언 커패시터든, 한 단자가 A이고 다른 단자가 G인 MOS의 Cgs·Cgd든 같은 식(소스 팔로워로 G를 구동해도 R_null = 1/(gm1 + gm2·C_AG/(C_AG + C_G)) -- 검증 2 독립 유도 `wt/_drafts/evidence/2026-10-29/design_v1152_validation2/hinf_derive.out.jsonl`). 조건 밖이면»
  더함: «경로(선언 커패시터 또는 MOS Cgs·Cgd)가 있으면»
- [replace] 지움(120자, moved_text 원문 존재=True): «G_m(∞)을 과소평가해 R₀ = 1/Σ_S gm > R_null -- **결과 = 유한 좌반면 영점이 남고 상자 [1/max Σgm, 1/min Σgm](§3.1-1 (b))가 R_null을 벗어날 수 있음**이라»
  더함: «Σgm을 과소평가하므로»
- [replace] 지움(2자, moved_text 원문 존재=True): «S를»
  더함: «S는»
- [replace] 지움(228자, moved_text 원문 존재=True): «초안이다. gate가 A·G 어디에도 없고 채널 단자만 A·G에 닿는 MOS(Cds 결합)를 같은 조건에 넣을지도 P2 대기 -- library 실측: current_reuse M9a·M9b(부유 전류원, gate = 바이어스 넷, 채널 = Vop1·Vg15)가 이 꼴이라 넣으면 current_reuse Rz1·Rz2 경로가 fail-closed가 된다(선언 수동소자·Cgs/Cgd 결합 꼴은 library»
  더함: «초안이다(library»
- [delete] 지움(3075자, moved_text 원문 존재=True): «계획 DEC-92 (3) '한계' 문언 정정도 P2. 2단 Miller 교과서식 z = 1/(C_c(1/gm − R))(Razavi 'Design of Analog CMOS Integrated Circuits' 2nd ed. 2단 op amp 보상 절·Allen-Holberg 'CMOS Analog Circuit Design' Miller 보상 절의 nulling resistor 식 -- **로컬 PDF 없음(저장소 `assets/*/sources/`에 교과서 없음), 절·쪽 미확인**; 이 판정의 근거는 교과서가 아니라 절점식 정 ... op | Vom: M16(Vop1), M15(Vg15 -- M9a·M9b 부유 전류원 경유); Vop: M26(Vom1), M25(Vg25 -- M18a·M18b 경유) | {M16}, {M26} | {M16, M15}, {M26, M25} | 현행 R₀ = 1/gm16 = 정확 R_null(우반면 영점 없음 -- A–G 결합 용량 0 가정; M9a·M9b»
- [replace] 지움(25자, moved_text 원문 존재=True): «처리는 P2 대기); 'AC 구동 포함' R₀»
  더함: «꼴(current_reuse M9a·M9b)을 넣을지·최종 문언·계획 '한계' 문언은 **계획 v6.38.4 대기(P2)**. 9회로 S: two_stage {M6}, current_reuse {M16}·{M26}, nmcnr {M301}, 나머지 6회로 R–C 경로 0(판독 `wt/_drafts/evidence/2026-10-28/s_def_connectivity.txt`). 옛 판의 절점식·162점 훑기·적용표·측정 한계 서술»
- [replace] 지움(818자, moved_text 원문 존재=True): «현행의 0.21~0.80배(훑기) -- 우반면 영점을 남김 | | nmcnr_amplifier | Rm–Cm2: NodeS2 → Vout; Rm–Cm1: NodeM2 → Vout(T 망) | Vout: M301(NodeS2), M302(VB5 bias) | {M301} ∪ ∅ = {M301} | {M301}(합집합이라 같음) | 같음 -- 원문 R_m = 1/g_m3과 같음 | | common_gate_amplifier·folded_cascode·ngcc_3stage_ff·pushpull_follower_buffer·sf_pushp ... _A로 둠, CMFB·반대쪽 가지 생략)이고 SPICE 전회로가 아니다; A–G 결합 용량 C_AG = 0을 가정했다(C_AG ≠ 0이면 위 '조건' 식). 결론(R_null = 1/gm16)은 C_G > 0인 모든 매개값에서 정확식이라 매개값에 의존하지 않는다; 실제 회로의 영점 위치는 R이 θ이므로 MNA 판정이 정한다(출발값 규칙만 이 판정에 기댐).»
  더함: «`wt/_drafts/evidence/2026-10-29/design_v1152/simplify/moved_text.md` S1.»

## @@ -1347 +1332 @@ RT를 고쳐도 색인은 필요하다(서로 다른 θ 비트는 다른 입력
- 지운 낱말 73 / 더한 낱말 52 / 공통 비 0.816
- [replace] 지움(110자, moved_text 원문 존재=False): «2(v1.15.1의 'Rʳ 위에서 같으면 수렴'은 그 소자의 W·`w_key`·`dc_finger`가 서로 다른 슬라이스를 가리키게 두어 철회 -- 41 §5.12.7 원래 취지와 다름 4 철회).»
  더함: «2.»

## @@ -1362 +1347 @@ RT를 고쳐도 색인은 필요하다(서로 다른 θ 비트는 다른 입력
- 지운 낱말 74 / 더한 낱말 101 / 공통 비 0.834
- [replace] 지움(2자, moved_text 원문 존재=False): «폭)»
  더함: «폭 -- 계획 v6.38.3 DEC-105 (2) 문언 그대로; 손가락 폭과 다른 폭 슬라이스 값을 쓰는 점의 물리 정합(bin 안 전류 밀도 비 0.54~1.74)과 대체 꼴은 **계획 v6.38.4 대기(P8)**)»

## @@ -1388,19 +1373,2 @@ RT를 고쳐도 색인은 필요하다(서로 다른 θ 비트는 다른 입력
- 지운 낱말 1003 / 더한 낱말 121 / 공통 비 0.066
- [replace] 지움(637자, moved_text 원문 존재=True): «(b)): integ/it12 `d759838a`를 고치지 않고 import·런타임 계측(monkeypatch)만으로 library 9회로를 G-10 test(`tests/integration/test_g10_no_recompute_9circuits.py`)와 같은 흐름(선언 E_B 40, 시간 예산 600 s)으로 돌렸다(2026-10-28, 1회 실행). **원자료·재현**(검증 M-2): `wt/_drafts/evidence/2026-10-29/design_v1152/dcblock_measure/`(`run_one.py`·`d ... 재현 = 그 폴더에서 `bash driver.sh`(회로마다 `python run_one.py <회로>`, PYTHONPATH = 사용자 site-packages, Python 3.14.2, 엔진 = integ/it12 `d759838a` 읽기·import만, 결과 `results.jsonl` append) 뒤 `python make_summary.py`.»
  더함: «(b),»
- [replace] 지움(164자, moved_text 원문 존재=True): «아님(card WB-1 완료 조건 (5)의 독립 재측정이 정본). FD = `fd_jacobian` 안 평가에서 일어난 블록 호출. ngcc_3stage_ff는 단계 B까지만(review_needed) 돌아 FD 없음; current_reuse·sf_pushpull은 이 예산에서 FD 호출 0»
  더함: «아님»
- [replace] 지움(1519자, moved_text 원문 존재=True): «세 회로의 θ 전류 열 비율은 **보충 측정**(같은 폴더 `domain_ratio.py`·`domain_ratio.out.jsonl`, 2026-10-29, integ/it12 `b12792ab` import만 -- 탐색 변수 `sctx.domain.variables` 구성, L 칸 제외; 대조 two_stage_ota 3/11(정의역) 대 3/16(FD 첫 야코비안, L 칸 포함))으로 채웠다. | 회로 | FD 노드 풀이 calls / reuse 비(실측) | 노드 풀이 compute 평균 ms(실측) | 노드 풀이 compu ... ) | 아니오 | | two_stage_ota | 48 / 25 % | 64.3 | 7 % | 79 % | 3/16 | 0.58 / 2 % | 1/5 / 0~1/2 | 예 | | two_stage_ota_sf | 40 / 25 % | 70.0 | 2 % | 76 % | 4/19 | 0.56 / 0 % | 4~5/6 / 1/3 | 예 | - **읽는 법**:»
  더함: «v1.15.2 단순화: 표·측정 서술은 evidence로):»
- [replace] 지움(131자, moved_text 원문 존재=True): «reuse는 지금도 11~25 %뿐이고, 그 reuse의 거의 전부가 θ 전류 열에서 나온다(전류 열 노드 풀이 reuse = 그 열 calls의 78~100 %; 다른 열(ln IDu·y·L) reuse는 0~3회). 합친 블록은 이»
  더함: «reuse·벽시계·θ»
- [replace] 지움(13자, moved_text 원문 존재=True): «reuse를 잃는다 --»
  더함: «비율·유도 손실 표 = `wt/_drafts/evidence/2026-10-29/design_v1152/dcblock_measure/`(재현 명령·한계 포함), Rʳ·소자 안 고정점 회차 = `wt/_drafts/evidence/2026-10-29/design_v1152/m4_measure/README.md`, 옛 본문 = `wt/_drafts/evidence/2026-10-29/design_v1152/simplify/moved_text.md` S4. 판단에 쓰는 요지(손계산 속도 P4 재료일 뿐 정밀 요구가 아님): (i) 합친 블록의»
- [replace] 지움(12자, moved_text 원문 존재=True): «0.2~1.9 s(실행»
  더함: «= 실행»
- [replace] 지움(163자, moved_text 원문 존재=True): «%, 상계: LUT memo 적중으로 실제 재계산 비용은 compute 평균보다 작다; 실측 아님). 노드 풀이는 DC 커널 시간의 73~98 %라 재계산 1회 비용은 노드 풀이 평균(29~498 ms) 그대로다. - **야코비안이 돌 때의 손실**(보충 측정 ‡): 이 예산에서 FD가 없던»
  더함: «%(6회로, 상계), 야코비안이 도는»
- [replace] 지움(34자, moved_text 원문 존재=True): «야코비안 한 번에 14 전류 열 × 노드 풀이 498 ms ≈»
  더함: «1회당 약»
- [replace] 지움(380자, moved_text 원문 존재=True): «s(유도, 상계)를 잃는다 -- 9회로 중 가장 크다. - **블록 안 반복 회차 수**(계획 'design 입력' -- 검증 M-4·재판정 P5로 측정; 원자료 `wt/_drafts/evidence/2026-10-29/design_v1152/m4_measure/`(`m4_measure.py`·`m4_measure.out.jsonl`·`README.md`), integ/it12 `b12792ab` import만): (i) **노드 재풀이 = library 0** -- Rʳ 후보(범위 3a 뒤 남는 읽기 = 순환 SCC 수렴 허용오차 소자 가운데 종속 소자)를 S0 필드(`dc_scc_order`·`dc_writer`·`dc_coord`)로 정적으로 세면 **9/9 회로에서»
  더함: «s (ii)»
- [replace] 지움(36자, moved_text 원문 존재=True): «∅**(순환 SCC의 값 노드는 VGS writer(θ 쓰기 소자»
  더함: «∅ 9/9»
- [delete] 지움(120자, moved_text 원문 존재=True): «DEC-88) 아니면 θ y 뿌리(`free_window` -- 값이 식이 아니라 θ에서 옴)라 종속 소자가 허용오차 소자가 되지 않음; common_gate는 종속 소자 0 -- 검증 2 m-7) -- DC 블록의»
- [replace] 지움(79자, moved_text 원문 존재=True): «한 번이고, 노드 재풀이 수는 Rʳ ≠ ∅ 회로가 생길 때만(구현 뒤 `dc_scc_log.slice_rounds`) 잰다. (ii) **소자»
  더함: «1회 (iii) 소자»
- [replace] 지움(374자, moved_text 원문 존재=True): «고정점 회차**(봉인점 노드 고정 + 슬라이스 직접 조회, 회로당 봉인점 최대 5): nmcnr 15/15·pushpull 5/5 1회차 수렴; folded_cascode 20 소자-점 중 1회차 12·2회차 3·`finger_below_min` 2·**`slice_cycle` 3**; two_stage_ota 10 중 1회차 8·`finger_below_min` 2(4회차); two_stage_ota_sf 15 중 1회차 10·`finger_below_min` 4·**`slice_cycle` 1**(4회차); common_gate 종속 소자 0; current_reuse·sf_pushpull(봉인점 0)·ngcc(탐색 미도달)은 측정 불능. **발견 -- 계획»
  더함: «고정점은 측정된 회로에서 대부분 1~2회차이고, 봉인점에서 `slice_cycle`·`finger_below_min`이 생기는 경우의 처리는 **계획»
- [replace] 지움(577자, moved_text 원문 존재=True): «대기(P5)**: 순환은 두 기제로 생긴다(검증 2 m-7) -- (가) bin 경계를 넘는 m 전환(folded M3·M4 3건: 5 µm 슬라이스 W ≈ 5.5~5.8 µm > w_hi 5 µm → m = 2·w_f ≈ 2.9 µm → 3 µm 슬라이스 W ≈ 4.7 µm → m = 1 → 5 µm -- 같은 총 폭의 두 실현이 모두 자기 일관이 아님) (나) 같은 W-bin 안 가까운 슬라이스 왕복(two_stage_ota_sf M4 1건: 1.0 → 0.42 → 0.55 → 0.42 µm, 0.42·0.55 µm는 같은 pmos bin (0.42, 0.55] -- 같은 모델 bin이라 매개변수는 같고 슬라이스 W 차이만 있는 경우); 계획 DEC-105 (2)대로면 그 점과 `finger_below_min` 점은 지금 봉인되는데 새 블록에서 봉인 실패가 된다(동작 변경) -- 규칙을 바꿀지는 계획 몫이라 이 design은 계획 규칙(재방문 = fail-closed)을 그대로 둔다. (v1.15.1의 '추정 → 회차 ≥ 2'와 v1.15.2 첫 판의 '구현 전 측정 불능'은 이 측정으로 대체.) - **슬라이스별»
  더함: «대기(P5·P8)**. 정밀값(슬라이스별»
- [replace] 지움(28자, moved_text 원문 존재=True): «비용**(7): 이 측정은 기준 폭 슬라이스만 썼다»
  더함: «비용»
- [replace] 지움(11자, moved_text 원문 존재=True): «슬라이스별 표 비용은»
  더함: «Q-DC3, Rʳ ≠ ∅ 회로의 노드 재풀이 수 포함)은 card WB-1 완료 조건 (5)가»
- [replace] 지움(298자, moved_text 원문 존재=True): «측정(Q-DC3). - **측정 한계**: 시간은 1회 실행 값(같은 측정 두 번 사이 노드 풀이 평균이 최대 약 40 % 달라짐 -- 크기 정도로만 읽음); 실행 벽시계에 단계 A·B·컨텍스트 구성이 들어가 two_stage_ota_sf처럼 탐색 구간이 짧은 회로는 비율이 작게 나옴(탐색 구간 대비 노드 풀이 합은 34~96 %); 슬라이스 변경 추정은 제조 격자 반올림 없이 셌고 W < 3 µm(m = 1, 기준 bin 아래) 소자도 '바뀜'으로 셈; current_reuse·sf_pushpull은 봉인점 0이라 추정 없음.»
  더함: «다시 잰다.»

## @@ -1448 +1416 @@ RT를 고쳐도 색인은 필요하다(서로 다른 θ 비트는 다른 입력
- 지운 낱말 125 / 더한 낱말 52 / 공통 비 0.429
- [delete] 지움(3자, moved_text 원문 존재=True): «추가로»
- [replace] 지움(224자, moved_text 원문 존재=True): «`dc_solve`·`dc_finger`·`FingerGeom`·`FingerSlice`·`finger_slice`·`slice_of_finger`·`reachable_slices`·`slice_cycle`·`slice_missing`·`finger_below_min`(v1.15.2)·`RealizedGeometry.layout_ref`(v1.15.2)·`dc_scc_log.slice_rounds`»
  더함: «`dc_solve`·`dc_finger`·`FingerGeom`·`FingerSlice`·`finger_slice`·`slice_of_finger`·`reachable_slices`·`slice_cycle`·`slice_missing`·`finger_below_min`·`RealizedGeometry.layout_ref`·`dc_scc_log.slice_rounds`»
- [replace] 지움(12자, moved_text 원문 존재=True): «자리(test 파일)는»
  더함: «자리 =»
- [replace] 지움(41자, moved_text 원문 존재=True): «§9 v1.15.2 행. **계획 v6.38.4 대기(P3)** -- 아래»
  더함: «§9. toy 목록»
- [replace] 지움(241자, moved_text 원문 존재=True): «계획이 고친다(그때 이 문단·41 §9 WB-1 행을 맞춤). **계획 정정 후보**(보고만 -- 이 design은 계획 toy를 그대로 둠): 계획 WB-1 완료 조건 (1)의 '종속 소자 슬라이스 되먹임 toy(입력 포트 W4 뿌리 꼴)'는 범위 3a(E-13) 뒤 입력 창 되먹임이 없어져 노드 풀이 되먹임을 보이지 못한다(소자 안 고정점만 보임) -- 되먹임 toy는 'writer 없는 SCC 허용오차 꼴'로 충분; 'R⁰»
  더함: «41 §5.12.7(**계획 v6.38.4 대기(P3)**; 옛 문단»
- [replace] 지움(88자, moved_text 원문 존재=True): «∅ 회로에서 종속 소자 슬라이스가 기준 폭과 다름 → W·`w_key`·`dc_finger` 같은 슬라이스' toy 하나를 추가 후보로 올린다(검증 C-1).»
  더함: «`wt/_drafts/evidence/2026-10-29/design_v1152/simplify/moved_text.md` S5).»

## @@ -1865 +1833 @@ design이 정하면 안 되는 것(범위·회로 해석·판정 기준 변경)
- 지운 낱말 398 / 더한 낱말 381 / 공통 비 0.968
- [replace] 지움(27자, moved_text 원문 존재=True): «결정자**(v1.15.2 -- 계획 v6.38.3»
  더함: «결정자**(계획»
- [replace] 지움(14자, moved_text 원문 존재=True): «E-11; v1.15.1의»
  더함: «E-11 --»
- [replace] 지움(85자, moved_text 원문 존재=False): «'기준 넷 DC가 선언·고정 노드가 아니면 (ii)를 두지 않고 `cm_reference_undetermined` 보고'는 삭제 -- gap §3-2):»
  더함: «없음):»

## @@ -2478,0 +2447,3 @@ P N5.2의 DF는 옛 엔진의 결함 기록이고, 새 엔진에서는 재발 
- 지운 낱말 0 / 더한 낱말 65 / 공통 비 0.000
- [insert] 지움(0자, moved_text 원문 존재=None): «»
  더함: «## 변경 이력 -- v1.15.2 단순화(손계산 원칙, 2026-10-29) 사용자 2026-10-29 '같은 기준으로 과도하게 복잡한 부분 고쳐'(근본원칙: gm/ID 손계산 우선, 손계산 오차는 감수하고 DEC-72 model_error로 기록, 최종 확정은 SPICE 오라클, 물리 정합 = 말이 되는 동작점)에 따라 측정 서술·절점식 상세·판 경위를 evidence로 옮겼다. 분류표 = `wt/_drafts/evidence/2026-10-29/design_v1152/simplify/classification.md`, 옮긴 원문 = `wt/_drafts/evidence/2026-10-29/design_v1152/simplify/moved_text.md`(ID S1~S12), 적용 스크립트 = 같은 폴더 `simplify.py`. 규칙·정의·인터페이스 문장의 뜻은 바꾸지 않았다(낱말 대조 = 분류표 §3).»

## @@ -1502 +1502 @@ N_T = floor((B − T_used − T_reserve) / t_e
- 지운 낱말 170 / 더한 낱말 82 / 공통 비 0.548
- [replace] 지움(5자, moved_text 원문 존재=True): «재료(40»
  더함: «재료 요지 = 40»
- [replace] 지움(125자, moved_text 원문 존재=True): «9 -- 원자료 `wt/_drafts/evidence/2026-10-29/design_v1152/dcblock_measure/`·`m4_measure/`): FD 단계 노드 풀이 reuse 11~25 %(실측 6회로), 유도»
  더함: «9(유도»
- [replace] 지움(16자, moved_text 원문 존재=True): «0.2~1.9 s/실행(벽시계»
  더함: «벽시계»
- [delete] 지움(133자, moved_text 원문 존재=True): «LUT memo 적중을 빼지 않은 상계), 이 예산에서 FD가 없던 current_reuse는 야코비안 1회당 14 전류 열 × 498 ms ≈ 7 s(유도 -- 보충 측정). **블록 안 반복**(v1.15.2 측정 -- 검증 M-4):»
- [replace] 지움(172자, moved_text 원문 존재=True): «0(평가마다 노드 풀이 1회), 소자 안 고정점은 측정된 6회로에서 대부분 1~2회차(최대 4); 단 순환·`finger_below_min`이 봉인점에서 생겨 그 점이 새로 거부된다(**계획 v6.38.4 대기(P5)** -- 규칙 판단은 계획). 구현 뒤에만 잴 것 = Rʳ ≠ ∅ 회로의 노드 재풀이 수.»
  더함: «0; 측정 원자료 evidence).»
- [replace] 지움(15자, moved_text 원문 존재=True): «개정(DEC-105 (2))»
  더함: «개정»
- [replace] 지움(15자, moved_text 원문 존재=True): «충분(노드 재풀이 0 실측)»
  더함: «충분»
- [replace] 지움(34자, moved_text 원문 존재=True): «재검토(R1-b -- q1 회로에 평가 수준 키 반복이 남음)»
  더함: «재검토(R1-b)»

## @@ -1504 +1504 @@ N_T = floor((B − T_used − T_reserve) / t_e
- 지운 낱말 117 / 더한 낱말 27 / 공통 비 0.236
- [replace] 지움(39자, moved_text 원문 존재=True): «측정 부하가 중간 rail에 걸린 회로(library nmcnr 1)의»
  더함: «(계획 승인 질문으로 옮김)»
- [replace] 지움(61자, moved_text 원문 존재=True): «정의 선택은 계획이 정한다(이 질문은 계획 승인 질문으로 옮김). v1.15.2 초안의 근거 'Tellegen»
  더함: «재료»
- [replace] 지움(122자, moved_text 원문 존재=True): «레일 단자 합 = 회로 안 소산'은 **틀림**(Tellegen은 DUT **모든** 단자 합 = DUT 소산; 레일 합 = 소산 + 출력 포트 전력, 기준 전위 의존 -- 검증 M-1)이라 철회. 계획이 쓸 재료(40»
  더함: «40»
- [replace] 지움(266자, moved_text 원문 존재=True): «전력'·`wt/_drafts/evidence/2026-10-29/design_v1152/m1_power/`): 후보 (가) 레일 단자 합·기준 = 넷리스트 0 V (나) DUT 소산(모든 단자, 기준 무관); nmcnr 꼴 toy(출력 DC 0.9 ± 0.25 V) class-A (가) 108 µW 불변·(나) 96.5~114.5 µW, push-pull (가) 72~90·(나) 72~78.5 µW, (가) − (나) = V_out·I_out 정확 | 판정 보류(계획 몫)»
  더함: «전력' 참조»
- [insert] 지움(0자, moved_text 원문 존재=None): «»
  더함: «-- |»

## @@ -1506 +1506 @@ N_T = floor((B − T_used − T_reserve) / t_e
- 지운 낱말 188 / 더한 낱말 84 / 공통 비 0.353
- [replace] 지움(31자, moved_text 원문 존재=True): «아님 -- 계획 문언 또는 물리 판정의 직접 결과)**:»
  더함: «아님)**:»
- [replace] 지움(3자, moved_text 원문 존재=True): «**W»
  더함: «W»
- [replace] 지움(5자, moved_text 원문 존재=True): «점**(m»
  더함: «점(m»
- [replace] 지움(34자, moved_text 원문 존재=True): «W_min'; 옛 Q-DC2를 사실로 재작성, 검증 M-1):»
  더함: «W_min'):»
- [replace] 지움(9자, moved_text 원문 존재=True): «않음; W_min»
  더함: «않음(W_min»
- [replace] 지움(41자, moved_text 원문 존재=True): «행은 봉인점 연속 여유로 남아 SLSQP 경계 기울기·활성 보고에 쓰인다;»
  더함: «행의 쓰임 = 40 §3.7-A 11;»
- [replace] 지움(3자, moved_text 원문 존재=True): «항목.»
  더함: «항목).»
- [replace] 지움(10자, moved_text 원문 존재=True): «**class-AB»
  더함: «class-AB S: 'AC 구동 소자 포함' 안 기각,»
- [replace] 지움(23자, moved_text 원문 존재=True): «정의**(40 §3.5 'S 일반형 판정'»
  더함: «= 연결 정의(손계산 꼴)»
- [replace] 지움(58자, moved_text 원문 존재=True): «계획 DEC-92 (3) '한계'의 design 판정; 연결 정의 = G_m(∞)은 **조건부**(A–G»
  더함: «40 §3.5;»
- [replace] 지움(46자, moved_text 원문 존재=True): «0 -- 조건 밖 판별·처리 = **계획 v6.38.4 대기(P2)** -- 초안은»
  더함: «경로가 있으면»
- [replace] 지움(60자, moved_text 원문 존재=True): «`zero_cancel_s_coupled`, 선언 커패시터·Cgs/Cgd 결합 꼴은 library 해당 0,»
  더함: «`zero_cancel_s_coupled` 초안,»
- [replace] 지움(390자, moved_text 원문 존재=True): «결합 꼴(current_reuse M9a·M9b)을 넣을지도 P2; 검증 M-2·검증 2 MJ-1)): 'AC로 같은 출력 노드를 구동하는 소자'를 넣는 일반형은 영점 무한대 조건에서 **틀림**(절점식 정확해 R_null = 1/gm16, 훑기 162점 전부에서 일반형 R이 우반면 영점을 남김 -- `wt/_drafts/evidence/2026-10-29/design_v1152/class_ab_s/`) -- 지금 연결 정의가 일반형(고주파 전달 컨덕턴스 G_m(∞))이라 규칙 변경 0·사용자 결정 불요. 계획 DEC-92 (3) '한계' 문언(Σgm 과소, 물리 결정자 = AC 구동 소자 합)은 물리 근거가 바뀌므로 계획 정정 후보로 보고한다(이 design은 계획 규칙을 그대로 쓴다).»
  더함: «꼴 포함·최종 문언은 **계획 v6.38.4 대기(P2)**.»

## @@ -1508 +1508 @@ N_T = floor((B − T_used − T_reserve) / t_e
- 지운 낱말 51 / 더한 낱말 27 / 공통 비 0.128
- [replace] 지움(19자, moved_text 원문 존재=True): «판(v1.15.1) 질문 처리**:»
  더함: «판 질문**:»
- [delete] 지움(1자, moved_text 원문 존재=True): «위»
- [replace] 지움(27자, moved_text 원문 존재=True): «(1)(질문 아님 -- 검증 M-1). Q-DC4»
  더함: «(1), Q-DC4·Q-GL1»
- [replace] 지움(171자, moved_text 원문 존재=True): «삭제(사용자 승인 P-2 design 문언 변경은 계획 v6.38.2 후속 정정 표·승인 목록 C10으로 O-166에서 이미 승인 -- gap §2 (2)). Q-GL1 → 삭제(계획 v6.38.3 DEC-105 (1) 개정·U-133 기본안 (A) 승인 O-170 -- §6.4-1이 계획 문언 그대로).»
  더함: «삭제(O-166·O-170 승인으로 해당 없음). **원래 취지와 다름**(이 판이 새로 만든 것): 없음. v1.15.1 목록·처리 경위 = `wt/_drafts/evidence/2026-10-29/design_v1152/simplify/moved_text.md` S8.»

## @@ -1510,3 +1510 @@ N_T = floor((B − T_used − T_reserve) / t
- 지운 낱말 237 / 더한 낱말 125 / 공통 비 0.685
- [delete] 지움(499자, moved_text 원문 존재=True): «**원래 취지와 다름**(이 판이 새로 만든 것 -- 계획 승인 표지가 있는 항목(DEC-106, N6.35 행의 '원래 취지와 다름', U-133, X-LA8~X-LA12, O-157~O-160·O-162·O-168~O-170)은 계획 그대로 옮김이라 다시 세지 않음): **없음**. v1.15.1 목록 처리 -- 1(Q-GL1)·3(θ 상자 커패시터만) = 계획 v6.38.3 개정으로 계획과 같아져 해소; 2(Q-DC4) = 승인 O-166으로 해당 없음; 4(종속 키 수렴 Rʳ 좁힘) = **철회**(검증 C-1 -- 계획 '키 벡터 전체' 그대로, 40 §3.7-A 2-5); 5('θ점 전류 0' 판정 = 대칭 묶음 아래 basis 행 항등 0) = 계획이 판정 방법을 design에 맡긴 재량 안(gap §2 (5) -- 다르지 않음)이라 목록에서 뺌, 우연한 0 전류 처리(`resistor_current_zero` fail-closed)는 §5.3.3 'θ 저항'에 더함.»
- [replace] 지움(43자, moved_text 원문 존재=True): «문언(위 고지 (2) -- 정정 문언에 결합 용량 조건 h(∞) 포함, P2)»
  더함: «문언(P2)»
