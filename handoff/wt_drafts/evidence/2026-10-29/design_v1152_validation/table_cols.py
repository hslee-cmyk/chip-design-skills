"""표 열 수 점검: 머리 행 열 수와 다른 본문 행(이스케이프 \\| 제외, 코드 스팬 안 | 제외)을 줄 번호로 낸다."""
import re
import sys

for path in sys.argv[1:]:
    lines = open(path, encoding="utf-8").read().split("\n")
    head = None
    bad = []
    for i, ln in enumerate(lines, 1):
        if not ln.startswith("|"):
            head = None
            continue
        t = re.sub(r"`[^`]*`", "C", ln.replace("\\|", "E"))
        n = t.count("|") - 1
        if head is None:
            head = n
            continue
        if re.match(r"^\|[\s:-]+\|", ln) and set(ln) <= set("|-: "):
            continue
        if n != head:
            bad.append((i, head, n))
    print(path.split("/")[-1], "mismatch rows:", len(bad), bad[:20])
