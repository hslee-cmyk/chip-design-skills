# 독립 검토: Phase 3 DoD 초안 v4s -- 검토 v4r(n-1~n-4) 반영 확인

검토 대상(diff 범위만): `phase3_dod_kit/judge_p3.py`·`judge_e6_selftest.py`·`run_dod.sh`·`_drafts/draft_phase3_dod.md` 대 각 `*.pre-v4s.bak`. 기준 `_drafts/review_phase3_dod_v4r.md` §4 n-1~n-4.
검토자는 작성자가 아니고 v4r 검토자도 아니다. 고친 파일 없음(이 파일만 씀). 실행은 `C:/g405`에서만(TMP/TEMP 그 아래, 셸 `cd` 없음, kit 판정기는 `C:/g405/kit`에 복사해서 실행), 끝에 삭제.

## 판정 요약

- **B(차단): 없음.**
- **S(중대): 없음.**
- **minor: 2건**(m-1 코드, m-2 문서). 둘 다 거짓 PASS가 아니다.
- **거짓 PASS: 0.** 내 합성 입력 34가지(E6 23 + e01 11, 작성자 69가지와 따로 만듦)에서 새 판정기가 PASS를 낸 것은 기대 PASS(V18·V19·V23·G08 E1, E0 PASS들)뿐이다. 옛 판정기(`pre-v4s.bak`)는 G07(H `findings` `""` + F2 base `"x"`)에서 **E1 거짓 PASS**를 냈고 새 판정기는 INVALID다.
- **기대값 5개 변경(R16a·R30a·A11a·A12a·A13a, INVALID → FAIL): 모두 n-1 원칙에서 바로 나오고 약화가 아니다**(§2).
- n-1·n-2·n-3·n-4 모두 반영됐다. E-id마다 판정 줄 정확히 1개: 내 34가지 전부 성립, traceback 0.

## 0. 실측 (`C:/g405`, 2026-10-07)

- 작성자 자체 시험 `judge_e6_selftest.py <out> judge_p3.py.pre-v4s.bak`: **`SELFTEST PASS 69/69`**, rc 0(작성자 주장과 같음).
  옛 판정기와 판정 종류가 다른 것은 정확히 11개: R16a·R30a·A11a·A12a·A13a·D01·D02(옛 INVALID → 새 FAIL), G01·G02·G04·G05(옛 **PASS** → 새 INVALID). 나머지 58개는 옛과 같다. 초안 머리 v4s 줄의 목록과 같다.
- 실제 경로 e01: `863a037`(= 메인 HEAD = gate `master`)의 `skills/analog-gmid-design/assets`+계획 문서를 `git archive`로 풀고 같은 판 `tools/gates/import_layering.py`를 돌린 출력(exit 0, `findings: []`, `present` 1/10)에 새/옛 판정기를 돌렸다 → 두 출력 **바이트 같음**(md5 `956dedd…`): `E0 FAIL present 1/10 …`, `E1 PENDING(E0 미충족 …) exit=0 findings=0`. E6은 `move_plan.py` 없음으로 실제 경로가 아직 PENDING이라 합성 입력으로만 봤다.
- `run_dod.sh`: `bash -n` OK. diff는 머리 이력 두 줄(15·16행)과 e6 주석 한 줄(182행)뿐 -- **명령 줄 변화 0**.
- 메인 저장소: 전후 HEAD `863a037`, status `--ignored` 177줄 `diff` 같음, reflog 359줄 같음. kit 파일 sha256 전후 같음, `__pycache__` 0.

## 1. 코드 변경 확인 (`judge_p3.py`)

- **PASS 경로 불변.** PASS는 `why == []`(거부 확인 성립) 그리고 `fail == False`(rc `"0"`·비지 않은 발견 없음)일 때만이다. `_e6_reject_check`의 조건을 v4r 한 줄 조건과 대조했다: `nrc != "1"` ↔ `exit≠1`, `nabs` ↔ `없는 종류 키`, `ids is None` ↔ `changed 원소 모양 모름`, `len != len(ids)` ↔ `changed 중복`, `not allow <= ids` ↔ `허용 id 빠짐`, `ids - allow != mids` ↔ `changed 차이`, `not same_rest` ↔ `나머지 발견 다른 종류`(합집합 키에 `.get` 비교 -- 한쪽에만 있는 키도 잡아 v4r dict 비교와 같다), `mids is None`은 앞으로 옮겨 INVALID. 출력 없음·`findings` 사전 아님·값 목록 아님도 그대로 불성립. **조건 집합이 v4r과 같다**(약화 없음).
- 바뀐 것은 불성립일 때의 분기 하나: `fail`이면 FAIL, 아니면 INVALID. 이는 v4r 검토 n-1 제안 문안 그대로다.
- e01: H `findings` 목록 아님 → E1 INVALID(E0 판정 줄 뒤, `miss` PENDING보다 앞), F2 base `findings` 목록 아님 → E1 INVALID. n-2 제안 그대로.
- 조건 이름(n-3)이 정확한지: 각 이름이 실제로 깨진 절과 1:1이다(N01~N04, 내 V05·V12·V13·V20·V21·V22에서 확인 -- 예 V21 `[A1, A2, A1, A2]` → `changed 중복 2`, V20 → `changed 차이(허용 두 id 밖) 거부 쪽만 [] 허용 쪽만 [A1]`, V05 → `exit≠1(exit=0); 나머지 발견 다른 종류 ['lost']`). 거부 쪽에 종류 키가 없으면 `없는 종류 키`와 `나머지 발견 다른 종류`가 같은 키로 두 번 나온다(R18) -- 틀린 말은 아니고 중복일 뿐.

## 2. 기대값 5개 변경 (R16a·R30a·A11a·A12a·A13a: INVALID → FAIL)

다섯 모두 허용 있는 실행 rc `"1"` + 비지 않은 발견(`newkind` 1 / `lost` 1·`rebind` 1 / `lost`·`rebind` / `import-dup` 1 / `zzz` 1)이고 거부 확인은 `OK_N`(exit 1, `changed` = 정확히 두 허용 id)이라 깨진 조건은 `나머지 발견 다른 종류` 하나다. n-1 원칙("허용 있는 실행이 이미 FAIL 모양이면 거부 확인 불성립을 덧붙여 FAIL, PASS 모양일 때만 INVALID")을 그대로 적용하면 **FAIL**이 나온다 -- 원칙에서 바로 나온다.

약화가 아닌 이유:
1. 다섯 다 옛·새 어느 쪽도 PASS가 아니다. DoD 종합 판정(E6이 PASS가 아니면 통과 아님)은 같다.
2. 거부 확인의 목적은 공허 PASS 막기뿐이다(v4r §3·n-1). 허용 있는 실행 자체가 비지 않은 발견을 내면 공허 PASS가 생길 수 없으므로 INVALID(재측정)로 둘 근거가 없다.
3. det3 모양(허용 있는 쪽에만 `lost`·`rebind` -- 도구 계약 위반)이 FAIL로 돌아가는 것은 v4r n-1이 미리 적은 결과이고 그 검토가 받아들였다. 줄에 `거부 확인 불성립(나머지 발견 다른 종류 [...])`이 붙어 읽는 사람이 도구 쪽 원인도 볼 수 있다.
4. 기대값이 PASS 쪽으로 움직인 케이스는 하나도 없다(diff 확인: CASES의 기대 열 변경은 이 5개뿐, 추가된 D·N·G는 새 케이스).

D01·D02(삭제된 허용 id, v4r V07)도 같은 원칙으로 FAIL이고 D03(허용 있는 실행 PASS 모양 + 허용 id 빠짐)은 INVALID로 남아 공허 PASS 막기가 살아 있음을 보인다.

## 3. 내 합성 입력 (`C:/g405/mine/vt.py`, 작성자 69가지와 따로)

E6(23가지, 새 / 옛, E6 판정 줄 수는 모두 1, traceback 0):

| # | 입력 | 새 | 옛 |
|---|---|---|---|
| V01 | **허용 있음 exit 2·발견 전부 빈 목록**, 거부 확인 정상 | FAIL | FAIL |
| V02 | **허용 있음 exit 2·빈 발견, 거부 확인 파일 없음** | FAIL | INVALID |
| V03 | 허용 있음 exit 1·빈 발견, 거부 확인 없음 | FAIL | INVALID |
| V04 | **허용 있음 FAIL(`lost` 1) + 거부 확인 파일 없음** | FAIL | INVALID |
| V05 | 허용 있음 FAIL + 거부 확인 exit 0 | FAIL(`exit≠1(exit=0); 나머지 발견 다른 종류 ['lost']`) | INVALID |
| V06 | 허용 있음 PASS 모양 + 거부 확인 없음 | INVALID | INVALID |
| V07 | **허용 있음 깨짐**: `lost` 값 문자열 | INVALID | INVALID |
| V08 | 허용 있음 `changed` 원소 모양 모름 + `lost` 발견 | INVALID | INVALID |
| V09 | 허용 있음 최상위 `[1, 2]` | INVALID(판정기 예외) | INVALID |
| V10 | 거부 쪽 최상위 목록, 허용 있음 PASS 모양 | INVALID(판정기 예외) | INVALID |
| V11 | 거부 쪽 최상위 목록, 허용 있음 FAIL 모양 | **INVALID**(판정기 예외) -- m-1 | INVALID |
| V12 | 거부 쪽에만 빈 열거 밖 키 `zzz: []` | INVALID | INVALID |
| V13 | 거부 쪽 `[A1, {"unit": A1}, A2]`(두 모양 중복) | INVALID(`changed 중복 1`) | INVALID |
| V14 | 선언 밖 `changed` X, 두 실행 같음 | FAIL | FAIL |
| V15 | 거부 쪽 `changed`에 `null` | INVALID | INVALID |
| V16 | 거부 쪽 `lost: true` | INVALID | INVALID |
| V17 | 허용 있음 rc `" 0"` | FAIL | FAIL |
| V18 | 올바른 H(`changed` 순서 바뀜) | PASS | PASS |
| V19 | 올바른 H + 최상위 다른 키 | PASS | PASS |
| V20 | 허용 id A1이 허용 있는 실행 `changed`에 남음 | FAIL(`changed 차이 … 허용 쪽만 [A1]`) | INVALID |
| V21 | 거부 쪽 두 id 각 2번 | INVALID(`changed 중복 2`) | INVALID |
| V22 | 거부 rc `"1.0"` | INVALID(`exit≠1(exit=1.0)`) | INVALID |
| V23 | 거부 쪽 `error` 키 + 정상 `findings`(도구 계약 밖, 참고) | PASS | PASS |

e01(11가지, 가짜 GC N3.10 10행; E0·E1 판정 줄 각 정확히 1개, traceback 0):

| # | 입력 | 새 E0/E1 | 옛 E0/E1 |
|---|---|---|---|
| G01 | H `findings: null` | PASS/INVALID | PASS/INVALID |
| G02 | E0 FAIL + H `findings` 문자열 | FAIL/INVALID | FAIL/PENDING |
| G03 | **F2 base `findings: ""`**(H 정상) | PASS/INVALID | PASS/INVALID |
| G04 | F2 base 최상위 `[1]` | PASS/PENDING | PASS/PENDING |
| G05 | F2 base 최상위 문자열 `"findings"` | PASS/INVALID(판정기 예외) | 같음 |
| G06 | H 최상위 `["present"]` | INVALID/INVALID(판정기 예외) | 같음 |
| G07 | **H `""` + F2 base `"x"`(둘 다 목록 아님)** | PASS/**INVALID** | PASS/**PASS(거짓)** |
| G08 | 정상(F2 base exit 0) | PASS/PASS | 같음 |
| G09 | H 위반 1 | PASS/FAIL | 같음 |
| G10 | H exit 1·빈 발견 | PASS/FAIL | 같음 |
| G11 | H `findings` 사전, F2 base 없음 | PASS/INVALID | PASS/INVALID |

결과: **34/34 기대와 같음, 새 판정기 거짓 PASS 0**, 모든 깨진 입력에서 E-id마다 판정 줄 1개.

## 4. 문서 대조

- 초안 §5 8행 v4s 문장 = 코드 분기(FAIL 모양 → 불성립 덧붙여 FAIL, PASS 모양일 때만 INVALID). §6 E6 거부 확인 행도 같다. "FAIL 모양 = exit ≠ 0 또는 비지 않은 발견"은 코드 `fail = rc != "0" or bool(nz)`와 같다.
- 단, 문장 "불성립이어도 E6 FAIL"에는 코드가 지키지 않는 예외 두 가지가 있다: (i) 허용 있는 실행 자체를 못 읽으면(값 목록 아님·`changed` 원소 모양 모름·종류 키 없음) INVALID -- 이것은 '판정 실행을 못 읽음'이라 타당하고 코드 주석에도 있다. (ii) 거부 쪽 출력이 최상위 사전이 아니면 `_e6_reject_check`의 `n.get`이 예외를 내 `INVALID 판정기 예외`가 된다(V11) -- m-1.
- `run_dod.sh` diff = 주석·이력만(§0). 머리 v4r 줄(n-4) 문구 정정 반영.

## 5. minor

**m-1 -- 거부 쪽 출력이 최상위 사전이 아니면 허용 있는 실행이 FAIL 모양이어도 INVALID(V10·V11).** `_e6_reject_check` 첫 줄 `if n is None or not isinstance(n.get("findings"), dict)`가 `n`이 목록·문자열이면 `AttributeError`를 내고 `main()`이 `E6 INVALID 판정기 예외`로 채운다. PASS가 아니고 판정 줄도 1개라 영향은 분류뿐이지만, §5 8행 문장("불성립이어도 FAIL")과 어긋난다. 고친다면 `if not isinstance(n, dict) or not isinstance(n.get("findings"), dict):`(거부 확인 '출력 없음' 조건으로 들어감 → FAIL 모양이면 FAIL). e6 첫 `d.get`(허용 있는 실행)도 같은 모양이지만 그쪽은 INVALID가 맞다.

**m-2 -- 초안 §8에 v4s 기록이 없고 §8.v4r 끝 줄이 지금 동작과 다르다.** §8.v4r 마지막 항목은 "R16a·R30a·A11a·A12a·A13a … 옛 FAIL → **INVALID**"이고 55/55를 적는다. v4s 결과(69/69, 위 다섯이 FAIL로 돌아감, G01·G02·G04·G05 옛 PASS → INVALID)는 머리 v4s 줄에만 있다. §6 E6 거부 확인 행 끝의 "판정기 합성 입력 확인 §8.v4·§8.v4r"도 v4s를 가리키지 않는다. 고칠 것: §8.v4s 짧은 절(또는 §8.v4r 끝 항목에 "v4s에서 FAIL로 바뀜 -- 머리 v4s 줄" 한 구절)과 §6 참조에 v4s. 머리 v4s 줄의 n-3 조건 이름 목록에 `changed 원소 모양 모름`·`findings 값 모양 모름`·`출력 없음`이 빠진 것도 같이(판정 무관).

참고(판정 무관, 조치 요구 아님):
- V01~V03: 허용 있는 실행이 exit ≠ 0인데 발견이 모두 빈 목록이면 FAIL이다. D0a 계약 1(exit 1 = 목록 하나라도 비지 않음, 2 = 입력 오류)로는 올바른 도구가 낼 수 없는 출력이라 '도구 계약 위반'이고, 거부 확인이 성립할 때 FAIL인 것은 v4r부터 그랬다(R21). v4s는 같은 처리를 거부 확인 불성립 쪽으로 넓혔을 뿐이고 줄에 `exit=2 비지 않은 발견 {}`가 그대로 찍혀 원인을 읽을 수 있다. 원하면 "rc ∉ {0,1} 또는 rc 1인데 발견 0 → INVALID"를 더할 수 있으나 PASS 경로와 무관하다.
- G08: e01 거부 확인은 F2 base exit 값을 보지 않는다(findings > 0만). diff 밖 기존 동작.

## 6. 뒷정리

메인 저장소 쓰기 0(HEAD `863a037`, status `--ignored` 177줄·reflog 359줄 전후 같음). kit 파일 sha256 전후 같음. 쓴 파일은 이 검토 파일 하나. `C:/g405`는 이 파일을 쓴 뒤 삭제했다.
