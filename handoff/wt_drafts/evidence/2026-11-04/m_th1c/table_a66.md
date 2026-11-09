# M-TH1c 정적 표 (2026-11-04, 위임 A-66)

정의: 계획 N5.3 M-TH1c(P:1259), Q-TH1 O-186 (A)(L2), DEC-11. 방법: `m_th1c_ast.py`가 master `dda16724` 트리(worktree `docs-cards1104e`)의 비test `.py`를 `ast`로 파싱. `gmid_engine` import·실행 0, LUT 0. 원자료 `consumers.jsonl`, 요약 `summary.txt`. 파싱 실패 0. 엔진 인용 = 재작성 범위(원칙 8).

**한계**: IT·EO-1·card C·TB-1·HC-S 코드가 master에 없다. 각 소유 card는 자기 base에서 스크립트를 다시 돌린다. 동적 호출(`_CURVE_FN` 표 경유)은 이름 참조로 잡았다. `curve.gm_id` 칸 읽기는 텍스트 grep이라 판정은 손 분류다.

**요약**: 적중 40파일. 소비자·정의 자리 28, 순방향이라 대상 아님 12. **표 전 명시 소유 없음 12파일**, 전부 아래 배정.

## 소비자와 소유

| # | 파일(`E/`) | 무엇 | 분류 | 소유 card | 근거 |
|---|---|---|---|---|---|
| 1 | `layout/slice_density.py:27` | `vgs_for_gm_id` 호출 | 역산 | LI-1 | P:1981 (5), O-186 (L2) `J_slice(VGS)` |
| 2 | `layout/finger_candidates.py:45·47` | `point.gm_id` 키 | gm/ID READS | LI-1 | P:1981 (2) 명시 |
| 3~6 | `layout/canon_block.py:94·144`, `contract_input.py:80`, `outputs.py:79`, `run.py:58` | 보존량 gm_id | gm/ID READS | LI-1 | P:1981 (3), LY1 |
| 7 | `convergence/layout_input.py:72` | `float(op.gm_id)` 사본 | gm/ID READS | LI-1 | P:1981 (1) |
| 8 | `search/_helpers_curves.py:29·152·154` | gm/ID 축 곡선 표, `_at_gm_id` | 축 곡선 | LA-1 | P:2102 M-TH1a·M-TH1c, 41 §6(ln IDu 구간), D-TH1 |
| 9~16 | `search/_helpers_guard.py:55·71·81`, `iv_area.py:61`, `iv_domain.py:60·88·97`, `iv_headroom.py:148`, `iv_matching_l.py:76`, `iv_speed.py:66·77`, `start_intervals.py`(147·207·322~341), `start_values.py:16` | gm/ID 마디·경계, `QUANTITY_GM_ID` | 축 곡선 | LA-1 | 같음 |
| 17 | `lut/vgs_root.py` | `vgs_for_gm_id` 정의 | 정의 | **없음 → LI-1** | 비lut 소비자가 #1 하나. D40:116·2222 '지운다'. 그 호출을 없애는 card가 같은 변경에서 지운다(O-153) |
| 18~22 | `lut/_helpers_gmid_axis.py`, `ft_curve.py`, `idu_curve.py`, `intrinsic_gain_curve.py`, `vdsat_curve.py` | gm/ID 축 곡선 정의 | 정의 | **없음 → LA-1** | 소비자 #8·#9~16·#23. 마지막 소비자 전환이 LA-1. D40:116 |
| 23 | `lut/derived_fns.py:111`(`_reference_vds`), `:136`(`_param_row`) | `vdsat_curve`, `intrinsic_gain_curve`. 값은 VGS 마디로 읽음 | 축 곡선 API 소비 | **없음 → LA-1** | #18~22를 지우려면 함께 순방향 조회로 바꿔야 한다. `param_row` 소비자는 GB4(UB-1·WB-1 포락)이고 뜻은 안 바뀐다 |
| 24 | `search/constraints.py:45·47·49` | `gm_id_curve` 정점, `CON_INVERSION` 행. `search/layer0_center.py:72`도 읽음 | 철회된 행 | **없음 → WB-1** | O-207, N3.6 정본 (10): 행을 두지 않는다. 삭제 card가 어디에도 없다(계획·design·spec grep). WB-1이 같은 줄의 키를 바꾸는 자리라 옮기면 철회된 행을 슬라이스 위에 새로 짓게 된다 |
| 25~27 | `lut/tolerance.py`, `lut/lut_types.py:22`, `lut/midpoint_checks.py:55·126` | `gm_id_inverse` 지표 칸, 외부 값 | 지표 | **없음 → WB-1** | P:681 소비자 0, 비lut 조회 0(AST). WB-1이 tol 표를 슬라이스마다 처음 구성하므로 먼저 지우면 소비자 없는 지표를 슬라이스 수만큼 계산하지 않고 디스크 표 재구성도 한 번이다 |
| 28 | `metrics/achievability_types.py:42` | `METHOD_INVERSE` 주석의 `vgs_for_gm_id` | 주석만(이름 읽기 0) | **없음 → WB-1** | 같은 파일을 WB-1이 고친다. 41:496 단조 = `vgs_for_current_density`. 상수 자체는 이 표 범위 밖 |

**LR5 `measure_L_knee`**: 엔진 정의·호출 0. 소비자 없음. 구현할 card는 곡선을 ln IDu 축으로 읽는다(P:779).

## 대상 아님(순방향, 12파일)

`lut/gm_id_curve.py`(VGS 마디 곡선, `vgs_current_density`·`id_inverse`의 정의역, 역산 아님), `lut/id_inverse.py`, `lut/vgs_current_density.py`(DEC-11의 유일한 역산), `lut/__init__.py`(재수출, 지운 이름은 소유 card가 뺀다), `search/fd_jacobian.py`, `search/front_query.py`, `metrics/metrics_aux.py`, `metrics/ss_linearize.py`, `sizing/seal_conduction.py`, `sizing/seal_kvl_branch.py`, `sizing/seal_tolerances.py`, `sizing/seal_vgs_match.py`. 모두 `dc_op.gm_id`(순방향 조회 칸, DEC-88) 또는 VGS 축 곡선이다.

## WB-1 범위 안 소비자 전수

WB-1이 파일을 고치지만 소유가 LA-1인 자리(#8~16 일부, `search/iv_context.py` 경유): 키만 포락으로 바꾸고 곡선 뜻은 그대로다. **새 소비자 0**의 판정 = `m_th1c_diff.py <base consumers.jsonl> <head consumers.jsonl>`, 키 (파일, how, name), how ≠ `gm_id_field_text`, 새 키 0. 새 파일 `sizing/block_dc.py`의 `dc_op.gm_id`는 순방향 쓰기라 키 밖이다.
