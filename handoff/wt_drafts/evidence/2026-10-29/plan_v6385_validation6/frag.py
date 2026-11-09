import sys, re, difflib
old, new, out = sys.argv[1], sys.argv[2], sys.argv[3]
a = open(old, encoding='utf-8').read().splitlines()
b = open(new, encoding='utf-8').read().splitlines()
sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
res = []
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == 'equal':
        continue
    if tag == 'insert' or (tag=='replace' and (i2-i1)!=(j2-j1)) or tag=='delete':
        for k in range(j1, j2):
            res.append(f"### INSERTED new line {k+1}\n{b[k]}\n")
        for k in range(i1, i2):
            if tag != 'insert':
                res.append(f"### REMOVED old line {k+1}\n{a[k][:400]}...\n")
        continue
    for k in range(i2-i1):
        x, y = a[i1+k], b[j1+k]
        ta = re.findall(r'\S+|\s+', x); tb = re.findall(r'\S+|\s+', y)
        s2 = difflib.SequenceMatcher(None, ta, tb, autojunk=False)
        res.append(f"### CHANGED old {i1+k+1} -> new {j1+k+1}")
        for t, p1, p2, q1, q2 in s2.get_opcodes():
            if t == 'equal':
                continue
            ctxb = ''.join(tb[max(0,q1-30):q1])
            ctxa = ''.join(tb[q2:q2+30])
            res.append(f"  [{t}] ...{ctxb[-200:]}\n    OLD: {''.join(ta[p1:p2])}\n    NEW: {''.join(tb[q1:q2])}\n    ...{ctxa[:200]}")
        res.append('')
open(out, 'w', encoding='utf-8').write('\n'.join(res))
