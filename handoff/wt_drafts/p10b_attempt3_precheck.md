# P10b 재시도 3차 사전 점검 (V3 예측, 공식 판정 아님)

- 날짜: 2026-10-01, 작업 경로 C:/g131 (점검 뒤 삭제)
- 병합본: 572d767 (role/test/20260930-df23-registry-record, 재시도 3차 test) + `_drafts/p10b_attempt2/code_3fd34f6.patch`를 `git apply` -> 임시 커밋 b064691a3a88d0654df24248744ab0578801c8a8
- `reg_check.py` blob = 38367fd8f872af04d61121abae08823ee1373cde (1·2차와 같음)
- 게이트 캐시: 0f23786 tools/gates (redteam 제외), auditor `extract_gate.py`로 추출, file_set_sha256 705036ea1039e7abb0e449918a8209b229f4a685ab2da9d0e03907bf571d82c4 (2차 판정 기록과 같음)
- 환경: APPDATA=C:/Users/HSLEE/AppData/Roaming, HOME=/c/Users/HSLEE, TMP·PYTHONPYCACHEPREFIX는 C:/g131 아래

## V3 보충 뮤테이션 (mut_df23.py)

auditor 스크립트 `scripts/mut_df23.py`의 사본을 썼다. 바꾼 것은 한 줄뿐이다. `run_tests()`의 `tempfile.mkdtemp(dir="C:/g88")`을 `dir="C:/g131/pyctmp"`로 바꿨다(C:/g88을 건드리지 않기 위해서다). 대상 규칙, 연산자, test 두 파일, pytest 옵션은 원본과 같다.

호출: `PYTHONPATH=<캐시> C:/Python314/python.exe -P mut_df23.py C:/g131/m <캐시> 0f237862c007f6a53122f2bdfb3c87e6366ec133 out/mut_m.jsonl`

- 대상 def: `_df23_expected` 170-216, `_df23_rows_under` 219-239, `check_df23` 242-318, `main` 349-385 (2차와 같음)
- 무변이 기준: exit 0, 179 passed
- **변이 290개 실행, 281개 죽음, 9개 생존, timeout 0** (스크립트 exit 1. 생존이 있으면 exit 1을 낸다)
- 생존 9개는 **전부** 승인 기록 `.ai/approvals/20261001-p10b-v3-equiv.md`의 target id 9개와 같다. 그 밖의 생존은 0개다.

| 생존 id | 줄 | 승인 등가 9 |
|---|---|---|
| reg_check:_df23_expected:const+:body[7].body[4].value.value.args[1] | 189 rsplit("/", 1) | 예 |
| reg_check:_df23_rows_under:const-:body[8].iter.args[0].slice.lower.right | 235 sec[start + 1:end] | 예 |
| reg_check:check_df23:const-:body[8].value.slice.lower.right | 258 lines[start + 1:end] | 예 |
| reg_check:check_df23:arith:body[15].orelse[1].body[0].value.right.right | 284 [""] * (3 - len(r)) | 예 |
| reg_check:check_df23:const+:body[15].orelse[1].body[0].value.right.right.left | 284 | 예 |
| reg_check:check_df23:arith:body[17].orelse[1].body[0].value.right.right | 304 [""] * (5 - len(r)) | 예 |
| reg_check:check_df23:const+:body[17].orelse[1].body[0].value.right.right.left | 304 | 예 |
| reg_check:main:stmt_delete:body[8].body[3].body[5] | 374-375 dict 검사 | 예 |
| reg_check:main:stmt_delete:body[8].body[3].body[5].body[0] | 375 | 예 |

2차에서 비등가로 생존했던 9개는 이번에 모두 죽었다. 여기에는 225·257행 break 삭제, 229·235·254·258행 start+2, 235·258행 start-1, 313행 r[2:6]이 포함된다. detail 6개도 죽었다.
판정 예측: 승인 등가 9개를 면제하면 V3 PASS가 예상된다. 단, auditor가 병합본에서 등가 여부를 다시 판정해야 한다(witness.py는 C:/g88에 임시 경로를 만들기 때문에 이번에는 돌리지 않았다).

## V4 test_lint (base 캐시 test_lint.py, 2차 V4와 같은 두 형태, --head = b064691)

- `--module-dir A/tests/tools --interface-card <병합본>/docs/02-design/specs/20260930-df23-registry-record.interface.md`: **verdict PASS, exit 0**. 발견은 (2) UNJUDGED 59, (2) NO-SUBJECT 31이고 FAIL은 0이다.
- `--subject reg_check:check_df23 --subject reg_check:main`: **verdict PASS, exit 0**. 발견은 (2) UNJUDGED 64, (2) NO-SUBJECT 15, (2) PASS 11이고 FAIL은 0이다.
- (1)(3)(4)(5) 규칙 발견: 0

## 전체 pytest (V1 형태)

`PYTHONPATH=<캐시> python -P -m pytest -c <캐시>/pytest_gate.ini --rootdir=<복제본> --confcutdir=<복제본> --gmid-phase=2 --gmid-strict= <복제본>/skills/analog-gmid-design/assets/tests -q -rfE -p no:cacheprovider`
-> **1008 passed, 15 xfailed**. failed, error, skip은 0이고 exit 0, 385.8s가 걸렸다. 뮤테이션은 별도 복제본(C:/g131/m)에서 돌렸고 pytest는 C:/g131/m2에서 돌렸다.

## 부수 사항

- 처음에 원본 mut_df23.py를 그대로 몇 초 실행했다가 멈췄다. 그때 `C:/g88/pyc_mut_xgy7z6cn`(20:13 생성, 빈 pycache 임시 디렉터리) 하나가 남았다. 지시상 C:/g88은 건드리면 안 되므로 지우지 않았다. 필요하면 정리해야 한다.
- C:/g131 삭제(`rm -rf C:/g131`)는 Claude Code 안전 검사에 막혀 실행하지 못했다. 디렉터리가 남아 있으니 수동으로 지워야 한다.
- 뮤테이션이 끝난 뒤 복제본 reg_check.py는 원본으로 복원됐다(status 0줄).
