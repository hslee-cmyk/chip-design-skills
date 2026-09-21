---
id: 20260921-gate-output-utf8
phase: 0.5
evidence_type: red-green
gate_change: yes
approval: 20260921-gate-output-utf8
---
## 의도

부트스트랩 ⑤ 설치 상태 재생(2026-09-21)에서 관찰: 역할 hook의 거부 메시지가 Claude Code 화면과 subagent 도구 결과에서 한글이
모두 깨진다(`[EL1 �ź�] ��ü ���ɽ�Ʈ������, …`). 원인: 게이트 진입점이 `sys.stdout`/`sys.stderr`를 프로세스 기본 인코딩으로
쓰는데, 한국어 Windows에서 파이프로 연결된 Python의 기본 인코딩은 cp949이고 Claude Code·git 출력 소비자는 UTF-8로 읽는다.
direct 재생은 `run_all.py`가 `PYTHONIOENCODING=utf-8`을 넣고 돌려 이 결함이 가려졌다. 거부 사유(맞는 행·조건·쓸 수 있는 glob)를
읽지 못하면 역할 agent가 왜 막혔는지 모르고 다른 경로를 더듬게 된다 -- 판정은 맞지만 거부 메시지라는 계약이 깨진 상태다.

이 변경은 게이트 진입점 전부가 로캘과 무관하게 UTF-8로 출력하게 한다. 판정(허용·거부, exit code, 메시지 문구)은 바꾸지 않는다.
게이트 변경이라 반영 뒤 §13.4 재설치(사용자: gate에 `tools/gates/gate/*` 복사, `.claude/hooks/role_*` 갱신,
`integrity.py check --scope session`)가 필요하다. 반영 push와 재설치 사이의 fail-closed는 정상이다.

## 관찰 가능한 계약

대상 진입점(명령행으로 실행되는 게이트 코드 전부, `tools/gates/redteam/**` 제외):
`hooks/role_guard.py`, `hooks/role_diff_guard_bash.py`, `hooks/role_diff_guard_stop.py`, `hooks/role_session_start.py`,
`tools/gates/githooks/gmid_gate.py`, `tools/gates/gate/gate-runner.py`, 그리고 `tools/gates/`의 `if __name__ == "__main__"` 모듈
`integrity.py`, `merge_gate.py`, `role_commit_gate.py`, `interface_card.py`, `weakening_diff.py`, `test_lint.py`, `source_lint.py`,
`reachability.py`, `mutate_changed.py`, `import_layering.py`.

1. 위 진입점을 **환경 변수 `PYTHONIOENCODING=cp949`** 또는 `PYTHONIOENCODING`·`PYTHONUTF8`이 없는 환경에서 파이프로 실행했을 때,
   stdout·stderr 바이트 전체가 strict UTF-8로 디코드된다.
2. 한글을 포함하는 메시지는 디코드한 텍스트에 원래 한글 그대로 나온다. 예: 메인 세션(agent_type 없음)이 엔진 소스
   `skills/analog-gmid-design/assets/<파일>.py`를 `Write`하는 PreToolUse 페이로드를 `hooks/role_guard.py`에 주면 stderr에
   `[EL1 거부]`와 `주체 오케스트레이터`가 나온다.
3. exit code와 메시지 문구는 변경 전과 같다(인코딩만 다르다). hook의 fail-closed 경로(예외 → exit 2)의 메시지도 UTF-8이다.
4. stdout으로 JSON을 내는 진입점(`integrity.py check`의 줄 단위 JSON 등)은 계속 한 줄에 JSON 하나이고 `json.loads`로 읽힌다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

red-green. 계약 1·2는 변경 전 코드에서 재현되는 실패다(2026-09-21 설치 상태에서 관찰: 위 거부 메시지, `integrity.py check` 출력).
design `05-role-separation` §18: ⑤ 뒤 게이트 변경은 spec card로 한다(red-green, oracle (a)).

## oracle 종류와 출처

(a) 구성으로 정답이 정해진 합성 입력: 입력 페이로드·인자는 test가 만들고, 기대는 "바이트가 UTF-8로 디코드되고 정해진 한글
부분 문자열이 있다" -- 피검 코드 출력에서 기대값을 만들지 않는다. 한글 부분 문자열은 이 spec card와 design 문서의 메시지 문구
(`[EL1 거부]` 등)에서 가져온다. test 위치는 `tools/gates/redteam/`(게이트 변경의 판정 기준 경로, 쓰기 경로표 N3.12.2).

## 거부해야 할 입력

판정 동작은 바뀌지 않는다 -- 변경 전에 거부하던 입력은 변경 뒤에도 같은 exit code로 거부해야 한다(계약 3). 최소한:
메인 세션의 엔진 소스 `Write`(EL1 exit 2), 알 수 없는 `gmid-` 접두 agent_type(EL1 exit 2).

## library 회로 적용 여부

해당 없음(게이트 코드 변경, 엔진·회로 선언 무관).

## 무동작 판정 입력(무발동 값)

해당 없음. 대신 판정 불변 확인: 기존 `run_all.py --phase 0.5 --mode direct`와 `--cases 0.5`의 케이스 판정이 변경 전과 같다.

## 재현할 수치

없음.

## 결정 필요 항목

없음(사용자 승인 기록 `20260921-gate-output-utf8`로 이 spec card를 승인).
