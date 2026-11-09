# 커널 A6 b 경로('tol 미정 → 뿌리 `unsettled`, 창은 한 번만 적용') 도달성 판정

- 작성: 2026-10-22, 읽기 전용 분석(저장소 파일 수정 0, 실험 LUT·스크립트는 저장소 밖 `wt/_scratch_a6b/`).
- 대상 엔진: `wt/it2b-code`. 분석 중 HEAD가 `85847b49` → `89536b5e`(5bd20156 helper 되돌림 포함)로 움직였다(다른 주체). 판정에 쓰는 함수
  `_tolerance`·`_Circuit.tolerance`·`_measure`·`solve_self`는 두 리비전에서 AST가 같고, `_solve_input_window`·`region_rows`·`_interior_solution`은
  이름 바꿈(`solve`→`_solve`, `FAILURES`→`_FAILURES`, `out`→`rows`)뿐이다(ast 비교, `_scratch_a6b/src_*.py`). 실험은 HEAD 작업 트리로 돌렸다.
  작업 트리의 `tests/sizing/test_block_columns.py` 수정(+62/−6)은 이 분석이 만든 것이 아니다.

## 결론: (나)에 해당하되, 일반형 도달은 **실행으로 확인**했다

- **운영 LUT(sky130 v2)에서는 도달 불가**: 전 슬라이스 VDSAT 열 출처가 `slice`이고, 이 경우 tol_VDsat 정의 ⇒ id_equivalent tol_V 정의가 점 단위로 성립한다(아래 §2.2 증명). 실측도 0건(§3).
- **일반형으로는 도달 가능**: VDSAT가 기준 LUT(`cap_table`)에서 오고, 기준 LUT의 점 조건(on_mask·VS 축)이 슬라이스보다 넓어 슬라이스 셀에는 LOO 점이 없는데 기준 LUT 셀에는 있을 때.
  저장소 밖 toy로 `dc_columns`를 끝까지 돌려 `Window(lo=0.0, hi=0.8825, constraints=1, input_status='unsettled', tol_v=None)`를 얻었다(§4).
- 픽스처를 만드는 데 엔진 변경은 필요 없다. test 도구는 `write_r4_lut`에 기준 LUT VDSAT 열을 넣는 인자 하나가 필요하다(또는 test 파일 안에서 `r4_arrays`+`load_lut_set`로 직접 씀).

## 1. `_tolerance`가 None을 내는 경로 (코드 경로 끝까지)

`_tolerance(c, values)` (block_columns.py) = `c.tolerance(c.coord 전부, values)`를 부르고 `SealViolationError`면 None.
`_Circuit.tolerance`는 소자마다 `tol_v_cell` → `tol_v_table(memo, kind, w_key).at(L, vds, "id_equivalent")`.

| 경로 | 발생 조건 | 행 측정(`region_rows`)과의 관계 |
|---|---|---|
| P1 `tol_v_undefined` (tols 비었음) | **모든** MOS의 `table_at` 블록(L 행 {lo, hi} × VDS 열 {k, k+1})의 id_equivalent 셀이 전부 None | 갈릴 수 있다 -- §2 |
| P2 `tol_v_cell`이 `SealViolationError`(사유 `lut_query`로 감쌈) | `table_at`의 `l_position` 실패(L이 앵커도 같은 bin 보간도 아님) 또는 VDS 축 밖 | **항상 함께 실패**: VDSAT 출처 표의 L 격자·VDS 격자는 슬라이스와 같고(`_build_caps`: `cap_grids[:3] != grids[:3]`이면 `lut_cap_axes_mismatch`), bin 지도도 같은 폭 슬라이스의 것(`same_w[0]`)이다. 같은 (L, vds)로 `vdsat()`·`tol_vdsat_table.at`이 먼저 실패해 `region_rows` → None → `_measure` None → A6 a. P2로는 A6 b에 못 간다 |
| P3 `tol_v_table` 구성 중 `SealViolationError` | `_checks_of` → `midpoint_l_bin_checks`(같은 인자) | `tol_vdsat_table`도 같은 호출을 먼저 하므로 함께 실패 → A6 a. (`midpoint_checks.py`에 raise 없음 -- 사실상 없음) |

KeyError·ValueError는 None이 되지 않고 전파된다(A6 b 아님).

## 2. 두 표의 정의 조건 -- 일반형

### 2.1 점 정의 조건 (코드 근거)
- id_equivalent(`tolerance.py::_id_equivalent`): 점 p, 축 a에서 p가 그 축 내부점이고 `on(p−e_a) & on(p) & on(p+e_a)`(슬라이스 `on_mask` = (ID>0)&(GM>0)), L 축은 같은 bin 내부 앵커만. 값 = |추정 − ln ID| / (gm/ID) / 2^p.
  세 점이 on이면 ln ID 유한(ID>0), gm/ID = exp(lnGM − lnID) 유한·양수, Hermite는 유한 입력의 다항식이라 **값은 항상 유한** → 점 조건만으로 정의.
- tol_VDsat(`vdsat_tolerance.py::_loo_cells`): 같은 점 조건을 **열 출처 표**(`column_source`)의 `on_mask`(기준 LUT에 ID·GM 열이 없으면 None → 모든 점 참)와 격자에서. 값 = |선형 추정 − VDSAT|, VDSAT가 비유한이면 NaN(정의 안 됨).
- 셀 = 그 (L 앵커, VDS) 안 점들의 최댓값(`cell_max`), 조회 = 블록 안 정의된 셀의 최댓값(`table_at`).
- 외부 중점 값(`with_external`)은 셀 값이 None이면 None 그대로다 -- **중점 파일 값은 None 셀을 살리지도 죽이지도 않는다.**

### 2.2 열 출처 = 슬라이스(운영 v2): A6 b 불가 (증명)
같은 슬라이스·같은 `on_mask`·같은 격자·같은 bin 내부 판정을 쓰므로 점마다 def(tol_VDsat) ⊆ def(id_equivalent)(VDSAT가 비유한인 점만 앞쪽에서 빠진다).
셀·블록 최댓값은 정의 집합의 합집합 위에서 취하므로 블록 단위로도 'tol_VDsat 정의 ⇒ tol_V 정의'. 그래서 A6 b 방향(tol_VDsat 정의·tol_V 미정)은 생기지 않는다.

### 2.3 열 출처 = 기준 LUT: 갈리는 길 셋 (수학적으로 존재)
L·VGS·VDS 격자와 bin 지도는 같으므로 차이는 다음뿐이다.
1. 기준 LUT `on_mask`가 슬라이스보다 넓음(기준 LUT에 ID·GM 열이 없으면 None = 전부 참; 또는 두 데이터의 on 영역이 다름).
2. **VS 축은 적재 검사 대상이 아니다**(`cap_grids[:3]`만 비교) -- 기준 LUT VS 격자에 내부점이 있고 슬라이스에는 없을 수 있다.
3. (반대 방향만) VDSAT 비유한 점.

### 2.4 커널 수준 추가 조건 (코드 근거)
- `device.dc_coord`의 MOS **전부**가 P1 조건(전부 미정)이어야 한다(`region_rows`·`_tolerance` 모두 전도 거르기 없음).
- 쓰기 계획에 **순환 SCC가 없어야** 한다(크기 1 자기참조 포함): `gauss_seidel`/`newton_solve`의 `tolerance`와 `solve_self`의 `self.tolerance((m,), ...)`가 그 소자들 tol 전부 None이면 `tol_v_undefined`로 풀이가 실패 → 후보 실패이지 A6 b가 아니다. 실험 A의 소스 팔로어·W4 둘 상호 창 구성에서 실제로 이렇게 실패했다(§4 표).
- 물리 일반형: 실제 MOS는 VDS>0인 모든 바이어스(약반전 포함)에서 ID>0·GM>0이라 on 영역 = VDS>0 전체다. 격자가 축마다 3점 이상이면 VDS=0 열 옆 블록까지 VGS 축 LOO 점이 있어 id_equivalent가 정의된다. 그래서 A6 b는 **격자가 축소된(축당 내부 LOO 점이 없는) 슬라이스 + VDSAT 출처가 기준 LUT**일 때만 생긴다. 쓰기 소자의 `vgs_for_current_density`가 곡선 전 VGS 마디 정의를 요구한다는 점(`lut_curve_undefined`)도 VGS 3점 이상이면 VGS 축 LOO 점을 보장한다고 보지만, `gm_id_curve` 내부(모서리 가중)는 끝까지 따라가지 않았다 -- **미확인**(결론에는 쓰지 않음).

## 3. 운영 LUT 실측 (sky130 v2, `count_a6b.py`)

`resolve_lut_location` 위치 그대로(manifest·cap r2·verify_midpoints r2), 32 슬라이스 전수. 블록 = `table_at` 규칙(단일 앵커 행 또는 같은 bin 인접 두 행 × VDS 칸 k의 열 k·k+1).

| 세트 | VDSAT 출처 | 셀 | tol_V None | tol_VDsat None | V None & VDsat 정의 | 반대 | 블록 | 블록 V None | 블록 V None & VDsat 정의 |
|---|---|---|---|---|---|---|---|---|---|
| 운영 v2(현행 슬라이스) | 32개 모두 slice | 28224 | 576 | 576 | **0** | 0 | 43008 | 0 | **0** |
| 참고: 결정 B 이전 v2 슬라이스(`_drafts/engine/lut_v2`, VDSAT 열 없음) | w_key 1000 두 개만 cap_table(나머지 30개 `lut_column_unavailable`) | 1764 | 36 | 36 | **0** | 0 | 2688 | 0 | **0** |

- None 셀은 전부 VDS=0 열(VDS index 0, 18 L × 슬라이스 수)이다 -- ID=0 열. 조회 블록은 늘 k+1 열을 포함하므로 블록 단위 None은 0.
- 기준 LUT(cap r2)는 ID·GM 열이 있어 `on_mask`가 슬라이스와 같은 수(423360/432180)이고 VS 격자도 10점으로 같다 -- 실데이터 cap_table 갈래에서도 갈리지 않는다.

## 4. 일반형 도달 실험 (`toy_a6b.py`, 저장소 밖 임시 LUT, HEAD 엔진)

LUT: tests/sizing conftest의 `r4_arrays`(r4 toy 식)로 슬라이스를 쓰고, 기준 LUT는 `write_r4_lut`과 같은 꼴(CGG·CGD, w_ref_m = W_M, ID·GM 열 없음 → `on_mask` None)에 `VDSAT_<접미사>`(r4 VDSAT 식)를 더함.
격자 = (L (1e-6, 2e-6), VGS (0.2, 1.2), VDS (0.0, 0.3, 1.8), VS (0.0, 1.8)). 이 값들은 test 입력(축소 격자 표현용)이지 엔진 상수가 아니다.

회로(이름 없는 일반 구성, 공통 게이트): M1 nmos (d = out, g = vb, s = in, b = gnd), RL 저항 (vdd, out), IS 전류원 (in, gnd); in = 입력 포트(입력 DC 미선언), out = 출력, vb = bias_inputs.
쓰기 계획: out = `resistor_drop`(vdd), in = 입력 W4 뿌리, vb = M1 `vgs_gate`(known in) -- **순환 SCC 0, 자기참조 0**. θ: L 1e-6, ln IDu(M1) = op_point(VGS 0.4, VDS 0.6, VSB 0.6), RL 6e4 Ω, 전류 1e-5 A, y_in = 1/2.

| 변형 | 슬라이스 VDSAT | 기준 LUT VDSAT | VDS=0 열 끔 | id_eq 셀 | tol_VDsat 셀(출처) | `node.dc_window["in"]` |
|---|---|---|---|---|---|---|
| **A (목표)** | 없음 | 있음 | 예 | 전부 None | k=1 열 0.0 정의 (cap_table) | **`input_status='unsettled'`, `tol_v=None`**, lo 0.0, hi 0.8825, V(in) 0.44125, V(out) 1.2 |
| B (대조) | 없음 | 있음 | 아니오 | k=1 열 1.07e-17 | k=1 열 0.0 (cap_table) | `unsettled`, tol_v 1.07e-17 (A6 c -- 아래 참고) |
| C (대조) | 없음 | 없음 | 예 | 전부 None | `lut_column_unavailable` | `unmeasured` (A6 a) |
| D (대조) | 있음 | 없음 | 예 | 전부 None | 전부 None (slice) | `unmeasured` (A6 a) -- §2.2 대로 출처가 슬라이스면 함께 None |

앞서 시도한 구성(같은 LUT A)에서 소스 팔로어(out 1노드 자기참조 SCC)와 in·out 두 W4 창이 서로 이웃인 구성(순환 SCC (in, out))은 `SealViolationError tol_v_undefined`로 풀이가 실패했다 -- §2.4 조건의 실증.

참고(범위 밖): B에서 tol_V가 1.07e-17(r4 식이 Hermite로 정확 재현돼 LOO 오차가 반올림 수준)이라 되풀이가 tol 안에 못 들어와 A6 c(`k_max` 소진)로 끝났다. 정확 재현 toy는 k_max 소진 toy를 쉽게 만든다는 뜻이므로 L12 (a) 계열 test 설계 때 참고.

## 5. design 41 694행 문언 대조 (사실 정정 후보)

- 도달 조건 본문(모든 MOS tol_VDsat 정의 + 모든 셀 tol_V 미정 + 순환 SCC·자기참조 없음, 열 출처가 기준 LUT일 때 하나)은 코드·실행과 맞다.
- **부정확 1**: '그 bin의 중점 파일 `id_equivalent_v`도 없음' -- `with_external`은 셀 값이 None이면 외부 값을 보지 않는다. 중점 값은 조건이 아니다.
- **부정확 2**: '반대 방향(tol_V 정의·tol_VDsat 미정)은 ... 중점 파일에 VDSAT 열이 없거나 격자가 달라 `vdsat_v`가 None일 때 생기고' -- 같은 이유로 외부 값 None은 정의된 셀을 None으로 만들지 않는다. 반대 방향의 실제 원인은 VDSAT 비유한 점 또는 출처 표 on_mask/VS 격자 차이다(§2.3).
- 빠진 사실: 기준 LUT의 VS 축은 적재 검사 대상이 아니라는 점(§2.3 2), 기준 LUT에 ID·GM 열이 없으면 점 조건이 '모든 점'이 된다는 점(§2.3 1) -- 픽스처 설계의 핵심이다.
- '실행 미확인' 표기는 이 실험으로 '실행 확인(저장소 밖 toy)'으로 바꿀 수 있다.

## 6. 계획 (12)(a) 'tol 미정 toy' 처리 권고

**권고: 계획 문언은 그대로 둔다(범위 축소 없음). 분기도 그대로 둔다. test 도구에 기준 LUT VDSAT 인자를 더해 toy를 만든다. design 41 694행은 §5의 사실 정정만 한다.**

- 근거: 분기는 죽은 코드가 아니다(§4 A에서 실제 도달). 운영 LUT에서 안 나오는 것은 현재 데이터의 성질이지 코드 경로의 성질이 아니다 -- 슬라이스 생성기가 VDSAT 열 없이 다시 돌거나 축소 격자 슬라이스가 들어오면 열린다(결정 B 이전 세트처럼 cap_table 출처는 실제로 있었다).
- 픽스처 설계(test 작성 주체 몫, 소스 열람 없이 interface card로 지정 가능):
  1. `write_r4_lut`에 인자 하나: 기준 LUT에 `VDSAT<접미사>`를 쓸 kind 목록(값 = 기존 `r4_arrays(..., vdsat=True)["VDSAT"]`). 슬라이스는 `vdsat=()`, `off_cols={kind: 1}`, `grids` = VGS 2점·VDS 3점(첫 점 0)·VS 2점, L은 bin 지도 없음(앵커만).
  2. 회로: 입력 포트가 W4 뿌리이고 쓰기 계획에 순환 SCC·자기참조가 없는 구성(위 공통 게이트 꼴). 전제 단언으로 `dc_scc_order`의 cyclic 전부 False, `dc_self_referential` 전부 False, 슬라이스 tol_V 셀 전부 None·기준 LUT tol_VDsat 셀 정의를 먼저 확인.
  3. 기대: 뿌리 `input_status == "unsettled"`, `tol_v is None`, 창 = 한 번 잰 창(되풀이 없음) -- 그다음 (12)(a)의 metric·ICMR 제약 정의 불능 단언(IT-2d 몫).
- 대안 비교: '계획 정정(사실 정정)으로 tol 미정 toy 삭제'는 도달 가능한 분기를 test 없이 남기는 것이라 범위 축소다(사용자 결정 필요) -- 권하지 않음. '분기 삭제'는 tol None이 `k_max(…, None)`으로 흘러 실패하거나 조용히 바뀌므로 fail-closed 위반 -- 기각.

### 원칙 점검
| 원칙 | 점검 |
|---|---|
| 만들면 배선 | 새 픽스처 인자는 (12)(a) test가 바로 소비. 엔진 새 코드 없음 |
| graph 단일 정본 | 새 필드·cache·사본 없음(엔진 변경 0) |
| 상수 발명 금지 | 격자·θ 값은 test 입력 리터럴, 엔진 상수 아님. 판정은 LUT 데이터의 점 조건에서 유도 |
| 일반화(회로 이름 금지) | 조건은 '열 출처·점 조건·SCC 구조'로만 기술, 회로 이름 없음 |
| 물리 먼저·일반형 | 물리 LUT(축당 3점 이상, VDS>0 전도)에선 불가, 퇴화 격자 + 기준 LUT 출처에서만 가능 -- 둘 다 근거와 함께 기술 |
| 원래 취지와 다름 | 해당 없음(계획 문언 유지). design 문언 정정 2건은 사실 정정 |
| 근거 없는 단정 금지 | `gm_id_curve` 모서리 규칙은 '미확인'으로 남김 |

## 재현
- `wt/_scratch_a6b/count_a6b.py <skill> <out> [manifest]` → `count.out`(운영), `count_nocol.out`(결정 B 이전 세트).
- `wt/_scratch_a6b/toy_a6b.py <skill> <out> <work>` → `toy.out`.
- 실행: `APPDATA` export, `GMID_LUT_TABLE_CACHE_DIR=wt/_scratch_a6b/tc`(실제 캐시 미사용), `python -I`, 순차.
