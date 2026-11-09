# g6 -- `references/design-report-spec.md` 대조 검토 (설계 보고서 사양 vs 새 엔진)

- 작성 2026-10-07. 읽기 전용 검토(저장소·코드 수정 없음).
- 맡은 문서(전문 정독, 610행): `chip-design-skills/skills/analog-gmid-design/references/design-report-spec.md`(이하 **DRS**). 구성: PRE-FLIGHT 1~27(1~174행), §1.6 단일 게이트(183~226), §1.7 floorplan 피드백 루프(228~382), §0(384~391), §1 필수 8개 섹션(393~428), §1.5 커버리지(430~529), §2 레이아웃 가이드 7항목(531~563), §3 이중 가독성(565~581), §4 시각 검증(583~604), §5(606~610).
- 대조 대상(약칭): **UD** = `wt/_drafts/user_decisions.md`(2026-10-07), **NR** = `wt/_drafts/engine/NEW_ENGINE_DESIGN_REQUIREMENTS.md`(맨 끝 확정 사항 우선), **DM7** = `design_mod7_layout.md`, **DM6** = `design_mod6_search_front.md`, **DM3** = `design_mod3_structure_u2_u5.md`, **DSF** = `design_spec_format.md`, **R** = `ROADMAP.md`, **P** = 계획서 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(v6.0, 현재 파일 행 번호), **LC** = `gmid_engine/layout/CONTRACT.md`, **SO** = `tools/spice_oracle/README.md`, **SD** = `legacy/stick_diagram.py`, **DR** = `legacy/design_report.py`.
- 표기: [추측] = 실측·원문 근거 없는 추론. 심각도: 높음 = 합격 시험(P N6.2 T1~T9)·정확도에 직접 영향, 중간, 낮음.

---

## 0. 먼저 -- DRS와 이미 맞는 것 (보강 불필요, 근거만)

| DRS 요구 | 새 엔진 쪽 | 판정 |
|---|---|---|
| 리포트 데이터를 손으로 옮기지 말고 함수 결과를 직렬화(212~218행) | NR 확정 1·3: graph 필드가 단일 정본, 결과 JSON·S3는 필드 직렬화 | 맞음(원리 같음) |
| 정본 데이터 1벌·net 이름 드리프트 금지(195~198, PRE-FLIGHT 9·11) | topology.json 단일 소스 → S1 한 번 생성(NR 3.3, DM3) | 맞음 |
| import≠call(PRE-FLIGHT 27 원인3) | NR 1.8 `test_reachable_from_entry` | 맞음 |
| Euler 시작 노드 비결정성 수정(364~368) | LC 2절 `canonical_row`(정렬 시작 노드), DM7 7절 | 맞음(더 엄격) |
| 사람이 재배열한 순서는 `check_walk_sequence`로 검산(PRE-FLIGHT 25) | DM7 3단계 4: 패턴 결과를 `check_walk_sequence`로 검산 | 맞음 |
| 패턴은 손으로 짜지 말고 `common_centroid_layout` 결과 rows 그대로(483~489) | DM7 L3·L10 복사 함수 사용 | 맞음 |
| 실패를 숨기지 않고 근본원인과 함께 보고(356~362) | DM7 L7(전 그룹 판정), 실패 레코드 N3.14 | 맞음 |
| 커버리지 함수 harness화(PRE-FLIGHT 27 원인2) | LC `coverage.py` 복사, DM7 3단계 7, LR9 | 맞음(입력 독립성은 G6-15) |

---

## 1. 발견 목록

### G6-01 [충돌] 계획서 합격 시험 T4·마일스톤 1이 "노드전압 tol_V 안"을 합격 조건으로 남김 -- 오늘 사용자 결정과 반대 | **높음**
- reference: DRS 402행 §1 표 6 "SPICE 결과 ... 가 §5 체크리스트의 **원 스펙을 여전히 만족**하는지" -- 합격 축은 스펙이다(사용자 결정과 같은 방향).
- 새 엔진 쪽: P 1087행 T4 "노드전압이 S2 `dc`와 tol_V 안, ID > 0인 모든 MOS 포화", P 1078행 마일스톤 1 "free 모드 SPICE에서 노드전압이 S2 `dc`와 tol_V 안". 반면 UD 129행(8번 수정안) "SPICE 합격 = free 모드 스펙 만족 + 전 MOS 포화. 노드전압·소자 ID/gm/gds·성능 차이는 **기록**", P 458행(N3.6 정정본)·SO "합격 정의"도 기록만.
- 유형: 충돌(계획서 내부 + 사용자 결정). 오늘 N3.6만 정정되고 N6.2 T4·마일스톤 문장이 남았다.
- 보강안: P 1087행 T4를 "ID > 0인 모든 MOS 포화(포화 여유 U-46). 노드전압 차는 T8 기록"으로, P 1078행 마일스톤 1에서 "노드전압이 S2 `dc`와 tol_V 안"을 빼고 "노드전압 차 기록"으로 정정. 그대로 두면 단위 11 판정자가 T4를 노드전압으로 걸어 스펙을 만족하는 해를 FAIL로 판정한다(P 458행 근거 그대로: free 모드 고임피던스 노드는 모델 차이에 민감).
- 누가: 엔진 내부(문서 정정 -- 결정은 이미 사용자가 함, E1 일괄 정정 방식).

### G6-02 [빠짐] SPICE 오라클이 잴 수 없는 선언 제약이 있다 -- 파일럿 T5가 구조적으로 PASS 불가 | **높음**
- reference: DRS 402행 표 6 "SPICE 결과(**gain/GBW/slew-rate/matching/전류** 등)가 ... 원 스펙을 여전히 만족".
- 새 엔진 쪽: SO 입력 스키마 `measure` enum = `dc_gain_db, ugf_hz, pm_deg, f3db_hz, supply_current_A` 5개뿐(`oracle_input.schema.json` 104·115행). 그런데 DSF 202행 파일럿 spec은 `ratio_ss_db >= 60`(CMRR 뷰)·`ratio_ss_db >= 60`(PSRR 뷰)를 선언하고, DSF 92행 `driving_spec.slew_rate_*`, DSF 91·208행 `settling{total_s, linear_s}`도 있다. SO C8: "SPICE 값을 못 얻은 제약이 있으면 `INCOMPLETE`" → P 1088행 T5 "선언된 성능 제약 **전부**를 SPICE 측정값이 만족"을 파일럿에서 채울 수 없다. DSF F11(435행)은 settling만 "합격 판정 대상 아님"으로 처리했고 CMRR·PSRR·slew는 처리 규칙이 없다.
- 유형: 빠짐.
- 보강안:
  1. 오라클 measure 추가: `cmrr_db`·`psrr_db`(MOD5 레지스트리의 뷰 선언 num/den과 **같은 여기 정의**로 .ac 두 번 -- PM과 같은 'U-48식 같은 정의' 원칙), `slew_rate_v_per_s`(.tran 큰 신호 계단, 출력 dV/dt 최대), `settle_s`(.tran, 오차 대역은 spec 선언값), 필요 시 `swing_v`(.dc 스윕). 각 측정 정의를 SO "측정 정의"에 추가하고 test.
  2. 엔진 쪽: metric 레지스트리 항목마다 `oracle_measure`(또는 `verified_by`) 필드를 두고, spec 로드 시 "SPICE 판정 수단이 없는 제약" 목록을 결과 JSON `spice_unverifiable[]`에 **실행 전에** 낸다(실행 끝에 INCOMPLETE로 처음 알게 되지 않도록).
  3. 그 전까지 임시로 T5를 "오라클 measure가 있는 제약 전부"로 좁힐지는 사용자 결정(DSF F11과 같은 종류).
- 누가: 오라클 측정 추가 = 엔진 내부(도구). 어느 제약을 합격 판정에 넣을지(정착·슬루·CMRR/PSRR) = **사용자 결정**(스펙·방법론).

### G6-03 [빠짐] "스냅 전/후 수치 차이와 그 원인" 기록이 없다 -- 모델 오차(T8)에 스냅 오차가 섞인다 | **높음**
- reference: DRS 402행 표 6 "box-shape 스냅으로 바뀐 **실제 W로 다시 돌린** SPICE 결과 ... **스냅 전/후 수치 차이와 그 원인을 명시**(§5 '스냅이 무해하다고 가정하지 말 것')", 374~379행 §1.7-5 "분할로 finger 수나 W가 실제로 바뀌면 ... SPICE를 그 소자에 대해 다시 실행".
- 새 엔진 쪽: DM7 5절 MOD8은 `W_err_rel <= W_tol_upper`이면 수렴으로 보고 엔진 재평가를 하지 않는다(재평가는 W_request일 때만, LY7). SO 입력 `devices[].W`(sizing 총폭)와 `finger_w·n_fingers`(실현폭)의 차는 `W_rel`로만 기록. 엔진 예측(`predictions`)이 **어느 W에서 계산된 값인지** 규정이 없다(P 1084행 T1, DM6 8절 front 스키마에도 없음). P 1090행 T7(U-45 front 점의 SPICE)도 MOD8 수렴 뒤 레이아웃 W로 돌린다는 문장이 없다.
- 문제: 예측이 sizing W, SPICE가 실현 W이면 T8의 `abs(엔진 − SPICE)`(DEC-72 모델 오차 = NFR-5 여유 바닥의 근거)에 스냅 오차가 섞인다. 허용 상한 `tol_V·(gm/ID)`(LY1)은 소자 하나의 ID 오차 한도일 뿐 회로 metric(gain·PM) 변화 한도가 아니다.
- 보강안:
  1. 최종 해(그리고 U-45 SPICE 대상 front 점)마다 MOD8 수렴 뒤 **모든 소자 W를 `W_realized`로 고정하고 finger_w 슬라이스 키를 적용한 평가 1회**(`search.evaluate(ctx, θ, w_fixed=W_realized)`, 투영 키 재사용이라 비용은 W 읽는 블록뿐)를 더 돌려 `metrics_at_realized_w`를 graph 필드로 쓴다.
  2. 결과 JSON·MOD9 표: metric마다 3열 -- 엔진@sizing W / 엔진@실현 W / SPICE@실현 W, 그리고 분해 = 스냅 효과(1열−2열) + 모델 오차(2열−3열). DEC-72 모델 오차 파일에는 **2열−3열만** 쓴다.
  3. 오라클 입력 `predictions`는 2열 값으로 채우고, `provenance.prediction_w = "realized"`를 남긴다. T7 문구에 "MOD8 수렴 레이아웃 W"를 명시.
- 누가: 엔진 내부.

### G6-04 [잘못] MOD7 box 개선 단계가 행 접기(`apply_explicit_row_split`)를 자동 적용하고 Euler·matching을 다시 확인하지 않는다 | **높음**
- reference: PRE-FLIGHT 13(61~65행) diffusion 안전 지점 확인, 14(66~70행) "diffusion 안전성과 matching 안전성은 별개 ... matching-critical 행은 diffusion만으로 안전 판정하지 않는다", 19(92~100행) "box-shape PASS는 물리적으로 지을 수 있다는 보장이 아니다 -- 분할 후 반드시 `build_stick_diagram()`으로 재확인", 20(101~107행) 분할 뒤 매칭쌍이 완전히 분리된 회귀, §1.7-3(290~301행) "matching-critical이면 `common_centroid_layout()`식 재구성 없이는 분할하지 않는다", §1.7-4(369행) "사용자가 실제로 쪼개기로 결정하면".
- 새 엔진 쪽: DM7 3절 순서 = 패턴(2) → finger(3) → **Euler(4)** → **box(5): FAIL이면 행 폭 큰 순으로 `apply_explicit_row_split` n_rows=2,3,...** → floorplan(6). 5단계 뒤 Euler·패턴 재판정이 없다("행 접기는 총 W 불변"만). SD 6115~6157 원본 docstring은 이 함수를 "매칭 파트너가 없는 단독 소자"용, "자동으로 판단하지 않고 호출자가 명시적으로 선언해야만 적용"으로 규정하고, 소자별로 독립 분할하므로 interdigitation/common-centroid 순서를 보존하지 않는다(실측: 본문이 소자마다 `divmod`로 조각을 나눠 행마다 소자 순서대로 다시 나열).
- 유형: 잘못(알고리즘 순서·적용 대상).
- 보강안(`layout/rows.py`·`box_shape.py`):
  1. 접기 대상 = matching group에 속하지 않은 소자만 있는 행. matching group이 있는 행은 접지 않고 그 그룹을 **패턴 함수로 다시 짓는다**: `common_centroid_layout(members, n_rows=k)`/`interdigitate_layout` 행 수 k 후보(DRS 303~316행 "짝수로 나눠 다시 짓기").
  2. 접거나 다시 지은 뒤 **4단계(row_euler)와 G6-05의 matching 감사를 다시 실행**하고 그 결과로 채택 여부를 정한다(DRS 317~326행 `audit_row_split` 고정 순서: Euler → box → 3b → 3c).
  3. 개선 판정은 행 폭 비가 아니라 G6-07의 전체 floorplan 결과로(PRE-FLIGHT 17: 그룹 지표가 아니라 전체 결과로 채택).
  4. test: 매칭 2멤버 행 + box FAIL 픽스처에서 접은 결과의 3c dx/dy가 접기 전보다 나빠지면 채택하지 않음.
- 누가: 엔진 내부. 단 "box FAIL을 자동 분할로 해소할지 설계자 선언으로만 할지"는 DRS 369행·SD docstring(§8.5 "box-shape FAIL을 수용할지 분할할지는 설계자 판단")과 DM7의 자동 적용이 다르다 → **결정 재검토 제안**(기본안: 비매칭 행 자동 접기는 유지, 매칭 행은 패턴 재구성만, 사용자 확인 1회).

### G6-05 [빠짐] 최종 행에 대한 독립 matching 감사(interdigitation 3b / common-centroid 3c, `check_mirror_symmetry`)가 없다 | **높음**
- reference: PRE-FLIGHT 2(18~20행) "Euler trail 존재와 `check_mirror_symmetry()` 통과는 별개 -- 반드시 둘 다", 7(36~39행) "존재하는가와 올바르게 배치됐는가는 별개", 20·24(101~131행) 3b·3c 분리, §1.7 3.5(317~354행) 종류별 필수 게이트(전류거울 3b 필수·3c 참고, 차동쌍 3c 필수·3b 참고, branch_symmetric 3c 필수), §1 표 4(400행) "matching-symmetry를 `check_mirror_symmetry()`로 실제로 검증했는가".
- 새 엔진 쪽: DM7 1절 복사 목록에 `check_mirror_symmetry`(SD 238행)가 없다(`build_mirror_symmetric_pattern` 210~230만 복사). `audit_row_split`(SD 7004)은 L8 위반으로 복사 제외(DM7 58행). 그 대체가 설계에 없다. 그룹 출력은 패턴 함수 자기 보고(`residual`, `ok`)뿐이고(DM7 167행), NR 3.3 출력 계약에 있던 `dx, dy`는 DM7 3절 `LayoutResult`에서 빠졌다. 패턴 함수 뒤에 crossover(4단계)·행 접기(5단계)·finger_w별 행 나누기(3단계)가 순서를 바꿀 수 있는데 최종 행 기준 재판정이 없다.
- 유형: 빠짐(검증 단계).
- 보강안: 새 파일 `layout/match_audit.py`(진입점 1, 필드 `ly.match[gid]`, input_fp = 최종 `ly.row` 지문들 + 그룹 레코드):
  - 3b: 그룹 멤버 finger의 행 안 인접 여부(복사본 `count_isolated_pairs` 재사용).
  - 3c: 멤버별 finger 위치 무게중심(행 안 x = finger 순번, 행 간 y = 행 순번)의 dx·dy(복사본 `common_centroid_residual` 재사용).
  - 대칭: matching 행이 `build_mirror_symmetric_pattern`으로 지어졌으면 `check_mirror_symmetry`(복사 추가, 해시 대조 대상) 판정.
  - 필수 게이트: role별로(차동쌍 3c, 미러 = UD 120행 "둘 중 하나" → 3b 또는 3c 하나 통과, branch_symmetric 3c -- G6-06) 판정하고 결과 JSON에 3b·3c·dx·dy·필수 게이트·ok를 모두 쓴다.
  - 허용 기준(상수 금지 충돌, G6-13): 3c 허용 = 멤버 finger 수 홀짝에서 오는 무게중심 양자화(전부 짝수면 0, 아니면 반 pitch)로 **유도**하고 SD `_common_centroid_residual`의 리터럴 0.5와 같은 값임을 test로 대조.
- 누가: 엔진 내부.

### G6-06 [빠짐/잘못] MOD3 matching group 유도가 DRS의 매칭 후보 판정 5패턴과 branch_symmetric을 다루지 않는다 | **중간**
- reference: §1.5-4(470~482행) `find_matching_candidates()` 반환은 **후보일 뿐** -- (a) 우연한 net 공유 기각 (b) diode→mirror 직렬 체인(interdigitation 대상 아님) (c) 작은 diode가 만든 바이어스 노드를 큰 소비 소자가 읽는 관계(비율 매칭 불성립, 기각) (d) 동적 피드백 루프 신호 공유(vcmfb, 기각) (e) 진짜 병렬 매칭쌍만 처리, "판단 근거는 리포트에 반드시 남긴다". §1.7 3.5(328~340행) 캐스코드 대칭쌍 `branch_symmetric`(같은 gate, source/drain 전부 다름)은 3c 필수. 490~495행 sub-block 경계를 넘는 기준-미러 인접 배치 판단은 "사용자 확인을 받는다".
- 새 엔진 쪽: DM3 91·149행 `matching_ratio` = "gate가 레일이 아닌 `gs_groups`(같은 kind·gate·source) 묶음(= 진짜 미러)", `matching_offset` = 같은 비레일 source·서로 다른 gate 2개. 그래서 (c)(d)형 묶음(같은 gate·같은 레일 source인 바이어스 소자와 큰 출력 소자, CMFB 피드백 gate 공유)도 '진짜 미러'로 레이아웃 matching group이 되고, branch_symmetric(source가 서로 다름)은 어떤 matching group에도 들어가지 않는다 → 캐스코드 대칭쌍은 common-centroid 요구가 사라진다. 또 그룹마다 '기각 근거' 기록이 없다.
- 유형: 빠짐(분류) + 잘못(과포함).
- 보강안: `graph/matching_groups.py` 레코드에 `role ∈ {diff_pair, mirror, branch_symmetric, bias_distribution, feedback_shared}`와 `evidence{rule, nets}`, `status(derived|proposed|review_needed)`:
  - branch_symmetric 유도: 같은 kind·같은 gate 넷이고 source·drain이 서로 다르며, 두 소자의 source 쪽 가지가 차동쌍 두 출력 가지로 대응(S1 기둥·`matching_offset` 대응으로 판정 -- 이름·태그 없이).
  - (c) 판정: 그룹 안 diode 소자와 비 diode 소자가 서로 다른 MOD3 블록(stage·bias)에 속하면 `bias_distribution`(레이아웃 matching 대상 아님, `proposed`).
  - (d) 판정: gate 넷이 MOD3 루프(loops.py) 위의 신호 넷이면 `feedback_shared`(`proposed`).
  - 레이아웃 계약에는 diff_pair·mirror·branch_symmetric만 넘기고, 나머지는 결과 JSON `matching_dispositions[]`에 근거와 함께 남긴다(DRS 482행).
- 누가: **사용자 결정 필요**(분류 규칙 = 회로 해석, J 공동분석으로 9회로 대조표 확인). 구현은 엔진 내부.

### G6-07 [잘못] floorplan 호출에서 `spine_groups`·`mirror_pairs`의 의미를 바꿔 넘긴다 -- PRE-FLIGHT 15 재발 구조 | **중간**
- reference: §1.7-1(259~269행) "나머지(spine)는 **회로의 기능 블록별로 그룹화** -- 이 절차에서 가장 중요한 회로 지식 반영 단계", 폴러리티 분리는 `sub_kinds`로 **실측 비교 후 채택**(PRE-FLIGHT 17). `mirror_pairs` = 좌우 대칭 stack 쌍(259~261행). PRE-FLIGHT 15(71~75행) 평평한 packing이 CMFB 행을 Stage-1 사이에 끼움, 16(76~80행) `net_weights`+`width_tolerance` 함께.
- 새 엔진 쪽: DM7 2절 135행 `spine_groups` = "행 그룹의 (kind, body 넷)(LR8)", `mirror_pairs` = "matching 그룹". SD 8335~8363행 docstring 기준 spine_groups는 "갈라지면 안 되는 기능 그룹", sub_kinds는 "더 나은 결과일 때만 채택되는 폴러리티 후보", mirror_pairs는 좌우 대칭 블록 쌍이다. matching 그룹은 이미 한 행 안에 interdigitate된 소자 묶음이라 블록 쌍이 아니다(타입 불일치). (kind, body)로 묶으면 모든 기능 블록의 nmos가 한 그룹 → 기능 블록끼리 섞이는 PRE-FLIGHT 15 구조가 된다. `net_weights`는 넘기지 않는다.
- 영향: 판정 축 면적 A_L(DM6 6.4, front 재필터, T6)이 이 결과에서 나온다.
- 보강안(`layout/floorplan.py`): `spine_groups` = MOD3 블록(stages.py 블록 구성·composite_blocks·루프 블록)별 행 묶음, `sub_kinds` = 그룹 안 (kind, body) 구분(후보), `mirror_pairs` = S1 그래프의 좌우 대칭 행 쌍(차동쌍 두 가지를 따라 대응되는 행; branch_symmetric 대응과 같은 유도), `net_weights` = 그룹 사이 공유 gate·drain 넷 수(가중 = 공유 넷 수, 상수 없음), `width_tolerance`는 복사본 기본값 유지(DRS 281행). test: 두 블록 픽스처에서 블록 행이 섞이지 않음.
- 누가: 엔진 내부(블록은 MOD3 유도 결과). 블록 경계가 애매한 회로는 J.

### G6-08 [빠짐] MOD9 설계 문서·단위 완료 조건이 없다 -- DRS 8개 섹션이 어디에도 배정되지 않음 | **중간**
- reference: §1(393~410행) "8개 섹션 중 하나라도 빠지면 산출물 미완성", §1.6-5(206~207행) 게이트가 OK가 아니면 완료 선언 금지, §3(565~581행) 한 HTML 안 시각 층 + `const REPORT` 기계 판독 층, layout_guide는 구조화 필드, SKILL.md §7(354행~) 최종 산출물.
- 새 엔진 쪽: P 553행 MOD9 책임에 "HTML 보고"는 있으나 design 문서가 없다(design_* 7개에 MOD9 없음). NR 3.1 `report` 행은 파일 이름 4개뿐, P N6.1 단위 6 완료 조건(1071행)과 T1(1084행)은 결과 JSON만, R은 HTML 시간 산정 없음. 참고 대상 DR(`design_report.py` 18~19·102~104행)은 "없으면 그 섹션은 조용히 ... 생략"이고 21~26행에서 `renderSchematic/renderStack`을 표 렌더러로 대체했다 -- DRS PRE-FLIGHT 5·§1 ⚠⚠(412~422행)와 정면 충돌한다(참고 구현 자체가 규격 위반).
- 보강안: `design_mod9_report.md` 신설 -- (1) 결과 JSON 스키마에 8섹션 키를 **필수**로 두고, 계산하지 못한 섹션은 생략이 아니라 `{"status": "not_run", "reason": ...}`(조용한 생략 금지, WP-02); (2) 섹션 ↔ graph 필드 대응표: §1 S1(+G6-12), §2 spec 원문(G6-19), §3 S2 `dc.device_op`(gm_id는 D-1 (라)여도 파생값으로), §4 `ly.group`·`ly.match`·후보 기록(G6-16), §5 `ly.row`(+`canonical_row`), §6 G6-03의 3열 표 + oracle `compare.json` 요약, §7 G6-09, §8 `ly.floorplan`(G6-14), 추가 §front(N6.3 front 표); (3) HTML은 결과 JSON의 순수 함수, JSON을 `<script type="application/json" id="REPORT">`로 바이트 그대로 삽입(두 층 불일치 0을 test로: 삽입 문자열 sha256 = 결과 JSON sha256); (4) 완료 게이트 `report_completeness`: 8섹션 status, coverage PASS, floorplan 존재, U-45 점 SPICE verdict 존재가 아니면 파이프라인 exit code를 review_needed 계열로. 일정: R에 MOD9 HTML 단위 추가.
- 누가: HTML 8섹션 보고를 '엔진 완성'(DEC-85) 범위에 넣을지 = **사용자 결정**(한 달 범위). 스키마·게이트 설계 = 엔진 내부.

### G6-09 [빠짐] §7 레이아웃 실행 가이드(DRS §2 7항목)를 만드는 곳이 없다 | **중간**
- reference: §2(531~563행) 항목 1 고임피던스/극점 노드(배선 최소·교차 금지·junction 최소), 2 matching 그룹의 실제 finger 순서·dummy·방향·well, 3 고전류 소자 EM strap·비아·열 거리, 4 민감 바이어스/tail 넷 격리, 5 보상 소자 배선 기생의 설계 여유, 6 확정 stack 배치 재진술, 7 검증 안 한 항목 정직 고지. §3(579~581행) `layout_guide: {critical_nodes, matching_groups, power_branches, ...}` 구조화. §1.5 규칙(442~445행) 수동소자(Cc/Rz)는 stick diagram 예외지만 §7에 배선 지침으로 반드시. 490~500행 블록 경계 미러 인접 배치 근거를 §7에.
- 새 엔진 쪽: 없음. P 994행 I-A13 "dummy·LDE 반영 없음". MOD7은 수동소자를 배치하지 않는다(P 278행 DEC-79).
- 보강안: `report/layout_guide.py`(결과 JSON `layout_guide`), 모두 graph 필드에서 유도(회로 이름 없음):
  1. `critical_nodes`: MOD3 stages.py 극점 노드·임피던스 등급 + **최종 해 1회** MNA 감도 dPM/dC_node, dGBW/dC_node → "PM이 목표에 닿기까지 허용되는 추가 기생 C" = (PM − PM_target)/(dPM/dC)(선형 근사임을 표기). DEC-74의 '최종 해에서만' 빈도와 같아 반복 계산 원칙과 충돌 없음.
  2. `matching_groups`: `ly.row` 순서 그대로 + `ly.match`(G6-05) + dummy 권고(엔진 미모델 I-A13임을 명시).
  3. `power_branches`: `branch_i` 상위 가지와 소자. EM 폭은 PDK 선언에 EM 규칙이 없으면 "PDK 확인" 고지(숫자 생성 금지, DRS 561~563행).
  4. `sensitive_nets`: 차동쌍 공통 source 넷, mirror 그룹 gate 넷(S1 유도).
  5. `compensation`: GB5가 정한 수동소자(값·넷), 직렬 기생 R·병렬 기생 C에 대한 PM 감도로 허용 여유.
  6. `placement`: `ly.floorplan` placements·그룹.
  7. `not_verified`: ESD·DRC·guard-ring 폭·LDE·dummy·수동소자 배치.
  - 수동소자 전부가 `layout_guide.passives`에 등장하는지 test(G6-15).
- 누가: 유도 = 엔진 내부. 범위 포함 여부 = G6-08과 함께 **사용자 결정**.

### G6-10 [빠짐] 확산 공유(Euler trail)를 SPICE·엔진 어느 쪽도 반영하지 않는다 -- 고임피던스 노드 용량이 체계적으로 틀어짐 | **중간**
- reference: §2-1(541~543행) 극점 노드 "junction 면적 최소화", §1 표 6(402행) 레이아웃 결정 반영 시뮬레이션, §0(386~389행) layout 결정이 성능에 결정적.
- 새 엔진 쪽: SO C3 `ad=as=ad_per_w_m*finger_w`, `m=n_fingers` -- finger마다 독립 확산으로 넣고 m배 한다. Euler 행에서는 내부 확산을 이웃 finger가 공유하므로(stick diagram의 목적 자체) 실제 소스/드레인 확산은 대략 절반 + 양끝이다. P 516행 "LUT에 없는 접합용량 때문에 못 세는 노드는 ... 별도 열로 보고" -- 엔진 `ss` 노드 C에도 접합용량이 없다. 결과: SPICE는 접합 C 과대(물리적으로 공유 확산을 무시), 엔진은 0 → T8 모델 오차의 PM·GBW 항에 레이아웃 무관한 체계 오차가 들어간다. [추측: 크기는 회로별 극점 노드 확산 면적 비율에 따라 다름 -- 측정 필요]
- 보강안: (1) MOD7 `ly.row`에서 소자·넷별 확산 통계(내부 공유 확산 수, 끝 확산 수)를 파생 필드 `ly.diffusion[dev]`로 기록 (2) SO 스키마에 소자별 `ad/as/pd/ps` override(선택)를 추가하고 MOD9가 그 통계로 채움 (3) 엔진 `ss` 노드 C에 PDK 선언 접합용량(Cj·Cjsw, `core/pdk_decl.py`에 출처와 함께 -- 없으면 '미반영' 표기)을 같은 통계로 더해 엔진·SPICE가 같은 기생을 본다 (4) [제안] Euler trail이 여러 개면 극점 넷이 내부 확산에 오는 trail을 우선(DRS 543행 지침을 알고리즘으로).
- 누가: 엔진 내부(오라클 스키마 확장 포함).

### G6-11 [결정 재검토] 차동쌍 interdigitation 완화(UD 122행)는 DRS의 "차동쌍 3c 필수, 억지 통과 금지"보다 느슨하다 | **중간**
- reference: §1.7 3.5(342~347행) "차동쌍은 common-centroid(3c)가 필수", 356~362행 "`ok=False`가 나와도 억지로 통과시키지 않는다 ... 실패를 숨기지 말고 근본 원인과 함께 리포트에".
- 새 엔진 쪽: UD 122행 "finger 수 조정이나 W 조정으로도 common centroid가 불가능하면 interdigitize로 완화하는 것은 가능", P 833행 LY5(`relaxed: true` + attempts 기록).
- 판단: 기록을 남기므로 DRS의 '숨기지 않음'은 만족한다. 다만 DRS는 완화를 합격으로 보지 않는다. 결정을 뒤집자는 것이 아니라 보고 방식 보강을 제안한다.
- 제안: 완화된 차동쌍은 결과 JSON·보고 맨 앞 `review_needed`(합격 시험 T1~T9에는 영향 없음 -- 공칭 SPICE는 불일치를 안 본다)로 올리고, G6-05의 dx·dy(finger pitch 단위)와 근본 원인(그래프 차수 제약 등, DRS 358~360행)을 함께 적는다. 오프셋 영향 수치화는 기울기 상수가 필요해 상수 금지 원칙과 충돌하므로 하지 않고 dx·dy만 낸다.
- 누가: **사용자 결정**(완화 결과를 review_needed로 표시할지).

### G6-12 [빠짐] §1 회로도 렌더링(`renderSchematic`)에 필요한 좌표의 출처가 없다 | **중간**
- reference: §1 표 1(397행) `renderSchematic()` 그대로 재사용, 손으로 좌표 박은 1회성 SVG 금지, PRE-FLIGHT 5(28~32행), 424~428행 검증.
- 새 엔진 쪽: `legacy/report_template.html` 291~340행 `renderSchematic(container, schem)`은 `rails/devices/wires/dots/labels`의 **x·y 좌표**를 입력으로 받는다. library topology.json에는 좌표 필드가 없다(grep 실측: `schema_version`만 걸림). DR 116~117행은 좌표를 사람이 `narrative.schematics`로 넘긴다 -- topology 종속 금지 원칙(UD 141행)상 엔진이 회로별 좌표를 가질 수 없다.
- 보강안(택1): (a) S1에서 자동 배치 -- x = MOD3 기둥 순서, y = 기둥 안 레일→소자 적층 순서, 배선은 넷별 직교 경로(일반 알고리즘, 손 좌표 없음) (b) topology.json에 선택 필드 `schematic`(사용자 소유 파일, connectivity와 별개 표시 정보) (c) §1을 연결 표 + 자동 배치 없이 생략 표기. 기본안 (a)[추측: 9회로 중 큰 회로(51소자)에서 가독성은 실측 필요].
- 누가: **사용자 결정**(topology 파일에 표시 정보를 둘지, 자동 배치 품질 수준).

### G6-13 [충돌] box 판정 기준을 spec 필수 필드로 요구하지만 spec 형식에 그 필드가 없다 + 3c 허용 리터럴 | **중간**
- reference: PRE-FLIGHT 23(118~124행) "실제 하드 게이트는 `check_box_shape(row_widths)`뿐, aspect_ratio는 참고", 317행 `audit_row_split(..., max_ratio)`, 241~247·281행 `width_tolerance(기본 2.0)`, 290~292행 "기본 60%" 등 수치 기본값을 문서가 직접 권고.
- 새 엔진 쪽: DM7 2.3(148행)·8절 1(237행) "허용 비 = 사람 선언(회로 spec 레이아웃 기준 -- D5 형식에 항목 추가, 없으면 로드 거부)". DSF(440행 전체)에 box·레이아웃 기준 필드가 없다(grep: `layout_floorplan_outline` 판정 축 규칙만). DM7이 그대로 구현되면 9회로 spec 전부가 로드 거부된다.
- 원칙 충돌 고지: DRS의 수치 권고(2.0, 60%, 0.5 허용)는 WP-03 상수 금지와 충돌한다. DM7 2.2는 탐색 폭 리터럴만 복사 예외로 묶었는데, `_common_centroid_residual`의 0.5(LC 1.1 표)는 탐색 폭이 아니라 **판정 기준**이다.
- 보강안: (1) DSF에 `layout_criteria{box_row_width_ratio_max: {value, source}}` 추가(사용자 값) 또는 DM7 기본안을 '선언 없으면 box는 판정 없이 보고만'으로 바꿈 (2) 3c 허용은 G6-05처럼 finger 수 홀짝에서 유도하고 0.5와 같음을 test로 고정 (3) 60%(`evaluate_row_split_candidates`)는 후보 생성 폭이라 복사 예외 유지.
- 누가: box 비율 값 = **사용자 결정**(스펙). 나머지 엔진 내부.

### G6-14 [빠짐] floorplan 결과 필드가 면적 하나로 줄었다 | 낮음
- reference: §1 표 8(404행) "bbox, aspect ratio, packing_density, 빈 공간 없이 실제로 채워진 배치", §1.7-2·3(270~301행) `packing_density` 핵심 지표, `row_split_candidates`·`splittable`·`diffusion_check`, §1.7-6(380~382행) 분할 안 한 근거를 리포트에.
- 새 엔진 쪽: DM7 `ly.floorplan` 필드 내용 미정, DM6 6.4는 A_L = bbox_w·bbox_h만 사용.
- 보강안: `ly.floorplan = {bbox_w, bbox_h, A_L, aspect_ratio, packing_density, placements, groups, row_split_candidates[{block, splittable, diffusion_check, decision, reason}]}`. `diffusion_check == "not_verified"` 금지(시퀀스는 항상 넘김, DM7 3단계 6) test.
- 누가: 엔진 내부.

### G6-15 [빠짐] 커버리지 판정의 입력 독립성과 수동소자·floorplan 커버리지 | 낮음
- reference: §1.5-5(507~518행) `sized_device_names`는 §3 표에서 직접 -- 같은 dict 재사용 금지, §1.5-7(524~529행) stick 커버리지 PASS ≠ floorplan 포함, 442~445행 수동소자는 §7에, §1.6-1(191~194행) 기능 블록별 소자 수 선언·차동 회로의 mirror branch 존재 질문.
- 새 엔진 쪽: DM7 3단계 7 "입력 소자 이름 집합 = 행 소자 이름 집합"(입력 = LayoutInput, 이미 sizing에서 파생된 집합).
- 보강안: `report_completeness`(G6-08)에서 4중 집합 비교 -- S1 MOS 집합 = S2 `device_op` 키 = `ly.row` 소자 = `ly.floorplan` 블록에 속한 소자; S1 수동소자 = 결과 JSON 수동소자 = `layout_guide.passives`. 그리고 MOD3 블록별 소자 수 표를 결과 JSON에 내 사용자가 논문과 대조하게 한다(§1.6-1의 새 엔진판 -- 판정은 사용자).
- 누가: 엔진 내부(블록별 개수 확인은 사용자).

### G6-16 [빠짐] 레이아웃 결정 추적(후보·탈락 사유·box FAIL 시 필요 행 수) | 낮음
- reference: §1 표 4(400행) "box-shape 탐색 후보와 채택한 finger_w/n_fingers, 스냅 오차 트레이드오프 ... `check_box_shape()` FAIL이면 ... 비율 임계값을 만족하는 데 필요한 물리 행 개수를 실제로 계산해 남겼는가(정성적 설명만으로 FAIL을 최종 결론 삼지 말 것)".
- 새 엔진 쪽: DM7 3절 2(c) 정렬 키는 계산하지만 채택안만 남기고, `attempts`는 차동쌍 완화에만 있다. 5단계 box FAIL은 "FAIL을 결과에 남긴다"뿐.
- 보강안: `ly.group[gid].candidates[{nf, finger_w, pattern, method, sort_key, err, reject_reason}]`(열거 상한 = 후보 생성 집합 그대로, 같은 필드라 추가 계산 0), `ly.box.fail_analysis{rows_needed_for_ratio}` = 행 finger 수와 선언 비율에서 계산.
- 누가: 엔진 내부.

### G6-17 [빠짐] 블록 경계를 넘는 확산 병합(hub-merge) 판단 기록 | 낮음
- reference: PRE-FLIGHT 1·8(16~17·40~42행) 전체 목록에서 한 번에, §1 표 4 "stage-경계 병합 여부를 `find_hub_merge_candidates()`로 실제로 확인했는가", §1.5-2(452~457행) 병합 안 하기로 한 근거.
- 새 엔진 쪽: DM7 행 그룹 = (kind, body) + 기둥 + matching 그룹(블록별로 자르지 않으므로 누락 구조는 아님). 그러나 서로 다른 그룹 소자가 같은 S/D 넷을 공유해 한 행으로 합칠 수 있었는지·왜 안 합쳤는지는 기록되지 않는다.
- 보강안: `rows.py`가 전체 소자에서 공유 S/D 넷 후보를 한 번 열거해 `ly.rows.merge_decisions[{devices, net, merged, reason}]`로 남김(SD `find_hub_merge_candidates` 논리 참고, 복사 여부는 해시 규칙대로).
- 누가: 엔진 내부.

### G6-18 [빠짐] 시각 검증 의무(§4)의 자동화 대체가 없다 | 낮음
- reference: §4(583~604행) Artifact 배포 + 브라우저로 각 섹션 스크린샷 확인, 문제 시 재배포·재검증, 시각 검증 없이 완료 보고 금지. 실사례(598~599행): 라벨 겹침, drain 미연결, `schem` 무시 버그.
- 새 엔진 쪽: 없음(MOD9 미설계).
- 보강안: MOD9 test에 headless 렌더(playwright) DOM 검사 -- 섹션마다 SVG 존재·`<pre>` 덤프 0·노드 라벨 bbox 겹침 0(자동으로 잡을 수 있는 것만), 그리고 보고서 배포 전 사람/agent 스크린샷 확인 1회를 절차로. 엔진 합격 시험과는 분리.
- 누가: 절차 포함 여부 = **사용자 결정**(가벼운 절차와의 관계). 자동 검사 = 엔진 내부.

### G6-19 [빠짐] §2 "spec 원문 그대로"와 파생값 구분 | 낮음
- reference: §1 표 2(398행) "사용자/논문이 지정한 스펙 원문 그대로(임의로 파생시키지 않음)", 224~226행 확신 없는 세부는 "⚠ 가정"으로 고지.
- 새 엔진 쪽: DSF는 `source` 필수(좋음). 결과 JSON에 spec을 어떻게 싣는지 규정 없음. 오늘 결정으로 엔진 계산값(파일럿 R1·R2, UD 143행)·논문 채택값(t_lln·t_settle·부하, UD 131행)·`derived_spec(why)`가 섞인다.
- 보강안: 결과 JSON `spec{declared: spec 파일 바이트 sha256 + 원문 객체, derived[{name, value, why, inputs}], engine_computed[{name, value, rule}]}` 3층 분리, 보고 표에 출처 열.
- 누가: 엔진 내부.

### G6-20 [충돌] front 표 필드·metric 이름 불일치 | 낮음
- reference: (DRS는 front를 다루지 않음 -- 계획서 기준) P 1105행 N6.3 "front 표(점마다 θ*, 전력, 면적의 탐색 축·판정 축과 그 차, gain 예산, 활성 제약과 여유, 선택 여부)와 **선택 점·선택 근거**".
- 새 엔진 쪽: DM6 8절 `runs.jsonl` front 항목에 `selected`는 있으나 선택 근거 필드가 없다. 목적 metric 이름이 DSF 98행 `supply_current_dc`, DM6 6.5·8절 `supply_current_dc_a`로 다르다. P 513행 N3.8 "판정 축 재필터는 보류"는 DEC-79(12번 (나))와 어긋남(DM6 D-6에 이미 기록 -- 보고 문구에 영향).
- 보강안: `runs.front[].selection{rule: "budget_point|endpoint|user", budget_ref, reason}` 추가, 이름은 레지스트리 정본 하나로 통일(DSF·DM6 정정), D-6 정정을 E1에 포함.
- 누가: 엔진 내부.

### G6-21 [빠짐] DRS PRE-FLIGHT 26의 검증 끝난 행 시퀀스를 회귀 오라클로 쓰지 않는다 | 낮음
- reference: PRE-FLIGHT 26(139~157행) folded_cascode·two_stage_ota 12개 행 시퀀스와 node_path 표(`check_walk_sequence` 전부 ok).
- 새 엔진 쪽: LC 1절 6의 동작 대조 입력 8개에 이 표가 없다.
- 보강안: `tests/layout/test_mirror_trail.py`·`test_canonical_rows.py` 오라클로 이 표(DRS 원문에서 test 작성자가 독립 전사)를 쓰고, `canonical_row` 결과 node_sequence와 DRS node_path가 다르면 시작점 규칙 차이로 설명(정렬 시작 노드). 단 DRS 예제는 Maloberti 예제(라이브러리 회로 아님)라 회로 결과 기대값이 아니라 함수 오라클로만.
- 누가: 엔진 내부(test 작성 주체).

### G6-22 [reference 오류] 오래된 경로·함수 이름 | 낮음
- 근거(실측):
  - 6·397·412·571행 `assets/report_template.html` → 실제 `legacy/report_template.html`(`assets/`에 없음, SKILL.md 71·381행은 이미 legacy).
  - 188·243·311행 `assets/stick_diagram.py` → `legacy/stick_diagram.py`.
  - 92·308행 `find_interleaved_symmetric_splits()`가 절차 단계로 남아 있으나 `legacy/tests/tools/interleave_splits.py`로 이동(문서 자신이 괄호로 적음) -- 절차에서 호출 불가.
  - 230~235행 `run_topology_pipeline()`·`function-selection-map.md` §10은 옛 엔진 경로.
  - 새 엔진이 의도적으로 복사하지 않은 함수(`run_full_circuit_audit`, `find_hub_merge_candidates`, `find_matching_candidates`, `audit_row_split`, `check_box_shape`, `search_stack_finger_w`, `search_shared_finger_w`, `build_stick_diagram`, DM7 58행 사유)를 DRS가 필수 근거로 지정한다 → 새 엔진으로 DRS를 '그대로' 만족할 방법이 없다.
- 보강안: DRS에 "옛 함수 → 새 엔진 대응" 표 추가(run_full_circuit_audit → S1 단일 소스 + `report_completeness`; check_box_shape → `box_verdict`; audit_row_split → `match_audit`(G6-05); build_stick_diagram → `row_euler`+`canonical_row`; find_matching_candidates → `graph.matching_groups`(G6-06); check_stick_diagram_coverage → 복사본 그대로), 경로 정정.
- 누가: 엔진 내부(문서 정정). 대응 표의 의미 판정(예: matching 분류)은 G6-06과 함께 사용자.

### G6-23 [reference 오류] DRS 내부 모순 | 낮음
- 498~500행 "최종 물리 배치는 floorplan 판단 영역(이 skill의 범위 밖)" ↔ 404·406~410행 floorplan은 필수 섹션(PRE-FLIGHT 27로 승격). 승격 전 문장이 남음.
- 380행 §1.7-6 "`pack_floorplan()`을 다시 실행" ↔ 243~247행 "기능 블록이 2개 이상이면 `pack_floorplan()`을 직접 쓰지 말고 반드시 grouped".
- 596행 §4-2 "최소 각 섹션(1~7)" ↔ 8개 섹션.
- 606~610행 §5 "7번(layout 가이드)만 신설" ↔ 8번 floorplan도 신설(PRE-FLIGHT 27).
- 400행 "§8.2 step 4", "§8.5"는 이 문서에 없는 절(다른 reference `stick-diagram-euler-layout.md`의 절로 추정 [추측]) -- 문서 이름 없이 절 번호만 적음.
- 보강안: 위 5곳 문구 정정(새 엔진 결정과 무관한 편집).
- 누가: 엔진 내부(문서 정정).

---

## 2. 요약표

| 심각도 | 개수 | ID |
|---|---|---|
| 높음 | 5 | G6-01, G6-02, G6-03, G6-04, G6-05 |
| 중간 | 8 | G6-06, G6-07, G6-08, G6-09, G6-10, G6-11, G6-12, G6-13 |
| 낮음 | 10 | G6-14 ~ G6-23 |
| 합계 | 23 | |

유형별: 빠짐 14, 잘못 3(G6-04·06·07, 06은 빠짐 겸), 충돌 3(G6-01·13·20), reference 오류 2(G6-22·23), 결정 재검토 2(G6-11, G6-04 일부).
사용자 결정 필요: G6-02(SPICE 판정 대상 제약), G6-04(자동 행 접기 범위), G6-06(matching 분류 규칙 = 회로 해석 J), G6-08·09(HTML 8섹션·레이아웃 가이드를 엔진 완성 범위에 넣을지), G6-11(완화 차동쌍 review_needed 표시), G6-12(회로도 좌표 출처), G6-13(box 비율 값), G6-18(시각 검증 절차).

## 3. 상위 5개 권고

1. **G6-01** 계획서 T4(1087행)·마일스톤 1(1078행)의 "노드전압 tol_V 안" 합격 조건을 오늘 결정(8번 수정안)대로 '포화만 판정, 노드전압은 기록'으로 정정 -- 그대로 두면 스펙을 만족하는 해가 FAIL로 판정된다.
2. **G6-02** SPICE 오라클에 CMRR·PSRR(엔진과 같은 뷰 정의)·slew·settling 측정을 추가하고, 엔진은 spec 로드 시 'SPICE로 판정할 수 없는 제약'을 미리 낸다. 지금 measure 5개로는 파일럿 T5(CMRR/PSRR 60 dB 선언)가 늘 INCOMPLETE다. 어느 제약을 합격에 넣을지는 사용자 결정.
3. **G6-03** 최종 해와 SPICE 대상 front 점마다 '실현 W 고정 재평가' 1회를 추가하고, metric별로 엔진@sizing W / 엔진@실현 W / SPICE 3열과 스냅·모델 오차 분해를 남긴다. 모델 오차 파일(T8, NFR-5 여유 바닥)에는 모델 오차분만 쓴다.
4. **G6-04 + G6-05** MOD7에서 box 개선 행 접기는 matching 없는 행에만 적용하고, matching 행은 패턴 함수로 n_rows를 다시 짓는다. 접기·crossover·finger_w 행 분할 뒤에는 Euler와 새 `match_audit`(3b·3c·dx/dy·`check_mirror_symmetry`, role별 필수 게이트)를 반드시 다시 돌린다(PRE-FLIGHT 14·19·20 재발 차단).
5. **G6-07 + G6-06** floorplan 호출의 의미를 바로잡는다(`spine_groups` = MOD3 기능 블록, (kind, body)는 `sub_kinds` 후보, `mirror_pairs` = 좌우 대칭 행 쌍, `net_weights` 공급). 판정 축 면적 A_L(front 재필터, T6)이 여기서 나온다. 함께 MOD3 matching group에 branch_symmetric을 넣고 바이어스 분배·피드백 공유 gate를 레이아웃 matching에서 빼는 분류를 J 공동분석으로 확정한다.
