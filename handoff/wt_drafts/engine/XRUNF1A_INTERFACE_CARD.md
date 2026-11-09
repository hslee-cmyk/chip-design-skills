# XRUN-F1 card A (RT + W) interface card 초안 (card id `xrunf1a`)

- 작성: 2026-10-15. 개정 2026-10-16(NFR-4 card 2 병합본 ebd7b3c 재측정, design cfe2e31 J-4 보완 반영). 읽기 전용 실측과 초안만 담았다. 엔진·test·git 브랜치는 고치지 않았다.
- **card base = `6be811b(NFR-4 card 2 병합 master, gmid_engine/ = ebd7b3c, 차이는 assets/technique 원문뿐)`**(NFR-4 card 2 병합 뒤 master). 재측정은 `wt/nfr4c2-integ` HEAD `ebd7b3c`에서 읽기 전용으로 했다(`wt/_scratch_xrunf1a_card/recheck_ebd7b3c.md`).
- design 근거: 40 §2.4.6 '첫 평가 버림 제거'(414~429행), §2.4.14 (2) 802행~, (5) 859행~, (6) 869~876행. 사용자 결정 X-1·X-4·X-6·X-14.
- **test 작성 주체는 소스를 보지 않고 이 문서(2·3절)만 쓴다.** 옛 `[J-n]` 미정 칸은 모두 결정됐다(J-1·J-4·J-5 = design, J-2·J-3·J-6·J-7 = 오케스트레이터 판단, 끝 절).
- 경로 접두 `E/` = `skills/analog-gmid-design/gmid_engine/`.

---

## 2. interface card (공개 계약)

### C1. `ThetaCoords` (`gmid_engine.search.theta_coords`, 새 파일)

```text
ThetaCoords.start(variables, theta) -> ThetaCoords          # frozen dataclass, classmethod
    variables = Variable(component, log, lo, hi) 의 순서 있는 묶음(gmid_engine.search.search_values.Variable)
    theta     = 시작 θ 전체 사전 {component: float}
    다른 인자는 없다: clip=... 같은 키워드를 주면 TypeError(X-14).
coords.to_theta(x) -> dict                                  # x = 변수 순서의 좌표(리스트·tuple·numpy 배열)
```

- 시작 좌표 x0ᵢ = `math.log(θᵢ)`(log 변수) 또는 θᵢ(그 밖). **자르지 않는다**(변수 bounds 밖이어도 그대로).
- `to_theta(x)`: 변수 i마다 v = `float(x[i])`. v == x0ᵢ(float 정확 일치)면 θᵢ 원값(비트 그대로), 아니면 log 변수는 `math.exp(v)`, 아니면 v. 변수 밖 성분은 `theta`의 값 그대로. 반환은 호출마다 새 dict(키 = `theta`의 키 전부).
- 성질: `to_theta(x0)`는 `theta`와 성분마다 비트 동일. 좌표 하나만 바꾼 x의 나머지 성분은 `theta`와 비트 동일.
- 공개면(J-2 판단): `start(variables, theta)`, `to_theta(x)`, 읽기 전용 칸 `x0`(tuple, 변수 순서). `gmid_engine.search`가 `ThetaCoords`를 재수출한다(모듈 경로 `gmid_engine.search.theta_coords`도 유효). 다른 칸 이름은 계약이 아니다. test는 x0 기대값을 `math.log`로 따로 만들어 `coords.x0`와 비교할 수 있다.

### C2. 세 경로의 좌표 규칙

| 경로(공개 진입) | 쓰는 variables | 시작 θ | 풀이·FD에 들어가는 시작 좌표 | 좌표 → θ |
|---|---|---|---|---|
| 외층 `gmid_engine.search.solve_eps(sctx, start, minimize, eps, origin)` | 탐색 변수 + 시작 칸이 구간인 MOS의 L(정준 순서, 1변수 노드 writer ln_idu 하한 조정 뒤) | `start.theta` + 칸이 한 점인 L의 고정값 | clip(x0ᵢ; loᵢ, hiᵢ) | clip(xᵢ; loᵢ, hiᵢ) 뒤 `to_theta` |
| 층 0 `gmid_engine.search.layer0_start(sctx, origin=())` 안 최대-최소 | 층 0 변수(하한 조정 뒤) | 층 0 출발점 θ(그 출발점의 첫 평가 결과 θ와 같은 점) | clip(x0ᵢ) | clip(xᵢ) 뒤 `to_theta` |
| 감도 게이트 `gmid_engine.search.gate_run.run_sensitivity_gate(sctx, base, origin=())` | `sctx.domain.variables`(조정 없음) | `dict(base.theta)` | x0 그대로(**자르지 않음**) | `to_theta` 그대로 |

- 결과(세 경로 공통): 시작 좌표가 상자 안이면 시작 좌표에서 만든 θ는 시작 θ와 변수 성분마다 비트 동일. 외층·층 0에서 시작 좌표가 상자 밖이면 그 성분은 `math.exp(clip 좌표)`(log 변수)로 원값이 아니다(as-built 외층과 같다). 감도 게이트는 상자 밖이어도 x0 = `math.log(θ)` 그대로이고 그 성분은 원값이다.
- 세 경로는 `ThetaCoords.start`로 좌표를 만들고 θ는 `ThetaCoords.to_theta`로 만든다(사본 없음).
- **관찰 지점(J-3 판단 -- code 쪽이 이름·서명·호출 방식을 바꾸지 않는 계약)**:
  - 모듈 속성 `fd_jacobian`: `gmid_engine.search.layer0_center`, `gmid_engine.search.slsqp_outer`, `gmid_engine.search.gate_run` 세 모듈이 이 이름으로 `fd_jacobian(sctx, variables, x, base, cells, to_theta, origin, skip=frozenset())`을 부른다. 시작점 FD에서는 x = 시작 좌표(위 표), base = 시작점 평가 결과.
  - 주의(사실): `gmid_engine.search.fd_jacobian`은 같은 이름의 **함수**다(패키지가 재수출해 모듈을 가린다). 모듈 객체는 `importlib.import_module("gmid_engine.search.fd_jacobian")`로 얻는다.
  - 모듈 속성 `size_and_seal`: `gmid_engine.search.kernel`이 커널 본체를 이 이름으로 부른다(커널 평가 1회 = 호출 1회).
  - 선례: 기존 `tests/search/test_gate_run.py`가 `gate_run.fd_jacobian`을 바꿔 끼운다. card 1 J-5가 `layer0_center.evaluate`를 공개 교체 지점으로 정했다(그대로 유효).
  - NFR-4가 정한 관찰 지점(그대로 유효, card A가 바꾸지 않음): 모듈 속성 `gmid_engine.search.layer0_center.scipy_minimize`(층 0 최대-최소가 이 이름으로 부름), `gmid_engine.search.find_front`의 모듈 속성 `layer0_start`·`sweep_front`, `gmid_engine.core.blas_env.loaded_blas_modules`.

### C3. `LutMemo` 계수 상태 (`gmid_engine.lut.LutMemo`)

```text
LutMemo.counting(lut, n_theta, *, table_cache=None) -> LutMemo   # classmethod, 신규. None = 생성자와 같은 뜻(TableCache.default())
memo.open_count() -> None      # 창 열기
memo.fix_bound() -> None       # 창 닫기 + 상한 고정
memo.bound_state -> str        # 읽기 전용 속성: "counting" | "window_open" | "fixed"
LutMemo.from_sweep, gmid_engine.lut.sweep_memo                # 없다(삭제)
BoundedLRU.adopt(key, value) -> None                          # gmid_engine.core, 신규(아래 C3b)
```

- `counting`이 만든 memo는 **계수 상태**(`bound_state == "counting"`)로 시작한다: 영역 point·curve·root는 상한 없이 값을 모은다(같은 키는 한 번만 계산). derived 영역은 처음부터 상한 = `len(lut.slice_map) * len(DERIVED_TABLES)`(계수 대상 아님).
- U_r(영역 r ∈ {point, curve, root}) = `open_count()`부터 `fix_bound()`까지 조회한 서로 다른 키 수. 창 열기 전 조회는 값을 모으되 U에 세지 않는다. 창 안 조회가 창 전에 모은 키를 다시 부르면(적중) 그 키도 U에 든다.
  - 키 = `(lut.fp, fn_name) + tuple(key)`(`lookup`의 키). '서로 다름'의 동치 = `BoundedLRU`와 같은 `canonical_key`(0.0과 −0.0은 다른 키, NaN은 같은 내용이면 같은 키, 1·1.0·True는 서로 다른 키).
  - 창 안에서 `compute()`가 예외로 끝난 조회는 U_r에 넣지 않는다(계수 상태 `misses`에는 센다).
- 상태 전이는 한 방향뿐: `"counting"` → `open_count()` → `"window_open"` → `fix_bound()` → `"fixed"`. 그 밖의 호출 -- 창 없이 `fix_bound`, 두 번째 `open_count`, `"fixed"` 상태에서 두 메서드 -- 는 모두 `ValueError`. `LutMemo(...)` 생성자 memo는 처음부터 `"fixed"`이고 두 메서드 모두 `ValueError`(고정된 계수 memo와 같다).
- `fix_bound()`: 영역 r 상한 = `(n_theta + 1) * U_r`. U_r = 0이면 그 영역은 memo하지 않는다(저장 없이 매번 계산, `stats()` capacity 0). 그 밖은 상한 LRU를 만들어 모은 항목을 **마지막 접근 순서**(오래된 것부터)로 `BoundedLRU.adopt`로 옮긴다. 모은 항목이 상한보다 많으면 가장 오래 접근하지 않은 것부터 퇴출되고, 그 수는 그 영역 `stats().evictions`에 든다. 고정 뒤 동작은 생성자 memo와 같다(상한 LRU, 퇴출 키 재계산은 `recomputes_after_eviction`).
- `stats()`: 계수 상태(`"counting"`·`"window_open"`)의 point·curve·root 영역 = `LruStats(capacity=None, size=모은 항목 수, hits, misses, evictions=0, recomputes_after_eviction=0)`. 고정 뒤 = `BoundedLRU` 계수(capacity·size·evictions·recomputes_after_eviction)에 계수 상태 동안의 hits·misses를 더한 값. 옮기기는 hits·misses를 바꾸지 않는다 -- 고정 직후 같은 원 key 조회는 hit(계산 0, `misses` 불변). derived 영역은 처음부터 `BoundedLRU` 그대로.
- 모든 조회는 `LutMemo.lookup`(클래스 속성)을 거친다(계수 상태 포함). 고정 단계의 항목 옮기기는 `LutMemo.lookup`을 부르지 않는다(design §2.4.6 '독립 계수' 행이 test에게 `LutMemo.lookup`을 클래스 수준에서 감싸 세게 하므로 따라오는 계약).
- 값: memo는 값을 바꾸지 않는다. 같은 인자의 조회 값은 계수 상태·고정 뒤·생성자 memo에서 같다(`is` 또는 비트 동일).

### C3b. `BoundedLRU.adopt` (`gmid_engine.core.BoundedLRU`, 부분 수정)

- `adopt(key, value)`: **원 key**를 받아 안에서 `lookup`과 같은 `canonical_key`를 적용해 넣는다. 그 뒤 같은 원 key의 `lookup`은 적중(계산 함수 안 부름). `hits`·`misses`를 바꾸지 않는다.
- 상한을 넘으면 `lookup`과 같은 규칙으로 가장 오래된 것을 퇴출하고 `evictions`에 세며 퇴출 키를 기록한다 -- 그 키를 나중에 `lookup`으로 다시 계산하면 `recomputes_after_eviction`이 센다.
- 기존 `BoundedLRU` 서명·`lookup`·`stats` 동작은 그대로.

### C4. `build_search_context` (서명 불변)

```text
gmid_engine.search.build_search_context(dc_ctx, spec, settings, archive_root, pdk_decl, lut_rule_decl, model_error=(), *, code_fp) -> SearchContext
```

- 이 호출 안에서 커널 평가는 **0**이다(`kernel.size_and_seal` 호출 0, 임시 컨텍스트 없음). 반환 직후 `sctx.counters["kernel_calls"] == 0`, `sctx.seq == 0`, `sctx.cache`는 비어 있다.
- 탐색 memo = `sctx.dc.lut.memo` = `LutMemo.counting(호출자 lut, n_θ, table_cache=호출자 memo의 table_cache)`. n_θ = `len(gmid_engine.search.layer0_center.centre_start(sctx)[0])`(상자 중심 변수 = 정의역 변수 + 구간인 L 칸 변수).
- 탐색 memo는 호출자 memo와 다른 객체이고, 호출자가 넘긴 `dc_ctx`(그 `lut`·memo)는 바꾸지 않는다. 호출자 memo의 상한 숫자는 탐색 memo 상한·탐색 결과에 영향이 없다.

### C5. `evaluate` 창 (서명 불변)

```text
gmid_engine.search.evaluate(sctx, theta, cells, parent=None, origin=(), geometry=None) -> EvalResult
```

- 커널을 부르는 평가(평가 캐시 적중·정의역 밖이 아닌 것)에서: 커널 호출 직전 `sctx.dc.lut.memo.bound_state == "counting"`이면 `open_count()`, `EvalResult`를 만든 직후(성공·후보 실패 모두) `"window_open"`이면 `fix_bound()`. 그래서 창은 그 컨텍스트의 **첫 커널 평가**에서만 열리고, 생성자 memo(`"fixed"`)로 도는 경로는 두 메서드를 부르지 않는다.
- 결과: 첫 커널 평가가 끝나면 탐색 memo 영역 r의 capacity = (n_θ + 1) × (그 평가 안에서 조회한 서로 다른 키 수). 평가 결과 값·키·`seq`·계수는 바뀌지 않는다.
- 사실(관찰용): `evaluate`가 커널 호출 전에 하는 일(요청 계수·키·캐시 확인·원뿔 행)은 LUT를 조회하지 않는다. 그래서 test가 `evaluate` 호출 하나 전체를 창으로 보아도 같다.

### C6. `find_front` `perf`

- 키 `lut_memo_bound` 추가: 탐색 memo `bound_state`가 `"fixed"`면 `"fixed"`(생성자 memo로 돈 탐색 포함), 첫 커널 평가 없이 끝났으면 `"unfixed_no_kernel_eval"`(예외 아님, 정상 결과).
- NFR-4가 넣은 결과 칸은 그대로: runs 줄 `env_fp`, notes `l_search` 한 줄(`perf` 키 아님).
- `perf` 키 집합(그리고 `runs.jsonl` 줄 `perf`) = 정확히 22개: `{requests, kernel_calls, hits, fail_hits, outside_domain, recompute_same_key, unique_keys, eval_time_median_s, wall_s, lut_memo_evictions, lut_memo_bound, block_calls, block_reuses, block_computes, block_recomputes_same_input, n_starts, n_solves, eval_budget, eval_budget_source, frozen_columns, stops_eval_budget, stops_wall_budget}`.

### C7. 바뀌지 않는 것

- 서명: `fd_jacobian(sctx, variables, x, base, cells, to_theta, origin, skip=frozenset())`, `solve_eps`, `layer0_start`, `run_sensitivity_gate`, `centre_start(sctx, rung=None)`, `evaluate`, `build_search_context`(키워드 전용 `code_fp` -- NFR-4 test N-T14가 단언), `find_front`, `LutMemo(lut, *, point, curve, root, table_cache=None)`, `LutMemo.lookup`·`lookup_persistent`·`stats`, `BoundedLRU` 생성자·`lookup`·`stats`.
- NFR-4 병합분: BLAS 재확인 다섯 지점(단계 A·`build_search_context`·`find_front`·`layer0_start`·`solve_eps` 진입)의 동작, `env_fp`·notes `l_search`, 층 0 끌어올림(BP1), L-b 정지 사유.
- 생성자 `LutMemo(...)`의 상한 0 → `ValueError`(as-built 그대로).
- S0 수준 계산(단계 A·B·탐색 컨텍스트 S0 블록) 값: `E/tests/integration/fixtures/u17_1b_s0_baseline.json` 지문 그대로.
- 감도 게이트의 '상자 밖 기준점' 동작(X-14: 자르지 않음, '검사 못 함' 보고는 후속).

### C8. 단언 금지 (계약 밖 -- test가 기대값으로 쓰지 않는다)

`ThetaCoords`의 `x0` 밖 칸 이름, log 변수 θ ≤ 0의 동작, `adopt`·`counting` 안쪽 자료 구조.

---

## 3. test 목록 (id / 위치 / 내용 / 계약 / oracle / base 결과)

위치는 제안이다(파일 분할 규칙 H: `tests/<pkg>/test_<file>.py` 1:1). 정확한 범위는 test 작성 주체가 정한다. oracle 종류: (식) design 식, (손) 손계산·손으로 만든 조회 순서, (비교) 같은 함수 두 출력 비교, (독립) 피검 계수를 읽지 않는 독립 계수, (Py) Python `math`의 값.

### 3.1 새 test

| id | 위치 | 내용 | 계약 | oracle | base(`6be811b(NFR-4 card 2 병합 master, gmid_engine/ = ebd7b3c, 차이는 assets/technique 원문뿐)`) 결과 |
|---|---|---|---|---|---|
| A-T1 | `tests/search/test_theta_coords.py`(신규) | 손으로 만든 `Variable` 셋(log 둘·선형 하나)과 θ(변수 밖 성분 하나 포함). `to_theta(x0)`가 θ와 성분마다 비트 동일(`float.hex` 비교). θ는 `math.exp(math.log(θ)) != θ`인 값을 고르고 test 안에서 그 전제를 먼저 단언(공허 방지) | C1 | (Py)+(식): x0 = `math.log`로 test가 만듦, 기대 = θ 원값 | red(모듈 없음) |
| A-T2 | 같은 파일 | 좌표 하나만 x0ᵢ + δ로 바꾼 x: 그 성분 = `math.exp(x0ᵢ + δ)`(log) 또는 x0ᵢ + δ(선형), 나머지 비트 동일, 변수 밖 성분 그대로 | C1 | (식)+(Py) | red |
| A-T3 | 같은 파일 | 변수 bounds 밖 θ: x0이 잘리지 않는다 -- `to_theta(x0)` = θ 원값, test가 `math.log(θ)`로 만든 x0 그대로 넘겨도 원값 | C1 | (Py) | red |
| A-T4 | 같은 파일 | `ThetaCoords.start(variables, theta, clip=True)` → `TypeError` | C1 | (식) X-14 | red |
| A-T5 | `tests/search/test_layer0_center.py` | 실제 회로 케이스로 `layer0_start` 실행, `layer0_center.fd_jacobian`을 감싸 첫 호출의 (variables, x, base, to_theta)를 기록. `to_theta(x)`의 변수 성분이 `dict(base.theta)`와 비트 동일. 전제(공허 방지): 그 변수 중 log 변수 θ 하나 이상이 `math.exp(math.log(θ)) != θ`이고 그 성분의 x가 상자 안 -- 전제가 안 서면 test 주체가 다른 케이스를 고른다. **ThetaCoords를 import하지 않는다**(base red 사유가 비트 단언이어야 함) | C2, J-3 관찰 지점 | (비교): 같은 엔진이 낸 기준점 θ와 변환 출력 비교 + (Py) 전제 | **red(비트 단언)** -- design (iii) 요구 |
| A-T6 | `tests/search/test_gate_run.py` | 손으로 만든 기준 결과(θ에 log 변수 하나 이상, 그 중 하나는 `sctx.domain.variables` bounds 밖)로 `run_sensitivity_gate` 실행, `gate_run.fd_jacobian`을 바꿔 끼워 (x, to_theta) 기록: x[i] == `math.log(θᵢ)`(자르지 않음, bounds 밖 성분 포함), `to_theta(x)`가 θ와 비트 동일. ThetaCoords import 없음 | C2, J-3 관찰 지점 | (Py)+(비교) | **red(비트 단언)** -- design (iii) 요구. x 자체는 base도 같다(자르지 않음) |
| A-T7 | `tests/search/test_slsqp_outer.py` | 외층: 시작 θ가 상자 안이면 첫 `fd_jacobian` 호출의 `to_theta(x)`가 시작 θ와 비트 동일. 상자 밖 시작(선언 시작점 θ 한 성분을 bounds 밖으로)이면 그 성분 = `math.exp(min(max(math.log θ, lo), hi))`(원값 아님) | C2 | (Py)+(식) | green(as-built 외층이 이미 원값 보존 -- base red 요구 없음, design (5)) |
| A-T8 | `tests/search/test_theta_coords.py` 또는 경로별 파일 | 정본 사용: `ThetaCoords.start`를 클래스 수준에서 감싸(원래 것을 부르는 wrapper) 세 경로가 각각 한 번 이상 부르고, 그 경로의 FD에 들어간 θ가 감싼 객체의 `to_theta` 출력과 같음 | C2 | (비교) | red(모듈 없음 -- 허용) |
| A-T9 | `tests/search/test_search_context.py` | `build_search_context` 동안 `kernel.size_and_seal`을 감싸 센 호출 = 0. 반환 뒤 `kernel_calls` 0·`seq` 0·`cache` 빔. 전제: 같은 케이스의 상자 중심이 원뿔 안(base가 평가를 했을 조건 -- test 주체가 케이스로 보장, 감사가 base에서 red 확인) | C4, J-3 관찰 지점 | (독립) | **red**(base는 임시 컨텍스트에서 1회) -- `kernel_calls`·`seq` 단언만으로는 base도 0이라 red가 아니다 |
| A-T10 | `tests/search/test_search_context.py` | 독립 계수: build 뒤 test가 `LutMemo.lookup`을 클래스 수준에서 감싸(영역, `(lut.fp, fn_name) + tuple(key)`)를 기록, `evaluate(sctx, θ, cells)` 한 번(첫 커널 평가 -- 원뿔 안 θ, 예: `centre_start(sctx)`의 θ·cells)의 호출 구간만 센 영역별 서로 다른 키 수 U_r. n_θ = `len(centre_start(sctx)[0])`(evaluate 뒤에 재도 된다). 단언: 영역 point·curve·root `stats()` capacity = (n_θ + 1) × U_r. 공허 방지: 창 안 기록 > 0 | C3, C4, C5 | (독립)+(식) | 같을 수 있음(base는 같은 중심점을 미리 평가했다) -- red 요구 없음 |
| A-T11 | `tests/search/test_search_context.py` | 첫 커널 평가 뒤 `sctx.dc.lut.memo.open_count()`·`fix_bound()` 각각 `ValueError` | C3 | (식) | red(속성 없음) |
| A-T12 | `tests/search/test_search_context.py` | 옮겨 온 성질(옛 `test_sweep_memo_wiring.py`): 탐색 memo ≠ 호출자 memo, 호출자 `dc_ctx.lut.memo` 그대로, 같은 입력의 탐색을 탐색 memo와 호출자 memo(상한 큰 생성자 memo로 바꿔 끼움)로 돌린 front·평가 결과 비트 동일, 호출자 상한 1과 4096 두 실행의 탐색 memo 상한·정의역·front·평가 결과 동일 | C4, C3 '값' | (비교) | green 가능(as-built도 성질을 지킴) |
| A-T13 | `tests/search/test_find_front.py` | `perf` 키 집합 정확히 22개(C6), 커널 평가가 있는 실행의 `lut_memo_bound == "fixed"`. (NFR-4 test `test_lb_stop_notes_line_exactly_once`가 쓰는 상수 `PERF_KEYS_C7`도 같은 22개로) | C6 | (식) | red(키 없음) |
| A-T14 | `tests/search/test_find_front.py` | 첫 커널 평가가 없는 실행(모든 출발 후보가 원뿔 밖 등 -- 만드는 방법은 test 주체)의 `lut_memo_bound == "unfixed_no_kernel_eval"`, 예외 없음 | C6 | (식) | red |
| A-T15 | `tests/lut/test_lut_memo.py` | toy LUT로 `LutMemo.counting(toy, n, table_cache=TableCache(None))`. 손으로 정한 순서: 창 전 키 a, b → `open_count` → b, c, c, d(영역 하나에서) → `fix_bound`: U = 3({b, c, d}), capacity = (n + 1)·3. 다른 영역은 창 안 조회 0 → capacity 0. `n_theta` 매개변수화(0 포함) | C3 | (손)+(식) | red(속성 없음) |
| A-T16 | `tests/lut/test_lut_memo.py` | 옮기는 순서·퇴출: n = 0이라 상한 = U인데 모은 항목이 더 많게 만든다(창 전 키 a 하나 + 창 안 키 U개, a는 창 안에서 다시 부르지 않음): 고정 뒤 `evictions` = 1, 이어서 a 조회 = miss 증분 1(재계산), 창 안 마지막 키 조회 = hit 증분 1. 창 안에서 다시 부른 창 전 키는 최근성이 갱신돼 남는다(별도 단언) | C3 | (손) | red |
| A-T17 | `tests/lut/test_lut_memo.py` | 값 불변: 같은 인자의 조회 값이 `counting` memo(고정 전·후)와 생성자 memo에서 같다. derived 영역 capacity = 슬라이스 수 × `len(DERIVED_TABLES)` | C3 | (비교)+(식) | red(속성 없음) |
| A-T19 | `tests/lut/test_lut_memo.py` | 상태·순서: `counting` memo `bound_state` = `"counting"` → `open_count` 뒤 `"window_open"` → `fix_bound` 뒤 `"fixed"`. `ValueError` 경우 각각: 창 없이 `fix_bound`, 두 번째 `open_count`, 고정 뒤 `open_count`·`fix_bound`, 생성자 memo(`bound_state == "fixed"`)의 `open_count`·`fix_bound` | C3 | (식) | red(속성 없음) |
| A-T20 | `tests/lut/test_lut_memo.py` | 계수 상태 `stats()`: point·curve·root capacity `None`, size = 모은 서로 다른 키 수(손계산), evictions 0. 고정 직후 같은 원 key 조회는 hit 증분 1·misses 증분 0(계산 함수 호출 0 -- test의 compute 계수). 고정 뒤 hits·misses = 계수 상태 동안 합 + 고정 뒤 증분(손계산). 키 동치: 0.0과 −0.0을 창 안에서 따로 조회하면 U에 2로 셈, 같은 NaN 두 번은 1. 창 안 compute 예외 조회는 U 제외(misses에는 셈) | C3 | (손)+(식) | red |
| A-T21 | `tests/core/test_bounded_lru.py`(기존 파일) | `adopt`: 원 key로 넣은 뒤 같은 원 key `lookup`이 적중(compute 호출 0), `hits`·`misses` 불변. canonical 동치 키(예 같은 내용 NaN)로도 적중. 상한 넘게 `adopt`하면 가장 오래된 것 퇴출·`evictions` 증가, 그 키를 `lookup`으로 다시 부르면 `recomputes_after_eviction` 1. 이름은 `test_bounded_lru_adopt_…`(`adopt` 기존 이름과 구분) | C3b | (손) | red(메서드 없음) |
| A-T18 | `tests/search/test_slsqp_outer.py:104` 주석 | 'x0 = exp(ln θ) 가 시작 θ 와 1 ulp 달라' 문장을 사실에 맞게 | -- | -- | -- |

### 3.2 삭제·고칠 test (실측)

| 파일 | 처리 | 비고 |
|---|---|---|
| `tests/lut/test_sweep_memo.py`(79줄) | 삭제(원본 삭제, 규칙 H) | `:73-79`(생성자 상한 0 → `ValueError`)는 `test_lut_memo.py:40-43`이 이미 덮는다 |
| `tests/search/test_sweep_memo_wiring.py`(134줄) | 삭제(원본 없음 = 고아, design (4)). 성질은 A-T10·A-T12로 | |
| `tests/lut/test_lut_memo.py:1`(docstring '`from_sweep` 상한 식'), `:46-53` `test_from_sweep_capacity` | 삭제·다시 씀(A-T15~A-T17·A-T19·A-T20) | `from_sweep`는 `tests/`도 grep 0 범위 |
| `tests/core/test_bounded_lru.py` | `adopt` test 추가(A-T21) | design (5) A 행 |
| `tests/search/test_find_front.py:19-24`, `:59-64` | 22개로(A-T13) | |
| 탐색 값을 고정한 단언 | test 주체가 grep으로 목록을 만들어 새 값으로 다시 쓴다(design (6)). 허용 폭 넓히기 금지. 후보(실측 grep, 확정 아님): `tests/search/test_layer0_center.py`, `test_kernel.py`, `test_find_front.py`, `test_slsqp_outer.py`, `test_eps_sweep.py`, `tests/convergence/test_converge_point.py`(`:135·165·195·225·284`). NFR-4 신규 후보: `tests/integration/test_layer0_boundary_rows.py`(slow 아님, 8회로 층 0 시작점의 `w_min` 경계 행 -- 층 0 최대-최소 결과라 RT 영향 가능), `tests/search/test_l_bin_search.py`의 `test_lb_stop_*`(커널 호출 수·예산 전제), `test_find_front.py`의 `test_lb_stop_notes_*`(front ≥ 1·stops ≥ 1 전제) | 새 값은 피검 코드 출력을 옮겨 적는 것이 아니라 독립 판정(A-5)이 확인한 값 변화 목록과 대조한다(J-7: base·head 같은 하네스) |

### 3.3 이름 규칙 (실측 충돌 확인)

- 0건 확인(ebd7b3c, 저장소 전체 docs 제외): `ThetaCoords`, `theta_coords`, `open_count`, `fix_bound`, `lut_memo_bound`, `unfixed_no_kernel_eval`, `bound_state`, `window_open`, `test_theta_coords`, `test_counting_memo`. `counting`은 `tests/pipeline/test_stage_a.py:517` 지역 함수 하나(무관).
- `adopt`는 이미 쓰인다(`CanonPointer.adopt`, test 이름 7개 이상) -- 새 test 이름은 `test_bounded_lru_adopt_…`로.
- 쓰이는 `-k` 식: `"test_ic"`, `"g10"`, `"ic11 or kvl_branch_residual"`, `"rule_g or design_value_location"`, `rule_k_`, `"duplicate_args or loop_invariant"`, `"ic1 or ic2 or ic9 or ic10 or shared_gate_net or kcl_residual"`, `"mna_assembly_count or mna_solve_count"`. 새 test 이름은 `test_ic`로 시작하지 않고 `g10`·`ic1`·`ic2`·`ic9`·`rule_g`·`rule_k_`를 담지 않는다. 작성 뒤 `pytest --collect-only -k <각 식>` 수집 수가 base와 같은지 보고한다.
- 권장 접두: `test_theta_coords_…`(A-T1~A-T4·A-T8), `test_counting_memo_…`(A-T15~A-T17·A-T19·A-T20), `test_bounded_lru_adopt_…`(A-T21).
- red 예상 목록(감사 A-3 대상)은 엔진 동작을 보는 test만이다. test 도구(마커 conftest·비교기·하네스) 자체를 시험하는 test를 새로 쓰면 base green이 정상이므로 red 예상에서 뺀다(nfr4c2 J-O2).

---

## 4. 판정 측정 (audit)

audit은 격리 복제본(`<W>/xrunf1a-audit`, base 비교용 base 복제본 따로)에서만 잰다. **9회로 측정 방법(모든 A-항목 공통)**: 회로마다 **새 프로세스**, 환경 = 허용 목록으로 새로 만든 dict(PATH·SYSTEMROOT·APPDATA·TEMP/TMP(회로별 빈 폴더)·`OPENBLAS_NUM_THREADS=1`(무해 -- 엔진이 import 때 1로 고정·확인)·`GMID_LUT_TABLE_CACHE_DIR`·`PYTHONDONTWRITEBYTECODE=1`·`PYTHONIOENCODING=utf-8`), **순차 실행**(무거운 실행은 한 번에 하나 -- 메모리), 평가 예산 **E_B 40 선언**(card 1 판정과 같음)·벽시계 정지 0이 되게 넉넉한 시간 예산, 결과는 회로마다 JSON 파일에 쓰고 진행은 append. 사슬 = 단계 A → B → 커널 컨텍스트 → 탐색 컨텍스트(빈 S3 루트) → `find_front([])`. 9회로 = `common_gate_amplifier`, `current_reuse_telescopic_ota`, `folded_cascode`, `ngcc_3stage_ff`(card 1 실측: 단계 A·B 상태 `review_needed`로 탐색 컨텍스트·`find_front` 없음 -- 보고서까지만), `nmcnr_amplifier`, `pushpull_follower_buffer`, `sf_pushpull_output_opamp`, `two_stage_ota`, `two_stage_ota_sf`. 재사용 후보: NFR-4 in-tree 하네스 `tests/integration/nfr4_run_dump.py`(회로별 새 프로세스, 층 0·sweep·`find_front` 기록, `find_front.layer0_start`·`sweep_front` 감쌈, perf 문자열 칸은 D 부류라 `lut_memo_bound`로 깨지지 않음)와 비교기 `nfr4_compare.py`, nfr4c2 감사 스크립트 `wt/_scratch_nfr4c2_audit/scripts/`(계측 추가 필요).

| # | 측정 | 방법 | 합격 |
|---|---|---|---|
| A-1 | 삭제 이름 grep 0 (i) | spec card 1.3.5 이름마다 그 범위에서 `git grep -nw`(history·design 제외). 범위 밖 남는 쓰임(`fd_jacobian` 인자 `to_theta`, `tests/search/conftest.py:459`, `u3-lut-pdk-record.md:129`)은 그대로인지 | 범위 안 0(`def to_theta`는 `E/search/` 중 `theta_coords.py` 밖) |
| A-2 | (ii) 커널 평가 0·고정 용량 | (a) 단위 test A-T9~A-T11 결과 (b) 9회로(탐색이 도는 8회로): 탐색 컨텍스트 생성 동안 `kernel.size_and_seal` 호출 수 = 0. `LutMemo.lookup` 클래스 수준 감쌈 + `kernel.evaluate`를 그 함수를 속성으로 가진 모든 `gmid_engine.search.*` 모듈에서 감싸, `kernel_calls`를 처음 늘린 `evaluate` 호출 구간을 창으로 영역별 서로 다른 키 수 U_r. n_θ = `find_front` 뒤 `len(centre_start(sctx)[0])`. 고정 용량 = 탐색 memo `stats()` capacity | 8/8 커널 0, capacity = (n_θ + 1)·U_r(세 영역), 공허 방지 U 합 > 0 |
| A-3 | (iii) 원값 보존 red-green | head에서 A-T1~A-T8 통과. base(`6be811b(NFR-4 card 2 병합 master, gmid_engine/ = ebd7b3c, 차이는 assets/technique 원문뿐)`) + 새 test: A-T5·A-T6은 **비트 단언 실패로** red(import 오류 아님 -- 실패 메시지·해시 기록), A-T7은 base green 허용 | head 전부 통과, A-T5·A-T6 base red(단언) |
| A-4 | 9회로 RT 관찰(보고만, J-6) | 세 모듈 `fd_jacobian` 감쌈: 호출마다 '`to_theta(x)` 변수 성분 == `base.theta` 성분'(비트) 일치 여부와 x가 상자 밖으로 잘린 성분 수를 센다. head·base 둘 다 | 보고만(기대: head 불일치 = 자른 성분이 있는 호출뿐) |
| A-5 | (iv) 기준선 재측정·값 변화 목록 | head·base 9회로 각 1회(위 방법, 같은 하네스·같은 환경 -- J-7 판단. card 1 판정 값은 쓰지 않는다: NFR-4 BP1로 base 궤적이 이미 바뀜). 비교 칸: front·pending·unmeasured 점(θ hex·목적), ε 풀이 기록(`failed_eps`·`resolution`), 층 0 결과(notes `layer0_*`), 시간 칸 뺀 `perf`, S3 evals·runs 줄(시간 칸 뺀 내용). 값 변화 목록 = (회로, 칸, 옛 값, 새 값). `run_id`·`code_fp`는 코드 변경으로 당연히 바뀌는 칸으로 따로 표시. 추가: `pytest gmid_engine/tests/integration/test_s0_layer_9circuits.py`(기준선 `u17_1b_s0_baseline.json` 대조 test 포함) | 목록 작성(변화는 X-4 범위 -- 판정에서 보고). S0 기준선은 diff 0(다르면 결함) |
| A-6 | 블록 재계산 계수(보고만) | `ComputeBlock.__call__` 클래스 수준 감쌈(엔진 코드 무변경)으로 9회로 실행 전체의 블록별 (calls, computes, recomputes_same_input) -- head. base 같은 계측 1회(J-7) | 보고만(card B 비교 자료, 판정 아님) |
| A-7 | 전체 suite·구조 | `python -m pytest -q gmid_engine/tests -p no:cacheprovider --run-slow` 한 번(명령 하나, 바깥 `OPENBLAS_NUM_THREADS` 미지정 -- 기본 실행은 conftest가 slow를 뺀다), `tests/structure` 위반 0, `-m structure_test_mapping`(규칙 H) 결과를 새 base와 비교(새 원본·새 test 1:1, `test_sweep_memo_wiring.py` 고아 해소. NFR-4가 test 파일을 넣었으므로 옛 base와 비교하지 않음) | 0 failed, 구조 위반 0, H = base 이하 |
| A-8 | 바뀌지 않아야 할 것 | `git diff base..head -- E/lut/table_cache.py E/core/compute_block.py E/core/blas_env.py` 0줄. `E/core/bounded_lru.py` diff는 `adopt` 추가(+ 그 docstring)만. `fd_jacobian` AST 인자 목록 그대로, `solve_eps`·`layer0_start`·`run_sensitivity_gate`·`build_search_context`·`evaluate`·`find_front` 서명 그대로. spec card 1.3.6 보존 계약(재확인 다섯 지점 호출 줄, `env_fp`·notes `l_search`, `scipy_minimize`·`layer0_start`·`sweep_front` 모듈 전역 호출, BP1, `_budget_stop` 3곳, search CONTRACT 432·481·513-514) 그대로, `tests/core/test_blas_env.py` 통과 | 0줄·같음 |
| A-9 | 이름 충돌 | 3.3 `-k` 식마다 `--collect-only` 수집 수 head = base + (이름 규칙상 0) | 같음 |
| A-10 | 실행 시간(보고만) | A-5 사슬 시간, base와 head를 같은 하네스로 대조(card 1 P1 224.6 s는 NFR-4 BP1 전 궤적이라 참고만) | 판정 아님 |
| A-11 | 공통 완료 조건 | design §10.4: `-k "rule_g or design_value_location"`, integration `-k g10`(있으면), §2.4.8 소유표 대조, gap-detector 일치율 ≥ 90 %, 42 D-XR1·D-XR2 | 통과 |

---

## 5. 공통 브리핑 (이 card의 code·test·audit agent 필독, 1쪽)

> spec card 2절과 같다. test agent는 이 문서 2·3절만 읽고 소스를 보지 않는다.

base = `6be811b(NFR-4 card 2 병합 master, gmid_engine/ = ebd7b3c, 차이는 assets/technique 원문뿐)`(NFR-4 card 2 병합 뒤 master). design: `docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md` §2.4.6('첫 평가 버림 제거', cfe2e31 J-4 보완 포함)·§2.4.14 (1)~(7)·§10.4·§11 XRUN-F1 행, `…42-gap-checklist.design.md` D-XR1·D-XR2. 계획: `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` NFR-2·U-91·U-94. 엔진: `skills/analog-gmid-design/gmid_engine/`. 사용자 결정 기록: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/user_decisions.md`(읽기만, X-1~X-19, N-1~N-6). card: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/engine/XRUNF1A_SPEC_CARD.md`(code·audit), `XRUNF1A_INTERFACE_CARD.md`(test는 이것만).

### 절대 규칙
1. **design 그대로 구현한다. as-built 결정 금지.** design에 없는 것을 정해야 하거나 design이 모순·불가능하면 그 자리에서 **멈추고 보고**한다. 범위 축소·대체 금지. card·끝 절 '오케스트레이터 판단'이 정한 것 밖은 손대지 않는다.
2. **graph 단일 정본(DEC-83)**: graph 밖 허용 저장소는 셋뿐 -- (a) LUT memo(디스크 LUT 파생표 캐시 포함, U-87), (b) S3 기록(출력)과 그 실행 안 메모리 캐시, (c) 실행 계수. 새 dict 캐시·객체 칸·사본·디스크 캐시 금지.
3. **계산값 재사용 = 실행 안에서**: 사용자 취지 "처음 topology를 실행할 때는 항상 계산하고 그 계산된 값이 나머지 최적화를 진행할 때 재사용". 벗어나는 판단은 멈추고 '원래 취지와 다름'으로 보고.
4. **틀린 구조는 전체 재작성**(범위 = design §2.4.14 (3) A 행), 옛 코드·CONTRACT 문장은 같은 변경에서 삭제, 만든 것은 반드시 배선.
5. **건드리지 않는 것**: card B·C·U17 ③ 범위(`_budget_stop` 3곳 합치기 포함), LUT 파생표 디스크 캐시, `ComputeBlock.code_hash`, 감도 게이트 clip(X-14), `fd_jacobian` 서명, NFR-4 병합분(spec card 1.3.6 보존 계약: 재확인 다섯 지점 호출, `env_fp`·notes `l_search`, `scipy_minimize`·`layer0_start`·`sweep_front` 모듈 전역 호출, BP1, search CONTRACT 432·481·513-514).
6. **상수 발명 금지**, **회로 이름·소자 이름 코드 금지**.
7. **파일 분할 규칙 A~I·K**, test 1:1(H): `search/theta_coords.py` ↔ `tests/search/test_theta_coords.py`, `core/bounded_lru.py` 수정 ↔ 기존 `tests/core/test_bounded_lru.py`에 `adopt` test, `lut/sweep_memo.py`와 `tests/lut/test_sweep_memo.py` 함께 삭제, 고아 `tests/search/test_sweep_memo_wiring.py` 삭제. `_module_map.py` 갱신(기계 검사 없음 -- 리뷰). `tests/structure` 위반 0.
8. **작성자 ≠ 검증자**: code agent는 test·기대값을 쓰지 않는다. test agent는 피검 코드를 불러 기대값을 만들지 않는다(oracle = design 식·손계산·같은 함수 두 출력 비교·독립 계수). 같은 커밋에서 코드와 기준을 함께 바꾸지 않는다. 기준 약화는 사용자 승인 사항.

### 실행 환경·git 가드
- python: `/c/Python314/python.exe`(bash `timeout` 래퍼 금지). 실행 위치 `<worktree>/skills/analog-gmid-design`, `python -m pytest -q gmid_engine/tests/<경로> -p no:cacheprovider`. BLAS 스레드는 엔진이 import 때 1로 고정·확인한다(conftest는 고정하지 않음). 기본 실행은 slow test를 빼고, 포함은 `--run-slow`.
- **무거운 실행은 한 번에 하나**(9회로·전체 suite 순차). 전체 suite는 끝에 한 번. 긴 실행은 결과를 파일에(`C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_xrunf1a_<role>/run.txt`, 케이스마다 append).
- git: 항상 `git -C <자기 worktree>`, 스크립트 `set -e`. 다른 worktree·master 금지, reset --hard·다른 브랜치 checkout·push·merge 금지, 커밋은 자기 브랜치에만.
- 커밋 메시지 끝(`--trailer`): `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`, `Claude-Session: https://claude.ai/code/session_012FxFP7YSWEBBCB9rmBQjLL`.
- 임시 파일: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_xrunf1a_<role>/`(자기 것만).

### 최종 보고(한국어) 필수 항목
1. 구현·작성한 design 절과 상태. 2. 멈춤·보고 항목('원래 취지와 다름' 후보 포함). 3. 지운 옛 코드·바뀐 배선(파일:줄)·이름별 grep 결과. 4. graph 단일 정본 자기 점검. 5. 계산값 재사용 자기 점검(컨텍스트 생성 안 커널 0, 세 경로 원값 보존). 6. `tests/structure` 결과(H는 base 비교)·관련 test·깨진 옛 test 목록. 7. 커밋 해시.


## 오케스트레이터 판단 (2026-10-15, 원칙 기본안 -- 사용자 결정 아님)
- J-1: `def to_theta` grep 0 범위를 'E/search/ 중 theta_coords.py 제외'로 design 정정(design 작성자에게 넘김). 메서드 이름은 design대로 to_theta 유지.
- J-2: ThetaCoords 공개면 = `start(variables, theta)`(생성), `to_theta(x)`, 읽기 전용 `x0`(tuple). search/__init__ 재수출(다른 search 공개 이름과 같은 관례).
- J-3: test 관찰 지점을 공개 계약으로 고정: 세 모듈(gate_run·layer0_center·slsqp_outer)의 모듈 속성 `fd_jacobian`, `kernel.size_and_seal` -- 이름·서명·모듈 속성 호출 방식 불변(card 1 J-5 `layer0_center.evaluate` 선례).
- J-4·J-5: 계수 상태 memo 세부 7가지는 design 공백 -> design 40 §2.4.6 보완(design 작성자) 후 검증, card는 그 결과를 따른다. 그 전 code·test 착수 금지. **[2026-10-16 해소: design cfe2e31 보완 병합 -- C3·C3b·C6가 그 결과]**
- J-6: 9회로 좌표 원값 관찰은 보고만(card A 판정은 단위 test 기준, design B-3 결정과 일관).
- J-7: 기준선 옛 값은 card 1 측정 파일을 쓰지 않고, auditor가 같은 환경·같은 하네스로 base(card A 직전 master)와 head를 둘 다 잰다(front가 digest로만 남은 문제, 같은 환경 비교 원칙).
- 측정 복제본 _scratch_xrunf1a_card/wt worktree 제거(깨끗함 확인 후).
- (2026-10-16, nfr4c2 J-O2 교훈) red 예상 목록에서 test 도구 자체를 시험하는 test는 뺀다(3.3).

## 오케스트레이터 design 정정 대기 (초안은 고치지 않음 -- spec card 끝 절과 같음)
- design 40 §10.4 1918·1980행 `-m "not slow"`·'전체 suite(`not slow`)' → conftest(`--run-slow`)에 맞게.
- design 40 §2.4.14 (4) card C 행 856행 `_budget_stop` 정의 2곳·줄 표기 → 3곳(`slsqp_outer.py:95`, `layer0_center.py:280`, `l_bin_search.py:35`).
