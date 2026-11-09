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
