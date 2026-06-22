#!/usr/bin/env python
"""PreToolUse(Edit|Write) nudge: RTL 편집 착수 시 지식 preflight를 환기 (지식 자산화 D).

RTL 파일(db/design/**/*.v|sv)을 Edit/Write 하려 할 때, 세션당 1회 에이전트 컨텍스트에
"착수 전 preflight로 장기 원칙(전역 RAG) + 단기 graphify를 조회하라"는 리마인더를 주입한다.
강제(block) 아님 — 판단은 에이전트가, 단 잊지 않게 적시에 찔러줌. 자세히: docs/05.

세션당 1회만(session_id 마커). 비-RTL 편집·파싱오류는 조용히 통과(fail-open, exit 0).
"""
import sys, os, json, re, tempfile

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if (data.get("tool_name") or "") not in ("Edit", "Write", "MultiEdit"):
        return 0
    ti = data.get("tool_input") or {}
    fp = (ti.get("file_path") or ti.get("path") or "").replace("\\", "/")
    # RTL 설계 파일만 (db/design 하위의 .v/.sv)
    if not re.search(r"/db/design/.*\.(v|sv|vh|svh)$", fp, re.I):
        return 0
    # 세션당 1회 dedup
    sid = data.get("session_id") or "nosid"
    marker = os.path.join(tempfile.gettempdir(), f"kb_preflight_{sid}")
    if os.path.exists(marker):
        return 0
    try:
        open(marker, "w").close()
    except Exception:
        pass
    msg = ("💡 RTL 편집 감지 — 착수 전 지식 preflight 권장(아직이면): "
           '"$KB_PY" .ai/rag/preflight.py "<증상/주제>" '
           "→ 장기 일반원칙(전역 RAG) + 단기 graphify 항법. "
           "해결 후엔 /solution-capture 로 자산화. (자세히: chip-design-skills/docs/05)")
    # PreToolUse additionalContext 로 에이전트에 주입(미지원 버전이면 무해하게 무시됨)
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "additionalContext": msg}}))
    sys.stderr.write(msg + "\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
