# NFR-4 card 2 (결정성: BLAS 고정·BP1~BP3·③ 비교기·L-b 정지 사유) spec card 최종본 (card id `nfr4c2`)

- 작성: 2026-10-15(초안) → 같은 날 최종본(design 보완 e8b619f 반영). 엔진·test·git 브랜치는 고치지 않았다.
- **card base = master `e8b619f`**(nfr4c2-design 병합: dcbac89·948b347·f190c80, 독립 검증 92 차단 0). 엔진 코드는 cfe2e31·609965d와 같다(`git diff --stat cfe2e31 e8b619f -- skills` 0줄, 바뀐 것은 design 40·41·42·history).
- 실측 기준: 측정 복제본 `wt/_scratch_nfr4card`(`--detach cfe2e31`, 엔진 코드 = e8b619f)에서 grep·읽기만, 가벼운 측정 스크립트 `wt/_scratch_nfr4card_m/{probe.py,pin.py}`(9회로 실행 없음). 복제본은 깨끗함 확인 뒤 `git worktree remove`로 제거했다.
- design 근거(e8b619f 줄 번호): `docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md` §1.2 EP-9(107행), §2.4.13(649~784행: (1) 667~691, (2) 693~705, (3) 707~716, (4) 718~735, (5) 737~751, (6) 753~755, (7) 757~765, (8) 767~784), §2.4.14 (3) 재작성 범위표의 NFR-4 card 2 관찰 지점 계약 문장(819·832·835·836·837행). `…41-gain-budget.design.md` §5.13(1235~1294행). `…42-gap-checklist.design.md` NFR-4 행·D-ND1~D-ND5. 계획 NFR-4·IC2·U-77~U-86.
- 사용자 결정 원문 `wt/_drafts/user_decisions.md`: 'NFR-4 BLAS 결정성', 'NFR-4 세부 결정 Q-N1~Q-N10', '실행 사이 재사용 제거', 'U-87~U-89·NFR4-F2·front 조회', X-19, **'NFR-4 card 2 기준선 변화 사전 승인'(N-1, N-2)**, **'NFR-4 card 2·offset trim 결정'(N-2 정정, N-3)**.
- 경로 접두 `E/` = `skills/analog-gmid-design/gmid_engine/`. design의 J-1~J-16 결정은 '오케스트레이터 기본안(사용자 결정 아님)'으로 design에 적혀 있고, N-1~N-3만 사용자 결정이다.

---

## 1. spec card

### 1.1 목표 (사용자 의도 원문)

- "1안·3안 진행하고 ③ 기준 변경도 승인해". 1안 = 엔진이 BLAS 스레드를 1로 고정. 3안 = 판정 경계에 일부러 맞춘 점 규칙(BP1~BP3, 층 0 끌어올림 닫힌 식). ③ = 같은 환경 비트 일치(1차 검사), 다른 환경·수치 보존 리팩터링 필드별 비교. 2안(순수 Python SQP)은 하지 않는다.
- "기본안대로 진행해"(Q-N1~Q-N10). "나로 해"(실행 사이 재사용 제거 -- S0 키 (iv)·Q-N1·Q-N5·Q-N8 대상 소멸).
- X-19: 이 card가 XRUN-F1 card A·B·C보다 먼저.
- N-1·N-3: 3안 기준선 변화 사전 승인(범위 안 통과, 범위 밖 사용자 보고). N-2(정정): 9회로 결정성 test는 두 설정(바깥 스레드 1, max(2, cpu)), 기본 suite에서 빼고 무거운 test 마커, 판정 agent 전체 suite·병합 직전에는 반드시 실행.
- 목표 한 줄: **엔진이 import 때 BLAS 스레드를 1로 고정·확인하고(못 하면 거부) 진입마다 무상태로 재확인하며, 실행 환경 지문을 단계 A 보고서와 S3 runs 줄에 남긴다. 층 0 끌어올림을 닫힌 식 + √ε 여유로 바꾸고, L-b 정지 사유를 기록하며, 같은 환경 두 실행의 비트 동일을 test 쪽 비교기로 판정한다.**

### 1.2 구현하는 design 절

| design 절 | 내용 | 이 card |
|---|---|---|
| 40 §2.4.13 (1) | 고정(시점·방법·거부·빌드 설정 출처·모듈 열거), 파일·공개 이름(J-1), 무상태 재확인 (a)~(e)(J-2), 결과 값과 기록 자리(J-4), 거둘 test 고정, test 주입·관찰 지점(J-3) | 구현 |
| 40 §2.4.13 (2) | 비트 동일 집합, 벽시계 경로, 1차 검사 전제 (가)(나)(다) | 비교기(test)·L-b 기록(code) |
| 40 §2.4.13 (3)·(4) | D·C·K·T, 분해능 표, 감도 전파(NFR4-F2 전 판정 불능) | 비교기(test) |
| 40 §2.4.13 (5) | 완료 조건 (i)~(iv), 비교기·하네스 위치(J-8), 결과 기록 밖 칸 수집(J-7), L-b 정지 사유 기록(J-5), 하네스·9회로 test 실행 방식과 무거운 test 마커(J-10·N-2), 기준선 변화 판정 규칙(N-1·N-3)과 B-1~B-3 | 구현·test·판정 |
| 40 §2.4.13 (6) | 캐시 키 비트 지문 유지 | 바꾸지 않음 확인 |
| 40 §2.4.13 (7) | 다시 쓸 test·새 test·XRUN-F1 A·C와의 경계·바꿀 코드 위치 | 1.4 |
| 40 §2.4.14 (3) | card A·B·C가 이 card의 관찰 지점 계약(`layer0_center.scipy_minimize`, `find_front`의 `layer0_start`·`sweep_front`, 재확인 (c)(d)(e), runs 줄 `env_fp`, notes `l_search`, L-b 반환)을 유지 | 계약 정의(이 card) |
| 41 §5.13 | BP1~BP3, 끌어올림 식·적용 조건(J-9)·√ε 정의식(J-6)·가장자리, test 3개(반올림 범위 J-15, 풀이기 해 주입 J-16, base red J-14) | 구현 |
| 42 NFR-4·D-ND1~D-ND4 | MISS·DEV → 완료 시 OK(D-ND4는 알려진 결함 DEV 유지), D-ND5 N/A | 판정 뒤 오케스트레이터 |

범위 밖: 2안, NFR4-F1(pushpull 외층 FD 열 실패·재시작 조사), NFR4-F2(매크로 해 주입 진입 -- 그 전까지 매크로·출발 구간 C 칸은 다른 환경 비교에서 판정 불능), LUT 파생표 캐시 키(Q-N6), 블록 입력 버전 키, XRUN-F1 A·B·C, IC2 파이프라인 단위 순서 섞기 test, `_REL` 공개화·core √ε 정본(J-6 범위 밖 정리).

### 1.3 대상 소멸 항목 (card 1 `xrun` 병합으로)

근거(엔진 전체 `git grep -nw`): `S0SnapshotStore`·`S0Slot`·`snapshot_codec`·`type_registry`·`KEY_CODE_FP`·`load_evals`·`load_runs`·`_disk_failures`·`disk_hits`·`disk_failures`·`pdk_decl_path`·`STAGE_B_WRITERS`·`GMID_S0_SNAPSHOT_DIR`·`KEY_ENV_FP` 모두 0. `s0_snapshot`은 `E/tests/integration/fixtures/u17_1b_s0_baseline.json:2` `_source` 설명 1건.

| # | 옛 항목 | 상태 |
|---|---|---|
| Z-1 | S0 키 (iv) 실행 환경 지문 | 소멸 -- `env_fp`는 결과 기록 칸만 |
| Z-2 | Q-N1 U-68 정리의 환경 칸 | 소멸 |
| Z-3 | Q-N5·D-ND5 S3 실행 간 재사용 `env_fp`(`S3Archive(..., *, env_fp)`) | 소멸 -- `S3Archive(root, context_fp, code_fp)` 불변 |
| Z-4 | Q-N8 넓은 S0 키 | 소멸 |
| Z-5 | §2.4.9 판정 2 | 소멸(40:566) |
| Z-6 | 40 §2.4.3의 'BLAS 스레드 고정'·'실행 환경 지문' 행 | 행 없음 -- 규칙은 §2.4.13 (1) |
| Z-7 | test 쪽 S0 폴더 고정 | 이미 지움 |
| Z-8 | 감사의 '빈 S0' 조건 | 소멸(S3 출력 폴더 분리만 남음) |
| Z-9 | 옛 초안의 순수 Python SQP(2안) | 소멸 |
| Z-10 | 옛 design N-6 '`env_fp` 출처 하나 + `build_search_context` 필수 인자 `env_fp`' | **J-4로 대체** -- 서명·`SearchContext`·`StageAResult`·`SearchFront` 불변, tests 약 30곳 호출부 변경 없음 |
| Z-11 | 옛 design '새 BLAS 모듈이 생겼으면 `RuntimeError`' | **J-2로 대체** -- 조회 1인 새 OpenBLAS 모듈은 통과하고 `env_fp` 차이(전제 (다))로 드러남 |

### 1.4 삭제·변경 목록 (e8b619f = cfe2e31 엔진 재측정)

#### 1.4.1 엔진 소스

| # | 대상 | 위치(실측) | 처리(design) |
|---|---|---|---|
| N1 | 새 파일 `E/core/blas_env.py` | 신규. 이름 충돌 0(`blas_env`·`blas_environment`·`pin_blas_threads`·`BlasModule`·`BlasEnvironment`·`loaded_blas_modules`, 엔진·tests·tools) | 40 (1) J-1: 공개 최상위 정의 = `BlasModule`(frozen, 칸 `path`·`family`(`"openblas"`·`"mkl"`·`"blis"`)·`set_threads`·`get_threads`·`config`·`corename`·`parallel`), `BlasEnvironment`(frozen·hashable), `loaded_blas_modules() -> tuple[BlasModule, ...]`, `blas_environment() -> BlasEnvironment`, `pin_blas_threads() -> BlasEnvironment`. 진입점(규칙 A) = `pin_blas_threads` 하나(앞 넷은 같은 파일 다음 정의가 이름으로 부른다). numpy·scipy는 함수 안 import. 빌드 설정 출처 = `show_config(mode="dicts")["Build Dependencies"]["blas"]["name"]`에 `openblas`(대소문자 무시). Windows `EnumProcessModules`+`GetProcAddress`, Linux `/proc/self/maps`, 그 밖 `RuntimeError`. `BlasEnvironment` BLAS 항목 = (family, 소유 패키지, 파일 이름(절대 경로 아님), config, corename, parallel, 확인 스레드 수), 항목 순서 = 사전식 정렬(None은 빈 문자열로). `config`·`corename`·`parallel` None은 거부 아님, `openblas`의 `set_threads`·`get_threads` None은 거부, `mkl`·`blis` 기록은 있는 것만으로 거부 |
| N2 | `E/__init__.py` | 3줄(docstring, `__all__ = ()`) | `from gmid_engine.core import pin_blas_threads` 뒤 1회 호출(규칙 C 루트 형식) |
| N3 | `E/core/__init__.py` | 재수출 3-31행, `__all__` 34행~ | `pin_blas_threads`·`blas_environment`만 재수출(나머지는 test가 `gmid_engine.core.blas_env`로) |
| N4 | 재확인 (a) + 단계 A 보고서 `env_fp` | `E/pipeline/stage_a.py:195-196` 진입, 보고서 dict 정지 `_stopped` 93-97·정상 240-243 | 진입의 재확인 (a) = `blas_environment()` 한 번(그 반환값이 기록 값), 보고서 최상위 키 `env_fp` = `fp_of(반환값)`, 정상·정지 경로 모두. 키 13 → 14. **`StageAResult` 칸 추가 없음**(J-4) |
| N5 | 재확인 (b) | `E/search/search_context.py:199` `build_search_context` 진입 | 재확인만(기록 없음). **서명·`SearchContext` 불변**(J-4) |
| N6 | 재확인 (c) + runs 줄 `env_fp` + notes `l_search` | `E/search/find_front.py:75` 진입, runs 줄 record 140-149, notes 83-125 | 진입의 재확인 (c) 반환값 `fp_of`를 runs 줄 최상위 키 `env_fp`에(`find_front`가 만드는 record dict -- `archive.py` 불변). notes에 `{"verdict": "l_search", "rule": "LR10", "stops": [...]}` 언제나 한 줄(L-b 없으면 빈 목록) -- runs 줄 notes와 `SearchFront.notes`에 함께. `perf` 키 불변. `SearchFront` 칸 불변 |
| N7 | 재확인 (d) | `E/search/layer0_center.py:638` `layer0_start` 진입 | 재확인만 |
| N8 | 재확인 (e) | `E/search/slsqp_outer.py:102` `solve_eps` 진입 | 재확인만(끝점·ε 풀이·L-b 모두 이 함수) |
| N9 | 층 0 끌어올림(BP1) | `E/search/layer0_center.py:238-246`(주석 238-239, `lift = u` 240, 시도 루프 241-246), 반환 247, 행 `rows` 207-209, `ref` 190-193, 클램프 244 | 41 §5.13 식: A_m·F_m, e^s = max_{m: A_m > 0}(1 + √ε − F_m)/A_m, s = max(0, ln 그 값), R 빔 또는 분자 모두 ≤ 0이면 s = 0. **√ε = `math.sqrt(sys.float_info.epsilon)`을 그 자리에서**(J-6, 선례 `macro_poles.py:282`·`iv_matching_l.py:99` -- `_REL` import 금지 규칙 B). **적용 조건 as-built 그대로**(J-9: 사다리 칸이 있고 `current_ref`가 비어 있지 않을 때만). 원뿔 깨지면 0·상자 클램프 as-built. `lift = u` 줄 삭제, u는 `centre_u` 반환값으로만 |
| N10 | 끌어올림 설명 문장 | 주석 238-239, `E/search/CONTRACT.md:1063-1065`(U13.2 '해의 편차 u(ln)만큼 … 올려'), 모듈 docstring 2번 항목 12-18(끌어올림 설명 없음) | 주석·CONTRACT를 닫힌 식으로, docstring 2번 항목에 한 문장 추가 |
| N11 | L-b 정지 사유 | `E/search/l_bin_search.py:32-34`(`_exhausted`), 37-73(`polish_l_cells`: 41 while 단락, 49 칸 이동 건너뜀, 63-66 버림) | 40 (5) J-5: 반환 `(수락 풀이 tuple, 정지 사유)`. **반환 직전 예산 확인을 한 번 더** -- 걸리면 그 사유, 아니면 `converged`. 우선순위 = 커널 호출 수 ≥ 평가 예산 → `eval_budget`, 아니고 마감 넘음 → `wall_budget`(as-built `_budget_stop` `slsqp_outer.py:94-99`와 같음). 버려진 `solve_eps` 정지는 따로 기록하지 않음 |
| N12 | `sweep_front`의 L-b 모음 | `E/search/eps_sweep.py:118-123`(호출 121) | L-b 실행마다 `{"class": 묶음 이름, "l_from": 점 id, "stop": 사유, "accepted": 수락 수}`를 실행 순서대로 반환 dict 키 `lb_stops`(tuple) |
| N13 | 모듈 지도 | `E/_module_map.py:40-51`(core 층 표), 195-240(core `ModuleEntry`) | `core/blas_env.py` `ModuleEntry`(kind `"entry"`, 진입점 `pin_blas_threads`, 계획 ID NFR-4·EP-9) + 층 표 |
| N14 | 함수 레지스트리 §2 | `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` 31~61행(관련 행 0) | code 주체 같은 변경: 'BLAS 스레드 고정·실행 환경 값' = `gmid_engine.core.pin_blas_threads`·`blas_environment`, '층 0 끌어올림(경계 배치점 닫힌 식)' = `layer0_center._current_centre` |

**관찰 지점 계약**(이 card가 정의, XRUN-F1 A·B·C가 유지 -- 40 §2.4.14 (3)): (가) `gmid_engine.core.blas_env.loaded_blas_modules`(이름·인자 없는 서명·`BlasModule` tuple 반환·같은 파일이 모듈 전역 이름으로 부르는 방식), (나) `gmid_engine.search.layer0_center.scipy_minimize`(이름·키워드 호출 `jac`·`method`·`bounds`·`constraints`·반환 `x` 읽기), (다) 모듈 `gmid_engine.search.find_front`의 속성 `layer0_start`·`sweep_front`(모듈 전역 이름 호출 -- 모듈 객체는 `sys.modules`로; 같은 이름 함수가 패키지 이름을 가린다), (라) 공개 속성 `SearchContext.cache`(실행 뒤 읽기만).

바꾸지 않는 것: `E/search/archive.py`, `build_search_context` 서명·`SearchContext`·`StageAResult`·`SearchFront` 칸, `perf` 키, 41 §5.13 같은 종류 자리 표의 '준수'·'해당 없음' 자리(`start_intervals.py:126-128·137-152·390-395`, `iv_area.py:72-78`, `iv_matching_l.py:63·99`, `iv_noise.py:61`, `layer0_center.py:244`·`_halton_probe`, `macro_poles.py:353-357`, `layer0_center.py:374`·`slsqp_outer.py:195`), 판정식 c ≥ 0(`layer0_center.py:407·683`, `slsqp_outer.py:230` -- BP2), 블록 입력 버전 키, LUT 파생표 캐시 키.

사실 메모: notes `verdict` 값 `"l_search"`는 `E/search/search_values.py:23` `STAGE_L_SEARCH = "l_search"`, `l_bin_search.py:62` `StartPoint` 출처 `"l_search"`와 같은 문자열이다(다른 칸 -- 충돌 아님).

#### 1.4.2 CONTRACT

| 위치 | 처리 |
|---|---|
| `E/core/CONTRACT.md` 새 절 §12(현재 마지막 §11 524-530행), §0 파일 표 | `blas_env` 계약(interface C1·C2) |
| `E/pipeline/CONTRACT.md:11-12`(보고서 키 집합) | 키 `env_fp`(14개), 재확인 (a) |
| `E/search/CONTRACT.md` §3.14(493-499 `polish_l_cells` 반환), §3.16(506- `find_front`: 재확인 (c), runs 줄 `env_fp`, notes `l_search`), runs 줄 칸 목록(649-651), §3.21 2(336-339), U13.2(1063-1065), §3.9(432·437 재확인 (b) 한 문장) | 갱신 |

#### 1.4.3 test (test 주체 몫, 실측)

| 파일 | 처리 |
|---|---|
| `E/tests/conftest.py:15-25` | 지움(주석 15-20, `_BLAS_THREAD_ENV` 21, numpy 선행 import 거부 22-23, 강제 24-25). 표 캐시 27-47 유지. **무거운 test 마커 추가**: `pytest_addoption` `--run-slow`, `pytest_configure` 마커 `slow` 등록, `pytest_collection_modifyitems`가 `--run-slow` 없으면 `slow` 항목을 `pytest_deselected`로(선례 `E/tests/structure/conftest.py:37-55` -- 그 선례는 `-m`이 있으면 손대지 않는데, 이 마커는 `-m`과 무관하게 옵션으로 가른다) |
| `E/tests/convergence/test_converge.py:243` | `OPENBLAS_NUM_THREADS="1"` 지움 |
| `E/tests/integration/test_no_s0_files_written.py:7·101` | 하위 프로세스 허용 env의 `OPENBLAS_NUM_THREADS="1"`과 docstring 문구 지움(J-11) |
| `E/tests/integration/test_s0_layer_9circuits.py:11` | 'conftest가 고정' → '엔진 import가 고정'. `:26`·`:275`는 그대로(N-2 비차단) |
| `E/tests/integration/test_blas_thread_determinism.py` | 다시 씀: strict xfail(146-153) 삭제, 병렬 `Popen`(114) → 순차 `subprocess.run`, 9회로 · S0 전 필드 · 층 0 · 탐색 결과, 바깥 1 대 max(2, cpu) 1차 검사, 모듈 수준 `pytestmark = pytest.mark.slow`(파일 전체 -- module fixture 때문), `test_single_thread_start_fp_matches_base` 유지 |
| `E/tests/pipeline/test_stage_a_report.py:34-35·62`, `E/tests/pipeline/test_stage_a.py:433-449`(`REPORT_KEYS`, `len == 13`, docstring 447) | 키 14개 |
| `E/tests/search/test_l_bin_search.py:24·42·50` | `polish_l_cells` 반환 형식 |
| `E/tests/integration/fixtures/u17_1b_s0_baseline.json:2` `_source` | `s0_snapshot` 설명을 새 설명으로(값 같으면 승인 대상 아님, J-12) |
| 새 test 파일 | `E/tests/core/test_blas_env.py`(규칙 H), `E/tests/integration/nfr4_compare.py`(비교기, 엔진 import 없음)·`nfr4_run_dump.py`(하네스)·`test_nfr4_compare.py`(단위 test), `E/tests/test_conftest_slow_marker.py`(마커 동작 -- 규칙 H 예외: `tests/` 바로 아래, `structure_checks.py:955` `len(tparts) < 2` 건너뜀), 41 §5.13 test(`tests/search/test_layer0_center.py` 둘, 9회로 하나는 `tests/integration/`), L-b 사유 test(`tests/search/test_l_bin_search.py`), `env_fp` 기록 test |
| **변경 없음**(옛 초안에서 삭제) | `build_search_context` 호출부 tests 17파일 약 30곳(J-4로 서명 불변), `tests/search/test_find_front.py` `perf` 21개 단언 |
| 탐색 값 고정 단언 | 기준선 판정 규칙(1.10)대로. 후보: `test_layer0_center.py`·`test_find_front.py:44-47`·`test_residual_probe.py`·`test_converge_point.py:195·225·264·360`(사전 승인 범위), `test_eps_sweep.py`·`test_slsqp_outer.py`·`test_search_context.py`(범위 밖 -- 바뀌면 사용자 보고) |

#### 1.4.4 문서

| 위치 | 처리 | 주체 |
|---|---|---|
| 함수 레지스트리 §2 | N14 | code, 같은 변경 |
| 42 NFR-4·D-ND1~D-ND3 OK, D-ND4 DEV 유지 | 판정 뒤 | 오케스트레이터 |
| NFR4-F1·NFR4-F2 백로그 등록 | 완료 조건 (iv) | 오케스트레이터 |

#### 1.4.5 완료 grep

| 이름 | 범위 | 기대 | 실측 base |
|---|---|---|---|
| `lift = u` | `E/search/layer0_center.py` | 0 | 1(240) |
| `OPENBLAS_NUM_THREADS` | `E/tests/conftest.py`, `E/tests/convergence/test_converge.py`, `E/tests/integration/test_no_s0_files_written.py` | 0 | 4·1·2 |
| `_BLAS_THREAD_ENV` | 엔진 전체 | 0 | 2 |
| `xfail` | `E/tests/integration/test_blas_thread_determinism.py` | 0 | 1 |
| `_REL` | `E/search/layer0_center.py` | 0(정의식을 그 자리에서) | 0 |
| 설정 기호(`set_num_threads` 조합) | 엔진 소스(tests 제외) | `E/core/blas_env.py` 밖 0 | 0 |
| 모듈 수준 `numpy`·`scipy` import | `E/core/*.py` | 0 | 0 |

### 1.5 배선

```text
import gmid_engine      -> pin_blas_threads(): env "1" -> numpy·scipy.linalg 적재 -> loaded_blas_modules() -> 설정 1 -> blas_environment()로 확인(실패 RuntimeError)
run_stage_a             -> 재확인 (a) = blas_environment() -> 보고서 "env_fp" = fp_of(그 값)  (정상·정지)
build_search_context    -> 재확인 (b)  (서명 불변, 기록 없음)
find_front              -> 재확인 (c) = blas_environment() -> runs 줄 "env_fp"
  layer0_start          -> 재확인 (d) -> centre_start -> _current_centre: SLSQP x -> s(닫힌 식, √ε 정의식, 조건 as-built) -> θ 전류 × e^s
  solve_eps (매번)       -> 재확인 (e)
  sweep_front -> polish_l_cells -> (수락, 사유[반환 직전 확인]) -> lb_stops -> find_front notes "l_search"
재확인 = 무상태: 지금 적재된 OpenBLAS 모듈 전부 조회 1, MKL·BLIS 없음, (1) 거부 조건 아님
```

### 1.6 결과 JSON·공개 API 형식 변경

| 출력·API | 변경 |
|---|---|
| 단계 A 보고서(dict·파일) | 최상위 키 `env_fp` → 14개(정상·정지) |
| S3 runs 줄 | 최상위 키 `env_fp`, notes 한 줄 `l_search` |
| `SearchFront.notes` | `l_search` 한 줄 |
| `polish_l_cells` | 반환 `(tuple[SolveResult], str)` |
| `sweep_front` 반환 dict | 키 `lb_stops` |
| `gmid_engine.core` | `pin_blas_threads`·`blas_environment` 재수출, 모듈 `core.blas_env` |
| import 부작용 | `OPENBLAS_NUM_THREADS="1"`, numpy+scipy 적재(실측 0.51 s/프로세스), 지원 밖 BLAS·플랫폼 → import `RuntimeError` |
| `run_id`·`code_fp` 값 | 코드 변경으로 바뀜(형식 불변) |
| 바뀌지 않음 | `build_search_context` 서명, `SearchContext`·`StageAResult`·`SearchFront` 칸, `perf` 키, evals 줄, `S3Archive` |

### 1.7 완료 조건

1. (i) L-b 정지 사유가 결과 기록(runs 줄·`SearchFront.notes`의 `l_search`)에 남는다.
2. (ii) 단계 A 보고서·S3 runs 줄에 `env_fp`, 같은 프로세스 `fp_of(blas_environment())`와 같음.
3. (iii) 비교기 첫 실행 9회로 같은 환경 두 번: 비트 동일 집합 전체 같음, 판정 불능 0. 판정 agent A-4: 바깥 1·1·8·18·미지정(+numpy 선행) 다섯 실행, R1 대 R2~R5 모두 PASS·판정 불능 0·`env_fp` 같음.
4. (iv) 42 D-ND4 알려진 결함 기록, NFR4-F1(·F2) 등록.
5. 1안 test(N-T1~N-T12), `env_fp`(N-T13·N-T14), L-b(N-T15~N-T18), 마커(N-T19), 3안 test(N-T20~N-T23 -- 9회로 test head 통과·base red), 비교기(N-T24~N-T28), 결정성 slow test(N-T29) 통과.
6. 1.4.5 grep 기대값.
7. 기준선 판정 규칙(1.10)대로 값 변화 목록 작성, 범위 밖 변화가 있으면 병합 전 사용자 결정.
8. 전체 suite `python -m pytest -q gmid_engine/tests -p no:cacheprovider --run-slow`(판정 agent, 병합 직전) 통과 -- 바깥 `OPENBLAS_NUM_THREADS` 미지정 셸. 기본 실행은 `deselected` 수 표시. `tests/structure` 위반 0, 규칙 H base 비교.
9. 공통 완료 조건(§10.4), gap-detector ≥ 90 %, `_module_map`·레지스트리 같은 변경.

### 1.8 위험·순서

#### 1.8.1 동작

- BP1 값 변화: 41 §5.13 실측(34932a9)은 folded·common_gate뿐. base(cfe2e31 = e8b619f 엔진)에서는 다시 재지 않음 -- 판정 agent가 base·head 같은 하네스로. folded red 재현은 test 동결 전 확인(J-14 결정: 재현 안 되면 멈추고 보고).
- `centre_start` 다른 소비자: `search_context.py:138`(`_wire_sweep_memo` 임시 평가 → LUT memo 상한·`lut_memo_evictions`), `residual_probe.py:67`(엔진 호출부 0, test 값).
- 무상태 재확인의 한계(J-2): 조회 1인 새 OpenBLAS 모듈은 재확인을 통과하고 `env_fp` 차이로만 드러난다(전제 (다)). design이 '옛 design 문장과 다름'으로 보고 대상이라 적었다.
- import 비용 0.51 s, 재확인 열거 약 23~27 ms × 진입 수. 바깥 프로세스 환경 변수 변경.
- 9회로 slow test 약 1,800 s(두 설정), A-4 다섯 설정 약 4,500 s -- 순차.

#### 1.8.2 이름 충돌 (실측)

- 0건: `blas_env`, `blas_environment`, `pin_blas_threads`, `BlasModule`, `BlasEnvironment`, `loaded_blas_modules`, `nfr4`, `nfr4_compare`, `nfr4_run_dump`, `field_class`, `compare_runs`, `run_slow`·`--run-slow`, `slow_marker`, `lb_stops`. `run_compare`는 `tools/spice_oracle/tests/` 함수(쓰지 않음). `l_search`는 1.4.1 사실 메모.
- `-k` 식: `"test_ic"`, `"g10"`, `"ic11 or kvl_branch_residual"`, `"ic1 or ic2 or ic9 or ic10 or shared_gate_net or kcl_residual"`, `"rule_g or design_value_location"`, `rule_k_`, `"duplicate_args or loop_invariant"`, `"mna_assembly_count or mna_solve_count"`, `"dup_w_calc or dup_kcl_edges"`, `"dup_"`, `new_topology`. test 함수 이름에 `kcl_residual`·`ic1`~`ic11`·`g10`·`dup_`·`mna_` 넣지 않음.

#### 1.8.3 XRUN-F1 card A와 겹침 (이 card가 먼저 병합, X-19)

| 파일·이름 | 이 card | card A | 영향 |
|---|---|---|---|
| `E/search/layer0_center.py` | 238-246 끌어올림, 638 재확인 (d), docstring 2번 항목, `scipy_minimize` 관찰 지점 계약 | `_maxmin` 270-288·353·411-412, `centre_start` docstring 631-632 | 줄 번호 이동 -- card A가 병합 뒤 다시 잰다. card A는 `scipy_minimize` 모듈 전역 호출 방식을 유지(40 §2.4.14 (3) 819행) |
| `E/search/slsqp_outer.py` | 102 `solve_eps` 진입 재확인 (e) | 51-76 `_layout`, 104·110-118 `to_theta` 삭제 | 같은 함수 머리 -- 병합 충돌 가능(문맥) |
| `E/search/search_context.py` | `build_search_context` 진입 재확인 (b)(서명 불변) | 134-150 `_wire_sweep_memo` | 다른 함수 |
| `E/search/find_front.py` | 75 재확인 (c), runs 줄 `env_fp`, notes `l_search`, `layer0_start`·`sweep_front` 모듈 전역 호출 계약 | 126-137 `perf.lut_memo_bound` | `perf` 키를 이 card가 건드리지 않으므로 card A 22개 단언과 겹치지 않음. card B·C도 이 계약 유지(40 §2.4.14 (3) 832·837행) |
| `E/tests/search/test_layer0_center.py` | 41 §5.13 test 둘 | A-T5 | 같은 파일 |
| `E/tests/search/test_find_front.py` | (변경 없음 -- notes 단언을 새로 둘 수 있음) | `perf` 22개 | 겹침 작음 |
| `E/tests/search/test_search_context.py` | (변경 없음) | A-T9~A-T12 | 겹침 없음(서명 불변) |
| `E/_module_map.py`, 레지스트리 §2, `E/search/CONTRACT.md` | 행 추가 | 행 추가 | 병합 순서대로 |
| 기준선 | BP1 변화 | card A J-7: base = card A 직전 master 재측정 | 자동 반영 |
| card C | L-b 반환·`lb_stops`·notes | `search_stop`이 `_exhausted` 대체 | 이어받음(40 §2.4.14 (3) 836행) |

### 1.9 design 보완으로 닫힌 항목 (옛 초안 J-1~J-16 → design 결정)

| 옛 id | design 결정(인용) |
|---|---|
| J-1 공개 이름·규칙 A | 40 §2.4.13 (1) '시점·위치' 행: 파일 하나, 정의 다섯, 진입점 `pin_blas_threads` |
| J-2 재확인 기준 | 40 (1) '재확인' 행: 무상태, 새 OpenBLAS(조회 1)는 `env_fp` 차이 |
| J-3 주입 수단 | 40 (1) 'test 주입·관찰 지점' 행: `loaded_blas_modules` 교체, `show_config`·`sys.platform` 하위 프로세스, 실제 라이브러리 경우 |
| J-4 기록 자리 | 40 (1) '결과 값' 행: 단계 A 보고서·runs 줄, 서명·칸 불변 |
| J-5 L-b 사유 | 40 (5) 'L-b 정지 사유 기록': 반환 형식, 반환 직전 확인, 우선순위, `lb_stops`, notes `l_search`, `perf` 불변 |
| J-6 √ε | 41 §5.13 BP1: 정의식 그 자리 |
| J-7 기록 밖 칸 | 40 (5) '결과 기록에 없는 칸': 하네스 수집, 관찰 지점 `find_front.layer0_start`·`sweep_front`, `SearchContext.cache` |
| J-8 비교기 파일 | 40 (5) '위치': `nfr4_compare.py`·`nfr4_run_dump.py`·`test_nfr4_compare.py` |
| J-9 적용 조건 | 41 §5.13 식: as-built 조건 유지 |
| J-10 9회로 실행 | 40 (5) '실행 하네스와 9회로 test 실행 방식'·'무거운 test 마커'(N-2 정정) |
| J-11 남은 고정 문장 | 40 (1) '쓰지 않는 것'·(7): `test_no_s0_files_written.py:7·101` 지움, `test_s0_layer_9circuits.py:11` 고침 |
| J-12 `_source` | 40 (5) B-1·(7): test 주체가 고침, 승인 대상 아님 |
| J-13 design 정정 | e8b619f에 반영(줄 번호·docstring 위치·`kernel.py` 줄) |
| J-14 base red | 41 §5.13 셋째 test: test 동결 전 auditor 재현, 안 되면 멈춤 |
| J-15 반올림 범위 | 41 §5.13: γ_n = n·ε/(1 − n·ε), 연산 셈 규칙 |
| J-16 풀이기 해 주입 | 41 §5.13: `layer0_center.scipy_minimize` 교체 지점 |

### 1.10 기준선 판정 규칙 (사용자 결정 N-1·N-3, 40 §2.4.13 (5) '기준선 변화 판정 규칙')

- auditor가 base(e8b619f, 바깥 `OPENBLAS_NUM_THREADS=1` -- base는 엔진 고정 없음)·head를 같은 하네스로 재어 값 변화 목록(회로·칸·옛 값·새 값)을 판정 기록에 남긴다. 변화마다 사전 승인 범위와 대조: **범위 안 = 통과, 범위 밖 = 판정 기록에 따로 적고 병합 전 사용자 결정**(통과로 세지 않음).
- 사전 승인 범위: (가) folded_cascode 층 0 `hard_ok` False → True(와 그 원인 시작점 `w_min:M8` c 부호), (나) common_gate_amplifier `EA:s1` best seq 34 → 23·stop `converged` → `slsqp_8`, (다) toy test 단언 중 `E/tests/search/test_layer0_center.py`·`test_find_front.py`·`test_residual_probe.py`·`E/tests/convergence/test_converge_point.py`, (라, N-3) 두 회로에서 (가)·(나)와 같은 원인으로 따라 바뀌는 칸(같은 풀이·같은 회로의 θ·목적값·평가 수·front 점·S3 줄 등) -- 칸마다 '같은 원인' 근거를 판정 기록에.
- 범위 밖(사용자 보고): `u17_1b_s0_baseline.json` 값 변화, 다른 회로 변화, 두 회로의 다른 원인 변화, 다른 test 파일(`test_eps_sweep.py`·`test_slsqp_outer.py`·`test_search_context.py` 등) 단언 변화.
- 판정 대상 아님(따로 표시): `run_id`·S3 줄 `code_fp`.
- 승인 불필요(기록만): xfail 제거·범위 확장(기준 강화), 1.6 형식 변경, `_source` 설명 문자열. 옛 측정 파일(`wt/_scratch_xrun_audit/…`, `wt/_nfr4_design_scratch/all_variant_a2.json`)은 기준선으로 쓰지 않음.

### 1.11 남은 판단 필요

| id | 내용 | 근거 |
|---|---|---|
| R-1 | (보고만) 무상태 재확인으로 '새 OpenBLAS 모듈(조회 1) → `RuntimeError`'가 '`env_fp` 차이로 드러남'으로 바뀐 것은 design이 '옛 design 문장과 다름 -- 보고 대상'이라 적었다(40:676). 사용자 보고가 끝났는지 확인 필요 | 결정 기록(user_decisions.md N-1~N-3)에 J-2 언급 없음 |
| R-2 | 마커 선례와의 차이: 기존 `structure/conftest.py:46-48`은 `-m`이 있으면 제외를 끄지만 새 `slow`는 `-m`과 무관하게 `--run-slow`로만 가른다(design 결정). `-m structure_test_mapping`을 줄 때 `--run-slow` 없이는 slow가 빠지는 것이 의도인지 -- design 문장대로면 의도. 확인만 | 40:743 |

그 밖에 card 작성 중 design이 정하지 않은 as-built 결정 필요 자리는 찾지 못했다.

### 1.12 원래 취지와 다른 판단

| # | 내용 | 상태 |
|---|---|---|
| D-1 | 재사용 경로·캐시 키 무변경, 새 이탈 없음 | -- |
| D-2 | 재확인이 같은 실행 안에서 열거를 여러 번 한다 -- '그 사이 변경 확인'이 목적이라 재사용 대상 아님(design 결정) | 보고만 |

---

## 2. 공통 브리핑 (이 card의 code·test·audit agent 필독)

base = master `e8b619f`(계획 v6.11, design 40·41·42 v1.11 + XRUN-F1 card C design + NFR-4 card 2 design 보완). design: `docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md` §1.2 EP-9·§2.4.13 (1)~(8)·§2.4.14 (3)의 NFR-4 card 2 관찰 지점 문장·§10.4, `…41-gain-budget.design.md` §5.13, `…42-gap-checklist.design.md` D-ND1~D-ND4. 계획 NFR-4·IC2·U-77~U-86. 엔진 `skills/analog-gmid-design/gmid_engine/`. 사용자 결정 기록 `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/user_decisions.md`(읽기만, N-1~N-3 포함). card: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/engine/NFR4C2_SPEC_CARD.md`(code·audit), `NFR4C2_INTERFACE_CARD.md`(test는 이것만 -- 소스 열람 금지).

### 절대 규칙
1. **design 그대로 구현한다. as-built 결정 금지.** design에 없는 것을 정해야 하거나 design이 모순·불가능하면 그 자리에서 **멈추고 보고**한다. 범위 축소·대체 금지.
2. **graph 단일 정본(DEC-83)**: graph 밖 허용 저장소는 셋뿐 -- (a) LUT memo(디스크 LUT 파생표 캐시 포함, U-87), (b) S3 기록(출력)과 그 실행 안 메모리 캐시, (c) 실행 계수. `env_fp`·`l_search`는 출력 칸. 재확인은 무상태(모듈 수준 상태 없음). 새 dict 캐시·객체 칸·사본·디스크 캐시 금지.
3. **계산값 재사용 = 실행 안에서**: "처음 topology를 실행할 때는 항상 계산하고 그 계산된 값이 나머지 최적화를 진행할 때 재사용". 벗어나는 판단은 멈추고 '원래 취지와 다름'으로 보고.
4. **틀린 구조는 전체 재작성**, 대체한 옛 코드(`lift = u`, test 쪽 스레드 고정 3곳, strict xfail, 병렬 `Popen`)·옛 CONTRACT 문장은 같은 변경에서 삭제. 만든 것은 반드시 배선.
5. **건드리지 않는 것**: XRUN-F1 A·B·C 범위, `build_search_context` 서명·`SearchContext`·`StageAResult`·`SearchFront` 칸·`perf` 키·`archive.py`, 블록 입력 버전 키, LUT 파생표 캐시 키, 판정식 c ≥ 0, 41 §5.13 '준수'·'해당 없음' 자리, `_REL`(공개화 안 함), 2안, NFR4-F1·F2. 관찰 지점 계약 넷(1.4.1)은 이름·호출 방식을 지킨다.
6. **상수 발명 금지**(√ε = 정의식, γ_n = 정의), **회로 이름·소자 이름 코드 금지**.
7. **파일 분할 규칙 A~I·K**: `core/blas_env.py` 진입점 `pin_blas_threads` 하나, numpy·scipy 함수 안 import(core 최하층), 규칙 G(모듈 수준 가변 상태 금지), 규칙 H `core/blas_env.py` ↔ `tests/core/test_blas_env.py`(`tests/integration/`·`tests/` 바로 아래 파일은 예외). `_module_map.py` 등록(리뷰 항목). `tests/structure` 위반 0.
8. **작성자 ≠ 검증자**: code agent는 test·기대값을 쓰지 않는다(옛 test가 깨지면 목록으로 보고). test agent는 피검 코드를 불러 기대값을 만들지 않는다(oracle = design 식·손계산·같은 함수 두 출력 비교·독립 관찰). 비교기 분해능 식은 design (4) 표 독립 구현. 같은 커밋에서 코드와 기준 동시 변경 금지. 기준 약화는 사용자 승인.

### 실행 환경·메모리 제약·git 가드
- python: `/c/Python314/python.exe`(bash `timeout` 래퍼 금지). 실행 위치 `<worktree>/skills/analog-gmid-design`, `python -m pytest -q gmid_engine/tests/<경로> -p no:cacheprovider`. 이 card 뒤 conftest는 스레드를 고정하지 않는다(엔진 import가 고정) -- 바깥 `OPENBLAS_NUM_THREADS` 미지정 셸에서도 같아야 한다.
- **메모리 제약: 무거운 실행은 한 번에 하나, 순차. 병렬 금지**(9회로 실행·전체 suite·slow test를 동시에 돌리지 않는다, 병렬 셸·병렬 pytest·`Popen` 동시 띄우기·pytest-xdist 금지). 전체 suite는 끝에 한 번(판정 agent·병합 직전은 `--run-slow`). 긴 실행은 결과를 파일에(`C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_nfr4c2_<role>/run.txt`, 케이스마다 append).
- git: 항상 `git -C <자기 worktree>`, 스크립트 `set -e`. 다른 worktree·master 금지, reset --hard·다른 브랜치 checkout·push·merge 금지, 커밋은 자기 브랜치에만.
- 커밋 메시지 끝(`--trailer`): `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`, `Claude-Session: https://claude.ai/code/session_012FxFP7YSWEBBCB9rmBQjLL`.
- 임시 파일: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_nfr4c2_<role>/`(자기 것만).

### 최종 보고(한국어) 필수 항목
1. 구현·작성한 design 절과 상태(구현됨/부분/못함 + 사유). 2. 멈춤·보고 항목('원래 취지와 다름' 후보 포함). 3. 지운 옛 코드(파일:줄), 바뀐 배선(호출부 파일:줄), 1.4.5 grep 결과. 4. graph 단일 정본 자기 점검(재확인 무상태 포함). 5. 계산값 재사용 자기 점검(캐시 키 불변). 6. `tests/structure` 결과(H는 base 비교)·관련 test·깨진 옛 test 목록. 7. 커밋 해시.


## 오케스트레이터 판단 (2026-10-15, auditor 판정 0305b8c 뒤)
- J-O1: red의 ValueError 9개(N-T15~N-T18 옛 반환 형식을 새 형식으로 못 풂)는 J-7 선례대로 red로 인정한다 -- 새 계약(반환 형식 변경) 부재가 원인이고 card 이유와 같다.
- J-O2: card A-3 결함 기록 -- N-T19·N-T24~N-T28은 test 쪽 도구(마커 conftest·비교기)를 시험하므로 base에서 green이 정상이다. 다음 card부터 'test 도구 시험은 red 예상 목록에서 뺀다'.
- J-O3: A-1 grep 문구 2건은 수용하지 않고 test 작성자가 고친다(test 쪽 재작업과 함께).
- J-O4: test 쪽 재작업 = nfr4_run_dump.py threads_env를 엔진 import 전에 읽기 + 문구 2건. 재판정 = test_blas_thread_determinism(--run-slow) + 전체 suite 1회.
- 대기(사용자): A-5 범위 밖 기준선 변화 3회로(nmcnr_amplifier·pushpull_follower_buffer·sf_pushpull_output_opamp). design 41 §5.13 (a2) '나머지 7회로 0건' 실측이 틀렸다(원래 취지와 다름으로 보고).


## 보완 card nfr4c2-r1 (2026-10-16 사용자 N-6)
- 범위: blas_environment()가 재확인 때도 _BUILD_PACKAGES(numpy·scipy) 각각의 소유 BLAS 항목이 있는지 확인하고 없으면 RuntimeError('... 의 BLAS 라이브러리를 적재 모듈에서 찾지 못했다'). pin_blas_threads의 같은 검사는 blas_environment로 옮겨 한 곳만 둔다(중복 금지). 공개 서명·반환 형식·칸 불변.
- test: (i) 재확인에서 소유 BLAS가 빠진 가짜 기록 -> blas_environment() RuntimeError (base 8ff81e2에서 red). (ii) 가짜 기록을 쓰는 기존 test는 경로를 numpy·scipy 패키지 폴더(또는 '<패키지>.libs') 아래로 두거나 실제 소유 항목을 함께 넣어 green 유지 -- 단언 약화 금지.
- 판정: red(test만, code 8ff81e2 위) -> 병합본 green, 전체 suite --run-slow 1회. A-4·A-5는 엔진 수치 경로 무변경이므로 재사용(재확인 경로만 바뀜). 판정 기록에 V10 N-5 승인 반영.
