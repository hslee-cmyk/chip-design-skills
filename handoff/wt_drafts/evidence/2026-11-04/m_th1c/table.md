# M-TH1c 정적 표 (2026-11-04, 위임 A-66, 재작성 A-67)

정의: 계획 N5.3 M-TH1c(P:1259), Q-TH1 O-186 (A)(L2), DEC-11, N3.6 정본 (9)(10). 방법: `m_th1c_ast.py`가 master `dda16724` 트리(worktree `docs-cards1104e`)의 비test `.py`를 `ast`로 파싱하고 정점·좌표는 텍스트로 잡는다. `gmid_engine` import·실행 0, LUT 0. 원자료 `consumers.jsonl`, 요약 `summary.txt`. 파싱 실패 0. 엔진 인용 = 재작성 범위(원칙 8). 앞 판 = `table_a66.md`, `a66/`.

**A-67에서 넓힌 것**: `curve_value`·`curve_bundle`·`curve_bundle_of`·`_at_gm_id`·`hull`(gm/ID 축 읽기 본체), `gm_id_for_target`, `peak_index`·`monotone_end`·`strong_inversion_root`·`branch_targets`·`ln_idu_floors`·`_peak_floor`·`_conduction_ok`·`curve_report`(정점·분지), 텍스트 `peak_text`(argmax 정점), `gm_coord_text`(gm/ID 좌표 변수).

**한계**: IT·EO-1·card C·TB-1·HC-S 코드가 master에 없다. 각 소유 card는 자기 base에서 다시 돌린다. 텍스트 적중의 판정은 손 분류다. `iv_gain_l.py`의 소비 세부는 `gm_id_lo` 입력까지만 읽었다.

**요약**: 적중 53파일(앞 판 40) + 손 추가 2(재판정 q5, 칸·인자 선언이라 패턴 밖). 소비자·정의 44(앞 판 28), 대상 아님 11. 소유: LI-1 10, LA-1 29, WB-1 5. 소유 없음 0. 멈춤 0.

## 소비자와 소유

| # | 파일(`E/`) | 무엇 | 분류 | 소유 | 근거 |
|---|---|---|---|---|---|
| 1 | `layout/slice_density.py:27` | `vgs_for_gm_id` 호출 | 역산 | LI-1 | P:1981, O-186 (L2) |
| 2~6 | `layout/finger_candidates.py`, `canon_block.py`, `contract_input.py`, `outputs.py`, `run.py` | 보존량·후보 gm_id | READS | LI-1 | P:1981 (2)(3) |
| 7 | `convergence/layout_input.py:72` | `op.gm_id` 사본 | READS | LI-1 | P:1981 (1) |
| 8 | `lut/vgs_root.py` | `vgs_for_gm_id` 정의 | 정의 | LI-1 | 비lut 소비자가 #1 하나, D40:116 |
| 손 | **`layout/contract_output.py:40·376`**, **`layout/w_tolerance.py:3·14·16`** | `gm_id` 칸, 인자 | READS | LI-1 | 재판정 q5, grep 확인, P:1983 |
| 9 | `search/_helpers_curves.py:29·152·154` | 곡선 표, `curve_value`, `_at_gm_id`, `hull` 정의 | 축 곡선 | LA-1 | P:2102, 41 §6 |
| 10~14 | `search/_helpers_guard.py`, `iv_area.py`, `iv_domain.py`, `iv_headroom.py`, `iv_speed.py` | 축 곡선, gm/ID 마디 | 축 곡선 | LA-1 | 같음 |
| 15~17 | `search/iv_matching_l.py`, `start_intervals.py`, `start_values.py` | `curve_value`, `QUANTITY_GM_ID` | 축 곡선 | LA-1 | 같음 |
| 18 | **`search/_helpers_area.py:36`** | `curve_value(IDU, gm_id[...])` | 축 곡선 | LA-1(새) | 판정 W3, grep 확인 |
| 19 | **`search/iv_currents.py:104·107`** | 같음 | 축 곡선 | LA-1(새) | 같음 |
| 20 | **`search/iv_noise.py:58·61`** | 같음 | 축 곡선 | LA-1(새) | 같음 |
| 21 | **`search/macro_poles.py:91`** | `curve_value(GAIN, gm_id[...])` | 축 곡선 | LA-1(새) | 같음, P:2040 매크로 |
| 22 | **`search/iv_gain_l.py:98·116`** | `gm_id_lo` 입력 | gm/ID 좌표 | LA-1(새) | LA-1a 이득 L 하한(P:2595 'gm/ID 역산 없음') |
| 23~27 | `lut/_helpers_gmid_axis.py`, `ft_curve.py`, `idu_curve.py`, `intrinsic_gain_curve.py`, `vdsat_curve.py` | 축 곡선 정의 | 정의 | LA-1 | 마지막 소비자 전환, D40:116 |
| 28 | `lut/derived_fns.py:111·136`, `:37~41` | `vdsat_curve`, `intrinsic_gain_curve`, **`_conduction_ok` 정점 분지(`edge_costs`)** | API 소비, 정점 | LA-1(정점 쪽 O-207) | 정의 삭제와 함께. 정점 쪽은 판정 표에 없음, 내 grep |
| 29 | `search/constraints.py:45~49` | `CON_INVERSION` 행 | 정점 | LA-1 O-207(A-66 WB-1에서 번복) | N3.6 (10), 판정 W2. WB-1은 키만 |
| 30 | **`search/cell_floor.py`** | `_peak_floor`, `ln_idu_floors` | 정점 | LA-1 O-207(새) | 판정 W3 |
| 31 | **`search/search_domain.py:54~57`** | ln IDu 상자 정점 하한 | 정점 | LA-1 O-207(새) | 판정 W3 |
| 32·33 | **`search/layer0_center.py:61·72·292·468·565`**, **`search/slsqp_outer.py:36·66`** | `_HARD_PREFIXES`, `ln_idu_floors` 호출 | 정점 소비 | LA-1 O-207(새) | 판정 표에 없음, 내 grep |
| 34 | **`lut/vgs_current_density.py:45`** | `peak_index` 역산 분지 | 정의역 분지 | LA-1 O-207(앞 판 '대상 아님' 틀림) | 판정 W3, 원문 확인 |
| 35 | **`lut/id_inverse.py:32·56`** | `gm_id_for_target`, 분지. 비lut 호출 0 | 역산 | LA-1 O-207(새) | DEC-11 밖 역산. 판정 표에 없음, 내 grep |
| 36·37 | **`lut/curve_check.py:27`**, **`lut/_helpers_root.py`**(`peak_index`, `monotone_end`) | 분지 검사, 정의 | 정점 | LA-1 O-207(새) | 같은 정점 규칙 |
| 38~40 | `lut/tolerance.py`, `lut/lut_types.py`(칸 :22·:346·:350·:373), `lut/midpoint_checks.py`(:55~:60, `_inverse`) | `gm_id_inverse` 지표 | 지표 | WB-1 | P:681, 슬라이스별 표 구성 전 |
| 41 | **`lut/_helpers_loo.py:131`** | `branch_targets`(사용 = `tolerance`, `midpoint_checks`뿐) | 지표 | WB-1(새) | 지표 삭제로 호출 0, 함께 삭제 |
| 42 | `metrics/achievability_types.py:42` | 주석 | 주석 | WB-1 | 같은 파일 |

**`strong_inversion_root`**(`lut/_helpers_root.py`): 사용 파일 = `tolerance`, `midpoint_checks`, `vgs_root`. WB-1 뒤 `vgs_root` 하나라 규칙 A `helper_single_user`다. WB-1이 `lut/vgs_root.py`로 옮기고 LI-1이 함께 지운다.

**LR5 `measure_L_knee`**: 엔진 정의·호출 0.

## 대상 아님(11)

`lut/gm_id_curve.py`(VGS 마디 곡선), `lut/__init__.py`, `search/__init__.py`(재수출), `search/fd_jacobian.py`, `search/front_query.py`, `metrics/metrics_aux.py`, `metrics/ss_linearize.py`, `sizing/seal_conduction.py`, `seal_kvl_branch.py`, `seal_tolerances.py`, `seal_vgs_match.py`. `dc_op.gm_id` 순방향 칸이거나 재수출이다.

## 새 소비자 판정

`m_th1c_diff.py <base consumers.jsonl> <head consumers.jsonl>`. 키 (파일, how, name), how ≠ `gm_id_field_text`. 그래서 `curve_value` 호출 파일 집합, 정점 텍스트, gm/ID 좌표 파일이 base와 같아야 한다. WB-1이 포락으로 고치는 자리는 키가 그대로이고, 새 파일 `sizing/block_dc.py`의 `dc_op.gm_id`는 키 밖이다.
