---
id: 20260930-df35-harness-paths
phase: 2
evidence_type: red-green
gate_change: no
approval: 20260923-20-dead-code-dup-design
---

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260930-df35-harness-paths.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 2(죽은 코드·DUP 정리) card이고 Phase 2는 폐기됐다(계획 N6.1 '옛 Phase 처리' 2행 -- 새 엔진은 모듈 지도 N3.10으로 처음부터 개념당 정본 하나). 본문의 spec card·interface card·auditor 판정(V1~V10)·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다(계획 N3.12·N4.2, DEC-40 행) -- 현행 완료 조건은 계획 N6.3이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. `run_harness.py`는 지금 `legacy/workspaces/`에 있다. 이 card가 만들거나 옮긴 파일 가운데 계약 test `legacy/tests/contracts/test_df35_harness_paths.py`는 O-180(LUT는 v2 r2 묶음만 남기고 sample LUT를 읽는 legacy test·probe도 지움)의 삭제 대상이다 -- LUT 정리(브랜치 `data/lut-v2-only`) 병합 전에는 `legacy/` 아래 있고, 병합 뒤에는 git 이력에만 있다(LT-1보다 먼저 지워짐). 본문은 기록이며 덧대지 않는다(O-169).

## 의도

계획 DF-35(담당 Phase 4 -- 사용자 지시 2026-09-30 "1부터 4까지 다 개선해"로 앞당김): 하네스 `workspaces/run_harness.py`가 저장소 경로를 **메인 체크아웃 절대
경로**로 박아 둔다(`sys.path.insert`, `ASSETS_DIR`, `WORKSPACES_DIR`). 그래서 다른 worktree·격리 복제본에서 import해도 메인 체크아웃의 엔진·LUT·library를 잡는다
(review21·22 C-01) -- auditor는 매 card마다 사본의 리터럴을 바꿔 치우는 우회를 했고, 복원 card에서는 test가 import 순서로 막아야 했다. 계획의 고칠 방향대로
**경로를 `__file__`에서 유도**한다. A = `skills/analog-gmid-design/assets`.

범위: `run_harness.py` 모듈 머리의 세 경로 줄만 바꾼다. LUT를 import 시점에 읽는 동작(`LUTFILE`, `np.load`)은 그대로 둔다 -- 경로가 바르면 그 import가 자기
체크아웃의 LUT를 읽는다. `instance.json`의 절대 경로(DF-36)는 다음 card.

## 관찰 가능한 계약

1. `workspaces/run_harness.py`의 문자열 상수(AST `Constant` 값) 중 Windows 절대 경로(`^[A-Za-z]:[\\/]`)와 POSIX 절대 경로 중 저장소 체크아웃을 가리키는 것이 0개다.
2. `run_harness.WORKSPACES_DIR`는 `run_harness.py` 파일이 있는 디렉터리, `run_harness.ASSETS_DIR`는 그 부모(저장소 루트) 아래 `skills/analog-gmid-design/assets`와 같은
   실제 경로다(`os.path.samefile` 또는 정규화 비교). 즉 어느 체크아웃에서 import하든 **그 체크아웃**을 가리킨다.
3. `run_harness` import 뒤 `sys.path`에 들어간 assets 경로가 계약 2의 `ASSETS_DIR`와 같다(메인 체크아웃 경로가 들어가지 않는다).
4. 파생 경로 `LIBRARY_DIR`·`LUTFILE`은 계약 2의 `ASSETS_DIR` 아래다(바뀌지 않은 식이 새 `ASSETS_DIR`를 따른다).
5. **동작 보존**: 메인 체크아웃 경로에서의 E-INST(파일럿·`folded_cascode` instance.json)가 base와 같다(경로 문자열이 같으므로). 격리 복제본에서는 이제 복제본 경로가
   들어간다 -- 이것이 이 card가 고치는 것이다(DF-36 전까지 instance.json의 `topology_ref`는 절대 경로라 경로별로 다르다). 전체 스위트 FAIL 0.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

red-green: base에서 계약 1(절대 경로 리터럴 3개)은 어디서나, 계약 2·3은 메인 체크아웃이 아닌 체크아웃(test worktree·격리 복제본)에서 실패한다. 병합본에서 green.

## oracle 종류와 출처

(a) 구성: 기대 경로는 test 파일 자신의 위치(`__file__`)에서 저장소 루트를 구해 만든다 -- 피검 모듈의 상수를 기대값으로 쓰지 않는다. (c) 동작 보존: E-INST 기대값 = base
실행 결과(같은 경로).

## 거부해야 할 입력

합성 소스로 판정기 자기 점검: `r"C:\x\y"`·`"D:/a"`·`"/home/u/repo"` 같은 절대 경로 상수 → 발견. 상대 경로·`os.path.join(...)` 식·주석·docstring 속 경로 예시 → 발견 아님.

## library 회로 적용 여부

E-INST(파일럿·`folded_cascode`)로 동작 보존.

## 무동작 판정 입력(무발동 값)

엔진(`A/*.py`)·library·기존 test 전부 -- 판정이 base와 같다(run_harness의 경로 세 줄만 바뀐다).

## 재현할 수치

없음.

## 결정 필요 항목

없음(사용자 지시로 DF-35를 Phase 4에서 앞당김).

## 작성 전 실측

1. 사실 문장: `grep -n 'C:\\Users' workspaces/run_harness.py` → 35(`sys.path.insert`)·42(`ASSETS_DIR`)·44(`WORKSPACES_DIR`) 세 줄, 45행 `LUTFILE = os.path.join(ASSETS_DIR, …)`, 63행
   `_d = np.load(LUTFILE)`(import 시점). `A/*.py`·`workspaces/*.py` 전체에서 절대 경로 리터럴이 있는 파일은 `run_harness.py` 하나.
2. 이름 충돌: 새 test `A/tests/contracts/test_df35_harness_paths.py` -- 기존 glob(`probe_*.py`, `test_probe_*.py`, `*.topology.json`, `*.py` 전수 스캔)에 걸리지만 전수 스캔 test들은
   AST 참조·print 판정이라 새 파일이 판정 대상이 될 뿐 충돌하지 않는다(새 파일은 이 규칙을 지킨다).
3. 원칙의 계약화: 경로를 `__file__`에서 유도 -- 계약 1~4에 적었다.
4. 쓰기 경로: `workspaces/run_harness.py` = code-author(P5·복원 card 선례), test = test-author.
5. 계획서 소비자: 바꾸는 이름 없음(상수 이름 불변).
6. 미배선: 새 def 없음.
7. 기존 계약 test: `grep -rn "run_harness" A/tests/contracts/` -- 경로 상수를 쓰는 test 없음. `test_restore_plan_functions.py`의 import 순서 우회는 이 card 뒤에도 무해하다.

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260930-df35-harness-paths.spec.md`.
