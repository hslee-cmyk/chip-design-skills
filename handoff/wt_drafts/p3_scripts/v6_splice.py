"""design v6 문서 편집 보조: `_drafts` 안의 파일에서 [start 표지, end 표지) 구간을 조각 파일 내용으로 바꾼다.
사용: python v6_splice.py <대상 md> <조각 파일> <start 표지> <end 표지>   (표지는 각각 정확히 한 번 나와야 한다)"""
import sys

target, part, start, end = sys.argv[1:5]
s = open(target, encoding="utf-8").read()
assert s.count(start) == 1 and s.count(end) == 1, (s.count(start), s.count(end))
a, b = s.index(start), s.index(end)
assert a < b
new = open(part, encoding="utf-8").read()
open(target, "w", encoding="utf-8", newline="\n").write(s[:a] + new + s[b:])
print("spliced", a, b, len(new))
