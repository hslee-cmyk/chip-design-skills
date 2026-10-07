"""-rA 'short test summary info' 절의 요약 줄 전체를 키로 base·병합본 대조(공백 든 parametrize id 때문에
id를 \\S+로 자르지 않는다). 결과 종류는 줄 머리 단어, id는 머리 단어 뒤 줄 전체(XFAIL의 ' - 사유' 포함).
usage: python cmp_v1.py <base.txt> <M.txt>"""
import re, sys
from collections import Counter

RX = re.compile(r"^(PASSED|FAILED|XFAIL|XPASS|ERROR|SKIPPED) (.+?)\s*$")


def load(p):
    lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
    start = max(i for i, l in enumerate(lines) if "short test summary info" in l)
    c = Counter()
    for line in lines[start + 1:]:
        m = RX.match(line)
        if m:
            c[(m.group(2), m.group(1))] += 1
    return c


b, m = load(sys.argv[1]), load(sys.argv[2])
kinds = lambda c: Counter(k for (_, k), n in c.items() for _ in range(n))
print("base lines", sum(b.values()), kinds(b), "dup keys", sum(1 for v in b.values() if v > 1))
print("M lines", sum(m.values()), kinds(m), "dup keys", sum(1 for v in m.values() if v > 1))
bid = {i for i, _ in b}
mid = {i for i, _ in m}
only_b = b - m
only_m = m - b
print("base에만(줄 단위)", sum(only_b.values()), sorted(only_b)[:10])
print("M에만(줄 단위)", sum(only_m.values()), sorted(only_m))
print("id 기준: base에만", len(bid - mid), "M에만", len(mid - bid))
changed = [(i, kb, km) for (i, kb) in b for (j, km) in m if i == j and kb != km]
print("결과 바뀐 기존 id", len(changed), changed[:10])
