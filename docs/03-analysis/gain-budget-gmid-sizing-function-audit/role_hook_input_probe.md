# role_hook_input_probe -- Claude Code hook 입력 실측 (부트스트랩 ② 앞당김)

* 일시: 2026-09-18. 사용자 허락("(1) 등록해")으로 `.claude/settings.local.json`에 더미 hook을 잠깐 등록했고, 측정 뒤 원복했다(원복 후 `hooks` 키 없음 확인).
* 더미 hook: `role_hook_probe_logs/probe.py`. stdin JSON 원문을 파일로 쓰고, `tool_input` 안의 표지로 exit code를 흉내 낸다(`GMIDPROBE_EXIT1` → exit 1, `GMIDPROBE_EXIT2` → exit 2, `GMIDPROBE_EXCEPT` → 예외).
* 등록 이벤트: PreToolUse(`Edit|Write|NotebookEdit|Bash|PowerShell|Read|Grep|Glob`), PostToolUse(`Bash|PowerShell`), SubagentStop, Stop.
* 원자료: `role_hook_probe_logs/*.json`(35개). hook stdin 원문에서 **식별자를 가렸다**(사용자 요청): 세션·프롬프트·도구 호출·agent id, transcript·scratchpad 경로, 권한 모드, 조수 메시지 본문은 `<redacted>`, 사용자 홈 경로는 `<HOME>`. 키가 있는지·어떤 값 종류인지(실측의 근거)는 그대로 남겼다. 가리기 전 원본은 저장소 밖(`.git/gmid-hook-probe/log`, 추적 안 됨)에만 있다.

## 결과

| 항목 | 관찰 | 근거 파일 |
|---|---|---|
| 설정 반영 시점 | `settings.local.json`에 등록한 **직후의 도구 호출부터** hook이 돈다(세션 재시작 불필요) | `PreToolUse-162912-716.json` |
| 메인 세션의 역할 필드 | `agent_type`·`agent_id` **없음**. 있는 키: `session_id`, `transcript_path`, `cwd`, `scratchpad_dir`, `prompt_id`, `permission_mode`, `effort`, `hook_event_name`, `tool_name`, `tool_input`(Post는 `tool_response`, `tool_use_id`, `duration_ms`) | `PreToolUse-162918-19184.json` 등 |
| subagent의 역할 필드 | PreToolUse(Bash, PowerShell, Write)·PostToolUse(Bash, PowerShell -- PostToolUse는 이 둘만 등록했다)와 SubagentStop 모두 `agent_type`(= Agent 도구에 준 `subagent_type`, 예 `general-purpose`)과 `agent_id`가 **있음** | `PreToolUse-162932-27728.json`, `SubagentStop-162958-9772.json` |
| 이름 없는 subagent | `agent_type`이 빈 문자열인 SubagentStop이 두 번 기록됐다(`agent_id` 있음). 사용자가 띄우지 않은 내부 subagent로 보인다 | `SubagentStop-162946-27940.json`, `SubagentStop-163001-13492.json` |
| hook 입력의 `cwd` | 메인 세션·subagent 모두 **세션 시작 디렉터리**(저장소 루트)다. subagent가 `cd ..`한 호출에서도 hook 입력 `cwd`는 저장소 루트였다 | `PreToolUse-162937-7116.json` |
| subagent Bash의 작업 디렉터리 | `cd .. && pwd`는 상위를 출력했지만 **다음 Bash 호출의 `pwd`는 다시 저장소 루트**였다(호출 사이에 유지되지 않는다) | `PostToolUse-162937-10252.json`, `PostToolUse-162939-22356.json` |
| 메인 세션의 작업 디렉터리 | 메인 세션은 `cd`가 다음 호출까지 **유지된다**(hook 입력 `cwd`도 바뀐 디렉터리로 기록) | `PostToolUse-162937-25408.json` |
| exit 2 | PreToolUse에서 도구 호출을 **막는다**. stderr가 호출자에게 오류로 전달된다. Stop·SubagentStop·PostToolUse에서도 막는다(아래 부작용) | 메인·subagent 두 경우 |
| exit 1 | **막지 않는다**(도구가 정상 실행됨) | `PostToolUse-162919-27008.json` |
| hook 안의 예외(파이썬 기본 exit 1) | **막지 않는다** | `PostToolUse-162920-24092.json` |
| PowerShell 도구 | 메인 세션과 subagent 모두 PowerShell 도구를 쓰고, hook은 `tool_name: PowerShell`로 받는다 | `PreToolUse-162920-20952.json`, `PreToolUse-162949-28304.json` |
| probe 결함(측정 부작용) | 종료 이벤트의 입력(transcript 경로·마지막 메시지)과 PostToolUse의 `tool_response`에 표지 문자열이 들어 있으면 probe가 그것까지 막았다 -- subagent의 최종 보고가 가려졌고, 요약 Bash 한 번이 PostToolUse에서 막혔다. 표지는 `tool_input`에서만 찾았어야 했다 | `Stop-162944-26544.json` |

## 05 설계에 주는 결론

1. **U-15는 필요 없다**(N7.2 "필드가 있으면 이 결정은 필요 없다"): subagent는 모든 관련 이벤트에서 `agent_type`을 준다. 메인 세션은 필드가 없다 → `오케스트레이터`. `agent_type`이 빈 문자열인 내부 subagent의 처리 규칙이 필요하다(역할 밖으로 볼지, 막을지).
2. **역할과 worktree를 `cwd`로 묶을 수 없다**: hook 입력 `cwd`는 세션 시작 디렉터리이고 subagent의 `cd`는 호출 사이에 유지되지 않는다(review28 P-10 확인). 역할이 자기 worktree에서 일하게 하려면 매 명령에 절대 경로(`git -C <worktree>`)를 쓰게 하거나, 역할을 worktree에 묶는 다른 수단이 필요하다.
3. **hook은 exit 2로만 막는다**: 판정 로직의 import 실패·예외는 exit 1이 되어 통과한다(review28 P-09 확인). 역할 hook은 최상위에서 모든 예외를 잡아 exit 2로 끝내야 한다.
4. **PowerShell도 쓰기 도구다**: matcher와 명령 판정에 PowerShell을 넣어야 한다(review28 P-08 일부 확인).
5. 사용자 정의 agent(`gmid-*`)의 `agent_type` 값이 정의 이름과 같은지는 이번에 재지 않았다(정의가 없어서). 부트스트랩 ⑤에서 설치 뒤 확인한다.
