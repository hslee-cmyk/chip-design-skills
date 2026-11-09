"""scratch: apply p3_doc_amendments.md v8.5 §1 (a)(가)~(d) + §9 (e)~(h) to the clone's plan (exact '현재' match asserted)."""
import re, sys
ROOT, AMD = sys.argv[1:3]
PLAN = ROOT + "/docs/01-plan/features/gain-budget-gmid-sizing.plan.md"
t = open(AMD, encoding="utf-8").read()
# pairs: '현재 `plan.md:N`:' block followed by next '새 문안' block(s); for (a) take the first new block ((가))
pairs = []
for m in re.finditer(r"현재 `plan\.md:(\d+)`:\n```\n(.*?)\n```\n(.*?)```\n(.*?)\n```", t, flags=re.S):
    pairs.append((int(m.group(1)), m.group(2), m.group(4)))
raw = open(PLAN, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in raw else "\n"
L = raw.split(nl)
pairs = [p for p in pairs if p[0] in (521, 522, 523, 524, 525, 526, 528, 529)]
assert sorted(p[0] for p in pairs) == [521, 522, 523, 524, 525, 526, 528, 529], [p[0] for p in pairs]
for ln, cur, new in pairs:
    if L[ln - 1] != cur:
        sys.exit("current mismatch %d" % ln)
for ln, cur, new in pairs:
    L[ln - 1] = new
open(PLAN, "w", encoding="utf-8", newline="").write(nl.join(L))
print("applied", len(pairs), "blocks; MOD2 rail_declaration" , "rail_declaration" in L[521])
