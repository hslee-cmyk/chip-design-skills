# review33 -- `05-role-separation` design v3.3(커밋 4b71067) review32 M-01~M-13 해소 독립 검증

* 대상: 4b71067 -- 05 v3.3, 계획(N3.12.3 7·N3.12.4 EL4·N4.2 V4 (2)·N4.3 공격 10b·19·23·N7.2 U-38), `v4_rule_probe/v4.py`·`v4.out.txt`
* 기준: `review32_05_v3_2.md` M-01~M-13
* 검증자: 독립 검증 agent(작성자 아님). 저장소에서는 이 보고서만 쓴다. 실측 스크립트·임시 저장소는 `C:\Users\HSLEE\AppData\Local\Temp\rv33\`(저장소 밖). 모든 git 실험은 `git -C <rv33 안 절대 경로>`, 셸 스크립트는 `set -euo pipefail`, Python 모델은 저장소 경로 가드 assert. 보고서 덧붙이기는 Python 바이너리 append(`rv33\rep\app.py`)
* 등급: **S1** 승인 차단 / **S2** 승인 전 수정 / **S3** 경미
* 시작 시점: `git -C <repo> log --oneline -1` = 4b71067, `git diff --stat` 비어 있음, `status --short` 27줄(모두 `??`, 대화 시작 스냅숏과 같음)

---

## 0. 실측 (git 2.52.0.windows.1, Python 3.14.2)

### 0.1 M-01·M-07 역할 밖 병합 (`rv33\el4\run33.py` → `results33.txt`; review32 `model.py`를 복사해 쓰고 병합 판정만 v3.3 글자대로 바꿈)

**모델한 것**: EL4 §9.2-3 "병합 커밋은 4의 M이거나 역할 밖 병합(부모 정확히 둘, `merge-base --is-ancestor <old> <병합^1>`, 병합 트리와 첫 부모 트리가 `overlaps_any` 경로 전부에서 같다)", §9.2-4(역할 커밋 없는 push는 3으로만, 역할 커밋이 있는 push에 역할 밖 병합 불가), EL3 §8.2-3 (라)(1)~(3)(`HEAD`가 `gate/master`와 같거나 그 후손). 장난감 경로표는 review32와 같다(역할 경로 `tests/`·`src/`·`.ai/`·`docs/`·`tools/gates/`, 역할 밖 `other/`).

| 케이스 | 기대 | EL4 | EL3 (라) |
|---|---|---|---|
| O1 역할 밖 병합(두 쪽 `other/`만, 트레일러 없음) | 통과 | 통과 | 통과 |
| L1 M^1 = old, M^2 = 오래된 조상에서 갈라진 RTL 커밋 | 통과 | 통과 | 통과 |
| L2 M^1 = old 위 트레일러 없는 역할 밖 커밋, M^2 = 조상 갈래 | 통과 | 통과 | 통과 |
| X4 조상 갈래 커밋 + old로 병합 | 통과 | 통과 | -- |
| O2 A19b 원형 | 거부 | 거부 | 차단 |
| **O3** 부모를 뒤집은 `-s ours`(M^1 = 조상 위 역할 밖 커밋) | 거부 | **거부** | **차단**(HEAD가 gate/master의 후손 아님) |
| **O3b** M^1 = 조상 자체, 새 커밋은 병합 하나 | 거부 | **거부** | **차단** |
| **O5** octopus(부모 3) | 거부 | **거부** | **차단**(부모 수) |
| O6 둘째 부모에 트레일러 없는 `tests/` 변경 | 거부 | 거부 | -- |
| X1 정상 모양 병합의 둘째 부모에 되돌림 병합(O3b)을 넣음 | 거부 | 거부(둘째 부모 쪽 병합도 `old..new`에 들어 판정됨) | -- |
| X2 M^1 = old, M^2 = 되돌림 병합, `-s ours`(트리 = old) | 거부 | 거부(같은 이유) | -- |

**우회 탐색**: EL4가 받아들이는 push에서 `new`의 첫 부모 사슬은 늘 `old`의 후손 안에 머문다 -- 병합 아닌 커밋은 부모가 하나라 `new`가 `old`의 후손이면 그 부모도 후손이고, 병합은 이번 조건으로 첫 부모가 후손이다. 그 사슬의 각 단계는 병합 아닌 커밋이면 커밋별 트레일러·경로 검사를, 역할 밖 병합이면 '역할 경로가 첫 부모와 같음'을 거치므로 `new`의 역할 경로 트리는 `old`의 역할 경로 트리에 커밋별로 허가된 변경만 더한 것이다. 둘째 부모 쪽 역사(조상에서 갈라진 커밋, 되돌림 병합 포함)는 트리에 들어오지 못하고, `old..new`에 들어오는 한 그 안의 병합도 같은 규칙으로 거부된다(X1·X2). 역할 밖 병합이나 역할 밖 커밋을 **이어 붙여** 역할 경로를 되돌리는 길은 git 모양 수준에서 찾지 못했다. 다만 역할 밖 경로 **자체가 판정을 바꾸는** 두 경로를 찾았다(§0.4, 새 결함 M2-01·M2-02).

**hook 실측**(`rv33\el4\hookrepo`): `git merge --no-ff`와 `git merge -s ours` 모두 `pre-commit`은 돌지 않고 `pre-merge-commit`과 `commit-msg`가 돌며, `commit-msg` 시점에 `MERGE_HEAD`가 있다 -- §8.2-3이 병합 판정을 commit-msg에 둔 것과 맞다.

### 0.2 M-02·M-03·M-04 V4 (2) (`v4.py`는 저장소 루트에서 실행, 추가 케이스는 `rv33\v4c\v4c.py`가 `v4.py`를 import → `v4c.out.txt`)

**재현**: 저장소 루트에서 `python docs/03-analysis/.../v4_rule_probe/v4.py` 실행 뒤 `git -C <repo> diff --stat`가 비었다(`v4.out.txt` 바이트 그대로). 판정 줄 45개(e329283 조합 4줄 제외)를 기대 열과 대조해 **모두 일치**: FAIL 27(e329283 7 + 합성 20), PASS 9, known_limit 6(PASS 5 = e329283 F1·F2·F3 셋 + 계수 둘, `UNJUDGED` 1 = 튜플 풀기), `UNJUDGED` 2(`**kw`, 식 안의 피검 호출), `NO-SUBJECT` 1 -- §10·공격 23·history 문장과 같다. probe에는 기대와 실제를 자동 대조하는 코드가 없어(출력에 둘을 나란히 적을 뿐) 대조는 이 검증에서 했다.

**review32 추가 케이스(`rv32\v4b`의 케이스 목록을 그대로 읽어 새 `v4.py`로)**: 18개 모두 목적상 기대와 같다 -- FP1~FP3(식 인자 통과 경로) PASS, FP4·FP5·FP5b(손 계산 계수) PASS로 일관, FN1·FN2(교환 재배열) FAIL로 순서 무관, FN3 `-(b+c)` FAIL, FN4~FN6(`for`·`with`·`assert_allclose`) FAIL, FN7(test 쪽 `*=`) FAIL, FN8(식 안의 피검 호출) `UNJUDGED`(설계 정의대로), FN9 `UNJUDGED`, 대조군 FAIL.

**새 정규화를 깨는 입력**(`v4c.out.txt`):

| 입력 | 결과 | 목적상 기대 | 분류 |
|---|---|---|---|
| N1 `rs = [gain(g, 50e3) for g in gms]` → `for r, g in zip(rs, gms): assert r == approx(g * 50e3)` (표 구동 test) | **NO-SUBJECT** | FAIL 또는 `UNJUDGED` | 재서술이 'V4 (2) 대상 아님'으로 빠진다. 루프 대상 이름은 그냥 불투명 이름(`<opaque:…>`)이 되고 피검 불투명(`<opaque-subject:…>`)이 되지 않는다 |
| N2 `for r in [gain(2e-3, 50e3)]: assert r == approx(2e-3 * 50e3)` | **NO-SUBJECT** | 같음 | 같음 |
| N3 `if …: r = gain(2e-3, 50e3)` 뒤(블록 밖) `assert r == approx(2e-3 * 50e3)` | **NO-SUBJECT** | 같음 | 블록 안에서 대입된 이름은 피검 호출을 담아도 불투명 이름 |
| N4 `with warnings.catch_warnings(): r = gain(…)` 뒤 assert | **NO-SUBJECT** | 같음 | 같음(수치 test에서 흔한 모양) |
| N5 `try: r = gain(…) except ValueError: r = 0.0` 뒤 assert | **NO-SUBJECT** | 같음 | 같음 |
| N6 `match` 문 안의 assert | **출력 없음**(`[]`) | FAIL 또는 `UNJUDGED` | 재귀 대상에 `ast.Match` 없음 |
| N7 test 안 중첩 함수 `def check(g): assert gain(g, 50e3) == approx(g * 50e3)` | **출력 없음** | 같음 | 중첩 `def`는 걷지 않는다 |
| N8 `try: assert … except* ValueError:` | **출력 없음** | 같음 | `ast.TryStar` 없음 |
| N9 쓰지 않는 선택 인자에 기대식을 넣음 `gain(2e-3, 50e3, note=2e-3 * 50e3) == approx(2e-3 * 50e3)` | PASS | FAIL | 통과 경로 제외가 '어느 결합 인자와든 같으면'이라 인자 하나로 제외를 맞출 수 있다(의도적 형태, S3) |
| N11 `assert len(x) > 0`(피검 없음), N12 `self.assertTrue(ok)` | **UNJUDGED** | NO-SUBJECT | 비교 쌍을 못 만들면 피검 유무와 무관하게 `UNJUDGED` -- §10 정의("피검 호출이 걸렸는데 판정하지 못함")와 다름. 과보고라 안전 쪽이지만 auditor 대조 목록이 부푼다 |
| P3 피검 안 중첩 함수의 return(`def inner(y): return y * k`)이 바깥 함수의 return 변형으로 섞임 | FAIL | PASS | `_walk_body`가 중첩 `def`의 Return까지 모은다(거짓 양성 가능, S3) |
| C1 `1e400`(inf) 리터럴 | **예외** `ValueError: Invalid literal for Fraction: 'inf'` | 판정 | `Fraction(repr(float))` |
| C8 `async def test_…` | **예외** `StopIteration` | 판정 | test 함수를 `FunctionDef`로만 찾는다 |
| 대조군: 인자가 식인 clamp 상한(P1)·기본값이 식인 통과 경로(P4)·`vin * 1.0` 기대(P5) PASS, starred 인자(C3)·lambda 피검(C4)·`assert all(…)`(C5) `UNJUDGED`, 피검 안 `match`(C6) FAIL, 피검 재귀(C7) 예외 없음, `x**200000`(C10) 0.41 s | 기대대로 | | |

→ M-02(식 인자의 통과 경로)와 M-03(부동소수 계수 순서)는 닫혔다: 판정이 곱하는 순서·반올림과 무관해졌고 손 계산 계수는 F1으로 일관되게 PASS다. M-04 중 review32가 든 모양(FN4~FN8)은 모두 고쳐졌다. 그러나 **피검 결과를 제어 흐름 블록이나 루프 대상으로 받은 재서술은 `NO-SUBJECT`**(N1~N5)로, **`match`·중첩 함수·`except*` 안의 assert는 출력 없이**(N6~N8) 빠진다. §10은 `NO-SUBJECT`를 'V4 (2) 대상 아님'으로 정의하고 F1~F5에도 이 부류가 없어, M-04가 지적한 '출력 없이/목록 밖으로 빠짐'이 모양만 바뀌어 남았다(M2-03). 두 예외(C1·C8)는 게이트 구현에서 fail-closed면 오거부로 끝나지만 probe가 그 입력을 다루지 않는다(S3).

### 0.3 M-05·M-06·M-08~M-13 문구 대조

* M-05: 계획 N3.12.3 7·N3.12.4 EL4·N4.3 10b·19·23, 05 §8.2-3 (라)·§9.2-3·§13.2 10b·19·§19 '병합 커밋'·'역할 밖 병합' 행이 같은 조건(부모 둘, 첫 부모가 base와 같거나 후손, 역할 경로 트리 = 첫 부모)을 적는다. §20 개정 목록에 review32 반영분이 있다. 계획 N3.12.4 EL3 행은 병합을 따로 적지 않지만 §4.3이 5분류만 정본으로 삼으므로 모순은 아니다.
* M-06: §8.2-2가 "변경 한 건의 병합 커밋(3 (나))은 `Change-Id`", "역할 밖 병합(3 (라))과 역할 밖 경로만 바꾼 병합 아닌 커밋(1)에는 트레일러를 요구하지 않는다"로 (라)와 맞는다.
* M-08: 공격 17 "`config_names` 리스트의 원소", §9.2-10 `pytest` 판 대조, 계획 U-38 행 pytest 고정 -- 셋이 맞는다.
* M-09: `PYTHONPATH` 첫 원소가 캐시인 네 형태를 적었다. 다만 bash 형태 `<캐시>:<기존>`은 Windows 경로의 드라이브 콜론(`C:/…`)과 구분자가 겹쳐 '첫 원소'를 어떻게 자르는지가 문구에 없다(S3, M2-09). 그리고 '첫 원소 = 맨 앞'이라는 전제 자체가 `-m pytest`에서 성립하지 않는다(§0.4, M2-01).
* M-10: 비용은 ⑤에서 재서 제시, 임계값 없음, 공격 22 (f) 기대 열 추가 -- 요구대로.
* M-11: `|&`를 파이프 구분자 하나로 -- 요구대로.
* M-12: §7에 "`role/test/<id>` 끝의 후손일 때 -- M은 병합 커밋이라 병합 아닌 test 끝과 같을 수 없다"를 넣었다. 그러나 equivalence는 `Role: test` 0개면 M^1 = `old`(§9.2-4 표)이고 v3.2부터 gate `master` 끝이 역할 밖 병합일 수 있으므로 **test 끝이 병합 커밋일 수 있다**(review32 §0.1 표 'equivalence, old = 역할 밖 병합: M = old 자신'이 실측). 판정 결과는 어느 해석이든 같지만(범위가 비어 0개) 새로 넣은 근거 문장이 사실과 다르다(S3, M2-08).
* M-13: 계획 공격 23 "알려진 놓침은 그 출력(PASS 또는 `UNJUDGED`)으로 고정" ↔ 05 공격 23 "known_limit 6(PASS 5·`UNJUDGED` 1)" 일치.
* 남은 문구: 05 §10 ④에 "숫자는 float 값"과 "숫자는 정확한 유리수(`Fraction(repr(float))`)"가 한 문장 안에 함께 있다(S3, M2-07). 계획 N4.2 V4 (2)의 정규화 괄호("숫자만의 식은 접지 않음")는 05의 "숫자끼리 곱하거나 더해 접지 않는다(이름 있는 곱의 계수 포함)·다중집합·나눗셈 역수"보다 좁다(S3, M2-10).

### 0.4 역할 밖 경로가 판정을 바꾸는 두 길 (`rv33\case\`; pytest 9.0.2, Windows 11)

M-01 수정으로 역할 밖 병합이 역할 경로를 되돌리는 길은 닫혔지만(§0.1), **트레일러 없는 역할 밖 커밋**(v3.2 N-01부터 EL3·EL4 통과, 메인 세션의 쓰기도 `overlaps_any` 거짓이라 EL1 통과, 공격 10b '오거부 0')은 역할 경로를 건드리지 않고도 판정 실행을 바꿀 수 있다.

**(가) 복제본 루트의 모듈이 게이트 캐시를 가린다.** `00-common` §8.1 red 수집과 05 §12-7은 "캐시 디렉터리를 `PYTHONPATH` 맨 앞에 둔다", 실행은 "복제본 루트에서 `$PY -m pytest --rootdir=<복제본 루트> -p merge_gate …`"이다. `python -m`은 현재 디렉터리를 `sys.path[0]`에 넣고 `PYTHONPATH`는 그 뒤다(실측 `sys.path[:3]` = `['', <캐시>, python314.zip]`).

| 실행(`PYTHONPATH=<캐시>`, cwd = 복제본 루트) | 결과 |
|---|---|
| 복제본 루트에 `merge_gate.py`, `python -m pytest -p merge_gate` | **복제본 루트의 `merge_gate.py`가 플러그인으로 로드**(캐시 판이 아님) |
| 복제본 루트에 `pytest.py`, `python -m pytest` | **`pytest.py`가 pytest 대신 실행**(`SHADOW pytest.py executed`, 종료 0) |
| 같은 조건, `python -P -m pytest` | 캐시 판 `merge_gate` 로드(`-P`는 `sys.path[0]`을 넣지 않는다, Python 3.11+) |

루트의 `merge_gate.py`·`pytest.py`(그리고 test가 import하는 모든 서드파티 모듈 이름)는 쓰기 경로표 어느 행과도 겹치지 않으므로, 메인 세션이 트레일러 없이 커밋해 gate에 넣을 수 있고, 다음 변경의 base·병합본 복제본에서 auditor의 red 수집·V1이 그 코드를 돌린다. §3.3 무결성 대조는 캐시·hook·설정만 보므로 드러나지도 않는다 → **M2-01**.

**(나) Windows에서 대소문자만 다른 `판정 환경` 이름.** §4.1 `match_glob`은 "대소문자 구분"(`fnmatch.fnmatchcase`)이라 `Pytest.ini`·`PYTEST.INI`·`Setup.cfg` 등은 `**/pytest.ini` 행에 맞지 않아 역할 밖이다. pytest `locate_config`는 `(base / name).is_file()`로 찾으므로 대소문자를 무시하는 파일 시스템에서는 그 파일을 설정으로 읽는다.

| 실행(복제본 루트, `-P`까지 적용) | 결과 |
|---|---|
| 대조군(실패 test 1, 통과 test 1) | 종료 1, `1 failed, 1 passed` |
| 루트 `PYTEST.INI`(`addopts = -k nothing_matches`) | `1 deselected` |
| 루트 `Pytest.ini`(`addopts = --deselect tests/test_a.py::test_a`) | **종료 0, `1 passed, 1 deselected`** -- 실패 test가 조용히 빠진다 |
| 루트 `Conftest.py`·`tests/CONFTEST.PY` | 파일은 찾지만 import 이름 `conftest`가 대소문자 구분이라 `ModuleNotFoundError`(수집 실패 -- 통과로 바꾸지는 못함) |

review31 N-05(`pytest.toml` 등 빠진 설정 이름, S1)와 같은 부류다 → **M2-02**. 두 길 모두 이번 커밋이 만든 것은 아니고 v3.2의 트레일러 없는 역할 밖 커밋 허용과 이전부터의 규칙(대소문자 구분 glob, `-m pytest`)이 겹친 결과다.

---

## 1. M-01~M-13 판정

| ID | 등급(32) | 판정 | 근거 |
|---|---|---|---|
| M-01 | S1 | **해결** | O3·O3b(부모를 뒤집은 `-s ours` 되돌림 병합)는 EL4에서 거부되고 EL3에서 차단된다. O1·L1·L2·X4(오래된 조상 갈래를 합치는 정상 병합 포함)는 통과한다(§0.1). 첫 부모 사슬이 `old`의 후손 안에 머문다는 논증으로 보아, 역할 밖 커밋·병합을 이어 붙여 되돌리는 길도 찾지 못했다(X1·X2 거부) |
| M-02 | S2 | **해결** | FP1~FP3 PASS. 인자가 식인 상한·식인 기본값·`vin * 1.0` 대조군도 PASS(§0.2). 부작용: 인자 하나로 제외 조건을 맞출 수 있다(N9, S3 M2-06) |
| M-03 | S2 | **해결** | 유리수 + 곱하지 않은 다중집합 + 나눗셈 역수로 FN1·FN2는 FAIL, FP4·FP5·FP5b는 PASS다. 순서·반올림과 무관하다. 다만 §10 ④에 'float' 문구가 남았다(S3 M2-07) |
| M-04 | S2 | **부분** | review32가 든 모양(FN4~FN8)은 모두 해결됐고 출력 넷이 정의됐다. 그러나 피검 결과를 블록·루프 대상으로 받은 재서술은 `NO-SUBJECT`(N1~N5)이고, `match`·중첩 함수·`except*` 안의 assert는 출력이 없다(N6~N8) → M2-03 |
| M-05 | S2 | **해결** | 계획 N3.12.3 7·N3.12.4 EL4·공격 10b·19·23과 05 §8.2·§9.2·§13.2·§19가 같은 조건을 적는다(§0.3) |
| M-06 | S3 | **해결** | §8.2-2 문구 |
| M-07 | S3 | **해결** | 부모 정확히 둘. octopus(O5)는 EL4 거부·EL3 차단, 공격 19 (g) |
| M-08 | S3 | **해결** | `config_names` 원소, §9.2-10 pytest 판, U-38 |
| M-09 | S3 | **해결(문구)** | 네 형태를 명시했다. 구분자 해석(S3 M2-09)과 '맨 앞' 전제가 무너지는 문제(M2-01)는 새 항목으로 뺐다 |
| M-10 | S3 | **해결** | 측정해 제시하고 계획 개정으로 올린다. 공격 22 (f) 기대 추가 |
| M-11 | S3 | **해결** | `\|&` |
| M-12 | S3 | **새 결함 도입(S3)** | 새로 넣은 근거 "M은 병합 커밋이라 병합 아닌 test 끝과 같을 수 없다"가 equivalence(test 0개)이면서 gate 끝이 역할 밖 병합인 경우에는 사실이 아니다. 판정 결과는 같다 → M2-08 |
| M-13 | S3 | **해결** | 계획·05 공격 23의 출력 값 일치 |

집계: **해결 11**(M-01·02·03·05·06·07·08·09·10·11·13) / **부분 1**(M-04 → M2-03) / **새 결함 도입 1**(M-12 → M2-08, S3) / **미해결 0**.

---

## 2. 새 결함

### M2-01 [S1] `python -m pytest`는 복제본 루트를 `PYTHONPATH`보다 앞에 둔다. 트레일러 없는 역할 밖 커밋으로 심은 `merge_gate.py`·`pytest.py`가 판정 코드를 대신한다
* **위치**: `00-common` §8.1 red 수집("캐시 디렉터리를 `PYTHONPATH` 맨 앞에 둔다", "복제본 루트에서 `$PY -m pytest … -p merge_gate`"), 05 §12-7·§6.2 '저장소 내부' 예외(M-09 문구), V1 실행 명령, 쓰기 경로표(루트·임의 디렉터리의 `.py`는 역할 밖), 공격 10b(트레일러 없는 역할 밖 커밋 오거부 0).
* **근거**: §0.4 (가) 실측. 루트 `merge_gate.py`가 캐시 판 대신 플러그인으로 로드되고, 루트 `pytest.py`가 pytest 대신 실행된다. 이 파일들은 EL1(`overlaps_any` 거짓)·EL3·EL4(역할 밖 경로만 바꾼 커밋)를 모두 통과하고, §3.3 무결성 대조 대상도 아니다. 계획 N3.12.0 '막는다'에 든 판정 환경 조작이 막히지도 않고 드러나지도 않는다(review31 N-05와 같은 부류).
* **수정**: 게이트가 부르는 모든 Python 실행(red 수집, V1~V3의 pytest, 세션 시작 재판정 등)을 `$PY -P …`(또는 `PYTHONSAFEPATH=1`)로 고정하고, §6.2 허용 형태도 그 형태만 받는다(실측: `-P`에서 캐시 판 로드). 공격 17에 '복제본 루트의 `merge_gate.py`·`pytest.py`'를 넣는다. `-P`를 써도 pytest `prepend` import 모드는 test 디렉터리를 `sys.path`에 넣지만, 그곳은 역할 경로라 문제없다.

### M2-02 [S1] 대소문자만 다른 `판정 환경` 이름을 Windows의 pytest가 설정으로 읽는다
* **위치**: 05 §4.1 `match_glob`("대소문자 구분", `fnmatchcase`), 계획 N3.12.2 `판정 환경` 행, 공격 17의 후보 대조.
* **근거**: §0.4 (나). 루트에 `Pytest.ini`(`addopts = --deselect <실패 test>`)를 두면 종료 코드가 1에서 **0**으로 바뀌고, `PYTEST.INI`로는 전부 deselect된다. 파일 이름이 `**/pytest.ini` 행에 맞지 않아 역할 밖이므로, 메인 세션이 쓰고 트레일러 없이 커밋해 gate에 넣을 수 있다. §4.1은 worktree 루트 접두 비교에만 `normcase`를 쓴다.
* **수정**: `판정 환경` 행(가능하면 모든 행)은 `casefold` 뒤에 대조한다(Windows·`core.ignorecase=true`). 또 EL3·EL4는 casefold하면 역할 경로와 겹치는 트리 경로(`Skills/…` 대 `skills/…`)를 거부한다. 공격 17에 대소문자 변형 셋(`Pytest.ini`·`PYTEST.INI`·`Setup.cfg`)을 넣는다.

### M2-03 [S2] 피검 결과를 블록·루프 대상으로 받은 재서술은 `NO-SUBJECT`가 되고, `match`·중첩 함수·`except*` 안 assert는 출력이 없다 (M-04 잔여)
* **위치**: 05 §10 ①(판정 문장 재귀 범위, 출력 넷의 정의), F1~F5, `v4.py` `_assert_pairs`·`judge`.
* **근거**: §0.2 N1~N8. 표 구동 test(`for r, g in zip(rs, gms)`)나 `with warnings…: r = f(…)` 뒤의 assert는 수치 test에서 흔한 모양이다. `NO-SUBJECT`는 'V4 (2) 대상 아님'이므로 F 목록(auditor가 메우는 범위)에도 들지 않는다.
* **수정**: (1) 피검 호출을 담은 식을 블록 안에서 대입받은 이름과, 피검 호출을 담은 반복 대상에서 나온 루프 변수는 `<opaque-subject:…>`로 둔다(→ `UNJUDGED`). (2) 재귀 대상에 `Match`(각 `case` 본문)와 `TryStar`를 넣고, 중첩 `FunctionDef`·`AsyncFunctionDef`·`ClassDef` 본문의 assert는 `UNJUDGED`로 낸다. (3) test 함수를 고를 때 `AsyncFunctionDef`도 받는다. 공격 23에 N1~N8을 넣는다.

### S3
* **M2-04** 비교 쌍을 만들지 못한 피검 없는 assert(`assert x > 0`, `self.assertTrue(ok)`)가 `UNJUDGED`로 나온다(N11·N12). §10의 정의("피검 호출이 걸렸는데")와 다르다. 정의를 넓히거나 probe가 `NO-SUBJECT`를 내게 한다.
* **M2-05** probe 예외: inf 리터럴(`Fraction('inf')` `ValueError`), `async def` test(`StopIteration`). `test_lint.py`로 옮길 때의 fail-closed 처리와 공격 23 케이스를 적는다.
* **M2-06** 통과 경로 제외 조건이 '결합 인자 중 어느 것과든 같음'이라, 쓰지 않는 선택 인자에 기대식을 넣으면 FAIL을 피한다(N9). 제외 비교를 그 return 경로가 실제로 돌려주는 매개변수 식으로 좁히는 방안이 있다. 또 `_walk_body`가 피검 안 중첩 `def`의 return을 바깥 함수의 return 변형에 넣는다(P3 거짓 양성).
* **M2-07** 05 §10 ④의 "숫자는 float 값"이 같은 문장의 "정확한 유리수"와 모순된다. 앞의 것을 지운다.
* **M2-08** §7의 M-12 근거 문장을 고친다: "equivalence(test 0개)에서는 test 끝 = `old`가 역할 밖 병합일 수 있다. 그때 M = `old`이면 두 범위가 같아 결과도 같다".
* **M2-09** `PYTHONPATH=<캐시>:<기존>`(bash)에서 Windows 경로의 드라이브 콜론과 구분자 `:`를 어떻게 자르는지 적는다(Windows의 Python은 `;`만 구분자로 본다). M2-01의 `-P` 고정과 함께 정리한다.
* **M2-10** 계획 N4.2 V4 (2)의 정규화 괄호를 05 §10 ④와 맞춘다(숫자끼리 접지 않음 -- 이름 있는 곱의 계수 포함, 다중집합, 나눗셈 역수, 합 위 단항 마이너스 분배).

---

## 3. 계획 · `00-common` · 05 사이 새 모순

| # | 곳 | 내용 | 항목 |
|---|---|---|---|
| 1 | `00-common` §8.1 "캐시를 `PYTHONPATH` 맨 앞에" + "`$PY -m pytest`" ↔ Python의 `sys.path` 순서(cwd가 먼저) | 캐시 판 게이트 코드가 쓰인다는 전제가 실행 형태와 맞지 않는다 | M2-01 |
| 2 | 05 §10 ①(`NO-SUBJECT` = 피검 호출이 없는 assert) ↔ `v4.py`(블록·루프에서 피검 결과를 받은 이름도 `NO-SUBJECT`, 피검 없는 비쌍 assert는 `UNJUDGED`) | 출력 정의와 probe 동작이 다르다 | M2-03, M2-04 |
| 3 | 05 §10 ④ "숫자는 float 값" ↔ 같은 ④의 "정확한 유리수" | 한 문장 안의 모순 | M2-07 |
| 4 | 05 §7 "M은 … test 끝과 같을 수 없다" ↔ 05 §9.2-4 equivalence(test 0개면 M^1 = `old`) + §9.2-3 역할 밖 병합 허용 | 근거 문장 | M2-08 |
| 5 | 계획 N4.2 V4 (2) 정규화 괄호 ↔ 05 §10 ④ | 정규화 범위 서술 | M2-10 |

확인한 일치:
* 계획 N3.12.3 7·N3.12.4 EL4·N4.3 10b·19·23 ↔ 05 §8.2-3 (라)·§9.2-3·4·§13.2·§19
* 05 §19 '병합 커밋'·'역할 밖 병합' 두 행(review32 모순 2 해소)
* §8.2-2 ↔ (라)(review32 모순 3 해소)
* §10 ⑤ ↔ §19 V4 (2) 행 ↔ `v4.py` `judge`(잎·결합 인자 정규형 제외, review32 모순 4 해소)
* U-38 ↔ §9.2-10 ↔ 공격 17(review32 모순 6 해소)
* 계획·05 공격 23 출력 값(review32 모순 7 해소)
* `00-common` 로더 규칙 10("기대값마다, `UNJUDGED` 포함") ↔ 05 §10 F5

---

## 4. 집계와 판정

| 구분 | 건수 | 항목 |
|---|---|---|
| M 해결 | 11 | M-01·02·03·05·06·07·08·09·10·11·13 |
| M 부분 | 1 | M-04(→M2-03) |
| M 새 결함 도입 | 1 | M-12(→M2-08, S3) |
| M 미해결 | 0 | |
| 새 S1 | 2 | M2-01, M2-02 |
| 새 S2 | 1 | M2-03 |
| 새 S3 | 7 | M2-04 ~ M2-10 |

review32의 S1(M-01)은 실측으로 닫혔고, 역할 밖 병합·커밋을 이어 붙여 역할 경로를 되돌리는 길은 더 찾지 못했다. V4 (2)의 거짓 양성(M-02)과 순서 의존(M-03)도 닫혔다.

새 S1 둘은 이번 커밋이 만든 것이 아니다. v3.2의 '트레일러 없는 역할 밖 커밋' 허용이 기존 실행 형태(`-m pytest`)·대소문자 구분 glob과 겹쳐 생긴 판정 환경 우회다. review31 N-05(S1)와 같은 부류라 같은 등급으로 둔다. 수정은 실행 형태 고정(`-P`)과 casefold 대조로, 규칙·문장 단위이며 구조 재작성은 필요 없다.

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
?? docs/03-analysis/gain-budget-gmid-sizing-function-audit/review33_05_v3_3.md
?? "skills/analog-gmid-design/assets/\354\225\204\353\202\240\353\241\234\352\267\270 \352\270\260\353\212\245\353\266\204\354\204\235\352\270\260.zip"
?? "skills/analog-gmid-design/assets/\355\232\214\353\241\234\353\217\204 \354\266\224\354\266\234\352\270\260.zip"
?? workspaces/current-reuse-telescopic-ota-report/current_reuse_telescopic_ota.report.html
?? workspaces/current-reuse-telescopic-ota-report/full_netlist_for_grammar.json
?? workspaces/current-reuse-telescopic-ota-report/smoke_run_harness_session18_save.py
$ git -C <repo> log --oneline -1
4b71067 docs(analog-gmid-design): 05-role-separation v3.3 -- review32 반영
$ git -C <repo> diff --stat
(비어 있음 = 추적 파일 변경 없음, v4.out.txt 포함)
$ git -C <repo> config --show-origin --get core.hooksPath
file:.git/config	C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/.githooks
```

시작 시점과 같다. 추적 파일 변경은 없고, 새 파일은 이 보고서 하나다. HEAD는 4b71067, `core.hooksPath`도 그대로다.
* 실제 저장소에서 쓴 git 명령은 읽기 전용(`show`·`log`·`diff`·`status`·`config --get`)뿐이다. `v4.py` 실행은 자기 `v4.out.txt`만 다시 썼다(바이트 동일).
* git 실험 저장소는 `%TEMP%\rv33\el4\repo`·`%TEMP%\rv33\el4\hookrepo`, pytest 실험은 `%TEMP%\rv33\case`다.
* 참고: 보고서 첫 덧붙이기를 bash `cat >>`로 했을 때 이 보고서 파일의 머리말이 사라졌다. Python 바이너리 쓰기로 복구했고, 이후 덧붙이기는 모두 Python으로 했다. 영향은 이 보고서 파일뿐이다.

**판정: 수정 후 승인** -- S1 2(M2-01·M2-02) · S2 1(M2-03) · S3 7(M2-04 ~ M2-10; M2-08은 M-12에서 생김)
