# review35 -- `05-role-separation` design v3.5(커밋 b60f021) review34 M3-01~M3-09 해소 독립 검증

* 대상: b60f021 -- 계획 N3.12.2(조건 `판정 트리`와 그 행, 트리 안 기존 파일 행, `판정 환경` 행 추가, `pytest_gate.ini` 행, hook 판정 범위), N4.2 V4 (2) 문구, 05 v3.5(§0·§4.1·§6.2·§9.2-7·§10·§12-7·§13 ①·17·23·§19·§20), `00-common` §8.1 red 수집 명령, `v4_rule_probe/v4.py`·`v4.out.txt`
* 기준: `review34_05_v3_4.md` M3-01~M3-09
* 검증자: 독립 검증 agent(작성자 아님). 저장소에서는 이 보고서만 쓴다(Python 바이너리 append). 실측 스크립트·임시 저장소는 `C:\Users\HSLEE\AppData\Local\Temp\rv35\`(저장소 밖). git 실험은 모두 `git -C <rv35 안 절대 경로>`(clone 포함), 셸은 `set -euo pipefail`.
* 등급: **S1** 승인 차단 / **S2** 승인 전 수정 / **S3** 경미
* 시작 시점: HEAD = b60f021, `git diff --stat` 비어 있음, `status --short` 27줄(모두 `??`, 대화 시작 스냅숏과 같음)
* 환경: Python 3.14.2, pytest 9.0.2, git 2.52(Windows), MSYS bash

---

## 0. 실측

### 0.1 M3-01: 쓰기 경로표 파싱과 기존 추적 파일 (`rv35\m1\pathrules.py`, `pathrules.out.txt`)

05 §4.1대로 구현했다: 절 `#### N3.12.2 `의 표를 이스케이프 안 된 `|`로 자르고 셀 수 4·주체·조건 값 집합 검사, `match_glob`은 `<id>` 치환(없으면 불일치) → 패턴·경로 모두 `casefold` → `/`로 조각, `**`는 0개 이상 조각, 나머지는 `fnmatch.fnmatchcase`. 우선순위: ① `판정 환경` 행에 맞으면 사용자만 ② `판정 트리` 행에 맞고 다른 조건의 행 어디에도 안 맞으면 사용자만 ③ 그 밖은 맞은 행의 주체.

| 측정 | 결과 |
|---|---|
| 파싱한 행 | 66개(표 파손 없음, 값 집합 밖 없음) |
| `git ls-files skills/analog-gmid-design`(읽기 전용) | **220개 모두 판정 트리 행 말고 다른 행에 맞는다**. 사용자 전용이 되는 추적 파일 **0개**, `판정 환경`에 걸리는 추적 파일 0개 |
| 주체 분포 | code-author 130(`assets/*.py`·`*.npz`·`_sweep.cir`·`report_template.html`·`ac_sweep_checkpoints/**`), test-author 49(`assets/tests/**`·기준선·`sky130_regression_reference.json`), 오케스트레이터 `없음` 31 + `승인 기록` 10(`*.topology.json`) |
| 추적 안 되는 트리 안 파일(`ls-files -o`) | `assets/*.log` 7개(`selftest_session6*.log` 등)·`assets/*.zip` 2개는 **판정 트리 기본 거부**(사용자 전용). `assets/tests/*.result.txt`·`*.json`은 test-author, `assets/library/.bkit/runtime/*`는 오케스트레이터 |

review34 V1~V3과 새 후보를 새 규칙에 넣은 결과(`rv35\m2\drive2.out.txt` 끝):

| 경로 | 결과 |
|---|---|
| `assets/numpy/__init__.py`, `assets/eng/__init__.py`, `assets/numpy.pyw`, `Skills/Analog-GMID-design/assets/numpy/__init__.py` | 사용자 전용(판정 트리 기본 거부) -- **닫힘** |
| `assets/__pycache__/eng.cpython-314.pyc` | 사용자 전용(`판정 환경`) -- **닫힘** |
| `workspaces/numpy.py`, `workspaces/numpy.pyc` | 사용자 전용(`판정 환경`) |
| **`workspaces/numpy.pyw`, `workspaces/numpy/__init__.pyw`** | **어느 행에도 안 맞음 = 역할 밖**(트레일러 없는 커밋 통과) |
| `assets/tests/tools/test_zz.py`, `assets/tests/tools/numpy/__init__.py` | code-author(`없음`) |
| `assets/test_zz_selfcheck.py`, `assets/ac_sweep_checkpoints/test_zz.py` | code-author(`없음`) |
| `references/test_zz.py` | 오케스트레이터(`없음`) -- 메인 세션이 도구 호출로 쓸 수 있다 |
| `assets/tests/tools/conftest.py` | 사용자 전용(`판정 환경`). `assets/tests/conftest.py`는 test-author |

**새 길 실측** (장난감 복제본. 실행은 v3.5 형태 그대로: 복제본 루트에서 `PYTHONPATH=<캐시> PYTHONPYCACHEPREFIX=<빈 임시> $PY -P -m pytest -c <캐시>/pytest_gate.ini --rootdir=<복제본> --confcutdir=<복제본> -p merge_gate …`. 대조군은 모두 `1 failed`·종료 1. `rv35\m2\drive.out.txt`·`drive2.out.txt`):

| # | 파일(쓰는 주체) | V1 대상 경로 | 결과 |
|---|---|---|---|
| N1 | `assets/tests/tools/test_tool_smoke.py`(code-author 행). 모듈 머리에서 `math.isclose = lambda *a, **k: True` | `skills` 또는 `…/assets/tests` | **`3 passed`, 종료 0** -- pytest는 수집 단계에서 모든 test 모듈을 import한 뒤 실행하므로 머리 코드가 모든 test보다 먼저 돈다 |
| N1b | 같은 내용의 `assets/tests/tools/measure.py`(수집 안 되는 이름) | `skills` | 종료 1(대조) |
| N1c | `assets/test_zz_selfcheck.py`(code-author `assets/*.py`) | `skills` / `…/assets/tests` | **종료 0** / 종료 1 |
| N1d | `assets/ac_sweep_checkpoints/test_zz.py`(code-author `ac_sweep_checkpoints/**`) | `skills` / `…/assets/tests` | **종료 0** / 종료 1 |
| N1e | `references/test_zz.py`(오케스트레이터 `references/**` -- **메인 세션**) | `skills` / `…/assets/tests` | **종료 0** / 종료 1 |
| N2 | `assets/helpers.py`(code-author)가 test-author `assets/tests/helpers.py`를 가림(conftest가 assets를 `sys.path` 0번에 넣을 때와 뒤에 붙일 때) | `skills` | 종료 1 -- pytest `prepend`가 test 모듈 import 때마다 test 디렉터리를 0번으로 다시 올린다. 가리지 못함 |
| N3 | `workspaces/numpy.pyw`(역할 밖). `00-common` §10.2 형태 별도 프로세스(`sys.path` 앞 = assets, workspaces)에서 `numpy.isclose`로 판정하는 도구 | -- | 대조 `same = False`·종료 1 → **`numpy from …\workspaces\numpy.pyw`, `same = True`, 종료 0** |
| N3c | `numpy/__init__.pyw` 패키지 | -- | 같음(`[FAKE numpy pkg __init__.pyw]`) |

`importlib.machinery.SOURCE_SUFFIXES`는 Windows에서 `['.py', '.pyw']`다. 판정 트리 안은 기본 거부로 `.pyw`도 닫히지만, 트리 **밖** `workspaces`는 여전히 이름 목록(`workspaces/*.py`, `workspaces/*/__init__.py`)이라 `.pyw`가 빠졌다. §10.2 절차 2(import한 모듈의 `__file__`이 worktree 안)와 3(`git status` 청결)은 커밋된 `workspaces/numpy.pyw`를 거르지 못한다(둘 다 참).

N1 계열: 계획 N3.12.2는 `assets/tests/tools/conftest.py`를 `판정 환경`으로 막는데(공격 17), 같은 pytest 세션에 수집되는 test 모듈은 conftest와 같은 힘(수집 전 import, 전역 몽키패치)을 갖는다. `pytest_gate.ini`는 빈 `[pytest]`라 `python_files`·`norecursedirs`·`testpaths`가 기본값이고, V1·red 수집의 대상 경로는 문서에 `…`로만 있다(00-common §8.1, 05 §12-7). EL3의 "code 커밋이 `tests/**`(`tests/tools/**` 제외)를 바꾸면 차단"도 `tests/tools/test_*.py`를 막지 않는다. `references/**`·`ac_sweep_checkpoints/**`·`assets/*.py`는 파일 종류를 가리지 않는 행이라 V1 대상이 skill 루트 이상이면 같은 길이 된다.

### 0.2 M3-02: 복제본 밖 설정·커밋된 `.pyc` (`rv35\m2\drive.out.txt`)

| 실행 | 결과 |
|---|---|
| 대조(v3.5 형태) | `configfile: …\cache\pytest_gate.ini`, `1 failed, 1 passed`, 종료 1 |
| 부모 `pytest.ini`(`addopts = --deselect …::test_a`), **v3.4 형태**(`-c`·`--confcutdir` 없음) | `configfile: ..\pytest.ini`, `1 passed, 1 deselected`, **종료 0** (review34 재현) |
| 같은 부모 `pytest.ini`, **v3.5 형태** | `configfile: …\cache\pytest_gate.ini`, **종료 1** |
| 부모 빈 `pytest.ini` + `conftest.py`(test_a 제거), v3.4 형태 / v3.5 형태 | **종료 0** / **종료 1** |
| 부모 `pyproject.toml` + `conftest.py`, v3.5 형태 | 종료 1 |
| 복제본 루트 `pytest.ini`(addopts deselect), v3.5 형태 | 종료 1 -- `-c`가 복제본 안 설정 탐색도 끈다 |
| 커밋된 unchecked-hash `assets/__pycache__/eng.cpython-314.pyc`(`git add -f`, 트레일러 없음, `--no-hardlinks --no-local` 복제), `PYTHONPYCACHEPREFIX` 없음 | **`2 passed`, 종료 0** (review34 V3 재현) |
| 같은 복제본, `PYTHONPYCACHEPREFIX=<빈 임시 디렉터리>` | **종료 1** -- 커밋된 `__pycache__`를 읽지 않는다 |

→ `-c <캐시>/pytest_gate.ini --rootdir --confcutdir`는 복제본 부모의 `pytest.ini`·`pyproject.toml`·`conftest.py`를 모두 무시하고, `PYTHONPYCACHEPREFIX`는 커밋된 `__pycache__` 바이트코드를 무력화한다. (소스 없는 `.pyc`(`assets/<이름>.pyc`)는 접두사와 무관하게 로드되지만 `**/*.pyc` `판정 환경` 행과 판정 트리가 막는다.)

### 0.3 M3-04·M3-05·M3-07: V4 (2) (`v4.py` 저장소 루트 실행, 추가 케이스는 `rv35\v4e\`가 `v4.py`를 import -- v4.py 수정 없음)

**재현**: 저장소 루트에서 `$PY docs/03-analysis/…/v4_rule_probe/v4.py` → 종료 0. `v4.out.txt` 66번째 줄 `케이스 65개, 기대 불일치 0개`(뒤에 R-05 네 조합 4줄, 파일 70줄). 기대값 분포를 직접 세면 FAIL 34·PASS 10·known_limit 7(PASS 6·UNJUDGED 1)·UNJUDGED 12·NO-SUBJECT 2 = 65로 05 §10·공격 23과 같다. 실행 뒤 `git -C <repo> diff --stat` 비어 있음(`v4.out.txt` 바이트 동일).

**review33 v4c 49줄 재실행**: review34 결과와 줄 단위로 같다(회귀 없음). **review34 v4d 27케이스 재실행**(`v4d.out.txt`) -- review34 대비 바뀐 줄:

| 케이스 | v3.4 | v3.5 | 판정 |
|---|---|---|---|
| D1 `append`·D2 첨자·D3 속성·D4 표 구동 사전 | NO-SUBJECT | **UNJUDGED** | 해결(M3-04) |
| D6 중첩 def 지역 이름, D7 comprehension 변수 | PASS | **FAIL** | 해결(M3-05) |
| D10·D11 블록 안 기대식 | PASS | PASS(F6로 문서화) | 설계대로 |
| **D25** 피검 `return inner(x)`(피검 안 중첩 함수 호출) | PASS | **예외 `SyntaxError: invalid syntax`** | **회귀** |

**새 적대 케이스**(`v4f.py`/`v4f.out.txt`, 8c5b9e3 판과 나란히):

| 입력 | 8c5b9e3 | b60f021 | 목적상 기대 | 분류 |
|---|---|---|---|---|
| E2 피검 `def inner…; return inner(x)` + 리터럴 기대 `6.0` | PASS | **EXC SyntaxError** | PASS/UNJUDGED | **회귀** -- `_assigned_names`가 중첩 def·class 이름을 넣어 불투명 이름 `<opaque:inner>`가 되고, `_inline`이 `ast.unparse` → `ast.parse`로 되읽다 `<opaque:inner>(x)`에서 구문 오류 |
| E3 피검 `class R…; return R()` | PASS | **EXC SyntaxError** | PASS/UNJUDGED | 같음 |
| E1 `return inner`(클로저 반환), E4·E5 test 안 중첩 helper | UNJUDGED/PASS | 같음 | -- | 예외 없음 |
| E10 `d.update(a=f(…))`, E16 `if` 안 첨자 대입 → 밖 assert | NO-SUBJECT | **UNJUDGED** | UNJUDGED/FAIL | 개선 |
| E6 `out['a'] += f(…)`, E7 `res.v: float = f(…)`, E8 `out['a'], k = f(…), 1`, E9 `setattr(ns, 'r', f(…))` | NO-SUBJECT | **NO-SUBJECT** | UNJUDGED/FAIL | M3-04 잔여(누적·주석 대입·튜플 대상·`setattr`) |
| E12 `assert (r := f(…)) == …` 뒤 `assert r == …` | UNJUDGED, NO-SUBJECT | 같음 | FAIL | 기존 동작(walrus 미추적) |
| E13 결정성 test `base['x'] = f(…); assert f(…) == base['x']` | PASS | PASS | PASS/UNJUDGED | 새 거짓 양성 없음 |
| E14 `pytest.xxx(f(…))`·E15 `log.info(f(…))` 뒤 재서술 | FAIL | FAIL | FAIL | 메서드 밑 이름 표시가 `pytest`를 가려 FAIL을 놓치게 하지 않음 |
| E17 comprehension 안 walrus `[(e := v) for …]`로 바깥 `e`가 1.0이 됨 | FAIL | FAIL | PASS/UNJUDGED | 기존 거짓 FAIL(PEP 572: walrus는 바깥 범위에 대입) |
| **E18** 중첩 `def h(): nonlocal e; e = 1.0` 뒤 `h()` → `approx(e)` | PASS | **FAIL** | PASS/UNJUDGED | **새 거짓 FAIL**(M3-05 변경: 중첩 범위 이름을 건너뛰어 `nonlocal` 대입을 못 봄) |
| E20 lambda 기본값 `lambda e=e: e` | FAIL | FAIL | FAIL | 기대대로 |

**실제 엔진 영향**(`rv35\v4e\scan_nested.py`): `skills/analog-gmid-design/assets/*.py`의 함수 516개 중 **17개**가 return 식에서 중첩 def·class 이름을 쓴다(`sizing_recipe.py` `_build_theta_evaluator`·`make_replica_feasibility_check`·`_optimize_theta_slsqp` 등, `stick_diagram.py` 3, `topology_library.py` 2). 이 함수들이 interface card 심볼(피검)이 되고 return이 그 이름을 호출·생성하는 모양이면 V4 (2)가 예외로 끝나고, 05 §10 머리 규칙("도구 자신의 예외는 exit 2, auditor는 FAIL")으로 **정상 test가 V4 FAIL**이 된다(E1처럼 이름만 돌려주는 경우는 예외가 없었다).

### 0.4 M3-08: V1 명령 형식 규칙의 `shlex.split`

```
shlex.split(r'PYTHONPATH=C:\Users\x\.git\gmid-gate-cache\abc … C:\Python314\python.exe -P -m pytest -c C:\Users\…\pytest_gate.ini --rootdir=C:\T\id-iso …')
→ ['PYTHONPATH=C:Usersx.gitgmid-gate-cacheabc', …, 'C:Python314python.exe', '-P', '-m', 'pytest', '-c', 'C:Usersx.gitgmid-gate-cacheabcpytest_gate.ini', '--rootdir=C:Tid-iso', …]
```

POSIX 모드 `shlex.split`은 따옴표 없는 `\`를 이스케이프로 먹는다. auditor가 Windows 경로를 따옴표 없이 적으면 첫 토큰이 `python_path`(`C:\Python314\python.exe`)와 달라지고 `-c` 값이 캐시 경로로 보이지 않아 **정상 기록이 EL4 거부**된다(안전 쪽). 따옴표로 감싸면 보존된다.

---

## 1. M3-01~M3-09 판정

| ID | 등급(34) | 판정 | 근거 |
|---|---|---|---|
| M3-01 | S1 | **부분** | review34 V1~V3(`assets/numpy/__init__.py`·`assets/eng/__init__.py`·커밋된 `.pyc`)은 판정 트리 기본 거부·`판정 환경` 행·`PYTHONPYCACHEPREFIX`로 닫혔고, 추적 파일 220개 중 의도치 않게 사용자 전용이 되는 것은 0개다(§0.1). 그러나 같은 부류가 (1) 역할 행 안에서 pytest가 수집하는 test 모듈(`tests/tools/test_*.py`, V1 대상이 넓으면 `assets/test_*.py`·`references/test_*.py`)과 (2) 판정 트리 밖 이름 목록의 빈칸(`workspaces/*.pyw`)으로 남아 둘 다 종료 1 → 0을 실측했다 → M4-01·M4-02 |
| M3-02 | S1 | **해결** | §0.2: v3.4 형태에서 부모 `pytest.ini`·`conftest.py`로 종료 0이던 것이 v3.5 형태(`-c`·`--rootdir`·`--confcutdir`)에서 종료 1. 커밋된 unchecked-hash `.pyc`는 `PYTHONPYCACHEPREFIX`로 종료 0 → 1 |
| M3-03 | S2 | **부분** | 05 §0(스크립트 형태는 `-P` 없음)·§9.1 `pre-receive`(`exec python gate-runner.py`)·§12-0·§17 명령·`00-common` §10 명령은 서로 맞는다. 그러나 05 §6.2 캐시 예외 행이 "두 형태(스크립트 인자 형태 포함) 모두 실행은 `$PY -P …`여야 한다"를 그대로 두어 §0과 모순이다 → M4-04. §0 "EL1은 그 밖 디렉터리의 게이트 스크립트 실행을 거부"는 '게이트 스크립트'의 판별식이 없고 §17 `$PY agent-quality/check_agents.py`(역할 경로·캐시·gate 밖)와 부딪힌다 → M4-08 |
| M3-04 | S2 | **해결(대상 넷) + 잔여 S3** | D1~D4 모두 `UNJUDGED`, `d.update`·블록 안 첨자도 `UNJUDGED`(§0.3). 누적 대입 `out[k] += f`, 주석 대입 `res.v: T = f`, 튜플 대상 안 첨자, `setattr`은 여전히 `NO-SUBJECT` → M4-05 |
| M3-05 | S3 | **해결 + 새 결함 도입** | D6·D7 FAIL, F6 문서화(05 §10, 공격 23 known_limit 7). 그러나 중첩 def·class **이름**을 불투명 이름으로 넣는 변경이 피검 return의 `inner(x)`·`R()`에서 `SyntaxError`를 내고(M4-03, S2), 중첩 범위를 건너뛰어 `nonlocal` 재대입을 못 봐 거짓 FAIL을 낸다(E18, M4-06) |
| M3-06 | S3 | **해결** | 계획 N4.2 V4 (2)가 "그 return 식에 나오는 매개변수에 결합된 인자 식 하나와 같다"로 05 §10 ⑤와 같다 |
| M3-07 | S3 | **해결** | `v4.py` docstring이 "정확한 유리수 … 다중집합"으로 바뀌었고 "자체 대조는 첫 판정 문장"을 적었다. 05 §10도 "둘째 이후 판정 문장은 출력만 기록" |
| M3-08 | S3 | **부분** | (가) `$PY` 글자 또는 `python_path` (나) `NAME=값` 앞붙임 건너뜀 (다) 형식 검사임을 명시 -- 셋 다 반영. 그러나 `shlex.split`이 따옴표 없는 Windows 경로의 `\`를 먹고(§0.4), `-c` 값이 "캐시의 `pytest_gate.ini`"인지 gate가 무엇과 대조하는지(gate는 작업 저장소의 `<git-common-dir>` 경로를 모른다), `--rootdir x`(두 토큰)·`--rootdir=x` 중 무엇을 받는지가 정해지지 않았다 → M4-07 |
| M3-09 | S3 | **해결** | 05 §6.2: hook은 `;`로만 자르고 POSIX `:` 목록은 첫 원소가 캐시로 보이지 않아 거부, 캐시 표기 `C:\…`·`C:/…`·`/c/…` 정규화 뒤 `normcase` |

집계: **해결 4**(M3-02·06·07·09) + **해결+잔여 1**(M3-04) / **부분 3**(M3-01·03·08) / **해결+새 결함 도입 1**(M3-05) / **미해결 0**.

---

## 2. 새 결함

### M4-01 [S1] pytest가 수집하는 test 모듈을 test-author가 아닌 역할이 쓸 수 있다 (`판정 환경`과 같은 힘)
* **위치**: 계획 N3.12.2 `gmid-code-author | skills/analog-gmid-design/assets/tests/tools/** | 없음`(그리고 `assets/*.py`, `assets/ac_sweep_checkpoints/**`, 오케스트레이터 `references/**` -- 파일 종류 무제한), `tools/gates/pytest_gate.ini`(빈 `[pytest]`), `00-common` §8.1·05 §12-7의 V1·red 수집 대상 경로(`…`), 계획 N3.12.4 EL3("code 커밋이 `tests/**`(`tests/tools/**` 제외)…"), 공격 17.
* **근거**: §0.1 N1 -- code-author가 `assets/tests/tools/test_tool_smoke.py`의 모듈 머리에서 `math.isclose`를 바꾸면 v3.5 판정 실행 형태 그대로(`-P`·`-c`·`--confcutdir`·`PYTHONPYCACHEPREFIX`)에서 실패 test가 통과한다(종료 1 → 0). pytest는 전체 수집(모듈 import)을 끝낸 뒤 실행하므로 파일 이름 순서와 무관하다. V1 대상이 `skills`처럼 넓으면 `assets/test_*.py`·`ac_sweep_checkpoints/test_*.py`(code-author)와 `references/test_*.py`(**메인 세션**)도 같은 결과(N1c~N1e). 설계는 같은 디렉터리의 `conftest.py`를 이 이유로 `판정 환경`에 넣었다(공격 17) -- 수집되는 test 모듈은 conftest와 같은 프로세스·같은 시점에 import된다.
* **수정 방향**: (1) `pytest_gate.ini`에 수집 범위를 고정한다 -- `testpaths = skills/analog-gmid-design/assets/tests`, `norecursedirs`에 `tools`(또는 V1·red 명령에 `--ignore=…/assets/tests/tools`), 그리고 V1·red 수집 명령의 위치 인자를 문서에 고정해 §9.2-7 형식 검사에 넣는다. (2) 또는 계획 N3.12.2에 `assets/tests/**`(tools 제외) 밖의 `test_*.py`·`*_test.py`를 `판정 환경`으로 둔다. (3) 공격 17에 N1·N1c~N1e를 넣는다.

### M4-02 [S1] 판정 트리 밖 `workspaces`의 import 가능 파일이 여전히 이름 목록이다 -- `.pyw`가 빠졌다
* **위치**: 계획 N3.12.2 `사용자 | workspaces/*.py | workspaces/run_harness.py | 판정 환경`, `workspaces/*/__init__.py`, 05 §4.1 `판정 트리` 문단("판정 트리 밖에서 import될 수 있는 것은 `판정 환경` 행이 덮는다"), `00-common` §10.2 절차 1(`sys.path` 맨 앞 = assets, workspaces).
* **근거**: §0.1 N3 -- `workspaces/numpy.pyw`(어느 행에도 안 맞는 역할 밖, 트레일러 없이 커밋 가능)가 §10.2 형태 프로세스에서 `numpy`를 대신해 `numpy.isclose` 판정이 뒤집힌다(종료 1 → 0). `numpy/__init__.pyw`도 같다. Windows `SOURCE_SUFFIXES = ['.py', '.pyw']`. §10.2 절차 2·3은 이것을 거르지 못한다. `measure_search_perf.py`·`noop_proof.py`는 `00-common` 등급표에서 "보고 수치·판정"이다. review34 M3-01과 같은 부류(역할 밖 파일이 import 해석으로 판정 실행을 바꿈)이고, 이번 개정이 "이름 목록이 아니라 기본 거부"로 옮긴 이유가 트리 밖에서 재발한 것이다.
* **수정 방향**: `workspaces`도 기본 거부로 옮기거나(예: 최상위 `workspaces/*` 전부를 `판정 환경`으로 두고 `run_harness.py`와 기존 보고서 디렉터리는 별도 행), 적어도 접미사를 `importlib.machinery.all_suffixes()` 기준으로 전부 덮는다(`*.pyw`, `*/__init__.pyw`). 공격 17 후보 대조에 `all_suffixes()`와 행 대조를 더한다(pytest `config_names` 대조와 같은 방식).

### M4-03 [S2] V4 (2): 피검 return이 중첩 def·class를 호출·생성하면 검출기가 예외로 끝난다 (M3-05 수정이 도입)
* **위치**: `v4.py` `_assigned_names`(중첩 def·class 이름을 넣음) → 불투명 이름 `<opaque:inner>` → `_inline`의 `ast.parse(ast.unparse(expr))`; 05 §10 V4 행 "중첩 함수·클래스·lambda·comprehension의 지역 이름은 바깥 이름을 가리지 않는다", §10 머리 "도구 자신의 예외는 exit 2(auditor는 FAIL)".
* **근거**: §0.3 D25·E2·E3 -- 8c5b9e3에서 PASS이던 `return inner(x)`·`return R()`가 `SyntaxError`. 실제 엔진 함수 17개(516개 중)가 return에서 중첩 def·class 이름을 쓴다. 게이트 규칙대로면 정상 test가 V4 FAIL이 된다(오거부). 65케이스 자체 대조에는 이 모양이 없어 `기대 불일치 0개`가 이것을 드러내지 못했다.
* **수정 방향**: 불투명 이름을 문자열로 되읽지 않게 한다(`ast.Name(id="<opaque:…>")`는 `unparse`→`parse` 왕복을 못 한다) -- 합법 식별자 접두를 쓰거나 `_inline`에서 왕복을 없앤다. 피검 쪽 return 변형에서 중첩 def·class 이름은 F3처럼 불투명 잎으로 둔다. probe에 D25·E2·E3을 기대 PASS(또는 UNJUDGED)로 넣는다.

### M4-04 [S2] 05 §6.2 캐시 예외가 스크립트 형태에도 `-P`를 요구해 §0과 모순 (M3-03 잔여)
* **위치**: 05 §6.2 '저장소 내부' 행 "두 형태 모두 실행은 `$PY -P …`여야 한다(§0, review33 M2-01)" ↔ 05 §0 "스크립트 형태(`$PY <경로>/<이름>.py`)는 `-P`를 쓰지 않는다", §12-0 `$PY <게이트 코드>/interface_card.py …`, 부록 CLI `$PY <게이트 코드>/merge_gate.py plan-tables-hash …`.
* **근거**: §6.2대로 구현한 EL1은 `-P` 없는 `$PY <캐시>/interface_card.py`를 거부하고, `-P`를 붙이면 review34 §0.1 실측대로 같은 디렉터리 import가 깨진다. 어느 쪽이든 §12-0 0단계가 멈춘다.
* **수정 방향**: §6.2 문장을 "`PYTHONPATH` 형태(`-m`·`-c`)는 `$PY -P …`, 캐시 스크립트 인자 형태는 `-P` 없이"로 고친다.

### S3
* **M4-05** V4 (2) 피검 불투명 표시가 `Assign`과 식 문장의 메서드 호출만 본다: `out[k] += f(…)`(`AugAssign`), `res.v: T = f(…)`(`AnnAssign`), 튜플 대상 안 첨자, `setattr(ns, 'r', f(…))`, walrus로 받은 이름은 `NO-SUBJECT`(E6~E9·E12). 05 §10 문구("첨자·속성으로 받거나")는 이들을 포함하는 것처럼 읽힌다 -- 구현을 넓히거나 F 목록에 적는다.
* **M4-06** 중첩 범위를 건너뛰는 규칙이 `nonlocal`·comprehension 안 walrus(PEP 572: 바깥 범위에 대입)를 놓쳐 실제 기대값이 리터럴 1.0인데 FAIL이다(E18은 v3.5에서 새로, E17은 기존). "FAIL은 확실한 복사"와 어긋난다. `nonlocal`·`global` 선언과 comprehension 안 `NamedExpr`가 대입하는 이름은 바깥 env에서 불투명으로 둔다.
* **M4-07** 05 §9.2-7: `shlex.split`(POSIX)이 따옴표 없는 `\` 경로를 먹어 정상 기록이 거부된다(§0.4) -- `posix=False` 또는 "경로는 따옴표나 `/`로 적는다"를 규칙에 넣는다. `-c` 값이 "캐시의 `pytest_gate.ini`"인지 gate가 무엇과 대조하는지(파일 이름만인지), `--rootdir`/`--confcutdir`의 두 토큰 형태 허용 여부를 정한다. 05 §4.4 "풀어 둔 게이트 코드"에 `pytest_gate.ini`(코드 아닌 파일)가 들어가는지도 적는다.
* **M4-08** 05 §0 "EL1은 그 밖 디렉터리의 게이트 스크립트 실행을 거부"는 '게이트 스크립트' 판별식이 없고, §17 `$PY agent-quality/check_agents.py`의 스크립트 디렉터리(`agent-quality/`)는 캐시·gate·역할 경로 어디에도 속하지 않는다. 판별식(예: 스크립트 경로가 `tools/gates/**`·캐시·gate 저장소인 것)을 정하고 §17 명령을 예외로 적거나 옮긴다.
* **M4-09** 운용 영향: 판정 트리 기본 거부로 `assets/*.log`(현재 추적 안 되는 `selftest_session6*.log` 등 7개)·`assets/*.zip`이 사용자 전용이 되어, 메인 세션·code-author가 리다이렉트로 `assets/`에 로그를 쓰면 EL1이 거부한다. 의도라면 계획 N3.12.2 문단이나 05 §4.1에 "판정 트리 안에 실행 산출물을 두지 않는다(출력은 트리 밖으로)"를 적는다(기존 `.gitignore` 예외 `tests/*.result.txt`는 test-author 행이라 괜찮다).

---

## 3. 계획 · `00-common` · 05 사이 새 모순

| # | 곳 | 내용 | 항목 |
|---|---|---|---|
| 1 | 05 §6.2 캐시 예외 "두 형태 모두 `$PY -P`" ↔ 05 §0 "스크립트 형태는 `-P`를 쓰지 않는다"·§12-0·부록 CLI | 같은 실행의 두 규칙 | M4-04 |
| 2 | 05 §4.1 "판정 트리 밖에서 import될 수 있는 것(`workspaces/*.py`·`__init__.py`, 컴파일 산출물)은 `판정 환경` 행이 덮는다" ↔ 계획 N3.12.2 행(`.pyw` 없음) ↔ Python `SOURCE_SUFFIXES` | 주장과 행의 범위 | M4-02 |
| 3 | 계획 N3.12.2 `assets/tests/tools/conftest.py` = `판정 환경`(공격 17) ↔ 같은 디렉터리 `test_*.py` = code-author `없음` | 같은 힘, 다른 권한 | M4-01 |
| 4 | 05 §10 V4 행 "중첩 … 지역 이름은 바깥 이름을 가리지 않는다" ↔ `v4.py`가 중첩 def·class **이름**을 불투명으로 넣어 예외 ↔ §10 머리 "도구 예외 = exit 2" | 설계 문장과 probe 동작 | M4-03 |
| 5 | 05 §0 "EL1은 그 밖 디렉터리의 게이트 스크립트 실행을 거부" ↔ 05 §17 `$PY agent-quality/check_agents.py` | 적용 범위 | M4-08 |
| 6 | 05 §9.2-7 `shlex.split` + `python_path` 대조 ↔ `00-common` §8.1·05 §0의 Windows 경로 표기(`C:\Python314\python.exe`) | 형식 검사의 입력 | M4-07 |

확인한 일치:
* 계획 N3.12.2 조건 `판정 트리` 정의 ↔ 05 §4.1 기본 거부 문단 ↔ §19 표 '판정 트리 기본 거부' 행 ↔ hook 판정 범위("트리 안은 늘 판정")
* 05 §0 `-P`는 `-m`·`-c`만 ↔ §9.1 `pre-receive` ↔ §17 ↔ `00-common` §10 명령(모두 스크립트 형태, `-P` 없음)
* `00-common` §8.1 red 수집 명령(`PYTHONPYCACHEPREFIX`·`-c <캐시>/pytest_gate.ini`·`--rootdir`·`--confcutdir`) ↔ 05 §12-7 ↔ §9.2-7 필수 옵션
* 계획 `tools/gates/pytest_gate.ini` 행(code-author 게이트 변경) ↔ N3.12.6 산출물 ↔ 05 §13 ①(빈 `[pytest]`)
* 계획 N4.2 V4 (2) 통과 경로 문구 ↔ 05 §10 ⑤(review34 모순 4 해소)
* `v4.py` docstring ↔ 05 §10 ④(review34 모순 5 해소)
* 05 §10 수치(FAIL 34·PASS 10·known_limit 7·UNJUDGED 12·NO-SUBJECT 2 = 65) ↔ 공격 23 ↔ `v4.out.txt`(직접 셈과 일치)
* 05 §20 "함께 덮는 개정" 목록 ↔ b60f021 계획 diff(행·문단·산출물)

---

## 4. 집계와 판정

| 구분 | 건수 | 항목 |
|---|---|---|
| M3 해결 | 4 | M3-02·06·07·09 |
| M3 해결 + 잔여(S3) | 1 | M3-04(→M4-05) |
| M3 부분 | 3 | M3-01(→M4-01·M4-02), M3-03(→M4-04·M4-08), M3-08(→M4-07) |
| M3 새 결함 도입 | 1 | M3-05(→M4-03·M4-06) |
| M3 미해결 | 0 | |
| 새 S1 | 2 | M4-01, M4-02 |
| 새 S2 | 2 | M4-03, M4-04 |
| 새 S3 | 5 | M4-05 ~ M4-09 |

판정 트리 기본 거부는 review34의 두 S1을 실측으로 닫았고(트리 안 패키지·`.pyc`, 복제본 부모 설정), 트리 안 추적 파일 220개 모두 기존 주체가 그대로 쓸 수 있다(오거부 0). 그러나 같은 부류 -- **판정 실행에 들어가는 파일을 사용자 아닌 주체가 쓴다** -- 가 두 곳에 남았다: pytest가 수집하는 test 모듈(역할 행 안, 메인 세션 포함)과 트리 밖 `workspaces`의 이름 목록(`.pyw`). 둘 다 종료 1 → 0을 실측했고, 수정은 `pytest_gate.ini` 수집 범위 고정·V1 대상 경로 고정·행 추가(또는 `workspaces` 기본 거부) 같은 규칙·설정 단위다. V4 (2)는 M3-04·M3-05의 목표 케이스를 닫았으나 중첩 def·class 이름 처리로 예외 회귀(실제 엔진 함수 17개 해당)를 들여왔다. 구조 재작성은 필요 없다.

## 5. 안전 점검 (검증 종료 시점)

아래 출력은 이 보고서 본문을 append한 직후에 잰 것이다.

```
$ git -C <repo> status --short
?? .bkit/audit/2026-08-07.jsonl
?? .bkit/audit/2026-08-10.jsonl
?? .bkit/audit/2026-08-11.jsonl
?? .bkit/audit/2026-08-12.jsonl
?? .bkit/audit/2026-08-13.jsonl
?? .bkit/audit/2026-08-14.jsonl
?? .bkit/audit/2026-08-18.jsonl
?? .bkit/audit/2026-08-19.jsonl
?? .bkit/audit/2026-08-24.jsonl
?? .bkit/audit/2026-08-27.jsonl
?? .bkit/audit/2026-08-31.jsonl
?? .bkit/audit/2026-09-03.jsonl
?? .bkit/audit/2026-09-04.jsonl
?? .bkit/audit/2026-09-07.jsonl
?? .bkit/audit/2026-09-08.jsonl
?? .bkit/audit/2026-09-09.jsonl
?? .bkit/audit/2026-09-10.jsonl
?? .bkit/audit/2026-09-14.jsonl
?? .bkit/audit/2026-09-15.jsonl
?? .bkit/audit/2026-09-16.jsonl
?? .bkit/audit/2026-09-17.jsonl
?? .bkit/audit/2026-09-18.jsonl
?? docs/03-analysis/gain-budget-gmid-sizing-function-audit/review35_05_v3_5.md
?? "skills/analog-gmid-design/assets/\354\225\204\353\202\240\353\241\234\352\267\270 \352\270\260\353\212\245\353\266\204\354\204\235\352\270\260.zip"
?? "skills/analog-gmid-design/assets/\355\232\214\353\241\234\353\217\204 \354\266\224\354\266\234\352\270\260.zip"
?? workspaces/current-reuse-telescopic-ota-report/current_reuse_telescopic_ota.report.html
?? workspaces/current-reuse-telescopic-ota-report/full_netlist_for_grammar.json
?? workspaces/current-reuse-telescopic-ota-report/smoke_run_harness_session18_save.py
$ git -C <repo> log --oneline -1
b60f021 docs(analog-gmid-design): 05-role-separation v3.5 -- review34 반영, 판정 트리 기본 거부
$ git -C <repo> diff --stat
(비어 있음 = 추적 파일 변경 없음, v4.out.txt 포함)
$ git -C <repo> config --show-origin --get core.hooksPath
file:.git/config	C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/.githooks
```

* `status --short` 28줄: 시작 시점 27줄(모두 `??`)에 이 보고서 파일 한 줄(`??`)만 더해졌다. HEAD는 b60f021, `core.hooksPath`도 그대로다.
* 실제 저장소에서 쓴 git 명령은 읽기 전용(`show`·`log`·`diff`·`status`·`ls-files`·`config --get`)뿐이다. `v4.py` 실행은 자기 `v4.out.txt`만 다시 썼다(바이트 동일, `diff --stat` 비어 있음).
* git 실험 저장소는 `%TEMP%\rv35\m2\work2\*\src`·`*\P\X-iso`(clone은 `git -C <부모 절대 경로> clone --no-hardlinks --no-local`)이고, 모든 git 호출은 `git -C <절대 경로>`로 했다. 커밋 작성자·hooksPath는 `-c` 명령행 값으로 줬다(설정 쓰기 없음).
* pytest·Python 실험(`rv35\m1`·`m2`·`v4e`)은 `%TEMP%\rv35` 안에서만 했다.

**판정: 수정 후 승인** -- S1 2(M4-01·M4-02) · S2 2(M4-03·M4-04) · S3 5(M4-05 ~ M4-09)
