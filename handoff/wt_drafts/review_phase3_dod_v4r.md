# 독립 검토: Phase 3 DoD 초안 v4r -- 검토 v4(S1·m-a~m-d) 반영 확인

검토 대상: `_drafts/draft_phase3_dod.md`(v4r)·`phase3_dod_kit/judge_p3.py`(v4r) 대 `*.pre-v4r.bak`, 새 `phase3_dod_kit/judge_e6_selftest.py`, `run_dod.sh` 178행 주석. 기준 `_drafts/review_phase3_dod_v4.md` §3 (a)~(c)·§4.
검토자는 작성자가 아니고 `review_phase3_dod_v4.md`를 쓴 검토자도 아니다. 고친 파일 없음(이 파일만 씀). 실행은 모래상자 `C:/g401`에서만 했다(TMP/TEMP 그 아래, 내 명령에 `cd` 없음, 변수는 `env NAME=… bash`로 넘김, run_dod.sh 복제는 kit 그대로 `clone -c core.autocrlf=false`, 끝에 삭제).

## 판정 요약

- **B(차단): 없음.**
- **S(중대): 없음.** 검토 v4 S1은 §3 (c) 문안 **그대로** 들어갔다(`judge_p3.py` 175~188행 = 제안 코드와 줄 단위로 같음). 초안 §5 8행·§6 E6 거부 확인 행도 §3 (a)·(b) 문안 그대로다. 진짜 E6 실패(선언 밖 `changed`, `lost` -- 두 실행 모두에 나옴)는 이제 `E6 FAIL`이다.
- **minor: 4건**(n-1~n-4, 아래). 모두 거짓 PASS가 아니다.
- **거짓 PASS: 0**. 내 합성 입력 52가지(E6 40 + 다른 명령·깨진 인자 12, 작성자 55가지와 따로 만듦)에서 새 판정기가 PASS를 낸 것은 기대 PASS 3건(V01·W11 E0·E1)뿐이다. 옛 판정기(`pre-v4r.bak`)는 이 중 **9건에서 거짓 PASS**(V09·V11a~e·V12·V22·V36)를 냈고 새 판정기는 모두 INVALID다.
- 작성자가 짚은 변경(허용 있는 실행에만 발견 → FAIL에서 INVALID로)은 **받아들일 수 있다**(§3).
- m-b(어떤 깨진 입력에도 E-id마다 판정 줄 정확히 1개): **성립**(내 W01~W12 12가지 모두 E-id마다 1줄, traceback 0). 단 e01의 `findings`가 목록이 아닌 경우는 판정 줄은 남지만 값 검사가 빠졌다(n-2).

## 0. 실측 (모래상자 `C:/g401`, 2026-10-07)

- 작성자 자체 시험 `judge_e6_selftest.py`(옛 판정기 비교 인자 포함): **`SELFTEST PASS 55/55`**, rc 0. 초안 §8.v4r와 같다.
- 내 합성 시험(`C:/g401/mine/verifier_tests.py`, 아래 §2): **52/52 기대와 같음, false_pass [], traceback 0**.
- `run_dod.sh <G> <H> rehearse guard inputs e01 e4 e6 n63 watch`를 두 판에서 돌렸다(kit 무수정, 쓰기는 `C:/g401` 아래만):

| H | 결과 |
|---|---|
| `ae1b588`(초안 §8 표의 판) | `missing` **25**, `N6.3 1 PASS(n=37) \| 2 FAIL(2/20, 기록 없음 1) \| 3 FAIL \| 4 PASS(n=2, 어긋남 0, 덮음 누락 0, 경로 밖 0) \| 5 FAIL`, 관찰 0.5 34·35 `PNNNNNNNNP` audit·merge True, B33·G1 없음 -- **초안 §8 174행·검토 v4 §0과 같다(변화 없음).** E0 FAIL 1/10, E1 PENDING, E4 PENDING, E6 PENDING. |
| `863a037`(지금 gate `master` = 메인 HEAD = `ls-remote`) | G1-H PASS, `missing` **24**, `N6.3 1 PASS(n=38) \| 2 FAIL(3/20, 기록 없음 1) \| 3 FAIL \| 4 PASS(n=3, 어긋남 0, 덮음 누락 0, 경로 밖 0) \| 5 FAIL`, 관찰 0.5 같음. E0·E1·E4·E6 줄은 `ae1b588`과 같다. |

  `ae1b588 → 863a037` 차이는 **저장소 진행 때문이고 kit 때문이 아니다**: `missing`에서 'b26pre 판정 기록'(`2db7622`)과 'backfill spec card 0장'(`863a037`)이 빠지고 'backfill 판정 기록(`20261001-b26-backfill-interdig-final-audit`)'이 새로 들었다(25 − 2 + 1 = 24). N6.3 2번 = card 3장(backfill 추가, `without_record` = backfill), 4번 n=3 = b26pre `Role: test` `e4d5833`(`in_list`)이 더해짐. design 30·계획·`tools/gates` 변경 0(`git diff --stat ae1b588 863a037 -- …` 빈 출력), 블록 `blk_sha256.txt`는 rev 줄만 다르다. `inputs_p3.py`·`n63_p3.py`는 v4r에서 바뀌지 않았다(mtime 10-02·10-06 21:51).
- 새/옛 판정기를 같은 실제 출력(두 판의 `layer.json`·`plan_final.json` 없음)에 돌린 `e01`·`e4` 줄은 바이트 같다(md5 같음). 실제 경로의 판정 줄 변화 0.
- `bash -n run_dod.sh` OK. `set -uo pipefail`(‐e 없음)이라 판정기의 새 종료 코드(예외 1·명령 모름 2)가 실행기를 멈추지 않는다.
- 메인 저장소: 실행 전후 HEAD = gate `master` = `863a037`, status `--ignored` 177줄·reflog 359줄 `cmp` 같음(run_dod `watch` W1~W3 PASS 두 번). kit 파일 30개 sha256 전후 같음, `__pycache__` 생성 0. 역할 브랜치 3개(`role/*/20261001-b26-backfill-interdig-final-audit` = `3004096`)는 이 검토 밖 주체다 -- 메인에는 `git -C` 읽기만 했다.

## 1. S1 반영 확인 (검토 v4 §3)

| 요구 | `judge_p3.py` v4r | 확인 |
|---|---|---|
| 거부 확인 exit 1 | `nrc != "1"` → INVALID | V04·V05·V27(`"01"`) INVALID |
| 허용 두 id ⊆ `changed` | `not allow <= ids` | V06·V08·V14~V17(유사 문자) INVALID |
| 중복 없음 | `len(nf["changed"]) != len(ids)` | V12(5만 개 중복)·V36 INVALID(옛 PASS) |
| 거부 확인 발견 − 두 id = 허용 있는 실행 발견 | `ids - allow != mids`, `same_rest`(changed 밖 모든 키·값 같음) | V02(거부 쪽에만 `lost`)·V03(거부 쪽에만 셋째 id)·V22·V23·V32·V35 INVALID |
| 판정은 허용 있는 실행 | `nz`·`rc`를 `mf`에서 | V13·V21·V24·V25·V26·V29 FAIL, V01 PASS |

- 문안 대조: 초안 §5 8행 v4 문장 = §3 (a), §6 E6 거부 확인 행 '기대' = §3 (b), §4 E6 행 끝 문장도 같은 뜻으로 고쳤다. kit 머리 docstring(10~12·19~20행)도 같다.
- PASS가 나오는 유일한 모양: rc `"0"`, 허용 있는 실행 모든 값이 빈 목록, 거부 확인 rc `"1"`, `changed` 단위 = 정확히 두 허용 id(중복 없음), 나머지 키·값 두 실행 같음. 이는 D0a 단계 `allow-changed-declared` (2) 모양 그대로이고 공허 PASS 경로가 없다.

## 2. 내 합성 입력 (작성자 55가지와 따로, `C:/g401/mine/verifier_tests.py`)

E6 40가지(허용 있음 / 허용 없음 → 새 / 옛):

| # | 입력 | 새 | 옛 |
|---|---|---|---|
| V01 | 올바른 H(빈 / 두 id rc 1) | PASS | PASS |
| V02 | **허용 있음 깨끗, 거부 쪽에만 관계없는 `lost` 1** | INVALID | INVALID |
| V03 | 허용 있음 깨끗, 거부 쪽에만 선언 밖 `changed` | INVALID | INVALID |
| V04·V05 | **거부 확인 exit 0**(두 id / 빈 목록) | INVALID | INVALID |
| V06 | **허용 id가 거부 쪽 `changed`에 없음**(둘 다 [X]) | INVALID | INVALID |
| V07 | 허용 id A1 삭제(`lost` A1 두 실행, 거부 쪽 `changed` = [A2]) | INVALID | INVALID -- n-1 |
| V08 | 허용 id 하나만 + X | INVALID | INVALID |
| V09 | 허용 있음 `changed: null` | INVALID | **PASS** |
| V10 | 거부 쪽 `rebind` 사전 | INVALID | INVALID |
| V11a~e | **목록 아닌 거짓 값**(`""`·`null`·`0`·`{}`·`false`) 두 실행 | INVALID | **PASS ×5** |
| V12 | **거대 중복** 거부 쪽 [A1]×50000 + A2 | INVALID | **PASS** |
| V13 | 허용 있음 [X]×1000 rc 1 / 두 id + X | FAIL | INVALID |
| V14~V17 | **유니코드·공백 id**(전각 `：：`, 폭 없는 공백, 끝 탭, 대문자) | INVALID | INVALID |
| V18~V20 | `findings` 목록 / 최상위 `[]` / 최상위 문자열 | INVALID(19·20은 `판정기 예외`) | INVALID / traceback·판정 줄 없음 |
| V21 | 열거 밖 종류 1 두 실행, rc 0 | FAIL | INVALID |
| V22 | 허용 있음에만 빈 `zzz: []` | INVALID | **PASS** |
| V23 | 허용 있음이 A1을 지우지 못함 | INVALID | FAIL |
| V24 | rc 0인데 `changed` [X] | FAIL | INVALID |
| V25·V26·V29 | rc 1·`"00"`·2(깨끗한 JSON) | FAIL | FAIL |
| V28·V30·V34 | 마지막 줄 깨짐 / BOM / 두 파일 없음 | INVALID | INVALID |
| V31 | `unit` 정수 | INVALID | INVALID |
| V32 | 같은 발견, 두 실행 순서 다름 | INVALID | INVALID |
| V33 | 거부 쪽 종류 키 없음 | INVALID | INVALID |
| V35 | 허용 있음에만 `lost` 1(작성자가 짚은 모양) | INVALID | FAIL |
| V36 | 거부 쪽 [A2, A1, A2] | INVALID | **PASS** |

다른 명령·깨진 인자 12가지(E-id마다 판정 줄 수 셈):

| # | 입력 | 새(줄 수) | 옛 |
|---|---|---|---|
| W01·W02 | `e6` 인자 0개·6개 | E6 INVALID ×1 | traceback, 줄 0 |
| W03 | 명령 `E6`(대문자) | `E? INVALID` ×1, rc 2 | traceback |
| W04 | e2, card 하나 V3 출력이 키 이름들을 담은 **문자열**(`k in str` 부분 문자열 통과 → `v3["defs"]` TypeError) | E2 INVALID ×1(앞 `E2 ③` 줄은 판정 줄 아님) | traceback |
| W05 | e2, card 하나 `moved_units` 정수 | E2 INVALID ×1 | traceback |
| W06·W07 | e4 plan 최상위 `[]` / `assignment` 값 정수 | E4 INVALID ×1 | traceback |
| W08 | e01(가짜 GC 10행) `findings` 정수 | **E0 PASS ×1 + E1 INVALID ×1** | E0만, traceback |
| W09 | e01 `present` 정수 | E0 INVALID ×1 + E1 INVALID ×1 | traceback |
| W10 | e01 F2 base `findings` 정수 | E0 PASS + E1 INVALID | E0만, traceback |
| W11 | e01 정상(거부 확인 F2 base 1) | E0 PASS + E1 PASS | 같음 |
| W12 | e2 cards.txt 빈 파일 | E2 PENDING ×1 | 같음 |

`main()`이 함수 출력을 버퍼에 받아 판정 줄 정규식(`^(E\d+b?) (PASS|FAIL|INVALID|PENDING)\b`)으로 이미 말한 ID를 세고 빠진 ID만 채우므로, 앞서 한 ID를 말하고 뒤에서 예외가 나도 중복 줄이 생기지 않는다(W08·W10). `E2 ③` 일관성 줄은 정규식에 걸리지 않는다.

## 3. 작성자가 짚은 변경 -- 허용 있는 실행에만 발견 → INVALID (옛 FAIL)

**받아들일 수 있다.** 근거:
1. 검토 v4 §3 (a)("두 실행이 어긋남 → E6 INVALID")·(c)(`same_rest`) 문안 그대로다 -- 작성자가 문안을 넘어 바꾼 것이 아니다.
2. D0a 계약 4(`draft_p3_d0a.spec.md` 178~181행): `--allow-changed`는 허용 id를 `changed` 목록에만 적지 않고, `lost`·`rebind` 예외는 그 단위를 포함해 두 실행에서 같게 정의된다. 그래서 올바른 도구에서 두 실행의 `changed` 밖 발견은 같아야 한다. 허용 있는 실행에만 `lost`·`rebind`가 있으면(det3 모양) **H의 결함이 아니라 도구가 계약을 어긴 것**이므로 '측정 무효'(INVALID)가 FAIL보다 정확하다.
3. 어느 쪽도 PASS가 아니어서 종합 판정은 같다. 실제 도구에서는 b 모양(두 실행 같음 → FAIL)만 나온다는 초안 §8.v4r 설명도 계약과 맞다.

남는 것은 문구뿐이다(n-3).

## 4. minor

**n-1 -- 삭제된 허용 id는 진짜 E6 실패인데 INVALID로 찍힌다(V07).** D0a 계약 4 180행: head에 같은 (종류, 키)가 없는 허용 id(삭제)는 `changed` 단위가 아니고 `lost`로 그대로 보고한다 -- 두 실행 모두 `lost`에 나오고, 거부 확인 `changed`에는 그 id가 없다. 그러면 `allow <= ids`가 거짓이라 `E6 INVALID 거부 확인 …`이 된다. 검토 v4 S1과 같은 종류의 오분류지만 (i) §3 (c) 문안이 정한 동작이고, (ii) M10이 선언 id를 지우는 드문 경우이며, (iii) PASS가 아니므로 minor다. 거부 확인의 목적은 **공허 PASS 막기**뿐이므로, 고친다면 판정 순서를 "허용 있는 실행이 이미 FAIL(rc ≠ 0 또는 `nz`)이면 거부 확인 불성립을 덧붙여 `E6 FAIL`, 허용 있는 실행이 PASS 모양일 때만 거부 확인 불성립 → INVALID"로 바꾸면 된다. 다만 그러면 §3의 det3 모양(도구 계약 위반)도 FAIL로 돌아가므로, 작성자 선택(지금 동작 유지 + §9-4에 "삭제된 허용 id는 INVALID로 나온다 -- 원인은 허용 있는 실행의 `lost`" 한 구절)도 받아들일 수 있다.

**n-2 -- e01은 `findings`가 목록인지 보지 않는다(거짓 PASS 가능, 실제 경로 아님).** 가짜 GC(10행)로 `layer.json` `findings`가 `""` 또는 `{}`이고 F2 base 출력이 정상이면 **`E1 PASS exit=0 findings=0`**이 나온다(`len("")`=0·`not f`). F2 base `findings`가 문자열 `"x"`이면 `nf`=1로 거부 확인이 성립한다. e2·e6에는 v4r m-b로 목록 검사를 넣었지만 e01(63~76행)에는 없다. `import_layering.py`는 병합된 gate 도구이고 출력 `findings`는 목록이라 실제 경로가 아니므로 minor. 제안: 63행 뒤 `if not isinstance(d["findings"], list): print("E1 INVALID … 목록 아님"); return`, 70행 조건에 `or not isinstance(fd.get("findings"), list)`. 초안 머리 v4r 줄의 "어떤 입력(… 목록 아닌 값 …)에도 판정 줄" 문구는 '판정 줄'에 대해서는 맞다(W08·W10).

**n-3 -- E6 INVALID 거부 확인 문구가 어느 조건이 깨졌는지 말하지 않는다.** 출력은 `nrc`·`ids`·`nabs`만 찍는다. V35·V02·V22처럼 `changed`가 정확히 두 id이고 exit 1인데 `same_rest`만 거짓인 경우, 줄에는 "exit=1 changed=[두 id] … 없는 키 []"만 보여 읽는 사람이 원인을 찾을 수 없다. 제안: 깨진 절 이름을 덧붙인다(예: `exit≠1`·`허용 id 빠짐 %s`·`중복 %d`·`changed 차이 %s`·`나머지 발견 다른 종류 %s`). 판정 영향 없음.

**n-4 -- 초안 머리 v4r 줄의 `run_dod.sh` 문장이 지금 파일과 다르다.** 머리 줄(5행, 12:31 저장)은 "`run_dod.sh` 무수정(e6 줄 위 주석 2줄은 옛 조건 문구 그대로 -- 동작 무관)"인데, `run_dod.sh`(12:32 저장) 178행 주석은 이미 v4r 조건("(v4r) exit 1·허용 두 id ⊆ changed·중복 없음·두 id를 뺀 발견 = 허용 있는 실행 발견 …")으로 바뀌어 있다. `pre-v4.bak` 대비 diff는 v4 변경(14행 이력·e6 두 실행·judge 줄) + 178행 주석뿐이고 명령 줄은 검토 v4 §1이 확인한 것과 같아 동작 변화는 없다. 고칠 것: 머리 줄을 "`run_dod.sh` 동작 무수정(178행 주석만 v4r 조건으로 정정)"으로, 그리고 `run_dod.sh` 머리 이력(14행 뒤)에 v4r 한 줄. `run_dod.sh.pre-v4r.bak` 사본이 없어 주석만 바뀐 것은 `pre-v4.bak` diff로만 확인된다.

참고(판정 무관): `judge_e6_selftest.py` docstring은 "M01~M06", 실제·초안은 M01~M05b(6가지). m-b 보강 6가지는 판정 줄 '정확히 1개'를 세지 않는다(E6 케이스만 `nverd == 1`) -- 내 W01~W12가 그 몫을 덮었다.

## 5. 뒷정리

메인 저장소 쓰기 0(HEAD·gate `master` `863a037`, status 177줄·reflog 359줄 전후 `cmp` 같음). kit 파일 sha256 전후 같음. 쓴 파일은 이 검토 파일 하나. `C:/g401`은 이 파일을 쓴 뒤 삭제했다.
