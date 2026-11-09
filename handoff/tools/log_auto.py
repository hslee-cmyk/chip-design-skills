"""wt/_drafts/la1_auto_decisions.md에 위임 기록 행(A-행)을 바이너리 append한다(heredoc append 금지 규칙의 대체).

사용: python handoff/tools/log_auto.py <행 파일> [la1_auto_decisions.md 경로]
기본 경로 = 저장소 상위(fpga)/wt/_drafts/la1_auto_decisions.md (이 파일 위치 기준 유도; 환경변수 GMID_LA1_LOG로 바꿀 수 있음).
"""
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # <repo>/handoff/tools -> <repo>
_DEFAULT = os.path.join(os.path.dirname(_REPO), "wt", "_drafts", "la1_auto_decisions.md")
p = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("GMID_LA1_LOG", _DEFAULT)
rows = open(sys.argv[1], encoding="utf-8").read().strip().splitlines()
b = "".join(r.rstrip() + "\n" for r in rows).encode("utf-8")
d = open(p, "rb").read()
assert d.endswith(b"\n")
with open(p, "ab") as f:
    f.write(b)
assert open(p, "rb").read()[:len(d)] == d  # 앞부분 보존 확인
print(len(d), "->", len(d) + len(b))
