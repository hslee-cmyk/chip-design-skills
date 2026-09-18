# review32 -- `05-role-separation` design v3.2(커밋 451fd8f) review31 N-01~N-14 해소 독립 검증

* 대상: 451fd8f -- 05 v3.2, 계획(N3.12.2 `판정 환경` 행·N4.2 V4·N4.3 공격 24·N7.2 U-15), `00-common`(로더 규칙 10·CC-1 행), `v4_rule_probe/v4.py`·`v4.out.txt`
* 기준: `review31_05_v3_1.md` N-01~N-14
* 검증자: 독립 검증 agent(작성자 아님). 저장소에서는 이 보고서만 쓴다. 실측 스크립트·임시 저장소는 `C:\Users\HSLEE\AppData\Local\Temp\rv32\`(저장소 밖). 모든 git 실험은 `git -C <rv32 안 절대 경로>`, 스크립트는 `set -euo pipefail`
* 등급: **S1** 승인 차단 / **S2** 승인 전 수정 / **S3** 경미


---

## 0. 실측 (git 2.52.0.windows.1, Python 3.14.2)

### 0.1 N-01 역할 밖 병합 · N-02 SubagentStop audit 범위 (`rv32\el4\model.py` → `results.txt`, `fixcheck.py` → `fixcheck.txt`)

**모델한 것**: v3.2 글자 그대로 -- EL4 §9.2-3(병합 아닌 커밋은 트레일러·경로, 역할 밖 경로만이면 트레일러 없이 통과; 병합은 M이거나 "병합 트리와 첫 부모 트리가 `overlaps_any` 경로 전부에서 같은" 역할 밖 병합), §9.2-4(역할 커밋 없는 push는 3으로만, 역할 커밋이 있는 push에 역할 밖 병합 불가, 모양 표), EL3 §8.2-3 (라)(staged 트리 = `HEAD` 트리, `overlaps_any` 경로에서), §7 SubagentStop audit 범위(M = `rev-list --merges -n 1 HEAD`이고 `role/test/<id>`의 후손이면 `M..HEAD`, 아니면 `role/test/<id>..HEAD`, 전부 `Role: audit`·그 id·비병합, 최대 1개). 장난감 경로표: 역할 경로 = `tests/`·`src/`·`.ai/`·`docs/`·`tools/gates/`, 역할 밖 = `other/`. 판정 기록 내용·승인 기록은 모델하지 않음. 저장소는 `rv32\el4\repo`(모든 git 호출 `git -C <절대 경로>`, 경로 가드 assert).

| 케이스 | 기대 | EL4 | EL3 (라) | 비고 |
|---|---|---|---|---|
| O1 역할 밖 병합(두 쪽 모두 `other/`만, 트레일러 없음) | 통과 | 통과 | 통과 | N-01 의도대로 |
| O2 A19b(M^1 = old, M^2 = 조상에서 갈라진 `Role: doc`, 트리 = M^2) | 거부 | 거부 | 차단 | 결과 트리: spec card 3개·`tests/test_b.py`·`tools/gates/gate_config.json` 삭제 |
| **O3 부모 순서를 뒤집은 A19b**: 조상 `anc`에서 트레일러 없는 `other/z.v` 커밋 Sx → `git merge --no-ff -s ours <old>` (부모 = (Sx, old), 트리 = Sx 트리) | 거부 | **통과** | **통과** | 결과 트리가 O2와 같다(spec card 3개·test·`gate_config.json` 삭제). Sx는 역할 밖 경로만 바꿔 §9.2-3 통과, 병합은 첫 부모(Sx)와 역할 경로가 같아 '역할 밖 병합' |
| **O3b** 새 커밋 없이 `anc`를 detach하고 `git merge --no-ff -s ours <old>` (부모 = (anc, old)) | 거부 | **통과** | 통과 | `old..new` 커밋 1개(병합 하나), 트레일러 없음. 위와 같은 삭제 |
| O4 역할 밖 병합 + red-green 한 push | 거부 | 거부 | -- | |
| O4b red-green 뒤에 역할 밖 병합 | 거부 | 거부 | -- | |
| O5 octopus 역할 밖 병합(부모 3) | (설계 미정) | 통과 | -- | 부모 수를 정하지 않았다(S3) |
| O6 둘째 부모 쪽에 트레일러 없는 `tests/` 변경, `-s ours`로 트리에서 뺌 | 거부 | 거부 | -- | 그 커밋 자체가 §9.2-3에서 거부 |

**수정안 확인**(`fixcheck.py`): 역할 밖 병합 조건에 "첫 부모가 `old`의 후손(또는 같음)"을 더하면 O3·O3b 거부, O1 통과, **오래된 조상에서 갈라진 RTL 브랜치를 현재 master에 합치는 정상 병합**(M^1 = old, 둘째 부모 = 조상 갈래) 통과 -- 오거부 없이 닫힌다. (모든 부모의 역할 경로가 같아야 한다는 식은 이 정상 병합을 거부하므로 쓰면 안 된다.)

EL1은 O3b를 막지 않는다: §6.2 표는 `checkout -B`·`switch -C`·`reset` 등을 거부하지만 `git checkout <커밋>`(detach), `git merge -s ours`, `git merge --ff-only`(§12-0이 쓰는 형태)는 거부 목록에 없고, 그 뒤 `git push gate master:master`는 오케스트레이터의 허용 형태다.

**N-02**(세 판정 유형 × gate `master` 끝이 보통 커밋 / 역할 밖 병합):

| 흐름 | 단계 3(병합 전) | 단계 6(병합 뒤) | 단계 7(audit 커밋 뒤) | 음성: audit 커밋 2개 |
|---|---|---|---|---|
| red-green, old 보통 | `T..` 0개 OK | `M..` 0개 OK | `M..` 1개 OK | 거부 |
| equivalence, old 보통 | `T..` 0개 OK | `M..` 0개 OK | `M..` 1개 OK | 거부 |
| test-only, old 보통 | `T..` 0개 OK | -- | `T..` 1개 OK | 거부 |
| red-green, old = 역할 밖 병합 | OK | OK | OK | 거부 |
| equivalence, old = 역할 밖 병합 | `M..`(M = old 자신, `is-ancestor`는 자기 자신을 참으로) 0개 OK | OK | OK | 거부 |
| test-only, old = 역할 밖 병합 | OK | -- | OK | 거부 |

→ v3.1의 test-only 종료 거부는 사라졌다. N-01로 gate `master` 끝이 병합일 수 있게 됐는데, equivalence 단계 3에서 그 병합이 M으로 잡혀도 범위가 비어 결과는 같다. '후손'이 자기 자신을 포함하는지는 문구에 없다(결과에는 영향 없음, S3 수준).

### 0.2 N-05 판정 환경 파일 (`rv32\pe\cand.py` → `cand.out.txt`, 설치된 pytest 9.0.2)

`_pytest/config/findpaths.py` `locate_config`의 `config_names` = `pytest.toml`, `.pytest.toml`, `pytest.ini`, `.pytest.ini`, `pyproject.toml`, `tox.ini`, `setup.cfg`. 계획 N3.12.2의 `판정 환경` 행(`**/<이름>` 12개: 위 7개 + `conftest.py`·`sitecustomize.py`·`usercustomize.py`·`*.pth`·`.gitattributes`)과 대조하면 **빠진 것 0**.

다만 공격 17의 '후보 대조' 문구 "`locate_config` 후보 이름(**AST의 문자열 상수**)"를 글자대로 구현하면 그 함수의 문자열 상수 10개에 docstring과 `"-"`(`startswith("-")`)가 들어가 대조가 항상 실패한다. `config_names` 대입의 리스트 원소로 좁혀야 한다(S3). 또 §9.2-10은 `jsonschema` 판만 대조하고 `pytest` 판은 대조하지 않아, 설치된 pytest를 올리면(새 설정 이름이 생겨도) 공격 17이 다시 돌 때까지 드러나지 않는다. 계획 U-38 행은 여전히 `jsonschema`만 적는다(S3).

### 0.3 N-03·N-04 V4 (2) (`v4.py`는 저장소 루트에서 실행, 추가 케이스는 `rv32\v4b\v4b.py`가 `v4.py`를 import → `v4b.out.txt`)

**재현**: 저장소 루트에서 `python .../v4_rule_probe/v4.py` 실행 뒤 `git -C <repo> diff --stat -- v4_rule_probe`가 비었다(`v4.out.txt` 바이트 그대로). 31케이스 = FAIL 20·PASS 6·known_limit 4(F1·F2·F3 `sum()`·튜플)·`UNJUDGED` 1 -- §10·공격 23 문장과 일치. review31의 probe 결함(N-09)도 고쳐졌다: assert 시점 환경(데이터 흐름), `kwonlyargs` 결합, `**kw` → `UNJUDGED`(예외 없음), 같은 모듈에 없는 피검 함수(메서드 등) → `funcs.get` → `UNJUDGED`.

**새 정규화를 깨는 입력**:

| 입력 | 결과 | 목적상 기대 | 분류 |
|---|---|---|---|
| FP1 `vdd = 1.8; vin = 0.5 * vdd; assert clamp(vin, 0.0, vdd) == approx(vin)` (무발동 값) | **FAIL** | PASS | 거짓 양성 -- 잎 판정을 **인자 결합 뒤**에 해서, 통과 경로 `return x`가 인자 식 `0.5*1.8`이 되어 연산자를 가진다 |
| FP2 단위 이득 `vin = 0.5 * 1.8; assert vout(vin) == approx(vin)` | **FAIL** | PASS | 같음(`vin * 1.0` → 항등원 제거 → `0.5*1.8`) |
| FP3 `assert buf(2.0 * 3.0) == approx(2.0 * 3.0)` (`return x`) | **FAIL** | PASS | 같음 |
| FP4 `f(x, k1=2.0, k2=3.0): return x*k1*k2`, `assert f(y) == approx(6.0 * y)` (명세 이득 6) | **FAIL** | F1 성격(손으로 접은 리터럴 -- 설계가 PASS로 두는 부류) | 이름이 있는 곱의 계수 모으기 = 상수 접기 |
| FP5 제곱 법칙 `0.5*kp*(w/l)*vov**2` 대 명세 계수 `4e-6 * W / L` | PASS | FP4와 같은 부류 | **부동소수 반올림 덕분**: `0.5*200e-6*0.2*0.2` = `4.000000000000001e-06` ≠ `4e-06`. FP4와 같은 모양인데 판정이 숫자 반올림에 달렸다 |
| FN1 `return a*b*c*x`, `f(y, 0.1, 0.2, 0.3) == approx(y*0.3*0.2*0.1)` (교환 재배열) | **PASS** | FAIL(§10이 교환 재배열은 FAIL이라 주장) | 계수를 인자 순서대로 곱해 `0.006000000000000001` 대 `0.006` -- v3.1에서는 숫자 인자를 정렬해 FAIL이었을 식이 v3.2 계수 모으기로 빠진다 |
| FN3 `return -(b + c)` 대 `-p - q` | PASS | FAIL | 단항 마이너스를 합 위로 분배하지 않는다(`a - (b+c)` 대 `a - b - c`는 FAIL -- 대조군). 적히지 않음 |
| FN4 `for gm in (...): assert gain(gm, 50e3) == approx(gm * 50e3)` | **출력 없음**(`[]`) | FAIL 또는 `UNJUDGED` | `_assert_pairs`가 test 본문 **맨 위 문장만** 본다 -- `for`·`with`·`if` 안의 assert는 FAIL도 `UNJUDGED`도 아니다. V4 (3)은 if·try만 본다 |
| FN5 `with ctx(): assert …` 재서술 | 출력 없음 | 같음 | 같음 |
| FN6 `np.testing.assert_allclose(gain(…), 2e-3 * 50e3)` | 출력 없음 | 같음 | assert 문이 아닌 판정 함수(수치 test에서 흔함) |
| FN7 test 쪽 `e = 2e-3; e *= 50e3` | PASS | FAIL | 피검 쪽은 `AugAssign`을 인라인하는데 test 쪽은 불투명 이름 -- 비대칭 |
| FN8 `assert gp(2.0, 3.0) * 1 == approx(2.0 * 3.0)` | `no-subject-call` | FAIL | 피검 호출이 식 안에 있으면 짝을 못 찾는다. 출력 값 `no-subject-call`은 설계에 없다(§10은 `UNJUDGED`만 정의, 공격 23의 튜플 케이스도 이 값) |
| 대조군: `abs(b - a)` 순서, `approx(…, rel=)`, 연쇄 비교(`UNJUDGED`) | 기대대로 | | |

→ N-03의 원 케이스(리터럴 인자)는 고쳐졌지만 **인자가 식이면 같은 거짓 양성이 그대로**다(FP1~FP3). spec card의 '무동작 판정 입력'은 보통 test 지역 변수로 쓰므로 흔한 모양이다. 그리고 N-04 수정으로 넣은 계수 모으기는 부동소수 곱이라 **순서·반올림에 따라 판정이 갈린다**(FN1 회귀, FP4 대 FP5 불일치). FAIL이 '확실한 복사'라는 §10의 전제가 FP1~FP4에서 깨지고, `for`·`with`·판정 함수 안의 재서술은 FAIL도 `UNJUDGED`도 아니어서 F1~F5 목록 밖이다.

---

## 1. N-01~N-14 판정

| ID | 등급(31) | 판정 | 근거 |
|---|---|---|---|
| N-01 | S2 | **새 결함 도입** | 역할 밖 커밋·병합 규칙이 EL3(§8.2-1·3(라))·EL4(§9.2-3·4)에서 통일됐고 O1(역할 밖 병합)·O4·O4b(역할 push에 섞임 거부)·A19b 원형(O2) 거부는 규칙대로다. 그러나 '첫 부모와 역할 경로가 같다'만 보므로 **부모 순서를 뒤집은 A19b**(O3, O3b: `anc`에서 `git merge --no-ff -s ours <old>`)가 EL3·EL4를 모두 통과해 spec card·test·`gate_config.json`을 지운다(§0.1) -- 아래 M-01 |
| N-02 | S1 | **해결** | audit 범위 "M이 있으면 `M..HEAD`, 없으면 `role/test/<id>..HEAD`, 최대 1개". 세 판정 유형의 단계 3·6·7 모두 통과, audit 커밋 둘은 거부, gate 끝이 역할 밖 병합인 경우도 통과(§0.1). 공격 20 (e)에 세 유형 명시 |
| N-03 | S2 | **부분** | 리터럴 인자의 잎 하나 경로(`clamp(5,0,10)`, `area(0)`, 단위 이득 리터럴)는 PASS가 됐다. 그러나 잎 판정이 인자 결합 뒤라 인자가 식이면 같은 거짓 양성(FP1~FP3) -- M-02 |
| N-04 | S2 | **부분 + 새 결함 도입** | 요구한 비교 형태(`<=`, 상대 오차, approx 양쪽, `isclose` 양 순서, `AnnAssign`), 단항 마이너스, `x/2` 대 `x*0.5`, `1/x` 대 `x**-1`, `UNJUDGED` 정의와 auditor 대조(로더 규칙 10)가 들어갔고 모두 재현된다. 그러나 계수 모으기가 부동소수 순서에 의존(FN1 회귀, FP4·FP5, M-03)하고, `for`·`with`·판정 함수 안의 assert가 출력 없이 빠진다(FN4~FN6, M-04) |
| N-05 | S1 | **해결** | 행 3개 추가로 pytest 9.0.2 후보 7개 전부 덮음(§0.2). `requirements.txt`에 pytest 고정과 후보 대조. 대조 문구·판 드리프트는 S3 |
| N-06 | S2 | **해결** | 생략 캐시 제거, 세션마다 전 구간 재판정, 공격 22 (f). 공격 22 기대 열에 (f)가 없고, 재판정 비용이 로그 길이에 비례하는데 ⑤ 측정 뒤 결정 규칙이 없다(S3) |
| N-07 | S2 | **해결** | '저장소 내부' 행에 캐시 읽기·실행 두 형태 예외, 쓰기 대상은 거부, 공격 10c 확장. PowerShell `$env:PYTHONPATH = …` 형태와 "맨 앞에"가 뜻하는 목록 값(`<캐시>;<기존>`)을 예외가 덮는지 문구에 없다(S3) |
| N-08 | S3 | **해결** | 리다이렉트 연산자 목록과 `&` 예외, 줄 이음 삭제(따옴표 밖·큰따옴표 안), 공격 24 (f)(g). `\|&`는 목록에 없다(S3) |
| N-09 | S3 | **해결** | §0.3 첫 문단 |
| N-10 | S3 | **해결** | `00-common` CC-1 행이 "diff·`staged_diff`·`plan_tables` 해시 재계산, red·outputs는 형식만"으로 §8.1과 일치 |
| N-11 | S3 | **해결** | 계획 N4.3 24가 05 §13.2 24와 같은 일곱 형태·"앞 셋 허용, 뒤 넷 거부". 계획 U-15가 "subagent의 `cwd`는 세션 시작, 메인 세션은 `cd`를 따라감"으로 05 §5와 일치 |
| N-12 | S3 | **해결** | 05 공격 10b에 '판정 환경 이름은 다른 skill에서도 통과 아님', 공격 17에 '재생 데이터는 실행 중 임시 저장소' |
| N-13 | S3 | **해결** | 행 2가 "값이 `remote.gate.url`의 접두인 `url.<base>.insteadOf`·`pushInsteadOf`"만 실패로 -- `insteadOf` 의미(값 = 바꿀 URL 접두)와 맞다 |
| N-14 | S3 | **해결** | §13.4 ②에 settings 수동 수정, 절 순서 §13.3 → §13.4 |

집계: **해결 11**(N-02·05·06·07·08·09·10·11·12·13·14) / **부분 1**(N-03 → M-02) / **부분 + 새 결함 도입 1**(N-04 → M-04, M-03) / **새 결함 도입 1**(N-01 → M-01) / **미해결 0**.

---

## 2. 새 결함과 잔여

### M-01 [S1] 부모 순서를 뒤집은 되돌림 병합이 '역할 밖 병합'으로 EL3·EL4를 통과한다 (N-01 수정이 만든 것)
* **위치**: 05 §8.2-3 (라) "staged 트리와 `HEAD` 트리가 `overlaps_any` 경로 전부에서 같을 때만 통과", §9.2-3 "병합 트리와 첫 부모 트리가 … 같다", §19 '역할 밖 병합' 행.
* **근거**: §0.1 O3·O3b. 오케스트레이터(메인 세션)가 `git checkout <old의 조상>` → `git merge --no-ff -s ours master`(트레일러 없이) → `git checkout master` → `git merge --ff-only <그 병합>` → `git push gate master:master`. 병합의 첫 부모가 조상이므로 역할 경로는 첫 부모와 같고(규칙 통과), 트리는 조상 트리라 그 뒤 반영된 test·spec card·`gate_config.json`·엔진 소스 변경이 모두 되돌아간다. 새 커밋은 병합 하나(O3b)라 §9.2-3의 커밋별 검사에 걸릴 것도 없다. EL1 §6.2 거부 목록에 이 명령들이 없다. review30 A19b(N3.12.0 '막는다'의 '흐름 밖 병합', 계획 공격 19 "조상에서 갈라진 부모로 되돌리는 병합")와 결과가 같다.
* **수정**: 역할 밖 병합 조건에 **"첫 부모가 `old`(EL3는 gate `master`)의 후손이거나 같다"**를 더한다(EL4: `merge-base --is-ancestor <old> <병합^1>`, EL3: `HEAD`가 `gate/master`의 후손). `fixcheck.py`에서 O3·O3b 거부, O1과 '오래된 조상에서 갈라진 RTL 브랜치를 현재 master에 합치는 병합' 통과를 확인했다. '모든 부모의 역할 경로가 같다'는 뒤 경우를 오거부하므로 쓰지 않는다. 공격 19에 (f) 부모를 뒤집은 되돌림 병합(`-s ours`, 새 커밋 없음)을 넣는다.

### M-02 [S2] 잎 하나 경로 제외가 인자 결합 뒤에 판정돼 식 인자의 통과 경로가 여전히 FAIL (N-03 잔여)
* **위치**: 05 §10 ⑤ "연산자를 하나 이상 가진 E_i", §19 V4 (2) 행, `v4.py` `judge`의 `_is_leaf(canon(e))`(e = 결합 뒤 식).
* **근거**: §0.3 FP1~FP3. §10 ⑤의 괄호 "잎 하나(매개변수·상수)로 끝나는 return 경로"는 결합 **전** return 식으로 읽히는데 ②·§19·probe는 결합 **뒤** E_i로 판정한다 -- 문구도 둘로 읽힌다. 단위 이득(FP2)은 결합 전 return이 `vin * gain`이라 결합 전 판정으로도 안 풀린다.
* **수정**: "E_i의 정규형이 결합된 인자 식 하나의 정규형과 같으면(입력을 그대로 돌려주는 경로) 비교하지 않는다"로 규칙을 바꾸고 §19 식도 맞춘다. 공격 23에 FP1~FP3를 PASS 기대로.

### M-03 [S2] 이름이 있는 곱의 계수 모으기가 부동소수 곱이라 판정이 순서·반올림에 달렸다 (N-04 수정이 만든 것)
* **위치**: 05 §10 ④ "곱에 이름·식 인자가 있으면 숫자 인자를 계수 하나로(`x/2` = `x*0.5`)", `v4.py` `_prod`.
* **근거**: §0.3 FN1(교환 재배열이 PASS -- §10이 FAIL로 주장하는 부류), FP4(손으로 접은 명세 계수 `6.0*y` FAIL) 대 FP5(같은 부류가 반올림 차이로 PASS). "숫자만의 식은 접지 않는다"(손으로 계산한 리터럴은 F1으로 PASS)와 "이름이 있으면 접는다"가 같은 기대값 부류에 다른 답을 준다.
* **수정**: 숫자 인자를 곱하지 말고 **정렬한 다중집합**으로 두되 나눗셈만 역수(`fractions.Fraction(repr(v))`의 역수)로 바꾼다 -- `x/2` = `x*0.5`는 유지, 교환 재배열은 순서 무관 FAIL, `6.0*y` 대 `2.0*3.0*y`는 F1과 같게 PASS. 또는 계수를 `Fraction`으로 정확히 곱해 순서 무관하게 하고 "이름이 있는 곱의 손 계산 계수는 FAIL"을 의도로 적는다. 어느 쪽이든 공격 23에 FN1·FP4·FP5를 넣는다.

### M-04 [S2] `for`·`with` 안의 assert와 판정 함수 호출은 V4 (2) 출력이 없다 (N-04 잔여)
* **위치**: 05 §10 ①(assert 비교만, `UNJUDGED` 정의), F1~F5, `00-common` §8.1 로더 규칙 10("`UNJUDGED`로 낸 assert 포함"), 계획 N4.2 V4 (2)·(3).
* **근거**: §0.3 FN4~FN6. 재서술이 루프(`for gm in …`)·`with` 블록 안이거나 `np.testing.assert_allclose`로 쓰이면 FAIL도 `UNJUDGED`도 나오지 않는다. V4 (3)은 if·try 안만 본다. §10은 auditor가 메울 범위를 F1~F5로 알려 주는데 이 부류는 거기에 없다. (FN7 test 쪽 `AugAssign`, FN8 식 안의 피검 호출, 출력 값 `no-subject-call` 미정의는 같은 목록 문제의 S3.)
* **수정**: 본문을 재귀로 걸어 모든 `Assert`를 모으고, 제어 흐름 안의 것(루프 변수 등 불투명 이름)은 판정하되 못 하면 `UNJUDGED`, `assert_allclose`·`assert_almost_equal`·`assertAlmostEqual`류를 비교 형태에 넣거나 `UNJUDGED`로. `no-subject-call`을 설계 출력값으로 정의(auditor 대조 대상 포함)하고 F 목록에 FN3·FN7·FN8을 적는다. 공격 23에 넣는다.

### M-05 [S2] 계획 N3.12.3·N3.12.4와 05 §19가 '역할 밖 병합'을 반영하지 않았다 (N-01 반영 누락)
* **위치**: 계획 N3.12.4 EL4 행("…그 밖의 병합 커밋은 거부"), N3.12.3 7("병합 커밋은 변경 한 건 구조의 병합 … 일 때만 받는다"), N4.3 공격 19(오거부 0은 "N3.12.3 순서 6 병합"만), N4.3 공격 10b(쓰기만), 05 §19 '병합 커밋' 행("변경 한 건의 M일 때만 … 그 밖의 병합 거부") ↔ 05 §8.2-3 (라)·§9.2-3·§19 '역할 밖 병합' 행·공격 19 (e)·10b.
* **근거**: 05 §4.3은 "정의는 계획 N3.12.4 EL3(v5.19)가 정본"이라 하고, §20 '함께 덮는 개정'의 review31 목록에도 N3.12.3·N3.12.4가 없다. 정본과 설계가 병합 허용 범위에서 반대 답을 낸다. 05 §19 안에서도 두 행이 모순이다.
* **수정**: 계획 N3.12.4 EL3·EL4, N3.12.3 7, N4.3 10b·19, 05 §19 '병합 커밋' 행을 M-01 조건까지 넣어 고치고 §20 목록에 적는다.

### S3
* **M-06** §8.2-2 "`code`·`test`·`audit`과 **병합 커밋은** `Change-Id` 정확히 하나"가 (라) "트레일러 불필요"와 부딪힌다(2 → 3 순서라 글자대로면 역할 밖 병합이 EL3에서 막힌다). 2의 병합 문구를 "(가)의 M은"으로.
* **M-07** 역할 밖 병합의 부모 수(octopus, O5 통과)를 정하지 않았다.
* **M-08** 공격 17 후보 대조의 "AST의 문자열 상수" → `config_names` 리스트 원소로(§0.2). §9.2-10에 `pytest` 판 대조를 넣거나 판 드리프트를 세션 시작 대조에, 계획 U-38 행에 pytest 고정 반영.
* **M-09** N-07 예외가 PowerShell `$env:PYTHONPATH = '<캐시>'`와 목록 값(`<캐시>;<기존>`)을 덮는지.
* **M-10** 공격 22 기대 열에 (f) 없음. 재판정 비용 측정 뒤 한계를 넘으면 어떻게 할지(예: 부트스트랩 이후 줄 수 상한 경고) 없음.
* **M-11** 분해기 리다이렉트 목록에 `|&`(bash의 `2>&1 |`)가 없어 `|` 뒤 `&`로 빈 명령이 생긴다.
* **M-12** §7 "M이 `role/test/<id>`의 후손"에 '같음 포함' 여부. 결과에는 영향 없음(§0.1).
* **M-13** 계획 공격 23 "알려진 놓침은 PASS로 고정" ↔ 05 공격 23(known_limit 중 튜플은 `no-subject-call`, `UNJUDGED` 1).

---

## 3. 계획 · `00-common` · 05 사이 새 모순

| # | 곳 | 내용 | 항목 |
|---|---|---|---|
| 1 | 계획 N3.12.4 EL4·N3.12.3 7·N4.3 19·10b ↔ 05 §8.2-3 (라)·§9.2-3·4·공격 19 (e)·10b | 역할 밖 병합 허용 여부 | M-05 |
| 2 | 05 §19 '병합 커밋' 행 ↔ 05 §19 '역할 밖 병합' 행 | 같은 표 안에서 반대 | M-05 |
| 3 | 05 §8.2-2 ↔ §8.2-3 (라) | 병합 커밋의 `Change-Id` 필수 여부 | M-06 |
| 4 | 05 §10 ⑤ 괄호(결합 전 return 경로) ↔ §10 ②·§19·`v4.py`(결합 뒤 E_i) | 잎 판정 시점 | M-02 |
| 5 | 05 §10 ④ "숫자만의 식은 접지 않는다"(F1 PASS) ↔ 같은 ④ 이름 있는 곱의 계수 모으기 | 손 계산 계수의 판정 | M-03 |
| 6 | 계획 U-38 행(`jsonschema`만) ↔ 05 §9.3 의존성 선언(`pytest==` 추가)·§9.2-10(`jsonschema`만 대조) | 고정 의존성 목록 | M-08 |
| 7 | 계획 N4.3 23 ↔ 05 §13.2 23 | known_limit 출력 값 | M-13 |

확인한 일치: 계획 N3.12.2 `판정 환경` 12행 ↔ pytest 9.0.2 후보; 계획 N4.2 V4 (2) ↔ 05 §10 (잎 제외·`UNJUDGED`·F 목록 요지); `00-common` 로더 규칙 10 ↔ 05 §10 F5; `00-common` CC-1 ↔ §8.1; 계획 N4.3 24 ↔ 05 24; 계획 U-15 ↔ 05 §5; 05 §3.3 행 2·3 ↔ 공격 21·22; §13.3 → §13.4 순서; 공격 개수 28 / 0.5 25는 이번 커밋이 바꾸지 않음.

---

## 4. 집계와 판정

| 구분 | 건수 | 항목 |
|---|---|---|
| N 해결 | 11 | N-02·05·06·07·08·09·10·11·12·13·14 |
| N 부분 | 1 | N-03(→M-02) |
| N 부분 + 새 결함 도입 | 1 | N-04(→M-04 잔여, M-03 새 결함) |
| N 새 결함 도입 | 1 | N-01(→M-01) |
| N 미해결 | 0 | |
| 새 S1 | 1 | M-01 |
| 새 S2 | 4 | M-02, M-03, M-04, M-05 |
| 새 S3 | 8 | M-06 ~ M-13 |

review31의 S1 둘(N-02·N-05)은 실측으로 닫혔고 문구 동기화 S3 대부분도 닫혔다. 그러나 N-01 수정이 연 '역할 밖 병합' 통로가 첫 부모만 보고 판정해, A19b와 같은 되돌림을 부모 순서만 바꿔 EL3·EL4 모두 통과시킨다(M-01, 조건 한 줄로 닫힘 -- 수정안 실측 확인). V4 (2)는 목표 케이스가 모두 재현되지만 거짓 양성이 인자 모양만 바꾸면 남고(M-02), 계수 모으기가 부동소수 순서에 의존하며(M-03), 제어 흐름 안의 assert가 빠진다(M-04). 계획 정본(N3.12.3·N3.12.4)은 병합 규칙 개정을 따라가지 않았다(M-05). 모두 규칙·문장 단위 수정이며 구조 재작성은 필요 없다.

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
?? docs/03-analysis/gain-budget-gmid-sizing-function-audit/review32_05_v3_2.md
?? "skills/analog-gmid-design/assets/\354\225\204\353\202\240\353\241\234\352\267\270 \352\270\260\353\212\245\353\266\204\354\204\235\352\270\260.zip"
?? "skills/analog-gmid-design/assets/\355\232\214\353\241\234\353\217\204 \354\266\224\354\266\234\352\270\260.zip"
?? workspaces/current-reuse-telescopic-ota-report/current_reuse_telescopic_ota.report.html
?? workspaces/current-reuse-telescopic-ota-report/full_netlist_for_grammar.json
?? workspaces/current-reuse-telescopic-ota-report/smoke_run_harness_session18_save.py
$ git -C <repo> log --oneline -1
451fd8f docs(analog-gmid-design): 05-role-separation v3.2 -- review31 반영
$ git -C <repo> config --show-origin --get core.hooksPath
file:.git/config	C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/.githooks
$ git -C <repo> diff --stat
(비어 있음 = 추적 파일 변경 없음, v4.out.txt 포함)
```

시작 시점 git 상태와 같다(추적 파일 변경 없음, 새 파일은 이 보고서 하나). 실제 저장소에서 쓴 git 명령은 읽기 전용(`show`·`log`·`diff`·`status`·`config --get`)뿐이고, `v4.py` 실행은 자기 `v4.out.txt`만 다시 썼다(바이트 동일). 모든 실험 저장소는 `%TEMP%\rv32\el4\repo`에서 `git -C <절대 경로>`로 만들었다.

**판정: 수정 후 승인** -- S1 1(M-01) · S2 4(M-02~M-05) · S3 8(M-06~M-13).
