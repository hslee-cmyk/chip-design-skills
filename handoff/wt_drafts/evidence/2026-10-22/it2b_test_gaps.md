# IT-2b test 멈춤 사유 판정 (2026-10-22)

- 자료: design 41 v1.12.8(master, `docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md`), 계획 v6.32(master `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`), card `wt/integ-it12/docs/02-design/specs/20261021-it2b-kernel-window.{spec,interface}.md`·`20261021-it2-common.md`, 엔진 `wt/integ-it12`(head 56080584, 엔진 = base 0c048327), test 커밋 `wt/it2b-test` 79323cbe.
- 실측: `wt/_scratch_it2b_gaps/`(it2b-test `--no-local` 복제, remote 제거) 안에서만 돌렸다. 실행한 것은 사유 3의 봉인 통과 확인 1건뿐이다(결과 `wt/_scratch_it2b_gaps/out_d.txt`).
- `E/` = `skills/analog-gmid-design/gmid_engine/`. 줄 = integ-it12 판.
- 읽기 전용 작업이다. 저장소 파일은 고치지 않았다.

## 요약

| 사유 | test 작성자 주장 | 판정 | 권고 | design | card | 계획 | 원래 취지와 다름 |
|---|---|---|---|---|---|---|---|
| 1 T-Pab-k 감도 음수 | 비F 성분의 뿌리 아닌 포트 감도는 늘 양수다. 음수가 되려면 소스 감도가 0 근처여야 하고, 그러면 F 성분이다 | **부분** | (가) toy 넘김(아래 T-NEG). LUT 픽스처가 필요하다 | 불요 | 불요(test 픽스처 몫) | 불요 | 아님 |
| 2(i) tol 미정 → exc.partial | `tol_v_undefined`가 먼저 난다 | **부분**(현상은 맞음. 그 toy는 A6 b toy가 아니다) | exc.partial로 읽지 않는다. A6 b는 비순환 쓰기 계획 + tol_V 미정·tol_VDsat 정의 LUT로 `run_blocks(upto="columns")`에서 직접 본다 | 불요 | 메모 권고 | 불요 | 아님 |
| 2(ii) k_max 소진 | 주입 지점이 없다 | **맞음** | 커널 주입 지점 `gmid_engine.sizing.block_columns.k_max`를 design·공통 문서에 정한다. IT-2d 이관은 기각 | **필요**(4.7-7 L12 (a), 4.7-4 '모듈 수준 이름') | **필요**(공통 '주입 지점') | 불요 | 아님 |
| 3 D 같은 점 봉인 거부 | (S4-나)에서는 불일치 점이 봉인을 통과한다 | **맞음**(엔진 실측) | O-58 S-4 '늦게 병합되는 card' 규칙을 triode 동작점 불일치(블록 `op_mismatch` 판정 + 봉인 거부)에도 적용한다 → (S4-나)이면 EO-1 몫 | **필요**(4.7-3a 2·3, 4.7-7 D, 4.7-2 상태 어휘 주석) | **필요** | **필요**(N6.6 완료 조건 (9), N6.20 범위 (4)) | **예(작음)** |
| 4(a) P(b) 선언 차 | 스칼라라 차가 늘 0이다 | **맞음**. 단언은 여전히 의미 있다 | 단언은 그대로 둔다. card에 '선언 차 = 0(spec 어휘)'을 메모한다 | 불요 | 메모 권고 | 불요 | 아님 |
| 4(b) assert_voltages 좁힘 | 뿌리 키로 좁혔다 | 전체 등식 '뿌리 ∪ 입력 포트'는 **유지 불가**. 그래도 좁힘은 약화다 | 뿌리 부분 등식 + 나머지 키 ⊆ 입력 포트 | 불요 | 불요 | 불요 | 아님 |

---

## 1. T-Pab-k -- 감도 음수 포트

### 판정: 부분

**물리 유도**(design 41:695 '뿌리 아닌 입력 포트 p(같은 성분, 트리 경로로 쓰임)'). 커널 감도 연립(`E/sizing/input_window.py:26-45`)의 writer 식은 전류를 θ로 고정한다(`writer_grad` docstring `E/sizing/block_columns.py:435-` -- ∂VGS/∂VDS = −gds/gm, ∂VGS/∂VSB = gmb/gm). F = ∂VGS/∂VDS(전류 고정, 포화에서 음수이고 |F| = gds/gm), η = ∂VGS/∂VSB로 두면 엣지마다 다음과 같다.
- source를 gate에서 쓰는 엣지(`vgs_source`): s_s·(1 + |F| + η) = s_g + |F|·s_d → s_s ≥ 0(s_g, s_d ≥ 0이면).
- gate를 source에서 쓰는 엣지(`vgs_gate`): **s_g = s_s·(1 + |F| + η) − |F|·s_d**.
- 저항 엣지(`resistor_drop`): 전류가 θ라 s_far = s_near.
- W4 순서 창 노드: lo + y(hi − lo)라 이웃 감도의 볼록 결합이다.

따라서 음수가 될 수 있는 엣지는 `vgs_gate` 하나다. 조건은 **|F|·(s_d − s_s) > s_s·(1 + η)**, 곧 그 소자의 드레인이 소스보다 x를 더 따라가고 동시에 gds/gm이 크다(진성 이득 gm/gds가 작다).

- test 작성자 식 '엣지 감도 = 1 + LAM/G′…'은 r4 LUT의 같은 식이다(`tests/sizing/conftest.py:48-50`: B = 20, C = 8, LAM = 0.1이라 |F| = LAM/(gm/ID) ≤ 0.1/5.6 ≈ 0.018). **r4 LUT 안에서는** 음수가 사실상 불가능하다. s_d가 s_s의 55배를 넘어야 한다.
- 일반 물리로는 '소스 감도가 0 근처라야 한다'가 유일한 길이 아니다. **경로 위 소자의 gm/gds가 작으면**(deep triode -- `intended_region: triode` 선언 소자) s_s가 1 근처여도 음수가 된다. 예: η_B ≈ 0.3이면 |F_T| > 약 4, gm/gds < 약 0.25로 충분하다. 이 소자는 포화 행이 아니라 triode 행(design 41:705 (나))을 받으므로 엔진이 허용하는 동작점이다.
- '소스 감도 ≈ 0이면 F 성분'은 레일에 소스가 닿는 경우에 맞다(레일 → F 성분 → 선언 포트 또는 `f_component_undeclared`, 41:697). 다만 비F 성분 안에서도 높은 body 효과의 긴 follower 사슬로 s_s를 작게 만들 수는 있다. 1.8 V 공급에서는 현실성이 없다.
- 결론: 포화 소자만으로 된 트리 경로라면 '양수'는 맞다. 포화 소자의 gm/gds ≫ |Δs_d|/((1+η)s_s)이기 때문이다. 일반 명제로는 **틀리고**, triode 선언 소자가 경로에 있으면 음수가 가능하다.

**코퍼스(13회로)**: `intended_region`이 모두 `{"pending": "CI-18"}`이다(library 9 + heldout 4 sizing_spec 실측). triode 선언 소자가 0개라 위 메커니즘은 발동하지 않는다. diff pair 꼴(뿌리 → 꼬리 `vgs_source` → 반대 입력 `vgs_gate`)은 s_in− = 1 + |F|·(s_d,a − s_d,b) 꼴이다. 드레인 감도 차 O(1) × |F| ≪ 1이므로 양수로 **추정**한다. 엔진 실측은 **미확인**이다(design 41:823 '4.7-8a s_p 부호' 칸은 '미측정', IT-0 판정 기록 없음 -- `wt/integ-it12/.ai/verification/`에 IT-0 기록 0건).

### 권고: (가) -- 음수 감도 toy(이름 없음)

**연결 T-NEG**(레일 vdd·gnd, 입력 포트 둘 x·p, 출력 없음 또는 게이트 전용 바이어스만):
- 소자 A nmos (d = vdd, g = x, s = t, b = gnd): x → t `vgs_source`.
- 저항 R (t, d): t → d `resistor_drop`, s_d = s_t. VDS_T를 작게 만드는 레벨 이동이다.
- 소자 B nmos (d = vdd, g = t, s = u, b = gnd): t → u `vgs_source`, s_u = s_t/(1 + |F_B| + η_B).
- 소자 T nmos (d = d, g = p, s = u, b = gnd), **`linear_devices = (T,)`**(triode 선언): u → p `vgs_gate`.
- 이상 전류 싱크: t·d·u에서 gnd로 필요한 만큼 둔다(KCL, `free_currents`).
- 성분 {x, t, d, u, p}에는 레일이 없다(드레인 vdd는 G_vgs 엣지가 아니다). 순환이 없다(엣지 4, 노드 5). 입력 DC는 미선언이다.
- 감도: s_p = s_u(1 + |F_T| + η_T) − |F_T|·s_t. **음수 조건 |F_T| > (1 + η_T)/(η_B + |F_B|)**(s_u/(s_t − s_u) = 1/(η_B + |F_B|)에서). 예: η_B ≈ η_T ≈ 0.3이면 |F_T| > 약 4.3. square law로는 VDS_T ≈ 0.05 V, Vov_T ≈ 0.4 V에서 |F_T| ≈ (Vov − VDS)/VDS ≈ 7이다.
- 전제 단언(test 안): 쓰기 계획이 x를 W4 뿌리로 고르는지(`node.dc_writer` relation). p가 뿌리로 뽑히면 s_x = 1/s_p로 역시 음수이므로 그 경우 포트 이름만 바꿔 단언한다. T가 해에서 triode 행 여유 ≥ 0인지도 확인한다.
- **LUT 조건**: r4 LUT는 |F| ≤ 0.018이라 **쓸 수 없다**. VDS 의존 ln ID가 작은 VDS에서 가파른 LUT 픽스처가 필요하다. 예: ln ID = f(VGS) + h(VDS)로 두고 그 점에서 h′(VDS_T)/(gm/ID) ≥ 위 문턱(약 4~5)을 만족시킨다. VDS 격자가 그 구간을 분해해야 하고 GDS 열(Hermite 기울기, `writer_grad`의 gm_gds)도 있어야 한다. 이는 test 픽스처 몫이고 엔진 상수는 아니다. 실제 PDK LUT를 쓰면 deep-triode 점으로 같은 효과를 얻는다.
- 오라클: 뿌리 창 끝 lo_x·hi_x에서 x를 고정한 독립 풀이(이분법)의 V_p를 쓴다. 기대 = [min(V_p(lo_x), V_p(hi_x)), max(…)] ∩ 레일, lo ≤ hi이고 V_p(lo_x) > V_p(hi_x)(음수 전제)이다. 감도 옮김 '추정' 허용오차는 K2와 같은 방식으로 둔다.
- 사유 3과 묶임: T는 triode 선언 소자다. (S4-나)에서 블록의 `op_mismatch` 판정이 EO-1 몫으로 가면(사유 3 권고) 이 toy는 그 판정과 얽히지 않는다. 사유 3을 다르게 결정하면 이 toy의 T가 커널 해에서 triode를 유지하는지 단언을 하나 더 둔다.
- 픽스처를 만들 수 없으면 멈추고 보고한다. 단언을 정렬 식만으로 약화하는 (나)는 권하지 않는다. [min, max] 정렬은 `dc_columns` 안 호출자 규칙(41:695 '포트 창은 호출자가 한 규칙으로 만든다')이라 공개 순수 함수로 따로 단언할 자리가 없다. 정렬을 피검 경로 밖에서 재면 행동 증거가 아니다.

### 원칙 점검
- graph 정본: 새 필드·cache 없음(test 픽스처만).
- fail-closed: 해당 없음.
- 상수 발명: 없음(문턱은 유도식이고 예시 수치는 toy 입력).
- 회로 이름: 없음.
- DC/AC 분리: DC 감도(전류 고정 writer 식)만 쓴다.
- 계획 우선: 계획 (7)(a) '커널 창과 다듬은 창 모두' 그대로다.

---

## 2. T-L12a-k -- unsettled

### (i) tol 미정 경로 -- 판정: 부분(현상은 맞음, 해석은 틀림)

- `tol_v_undefined`를 내는 자리는 엔진 비test 코드에서 `Circuit.tolerance` 하나다(`E/sizing/block_columns.py:524-536`, grep 실측). 순환 SCC 풀이(`:578-579` Gauss-Seidel/Newton tolerance)와 자기참조 bisection(`solve_self` `:377`)이 이 함수를 부른다. 그래서 순환 SCC가 있는 toy에서 tol_V가 미정이면 **노드 풀이 자체가 실패**한다. y = 1/2 실패 → `_interior_solution`(`:629-649`, tol 없으면 None) → `return _solve(c)`(`:715-717`)가 예외를 낸다. 이는 후보 실패이지 A6 b가 아니다.
- design A6 b(41:660 (b) "`tolerance`가 미정이면 창을 한 번만 적용하고 되풀이 수렴 판정 없이 푼다", as-built `:707-712`)는 **풀이는 성공하고 되풀이 수렴 판정 tol만 미정**인 경로다. 도달 조건:
  - 쓰기 계획에 순환 SCC·자기참조 노드가 없다(비순환 SCC는 `update`만 부르고 tol을 읽지 않는다 -- `:404-433`).
  - 모든 행의 tol_VDsat가 정의된다(`saturation_rows` `:232-236`, 미정이면 rows None → A6 a `unmeasured`).
  - 해의 모든 MOS VDS 셀에서 id_equivalent tol_V가 None이다(`tolerance`는 하나라도 정의되면 최솟값을 낸다).
- **exc.partial로 읽을 수 있는가: 없다.**
  - 예외가 `dc_columns`에서 나면 `_call_block`이 **그 블록에 들어간 스냅샷**을 붙인다(`E/sizing/kernel_run.py:56-63`, `core/failure_partial.py:13-20`). 그 평가의 `dc_columns` 출력은 없다.
  - parent가 있으면 지금(IT-2a 뒤) keep에 `dc_columns`가 들어 있다(`kernel_run.py:84-86` derive_child keep = base writer ∪ 커널 블록 ∪ 봉인 항목 블록). 그래서 partial에 **parent의 낡은 `node.dc_window`**가 남을 수 있다. 바로 B69다.
  - v6.32 B69 규칙(계획 N3.3 '실패 평가의 부분 스냅샷', O-96: 남기는 writer = base writer ∪ 실패 전에 성공한 블록, card IT-2e)을 적용하면 실패 블록 `dc_columns`의 필드는 빠진다. 어느 쪽이든 '그 평가의 unsettled'를 partial에서 읽는 단언은 성립하지 않는다.
  - `dc_columns`가 성공하고 뒤 블록이 실패하면 B69 규칙으로 partial에 `dc_columns` 출력이 남는다. 그래도 그 단언은 `run_blocks(ctx, θ, upto="columns")`(conftest `:737`)로 직접 보는 편이 맞다. partial은 필요 없다.
- **권고**: A6 b toy = 비순환 쓰기 계획(예: 입력 미선언 source follower 뿌리 하나 -- 순환·자기참조 없음, `node.dc_scc_order`로 전제 단언) + **tol_V(id_equivalent) None·tol_VDsat 정의** LUT 픽스처. 이 LUT 조합은 test 픽스처 몫이다. 두 표의 외부 값 칸이 다르므로(`lut/tolerance.py` l_bin_checks의 `id_equivalent_v`, `lut/vdsat_tolerance.py` `vdsat_v`) 축 내부점이 없는 격자 + 중점 파일 `vdsat_v`만 주는 구성이 후보다. **실제로 만들 수 있는지는 미확인**이다. 만들 수 없으면 멈추고 보고한다. 이때 tol 주입 지점을 design에 더할지는 사용자 결정이다(오케스트레이터가 지어내지 않음).
- card 메모 권고: '2점 격자 LUT + 순환 SCC toy의 `tol_v_undefined`는 후보 실패(A6 b 아님)'.

### (ii) k_max 소진 -- 판정: 맞음(주입 지점 없음)

- 엔진(as-built): 커널 A6 되풀이에 상한이 있다. `for _ in range(k_max(c.hi - c.lo, tol))`(`E/sizing/block_columns.py:713`). `k_max` = ceil(log2(폭/tol))이고 상수가 없다(`E/sizing/k_max.py`). 모듈 수준 import는 `block_columns.py:46` `from .k_max import k_max`다. 같은 모듈 `_interior_solution`의 시도 상한(`:636`)과 `_refine_ends`(`:659`)도 같은 이름을 읽는다.
- design: 41:694 '되풀이(상한 `k_max`)', 41:660 A6 (c), 41:688 `"unsettled"` 정의가 있다. 주입 허용은 41:804 R2 하나뿐이고 대상은 `gmid_engine.sizing.window_refine.solve`·`.k_max`(4.7-4 모듈 수준 이름, 41:762)다. 공통 문서 `20261021-it2-common.md:149`도 "주입 지점 밖 내부 이름 monkeypatch는 test 금지(R2: `window_refine.solve`·`.k_max`만)"이다. → IT-2b 커널 쪽 공개 주입 지점은 **없다**.
- 자연 toy 가능성: A6 되풀이는 '해에서 잰 선형 끝(= 행 여유의 Newton 추정)'을 y 범위로 다시 넣는 고정점 사상이다. 창 끝의 y 범위 의존은 2차라 축소가 강하다(보통 2~3회에 tol 안). ceil(log2(폭/tol)) 회 안에 수렴하지 않는 toy는 곡률·결속 행 전환을 인위로 맞춰야 한다. 재현성 있게 설계하기 어렵다고 판단한다(실측 안 함 -- 미확인).
- **IT-2d로 옮기는 안: 기각.** `window_refine.k_max`는 다듬은 창 끝 풀이 상한이다(R2 → `window_end_k_max_exhausted`). 커널 A6 되풀이(→ `node.dc_window` `"unsettled"`)를 건드리지 않아 다른 루프를 재게 된다. 계획 (12)(a) 앞부분 "커널 되풀이 `k_max` 소진 toy"와 맞지 않는다.
- **권고**: design 41 4.7-7 L12 (a)에 커널 주입 지점을 정한다. R2와 같은 꼴로 **`gmid_engine.sizing.block_columns.k_max`(상한 1)**만 허용하고, 4.7-4 '모듈 수준 이름'에 "`block_columns.py`는 `from .k_max import k_max`를 모듈 수준에 유지한다(`_solve_input_window`가 남는 모듈)"를 더한다. 공통 문서 '거부해야 할 입력'의 주입 지점 줄에 이 하나를 더한다.
  - 근거: 4.7-4 이동 범위는 `Circuit`·`solve`·`FAILURES`뿐이다(41:760). `_solve_input_window`는 `block_columns`에 남고, `solve_self`는 helper 쪽 import를 쓰므로 영향이 갈리지 않는다.
  - test 전제 단언: 요청 y ≠ 1/2, y = 1/2 풀이 성공(같은 모듈의 `_interior_solution`도 이 이름을 읽으므로 그 경로에 들어가지 않음을 전제로 둔다), 첫 회 창과 둘째 측정 창의 차 > tol(손계산).
  - 기대값: 뿌리 `input_status == "unsettled"`, `lo`·`hi` = 마지막으로 잰 창 ∩ 순서 창(y 범위 그대로), V(뿌리) = lo + y(hi − lo).
  - base red: as-built `Window`에 `input_status` 칸이 없다(AttributeError).
- 계획 (12)(a) 커널 쪽 문언("커널 되풀이 `k_max` 소진 toy·tol 미정 toy -- … W4 y 범위는 그대로 쓰임(base는 마지막 창 값을 냄 -- red)")과 맞는다. 'toy'를 주입으로 만드는 것은 R2 선례(41:804 "자연 toy로 만들기 어려우면 monkeypatch")와 같은 수단이고 계획 개정은 필요 없다.

### 원칙 점검(2)
- graph 정본: 새 필드·cache·사본 없음. 주입은 기존 모듈 수준 이름이다.
- fail-closed: A6 b·c 모두 `"unsettled"`이다.
- 상수 발명: 없음(k_max는 유도식, 주입값 1은 R2 선례).
- 회로 이름: 없음.
- DC/AC: DC.
- 계획 우선: 계획 불변, design 4.7-7 L12 (a)·4.7-4만 고친다.

---

## 3. D '같은 점 봉인 거부(선언 오류)'

### 판정: 맞음(엔진 실측)

- 봉인 7은 선언 소자를 빼기만 한다(`E/sizing/seal_saturation.py:56` `if op.current > 0 and m not in linear_devices`). 봉인 9는 전도(I_off ≤ ε·ID)만 본다(`E/sizing/seal_conduction.py:1-14`). 다른 봉인 항목에도 영역 대조가 없다(`grep linear_devices|triode` -- `seal.py:57`, `seal_saturation.py`뿐). spec 어휘는 `REGIONS = (REGION_TRIODE,)`이다(`E/authoring/spec_regions.py:16-17`). EO-1은 미병합이다(card '작성 전 실측' S4-나).
- **실측**(scratch 복제, test 작성자 toy `test__helpers_dc_solve._toy_ctx`, y = 0.7, vsg2 = 0.3, `size_and_seal` raise 모드): 예외 없이 통과했다. V(out) = 1.5, V(in) = 0.8 → M1 VDS = 0.7 > VDsat 0.5234 + tol 0.00098, 곧 선언 triode 소자가 포화다. 봉인 보고서 항목 1~9가 모두 `pass`이고, 항목 7 `n_checked = 2`(M1 제외)다(`wt/_scratch_it2b_gaps/out_d.txt`).

### design에 거부 자리가 정해져 있는가: EO-1에 정해져 있다 → (S4-나)에서는 gap

- 41:710 (4.7-3a 3): "거부 자체는 봉인 게이트(계획 N3.6 표 7·9행, card EO-1 범위 4 (b))가 '선언 오류'로 낸다(노드 풀이 블록은 봉인 전이라 거부하지 않는다)".
- 41:712: "판정 함수·기준 = 봉인 7·9와 같은 것: … `triode` = 봉인 7의 triode 대조와 같은 함수·기준(… 맡는 card EO-1 N6.20 범위 (4) (b)) … 이 블록은 행 여유 부호로 따로 판정하지 않는다(정본 하나)".
- 계획 N6.20 범위 (4)(b)(plan 1936행): 공용 전도 판정 함수(전도·꺼짐·선언 영역 판정, `triode` 대조 기준 = T-1)와 "`triode` 선언 MOS가 꺼짐이면 거부(포화 쪽은 봉인 7 대조)"가 EO-1 범위다.
- 반면 S-4 갈래(41:706-709, 계획 (9) "`off` toy는 … 늦게 병합되는 card")는 **`off` 행·V_on만** 나눴다. 계획 완료 조건 (9) 끝 "동작점에서 선언 영역과 어긋나는 toy → 창이 아니라 선언 오류 거부"와 design 4.7-7 D(41:810)는 S4 갈래와 관계없이 IT-2에 남아 있다.
- 결과: (S4-나)에서 IT-2b는 (1) **블록의 `op_mismatch` 판정**에 쓸 함수가 없다. 그 함수는 EO-1이 만들고, design은 행 여유 부호 판정을 금한다. (2) **같은 점 봉인 거부**도 없다. 블록 쪽은 test 작성자가 보고한 것보다 더 깊다. code 작성자가 design대로 `op_mismatch`를 쓰려면 EO-1 함수를 당겨 만들거나(범위 침범, 나중에 EO-1이 둘째 생산자가 됨) 행 여유로 판정해야 한다(41:712 위반). 둘 다 graph 단일 정본 규칙 1(writer 하나·둘째 생산자 금지)과 card '범위 밖 하위 card 일을 당겨오지 않는다'에 걸린다.

### 권고(하나): S-4 규칙을 triode 동작점 불일치까지 넓힌다 -- **원래 취지와 다름(작음)**

- 규칙: 4.7-3a 3 전체(블록의 `op_mismatch` 기록 + 같은 점 봉인 거부 + D 동작점 불일치 toy + metric code `input_window_operating_point_mismatch` 배선)는 **IT-2·EO-1 가운데 늦게 병합되는 card**의 변경이다. 사용자 결정 O-58 S-4·O-56 (b)와 같은 원리이고, 공용 판정 함수 없이 넣는 판정은 정본 없는 판정이거나 죽은 코드다.
  - (S4-가)(EO-1 먼저): IT-2b가 지금 design대로 블록 판정(EO-1 함수 호출)을 넣고 test D가 봉인 거부까지 단언한다.
  - (S4-나)(지금): IT-2b·IT-2d는 `"op_mismatch"` 상태·`status_detail` 쓰기·metric code를 **넣지 않는다**(배선 없는 어휘는 '만들면 배선' 위반). EO-1이 늦게 병합될 때 공용 함수 + 봉인 7 triode 대조 + 블록 `op_mismatch` + metric code + D toy(같은 점 봉인 거부 포함)를 한 변경으로 넣는다. IT-2b의 D는 **triode 행 영 교차 = 창 끝**(41:810 앞부분, EO-1 무관 -- 행 여유는 tol_VDsat 정본 값만 쓴다)과 (S4-나) 부재 단언만 남긴다. `test_it2b_d_operating_point_mismatch_status_and_detail`은 EO-1 test로 옮긴다.
  - 부재 단언 추가 권고: (S4-나)에서 `dc_columns`가 `input_status == "op_mismatch"`를 쓰지 않음, 곧 엔진 비test 소스에 그 문자열 0(`git grep`).
- 고칠 자리:
  - 계획 N6.6 완료 조건 (9) 끝 문장, N6.20 범위 (4)(이 card 범위 쪽에 블록 `op_mismatch`·D toy 추가), O-58 S-4 인용 문언.
  - design 41 4.7-3a 2 S-4 갈래 두 항(41:707-708), 4.7-3a 3 머리, 4.7-2 값 형식 `"op_mismatch"` 칸에 '(S4 갈래)' 표시, 4.7-5 code 표 해당 행, 4.7-7 D(41:810).
  - card IT-2b spec '관찰 가능한 계약' 둘째 항의 '동작점 불일치 = 성분 전체 `op_mismatch`'와 '판정 단언 D'.
  - 공통 문서 표 D 행('IT-2b(창)·IT-2d(metric code)' → S4 갈래).
- 계획 우선: 완료 조건 (9)의 card 배정이 바뀌므로 **계획부터** 개정 → 검증 → 사용자 승인 → design → card 재동결 순서다.
- 원래 취지와 다름(작음): 원래 취지(O-54·O-55 U1)는 IT-2가 동작점 불일치를 선언 오류로 거부하는 것이었다. (S4-나)에서는 EO-1 병합까지 이 거부가 늦어진다. 그 사이 triode 선언 소자가 포화인 점이 봉인을 통과하는 as-built 상태가 이어진다. 영향: 13회로 모두 `intended_region` pending(CI-18)이라 선언 소자 0개, 발동 0이다(spec 실측). 새 결함을 만드는 것이 아니라 지금 상태가 늦게 고쳐진다.
- 기각한 대안:
  - (가) IT-2b가 행 여유 부호로 블록 판정: 41:712 '정본 하나' 위반, EO-1 뒤 둘째 생산자.
  - (나) IT-2b가 EO-1 공용 함수를 먼저 만듦: 범위 침범, EO-1 순서·완료 조건 (8)(b) 호출 자리 단언과 충돌.
  - (다) IT-2b 범위의 다른 봉인 항목으로 거부(예: 봉인 7에서 선언 소자를 빼지 않음): triode에 올바로 있는 소자까지 거부하는 물리 오류. 새 봉인 항목을 만들면 EO-1의 봉인 7 triode 대조와 둘째 생산자가 된다.
  - (라) 'EO-1 뒤로 미루기'만 하고 IT-2b에 `op_mismatch` 어휘·쓰기를 남김: 판정 함수 없이 쓰기를 둘 수 없다. 어휘만 남기면 죽은 코드다.

### 원칙 점검(3)
- graph 정본: 새 writer·사본 0, 판정 정본 = EO-1 함수 하나.
- fail-closed: 지금 상태보다 나빠지지 않는다(as-built 유지). 발동 0은 실측.
- 상수 없음, 회로 이름 없음.
- DC/AC: DC 동작점 영역 판정.
- 계획 우선: 계획 개정이 먼저다.

---

## 4. 보조 판정

### (a) P(b) '선언 둘 포트 창 끝 차 = 선언 차' -- 판정: 맞음(차는 늘 0), 단언은 의미 있음

- `DcInputs.input_dc_v` = "입력 포트 공통 DC(V)"(`E/sizing/s2_values.py:185-192`)다. `dc_inputs_from_spec`은 InputDc mode `net`/`value` 하나를 투영하고(`E/sizing/dc_inputs.py:28-33`), `kernel_fields`가 모든 입력 포트에 같은 값을 고정한다(`E/sizing/kernel_fields.py:51-54`). spec 어휘에 포트별 DC가 없다. → 선언 차 ≡ 0.
- design 41:700 "각 포트 전압 = 선언값 + Δ … 포트별 창 끝이 선언 차만큼 어긋난다"는 일반형 문언이다. 지금 어휘에서는 차가 0인 특수형만 도달한다. design을 고칠 필요는 없다(일반형이 특수형을 포함하고, 포트별 DC 어휘는 spec card 몫).
- 단언의 변별력: '같은 x 묶음'과 '포트별 따로 훑기'를 가른다. test 작성자 diff pair toy에서 꼬리 t를 한 소자가 쓰므로 따로 훑으면 끝이 달라진다(red). '끝 차 = 0 + 묶음 손계산 끝'은 의미 있는 행동 단언이다.
- 권고: card 메모 한 줄 -- "선언 차 = 0(`DcInputs.input_dc_v` 스칼라, 포트별 DC 어휘 없음); P(b) 단언 = 두 포트 끝 동일 + 묶음 손계산". 비영 선언 차 toy는 미도달이므로 요구하지 않는다.

### (b) `assert_voltages` 키 집합 -- 판정: '뿌리 ∪ 입력 포트' 전체 등식은 유지 불가, 지금 좁힘은 약화

- design 41:701(4.7-3 4): 측정 실패(A6 a)면 "뿌리 아닌 포트·x를 따로 두는 포트 항목은 쓰지 않는다". `"f_component_undeclared"` 포트는 항상 쓰인다(41:697). 그래서 `node.dc_window` 키 집합은 측정 성공 여부에 따라 달라지고, '뿌리 ∪ 입력 포트' 등식은 일반 불변식이 아니다. VDSAT 열 없는 `toy_access` LUT를 쓰는 기존 toy는 이 측정 실패 경로를 탄다.
- test 작성자 좁힘(`win = {n ∈ roots}` 뒤 등식)은 원래 단언이 잡던 '뿌리도 입력 포트도 아닌 넷에 창이 쓰임'을 놓친다. 그 축의 약화다.
- **대안(약화 없음)**: 키를 둘로 나눠 단언한다.
  - (1) `set(win_all) & roots == set(win_exp)`, 그리고 뿌리 끝 값 대조.
  - (2) `set(win_all) - roots ⊆ input_ports`. `input_ports` = 스냅샷 `node.port_direction == "input"`(입력 필드, 피검 출력 아님).
  - 입력 포트 항목의 존재·상태는 K1·L12(b) test가 정확히 본다.
- 7 호출(`tests/sizing/test_block_columns.py`)에 모두 적용된다. test 작성자 몫이고 design·card 변경은 없다.

---

## 확인하지 못한 것(미확인)
- library/heldout 13회로의 실제 s_p 부호(엔진 실측 안 함 -- IT-0 M-I4 '미측정'). 연결·물리 분석과 `intended_region` 전부 pending이라는 사실로만 추정했다.
- A6 b용 LUT 픽스처(tol_V None·tol_VDsat 정의)를 기존 conftest 도구로 만들 수 있는지.
- 커널 A6 되풀이 자연 소진 toy의 존재(분석상 비현실적이라고 판단했고 실측은 안 함).
- T-NEG toy의 실제 수치 성립(LUT 픽스처가 없어 실행 안 함).
