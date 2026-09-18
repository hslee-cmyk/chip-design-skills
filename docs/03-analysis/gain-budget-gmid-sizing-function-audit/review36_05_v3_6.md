# review36 -- `05-role-separation` design v3.6(커밋 3bf0100) 마지막 좁은 확인

* 검증자: 독립 검증 agent(3bf0100 작성자 아님). 대상: `git show 3bf0100`(review35 M4-01·M4-03·M4-04·M4-07·M4-08 반영, §13.5 분류표, probe·sweep).
* 등급은 계획 `N3.12.0 위협 범위`로 매긴다: **S1** = (a) '막는다' 행의 이력 패턴(`agent7_self_concealment.md`)이 설계대로의 게이트를 통과, (b) 정상 흐름(05 §12, §13.1)이 오거부되거나 적힌 대로 돌지 않음, (c) 3bf0100 자체가 만든 회귀. **S2** = 계획·00-common·05 사이 구현자가 풀 수 없는 모순. 그 밖은 S3 또는 '범위 밖 참고'.
* 실험은 전부 `%TEMP%\rv36\` 아래에서 했다. 저장소에서는 지시된 두 probe 실행(저장소 루트)과 읽기 전용 git 명령만 했다.

## 0. 실측

### 0.1 probe·sweep 재실행 (저장소 루트)

| 명령 | 결과 | 기대 |
|---|---|---|
| `python docs/.../v4_rule_probe/v4.py` | `케이스 67개, 기대 불일치 0개` | 같음 |
| `python docs/.../v4_rule_probe/sweep_engine.py` | `functions 344, exceptions 0, outputs {'PASS': 344}` (2.8 s) | 같음 |
| 실행 뒤 `git -C <repo> diff --stat` | 빈 출력(두 `.out.txt`가 커밋본과 바이트 동일) | 비어야 함 |

`v4.out.txt`의 기대 분류를 직접 셌다: FAIL 34, PASS 11, UNJUDGED 12, NO-SUBJECT 2, known_limit 8(PASS 7·UNJUDGED 1) = 67. 05 §10 문장과 §13.2 공격 23 행의 수와 같다.

### 0.2 review35 추가 V4 케이스를 b60f021 판과 3bf0100 판으로 (`rv36\v4\`)

`rv35\v4e\`의 `v4c_rerun.py`·`v4d_rerun.py`·`v4f.py`·`d25.py`를 복사해 import 경로만 바꿨다(`v4_b60.py` = `git show b60f021:…/v4.py`, `v4_new.py` = 3bf0100 판이고 작업 트리 `v4.py`와 바이트 동일). 두 판의 출력 diff:

| 케이스 | b60f021 | 3bf0100 |
|---|---|---|
| D25 피검 return의 중첩 함수 호출 | `EXC SyntaxError` | `PASS` |
| E2 피검 return의 중첩 def 호출 + 리터럴 | `EXC SyntaxError` | `PASS` |
| E3 피검 return의 중첩 class 인스턴스 | `EXC SyntaxError` | `PASS` |
| d25 스크립트 | traceback(`<opaque:inner>(x)` 재파싱) | `[(2, 'PASS')]` |
| 그 밖 전부(v4c 50여 개, v4d, v4f의 나머지) | -- | 판정 동일(시간 표기만 0.19 s → 0.20 s) |

회귀 0건. M4-03(예외)는 해소됐다.

### 0.3 3bf0100 변경을 케이스 밖에서 (`rv36\sweep2\`, `rv36\f8\`)

* **기대식 쪽 전수**: 엔진 최상위 함수 344개 각각을 **기대식 쪽**에서 부르고 피검은 모듈 끝에 붙인 합성 함수로 둔 sweep(`sweep_x.py new`) → `functions 344, exceptions 0`. 커밋의 sweep은 피검 쪽만 확인했는데, 같은 모듈 인라인이 기대식 쪽에도 도는 경로에서도 예외나 멈춤이 없다.
* **F8(return이 여럿인 같은 모듈 보조 함수)**: `_gm`(return 둘)을 거친 `gain`에서 기대식 `2.0*1e-4/0.2*5e4` → b60f021 `FAIL`, 3bf0100 `PASS`. 이것은 선언된 대가다(05 §10 ③ "return이 하나인 함수만", 알려진 놓침 F8, oracle 대조와 V3가 맡음). 이력 패턴 #9(e329283 `estimate_area_budget`)는 두 판 모두 `FAIL`이다(0.1).
* **`RecursionError` → `UNJUDGED`의 범위**: 5장 S3-2.

### 0.4 `pytest_gate.ini` 수집 범위 (`rv36\clone\`, `rv36\ini\pytest_gate.ini`)

`git -C %TEMP%\rv36 clone --no-hardlinks --no-local <repo> rv36\clone` 뒤 `remote remove origin`. 현재 저장소에는 `test_*.py`와 `conftest.py`가 하나도 없어서 합성 파일을 복제본 안에만 만들었다: `assets/tests/test_ok.py`, `assets/tests/sub/test_sub.py`(수집돼야 함), `assets/tests/tools/test_evil.py`, `assets/tests/sub/tools/test_evil2.py`, `assets/tests/tools/conftest.py`(import 시 `RuntimeError`), `assets/test_outside.py`, `workspaces/test_ws.py`, 루트 `test_root.py`, `tools/gates/test_gate.py`(수집되면 안 됨). ini = `[pytest]` / `testpaths = skills/analog-gmid-design/assets/tests` / `norecursedirs = tools`. 명령은 `PYTHONPYCACHEPREFIX=<빈 디렉터리> python -P -m pytest -c <ini> --rootdir=<clone> --confcutdir=<clone> --collect-only -q -p no:cacheprovider`(pytest 9.0.2).

| 실행 위치(cwd) | 수집 | 종료 |
|---|---|---|
| **복제본 루트** | `assets/tests/sub/test_sub.py`, `assets/tests/test_ok.py` 2개만. `tools/` 아래 test와 conftest 모두 로드 안 됨 | 0 |
| 복제본 밖(`%TEMP%\rv36`) | 위 2개 + `assets/test_outside.py`, `test_root.py`, `workspaces/test_ws.py` = 5개 | 0 |
| `assets/` | 위 2개 + `assets/test_outside.py` = 3개 | 0 |
| 명시 경로 인자 `<clone>/…/assets/tests`, cwd 복제본 밖 | 2개만(`norecursedirs`는 적용됨) | 0 |
| 복제본 루트, `assets/tests` 디렉터리 없음 | `PytestConfigWarning: No files were found in testpaths … Searching recursively from the current directory instead.` 뒤 3개 | 0 |

결론: **cwd = 복제본 루트**이면 M4-01 수정은 설계대로 동작한다. `assets/tests/tools/test_*.py`와 testpaths 밖 test는 수집되지 않고, `assets/tests/test_*.py`는 수집된다. 원인은 pytest의 `Config._decide_args`다: `testpaths`는 `invocation_dir == rootpath`일 때만 쓰이고, 아니면(또는 glob 결과가 비면) **실행 위치 전체**를 수집한다(5장 S3-1).

## 1. 3bf0100 수정별 판정

| 항목 | 판정 | 근거 |
|---|---|---|
| M4-01 `testpaths`·`norecursedirs` (§13.1 ①, §9.2-7 "test 경로 인자가 없다") | **해결(조건부)** | 0.4: 복제본 루트에서 실행하면 정확하다. 00-common §8.1 red 수집이 "실행은 복제본 루트에서"라고 적고 05 §12-7이 "그 안에서 V1~V10"이라고 적어 정상 흐름에서는 성립한다. 조건이 명시되지 않은 점은 S3-1 |
| M4-03 AST 복사(`_inline`·`_replace`에서 `unparse→parse` 왕복 제거) | **해결** | 0.2 D25·E2·E3·d25가 예외 → PASS. 회귀 0 |
| M4-03 `RecursionError`·`MemoryError` → `UNJUDGED` | **부분** | `_hits` 안에서만 잡는다. S3-2 |
| M4-03 return이 하나인 같은 모듈 함수만 인라인 | **해결 + 선언된 대가** | sweep 344(피검 쪽), sweep_x 344(기대식 쪽) 예외·멈춤 0. F8 놓침은 05 §10에 적혀 있다(0.3) |
| `return_variants` AST 노드 캐시, `_module_funcs` `lru_cache(8)` | 문제 없음 | `_inline`이 입력을 deepcopy하므로 캐시된 노드가 바뀌지 않는다. 캐시 상한이 있다. 판정 결과가 b60f021과 같다(0.2) |
| M4-04 §6.2 "`-m`·`-c`는 `-P`, 캐시 스크립트는 `-P` 없이" | **해결** | §0·§6.2·§12-0 서로 일치 |
| M4-07 §9.2-7 `-c` 두 토큰, `--rootdir=`·`--confcutdir=` 한 토큰(값 같음), 경로 슬래시 표기 | **해결 + 잔여 S3** | 00-common §8.1과 05 §12-7의 표기(`=` 한 토큰)와 맞는다. 첫 토큰 대조의 잔여는 S3-4 |
| M4-08 '게이트 스크립트' 판별식(캐시 또는 `<gate_path>` 안의 `.py`) | **해결 + 규정 하나 삭제** | 판별식이 정해져 §17 `check_agents.py`, 사용자 도구, `integrity.py`(작업 트리 실행)가 오거부되지 않는다. 대신 "EL1은 그 밖 디렉터리의 게이트 스크립트 실행을 거부한다"가 빠졌다. S3-3 |
| 05 §10·§13.2 공격 23 수치(67 = 34+11+8+12+2) | 일치 | 0.1 |
| 계획·00-common | 3bf0100은 계획 history만 바꿨다(`git diff b60f021 3bf0100 --stat -- docs/01-plan docs/02-design/...00-common...` = history.md +8) | 계획 N4.2 V4 (2) "같은 모듈 함수까지 인라인 … 놓친다(05 §10)"가 한계를 05 §10에 맡기므로 F8 추가와 모순되지 않는다 |

## 2. §13.5 분류와 N3.12.0 대조

| review35 항목 | §13.5 분류 | N3.12.0 대조 | 판정 |
|---|---|---|---|
| M4-01 `tests/tools/test_*.py` 수집 | 막는다(판정 환경 조작 부류) | agent7 이력에 test 모듈이나 판정 환경 조작 사례는 없다. 그러나 계획 N3.12.2가 같은 디렉터리 `conftest.py`를 `판정 환경`으로 두므로 '막는다' 쪽으로 넣은 것은 보수적이고, 수정도 설정 두 줄이다 | 타당(과잉 쪽) |
| M4-02 `workspaces/numpy.pyw` 모듈 가림 | 의도적 공격 → 알려진 한계, 공격 재생 '기록' | agent7 68건에 모듈 가림이나 `sys.path` 조작 사례가 없다. 같은 계정의 의도적 설계 공격이다 | 타당 |
| M4-03 V4 예외 | 정상 흐름 오거부 → 수정 | 맞다(정상 test가 exit 2 → FAIL) | 타당 |
| M4-04·M4-07·M4-08 | 정상 흐름 오거부 → 문구 | 맞다 | 타당 |
| M4-05 누적·주석 대입·`setattr`·walrus 놓침 | 검출기 한계(F7) | V4 (2)는 "확실한 복사 검출 + oracle 대조"(사용자 결정 (c))이다. 00-common §8.1 로더 규칙 10의 oracle 대조가 "기대값마다"라서 `NO-SUBJECT`로 빠진 assert도 덮는다. 이력 #9(e329283)는 여전히 FAIL | 타당 |
| M4-06 `nonlocal`·comprehension walrus 거짓 FAIL | 검출기 한계(F7) | E17·E18은 test가 먼저 `e = 2e-3 * 50e3`(피검 재서술)을 적은 뒤 가려 쓰는 인위적 모양이다. 정상 흐름의 test가 아니고, 거짓 FAIL이 가리키는 문장도 실제로 재서술을 담고 있다 | 타당 |
| M4-09 판정 트리 안 로그 | 선언된 대가 | §4.1 쓰기 경로표 개정 경로가 있다 | 타당 |

**범위 밖으로 잘못 분류된 항목은 없다.** 참고로 M4-01과 M4-02를 가르는 근거("같은 부류" 대 "이력에 없음")는 둘 다 이력에 없다는 점에서 비대칭이다. 그래도 M4-01을 막는 쪽으로 둔 결과가 해를 주지 않으므로 등급 대상이 아니다.

## 3. 계획 · 00-common · 05 모순

새 S2 없음. 확인한 일치:
* 05 §0 ↔ §6.2 ↔ §12-0 ↔ 00-common §10: `-P` 적용 범위(M4-04 해소)
* 05 §9.2-7 ↔ §12-7 ↔ 00-common §8.1: `-c <캐시>/pytest_gate.ini`, `--rootdir=`·`--confcutdir=` 한 토큰
* 05 §13.1 ① ↔ 계획 N3.12.6 산출물 `tools/gates/pytest_gate.ini`(내용은 05가 정함)
* 05 §10 알려진 놓침 F7·F8 ↔ 계획 N4.2 V4 (2)의 "놓친다(05 §10)" 위임

## 4. S1 · S2

없음.

## 5. S3

* **S3-1 `testpaths`는 cwd = rootdir일 때만 쓰인다.** 3bf0100이 V1에서 test 경로 인자를 없애 수집 범위를 `testpaths`에 맡겼다. 그런데 pytest는 실행 위치가 `--rootdir`와 다르면 `testpaths`를 무시하고 **실행 위치 전체**를 수집한다(0.4: 복제본 밖에서 5개, `assets/`에서 3개, 종료 0). auditor subagent의 셸이 audit worktree로 돌아가 있는 상태에서 V1을 치면 M4-01 수정이 꺼지고, 격리 복제본이 아닌 곳의 test가 수집된다. `assets/tests`가 없어도 경고 하나만 내고 같은 일이 일어난다. 00-common §8.1(red)은 "복제본 루트에서"라고 적었고 05 §12-7도 "그 안에서"라고 적었으므로 설계대로면 성립한다. 그래서 S3로 둔다. 권고(한 줄 수준): 05 §12-7과 §9.2-7에 "V1·red는 cwd = 복제본 루트"를 명시하고 V1 기록 형식에 넣는다(예: `cd <복제본 루트> && …`를 §9.2-7이 대조). 아니면 V1에 `<복제본 루트>/skills/analog-gmid-design/assets/tests` 절대 경로 인자 하나를 고정한다(0.4 넷째 줄: cwd와 무관하게 2개). `-W error::pytest.PytestConfigWarning`을 ini의 `filterwarnings`에 넣으면 빈 testpaths로 되돌아가는 경로도 막힌다.
* **S3-2 `RecursionError` → `UNJUDGED`는 `_hits` 안에서만 잡는다.** 기대식 쪽(`_assert_pairs`, `expand(x)`, `canon`)과 피검 `return_variants`(`_walk_body` → `_inline` deepcopy)는 `try` 밖이다. 실측(`rv36\f8\thr.py`, 기본 재귀 한도): 기대식 항 248개, 피검 연쇄 대입 246개, test 연쇄 대입 248개부터 `RecursionError`가 그대로 나간다(게이트에서는 exit 2 → FAIL). b60f021도 같아서(`f8.out.txt`) 3bf0100의 회귀가 아니고, 실제 엔진 344개 함수는 피검 쪽과 기대식 쪽 모두 예외 0이다. 05 §10 ③의 "식이 너무 깊어 펼치지 못하면 `UNJUDGED`"를 `test_lint.py`로 옮길 때 `judge`의 assert 한 건 처리 전체(`return_variants`·`expand(x)`·`canon` 포함)를 감싸면 된다.
* **S3-3 §0의 "EL1은 그 밖 디렉터리의 게이트 스크립트 실행을 거부한다"가 삭제됐다.** 판별식(캐시 또는 `<gate_path>` 안의 `.py`)이 생기면서 그 정의상 '밖의 게이트 스크립트'가 없어졌다. 그래서 auditor가 복제본의 `tools/gates/*.py`(같은 변경에서 code-author가 바꿀 수 있는 '게이트 변경' 경로)를 실행하는 것을 막는 문장은 이제 §12-7의 절차 규정("복제본의 것이 아니라 base 판")뿐이다. 오거부는 없다. 옛 문장은 판별식이 없어 구현할 수 없었으므로 실효가 줄어든 것은 아니다. 필요하면 공격 재생에서 "auditor가 복제본 `tools/gates/`의 V3~V7을 실행"을 기록 케이스로 둔다.
* **S3-4 §9.2-7 첫 토큰 대조와 "슬래시 표기".** `shlex.split(r"C:\Python314\python.exe -P …")` → `['C:Python314python.exe', …]`(실측). 슬래시로 적은 `C:/Python314/python.exe`는 `gate_config.json`의 `python_path`가 역슬래시(05 §0의 `$PY` 정의 표기)이면 "같고"를 만족하지 않는다. `$PY` 글자 그대로 적는 길이 있어 정상 흐름이 막히지는 않는다. 그래도 `python_path`를 슬래시로 적게 하거나, 대조를 `normpath`·`normcase` 뒤에 한다고 한 줄 적는 것이 좋다.

## 6. 범위 밖 참고

* `norecursedirs = tools`는 pytest 기본 목록(`.*`, `build`, `dist`, `venv`, `node_modules` 등)을 **대체**한다. `assets/tests/.x/` 같은 곳의 test도 수집된다. test-author 경로 안의 일이라 위협 범위에서는 의미가 없다.

## 7. 안전 점검 (검증 종료 시점)

* 실험 위치: `%TEMP%\rv36\`(`v4\`, `sweep2\`, `f8\`, `clone\`, `clone_notests\`, `ini\`, `pyc\`). 복제는 `git -C %TEMP%\rv36 clone …`, 복제본 조작은 `git -C <복제본> …`. 쓰기 스크립트는 `set -euo pipefail`로 시작했다. 저장소에서 쓰기형 git 명령은 실행하지 않았다.
* `git -C <repo> status --short`: 시작 스냅숏과 같다. 추적되지 않는 파일만 있다(`.bkit/audit/*.jsonl` 22개, `assets/` zip 2개, `workspaces/current-reuse-telescopic-ota-report/` 3개). 이 보고서 파일은 기록 뒤 추가된다.
* `git -C <repo> log --oneline -1`: `3bf0100 docs(analog-gmid-design): 05-role-separation v3.6 -- review35 위협 범위 재분류, 문서 검토 종료`(기대와 같음)
* `git -C <repo> diff --stat`: 빈 출력(probe 두 개 재실행 뒤에도)
* `git -C <repo> config --show-origin --get core.hooksPath`: `file:.git/config	C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/.githooks`

## 8. 집계와 판정

| 구분 | 건수 | 항목 |
|---|---|---|
| S1 | 0 | -- |
| S2 | 0 | -- |
| S3 | 4 | S3-1 testpaths의 cwd 조건, S3-2 RecursionError 부분 처리, S3-3 EL1 게이트 스크립트 문장 삭제, S3-4 첫 토큰 대조 표기 |
| review35 수정 확인 | M4-01(조건부)·M4-03·M4-04·M4-07·M4-08 해결, 3bf0100의 회귀 0 | |
| §13.5 분류 | 범위 밖으로 잘못 분류된 항목 0 | |

**승인 가능** -- S1 0 · S2 0 · S3 4
