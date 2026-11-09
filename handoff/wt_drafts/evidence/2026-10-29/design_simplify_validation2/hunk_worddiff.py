# word-level diff of each -/+ hunk in a unified -U0 diff; writes markdown
import sys,re,difflib
src,out=sys.argv[1],sys.argv[2]
lines=open(src,encoding='utf-8').read().split('\n')
hunks=[];cur=None
for l in lines:
    if l.startswith('@@'):
        cur={'h':l.split('@@')[1],'m':[],'p':[]};hunks.append(cur)
    elif cur is not None and l.startswith('-') and not l.startswith('---'): cur['m'].append(l[1:])
    elif cur is not None and l.startswith('+') and not l.startswith('+++'): cur['p'].append(l[1:])
tok=lambda s: re.findall(r'\S+|\s+',s)
with open(out,'w',encoding='utf-8') as f:
    for h in hunks:
        a=tok('\n'.join(h['m']));b=tok('\n'.join(h['p']))
        sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
        f.write(f"\n## hunk {h['h']}  (old {len(''.join(a))} B, new {len(''.join(b))} B)\n")
        for op,i1,i2,j1,j2 in sm.get_opcodes():
            if op=='equal': continue
            if i2>i1: f.write('  DEL: '+''.join(a[i1:i2]).strip()+'\n')
            if j2>j1: f.write('  ADD: '+''.join(b[j1:j2]).strip()+'\n')
