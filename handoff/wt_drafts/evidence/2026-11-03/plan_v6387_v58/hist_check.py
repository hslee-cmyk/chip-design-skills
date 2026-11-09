"""v52 history losslessness ef911010 -> c19c4f17.
(1) each history file: line-level opcodes insert only, new minus inserted lines == old bytes, CRLF count delta.
(2) plan char-level deleted/replaced-away segments >= MIN chars: is the old segment present (verbatim, or with '|'->'\\|')
    in any c19c4f17 history file? Report misses with context."""
import subprocess, difflib
W = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6387"
OUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-03/plan_v6387_v58/hist_check_out.txt"
A, B = "c11fcf9f", "106cd524"
names = ["gain-budget-gmid-sizing", "graph-consumption", "headroom-chain", "offset-strategy", "offset-trim", "oracle-portability"]
MIN = 60

def raw(rev, p):
    return subprocess.run(["git", "-C", W, "show", f"{rev}:{p}"], capture_output=True).stdout

o = open(OUT, "w", encoding="utf-8")
hist_all = ""
for n in names:
    p = f"docs/01-plan/features/{n}.history.md"
    a, b = raw(A, p), raw(B, p)
    al, bl = a.split(b"\n"), b.split(b"\n")
    ops = [op for op in difflib.SequenceMatcher(None, al, bl, autojunk=False).get_opcodes() if op[0] != "equal"]
    kinds = {op[0] for op in ops}
    ins = set()
    for op, i1, i2, j1, j2 in ops:
        if op == "insert":
            ins.update(range(j1, j2))
    rest = b"\n".join(x for k, x in enumerate(bl) if k not in ins)
    o.write(f"[hist] {n}: ops={sorted(kinds)} n_ops={len(ops)} inserted_lines={len(ins)} rest==old {rest == a} CRLF old={a.count(b'\\r\\n')} new={b.count(b'\\r\\n')}\n")
    hist_all += b.decode("utf-8") + "\n"
hist_esc = hist_all.replace("\\|", "|")
miss = 0; tot = 0
for n in names:
    p = f"docs/01-plan/features/{n}.plan.md"
    a, b = raw(A, p).decode("utf-8").split("\n"), raw(B, p).decode("utf-8").split("\n")
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        if op == "replace" and i2 - i1 == j2 - j1:
            for k in range(i2 - i1):
                x, y = a[i1 + k], b[j1 + k]
                cs = difflib.SequenceMatcher(None, x, y, autojunk=False)
                for o2, p1, p2, q1, q2 in cs.get_opcodes():
                    if o2 in ("delete", "replace") and p2 - p1 >= MIN:
                        seg = x[p1:p2]; tot += 1
                        ok = seg in hist_all or seg.replace("\\|", "|") in hist_esc
                        if not ok:
                            # try: whole old line present?
                            ok2 = x in hist_all or x.replace("\\|", "|") in hist_esc
                            miss += 0 if ok2 else 1
                            o.write(f"[{'LINE-OK' if ok2 else 'MISS'}] {n} old {i1+k+1} len {p2-p1}: {seg[:400]}\n")
        else:
            for k in range(i1, i2):
                if len(a[k]) >= MIN:
                    tot += 1
                    ok = a[k] in hist_all or a[k].replace("\\|", "|") in hist_esc
                    if not ok:
                        miss += 1
                        o.write(f"[MISS-LINE] {n} old {k+1}: {a[k][:400]}\n")
o.write(f"segments checked {tot}, miss {miss}\n")
o.close()
print("done", tot, miss)
