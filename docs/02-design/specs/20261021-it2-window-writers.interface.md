# interface card: 20261021-it2-window-writers

test 작성 주체는 소스를 보지 않고 이 문서만 쓴다(05-role-separation §11.1, DEC-38 -- 본문 코드 없음). 정본 문장 = design 41 v1.12.3 §4.7(master `468e6e73`) -- 줄 번호 `41:n`. 하위 card 나눔(U-1)이 승인되면 아래 계약 행의 '하위 card' 칸대로 interface card를 넷으로 자른다(내용 불변). `E/` = `skills/analog-gmid-design/gmid_engine/`.

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `gmid_engine.core.graph_snapshot` | `GraphSnapshot.derive_child` | `def derive_child(self, keep_writers) -> GraphSnapshot` |
| `gmid_engine.sizing.seal_versions` | `seal_versions` | `def seal_versions(snapshot, calls, base)` |
| `gmid_engine.sizing.s2_values` | `Window` | `Window(lo, hi, constraints, input_status=None, tol_v=None, status_detail=())` |
| `gmid_engine.sizing.s2_values` | `RefinedWindow` | `RefinedWindow(lo, hi, lo_end, hi_end, tol_v, criterion)`(기본값 없음) |
| `gmid_engine.sizing.s2_values` | `WindowEnd` | `WindowEnd(x, v, reason)` |
| `gmid_engine.sizing.s2_values` | 상수 | `OUTPUT_HIGH_IMPEDANCE == "high_impedance"`, `OUTPUT_KVL_FIXED == "kvl_fixed"`, `CRITERION_TOL_JUDGEMENT == "tol_judgement"`, `CRITERION_DEFINITION == "definition"`, `REASON_WINDOW_END_SOLVE_FAILED == "window_end_solve_failed"`, `REASON_WINDOW_END_K_MAX == "window_end_k_max_exhausted"`, `REASON_WINDOW_END_UNCONFIRMED == "window_end_saturation_unconfirmed"`, `DC_WINDOW_REFINE_WRITER == "dc_window_refine"` |
| `gmid_engine.sizing._helpers_dc_solve` | `Circuit`, `solve`, `FAILURES` | 공개 이름(옛 `block_columns._Circuit`·`_solve`·`_FAILURES`), `Circuit.region_rows(values)` -> 5원소 행 `(a, b, sign, slack, kind)` 목록 또는 None |
| `gmid_engine.sizing.input_window` | `saturation_window` | `def saturation_window(unknown, roots, values, gradient, rows, *, slope=None) -> tuple \| None` -- 반환 `(dlo, dhi, slope)` |
| `gmid_engine.sizing.window_refine` | `refine_input_windows` | 계산 블록(writer `dc_window_refine`), 모듈 수준 이름 `solve`·`k_max`(주입 지점) |
| `gmid_engine.metrics.ss_nodal` | `ss_nodal_system` | 계산 블록(writer `ss_nodal`) |
| `gmid_engine.metrics.icm_config` | `icm_config_window`, `kvl_sensitivity` | 계산 블록(writer `icm_config`), `def kvl_sensitivity(nodal, drive, closure)` |
| `gmid_engine.metrics.icm_window` | `icm_window_metrics` | `def icm_window_metrics(ports, input_dc, config_undefined=()) -> IcmWindow` |
| `gmid_engine.metrics.icm_front` | `icm_front` | 계산 블록(writer `metrics_icm_front`) |
| `gmid_engine.metrics.aux_types` | `IcmPort`, `IcmWindow`, `IcmConfig`, `NodalSystem` | `IcmPort(net, v, lo, hi, tol_v, missing)`; `IcmWindow` 칸 `icmr_v, icm_margin_v, required_input_cm_v, window, v_icm, input_dc, icmr_resolution, margin_resolution, undefined, model_error_ref, sources`; `IcmConfig` 칸 `config, inverting_port, tied_ports, transfer, undefined`; `NodalSystem` 칸 `nodes, fixed, g, factor` |
| `gmid_engine.metrics.ls_swing` | `ls_swing` | `def ls_swing(devices, rails, node_v, outputs, diff_outputs=False) -> SwingIcmr` |
| `gmid_engine.search.front_windows` | `refine_front_windows` | `def refine_front_windows(sctx, result) -> EvalResult` |

서명 불변 진입점(행동 red를 맡는 자리): `dc_writer_plan(snapshot, target_nets, input_dc_declared, order_hints=NO_ORDER_HINTS)`, `dc_columns`, `run_kernel`/`size_and_seal`, `seal_dc`, `ss_evaluate`, `metrics_aux`, `evaluate`, `find_front`.

### 필드(graph) -- writer 하나·소비자

| 필드 | 값 | writer | 하위 card |
|---|---|---|---|
| `node.dc_output_structure` | 출력 포트 넷마다 `"high_impedance"` \| `"kvl_fixed"`(출력 아닌 넷 항목 없음) | `dc_writer_plan` | IT-2b |
| `node.dc_window` | `Window` -- 모든 입력 포트 + W4 뿌리; `input_status` ∈ {None(입력 아닌 W4 뿌리), `"measured"`, `"unsettled"`, `"unmeasured"`(뿌리만), `"op_mismatch"`(`lo`·`hi` None, `status_detail` = `(("devices", 정렬 tuple),)`), `"f_component_undeclared"`(`lo`·`hi` None)} | `dc_columns` | IT-2b |
| `graph.ss_nodal` | `NodalSystem`, `g`·`factor`의 모든 ndarray `flags.writeable is False` | `ss_nodal` | IT-2c |
| `node.dc_window_cfg` | `Window`(입력 포트마다, 모든 측정 구성; 구성 None이면 항목 없음; 자기 측정 실패 = `Window(None, None, 0, input_status="unmeasured")`; 커널 `unsettled` 이어받기(평가점 전체), `f_component_undeclared` 이어받기; definitional 상태가 numeric보다 앞섬) | `icm_config` | IT-2c |
| `graph.icm_config` | `IcmConfig`; `config` ∈ {`"declared_feedback"`, `"follower_beta1"`, `"as_is_single_input"`, None} | `icm_config` | IT-2c |
| `node.dc_window_def_refined` | `RefinedWindow`(`criterion == "tol_judgement"`); 쓰지 않는 포트 = F 성분 미선언·`kvl_fixed` 출력 또는 `as_is_single_input` 평가의 입력 포트 전부·출발 창 없음·출발 창 `unsettled` | `dc_window_refine` | IT-2d |
| `graph.metrics_icm_front` | {METRICS_KEY: `IcmWindow`} -- 출력 전용 | `metrics_icm_front` | IT-2d |
| perf `window_end_solves` | 끝 풀이 수(실행 합) -- 출력 전용 | -- | IT-2d |

창 규칙(41:688-689, :695, :700): 포트 창 = 두 끝 전압 [min, max] ∩ [rail_lo, rail_hi]; 다듬은 창은 어느 끝이라도 결측이면 `lo` = `hi` = None; `WindowEnd`는 x 쪽 끝(`lo_end` = x 아래 끝); 선언 포트 묶음은 같은 x 이동량 Δ로 함께 움직임(묶음 = 선언 포트 − `tied_ports`).

metric 규칙(41:779-786): margin_p = min(V_p − lo_p, hi_p − V_p), `icm_margin_v` = 최솟값(동률 = `ports` 순서 첫); `icmr_v` = min hi − max lo(음수 그대로); `required_input_cm_v` = 미선언이면 (V_p*, lo_p*, hi_p*), 선언이면 None; `margin_resolution` = p* `tol_v`, `icmr_resolution` = 아래 끝 포트 `tol_v` + 위 끝 포트 `tol_v`(None이면 None). 정의 불능: `no_input_port`(definitional), 포트 `missing` code(numeric; `input_window_operating_point_mismatch`·`input_window_f_component_undeclared`는 definitional), detail에 `("port", net)`; 한 metric에 원소 하나(definitional 먼저). 구성 None(M7): `config_undefined` 원소 u마다 quantity ∈ {`icmr_v`, `icm_margin_v`, `required_input_cm_v`}로 `Undefined` -- `metric_value`가 `unrecorded_cause`를 내지 않음. `SwingIcmr` 형식·결과 JSON 키 불변.

정의 불능 code 전체: spec card '정의 불능 code' 절과 같다.

### 단언 금지

`NodalSystem.factor` 내부 배열 값, `input_version` 문자열 값(같음·다름만), 분해능 수치 자체(O-67 (3) -- 정의 함수는 계획 v6.24; '분해능보다 충분히 작은/큰 전달' toy 양 끝만), `transfer` 칸의 resolution 수치, `IcmWindow.model_error_ref`(늘 None만 단언 가능), S3 색인 내부, `RunCounters` 행 타입 이름, 다른 블록 이름 집합의 순서.

## test 목록(위치 제안 -- 규칙 H 1:1, 이름 접두 `test_it2_`)

oracle: (손) toy 손계산, (식) 위 규칙, (비교) 같은 스냅샷으로 부른 `icm_window_metrics`와 블록 출력, (독립) `RunCounters`·perf 증분·`git grep`.

| id | 위치 | 내용(정본) | oracle | base | 하위 card |
|---|---|---|---|---|---|
| T-L11a | `tests/core/test_graph_snapshot.py`·`tests/sizing/test_kernel_run.py` | `derive_child` keep 밖 필드·`block_version` 삭제; parent에 `dc_window_refine` 필드를 실은 픽스처 → child에 없음, base writer 필드 남음, parent 없는 평가가 봉인 4 통과, base writer 버전 다른 parent `ValueError`(41:812 (a)) | (식)+(독립) | red | IT-2a |
| T-L11b | `tests/sizing/test_seal_versions.py`(없으면 seal test 파일) | 봉인 4 위반 픽스처 둘 → `SEAL_FAIL`·`foreign_writers` / `base_call_overlap`(먼저 '실제 거부' 확인) | (식) | red | IT-2a |
| T-L11c | `tests/search/…` | 같은 θ ss 재평가 → ss 블록 outcome `graft`, `computes` 증분 0 | (독립) | red | IT-2a |
| T-OS | `tests/sizing/test_output_structure.py` | OS (a)~(k)(41:727) | (손)+(독립) | red((d)(e)(f)(k) 행동 red, 나머지 부재) | IT-2b |
| T-K1·K2 | `tests/sizing/test_block_columns.py`(또는 `test_dc_columns…` 기존 파일) | 41:799-800 | (손) | red | IT-2b |
| T-Pab-k | 같은 파일 | 감도 음수 포트 커널 창 lo ≤ hi = [min, max], 선언 둘 끝 차 = 선언 차 | (손) | red | IT-2b |
| T-D | `tests/sizing/test__helpers_dc_solve.py` | `triode` 행 영 교차가 창 끝, (S4-나) `kind` ⊆ {`"sat"`, `"triode"`}·공용 전도 함수 호출 0(`git grep`), `op_mismatch` 상태·detail·같은 점 봉인 거부(41:809) | (손)+(독립) | red | IT-2b |
| T-SW | `tests/sizing/test_input_window.py`(고침) | 새 서명: 이동량 창, `roots` 쌍 원소, `slope` 주면 감도 연립 없이 끝만(반환 slope = 받은 값), 5원소 행 | (식)+(손) | red | IT-2b |
| T-L12a-k | 커널 쪽 | `k_max` 소진·tol 미정 → 뿌리 `unsettled`, y 범위 그대로(41:813 (a) 앞부분) | (손) | red | IT-2b |
| T-FD | `tests/search/test_fd_jacobian.py` | 입력 포트 항목이 늘어도 y 스텝 = W4 뿌리 창 폭만 | (식) | green 유지 | IT-2b |
| T-L8 | `tests/metrics/test_icm_config.py` | 41:810 (a)~(e), S-OS1·S-OS2 fail-closed | (손) | red | IT-2c |
| T-L10 | `tests/metrics/test_ss_nodal.py`·`test_icm_config.py` | 41:811 (b)~(g); (f)는 `writeable=False` 뺀 변형에서 FAIL 먼저 | (손)+(독립) | red | IT-2c |
| T-INH | `tests/metrics/test_icm_config.py` | 커널 `unsettled` → 평가점 모든 cfg 항목 `unsettled`, F 성분 미선언 → `f_component_undeclared`, 겹침 시 definitional 우선 | (식) | red | IT-2c |
| T-RES | 같은 파일 | 반전 입력 후보 0·2·분해능 이하 → 세 code, role 이름 맞바꿈 같은 `inverting_port`(분해능 수치 단언 금지) | (손) | red | IT-2c |
| T-K3 | `tests/search/test_front_windows.py` | 41:801 (a)~(d) | (독립) | red | IT-2d |
| T-R1·R2 | `tests/sizing/test_window_refine.py` | 41:802-803(주입 지점 `gmid_engine.sizing.window_refine.solve`·`.k_max`만) | (손)+(식) | red(ImportError) | IT-2d |
| T-Pcde | 같은 파일 | 41:808 (c)(d)(e) | (손)+(독립) | red | IT-2d |
| T-M1·W1 | `tests/metrics/test_icm_front.py`·`tests/search/test_front_windows.py` | 41:804-805 | (비교)+(손) | red | IT-2d |
| T-IW | `tests/metrics/test_icm_window.py` | 순수 함수 규칙·예시 리터럴(0.28 / 0.83 / (0.90, 0.33, 1.18))·정의 불능 우선순위·M7 quantity | (식) | red(ImportError) | IT-2d |
| T-LS | `ls_swing` test | 새 서명, 입력 칸 기본값, 입력 포트 없는 회로 `swing_out_v` 값 있음·입력 두 metric만 `no_input_port` | (식) | red | IT-2d |
| T-L12 | 41:813 (a) front 쪽·(b)·(c)·(d) | 미수렴 점 다듬지 않음·front 제외·원인 `input_window_unsettled`, F 성분 metric code, KVL·단일 입력 cfg 출처·`sources`, READS 단언 | (손)+(독립) | red | IT-2d |
| T-G | `tests/structure`(또는 integration) | 계약 G1·G2·G6 `git grep` 수(writer 자리 하나·`front_cache` 0·사본 칸 부재·필드별 엔진 소비자 ≥ 1 또는 출력 전용 목록) | (독립) | red | 각 하위 card 끝 |

### 고칠 기존 test(test 주체 몫)

- `tests/sizing/test_s2_values.py:118-124`(`DC_TABLE`에 `dc_output_structure`·`dc_window_def_refined` 행)·`:127-128`(블록 WRITES = 표)·`:70-75`(`DC_TABLE` 길이 33 -> 35)·`:97-106`(S2_WRITERS = S1 + DC_TABLE + SS_TABLE -- `SS_TABLE`에 `ss_nodal`·`icm_config` 두 필드·`metrics_icm_front`) -- 기대 갱신(약화 아님, 표 확대).
- ss 블록 `reuse` 계수 단언 search test → `graft`(변화표에 적음).
- `saturation_window`·`ls_swing` 옛 서명 호출 test.
- IT-1이 지운 `input_tie` 어휘 test는 IT-1 몫.

### red 예상 목록 규칙

엔진 동작·엔진 트리 구조를 보는 test만(T-FD는 green 유지 대상이라 제외). 하네스·비교기·마커 conftest 자체 test 제외(xrunf1b J-O2 상속). 새 키워드 직접 호출 `TypeError`는 red로 세지 않는다.

## 판정 측정(audit, 하위 card마다 + 통합 병합 전 한 번)

| # | 측정 | 합격 |
|---|---|---|
| I-1 | red-green(위 목록), head 통과 | head 0 failed |
| I-2 | graph 단일 정본 G1~G7(별도 검사 항목 -- CLAUDE.md 규칙 7): writer 자리 수, 새 cache·`sctx` 슬롯·`EvalResult` 값 칸·사본 칸 0, 필드별 소비자 표 | 위반 0 |
| I-3 | 9회로 변화표(원인 칸 = IT-0 기록 대비, 41:816 (1)~(7) 원인 분류), 결정성(같은 head 두 번 비트 동일) | 변화가 모두 원인 칸에 있음 |
| I-4 | G-10 9회로 0, WP-10 중복 인자 0, `kernel_calls`·E_B가 두 front 블록 때문에 늘지 않음 | 0 |
| I-5 | `fd_jacobian` y 스텝·θ 프레임 W4 뿌리 창 비트 동일(9회로) | 같음 |
| I-6 | 전체 suite `--run-slow` 한 번, `tests/structure` 위반 0(규칙 A·B·C·H·M) | 통과 |
| I-7 | 이름: 13회로·소자 이름 엔진 코드 0, 새 `-k` 충돌 base·head 수 | 0 / 보고 |
| I-8 | gap-detector(design 41 §4.7 ↔ 구현) ≥ 90 %, 42 D-IT2·D-ICM 행 | 통과 |
