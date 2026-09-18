# review34 -- `05-role-separation` design v3.4(커밋 8c5b9e3) review33 M2-01~M2-10 해소 독립 검증

* 대상: 8c5b9e3 -- 05 v3.4(§0·§4.1·§6.2·§7·§9.2-7·§10·§12-7·§13.2 17·23), 계획(N3.12.2 문단·N4.2 V4 (2)), `00-common` §8.1 red 수집, `v4_rule_probe/v4.py`·`v4.out.txt`
* 기준: `review33_05_v3_3.md` M2-01~M2-10
* 검증자: 독립 검증 agent(작성자 아님). 저장소에서는 이 보고서만 쓴다. 실측 스크립트·임시 저장소는 `C:\Users\HSLEE\AppData\Local\Temp\rv34\`(저장소 밖). git 실험은 `git -C <rv34 안 절대 경로>`, 셸 스크립트는 `set -euo pipefail`. 보고서는 Python 바이너리 append로 썼다.
* 등급: **S1** 승인 차단 / **S2** 승인 전 수정 / **S3** 경미
* 시작 시점: `git -C <repo> log --oneline -1` = 8c5b9e3, `git diff --stat` 비어 있음, `status --short` 27줄(모두 `??`, 대화 시작 스냅숏과 같음)
* 환경: Python 3.14.2, pytest 9.0.2, numpy 2.4.6, git 2.52(Windows), MSYS bash

---

## 0. 실측

### 0.1 M2-01 재측정: `-P` (`rv34\m1\`)

장난감 복제본: 루트에 `merge_gate.py`(SHADOW 출력)·`pytest.py`(SHADOW 출력), 캐시 `cache\merge_gate.py`(CACHE 출력), `skills/analog-gmid-design/assets/eng.py`(`numpy.isclose`), `assets/tests/conftest.py`(assets를 `sys.path`에 넣음), `assets/tests/test_a.py`(실패 1·통과 1). 실행은 복제본 루트, `PYTHONPATH=<캐시>`.

| 실행 | 결과 |
|---|---|
| R1 `python -m pytest -p merge_gate …` | `[SHADOW pytest.py executed]`, 종료 0 (review33 재현) |
| R2 `python -P -m pytest -p merge_gate …` | `[CACHE merge_gate loaded] …\rv34\m1\cache\merge_gate.py`, 루트 `pytest.py` 실행 안 됨, `1 failed, 1 passed`, 종료 1 |
| `python -P -c "import sys; print(sys.path[:3])"` | `[<캐시>, python314.zip, DLLs]` -- cwd 없음 |

→ `-P`는 review33이 든 두 파일(루트 `merge_gate.py`·`pytest.py`)을 막는다.

**`-P`가 깨는 것** (`rv34\sp\`):

| 실행 | 결과 |
|---|---|
| `python scr\runner.py`(같은 디렉터리 `sib.py`를 import) | `runner ok 1` |
| `python -P scr\runner.py` | **`ModuleNotFoundError: No module named 'sib'`** -- `-P`는 스크립트 실행에서 스크립트 디렉터리도 `sys.path`에 넣지 않는다 |
| `python -P -m pytest tests`(test가 같은 디렉터리 `helpers.py` import, 기본 `prepend` 모드) | `1 passed` -- pytest가 test 디렉터리를 넣는다 |
| 같은 것 `--import-mode=importlib` | `1 error` |

→ pytest 경로(V1, red 수집)는 `-P`로 깨지지 않는다(test의 엔진 import는 conftest/하네스의 `sys.path` 삽입, test 보조 모듈은 `prepend`). 그러나 05 §0이 `-P`를 강제한 **스크립트 형태**(hook 실행기, `gate-runner.py`, V3~V7 `tools/gates/*.py`, `integrity.py`)는 서로 import하면(§4.1 "`merge_gate.read_plan_tables`와 같은 함수") `-P`에서 import 실패한다 → M3-03.

**`-P`로 닫히지 않는, 역할 밖 경로가 판정 실행을 바꾸는 길** (모두 `-P -m pytest -p merge_gate`, 캐시 판 로드 확인 상태):

| # | 역할 밖 파일(쓰기 경로표 어느 행과도 겹치지 않음) | 결과 |
|---|---|---|
| V0 | 대조군 | `1 failed, 1 passed`, 종료 1 |
| V1 | `assets/numpy/__init__.py`(`isclose`가 늘 True) | `numpy from …\assets\numpy\__init__.py`, **`2 passed`, 종료 0** |
| V2 | `assets/eng/__init__.py`(코드 역할 `assets/eng.py`와 같은 이름의 패키지) | `[FAKE eng package shadows eng.py]`, **`2 passed`, 종료 0** -- 같은 디렉터리에서 패키지가 모듈보다 먼저 찾아진다 |
| V2b | `assets/eng/`(`__init__.py` 없는 namespace 디렉터리) | 종료 1(영향 없음) |
| V3 | 커밋된 `assets/__pycache__/eng.cpython-314.pyc`(`py_compile` `UNCHECKED_HASH`, `git add -f`, 트레일러 없는 커밋 → `git clone --no-hardlinks --no-local` 격리 복제본) (`rv34\m3\`) | `[FAKE eng from unchecked-hash pyc]`, **`2 passed`, 종료 0**. 같은 복제본에서 `__pycache__`를 지우면 종료 1 |

`assets/*.py` 행은 한 조각만 맞으므로 `assets/<이름>/__init__.py`·`assets/__pycache__/*.pyc`는 역할 밖이다(EL1 `overlaps_any` 거짓, EL3·EL4 역할 밖 커밋 통과 -- review33 §0.4와 같은 조건). `.gitignore`의 `__pycache__/`·`*.pyc`는 `git add -f`로 넘고, EL1 명령 표에는 `add -f` 규칙이 없다. 00-common §10.2 도구는 `<worktree>/workspaces`도 `sys.path` 앞에 두므로 역할 밖 `workspaces/<서드파티 이름>.py`도 같은 부류다(미실측, V1과 같은 기제). 확장 모듈(`assets/<엔진 이름>.pyd`)은 FileFinder가 `.py`보다 먼저 보는 접미사라 같은 부류로 추정한다(미실측).

### 0.2 격리 복제본 **바깥**의 pytest 설정 (`rv34\tp\`)

복제본 `tp\X-iso`, 실행은 00-common §8.1 형태(`-P -m pytest -p merge_gate --rootdir=. skills`).

| 복제본의 부모 디렉터리(`tp\`)에 둔 파일 | 결과 |
|---|---|
| 없음(대조군) | `1 failed, 1 passed`, 종료 1 |
| `pytest.ini`(`addopts = --deselect …::test_a`) | **`configfile: ..\pytest.ini`**, `1 passed, 1 deselected`, **종료 0** |
| 빈 `pytest.ini` + `conftest.py`(`test_a`를 수집에서 뺌) | **`1 passed`, 종료 0** -- ini가 부모에 있으면 `confcutdir`가 그 디렉터리가 되어 부모 `conftest.py`까지 읽는다 |
| `conftest.py`만 | 종료 1(`confcutdir` = rootdir이라 안 읽음) |

`--rootdir`를 줘도 pytest는 인자 경로에서 위로 설정 파일을 찾는다. 저장소 루트에는 추적되는 pytest 설정이 없으므로 탐색은 복제본 밖으로 나간다. 격리 복제본은 `<TEMP>/<id>-iso`(§12-7)이고, `$TEMP`는 "어느 worktree에도 속하지 않는 경로"라 `overlaps_any` 거짓(§4.1) -- 메인 세션이 `%TEMP%\pytest.ini`를 도구 호출 하나로 쓸 수 있고 커밋도 필요 없다. §3.3 무결성 대조 대상도 아니다 → M3-02.

### 0.3 M2-02 casefold (`rv34\uni\`, `rv34\ntfs\`)

| 입력 | NTFS에서 `pytest.ini`/`setup.cfg`로 열림 | casefold glob 대조 |
|---|---|---|
| `Pytest.ini`·`PYTEST.INI`(review33) | 열림 | **맞음**(v3.4) |
| `pytest.ını`(U+0131 점 없는 i) | 안 열림 | 안 맞음(일치 -- 문제없음) |
| `pytest.İNI`(U+0130) | 안 열림 | 안 맞음 |
| `ſetup.cfg`(U+017F) | 안 열림 | 맞음(과잉 보호, 무해) |
| 추적 경로 `PYTEST~1.INI`(clone 결과 그 이름 그대로) | `pytest.ini`로 안 열림 | -- |
| `pytest.ini.`·`pytest.ini `(끝 점·공백) | git이 `Invalid path`로 index 추가 거부 | -- |

pytest는 정확한 이름(`(base / name).is_file()`)으로만 찾으므로 8.3 짧은 이름은 읽히지 않는다(`pytest.ini`·`conftest.py`는 그 자체가 8.3 형식이라 다른 긴 이름이 그 짧은 이름을 받지 않는다). **대소문자 변형은 닫혔고, 유니코드·8.3·끝 점 변형으로 새는 길은 찾지 못했다.**

### 0.4 V4 (2) (`v4.py` 저장소 루트 실행, 추가 케이스는 `rv34\v4d\`가 `v4.py`를 import -- v4.py 수정 없음)

**재현**: 저장소 루트에서 `python docs/03-analysis/.../v4_rule_probe/v4.py` → 종료 0. `v4.out.txt` 60번째 줄이 `케이스 59개, 기대 불일치 0개`이고 그 뒤에 R-05 네 조합 줄 4개가 온다(파일 마지막 줄은 아니다 -- 요약 줄은 자체 대조 59케이스 뒤, 조합 줄 앞). 실행 뒤 `git -C <repo> diff --stat` 비어 있음(`v4.out.txt` 바이트 동일). 네 조합 출력은 4b71067 판과 같다.

**review33 추가 케이스 재실행**(`rv33\v4c\v4c.py`를 출력 경로만 바꿔 복사, `rv34\v4d\v4c_rerun.out.txt`): review32 v4b 18개는 v3.3과 같은 결과(회귀 없음). review33 새 케이스:

| 케이스 | v3.3 | v3.4 | 판정 |
|---|---|---|---|
| N1~N5 블록·루프로 받은 피검 결과 | NO-SUBJECT | **UNJUDGED** | 해결 |
| N6 `match`, N8 `except*` | 출력 없음 | **FAIL** | 해결 |
| N7 test 안 중첩 함수 | 출력 없음 | **UNJUDGED** | 해결 |
| N9 쓰지 않는 인자로 제외 맞추기 | PASS | **FAIL** | 해결 |
| N11·N12 쌍 없는 피검 없는 판정 | UNJUDGED | **NO-SUBJECT** | 해결 |
| P3 피검 안 중첩 함수 return | FAIL | **PASS** | 해결 |
| C1 `1e400*1.0` | 예외 | PASS(`*1.0` 제거 뒤 잎 하나 -- 단위 이득 규칙과 일관) | 해결 |
| C8 `async def` | 예외 | **FAIL** | 해결 |
| N10·N13·N14·P1·P2·P4·P5·C2~C7·C9·C10 | -- | v3.3과 같음(C10 0.21 s) | -- |

**새 적대 케이스**(`v4d.out.txt`, 27개):

| 입력 | 결과 | 목적상 기대 | 분류 |
|---|---|---|---|
| D1 `rs = []; rs.append(gain(…))` 뒤 `assert rs[0] == approx(2e-3*50e3)` | **NO-SUBJECT** | FAIL/UNJUDGED | 이름 대입이 아닌 수신(메서드 호출)은 피검 불투명이 되지 않는다 |
| D2 `d['a'] = gain(…)` 뒤 `assert d['a'] == …` | **NO-SUBJECT** | 같음 | 첨자 대상 대입 |
| D3 `ns.r = gain(…)` 뒤 `assert ns.r == …` | **NO-SUBJECT** | 같음 | 속성 대상 대입 |
| D4 `for g in …: out[g] = gain(g, 50e3)` → `for g, r in out.items(): assert r == approx(g * 50e3)` (표 구동) | **NO-SUBJECT** | 같음 | N1의 사전판 |
| D5 `rs = [gain(g, …) for g in …]; assert rs[0] == …` | UNJUDGED | 같음 | 기대대로 |
| D6 test 안 중첩 `def helper(x): e = x` 가 바깥 `e = 2e-3*50e3`를 가림 | **PASS** | FAIL | 중첩 def의 지역 이름까지 바깥 env에서 불투명 처리(4b71067에도 있던 동작) |
| D7 `print([e for e in (1,)])`가 바깥 `e`를 가림 | **PASS** | FAIL | comprehension 변수(파이썬 3에서는 새지 않음)도 같은 처리(기존 동작) |
| D10 `for …: e = 2e-3*50e3` 뒤 루프 밖 assert, D11 `try: e = …` 뒤 밖 assert | **PASS** | FAIL/UNJUDGED | 블록 안에서 만든 **기대식**은 불투명 이름(§10 설계대로) -- F 목록에 없는 놓침 |
| D8·D9·D12~D17·D19~D22·D26 | FAIL / 기대대로 | | `await`·`async with/for`·`yield`·`match` guard·`while/else`·`-inf`·`nan`·`inf*0`·매개변수 재대입 모두 예외 없음 |
| D18 중첩 class 안 assert, D27 클로저 반환 | UNJUDGED | UNJUDGED | 기대대로 |
| D23·D24 통과 경로(인자가 식) | PASS | PASS | 쓰인 매개변수 기준 제외가 기존 FP1~FP3 성격을 지킨다 |
| D25 `return inner(x)`(피검 안 중첩 함수 호출) | PASS | FAIL/UNJUDGED | F3(모듈 밖 호출) 성격, 설계 범위 안 |

→ M2-03이 든 N1~N8은 모두 닫혔고 예외·새 거짓 양성은 찾지 못했다. **피검 결과를 이름이 아닌 대상(첨자·속성·메서드 호출)으로 받은 재서술은 여전히 `NO-SUBJECT`**(D1~D4)로 V4 (2) 대상 밖이고 F 목록에도 없다 → M3-04. D6·D7·D10·D11은 4b71067부터 있던 동작이고 PASS(=독립의 증거 아님)라 S3로 둔다(M3-05).

### 0.5 MSYS의 `PYTHONPATH` 변환

`PYTHONPATH=/c/tmp/a:/c/tmp/b python -c …`(MSYS bash) → 자식이 받은 값 `'C:\\tmp\\a;C:\\tmp\\b'`, `sys.path[:2] = ['C:\\tmp\\a', 'C:\\tmp\\b']`. MSYS는 POSIX 형식 경로 목록의 `:`를 `;`로 바꿔 넘긴다. §6.2 "`:`는 구분자로 보지 않는다"는 hook이 명령 문자열을 자를 때의 규칙으로는 fail-closed(그 형태는 첫 원소가 캐시가 아니라 거부)지만 "Windows Python이 `;`만 본다"는 설명은 MSYS 경유에서는 사실과 다르다(S3, M3-09).

---

## 1. M2-01~M2-10 판정

| ID | 등급(33) | 판정 | 근거 |
|---|---|---|---|
| M2-01 | S1 | **부분 + 새 결함 도입** | 루트 `merge_gate.py`·`pytest.py` 가림은 `-P`로 닫혔다(§0.1 R2). 그러나 (1) 같은 부류 -- 역할 밖 경로가 판정 실행을 바꿈 -- 가 `-P`와 무관한 import 해석 경로(`assets/<이름>/__init__.py`, 커밋된 unchecked-hash `.pyc`)와 복제본 밖 설정 파일(`%TEMP%\pytest.ini`)로 남는다(§0.1 V1~V3, §0.2 → M3-01·M3-02, S1). (2) `-P`를 스크립트 형태까지 일괄 강제해 서로 import하는 게이트 스크립트가 깨지고, §9.1 `pre-receive`·§17 명령·00-common §10 도구는 `-P` 없이 남아 문서끼리 어긋난다(→ M3-03, S2). V1 명령 형태 확인(§9.2-7)은 auditor가 적은 문자열의 형식 검사일 뿐이다(M3-08) |
| M2-02 | S1 | **해결** | §4.1·계획 N3.12.2가 모든 행을 casefold 대조, casefold 충돌 경로 거부, 공격 17에 변형 셋. 유니코드(ı·İ·ſ)·8.3·끝 점/공백 변형으로 새는 길 없음(§0.3) |
| M2-03 | S2 | **부분** | N1~N8 모두 해결(§0.4). 이름이 아닌 대상(첨자·속성·`append`)으로 받은 피검 결과는 `NO-SUBJECT`(D1~D4) → M3-04 |
| M2-04 | S3 | **해결** | N11·N12 `NO-SUBJECT`, §10 정의 "쌍을 못 만든 것 포함" |
| M2-05 | S3 | **해결** | inf·`-inf`·nan·`inf*0` 예외 없음, `async def`·`await`·`async with/for` 판정. §10 "도구 자신의 예외는 exit 2(auditor는 FAIL)" |
| M2-06 | S3 | **해결(05·probe)** | N9 FAIL, P3 PASS, D22~D27 새 FP 없음. 계획 N4.2의 제외 문구는 옛 표현 그대로(M3-06, S3) |
| M2-07 | S3 | **해결** | 05 §10 ④에서 "float 값" 삭제. `v4.py` 머리 docstring(6줄)에는 "숫자는 float"가 남았다(M3-07, S3) |
| M2-08 | S3 | **해결** | §7(파일 232줄) "equivalence(test 커밋 0개)에서는 `role/test/<id>` 끝 = `old`이고 `old`가 역할 밖 병합일 수 있다 -- 두 범위가 같아 결과가 같다" |
| M2-09 | S3 | **해결(문구)** | `;`만 구분자, 두 형태 명시. MSYS 변환 설명은 M3-09(S3) |
| M2-10 | S3 | **해결** | 계획 N4.2 V4 (2) 괄호가 05 §10 ④(부호 밖으로·합 위 분배·유리수·다중집합·나눗셈 역수·숫자끼리 접지 않음)와 같다 |

집계: **해결 7**(M2-02·04·05·06·07·08·10) + **해결(문구) 1**(M2-09) / **부분 2**(M2-01·M2-03) / **미해결 0** / **새 결함 도입 1**(M2-01 → M3-03).

---

## 2. 새 결함

### M3-01 [S1] `-P` 뒤에도 역할 밖 경로가 import 해석으로 엔진·서드파티 모듈을 바꾼다 (M2-01 부류 잔여)
* **위치**: 계획 N3.12.2 쓰기 경로표(`skills/analog-gmid-design/assets/*.py`는 한 조각만), 05 §4.1 `overlaps_any`, §8 EL3·EL4의 역할 밖 커밋 허용, §6.2 명령 표(`git add -f` 규칙 없음), 00-common §10.2(`sys.path` 앞에 assets·workspaces), §12-7 격리 복제본.
* **근거**: §0.1 V1(`assets/numpy/__init__.py` → 종료 1→0), V2(`assets/eng/__init__.py`가 코드 역할 `assets/eng.py`를 대신 → 1→0), V3(트레일러 없이 커밋한 unchecked-hash `.pyc`가 격리 복제본에서 엔진 코드를 대신 → 1→0). 셋 다 `-P`·캐시 판 플러그인 로드 상태에서 재현했다. 계획 N3.12.0 '막는다' 행의 "역할 밖 편집(엔진 소스를 메인 세션이 쓰기 등)"·"판정 환경 조작"이 막히지 않고 드러나지도 않는다.
* **수정 방향**: (1) 판정 때 `sys.path`에 오르는 디렉터리(assets, `assets/tests`, workspaces, 캐시) 아래에서 **Python이 import할 수 있는 모든 것**(`*.py`, 패키지 `*/__init__.py`, `*.pyc`·`__pycache__/**`, `*.pyd`·`*.so`)을 역할 경로나 `판정 환경` 행으로 덮는다(예: `assets/**/*.py`에서 tests 제외 행을 code 역할로, `**/__pycache__/**`·`**/*.pyc`·`**/*.pyd`를 `판정 환경`으로). (2) EL3·EL4는 추적되는 `.pyc`·`__pycache__` 경로를 거부한다. (3) 격리 복제본 실행에 `PYTHONPYCACHEPREFIX=<빈 임시 디렉터리>`를 둬 커밋된 `__pycache__`를 읽지 않게 한다. 공격 17에 V1~V3을 넣는다.

### M3-02 [S1] 격리 복제본 **바깥**(`%TEMP%`)의 `pytest.ini`·`conftest.py`를 V1·red 수집이 읽는다
* **위치**: 00-common §8.1 red 수집 명령, 05 §12-7(`<TEMP>/<id>-iso`), §4.1 "어느 worktree에도 속하지 않는 경로는 `overlaps_any` 거짓", 공격 17.
* **근거**: §0.2. 부모 디렉터리의 `pytest.ini`가 `configfile`이 되어 실패 test가 빠지고(종료 1→0), ini가 있으면 부모 `conftest.py`도 로드된다. 쓰는 데 커밋도 역할 경로도 필요 없다.
* **수정 방향**: 판정 실행을 `-c <복제본 루트>/<추적되는 설정 파일>`(또는 `--config-file`)과 `--confcutdir=<복제본 루트>`로 고정하고, 저장소 루트에 `사용자` 소유 설정 파일을 추적해 두며, 판정 기록에 pytest 머리의 `rootdir:`·`configfile:` 줄을 남겨 auditor와 EL4 형식 검사가 그 경로가 복제본 안인지 대조한다. 공격 17에 '복제본 부모의 `pytest.ini`·`conftest.py`'를 넣는다.

### M3-03 [S2] `-P` 일괄 강제가 스크립트 형태 게이트 코드의 상호 import를 깨고, 문서 안에서 적용이 어긋난다 (M2-01 수정이 도입)
* **위치**: 05 §0(모든 Python 실행 `$PY -P`, hook 실행기·`gate-runner.py` 포함), §4.1("`merge_gate.read_plan_tables`와 같은 함수"), §6.2 `$PY <캐시>/<이름>.py` 형태, §9.1 `pre-receive`(`exec "C:/Python314/python.exe" "<gate_path>/gate-runner.py"` -- `-P` 없음), §17 명령(`integrity.py`·`run_all.py`), 00-common §10(`$PY …/measure_search_perf.py`·`noop_proof.py` -- `-P` 없음).
* **근거**: §0.1 `-P` 스크립트 실행에서 같은 디렉터리 모듈 import가 `ModuleNotFoundError`. 문서대로 구현하면 EL1은 모든 도구 호출을 exit 2로 막고(fail-closed), 반대로 §9.1대로면 §0과 모순이다. 스크립트 형태의 위험(스크립트 디렉터리)은 그 디렉터리가 역할 경로인 한 없으므로 `-P`의 대상은 `-m`·`-c` 형태다.
* **수정 방향**: 규칙을 "`-m`·`-c` 실행은 `-P`, 스크립트 실행은 스크립트 디렉터리가 역할 경로·캐시·gate 저장소일 때만 허용하고 게이트 스크립트는 자기 디렉터리를 명시적으로 `sys.path`에 넣는다(또는 `PYTHONPATH=<캐시>`)"로 좁히고, §9.1·§17·00-common §10의 명령을 그 규칙과 맞춘다.

### M3-04 [S2] 피검 결과를 이름이 아닌 대상(첨자·속성·메서드 호출)으로 받은 재서술이 `NO-SUBJECT` (M2-03 잔여)
* **위치**: 05 §10 ①(피검 불투명 규칙은 '이름'에만), `v4.py` `_assert_pairs`의 이름 대입 외 분기(`mark`는 `Store` 이름만 본다).
* **근거**: §0.4 D1~D4. 표 구동 test의 흔한 모양(`out[g] = f(g)` → `for g, r in out.items(): assert r == approx(식)`)이 V4 (2) 대상 밖이 되고 F1~F5에도 없어 auditor 대조 목록에도 오르지 않는다 -- M-04·M2-03과 같은 '목록 밖으로 빠짐'.
* **수정 방향**: 대입 대상이 `Subscript`·`Attribute`이거나 식 문장이 `<이름>.<메서드>(…피검…)`이면 그 **밑 이름**을 피검 불투명으로 둔다(값·인자에 피검 호출이나 피검 불투명 이름이 있을 때). 공격 23에 D1~D4를 넣는다.

### S3
* **M3-05** 블록 안에서 만든 **기대식**(D10·D11), 중첩 `def`·comprehension의 지역 이름이 바깥 기대식 이름을 가리는 경우(D6·D7)는 PASS다. 앞의 것은 §10 설계대로지만 F 목록에 없고, 뒤의 둘은 `_assigned_names`가 중첩 범위까지 걷는 탓이다. F 목록에 적거나 중첩 범위(`FunctionDef`·`Lambda`·comprehension)를 건너뛰게 한다.
* **M3-06** 계획 N4.2 V4 (2)의 통과 경로 제외 "(정규형이 잎 하나이거나 결합된 인자 식 하나와 같다)"가 05 §10 ⑤ "그 return 식에 나오는 매개변수에 결합된 인자 식"(M2-06)보다 넓다. 계획 문구를 맞춘다.
* **M3-07** `v4.py` 머리 docstring(6줄) "숫자는 float"가 M2-07 뒤의 정의와 다르다. 또 자체 대조는 케이스마다 **첫 판정 문장**만 본다(e329283 둘째 assert(15줄)의 PASS는 대조 밖) -- §10 "59개가 모두 기대와 같다"의 범위를 그렇게 적는다.
* **M3-08** §9.2-7 "V1 원소가 `$PY -P -m pytest`로 시작"은 (가) `$PY`를 글자 그대로인지 펼친 경로인지 정하지 않았고, (나) red 수집처럼 `PYTHONPATH=<캐시> $PY -P …` 앞붙임 형태면 거부되며, (다) auditor가 적은 문자열의 형식 검사일 뿐 실제 실행을 증명하지 않는다(§9.2-6과 같은 성격이라고 적는다).
* **M3-09** §6.2 "`:`는 드라이브 콜론과 겹쳐 구분자로 보지 않는다"는 hook 파서 규칙으로는 안전 쪽이지만, MSYS bash는 `/c/…:/c/…`를 `;` 목록으로 바꿔 넘긴다(§0.5). 설명을 "hook은 `;`만 자른다(POSIX `:` 목록은 첫 원소가 캐시로 보이지 않아 거부)"로 고친다. 캐시 경로의 MSYS 형식(`/c/Users/…`)·`\`·`/` 표기를 같은 경로로 보는지도 적는다.

---

## 3. 계획 · `00-common` · 05 사이 새 모순

| # | 곳 | 내용 | 항목 |
|---|---|---|---|
| 1 | 05 §0 "hook 실행기·`gate-runner.py`도 `$PY -P`" ↔ 05 §9.1 `pre-receive`의 `exec python gate-runner.py`(`-P` 없음) | 같은 실행의 두 형태 | M3-03 |
| 2 | 05 §0 "V1~V10의 pytest·도구 모두 `-P`" ↔ 00-common §10 `$PY …/measure_search_perf.py`·`noop_proof.py`, 05 §17 `$PY tools/gates/integrity.py`·`run_all.py` | 적용 범위 | M3-03 |
| 3 | 05 §0·§4.1 "`-P`" + "`merge_gate.read_plan_tables`와 같은 함수"(게이트 스크립트 상호 import) ↔ Python `-P` 동작(스크립트 디렉터리 제외) | 실행 전제 | M3-03 |
| 4 | 계획 N4.2 V4 (2) 통과 경로 제외 ↔ 05 §10 ⑤ | 제외 범위 | M3-06 |
| 5 | 05 §10 ④ 숫자 = 유리수 ↔ `v4.py` docstring "숫자는 float" | 문구 | M3-07 |

확인한 일치:
* 계획 N3.12.2 문단(대소문자 무시) ↔ 05 §4.1 casefold ↔ 공격 17 변형 셋
* 00-common §8.1 red 수집 `$PY -P -m pytest` ↔ 05 §12-7 ↔ §9.2-7 V1 형태
* 계획 N4.2 V4 (2) 정규화 괄호 ↔ 05 §10 ④(review33 모순 5 해소)
* 05 §10 출력 정의(`UNJUDGED`·`NO-SUBJECT`) ↔ `v4.py` 동작(review33 모순 2 해소, D1~D4는 정의대로 `NO-SUBJECT`라 모순이 아니라 범위 결함 M3-04)
* 05 §7 ↔ §9.2-4(review33 모순 4 해소)
* 05 §10 수치(FAIL 32·PASS 10·known_limit 6·UNJUDGED 9·NO-SUBJECT 2 = 59) ↔ `v4.out.txt`(직접 셈과 일치)

---

## 4. 집계와 판정

| 구분 | 건수 | 항목 |
|---|---|---|
| M2 해결 | 8 | M2-02·04·05·06·07·08·09(문구)·10 |
| M2 부분 | 2 | M2-01(→M3-01·M3-02), M2-03(→M3-04) |
| M2 새 결함 도입 | 1 | M2-01(→M3-03) |
| M2 미해결 | 0 | |
| 새 S1 | 2 | M3-01, M3-02 |
| 새 S2 | 2 | M3-03, M3-04 |
| 새 S3 | 5 | M3-05 ~ M3-09 |

review33의 두 S1 중 대소문자 변형(M2-02)은 실측으로 닫혔고, `-m`의 cwd 가림도 `-P`로 닫혔다. V4 (2)는 N1~N8을 모두 닫았고 새 거짓 양성·예외는 없었다. 그러나 M2-01이 대표한 부류 -- **역할 밖 경로(또는 저장소 밖 경로)가 판정 실행을 바꿈** -- 는 import 해석(패키지·`.pyc`)과 pytest 설정 탐색(복제본 부모)으로 남아 둘 다 종료 코드 1→0을 실측했다. 수정은 경로표 행 추가, 커밋된 바이트코드 거부, pytest 설정 고정(`-c`·`--confcutdir`) 같은 규칙·명령 단위라 구조 재작성은 필요 없다.

## 5. 안전 점검 (검증 종료 시점)

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
?? "skills/analog-gmid-design/assets/\354\225\204\353\202\240\353\241\234\352\267\270 \352\270\260\353\212\245\353\266\204\354\204\235\352\270\260.zip"
?? "skills/analog-gmid-design/assets/\355\232\214\353\241\234\353\217\204 \354\266\224\354\266\234\352\270\260.zip"
?? workspaces/current-reuse-telescopic-ota-report/current_reuse_telescopic_ota.report.html
?? workspaces/current-reuse-telescopic-ota-report/full_netlist_for_grammar.json
?? workspaces/current-reuse-telescopic-ota-report/smoke_run_harness_session18_save.py
$ git -C <repo> log --oneline -1
8c5b9e3 docs(analog-gmid-design): 05-role-separation v3.4 -- review33 반영
$ git -C <repo> diff --stat
(비어 있음 = 추적 파일 변경 없음, v4.out.txt 포함)
$ git -C <repo> config --show-origin --get core.hooksPath
file:.git/config	C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/.githooks
```

위 출력은 이 보고서 파일을 쓰기 직전에 잰 것이다. 시작 시점과 같고, 이 보고서 파일(`review34_05_v3_4.md`, 새 `??` 한 줄)만 더해진다. HEAD는 8c5b9e3, `core.hooksPath`도 그대로다.
* 실제 저장소에서 쓴 git 명령은 읽기 전용(`show`·`log`·`diff`·`status`·`check-ignore`·`config --get`)뿐이다. `v4.py` 실행은 자기 `v4.out.txt`만 다시 썼다(바이트 동일, `diff --stat` 비어 있음).
* git 실험 저장소는 `%TEMP%\rv34\m3\repo`·`m3\iso`(pyc)와 `%TEMP%\rv34\ntfs\repo`·`ntfs\iso`(경로 이름)다. 실험 저장소 안의 git 명령은 `git -C <절대 경로>`로 했고, 예외로 `git clone` 두 번은 `-C` 없이 원본·대상 모두 `%TEMP%\rv34` 안 절대 경로로 불렀다(cwd와 무관). 커밋 작성자는 `-c user.name/user.email` 명령행 값으로 줬다(설정 쓰기 없음).
* pytest·Python 실험(`rv34\m1`·`sp`·`tp`·`uni`)은 git 없이 `%TEMP%\rv34` 안에서만 했다.

**판정: 수정 후 승인** -- S1 2(M3-01·M3-02) · S2 2(M3-03·M3-04) · S3 5(M3-05 ~ M3-09)
