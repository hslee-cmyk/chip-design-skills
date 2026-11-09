# 실행 사이 재사용 제거 card 초안 (card id `xrun-removal`, 구현 card 1)

- 작성: 2026-10-15. 읽기 전용 실측과 초안만 담았다. 엔진·test·git 브랜치는 고치지 않았다.
- **동기화(2026-10-15)**: design 최종본이 master `0538dec`(design 브랜치 끝 `af60448`, 계획 v6.10, design 40·41·42 v1.10)로 병합됐다. 이 초안의 card base = **master `0538dec`**. 실측: `git diff --stat 5870d80 0538dec -- skills .gitignore` = 0줄(엔진·test·`.gitignore`는 5870d80과 같다, 문서 5개만 바뀜). 아래 design 인용은 0538dec의 design 40 §2.4.3(217~284행)이다. 옛 'design 수정 대기 (B-1/B-2)' 표시는 최종 규칙으로 바꿨다.
- 처음 초안 출처(읽기만): worktree `C:/Users/HSLEE/Documents/Todoc/fpga/wt/nfr4-design` @ `94acb52`
  - 계획 v6.10 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`: NFR-2(186행), WP-23(327행), 시작점(453행), U-87~U-90(1304~1307행)
  - design 40 v1.10 `docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md`: §2.4.1, §2.4.3(삭제·변경 목록, test 삭제·변경 목록), §2.4.5, §2.4.9 G-10, §2.4.10, §2.4.12 Q2·Q9·Q10·Q11, §11 U17 ② 선행 행
  - design 42 v1.10: 확인 행 D-GR3(주), D-GR1·D-GR11·D-GR12(문구), D-ND5(N/A)
- 사용자 결정 원문: `wt/_drafts/user_decisions.md` '실행 사이 재사용 제거 (2026-10-15)', '원래 취지와 다른 판단 보고 규칙 (2026-10-15)', 'U-87~U-89·NFR4-F2·front 조회 (2026-10-15)'.
- 엔진 실측 기준
  - `git -C wt/nfr4-design diff --stat 34932a9 HEAD -- skills/` = 출력 0줄(엔진 파일이 34932a9와 같다).
  - **주의(실측)**: master `0538dec`(= `5870d80` + 문서 5개)는 34932a9 이후 엔진 **test** 파일 7개와 `.gitignore`가 바뀌었다(`authoring/SPEC_CONTRACT.md`, `tests/convergence/conftest.py`, `tests/integration/fixtures/u17_1b_s0_baseline.json`, `tests/integration/test_blas_thread_determinism.py`, `tests/integration/test_j_rules_library.py`, `tests/integration/test_s0_layer_9circuits.py`(+4줄), `tests/integration/test_spec_library_load.py`). 엔진 소스(tests 밖 `.py`)와 CONTRACT(`authoring/SPEC_CONTRACT.md` 제외)는 같다. 아래 test 줄 번호는 **master 5870d80 기준으로 다시 잰 값**이고, 엔진 소스 줄 번호는 34932a9 = 5870d80 기준이다.
- 경로 접두 `E/` = `skills/analog-gmid-design/gmid_engine/`.

> **B-1·B-2 반영 완료**: design 검증 차단 지적 두 건(삭제 이름의 이름별 grep 범위, U-90 조회 전용 읽기 경로)은 0538dec design 40 §2.4.3의 '완료 규칙' 표와 'front 조회 전용 읽기 경로' 표로 확정됐다. 이 초안 1.3.5·1.5·3.3은 그 표를 옮긴 것이다(새로 정한 규칙 없음).

---

## 2. interface card (공개 계약만 -- test 작성 주체는 소스를 보지 않고 이것만 쓴다)

### C1. 서명

```text
gmid_engine.pipeline.run_stage_a(topology_path, spec_path, lut, *, output_dir, pdk_decl, lut_rule_decl, supplies_v=None, structure_path=None) -> StageAResult
    (J-1 결정에 따라 pdk_decl·lut_rule_decl 줄이 바뀔 수 있다)
    pdk_decl_path / lut_rule_decl_path 키워드를 주면 TypeError(모르는 키워드).
StageAResult 칸 = (exit_code, status, report, report_paths, s1, spec, code_fp)   # 정확히 이 7개, 순서 그대로
StageAResult.report 키 집합(정상·정지 경로 모두 같은 13개) =
    {circuit, status, exit_code, count_budget, declared_comparison, stop_reasons, review_needed, views, applied_facts,
     ff_ratio_candidates, coupling, tables, orbit_matching_crosstab}

gmid_engine.search.build_search_context(dc_ctx, spec, settings, archive_root, pdk_decl, lut_rule_decl, model_error=(), *, code_fp) -> SearchContext
    s0 키워드를 주면 TypeError(모르는 키워드).
SearchContext.counters 키 집합 = {requests, kernel_calls, hits, fail_hits, outside_domain, recompute_same_key}
```

`run_stage_b`, `build_kernel_context`, `find_front`, `layer0_start`, `start_points`, `S3Archive` 생성자 서명은 바뀌지 않는다.

### C2. S0 파일을 어디에도 쓰지 않는다

- 단계 A → 단계 B → 커널 컨텍스트 → 탐색 컨텍스트 → `find_front` 사슬은 다음 밖에 파일을 만들거나 바꾸지 않는다: `output_dir` 아래 단계 보고서, `archive_root`가 None이 아니면 `<archive_root>/<context_fp>/` 아래 `evals.jsonl`·`runs.jsonl`·`snapshots/`, LUT 파생표 캐시 폴더(`GMID_LUT_TABLE_CACHE_DIR`, U-87).
- 특히 엔진 폴더(`gmid_engine/` 아래)에 파일·폴더를 만들지 않는다(바이트코드 캐시 `__pycache__` 제외). 환경 변수와 무관하다(엔진은 S0 위치 환경 변수를 읽지 않는다).

### C3. 반복 실행은 다시 계산한다, 출력은 비트 같다

- 같은 입력(topology·spec·LUT·PDK 선언·설정)으로 사슬을 두 번 돌리면(같은 프로세스에서 블록 계수를 `reset_stats()`로 비운 뒤, 또는 서로 다른 프로세스에서) **두 번 모두** S0 수준 writer 블록마다 `computes` = 1이다. 앞 실행이 남긴 것(디스크·S3)으로 계산을 건너뛰지 않는다.
- 같은 BLAS 설정(test 환경: `OPENBLAS_NUM_THREADS=1`, conftest가 고정)이면 두 실행의 다음 출력이 비트 같다: 단계 A·B 보고서 JSON, S0 수준 스냅샷의 필드 (kind, key, field) → `value_fp` 표(탐색 컨텍스트 `dc.base`), `context_fp`, `schema_fp`, `find_front` 결과(front 점 θ의 `float.hex`, `failed_eps`, 시간 칸을 뺀 `perf`), 그 실행이 S3에 붙인 줄(시간 칸을 뺀 내용).
- 시간 칸(비교에서 뺀다): `perf.wall_s`, `perf.eval_time_median_s`. 평가 예산은 선언해야 한다(`SearchSettings.eval_budget` 선언 -- 선언하지 않으면 벽시계로 유도되어 비결정, as-built `kernel.py:160-165`). 벽시계 정지(`stops_wall_budget`)가 0이 되도록 시간 예산을 넉넉히 준다.

### C4. 실행 안 G-10

- 한 실행(단계 A → B → 탐색 컨텍스트)에서 S0 수준 writer 블록마다 `computes` = 1, `recomputes_same_input` = 0. 단계 B·탐색 컨텍스트가 단계 A가 계산한 블록을 부르면 `reuses`로 센다.
- 블록 계수는 as-built `ComputeBlock.stats()`·`reset_stats()`로 읽는다(실행 경계 = `reset_stats()`. `RunCounters`는 U17 ② 몫이라 이 card에 없다).
- 탐색(`find_front`)에서 `perf.recompute_same_key` = 0. `perf.block_recomputes_same_input`의 판정 여부는 J-2.

### C5. S3는 출력만

- `archive_root`를 주면 S3 줄을 계속 쓴다(`evals.jsonl` = 커널 1회당 1줄, `runs.jsonl` = `find_front` 1회당 1줄, front·채택 스냅샷 파일).
- 두 번째 실행의 탐색은 첫 실행의 front 점을 시작점으로 쓰지 않고, 첫 실행(또는 누가 써 넣은) 실패 줄을 실패로 받지 않는다. 그래서 같은 입력이면 `<archive_root>/<context_fp>/`에 이전 내용이 있든(실패 줄을 손으로 넣은 경우 포함) 비어 있든 그 실행의 출력(C3 목록)과 그 실행이 새로 붙인 줄이 같다.
- 시작점 기록(`runs.jsonl` 줄 `starts`의 `source`)은 `layer0` 출처와 `"given"`뿐이다.

### C6. front 조회 읽기 경로 (U-90, design 40 §2.4.3 0538dec)

```text
gmid_engine.search.read_front_entries(run_dir) -> tuple[dict, ...]
    run_dir = <archive_root>/<context_fp> (= S3Archive(...).dir). runs.jsonl 을 줄 순서대로 읽어 각 줄의 front·pending_front 항목 dict 를
    원래 그대로(키 추가: 그 줄의 run_id, code_fp) 차례로 낸다. code_fp 로 거르지 않는다. 파일이 없으면 ().
gmid_engine.search.node_across_front(front, node, archive=None) -> tuple[NodeRow]     # 서명·동작 불변
    front 원소 = FrontPoint(실행 안 메모리) 또는 read_front_entries 가 준 dict. dict 는 archive.dir/<snapshot_ref> 파일을 읽는다.
    dict 원소가 있는데 archive 가 None 이면 ValueError. 노드가 없으면 KeyError. 커널 호출 0.
S3Archive 공개 메서드 = append_eval, append_run, write_snapshot (+ 속성 dir). read_snapshot·load_evals·load_runs 는 없다.
```

- 엔진 안(`tests/` 밖)에서 위 두 함수를 부르거나 import하는 곳은 없다(정의 파일과 `search/__init__.py` 재수출뿐). 결과는 graph 필드·시작점·실패 캐시로 들어가지 않는다. 구조 규칙 K가 이것을 강제한다(3.3).
- **test 주체 확인 항목**: 옛 `load_runs`는 `code_fp`가 같은 줄만 냈고 `read_front_entries`는 거르지 않는다. 또 `read_front_entries`는 `pending_front` 항목도 내고 항목마다 `run_id`·`code_fp` 키를 더한다. 지금 `tests/search/test_front_query.py:75`(`rec["front"]`를 넘겨 메모리 `fr.front`와 길이·순서 비교)와 `:83`(archive 없이 dict → `ValueError`)의 기대값이 이 계약에서도 맞는지 확인해야 한다(예: 같은 폴더에 다른 실행 줄이 있거나 `pending_front`가 비어 있지 않으면 `:75`의 길이 비교가 달라진다).

### C7. 결과 JSON `perf` 키

`find_front` `perf`(그리고 `runs.jsonl` 줄 `perf`) 키 집합 = `{requests, kernel_calls, hits, fail_hits, outside_domain, recompute_same_key, unique_keys, eval_time_median_s, wall_s, lut_memo_evictions, block_calls, block_reuses, block_computes, block_recomputes_same_input, n_starts, n_solves, eval_budget, eval_budget_source, frozen_columns, stops_eval_budget, stops_wall_budget}` (21개, as-built에서 `disk_hits` 하나만 빠짐).

### C8. 바뀌지 않는 것

LUT 파생표 디스크 캐시 동작, `ComputeBlock.code_hash` 값, `engine_code_fp()` 값, S3 줄의 `code_fp` 칸, `S3Archive` 쓰기 형식.

---

## 3. test 목록 (id / 위치 / 내용 / 계약)

위치는 제안이다. 파일 분할 규칙(1:1 대응, 교차 관심사 폴더 `tests/{structure,integration,...}`)을 따른다. 정확한 변경 범위는 test 작성 주체가 정한다.

### 3.1 base에서 red가 재현되는 test

| id | 위치(제안) | 내용 | 계약 | base 결과(예상 근거) |
|---|---|---|---|---|
| XR-1 | `tests/integration/`(9회로, slow) -- 아래 3.2의 `test_s0_layer_9circuits.py` 재작성본에 넣어도 된다 | 회로마다 같은 프로세스에서 사슬을 두 번(사이에 `reset_stats()`). 두 번째도 S0 writer 블록마다 `computes` = 1, `recomputes_same_input` = 0. writer 목록은 디스크 파일이 아니라 탐색 컨텍스트 `dc.base`의 graph S0 레코드 필드 writer에서 모은다 | C3, C4 | red: conftest가 세션 S0 폴더를 고정하므로 두 번째가 적중해 `computes` = 0(as-built `test_second_run_hits_...`가 단언하는 바로 그 성질) |
| XR-2 | `tests/integration/` | 하위 프로세스(환경 = 허용 목록으로 새로 만든 dict: PATH·SYSTEMROOT·TEMP/TMP(tmp 폴더)·OPENBLAS·`GMID_LUT_TABLE_CACHE_DIR`·PYTHON 설정만, `PYTHONDONTWRITEBYTECODE=1`)에서 회로 하나의 사슬을 돌리고, 실행 전후 엔진 폴더 파일 목록(`__pycache__` 제외)과 tmp 폴더 목록을 비교: 새 파일은 `output_dir` 보고서와(주면) S3 폴더와 표 캐시뿐 | C2 | red: S0 위치 환경 변수가 없으면 base는 `gmid_engine/.s0_snapshot/<키>.json.gz`를 만든다. **base red 재현은 격리 복제본에서만**(base는 그 checkout의 엔진 폴더에 쓴다) |
| XR-3 | `tests/search/test_kernel.py`(기존 `test_disk_failure_hit_...` 자리) | 같은 `archive_root`에서 θ 하나를 평가해 성공을 얻고, 그 θ의 실패 줄을 `evals.jsonl`에 손으로 붙인 뒤 새 컨텍스트로 같은 θ를 평가: 상태가 첫 평가와 같고 `kernel_calls` = 1 | C5 | red: base는 디스크 실패로 `STATUS_FAILED`, `kernel_calls` = 0 |
| XR-4 | `tests/search/test_start_points.py`(기존 `test_previous_run_front_points_come_first` 자리) | 같은 `archive_root`로 `find_front` 두 번: 두 번째 실행의 `starts` 기록에 `layer0`/`given` 밖 출처가 없고 시작점 수가 빈 S3 실행과 같다 | C5 | red: base는 `"s3"` 출처 시작점이 앞에 붙는다 |
| XR-5 | `tests/integration/`(slow, 9회로 중 탐색까지 가는 회로) | 빈 S3 실행 A, 같은 입력의 실행으로 채운 S3 위 실행 B(새 프로세스 또는 `reset_stats()`): A와 B의 C3 출력과 '그 실행이 붙인 줄'이 같다 | C3, C5 | red: base는 B가 이전 front 점·실패 줄을 읽어 시작점·평가 수가 달라진다 |
| XR-6 | `tests/pipeline/test_stage_a.py` | `StageAResult` 칸 목록 정확히 7개(C1), 보고서 키 집합 정확히 13개(정상·`A1_load`·`A2_build_s1` 정지), `pdk_decl_path=` 키워드는 TypeError | C1 | red: base는 칸 `s0`·키 `s0_snapshot`가 있고 경로 인자가 필수 |
| XR-7 | `tests/search/test_search_context.py`·`test_find_front.py` | `counters` 키 집합 6개, `perf` 키 집합 21개(양성 형식), `s0=` 키워드 TypeError | C1, C7 | red: base는 `disk_hits` 키가 있고 `s0=`를 받는다 |

위 표는 양성 형식(키 집합·칸 목록 정확히 같음)으로 적었다. 1.3.5 범위상 `s0_snapshot`·`disk_hits`·`disk_failures`·`STAGE_B_WRITERS`·`pdk_decl_path`·`lut_rule_decl_path`는 `tests/`에서도 grep 0이어야 하므로 이름 문자열로 '없다'를 단언하는 음성 형식은 쓰지 않는다.

### 3.2 삭제·고칠 test (design 목록 + master 재측정 -- 5870d80 = 0538dec test 파일)

| 파일 | design 처리 | master 실측 | 비고 |
|---|---|---|---|
| `tests/core/test_snapshot_codec.py` | 삭제 | 이름 hit 32 | |
| `tests/core/test_s0_slot.py` | 삭제 | 9 | |
| `tests/core/test_type_registry.py` | 삭제 | 14 | |
| `tests/integration/test_code_hash_checkout.py` | 삭제 | 테스트 `:124·135·139·149·155` | J-4 |
| `tests/integration/test_s0_layer_9circuits.py` | design: `:326` test와 S0 폴더 조작(`:56·152·175-190`)만 | master 줄: S0 폴더 `:60`, 경로 인자 `:159-160`, `s0=` `:140`, `_run` `:174-` , 두 번째 실행 test `:330`. **추가 실측**: 디스크 파일을 읽는 test가 더 있다 -- `test_independent_decoder_roundtrips_design_format`(:231, 코덱 형식 디코더), `test_s0_fields_present_with_single_block_writer`(:243, `_doc` = 파일), `test_s0_file_values_roundtrip_bit_identical`(:291), `test_cold_run_computes_each_s0_block_once`(:317, writer 목록을 `_doc`(파일)에서 모은다), `test_junction_source_value_has_no_checkout_path`(:421, 파일의 `junction_source` 칸) | 파일 단위 재작성 범위. 남길 성질: 필드 존재·writer 유일성, 첫 실행 `computes` = 1(→ XR-1), 보고서·필드 값 base 불변(`:350·362·408`), junction 경로 없음(메모리 값으로) |
| `tests/search/test_start_points.py:61-` `test_previous_run_front_points_come_first`, 모듈 docstring `:1` | 삭제 | | XR-4로 대체 |
| `tests/search/test_kernel.py:147-169` `test_disk_failure_hit_same_code_and_invalid_when_code_differs`, `:72` 계수 dict의 `disk_hits` | 삭제·고침 | | XR-3으로 대체 |
| `tests/search/test_search_context.py:21`(COUNTERS), `:76`(`disk_failures`) | 고침 | `:21`은 design 목록 밖 | XR-7 |
| `tests/search/test_find_front.py:19` `PERF_KEYS` | (design 목록 밖) 고침 | 실측 추가 | |
| **`tests/search/test_layer0_center.py`** | (design 목록 밖) | `write_failures`(:144, `evals.jsonl`에 실패 줄을 손으로 씀), `run_l0(inject=)`(:170-177), 이 경로를 쓰는 test 3개: `test_single_current_first_probe_direction_zero`(:335, `:345` `disk_hits >= 1` 단언), `_window_with_probe_failures`(:357) 경유 `test_repair_bisection_count_and_points`(:373 부근)와 `:417` 부근 test | 디스크 실패 주입으로 층 0 수리 경로를 몰아가는 test다. 주입 수단이 사라져 **3개가 깨진다**. 다른 주입 수단(엔진 공개 경로 안)은 test 주체가 정한다 -- 엔진에 주입 구멍을 새로 만들지 않는다 |
| `tests/search/test_s0_fields.py:51` `STAGE_B_WRITERS` 단언 | (design 목록 밖) 고침 | 실측 추가 | |
| `tests/search/test_archive.py:2·71-72` | 고침(design 0538dec): `:71-72`의 `s.archive.read_snapshot(entry["snapshot_ref"])` 왕복 단언을 front_query의 스냅샷 읽기로 옮긴다, `:2` docstring '스냅샷 왕복(read_snapshot)' | `read_snapshot` 삭제로 깨진다 | 옮기는 방법은 **test 주체 선택**: (가) 비공개 `_read_snapshot_file`을 test에서 import (나) `node_across_front`로 왕복(파일 항목 → NodeRow를 메모리 스냅샷과 대조). 규칙 B(다른 파일의 `_` 이름 import 금지)의 검사 대상은 엔진 소스(`tests/` 제외)라 (가)도 구조 규칙에 걸리지 않는다 |
| `tests/search/test_front_query.py:1·25-26·75·83` | 고침(design): 서명 그대로, 파일 front 항목을 `runs.jsonl` 직접 읽기(`:25-26`) 대신 `read_front_entries(archive.dir)`로 얻음 | C6 '확인 항목' -- `code_fp` 거르기 없음·`pending_front` 포함·키 추가가 `:75` 길이 비교와 `:83` 기대에 맞는지 확인 | |
| 새 `tests/search/test_front_entries.py` | 신규(design, 규칙 H) | | 3.3 K-4 |
| `tests/conftest.py:52-62` | 삭제 | | |
| `tests/pipeline/test_stage_a.py` | 경로 인자·`s0_snapshot`·적중 단언, `:481-482`(`STAGE_B_WRITERS`·`r.s0.save`), `:710`(진입 대조 거부), `:885-886`(등록부 이름) | hit 63 | |
| `tests/pipeline/test_stage_a_report.py`(5), `test_stage_a_loop_cut.py`(2), `test_stage_b.py`(3, `:248-249` 등록부) | 고침 | | |
| `tests/integration/test_stage_a_library.py`(7), `test_stage_b_library.py`(2), `test_j_rules_library.py`(6, master `:61·129·161·177·179·199`) | 고침(경로 인자) | | |
| `tests/integration/test_blas_thread_determinism.py`(master `:79-80` 경로 인자, `:106` 환경 변수) | 고침(이 card 몫만: 경로 인자·S0 환경 변수) | | xfail·스레드 고정은 card 2 |
| `tests/search/conftest.py`(1), `test_cell_floor.py`(2), `u13_hand.py`(1), `u13_real.py`(2), `tests/metrics/gb4_hand.py`(1), `tests/sizing/test_current_basis.py`(2) | 고침 | | |
| `tests/search/test_start_intervals.py:216-217`, `test_constraint_classes.py:18·81` | 등록부 단언 삭제 | | |
| `tests/core/test_engine_code_fp.py` | S0 키 문구만 | | |
| `tests/core/test_pdk_decl.py`(이름 hit 8) | **바꾸지 않는다** -- `read_pdk_decl`의 살아 있는 거부 사유 | | 1.3.5 범위 밖(design 확정) |
| `tests/integration/fixtures/u17_1b_s0_baseline.json:2` `_source`의 `s0_snapshot` 언급 | **이 card에서 고치지 않는다**(1.3.5 범위 밖, design: NFR-4 기준선 재측정 때 다시 씀) | | |
| design 목록에 있으나 master에서 이름 hit 0 | `tests/generality/pipeline.py`(`code_fp=` 호출 -- 불변), `tests/sizing/test_bracket_root.py`(`s0=`는 지역 변수, 무관) | | 변경 불필요로 보인다 |

### 3.3 구조 규칙 K (U-90 import·참조 금지, design 40 §2.4.3 '검사' 행 0538dec)

design이 정한 것: 새 구조 규칙 **K**(글자 J는 J 공동분석과 겹쳐 건너뜀). `E/tests/structure/structure_checks.py`에 `check_k`, `E/tests/structure/README.md` 규칙 표에 K 행, 픽스처 `E/tests/structure/fixtures/rule_k/{bad,good}/gmid_engine/`, `test_structure_rules.py`와 `test_structure_rules_reject_fixtures.py`에 K. 판정은 1.5 '검사(규칙 K)' 행(K-a·K-b·K-c, 허용 파일 셋).

| id | 위치 | 내용 | 계약 |
|---|---|---|---|
| K-1 | `test_structure_rules.py` `test_rule_k_...`(진짜 엔진 트리) | `check_k(engine_root)` 위반 0, `report(n, len(v))`로 대상 수 보고 | C6 |
| K-2 | `test_structure_rules_reject_fixtures.py` `EXPECTED_BAD["rule_k"]`와 good 픽스처 | bad 트리 = K-a·K-b·K-c를 하나씩 이상(design 예: `pipeline/run.py`의 `from gmid_engine.search import node_across_front`, `search/start_points.py`의 `from .front_entries import read_front_entries`, `search/kernel.py`의 `reader = sctx.archive.read_snapshot`). 기대 위반 목록은 픽스처 줄을 손으로 읽어 적는다. good 트리 = 허용 파일 셋 안의 정의·재수출·`_read_snapshot_file` 사용은 통과 | C6 |
| K-3 | base red 여부 | base 엔진 트리에서 K-1은 **red가 아니다**(base에는 허용 파일 밖 참조가 없다 -- `read_snapshot`은 허용 파일 `front_query.py` 안에서만 쓰인다). 공허하지 않음 증거는 K-2가 맡는다 | -- |
| K-4 | `tests/search/test_front_entries.py`(규칙 H 1:1) | `read_front_entries`: 파일 없음 `()`, 줄 순서·한 줄 안 `front` 다음 `pending_front`, 원 dict 보존 + `run_id`·`code_fp` 추가, `code_fp`가 다른 줄도 낸다(거르지 않음) | C6 |

구현 주의(최종 검증 메모):
1. K test 함수 이름은 **`rule_k_` 접두**로 쓴다(`test_rule_k_...`). 이유: `E/tests/authoring/test_topology_load.py:83` `test_cases_cover_all_32_rule_kinds`가 `-k rule_k`에 걸린다 -- `rule_k`로만 고르면 이 test도 함께 뽑힌다. 이름을 정한 뒤 `-k rule_k_`·`check_k`·`rule_k/` grep으로 **식별자 충돌 0건**을 확인해 보고한다.
2. `tests/structure/README.md` 규칙 표(37~47행, A~I)에 K 행을 더할 때 **'J 없음' 행**(사유: J 공동분석·`test_j_rules_library.py`와 겹쳐 건너뜀)도 한 줄 넣는다. 위반 픽스처 표(98~108행)에도 K 행.
3. 기존 형식(실측): 검사기는 엔진을 import하지 않고 AST만 읽는다(`engine_files`·`parse`·`rel`·`resolve_from`), 규칙별 test는 `_assert_clean`, 공허하지 않음 = 가짜 트리 + 손으로 적은 `EXPECTED_BAD`.
4. 누가 쓰나는 J-6.

---

## 4. 감사(audit) 측정

audit은 격리 복제본(`<W>/xrun-removal-audit`)에서만 잰다. base red 재현(XR-2)은 base 복제본의 엔진 폴더에 S0 파일을 쓰므로 반드시 복제본에서.

| # | 측정 | 방법 | 합격 |
|---|---|---|---|
| A-1 | 실행 안 G-10 | 9 library 회로마다 단계 A → B → 커널 컨텍스트 → 탐색 컨텍스트(단계 A·B ok 회로) → `layer0_start`·`find_front`(선언 평가 예산). `reset_stats()` 뒤 S0 writer 블록(탐색 컨텍스트 `dc.base`의 graph S0 레코드·`device: start.*` writer)별 `computes`·`recomputes_same_input`, `perf.recompute_same_key`, `perf.block_recomputes_same_input` | S0 writer `computes` = 1·`recomputes_same_input` = 0, `recompute_same_key` = 0. `block_recomputes_same_input`은 J-2 결정대로(판정 또는 보고) |
| A-2 | 삭제 이름 grep 0 | 1.3.5 표의 이름마다 그 범위에서 `rg -nw`(history·design '옛' 문장 제외). 범위 밖 남는 쓰임(`core/pdk_decl.py:340·592`, `core/CONTRACT.md:317·372·376·420`, `tests/core/test_pdk_decl.py`, 기준선 픽스처 `_source`)이 그대로 있는지도 확인. 추가: 엔진 소스 `rg -nw read_snapshot` = 0 | 범위 안 0, 범위 밖 불변 |
| A-3 | 새 실행 두 번 비트 동일(9회로) | 서로 다른 프로세스 둘(같은 OPENBLAS 1), 각각 빈 S3·빈 출력 폴더. 비교: 단계 A·B 보고서 JSON 바이트, `dc.base` 필드 `value_fp` 표, `context_fp`·`schema_fp`, `find_front` 결과(front θ hex, `failed_eps`, 시간 칸 뺀 `perf`), S3 줄(시간 칸 뺀 내용). 각 프로세스에서 S0 writer `computes` = 1 | 9/9 비트 같음, 두 프로세스 모두 계산 > 0 |
| A-4 | S3 이전 내용 유무 무관 | 회로마다 (i) 빈 S3로 실행 → 결과 R1, (ii) 그 S3 폴더에 R1 실행 줄이 남은 채로 새 프로세스 실행 → R2, (iii) 실패 줄을 손으로 넣은 S3 위 실행 → R3 | R1 = R2 = R3(C3 목록 + 그 실행이 붙인 줄) |
| A-5 | S0 파일 0 | XR-2 방식으로 엔진 폴더·TEMP 전후 목록 | 새 파일 = 보고서·S3·표 캐시뿐 |
| A-6 | 바뀌지 않아야 할 것 | `git diff base..head -- E/lut/table_cache.py E/core/compute_block.py`(code_hash 부분), `node_across_front` 서명(AST 인자 목록 `front, node, archive=None`) | 0줄, 서명 같음 |
| A-6b | 규칙 K | `pytest tests/structure -k rule_k_`(엔진 트리 위반 0, `rule_k` 픽스처 기대 목록과 정확히 같음), `-k rule_k_`가 `test_cases_cover_all_32_rule_kinds`를 고르지 않음(식별자 충돌 0건) | 통과 |
| A-7 | red 재현 | base에서 XR-1~XR-7 실행 | 각각 red(XR-2는 복제본에서) |
| A-8 | 전체 suite | `python -m pytest -q gmid_engine/tests -p no:cacheprovider`(not slow) + 이 card가 바꾼 slow test, `tests/structure` | 0 failed, 구조 위반 0 |
| A-9 | 실행 시간(보고만) | A-3의 사슬 시간 | 판정에 쓰지 않음(design §2.4.3 '실행 시간 영향' 402.8 s 대조용) |

---

## 6. 공통 브리핑 (이 card의 code·test·audit agent 필독, 1쪽)

> `U17_STEP1_COMMON_BRIEF.md`를 이 card에 맞춘 판이다.

base = master `0538dec`(계획 v6.10, design 40·41·42 v1.10 최종본 병합, 엔진 코드는 그 전과 같다). design: `docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md` v1.10 §2.4.1·§2.4.3·§2.4.5·§2.4.9·§2.4.12·§11, `…42-gap-checklist.design.md` D-GR3. 계획: `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` NFR-2·WP-23·U-87~U-90. 엔진: `skills/analog-gmid-design/gmid_engine/`. 사용자 결정 기록: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/user_decisions.md`(읽기만). card: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/engine/XRUN_REMOVAL_CARD_DRAFT.md`(code·audit는 1~5절, test는 2·3절만 -- 소스 열람 금지).

### 절대 규칙
1. **design 그대로 구현한다. as-built 결정 금지.** design에 없는 것을 정해야 하거나 design이 모순·불가능하면 그 자리에서 **멈추고 보고**한다(무엇이, 어느 절이, 선택지). 범위 축소·대체 금지. card 1.8의 J-1~J-4·J-6은 오케스트레이터가 결정을 알려 주기 전에는 손대지 않는다.
2. **graph 단일 정본(DEC-83, 40 §2.4)**: 설계 값은 graph 필드에만. graph 밖 허용 저장소는 **셋뿐**이다 -- (a) LUT memo(순수 함수, 디스크 LUT 파생표 캐시 포함 -- U-87로 실행 사이 유지), (b) S3 기록(evals·runs jsonl·`snapshots/` = **출력**, 엔진은 실행 사이에 읽지 않는다)과 그 실행 안 메모리 캐시, (c) 실행 계수. **S0 스냅샷 영속화는 없어졌다.** 새 dict 캐시·객체 칸·사본·디스크 캐시 금지.
3. **계산값 재사용 = 실행 안에서만**: 사용자 취지 "처음 topology를 실행할 때는 항상 계산하고 그 계산된 값이 나머지 최적화를 진행할 때 재사용". 한 실행 안에서는 입력이 같으면 다시 계산하지 않는다(필드가 곧 캐시). 실행 사이에는 설계 값을 재사용하지 않는다. 이 취지에서 벗어나는 판단이 필요하면 멈추고 '원래 취지와 다름'으로 보고한다(사용자 규칙 2026-10-15).
4. **틀린 구조는 전체 재작성**. 대체한 옛 코드·경로·CONTRACT 문장은 **같은 변경에서 삭제**(만들면 반드시 배선).
5. **front 조회(U-90)는 card 1.5 그대로**: 새 `search/front_entries.py`의 `read_front_entries(run_dir)`, `front_query.py` 비공개 `_read_snapshot_file`, `node_across_front(front, node, archive=None)` 서명 불변, `S3Archive.read_snapshot` 삭제, 엔진 안 호출 0(구조 규칙 K). K test 이름은 `test_rule_k_` 접두(식별자 충돌 0건 확인), README 규칙 표에 K 행과 'J 없음' 행. code 주체는 함수 레지스트리 §2(`docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`)에 `read_front_entries` 행을 같은 변경에서 더한다.
6. **건드리지 않는 것**: LUT 파생표 디스크 캐시(`lut/table_cache.py`, `GMID_LUT_TABLE_CACHE_DIR`, test 쪽 `lut_table_cache_tests`, U-87), `ComputeBlock.code_hash`(U-88), NFR-4(BLAS 고정·`env_fp`·BP 규칙·비교기·test 스레드 고정 -- card 2), `RunCounters`·`S3Index`(U17 ②), `core/pdk_decl.py`의 거부 사유(살아 있는 검사).
7. **상수 발명 금지**(WP-03), **회로 이름·소자 이름 코드 금지**(topology 무관).
8. **파일 분할 규칙**: 파일 하나 = 한 개념, (A) 독립 진입점 1개, (B) `_` helper는 그 파일만, (C) `@compute_block` 파일당 ≤ 1, (D) test는 `tests/<pkg>/test_<file>.py` 1:1. 지운 파일은 `_module_map.py`에서도 지운다. 끝나기 전 `tests/structure` 통과(위반 0).
9. **작성자 ≠ 검증자**: code agent는 test·기대값을 쓰지 않는다(옛 test가 깨지면 고치지 말고 목록으로 보고). test agent는 피검 코드를 불러 기대값을 만들지 않는다. 같은 커밋에서 코드와 기준을 함께 바꾸지 않는다.

### 실행 환경·git 가드
- python: `/c/Python314/python.exe`(bash에서 `timeout` 래퍼 금지). 실행 위치 `<worktree>/skills/analog-gmid-design`, `python -m pytest -q gmid_engine/tests/<경로> -p no:cacheprovider`. test conftest가 `OPENBLAS_NUM_THREADS=1`을 고정한다.
- 전체 suite는 끝에 한 번만. 긴 실행은 결과를 파일에 쓴다(`C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_xrun_<role>/run.txt`, 케이스마다 append).
- git: 항상 `git -C <자기 worktree>`, 스크립트는 `set -e`. 다른 worktree·master를 건드리지 않는다. reset --hard·다른 브랜치 checkout·push·merge 금지. 커밋은 자기 브랜치에만. **다른 worktree의 `.s0_snapshot/` 폴더를 지우지 않는다**(사용자 승인 대상, card 5.2).
- 커밋 메시지 끝: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` 와 `Claude-Session: https://claude.ai/code/session_012FxFP7YSWEBBCB9rmBQjLL`.
- 임시 파일은 `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_xrun_<role>/`(자기 것만).

### 최종 보고(한국어) 필수 항목
1. 구현·작성한 design 절과 상태(구현됨/부분/못함 + 사유).
2. 멈춤·보고 항목(as-built 결정이 필요했던 곳, '원래 취지와 다름' 후보).
3. 지운 옛 코드·경로(파일:줄), 바뀐 배선(호출부 파일:줄), 남은 소비자 grep 결과.
4. graph 단일 정본 자기 점검: graph 밖 저장소가 허용 셋뿐인지(옛 (d) 0), 40 §2.4.8 소유표 대조.
5. 계산값 재사용 자기 점검: S0 writer 블록 `computes` = 1·`recomputes_same_input` = 0, 실행 사이 읽기 경로 0.
6. `tests/structure` 결과(규칙별 대상·위반 수), 관련 test 결과, 깨진 옛 test 목록.
7. 커밋 해시.



## 사용자 결정 (2026-10-15 "권고대로 진행해")
- J-1: run_stage_a 의 pdk_decl·lut_rule_decl 인자(S0 키에만 쓰이던 것)를 지운다. 탐색 준비(build_search_context)의 같은 이름 인자는 그대로.
- J-2: _wire_sweep_memo 첫 평가 버림(실행 안 중복 계산 가능)은 이 card 범위 밖, 후속 card XRUN-F1 에서 측정·수정. 이 card 의 G-10 판정은 S0 블록과 recompute_same_key 만.
- J-3: 옛 .s0_snapshot 폴더 6곳·TEMP 빈 폴더 삭제 승인 -- 오케스트레이터가 card 병합 뒤 정리한다(역할 agent 는 지우지 않는다). .gitignore:39 는 이 card 에서 지운다.


## J-5 (사용자 2026-10-15 "권장대로 해") -- 수리 경로 test 대체 지점 (공개 계약)
- 대체 지점: 모듈 속성 `gmid_engine.search.layer0_center.evaluate` (서명 `evaluate(sctx, theta, cells, parent=None, origin=(), geometry=None) -> EvalResult`).
  layer0_center 는 시작점·시험 점·수리 평가를 모두 이 모듈 이름으로 부른다. code 쪽은 이 이름·서명·호출 방식을 바꾸지 않는다.
- test 가 쓸 수 있는 공개 타입: `gmid_engine.search.search_values.EvalResult`(칸: key, theta, status, evaluation, objectives, constraints, cone, failure, seq, unmeasured, warnings),
  `STATUS_FAILED`(search_values), `gmid_engine.core.failure_record.FailureRecord(failure_class, devices, margin, detail)`, `gmid_engine.sizing.REASON_NO_ROOT`.
- 방식: wrapper 가 진짜 evaluate 를 부르고, 지정 점(θ 키)에서는 그 결과를 dataclasses.replace 로 status=STATUS_FAILED·failure=합성 FailureRecord 로 바꿔 돌려준다
  (또는 진짜 evaluate 를 부르지 않고 합성 결과를 만든다 -- 둘 중 무엇을 쓰고 커널·S3 줄 수 단언을 어떻게 바꾸는지는 test 작성자가 정하고 주석에 적는다).
- 대상: test_layer0_center.py 의 디스크 주입 test 3개와 run_l0(inject=)·write_failures 의 디스크 주입 helper(삭제). disk_hits 단언은 지운다.
