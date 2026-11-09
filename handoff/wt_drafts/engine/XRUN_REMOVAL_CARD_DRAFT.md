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

## 1. spec card

### 1.1 목표 (사용자 의도 원문)

- 사용자 원문(2026-10-15): "계산 재사용은 처음 topology를 실행할 때는 항상 계산하고 그 계산된 값이 나머지 최적화를 진행할 때 재사용되게 한다는 것이 원래 취지였어. 지금 그렇게 구현되어 있는건가?" → 선택지 (가) 현행 유지 / (나) 디스크 S0 스냅샷 제거, 실행 안 재사용만 → **"나로 해"**.
- 사용자 원문(2026-10-15): "U-87은 LUT는 관리복잡도가 없다는 네 판단근거에 따라 유지. 나머지는 기본안대로" → U-87 LUT 파생표 디스크 캐시 유지(취지의 예외로 기록), U-88 code_hash checkout 무관 성질 유지, U-89 S3 실행 사이 재사용 제거, U-90 front 조회는 출력 조회로 유지.
- 이 card의 목표 한 줄: **S0 수준 graph 층은 실행마다 처음부터 계산하고 그 실행 안에서만 재사용한다. 설계 값(graph 필드, S3 평가)은 실행 사이에 재사용하지 않는다. S3 jsonl은 출력으로만 쓴다.**

### 1.2 구현하는 design 절

| design 절 | 내용 | 이 card |
|---|---|---|
| 40 §2.4.3 전체 | S0 수준 층 수명 = 실행, 디스크 없음, 단계 사이 전달은 결과 값, S3 실행 사이 읽기 없음, 이름별 grep 범위 완료 규칙, 삭제·변경 목록, **front 조회 전용 읽기 경로(새 `search/front_entries.py`, 구조 규칙 K)**, test 삭제·변경 목록 | 구현 |
| 40 §2.4.1 | graph 밖 허용 저장소 셋(LUT memo·S3 기록과 색인·실행 계수), 옛 (d) 폐지 | 구현(옛 (d) 코드 삭제) |
| 40 §2.4.5 `failure` 출처 문장, 정보(m8) | 실패 캐시는 그 실행에서 평가한 실패만, 시작할 때 디스크에서 재구성하지 않는다 | 구현(as-built `disk_failures` 삭제. 색인 `S3Index` 신설은 U17 ② 몫이라 하지 않는다) |
| 40 §2.4.9 판정 1, 판정 2 폐지, test 목록 v1.10 삭제 | 실행 안 같은 입력 재계산 0, 두 번째 실행 test 삭제 | 판정 1을 S0 수준 블록 범위에서 확인(아래 1.7), RunCounters·G-10 9회로 test는 U17 ②·③ 몫 |
| 40 §2.4.12 Q2·Q9·Q10·Q11 | Q2 대상 소멸, Q9 유지(U-87), Q10 유지(U-88), Q11 제거(U-89) | Q2·Q11 구현, Q9·Q10은 **건드리지 않음** |
| 40 §11 U17 ② 선행 '실행 사이 재사용 제거 card' | 삭제·변경 목록 전부, 옛 코드·test 같은 변경에서 삭제, LUT 파생표 캐시·`code_hash` 불변, front 조회 유지 | 이 card의 범위 정의 |
| 42 D-GR3 | 제거 항목(DEV → 완료 시 OK) | 확인 행 |
| 42 D-GR1·D-GR11·D-GR12 | 문구(허용 저장소 셋, 허용 모듈 목록에서 codec·registry 빠짐, `perf.s0_snapshot`·두 번째 실행 test 폐지) | 해당 부분만 |

범위 밖(이 card에서 하지 않음): NFR-4(BLAS 고정·BP 규칙·비교기, card 2), `env_fp`, `RunCounters`·`S3Index`·분할 블록(U17 ②), LUT memo `call`·lint 확장(U17 ③), LUT 파생표 디스크 캐시(U-87 유지), `ComputeBlock.code_hash`(U-88 유지), `snapshots/` 인코딩 요구(§2.4.5 'U17 ② 착수 전 정의').

### 1.3 삭제·변경 목록 (2026-10-15 grep 재측정)

design 40 §2.4.3 표를 행마다 다시 grep했다. "design 줄"과 실측이 다르면 실측 열에 적었다.

#### 1.3.1 엔진 소스

| # | 대상 | 위치(실측) | 처리(design) | 비고 |
|---|---|---|---|---|
| S1 | S0 코덱·저장소·손상 처리·U-68 정리 | `E/core/snapshot_codec.py` 1~431(전체, 431줄 실측) | 파일 삭제 | `S0SnapshotStore`(:305), `_CLEANUP_STARTED`(:91), `SNAPSHOT_DIR_ENV`(:65), `KEY_CODE_FP`(:67), `OUTCOME_*`(:73-75) 모두 이 파일 |
| S2 | S0 키 자리 | `E/core/s0_slot.py` 1~36(전체) | 파일 삭제 | |
| S3 | 타입 등록부 | `E/core/type_registry.py`(전체, 63줄) | 파일 삭제 | 소비자 = 코덱뿐(`snapshot_codec.py:59·110·132`) |
| S4 | core 재수출 | `E/core/__init__.py:30-38`(import), `:46`(등록 호출), `__all__` `:65`(`KEY_CODE_FP`), `:73-75`(`OUTCOME_*`), `:83-84`(`S0Slot`·`S0SnapshotStore`), `:102`(`type_registry`) | 삭제 | design은 `:30-37·83·102`, `:38·46` -- 실측 `:65·73-75·84`가 더 있다(같은 `__all__` 항목) |
| S5 | 패키지별 등록 호출 | `E/graph/__init__.py:6·208·216`, `E/metrics/__init__.py:8·174·182`, `E/sizing/__init__.py:8·163·167`, `E/search/__init__.py:8·102·106` | 삭제 | 각 `:208`·`:174`·`:163`·`:102`는 등록 목록 주석(실측 추가). 등록 대상 tuple(`_field_value_type` 순회 원천)이 다른 소비자가 없는지 code 주체가 확인 |
| S6 | 모듈 지도 | `E/_module_map.py:46`(`type_registry.py` 층 0 목록), `:52`(`snapshot_codec.py` 층 목록), `:238·244·247`(세 파일 `ModuleEntry`), 문구 `:242`(engine_code_fp 역할 "S0 수준 스냅샷 키 (iii)"), `:868`(archive "디스크 실패 캐시 원천"), `:916`(search_context "S0 스냅샷 1회 저장"), `:1029`(stage_a "S0 키·스냅샷 읽기") | 삭제·문구 고침 | `:242·868·916·1029`는 design 목록 밖 실측(문구) |
| S7 | 단계 A S0 키·읽기 | `E/pipeline/stage_a.py:199-205`(`_s0_inputs`), `:212-222`(`_s0_sources`), `:264-268`(키 입력·`S0Slot` 생성·`load`·`base`), `:45-46`(import `S0Slot`·`S0SnapshotStore`) | 삭제. `:268`은 `base = GraphSnapshot.empty(S0_WRITERS)` | `_structure_sha`(:207-209)는 `structure.json` 칸·진입 sha 대조가 같이 쓴다 -- 진입 대조(S9)를 지우면 남는 소비자를 code 주체가 grep(남지 않으면 삭제) |
| S8 | 보고서 `s0_snapshot` 칸 | `E/pipeline/stage_a.py:110`(`_stopped`), `:272·279`(정지 경로 `dict(..., s0_snapshot=...)`), `:301`(정상 보고서) | 삭제 | |
| S9 | PDK 선언 경로 인자·진입 sha 대조 | `E/pipeline/stage_a.py:236`(서명), `:241-248`(주석·대조·거부 2종) | 삭제 | 거부 사유 이름은 core에도 살아 있다 → 1.3.5 범위(core 쪽은 남긴다) |
| S10 | `StageAResult.s0` | `E/pipeline/stage_a.py:103`(칸), `:93-94`(docstring), `_finish` `:231-233`(인자 `s0`), 호출 `:272·279·302` | 삭제 | |
| S11 | S0 저장 | `E/search/search_context.py:215`(서명 `s0=None`), `:225-226`(형식 검사), `:228-229`(`save`), `:29`(import `S0Slot`), `:41`(import `STAGE_B_WRITERS`) | 삭제 | |
| S12 | 직렬화 제외 writer 목록 | `E/search/s0_fields.py:35`(`STAGE_B_WRITERS`), 재수출 `E/search/__init__.py:47·130` | 변경 → 실측 결과 엔진 소비자 0(S11 삭제 뒤) → 삭제 | `STAGE_B_WRITES`(:34, :40 소비)는 남는다 |
| S13 | 디스크 실패 기록 읽기 | `E/search/search_context.py:63`(칸), `:137-147`(`_disk_failures`), `:160`(`tmp.disk_failures` 대입), `:234-235`(재구성), 계수 키 `:65`의 `"disk_hits"` | 삭제 | design `:137-149` → 실측 함수 끝 `:147` |
| S14 | 커널 디스크 분기 | `E/search/kernel.py:105`(`disk = ...`), `:108-112`(`if disk` 분기 전체) | 삭제. `:106-107`(원뿔 행 계산) 남김 | |
| S15 | 이전 실행 front 점 시작점 | `E/search/start_points.py:33-42`(`_s3_thetas`), `:47`(후보 추가) | 삭제 | design `:33-47`과 같은 범위 |
| S16 | S3 읽기 API | `E/search/archive.py:58-69`(`load_evals`), `:71-78`(`load_runs`), **`:99-102`(`read_snapshot`)** | 삭제 | 엔진 소비자: `load_*` = S13·S15뿐, `read_snapshot` = `front_query.py:31` 하나(실측). `read_snapshot`의 gzip JSON 읽기는 S18로 옮긴다. `S3Archive`에는 `append_eval`·`append_run`·`write_snapshot`과 `.dir`만 남는다 |
| S17 | 결과 JSON `perf.disk_hits` | 원천 = `search_context.py:65` 계수 키, `find_front.py:127` `perf = dict(sctx.counters)`가 그대로 옮김 | S13과 같이 삭제 | 1.6 |
| S18 | front 조회 스냅샷 읽기 | `E/search/front_query.py:30-31`(`_from_file`이 `archive.read_snapshot(entry["snapshot_ref"])`를 부름), `:3·5`(docstring) | 고침: 같은 파일에 비공개 `_read_snapshot_file(path)`(gzip JSON 읽기)를 두고 `archive.dir / entry["snapshot_ref"]`를 읽는다. `node_across_front(front, node, archive=None)` 서명 불변, `archive` 없으면 `ValueError` 그대로 | 1.5 |
| S19 | 새 파일 `E/search/front_entries.py` | 신규. 진입점 `read_front_entries(run_dir) -> tuple[dict, ...]` 하나 | 신규 | 1.5. 규칙 A(파일당 진입점 1개) 때문에 `front_query.py`와 나눈다 |
| S20 | 재수출 | `E/search/__init__.py:27·190`(`node_across_front`) | 유지 + `read_front_entries` 추가(import·`__all__`) | 1.5 |
| S21 | 모듈 지도 | `E/_module_map.py`(신규 행) `ModuleEntry("search/front_entries.py", "entry", "read_front_entries", "다른 실행의 runs.jsonl front 항목을 읽는 출력 조회 전용 함수(엔진 계산 경로는 부르지 않는다)", ("N3.3", "U-90"))`, search 파일 순서 표(`:145-152` 부근, `front_query.py`는 `:150`)에 `front_entries.py` 추가(자리는 그 표 규칙대로) | 추가 | design 문구 그대로 |
| S22 | 함수 레지스트리 | `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` §2(31행 '개념별 정본') | **code 주체 몫**: `read_front_entries` 행 추가(개념 = 다른 실행 S3 front 항목 조회, 정본 = `search/front_entries.py`). 지운 `S3Archive.read_snapshot`·`load_evals`·`load_runs`가 레지스트리에 있으면 같은 변경에서 지운다 | 함수 레지스트리 원칙(같은 커밋에서 갱신) |
| S23 | 구조 규칙 K | `E/tests/structure/structure_checks.py`(`check_k`), `README.md` 규칙 표(K 행 + 'J 없음' 행), `fixtures/rule_k/{bad,good}/gmid_engine/`, `test_structure_rules.py`·`test_structure_rules_reject_fixtures.py` | 신규 -- 누가 쓰나는 J-6(design은 위치만 정했다. 초안 가정 = `tests/` 안이라 test 주체) | 3.3 |

#### 1.3.2 docstring (design 목록 + 실측 추가)

| 위치 | 처리 | 출처 |
|---|---|---|
| `E/pipeline/stage_a.py:3`(진입점 서명), `:25-34`(S0 영속화 문단·`s0` 칸 설명), `:93`, `:200`, `:213-216`, `:238·240`(TypeError 문구의 'S0 키' 근거) | 고침 | design `:3·28-32·45·93` + 실측 `:25-27·33-34·200·213-216·238·240` |
| `E/search/search_context.py:3`(서명), `:6-7`('같은 S0 의 다음 실행은 디스크 스냅샷 위에서 계산 0'), `:11-12`(저장), `:21-22`(디스크 실패 캐시·`disk_hits`), `:217`(`s0` 인자) | 고침 | design `:11·21-22·29·41` + 실측 `:3·6-7·12·217` |
| `E/search/kernel.py:11`(순서 문장의 '디스크 실패 캐시 적중') | 고침 | 실측 추가 |
| `E/search/start_points.py:5-8`(출처 순서 ②) | 고침 | design `:7` |
| `E/search/archive.py:7-9`('지문이 다른 디렉터리는 읽지 않는다', 디스크 실패 캐시) | 고침 | design `:8-9` |
| `E/search/find_front.py:13`(`disk_hits`) | 고침 | design |
| `E/search/s0_fields.py:9`('직렬화하지 않는다'·`STAGE_B_WRITERS`) | **같은 변경에서 `STAGE_B_WRITERS` 언급 삭제**(이 docstring이 이름을 담고 있어 grep 0 범위 '엔진 전체'에 걸린다) | design 0538dec 목록에 있음 |
| `E/search/__init__.py:4`(공개 흐름 서명 `s0=None`, 'S0 스냅샷') | 고침 | 실측 추가 |
| `E/search/search_domain.py:7`('설정은 S0 키 밖') | 고침 | 실측 추가 |
| `E/graph/s1_build.py:9`(`previous`가 디스크 스냅샷일 수 있다) | 고침 | design |
| `E/graph/s1v_key.py:6`('실행 사이는 S0 키의 엔진 코드 지문') | 고침 | 실측 추가 |
| `E/pipeline/stage_b.py:9`('같은 S0 의 디스크 스냅샷 위에서 계산 0') | 고침 | 실측 추가 |
| `E/core/engine_code_fp.py:8` 주석 | 확인(현재 문장은 블록 코드 해시 설명. 'S0 키' 언급이 있으면 '결과 기록 출처 칸'으로) | design §2.4.3 '엔진 코드 지문' 행 |

#### 1.3.3 CONTRACT

| 위치 | 처리 | 출처 |
|---|---|---|
| `E/core/CONTRACT.md:4-5`(머리 요약의 `S0SnapshotStore.save`·`S0Slot`), `:15`(머리의 '직렬화하지 않는다' 문맥 확인) | 고침 | design `:5` + 실측 `:4·15` |
| `E/core/CONTRACT.md:525-579` §11 전체 | §11.1(`type_registry`)·§11.3(`S0SnapshotStore`) 삭제, §11.2 `engine_code_fp`는 '용도 = S3 줄·`run_id` 출처 칸'(`:544` 소비자 문장 포함)으로 고침 | design |
| `E/pipeline/CONTRACT.md:5`(§1 서명), `:7-10`(U17 ①-b 문단의 S0 키·sources·읽기만), `:14`(U17 ①-a 문단), `:42-46`(§3 `StageAResult` 칸 `s0`, `build_search_context(..., s0=stage_a.s0)`) | 고침 | design `:5·8·14·45` + 실측 `:7·9-10·42·46` |
| `E/search/CONTRACT.md:7-8`(머리의 `s0` 저장·'다음 실행 계산 0'), `:438`(`disk_failures`), `:440`(`counters` 키 `disk_hits`), `:450`(디스크 실패 적중 단계 3), `:474-475`(§3.12 후보의 'S3 runs front 점'), `:621`(불변식 **I-3** '같은 code_fp·S0 면 디스크 실패 적중') | 삭제·고침 | design `:7·438·440·450·473-474` + 실측 `:8·621`(I-3 행은 design 목록에 없다) |
| `E/search/CONTRACT.md:529` §3.18 `S3Archive(root, context_fp, code_fp)` | 서명 변경 없음(design) | |
| `E/search/CONTRACT.md:172`(`S3Archive.read_snapshot(rel)` 계약) | 삭제 | design 0538dec |
| `E/search/CONTRACT.md:206`(파일별 진입점 표) | `front_entries.py` \| `read_front_entries` 행 추가 | design 0538dec |
| `E/search/CONTRACT.md:524-525`(§3.17 `node_across_front`) + 새 절 `read_front_entries` | dict 원소는 `archive.dir`의 스냅샷 파일을 `_read_snapshot_file`로 읽는다(서명 그대로), 새 절에 1.5의 읽기 함수 계약 | design 0538dec |

#### 1.3.4 저장소 파일

| 위치 | 처리 | 비고 |
|---|---|---|
| `.gitignore:38-39`(주석 + `skills/analog-gmid-design/gmid_engine/.s0_snapshot/`) | design: 삭제 | master 5870d80에서도 같은 줄(실측). 위험은 5.3 |
| `E/tests/conftest.py:52-62`(`_S0_ENV`·`_S0_DIR`·`pytest_unconfigure`), import `shutil`(:13)·`tempfile`(:15)의 남은 소비자 | test 주체 몫(삭제) | design `:52-61` → 실측 `:52-62` |

#### 1.3.5 삭제 이름 grep 0 (design 40 §2.4.3 '완료 규칙', 0538dec 확정)

완료 규칙(design 원문 요지): 아래 이름을 **이름마다 정한 범위**에서 단어 단위 grep한 결과가 0이 될 때까지 지운다(history·design의 '옛' 문장 제외).

| 이름 | grep 범위(이 안에서 0) | 범위 밖에 남는 쓰임(지우지 않는다) | 실측 hit(엔진 소스 `.py` / `.md` / tests, 34932a9 = 0538dec 엔진) |
|---|---|---|---|
| `S0SnapshotStore`, `S0Slot`, `snapshot_codec`, `type_registry`, `KEY_CODE_FP`, `OUTCOME_HIT`·`OUTCOME_MISS`·`OUTCOME_CORRUPT`, `SNAPSHOT_DIR_ENV`, `_CLEANUP_STARTED`, `GMID_S0_SNAPSHOT_DIR`, `_disk_failures`, `load_evals`, `load_runs`, `_s3_thetas`, `STAGE_B_WRITERS` | 엔진 전체(`gmid_engine/` 소스·CONTRACT·`tests/`) | 없음 | `S0SnapshotStore` 26/4/11, `S0Slot` 17/4/6, `snapshot_codec` 19/1/9, `type_registry` 25/3/24, `KEY_CODE_FP` 11/2/3, `OUTCOME_HIT` 6/1/9, `OUTCOME_MISS` 5/1/4, `OUTCOME_CORRUPT` 5/1/2, `SNAPSHOT_DIR_ENV` 4/1/0, `_CLEANUP_STARTED` 4/1/7, `GMID_S0_SNAPSHOT_DIR` 2/1/9, `_disk_failures` 2/0/0, `load_evals` 3/0/0, `load_runs` 2/0/0, `_s3_thetas` 2/0/0, `STAGE_B_WRITERS` 6/0/3(`s0_fields.py:9` docstring 포함) |
| `disk_failures`, `disk_hits` | 엔진 전체 | 없음. test 쪽 `tests/search/test_find_front.py:19`(`PERF_KEYS`), `tests/search/test_layer0_center.py:345`도 고친다 | `disk_failures` 5/1/3, `disk_hits` 4/2/6 |
| `s0_snapshot` | 엔진 소스·CONTRACT·`tests/`(아래 픽스처 제외) | `tests/integration/fixtures/u17_1b_s0_baseline.json` `_source` 설명 문자열 -- 기준선 재측정(design §2.4.13 (7), NFR-4 card 몫) 때 새 설명으로 다시 쓴다 | 8/4/29 |
| `pdk_decl_path`, `lut_rule_decl_path` | 엔진 전체 | 없음 | 각 8/3·2/64 |
| `pdk_decl_missing`, `pdk_source_sha256_mismatch` | `E/pipeline/stage_a.py`, `E/pipeline/CONTRACT.md`, `E/tests/pipeline/test_stage_a.py`(`:710` 주석 포함)만 | **남긴다**: `E/core/pdk_decl.py:340·592`, `E/core/CONTRACT.md:317·372·376·420`, `E/tests/core/test_pdk_decl.py:535·583·594·626·754·1120·1128·1410` -- PDK 선언을 읽는 살아 있는 검사(U-68 무관) | 범위 안: `stage_a.py:245·247`, `pipeline/CONTRACT.md`, `test_stage_a.py:710` |

추가로 0538dec design이 지우는 이름(grep 0 표에는 없지만 삭제 대상): `S3Archive.read_snapshot`(S16). 엔진 소스에서 이 속성 참조는 규칙 K-c가 거부한다(1.5).

검사 방법 메모(사실): 같은 형식의 '폐기 이름 부재' AST test가 `E/tests/structure/test_removed_names.py`(`REMOVED_SCOPES = ((이름, 경로 접두 | None), ...)`)에 있다. 다만 이 card의 범위는 CONTRACT(`.md`)와 `tests/`까지 들어가므로 AST 검사만으로는 덮지 못한다. 감사는 `rg -nw`로 이름·범위마다 잰다(4절 A-2). test 쪽 단언은 이름 문자열을 쓰지 않는 양성 형식(키 집합·칸 목록 정확히 같음)으로 써야 범위 안 grep 0과 맞는다(`s0_snapshot`·`disk_hits`·`disk_failures`·`STAGE_B_WRITERS`·경로 인자 이름은 `tests/`도 범위 안).

### 1.4 배선 변경 (design 그대로)

#### 1.4.1 `run_stage_a`

```text
전: run_stage_a(topology_path, spec_path, lut, *, output_dir, pdk_decl, lut_rule_decl, pdk_decl_path, lut_rule_decl_path, supplies_v=None, structure_path=None) -> StageAResult
후: run_stage_a(topology_path, spec_path, lut, *, output_dir, pdk_decl, lut_rule_decl, supplies_v=None, structure_path=None) -> StageAResult
```

- 흐름: 로드 → `structure.json` → `base = GraphSnapshot.empty(S0_WRITERS)` → `build_s1(topology, supplies, previous=base, ...)` → `build_s1v` → `coupling_vars`. 키 만들기·디스크 읽기 없음.
- `StageAResult(exit_code, status, report, report_paths, s1=None, spec=None, code_fp=None)`: `s0` 칸 삭제. `code_fp`(= `engine_code_fp()`, 실행마다 한 번)는 남는다 -- S3 줄·`run_id`의 출처 칸(design §2.4.3 '엔진 코드 지문' 행).
- 보고서(JSON·md): `s0_snapshot` 키 삭제.
- **판단 필요(2.x J-1)**: 경로 인자와 S0 키 입력을 지우면 `pdk_decl`·`lut_rule_decl`은 `run_stage_a` 안에서 형식 검사(:237-240) 말고 읽는 곳이 없다(실측: 그 밖의 쓰임은 `_s0_inputs`·`_s0_sources`·진입 대조뿐). design은 이 두 인자를 남긴다고도 지운다고도 적지 않았다.

#### 1.4.2 `build_search_context`

```text
전: build_search_context(dc_ctx, spec, settings, archive_root, pdk_decl, lut_rule_decl, model_error=(), *, code_fp, s0=None) -> SearchContext
후: build_search_context(dc_ctx, spec, settings, archive_root, pdk_decl, lut_rule_decl, model_error=(), *, code_fp) -> SearchContext
```

- 흐름: 입력 형식 검사 → `_s0_blocks`(S0 수준 블록 차례 호출 -- 단계 A·B가 이미 쓴 블록은 입력 버전이 같아 재사용) → `context_fp` → `archive = None | S3Archive(archive_root, context_fp, code_fp)` → `SearchContext(...)` → `_wire_sweep_memo`. **저장 없음, 디스크 실패 재구성 없음.**
- `pdk_decl`·`lut_rule_decl`은 여기서 실제로 쓰인다(`search_domain`·`junction_field`·`mismatch_field`·`passive_area_decl`·`start_intervals`).

#### 1.4.3 단계 사이 전달 (변경 뒤 모습)

```text
StageAResult.s1 (S0 수준 스냅샷 위 S1Graph)
  -> run_stage_b(stage_a, memo, pdk_decl, *, output_dir, settings, diagnostic=False)   # 서명 불변
  -> StageBResult.s1 -> sizing.build_kernel_context(b.s1, dc_inputs, lut_access)
  -> build_search_context(kctx, spec, settings, archive_root, pdk, rule, *, code_fp=a.code_fp)
```

같은 실행 안에서는 스냅샷 참조만 넘기고, 블록은 입력 버전이 같으면 다시 계산하지 않는다(필드가 곧 캐시). 실행이 끝나면 버린다.

#### 1.4.4 `start_points` (변경 뒤)

- 후보 순서: ① `layer0`(층 0 시작점) → ③ `given`(선언 x0). 옛 ②(S3 이전 실행 front 점, 출처 `"s3"`)는 없다.
- 시작점 id는 후보 순번 그대로 `s1, s2, ...`(as-built 규칙 불변, 후보가 줄면 번호가 당겨진다).

#### 1.4.5 `kernel.evaluate` (변경 뒤)

- 순서: 요청 계수 → 키 → **메모리 캐시**(그 실행에서 평가한 성공·실패, `hits`·`fail_hits`) → 원뿔 행 c ≤ 0이면 `STATUS_OUTSIDE_DOMAIN` → `size_and_seal`. 디스크 실패 단계 없음.

#### 1.4.6 `SearchContext` (변경 뒤)

- 칸: `dc`, `spec`, `settings`, `context_fp`, `code_fp`, `archive`, `cache`, `computed_keys`, `counters`, `eval_times`, `seq`, `eval_budget`, `eval_budget_source`, (as-built 나머지 실행 수명 칸). `disk_failures` 없음.
- `counters` 키 6개: `requests`, `kernel_calls`, `hits`, `fail_hits`, `outside_domain`, `recompute_same_key`.
- `_wire_sweep_memo`의 임시 컨텍스트도 `disk_failures`를 비우지 않는다(칸이 없다).

#### 1.4.7 S3

- `S3Archive(root, context_fp, code_fp)` 서명 불변. 남는 것: `append_eval`, `append_run`, `write_snapshot`과 속성 `.dir`(`read_snapshot`·`load_evals`·`load_runs`는 삭제, 스냅샷 읽기는 `front_query._read_snapshot_file`로 -- 1.5).
- 같은 `context_fp` 폴더를 여러 실행이 쓰면 `evals.jsonl`·`runs.jsonl`에 줄이 계속 붙는다(출력 누적). 엔진은 그 줄을 읽지 않는다.
- `runs.jsonl` 줄의 `"s0"` 키(값 = `context_fp`, `find_front.py:141`)는 S0 스냅샷과 무관한 옛 이름이고 design 삭제 목록에 없다 -- 바꾸지 않는다.

### 1.5 U-90 조회 전용 읽기 경로 (design 40 §2.4.3 'front 조회 전용 읽기 경로', 0538dec 확정)

design 표를 그대로 옮긴다(원래 취지 보호 장치: 다른 실행의 출력이 계산으로 새지 않게 막는다).

| 항목 | 규칙 |
|---|---|
| 파일 나눔(규칙 A) | 읽기 함수는 새 파일 `E/search/front_entries.py`(진입점 `read_front_entries` 하나). `front_query.py`는 지금처럼 `node_across_front` 하나 |
| 읽기 함수 | `read_front_entries(run_dir) -> tuple[dict, ...]`. `run_dir` = `<archive_root>/<context_fp>`(= `S3Archive.dir`). `runs.jsonl`을 줄 순서대로 읽어 각 줄의 `front`·`pending_front` 항목을 원래 dict 그대로 돌려주고, 항목마다 그 줄의 `run_id`·`code_fp`를 더한다. **거르지 않는다**(조회 결과를 보는 쪽이 판단). 파일이 없으면 `()`. 엔진 소스(`tests/` 제외)에서 `runs.jsonl`을 읽는 곳은 이 함수 하나(기계 강제 없음, 리뷰 확인 항목) |
| 스냅샷 파일 읽기 | `S3Archive.read_snapshot` 삭제. 그 읽기는 `E/search/front_query.py`의 비공개 `_read_snapshot_file(path)`(gzip JSON)로 옮긴다 |
| `node_across_front` 서명 | **불변**: `node_across_front(front, node, archive=None) -> tuple[NodeRow]`. 파일 항목(dict)은 `archive.dir / entry["snapshot_ref"]`를 `_read_snapshot_file`로 읽는다. `archive`가 없으면 `ValueError`. 파일 front 항목은 조회하는 쪽이 `read_front_entries(archive.dir)`로 얻는다(지금은 test) |
| 재수출 | `E/search/__init__.py:27·190`의 `node_across_front` 유지, `read_front_entries` 추가 |
| 부를 수 있는 곳 | 엔진 안에서는 **없다**. 이름을 가지는 곳은 정의(`search/front_query.py`, `search/front_entries.py`)와 재수출(`search/__init__.py`)뿐. 호출자는 test(`tests/search/test_front_query.py`, 새 `tests/search/test_front_entries.py`). `E/report/` 호출이 필요해지면 design 변경이 먼저. `E/pipeline/` 전부 금지 |
| 검사(규칙 K) | 엔진 소스(`tests/` 제외) 전체 AST, 허용 파일(`search/front_query.py`, `search/front_entries.py`, `search/__init__.py`) 밖에서 거부: **(K-a)** 이름 `node_across_front`·`read_front_entries` 참조(import 별칭, `ast.Name`, `ast.Attribute.attr`) **(K-b)** 모듈 `front_query`·`front_entries` import(상대·절대) **(K-c)** `attr`이 `read_snapshot`·`_read_snapshot_file`인 모든 `ast.Attribute`(호출 아닌 참조 포함)와 이름 `_read_snapshot_file`. 규칙 C 층 순서상 `core`~`metrics`는 이미 `search`를 import 못 한다 -- K는 `search` 안 다른 모듈과 `layout`·`convergence`·`report`·`pipeline`을 잡는다 |
| 결과의 쓰임 | graph 필드·시작점·실패 캐시·S3 메모리 색인에 넣지 않는다(K가 엔진 안 호출을 막아 구조로 보장) |
| 모듈 지도·test 1:1 | `_module_map.py`에 `search/front_entries.py` 행(S21), 규칙 H에 맞춰 `tests/search/test_front_entries.py` |

as-built 실측(0538dec = 34932a9 엔진): `front_query.py`(58줄) 진입점 `:49`, 파일 분기 `_from_file` `:30-46`(`archive.read_snapshot` `:31`), 엔진 안 import는 `search/__init__.py:27` 하나, `read_snapshot` 호출은 `front_query.py:31` 하나, report 패키지 소비자 0. 지금 엔진 트리에서 K에 걸리는 곳은 0이어야 한다(재수출은 허용 파일) -- `read_snapshot` 삭제·`_read_snapshot_file` 이동 뒤 기준.

### 1.6 결과 JSON 형식 변경

| 출력 | 바뀌는 것 | 원천 |
|---|---|---|
| `find_front` 결과 `SearchFront.perf`, `runs.jsonl` 줄의 `perf` | 키 `disk_hits` 삭제 | `search_context.py:65` → `find_front.py:127` |
| 단계 A 보고서 JSON(`<circuit>` 보고서 파일)·`StageAResult.report` | 키 `s0_snapshot` 삭제(정상·정지 경로 모두) | `stage_a.py:110·272·279·301` |
| `StageAResult` | 칸 `s0` 삭제 | `stage_a.py:103` |
| `runs.jsonl` 줄의 `starts`(시작점 기록) | `"source": "s3"` 항목이 생기지 않는다 | `start_points.py:47` |
| `SearchContext.counters` | `disk_hits` 삭제 | 같은 원천 |
| 공개 API(출력 형식은 아니지만 함께 적음) | `S3Archive.read_snapshot` 삭제, `gmid_engine.search.read_front_entries` 추가 | 1.5 |

그 밖의 칸(`code_fp`, `run_id`, `s0`(=`context_fp`), `schema_fp`)은 그대로다. 계획만 있던 `perf.s0_snapshot`과 design만 있던 `regenerated_from_prior_run`은 as-built에 없다(grep 0).

### 1.7 완료 조건

1. 1.3.1 S1~S23, 1.3.2, 1.3.3, 1.3.4의 처리가 모두 반영됐다(옛 코드는 같은 변경에서 삭제).
2. 삭제 이름 grep 0: 1.3.5 표의 이름마다 그 범위 안 단어 단위 grep = 0, 범위 밖 남는 쓰임(`core/pdk_decl.py:340·592` 등)은 그대로 있다.
3. 어떤 실행도 S0 수준 층을 디스크에 쓰거나 읽지 않는다(interface card C2).
4. 같은 입력으로 반복 실행하면 실행마다 S0 수준 블록을 계산한다(각 S0 writer 블록 `computes` = 1), 같은 BLAS 설정이면 출력이 비트 같다(C3).
5. 실행 안 G-10(판정 1의 S0 범위): 단계 A → B → 탐색 컨텍스트 사슬에서 S0 writer 블록마다 `computes` = 1, `recomputes_same_input` = 0. 탐색에서 `recompute_same_key` = 0(C4).
6. S3에 이전 내용이 있든 없든 탐색 결과가 같다(C5).
7. U-90: `read_front_entries`·`_read_snapshot_file`·`node_across_front`(서명 불변)가 1.5대로 있고, `S3Archive.read_snapshot`이 없으며, 구조 규칙 K가 엔진 트리에서 위반 0·`rule_k` 위반 픽스처(K-a·K-b·K-c 각 하나 이상)를 기대 목록과 정확히 같게 거부한다. 함수 레지스트리 §2에 `read_front_entries` 행(S22).
8. LUT 파생표 디스크 캐시(`E/lut/table_cache.py`, `GMID_LUT_TABLE_CACHE_DIR`, test 쪽 `lut_table_cache_tests`)와 `ComputeBlock.code_hash`의 diff = 0줄(U-87·U-88).
9. 전체 suite(`not slow` 및 이 card가 바꾼 slow test) 통과, `tests/structure` 위반 0.
10. 공통 완료 조건(design 40 §11): graph 단일 정본 확인 (a)~(d)와 계산값 재사용 확인 (a)~(d), 숫자와 함께 보고(`graph_canon_check`·`reuse_check`). 이 card에서 graph 밖 저장소는 줄기만 한다(옛 (d) 삭제).
11. design ↔ 구현 gap 분석(bkit gap-detector, 일치율 90% 이상), 42 D-GR3 OK.

### 1.8 착수 전 판단 필요 (design이 정하지 않은 것 -- 이 초안은 정하지 않는다)

| id | 질문 | 실측 근거 | 선택지(정하지 않음) |
|---|---|---|---|
| J-1 | `run_stage_a`의 `pdk_decl`·`lut_rule_decl` 키워드 필수 인자를 남기나 | 경로 인자·S0 키를 지우면 두 값은 형식 검사(:237-240) 말고 읽는 곳이 없다. TypeError 문구의 근거도 'S0 키의 PDK 선언 해시'다. 남기면 '만들면 배선' 원칙상 안 쓰는 인자, 지우면 design 1.4.1 서명과 pipeline CONTRACT §1이 더 바뀐다 | (가) 남김(서명 문구만 고침) (나) 지움 |
| J-2 | 실행 안 G-10 판정 범위 | 계획 NFR-2 합격 기준은 '같은 실행 안 같은 입력 재계산 0'. as-built `_wire_sweep_memo`(`search_context.py:150-167`)는 임시 컨텍스트에서 첫 평가를 돌리고 빈 캐시로 버린다 → 본 탐색이 같은 θ를 다시 평가하면 블록 `recomputes_same_input`이 늘 수 있다(**측정하지 않았다**). 이것은 실행 사이 재사용과 무관한 기존 동작이고 `sweep_memo` 삭제는 U17 ③ 몫(§2.4.10) | (가) 이 card의 G-10 판정은 S0 writer 블록 + `recompute_same_key`만, `perf.block_recomputes_same_input`은 보고만 (나) 탐색 블록 계수까지 0 요구(그러면 ③ 일부를 당겨야 할 수 있다) |
| J-3 | `.gitignore:38-39` 삭제 시점 | 지우면 디스크에 남은 `.s0_snapshot/` 폴더(5.2: 6곳)가 그 worktree의 `git status`에 미추적으로 뜬다 | (가) 이 card에서 삭제(design) + 남은 폴더 정리 승인 요청 (나) 폴더 정리 승인 뒤 삭제 |
| J-4 | `integration/test_code_hash_checkout.py`의 '두 checkout `context_fp` 같음' 단언 | design §2.4.12 Q10은 파일 삭제. 그런데 U-88로 checkout 무관 성질은 유지되고, `context_fp`는 S3 폴더 이름이라 여전히 출력에 의미가 있다. 단위 test(`core/test_compute_block.py` 경로 무관)는 남는다 | (가) design대로 파일 삭제 (나) S0 적중 단언만 지우고 `context_fp` 같음은 남김(design 정정 필요) |
| J-6 | 구조 규칙 K 검사기(`tests/structure/structure_checks.py` `check_k`)와 그 픽스처·README 행을 누가 쓰나 | design은 위치만 정했다(§2.4.3 '검사' 행). 검사기는 `tests/` 안이지만 '엔진이 지켜야 할 규칙의 구현'이기도 하다. 선례: U17 ③ 범위표는 `structure_checks.py` 확장을 단위 범위에 넣었고, `tests/structure/test_removed_names.py`(U17 ①) 머리는 작성 주체를 적지 않았다 | (가) test 주체(검사기 + 픽스처 + 기대 위반 목록 전부) (나) code 주체가 `check_k`, test 주체가 픽스처·기대 목록(작성자≠검증자 분리) |

### 1.9 원래 취지와 다른 판단 (사용자 규칙 2026-10-15)

취지 문장: "처음 topology를 실행할 때는 항상 계산하고 그 계산된 값이 나머지 최적화를 진행할 때 재사용".

| # | 내용 | 상태 |
|---|---|---|
| D-1 | LUT 파생표 디스크 캐시는 실행 사이에 유지한다(U-87) | **사용자 승인된 예외**(2026-10-15 "U-87은 … 유지"). 이 card는 건드리지 않는다. 새 판단 아님 |
| D-2 | front 조회 `node_across_front`·`read_front_entries`가 다른 실행의 출력(`runs.jsonl` front 항목·`snapshots/`)을 읽는다(U-90) | 사용자 결정(기본안 채택). 출력 조회이고, 규칙 K가 엔진 안 호출을 구조로 막는다(design '원래 취지 보호 장치'). 새 판단 아님 |
| D-3 | (기존 동작, 이 card 범위 밖) `_wire_sweep_memo`가 첫 평가를 임시 컨텍스트에서 계산하고 버린다 | 실행 **안** 재사용 취지('그 계산된 값이 나머지 최적화에서 재사용')와 어긋날 **수 있다**. 측정하지 않았다. J-2로 판단 요청, 이 card는 바꾸지 않는다 |
| D-4 | design §2.4.3 '실행 시간 영향': 나중에 test가 느려지면 pytest 세션 fixture가 메모리에서 S0를 한 번 계산해 여러 test에 나눠 준다 | 프로세스 안이지만 'test 하나 = 실행 하나'로 보면 실행 사이 재사용에 가깝다. **이 card는 만들지 않는다.** 만들게 되면 그때 따로 보고 |

이 card 자체에는 위 밖의 새 이탈이 없다.

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

## 5. 위험

### 5.1 깨질 낡은 test (design 목록 밖 실측)

- `tests/search/test_layer0_center.py` 3개 test: 디스크 실패 주입(`write_failures` → `evals.jsonl`)으로 층 0 첫 시험·bisection 수리를 몰아간다. 주입 수단이 없어진다. 대체 주입 방법은 test 주체가 정하고, 엔진에 test용 주입 진입을 새로 만들지 않는다(필요하면 멈추고 보고).
- `tests/integration/test_s0_layer_9circuits.py` 5개 test가 디스크 S0 파일을 읽는다(3.2). design 목록은 `:326`과 폴더 조작만 적었다.
- `tests/search/test_find_front.py:19`, `test_search_context.py:21`, `test_s0_fields.py:51`, `test_kernel.py:72`: 키·이름 목록 단언.
- master 5870d80은 34932a9 이후 test 7개가 바뀌었으므로 design 줄 번호(34932a9 기준)는 그대로 쓰면 안 된다(이 초안은 master로 다시 쟀다).

### 5.2 디스크에 남은 S0 폴더 (사용자 파일 -- 지우지 않고 목록만)

| 위치 | 파일 수 | 크기 |
|---|---|---|
| `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/gmid_engine/.s0_snapshot/` (메인 checkout) | 2 | 24K |
| `wt/heldout-c-r2r/.../gmid_engine/.s0_snapshot/` | 6 | 76K |
| `wt/heldout-d-cnr/.../gmid_engine/.s0_snapshot/` | 1 | 20K |
| `wt/heldout-d-cnr-res/.../gmid_engine/.s0_snapshot/` | 1 | 16K |
| `wt/u17-1a-codec/.../gmid_engine/.s0_snapshot/` | 3 | 84K |
| `wt/u17-1a-integ/.../gmid_engine/.s0_snapshot/` | 226 | 1.4M |
| `C:/Users/HSLEE/AppData/Local/Temp/gmid_s0_tests_*` (test 세션 임시 폴더, 비정상 종료로 남음) | 23개 폴더, 모두 비어 있음 | 0 |

- 이 card 병합 뒤 이 파일들을 읽는 코드는 없다(무해, 공간만). 정리 여부는 사용자 승인 사항이다(삭제 = 사용자 파일).
- 오케스트레이터 기본안 후보(결정 아님): 병합 뒤 한 번 목록을 보여 드리고 승인받아 지운다. `.gitignore` 줄을 먼저 지우면(J-3) 위 worktree들의 `git status`에 미추적 폴더로 나타난다.
- 측정 범위: `chip-design-skills`, `wt/*`(깊이 7까지 `find`), 사용자 TEMP. 다른 위치(다른 드라이브, scratch 폴더 깊은 곳)는 재지 않았다.

### 5.3 `.gitignore`

- 대상: `.gitignore:38`(주석)·`:39`(`skills/analog-gmid-design/gmid_engine/.s0_snapshot/`). master 5870d80에서도 같은 줄(34932a9 이후 추가분은 파일 끝 `pages/`·`images/` 줄).
- 위험: 지우면 5.2의 폴더가 미추적으로 보이고, 누군가 `git add -A`하면 S0 파일이 커밋된다. J-3으로 순서를 정한다.
- `lut_table_cache` 쪽 무시 줄은 건드리지 않는다(U-87).

### 5.4 그 밖

- 실행 시간: 같은 회로를 다시 돌리면 S0를 다시 계산한다(design H4 실측 9회로 합 402.8 s 증가). test 세션은 S0 적중에 기대던 test가 두 개뿐이라 영향이 작다(design 판단). 다만 3.2의 `test_s0_layer_9circuits.py` 재작성본이 XR-1처럼 회로마다 두 번 돌리면 그 파일 시간은 늘어난다.
- `_wire_sweep_memo`(J-2): 실행 안 G-10을 탐색 블록까지 넓혀 판정하면 기존 동작 때문에 실패할 수 있다(측정하지 않음).
- NFR-4 card 2와의 순서: §11은 '이 card가 NFR-4 card보다 먼저 또는 같은 변경'. card 2 초안(`NFR4_BLAS_CARD_DRAFT.md`)의 S0 키 (iv)·Q-N1·Q-N5·Q-N8 부분은 이 card로 대상이 사라진다. card 2가 `test_blas_thread_determinism.py`를 같은 시기에 고치면 충돌한다(이 card는 경로 인자·S0 환경 변수 줄만).

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


## 오케스트레이터 판단 (2026-10-15, 원칙으로 확정)
- J-4: design 대로 test_code_hash_checkout.py 삭제. checkout 무관 성질(U-88)은 tests/core/test_compute_block.py:568(test_code_hash_same_source_two_checkout_paths)·:581·:614 단위 test 가 계속 덮는다. 두 checkout context_fp 같음은 code_hash 경로 무관 + S0 디스크 없음에서 따라오는 성질이라 별도 통합 단언 불필요.
- J-6: 구조 규칙 K 검사기(check_k)·픽스처·기대 목록 모두 test 작성 주체. 근거: tests/structure 는 판정 기준이고 작성자=검증자 분리 원칙(code 작성 주체가 자기 코드를 거르는 검사기를 쓰지 않는다).
- J-1·J-3·J-2 는 사용자 결정 대기(J-1 = design 밖 API 삭제, J-3 = 사용자 디스크 폴더 삭제, J-2 = 원래 취지와 다를 수 있는 기존 동작).
