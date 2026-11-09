# XRUN-F1 card B (색인 + 부분 스냅샷 + 계수) interface card (card id `xrunf1b`)

- 작성: 2026-10-16. 개정 2026-10-16: design 40 card B 개정 병합(`083b103`)·사용자 승인 X-21 반영 -- 미정 칸 `[J-n]` 없음. 읽기 전용 실측과 card 초안만 담았다. 엔진·test·git 브랜치는 고치지 않았다.
- **card base = `083b103`**(design 40 card B 개정 병합 master. 엔진은 card A 병합 `b0077a8`과 `lut/CONTRACT.md` 한 줄 말고 같다).
- design 근거: 40 §2.4.4(API·입력 버전 정본·호출 규칙), §2.4.5(블록 결과 색인 표 '수명'·'전달'·'상한'·fail-closed·조회 API·생성자 문단), §2.4.7(`KernelContext`·`LayoutResult`·부분 스냅샷), §2.4.9(`RunCounters`·`PerfCounters`·판정), §2.4.14 (5) B 행. 사용자 결정 X-1 (3)·X-2·X-3·X-5·X-7·X-9~X-13·**X-20**(실행 비공유를 구조로)·**X-21**(승인). 계획 offset-strategy PD-7·PD-8.
- **test 작성 주체는 소스를 보지 않고 이 문서(2·3절)만 쓴다.**
- 경로 접두 `E/` = `skills/analog-gmid-design/gmid_engine/`.

---

## 2. interface card (공개 계약)

### C0. `open_run` -- 색인·계수의 유일한 생성 자리 (`gmid_engine.search.open_run`, 새 파일 `search/open_run.py`)

```text
open_run() -> (donors, counters)        # 인자 없음. donors = 새 S3Index, counters = 새 RunCounters
```

- 부를 때마다 새 두 객체(앞 호출의 것과 `is`가 아님, 항목·계수 0).
- `S3Index(...)`·`RunCounters(...)`를 직접 만들지 않는다(비공개 계약 -- C9 규칙 M M-b가 test 쪽도 검사한다). test는 언제나 `open_run()`으로 얻는다.

### C1. `RunCounters` (`gmid_engine.core.RunCounters`, 파일 `core/run_counters.py`)

```text
counters.record(block, part, outcome, input_version) -> None      # outcome ∈ {"reuse", "graft", "replay", "compute"}
counters.result(block, part, input_version, ok) -> None           # compute 뒤: ok=True 성공, ok=False 결정적 도메인 실패
counters.snapshot() -> PerfCounters                               # 불변 값
PerfCounters(blocks, block_totals)                                # gmid_engine.core, frozen
```

- `block`·`part`·`input_version`은 문자열(card B에서 `part`는 늘 `"*"`).
- (block, part)마다 `calls`, `reuses`, `grafts`, `replays`, `computes`, `recomputes_same_input`. `calls = reuses + grafts + replays + computes`.
- `recomputes_same_input`: `record(..., "compute", v)` 때 같은 (block, part, v)의 `"compute"`가 이미 있었으면 +1. `reuse`·`graft`·`replay`는 바꾸지 않는다.
- `result`: 한 (block, part, v)에 `ok=True`와 `ok=False`가 섞이면 섞이는 그 호출에서 `ValueError`.
- `PerfCounters.blocks` = 행 tuple, 행 = frozen 값(속성 `block, part, calls, reuses, grafts, replays, computes, recomputes_same_input`), (block, part) 정렬, 한 번이라도 `record`된 것만. `block_totals` = 여섯 계수 칸(`calls, reuses, grafts, replays, computes, recomputes_same_input`) 합(같은 이름 속성).
- `snapshot()` 결과는 그 뒤 기록에 따라 바뀌지 않는다. 서로 다른 `open_run()`의 계수는 서로 보지 않는다.

### C2. `Donors`·`S3Index`

```text
gmid_engine.core.Donors                  # abc.ABC, core/donors.py. 직접 생성 TypeError
  find(writer, part, input_version) -> GraphSnapshot | None              # 네 메서드 모두 추상
  register(writer, part, input_version, snapshot) -> None
  find_failure(writer, part, input_version) -> FailureRecord | None
  register_failure(writer, part, input_version, record) -> None
gmid_engine.search.S3Index(Donors)       # search/s3_index.py. 생성은 open_run() 만
  entry_count() -> int                   # 성공 키 수 + 실패 키 수
```

- 키 = (writer, part, input_version). `find`·`find_failure`는 등록한 그 객체(`is`)를 준다. 없는 키 → None. 퇴출 없음.
- 같은 키 두 번째 `register` → `ValueError`, 첫 등록 유지(원천은 키마다 하나). 같은 키 두 번째 `register_failure`도 `ValueError`.
- `register`하는 스냅샷의 `block_version(writer)` ≠ 키의 입력 버전 → `ValueError`.
- 한 키에 성공과 실패를 함께 등록하려 하면(순서 무관) `ValueError`.
- 추상 메서드 하나를 빠뜨린 `Donors` 하위 클래스는 생성 때 `TypeError`.

### C3. `graft` (`gmid_engine.core.graft`, 파일 `core/graft.py`)

```text
graft(target, block, part, donor, input_version) -> GraphSnapshot
```

- `part != "*"` → `ValueError`. `donor.block_version(block.name) != input_version` → `ValueError`(이 검사가 블록 호출 fail-closed (2)의 유일한 자리).
- 결과: donor의 그 블록 열(`block.writes`) 전부를 target에 쓴 스냅샷. 결과 `block_version(block.name) == input_version`, 그 열 필드의 `value_fp`·`input_version`이 donor와 같다. 블록이 쓰지 않는 열은 target 그대로.
- 성질(`test_graft_equals_compute`): 같은 입력을 빈 lineage에서 계산한 결과와, 다른 lineage 결과를 원천으로 이식한 결과의 스냅샷 `fp`와 그 열 `value_fp`가 같다.

### C4. 계산 블록 호출 (`gmid_engine.core.ComputeBlock`)

```text
block(snapshot, *extras, donors, counters) -> GraphSnapshot     # 두 키워드 필수, 기본값 없음
block.input_version(snapshot, *extras) -> str                    # 입력 버전 정본(블록 이름·블록 코드 해시·투영 지문의 지문)
```

- 빠지면 `TypeError`. `donors`가 `Donors` 하위가 아니면 `TypeError`(블록 함수 호출 0). extras 불변 검사 `TypeError`는 그대로이고 그 호출은 계수에 들지 않는다.
- 판정 순서(분할 `"*"`, v = `block.input_version(snapshot, *extras)`와 같은 값):
  1. `snapshot.block_version(name) == v` → `snapshot` 그대로(`is`), outcome `"reuse"`, 블록 함수 0, `find` 부르지 않음.
  2. `donors.find(name, "*", v)`가 스냅샷을 주면 이식 결과, outcome `"graft"`, 블록 함수 0, `find_failure` 부르지 않음. 준 스냅샷의 `block_version(name) != v`면 `ValueError`(graft가 냄).
  3. `donors.find_failure(...)`가 기록을 주면 블록 함수를 부르지 않고 예외를 던진다 -- 클래스 = `FAILURE_CLASSES[record.failure_class].exc`, `.record is` 그 기록, outcome `"replay"`.
  4. 계산: `record(..., "compute", v)`는 블록 함수 전에. 성공 → 결과를 `register`, `result(ok=True)`. `InfeasibleSizingError` 하위·`SchemaRejectedError` → `register_failure(..., exc.record)`, `result(ok=False)`, 같은 예외 객체를 올린다. 그 밖 예외(순수 `ValueError`·`TypeError`·`MemoryError`·`KeyboardInterrupt`·기타 `BaseException`) → 등록·`result` 없이 올린다(같은 입력 재호출 = 다시 계산 → `recomputes_same_input` +1).
- 블록 객체는 상태가 없다: `stats`·`reset_stats` 속성 없음, `gmid_engine.core`에 `BlockStats` 없음. 같은 블록을 두 `open_run()` 쌍으로 같은 입력에 부르면 두 쌍 모두 `"compute"` 1.
- 경로와 무관하게 같은 입력이면 같은 결과(스냅샷 `fp`·필드 `value_fp`).
- `block.input_version`은 같은 인자에 같은 값이고, 블록 호출이 쓰는 입력 버전(결과 `block_version(name)`)과 같다.

### C5. 후보 실패의 부분 스냅샷·`from_record` (`gmid_engine.core`)

```text
InfeasibleSizingError.from_record(record), SchemaRejectedError.from_record(record)   # classmethod, 하위 클래스에서 부르면 그 클래스. .record is record
exc.partial -> GraphSnapshot | None        # InfeasibleSizingError 하위, 생성 직후 None
attach_partial(exc, snapshot) -> None      # gmid_engine.core, 파일 core/failure_partial.py
```

- `attach_partial`: `exc`가 `InfeasibleSizingError` 하위가 아니면 `TypeError`, `snapshot`이 `GraphSnapshot`이 아니면 `TypeError`. `exc.partial`이 이미 있으면 바꾸지 않는다(첫 부착 유지).
- 엔진이 붙이는 곳(결과는 C7로 본다): 커널 DC 블록 단계(그 블록에 들어간 스냅샷), 봉인 위반(`dc_seal_report`까지 쓴 스냅샷), ss 단계(실패 직전, 적어도 봉인 스냅샷). 재연한 예외도 바깥이 같은 규칙으로 붙인다.

### C6. 두 객체를 받는 공개 진입

| 진입 | 서명(card B 뒤) |
|---|---|
| `gmid_engine.pipeline.run_stage_a` | `run_stage_a(topology_path, spec_path, lut, *, output_dir, donors, counters, supplies_v=None, structure_path=None)` -- 빠지면 `TypeError`. 결과 `StageAResult` 칸 `donors`·`counters`(넘긴 객체 `is`, 정지 경로 결과 포함) |
| `gmid_engine.pipeline.run_stage_b` | 서명 그대로 `(stage_a, memo, pdk_decl, *, output_dir, settings, diagnostic=False)` -- `stage_a`의 두 칸을 쓴다 |
| `gmid_engine.sizing.build_kernel_context` | `build_kernel_context(s1graph, inputs, lut, order_hints=NO_ORDER_HINTS, *, donors, counters)` -- 결과 `KernelContext` 칸 `donors`·`counters`(`is`) |
| `gmid_engine.search.build_search_context` | 서명 그대로 -- `dc_ctx`의 두 칸을 쓴다. `sctx.dc`도 같은 두 객체 |
| `gmid_engine.graph.build_s1` | `build_s1(doc, supplies_v=None, previous=None, column_limit=None, *, structure=None, marks=NO_MARKS, donors, counters)` |
| `gmid_engine.graph.build_s1v` | `build_s1v(s1, spec, *, count_budget, declared=(), structure=None, declared_loop_cuts=(), stop_on_unsupported=True, donors, counters)` |
| `gmid_engine.sizing.seal_dc` | `seal_dc(snapshot, calls, lut, resistances, linear_devices, raise_on_violation=True, *, donors, counters)` |
| `gmid_engine.layout.run_layout` | `run_layout(layout_input, memo, design_point, previous=None, *, donors, counters)` |
| `gmid_engine.convergence` `place_layout` | 기존 인자 + `*, donors, counters` |
| `size_and_seal`, `size_and_seal_local`, `ss_evaluate(sealed, ctx, ...)`, `evaluate`, `find_front`, `converge_point` | 서명 그대로(`KernelContext`·`sctx`에서 꺼낸다) |

- 위 표의 필수 키워드 둘은 모두 기본값이 없다(빠지면 `TypeError`). test는 키워드로만 넘긴다.
- 한 실행(한 `open_run()` 쌍) 안: 단계 A의 블록 결과가 단계 B·커널 컨텍스트·탐색·평가에서 같은 lineage 재사용 또는 이식으로 쓰인다(같은 입력 재계산 0).
- 두 실행(두 `open_run()` 쌍)은 아무것도 나누지 않는다: 두 번째 실행의 S0 수준 블록 행도 `computes` 1, 첫 실행 계수 불변.
- `LayoutResult.computed_blocks`: 이번 호출에서 그 블록의 값을 스냅샷에 쓴 writer(계산 또는 이식). 계산·이식 구분은 `RunCounters` 행으로 본다.

### C7. `EvalResult.partial`·S3 evals 실패 줄

- `EvalResult` 끝에 칸 `partial`(기본 None). 성공·정의역 밖 = None. 후보 실패(`status == "failed"`) 커널 평가 = 부분 스냅샷:
  - DC 블록 단계(전류·길이·기둥·폭) 실패: `block_versions`에 앞 블록은 있고 실패한 블록은 없다.
  - 봉인 위반: `block_versions`에 `dc_seal_report`가 있다.
  - ss 단계 실패: 봉인 스냅샷의 블록(`dc_seal_report` 포함)이 있다.
- 실패 평가의 `evaluation`은 여전히 None, 다른 칸은 card A와 같다.
- S3 evals 실패 줄(`ok` false·`fail` 있음)에도 `snapshot_fp` = `partial.fp`. 성공 줄은 그대로.
- 부분 스냅샷 안 블록 결과는 이미 색인에 있다: 같은 블록 입력의 다른 평가가 이식한다.

### C8. `find_front` `perf`

- 키 정확히 22개: `{requests, kernel_calls, hits, fail_hits, outside_domain, recompute_same_key, unique_keys, eval_time_median_s, wall_s, lut_memo_evictions, lut_memo_bound, blocks, block_totals, block_index_entries, block_index_bound, n_starts, n_solves, eval_budget, eval_budget_source, frozen_columns, stops_eval_budget, stops_wall_budget}`. 옛 `block_calls`·`block_reuses`·`block_computes`·`block_recomputes_same_input` 없음. runs 줄 `perf`도 같다.
- `blocks` = 행 목록 `{block, part, calls, reuses, grafts, replays, computes, recomputes_same_input}`, (block, part) 정렬, 실행 전체(단계 A부터, 그 `sctx.dc.counters`), 불린 것만, 행마다 `calls = reuses + grafts + replays + computes`.
- `block_totals` = 여섯 칸 각각의 행 합(dict).
- `block_index_entries` = 그 실행 `S3Index.entry_count()`.
- `block_index_bound` = `len(blocks) × (E_total + 1)`. E_total: `eval_budget_source == "declared"`면 `eval_budget` + 2 × (정의역 변수 수), 유도(`derived_once:...`)면 `eval_budget`, `eval_budget`이 None이면 `block_index_bound` = null.
- NFR-4 `env_fp`·notes `l_search`, card A `lut_memo_bound` 그대로.

### C9. 구조 규칙 M (test 쪽에도 걸린다 -- `E/tests/structure`)

- **M-a**: 엔진 소스(`tests/` 제외)에서 `open_run` 참조는 `search/open_run.py`·`search/__init__.py`뿐.
- **M-b**: `S3Index(`·`RunCounters(` 생성 호출은 그 정의 모듈과 `open_run.py`에만 -- **test·하네스 포함**.
- **M-c**: `run_stage_a` 호출의 `donors`·`counters` 인자는 같은 함수 본문에서 `donors, counters = open_run()`(튜플 풀기, 이름은 자유)으로 대입된 두 이름이고, 그 이름은 그 함수 안 `run_stage_a` 호출 **하나**에만 쓰인다. `run_stage_a`가 반복문 본문 안이면 그 `open_run()`도 같은 반복문 본문 안. 위반: 매개변수·속성·결과 칸(`StageAResult`·`KernelContext`·`sctx.dc`)·다른 호출 반환에서 온 쌍, 바깥 함수의 쌍을 안쪽 `def`·`lambda`에서 씀(자유 변수), 내포식·generator 식 안 `run_stage_a`(반복문 본문으로 본다), `run_stage_a(**kw)`·`run_stage_a(*args)`. 그래서 `run_stage_a`를 감싸는 helper는 쌍을 매개변수로 받지 않고 스스로 `open_run`을 부른다. 범위는 `run_stage_a` 인자뿐 -- 감쌈 함수·블록을 직접 부르는 단위 test는 한 test 함수 안 `open_run()` 하나를 여러 호출에 써도 된다.
- **M-d**: `open_run` 결과(또는 두 객체) 보관 금지 -- 모듈 수준 이름, 클래스 속성, session·module·package 범위 fixture, 함수 기본 인자값, `functools.lru_cache`·`functools.cache`(데코레이터·호출형) 함수의 반환, 모듈 수준 컨테이너 변경(`append`·`extend`·`add`·`update`·`setdefault`·항목 대입), conftest `pytest_configure`·`request.config`·`config.cache`·`config.stash`, 수명이 test 하나보다 긴 객체의 인스턴스 속성(함수 지역·반환은 허용). function 범위 fixture가 `open_run()`을 반환하는 것은 허용.
- **M-f**: `S3Index`·`RunCounters` 객체 또는 그 내부 칸(`_` 속성 포함)이 `pickle`·`json`·`shelve`·`marshal` 쓰기 함수(`dump`·`dumps`·`Shelf` 항목 대입 등) 인자에 나타나면 위반.
- (M-e 없음.) 색인 키에 실행 바깥 지문(`code_fp`·`env_fp`·spec 지문·`context_fp`·`run_id`)을 넣지 않는다(엔진 계약 -- C2 키 그대로).

### C10. 바뀌지 않는 것

- `GraphSnapshot.write(writer, input_version, columns)`·`block_version(writer)`, `compute_block(name, reads, writes)`, 블록 코드 해시.
- card A: `ThetaCoords`, `LutMemo.counting`·`open_count`·`fix_bound`·`bound_state`, `BoundedLRU.adopt`, `perf.lut_memo_bound`. card A·NFR-4 관찰 지점(세 모듈 `fd_jacobian`, `kernel.size_and_seal`, `layer0_center.scipy_minimize`, `find_front`의 `layer0_start`·`sweep_front`, `core.blas_env.loaded_blas_modules`).
- NFR-4 BLAS 재확인 다섯 지점, `env_fp`·notes `l_search`.
- 탐색 궤적: 9회로 front·pending·unmeasured·층 0·ε 풀이·S0 칸·평가 수·`seq`는 card A 병합 엔진과 같다.
- `E/tests/integration/fixtures/u17_1b_s0_baseline.json` 지문.
- `sctx.counters`(dict)·`sctx.cache`·`computed_keys`(U17 ②).

### C11. 단언 금지

`S3Index`·`RunCounters` 안쪽 자료 구조, 같은 키 `result(ok=True)` 두 번의 동작, `FailureRecord.detail` 내용, 부분 스냅샷 `fp` 값 자체(같음·다름만), `input_version` 문자열 값 자체(같음·다름만), `PerfCounters` 행 타입 이름.

---

## 신규 시그니처 (merge_gate가 새 심볼 부재 red를 card 이유로 센다 -- card A J-O1)

base `083b103`에 없는 이름. 이 이름 때문에 base에서 나는 `ImportError`·`AttributeError`·`TypeError`(새 키워드 인자·새 칸)·`KeyError`(새 perf 키)는 card 이유의 red다.

| 심볼 | 공개 경로(파일) | 종류 |
|---|---|---|
| `open_run` | `gmid_engine.search`(`search/open_run.py`) | 함수 |
| `RunCounters`(`record`·`result`·`snapshot`), `PerfCounters` | `gmid_engine.core`(`core/run_counters.py`) | 클래스·불변 값 |
| `Donors`(네 추상 메서드) | `gmid_engine.core`(`core/donors.py`) | 추상 클래스 |
| `graft(target, block, part, donor, input_version)` | `gmid_engine.core`(`core/graft.py`) | 함수 |
| `attach_partial(exc, snapshot)` | `gmid_engine.core`(`core/failure_partial.py`) | 함수 |
| `S3Index`(네 메서드·`entry_count`) | `gmid_engine.search`(`search/s3_index.py`) | 클래스 |
| `ComputeBlock.__call__(..., donors, counters)`, `ComputeBlock.input_version` | `gmid_engine.core` | 키워드·메서드 |
| `InfeasibleSizingError.from_record`, `SchemaRejectedError.from_record`, 예외 칸 `partial` | `gmid_engine.core` | classmethod·칸 |
| `KernelContext.donors`·`.counters` | `gmid_engine.sizing` | 칸 |
| `StageAResult.donors`·`.counters`, `run_stage_a(..., donors, counters)` | `gmid_engine.pipeline` | 칸·키워드 |
| `build_kernel_context`·`build_s1`·`build_s1v`·`seal_dc`·`run_layout`·`place_layout`의 `donors`·`counters` | 각 패키지 | 키워드 |
| `EvalResult.partial` | `gmid_engine.search` | 칸 |
| perf 키 `blocks`·`block_totals`·`block_index_entries`·`block_index_bound` | `find_front` 결과 | 결과 칸 |
| S3 evals 실패 줄 `snapshot_fp` | S3 기록 | 결과 칸 |
| 구조 검사 `check_m`(규칙 M) | `E/tests/structure/structure_checks.py` | test 도구 |

없어지는 심볼: `gmid_engine.core.BlockStats`, `ComputeBlock.stats`, `ComputeBlock.reset_stats`, perf 키 `block_calls`·`block_reuses`·`block_computes`·`block_recomputes_same_input`.

---

## 3. test 목록

위치는 제안이다(규칙 H 1:1). oracle: (식) design 식, (손) 손으로 만든 블록·조회 순서, (비교) 같은 함수 두 출력 비교, (독립) 피검 계수를 읽지 않는 독립 계수(블록 함수를 감싸 센 호출 수 등). 두 객체는 언제나 `open_run()`으로 얻는다(M-b).

### 3.1 새 test

| id | 위치 | 내용 | 계약 | oracle | base 결과 |
|---|---|---|---|---|---|
| B-T0 | `tests/search/test_open_run.py`(신규) | `open_run()` 두 번: 서로 다른 객체 쌍(`is not`), 타입(`Donors` 하위·`RunCounters`), 새 쌍 `entry_count() == 0`·`snapshot().blocks == ()` | C0 | (식) | red(ImportError) |
| B-T1 | `tests/core/test_run_counters.py`(신규) | 손으로 정한 `record` 순서(같은 키 compute 두 번, 다른 키 compute, reuse·graft·replay 섞음)에서 행 여섯 칸·항등식, 같은 키 두 번째 compute만 `recomputes_same_input` +1 | C1 | (손)+(식) | red |
| B-T2 | 같은 파일 | `result` 섞임(두 순서) `ValueError` | C1 | (식) | red |
| B-T3 | 같은 파일 | `snapshot()` 불변(속성 대입 실패)·기록 뒤 불변, 행 정렬, 불린 것만, `block_totals` = test가 더한 합, 두 `open_run()` 계수 독립 | C1 | (손)+(비교) | red |
| B-T4 | `tests/core/test_donors.py`(신규) | `Donors()` `TypeError`, 추상 메서드 하나 빠진 하위 클래스 생성 `TypeError`(네 메서드 각각) | C2 | (식) | red |
| B-T5 | `tests/core/test_compute_block.py`(다시 씀) | toy 블록: 두 키워드 중 하나 빠짐 `TypeError`, `donors`가 `Donors` 하위 아님 `TypeError`(블록 함수 호출 0) | C4 | (식)+(독립) | red |
| B-T6 | 같은 파일 | 같은 lineage 재호출 → 같은 스냅샷 `is`, `reuse`, 블록 함수 0 | C4 | (독립) | red |
| B-T7 | 같은 파일 `test_graft_equals_compute` | 같은 입력을 빈 스냅샷에서 시작한 두 lineage에 부름: 두 번째 블록 함수 0·`graft`, 두 결과 `fp`·열 `value_fp`가 별도 `open_run()` 쌍으로 계산만 한 결과와 같음 | C3·C4 | (비교)+(독립) | red |
| B-T8 | 같은 파일 | 블록 함수가 `SealViolationError`(또는 `NonconvergentError`, `SchemaRejectedError`) → 다른 lineage 재호출: 블록 함수 0, 같은 클래스, `.record is` 첫 기록, `replay`, 재계산 0 | C4·C5 | (독립)+(비교) | red |
| B-T9 | 같은 파일 | 순수 `ValueError`·`BaseException` 하위(중단 흉내) → 재호출에서 블록 함수 다시 호출, `recomputes_same_input` 1. `InfeasibleSizingError` 하위는 등록됨(대조) | C4 | (독립) | red |
| B-T10 | 같은 파일 | 무상태: `stats`·`reset_stats` 속성 없음, `core.BlockStats` 없음, 두 `open_run()` 쌍 모두 `compute` 1 | C4 | (식)+(독립) | red(속성이 있음 -- 단언 실패) |
| B-T11 | 같은 파일 | 판정 순서: 같은 lineage면 `find` 미호출, `find`가 주면 `find_failure` 미호출(가짜 `Donors` 하위로 기록), 가짜가 버전 다른 스냅샷을 주면 `ValueError`·블록 함수 0 | C4·C3 | (손) | red |
| B-T12 | 같은 파일 | `block.input_version(snapshot, *extras)`: 같은 인자 같은 값, extras 하나 바꾸면 다른 값, 블록 호출 결과의 `block_version(name)`과 같음 | C4 | (비교) | red(AttributeError) |
| B-T13 | `tests/search/test_s3_index.py`(신규) | `find`·`register`(`is`), 같은 키 재등록 `ValueError`·첫 등록 유지(`test_index_single_source`), 버전 다른 스냅샷 등록 `ValueError`, 성공·실패 섞임 `ValueError`(두 순서), `find_failure`·`register_failure`(`is`)·실패 재등록 `ValueError`, 없는 키 None, `entry_count` | C2 | (손) | red(ImportError) |
| B-T14 | `tests/core/test_graft.py`(신규) | `graft` 단독: 결과 `block_version`·열 `value_fp`가 donor와 같고 다른 열은 target 그대로, `input_version` 불일치 `ValueError`, `part="P"` `ValueError` | C3 | (비교)+(식) | red |
| B-T15 | `tests/core/test_failure_partial.py`(신규) | `attach_partial`: 첫 부착 유지·두 번째 무시, `exc`·`snapshot` 형식 거부 `TypeError`, 새 예외 `partial` None. `from_record`: N3.14 분류 클래스마다(두 기반 하위 모두) 새 예외 클래스 = 그 클래스, `.record is` 넘긴 기록 | C5 | (식)+(비교) | red(ImportError·AttributeError) |
| B-T16 | 각 패키지 test | C6 표의 필수 키워드: 빠지면 `TypeError`. `StageAResult`·`KernelContext`·`sctx.dc`의 두 칸이 넘긴 객체 `is` | C6 | (식)+(비교) | red(TypeError) |
| B-T17 | `tests/integration/test_run_isolation.py`(신규) | 한 test 안에서 같은 회로를 `run_stage_a` 두 번 -- 호출마다 바로 앞에서 `donors, counters = open_run()`(M-c 꼴): 두 번째 실행 S0 수준 블록 행 `computes` 1, 첫 실행 계수 불변 | C6·C1·C9 | (비교) | red |
| B-T18 | `tests/search/test_kernel.py` | 계보 무관: parent 없이 두 평가 -- 전류 성분 같고 L만 다르게: 두 번째 평가의 전류 블록 행이 `graft`, 같은 입력 재계산 0. 전제: 두 평가 모두 커널 평가 | C4·C8 | (비교)+(식) | red |
| B-T19 | `tests/search/test_kernel.py` | 부분 스냅샷 세 경우(DC 블록 실패·봉인 위반·ss 실패): `EvalResult.partial.block_versions`(C7), 실패 줄 `snapshot_fp == partial.fp`, 성공·정의역 밖 None. 전제: `status == "failed"`·분류 | C7 | (식)+(비교) | red(AttributeError) |
| B-T20 | `tests/search/test_kernel.py` | 부분 스냅샷 재사용: 실패 평가가 계산한 블록 결과를 같은 블록 입력의 뒤 평가가 이식(그 행 `grafts` ≥ 1, 재계산 0) | C7·C4 | (비교) | red |
| B-T21 | `tests/search/test_find_front.py` | perf 키 22개(C8), 옛 네 칸 없음, `blocks` 정렬·항등식, `block_totals` = test 합, `block_index_entries` 정수, `block_index_bound` = `len(blocks) × (E_total + 1)`(선언 실행: test가 `eval_budget` + 2·변수 수로 계산). `PERF_KEYS_C7`도 22개로 | C8 | (식)+(독립) | red(KeyError) |
| B-T22 (slow) | `tests/integration/test_g10_no_recompute_9circuits.py`(신규) | 9 library 회로 각 한 실행(단계 A → `find_front`, 선언 E_B 40, 실행마다 `open_run()`): `perf.blocks` 모든 행 `recomputes_same_input` = 0, `recompute_same_key` = 0(**같은 입력 재계산 0**), S0 수준 블록 행 `computes` = 1. `ngcc_3stage_ff`는 단계 A·B까지 넘긴 `counters.snapshot()`로 같은 단언 | C8·C1 | (식) | red |
| B-T23 | `tests/structure/`(규칙 M) | `check_m`이 엔진 소스·`tests/` 트리에서 위반 0 | C9 | (식) | red(검사 부재 -- 신규 시그니처 표) |
| B-T24 | `tests/structure/` 위반 픽스처(`fixtures/rule_m/bad/gmid_engine/…`) | 각 픽스처가 **실제로 거부**된다: M-a(엔진 소스 `open_run` 참조), M-b(test에서 `S3Index()` 직접 생성), M-c 꼴마다(매개변수로 받은 쌍, 결과 칸 `a.donors`, 반복문 밖 `open_run`, `open_run()` 대입 문장 하나를 두 `run_stage_a`에 사용, `if`/`else` 가지 안 대입(호출은 가지 밖), `with` 본문 안 대입(호출은 본문 밖) -- 원문보다 엄격한 안전 쪽 해석(O-17 (2)), 안쪽 `def` 자유 변수, `**kw`, 별칭·이름 대입·`getattr` 간접 호출도 같은 판정), M-d 경로마다(모듈 수준, 클래스 속성, session fixture, 기본 인자값, `lru_cache`, 모듈 리스트 `append`, `request.config`, 인스턴스 속성), M-f(`pickle.dump(donors)`). 허용 픽스처(`good/`): 튜플 풀기 1:1, 같은 이름에 새 `open_run()` 재대입 후 다음 호출(대입마다 1:1, O-17 (1)), 반복문 안 `open_run`, function fixture 반환, 단위 test 한 쌍 여러 감쌈 호출 | C9 | (식) | 검사기 자체 시험 -- red 예상 목록 밖(3.3) |

### 3.2 삭제·고칠 test (083b103 실측)

| 대상 | 처리 |
|---|---|
| 옛 계수 API 39파일(`reset_stats`·`BlockStats` 32 + 블록 `.stats()` 7, 목록 spec card 1.3.3) | `RunCounters`(C1)·`perf.blocks`(C8)로. LUT memo `.stats()`는 그대로 |
| `run_stage_a` 호출 16파일 46곳: `tests/integration/nfr4_run_dump.py`, `test_j_rules_library.py`, `test_layer0_boundary_rows.py`, `test_rerun_s3_independence.py`, `test_s0_layer_9circuits.py`, `test_stage_a_library.py`, `test_stage_b_library.py`, `tests/metrics/gb4_hand.py`, `tests/pipeline/test_stage_a.py`, `test_stage_a_loop_cut.py`, `test_stage_a_report.py`, `test_stage_b.py`, `tests/search/test_cell_floor.py`, `u13_hand.py`, `u13_real.py`, `tests/sizing/test_current_basis.py` | 호출마다 같은 함수 안 `donors, counters = open_run()` → 그 호출 하나에만(M-c). helper는 스스로 `open_run`. 한 함수 안 2회 이상 8함수(`test_stage_a_library.py` 둘, `test_j_rules_library.py` 하나, `pipeline/test_stage_a.py` 다섯)는 호출마다 자기 `open_run()` |
| 그 밖 감쌈 함수·블록 직접 호출(블록 189곳, `build_s1` 177·51, `build_kernel_context` 48·23, `build_s1v` 22·10, `run_layout` 19·2, `seal_dc` 6·3, `place_layout` 6·2 -- 합집합 98파일) | 키워드 두 객체. 단위 test는 그 test 함수 안 `open_run()` 하나를 여러 호출에 써도 된다 |
| `tests/search/test_find_front.py:19-21`·`:28` | 22개 새 집합(B-T21) |
| `tests/integration/nfr4_run_dump.py:41`(`K_NAMES` 옛 네 칸), 사슬 `:376-401` | 네 이름 삭제, 회로 실행 함수 안에서 `open_run` -- 하네스 = test 도구(red 예상 밖) |
| `tests/integration/test_s0_layer_9circuits.py`(G-10 C4 절) | `RunCounters`로 |
| `tests/search/test_search_values.py`(`EvalResult` 직접 생성 2곳) | 새 칸 끝·기본 None -- 깨지지 않으면 그대로 |

### 3.3 이름 규칙

- 0건 확인(083b103, docs·`.md` 제외): `open_run`, `RunCounters`, `run_counters`, `graft`, `Donors`, `S3Index`, `s3_index`, `attach_partial`, `failure_partial`, `from_record`, `find_failure`, `register_failure`, `replays`, `entry_count`, `block_totals`, `block_index_entries`, `block_index_bound`, `PerfCounters`, `rule_m`, `check_m`, `test_open_run`, `test_run_counters`, `test_graft`, `test_donors`, `test_s3_index`, `test_failure_partial`, `test_run_isolation`, `test_g10_no_recompute_9circuits`, `test_index_single_source`, `test_graft_equals_compute`.
- `partial`은 test 지역 이름·`test_compute_block.py`의 parametrize id `"partial"`로 있다 -- 새 이름은 `test_partial_snapshot_…`.
- 권장 접두: `test_open_run_…`(B-T0), `test_run_counters_…`(B-T1~3), `test_donors_…`(B-T4), `test_block_call_…`(B-T5~12), `test_s3_index_…`(B-T13), `test_graft_…`(B-T14), `test_failure_partial_…`·`test_from_record_…`(B-T15), `test_partial_snapshot_…`(B-T19·20), 구조 `test_rule_m_…`(B-T23·24).
- 쓰이는 `-k` 식: `"test_ic"`, `"g10"`, `"ic11 or kvl_branch_residual"`, `"rule_g or design_value_location"`, `rule_k_`, `"duplicate_args or loop_invariant"`, `"ic1 or ic2 or ic9 or ic10 or shared_gate_net or kcl_residual"`, `"mna_assembly_count or mna_solve_count"`. 새 이름은 `test_ic`로 시작하지 않고 `ic1`·`ic2`·`ic9`·`rule_g`·`rule_k_`를 담지 않는다. `g10`은 `test_g10_no_recompute_9circuits`만 일부러 담는다. 작성 뒤 `--collect-only -k <각 식>` 수를 base와 함께 보고(base에도 `Vg10` id가 걸릴 수 있다).
- **red 예상 목록**(감사 대상) = B-T0~B-T23(엔진 동작·엔진 트리 구조를 보는 test). 제외: B-T24(규칙 M 검사기 자체 시험 -- base에서는 `check_m` 부재로만 실패, 신규 시그니처 표의 부재 red로 센다), 하네스 `nfr4_run_dump.py`·비교기 `nfr4_compare.py`·마커 conftest 자체 test(nfr4c2 J-O2).

---

## 4. 판정 측정 (audit)

격리 복제본(`<W>/xrunf1b-audit`, base 비교용 base 복제본 따로)에서만 잰다. 9회로 방법은 card A 4절과 같다(회로마다 새 프로세스, 허용 목록 환경, 순차, E_B 40 선언, 넉넉한 시간 예산, 회로별 JSON·진행 append, `ngcc_3stage_ff`는 단계 B까지). head 사슬은 회로 실행 함수 안에서 `open_run()` 한 번. base = `083b103`(엔진 = card A 병합 엔진).

| # | 측정 | 방법 | 합격 |
|---|---|---|---|
| B-1 | 삭제 이름 grep 0 | spec card 1.3.5 이름·범위별 `git grep -nw`, `ComputeBlock` 본문 AST, `seal_versions.py` 식 사본 0 | 범위 안 0 |
| B-2 | 같은 입력 재계산 0 | 9회로 `perf.blocks` 모든 행 `recomputes_same_input` = 0, `recompute_same_key` = 0, 회로별 `block_totals` 보고 | 9/9 |
| B-3 | 독립 계수 대조 | `ComputeBlock.__call__`·블록 `fn` 클래스 수준 감쌈으로 블록별 호출·실계산 수 → `perf.blocks` 합과 대조, card A A-6 head 47건 → 0 | 같음, 0 |
| B-4 | 궤적 불변 | base·head 같은 하네스·환경, §2.4.13 비교기 1차 검사. 제외 칸 목록은 감사 소유(후보: `perf` 블록 계수·색인 칸, 지운 네 칸, T 부류, evals 실패 줄 `snapshot_fp`, 하네스 `partial` 덤프 경로, `run_id`·`code_fp`) -- 제외 이유 기록. `test_s0_layer_9circuits.py` | 제외 밖 diff 0, S0 diff 0 |
| B-5 | 색인 크기 보고 | `block_index_entries`·`block_index_bound`·비율 | 보고만 |
| B-6 | red-green | base + 새 test: red 예상(B-T0~23)이 red이고 사유가 신규 시그니처 부재 또는 단언 실패인지 test마다 기록. head 전부 통과 | head 통과 |
| B-7 | 구조 규칙 M | head: 엔진 소스·`tests/` 위반 0. 위반 픽스처 전부 거부(B-T24) -- **'실제로 거부'를 먼저 확인**. M-c를 손으로 깨는 변형 한 개(복제본 안 임시 test 파일, 커밋 안 함)도 거부되는지 | 위반 0, 거부 전부 |
| B-8 | 부분 스냅샷 9회로(보고만) | 실패 줄 수·`snapshot_fp` 있는 줄 수·실패 평가 원천 이식 수 | 실패 줄 전부 `snapshot_fp` |
| B-9 | 전체 suite·구조 | `--run-slow` 한 번, `tests/structure` 위반 0(규칙 A -- `failure_errors.py` 데이터 모듈 유지·새 파일 여섯), H를 base와 비교 | 0 failed, 위반 0 |
| B-10 | 바뀌지 않아야 할 것 | `git diff base..head -- E/core/graph_snapshot.py E/core/bounded_lru.py E/lut/ E/search/theta_coords.py E/core/blas_env.py` 0줄, 코드 해시 부분 AST 같음, spec card 1.3.6 보존 계약, `tests/core/test_blas_env.py` 통과. 색인 키에 실행 바깥 지문 없음·디스크 쓰기 없음(코드 리뷰) | 0줄·같음 |
| B-11 | 이름 충돌 | 3.3 `-k` 식 `--collect-only` head·base | `g10` 증가분 = 새 g10 test만 |
| B-12 | 시간·메모리(보고만) | 사슬 시간 base/head, 회로별 최대 RSS | 판정 아님 |
| B-13 | 공통 완료 조건 | §10.4 `-k "rule_g or design_value_location"`, `-k g10`, §2.4.8 소유표(`S3Index` = (b), `RunCounters` = (c)), gap-detector ≥ 90 %, 42 D-XR3~5 | 통과 |

---

## 5. 공통 브리핑

> spec card 2절과 같다. test agent는 이 문서 2·3절만 읽고 소스를 보지 않는다.

base = `083b103`. design: 40 §2.4.4·§2.4.5('수명' 규칙 M)·§2.4.7·§2.4.9·§2.4.14 (3)(4)(5) B 행·§10.4, 42 D-XR3~D-XR5. 사용자 결정 기록: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/user_decisions.md`(읽기만, X-1~X-21). card: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/engine/XRUNF1B_SPEC_CARD.md`(code·audit), `XRUNF1B_INTERFACE_CARD.md`(test는 이것만).

### 절대 규칙
1. design 그대로. as-built 결정 금지 -- 모르면 멈추고 보고.
2. graph 단일 정본: graph 밖 허용 저장소는 LUT memo, S3 기록·S3 메모리 색인(스냅샷 참조·`FailureRecord`만), 실행 계수뿐.
3. 재사용 = 실행 안·계보 무관, 판정 = 같은 입력 재계산 0. 두 객체는 `open_run()`으로만, `run_stage_a` 호출마다 1:1, 보관·디스크·실행 바깥 지문 키 금지(규칙 M).
4. 틀린 구조는 재작성, 옛 코드·CONTRACT 같은 변경에서 삭제, 만든 것은 배선.
5. 건드리지 않는 것: card C·U17 ②·③·OS-2·OS-5, 블록 코드 해시, `GraphSnapshot` 서명, card A 결과, NFR-4 병합분, `_budget_stop` 3곳.
6. 상수 발명 금지, 회로·소자 이름 코드 금지.
7. 파일 분할 규칙(A: `failure_errors.py` 데이터 모듈 유지, C: `open_run`·`S3Index`는 search, H: 1:1), `tests/structure` 위반 0(규칙 M 포함).
8. 작성자 ≠ 검증자(규칙 M 검사기·픽스처는 test 주체 몫). 같은 커밋에서 코드와 기준 동시 변경 금지, 기준 약화는 사용자 승인.

### 실행 환경·git 가드
- python `/c/Python314/python.exe`, 위치 `<worktree>/skills/analog-gmid-design`, `python -m pytest -q gmid_engine/tests/<경로> -p no:cacheprovider`, slow 포함 `--run-slow`.
- 무거운 실행은 한 번에 하나, 결과는 `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_xrunf1b_<role>/run.txt`에 append, 백그라운드 실행이 끝날 때까지 턴을 끝내지 않는다.
- git: `git -C <자기 worktree>`, `set -e`, 다른 worktree·master 금지, reset --hard·checkout·push·merge 금지.
- 커밋 트레일러(`--trailer`): `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`, `Claude-Session: https://claude.ai/code/session_012FxFP7YSWEBBCB9rmBQjLL`.

### 최종 보고(한국어)
1. 구현·작성한 절과 상태 2. 멈춤·보고 3. 지운 코드·바뀐 배선·grep 4. graph 정본 점검 5. 재사용 점검(같은 입력 재계산 0, 규칙 M 위반 0) 6. `tests/structure`·관련 test·깨진 옛 test 7. 커밋 해시.


## 오케스트레이터 판단 (상속)
- (card A J-O1) 위 '## 신규 시그니처' 절.
- (nfr4c2 J-O2) red 예상 = 엔진 동작·엔진 트리 구조 test(B-T0~23). 검사기 자체 시험(B-T24)·하네스·비교기 test는 제외.
- 재사용 판정 문구 = '같은 입력 재계산 0'.
- (card A J-7) base·head 같은 하네스·같은 환경.
- 미정 칸 없음(design 083b103, X-20·X-21).
