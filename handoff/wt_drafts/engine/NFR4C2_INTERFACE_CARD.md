# NFR-4 card 2 (결정성) interface card 최종본 (card id `nfr4c2`)

- 작성: 2026-10-15(초안) → 같은 날 최종본(design 보완 e8b619f 반영). 엔진·test·git 브랜치는 고치지 않았다.
- **card base = master `e8b619f`**(엔진 코드는 cfe2e31과 같다 -- `git diff --stat cfe2e31 e8b619f -- skills` 0줄).
- design 근거: 40 §2.4.13 (1)~(8)(649~784행), §2.4.14 (3) NFR-4 card 2 관찰 지점 문장, 41 §5.13(1235~1294행), 42 D-ND1~D-ND4. 사용자 결정 'NFR-4 BLAS 결정성', Q-N1~Q-N10, N-1·N-2(정정)·N-3, X-19.
- **test 작성 주체는 소스를 보지 않고 이 문서(2·3절)만 쓴다.**
- 경로 접두 `E/` = `skills/analog-gmid-design/gmid_engine/`.

---

## 2. interface card (공개 계약)

### C1. BLAS 스레드 고정 (`gmid_engine.core.blas_env`, 새 파일)

```text
gmid_engine.core.pin_blas_threads() -> BlasEnvironment          # import gmid_engine 이 1회 부른다(재수출)
gmid_engine.core.blas_environment() -> BlasEnvironment          # 확인·거부·값(재수출). 재확인 지점이 부른다
gmid_engine.core.blas_env.loaded_blas_modules() -> tuple[BlasModule, ...]   # 적재 모듈 열거·기호 찾기(재수출 안 함)
gmid_engine.core.blas_env.BlasModule      # frozen: path(str), family("openblas"|"mkl"|"blis"),
                                          #   set_threads(n), get_threads(), config(), corename(), parallel()  -- 기호 없으면 None
gmid_engine.core.blas_env.BlasEnvironment # frozen·hashable
```

- **import 시점**: `import gmid_engine`(어느 하위 패키지든) 뒤
  - `os.environ["OPENBLAS_NUM_THREADS"] == "1"`.
  - 적재된 OpenBLAS 라이브러리마다 조회 = 1. 지금 환경(실측): numpy 2.4.6 `<numpy 폴더>.libs/libscipy_openblas64_-*.dll`(조회 `scipy_openblas_get_num_threads64_`, 설정 `scipy_openblas_set_num_threads64_`), scipy 1.18.0 `<scipy 폴더>.libs/libscipy_openblas-*.dll`(조회 `scipy_openblas_get_num_threads`, 설정 `scipy_openblas_set_num_threads`). `…get_config…`·`…get_corename…`(`restype = c_char_p`) = 'OpenBLAS 0.3.31… Haswell MAX_THREADS=24'·'Haswell'. 바깥 기본 스레드(환경 변수 없음) = 18.
  - 호출자가 numpy를 먼저 import했어도, 바깥 `OPENBLAS_NUM_THREADS`가 1·8·18·미지정 어느 것이어도 같다.
- **거부(`RuntimeError`, 조용한 대체 없음)**: 빌드 설정 BLAS 이름(`numpy`·`scipy`의 `show_config(mode="dicts")["Build Dependencies"]["blas"]["name"]`)에 `openblas`(대소문자 무시)가 없음, 그 패키지의 BLAS 라이브러리를 못 찾음, `family` `"openblas"` 기록의 `set_threads`·`get_threads`가 None(기호 없음), 설정 뒤 조회 ≠ 1, `family` `"mkl"`·`"blis"` 기록이 하나라도 있음, 열거 미구현 플랫폼(`sys.platform`이 Windows·Linux 밖).
  - `config`·`corename`·`parallel`이 None이면 거부하지 않고 `BlasEnvironment` 해당 항목의 그 값이 None이다.
- **`BlasEnvironment` 구성**: Python 구현·판, `sys.platform`, `platform.machine()`, numpy 판, scipy 판, BLAS 항목 tuple. BLAS 항목 = (family, 소유 패키지, 파일 이름, config, corename, parallel, 확인 스레드 수 = 1). 소유 패키지 = 모듈 파일이 최상위 Python 패키지 폴더 또는 그 형제 `<패키지>.libs` 안이면 그 패키지 이름(지금 `numpy`·`scipy`), 아니면 None. 파일 이름 = 경로 마지막 성분(절대 경로 아님). 항목 순서 = 항목 tuple의 사전식 정렬(None은 빈 문자열로 비교) -- 열거 순서와 무관. 같은 프로세스 두 호출의 core `fp_of` 같음. 바깥 스레드 설정과 무관.
- **교체 지점(계약)**: 모듈 속성 `gmid_engine.core.blas_env.loaded_blas_modules` -- 이름·인자 없는 서명·`BlasModule` tuple 반환·`blas_environment`·`pin_blas_threads`가 모듈 전역 이름으로 부르는 방식은 바뀌지 않는다. test는 Python 호출 가능 객체로 만든 가짜 `BlasModule`(설정이 듣지 않음·조회 2·기호 없음·MKL·BLIS)을 돌려주게 바꿔 `blas_environment()`·`pin_blas_threads()`의 `RuntimeError`를 본다. 빌드 설정·플랫폼은 하위 프로세스에서 `numpy.show_config` 교체·`sys.platform` 대입 뒤 `import gmid_engine`로 본다.
- core는 numpy·scipy를 모듈 수준에서 import하지 않는다(`E/core/*.py` 전부).
- `gmid_engine.core.__all__`에 `pin_blas_threads`·`blas_environment`가 있고 `loaded_blas_modules`·`BlasModule`·`BlasEnvironment`는 없다.

### C2. 재확인 지점 (a)~(e) -- 무상태

| 지점 | 공개 진입(서명 불변) |
|---|---|
| (a) | `gmid_engine.pipeline.run_stage_a(topology_path, spec_path, lut, *, output_dir, supplies_v=None, structure_path=None)` 진입 |
| (b) | `gmid_engine.search.build_search_context(dc_ctx, spec, settings, archive_root, pdk_decl, lut_rule_decl, model_error=(), *, code_fp)` 진입 |
| (c) | `gmid_engine.search.find_front(sctx, given_starts)` 진입 |
| (d) | `gmid_engine.search.layer0_start(sctx, origin=())` 진입 |
| (e) | `gmid_engine.search.solve_eps(sctx, start, minimize, eps, origin)` 호출마다 진입 |

- 재확인 = `blas_environment()`(열거·조회만, 설정 안 함). C1 거부 조건이면 `RuntimeError`.
- **무상태**: 고정 때 모듈 집합과 비교하지 않는다. 조회 1인 새 OpenBLAS 모듈이 실리면 재확인은 통과하고 `blas_environment()` 값에 항목이 하나 늘어 `fp_of`가 달라진다.

### C3. 실행 환경 지문 `env_fp` -- 기록 두 곳

- **단계 A 보고서**(dict `StageAResult.report`와 파일 `<output_dir>/<circuit>.stage_a.json`): 최상위 키 `env_fp` = 재확인 (a)의 `blas_environment()` 값의 core `fp_of`(같은 프로세스에서 test가 부른 `fp_of(blas_environment())`와 같다). **정상·정지 경로 모두**. 최상위 키 집합 = 정확히 14개: `applied_facts, circuit, count_budget, coupling, declared_comparison, env_fp, exit_code, ff_ratio_candidates, orbit_matching_crosstab, review_needed, status, stop_reasons, tables, views`.
- **S3 runs 줄**(`<archive_root>/<context_fp>/runs.jsonl` 줄): 최상위 키 `env_fp` = 재확인 (c) 값의 `fp_of`.
- 없는 곳: evals 줄, `StageAResult` 칸, `SearchContext` 칸, `SearchFront` 칸, `perf`.
- 바뀌지 않음: `build_search_context` 서명(필수 키워드는 `code_fp` 하나), `S3Archive(root, context_fp, code_fp)`.

### C4. 층 0 끌어올림 (BP1, 41 §5.13)

공개 관찰: `gmid_engine.search.layer0_center.centre_start(sctx, rung=None) -> (variables, theta, cells, centre_u)`(서명 불변).

- 기호: 전류 중심 풀이기 해의 θ 전류 ln 좌표 x. 행 m = 원뿔(`schema.current_cone`) 행 중 움직이는 θ 전류를 하나라도 읽는 행. ref_m = 그 MOS 기준 전류(사다리 칸 `StartRung.current_ref`에 있으면 그 값). A_m(x) = Σ_{움직이는 항} 계수·e^{x}/ref_m, F_m = Σ_{고정 항} 계수·고정값/ref_m, q_m(s) = A_m·e^s + F_m. √ε = `math.sqrt(sys.float_info.epsilon)`.
- 식: R = {m : A_m > 0}. R이 비거나 max_{m∈R}(1 + √ε − F_m) ≤ 0이면 s = 0. 아니면 s = max(0, ln max_{m∈R}(1 + √ε − F_m)/A_m). 풀이기 목적값 u는 쓰지 않는다(`centre_u`는 그 u 그대로).
- θ 전류 = exp(min(max(xᵢ + s, loᵢ), hiᵢ)). 끌어올린 점에서 원뿔 행에 c ≤ 0이 있으면 s = 0으로(as-built).
- **적용 조건**: 사다리 칸(`rung`)이 있고 그 `current_ref`가 비어 있지 않을 때만(as-built 그대로). 아니면 끌어올리지 않는다.
- 결과(클램프가 걸리지 않고 원뿔 유지): |min_{m∈R} q_m − (1 + √ε)| ≤ γ_n·(1 + √ε), 나머지 m∈R은 q_m ≥ 1 + √ε. γ_n = n·ε/(1 − n·ε), ε = `sys.float_info.epsilon`, n = 그 toy에서 s 계산(항마다 exp·곱·나눗셈과 합, 분자, 나눗셈, ln) + θ = exp(x + s)(덧셈·exp) + q_m 재계산(항마다 곱·나눗셈과 합)의 연산 수 -- 사칙연산·exp·ln 각 1회로 센다, `max`·`min`·클램프·비교는 세지 않는다.
- 판정 그대로(BP2): `Layer0Result.hard_ok` = 시작점 경성 행(W 하한·반전 하한·원뿔) c ≥ 0 전부.
- **풀이기 해 주입 교체 지점(계약)**: 모듈 속성 `gmid_engine.search.layer0_center.scipy_minimize`(`scipy.optimize.minimize`와 같은 호출 -- 키워드 `jac`·`method`·`bounds`·`constraints`, 반환의 `x`를 읽는다). `centre_start` 호출 동안만 바꾼다(`centre_start`는 전류 중심만 부르고 최대-최소는 부르지 않는다).

### C5. L-b 정지 사유

- `gmid_engine.search.polish_l_cells(sctx, solved, origin) -> (tuple[SolveResult], str)` -- 둘째 값 ∈ {`converged`, `eval_budget`, `wall_budget`}.
- 사유 = **반환 직전 예산 확인 한 번**: `sctx.counters["kernel_calls"] >= sctx.eval_budget`(예산이 있을 때)면 `eval_budget`, 아니고 `sctx.deadline`이 있고 지났으면 `wall_budget`, 둘 다 아니면 `converged`. 끝난 길(while 조건·칸 이동 건너뜀·수락 없는 바퀴)과 무관.
- `find_front` 결과: notes(`SearchFront.notes`와 runs 줄 notes)에 `{"verdict": "l_search", "rule": "LR10", "stops": [...]}`가 **언제나 정확히 한 줄**(L-b가 돌지 않았으면 `stops` 빈 목록). `stops` 원소 = `{"class": 묶음 이름, "l_from": 점 id, "stop": 사유, "accepted": 수락 수}`, L-b 실행 순서대로.
- `perf` 키는 바뀌지 않는다.

### C6. 무거운 test 마커

- 마커 `slow`, 옵션 `--run-slow`(`E/tests/conftest.py`가 등록). `--run-slow` 없으면 `slow` 표시 항목은 수집 뒤 deselected(요약에 `deselected`로 보임), 있으면 실행. `-m` 식과 무관.
- 대상: `E/tests/integration/test_blas_thread_determinism.py` 파일 전체(모듈 수준 `pytestmark`).
- 반드시 포함 실행(판정 agent 전체 suite, 병합 직전): `python -m pytest -q gmid_engine/tests -p no:cacheprovider --run-slow`(위치 `skills/analog-gmid-design`).

### C7. 비교기·실행 하네스 (test 쪽 -- test 작성 주체가 만든다)

- 파일: 비교기 `E/tests/integration/nfr4_compare.py`(엔진을 import하지 않는다), 하네스 `E/tests/integration/nfr4_run_dump.py`(회로 하나의 사슬을 그 프로세스에서 돌려 실행 기록을 파일로 덤프), 단위 test `E/tests/integration/test_nfr4_compare.py`.
- **하네스 수집**(결과 기록에 없는 칸 -- 성공 ε 풀이의 `stop`·`aborts`·`frozen`·`restarts`·`iterations`, `Layer0Result`의 `iterations`·`restarts`·`aborts`·`frozen`·`start_failure`·`rows`, 평가마다 metric 열·cone 행): 관찰 지점(계약) = 모듈 `gmid_engine.search.find_front`(모듈 객체는 `sys.modules["gmid_engine.search.find_front"]` -- `gmid_engine.search.find_front` 이름은 같은 이름 함수가 가린다)의 속성 `layer0_start`·`sweep_front`(반환값을 기록하고 그대로 돌려주는 감싸개), 공개 속성 `SearchContext.cache`(실행 뒤 읽기만). S0 수준 스냅샷은 필드별 덤프(`fp_of`, float는 `float.hex`). 탐색 실행마다 `archive_root`를 준다.
- **실행 방식**: 회로마다 새 프로세스 하나씩 **순차**(`subprocess.run`, 병렬 금지), 환경 = 허용 목록 dict(PATH·SYSTEMROOT·APPDATA·TEMP/TMP(실행별 빈 폴더)·`GMID_LUT_TABLE_CACHE_DIR`(실행마다 빈 폴더)·`PYTHONDONTWRITEBYTECODE`·`PYTHONIOENCODING` + 비교할 바깥 `OPENBLAS_NUM_THREADS`), 실행마다 별도 S3 폴더, E_B 40 선언, 넉넉한 `front_budget_s`, 회로마다 파일로.
- **같은 환경**(두 실행의 `env_fp` 같음·엔진 코드 지문 같음): 1차 검사 = 비트 동일 집합(S0 필드 덤프, 단계 A·B 보고서, 층 0 결과, 탐색 결과(front·pending·unmeasured, ε 풀이 기록, `failed_eps`, `perf`), S3 evals·runs 줄)에서 T 칸(`perf.wall_s`, `perf.eval_time_median_s`, 수렴 `perf` `wall_s`, `eval_times`)만 뺀 것이 비트 동일. 다르면 FAIL, 필드별로 넘어가지 않는다.
- **다른 환경·수치 보존 리팩터링**: D 정확히 같음, C \|Δ\| ≤ 분해능(같은 구역 D가 모두 같을 때만), K 보고만, T 보고만. 부류 정의 = 40 §2.4.13 (3).
- **분해능** = 40 §2.4.13 (4) 표: c 1, W `grid_m`, 면적 `grid_m`·`w_min_m`, 전력 Σ\|V_k\|·tol_I,k, metric `MetricResult.resolution`(None → 판정 불능), `kcl_residual_a` Σ tol_I,k, θ = 그 점 FD 스텝 hᵢ(스냅샷 없으면 판정 불능), 층 0 `t` 1, `failure.margin` 1, 노드 전압 tol_V = 닿는 MOS `dc_tol_v` 최솟값(MOS 없으면 판정 불능), 출처 없는 칸(`centre_u`, 전류 중심 x, 출발 구간 행·사다리·`conflicts`·매크로) = 감도 전파(NFR4-F2 전 판정 불능), `w_m`·`area_est_m2` = max(선언, 전파)(전파 없으면 판정 불능).
- **전제**(하나라도 어기면 판정 불능): (가) E_B 선언(`perf.eval_budget_source`), (나) 벽시계 정지 없음 -- `perf.stops_wall_budget` = 0이고 층 0 `stop`·Halton 사유·ε `stop`·`aborts`·`failed_eps`·L-b `stops`에 `wall_budget` 없음, (다) 같은 실행의 `env_fp` 기록(단계 A 보고서·runs 줄)이 모두 같음 -- 탐색 없는 실행(예: `ngcc_3stage_ff`)은 보고서 하나로 성립, 탐색이 있는데 runs 줄이 없으면 판정 불능.
- **출력**: 보고 JSON -- 맨 위 판정 불능 칸 수, 필드마다 (부류, 기준 값, 비교 값, \|Δ\|, 분해능, 출처, 판정 PASS·FAIL·판정 불능).

### C8. 바뀌지 않는 것

서명: `build_search_context`, `fd_jacobian`, `solve_eps`, `layer0_start`, `centre_start`, `find_front`, `evaluate`, `run_stage_a`, `run_stage_b`, `S3Archive`. 칸: `StageAResult`, `SearchContext`, `SearchFront`. `perf` 키 집합, evals 줄 칸. 판정식 c ≥ 0. S0 수준 값(`E/tests/integration/fixtures/u17_1b_s0_baseline.json` 그대로로 본다 -- 독립 재측정).

---

## 3. test 목록 (id / 위치 / 내용 / 계약 / oracle / base 결과)

oracle: (식) design 식, (손) 손계산·손으로 정한 toy·기록, (비교) 같은 함수 두 출력 비교, (독립) 피검을 거치지 않는 관찰(ctypes OpenBLAS 직접 조회, AST, 파일 읽기, 하위 프로세스), (Py) Python 표준 값. **피검 함수의 출력으로 기대값을 만들지 않는다**(`fp_of(blas_environment())`는 '같은 함수 두 출력 비교'로만 쓴다). **하위 프로세스·9회로 test는 순차**(병렬 금지).

### 3.1 새 test

| id | 위치 | 내용 | 계약 | oracle | base(e8b619f) |
|---|---|---|---|---|---|
| N-T1 | `tests/core/test_blas_env.py`(신규) | 하위 프로세스(바깥 8): `import gmid_engine` 뒤 ctypes로 numpy·scipy `.libs`의 `*openblas*`를 열어 조회 = 1(각각), `os.environ` 값 "1". 공허 방지: 라이브러리 ≥ 2 | C1 | (독립) | red(8) |
| N-T2 | 같은 파일 | 하위 프로세스(바깥 미지정): `import numpy, scipy.linalg` 먼저(전제: 이때 조회 > 1) → `import gmid_engine` → 조회 1 | C1 | (독립) | red |
| N-T3 | 같은 파일 | 바깥 1·8·18·미지정 하위 프로세스 넷(순차): 모두 조회 1, `fp_of(blas_environment())` 넷 같음 | C1 | (독립)+(비교) | red(이름 없음 -- 허용) |
| N-T4 | 같은 파일 | `BlasEnvironment`: hash 가능·칸 대입 예외, 두 호출 `fp_of` 같음, Python 판·`sys.platform`·`platform.machine()`·numpy·scipy 판이 값에 있음, BLAS 항목 2개·각 family `"openblas"`·소유 패키지 {`numpy`, `scipy`}·파일 이름에 경로 구분자 없음·확인 스레드 1, 항목 순서 = 사전식 정렬 | C1 | (Py)+(비교)+(독립: 파일 이름은 `.libs` glob) | red |
| N-T5 | 같은 파일 | 재확인: 하위 프로세스에서 ctypes로 numpy 쪽 설정 API에 2(전제: 조회 2) → 지점 (a)~(e) 각각 호출 `RuntimeError`(매개변수화 5, 입력 toy) | C2 | (독립) | red |
| N-T6 | 같은 파일 | 새 OpenBLAS 모듈: 하위 프로세스에서 import 뒤 numpy OpenBLAS DLL을 임시 폴더에 다른 이름으로 복사·`ctypes.CDLL`(전제 단언: 별도 핸들로 적재, 조회 1) → 재확인 지점 하나 통과, `blas_environment()` BLAS 항목 3개, `fp_of`가 적재 전과 다름 | C2 | (독립)+(비교) | red(함수 없음) |
| N-T7 | 같은 파일 | `loaded_blas_modules` 교체: 설정이 듣지 않는 가짜(조회 2 고정) → `blas_environment()`·`pin_blas_threads()` `RuntimeError` | C1 | (손) | red |
| N-T8 | 같은 파일 | 교체: openblas 기록의 `set_threads` 또는 `get_threads` None → `RuntimeError`. `config`·`corename`·`parallel` None인 가짜(조회 1) → 거부 없음, 그 항목 값 None | C1 | (손) | red |
| N-T9 | 같은 파일 | 교체: family `"mkl"` 기록, `"blis"` 기록 각각 → `RuntimeError` | C1 | (손) | red |
| N-T10 | 같은 파일 | 하위 프로세스: `numpy.show_config`를 BLAS 이름 비 OpenBLAS dict로 교체 뒤 `import gmid_engine` → `RuntimeError`. `sys.platform`을 지원 밖 값으로 대입 뒤 import → `RuntimeError` | C1 | (손) | red |
| N-T11 | 같은 파일 | `E/core/*.py` AST: 모듈 최상위(함수·클래스 밖) `numpy`·`scipy` import 0 | C1 | (독립) | green(성질 유지) |
| N-T12 | 같은 파일 | `gmid_engine.core.__all__`: `pin_blas_threads`·`blas_environment` 있음, `loaded_blas_modules`·`BlasModule`·`BlasEnvironment` 없음 | C1 | (식) | red |
| N-T13 | `tests/pipeline/test_stage_a_report.py`(고침)·`tests/pipeline/test_stage_a.py`(고침) | `test_env_fp_recorded`(보고서 쪽): toy 정상 경로와 정지 경로(기록만 정지·A1_load·A2_structure_json)에서 최상위 키 = C3 14개 정확히, dict와 파일 JSON `env_fp` 같은 값 = 같은 프로세스 `fp_of(blas_environment())` | C3 | (식)+(비교)+(독립: 파일) | red(13개) |
| N-T14 | `tests/search/test_find_front.py` | archive 있는 toy 실행: runs 줄 `env_fp` = 같은 프로세스 `fp_of(blas_environment())`, evals 줄에 `env_fp` 없음, `inspect.signature(build_search_context)` 키워드 전용 = (`code_fp`,) | C3 | (비교)+(독립: 파일)+(식) | red |
| N-T15 | `tests/search/test_l_bin_search.py` | `polish_l_cells` 반환 2-tuple, 사유 `converged`(E_B 넉넉, deadline 없음) | C5 | (식) | red(반환 형식) |
| N-T16 | 같은 파일 | 사유 `eval_budget`(L-b 중 E_B 도달), 두 예산이 함께 닿으면 `eval_budget` | C5 | (식) | red |
| N-T17 | 같은 파일 | 사유 `wall_budget`(`sctx.deadline`을 지난 값, E_B 넉넉) | C5 | (식) | red |
| N-T18 | 같은 파일 + `tests/search/test_find_front.py` | 끝 확인: 수락 없는 바퀴로 끝나도 반환 직전 마감이 지났으면 `wall_budget`. `find_front` notes에 `verdict == "l_search"` 줄이 정확히 하나(L-b 없는 실행은 `stops == []`), `stops` 원소 키 = {class, l_from, stop, accepted}, `perf` 키 집합 base와 같음 | C5 | (식)+(비교) | red |
| N-T19 | `tests/test_conftest_slow_marker.py`(신규, 규칙 H 예외) | 하위 프로세스 `python -m pytest --collect-only -q gmid_engine/tests/integration/test_blas_thread_determinism.py` -- `--run-slow` 없으면 그 파일 항목 전부 deselected, 있으면 전부 수집. 무거운 실행 없음, 임시 test 파일 없음 | C6 | (독립) | red(옵션 없음) |
| N-T20 | `tests/search/test_layer0_center.py` | `test_layer0_lift_closed_form`: 손으로 정한 toy 원뿔(전류 변수·행·ref·고정 전류를 test가 앎, F_m ≠ 0인 행이 최소인 toy 포함). `centre_start(sctx, rung)` 결과 θ로 q_m을 test가 계산: \|min q − (1 + √ε)\| ≤ γ_n·(1 + √ε)(n은 test가 C4 셈 규칙으로 센다), 나머지 ≥ 1 + √ε | C4 | (손)+(식) | red(as-built min q ≈ 1) |
| N-T21 | 같은 파일 | `test_layer0_lift_independent_of_solver_noise`: `scipy_minimize` 교체로 진짜 해의 x를 허용오차 안에서 흔든 두 입력 → 최소 행이 같으면 끌어올린 점의 그 행 `w_min` c(평가 `constraints`)가 둘 다 > 0 | C4 | (비교)+(식) | base red 요구 없음 |
| N-T22 | 같은 파일 | 가장자리(같은 교체 지점으로 x 지정): R 빔 → s = 0, 분자 모두 ≤ 0 → s = 0, 식 값 < 0 → s = 0(낮추지 않음). 기대 θ 전류 = exp(clip(x))(손). 적용 조건: `current_ref` 빈 사다리 칸 → 끌어올리지 않음 | C4 | (손)+(식) | 일부 red 가능 -- 요구 없음 |
| N-T23 | `tests/integration/`(새 파일, slow 아님) | `test_layer0_boundary_rows_positive_9circuits`: 9회로(층 0 없는 `ngcc_3stage_ff` 제외) 층 0 시작점에서 BP1로 경계에 놓인 `w_min:*` 행 c > 0, `hard_ok`가 경계 배치 때문에 False가 아님. 순차 | C4 | (식) | **red(folded_cascode `w_min:M8` c < 0 -- 부호 단언)**. test 동결 전 auditor가 base 재현 확인, 안 되면 멈추고 보고 |
| N-T24 | `tests/integration/test_nfr4_compare.py`(신규) | 같은 환경 1차 검사: 같은 기록 → PASS·판정 불능 0. 비트 동일 집합 칸 하나(D·C·K 칸 각각)의 마지막 비트를 바꾼 기록 → FAIL, 필드별로 넘어가지 않음. T 칸만 다름 → PASS | C7 | (손: 손으로 만든 기록) | red(모듈 없음 -- 허용) |
| N-T25 | 같은 파일 | 필드별: D 불일치 FAIL, C \|Δ\| ≤ 분해능 PASS·초과 FAIL, 같은 구역 D가 다르면 C 비교 안 함, K는 판정 없이 보고 | C7 | (손) | red |
| N-T26 | 같은 파일 | 분해능 식: 손으로 만든 PDK·레일·tol 값에서 c 1, W `grid_m`, 면적 `grid_m·w_min_m`, 전력 Σ\|V_k\|·tol_I,k, 레일 전류 합 Σ tol_I,k, `t`·`margin` 1, 노드 전압 = 닿는 MOS `dc_tol_v` 최솟값 | C7 | (손)+(식) | red |
| N-T27 | 같은 파일 | 판정 불능 분류: metric `resolution` None, θ 칸 스냅샷 없음, MOS 없는 노드, 출처 없는 칸, max(선언, 전파) 칸의 전파 없음 → 판정 불능. 보고 맨 위 수 = 손으로 센 수 | C7 | (손) | red |
| N-T28 | 같은 파일 | `test_first_pass_preconditions`: E_B 미선언, `stops_wall_budget` > 0, 층 0 stop·Halton 사유·ε `stop`·`aborts`·`failed_eps`·L-b `stops` 중 하나에 `wall_budget`, 같은 실행 두 `env_fp` 다름, 탐색 있는데 runs 줄 없음 → 각각 판정 불능(PASS·FAIL 아님). 탐색 없는 실행(보고서 하나)은 (다) 성립 | C7 | (손) | red |
| N-T29 | `tests/integration/test_blas_thread_determinism.py`(다시 씀, `pytestmark = slow`) | 9회로, 회로마다 새 프로세스 둘(바깥 1, max(2, cpu)) **순차**, `nfr4_run_dump` 하네스, 두 실행 `env_fp` 같음, `nfr4_compare` 1차 검사 PASS·판정 불능 0. strict xfail 없음. `test_single_thread_start_fp_matches_base`(기준선 파일 대조) 유지 | C1·C3·C6·C7 | (비교)+(독립: 기준선 파일) | **red**(base 고정 없음 → MANY에서 출발 구간 지문 다름) |

### 3.2 삭제·고칠 test (실측)

| 파일 | 처리 |
|---|---|
| `tests/conftest.py:15-25` | 지움(주석 15-20, 21, 22-23 numpy 선행 거부, 24-25 강제). 27-47 유지. C6 마커·옵션 추가 |
| `tests/convergence/test_converge.py:243` | `OPENBLAS_NUM_THREADS="1"` 지움 |
| `tests/integration/test_no_s0_files_written.py:7·101` | 허용 env의 `OPENBLAS_NUM_THREADS="1"`과 docstring 문구 지움 |
| `tests/integration/test_s0_layer_9circuits.py:11` | 'conftest가 고정' → '엔진 import가 고정'(`:26`·`:275` 그대로) |
| `tests/integration/test_blas_thread_determinism.py` | N-T29(docstring 1-17, `CODE` 40-92, 병렬 `_launch`·`runs` 95-133, xfail 146-153 다시 씀) |
| `tests/pipeline/test_stage_a_report.py:34-35·62`, `tests/pipeline/test_stage_a.py:433-449` | 키 14개(N-T13) |
| `tests/search/test_l_bin_search.py:24·42·50` | 반환 2-tuple |
| `tests/integration/fixtures/u17_1b_s0_baseline.json:2` `_source` | `s0_snapshot` 설명을 새 설명으로(값은 독립 재측정으로 확인) |
| **바꾸지 않음** | `build_search_context` 호출부(서명 불변), `tests/search/test_find_front.py` `perf` 21개 단언 |
| 탐색 값 고정 단언(3안 영향) | 판정 agent 값 변화 목록과 대조해 다시 쓴다. 사전 승인 범위 파일 = `tests/search/test_layer0_center.py`·`test_find_front.py`·`test_residual_probe.py`·`tests/convergence/test_converge_point.py`. 그 밖(`test_eps_sweep.py`·`test_slsqp_outer.py`·`test_search_context.py` 등)이 바뀌면 고치기 전에 보고(사용자 결정 대상). 허용 폭 넓히기 금지 |

### 3.3 이름 규칙

- 새 이름 충돌 0(실측): `blas_env`, `blas_environment`, `pin_blas_threads`, `BlasModule`, `BlasEnvironment`, `loaded_blas_modules`, `nfr4_compare`, `nfr4_run_dump`, `run_slow`, `slow_marker`, `lb_stops`. `run_compare`(tools/spice_oracle)는 쓰지 않는다.
- `-k` 식: `"test_ic"`, `"g10"`, `"ic11 or kvl_branch_residual"`, `"ic1 or ic2 or ic9 or ic10 or shared_gate_net or kcl_residual"`, `"rule_g or design_value_location"`, `rule_k_`, `"duplicate_args or loop_invariant"`, `"mna_assembly_count or mna_solve_count"`, `"dup_w_calc or dup_kcl_edges"`, `"dup_"`, `new_topology`. test 함수 이름에 `kcl_residual`·`ic1`~`ic11`·`g10`·`dup_`·`mna_`·`rule_g`·`rule_k_`·`new_topology` 넣지 않음. 작성 뒤 각 식 `--collect-only` 수 base와 같음 보고.
- 권장 접두: `test_blas_pin_…`(N-T1~N-T12), `test_env_fp_…`(N-T13·N-T14), `test_lb_stop_…`(N-T15~N-T18), `test_layer0_lift_…`(N-T20~N-T22), `test_nfr4_cmp_…`(N-T24~N-T27).

---

## 4. 판정 측정 (audit)

격리 복제본(`<W>/nfr4c2-audit`, base 비교용 base 복제본 따로)에서만. **9회로 방법**: C7 '실행 방식' 그대로(회로마다 새 프로세스, **순차**, 허용 목록 env, 실행마다 빈 표 캐시·별도 S3, E_B 40, 넉넉한 시간 예산, 회로마다 파일, 진행 append). **무거운 실행은 한 번에 하나**(9회로 측정·전체 suite·slow test를 겹치지 않는다).

| # | 측정 | 방법 | 합격 |
|---|---|---|---|
| A-1 | 완료 grep | spec card 1.4.5 | 기대값 |
| A-2 | 고정 관찰 | 하위 프로세스: 바깥 1·8·18·미지정·미지정+numpy 선행 -- ctypes 조회 둘, `os.environ`, `fp_of(blas_environment())` | 모두 1, 다섯 값 같음 |
| A-3 | red-green | head: N-T1~N-T29 통과. base(e8b619f) + 새 test: N-T1·N-T2·N-T5·N-T13·N-T15·N-T19·N-T20·N-T29는 단언 실패 red, N-T23은 folded `w_min:M8` c < 0 부호 단언 red(test 동결 전 확인), 새 API test는 ImportError·AttributeError red 허용(card 1 J-7 선례) | 메시지·해시 기록 |
| A-4 | **완료 조건 (iii)** | head 9회로 × R1(바깥 1)·R2(1 다시)·R3(8)·R4(18)·R5(미지정 + numpy 선행) = 45 프로세스 순차(약 4,500 s). 비교기 1차 검사 R1 대 R2~R5. 판정 기록에 `env_fp`·엔진 코드 지문·비교 보고 경로 | 36 비교 PASS, 판정 불능 0, `env_fp` 같음 |
| A-5 | 기준선(N-1·N-3 규칙) | (a) `test_s0_layer_9circuits.py` head 통과(`u17_1b_s0_baseline.json` 대조) (b) base(e8b619f, 바깥 1)·head 같은 하네스 9회로 1회씩: 층 0 notes·시작점 c, ε 풀이 기록, front·pending·unmeasured, `failed_eps`, 시간 칸 뺀 `perf`, S3 줄 → 값 변화 목록(회로·칸·옛 값·새 값). 변화마다 사전 승인 범위 (가)~(라) 대조, (라)는 '같은 원인' 근거를 적음. `run_id`·`code_fp`는 따로 표시 | 범위 안 통과. 범위 밖(기준선 파일 값, 다른 회로, 다른 원인, 다른 test 파일)은 판정 기록에 따로 적고 병합 전 사용자 결정 |
| A-6 | 다른 환경(보고만) | 가능하면 판이 다른 venv 1개로 필드별 | 보고만. pushpull D 불일치 = D-ND4, 매크로·출발 구간 C 판정 불능 = NFR4-F2 |
| A-7 | 전체 suite·구조 | 바깥 `OPENBLAS_NUM_THREADS` 미지정 셸에서 `python -m pytest -q gmid_engine/tests -p no:cacheprovider --run-slow`(한 번, 다른 무거운 실행과 겹치지 않게), `tests/structure` 위반 0, `-m structure_test_mapping` base 비교 | 0 failed, 위반 0, H = base 이하 |
| A-8 | 바뀌지 않을 것 | `git diff base..head -- E/search/archive.py E/core/compute_block.py E/lut/table_cache.py E/search/macro_poles.py E/search/fd_jacobian.py E/search/start_intervals.py E/search/iv_area.py E/search/iv_matching_l.py E/search/iv_noise.py` 0줄. `build_search_context`·`run_stage_a`·`find_front`·`solve_eps`·`layer0_start`·`centre_start` 서명, `StageAResult`·`SearchContext`·`SearchFront` 칸, `perf` 키, 판정식 `c >= 0` 그대로 | 0줄·같음 |
| A-9 | 이름 충돌 | 3.3 `-k` 식 `--collect-only` head = base | 같음 |
| A-10 | 비용(보고만) | import 시간(실측 0.51 s), 재확인 1회(실측 22.6 ms), 9회로 사슬 합 head 대 base | 판정 아님 |
| A-11 | 공통 | design §10.4, §2.4.8 소유표, gap-detector ≥ 90 %, 42 NFR-4·D-ND1~D-ND3 OK·D-ND4 DEV, NFR4-F1·F2 백로그, 관찰 지점 계약 넷 유지 | 통과 |

---

## 5. 공통 브리핑

spec card 2절과 같다(base = master `e8b619f`, 메모리 제약: 무거운 실행은 한 번에 하나·순차·병렬 금지). test agent는 이 문서 2·3절만 읽고 소스를 보지 않는다.
