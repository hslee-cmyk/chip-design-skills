"""F1/F2 작성 전 실측(측정 전용): p3_doc_amendments.md §1 (a)(가)~(d)·§9 (e)~(h)의 N3.10 행(plan.md 521~529)을 격리 복제본 계획서에 적용한다.

    python -B apply_ud0_v85.py <복제본 루트> <p3_doc_amendments.md>

'현재 `plan.md:N`:' 다음 코드 블록 = 현재, 그다음 코드 블록 = 새 문안((a)는 첫 새 문안 = D-19 (가)). N이 521~529인 것만.
'현재'가 그 줄과 정확히 같지 않으면 exit 1(아무것도 쓰지 않음).
"""
import re
import sys

ROOT, AMD = sys.argv[1:3]
PLAN = ROOT + "/docs/01-plan/features/gain-budget-gmid-sizing.plan.md"
md = open(AMD, encoding="utf-8").read()
spec = []
for m in re.finditer(r"현재 `plan\.md:(\d+)`:\n```\n(.*?)\n```\n(.*?)```\n(.*?)\n```", md, flags=re.S):
    ln = int(m.group(1))
    if 521 <= ln <= 529:
        spec.append((ln, m.group(2), m.group(4)))
raw = open(PLAN, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in raw else "\n"
lines = raw.split(nl)
lns = sorted(s[0] for s in spec)
for ln, cur, new in spec:
    if lines[ln - 1] != cur:
        print("current mismatch at %d" % ln)
        sys.exit(1)
for ln, cur, new in spec:
    lines[ln - 1] = new
open(PLAN, "w", encoding="utf-8", newline="").write(nl.join(lines))
print("applied lines", lns)
