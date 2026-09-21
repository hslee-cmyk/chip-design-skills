"""게이트 인터페이스 가정 -- 한 곳에만 둔다.

이 파일의 경로·명령 형태는 05-role-separation v3.6 design과 00-common v1.8만 보고 정했다(작성본을 보기 전).
design이 고정하지 않은 모양은 INTERFACE_ASSUMPTIONS.md에 한 줄씩 적었다(번호 A-xx). 재생 단계에서 작성본의
실제 인터페이스가 다르면 **이 파일만** 고친다 -- 기대(expect.json·cases/*.json)는 인터페이스와 무관하게
design 문장에서 나왔으므로 고치지 않는다.
"""
from __future__ import annotations

import json
import sys

# design 경로(고정): §2 표, §6, §7, §8, §9, §10, 계획 N3.12.6 산출물 표
GATE_FILES = {
    "EL1": "hooks/role_guard.py",                 # §6 (A-01: 스크립트 하나가 PreToolUse 실행기)
    "EL2_bash": "hooks/role_diff_guard_bash.py",  # §7
    "EL2_stop": "hooks/role_diff_guard_stop.py",  # §7
    "SESSION": "hooks/role_session_start.py",     # §3.3
    "EL3": "tools/gates/role_commit_gate.py",     # §8.2
    "EL4": "tools/gates/merge_gate.py",           # §9.2
    "INTEGRITY": "tools/gates/integrity.py",      # §3.3
    "V3": "tools/gates/mutate_changed.py",        # §10
    "V4": "tools/gates/test_lint.py",
    "V5": "tools/gates/weakening_diff.py",
    "V6": "tools/gates/source_lint.py",
    "V7": "tools/gates/reachability.py",
    "CARD": "tools/gates/interface_card.py",      # §11.1
    "CONFIG": "tools/gates/gate_config.json",     # §13.1 ①
    "REQUIREMENTS": "tools/gates/requirements.txt",  # §9.3
    "PYTEST_INI": "tools/gates/pytest_gate.ini",  # §13.1 ①
}

HOOK_FOR_EVENT = {
    "PreToolUse": "EL1",
    "PostToolUse": "EL2_bash",
    "SubagentStop": "EL2_stop",
    "SessionStart": "SESSION",
}


def hook_payload(event: str, cwd_win: str, *, tool: str | None = None, tool_input: dict | None = None,
                 agent_type: str | None = None, tool_use_id: str = "toolu_redteam",
                 tool_response: dict | None = None) -> dict:
    """Claude Code hook stdin JSON. 필드는 role_hook_input_probe.md 실측(메인 세션은 agent_type·agent_id 없음)."""
    p = {
        "session_id": "redteam-session",
        "transcript_path": cwd_win + "\\redteam-transcript.jsonl",
        "cwd": cwd_win,
        "permission_mode": "default",
        "hook_event_name": event,
    }
    if agent_type is not None:          # subagent: agent_type과 agent_id가 함께 온다(빈 문자열 포함)
        p["agent_id"] = "redteam-agent"
        p["agent_type"] = agent_type
    if event in ("PreToolUse", "PostToolUse"):
        p["tool_name"] = tool
        p["tool_input"] = tool_input or {}
        p["tool_use_id"] = tool_use_id
    if event == "PostToolUse":
        p["tool_response"] = tool_response if tool_response is not None else {
            "stdout": "", "stderr": "", "interrupted": False, "isImage": False, "noOutputExpected": False}
        p["duration_ms"] = 1
    if event == "SubagentStop":
        p["stop_hook_active"] = False
        p["agent_transcript_path"] = cwd_win + "\\redteam-agent-transcript.jsonl"
        p["last_assistant_message"] = "redteam"
    if event == "SessionStart":
        p["source"] = "startup"
    return p


def el3_commands(py: str, gate_script: str, msg_file: str) -> list[tuple[str, list[str]]]:
    """§8.1: pre-commit은 `role_commit_gate.py pre-commit`, commit-msg는 `role_commit_gate.py commit-msg <파일>`."""
    return [("pre-commit", [py, gate_script, "pre-commit"]),
            ("commit-msg", [py, gate_script, "commit-msg", msg_file])]


def el4_command(py: str, gate_script: str, old: str, new: str) -> list[str]:
    """§9.1-3·§3.3 행 3: `merge_gate.py receive --old <old> --new <new>`."""
    return [py, gate_script, "receive", "--old", old, "--new", new]


def plan_tables_hash_command(py: str, gate_script: str, plan_path: str) -> list[str]:
    """§15.2 CLI: `merge_gate.py plan-tables-hash <계획서 파일>`."""
    return [py, gate_script, "plan-tables-hash", plan_path]


def vtool_command(py: str, tool_script: str, repo: str, base: str, head: str, card: str | None) -> list[str]:
    """§10은 출력(JSON 한 줄, exit 0/1/2)만 고정한다. 입력 인자는 A-08."""
    cmd = [py, tool_script, "--repo", repo, "--base", base, "--head", head]
    if card:
        cmd += ["--interface-card", card]
    return cmd


def card_command(py: str, card_script: str, spec_card: str) -> list[str]:
    """§11.1: `interface_card.py <spec card>` -> docs/02-design/specs/<id>.interface.md."""
    return [py, card_script, spec_card]


JUDGEMENTS = ("FAIL", "PASS", "UNJUDGED", "NO-SUBJECT")


def first_json_line(stdout: str):
    """§10: 판정은 JSON 한 줄로 표준출력. 첫 번째로 JSON으로 읽히는 줄."""
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except ValueError:
                continue
    return None


def v4_statements(obj) -> list[tuple[int, str]] | None:
    """V4 (2) 판정 문장별 출력(§10 ①: 판정 문장마다 FAIL·PASS·UNJUDGED·NO-SUBJECT 중 하나).
    A-09: JSON 안 어디든 `line`(또는 `lineno`) 정수와 네 값 중 하나를 값으로 가진 객체를 판정 문장으로 본다.
    값을 가진 키 이름은 가정하지 않는다. 찾지 못하면 None."""
    found: list[tuple[int, str]] = []

    def walk(o):
        if isinstance(o, dict):
            ln = o.get("line", o.get("lineno"))
            vals = [v for v in o.values() if isinstance(v, str) and v in JUDGEMENTS]
            if isinstance(ln, int) and len(vals) == 1:
                found.append((ln, vals[0]))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            if len(o) == 2 and isinstance(o[0], int) and isinstance(o[1], str) and o[1] in JUDGEMENTS:
                found.append((o[0], o[1]))
            else:
                for v in o:
                    walk(v)
    if obj is None:
        return None
    walk(obj)
    if not found:
        return None
    return sorted(set(found))


PY = sys.executable
