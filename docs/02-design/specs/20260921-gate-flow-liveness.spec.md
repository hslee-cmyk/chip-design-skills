---
id: 20260921-gate-flow-liveness
phase: 0.5
evidence_type: red-green
gate_change: yes
approval: 20260921-gate-flow-liveness
---

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260921-gate-flow-liveness.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 0.5(역할 분리 인프라) card다. 역할 분리 gate·auditor는 DEC-86으로 꺼졌다(계획 N6.1 '옛 Phase 처리' 0.5행; N3.12 역할 분리·N4.2 auditor V1~V10·N4.3 게이트 거부 증명은 폐기 절). 본문의 게이트 동작(EL1~EL4·V1~V10)·§13.4 재설치·승인(DEC-40·R1) 문장은 현행 절차가 아니다 -- 현행 완료 조건은 계획 N6.3(가벼운 절차)이다. `tools/gates/**`·`hooks/role_*`·`.githooks/`에 남은 파일은 꺼진 잔여물이다(DEC-86). 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 본문은 기록이며 덧대지 않는다(O-169).

## 의도

부트스트랩 ⑤ 설치 상태 재생(2026-09-21, `docs/03-analysis/gain-budget-gmid-sizing-bootstrap5/installed-replay.md`)에서 드러난
정상 흐름 오거부·복구 불가·판정 누락을 고친다. 판정의 막는 범위는 넓히지도 좁히지도 않고, 아래 여섯 곳만 바꾼다.

* D-7 §12-3이 audit worktree에 미커밋으로 두는 `base_check.json` 때문에 다른 역할의 EL2(PostToolUse·SubagentStop)가 거부한다.
* D-3 §12-6 병합이 EL3에 막혀 남은 병합 상태, §12-3 뒤 재시도 정리에서 audit worktree의 미커밋 파일을 오케스트레이터가 치울 수 없다.
* D-8 EL3가 `integrity-failed` 표지를 보지 않는다(§3.3은 EL1·EL3 모두 거부).
* D-10 EL1이 대입 안의 명령 치환(`X=a/$(cmd)`)에서 예외로 fail-closed 된다(판정이 아니라 예외).
* D-6 `git worktree add -q …`(§12 형태에 `-q`만 더함)가 거부된다.
* V6 관찰: 앞 변경이 16곳에 넣은 광범위 `except Exception: pass`.

## 관찰 가능한 계약

1. (D-7) 역할 R의 EL2 대조에서 **다른 역할 worktree의 미커밋 경로**는, 그 경로가 **그 worktree 주인 역할에게 허용된 경로**(쓰기 경로표,
   그 worktree의 변경 id)이면 R의 위반으로 세지 않는다. 주인 역할에게도 허용되지 않은 경로는 지금처럼 위반이다.
   예: audit worktree의 `.ai/verification/<id>/base_check.json` 미커밋 → code-author·test-author의 PostToolUse·SubagentStop 통과.
   audit worktree의 `skills/analog-gmid-design/assets/x.py` 미커밋 → 여전히 거부.
2. (D-3) 오케스트레이터(메인 세션)에게 다음 두 명령을 허용한다: `git -C <W>/<id>-audit merge --abort`,
   `git worktree remove --force <W>/<id>-{test,code,audit}`(§12 경로 형태와 같고, code worktree는 지금과 같은 dispute 기록 검사).
   역할에게는 여전히 거부. 다른 경로·다른 형태의 `--force`는 여전히 거부.
3. (D-8) 저장소 공통 디렉터리의 게이트 캐시에 `integrity-failed` 표지가 있으면 EL3(`pre-commit`·`commit-msg`·`pre-merge-commit`)가
   판정 범위와 무관하게 커밋·병합을 거부(exit 1)하고 표지 경로와 복구 절차를 출력한다.
4. (D-10) EL1이 `NAME=<문자열>$(<명령>)<문자열>; …` 꼴 Bash 명령을 예외 없이 판정한다(Traceback·`판정 실패(fail-closed)` 메시지 없음).
   치환 안 명령은 지금 `$(…)` 규칙대로 판정한다(공격 24 c와 같음).
5. (D-6) `git worktree add -q <§12 경로> -b role/<r>/<id> <base>`는 `-q` 없는 형태와 같은 판정을 받는다.
6. (V6 관찰) 변경 `20260921-gate-output-utf8`이 16개 진입점에 넣은 `try: …reconfigure… except Exception: pass`를 광범위 except 없이
   쓴다(Python 3.14에서 `reconfigure`는 항상 있다). 출력 계약(공격 26)은 그대로 PASS.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

red-green. 계약 1~6 모두 변경 전 게이트에서 재현되는 실패다(설치 재생 기록 D-3·D-6·D-7·D-8·D-10).

## oracle 종류와 출처

(a) 구성으로 정답이 정해진 합성 입력(redteam 케이스). 기대는 이 spec card 계약과 design 05 §3.3·§6.2·§7·§12.

## 거부해야 할 입력

계약 1의 두 번째 예(주인에게도 허용 안 된 미커밋 경로), 역할의 `merge --abort`·`worktree remove --force`, §12 밖 경로의
`remove --force`, 표지가 없는 상태의 EL3 판정 변화 없음, 공격 24 c(치환 안 push) 거부 유지.

## library 회로 적용 여부

해당 없음.

## 무동작 판정 입력(무발동 값)

해당 없음. 판정 불변: `run_all.py --phase 0.5 --mode direct` 전체와 `--cases 0.5`가 변경 전과 같다.

## 재현할 수치

없음.

## 결정 필요 항목

없음.

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260921-gate-flow-liveness.spec.md`.
