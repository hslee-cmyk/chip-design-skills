# -*- coding: utf-8 -*-
"""00-common/05 부트스트랩 ② 앞당김: hook 입력 실측용 더미 hook. 판정하지 않는다.
stdin JSON 원문을 .git/gmid-hook-probe/log/<event>-<시각>-<pid>.json에 쓴다.
tool_input 안에 표지 문자열이 있으면 exit code를 흉내 낸다(차단 의미 실측):
  GMIDPROBE_EXIT1 -> exit 1, GMIDPROBE_EXIT2 -> exit 2(stderr 메시지), GMIDPROBE_EXCEPT -> 예외(파이썬 기본 exit 1)."""
import json, os, sys, time
raw = sys.stdin.buffer.read()
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log")
os.makedirs(d, exist_ok=True)
try:
    ev = json.loads(raw.decode("utf-8")).get("hook_event_name", "unknown")
except Exception:
    ev = "unparsed"
p = os.path.join(d, f"{ev}-{time.strftime('%H%M%S')}-{os.getpid()}.json")
open(p, "wb").write(raw)
s = raw.decode("utf-8", "replace")
if "GMIDPROBE_EXIT2" in s:
    sys.stderr.write("GMIDPROBE: exit 2 by probe\n"); sys.exit(2)
if "GMIDPROBE_EXIT1" in s:
    sys.stderr.write("GMIDPROBE: exit 1 by probe\n"); sys.exit(1)
if "GMIDPROBE_EXCEPT" in s:
    raise RuntimeError("GMIDPROBE: exception by probe")
sys.exit(0)
