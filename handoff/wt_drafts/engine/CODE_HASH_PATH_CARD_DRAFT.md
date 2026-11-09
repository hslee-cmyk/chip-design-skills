# code_hash 경로 의존 수정 card 초안 (사용자 결정 10)

- 작성: 2026-10-14. 읽기 전용 실측과 초안만 담았다. 엔진 코드와 저장소는 고치지 않았다.
- 기준 저장소: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/u17-1b-integ2`, HEAD `bcf070c`. 측정 뒤 `git status --short`는 비어 있었다(저장소에 쓴 것 없음).
- 실험 위치: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_codehash_scratch/`. 스크립트는 `toy.py`, `real.py`, `hook.py`, `fpof.py`, `unwrap.py`, `cands.py`, `cmp.py`이고, 결과는 `toy_result.txt`, `cmp_result.txt`, `seed_result.txt`, `fpof_result.txt`, `unwrap_result.txt`, `consts_314.txt`, `r_*.json`, `h_*.json`, `f_*.json`에 있다.
- 실행 환경: Python 3.14.2 (`C:\Python314\python.exe`). 모든 실행에 `-B`를 붙여 `.pyc`를 쓰지 않았다.
- checkout 복제: `gmid_engine`에서 `tests/`와 `__pycache__`를 뺀 사본을 두 곳에 두었다. c1은 `_codehash_scratch/c1/...`이고, c2는 경로가 더 긴 `_codehash_scratch/c2_a_much_longer_checkout_name/x/...`이다. 원본 worktree(wt)도 함께 비교했다.
- 사용자 결정 원문: `wt/_drafts/user_decisions.md`의 "2026-10-14 결정 10" 항목이다. 원문은 다음과 같다. "core code_hash(marshal(fn.__code__))의 co_filename 경로 의존을 U17 2 착수 전에 수정(코드 내용만 지문에). 순서: U17 1-b 병합 뒤 별도 card(design 정정 v1.9.2 '미결' 문구를 결정으로 갱신 + code/test/audit), 2의 RunCounters·G-10 test 전에 끝냄."
- 독립 판정 근거: `wt/_audit_u17_1b_r2/audit_report.md` 3절 표 56~57행과 61행, 원자료 `results/xcheckout_fp_compare.txt`. 다른 checkout에서 실행하면 8/8 회로 모두 hit인데도 S0 블록은 31/31을 다시 계산하고 context_fp가 달라진다. code_hash에서 co_filename을 재귀적으로 비운 측정에서는 계산 0이고 context_fp가 같다.

---

## 1. `code_hash`를 만드는 곳과 쓰는 곳 (사실, grep 결과)

경로 접두 `E/` = `skills/analog-gmid-design/gmid_engine/`.

### 1.1 정의

| 위치 | 내용 |
|---|---|
| `E/core/compute_block.py:22` | `import marshal` |
| `E/core/compute_block.py:65` | `self.code_hash = hashlib.sha256(marshal.dumps(fn.__code__)).hexdigest()`. 엔진 안에서 이 값을 만드는 유일한 곳이다. 데코레이트 시점(모듈 import 중)에 한 번 계산된다. |

### 1.2 소비 (지문 사슬)

| 위치 | 소비 방식 |
|---|---|
| `E/core/compute_block.py:75` | `input_version = fp_of((self.name, self.code_hash, projection.fp))` |
| `E/core/compute_block.py:77` | `snapshot.block_version(self.name) == input_version`이면 재사용한다. 다르면 계산한다. |
| `E/core/compute_block.py:90` | `snapshot.write(self.name, input_version, result)`. 이 값이 `block_versions[writer]`와 각 필드의 `input_version`이 된다. |
| `E/core/graph_snapshot.py:39-41, 149-151` | `block_versions`를 보관한다. 스냅샷 `fp`에는 block_versions를 넣지 않는다(41행). 그래서 판정에서 "스냅샷 fp는 같은데 재계산 31/31"이 나왔다. |
| `E/core/snapshot_codec.py:20, 160, 174, 196` | S0 스냅샷 파일에 `block_versions{writer: 입력 버전}`을 직렬화하고 다시 읽는다. 다른 checkout이 같은 S0 파일을 hit로 읽어도, 이 값과 그 checkout에서 다시 잰 입력 버전이 달라 재계산이 일어난다. |
| `E/sizing/seal_versions.py:21` | 봉인 4는 `fp_of((block.name, block.code_hash, projection.fp)) != recorded`로 검사한다. |
| `E/search/search_context.py:48, 231` | `context_fp = fp_of((tuple((w, base.block_version(w)) for w in _CONTEXT_WRITERS), dc.lut, dc.inputs))`. code_hash가 block_version을 거쳐 context_fp로 들어간다. |
| `E/search/search_context.py:232, 235, 137-147` | `S3Archive(archive_root, context_fp, code_fp)`의 폴더 이름과 `_disk_failures` 키를 정한다. |
| `E/search/archive.py:42-43` | `self.dir = Path(root) / context_fp` |
| `E/search/eval_key.py:13-22`, `E/search/kernel.py:98` | 평가 키 `EvalKey(context_fp, ...)`의 첫 칸이다. |
| `E/search/find_front.py:138, 141` | `run_id = fp_of((sctx.context_fp, ...))`이고, runs 기록의 `"s0"` 칸이다. |

참고로 `E/core/engine_code_fp.py:23-37`(엔진 코드 지문)은 code_hash와 별개다. 이 지문은 engine_root 기준 posix 상대 경로와 파일 바이트 sha로 만들기 때문에 이미 checkout과 무관하다. 근거는 `E/tests/core/test_engine_code_fp.py:70` `test_engine_code_fp_is_independent_of_checkout_location`이다. S0 스냅샷 파일 키(`snapshot_codec.py:344`)와 S3 `code_fp`는 이 값을 쓴다.

### 1.3 관련 test (현재)

| 위치 | 검사 내용 |
|---|---|
| `E/tests/core/test_compute_block.py:68-69` | `code_hash`가 64자 소문자 hex인지만 본다. |
| `E/tests/core/test_compute_block.py:116` | `v = fp_of((block.name, block.code_hash, Projection.from_snapshot(s0, READS).fp))`와 input_version이 같은지 본다. |
| `E/tests/sizing/test_seal_versions.py:2, 15` | 봉인 4 식을 같은 방식으로 재구성한다. |
| 없음 | code_hash가 checkout과 무관한지, 프로세스 사이에서 결정론적인지, 코드가 바뀌면 값이 바뀌는지를 보는 test가 없다. |

### 1.4 문서·레지스트리에 나오는 곳

- `E/core/CONTRACT.md:237`: §6.1 선언. 속성 목록에 "`code_hash`(64자 hex)"가 있고 정의는 없다.
- `E/core/CONTRACT.md:245`: §6.2 "입력 버전 `v = fp_of((name, code_hash, projection.fp))`"
- `E/sizing/CONTRACT.md:112, 574` (봉인 4), `E/metrics/CONTRACT.md:506`: "코드 해시" 식을 인용한다. 식 자체는 바뀌지 않으므로 문구를 고칠 필요는 없다.
- `E/_module_map.py:223-225`: `core/compute_block.py` 항목. 역할 문구는 바뀌지 않는다.
- design 40(`docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md`)의 12, 218, 226, 242, 463행. 자세한 내용은 4절에 적었다.

---

## 2. marshal된 code 객체에서 경로가 들어가는 칸 (실측)

### 2.1 장난감 실험 (`toy.py`, 결과 `toy_result.txt`)

실험 대상 함수 `blk`의 몸체에는 lambda, 내부 함수 `inner`(안에 list comprehension 포함), generator expression, dict comprehension, frozenset 상수, docstring이 있다. 같은 바이트의 소스 파일을 `pA/`와 `pB_much_longer_checkout_path/deeper/` 두 곳에 두고 각각 import했다.

| 측정 | 결과 |
|---|---|
| 중첩 code 객체 | `fn/<lambda>`, `fn/inner`, `fn/<genexpr>` 3개. Python 3.12부터 list/dict comprehension은 인라인되어(PEP 709) 별도 code 객체가 생기지 않는다. |
| marshal 길이 | pA 1079 B, pB 1112 B. 첫 차이는 offset 313이다. |
| marshal 바이트 안 경로 문자열 등장 수 | 1회. 중첩 code 4개가 같은 `co_filename` 문자열 객체를 공유하고, marshal은 두 번째부터 FLAG_REF 역참조로 쓴다. |
| 속성별 차이 (code 객체 4개 전부 비교) | **`co_filename`만** 다르다(최상위·lambda·inner·genexpr 4곳). `co_name`, `co_qualname`, `co_firstlineno`, `co_linetable`, `co_code`, `co_consts`, `co_names`, `co_varnames`, `co_exceptiontable`, `co_flags`, 인자 수, `co_stacksize`는 모두 같다. |
| 최상위 co_filename만 비울 때 | 여전히 다르다. 경로가 1회 남는다(중첩 code의 co_filename). **재귀적으로** 비워야 한다. |
| 재귀적으로 비울 때 | marshal 바이트가 완전히 같다. |

### 2.2 실제 엔진 (`real.py`, 결과 `r_c1.json`·`r_c2.json`·`r_wt.json`, 요약 `cmp_result.txt`)

- 계산 블록 객체는 53개, 파일은 52개다. import 실패와 이름 중복은 없다. grep으로 `@compute_block` 행을 세면 107개가 나오는데, docstring과 주석 속 언급까지 센 값이다.
- 중첩 code가 있는 블록은 41개이고, 중첩 code는 모두 223개다.
- 모든 블록에서 marshal 바이트에 checkout 폴더 문자열이 1회씩 들어 있다.
- 현행 code_hash가 세 checkout(c1, c2, wt)에서 같은 블록 수는 **0/53**이다.

### 2.3 별도 발견 1: 현행 marshal 해시는 참조 수에 의존한다 (사실)

`hook.py`로 `ComputeBlock.__init__` 시점(데코레이트 시점)과 import가 끝난 뒤, 같은 프로세스에서 `marshal.dumps(fn.__code__)`를 두 번 쟀다(`h_c1_fwd.json`).

- 53개 중 **5개**의 바이트가 달랐다: `dc_writer_plan`, `metrics_aux`, `passive_area_decl`, `s1_gvgs`, `s1_matching_groups`.
- 달라진 바이트는 `0xa9`와 `0x29`다. `0x29`는 TYPE_SMALL_TUPLE이고 `0x80`은 FLAG_REF 비트다. marshal은 참조 수가 1보다 큰 객체에만 FLAG_REF를 붙인다. 따라서 같은 code 객체라도 그 순간의 참조 수에 따라 바이트가 달라진다.
- 추측: 데코레이트 시점에는 모듈 code 객체가 아직 살아 있어 상수 tuple을 함께 참조한다. import가 끝나면 모듈 code가 해제되어 참조 수가 2에서 1로 떨어진다.
- 저장되는 값(데코레이트 시점 값)은 import 순서를 바꿔도(정방향/역방향 `walk_packages`) 53/53 같았고, `real.py`로 다른 방식으로 import해도 53/53 같았다. 지금까지 같은 경로 재실행에서 hit가 났던 것과 맞는다.
- 그러나 이 값은 "코드 내용"이 아니라 import 중 참조 수 상태의 함수다. 결정 10의 "코드 내용만 지문에"와 맞지 않는 성질이고, marshal을 쓰는 후보(A, C)는 이 성질을 그대로 물려받는다. 이번 측정에서는 A와 C가 데코레이트 시점 값과 나중 값이 53/53 같았다. 추측: 새 `co_consts` tuple이 직접 상수에 참조를 하나 더 붙여서 우연히 안정된 것이고, 보장된 성질은 아니다.

### 2.4 별도 발견 2: 감싼 블록은 실제 몸체가 해시에 들어가지 않는다 (사실)

- `ly_pattern_select`와 `ly_rows`(`E/layout/canonical_naming.py:93`의 `canonical_names()` 데코레이터 공장)는 `functools.wraps`로 감싼 `run` 함수가 블록 fn이다. 실제 몸체 `pattern_select`와 `compose_rows`는 closure(`__wrapped__`)에만 있다.
- 그 결과 두 블록의 현행 code_hash는 서로 같다(53개 중 고유값 52개). 실제 몸체를 고쳐도 code_hash가 바뀌지 않는다. 이 성질은 후보 A, C, D에도 그대로 남는다.
- `__wrapped__` 사슬까지 D로 지문을 만들면 고유값이 53/53이 된다(`unwrap.py`, `unwrap_result.txt`).
- 실행 사이 재사용에서는 엔진 코드 지문(`engine_code_fp`)이 S0 파일 키에 들어가므로, 소스를 고치면 어차피 miss가 된다. 그래서 지금 값이 틀리게 재사용되는 경로는 확인되지 않았다. 다만 "코드가 바뀌면 code_hash가 바뀐다"는 계약은 이 2개 블록에서 거짓이다.
- 이 card의 범위에 넣을지는 5.3절에서 판단을 요청한다.

---

## 3. 수정 후보 비교

후보 정의(scratch `cands.py`, `fpof.py`):

- **A**: 중첩 code까지 재귀적으로 `co_filename`을 `""` 또는 모듈 상대 경로로 `replace`한 뒤 `marshal.dumps`하고 sha256을 잰다. 감사 측정에 쓴 방식과 같다.
- **B**: `inspect.getsource(fn)` 텍스트의 sha256.
- **C**: A에 더해 `co_firstlineno=1`, `co_linetable=b""`로 바꾼 뒤 marshal한다(줄 정보를 뺀 marshal).
- **D**: marshal을 쓰지 않는다. code 객체를 다음 칸들로 재귀 정규화해 정준 바이트로 인코딩한다: `co_argcount`, `co_posonlyargcount`, `co_kwonlyargcount`, `co_flags`, `co_stacksize`, `co_code`, `co_consts`(중첩 code는 재귀), `co_names`, `co_varnames`, `co_freevars`, `co_cellvars`, `co_name`, `co_qualname`, `co_exceptiontable`. `co_filename`, `co_firstlineno`, `co_linetable`은 넣지 않는다. 변형 D-line은 `co_firstlineno`와 `co_linetable`도 넣는다.
- **D-fp_of**: D의 정규화 결과를 core `fp_of`로 지문화한 형태다. 정규화된 code는 frozen dataclass로 감싸서 타입 이름이 인코딩에 들어가게 했다(같은 모양의 일반 tuple 상수와 구분된다).

### 3.1 (a) 다른 경로에서 같은 값이 나오는가

| 후보 | 장난감 pA 대 pB | 엔진 c1·c2·wt (53 블록) | PYTHONHASHSEED 7, 12345, 99 |
|---|---|---|---|
| 현행 | 다름 | **0/53** | -- |
| A (빈 값) | 같음 | 53/53 | 53/53 |
| A (상대 경로) | 같음 | 53/53 | -- |
| B | 같음 | 53/53 | 53/53 |
| C | 같음 | 53/53 | 53/53 |
| D | 같음 | 53/53 | 53/53 |
| D-line | 같음 | 53/53 | 53/53 |
| D-fp_of | -- | c1 대 c2(seed 99) 53/53 | 53/53 |

장난감에서는 PYTHONHASHSEED 1, 2, 3에서도 모든 후보가 같은 값을 냈다. frozenset 상수를 포함한 경우다.

### 3.2 (b) 코드가 바뀌면 값이 바뀌는가 (장난감 기준 변화, `toy_result.txt`. 표의 "바뀜"은 base와 다르다는 뜻)

| 변경 | 실제로 달라진 code 속성 | 현행 | A | B | C | D | D-line |
|---|---|---|---|---|---|---|---|
| 상수 변경 (`1.5` -> `1.25`) | co_consts, co_linetable | 바뀜 | 바뀜 | 바뀜 | 바뀜 | 바뀜 | 바뀜 |
| 중첩 함수 안 상수 (`z + 1` -> `z + 2`) | co_code, co_consts | 바뀜 | 바뀜 | 바뀜 | 바뀜 | 바뀜 | 바뀜 |
| 지역 변수 이름 변경 | co_varnames, co_linetable | 바뀜 | 바뀜 | 바뀜 | 바뀜 | 바뀜 | 바뀜 |
| docstring 변경 | co_consts | 바뀜 | 바뀜 | 바뀜 | 바뀜 | 바뀜 | 바뀜 |
| 함수 위에 줄 추가(줄 위치만 이동) | co_firstlineno | 바뀜 | **바뀜** | 같음 | 같음 | 같음 | **바뀜** |
| 함수 안에 주석 한 줄 추가 | co_firstlineno, co_linetable | 바뀜 | **바뀜** | 바뀜 | 같음 | 같음 | **바뀜** |
| 같은 줄 끝에 주석 추가 | (co_filename 외 없음) | 바뀜 | 같음 | **바뀜** | 같음 | 같음 | 같음 |

장단점은 다음과 같다.

- **줄 정보 포함(A, D-line)**
  - 장점: 보수적이다. 무엇이든 바뀌면 다시 계산한다.
  - 단점: 의미가 같은 편집(위쪽 함수 수정, 주석 줄)에도 입력 버전이 바뀐다.
  - 엔진에서 줄 정보를 값에 쓰는 곳은 없다. `traceback`, `lineno`, `inspect.`를 grep한 결과 엔진(test 제외)에서 0건이다. 따라서 줄 정보는 출력 값에 영향이 없다.
- **줄 정보 제외(C, D)**
  - 장점: "코드 내용만"이라는 결정 원문에 맞는다.
  - 단점: 없음(줄 정보는 traceback 표시에만 쓰인다).
- **실제 효과의 크기 (사실 기반 추론)**
  - 소스 파일 바이트가 하나라도 바뀌면 `engine_code_fp`가 바뀐다. 그러면 S0 파일 키(`snapshot_codec.py:344`)와 S3 기록 필터(`archive.py:8`, code_fp가 같은 줄만)가 miss가 된다.
  - 그래서 실행 사이 재사용 관점에서 줄 민감도의 차이는 지금 구조에서 거의 드러나지 않는다.
  - 고르는 기준은 계약의 뜻("코드 내용만")과 결정론이다.
- **B(소스 텍스트)의 성질**
  - 주석, 공백, 데코레이터 줄 변경에도 바뀐다. 너무 민감하다.
  - 상수를 접은 결과나 Python 판에 따른 바이트코드 차이는 반영하지 않는다.
  - `linecache`와 소스 파일이 있어야 한다. `.pyc`만 있는 배포나 zip import에서는 `OSError`가 난다(추측: 엔진은 소스로 배포되므로 지금은 해당 없음).
  - `functools.wraps`를 따라 `__wrapped__`의 소스를 읽는다. 그래서 2.4절의 두 블록이 우연히 구분된다.
- **공통 한계(모든 후보, 이 card 범위 밖)**
  - 블록 함수가 부르는 헬퍼 함수, 모듈 전역, closure 값, 기본 인자는 code 객체에 없다. 그래서 어느 후보도 이것들을 덮지 않는다.
  - 실행 사이에서는 `engine_code_fp`가 이것을 덮는다(`engine_code_fp.py:7-8` 주석이 이미 이 분담을 적고 있다).
- **Python 판 변경**: `co_code`가 바뀌므로 B를 뺀 모든 후보의 값이 바뀐다. 다시 계산하는 쪽으로 바뀌는 것이므로 안전하다.
- **3.14 상수 타입**: `consts_314.txt`에서 `a[1:3]`, `1j`, `...`가 각각 `slice`, `complex`, `ellipsis` 상수로 `co_consts`에 들어간다.
  - core `fp_of`는 이 세 타입에서 `TypeError`를 낸다(`fingerprint.py`의 "그 밖의 타입은 TypeError").
  - 현재 53개 블록의 상수는 str 384, None 231, tuple 144(안쪽 str 208, tuple 4, bool 1), int 37, bool 20, float 11개다(`fpof_result.txt`). 세 타입은 아직 없다.
  - D-fp_of를 쓴다면 정규화 단계에서 이 세 타입을 명시적으로 인코딩해야 한다. 그렇지 않으면 이런 상수를 쓰는 블록은 데코레이트할 때 거부된다.

### 3.3 (c) 비용 (53 블록 전체 한 번 계산, 7회 반복 중 최솟값, 단위 ms. c1 / c2 / wt)

| 후보 | c1 | c2 | wt |
|---|---|---|---|
| 현행 | 0.77 | 0.73 | 0.60 |
| A 빈 값 | 1.81 | 1.69 | 1.56 |
| A 상대 경로 | 1.80 | 1.68 | 1.56 |
| B 소스 | 53.4 | 53.4 | 50.0 |
| C | 1.76 | 1.90 | 2.32 |
| D (자체 인코더) | 5.67 | 5.69 | 8.60 |
| D-line | 6.31 | 6.39 | 9.27 |
| D-fp_of | 7.41 | 6.16 | -- |

- B는 반복마다 `linecache.clearcache()`로 파일을 다시 읽은 값이다.
- 비교 기준: 엔진 전체 import 시간은 2.20~2.50 s다. D-fp_of는 7.4 ms로 import의 약 0.3%이고, import 때 한 번만 든다. 평가 루프 안에서는 비용이 0이다(code_hash는 속성으로 보관한다).

### 3.4 권고안

**D-fp_of를 권고한다.**

- 정의: code 객체를 재귀 정규화한다. 넣는 칸은 바이트코드, 상수(중첩 code 포함), 이름, 변수 이름, 인자 수, 플래그, 예외표, `co_name`, `co_qualname`이다. 파일 경로, 첫 줄 번호, 줄 표는 뺀다. 이 결과를 core `fp_of`로 지문화한다. 정규화 단계에서는 `slice`, `complex`, `Ellipsis`, `bytes`, `frozenset`을 포함해 Python 3.14 code 상수 타입 전부를 명시적으로 인코딩한다.
- 근거 1, checkout 무관: 엔진 53/53 블록이 세 checkout과 세 해시 시드에서 같은 값을 냈다.
- 근거 2, 결정론: marshal을 쓰지 않으므로 2.3절의 참조 수 의존(현행 5/53)이 구조적으로 없다. A와 C는 이번 측정에서 안정했지만, 그 안정은 우연(추측)에 기대고 있다.
- 근거 3, 결정 원문 "코드 내용만"에 맞는다: 의미가 바뀌는 편집(상수, 중첩 상수, 이름, docstring)은 모두 값을 바꾸고, 줄 위치와 주석만 바뀐 편집은 값을 바꾸지 않는다.
- 근거 4, 단일 정본: 지문 인코더를 새로 만들지 않고 core `fp_of`를 다시 쓴다. 정규화 함수 하나만 추가한다(함수 레지스트리 원칙).
- 근거 5, 비용: import 때 약 7 ms다.
- 차선: 경로 의존만 고치는 최소 변경을 원하면 A(재귀 `co_filename=""`)다. 감사가 이미 실측한 방식이다. 다만 marshal의 참조 수 의존이 남고, 줄 이동에도 반응한다.
- 비권고: B. 주석과 공백에 반응하고, 소스 파일 의존이 있고, 53 ms가 든다.

---

## 4. design 40 v1.9.2 정정 위치와 문장 초안

파일: `docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md` (HEAD bcf070c)

| 행 | 현재 문장(요지) | 바꿀 문장 초안 |
|---|---|---|
| 12 (Status 머리, 끝부분) | "참고 기록(결정 아님): core `ComputeBlock.code_hash`의 `co_filename` 경로 의존은 **미결**(사용자 결정 10 대기, §2.4.3)." | (v1.9.3 머리를 새로 추가하고 v1.9.2 줄은 그대로 둔다.) "v1.9.3 -- 사용자 결정 10(2026-10-14 '10도 권고대로', 원문 `_drafts/user_decisions.md` '결정 10'): §2.4.3 'checkout 무관' 행의 code_hash 미결을 결정으로 갱신. `ComputeBlock.code_hash` = 블록 함수 code 객체의 코드 내용 지문(경로·줄 정보 제외, marshal 미사용). §2.4.9 판정 2의 다른 checkout 단서 삭제. 경위는 history." |
| 226 ('checkout 무관(v1.9.2 결정 7)' 행의 뒤 절반) | "**미결**(참고 기록, 결정 아님): 블록 입력 버전의 코드 해시 `ComputeBlock.code_hash` = sha256(marshal(코드 객체))(`E/core/compute_block.py:65`)가 `co_filename`(절대 경로)을 담아 checkout에 의존한다(... base도 다른 checkout에서 23/23 재계산 ...). 사용자 결정 10 대기" | "**블록 코드 해시**(v1.9.3 결정 10): `ComputeBlock.code_hash`는 블록 함수 code 객체(중첩 code 포함 -- 람다·내부 함수·generator)의 **코드 내용만**의 지문이다. 넣는 것은 바이트코드, 상수, 이름, 변수 이름, 인자 수, 플래그, 예외표, `co_name`·`co_qualname`이다. 파일 경로(`co_filename`), 첫 줄 번호, 줄 표는 넣지 않는다. 직렬화는 marshal이 아니라 core `fp_of`이다(marshal 바이트는 참조 수에 따라 FLAG_REF가 달라진다 -- 실측 53블록 중 5개가 데코레이트 시점과 import 뒤에 달랐다). 그래서 같은 커밋은 checkout 경로와 무관하게 같은 입력 버전과 같은 `context_fp`를 낸다(근거: `wt/_audit_u17_1b_r2/audit_report.md` 3절, co_filename을 비운 측정에서 8/8 계산 0, context_fp 같음). 헬퍼·전역·closure 값은 이 해시가 덮지 않고 (iii) 엔진 코드 지문이 덮는다." (2.4절 `__wrapped__`를 범위에 넣으면 다음을 덧붙인다: "`functools.wraps`로 감싼 블록은 `__wrapped__` 사슬의 code까지 넣는다.") |
| 218 (키 (iii) 설명 중간) | "블록 입력 버전의 코드 해시는 블록 함수 자신의 코드 객체만 덮으므로(`E/core/compute_block.py:65`) 실행 사이 재사용에는 (iii)이 필요하다." | 내용은 그대로 두고 줄 번호 참조만 구현 뒤 실측 행으로 갱신한다(같은 문장 유지, 행 번호는 code card 병합 뒤에 다시 잰다). |
| 463 (§2.4.9 판정 2 끝) | "다른 checkout 사이 재사용은 §2.4.3 'checkout 무관' 행의 코드 해시 미결에 묶인다." | "다른 checkout(같은 커밋)이 같은 S0 폴더를 읽으면 S0 수준 블록의 `computes` = 0이고 `context_fp`가 같다(v1.9.3 결정 10, §2.4.3 'checkout 무관' 행)." |
| 242 (§2.4.4 입력 버전 식) | `fp_of((name, 코드 해시, 그 분할의 투영 지문))` | 바꾸지 않는다. 식은 그대로다. |

history(`docs/01-plan/features/gain-budget-gmid-sizing.history.md`)에 경위 행을 하나 추가한다. 내용은 결정 10 원문, 감사 실측, 이 초안의 측정 수치다. 계획서에는 이력을 넣지 않는다.

### 4.1 영향받는 CONTRACT 문서

| 문서 | 위치 | 변경 |
|---|---|---|
| `E/core/CONTRACT.md` | 237 (§6.1 속성 목록) | `code_hash`(64자 hex) 뒤에 정의 한 문장을 추가한다. 5.1절 I1~I6을 요약해 넣는다. |
| `E/core/CONTRACT.md` | 245 (§6.2) | 식은 그대로 둔다. "같은 커밋이면 checkout 경로와 무관하게 같은 v"를 추가한다. |
| `E/sizing/CONTRACT.md` | 112, 574 | 식 인용뿐이라 변경하지 않는다. 확인만 한다. |
| `E/metrics/CONTRACT.md` | 506 | 식 인용뿐이라 변경하지 않는다. 확인만 한다. |
| `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` | -- | grep 결과 `code_hash`와 `compute_block`이 0건이다. 정규화 함수가 core 내부 비공개면 등록하지 않는다. 공개 이름으로 내보내면 §2 개념표에 "블록 코드 내용 지문" 행 하나를 추가한다. |

---

## 5. interface card 초안 (공개 계약만)

### 5.1 계약: `ComputeBlock.code_hash`

- 형식: 64자 소문자 hex 문자열이다(현행과 같다). 입력 버전 식 `fp_of((name, code_hash, projection.fp))`는 바뀌지 않는다.
- **I1 경로 무관**: 같은 바이트의 소스를 서로 다른 절대 경로(다른 checkout)에서 import하면 같은 값이다. 중첩 code(lambda, 내부 함수, generator expression)를 가진 블록도 같다.
- **I2 결정론**: 같은 함수에 대해 데코레이트 시점에 잰 값과 import가 끝난 뒤 다시 잰 값이 같다. 다른 프로세스, 다른 `PYTHONHASHSEED`, 다른 import 순서에서도 같다.
- **I3 의미 변경 감지**: 다음 중 하나라도 바뀌면 값이 다르다.
  - 바이트코드
  - 상수(중첩 code 안의 상수 포함)
  - 전역·속성 이름
  - 지역 변수 이름
  - 인자 수(위치 전용·키워드 전용 포함)
  - 플래그
  - 예외표
  - docstring
  - 함수 이름과 qualname
  - `-0.0`과 `0.0`, `True`와 `1`도 서로 다른 상수로 구분한다.
- **I4 줄 정보 무시**: 함수 위에 줄을 넣거나, 함수 안에 주석 줄을 넣거나, 줄 끝에 주석을 붙이는 것처럼 줄 위치와 주석만 바뀌면 값이 같다.
- **I5 상수 타입 전 범위**: 해당 Python 판에서 code 상수로 나올 수 있는 모든 타입에 값이 정의된다(Python 3.14 기준 None, Ellipsis, bool, int, float, complex, str, bytes, tuple, frozenset, slice, code). frozenset은 원소 순회 순서와 무관하다. 정의되지 않은 타입을 만나면 데코레이트할 때 `TypeError`를 낸다(fail-closed, 조용한 대체 금지).
- **I6 (선택, 5.3절 결정 필요)**: `functools.wraps`로 감싼 함수는 `__wrapped__` 사슬 끝의 함수 코드까지 지문에 넣는다. 감싸는 함수가 같고 안쪽 함수만 다른 두 블록은 code_hash가 다르다.
- 덮지 않는 것(계약에 명시한다): 블록 함수가 부르는 다른 함수, 모듈 전역 값, closure 셀 값, 기본 인자 값. 실행 사이 재사용에서는 core `engine_code_fp()`가 이것을 덮는다.
- 하류 결과(통합 계약): 같은 커밋, 같은 S0 입력, 같은 S0 폴더라면 checkout 경로가 달라도 `build_search_context(...).context_fp`가 같다. 단계 A가 ok인 회로에서는 S0 수준 블록의 `computes` = 0이다.

### 5.2 필요한 test 목록 (test author는 소스를 보지 않고 이 계약만으로 작성한다)

| id | 위치(제안) | 내용 | 계약 |
|---|---|---|---|
| T1 | `E/tests/core/test_compute_block.py` | 같은 소스 텍스트를 tmp 폴더 두 곳(경로 길이가 다르게)에 쓰고 `importlib.util.spec_from_file_location`으로 각각 import한다. 같은 이름으로 데코레이트한 두 블록의 code_hash가 같은지 본다. 블록 몸체에는 lambda, 내부 함수, generator expression을 넣는다. | I1 |
| T2 | 같은 파일 | red 확인: T1을 현행 코드에서 돌리면 실패해야 한다(audit이 base에서 재현한다). | I1 |
| T3 | 같은 파일 | 데코레이트 직후 code_hash와, 모듈 로드가 끝난 뒤 같은 함수로 다시 만든 블록의 code_hash가 같은지 본다. 모듈 수준 상수 tuple을 함수 안에서 함께 쓰는 소스를 쓴다(2.3절 재현 조건). | I2 |
| T4 | 같은 파일 | 하위 프로세스 두 개(`PYTHONHASHSEED` 다르게, import 순서 다르게)에서 같은 소스로 잰 code_hash가 같은지 본다. frozenset 상수를 포함한다. | I2, I5 |
| T5 | 같은 파일 (parametrize) | 상수, 중첩 상수, 지역 변수 이름, docstring, 인자 수, 키워드 전용 인자, 전역 이름, `-0.0`과 `0.0`, `True`와 `1`을 하나씩 바꾼 쌍마다 code_hash가 다른지 본다. | I3 |
| T6 | 같은 파일 (parametrize) | 위에 줄 추가, 안에 주석 줄 추가, 줄 끝 주석 추가 쌍마다 code_hash가 같은지 본다. | I4 |
| T7 | 같은 파일 | 몸체에 `a[1:3]`, `1j`, `...`, `b"x"` 상수를 가진 블록이 데코레이트되는지(TypeError 없음), 각 상수를 바꾸면 값이 바뀌는지 본다. | I5 |
| T8 | 같은 파일 (I6 채택 시) | 같은 감싸기 데코레이터로 안쪽 몸체만 다른 두 함수를 감싼 블록의 code_hash가 다른지 본다. | I6 |
| T9 | 기존 `E/tests/core/test_compute_block.py:68-69, 116`, `E/tests/sizing/test_seal_versions.py:15` | 바꾸지 않고 통과하는지 확인한다(형식과 식 불변). | 형식 |
| T10 | `E/tests/generality/` 또는 G-10 test 자리(슬로 마커) | 엔진 폴더를 tmp 두 곳에 복사하고 같은 `GMID_S0_SNAPSHOT_DIR`로 단계 A, B, 탐색 컨텍스트를 순서대로 실행한다. 두 번째 checkout에서 S0 수준 블록 `computes` = 0이고 `context_fp`가 같은지 본다(단계 A ok 회로 1개 이상). | 하류 |

audit 독립 측정(순서 6): `_audit_u17_1b_r2/scripts/measure_g10.py`의 xco 측정을 패치 없이 다시 돌린다. 기대 결과는 8/8 계산 0, context_fp 같음이다. 이번 실측에서 쓴 53블록 3-checkout 비교(`real.py` 방식)도 다시 돌린다.

### 5.3 card 착수 전 범위 판단이 필요한 것

1. **I6 `__wrapped__`**: 결정 10의 원문 범위는 "co_filename 경로 의존"이다. 2.4절의 감싼 블록 문제는 그 전부터 있던 별개 결함이다(대상은 `ly_pattern_select`와 `ly_rows` 2개).
   - 기본안: 같은 줄을 고치는 일이고 비용이 측정 범위 안이므로 포함을 권고한다. "코드 내용만 지문에"라는 원문에도 맞는다.
   - 제외하면 백로그로 넘기고 계약에 "감싼 블록은 바깥 함수만 덮는다"고 명시한다.
2. **줄 정보 포함 여부(D와 D-line)**: 결정 원문 "코드 내용만"을 근거로 D(제외)를 기본안으로 했다. 사용자가 보수적인 쪽을 원하면 D-line으로 바꾸고 I4를 반대로 뒤집는다.
3. **기존 S0 스냅샷 파일**: code_hash 식이 바뀌면 `core/compute_block.py`의 바이트가 바뀌므로 `engine_code_fp`도 바뀐다. 따라서 옛 S0 파일은 키 miss가 되고 U-68 정리 대상이 된다. 별도 이전(migration) 작업은 필요 없다(사실에 근거한 추론: `snapshot_codec.py:344` 키에 code_fp가 있다).
