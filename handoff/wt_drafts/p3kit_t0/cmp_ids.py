"""pytest -rA 출력 두 개의 (판정, test id) 집합 대조(측정 전용).

    C:/Python314/python.exe -B cmp_ids.py <출력 A> <출력 B> [<결과 JSON>]

test id는 'skills' 앞 경로를 지워 복제본 위치와 무관하게 맞춘다. 결과(같음 여부·차이·판정별 수)를 stdout과 JSON에 쓴다.
"""
import collections
import json
import re
import sys

PAT = re.compile(r"^(PASSED|FAILED|XFAIL|XPASS|ERROR|SKIPPED) (.*)$")


def load(p):
    out = set()
    with open(p, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = PAT.match(line.rstrip("\n"))
            if not m:
                continue
            tid = m.group(2).replace("\\", "/")
            i = tid.find("skills/")
            tid = tid[i:] if i >= 0 else tid
            tid = re.sub(r" - .*$", "", tid) if m.group(1) in ("XFAIL", "SKIPPED") else tid
            out.add((m.group(1), tid))
    return out


a, b = load(sys.argv[1]), load(sys.argv[2])
res = {"same": a == b, "count_a": dict(collections.Counter(v for v, _ in a)), "count_b": dict(collections.Counter(v for v, _ in b)),
       "only_a": sorted(a - b)[:50], "only_b": sorted(b - a)[:50],
       "ids_same": {t for _, t in a} == {t for _, t in b}}
print(json.dumps(res, ensure_ascii=False, indent=1))
if len(sys.argv) > 3:
    with open(sys.argv[3], "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
