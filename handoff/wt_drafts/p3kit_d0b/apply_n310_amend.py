"""D0b 작성 전 실측(측정 전용): p3_doc_amendments.md §1 (a)~(d) N3.10 블록을 격리 복제본 계획서에 적용한다.

    python -B apply_n310_amend.py <복제본 루트> <amendments md> <ga|na>

'현재' 블록이 해당 줄(522·523·526·528)과 정확히 같지 않으면 exit 1(아무것도 쓰지 않음). 저장소 원본은 건드리지 않는다.
"""
import os
import re
import sys

ROOT, AMD, VAR = sys.argv[1:4]
PLAN = os.path.join(ROOT, "docs/01-plan/features/gain-budget-gmid-sizing.plan.md")
blocks = [b for b in re.findall(r"```\n(.*?)\n```", open(AMD, encoding="utf-8").read(), flags=re.S) if not b.startswith("…")]
# 문서 순서: a_cur, a_ga, a_na, b_cur, b_new, c_cur, c_new, d_cur, d_new, ...
spec = [(522, 0, 1 if VAR == "ga" else 2), (523, 3, 4), (526, 5, 6), (528, 7, 8)]
raw = open(PLAN, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in raw else "\n"
lines = raw.split(nl)
for ln, ci, ni in spec:
    if lines[ln - 1] != blocks[ci]:
        print("current mismatch at %d" % ln)
        sys.exit(1)
for ln, ci, ni in spec:
    lines[ln - 1] = blocks[ni]
open(PLAN, "w", encoding="utf-8", newline="").write(nl.join(lines))
print("applied", VAR)
