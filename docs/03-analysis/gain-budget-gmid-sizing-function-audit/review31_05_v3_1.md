# review31 -- `05-role-separation` design v3.1(커밋 d625483) R-01~R-16 해소 독립 검증

* 대상: d625483 -- 05 v3.1, 계획 v5.19(N3.12.2·N3.12.3·N3.12.4 EL4·N3.12.6·N4.2 V4·N4.3·N6.2·N9.1), `00-common` §8.1·§8.2, `v4_rule_probe/v4.py`·`v4.out.txt`
* 기준: `review30_05_v3.md` R-01~R-16(S1·S2)
* 검증자: 독립 검증 agent(작성자 아님). 저장소에서는 이 보고서만 쓴다. 실측 스크립트·임시 저장소는 `C:\Users\HSLEE\AppData\Local\Temp\rv31\`(저장소 밖)
* 등급: **S1** 승인 차단 / **S2** 승인 전 수정 / **S3** 경미

## ! 검증 중 사고 기록 (사용자 확인 필요)

R-02 실측 첫 시도에서 임시 디렉터리로의 `cd`가 실패했는데, 명령이 `&&`로 이어지지 않은 다음 줄부터 **실제 저장소에서** 실행됐다. 결과와 복구:

* 실제 저장소 `master`에 시험 커밋 4개(`base`·`side`·`m2`·`merge y`), 브랜치 `side`, 파일 `a`·`b`·`c`·`.hk/`, 로컬 설정 `core.hooksPath=<저장소>/.hk`가 생겼다. push는 없었다.
* 복구함: `core.hooksPath`를 `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/.githooks`로 되돌림(review28 E4가 기록한 '절대 경로 `.githooks`'. 원래 표기가 역슬래시였다면 표기만 다르다 -- 확인 바람), `git reset --mixed d625483`(작업 트리 비접촉), `git branch -D side`, 시험 파일 삭제. 현재 HEAD = d625483, 다른 브랜치·원격 변화 없음. reflog에는 시험 커밋이 남아 있다.
* **복구 못 함**: 시험 순서의 `git reset --hard HEAD^`가, 시작 시점에 커밋되지 않은 수정이 있던 추적 파일 6개(`.bkit/audit/2026-08-06.jsonl`, `.bkit/state/pdca-status.json`, `.bkit/state/session-history.json`, `skills/analog-gmid-design/assets/.bkit/runtime/{cc-version.json,session-ctx-fp.json,worktree-warning.flag}`)의 작업 트리 수정을 지웠다. 모두 bkit 플러그인 상태 파일이고 git에 없던 내용이라 되살릴 수 없다. 추적되지 않는 파일(`.bkit/audit/2026-08-07~09-18.jsonl`, zip 2개, `workspaces/current-reuse-telescopic-ota-report/*` 3개)은 그대로다.
* 이후 실측은 모두 `rv31\` 안에서 절대 경로(`git -C <경로>`)로만 했다. (이 보고서도 bash `cat >>` 추가에서 앞부분이 한 번 지워져 다시 썼다 -- 메모리 규칙대로 이후는 편집 도구로만 추가.)

---

## 0. 실측 (git 2.52.0.windows.1, Python 3.14.2)

### 0.1 R-02 -- 병합 경로별 hook과 `MERGE_HEAD` (`rv31\h\`)

임시 저장소에 `pre-commit`·`pre-merge-commit`·`prepare-commit-msg`·`commit-msg`가 각각 `git rev-parse -q --verify MERGE_HEAD`, `GITHEAD_*` 환경 변수, `git diff --cached --quiet MERGE_HEAD`, `interpret-trailers --parse`를 기록하게 했다.

| 경로 | 돈 hook과 `MERGE_HEAD` |
|---|---|
| `merge --no-ff side -m "merge x" -m "Role: doc<LF>Change-Id: x"` | `pre-merge-commit`: **없음**(`GITHEAD_<sha>=side`만) / `prepare-commit-msg`·`commit-msg`: 있음, 트레일러 `Role: doc`·`Change-Id: x` 둘 다 파싱. `pre-commit`은 돌지 않음 |
| `merge --no-ff --no-commit side` → `git commit -m … -m "Role: doc<LF>Change-Id: y"` | `pre-commit`·`prepare-commit-msg`·`commit-msg` 모두 `MERGE_HEAD` 있음. `pre-merge-commit`은 돌지 않음 |
| §12-6 모양(linked worktree `audit`가 T, 병합 대상 K = T의 후손) | `commit-msg`에서 `MERGE_HEAD` 있음, `git diff --cached --quiet MERGE_HEAD` 참(staged 트리 = K 트리) |

→ v3.1 §8.1(병합 판정은 commit-msg, pre-merge-commit은 무결성 대조만)과 §8.2-3의 전제가 실측과 일치한다.

### 0.2 R-01·R-07 -- EL4 모양 규칙 모델 (`rv31\el4\model.py`, 결과 `results.txt`)

**모델한 것**: gate-runner의 ff 요구(§9.1-2), §9.2-3(병합 아닌 커밋마다 트레일러·`Change-Id`·경로 권한, 역할 밖 경로만 바꾼 트레일러 없는 커밋 통과, 병합은 §9.2-4의 M일 때만), §9.2-4(역할 커밋 없는 push는 병합 아닌 `doc`·`user` 커밋만, 역할 커밋이 있으면 `Change-Id` 하나·`old` 트리의 spec card·`evidence_type`별 모양을 글자 그대로 -- ① `old..M^1` 첫 부모 사슬 전부 `test` ② `M^1..M^2` 전부 `code`·병합 없음·M^2가 M^1의 후손 ③ M 부모 둘·`Role: doc`·트리 = M^2 트리 ④ `new` = 부모가 M인 `audit` 하나, 커밋 집합이 정확히 같음). 경로 권한은 장난감 표(test→`tests/`, code→`src/`, audit→`.ai/verification/`, doc→`docs/`, 역할 밖→`other/`). **모델하지 않은 것**: 판정 기록 내용(§9.2-5~10), 계획서 판정 표, 승인 기록. §9.2-4 첫 문장은 두 가지로 읽었다: 글자대로(트레일러 없는 역할 밖 커밋도 거부) / 느슨하게(§9.2-3이 통과시킨 역할 밖 커밋은 허용).

| 케이스 | 기대 | 글자대로 | 느슨하게 | 거부 사유 |
|---|---|---|---|---|
| N1 정상 red-green(§12: T → K → M → A) | 통과 | 통과 | 통과 | |
| N2 정상 equivalence(test 커밋 없음, M^1 = old) | 통과 | 통과 | 통과 | |
| N3 정상 test-only | 통과 | 통과 | 통과 | |
| N4 문서만 push(`Role: doc`) | 통과 | 통과 | 통과 | |
| **N5 트레일러 없는 역할 밖 커밋**(`other/rtl.v`) | 통과(§9.2-3) | **거부** | 통과 | §9.2-4 "역할 커밋 없는 push는 `doc`·`user`만" |
| **N6 역할 밖 경로만 합치는 병합**(트레일러 없음) | 통과(EL3 §8.2-1) | **거부** | **거부** | 병합은 M일 때만 |
| **A19b** 역할 커밋 없음, 둘째 부모 = 조상에서 갈라진 `Role: doc` 커밋, `read-tree --reset -u S`로 트리 = S(결과 트리: spec card 3개·`tests/test_b.py` 삭제) | 거부 | 거부 | 거부 | 역할 커밋 없는 병합 |
| A19b' 같은 병합을 red-green push의 M 자리에 | 거부 | 거부 | 거부 | M^2가 M^1의 후손 아님, `M^1..M^2` ≠ 전부 code |
| A19b'' M^2 = 조상에서 갈라진 `Role: code` 커밋 | 거부 | 거부 | 거부 | 트리 ≠ M^2, 후손 아님 |
| **A20** code 쪽에 끼운 `Role: test` T'(`assert True`) | 거부 | 거부 | 거부 | `M^1..M^2` ≠ 전부 code |
| A20b code 쪽에 끼운 `Role: doc` 커밋 | 거부 | 거부 | 거부 | 같음 |
| A21 code 쪽에 끼운 트레일러 없는 역할 밖 커밋 | 거부 | 거부 | 거부 | 같음 |
| A22 audit 커밋 둘 | 거부 | 거부 | 거부 | `new`의 부모 ≠ M, 여분 커밋 |

→ R-01·R-07이 요구한 거부(A19b·A20)와 정상 세 모양 통과는 규칙대로 성립한다. 대신 **N5·N6**(흐름과 무관한 작업의 push)에서 §9.2-3·§8.2-1과 §9.2-4가 서로 다른 답을 낸다 -- 아래 N-01.

### 0.3 R-05·R-06 -- V4 (2) probe (`v4_rule_probe/v4.py` 그대로 import, 추가 케이스 `rv31\v4x\{v4x.py,v4y.py}` → `v4x.out.txt`·`v4y.out.txt`)

**probe가 실제 입력을 쓰는가**: 그렇다. `e329283_inputs()`는 `git show e329283:skills/analog-gmid-design/assets/sizing_recipe.py`를 읽어 `[7-4b 확장 estimate_area_budget()` 표지 줄 다음부터 첫 `print()` 줄 앞까지를 test 함수 본문으로 옮긴다(§13.3 규칙: 본문·리터럴·`print` 그대로). 피검 함수는 같은 소스의 AST에서 찾는다(return 둘: `a_1d / prior["packing_density_mean"]`, `(1 - cold_start_alpha) * a_1d + cold_start_alpha * a_2d_cold` -- 인라인 결과 확인). 손으로 쓴 문자열은 변형 케이스의 대체 줄과 합성 모듈 8개뿐이다. 저장소 루트에서 다시 실행하면 `v4.out.txt`가 바이트 그대로 재현된다(`git status` 변화 없음). §10의 실측 문장(실제 첫 assert FAIL, 둘째 assert F3 PASS, 네 조합 결과, FAIL 9 / PASS 2 / known_limit 3)은 출력과 일치한다.

**설계가 한계로 적지 않은 표기 변형**(F1 접은 리터럴·F2 대수 변형·F3 모듈 밖/자료구조 밖):

| 입력 | 결과 | 규칙의 목적(§10·계획 N4.2) | 분류 |
|---|---|---|---|
| **실제 e329283**, assert만 `abs(…) <= 1e-9`로 | 해당 assert **판정 없음**(쌍을 못 만듦) | FAIL | 적지 않은 거짓 음성 |
| **실제 e329283**, 상대 오차 `abs((a - b) / b) < 1e-9` | 판정 없음 | FAIL | 같음 |
| **실제 e329283**, `pytest.approx(exp) == actual`(approx 왼쪽) | PASS | FAIL | 같음 |
| **실제 e329283**, `_area_cold_expected: float = …`(주석 달린 지역 대입) | PASS | FAIL | 같음 |
| 실제 e329283, `math.isclose(exp, actual)`(순서 바꿈) | FAIL | FAIL | 정상 |
| `-gm*ro` 대 `-(2e-3*50e3)` / `2e-3*(-50e3)` | PASS / PASS | FAIL | 단항 마이너스 위치 -- 적지 않은 거짓 음성 |
| `a - b*c` 대 `a + (-b)*c` / `-b*c + a`(숫자) | PASS / PASS | FAIL | 같음(숫자 앞 `-`는 리터럴로 접히고 괄호 밖 `-`는 항 부호가 된다) |
| `x / 2` 대 `x * 0.5` | PASS | FAIL | F1과 경계(역수 접기) -- 적혀 있지 않음 |
| `1 / x` 대 `x ** -1` | PASS | FAIL | F2와 경계 -- 적혀 있지 않음 |
| 키워드 전용 매개변수 기본값(`def f(a, *, k=2.0)`) | PASS | FAIL | `_bind`가 `kwonlyargs`를 결합하지 않음 -- probe 결함 |
| 튜플 반환 `a, _ = gp(…)` | 판정 없음 | (복사) | F3 성격 -- 적혀 있지 않음 |
| 키워드·혼합 인자 `gain(gm=…, ro=…)` | FAIL | FAIL | 정상 |
| `gain(**kw)` | **예외**(`TypeError`, `_bind`가 `None`을 돌려 `_inline(…, None)`) | FAIL 또는 F3 | probe 결함(도구로 옮기면 auditor 도구 오류) |
| 지역 변수를 assert 뒤에 다시 대입 | PASS | FAIL | `_test_env`가 test 본문 전체를 한 번에 모아 **마지막 값**으로 인라인 -- 데이터 흐름이 틀림(반대 순서면 거짓 양성) |
| **거짓 양성**: `clamp(5, 0, 10) == 5`, `clamp(-3, 0, 10) == 0` | FAIL / FAIL | PASS(명세 리터럴) | return이 매개변수 하나인 경로 |
| **거짓 양성**: `area(0) == 0.0`(`if n == 0: return 0.0`) | FAIL | PASS | return이 상수 하나인 경로 |
| **거짓 양성**: 단위 이득 `vout(0.9) == approx(0.9)`(`vin * gain`, 기본값 1.0) | FAIL | PASS에 가까움 | 항등원 제거 뒤 매개변수 하나 |

요약: 적힌 주장은 모두 재현되지만, (1) 역사적 사례 e329283 자체가 **토큰 하나 바꾼 비교 형태**(`<=`, 상대 오차, approx 왼쪽, 주석 대입)로 빠지고 이 형태들은 §10의 알려진 놓침(F1~F3)에 없다 (2) return 경로가 **잎 하나**(매개변수·상수)이면 그 값과 같은 명세 리터럴이 전부 FAIL이다 -- "FAIL은 확실한 복사"가 성립하지 않는다(N-03·N-04).

### 0.4 R-04 -- 판정 환경 파일 (`rv31\pe\`, pytest 9.0.2, `--rootdir=<root> skills/analog-gmid-design/assets/tests`, test는 `assert f(1) == 10`이고 실제 0)

pytest 9.0.2 `_pytest/config/findpaths.py`의 `locate_config`가 찾는 설정 파일 이름은 `pytest.toml`, `.pytest.toml`, `pytest.ini`, `.pytest.ini`, `pyproject.toml`, `tox.ini`, `setup.cfg`다. 계획 N3.12.2의 새 `판정 환경` 행에는 앞 둘과 `.pytest.ini`가 없다.

| 파일 | 결과 | 계획 행 |
|---|---|---|
| 없음(기준) | `1 failed` | |
| `skills/analog-gmid-design/pytest.toml`(`[pytest]` `addopts = ["-k", "not test_f"]`) | **`1 deselected`** | 없음 → `overlaps_any` 거짓 |
| `skills/.pytest.toml` | **`1 deselected`** | 없음 |
| `skills/analog-gmid-design/assets/tests/.pytest.ini` | **`1 deselected`** | test-author 행(`assets/tests/**`)에 맞음 → V5 '`.py` 아닌 파일' 규칙으로 승인 필요(막힘) |

`match_glob`(§4.1: `/`로 조각, `**`는 0개 이상 조각, 나머지 `fnmatchcase`)을 새 행에 대 보면: `**/conftest.py`는 루트 `conftest.py`에 맞는다(`**` = 0조각). 제외 `skills/analog-gmid-design/assets/tests/conftest.py`는 그 한 파일만 빼므로 test-author 행이 그것을 허용하고, `assets/tests/tools/conftest.py`·`assets/tests/<하위>/conftest.py`는 판정 환경 우선으로 test-author도 거부된다(공격 17 기대와 일치). `판정 환경` 우선 규칙(§4.1)과 계획 조건 정의는 같은 말을 한다.

### 0.5 R-08 -- §6.2 분해기를 문구 그대로 구현 (`rv31\split\split.py` → `split.out.txt`)

문구에 있는 규칙만 구현했다(따옴표 밖 `;`·`&&`·`||`·`|`·`&`·줄바꿈 분리, bash 이스케이프, `$(…)`·백틱·`<(…)` 재귀, heredoc 건너뛰기, `$'…'` 거부).

| 입력 | 분해 결과 | 설계 기대 |
|---|---|---|
| (a) §12-6 `… -m "merge c1" -m "Role: doc<LF>Change-Id: c1"` | 명령 하나, 마지막 인자 `Role: doc\nChange-Id: c1` | 허용 -- 일치 |
| (b) `echo a<LF>git push gate master:master` | `[echo a]`, `[git push gate master:master]` | push 규칙 판정 -- 일치 |
| (c) `echo "$(git push gate x:master)"` | 안쪽 `git push …` 따로 | 거부 -- 일치 |
| (d) quoted heredoc 본문의 `git push` | 건너뜀 | 허용 -- 일치 |
| (e) `$'a\nb'` | 거부 | 거부 -- 일치 |
| `git status 2>&1 \| head` | `[git status 2>]`, `[1]`, `[head]` | **문구가 정하지 않음** -- `&` 분리가 `2>&1`·`>&2`·`&>`를 자른다 |
| `cp a \<LF>skills/…/eng.py`(줄 이음) | 대상 `\nskills/…/eng.py` | **문구가 정하지 않음** -- bash는 역슬래시-줄바꿈을 지우지만 "다음 문자를 그대로"는 줄바꿈을 남겨 경로 판정이 빗나간다 |
| `X=push; git $X gate x:master` | `[git $X gate x:master]` | 변수 확장 미정(목록 불완전은 설계가 인정, EL4가 최후 겹) |

→ R-08이 요구한 두 경우는 명세대로 동작한다. 새 모호함 둘(N-08).

---

## 1. R-01~R-16 판정

| ID | 등급(30) | 판정 | 근거 |
|---|---|---|---|
| R-01 | S1 | **해결** | §9.2-3 "병합은 M일 때만", §9.2-4 역할 커밋 없는 push는 병합 아닌 `doc`·`user`만, M에는 경로 권한 면제(C5 해소). 모델: A19b·A19b'·A19b'' 거부, N1~N3 통과(§0.2). EL3도 commit-msg (나)에서 브랜치·HEAD·`MERGE_HEAD`를 `role/{audit,test,code}/<id>`로 묶어 흐름 밖 병합을 막는다. 다만 이 수정이 흐름과 무관한 커밋·병합을 새로 막는다(N-01) |
| R-02 | S1 | **해결** | 실측(§0.1): `merge --no-ff`의 pre-merge-commit에는 `MERGE_HEAD`가 없고 commit-msg에는 있다. `--no-commit` 뒤 `git commit`도 commit-msg에서 있다. 병합 판정을 commit-msg로 옮긴 §8.1·§8.2-3이 맞다. ⑤에 §12-6 실제 명령 재생도 들어갔다 |
| R-03 | S1 | **부분** | 역할별 범위(test `gate/master..HEAD`, code `role/test/<id>..HEAD`, audit `M..HEAD`)로 red-green·equivalence 정상 흐름의 오거부는 사라졌다. 그러나 **test-only**에서는 병합이 없어 audit 범위가 대체 규칙 "`role/test/<id>..HEAD`이고 비어 있어야 한다"로 떨어지고, auditor의 `Role: audit` 커밋 자체가 그 범위에 있어 **auditor 종료가 매번 거부**된다(N-02) |
| R-04 | S1 | **부분** | `판정 환경` 조건과 `**/` 행 9개, 우선 규칙, V5의 `tests/conftest.py` 무조건 승인, 공격 17 확장. `match_glob` 의미(루트 `conftest.py` 포함, 제외로 `assets/tests/conftest.py`만 test-author에게)는 의도대로다(§0.4). 그러나 pytest 9.0.2가 읽는 `pytest.toml`·`.pytest.toml`·`.pytest.ini`가 행에 없고, 셋 다 실측에서 test를 deselect했다 -- tests 밖에 두면 어느 행과도 겹치지 않아 트레일러 없이 EL1·EL3·EL4를 통과한다(N-05) |
| R-05 | S1 | **해결(주장 범위)** | probe가 `git show e329283`의 실제 함수와 실제 self-test 섹션을 입력으로 받고(§0.3), 재실행 결과가 `v4.out.txt`와 같으며, §10 문장과 일치한다. 단 실제 e329283이 비교 형태 한 토큰 변경으로 빠지고 그 형태가 알려진 놓침에 없다(N-04) |
| R-06 | S2 | **부분** | 목적("피검 식의 재서술은 전부 자기참조")을 계획 N4.2 V4 (2)에 먼저 적고 반복 잎 조건을 뺐으며, 한계 F1~F3와 auditor oracle 대조(로더 규칙 10)로 나눴다 -- 요구한 방향 그대로. 그러나 새 규칙은 return 경로가 잎 하나(매개변수·상수)일 때 명세 리터럴을 FAIL로 만든다(거짓 양성, N-03)이고, 단항 마이너스 위치·`x/2` 대 `x*0.5`는 정규화가 주장하는 범위 안인데 빠진다(N-04) |
| R-07 | S2 | **해결** | 모양 ② "`M^1..M^2`는 전부 `Role: code`, 병합 없음, M^2는 M^1의 후손". 모델: T'(A20)·code 쪽 `doc` 커밋·트레일러 없는 커밋 모두 거부(§0.2). 계획 N3.12.4 EL4 행도 같게 고쳤다 |
| R-08 | S2 | **해결** | 분해기 명세(따옴표 밖에서만 분리, 치환 재귀, heredoc, `$'…'` 거부)를 문구대로 구현하면 §12-6 두 줄 `-m`은 한 인자, `echo a<LF>git push …`는 두 명령이다(§0.5). 명세에 없는 `2>&1`·줄 이음은 N-08 |
| R-09 | S2 | **부분** | 사슬(가)·구간 재판정(나)·빈 로그 = 실패·④(b) 첫 줄·복제본 `origin` 제거는 모두 들어갔다. 그러나 재판정 생략 캐시 `<git-common-dir>/gmid-gate-cache/rejudged`에 (old, new) 한 줄을 미리 쓰면 (나)가 그 구간을 건너뛴다 -- v3.0의 "로그 한 줄로 무력화"(I6b)가 "캐시 한 줄로 무력화"로 옮겨졌다(N-06) |
| R-10 | S2 | **해결** | 행 2: `--show-origin --get-regexp`로 모든 범위, 역할 worktree 각각. 행 4: EL1 push 직전·EL3·세션 시작에도. `hooks/role_session_start.py`+`.json`이 §2·계획 N3.12.6 산출물에 있고 행 5가 '네 항목'. SessionStart exit 코드 미측정을 표지 파일로 우회한 것은 정직하다(표지 파일 삭제는 C 범위 밖). 공격 21·22 기대 시점이 §3.3 표와 맞는다 |
| R-11 | S2 | **해결** | 05 ④(b)와 계획 N3.12.6 (b) 모두 `hooks/*.sample` 삭제를 첫 push 전에 둔다 |
| R-12 | S2 | **해결** | 계획 표 `gmid-code-author \| tools/gates/gate/** \| -- \| 게이트 변경`, 05 §13.4 재설치 절차와 fail-closed 구간 명시. 작은 틈: `install.py`의 `_register_hook`은 태그가 이미 있으면 등록을 건너뛰므로 게이트 변경이 `hooks/role_*.json`의 event·matcher를 바꾸면 ②가 설정을 고치지 않는다(행 5가 영구 실패 -- §13.4에 사용자 수동 수정 한 줄 필요, S3) |
| R-13 | S2 | **해결** | `00-common` §8.1의 두 소비자를 "auditor가 격리 복제본에서 계산·기록, merge gate는 형식만"으로, 05 §9.2-6에 "형식 검사이지 증거의 증명이 아니다". 잔여: `00-common` CC 표(§17, CC-1 행)의 "로더 규칙 전부 + **해시 재계산**" 문구가 남아 있다(S3). 그리고 격리 복제본에서 base 판 게이트 코드를 쓰는 방식이 EL1 규칙과 부딪힌다(N-07) |
| R-14 | S2 | **해결** | `00-common` §8.2: `target_kind`에 `staged_diff`, 허용 키 목록 안에서 `diff_head` 금지, `diff_path` = `.ai/approvals/**`를 뺀 바뀐 경로 전부(자기 제외 이유 명시), head blob은 EL3 index / EL4 커밋 트리, 다시 계산하는 쌍 (HEAD, index)·(첫 부모, 커밋). 05 §8.2-5의 topology·`Role: user` 두 조건과 §9.2-9가 같은 말을 한다. 내부 모순 없음. 공격 15에 `staged_diff` 케이스 추가 |
| R-15 | S2 | **해결** | 계획 N4.3 "28건(1~25와 1b·10b·10c)" = 표의 행 수 28, 0.5 = 25(12·13·14 제외), N6.2·N9.1·05 §19 모두 25/28. N3.12.3 7 = audit 브랜치 끝 push, 병합 모양 명시. N3.12.6 ④ 순서((b) 샘플 삭제 → 원격 → baseline push → 로그 첫 줄 → pre-receive, (c) 표지 커밋, (d) 설치)가 05 §13.1과 같다. `부트스트랩` 정의 = gate `master`에 표지 반영. 잔여 불일치는 S3(§2 N-10) |
| R-16 | S2 | **해결** | 05 §12 재시도·§6.2 '정리 전 dispute 보존'(blob id가 spec card `## dispute 기록`에 없으면 정리 거부)·§11.2 절 추가, 계획 N3.12.3 5, 공격 25 |

집계: **해결 12**(R-01·02·05·07·08·10·11·12·13·14·15·16, R-05는 주장 범위 한정) / **부분 4**(R-03·04·06·09) / **미해결 0**. '새 결함 도입'은 R-01(N-01), R-03(N-02), R-06(N-03), R-09(N-06), R-13(N-07)의 수정이 각각 만든 것이다(아래).

---

## 2. 새 결함과 잔여

### N-02 [S1] test-only 흐름에서 auditor의 SubagentStop이 매번 거부된다 (R-03 수정이 만든 것)
* **위치**: 05 §7 SubagentStop "audit = `M..HEAD`(M = `git rev-list --merges -n 1 HEAD`이고 `role/test/<id>`의 후손일 때. 병합 전이면 `role/test/<id>..HEAD`이고 비어 있어야 한다)", §16 SubagentStop 범위 행, 공격 20 (e).
* **근거**: test-only는 계획 N3.12.3에서 순서 4·5(그래서 6 병합도)를 생략하고 auditor가 `role/audit/<id>`(= `role/test/<id>`에서 만든 브랜치)에 `Role: audit` 커밋을 바로 쌓는다. M이 없으므로(가장 가까운 병합은 이전 변경의 M -- `role/test/<id>`의 조상이지 후손이 아니다) 범위는 `role/test/<id>..HEAD` = {audit 커밋}이고 "비어 있어야 한다"를 어긴다 → exit 2 → auditor가 끝나지 못한다. EL4 모양 표의 test-only 행(`new`는 `Role: audit` 1개, 병합 없음)과도 어긋난다. test-only는 Phase 1 TS2·TS3·TS5와 TS6 승격·삭제의 판정 유형이다.
* **수정**: 범위를 "M이 있으면 `M..HEAD`, 없으면 `role/test/<id>..HEAD`"로 두고, 조건을 "범위 안 커밋은 전부 `Role: audit`·그 id, 병합 아님, **최대 1개**"로. 공격 20 (e)에 세 판정 유형 각각의 auditor 정상 종료를 넣는다.

### N-05 [S1] 판정 환경 행에 pytest 9의 설정 파일 셋이 없다 (R-04 잔여)
* **위치**: 계획 N3.12.2 `판정 환경` 행, 05 §4.1, 공격 17.
* **근거**: §0.4. pytest 9.0.2 `locate_config`의 후보는 `pytest.toml`·`.pytest.toml`·`pytest.ini`·`.pytest.ini`·`pyproject.toml`·`tox.ini`·`setup.cfg`. `skills/analog-gmid-design/pytest.toml`·`skills/.pytest.toml`은 실측에서 `1 failed` → `1 deselected`였고 어느 행과도 겹치지 않아 오케스트레이터가 쓸 수 있고(EL1 즉시 통과) 트레일러 없는 커밋으로 EL3·EL4를 통과한다 -- R-04와 같은 N3.12.0 '막는다'(판정 환경 조작) 통과다. (`assets/tests/.pytest.ini`는 test-author 행 + V5 '`.py` 아닌 파일' 규칙으로 막힌다.)
* **수정**: `**/pytest.toml`·`**/.pytest.toml`·`**/.pytest.ini` 행 추가(`plan_tables` 승인). 행 목록이 pytest 판에 기대므로 `tools/gates/requirements.txt`에 고정한 pytest 판의 `locate_config` 후보와 행 목록을 대조하는 test(부트스트랩 ③ 재생)를 두면 판 올림 때 다시 새지 않는다. 공격 17에 세 파일을 넣는다.

### N-01 [S2] 흐름과 무관한 커밋·병합에 대해 §9.2-3·§8.2-1과 §9.2-4가 다른 답을 낸다 (R-01 수정이 만든 것)
* **위치**: 05 §9.2-3("역할 밖 경로만 바꾼 커밋은 통과"), §9.2-4 첫 문장("역할 커밋이 없는 push는 병합 아닌 `Role: doc`·`Role: user` 커밋만 가진다"), §8.2-1(EL3: 역할 밖 경로만이면 통과 -- 병합 판정 3보다 앞), §3.1(gate가 유일한 master 경로, `origin`은 백업).
* **근거**: §0.2 N5·N6. 글자대로면 트레일러 없는 역할 밖 커밋(다른 skill, RTL -- hook 판정 범위가 "즉시 통과"로 둔 작업)이 든 push가 전부 거부된다. 느슨하게 읽어도 역할 밖 경로만 합치는 병합은 EL3는 통과(§8.2-1), EL4는 거부(§9.2-3)다. gate가 이 저장소 `master`의 유일한 경로이므로 gmid 밖 작업이 master에 닿는 길을 설계가 정하지 않은 셈이다.
* **수정**: §9.2-4 첫 문장을 "역할 커밋이 없는 push는 병합 커밋을 가질 수 없다(비병합 커밋은 3으로 판정)"로. 역할 밖 병합을 허용할지(예: 두 부모 모두 역할 밖 경로만 바꿨고 트리가 역할 경로에서 첫 부모와 같음) 한 줄로 정하고 EL3 §8.2-3과 맞춘다. 공격 10b에 "트레일러 없는 역할 밖 커밋 push 통과"를 넣는다.

### N-03 [S2] V4 (2) 검출기가 잎 하나짜리 return 경로에서 명세 리터럴을 FAIL로 만든다 (R-06 수정이 만든 것)
* **위치**: 05 §10 V4 (2) ②·⑤("정규화한 X가 **어떤** E_i와 같으면 FAIL", "FAIL은 확실한 복사"), 계획 N4.2 V4 (2)("독립 기대값은 출처가 있는 리터럴").
* **근거**: §0.3. `clamp(5, 0, 10) == 5`, `clamp(-3, 0, 10) == 0`, `area(0) == 0.0`이 FAIL. E_i가 매개변수 하나(인자 결합 뒤 리터럴)나 상수 하나이면, 입력값과 같은 기대값(통과 경로·하한·0 출력 같은 경계 test)이 '재서술'로 판정된다. 게다가 비교 대상이 **그 입력이 실제로 지나는 return**이 아니라 모든 return이다. spec card 양식의 '무동작 판정 입력(무발동 값)'·'거부해야 할 입력'이 바로 이런 test를 만든다. V4 FAIL을 면제하는 경로(V3의 `decision` 승인 같은 것)는 설계에 없다.
* **수정**: E_i가 연산자를 하나 이상 가질 때만 비교(잎 하나는 비교하지 않음 -- 그런 복사는 V3가 잡는다)로 좁히고, 공격 23에 위 셋을 PASS 기대로 넣는다. 또는 면제 승인 경로를 정한다.

### N-04 [S2] V4 (2) 알려진 놓침 목록이 불완전하다 -- 실제 e329283이 비교 형태 한 토큰으로 빠진다
* **위치**: 05 §10 V4 (2) ①(비교 형태 목록)·④(정규화)·알려진 놓침 F1~F3, 계획 N4.2 V4 (2), 공격 23.
* **근거**: §0.3. 실제 e329283 test에서 `<`를 `<=`로, 또는 상대 오차 형태로, 또는 `pytest.approx`를 왼쪽에, 또는 기대값 대입에 타입 주석을 붙이면 첫 assert가 판정 없음·PASS다. `-(a*b)` 대 `(-a)*b`, 숫자 앞 단항 마이너스, `x/2` 대 `x*0.5`, `1/x` 대 `x**-1`, 키워드 전용 기본값도 빠진다. 이것들은 F1~F3 어디에도 적혀 있지 않고 ④가 주장하는 "뺄셈·나눗셈 평탄화" 범위 안에 있는 것도 있다. (c) 결정상 PASS는 auditor oracle 대조가 메우므로 '막는다'의 유일한 겹은 아니지만, §10은 auditor에게 무엇을 메워야 하는지를 F1~F3로 한정해 알려 준다.
* **수정**: 비교 형태를 `<`·`<=`·양변 `approx`·`abs((a-b)/b)`·`isclose` 양 순서로, 지역 대입에 `AnnAssign`을 넣고, 단항 마이너스를 항 부호로 정규화(숫자 리터럴 포함). 남는 것(`x/2` 대 `x*0.5` 등)은 F1·F2에 예로 적는다. '판정 없음'(비교 쌍을 못 만든 assert)의 처리(FAIL? auditor 확인?)를 정한다. 모두 공격 23 케이스로.

### N-06 [S2] 재판정 생략 캐시 한 줄이 행 3(나)를 무력화한다 (R-09 수정이 만든 것)
* **위치**: 05 §3.3 행 3(나) "통과한 (old, new) 쌍은 `<git-common-dir>/gmid-gate-cache/rejudged`에 적어 다음 세션에서 건너뛴다".
* **근거**: I6b(참조 이동 + 로그 한 줄)를 드러내려고 만든 재판정이, 같은 계정이 쓸 수 있는 캐시 파일에 그 (old, new)를 한 줄 적으면 건너뛰어진다. review30 R-09가 지적한 "로그 한 줄로 감지 무력화"가 캐시로 옮겨졌을 뿐이다. 캐시 없이 전 구간을 세션마다 재판정해도 비용은 로그 줄 수 × `merge_gate.py` 한 번(데이터만)이다.
* **수정**: 생략 캐시를 없애거나, 생략해도 마지막 K줄은 항상 재판정(K는 수치가 아니라 "앞 세션 이후 새 줄 + 마지막 줄")으로. 공격 22에 "(c) + 캐시에 줄 덧붙이기"를 넣는다.

### N-07 [S2] base 판 게이트 코드를 `<git-common-dir>` 캐시에서 부르는 명령을 EL1 '저장소 내부' 규칙이 거부한다
* **위치**: 05 §12-7(v3.1 추가: "base 판(§4.4 캐시)을 `PYTHONPATH` 맨 앞에"), `00-common` §8.1 red 수집(같은 문장), §12-0(`$PY <게이트 코드>/interface_card.py`), §4.4(캐시 = `<git-common-dir>/gmid-gate-cache/<커밋 id>/`), §6.2 '저장소 내부' 행(전부: `<git-common-dir>/**`를 가리키는 **인자**·`--git-dir`·리다이렉트·도구 대상 거부).
* **근거**: auditor의 red 수집 명령(`PYTHONPATH=<git-common-dir>/gmid-gate-cache/<id> $PY -m pytest -p merge_gate …`)과 오케스트레이터의 §12-0 명령은 모두 `<git-common-dir>/**`를 가리키는 토큰을 가진다. 문구대로면 EL1이 정상 흐름을 거부하고, 예외를 두면 그 캐시 파일을 쓰는 인자도 같은 모양이 된다. 어느 쪽인지 설계가 정하지 않았다.
* **수정**: '저장소 내부' 행에 "읽기·실행 목적의 캐시 경로(`$PY <캐시>/*.py`, `PYTHONPATH=<캐시>`)는 허용, 쓰기 대상(리다이렉트·`cp`·`mv`·`rm`·도구 쓰기)은 거부"를 적고 공격 10c·24에 두 명령을 넣는다.

### S3
* **N-08** §6.2 분해기: `&`를 구분자로 적어 `2>&1`·`>&2`·`&>`를 자른다(§0.5 -- 메인 세션이 늘 쓰는 형태라 구현자가 문구를 따르면 오거부나 대상 없는 리다이렉트가 된다). 역슬래시-줄바꿈(줄 이음)은 bash가 지우는데 문구는 "다음 문자를 그대로"라 대상 경로 앞에 줄바꿈이 붙는다(EL1 조기 경보 누락, EL3·EL4는 잡음). 리다이렉트 연산자 목록과 줄 이음 규칙을 적는다.
* **N-09** probe 결함(도구로 옮기기 전에 고칠 것): `_test_env`가 test 본문 전체를 먼저 모아 마지막 대입값으로 인라인(데이터 흐름 무시 -- 거짓 음성·양성 양쪽), `_bind`가 `kwonlyargs`를 결합하지 않음, `**kw` 호출에서 `_bind`가 `None` → `judge`가 `TypeError`, 피검 함수가 클래스 메서드면 `funcs[...]` `KeyError`.
* **N-10** `00-common` CC 표 CC-1 행 "로더 규칙 전부 + 해시 재계산" -- §8.1 개정 뒤에는 red·outputs 해시를 gate가 재계산하지 않는다(diff 해시 재계산만 남는다).
* **N-11** 계획 N4.3 공격 24 "앞은 허용, 뒤 셋은 거부"는 네 형태만 적고 05 §13.2 24의 (d) heredoc(허용)가 없다. 계획 N7.2 U-15 행은 여전히 "hook 입력 `cwd`는 세션 시작 디렉터리로 고정"이라 적어 05 §5(R-18: 메인 세션은 `cd`를 따라 바뀐다)와 다르다.
* **N-12** `판정 환경` 행은 저장소 전체(`**/`)라 다른 skill·workspace의 `conftest.py`·`pyproject.toml`도 메인 세션이 쓸 수 없고 커밋에 `Role: user`+승인이 필요하다(현재 추적 파일에는 해당 0개 -- 실측). 공격 10b의 "다른 skill 쓰기 통과"가 이 이름들에는 성립하지 않음을 적는다. 공격 17의 재생 데이터는 이 이름의 파일을 저장소에 둘 수 없으니(`tools/gates/redteam/**`도 판정 환경 우선에 걸린다) 실행 중 임시 저장소에 만드는 방식임을 적는다.
* **N-13** 행 2의 `^url\.` 규칙은 gate와 무관한 전역 `url.*.insteadOf`(흔한 GitHub 설정)도 실패로 만든다(현재 사용자 설정에는 없음 -- 실측). 대상을 gate URL에 영향을 주는 키로 좁히거나 사용자 확인 항목으로.
* **N-14** §13.4 재설치 ②: `install.py`의 `_register_hook`은 태그가 이미 있으면 건너뛴다 -- `hooks/role_*.json`의 event·matcher가 바뀐 게이트 변경은 설정이 갱신되지 않아 행 5가 계속 실패한다. §13.4에 "`.json`이 바뀌었으면 `.claude/settings.json`의 해당 항목을 사용자가 고친다"를 넣는다. 또 절 순서가 §13.4 → §13.3이다.

---

## 3. 계획 · `00-common` · 05 사이 새 모순

| # | 곳 | 내용 | 항목 |
|---|---|---|---|
| 1 | 05 §9.2-3 ↔ §9.2-4 ↔ §8.2-1 | 트레일러 없는 역할 밖 커밋·병합의 통과 여부 | N-01 |
| 2 | 05 §7 SubagentStop ↔ 계획 N3.12.3 test-only ↔ 05 §9.2-4 test-only 모양 | test-only의 audit 커밋이 범위 규칙에 걸림 | N-02 |
| 3 | 05 §6.2 '저장소 내부' ↔ 05 §12-0·§12-7 ↔ `00-common` §8.1 red 수집 | 캐시 경로 인자 | N-07 |
| 4 | 계획 N4.2 V4 (2) "출처가 있는 리터럴은 독립" ↔ 05 §10 검출기 동작 | 잎 하나 return의 명세 리터럴 FAIL | N-03 |
| 5 | `00-common` CC-1 행 ↔ `00-common` §8.1 | "해시 재계산" | N-10 |
| 6 | 계획 N4.3 24 ↔ 05 §13.2 24, 계획 U-15 ↔ 05 §5 | heredoc 케이스, `cwd` 기술 | N-11 |

그 밖에 확인한 일치: 공격 개수(28 / 0.5 25)는 계획 N4.3 표 행 수·N6.2·N9.1·05 §19에서 같다. N3.12.3 7 ↔ 05 §12-8·§9.2-4, N3.12.4 EL4 ↔ 05 §9.2-3·4, N3.12.6 ④⑤ ↔ 05 §13.1, `부트스트랩` 조건 ↔ 05 §4.1, `staged_diff` ↔ 05 §8.2-5·§9.2-9, 공격 23 개수(FAIL 9·PASS 2·known_limit 3) ↔ `v4.out.txt`.

---

## 4. 집계와 판정

| 구분 | 건수 | 항목 |
|---|---|---|
| R 해결 | 12 | R-01·02·05·07·08·10·11·12·13·14·15·16 |
| R 부분 | 4 | R-03(→N-02)·R-04(→N-05)·R-06(→N-03·N-04)·R-09(→N-06) |
| R 미해결 | 0 | |
| 새 S1 | 2 | N-02, N-05 |
| 새 S2 | 5 | N-01, N-03, N-04, N-06, N-07 |
| 새 S3 | 7 | N-08 ~ N-14 |

**판정: 수정 후 승인** -- review30의 S1 다섯 중 셋(R-01·R-02·R-05)은 실측으로 닫혔고(병합 모양 모델, hook 시점, 실제 e329283 입력 probe), 나머지 둘(R-03·R-04)은 방향이 맞되 한 곳씩 남았다. 새 S1 둘은 모두 국소 수정이다: SubagentStop audit 범위의 test-only 경우(N-02, 규칙 한 줄)와 판정 환경 행 세 개 추가(N-05, `plan_tables` 승인). S2 다섯도 문장·규칙 단위 수정이며, 고친 뒤 §0의 케이스(N5·N6, test-only 종료, `pytest.toml`, V4 표 전부, 캐시 한 줄, 캐시 경로 명령)를 공격 재생 데이터에 넣어 재검증하면 된다. 구조를 다시 짤 필요는 없다.

실측 스크립트: `C:\Users\HSLEE\AppData\Local\Temp\rv31\{h\ (R-02), el4\model.py (R-01·R-07), v4x\v4x.py·v4y.py (R-05·R-06), pe\ (R-04), split\split.py (R-08)}`와 각 `*.out.txt`·`results.txt`.

