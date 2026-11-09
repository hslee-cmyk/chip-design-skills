# design v1.15.2 독립 검증 (design-validator)

- 대상: worktree `wt/design-v115`, 브랜치 design/v115 HEAD `1fe06217`, 범위 `git diff ecd634d8 1fe06217`(커밋 3ec5a681·e6bc2a46·3b9103b2·1fe06217) -- D40·D41·D42, `gmid_engine/{convergence,sizing}/CONTRACT.md`
- 대조: 계획 v6.38.3(같은 worktree `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` -- DEC-92 (3) 291행, DEC-105 (2), SF-1 범위 8, N6.35), 이전 검증 `wt/_drafts/evidence/2026-10-28/design_v1151_validation.md`(76/100)
- 검증자: 작성자 아님. 작성자 보고·자기 점검표는 증거로 쓰지 않았다. 읽기·측정만(git `diff`/`show`/`log`, 문서 수정 0).
- 측정 자료(이 검증): `wt/_drafts/evidence/2026-10-29/design_v1152_validation/`
  - `full.diff` -- 검증 대상 diff 원문
  - `indep_zero/indep_zero.py`·`out.jsonl` -- class-AB 영점 **독립 정식화**(노드 어드미턴스 행렬 + Cramer 분자, 작성자 스크립트와 별개) + A–G 용량 결합 실험
  - `class_ab_rerun/` -- 작성자 스크립트 `class_ab_zero.py` 재실행(같은 인자 `symbolic sweep sweep_cgd`)
  - `qpw1/qpw1_toy.py`·`out.jsonl` -- Q-PW1 DUT 전력 정의 손계산 toy
  - `table_cols.py`·`table_cols.out` -- 표 열 수 점검, `judged_grep.txt` -- 낡은 `judged` 문언 grep

## 점수: 81 / 100

| 축 | 배점 | 점수 | 근거 |
|---|---|---|---|
| 이전 지적 해소 | 20 | 19 | C-1·M-1~M-4·m-1~m-5·m-7·m-8 해소, m-6은 계획 몫(정정 후보로 올림) |
| 내부 정합·낡은 문언 | 15 | 12 | m-1(낡은 문언 5곳), M-3(같은 양 두 자리) |
| graph 단일 정본 | 20 | 16 | M-3, m-5·m-8 |
| O-153·O-165·O-169 | 10 | 9 | m-2(W_min 행 보존에 비교 행 없음) |
| O-171 물리·회로이론 | 25 | 18 | M-1(Q-PW1 Tellegen 오용·toy 기대 틀림), M-2(S 일반형 조건 누락) |
| 승인 질문·계획 정정 후보 | 10 | 7 | M-4('측정 불능' 과대), Q-PW1 재료 오류(M-1과 같은 원인, 여기서는 재료 충분성만 셈) |

## 1. 이전 지적(v1.15.1, 76/100) 해소 여부

| ID | 판정 | 근거(현재 줄) |
|---|---|---|
| C-1 종속 키 수렴 | **해소** | D40:1343-1349 -- 수렴 = 종속 소자 키 벡터 전체(계획 DEC-105 (2) (ii) 그대로), Rʳ 위가 같으면 노드 풀이 재사용·Rʳ 밖은 소자 안 고정점, '결과 성질'(W·`w_key`·`dc_finger` 같은 슬라이스) 명시; 비교표 D40:1430-1433 (가)~(라), 원래 취지와 다름 4 철회 D41:1510, D42 D-WB1. 노드 풀이 재사용의 정당성 확인: 노드 풀이는 (θ, k|Rʳ)의 결정론 함수라 Rʳ 위 키가 같으면 같은 값·같은 Rʳ이 나온다(맞음). 계획 DEC-105 (2) (ii)도 '블록 안 local 반복(O-15 (E))'을 문언으로 승인 -- 3절 참조 |
| M-1 W_min | **해소** | D40:1364 `finger_below_min`(m = 1에서 w_f < W_min, 격자 정수 비교)과 `slice_missing` 정의 축 구분, D40:1365 W_min 제약 행 역할(c ≥ −½ 유도 맞음: w_f ≥ W_min, \|W − w_f\| ≤ g/2), Q-DC2 → 고지 (1) D41:1506 |
| M-2 측정 원자료 | **해소** | D40:1388 evidence 이관·재현 명령·엔진 커밋. `dcblock_measure/SHA256SUMS`·`class_ab_s/SHA256SUMS` 전부 OK(이 검증 `sha256sum -c`). 보충 측정 `domain_ratio.out.jsonl` 값(current_reuse 14/38, sf_pushpull 7/26, ngcc 9/22, two_stage 3/11)이 표 † 칸과 같음 |
| M-3 (a)(b)(c) | **해소** | (a) D40:1368 출발 블록 안 값·출발 정의 불능 기록 (b) D40:1379 LUT 적재 1회 -- 슬라이스 수 실측 nfet 18(W_min 0.42 µm 이상)·pfet 12(`lut_data/sky130_lut_v2/manifest.json`, 이 검증 계수 일치) (c) D40:1384 L 인자 |
| M-4 되먹임 읽기·키 제외 | **해소** | D40:1350 ②④를 정의(그 노드 값을 낸 식의 소자 tol_V 최솟값)로 재유도, ①③은 범위 3a로 소멸; D40:1374 상한 문장 철회(범위 5 준수); 비교표 D40:1434-1446 |
| m-1 `dc_finger` 빈 열 | 해소 | D40:1354 |
| m-2 B_r | 해소(단 m-5 참고) | D40:1378 |
| m-3 참조 전달 | 해소 | D40:1371 `RealizedGeometry(layout_ref, w_request)`, 비교표 D40:1440-1442 |
| m-4 스냅샷 규칙 5 | 해소 | D41:1841 |
| m-5 근거 문구 | 해소 | D40:1371 'LY3 정의' |
| m-6 병합 순서 소유 | 부분(계획 몫) | D41:1512 계획 정정 후보 (d)로 올림 -- design 단독으로 고칠 수 없는 계획 문언이라 적절 |
| m-7 표 열 수 | 해소 | `table_cols.out`: D40·D41·D42 불일치 0 |
| m-8 D42 집계 | 해소 | D42 §4: DEC 84→85(MISS +1), 설계 항목 203→217(MISS 147−1+13 = 159, N/A 3+2 = 5), 합계 302→317·MISS 184·N/A 11 -- 산술 일치 |

## 2. 내부 정합·낡은 문언

grep 대상(`use_macro`·`U-51`·`_box_centre`·`judged`·`spice_check`·`kvl_fixed`·`input_port_multiple_roots`·`input_status`·`cm_loop_unconstrained`·`cm_reference_undetermined`·`optional_stages`·`search_method`·`compensation_fixed_fallback`·`macro_root_missing`·`macro_rhp_start`·`resistance_bounds_ohm`·`k_max`) 중 v1.15.2 표지·'기록'·'삭제' 표지가 없는 줄을 하나씩 읽었다. 대부분은 '(기록)'·취소선·대체 표 안이라 정상이고, 표지 없이 현행처럼 읽히는 곳이 다섯이다(m-1). `kvl_fixed`·`spice_check`·`use_macro`·`macro_rhp_start`·`cm_loop_unconstrained` 남은 자리는 모두 삭제·기록 표지 안(정상). `k_max`의 D41:1022-1033은 SCC 고정점 상한(다른 양, 정상).

같은 양 두 정의: **판정 대상 집합**이 `is_judged`/`SizingSpecDoc.judged_constraints`(D40:1031)와 S0 그래프 필드 `graph/kernel: constraint_classes`의 `judged` 칸(D40:516·552, as-built `E/search/constraint_classes.py:43` `ConstraintClasses(judged, ss, notes)`) 두 자리에 있다 -- M-3.

## 3. graph 단일 정본

- 새/바뀐 필드: `gvgs_summary.off_vgs0`(writer `s1_gvgs`, 소비자 쓰기 계획·S1v 정지), `perf.solver_stops`(출력 전용, writer 결과 JSON 조립 한 자리), `dc_scc_log.slice_rounds`(출력 전용) -- writer 1·소비자 ≥ 1 확인(문서 수준). 새 cache·memo·sctx 슬롯·`EvalResult` 값 칸 0 확인(diff 전수 읽기).
- **C-1의 노드 풀이 재사용 = O-15 (E) 승인 예외 범위 안**: 회차 사이에 직전 회차 노드값·Rʳ을 블록 호출 안 지역 변수로 들고 있는 것뿐이고(호출을 넘어 남지 않음, 키·지문 없음), 계획 DEC-105 (2) (ii)·3이 '블록 안 local 반복(O-15 (E) -- 저장·cache 아님)'을 문언으로 둔다. 판정: 범위 안.
- 슬라이스별 tol 표: LUT 적재 메타 + U-87 디스크 파생표 예외 안(정상). B_r 계수 규칙: 식 불변·계수 규칙만(계획 '§2.4.6 식으로 다시 잰다' 위임 안) -- 단 m-5.
- 위반·미결: M-3(판정 대상 집합 두 자리), m-8(엔진 CONTRACT에 규칙 본문 복사 = 같은 규칙 둘째 자리).

## 4. O-153·O-165·O-169

- as-built를 근거로 보존한 문장: 새로 쓴 부분에서는 없음. '(as-built와 같은 종료)'(D40:1374)·'동작은 as-built와 같음 -- 값 변화 0'(D40:1350)은 동작 변화 서술이지 근거가 아님(단 후자는 자기보고 -- m-6).
- 엔진 인용 용도: 새 문장의 `E/...:줄` 인용은 모두 '지우는 것/재작성 범위' 또는 'as-built 갭 증거' 열 -- 허용 두 용도 안.
- '현행 유지'가 비교 없이 남은 자리: **W_min 제약 행 보존**(D40:1365 -- 정의·소비자 근거는 있으나 삭제안과의 비교 행 없음, m-2). §3.5 S 정의 '규칙 변경 0'은 물리 유도·대안 비교(일반형 기각)가 있어 O-165 충족(단 조건 누락 -- M-2).
- 엔진 디렉터리 CONTRACT 수정의 범위: convergence·sizing CONTRACT 변경은 '[개정 예정 -- design …]' 표지 안의 문구다(as-built 계약 본문 불변) -- 표지 갱신은 범위 안(v1.15.1 검증도 같은 판단). 단 sizing CONTRACT에 새로 넣은 'v1.15.2 보충' 문장은 design 규칙(키 벡터 재방문·`finger_below_min`·범위 3a)을 본문으로 옮겨 적은 것이라 같은 규칙의 둘째 자리 -- m-8.

## 5. O-171 물리·회로이론

### (a) class-AB S 판정(D40:1196-1215, 3b9103b2)

- **물리 결정자**: 보상 가지 A→B 전달의 영점 = 능동 단락 전달 어드미턴스 y21,act(s)와 보상 가지 Y_c(s) = sC_c/(1+sRC_c)가 같아지는 s. 우반면 영점이 사라지는 R 문턱은 분자 최고차 계수의 부호(= s→∞ 균형)로 정해진다.
- **topology 판독(이 검증 직접)**: `assets/library/current_reuse_telescopic_ota.topology.json` -- Cc1 = {Vom, N_cc_rz1}, Rz1 = {N_cc_rz1, Vop1} → A = Vop1, B = Vom. M16 nmos g = Vop1·d = Vom·s = gnd; M15 pmos g = Vg15·d = Vom·s = vdd; M9a pmos s = Vg15·d = Vop1; M9b nmos s = Vop1·d = Vg15; M8 pmos d = Vg15; M10 nmos d = Vop1. 작성자 모델과 같음. Vop1–Vg15 사이에 선언 커패시터 없음(Vop1에 닿는 수동소자 = Rz1뿐).
- **독립 유도**(`indep_zero/out.jsonl`, 노드 어드미턴스 행렬·Cramer -- 작성자 정식화와 별개): C_AG = 0에서 분자 최고차 계수 = **−C_G·C_c·(R·gm16 − 1)** → R_null = 1/gm16(작성자 결과와 기호까지 같음). 손풀이 확인(1극 근사 H(s) = k₀ω_G/(s+ω_G)): 분자 = C_c(1 − R·gm16)s² + [C_cω_G(1 − R·G₀) − gm16]s − G₀ω_G(G₀ = gm16 + k₀·gm15) -- R < 1/gm16이면 계수 곱이 음이라 우반면 근 하나, R ≥ 1/gm16이면 두 근 모두 좌반면. R = 1/G₀(일반형)는 1/gm16보다 작으므로 우반면 영점 하나가 남는다.
- **162점 재현**: 독립 스크립트 `indep_sweep_162` = 현행 R 우반면 0인 점 162/162, 일반형 R 우반면 ≥ 1인 점 162/162(작성자 주장과 같음). 작성자 원자료 대조: R* = 1.0092/gm16(401점 격자 한 칸 = ×1.0116 안), 일반형 R = 0.2077~0.7985배, Cgd 포함 시 feedthrough 우반면 영점 위치 비(현행/일반형) 1.019~215.4(n = 162) -- D40:1201 문언과 일치. 작성자 스크립트 재실행 결과는 아래 '재실행' 절.
- **조건(M-2)**: 독립 실험에서 A와 중간 gate 넷 G 사이에 용량 C_AG를 두면 R_null = (C_AG + C_G)/(C_AG·(gm15 + gm16) + C_G·gm16) = 1/(gm16 + gm15·h∞), h∞ = C_AG/(C_AG + C_G)(기호 정확해), 수치 문턱 R*가 이 예측과 0.5 % 안에서 일치(6/6). 즉 'G_m(∞) = gate가 A에 직접 닿은 소자만의 합'은 **중간 gate 넷이 A와 용량으로 결합하지 않을 때만** 성립한다. 설계 본문 '그 중간 넷의 용량이 s → ∞에서 그 넷을 교류 접지로 만들어 0'은 접지 용량만 보고 결합 용량을 빼먹었다. current_reuse는 결합 경로가 M9a·M9b의 Cds뿐이라(gate 용량은 바이어스 넷 = 교류 접지 쪽) h∞ ≈ 0 -- **library 9회로 결론은 맞음**, 일반 규칙 문장은 **조건부**.
- **교과서 근거**: Razavi, *Design of Analog CMOS Integrated Circuits* 2nd ed., §10.5 'Compensation of Two-Stage Op Amps'(nulling resistor, z = 1/[C_c(1/g_m2 − R_z)], R_z = 1/g_m2에서 영점 무한대) -- 쪽 번호 미확인, **로컬 PDF 없음**(저장소 `assets/*/sources/`에 교과서 없음 -- 이 검증 `find`). Allen-Holberg *CMOS Analog Circuit Design* 3rd ed. §6.2 'Miller Compensation' nulling resistor 식 -- 로컬 PDF 없음, 쪽 미확인(design도 '절 번호 미확인'으로 적음). 저장소 안 원문: Leung 1999(NMCNR) `assets/library/sources/nmcnr_amplifier__leung_1999/source.pdf` p.2 Structure 4(R_m = 1/g_m3 -- design 인용과 같음), Xie·Chen 2019 class-AB 2단 `assets/library/sources/current_reuse_telescopic_ota__xie_chen_2019/source.pdf` p.2-3 Fig.3('Rz' 표기, paper.md:249-314; Rz 값 식은 원문에 없음). Monticelli 1986(doi 10.1109/JSSC.1986.1052645)은 계획 표기대로 로컬 PDF 없음.
- **판정**: R_null = 1/gm16과 '일반형(AC 구동 포함) 기각' = **맞음(실측·독립 유도)**; 'S 연결 정의 = 일반형 G_m(∞)' 일반 규칙 = **조건부**(중간 gate 넷의 A 쪽 용량 결합 0일 때).

### (b) 나머지 규칙

| 항목 | 물리 결정자 | 식·출처 | 실측 | 판정 |
|---|---|---|---|---|
| DEC-106 입력 공통모드 한 점(D40:1707-1713) | 측정 구성 -- 한 차동쌍은 같은 공통모드 원이 구동, 두 입력 DC 차 = 계통 offset(계산 결과) | DEC-23 \|V_os\| ≈ \|V_out0 − V_ref\|/A_dc; 단일 출력 고이득 회로는 출력 DC가 y(θ)이고 offset이 그 결과로 유도됨 | 아니오(문서 대조) | **조건부 맞음**(단일 출력 회로의 출력 DC는 θ y로 두고 servo 측정 틀이 판정 -- 감사 A1 조건 그대로 본문에 있음) |
| CMFB 기준 결정자 Voc = (R2·Vom + R1·Vop)/(R1 + R2)(D40:1865) | 저항 분압 KCL | R1 = {Vom, Voc}, R2 = {Voc, Vop}(topology 판독) → (Vom−Voc)/R1 + (Vop−Voc)/R2 = 0 → 식과 같음; R1 ≠ R2면 DM→CM 누설 | 손계산 | **맞음**. 덧붙임(지적 아님): (i)+(ii) 두 등식이 함께 '오차 쌍 VGS 같음'을 강제하므로 오차 쌍이 같은 L·대칭 묶음이 아니면 W가 종속으로 정해짐 -- v1.15.1 승인 범위 |
| E-13 θ y = KVL 순서 창(VDS ≥ 0)과 +tol 포화 창 분리(D40:1690-1694, D41:657) | 포화 VDS ≥ VDSAT(> 0) ⊂ VDS ≥ 0 | 순서 창 ⊇ 유효점(손실 0), 포화 밖은 봉인 7 거부; 두 창은 판정 여유·범위·틀이 다른 양 | 아니오 | **맞음**(m-3: pmos 부호 표기) |
| `finger_below_min`(w_f < W_min)(D40:1364) | 제조 규칙 sky130 difftap.2(트랜지스터 확산 최소 폭 0.42 µm) | W_min 아래 bin 슬라이스(nfet 0.36·0.39)는 읽지 않음 | LUT manifest 확인 | **맞음** |
| DUT 전력 = DUT 단자 전류(Tellegen)(D40:1033, D41:1504) | 공급 레일에서 DUT로 드는 전력 | Tellegen은 **DUT 모든 단자**(레일 + 출력 포트)의 Σ V·I = DUT 소산. 레일만 더하면 = DUT 소산 + V_out·I_out(0 V 기준 출력 포트 전력)이고 기준 전위에 따라 값이 바뀜 | **예**(`qpw1/out.jsonl`) | **틀림(근거)·조건부(정의)** -- M-1 |

**재실행**(작성자 스크립트, `class_ab_rerun/`): 아래 '부록 A'에 결과.

## 6. 승인 질문 메모(D41:1496-1512)

- **Q-DC1**: 판단 재료 중 '블록 안 반복 회차 수 = 구현 전 측정 불능'(D41:1502, D40:1404)은 **일부만 정당**하다 -- M-4. (i) 노드 풀이 재계산이 생길 수 있는 회로(Rʳ ≠ ∅ = SCC 수렴 허용오차 소자 가운데 종속 소자가 있는 회로)는 as-built S0 필드(`dc_writer`·`dc_coord`·`dc_scc_order`)에서 정적으로 9회로 계수 가능하고, (ii) 소자 안 고정점 회차 수는 측정 자료 `dcblock_measure`의 봉인점(회로당 5개) 노드값을 고정하고 슬라이스 파일을 엔진 밖에서 직접 조회해(W = ID·L/IDu → `finger_slice` 규칙 → 다시 IDu) 잴 수 있다(엔진 수정 없음, DEC-104 (1′) (b) 꼴). 구현 뒤에만 잴 수 있는 것은 Rʳ 안 키가 바뀐 뒤의 노드 재풀이 횟수뿐이다.
- **Q-DC3**: 비용 산식(30 × 14~19 s ≈ 7~10 분)과 슬라이스 수 실측 일치, 구성 시점 판단(LUT 적재) 물리 근거 맞음. 충분.
- **Q-PW1**: 판단 재료가 **틀린 근거를 담고 있다** -- M-1. 기본안의 정의 자체(레일 단자 전력, 측정 부하 원소 제외)는 일관된 하나의 정의지만 'Tellegen = 회로 안 소산'은 이 정의가 아니고, toy 기대 '출력 DC를 옮겨도 DUT 전력이 측정 부하 전력만큼 흔들리지 않음'은 push-pull 출력단에서 거짓(아래 M-1 수치). 대안 (나)(다)의 ⚠ 판단도 그 근거에 기대므로 다시 써야 한다.
- 고지 (1)(2): 질문이 아니라 계획 문언·물리 판정 결과로 둔 판단은 맞음(단 (2)는 M-2 조건을 붙일 것).

## 7. 작성자 '계획 정정 후보'(D41:1512)와 숨은 계획 차이

| 후보 | 판정 | 근거 |
|---|---|---|
| (a) DEC-92 (3) '한계' 문언 | **타당, 조건 추가 필요** | 계획 291행 '물리 결정자 = 그 출력 노드를 AC로 구동하는 모든 이득 소자의 gm 합(우반면 영점 = Σgm/C_c)'은 C_G = 0 저주파 근사 -- 독립 유도로 틀림 확인. 단 정정 문언은 'G_m(∞) = Σ gm_c·h_c(∞), h_c(∞) = A에서 그 gate 넷으로의 고주파 용량 분압비; 결합 용량이 없으면 연결 정의와 같음'으로 조건을 담아야 한다(M-2) |
| (b) WB-1 완료 조건 (1) 입력 포트 W4 뿌리 되먹임 toy | **타당** | E-13 뒤 입력 창 되풀이가 사라져 그 toy는 노드 풀이 되먹임을 보이지 못한다. 덧붙여 계획 DEC-105 (2) (ii) 본문도 아직 '입력 창 되풀이가 종속 coord 소자의 슬라이스를 읽음'을 되먹임 경로로 적고 있어(같은 계획 안 E-13과 긴장) 함께 정정 대상 |
| (c) C-1 toy(R⁰ = ∅ 종속 소자 슬라이스 ≠ 기준 폭) | **타당** | 수렴 정의(벡터 전체)의 핵심 경우이고 지금 계획 toy에 없음 |
| (d) 병합 순서 의존 소유 문언(m-6) | **타당** | 구현 agent가 병합 상태로 분기하는 문언 |

숨은 계획 차이: (1) **판정 대상 집합의 저장 자리**(M-3) -- 계획 SF-1 범위 8은 '술어 하나, 저장 사본 없음, S1v·front·S-10이 같은 술어를 부른다'인데 design은 `constraint_classes.judged` 칸(그래프 필드)을 그대로 두어 '저장 없음'과 어긋나고, 계획 자체도 프로젝트 graph 규칙 1('계산값은 graph 필드로만, 다른 곳은 READS')과 긴장 -- design이 표지 없이 지나갔다. (2) 그 밖에 계획과 다르게 쓴 자리는 찾지 못함(DEC-106·E-01~E-35 design 몫 표 D40:1724-1760은 계획 행 ID 인용·이름만).

## 지적 목록

### Critical
없음.

### Major

**M-1. Q-PW1 'DUT 전력' 근거의 Tellegen 오용과 틀린 toy 기대**(D40:1033, D41:1504, D41:2107 SF-1 toy 행)
- 근거: Tellegen 정리는 한 망의 **모든** 단자에서 Σ V·I = 그 망의 소산이다. DUT 레일 단자만 더한 P_def = Σ_rails V_k·I_k,DUT는 DUT 소산 + V_out·I_out(출력 포트로 나가는 전력, 0 V 기준)이고, 출력 DC 전류가 0이 아니면 기준 전위를 옮길 때 값이 −V_ref·I_out만큼 바뀐다. 손계산 toy(`qpw1/out.jsonl`, nmcnr 레일 1.8/0/0.9 V·RL 25 kΩ): 출력 DC 0.9 ± 0.3 V에서 P_def − P_diss = V_out·I_out(−7.2~+14.4 µW)로 정확히 일치; push-pull 출력단은 δ = +0.3 V에서 P_def가 126 → 147.6 µW(+21.6 µW)로 흔들리고 P_RL은 3.6 µW -- '측정 부하 전력만큼 흔들리지 않음'은 판정 가능한 oracle이 아니다(class-A 출력단만 P_def 불변). agnd를 0 V로 옮기면 같은 점의 P_def가 270 → 259.2 µW(class-A, δ = +0.3)로 바뀐다(기준 의존).
- 수정안(원칙 점검: 새 상수·필드 0, 정의 하나, DC 양, fail-closed): 정의를 '**DUT 공급 단자 전력 = Σ_{k ∈ counted_rails} (V_k − V_0)·I_k,DUT, V_0 = 넷리스트 0 V 노드(spec 레일 절대값의 기준)**'로 기준 전위를 명시하고 이름에서 '소산'을 뺀다; Tellegen은 'DUT 소산 = 레일 단자 합 − V_out·I_out' 항등식(검산용)으로만 인용. toy 기대를 바꾼다: (i) class-A toy -- P_def가 출력 DC와 무관 (ii) push-pull toy -- ΔP_def = V_DD·ΔI_DD(손계산) (iii) 항등식 P_def − P_diss = V_out·I_out. 승인 질문 대안표에 (라) 'DUT 소산(Tellegen, 모든 DUT 단자 -- 기준 무관)'을 넣어 비교하고 ⚠ 판단을 새 근거로 다시 쓴다. 정의 선택 자체는 사용자 몫(Q-PW1 유지).

**M-2. class-AB S 일반형 판정의 조건 누락**(D40:1198·1200-1215, D41:1508 고지 (2), D41:1512 (a))
- 근거: 독립 기호 유도(`indep_zero/out.jsonl` `indep_symbolic_CAG`)에서 A–G 결합 용량 C_AG가 있으면 R_null = 1/(gm16 + gm15·C_AG/(C_AG + C_G)), 수치 문턱이 예측과 일치(6/6). design 본문의 's → ∞에서 중간 넷은 교류 접지'는 접지 용량만 본 결론이다. 결합 용량이 있는 회로(선언 커패시터로 출력 소자 gate를 A와 결합하는 class-AB 등)에서는 S 연결 정의가 G_m(∞)를 과소평가하고, R = 1/Σ_{S}gm은 우반면 영점은 없애지만(R > R_null) 유한 좌반면 영점을 남기며 상자 [1/max Σgm, 1/min Σgm](§3.1-1 (b))가 정확한 R_null을 벗어날 수 있다. library 9회로는 해당 0(current_reuse Vop1에 닿는 선언 수동소자 = Rz1뿐, M9a·M9b 결합은 Cds뿐).
- 수정안(원칙 점검: 일반 규칙의 조건을 물리로 명시, 회로 이름 0, 새 상수 0): (1) D40:1198 결정자 문장을 'G_m(∞) = Σ_c gm_c·h_c(∞), h_c(∞) = A에서 소자 c gate 넷으로의 고주파 전압비(용량 분압); 그 gate 넷이 A와 용량으로 결합하지 않으면 0 -- 연결 정의 S는 이 조건에서 G_m(∞)와 같다'로 고친다. (2) 판정을 '맞음(조건부)'로, 조건 위반 회로(선언 커패시터가 A와 S 밖 출력 소자 gate 넷을 잇는 경우)의 처리는 규칙 확장이므로 사용자 결정 질문으로 올리거나 그때까지 fail-closed(S 미정 → DEC-105 (10) (d))로 둔다. (3) 계획 정정 후보 (a) 문언에 같은 조건을 싣는다. (4) 측정 한계 절(D40:1215)에 'A–G 결합 용량 0 가정'을 추가.

**M-3. 판정 대상 집합이 두 자리**(D40:516·552 대 D40:1031)
- 근거: §2.4.8 표는 `judged_constraints`를 S0 그래프 필드 `graph/kernel: constraint_classes`(writer = 제약 분류 블록)에 둔다(as-built `E/search/constraint_classes.py:43` `ConstraintClasses(judged, ss, notes)`). §3.1-1은 같은 양을 `is_judged` 술어 + `SizingSpecDoc.judged_constraints` 계산 속성으로 두고 S1v·front·S-10이 '같은 함수를 부른다'고 한다. 같은 정의의 양이 저장 칸 하나와 호출부 여럿에 있어 graph 규칙 1·3과 계획 SF-1 범위 8 '저장 사본 없음' 양쪽에 어긋나고, 어느 쪽이 정본인지 design이 말하지 않는다.
- 수정안: 정본 자리를 하나로 정한다 -- (가) `constraint_classes.judged`를 그 양의 유일한 필드로 두고(writer가 `is_judged`를 한 번 부름) 소비자는 READS, 단 S1v 뷰 선택이 이 필드보다 앞 층이면 층 역전이므로 (나) `ConstraintClasses`에서 `judged` 칸을 지우고 spec 로더 단계의 결과(S0 입력, 사본 아님) 하나로 둔다. 어느 쪽이든 계획 문언('술어 하나·여럿이 부름')과 graph 규칙 1의 충돌은 design이 정하지 말고 **멈추고 보고**(CLAUDE.md 규칙 6) -- 계획 정정 후보 (e)로 올린다.

**M-4. Q-DC1 '구현 전 측정 불능' 표지의 과대**(D41:1502, D40:1404)
- 근거: 6절 -- Rʳ ≠ ∅ 회로 집합은 as-built S0 필드로 정적으로, 소자 안 고정점 회차는 봉인점 노드값 고정 + 슬라이스 파일 직접 조회로 엔진 밖에서 잴 수 있다(DEC-104 (1′) (b) 측정 꼴, 이미 `dcblock_measure`가 봉인점·W를 갖고 있음). 구현 뒤에만 잴 수 있는 것은 Rʳ 안 키가 바뀐 뒤 노드 재풀이 수뿐이다.
- 수정안: 두 양을 9회로로 재고 9 표에 칸을 더한 뒤 Q-DC1의 '판단 재료 부족' 표지를 '노드 재풀이 수만 구현 뒤'로 좁힌다(새 상수 0, 측정 = evidence 폴더, 판정 기록 아님).

### Minor

- **m-1 낡은 문언 다섯**: D40:51(색인 'U-51 결정 … §3.6 외층 보상 단 폴백' -- 삭제 표지 없음), D40:869(`_box_centre`를 '새 점을 만드는 곳'으로 열거 -- E-32로 출발 경로 삭제), D40:989(`spice_unverifiable` = '판정 제약(`judged`) 중' -- 지운 로더 칸 이름; `is_judged`로), D41:700(test interface 예시 리터럴 `Window(…, input_status="measured", tol_v=…)` 커널 뿌리 쪽 -- 4.7-V 표지 없음), D42:75(DEC-22 bisection '켜기 경로(`optional_stages` …)가 설계됐다' -- SF-1 범위 11로 칸 삭제). 각 자리에 v1.15.2 대체 표지.
- **m-2 W_min 제약 행 보존에 비교 행 없음**(D40:1365): 같은 물리 하한을 봉인(`finger_below_min`, w_f 기준)과 제약 행(W 기준, 반 칸 엄함) 두 정의로 둔다. 정의 축이 달라 규칙 3 위반은 아니나 O-165 의무 조항상 (가) 유지 (나) 삭제(봉인 + FD 반대 방향 규칙만) 비교 한 행을 §3.7-A 11에 더할 것.
- **m-3 순서 창 부호**(D40:1691, D41:657): 'VDS ≥ 0'을 pmos에도 그대로 적음 -- '채널 전도 방향 전압(nmos V_DS, pmos V_SD) ≥ 0'으로.
- **m-4 `reopen` 칸 '출력 전용' 표기 충돌**(D41:1270 대 §5.3.2): 같은 칸이 층 0에서는 고정 입력 지문에 들어가는 소비 대상이다. '외층 스냅샷에서는 소비자 없음(기록만)'으로 고칠 것.
- **m-5 B_r 계수 규칙의 메모리 영향 미기재**(D40:1378): 조회 하나를 도달 가능 슬라이스 수(nfet 최대 18)만큼 세면 상한이 최대 그 배수로 커진다 -- 식 불변이어도 메모리 상한 영향은 WB-1 완료 조건 (5)의 기록 항목으로 명시.
- **m-6 자기보고 표지**(D40:1350 '동작은 as-built와 같음 -- 값 변화 0'): 측정 없는 주장 -- '자기보고, WB-1 변화표에서 확인'으로 표지.
- **m-7 교과서 근거 표기**(D40:1198): Allen-Holberg '절 번호 미확인'만 있음 -- Razavi 2nd ed. §10.5 nulling resistor 식을 같이 적고 '로컬 PDF 없음(저장소 sources에 교과서 없음)'을 명시(원문 링크 규칙 -- 사용자 피드백 2026-10-13).
- **m-8 엔진 CONTRACT의 규칙 본문 복사**(`gmid_engine/sizing/CONTRACT.md` 144행 '[개정 예정]' 블록 안 'v1.15.2 보충' 문장): 표지 갱신은 범위 안이지만 design 규칙(키 벡터 재방문·`finger_below_min`·범위 3a)을 본문으로 옮겨 같은 규칙의 둘째 자리가 됐다 -- 'design 40 v1.15.2 §3.7-A 2·5 참조' 포인터만 남길 것(convergence CONTRACT 변경은 포인터 범위라 그대로 가능).

## 수정안 자기 점검

| 원칙 | M-1 | M-2 | M-3 | M-4 |
|---|---|---|---|---|
| graph 단일 정본(새 필드·cache·사본) | 0 | 0 | 정본 자리 하나로 줄임 | 0(evidence 측정) |
| 새 상수 | 0(기준 = spec 레일 기준 노드) | 0 | 0 | 0 |
| 회로 이름 조건 | 0 | 0(조건은 연결·용량) | 0 | 0(실측 기록에만) |
| DC/AC 분리 | DC 양 | AC 영점 | -- | -- |
| fail-closed | 정의 하나·toy 정정 | 조건 밖은 fail-closed 또는 사용자 결정 | 멈추고 보고 | -- |
| 계획과 다르면 계획부터 | 정의 선택은 사용자(Q-PW1 유지) | 계획 정정 후보 (a)에 조건 | 계획 정정 후보 (e) | 계획 무관 |
| O-171 실측 | `qpw1/out.jsonl` | `indep_zero/out.jsonl` | 문서·as-built grep | 측정 방법 제시(미실행) |

## 부록 A. 작성자 스크립트 재실행

작성자 `class_ab_zero.py`를 이 검증 폴더 `class_ab_rerun/`에 복사해 같은 인자(`symbolic sweep sweep_cgd`)로 다시 돌렸다(Python 3.14.2, numpy 2.4.6, sympy 1.14.0). 결과 326행이 작성자 `class_ab_zero.out.jsonl`의 같은 케이스 326행(`lut_fT` 64행 제외)과 **레코드 단위로 모두 같다**(`class_ab_rerun/compare.txt`: identical 326/326). sweep 162점: 현행 R 우반면 0 = 162, 일반형 R 우반면 ≥ 1 = 162. 독립 정식화(`indep_zero/`)와도 기호 결과·162점 셈이 같다. `lut` 케이스(f_T)는 다시 돌리지 않았다(LUT 값 인용만이고 판정에 쓰지 않음).

실행 메모: 이 환경에서 `timeout` 명령으로 감싸면 사용자 site-packages가 잡히지 않아 numpy·sympy import가 실패한다(재현 명령에 `timeout`을 붙이지 말 것).
