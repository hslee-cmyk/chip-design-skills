"""v6 문서들의 마크다운 표 셀 수(머리 대비) 점검과 남은 옛 문자열 계수 -- 읽기 전용."""
import re
import sys

PIPE = re.compile(r"(?<!\\)\|")
for p in sys.argv[1:]:
    lines = open(p, encoding="utf-8").read().split("\n")
    incode, hdr, bad = False, None, []
    for i, l in enumerate(lines, 1):
        if l.strip().startswith("```"):
            incode, hdr = not incode, None
            continue
        if incode:
            continue
        s = l.strip()
        if s.startswith("|"):
            n = len(PIPE.split(s)) - 2
            if hdr is None:
                hdr = n
            elif n != hdr:
                bad.append((i, hdr, n))
        else:
            hdr = None
    print(p.replace("\\", "/").rsplit("/", 1)[1], "bad rows:", bad[:10])
s = open(sys.argv[1], encoding="utf-8").read()
for pat in ["card 수 15", "v3 27", "27/27", "아직 32", "<캐시>"]:
    print(repr(pat), s.count(pat))
