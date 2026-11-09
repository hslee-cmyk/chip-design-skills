# 공유 순수 함수 감사 -- '한 규칙'(계획 v6.38.4 SF-1 범위 8) 대 엔진 as-built

- 날짜: 2026-10-29. 감사자: graph 단일 정본 감사 agent(읽기·측정만, 엔진·계획 수정 0).
- 엔진: `wt/integ-it12` HEAD `b12792ab`, `skills/analog-gmid-design/gmid_engine/`(tests 제외 420 파일). 계획: `wt/plan-v6384` HEAD `c9340f8b`, `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` 2225행(SF-1 범위 8).
- 스크립트·원자료: `wt/_drafts/evidence/2026-10-29/shared_pure_fn_audit/`
  - `scan_shared_calls.py` -> `calls.json`(해석된 모듈 간 호출 4,209건), `shared.tsv`(호출 모듈 ≥ 2 인 callee 201개)
  - `reach_roots.py` -> `reach.tsv`(호출 자리마다 그 자리에 닿는 계산 블록 진입점 또는 뿌리 함수)
  - `summarize.py` -> `summary.tsv`, `dump_sites.py` -> `sites.txt`(호출 자리별 인자 원문), `dup_names.py` -> `dup_names.tsv`(같은 이름 함수가 둘 이상 모듈에 있는 69건 -- 쌍둥이 구현 탐지용)
  - `classification.tsv` -- 133개 callee 분류(아래 §2)
- **엔진 인용의 용도**: 아래 파일:행은 재작성 범위 목록일 뿐이다. as-built 구조를 규칙 근거로 쓰지 않는다(O-153·O-165).

## 0. 결론 요약

1. 모듈 간 공유 callee 201개 가운데 인프라(검사·지문·정렬 26)와 레코드 생성자(42)를 빼고 **133개**를 분류했다: (A) 블록 재사용 2, (A′) LUT 파생표 승인 예외 6, **(B) 같은 입력 재계산 21**, (C) 다른 입력 71, (D) 판정 불가 1, (E) 한 블록 안 21, (X) 계산값 아님(상수 표·접근자·투영) 11. **(B) 21개 함수와, 공유 호출이 아닌 인라인·쌍둥이 구현 3건을 묶으면 사안은 15건(B1~B15)**이다.
2. 작성자가 보고한 `_input_side` 사례는 **맞다**(B8). 지금 엔진에는 `icm_config` 호출이 없고(O-115로 소멸), 자리는 `authoring/spec_elements.py:104`·`authoring/spec_views.py:101`(`input_terminal_nets`)과 둘째 구현 `metrics/noise_plan.py:28` `_input_side` 셋이다.
3. SF-1 범위 8의 '한 규칙' **일반 문장은 B1~B15를 원칙상 모두 덮는다**. 그러나 다음 세 문제가 있다.
   - **소유·완료 조건이 없다**: 이 규칙을 강제하는 완료 toy·`git grep`은 판정 대상 술어 하나뿐이다. B1(IT-2c)을 빼면 나머지 14건은 어느 card에도 대체 자리가 없다. 또 B14(판정 제약에서 파생한 면적 예산·이득 목표)는 SF-1의 '지우면 깨지는 곳' 목록에 소비자로 올라 있지만, 완료 조건은 '술어 호출 0'만 본다. 그래서 파생값 재계산(4자리·3자리)은 그대로 남는다.
   - **다른 card 문언과 충돌한다**: N6.26 TN-1은 같은 입력 세 자리가 '순수 함수 하나를 공유'하게 한다. headroom-chain HC-S는 봉인점 `sat_threshold`를 '정본 함수 하나'로 둔다. 둘 다 한 규칙이 금지하는 꼴이다(§3.2).
   - **경계 문언이 (B)와 (C)를 가를 만큼 명확하지 않다**: 이 감사에서 실제로 판정이 갈린 축 일곱 개(G1~G7, §3.3)를 문언이 정하지 않는다. 로더 단계, 투영 뷰, LUT memo 적중, 모형 생성 대 평가, 반복 마지막 점 대 봉인값, 파이프라인 접착 코드, 블록 안 값의 층이 그것이다.
4. 권고: 한 규칙을 card 범위 문장(SF-1 8)에서 graph 규칙 층(N3.3 또는 DEC)으로 올린다. 그리고 (B) 사안 표(§2.1)를 대체 card 표로 붙이고, 경계 정의 G1~G7을 문언에 넣는다(§4). 정본 자리를 정할 수 없는 사안(B10·B11 로더 단계)은 graph 규칙 6대로 계획에서 먼저 정한다.

## 1. 방법과 한계

- AST로 모듈 top-level 함수·클래스 정의를 모으고, `from … import`·`import … as`·재수출(`__init__`)을 따라 호출을 정의 모듈로 해석했다(4,209건). 호출 모듈이 둘 이상인 callee를 '공유'로 셌다.
- 자리 판정: 호출 자리에서 위로 호출 그래프를 거슬러 `_module_map.MODULES`의 `compute_block` 진입점(49개)이나 뿌리 함수(엔진 안 호출자 없음)에 닿는 집합을 구했다(`reach.tsv`). 한 callee의 자리가 모두 같은 블록 하나에 닿으면 (E) 후보로 봤다.
- 같은 입력 판정은 손으로 했다. 호출 인자 원문(`sites.txt`)을 보고, 그 값이 어느 graph 필드(같은 입력 버전)에서 오는지 호출부를 열어 확인했다. 확인한 파일은 §2 표의 근거 칸에 적었다.
- **한계**: (i) 인스턴스 메서드 호출(`obj.m()`)은 해석하지 않았다. 그래서 일부 뿌리가 '?(cycle)'나 엉뚱한 뿌리로 나온다. 예: `ss_evaluate`는 실제로 `search/kernel.py`가 부른다. (ii) 공유 호출이 아닌 인라인 중복(같은 식을 두 파일에 따로 씀)은 `dup_names.tsv`(이름이 같은 함수)와 `judged_constraints` 소비자 grep으로만 찾았다. 전수가 아니다. (iii) 실행 계측(같은 키 호출 수)은 하지 않았다. 판정은 정적 근거다.

## 2. 분류 결과

| 분류 | 개수 | 뜻 |
|---|---|---|
| A | 2 | 계산 블록 자체 호출 -- 같은 입력이면 S3 graft(`metrics_dc`, `passive_area_decl`) |
| A′ | 6 | LUT 파생표(`derived`·`tol_v_table`·`tol_vdsat_table` 표 자체·`midpoint_l_bin_checks`·`noise_planes`·`edge_cost`/`tol_vdsat`) -- 승인 예외(LUT memo·디스크 캐시 U-87) |
| **B** | **21** | 같은 입력 재계산 -- §2.1 사안 B1~B15(인라인 3건 포함) |
| C | 71 | 다른 입력 -- LUT 내부 보간·근·LOO 도구 31, 봉인점 대 출발 추정점 LUT 조회·소신호 풀이 도구, θ마다 다른 탐색 도구, layout 다른 소자 집합·행 수 등 |
| D | 1 | `sizing/_helpers_lut.tol_v_cell` -- `dc_columns` 반복점 대 `dc_tolerances` 봉인값. 마지막 반복점이 봉인값과 같은 입력인지 미확인 |
| E | 21 | 한 블록 안(`start_intervals`·`metrics_aux`·`metrics_ss`·`search_domain`·`build_s1v`) -- 규칙상 블록 안 값 |
| X | 11 | 계산값 아님: 상수 표(`metric_registry`·`metric_catalog`), 접근자(`w_key_of`·`slice_of`·`l_anchors`), 오류 꼬리표(`with_device`), 장식자, 입력 θ 검사(`check_theta`), 투영 재구성(`device_views`·`node_values`(sizing)·`canonical_row_key`) |

함수별 분류·한 줄 근거는 `shared_pure_fn_audit/classification.tsv`에 있다.

### 2.1 (B) 같은 입력 재계산 -- 사안 표

열 설명: '같은 입력 근거' = 두 자리가 읽는 graph 필드·인자가 같은 버전이라는 근거. '정본 자리 후보' = graph 규칙 1에 따라 값을 둘 필드와 writer(층·블록). '계획 소유' = 계획(plan-v6384)에 그 자리를 하나로 만드는 card 문언이 있는가.

| # | 값(정의) | 자리(재작성 범위 인용) | 같은 입력 근거 | 정본 자리 후보(층·writer) | 계획 소유 |
|---|---|---|---|---|---|
| B1 | 소신호 회로 `ss_circuit` + 그 스탬프(`mos_stamps`·`two_terminal_stamps`·`admittance_pair`) | `metrics/metrics_aux.py:105` 대 `metrics/ss_metrics.py:394`(스탬프는 `_helpers_nodal.py:29` 대 `mna_build.py:62-63`) | 같은 projection의 `ss_dev`·`passive_value`·`pins`·`dc_colour`를 읽는다. `metrics_aux` 머리말에 "metrics_ss 와 같은 정준 순서로 ss_circuit 을 다시 만든다(같은 입력 -> 같은 회로)"라고 적혀 있다 | `graph.ss_circuit`(+ `graph.ss_nodal` 인수분해) -- ss 층, writer 하나 | **있음** -- IT-2c(plan 1639행: `graph.ss_circuit`·`ss_nodal` READS). as-built는 미구현 |
| B2 | 소자별 VDsat(dc_op) · tol_VDsat 셀(L, VDS) | `sizing/seal_saturation.py:36·42` 대 `metrics/metrics_aux.py:119-120` | 두 자리 모두 `device.dc_op`의 (kind, w_key, L, vgs, vds, vsb)로 같은 LUT 조회를 한다 | device 필드(예: 봉인 7 앞 S2 dc 층 `dc_vdsat`·`dc_tol_vdsat`, writer 하나). 봉인 7과 `metrics_aux`(ls_swing·sat 행)가 READS | **없음**. HC-S는 '정본 **함수** `sat_threshold` 하나'라 오히려 충돌(§3.2) |
| B3 | 봉인 (L, vgs, vds, vsb)의 LUT 순방향 점 `OpPoint`(IDu·gm/ID·gds_per_w·VTH) | `sizing/block_columns.py:825`(최종 노드 전압, 비writer 좌표) · `sizing/block_widths.py:46`(전 MOS) · `metrics/ss_linearize.py:65`(`ss_dev`) | `dc_widths`는 `dc_columns`가 쓴 `node.dc_v`에서 단자 전압을 만든다. `ss_dev`는 그 결과 `dc_op`의 같은 네 값으로 다시 조회한다. `DeviceOp` 머리말은 이미 "같은 순방향 조회를 항목마다 다시 하지 않는다"(`idu_forward`)고 한다. 그러나 `gds_per_w`는 싣지 않아 `ss_dev`가 다시 조회한다 | `device.dc_op`(writer `dc_widths`)에 OpPoint 전체를 싣는다. `dc_columns`의 최종 IDu는 `dc_ln_idu`로 이미 쓰므로 `dc_widths`가 READS | 없음 |
| B4 | S1 -> 뷰 계산 모형 `NetModel`(diode_nodes·composite_* 술어 포함) | `graph/s1v_fields.py:253`(`build_s1v`) 대 `graph/coupling_vars.py:179`(`coupling_vars`) | 둘 다 `net_model(s1)`이고 입력은 같은 S1 투영이다. 모듈 머리말은 "S0 당 1회"라고 하지만 실제로는 두 번 만든다 | S1v 필드(writer `build_s1v`). `coupling_vars`가 READS. 또는 모형 안 술어(`diode_nodes` 등)만 S1 필드로 둔다 -- G2 판정에 달림 | 없음 |
| B5 | 블록 이득 모형 입력: `block_spec`·`ParamTables`·`block_gain_model_of(local, spec)` | `metrics/achievability.py:153·161·352` 대 `search/iv_context.py:55-56`·`search/iv_gain_l.py:106` | `start_intervals`는 `graph/ach: local_inputs`를 READS하지만, 같은 함수(`block_spec`)로 블록 spec을 다시 만든다. 같은 (memo, w_keys, grids)로 `ParamTables`를 만들고, 같은 (local, spec)으로 모형을 다시 짓는다 | `graph/ach` 칸(writer `achievability`) -- 블록 spec·모형 구조. 평가 `row_gains`는 (C)(계획 예시 '범위 끝 이득 함수') | 부분 -- LA-1 범위 15(a)는 g_i 필드만, UB-1은 구현 둘 -> 하나만 다룬다. 블록 사이 재구축은 없음 |
| B6 | kind별 θ 전류 상자 원값 (I_off, I_max_LUT) | `search/search_domain.py:100` 대 `search/iv_context.py:107` | 둘 다 `current_box(lut, kind)`이고 같은 LUT·kind다. 모듈 머리말은 "S0 당 kind 마다 1회(search_domain 이 표로 든다)"라고 한다 | `graph/kernel: search_domain` 칸(writer `search_domain`) -- 예산으로 깎기 전 원 상자 | 없음 |
| B7 | 출발 상자 중심점·n_θ | `search/search_context.py:137`(`_wire_sweep_memo` -- 변수 **개수만** 쓴다) · `search/residual_probe.py:67` · `search/layer0_center.py:662`(rung None) | 셋 다 `centre_start(sctx)`이고 같은 sctx다 | n_θ = `search_domain` 칸(변수 수) READS. 중심점 경로 자체는 v6.38.4 P4가 지운다(LA-1 범위 6) | 부분 -- P4가 경로를 지운다. n_θ 자리는 없음 |
| B8 | 되먹임 소자의 절단 넷(입력 포트 넷 쪽 단자) | `authoring/spec_elements.py:104`(검사) · `authoring/spec_views.py:101`(루프 뷰) · 둘째 구현 `metrics/noise_plan.py:28` `_input_side`(`metrics_ss` 안, θ마다) | topology + spec `feedback`이 같다. `noise_plan`은 같은 S1 pins에서 만든 ss 노드 색인으로 같은 정의를 다시 세운다(규칙 3: 같은 정의) | S0 필드 하나(예: `noise_decl` 블록 `graph/s1v: noise_input_cells` 확장 또는 루프 뷰 `cuts`의 S0 자리). 로더 검사가 graph보다 앞이면 G1 판정 필요 | **충돌** -- N6.26 TN-1이 '순수 함수 하나·세 호출 자리'로 정함(§3.2) |
| B9 | gate 전용 넷(DEC-104 R1 '바이어스 고정 넷' 계열 구조 술어) | `authoring/bias_inputs.py:23` `gate_only_nets` 대 `authoring/spec_views.py:163` `_gate_only_nets`(+182행 `fixed` = 레일 ∪ 입력 ∪ gate 전용) | 같은 topology에서 정의가 거의 같은 두 구현이다(제외 포트 집합: 전체 포트 대 입력 포트만 -- 규칙 3이면 다른 축을 문서화하거나 하나로) | 로더 검증값 `bias_inputs`(선언 = gate 전용 넷임을 로더가 단언) 또는 S1 node 필드 | 없음(R1 술어는 계획이 '구조 술어 예외 없음'으로 이름만 듦) |
| B10 | topology가 아는 넷 집합(MOS d·g·s·bulk ∪ 2단자 단자) | `authoring/topology_load.py:88` · `spec_constraints.py:301` · `spec_gain_override.py:51` · `spec_node_targets.py:28` · `name_uniqueness.py:45` · `hidden_rails.py:17-18` | 같은 `topology.devices/passives/sources` | 로더 산출 `TopologyDoc` 칸 또는 S0/S1 node 집합 -- **정본 자리 미정(G1)** | 없음 |
| B11 | 가지치기 전 DC 엣지 | `authoring/hidden_rails.py:24`(로더 검사) 대 `graph/s1_structure.py:80` | 같은 소자 목록 | S1 `s1_structure`가 쓰는 엣지 필드. 로더 검사가 graph보다 앞이라 READS가 층 역전 -- **G1** | 없음 |
| B12 | 정규화 레일 전위 ((넷, V) tuple) | `graph/s1_build.py:71` 대 `sizing/kernel_context.py:61`(S1 key 지문과 대조하려고 다시 정규화) | 같은 supplies_v·레일 집합. S1은 지문만 key에 두고 값은 필드로 두지 않는다 | S1 필드(writer S1 블록 하나). `kernel_context`는 READS(대조 불필요) | 없음 |
| B13 | spec -> DC 입력 투영 `DcInputs`(+ extras 준비 `spec_bounds`·`untie`) | `pipeline/stage_a.py:213` 대 `pipeline/stage_b.py:151`. extras는 `stage_b.py:153-156` 대 `search/search_context.py:164-168` | 같은 spec 객체 | 단계 A 결과 참조(규칙 4) 또는 S0 필드 -- 파이프라인 접착 코드라 **G6** | 없음 |
| B14 | 판정 제약 파생값: 면적 예산 min(`area_search_m2 <=`), 이득 목표 max(`gain >=`) | 면적: `metrics/achievability.py:257` · `pipeline/stage_b.py:153` · `search/iv_context.py:89-90` · `search/search_context.py:168`. 이득: `metrics/achievability.py:149` · `search/iv_context.py:39·54` | 같은 spec `judged_constraints`에서 같은 필터와 min/max를 매번 계산한다 | `graph/kernel: constraint_classes` 칸(writer `constraint_classes`) -- 판정 대상 칸과 같은 블록 | **부분** -- SF-1 8 '지우면 깨지는 곳'에 소비자 행은 있다. 완료 조건은 술어 호출 0만 보고 파생 예산·목표 재계산은 보지 않음 |
| B15 | layout 그룹 무게중심 차 (dx, dy) · hub 방향 ends | `layout/rows.py:204`(`offsets(old,…)` -- `GroupLayout.dx/dy`가 이미 `ly_groups`에 있음) · `layout/rows.py:188` 대 `layout/pattern_select.py:249`(`orient`) | 같은 그룹·같은 `ly_point`/`ly_pins`. dx/dy는 writer `ly_pattern_select`가 이미 필드로 쓴다 | dx/dy: `ly_groups` READS(이미 필드). ends: `ly_groups` 칸 추가 | 없음 |

(B) 21개 함수와 사안의 대응: B1 = `ss_circuit`·`mos_stamps`·`two_terminal_stamps`·`admittance_pair`, B2 = `vdsat`·`tol_vdsat_table`(셀 조회), B3 = `op_point`·`forward_point`, B4 = `net_model`, B5 = `block_gain_model_of`·`ParamTables`, B6 = `current_box`, B7 = `centre_start`, B8 = `input_terminal_nets`, B9·B10 = `mos_terminal_nets`·`two_terminal_nets`, B11 = `dc_edges_unpruned`, B12 = `supplies_declaration`, B13 = `dc_inputs_from_spec`, B15 = `offsets`·`orient`. B14와 B8 `_input_side`, B9 쌍둥이는 인라인·쌍둥이 구현이라 공유 호출 목록 밖에서 찾았다.

### 2.2 (C) 다른 입력 -- 대표 갈래

- **봉인점 대 출발 추정점**(계획 예시와 같은 꼴): `caps`·`noise_params`·`mismatch_dvgs`·`mismatch_sigma_vgs`(봉인 `dc_op` 대 `start_intervals` 곡선 추정점), 소신호 풀이 도구 `solve_dc_limit`·`solve_responses`·`analyze_loop`·`probe_pencil`·`finite_eigs`·`product_at`·`solve_point`·`dc_limit_parts`(`metrics_ss` 봉인 ss 대 `macro_poles` 매크로 망), `row_gains`(범위 끝 격자 대 행 평가).
- **같은 함수, 다른 점**: `op_point`의 나머지 자리(봉인 9 꺼짐 전류 VGS = 0 `seal_conduction.py:29`, 슬루 전류 `vgs_max` `ls_fields.py:55`, 폭 키별 `slice_density.py:28`, LUT 내부 격자), `vdsat`의 `dc_columns` 반복점·`vdsat_curve` 격자.
- **θ·시작점마다**: `evaluate`·`fd_jacobian`·`solve_eps`·`cone_rows`·`expand_ties`·`ln_idu_floors`·`canonical_order`(시작 칸 L 변수 포함)·`nondominated`·`area_tie_m2`·`run_kernel`·`theta_passive_pairs`(커널 봉인·비봉인 배타 갈래).
- **LUT 내부 도구 31개**(보간·근·LOO·bin·격자) -- 다른 배열.
- **layout**: Euler·crossover·행 패턴 함수 -- 다른 소자 집합·행 수(`ly_rows`는 현재 행 수 + 1부터 시도).

### 2.3 (E) 한 블록 안 -- 규칙상 허용, NFR-2 점검 대상

블록 안 같은 입력 반복(규칙 '한 블록 안에서만 쓰면 블록 안 값'에 걸리지 않지만, 같은 실행 안 재계산이라 O-15 (E) 블록 안 local memo 대상):
- `start_intervals`: `dominant_node(ctx.transfer)` 2회(`macro_poles.py:330`·`start_intervals.py:268`), `guard_devices(ctx)`·`guard_input_gm_id(같은 인자)` 2회(`iv_matching_l.py:109·140` 대 `iv_noise.py:76·86`), `curve_bundle_of` 19자리(같은 (소자, L) 반복 -- 블록 안 memo 여부 미확인).
- `metrics_aux`: 같은 `ss.circuit`의 `conductance_matrix`·`nodal_factor` 최대 3회(`block_residual.py:73`·`offset_analysis.py:69`·`offset_systematic.py:46`), `view_system` 3회. B1의 IT-2c `graph.ss_nodal`이 이것도 대체한다.
- `build_s1v`: `collect_views(model, …)` 3회(`s1v_fields.py:122`·`254`, 다른 제약 부분집합 -- 입력이 다름).

## 3. 계획 v6.38.4 SF-1 범위 8 문언 평가

대상 문장(plan 2225행): "같은 입력 버전에서 같은 값을 내는 계산(술어 포함 -- …구조 술어 모두)을 두 자리 이상이 쓰면 그 값은 graph 필드 하나(writer 하나)이고 소비자는 READS한다 …; 한 블록 안에서만 쓰면 블록 안 값이고, 입력이 다른 호출(출발 추정 동작점 대 봉인값 -- R9 조회·범위 끝 이득 함수)은 다른 양이라 순수 함수 정의 하나를 공유한다(N6.1 '조건부 제작 함수')".

### 3.1 (B)를 빠짐없이 덮는가

| 판단 | 근거 |
|---|---|
| **원칙 문장은 덮음** | B1~B15는 모두 '같은 입력 버전·두 자리 이상·값' 조건을 충족한다. 구조 술어(B4 `diode_nodes`, B9 gate 전용 넷, B11 DC 엣지)도 '구조 술어 예외 없음'으로 들어간다 |
| **강제 수단은 판정 대상 술어 하나뿐** | 문장이 SF-1 범위 8(`counted_rails`·E-03 항목) 안에 있다. 완료 toy·`git grep`도 판정 대상 술어만 잰다. B2~B13·B15(13건)는 어느 card에도 대체 자리·완료 조건이 없다. B1은 IT-2c, B7은 일부만 P4가 지운다 |
| **B14 미완** | '지우면 깨지는 곳'에 `achievability.py:149·257`·`stage_b.py:153`·`iv_context.py:39·89`·`search_context.py:168`이 있다. 하지만 이 자리들이 술어 대신 칸을 READS하게 바뀐 뒤에도 같은 필터 + min/max(예산·목표)는 4자리·3자리에서 다시 계산한다. 완료 조건 '소비자 쪽 술어 호출 0'은 이것을 잡지 못한다 |
| **문장 위치** | card 범위 항목 안의 전역 규칙이다. 다른 card(TN-1·HC-S·UB-1·LA-1)의 design·완료 조건이 이 문장을 인용할 의무가 없다. N3.3 graph 규칙 층이나 DEC 행으로 올려야 전 card 점검 항목이 된다(프로젝트 CLAUDE.md 규칙 7 '전달·검증 단계 점검') |

### 3.2 다른 계획 문언과 충돌(같은 입력인데 '순수 함수 공유'로 정한 곳)

| 자리 | 지금 문언 | 한 규칙 적용 결과 |
|---|---|---|
| N6.26 TN-1(plan 2182-2192행) | 절단 넷 규칙 = 순수 함수 하나, `spec_elements`·`spec_views`·`noise_plan` 세 자리가 직접 부른다. 완료 = '정의 1곳·호출 자리 셋' | 세 자리 입력은 같은 topology + feedback이다(B8). 그래서 값은 S0 필드 하나, 호출 자리는 writer 하나여야 한다. TN-1 완료 조건 '호출 자리 셋'은 한 규칙 위반을 완료로 센다 |
| headroom-chain HC-S(`sat_threshold` 정본 '함수', headroom-chain plan 51·139행) | 포화 기준값은 정본 함수 `sat_threshold` 하나에서만 읽는다 | 봉인 `dc_op` 점의 사용(봉인 7·`metrics_aux` ls_swing·sat 행 -- B2)은 같은 입력이라 필드여야 한다. 출발 동작점·R-1′ 후보점 사용은 다른 입력이라 함수 공유가 허용된다. 문언이 두 갈래를 나누지 않는다 |

### 3.3 경계 문언 -- (C)와 (B)를 가르는가

계획의 경계는 예시 하나('출발 추정 동작점 대 봉인값')와 '한 블록 안' 단서뿐이다. 이 감사에서 실제로 판정이 갈린 축은 다음과 같다. 문언은 어느 것도 정하지 않는다.

| # | 축 | 이 감사의 사례 | 문언이 정해야 할 것 |
|---|---|---|---|
| G1 | **로더(authoring) 단계** -- graph가 생기기 전 계산 | B8(로더 두 자리), B10(로더 6자리), B11(로더 검사 대 S1) | 로더 안 같은 입력 재계산이 대상인가, 정본 자리가 로더 산출 객체 칸인가 S0 graph 필드인가. 로더 검사가 S1 필드를 READS하면 층이 역전되는데 그것을 어떻게 처리하는가. SF-1 8 자체가 로더 칸 `ConstraintDecl.judged`를 S0 필드로 옮기므로, 문언은 '로더 칸은 정본 아님'을 함의하지만 명시하지 않는다 |
| G2 | **투영·재구성 뷰** | B4 `net_model`(재구성 + 파생 술어 섞임), X `device_views`·`node_values`·`canonical_row_key` | '필드 열을 읽어 모양만 바꾼 것(새 양 없음)'은 계산이 아니라 READS이고, 파생 술어·집계가 하나라도 있으면 계산이라는 판정 기준 |
| G3 | **LUT memo 적중** | B2·B3 -- 같은 봉인점 LUT 조회는 memo 적중이라 비용은 거의 0이지만 생산자는 둘 | 승인 예외(LUT memo U-87)가 '두 자리 생산'까지 면제하는가. `DeviceOp.idu_forward` 선례는 면제하지 않는 쪽이다. 문언으로 확정해야 한다 |
| G4 | **모형 생성 대 모형 평가** | B5 -- 모형 생성(같은 입력)과 `row_gains` 평가(다른 입력)가 한 함수 묶음 안에 있음 | '입력이 다른 호출'은 평가 단계에만 해당하고, 평가 입력과 무관한 구조·모형 생성은 같은 입력이라 필드라는 분해 규칙 |
| G5 | **반복 풀이의 마지막 점 대 봉인값** | B3 `dc_columns:825` 대 `dc_widths`, D `tol_v_cell` | 입력 동일성 = 읽는 graph 필드의 버전(값의 역할 이름이 아님). 풀이 블록이 최종값으로 쓴 필드와 같은 버전을 다음 블록이 다시 조회하면 같은 입력 |
| G6 | **블록 밖 파이프라인 접착 코드** | B13 `stage_a`·`stage_b`·`search_context` extras 준비, B7 `_wire_sweep_memo` | '자리'가 계산 블록만인가, 파이프라인 함수도 포함하는가. 포함한다면 writer가 없는 자리의 정본은 단계 결과 참조(규칙 4)인가 S0 블록인가 |
| G7 | **블록 안 값의 층** | B8 `noise_plan`은 `metrics_ss` 한 블록 안이지만 입력이 θ 무관 S0 양이라 θ마다 다시 계산 | '한 블록 안에서만 쓰면 블록 안 값' 단서가 블록 입력보다 낮은 층(S0·S1)만 읽는 값에도 적용되는가 -- 적용되면 NFR-2(같은 값 재계산 금지)와 충돌 |

## 4. 권고(재작성 범위 기준, O-153·O-169)

1. **한 규칙의 자리**: SF-1 범위 8의 문장을 N3.3 graph 규칙(또는 DEC 행)으로 옮긴다. SF-1 8에는 판정 대상 술어 적용만 남긴다. 그러면 모든 design·card 완료 조건이 이 규칙을 점검 항목으로 갖는다.
2. **경계 정의 G1~G7을 문언에 넣는다.** 최소 기본안은 다음과 같다(원칙 근거: graph 규칙 1·3·4, NFR-2).
   - 입력 동일성 = 읽는 graph 필드·선언의 버전(G5).
   - 새 양이 없는 열 재구성은 READS(G2).
   - LUT memo는 비용 예외일 뿐 생산자 예외가 아니다(G3).
   - 구조 생성과 점 평가는 분해한다(G4).
   - 블록 입력 층보다 낮은 층만 읽는 값은 그 층의 필드다(G7).
   - 로더·파이프라인은 정본 자리가 아니다(G1·G6). 로더 검사가 graph 앞에 있어야 하는 사안(B10·B11)은 정본 자리가 없으므로, graph 규칙 6대로 계획이 먼저 정한다(로더 검사를 S1 블록으로 옮길지 등).
3. **(B) 대체 card 표**: §2.1 B2~B15(B1은 IT-2c)를 N6.35 예외 정리 표와 같은 꼴(대체 규칙·소유 card·완료 toy = `git grep` 생산 자리 1·READS)로 등록한다. 기존 card 범위에 넣을 후보는 다음과 같다(파일 겹침 기준).
   - B5·B6·B7·B14 -> LA-1 / SF-1
   - B2 -> HC-1·HC-S
   - B3 -> DE-1 또는 별도
   - B4 -> GC 계열
   - B8 -> TN-1 재작성
   - B9 -> IT-1(DEC-106 입력 공통모드)·R1
   - B15 -> LI-1
4. **충돌 정정**: TN-1 완료 조건 '호출 자리 셋'을 'writer 1·READS'로 바꾼다. HC-S `sat_threshold`는 봉인점 사용(필드)과 출발점 사용(함수 공유)으로 나눈다. 둘 다 원래 취지와 다르게 바뀌므로 사용자 결정 대상이다.
5. **B14 완료 조건 보강**: '판정 대상 칸 READS' 외에 '면적 예산·이득 목표 계산 자리 = `constraint_classes` 블록 하나(`git grep` 소비자 쪽 min/max 0)'를 SF-1 8 완료 toy에 더한다.

### 원칙 점검(권고 자체)

- graph 규칙 1·3·4: 정본 자리 후보는 모두 기존 블록의 필드다(새 cache·memo·sctx 슬롯·사본 0). 규칙 6이 걸리는 B10·B11은 '계획 먼저'로 올렸다.
- 규칙 2: E(블록 안 반복)는 O-15 (E) 블록 안 local memo 범위로만 언급했다. 새 cache는 권고하지 않았다.
- O-165·O-153: 엔진 파일:행은 재작성 범위로만 인용했다. 정본 자리는 층·writer 정의로 정했고, 지금 함수 이름·자리를 근거로 쓰지 않았다.
- 원래 취지와 다름: 권고 4(TN-1 '순수 함수 공유' -> 필드, HC-S '정본 함수' -> 필드 + 함수 분리)는 승인된 card 문언의 취지를 바꾼다. 따라서 사용자 결정이 필요하다.
- 실측 출처: 모든 수치는 위 스크립트 산출(`classification.tsv`·`summary.tsv`·`sites.txt`)과 이 문서에 적은 파일:행을 직접 열람한 결과다. 같은 키 호출 수 같은 실행 계측은 하지 않았다(한계 §1).
