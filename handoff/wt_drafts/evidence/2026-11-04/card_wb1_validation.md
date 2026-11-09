# card WB-1 독립 판정 (2026-11-04)

대상: `docs/cards1104e` `master..389a9948`(master `dda16724`). 계획 v6.38.14, design v1.16.12, card `20261104-wb1.*`, `wt/_drafts/evidence/2026-11-04/m_th1c/`. 위임 A-65·A-66.

방법: 문서 읽기와 `git show`·`git grep`, 그리고 소스 텍스트 grep·float 산술 스크립트만 썼다. pytest·LUT·엔진·ngspice 실행은 없다. 엔진 인용은 재작성 범위, 호출 자리, 구조 규칙 대입, 엔진 밖 사실에만 쓴다(원칙 8). 줄 번호는 지정이 없으면 `389a9948`, 소스는 `dda16724`다. 표기: P = 계획, D40·D41 = design, IF = interface, SP = spec.

## 결론

**이 판으로 test 동결에 들어가면 안 된다. Major 5.** 대부분의 손 값(§1·§2 표, D-1, R-3~R-12, T-O, T-W)은 재유도해 맞았고 구조 규칙도 거의 통과한다. 막는 것은 다음 다섯이다.

| Major | 내용 | 볼 항목 |
|---|---|---|
| W1 | D-2 회로는 쓰기 소자로 닫혀 Rʳ = ∅이고, stub는 소자를 구별할 수 없다 | 1 |
| W2 | `CON_INVERSION` 행만 지우면 O-207이 이뤄지지 않고 M-3 toy를 만들 수 없다 | 3 |
| W3 | M-TH1c 표가 `curve_value` 경유 소비자와 정점 하한을 놓쳤고 새 소비자 판정이 그쪽을 못 본다 | 3 |
| W4 | R-2 회로와 `realize_front` `points` 꼴이 interface에 없다 | 1 |
| W5 | J-6 표 구성 뒤 `_wire_sweep_memo`가 memo를 바꿔 '평가 안 표 구성 0'이 성립하지 않는다 | 5 |

줄바꿈은 정상이다: `git show --numstat 47e0d9f8` = 계획 9/9, history 11/0.

## Major

### W1. D-2 회로

**IF:163**은 `tests/sizing/test_block_columns.py`의 `_cycle_ctx`를 쓴다. 그 fixture가 스스로 단언한다: `w["x"]` = (`vgs_gate`, MA), `w["y"]` = (`vgs_source`, MB)(`:557~558`). `_solve`의 `writers`가 비어 있지 않으므로 수렴 tol 소자 = MA, MB이고 둘 다 θ 쓰기 소자다. D40:1195 정의로 Rʳ = ∅이다. 그래서 '항상 키 200 → `slice_rounds` = 2'와 `slice_cycle` 행은 이 회로에서 나오지 않는다. '멈추고 보고' 문장이 있어도 멈출 것이 이미 정해져 있다.

**stub 문제**: `finger_slice(lut, kind, L, w_of)`에 소자 인자가 없다. '소자별 호출 수'를 셀 수 없고, 쓰기 소자의 호출도 수에 섞인다.

**손 값**: 시작 키 100. 호출 1 = 200 → 달라짐. 호출 2 = 100 → 그 전 벡터 재방문 → `slice_cycle`. 호출 3은 불리지 않는다. 표의 '3 = 200'은 쓰이지 않는다. '항상 200'은 호출 2에서 수렴, `slice_rounds` = 2(맞음).

**고칠 문언**(IF:163~171 대체)

> **손 회로 D-2**(Rʳ ≠ ∅): 기존 writer 없는 SCC `_scc_s_doc`(`test_block_columns.py:861`, {vin, vout})에서 M1 gate `nb1`을 bias 대신 diode M0 nmos (nb1, nb1, gnd) + 이상 전류원 vdd → nb1로 쓴다. 그러면 M1은 θ ln IDu가 없는 종속 소자이고 SCC 수렴 tol 소자에 들어 Rʳ = {M1}이다. 전제를 먼저 단언한다: cyclic SCC 하나, `dc_writer`의 그 넷 relation이 VGS 쓰기 아님, M1 `dc_coord.role` ≠ writer. 전제가 깨지면 회로·기대값을 고치지 말고 멈추고 보고한다.
> stub은 `sys.modules["gmid_engine.sizing.block_dc"].finger_slice`를 **M1의 θ L을 다른 소자와 다르게 둔 (kind, L)** 로 구별하고, 그 밖 호출은 원 함수로 넘긴다. M0와 L 동치이면 M0 호출은 노드 풀이 전 1회이므로 그 첫 호출을 건너뛴다.

| M1 stub 답 | 기대 |
|---|---|
| 항상 200 | 수렴, `slice_rounds` = 2 |
| 200, 100 | 벡터 100 → 200 → 100, `slice_cycle`, 호출 2회 |
| 항상 100 | `slice_rounds` = 1 |

이 회로는 코드로 재지 않았다(**미측정**). 계획 toy '순환 SCC 허용오차 꼴'에 맞는 회로가 저장소에 없고, library는 9/9 Rʳ = ∅이다. 전제 단언이 깨지면 그 사실 자체가 결정 입력이다.

### W2. `CON_INVERSION` 삭제

**O-207 대조**: P:676 '(10) 행을 지운다 -- 깊은 약반전의 대가는 면적·C 열이 맡고 바닥은 LUT 정의역'. P:675 '반전 수준 하한 행은 S_d·탐색 개방 범위에 두지 않는다'. 행 삭제 문언은 맞지만 O-207은 **행 하나로 이뤄지지 않는다.**

**사실**(재작성 범위):
1. `lut/vgs_current_density.py`: 역산 대상이 '강반전 분지(정점 index p 이상)'다. 목표가 그 아래면 `lut_target_out_of_range`.
2. `search/cell_floor.py` `_peak_floor`: 칸별 gm/ID 정점 ln IDu 하한(1변수 writer).
3. `search/search_domain.py:10-12`: ln IDu 상자 하한 = 정점 ln IDu 최솟값.

**손 유도**: 행 값 c = (r − r_peak)·(gm/ID)/tol, r_peak = 같은 (L, VDS, VSB) 곡선 정점의 ln IDu. 쓰기 소자의 VGS는 같은 곡선에서 `y[p] ≤ goal`일 때만 나오고 goal = r + ln w_m − ln L = y에 대응하므로 r ≥ r_peak다. **봉인을 지난 탐색 점에서 c ≥ 0이 항상 성립한다.** 행은 실현 집합을 자르지 않고, 경계 앞 기울기만 준다.

**귀결**:
- 행만 지워도 깊은 약반전 점은 여전히 도달 불가다. O-207의 취지가 이뤄지지 않는다.
- 잃는 것은 기울기뿐이다. SLSQP가 경계를 넘으면 `lut_target_out_of_range` 봉인 실패로만 드러난다. D40이 W_min 행을 남긴 이유(비교표 '기울기 없이 되돌아옴')와 같은 기제의 동작 변경이다.
- **IF:298 M-3 '깊은 약반전 점이 그 행 때문에 층 0 필수 위반이 되지 않음'은 toy를 만들 수 없다.** 그런 점은 평가가 먼저 실패한다.
- 범위: 슬라이스 변경과 같은 커밋 4에 들어가 변화표 원인이 섞인다(SP 묶음 판단 '변화표 원인을 가른다'와 어긋남).

**LI-1 전에 LA-1 측정**: 끝나지 않아도 된다. T4-pre = MOD8 전 기하(P:1496)이고 LA-1 선행(P:1321)에 LI-1이 없다. `layout/slice_density`의 역산은 `find_front` 밖이다. 단 실행 경로를 코드로 재지 않아 미측정으로 표지한다.

**위임 결정 후보(권고)**: O-207 묶음(행, `_peak_floor`, `search_domain` 정점 하한, 역산 분지 p)을 **LA-1로 함께 옮기고**, WB-1은 그 행의 키만 소자 키로 바꾼다.

| 안 | 동작 | O-207 | 범위 |
|---|---|---|---|
| **(b) 권고**: WB-1은 키만, 묶음은 LA-1 | 변화 없음(c 정의 같음) | LA-1에서 전부 | S_d 재작성과 같은 card. WB-1 동작 변경 0 |
| (a) WB-1에서 묶음 전부 | 약반전 개방 | 전부 | ⚠ 역산·상자·층 0 동작 변경을 끌어옴, 변화표 섞임 |
| (c) 지금 판: 행만 | 기울기 소실, 집합 불변 | 안 됨 | ⚠ M-3 불가 |

(b)의 손 값: `gm_id_curve(memo, op.kind, op.w_key, op.L, op.vds, op.vsb)`, `w_m = slice_map[(op.kind, op.w_key)].w_m`. 쓰기 소자 역산과 같은 슬라이스 곡선이라 c ≥ 0 유지. 작성자가 염려한 '철회된 행을 슬라이스 위에 새로 짓는다'는 맞지만, 정의를 바꾸지 않는 키 치환이고 LA-1까지의 임시 상태로 표지한다. **원래 취지와 다름**: O-207 구현 시점이 LA-1로(A-66 배정 번복). 실현 평가 점은 KCL 재풀이라 c < 0이 나올 수 있으나 그 행은 층 0·탐색용이고 실현 판정이 읽지 않는다.

**고칠 문언**
- P:2479 (b): '반전 수준 하한 행 `CON_INVERSION`은 이 card에서 키만 `DeviceOp.w_key`로 바꾼다(정의 불변). 삭제는 O-207 묶음으로 LA-1(N6.14 M-TH1c)'.
- P:2038 끝: '**O-207 묶음**(N3.6 정본 (9)(10)): `CON_INVERSION` 행, `search/cell_floor.py` `_peak_floor`, `search/search_domain.py` 정점 하한, `lut/vgs_current_density.py` 분지 p를 같은 변경에서'.
- P:2482 '`gm_id_inverse`·`CON_INVERSION` `git grep` 0' → '`gm_id_inverse` `git grep` 0'. P:2094에 '`CON_INVERSION` 0'.
- D40 v1.16.12의 철회 행 키 전환 정정을 되돌린다. SP 계약 19, SP 재작성 표 M-TH1c 행, table #24의 소유 = LA-1.
- IF:298 M-3 삭제. IF:299 M-4에서 `CON_INVERSION`, `inversion_floor` 제외. IF에 'T: 쓰기 소자 `inversion_floor` 행이 소자 슬라이스 곡선을 읽음(슬라이스 ≠ 기준 폭인 합성 회로, 손 값 c)'를 더한다.

### W3. M-TH1c 표 누락

**놓친 소비자 유형**: `m_th1c_ast.py`의 `FUNCS`에 `curve_value`, `curve_bundle`, `_at_gm_id`가 없다. 이 경로가 gm/ID 축 곡선 읽기의 본체다(`_helpers_curves.py:148-154`).

| 파일(소스 grep) | 무엇 | 표 |
|---|---|---|
| `search/_helpers_area.py:36` | `curve_value(bundle, QUANTITY_IDU, gm_id[...])` | **없음** |
| `search/iv_currents.py:104·107` | 같음 | **없음** |
| `search/iv_noise.py:58·61` | 같음 | **없음** |
| `search/macro_poles.py:91` | `curve_value(bundle, QUANTITY_GAIN...)` | **없음** |
| `search/iv_gain_l.py` | `gm_id_lo` 입력(`row_gains`) | **없음**(표시 재확인 필요) |
| `search/cell_floor.py` `_peak_floor` | gm/ID 정점 | **없음** |
| `search/search_domain.py:10-12` | 정점 ln IDu | **없음** |
| `lut/vgs_current_density.py` | `peak_index(g)` 분지 | '대상 아님'으로 분류, **틀림**: 역산 정의역을 gm/ID 정점이 정한다 |

**표본 대조 통과**: `layout/slice_density.py`, `finger_candidates.py`, `search/constraints.py`, `lut/tolerance.py`는 표 그대로다. `measure_L_knee` 엔진 0도 표 그대로(AST 요약에 없음). 순방향 12개 중 `sizing/seal_*`, `metrics/ss_linearize`, `metrics/metrics_aux`의 `gm_id`는 `dc_op` 순방향 칸으로 맞다.

**왜 Major**: P:1259·P:1383은 '소유 없는 소비자가 남으면 정지'다. `m_th1c_diff.py` 키에 `curve_value`가 없어 IF A-6 '새 소비자 키 0'이 WB-1이 포락으로 고치는 바로 그 자리들(`iv_noise`, `iv_matching_l`, `_helpers_curves`)을 보지 못한다. 또 P:2038 LA-1 목록에 넷이 없어 그 card가 곡선 파일을 지울 때 소유 없이 깨진다.

**배정 판단**: 나머지는 Q-TH1 O-186·DEC-11과 맞다. LI-1(layout), LA-1(출발 축), WB-1(지표 칸, 주석) 분류는 옳다. M-TH1c는 정적이라 계획 게이트 (나)에 맞는다.

**고칠 문언**
- `m_th1c_ast.py` `FUNCS`에 `"curve_value", "curve_bundle", "curve_bundle_of", "_at_gm_id", "peak_index"`를 더해 표를 다시 낸다.
- table.md에 위 표 행을 더한다. 소유 = LA-1(W2 묶음 포함). `lut/vgs_current_density.py`는 '정의역 분지 = LA-1 O-207 묶음'으로 옮긴다.
- P:2038 목록에 `search/_helpers_area.py`, `iv_currents.py`, `iv_noise.py`, `macro_poles.py`, `iv_gain_l.py`.
- IF A-6 뒤: '`curve_value` 호출 파일 집합도 base와 같음'.

### W4. R-2 회로와 `points`

IF §6은 '단단 차동쌍 + 전류 거울 손 회로'로만 적었고 `realize_front(sctx, points)`의 원소 꼴이 없다. test 주체가 interface만으로 쓸 수 없고 `tamper` 대상도 정해지지 않는다. 소스상 `sweep_front` front 원소는 `FrontPoint`(`point_id`, `result`), 스냅샷은 `point.result.evaluation.snapshot`이다.

**식 검증**: Δ = [−g + √(g² + 2C·ln(1 + r))]/C는 맞다(I_u(V0 − Δ) = I_u(V0)/(1 + r)에서 CΔ²/2 + gΔ − ln(1 + r) = 0). r4 식에 LAM·VDS가 있어 꼬리 넷이 움직인다. 유도: M1·M2 VDS가 같이 δ 움직이고 양쪽 전류가 불변이면 1차로 LAM 항이 소거된다. 2차 잔차 ≈ C·Δ·b, b = LAM·(Δ/2)/g. V0 = 0.6: g = 15.2, r = 0.5 → Δ = 26.5 mV, b = 8.7e-5, 잔차 1.2e-6 V. bulk = source여야 VS 항이 빠진다.

**tol 표지**: VS 격자 간격 0.25 V, A = 2라 VS LOO 값이 ln 단위 약 0.125, tol_V ≈ 8 mV(추정)다. Δ = 26.5 mV라 공허하지는 않지만 ln(1 + r)/g = 26.7 mV와는 구별하지 못한다(IF의 '쓰지 않는다'는 기대값 문장으로 충분).

**고칠 문언**(IF §6 R-2 앞)

> `points` = `FrontPoint` tuple(`point_id`, `result`). `RealizeOutcome.points`도 같은 꼴이고 `result`만 실현 평가 값이다. `search_ref` = `point.result.evaluation.snapshot`. tamper = 이 스냅샷의 `device.dc_finger`.
> **R-2 회로**(새 topology, 회로 이름 없음): M1 nmos (x, inp, t, bulk = t), M2 nmos (out, inn, t, bulk = t), M3 pmos (x, x, vdd), M4 pmos (out, x, vdd), 이상 전류원 t → gnd. 포트: `inp`·`inn` 차동 입력 쌍, `out` 단일 출력. 슬라이스 {1, 2} µm. θ는 VGS0 = 0.6 V, 전류 = Oracle 식으로 W_M1 = W_M2 = 2e-6. 단언 = |V_id(실현) − V_id(탐색)| 와 Δ의 차 ≤ 봉인 tol_V, 그리고 |V_id 이동| ≥ Δ/2(공허 방지). 입력쌍 선언·`graph.icm_config` 칸 이름은 IT-2c base에서 재확인, 불러들이기에서 멈추면 보고.

R-6의 `as_is_single_input`은 design·계획 문언에 있으나 base 코드 이름은 IT-2c 병합 뒤 재확인이다(미측정).

### W5. 표 구성과 memo 교체

**J-6**: `build_slice_tables(memo)`를 `build_kernel_context`에서 부른다. **사실**: `search/search_context.py:139` `_wire_sweep_memo`가 그 뒤 `ctx.dc.lut`를 새 `LutMemo.counting`으로 바꾼다. 새 memo는 표가 비어 있다.

**손 추적**: 탐색 경로 첫 평가의 `tol_v_table(memo, ...)`은 memo 미스 → 표 캐시 적중이면 읽기, 없으면 평가 안에서 구성한다. IF:286 '평가 안 표 구성 0'이 탐색 경로에서 거짓이고, D40:1232와 비교표가 기각한 '평가 안 구성'이 된다. §9 표에 그 관찰 지점도 없다.

**고칠 문언**
- SP J-6·IF:286: '호출 = memo를 확정하는 자리마다: `build_kernel_context`와 `_wire_sweep_memo` 교체 직후. 계수 창은 첫 커널 평가부터라 세지 않는다(D40 U_eval 행). 표 캐시를 공유하므로 둘째 호출은 파일 읽기다.'
- IF §9에 `gmid_engine.lut.tolerance`의 표 계산 함수 또는 `derived` 호출 계수를 어떻게 잴지 한 줄. 잴 수 없으면 '평가 안 표 구성 0' 단언을 빼고 `build_slice_tables` 반환 수와 두 호출 자리 소스 grep으로 바꾼다.

손 값: 슬라이스 {100, 200}, kind 둘, 표 둘 → 8(`TOY_SPEC` W_min 1e-6 = 키 100이라 둘 다 `widths`에 듦). 맞다.

## 항목별 판정

### 1. 손 값·회로·관찰 지점

| 대상 | 판정 |
|---|---|
| `bin_index` 표 | 맞음. 1e-6·(1 − 32 eps)는 1 ulp 밖이라 base red |
| `reachable_slices` 표 | 맞음 |
| `finger_slice` 표, 2⁻²⁶ m 표 | 맞음. `w_f_m` = key·g는 키 100·200·400·500·700에서 리터럴과 비트 같음(float 계산) |
| `slice_of_finger` | 맞음. 5.000000001e-6: 몫 500.0000001, 2 ulp 밖 |
| D-1 | 맞음. W_M2 ∈ (3.5, 4.5) µm: 키 100 m = 4, 키 200 m = 2, 곱 400 비트 동률 → 200. W_M1 ∈ [1, 1.5) → 키 100. r4 L (1e-6, 2e-6), 격자 1e-8, §4 bin 끝 격자 위. `circuit_mirror` 포트 있음, 구조적 0 전류 없음 |
| R-3·R-10·R-12 | 맞음 |
| T-O, T-W1~3 | 맞음 |
| 재수출·monkeypatch | 맞음. `find_front`·`realize_front`·`ss_off_op`은 `sys.modules`, `block_dc`는 같은 이름 함수 없음. `search.constraints`는 모듈 |

### 2. None·규칙·칸

- None·축 밖: `w_of`, `reachable_slices`, `slice_of_finger`, IDu ≤ 0, tol None 모두 산술 전 처리. `SccLog`는 비순환 entry도 항목이 있어(`block_columns.py:572`) J-8 첫 항목 읽기가 안전하다. 새 칸 0.
- 규칙 A·H: `is_slice_gap`, `build_slice_tables`, `slice_of_finger`, `file_sha256`, `finger_slice`(`reachable_slices`를 Name으로 읽음) 뿌리 하나, test 자리 일치. S-1 `test_block_dc.py`는 최종 형태 통과. **단** n2·n3.
- L-4: SP 표 맞음. L-5: 사본 없음.

### 4. S-3

**z 표지는 맞지만 범위가 좁다. x도 같다.**
- 범위 밖 손 값(z): 블록에 캐스코드(z 클수록 큼)와 팔로워(z 클수록 작음)가 함께 있으면 진짜 상계는 소자마다 다른 z에서 나오고 두 표는 전부 min 또는 전부 max뿐이라 그보다 작을 수 있다.
- **x 손 값**: diode 부하 A = gm1/gm2 = x1/x2. 슬라이스 x ∈ {10, 20}이면 x 최대 표는 A = 1, 실제 최대는 2. D40:1237 'x = 최대, y = 최소면 상계 유지'는 x가 분모인 행에서 거짓이다. `row_gains`는 일반 국소 MNA라 이런 행을 낸다.
- **fail-open인가: 아니다.** 나쁜 점이 통과하지 않는다. 최종 판정은 봉인·oracle이다. 방향은 반대다: bound가 낮으면 `sum_db + b_db < target` → `VERDICT_INFEASIBLE` → `stage_b` exit 3(거짓 '달성 불가'), 그리고 `iv_context:53-55` 예산 배분이 달라진다. D41:527 '실현 가능한 점을 자르지 않음'이 보장되지 않는다.
- 기준 폭 하나였던 base도 슬라이스 위 상계가 아니었으므로 **퇴행은 아니다.** 그래서 막지 않고 문언만 고친다(n1).

### 5. J-1~J-9

J-1·J-3·J-5·J-8·J-9 맞음. J-2: W5와 무관, 호출부 수는 n4. J-4: n5. J-6: W5. J-7: P:305·D40 w_hi 정의와 맞음, 단 n6.

### 6. 넘긴 항목·절차

g1~g4, T-O, 소비자 재조사, 착수 조건 표 들어감. base 조건(HC-S 뒤), OP-7 선언 파일 미충족 표지, A-34(`E/graph`에 `dc_drop_current`·`w_keys`·`dc_columns` grep 0), GL-1 래칫, 원칙 8, 원칙 24 표지 맞음. mismatch p0 표는 미측정으로 착수 조건에 남아 있고 맞다.

## minor(막지 않음)

- **n1** D40:1237·SP S-3 문언: 'x 최대·y 최소·z 두 끝은 gain이 x 증가·y 감소이고 소자들의 z 방향이 같은 행에서만 상계다(diode 부하, 캐스코드와 팔로워 혼합은 아님). 그 밖은 상계 추정이고 `VERDICT_INFEASIBLE`이 거짓일 수 있다. 측정 = LA-1 재점검'. IF A-9에 'GB4 verdict 기록'.
- **n2** SP `_helpers_lut` 처리: `terminal_voltages`도 사용 파일이 `block_columns`·`block_widths`뿐이라(`helper_single_user`) `forward_point`와 함께 `block_dc.py`로. `with_device`는 EO-1 뒤 재조사.
- **n3** `test_block_dc.py`는 모듈 머리에서 `block_dc`를 import하지 않는다(커밋 3에서 T-W가 돌아야 함). conftest `run_blocks`도 같다.
- **n4** SP '호출부 16곳'인데 목록은 13곳(소스 grep도 정의 제외 13). '표 클래스 넷' = `TolVTable`, `TolVdsatTable`, `TolNoiseTable`, `TolMismatchTable`을 이름으로 적는다.
- **n5** J-4 작성자 목록에 없는 합성 LUT 자리: `tests/lut/test__helpers_width.py`, `test_midpoint_checks.py`, `test_slope_unit_check.py`, `test_vdsat_query.py`, `tests/search/test_kernel.py`, `test_search_domain.py`, `u13_hand.py`. 적재 57곳은 맞음(grep). 53파일은 내 grep 55(패턴 차이, 착수 재측정).
- **n6** J-7 'OP-7이 먼저 멈춘다': `w_boundary_not_product`는 L 구간이 겹칠 때만 잡는다. L 구간이 서로소이고 W 행이 다른 표는 통과한다. 실제 PDK bin 표 미측정(scratch 파일 비어 있음). 착수 때 OP-7 `points`로 확인.
- **n7** M-4 grep 대상 docstring: `layout/w_tolerance.py:6`(`gm_id_inverse`), `metrics/curve_checks.py`(`vgs_for_gm_id`). SP 목록에 더한다. W2 (b)를 택하면 `search_domain.py`·`canonical_rows.py` 쪽은 LA-1.
- **n8** T-W4 기대값: 뿌리에 채널 소자가 없으면 창 = 레일 범위, `constraints` = 0이라고 적는다(`fd_jacobian` 창 폭이 유한해야 함).
- **n9** 커밋 분리: W2 (a)·(c)를 택할 경우 M-TH1c 행 삭제는 커밋 4와 나눈다.

## 미측정

pytest 전부, 구조 test 실제 결과, base 코드(IT·EO-1·card C·TB-1·HC-S) 뒤 이름과 줄, D-1·D-2·R-2 회로의 실제 통과, W2 (b) 키 치환 뒤 동작, LI-1 전 LA-1 실행 경로, tol_V 실제 값(R-2, 추정 8 mV), OP-7 선언 파일, PDK bin 표 격자꼴, mismatch p0 표, S-3 크기, `iv_gain_l` 소비 세부. 이 판정은 문서·손 값 판정이다.

1차 판정(head `389a9948`): Major 5

## 재판정 (`389a9948..6c03871c`)

범위: 이 diff, 그것이 닿는 문장, `m_th1c/table.md`. 방법은 앞과 같다(실행 없음). 줄 번호는 `6c03871c`, 소스는 `dda16724`.

### 결론

W1~W5와 n1~n8은 들어갔고, 작성자가 넓힌 곳도 맞다. **Major 1: 41:527과 40 §3.7-A 8의 차이는 지금 고쳐야 한다.** 격자 곱과 `found_db` 규칙이 갈려 card가 한쪽을 조용히 고르게 된다. 고치면 test 동결로 갈 수 있다.

### 1. 반영

| 항목 | 판정 | 원문 |
|---|---|---|
| W1 | 들어감. 손 값 재확인(항상 200 → 호출 2에서 수렴, `slice_rounds` 2; 200, 100 → `slice_cycle`, 호출 2; 항상 100 → 1) | IF:163~175 |
| W2 | 들어감 | P:676, P:1259, P:2038, P:2094, P:2479, P:2482, D40:1248·1253, D41:669, D42:345, IF M-5·M-6, SP 19 |
| W3 | 들어감, 넓힘 | table.md, P:2038, IF A-6 |
| W4 | 들어감. 잔여 q2 | IF:229~233·238 |
| W5 | 대체안으로 들어감 | IF:294, SP J-6 |
| n1~n8 | 들어감 | D40:1237, SP S-3, IF A-9; SP `_helpers_lut`; IF:368; SP:103·239; SP:121; SP J-7; IF M-4; IF T-W4 |
| n9 미반영 | **맞다.** n9는 W2 (a)·(c)일 때의 조건이었고 (b)를 택해 행 삭제가 커밋 4에 없다 | |

### 2. W2·W3 문언 재검증

**O-207 묶음을 LA-1로**: 맞다. P:668이 출발 정의역 S_d를 card LA-1 적용 자리로 적고, P:675·P:676이 같은 S_d·탐색 개방 범위를 말한다. O-207 결정을 바꾸지 않고 구현 시점만 옮겼다(SP '원래 취지와 다름' 9 표지 있음). `tolerance`의 `id_equivalent`는 `on_mask` 전부에서 재므로 정점 아래 점도 tol이 정의된다(`tolerance.py:22`). LA-1 깊은 약반전 toy가 tol 때문에 막히지 않는다.

**WB-1이 키만 바꾸면 동작 변경 0인가**: 구별해서 **조건부로 맞다.**
- 탐색 평가: 맞다. 행 정의가 같고, 쓰기 소자 역산과 같은 슬라이스 곡선이라 c ≥ 0 집합도 그대로다. 값은 슬라이스를 따라 바뀌지만 이 card 전체의 슬라이스 변경에 속하고 새 규칙이 없다.
- **실현 평가: 내 W2 문언과 SP '원래 취지와 다름' 9가 넓게 말했다.** '실현 판정이 읽지 않는다'는 `realize_front`만 맞다. `convergence/converge.py:47`, `converge_point.py:55`는 `all(row.c >= 0)`를 읽는다. 손 값: 정점 근처 점에서 W′ = 1.37·W면 ln IDu가 ln 1.37 = 0.31 내려가 c < 0이 될 수 있고, 그 front 점은 수렴 단계에서 거부된다. fail-closed이고 LA-1이 행을 지우면 사라지므로 막지 않는다. 문언은 q1.

**W3**: `curve_value` 경로 추가, `vgs_current_density` 재분류 맞다.

### 3. 작성자가 달리 쓰거나 넓힌 곳

| 자리 | 판정 | 근거 |
|---|---|---|
| `gm_id_for_target` | 맞다. 내가 놓침 | 비lut 호출 0, DEC-11 밖 역산 |
| `_conduction_ok`, `curve_check`, `ln_idu_floors` 호출 | 맞다. 내가 놓침 | 정점 규칙의 소비. `layer0_center`, `slsqp_outer` 호출 있음. `ln_idu_floors`의 `_conduction_floor`도 옛 봉인 9 ε이라 P:675와 맞아 함께 삭제가 옳다 |
| M-5 | **맞다, 내 문언보다 낫다** | 비례 슬라이스면 두 키가 같아 공허하다. 손 값: 키 200의 ID를 폭 비 2의 두 배(4배)로 → IDu₂₀₀ = 2·IDu₁₀₀, GM도 4배라 gm/ID 그대로. r4 gm/ID = B − C·VGS라 정점 = VGS 0. r_peak = ln(id_vals[0]) + ln L − ln w_m = ln(2·I0) + LAM·VDS(VS = 0). W ≈ 2e-6: 키 100 m = 2, 키 200 m = 1, 곱 200 동률 → 200. 기준 키면 ln 2 차 |
| `strong_inversion_root` → `lut/vgs_root.py` | **맞다, 규칙 A상 필요.** WB-1 뒤 사용 파일이 `vgs_root` 하나라 `helper_single_user`다. 옮기면 `vgs_root` 뿌리는 그대로 하나. 순서: N6.1 15 card에 LI-1이 없어 WB-1이 먼저다. LI-1이 먼저면 할 일이 '삭제'로 바뀐다(q3) | |
| `branch_targets` 삭제 | 맞다 | 사용 = `tolerance`, `midpoint_checks`뿐(소스 grep). 계획 쪽 표기는 q4 |
| LA-1 깊은 약반전 toy(P:2094) | 맞다. 표지: r4 LUT는 정점이 VGS 0이라 '정점 아래' 점이 없다. 그 toy는 정점이 안쪽인 합성 곡선을 써야 한다(LA-1 card 몫) | |
| W5 대체안 | 맞다 | 평가 안 구성 수를 잴 자리가 없으면 단언을 빼는 것이 공허한 단언보다 낫다. 호출 자리 둘을 소스로 잠근다. 잃는 것은 소스 grep 밖 지연 구성 검출뿐이고 표 캐시 키는 불변 |
| D41:527 표지 | **부족** | 아래 R1 |

### 4. R1(Major): 41:527 대 40 §3.7-A 8

**차이**(D41:527, D40:1237):

| 항목 | 41:527 | 40 §3.7-A 8 |
|---|---|---|
| A_i,max | 슬라이스별 gain의 최댓값 | 열별 포락 표 둘(x 최대, y 최소, z 두 끝) bound의 큰 쪽 |
| 격자 곱 Π | 슬라이스 수를 곱함, N_S 판정도 그 Π로 | 슬라이스 축 없음 |
| `found_db` | 격자 점마다 포락 최솟값 | 없음 |

**왜 지금인가**: IF·SP에 `found_db`·`N_S` 언급이 0건이다. `block_gain_bound`는 같은 `tables`로 `found_db`를 내므로 IF:202대로 구현하면 `found_db`가 상한 쪽 표에서 나온다. 이것은 P:305 '하한 양은 최솟값'과 어긋나고 `g_i^(1)` 분배 입력이 조용히 바뀐다. Π도 어느 쪽인지에 따라 `grid_product_over_budget`이 달라진다.

**정본 권고: 40 §3.7-A 8 열별 포락**(A-66 S-3 유지).

| 안 | 상계 쪽 | Π | 비고 |
|---|---|---|---|
| **열별(권고)** | 슬라이스 (x, y) = (10, 1), (12, 2): 12/1 = 12 ≥ 슬라이스별 최대 10 | 그대로 | 표만 바꿈. 손계산 속도 맞음 |
| 슬라이스별 | 10 | 슬라이스 수 배 | ⚠ 미상 증가 → verdict 미정. 소자마다 다른 슬라이스 조합은 어차피 못 봄 |

x가 분모인 행은 두 안 모두 상계가 아니다(같은 슬라이스·같은 표에서 x₁/x₂ = 1). 열별이 더 나쁘지 않다. **원래 취지와 다름**: 41 v1.15.1의 슬라이스별 행 평가 문언. 계획 P:305 문구(상한 = 최댓값, 하한 = 최솟값)와는 맞다.

**고칠 문언**
- D40:1237 '큰 쪽을 상한으로 쓴다(...)' 뒤: '**하한 양 `found_db`** = x 최솟값·y 최댓값 표를 z 두 끝에서 각각 내어 작은 쪽이다. 슬라이스 축은 격자 곱 Π에 넣지 않는다(표 값만 바뀐다). 이 절이 정본이다.'
- D41:527 대체: '행마다 소자 파라미터를 40 §3.7-A 8 열별 포락 표에서 읽는다. A_i,max = 상한 표 둘의 bound 큰 쪽(상계 조건은 그 절), found_db = 하한 표 둘의 값 작은 쪽. 격자 곱 Π는 슬라이스 수를 곱하지 않으며 N_S 판정은 그대로다. 변화는 card WB-1 변화표 원인 항목. **원래 취지와 다름**: 옛 슬라이스별 행 평가(위임, 재점검 LA-1).'
- IF:202: '`ParamTables(memo, grids, side, z_side)`, `side` ∈ {`"upper"`, `"lower"`}, upper = x 최댓값·y 최솟값, lower = x 최솟값·y 최댓값'. 블록 값: A_max = upper 두 표의 큰 쪽, `found_db` = lower 두 표의 작은 쪽.
- IF E-1에 더함: '`found_db` = LAM 0.2 슬라이스 값(독립 계산 `gb4_hand`). 손: y가 두 배라 gain이 절반, 단순 공통 소스에서 A_max보다 6.02 dB 아래'. E-6 '`z_side` 표마다' 뒤에 'Π 불변(`grid_product_over_budget` 판정 입력이 슬라이스 수로 바뀌지 않음)'.

손 값: 슬라이스 LAM 0.1, 0.2, 같은 ID·GM. upper y = 0.1λ 꼴 → gain G. lower y = 2배 → gain G/2 → 20·log10(1/2) = −6.02 dB. 맞다.

### 5. M-TH1c

- **표 대조**: `summary.txt` 53파일 전부 표에 있다(스크립트 대조). 42 + 11 = 53, LI-1 8(#1~8), LA-1 29(#9~37), WB-1 5(#38~42), 소유 없음 0. `curve_value`·`peak_index`·`gm_id_lo`·`gmid_max` 적중 파일 중 표 밖 0.
- **LA-1 29가 계획 문언에 있는가: 있다.** P:2038: 축 소비 14(`_helpers_curves`, `_helpers_guard`, `_helpers_area`, `iv_area`, `iv_currents`, `iv_domain`, `iv_gain_l`, `iv_headroom`, `iv_matching_l`, `iv_noise`, `iv_speed`, `macro_poles`, `start_intervals`, `start_values`), 곡선 정의 5, `derived_fns` 1, O-207 묶음 9(`constraints`, `cell_floor`, `search_domain`, `layer0_center`, `slsqp_outer`, `vgs_current_density`, `id_inverse`, `curve_check`, `_helpers_root`). 합 29.
- **LI-1 8**: P:1259, P:1981 맞음. 다만 q5.
- **WB-1 5**: `_helpers_loo`만 계획에 없음(q4).
- 대상 아님 표본: `metrics/mirror_ratio`, `lut/point_query`, `lut/lut_set`은 순방향·로드 검사라 키워드 밖 처리가 맞다.

### minor(막지 않음)

- **q1** SP '원래 취지와 다름' 9 끝: '`realize_front`는 읽지 않는다. `convergence/converge.py:47`·`converge_point.py:55`는 c ≥ 0을 읽어 그 점을 거부한다(fail-closed, LA-1까지 임시, 크기 미측정)'.
- **q2** IF R-2: 'θ의 y는 V(out) = V(x)로 둔다(M1·M2 VDS가 같아야 W_M1 = W_M2 = 2e-6이고 M2 r = 0이다)'. 아니면 r4 LAM 항으로 W_M2 ≠ 2e-6이고 Δ 식 전제가 깨진다.
- **q3** IF M-4 '`strong_inversion_root` 사용 파일 = `lut/vgs_root.py` 하나'에 'LI-1이 먼저 병합됐으면 정의 삭제'를 더한다. `tests/lut/test__helpers_root.py`의 그 함수 test는 `test_vgs_root.py`로(옮김 목록).
- **q4** P:2479 (a)에 '호출이 없어지는 `lut/_helpers_loo.py` `branch_targets` 삭제, `strong_inversion_root`는 `lut/vgs_root.py`로(규칙 A)'.
- **q5** table·P:1983: `layout/contract_output.py`, `layout/w_tolerance.py`의 `gm_id` 칸·인자도 LI-1 몫으로 적는다. 소유 card가 같아 문제는 표 누락뿐이다.
- **q6** P:2094 '`peak_index` 소비 0'은 P:2038 'LI-1과 선후 고정 없음'과 어긋난다. `vgs_root`가 `peak_index`를 읽는다. 문언: '`peak_index` 소비 = `lut/vgs_root.py`뿐이면 같은 변경에서 그 파일로 옮긴다(규칙 A), LI-1이 지운다'. LA-1 card 때 처리해도 된다.

### 미측정

pytest 전부, 구조 test 실제 결과, base 코드 뒤 이름과 줄, D-1·D-2·R-2 회로의 실제 통과, 실현 평가 c < 0 발생 수, LI-1 전 LA-1 실행 경로, tol_V 실제 값, OP-7 선언 파일, PDK bin 표 격자꼴, mismatch p0 표, S-3 크기와 열별 포락 대 슬라이스별 차, `found_db` 변화가 층 0 배분에 주는 크기.

재판정(head `6c03871c`): Major 1

## 최종 재판정 (`6c03871c..529534e5`)

범위: 이 diff와 그것이 닿는 문장. 방법은 앞과 같다(실행 없음). 줄 번호는 `529534e5`, 소스는 `dda16724`.

### 결론

**Major 0. 문서·손 값 판정으로는 test 동결로 갈 수 있다.** 단 SP 착수 조건의 미충족(base, OP-7 선언 파일, library 13 회귀 전제, mismatch p0 표)은 그대로이고, 그것을 대신하지 않는다. 회로 통과와 수치는 미측정이다.

### 1. R1·q1~q6

| 항목 | 판정 | 원문 |
|---|---|---|
| R1 | 들어감 | D40:1237, D41:527, IF:206~208·212·218, SP:67·256·272, D42:10 |
| q1 | 들어감 | SP 9 |
| q2 | 들어감 | IF:234 |
| q3 | 들어감 | IF:309·371 |
| q4 | 들어감 | P:2479 |
| q5 | 들어감 | P:1983, SP:84, table.md 요약 |
| q6 | 들어감 | P:2094 |

옛 '슬라이스별 gain', Π 슬라이스 축 잔재 0건(대체 표지 문장뿐, 계획·design·card grep).

**`side` 칸과 소스**: 맞다. `block_gain_bound(model, tables, budget, members)` 한 번이 `BlockBound` 하나를 내고 `a_max_db`·`b_db`·`status`·`found_db`·`pi`가 함께 있다(`block_gain_bound.py:227-247`). 호출 자리 = `achievability._bound`(:160-165), 표 생성 = `:355`·`iv_context.py:56` 둘이고 IF가 둘 다 다룬다.

표 넷의 뜻도 소스와 맞다. 인증이면 `found_db` = max(ascent, best) = 그 표의 최대라, lower 표의 값은 '그 표에서 도달한 최대'다. E-1 손 값 6.02 dB가 그대로 성립한다. 예산 초과면 ascent 값만 나오고, 기준점이 없으면 None이다.

### 2. 작성자가 더한 곳

| 자리 | 판정 | 근거 |
|---|---|---|
| `found_db` 한쪽 None → None | 맞다 | `_gain` `found_sum`이 None을 이미 처리(`achievability.py`). 산술 없음 |
| 상한 = upper 두 표 모두 `CERTIFIED`일 때만 인증 | 맞다 | 한 표만 인증이면 큰 쪽을 모른다. 미상은 `_chain`·`sum_db`에서 None, verdict 미정. `iv_context:50`도 미인증이면 비활성. fail-closed |
| `b_db` = 큰 쪽 표 값 | 맞다 | `_resolution`은 그 최대 행 이웃의 차라 그 표의 양이다. `sum_db + b_db < target`의 뜻 불변 |
| E-7 | 맞다 | 빈칸 s2 |
| 표 칸 포락(정의 안 된 슬라이스 제외, 없으면 NaN) | 맞다 | 4절. 슬라이스 하나의 행이 x·y·z를 함께 내므로 칸 일부만 빠지는 경우가 없다 |
| q5 '손 추가 2' | 맞다 | 44 = 42 + 2, LI-1 10. 패턴 밖임을 표지. A-6 재실행 판정은 키 비교라 영향 없음 |
| P:2094 toy 문언 | 맞다 | '정점이 곡선 안쪽인 합성 곡선'. r4는 정점이 VGS 0 |

### 3. `GainInputs` = upper·`z_side` `"max"` 표 하나

**받아들인다. 판정에 닿는 경로가 없다.**
- 소비: `iv_gain_l.gain_l_bounds`만 이 표를 읽는다(`inputs.tables`, `_row`, `_gain_db`).
- 출력: `Bound(QUANTITY_L, SIDE_LO, SRC_GAIN_L, ...)`와 `StartConflict`. `start_intervals` 머리 '출발값과 보고에만 쓴다(EP-7 -- 판정은 외층 봉인·metric)', '충돌이면 자르지 않고 남긴다'.
- 상위 게이트 `VERDICT_INFEASIBLE`은 `_bound`의 표 넷을 쓰고 이 표를 읽지 않는다.
- 간접 영향: 시작점이 바뀌어 국소 탐색 결과가 달라질 수는 있다. 그것은 판정이 아니라 출발 품질이고, 팔로워 블록에서 gain이 낮게 잡혀 L 하한이 높아지는 쪽이다. 크기 미측정, LA-1 재작성 때 다시 본다.
- 대안: z 두 표로 큰 쪽 ⚠ 곧 재작성할 card 범위(LA-1a 범위 1)인데 이득 L 하한 평가만 2배. 지금 고칠 이유가 없다.

작성자 표지 '재점검 LA-1'로 충분하다. **원래 취지와 다름 없음**(출발값 범위 안).

### 4. 표 칸 NaN

**사유 없이 지나가지 않고 fail-open도 없다.** 기존 NaN 경로와 같다.
- `row_gains`: `valid &= isfinite(x)·isfinite(y)·isfinite(z) & current > 0`, 끝에서 `np.where(valid & isfinite(gain), gain, nan)`(`:58·:78`).
- `_exhaustive`·`_ascent`: `np.where(isfinite, gain, -inf)`. 전부 NaN이면 `idx` None → `STATUS_UNKNOWN`, `REASON_AXIS_RANGE`(`:236-239`). 이것이 D40:1237 '`()`면 A_i,max 미정, 기존 미정 갈래 READS'의 그 갈래다. E-4의 '갈래가 없으면 멈춤'은 해당 없음.
- `_refine`·`_resolution`: `isfinite` 거름.
- `iv_gain_l._row`: `x >= g_lo`가 NaN에서 거짓, `isfinite(ratio)` 거름, 없으면 row None → 건너뜀.

슬라이스를 칸에서 빼면 upper 값이 낮아질 수 있으나, 그 슬라이스는 그 점을 LUT가 정의하지 않아 실현 근거가 없다(D1과 같다). 잘못 통과하는 쪽이 아니다.

### 5. 새 모순

찾지 못했다. D1·D2·D4~D6, A-63·A-64, R3 `residual`, W2 키 치환과 충돌 없음. 규칙 A: 합치는 일은 `achievability._bound` 안이고 새 공개 이름이 없다. graph 규칙: `graph/ach` 칸 불변, 새 칸 0, 표는 호출 안 객체라 사본 칸이 아니다.

### minor(막지 않음)

- **s1** IF 블록 값: 합친 `BlockBound`의 나머지 칸을 적는다. `condition` = 큰 쪽 표, `reason` = 미상인 첫 upper 표(`z_side` `"min"` 먼저, 결정성), `n_rows` = 네 표 합, `axes` 같음. 값이 같으면 `"min"` 표.
- **s2** IF §9에 E-7 관찰 지점: `sys.modules["gmid_engine.metrics.achievability"].block_gain_bound`(패키지에 같은 이름 함수가 있어 점 표기는 함수가 나옴).
- **s3** 표 구현: 전부 NaN 칸의 경고를 피하게 `np.fmax`·`np.fmin` 꼴. `_load`의 `searchsorted`는 슬라이스 VGS 격자가 `grids`와 같다는 전제이므로 슬라이스마다 축 일치를 재고 다르면 거부한다(새 입력이 슬라이스 여럿이 되면서 처음 필요).
- **s4** `derived_fns._param_row`의 `except SealViolationError: return None`은 `lut_column_unavailable`도 삼켜 그 슬라이스를 조용히 뺀다. IF '`is_slice_gap`이면 뺀다'와 맞추려면 그 함수에서 사유로 가른다.
- **s5** GB4 비용이 표 넷으로 최대 4배다(`_exhaustive`·`_refine`을 표마다 돎). A-9 기록에 GB4 벽시계를 더한다. 문턱 없음.

### 미측정

pytest 전부, 구조 test 실제 결과, base 코드 뒤 이름과 줄, D-1·D-2·R-2 회로의 실제 통과, 실현 평가 c < 0 발생 수, LI-1 전 LA-1 실행 경로, tol_V 실제 값, OP-7 선언 파일, PDK bin 표 격자꼴, mismatch p0 표, 열별 포락 대 슬라이스별 차와 거짓 `VERDICT_INFEASIBLE` 발생, `found_db`·`GainInputs` 표 선택이 층 0·출발에 주는 크기, 슬라이스별 VGS 격자 일치, GB4 벽시계.

verdict: Major 0
