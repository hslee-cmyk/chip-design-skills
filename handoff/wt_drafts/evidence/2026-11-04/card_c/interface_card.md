# XRUN-F1 card C (평가 예산 상한) interface card (card id `20261103-xrunf1c`)

- 작성 2026-11-04. 커밋 안 함, 독립 검증 전. **card base = GL-1·IT-1 + IT-2·EO-1 범위 4를 포함한 master**(오케스트레이터가 sha를 적어 준다).
- design 근거: 40 §2.4.5 fail-closed (5)·§2.4.14 (1)~(9) C 행(v1.16.3, DF-1~DF-6). 사용자 결정 X-8·X-15·X-16·X-17.
- **test 작성 주체는 소스를 보지 않고 이 문서만 쓴다.** 경로 접두 `E/` = `skills/analog-gmid-design/gmid_engine/`.

## 1. 정의

- n_θ = `len(sctx.domain.variables)`. R = 2 × n_θ.
- 선언 실행(`sctx.eval_budget_source == "declared"`): 탐색 예산 = E_B = `sctx.eval_budget`, E_total = E_B + R.
- 유도 실행(`settings.eval_budget` None): D = ⌊`front_budget_s` / 평가 시간 중앙값⌋(`EvalBudget(front_budget_s, times).limit()`), E_total = D, 탐색 예산 = D − R. 유도 뒤 `sctx.eval_budget` = D.
- 커널 평가 수 = `sctx.counters["kernel_calls"]`. 평가 시간 = `sctx.eval_times`(목록).

## 2. 공개 계약

### C1. `search_ceiling` (`gmid_engine.search.search_ceiling`)

```text
search_ceiling(sctx, *, final=False) -> int | None     # 탐색 예산. 유도 전이면 None
```

- 선언: E_B 그대로. 작은 E_B도 거부 없음.
- `eval_budget` None, 평가 시간 < n_θ + 1개, `final=False`: None, 상태 불변.
- `eval_budget` None, 평가 시간 ≥ n_θ + 1개: **첫 n_θ + 1개**로 D를 내(더 많아도 같은 값) `sctx.eval_budget` = D, `sctx.eval_budget_source` = `derived_once:floor(B/median_t_eval)@n_evals=<그 호출 때 평가 수>`.
- 그 전이 호출: `kernel_calls` ≥ D − R → `ValueError`(메시지에 `time_budget_below_search_reserve`). = D − R − 1 → 통과, 반환 D − R.
- 전이 뒤 호출: `kernel_calls` > 탐색 예산 → `RuntimeError`. = 탐색 예산은 정상.
- `final=True`: `eval_budget` None이고 평가 시간 ≥ 1개면 그 전부로 유도. `kernel_calls` = D − R 통과, + 1 → `ValueError`. 평가 시간 0개면 None.

### C2. `search_stop` (`gmid_engine.search.search_stop`)

```text
search_stop(sctx) -> str | None     # "eval_budget" | "wall_budget" | None
```

- `kernel_calls` ≥ 탐색 예산 → `"eval_budget"`. 탐색 예산 = `search_ceiling` 값. `sctx.deadline` 지남 → `"wall_budget"`. 그 밖 None. 유도 전 호출은 C1 전이를 일으킬 수 있다.

### C3. `gate_reserve`·`e_total` (`gmid_engine.search._helpers_ceiling`)

```text
gate_reserve(sctx) -> int      # R
e_total(sctx) -> int | None    # 선언 E_B + R, 유도 D, eval_budget None이면 None
```

### C4. `fd_jacobian` (`gmid_engine.search.fd_jacobian`)

```text
fd_jacobian(sctx, variables, x, base, cells, to_theta, origin, skip=frozenset(), *, ceiling) -> tuple[(EvalResult | None, 스텝)]
class FdBudgetShortfall(Exception)     # 속성 needed, remaining. InfeasibleSizingError 하위 아님
```

- `ceiling` 필수(빠지면 `TypeError`). None = 확인 없음.
- 상계 = 평가할 열 수 × 2. 평가할 열에서 `skip`·스텝 0·`None`인 열을 뺀다. 남은 한도 = `ceiling` − `kernel_calls`.
- 남은 한도 = 상계 → 평상 실행. = 상계 − 1 → `evaluate` 호출 0, `FdBudgetShortfall(needed=상계, remaining=남은 한도)`.
- 묶음 시작 뒤에는 멈추지 않는다. 열 평가 규칙은 그대로.

### C5. 층 0·외층(`layer0_center`·`slsqp_outer`)

- 단일 평가: `kernel_calls` = 탐색 예산 − 1이면 평가, = 탐색 예산이면 평가 안 함, 정지 사유 `eval_budget`. 대상: 최대-최소 점, 수리, Halton 시험, 출발 사다리 칸(`start_status` = `eval_budget`), 외층 점.
- 반복 중 `FdBudgetShortfall`: 정지 사유 `eval_budget`, `aborts`에 `eval_budget`, 수락점 중 best.
- 첫 스텝 `FdBudgetShortfall`: 반복 0, 재시작 0, 정지 사유 `eval_budget`, `aborts` == (`eval_budget`,). 외층 best = c ≥ 0이면 시작점, 아니면 None. 층 0 best = 시작점 항목.
- 호출 전후 `kernel_calls` ≤ 탐색 예산.
- 관찰 지점 그대로: `layer0_center.scipy_minimize` 모듈 전역 이름.

### C6. 그 밖 탐색 자리

- `l_bin_search.polish_l_cells`: 탐색 예산에 닿으면 평가 안 함, 반환 정지 사유 = `search_stop` 값 또는 `"converged"`. 반환 모양 그대로.
- `eps_sweep`: ε 점 수 n_ε = ⌊(탐색 예산 − E_fixed)/e_ε⌋, 해상도 기록 칸 이름 `E_B` 그대로, 값 = `search_ceiling` 값.
- `residual_probe`: 정지는 `search_stop` 기준.
- `start_points`: 층 0 시작점 재확인은 예산에 닿아도 평가 캐시 적중(커널 0)으로 읽는다. 주어진 시작점(`given`)은 예산에 닿으면 그 뒤 후보를 평가하지 않고 기록 `starts`에 `status` = `eval_budget`.
- `kernel.evaluate`: `eval_times`만 기록. `sctx.eval_budget`·`eval_budget_source` 불변.

### C7. 감도 게이트(`gate_run.run_sensitivity_gate`)

- 묶음 `ceiling` = `e_total(sctx)`. `FdBudgetShortfall`을 잡지 않는다(주입하면 실행이 그 예외로 끝남).
- 게이트 시작 뒤 `search_ceiling`·`search_stop` 호출 0.

### C8. `find_front`

- 게이트 진입 때 `kernel_calls` ≤ 탐색 예산. 게이트 안 커널 평가 수 ≤ R.
- front 점이 있으면 탐색 예산을 다 써도 게이트가 돈다(`not_run` 없음).
- `sweep_front` 뒤 게이트 전에 `search_ceiling(sctx, final=True)` 한 번.
- 끝에서 `kernel_calls` > E_total → `RuntimeError`.
- 진입에서 `donors.open_bound(...)`, 끝 확인 뒤 `donors.close_bound()`.
- 결과 JSON 칸 변경 0, perf 키 22개 그대로. `perf.eval_budget` = 선언 E_B / 유도 D. `perf.block_index_bound` = `donors.index_bound(e_total(sctx))`, 선언 실행에서 `len(perf.blocks) × (E_total + 1)`과 같음, E_total None이면 null.
- 관찰 지점 그대로: `find_front` 모듈의 전역 이름 `layer0_start`·`sweep_front`·`run_sensitivity_gate`. notes `l_search`, runs 줄 `env_fp` 그대로.

### C9. `S3Index` (`open_run()`으로만 얻는다, 규칙 M)

```text
donors.open_bound(total_of) -> None    # total_of: 인자 없는 호출 가능 객체, E_total 또는 None
donors.close_bound() -> None
donors.index_bound(total) -> int       # (등록된 서로 다른 (블록, 분할) 수) × (total + 1)
```

- 열린 동안 등록(`register`·`register_failure`) 직후 `entry_count()` > `index_bound(total_of())`면 `RuntimeError`. 같은 값이면 통과.
- `total_of()`가 None이면 검사 없음. 정해진 뒤 첫 등록에서 잰다.
- 열기 전·닫은 뒤 등록은 검사 없음. 닫기 전 두 번째 `open_bound` → `ValueError`.
- `open_run()`·`S3Index()` 인자 없음 그대로. `Donors` 추상 메서드 그대로 넷.

### C10. 없어지는 이름

`E/search/`의 `_budget_stop`, `find_front._e_total`, `kernel.py`의 `EvalBudget` import. `EvalBudget` 클래스 자체와 `gmid_engine.search` export는 남는다.

### C11. 단언 금지

`S3Index` 안쪽 자료 구조, `ValueError`·`RuntimeError` 메시지 전문(사유 이름 포함 여부만), `eval_budget_source`의 `n_evals` 값(유도 시점이 늦어질 수 있다), 파일 내부 신호 `_Abort`.

## 3. 신규 시그니처 (부재 red는 card 이유로 센다, 단 아래 3.1 red 자리 별도)

`search_ceiling`, `search_stop`, `gate_reserve`, `e_total`, `FdBudgetShortfall`, `fd_jacobian(..., *, ceiling)`, `S3Index.open_bound`·`close_bound`·`index_bound`, 사유 `time_budget_below_search_reserve`.

### 3.1 test 목록

oracle: 구성으로 정답이 정해진 합성 입력. 경계값은 1절 정의에서 손으로 낸다. 피검 함수 호출로 기대값을 만들지 않는다. 가짜 `sctx`는 이 문서의 칸만 쓴다. 평가 시간은 test가 정한다.

| id | 위치 | 내용 | 계약 | base 결과 |
|---|---|---|---|---|
| C-T1 | `tests/search/test_search_ceiling.py`(신규) | 선언 E_B 그대로(작은 값 포함), 유도 전 None, n_θ + 1개 이상이면 첫 n_θ + 1개로 D(더 많아도 같음), source 형식(`n_evals` 값 제외) | C1 | red(부재) |
| C-T2 | 같은 파일 | 전이 경계: `kernel_calls` = 탐색 예산 → `ValueError`, − 1 → 통과. `final=True`: = D − R 통과, + 1 `ValueError`, 평가 시간 0개 None. 전이 뒤 + 1(주입) `RuntimeError`, = 정상 | C1 | red(부재) |
| C-T3 | `tests/search/test_search_stop.py`(신규) | `eval_budget`·`wall_budget`·None, 경계 −1/0 | C2 | red(부재) |
| C-T4 | `tests/search/test__helpers_ceiling.py`(신규) | `gate_reserve`, `e_total` 선언·유도·None | C3 | red(부재) |
| C-T5 | `tests/search/test_fd_jacobian.py` | 경계: 남은 = 상계 실행, = 상계 − 1 평가 0·`needed`·`remaining` 값, `ceiling=None` 확인 없음, 빠짐 `TypeError`. `skip`·스텝 0·None 열은 상계에서 제외. 기존 8곳·`test_layer0_center.py` 1곳은 `ceiling=None`을 넘긴다 | C4 | red(`TypeError`만의 실패는 신규 인자 이유) |
| C-T6 | `tests/search/test_layer0_center.py`·`test_slsqp_outer.py` | 반복 중 shortfall: 정지 사유·`aborts`. 첫 스텝 shortfall: 반복 0·best. `kernel_calls` ≤ 탐색 예산. 사다리 칸 예산 도달 평가 0·`start_status` | C5 | red |
| C-T7 | `tests/search/test_start_points.py` | `given` 도달 평가 안 함·`status`, 층 0 재확인은 도달해도 커널 0 | C6 | red |
| C-T8 | `tests/search/test_l_bin_search.py`·`test_eps_sweep.py`·`test_residual_probe.py` | 탐색 예산으로 정지·계획, 유도 실행에서 칸 `E_B` = D − R | C6 | red |
| C-T9 | `tests/search/test_kernel.py` | `evaluate`가 `eval_budget`·source를 바꾸지 않음(유도 실행, 평가 n_θ + 2회) | C6 | red(단언 실패) |
| C-T10 | `tests/search/test_gate_run.py` | 게이트 `ceiling` = E_total(인자 관찰), shortfall 주입 시 예외 전파, 게이트 안 `search_ceiling`·`search_stop` 호출 0(감싸 계수) | C7 | red |
| C-T11 | `tests/search/test_find_front.py` | **red 핵심**: `run_sensitivity_gate` 전역 이름을 감싸 진입 때 `kernel_calls` 기록, 탐색 묶음이 예산을 넘는 합성 입력에서 ≤ 탐색 예산. 탐색이 예산을 다 써도 게이트 실행. 끝 확인 위반 `RuntimeError`(주입). 평가 n_θ 이하 실행의 게이트 전 유도. `perf.block_index_bound` 식 | C8 | red(단언 실패) |
| C-T12 | `tests/search/test_s3_index.py` | 상한 정확히 = 통과, + 1 `RuntimeError`, total None 무검사 뒤 첫 등록 검사, 열기 밖 무검사, 두 번째 열기 `ValueError`, `index_bound` 값, 실패 등록도 계수 | C9 | red(부재) |
| C-T13 | `tests/search/test_find_front.py` | 무동작: E_B를 넉넉히 선언한 합성 실행에서 `eval_budget` 사유 0·shortfall 0, 궤적(θ·`seq`) 동일 쌍 비교 | C8 | green 유지 |
| C-T14 | `tests/integration/test_g10_no_recompute_9circuits.py` | 게이트 진입 단언·`kernel_calls` ≤ E_total 추가, 유도 실행 1회로 이상. 회로 구분은 오케스트레이터가 넘기는 B-2 결과 파일에 맞춘다(지금 단언 `len(CIRCUITS) == 9`는 13과 맞지 않음). 13회로 판정은 LA-1 측정 시점 | C8 | slow, B-2 뒤 |

### 3.2 이름 규칙

- 새 test 함수 접두: `test_search_ceiling_…`, `test_search_stop_…`, `test_gate_reserve_…`, `test_e_total_…`, `test_fd_shortfall_…`, `test_open_bound_…`, `test_gate_entry_budget_…`. 지역 변수 `e_total`이 `test_find_front.py:107`에 있다.
- 새 이름은 `test_ic`로 시작하지 않고 `ic1`·`ic2`·`ic9`·`ic10`·`rule_g`·`rule_k_`·`g10`을 담지 않는다(`-k` 식 충돌, card B 3.3 목록). C-T14만 기존 g10 파일 안에 둔다. 작성 뒤 `--collect-only -k <각 식>` 수를 base와 함께 보고.
- 파일 이름 `test__helpers_ceiling.py`는 규칙 H 꼴(`test__helpers_*` 선례).

## 4. 판정 측정 (audit)

격리 복제본에서만 잰다. 무거운 실행은 회로마다 새 프로세스, 순차, 결과는 케이스마다 append.

| # | 측정 | 합격 |
|---|---|---|
| C-1 | red-green: base + 새 test. C-T1~C-T12가 red, C-T11은 **assertion 실패**. head 전부 통과 | 충족 |
| C-2 | 문언 grep(spec card '문언 grep 0') | 범위 안 0 |
| C-3 | 전체 test 체계 + `tests/structure`. base에 실패가 남으면 목록을 올리고 판정을 멈춘다 | 전체 0 failed, 구조 위반 0 |
| C-4 | N6.3 넷(G 확장 lint·값 타입 위치·소유표·G-10) + 같은 입력 재계산 0 | 통과 |
| C-5 | 연기 시험(spec card, 선택·결과 기록). 예외 또는 직전에 없던 정지 사유면 병합 금지·보고 | 예외 0 |
| C-6 | 결정성: 같은 입력 두 번 비트 동일(`run_id`·시간 칸 제외, 제외 이유 기록) | 동일 |
| C-7 | graph 정본 추가 점검: 새 필드 0, `S3Index`에 E_total 값 칸 0(코드 리뷰), `eval_budget` 칸 재판정 | 위반 0 |
| C-8 | design ↔ 구현 gap, 42 D-XR6 | Major 0 |
| 보류 | 13회로 변화표·`kernel_calls` ≤ E_total 전수 = LA-1 측정 시점. SPICE = OP-5·CL-1. 판정 기록 '미완료(보류 다리…)' | 통과로 세지 않음 |
