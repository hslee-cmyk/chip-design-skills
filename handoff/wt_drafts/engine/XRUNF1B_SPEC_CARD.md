# XRUN-F1 card B (색인 + 부분 스냅샷 + 계수) spec card (card id `xrunf1b`)

- 작성: 2026-10-16. 개정 2026-10-16: design 40 card B 개정 병합(`083b103`)과 사용자 승인 X-21("card B는 승인")을 반영해 J 전부를 확정값으로 바꾸고 멈춤을 풀었다. 읽기 전용 실측과 card 초안만 담았다. 엔진·test·git 브랜치는 고치지 않았다.
- **card base = `083b103`**(design 40 card B 개정 병합 master). 엔진 `gmid_engine/`은 `b0077a8`(card A 병합) 뒤 `lut/CONTRACT.md` 한 줄(oracle-portability 문언) 말고 바뀌지 않았다(`git diff --stat 2f684d6 083b103 -- skills/analog-gmid-design/gmid_engine` 0줄, b0077a8 → 2f684d6은 lut/CONTRACT 1줄). 그래서 아래 엔진 줄 번호(b0077a8에서 잰 것)는 083b103에서도 같다.
- 실측 방법: 저장소를 `git archive`로 저장소 밖(scratchpad)에 풀어 grep·AST로만 셌다(실행 없음). 호출부 수는 AST `Call` 노드 수(함수 이름·속성 이름 일치), 루프 안 `block(snapshot, *extras)` 같은 간접 호출은 따로 적었다.
- design 근거(줄 = `083b103`의 `docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md`): §2.4.4 이식 API·입력 버전 정본·호출 규칙(310~359행), §2.4.5 블록 결과 색인 표 -- 특히 '수명'(376행: `open_run`·규칙 M·키·디스크)·'전달'(377행)·'상한'(378행)·fail-closed(380행)·조회 API와 생성자 문단(382~402행), §2.4.7 `KernelContext` 행·`LayoutResult` 행(483행)·'실패 평가의 부분 스냅샷'(487~497행), §2.4.9 계수·`RunCounters`·`PerfCounters`(556~600행), §2.4.14 (3) 재작성 범위(835~869행)·(4) 삭제 목록(870~885행)·(5) B·C 행(891~892행). 42 D-XR3(규칙 M 문장 포함)·D-XR4·D-XR5. 경위: 계획 history `docs/01-plan/features/gain-budget-gmid-sizing.history.md` H1 끝 네 행(card B 보완, 구조로 막음, 규칙 M 세부, 단순화).
- 계획 근거: `docs/01-plan/features/offset-strategy.plan.md` PD-7·PD-8(S-8), XS-7(S-5, 문언은 card B 보완 기준으로 정합).
- 사용자 결정 원문: `wt/_drafts/user_decisions.md` X-1~X-19, S-7·S-8, **X-20**(2026-10-16 "권고대로 구조로 막는 방향으로 진행해"), **X-21**("card B는 승인").
- card A 판정 기록(기준 자료): `.ai/verification/xrunf1a.json`, `.ai/verification/xrunf1a/a2_a4_a6_a10.json`(A-6).
- 경로 접두 `E/` = `skills/analog-gmid-design/gmid_engine/`.

> **멈춤 해제(2026-10-16)**: 옛 1.10(PD-8)과 1.8 J-2~J-14는 design 40 개정(브랜치 `xrunf1b-design` `7b104cc`·`1ce04cb`·`b4929a2`·`add3f51`·`06bd901`·`3670ad4`, 병합 `083b103`)으로 정해졌고 사용자가 승인했다(X-21). code·test 착수 가능.

---

## 1. spec card

### 1.1 목표 (사용자 의도 원문)

- 취지 원문(2026-10-15): "계산 재사용은 처음 topology를 실행할 때는 항상 계산하고 그 계산된 값이 나머지 최적화를 진행할 때 재사용되게 한다는 것이 원래 취지였어".
- X-1 (3) 실행 수명 재사용 색인(값 사본 금지, 상한 = §2.4.9 증거 집합 식), X-2 실행 수명 보존, X-3 실패 평가 부분 스냅샷, X-5 계수 범위 = 모든 (블록, 분할), X-7 `donors` 필수, X-9 결정적 도메인 실패 등록·재연(판정 1 엄격), X-10 evals 실패 줄 `snapshot_fp`, X-11 U17 ② 항목 앞당김, X-12 색인 수명 = 단계 A부터, X-13 과도기 참조 칸.
- X-20(2026-10-16) 우려 원문: "원래 취지와 다른 실행에 색인을 넘기는 문제가 이전에 폐기했던 아주 큰 hash코드 redundancy를 다시 만드는 것이 아닌지 걱정돼." → 실행 사이 비공유를 **구조로** 막는다(`open_run` 단일 생성·규칙 M·색인 키에 실행 바깥 지문 금지·디스크 저장 금지).
- 목표 한 줄: **한 실행 안에서 같은 (블록, 분할, 입력 버전)은 계보와 무관하게 한 번만 계산한다(두 번째부터 같은 lineage 재사용·이식·실패 재연). 실패한 평가도 그때까지 계산한 블록 결과를 남긴다. 색인과 계수는 실행 하나에만 살고, 다른 실행으로 넘어가는 길은 구조 test가 막는다.**

### 1.2 구현하는 design 절

| design 절 | 내용 | 이 card |
|---|---|---|
| §2.4.4 API(310~343행) | `graft(target, block, part, donor, input_version)`(part `"*"`만, 아니면 `ValueError`, fail-closed (2) 검사 주체), `Donors` 네 추상 메서드, 입력 버전 정본 `ComputeBlock.input_version(snapshot, *extras)`(`__call__`은 비공개 helper로 (투영, 버전) 한 번), `__call__(snapshot, *extras, donors, counters)` 필수 키워드 | 구현 |
| §2.4.4 호출 규칙·실패 재연(345~349행) | 판정 1 같은 lineage → 2 이식 → 실패 재연 → 3 계산, `from_record` 두 기반 | 구현 |
| §2.4.5 표 '수명'(376행) | `open_run() -> (donors, counters)`(`search/open_run.py`), 생성자 비공개 계약, 구조 규칙 M(M-a·M-b·M-c·M-d·M-f, M-e 없음), 색인 키 = (블록, 분할, 입력 판)만, 디스크 저장 금지 | 구현 |
| §2.4.5 '전달'(377행) | `run_stage_a(..., *, output_dir, donors, counters, supplies_v=None, structure_path=None)`, 감쌈 함수 필수 키워드, `KernelContext`·`sctx`를 받는 함수는 서명 불변 | 구현 |
| §2.4.5 '상한'(378행) | `perf.block_index_entries`·`block_index_bound`(card B E_total 식, card C가 지움) -- 보고만 | 구현 |
| §2.4.5 fail-closed(380행)·조회 API·생성자 문단 | (1)~(4)·(6), `S3Index()` 비공개·`entry_count()` | 구현 |
| §2.4.7 `KernelContext`·`LayoutResult`·부분 스냅샷 | 참조 칸 둘, `computed_blocks` 뜻 정정(코드 무변경, docstring·CONTRACT 문구만), `partial` 칸 + `core/failure_partial.py` `attach_partial(exc, snapshot)` | 구현 |
| §2.4.9 | `RunCounters`(`record`·`result`·`snapshot`), `PerfCounters`(`blocks`·`block_totals`), 계수에 `replays`, `perf.blocks`·`block_totals`, 옛 네 칸 삭제, 판정 1·5 | 구현 |
| §2.4.14 (3)(4)(5) B 행 | 재작성 범위·삭제 이름·완료 조건·test 초안 | 범위·완료 조건 |
| 42 D-XR3·D-XR4·D-XR5 | MISS/DEV → 완료 시 OK | 확인 행 |

범위 밖: 분할 선언·`write(name, part, ...)`·`block_version(name, part)`(U17 ②), `S3Index.get`·`failure`·`local`·`solved`와 `sctx.cache`·`computed_keys` 대체(U17 ②), 색인 상한 등록 검사 (5)·E_total 계산 자리 하나(card C -- card C가 card B의 `find_front` E_total 식과 `open_run` 서명·호출부를 같은 변경에서 고친다), B_S0(OS-5), 실행 계획 세션 열기(OS-2 -- M-a 허용·M-c 예외를 OS-2 design이 더한다), `RunCounters`의 LUT memo·디스크 파생표 계수(U17 ②·③), `fd_step` 원인 칸(U17 ②), `_Unmemoized` 제거·memo 인스턴스 하나(U17 ③), 구조 규칙 G 확장(U17 ③), `_wire_sweep_memo`의 `centre_start` 이중 호출(card A J-O5 개선 후보).

### 1.3 삭제·변경 목록 (083b103 실측 -- 엔진 줄 = b0077a8과 같음)

#### 1.3.1 엔진 소스

| # | 대상 | 위치(실측) | 처리(design) |
|---|---|---|---|
| B1 | 새 `E/core/run_counters.py` | 신규 | 진입점 `RunCounters`(`record(block, part, outcome, input_version)`·`result(block, part, input_version, ok)`·`snapshot() -> PerfCounters`), 같은 파일 frozen `PerfCounters(blocks, block_totals)`(진입점이 참조 -- 규칙 A 진입점 아님). 생성자는 비공개 계약(`open_run`만 부름) |
| B2 | 새 `E/core/donors.py` | 신규 | `Donors(abc.ABC)`: 추상 `find`·`register`·`find_failure`·`register_failure`. 상태·생성자 인자 없음 |
| B3 | 새 `E/core/graft.py` | 신규 | `graft(target, block, part, donor, input_version)`: part `"*"` 아니면 `ValueError`, `donor.block_version(block.name) != input_version`이면 `ValueError`(fail-closed (2)의 검사 주체), 아니면 donor의 `block.writes` 열을 `target.write(block.name, input_version, 그 행)`. 투영을 다시 만들지 않는다 |
| B4 | 새 `E/search/s3_index.py` | 신규 | `S3Index(Donors)`: 네 메서드, fail-closed (3)(4)(6), 읽기 `entry_count() -> int`. 생성자 `S3Index()` 인자 없음·비공개 계약 |
| B5 | 새 `E/search/open_run.py` | 신규 | 진입점 `open_run() -> (donors, counters)` = 새 `S3Index`와 새 `RunCounters`의 쌍. 두 객체의 유일한 생성 자리(규칙 M (M-b)) |
| B6 | 새 `E/core/failure_partial.py` | 신규 | 진입점 `attach_partial(exc, snapshot) -> None`: `exc`가 `InfeasibleSizingError` 하위가 아니거나 `snapshot`이 `GraphSnapshot`이 아니면 `TypeError`, `exc.partial`이 이미 있으면 바꾸지 않음 |
| B7 | `ComputeBlock` | `E/core/compute_block.py:92-101`(`BlockStats`), `:119-164`(계수 칸 `:129-133`, `__call__` `:135-152`, `stats` `:154-156`, `reset_stats` `:158-164`), docstring `:20-21` | **단위 재작성**: `__call__(snapshot, *extras, donors, counters)`, 공개 `input_version(snapshot, *extras)`(식 = `:136-137` 그대로), 비공개 helper 하나로 (투영, 버전), `BlockStats`·`stats`·`reset_stats` 삭제. 코드 해시 `:32-89` 그대로 |
| B8 | 예외 기반 | `E/core/failure_errors.py:20-27`, `:60-67` | 부분 수정: 칸 `partial`(`InfeasibleSizingError.__init__`이 None), classmethod `from_record(record)`를 `InfeasibleSizingError`·`SchemaRejectedError` 둘 다에. 데이터 선언 모듈 유지(`_module_map.py:228` kind `"data"`, `structure_checks.py:241-249·252-272`) |
| B9 | `seal_versions` | `E/sizing/seal_versions.py:20-21`(입력 버전 식 사본) | 부분 수정: `block.input_version(snapshot, *extras)` 호출로, 사본 삭제. 봉인 4 판정 그대로 |
| B10 | `KernelContext` | `E/sizing/s2_values.py:431-439` | 참조 칸 `donors`·`counters`(과도기) |
| B11 | `build_kernel_context` | `E/sizing/kernel_context.py:51`, 블록 `:80-88`(7개), 생성 `:89` | 키워드 `donors`·`counters` 필수, 블록에 넘기고 `KernelContext`에 둔다. 호출부 소스 `pipeline/stage_b.py:152` |
| B12 | `run_kernel` | `E/sizing/kernel_run.py:53`, 루프 `:71-73`·`:82-85`, `seal_dc` `:88` | `ctx`의 두 객체를 블록에, 블록 단계마다 후보 실패 클래스를 이름으로 잡아 `attach_partial`(그 블록에 들어간 스냅샷) 뒤 다시 냄 |
| B13 | `seal_dc` | `E/sizing/seal.py:32`, 루프 `:44-46`, `dc_seal_report` `:49`, 위반 `:51-57` | 키워드 두 객체 필수, 위반 예외에 `:49` 스냅샷 부착 |
| B14 | 단계 A | `E/pipeline/stage_a.py:83-94`(`StageAResult`), `:199`(서명), `build_s1` `:218`, `build_s1v` `:231`, `coupling_vars` `:150` | `run_stage_a(..., *, output_dir, donors, counters, supplies_v=None, structure_path=None)` -- 만들지 않고 받는다. `StageAResult` 칸 `donors`·`counters`(정지 경로 포함). 보존 `:200` 재확인 (a), `:201` |
| B15 | 단계 B | `E/pipeline/stage_b.py:134`(서명 불변), `:152`·`:158`·`:167`·`:168` | `stage_a`의 두 칸으로 |
| B16 | S1·S1v | `E/graph/s1_build.py:57`·블록 `:75-87`(13), `E/graph/s1v_build.py:34`·`:42` | 키워드 두 객체 필수 |
| B17 | ss 단계 | `E/metrics/ss_evaluate.py:78`(서명 불변), 블록 `:94·95·98·103·106` | `ctx`에서 꺼냄, ss 실패 부분 스냅샷 부착 |
| B18 | 레이아웃 | `E/layout/run.py:93`(`run_layout`), 루프 `:101-105`, `E/convergence/place_layout.py:32·39·52`, `E/convergence/converge_point.py:99`, `E/layout/contract_output.py:369`(docstring) | `run_layout`·`place_layout` 키워드 두 객체 필수, `converge_point`는 `sctx.dc`에서. `computed_blocks` 판정 코드 무변경, docstring '다시 계산한 writer' → '값을 쓴 writer(계산 또는 이식)' + `layout/CONTRACT.md` 같은 칸 |
| B19 | 탐색 S0 블록 | `E/search/search_context.py:161-186`(블록 9), `:189-207` | `dc_ctx`에서. 서명 불변. 보존 `:194`, `_wire_sweep_memo` `:132-143` |
| B20 | `evaluate` | `E/search/kernel.py:121-125`·`:132-138`(실패 경로), `:141-142`(블록), `:162`(`EvalResult`), `_record` `:68-88`(`snapshot_fp` `:83-84`) | `EvalResult.partial`, 블록 호출에 두 객체, 실패 줄 `snapshot_fp` = `partial.fp`. 보존 `:116-118`·`:164-165`(card A 창) |
| B21 | `EvalResult` | `E/search/search_values.py:157-174` | 칸 `partial`(끝, 기본 None) |
| B22 | `find_front` perf | `E/search/find_front.py:46-47`(`_BLOCKS`), `:55-61`(`_block_totals`), `:80`·`:85`, `:136-138` | 삭제 후 `perf.blocks`·`block_totals`(= `sctx.dc.counters.snapshot()`), `block_index_entries`(= `entry_count()`), `block_index_bound`(= `len(blocks) × (E_total + 1)`, E_total: `eval_budget_source == "declared"`면 `eval_budget` + 2 × `len(sctx.domain.variables)`(as-built N_T = 0), 유도면 `eval_budget`, None이면 null). 보존 `:78`·`:82`·`:84`·`:117`·`:134`·`:154` |
| B23 | 재수출 | `E/core/__init__.py:6`·`:37`·`:41`·`:75`, `E/search/__init__.py` | `BlockStats` 삭제, core에 `RunCounters`·`PerfCounters`·`graft`·`Donors`·`attach_partial`, search에 `S3Index`·`open_run` |
| B24 | 모듈 지도 | `E/_module_map.py:44-51`, `:225`, `:228`, search 층 `:136-155` | 새 파일 다섯(`run_counters.py`·`donors.py`·`graft.py`·`failure_partial.py`(core), `s3_index.py`·`open_run.py`(search)) 항목·층, `compute_block.py` 책임 문장에서 계수 삭제 (기계 검사 없음 -- 리뷰) |
| B25 | 함수 레지스트리 | `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` §2(31~64행, 끝 `:64` `ThetaCoords`), §16(717~722행) | code 주체 같은 변경: §2 끝에 '실행 수명 블록 결과 색인' = `S3Index`, '실행 하나의 색인·계수 생성' = `open_run`, '블록 결과 이식' = `graft`, '실행 계수' = `RunCounters`, '후보 실패의 부분 스냅샷' = `attach_partial`, '계산 블록 입력 버전' = `ComputeBlock.input_version`(사본 `seal_versions` 삭제) |
| B26 | 구조 규칙 M | `E/tests/structure/structure_checks.py`(새 `check_m`, 규칙 K `check_k` `:1180` 선례), `README.md` 규칙 표, `fixtures/rule_m/{bad,good}/gmid_engine/`, `test_structure_rules.py`·`test_structure_rules_reject_fixtures.py` | design §2.4.5 '수명' (2) 그대로(아래 1.4.5). **test 쪽 파일이지만 design (3) 표가 card B 재작성 범위에 넣었다 -- test 주체 몫**(규칙 K 선례와 같음) |

#### 1.3.2 CONTRACT (실측 위치)

| 위치 | 처리 |
|---|---|
| `E/core/CONTRACT.md:59`(`BlockStats` 비진입 공개 이름), `:249-266`(§6.2 호출), `:267-272`(§6.3 계수 `stats`·`reset_stats`), `:125-140`(§4.2 예외) | 새 파일 넷 행, `block(snapshot, *extras, donors, counters)`·판정 순서·fail-closed·`input_version`, §6.3을 `RunCounters` 절로, `partial`·`from_record`(두 기반), `attach_partial`·`graft`·`Donors` 절 |
| `E/graph/CONTRACT.md:447` | 계수 문구 삭제, `build_s1`·`build_s1v` 두 객체 |
| `E/sizing/CONTRACT.md:3-8`·`:113`·`:150-160` | `KernelContext` 칸 둘, `build_kernel_context`·`seal_dc` 두 객체, 부분 스냅샷 부착, `seal_versions`의 정본 사용 |
| `E/metrics/CONTRACT.md`(`ss_evaluate`) | ss 부분 스냅샷 |
| `E/layout/CONTRACT.md`(`run_layout`·`LayoutResult`) | 두 객체, `computed_blocks` 뜻 |
| `E/pipeline/CONTRACT.md` | `run_stage_a` 필수 키워드 둘, `StageAResult` 칸 둘 |
| `E/search/CONTRACT.md:531-532`(§3.16 perf 'block_*'), `:448-466`(§3.10), `:673`(evals 줄 `snapshot_fp?`), `:1001`(§10.1 r1 실측 기록 안 `block_recomputes_same_input` -- 이름 없이 고침, card A 선례) | 새 perf 칸 넷, 부분 스냅샷, 실패 줄 `snapshot_fp`, `S3Index`·`open_run` 새 절 |

#### 1.3.3 test (test 주체 몫 -- 083b103 실측)

| 대상 | 처리 | 실측 |
|---|---|---|
| 옛 계수 API: `reset_stats`·`BlockStats` 32파일 + 블록 `.stats()`만 7파일 = **39파일** | `RunCounters`·`perf.blocks`로 다시 씀 | 목록: `tests/core/test_compute_block.py`, `graph/test_s1_symmetry.py`·`test_s1v_build.py`·`test_s1v_fields.py`, `integration/test_rerun_s3_independence.py`·`test_s0_layer_9circuits.py`, `layout/test_finger_candidates.py`·`test_pattern_select.py`·`test_rows.py`·`test_run.py`, `metrics/test_dc_metrics.py`·`test_junction_field.py`·`test_mismatch_field.py`·`test_model_error_field.py`·`test_passive_values.py`·`test_ss_evaluate.py`·`test_ss_linearize.py`·`test_ss_metrics.py`, `pipeline/test_stage_a.py`, `search/test_constraint_classes.py`·`test_kernel.py`, `sizing/test_block_currents.py`·`test_block_widths.py`·`test_kernel_fields.py`·`test_kernel_run.py`·`test_s2_lift.py`·`test_seal_conduction.py`·`test_seal_report.py`·`test_size_and_seal.py`·`test_theta_schema.py`·`test_w0_rails.py`·`test_writer_plan.py` + `graph/test_bulk_default.py`·`test_columns.py`·`test_dc_conduction.py`·`test_s1_build.py`·`test_s1_structure.py`, `search/test_fd_jacobian.py`·`test_search_domain.py` |
| `run_stage_a` 호출(규칙 M (M-c) 1:1 동반) **16파일 46곳** | 호출마다 같은 함수 안 `donors, counters = open_run()`을 두고 그 이름을 그 호출 하나에만 넘긴다. helper는 쌍을 매개변수로 받지 않고 스스로 `open_run` | `tests/integration/nfr4_run_dump.py`, `test_j_rules_library.py`, `test_layer0_boundary_rows.py`, `test_rerun_s3_independence.py`, `test_s0_layer_9circuits.py`, `test_stage_a_library.py`, `test_stage_b_library.py`, `tests/metrics/gb4_hand.py`, `tests/pipeline/test_stage_a.py`, `test_stage_a_loop_cut.py`, `test_stage_a_report.py`, `test_stage_b.py`, `tests/search/test_cell_floor.py`, `u13_hand.py`, `u13_real.py`, `tests/sizing/test_current_basis.py`. 한 함수 안 `run_stage_a` 2회 이상 8함수(`test_stage_a_library.py` `test_stage_a_library_circuit`(2)·`test_structure_json_declared_comparison`(3), `test_j_rules_library.py` `test_pilot_stage_a_with_spec_has_no_unmatched_cut`(2), `pipeline/test_stage_a.py` 다섯 함수(각 2)) -- 호출마다 자기 `open_run()`이면 유지 |
| 그 밖 두 객체를 받게 되는 진입을 부르는 test | 두 객체를 넘긴다(단위 test = 실행 하나, 한 test 함수 안 `open_run()` 한 번을 여러 호출에 써도 됨 -- design M-c 범위 한정) | 블록 직접 호출 189곳(블록 53개), `build_s1` 177곳·51파일, `build_kernel_context` 48·23, `build_search_context` 30·15(서명 불변 -- `dc_ctx`가 두 객체를 가져야 함), `build_s1v` 22·10, `run_layout` 19·2, `run_stage_b` 12·9(서명 불변), `seal_dc` 6·3, `place_layout` 6·2. 이 함수·블록 이름을 부르는 test 파일 합집합 98 |
| `tests/search/test_find_front.py:19-21`(`PERF_KEYS` 18), `:28`(`PERF_KEYS_C7`) | 22개로(옛 네 칸 → `blocks`·`block_totals`·`block_index_entries`·`block_index_bound`) | NFR-4 `test_lb_stop_notes_line_exactly_once`가 따라옴 |
| `tests/integration/nfr4_run_dump.py:41`(`K_NAMES` 옛 네 칸), 사슬 `:376-401` | 네 이름 삭제, 회로 실행 함수 안에서 `open_run` | 하네스 = test 도구 |
| `tests/search/test_search_values.py`(`EvalResult` 직접 생성 2곳) | 새 칸이 끝·기본 None이라 깨지지 않으면 그대로 | |
| 새 test 파일 | `tests/core/test_run_counters.py`, `test_donors.py`, `test_graft.py`, `test_failure_partial.py`, `tests/search/test_s3_index.py`, `test_open_run.py`(규칙 H 1:1), `tests/integration/test_run_isolation.py`, `test_g10_no_recompute_9circuits.py`(integration -- 규칙 H 밖), 구조 규칙 M test·픽스처(B26) | 이름 충돌 0(1.7.2) |

#### 1.3.4 문서

| 위치 | 처리 |
|---|---|
| 함수 레지스트리(B25) | code 주체, 같은 변경 |
| 42 D-XR3·D-XR4·D-XR5, D-GR4·12·15 | 판정 뒤 OK(오케스트레이터) |
| history·design의 옛 문장 | 바꾸지 않는다 |

#### 1.3.5 삭제 이름 grep 0 (design §2.4.14 (4) B 행)

| 이름 | grep 범위 | 범위 밖 남는 쓰임 | 실측 hit(엔진 `.py` / CONTRACT `.md` / `tests/`) |
|---|---|---|---|
| `BlockStats` | 엔진 전체 | 없음 | 5 / 2 / 3(2파일) |
| `reset_stats` | 엔진 전체 | 없음 | 1 / 3 / 58(32파일) |
| `_seen_inputs` | 엔진 전체 | 없음 | 4 / 0 / 0 |
| `_block_totals` | `E/search/find_front.py` | 없음 | 3 |
| `_BLOCKS` | `E/search/find_front.py` | `E/layout/run.py:42·101` | 2 |
| `block_calls`·`block_reuses`·`block_computes`·`block_recomputes_same_input` | 엔진 전체 | 없음 | 각 1 / `block_recomputes_same_input`만 1(`search/CONTRACT.md:1001`) / 각 2(`tests/search/test_find_front.py:28`, `tests/integration/nfr4_run_dump.py:41`) |
| `retain`·`release`·`regenerated_after_release` | 엔진 전체 | design·계획만 | 0 / 0 / 0 |
| 메서드 `ComputeBlock.stats`·`reset_stats` | `E/core/compute_block.py` | `LutMemo.stats`·`BoundedLRU.stats` | AST로 `ComputeBlock` 본문 정의 0 |
| `seal_versions.py`의 입력 버전 식 사본 | `E/sizing/seal_versions.py` | -- | `fp_of((block.name, block.code_hash` 꼴 0(정본 `input_version` 호출) |

#### 1.3.6 보존 계약 (card A·NFR-4)

| 파일:줄 | 내용 |
|---|---|
| `E/search/kernel.py:116-118`·`:164-165` | card A 첫 커널 평가 창 |
| `E/search/search_context.py:132-143` | card A `_wire_sweep_memo` |
| `E/search/theta_coords.py` 및 세 사용처, `E/core/bounded_lru.py`, `E/lut/lut_memo.py` | card A 결과 무변경 |
| `E/pipeline/stage_a.py:200`, `E/search/search_context.py:194`, `E/search/find_front.py:78`, `E/search/layer0_center.py:651`, `E/search/slsqp_outer.py:95` | NFR-4 재확인 (a)~(e) |
| `E/search/find_front.py:82`·`:84`, `layer0_center.scipy_minimize`, `find_front.py:117`·`:154` | NFR-4 관찰 지점·notes `l_search`·`env_fp` |
| `_budget_stop` 3곳 | card C |
| `E/core/compute_block.py:32-89` | 코드 해시 |
| `E/core/graph_snapshot.py:149-151`·`:153` | `block_version`·`write` 서명(분할은 U17 ②) |
| `E/tests/integration/fixtures/u17_1b_s0_baseline.json` | S0 지문 그대로 |

### 1.4 배선 (design 확정값)

#### 1.4.1 블록 호출 판정(분할 `*`)

```text
block(snapshot, *extras, donors=D, counters=C):
  두 키워드 없음 / D 가 Donors 하위 아님                      -> TypeError (fail-closed 1)
  projection, iv = 비공개 helper(snapshot, extras)            # 한 번. 공개 block.input_version() 은 같은 helper
  1 snapshot.block_version(name) == iv  -> C.record(name, "*", "reuse", iv); return snapshot
  2 donor = D.find(name, "*", iv)       -> C.record(.., "graft", iv); return graft(snapshot, block, "*", donor, iv)   # 버전 불일치 ValueError 는 graft
  R rec = D.find_failure(name, "*", iv) -> C.record(.., "replay", iv); raise FAILURE_CLASSES[rec.failure_class].exc.from_record(rec)
  3 C.record(.., "compute", iv); rows = fn(projection)
      (InfeasibleSizingError | SchemaRejectedError) -> D.register_failure(.., iv, e.record); C.result(.., iv, ok=False); raise
      그 밖 예외 -> 등록·알림 없이 raise
      out = snapshot.write(name, iv, rows); D.register(.., iv, out); C.result(.., iv, ok=True); return out
```

#### 1.4.2 두 객체가 흐르는 길

| 단계 | 받는 곳 |
|---|---|
| 생성 | `open_run()`(card B: 하네스·test가 `run_stage_a` 호출마다 1:1, OS-2 뒤 세션 열기) |
| 단계 A | `run_stage_a(..., donors, counters)` → `build_s1`(13)·`build_s1v`(1)·`coupling_vars`(1), `StageAResult` 칸 |
| 단계 B | `run_stage_b` → `stage_a`의 칸 → `build_kernel_context`(7)·`search_domain`·`passive_area_decl`·`achievability` |
| 커널 컨텍스트 | `KernelContext.donors`·`.counters` |
| 탐색 | `build_search_context`(`dc_ctx`) → `_s0_blocks`(9) |
| 평가 | `evaluate` → `size_and_seal` → `run_kernel`(4) → `seal_dc`(9), `ss_evaluate`(5), `passive_values`·`metrics_dc` |
| MOD8 | `converge_point`(`sctx.dc`) → `place_layout` → `run_layout`(4) |

#### 1.4.3 부분 스냅샷

`run_kernel`(그 블록에 들어간 스냅샷) → `seal_dc`(`dc_seal_report`까지) → `ss_evaluate`(ss 실패 직전) → `evaluate`가 잡은 예외의 `partial`을 `EvalResult.partial`로 → `_record` 실패 줄 `snapshot_fp`. 모두 `core.attach_partial`(가장 안쪽이 이긴다). 재연 예외는 `partial` None으로 시작하고 바깥 `run_kernel`이 붙인다.

#### 1.4.4 배선 확인(만들면 반드시 배선)

`open_run`은 하네스·test의 `run_stage_a` 호출부가, `RunCounters`·`S3Index`·`graft`는 모든 블록 호출(소스 이름 호출 42곳 + 루프 간접 4곳: `kernel_run.py:72-73`·`:84-85`, `seal.py:44-45`, `layout/run.py:101-103`)이, `input_version`은 `__call__`(helper 경유)·`seal_versions`가, `PerfCounters`·`entry_count`는 `find_front`가, `find_failure`·`register_failure`·`from_record`는 블록 호출이, `attach_partial`·`partial`은 `run_kernel`·`seal_dc`·`ss_evaluate`·`evaluate`·`_record`가 쓴다.

#### 1.4.5 구조 규칙 M (design §2.4.5 '수명' (2) 그대로)

- **M-a**: 엔진 소스(`tests/` 제외)에서 `open_run` 참조는 `search/open_run.py`·`search/__init__.py`뿐(card B 허용 목록 비어 있음, OS-2가 세션 열기 파일 하나를 design 변경으로 더함).
- **M-b**: `S3Index(`·`RunCounters(` 생성 호출은 정의 모듈과 `open_run.py`에만(엔진·test 모두).
- **M-c**: `run_stage_a`의 `donors`·`counters` 인자 = 같은 함수 본문의 `donors, counters = open_run()` 튜플 풀기로 대입된 두 이름이고, 그 이름은 그 함수 안 `run_stage_a` 호출 하나에만 쓰인다. 반복문 안 호출이면 `open_run`도 같은 반복문 본문. fail-closed 판정: 매개변수·속성·결과 칸(`StageAResult`·`KernelContext`·`sctx.dc`)·다른 호출 반환에서 온 쌍 위반, 바깥 함수의 쌍을 안쪽 `def`·`lambda`에서 씀(자유 변수) 위반, 내포식·generator 식 = 반복문 본문, `**kw`·`*args` 묶음 인자 위반. 예외 = OS-2 세션 열기 파일(OS-2 design). 범위는 `run_stage_a` 인자뿐 -- 감쌈 함수·블록을 직접 부르는 단위 test는 '실행 = test 함수 하나'.
- **M-d**: `open_run` 결과 보관 금지 -- 모듈 수준 이름, 클래스 속성, session·module·package 범위 fixture, 함수 기본 인자값, `functools.lru_cache`·`cache`(데코레이터·호출형) 함수의 반환, 모듈 수준 컨테이너 변경(`append`·`extend`·`add`·`update`·`setdefault`·항목 대입), conftest `pytest_configure`·`request.config`·`config.cache`·`config.stash`, 수명이 test 하나보다 긴 객체의 인스턴스 속성.
- **M-f**: `S3Index`·`RunCounters` 객체·내부 칸(`_` 속성 포함)이 `pickle`·`json`·`shelve`·`marshal` 쓰기 함수 인자면 위반.
- (M-e 없음 -- M-c에 흡수.) 색인 키 = (블록, 분할, 입력 판)만 -- `code_fp`·`env_fp`·spec 지문·`context_fp`·`run_id`를 키에 넣지 않는다(코드 리뷰·감사 항목).

### 1.5 결과 JSON·공개 API 형식 변경

| 출력 | 바뀌는 것 |
|---|---|
| `SearchFront.perf`, runs 줄 `perf` | 삭제 옛 네 칸, 추가 `blocks`·`block_totals`·`block_index_entries`·`block_index_bound` -- 22 → 22 |
| S3 evals 실패 줄 | `snapshot_fp`(= 부분 스냅샷 `fp`) |
| `perf.blocks` 범위 | `find_front` 구간 sizing 12블록 → 실행 전체 모든 블록 |
| 공개 API | 추가: core `RunCounters`·`PerfCounters`·`graft`·`Donors`·`attach_partial`, `ComputeBlock.input_version`, 예외 `partial`·`from_record`(두 기반), search `S3Index`(`entry_count`)·`open_run`, `KernelContext`·`StageAResult`의 `donors`·`counters`, `EvalResult.partial`. 삭제: `core.BlockStats`, `ComputeBlock.stats`·`reset_stats`. 서명: `ComputeBlock.__call__`, `run_stage_a`·`build_s1`·`build_s1v`·`build_kernel_context`·`seal_dc`·`run_layout`·`place_layout`에 필수 키워드 둘 |
| `LayoutResult.computed_blocks` | 값 규칙 불변, 뜻 문구만(계산 또는 이식으로 값을 쓴 writer) |

### 1.6 완료 조건

1. (i) 1.3.5 이름별 범위 grep 0, `ComputeBlock` 본문 `stats`·`reset_stats` 정의 0, `seal_versions.py` 식 사본 0.
2. (ii) 9회로 각 한 실행에서 `perf.blocks` 모든 행 **같은 입력 재계산(`recomputes_same_input`) = 0**, `perf.recompute_same_key` = 0(판정 1·5). `ngcc_3stage_ff`는 단계 A·B까지의 `RunCounters.snapshot()`. 처음 계산(`computes`)은 0이 아니어도 된다.
3. (iii) card A 병합 엔진(083b103과 엔진 동일한 base) 대비 같은 환경 비트 동일 집합이 제외 칸(`perf` 블록 계수·색인 칸, 지운 네 칸, T 부류, evals 실패 줄 `snapshot_fp`, 하네스가 덤프한 `partial` 경로, `run_id`·`code_fp` -- 목록은 감사 소유) 말고 비트 동일.
4. (iv) `perf.block_index_entries`·`block_index_bound` 9회로 보고(card C 전 보고만).
5. 독립 계수 대조: `ComputeBlock.__call__` 클래스 수준 감쌈과 `perf.blocks` 합이 같고, card A A-6 head 47건 → 0.
6. 부분 스냅샷 세 경우(DC 블록·봉인 위반·ss)의 `partial.block_versions`가 design 정의와 같고 실패 줄 `snapshot_fp` = `partial.fp`.
7. 구조 규칙 M: 엔진 소스·`tests/` 위반 0, 위반 픽스처(M-a·M-b·M-c 꼴마다·M-d 경로마다·M-f)가 각각 거부된다(**'통과'가 아니라 '실제로 거부'를 먼저 확인**).
8. 전체 suite 한 번(`--run-slow`) 통과, `tests/structure` 위반 0(규칙 A -- `failure_errors.py` 데이터 모듈 유지·새 파일 여섯 진입점 하나, H는 base 비교). 1.3.6 보존 계약 유지.
9. 공통 완료 조건(§10.4): graph 단일 정본 확인 (a)~(d)(`S3Index` = (b), `RunCounters` = (c), 값 사본 없음)·계산값 재사용 확인 (a)~(d) 숫자와 함께. gap-detector ≥ 90 %, 42 D-XR3·D-XR4·D-XR5 OK.
10. 함수 레지스트리 B25가 같은 변경에 있다.

### 1.7 위험

#### 1.7.1 동작·기준 자료

- card A A-6(프로세스 전체 블록 계수, 보고만) head 같은 입력 재계산 47: cga `dc_lengths` 9, crto `dc_currents` 6·`dc_lengths` 12, folded `dc_seal_report` 3, nmcnr `dc_lengths` 6, sfpp `dc_lengths` 6, tso `dc_seal_report` 3, tsosf `dc_seal_report` 2, pp 0. head (calls, reuses, computes): cga (785, 77, 708), crto (161, 10, 151), folded (1167, 127, 1040), nmcnr (819, 111, 708), pp (689, 70, 619), sfpp (161, 10, 151), tso (925, 134, 791), tsosf (783, 110, 673). 입력과 무관한 예외 재호출이 섞여 있으면 0이 되지 않는다(그때는 결함 보고).
- card A `perf.block_*`(sizing 12블록·`find_front` 구간)와 card B `perf.blocks`(실행 전체)는 직접 비교하지 않는다.
- 메모리: 색인이 실행 수명 동안 결과 스냅샷 참조를 쥔다 -- 감사가 회로별 최대 RSS 보고(판정 아님).
- 성공·실패 섞임(이식 비트 동일 전제 위반)이 나오면 `ValueError`로 멈춘다 -- 결함 보고.
- 규칙 M M-c는 정적 검사라 동적 우회(예 `getattr`로 `run_stage_a` 호출)를 보지 못한다 -- fail-closed 판정(묶음 인자 위반)으로 줄이고 리뷰 항목으로 둔다.

#### 1.7.2 이름 충돌 (083b103, docs·`.md`·`.ai`·`.bkit` 제외)

- 0건: `RunCounters`, `run_counters`, `graft`, `grafts`, `Donors`, `S3Index`, `s3_index`, `open_run`, `attach_partial`, `failure_partial`, `from_record`, `find_failure`, `register_failure`, `replays`, `entry_count`, `block_totals`, `block_index_entries`, `block_index_bound`, `PerfCounters`, `rule_m`, `check_m`, `test_run_counters`, `test_graft`, `test_donors`, `test_s3_index`, `test_open_run`, `test_failure_partial`, `test_run_isolation`, `test_g10_no_recompute_9circuits`, `test_index_single_source`, `test_graft_equals_compute`.
- `donors`: `graph/drive_kind.py:164-171` 지역 변수(무관). `input_version`: 이미 `FieldValue.input_version` 칸·인자 이름으로 널리 쓰인다 -- 새 것은 `ComputeBlock` 메서드라 기능 충돌 없음(`.input_version(` 호출 꼴은 0건). `partial`: test 지역 이름·`test_compute_block.py:862` parametrize id -- 새 test 이름은 `test_partial_snapshot_…`.
- `-k g10`: `test_g10_no_recompute_9circuits`는 design §10.4 integration 식에 걸리도록 정한 이름. base에서도 `Vg10` 든 id가 걸릴 수 있다 -- 감사가 base·head 수집 수를 함께 보고.
- 그 밖 `-k` 식은 card A와 같다(`test_ic`·`rule_g`·`rule_k_`·`ic1`·`ic2`·`ic9` 금지). 규칙 M test 이름은 `rule_m_…`(`-k rule_k_`와 겹치지 않음).

#### 1.7.3 순서·충돌

- card C가 `S3Index` 생성자에 상한 인자를 더할 때 `open_run` 서명과 그 호출부 전부, `find_front`의 card B E_total 식을 같은 변경에서 고친다(design C 행). OS-5 B_S0도 같은 길.
- OS-2는 세션 열기 파일 하나를 M-a 허용·M-c 예외로 더한다(OS-2 design).
- test 영향이 넓다(옛 계수 39파일 + `run_stage_a` 16파일 + 서명 변경 98파일 합집합). 같은 interface card 한 판으로 쓴다.

#### 1.7.4 구조 규칙

- 규칙 A: `core/failure_errors.py`는 데이터 선언 모듈로 남는다(`partial`은 `__init__` 칸, `from_record`는 `from_` classmethod -- `structure_checks.py:241-249`). 새 파일 여섯은 진입점 하나씩(`RunCounters`(+`PerfCounters`), `Donors`, `graft`, `attach_partial`, `S3Index`, `open_run`).
- 규칙 C: `open_run`은 search(`S3Index`가 search) -- core는 search를 import하지 않는다.

### 1.8 판단 기록 (모두 확정 -- design 083b103, 사용자 승인 X-21)

| id | 확정 | design 자리 |
|---|---|---|
| PD-8 | `run_stage_a`는 두 객체를 필수 키워드로 받고 만들지 않는다. 실행 경계 = 두 객체를 만드는 호출자 | §2.4.5 '수명'·'전달', §2.4.9 `RunCounters` 문단 |
| X-20 | 실행 비공유는 구조로: `open_run` 단일 생성, 규칙 M, 키에 실행 바깥 지문 금지, 디스크 저장 금지 | §2.4.5 '수명' (1)~(4) |
| card B J-2 | `graft(target, block, part, donor, input_version)`, part `"*"`만, fail-closed (2) 검사 주체 = graft | §2.4.4 API |
| card B J-3 | `attach_partial`은 `core/failure_partial.py` 함수, `from_record` 두 기반 | §2.4.4 실패 재연, §2.4.7 '전달' |
| card B J-4 | 감쌈 함수 필수 키워드(기본값 없음) | §2.4.5 '전달' |
| card B J-5 | `Donors` 네 추상 메서드, `S3Index()` 인자 없음·비공개, `entry_count()` | §2.4.4, §2.4.5 생성자 문단 |
| card B J-6 | card B E_total 식은 `find_front`, card C가 자리 하나로 정하며 지움 | §2.4.5 '상한', (3)·(4) C 행 |
| card B J-8 | `PerfCounters(blocks, block_totals)` | §2.4.9 |
| card B J-9 | `computed_blocks` 뜻 정정(코드 무변경, docstring·CONTRACT 문구는 card B) | §2.4.7 `LayoutResult` 행 |
| card B J-10 | `search/CONTRACT.md:1001`은 이름 없이 고친다(card A 선례, 오케스트레이터 기본안 -- design (4) 범위 '엔진 전체' 그대로) | -- |
| card B J-11 | 입력 버전 정본 `ComputeBlock.input_version`, `seal_versions` 사본 삭제 | §2.4.4 |
| card B J-13 | (iii) 비교 제외 칸 목록은 감사 소유(작성자≠검증자) | -- |
| card B J-14 | 42 D-XR3 fail-closed 다섯 | 42 |

### 1.9 원래 취지와 다른 판단

| # | 내용 | 상태 |
|---|---|---|
| D-1 | 이 card는 취지 쪽으로 움직인다(계보 무관 같은 입력 재사용, 실패 결과 재사용) | -- |
| D-2 | (기존, 범위 밖) `sctx.cache`·`computed_keys` dict 그대로(U17 ②) | 재사용은 이미 함 |
| D-3 | (기존, 범위 밖) LUT memo 두 인스턴스 | U17 ③ |
| D-4 | 입력과 무관한 예외로 끝난 계산의 재호출은 판정 1 FAIL로 센다 | design 결정(X-9) |
| D-5 | PD-8로 생성 자리가 엔진 밖으로 옮겨 생긴 '실행 사이 넘김' 빈틈 | **구조 규칙으로 막음(X-20)** -- 옛 '원래 취지와 다름(보고)'에서 바뀜 |
| D-6 | card B 시점 제품 진입이 없어(엔진 소스 `run_stage_a` 호출 0) 두 객체를 만드는 쪽은 test·하네스뿐 | OS-2·U16 몫 |

---

## 2. 공통 브리핑 (이 card의 code·test·audit agent 필독, 1쪽)

base = `083b103`(design 40 card B 개정 병합 master). design: `docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md` §2.4.4·§2.4.5(특히 '수명' 376행의 규칙 M)·§2.4.7·§2.4.9·§2.4.14 (3)(4)(5) B 행·§10.4, `…42-gap-checklist.design.md` D-XR3~D-XR5. 계획: gain-budget NFR-2·U-96·U-97, offset-strategy PD-7·PD-8·XS-7. 엔진: `skills/analog-gmid-design/gmid_engine/`. 사용자 결정 기록: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/user_decisions.md`(읽기만, X-1~X-21). card: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/engine/XRUNF1B_SPEC_CARD.md`(code·audit), `XRUNF1B_INTERFACE_CARD.md`(test는 이것만 -- 소스 열람 금지). 기준 자료: `.ai/verification/xrunf1a/a2_a4_a6_a10.json`(A-6).

### 절대 규칙
1. **design 그대로 구현한다. as-built 결정 금지.** design에 없는 것을 정해야 하거나 모순이면 멈추고 보고(무엇이, 어느 절이, 선택지).
2. **graph 단일 정본(DEC-83)**: graph 밖 허용 저장소는 셋뿐 -- (a) LUT memo, (b) S3 기록·S3 메모리 색인(`S3Index`: 스냅샷 참조와 `FailureRecord`만), (c) 실행 계수(`RunCounters`). 새 캐시·사본·디스크 캐시 금지.
3. **계산값 재사용 = 실행 안에서, 계보 무관**: 판정 = 같은 입력 재계산 0. 색인·계수는 실행 하나에만 산다 -- 두 객체는 `open_run()`으로만 만들고(`run_stage_a` 호출마다 1:1), 보관·디스크 저장·실행 바깥 지문 키 금지(규칙 M). 벗어나는 판단은 멈추고 '원래 취지와 다름'으로 보고.
4. **틀린 구조는 전체 재작성**(`ComputeBlock.__call__`·계수 상태는 단위 재작성), 옛 코드·CONTRACT 문장은 같은 변경에서 삭제, 만든 것은 반드시 배선(1.4.4).
5. **건드리지 않는 것**: card C·U17 ②·③·OS-2·OS-5 범위, 블록 코드 해시, `GraphSnapshot` 서명, card A 결과, NFR-4 병합분, `_budget_stop` 3곳.
6. **상수 발명 금지**, **회로 이름·소자 이름 코드 금지**.
7. **파일 분할 규칙**: (A) 진입점 하나(`failure_errors.py` 데이터 모듈 유지), (C) 층 순서(`open_run`·`S3Index`는 search), (H) test 1:1 -- `core/run_counters.py`·`donors.py`·`graft.py`·`failure_partial.py` ↔ `tests/core/test_run_counters.py`·`test_donors.py`·`test_graft.py`·`test_failure_partial.py`, `search/s3_index.py`·`open_run.py` ↔ `tests/search/test_s3_index.py`·`test_open_run.py`. `_module_map.py` 갱신. `tests/structure` 위반 0(규칙 M 포함).
8. **작성자 ≠ 검증자**: code agent는 test·기대값을 쓰지 않는다(구조 규칙 M 검사기·픽스처도 test 주체 몫). test agent는 피검 코드를 불러 기대값을 만들지 않는다. 같은 커밋에서 코드와 기준을 함께 바꾸지 않는다. 기준 약화는 사용자 승인 사항.

### 실행 환경·git 가드
- python: `/c/Python314/python.exe`(bash `timeout` 래퍼 금지). 실행 위치 `<worktree>/skills/analog-gmid-design`, `python -m pytest -q gmid_engine/tests/<경로> -p no:cacheprovider`. 기본 실행은 slow를 빼고, 포함은 `--run-slow`.
- **무거운 실행은 한 번에 하나**(9회로·전체 suite 순차). 긴 실행은 결과를 파일에(`C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_xrunf1b_<role>/run.txt`, 케이스마다 append). 백그라운드 실행이 끝날 때까지 턴을 끝내지 않는다.
- git: 항상 `git -C <자기 worktree>`, 스크립트 `set -e`. 다른 worktree·master 금지, reset --hard·다른 브랜치 checkout·push·merge 금지, 커밋은 자기 브랜치에만.
- 커밋 메시지 끝(`--trailer`): `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`, `Claude-Session: https://claude.ai/code/session_012FxFP7YSWEBBCB9rmBQjLL`.
- 임시 파일: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_xrunf1b_<role>/`(자기 것만).

### 최종 보고(한국어) 필수 항목
1. 구현·작성한 design 절과 상태. 2. 멈춤·보고 항목. 3. 지운 옛 코드(파일:줄), 바뀐 배선(호출부 파일:줄), 1.3.5 이름별 grep. 4. graph 단일 정본 자기 점검. 5. 계산값 재사용 자기 점검(모든 블록 호출이 색인 경유·같은 입력 재계산 0·규칙 M 위반 0). 6. `tests/structure` 결과(규칙별, H는 base 비교)·관련 test·깨진 옛 test 목록. 7. 커밋 해시.


## 오케스트레이터 판단 (상속 -- card A 교훈)
- (card A J-O1) interface card '## 신규 시그니처' 절로 merge_gate가 새 심볼 부재 red를 card 이유로 센다.
- (nfr4c2 J-O2) red 예상 목록에는 엔진 동작을 보는 test만. test 도구(마커 conftest·비교기·하네스) 자체를 시험하는 test는 빼고 감사도 세지 않는다. **규칙 M 검사기 test는 엔진 소스·test 트리의 구조를 보는 검사라 base에서 위반을 내면 red다** -- 단 '위반 픽스처가 거부된다' test(검사기 자체 시험)는 base에서 `check_m` 부재로만 red이고 엔진 동작 red가 아니다(신규 시그니처 표의 부재 red로 센다).
- 재사용 판정 문구는 '같은 입력 재계산 0'.
- (card A J-7) base·head를 같은 하네스·같은 환경으로 감사가 둘 다 잰다.
- (2026-10-16) design 개정은 X-20(구조로 막기)·X-21(승인)로 닫혔다. 이 card 착수 조건은 남지 않았다.
