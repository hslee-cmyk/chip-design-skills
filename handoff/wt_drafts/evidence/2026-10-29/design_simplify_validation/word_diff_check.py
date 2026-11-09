# 독립 낱말 diff: 바뀐 줄 쌍(-/+)마다 지워진 낱말 구간과 더해진 낱말 구간을 뽑고,
# 지워진 구간이 moved_text.md에 원문 그대로 있는지 확인한다. 결과 = word_diff_check.out.md
import re, difflib
diff = open('diff_285ec820_fc874bd6.diff', encoding='utf-8').read().splitlines()
mv = re.sub(r'\s+', ' ', open('../design_v1152/simplify/moved_text.md', encoding='utf-8').read())

# group hunks
hunks = []
cur = None
for l in diff:
    if l.startswith('@@'):
        cur = {'hdr': l, 'm': [], 'p': []}
        hunks.append(cur)
    elif cur is not None and l.startswith('-') and not l.startswith('---'):
        cur['m'].append(l[1:])
    elif cur is not None and l.startswith('+') and not l.startswith('+++'):
        cur['p'].append(l[1:])

def toks(s):
    return re.findall(r'\S+', s)

out = ['# 낱말 diff 독립 확인 (285ec820 -> fc874bd6)', '']
for h in hunks:
    a = toks(' '.join(h['m'])); b = toks(' '.join(h['p']))
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    out.append('## ' + h['hdr'][:60])
    out.append(f'- 지운 낱말 {len(a)} / 더한 낱말 {len(b)} / 공통 비 {sm.ratio():.3f}')
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal':
            continue
        rem = ' '.join(a[i1:i2]); add = ' '.join(b[j1:j2])
        inmv = (rem in mv) if rem else None
        if len(rem) > 600:
            rem_s = rem[:300] + ' ... ' + rem[-200:]
        else:
            rem_s = rem
        out.append(f'- [{op}] 지움({len(rem)}자, moved_text 원문 존재={inmv}): «{rem_s}»')
        if add:
            out.append(f'  더함: «{add[:600]}»')
    out.append('')
open('word_diff_check.out.md', 'w', encoding='utf-8').write('\n'.join(out))
print('ok', len(hunks))
