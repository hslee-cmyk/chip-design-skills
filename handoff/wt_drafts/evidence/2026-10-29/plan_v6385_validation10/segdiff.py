"""Segment-level diff of changed lines between two plan versions (validation 9)."""
import difflib, re, sys, os
D = os.path.dirname(os.path.abspath(__file__))
a_c, b_c, kind = sys.argv[1], sys.argv[2], sys.argv[3]  # kind = plan|hist
A = open(os.path.join(D, f"{kind}_{a_c}.md"), encoding="utf-8").read().split("\n")
B = open(os.path.join(D, f"{kind}_{b_c}.md"), encoding="utf-8").read().split("\n")
out = open(os.path.join(D, f"segdiff_{kind}_{a_c}_{b_c}.txt"), "w", encoding="utf-8")
sm = difflib.SequenceMatcher(None, A, B, autojunk=False)
def segs(s):
    return re.split(r"(?<=[.;。])\s+|(?<=\))\s*,\s+|\s+--\s+", s)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal":
        continue
    out.write(f"\n===== {tag} old {i1+1}-{i2} new {j1+1}-{j2}\n")
    old = " ".join(A[i1:i2]); new = " ".join(B[j1:j2])
    if tag == "insert" or not old:
        for k in range(j1, j2):
            out.write(f"[+{k+1}] {B[k]}\n")
        continue
    sa, sb = segs(old), segs(new)
    m2 = difflib.SequenceMatcher(None, sa, sb, autojunk=False)
    for t2, a1, a2, b1, b2 in m2.get_opcodes():
        if t2 == "equal":
            continue
        for s in sa[a1:a2]:
            out.write(f"  - {s}\n")
        for s in sb[b1:b2]:
            out.write(f"  + {s}\n")
        out.write("  ~~\n")
out.close()
