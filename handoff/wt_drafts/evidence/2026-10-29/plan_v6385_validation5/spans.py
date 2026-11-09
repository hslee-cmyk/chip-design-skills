"""커밋 7252a725 -> 7252a725 바뀐 조각 추출(줄 번호 = 새 파일). 결과 = spans.txt"""
import difflib
import subprocess

W = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6385"
M = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-29/plan_v6385_validation5/"
out = open(M + "spans.txt", "w", encoding="utf-8")
for f in ("plan", "history"):
    p = "docs/01-plan/features/gain-budget-gmid-sizing.%s.md" % f
    old = subprocess.run(["git", "-C", W, "show", "7252a725:" + p], capture_output=True).stdout.decode("utf-8")
    new = subprocess.run(["git", "-C", W, "show", "426c98b7:" + p], capture_output=True).stdout.decode("utf-8")
    open(M + "old_%s.md" % f, "w", encoding="utf-8").write(old)
    open(M + "new_%s.md" % f, "w", encoding="utf-8").write(new)
    a, b = old.split("\n"), new.split("\n")
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        out.write("\n#### %s %s old %d-%d new %d-%d\n" % (f, tag, i1 + 1, i2, j1 + 1, j2))
        if tag == "replace" and i2 - i1 == j2 - j1:
            for k in range(i2 - i1):
                x, y = a[i1 + k], b[j1 + k]
                s2 = difflib.SequenceMatcher(None, x, y, autojunk=False)
                out.write("-- line new %d\n" % (j1 + k + 1))
                for t, p1, p2, q1, q2 in s2.get_opcodes():
                    if t == "equal":
                        continue
                    ctx = x[max(0, p1 - 60):p1]
                    out.write("  [%s] ctx«%s»\n    OLD«%s»\n    NEW«%s»\n" % (t, ctx, x[p1:p2], y[q1:q2]))
        else:
            for k in range(i1, i2):
                out.write("OLD %d: %s\n" % (k + 1, a[k]))
            for k in range(j1, j2):
                out.write("NEW %d: %s\n" % (k + 1, b[k]))
out.close()
