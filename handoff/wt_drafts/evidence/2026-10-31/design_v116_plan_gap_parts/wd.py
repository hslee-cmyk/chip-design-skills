import difflib,sys,re
name=sys.argv[1]
o=open(f'old_{name}.md',encoding='utf-8').read().splitlines()
n=open(f'new_{name}.md',encoding='utf-8').read().splitlines()
sm=difflib.SequenceMatcher(None,o,n,autojunk=False)
heads=[]
cur=''
hd={}
for i,l in enumerate(n):
    if l.startswith('#'): cur=l[:90]
    hd[i]=cur
tok=lambda s: re.findall(r'\s+|[^\s]+',s)
out=open(f'wd_{name}.txt','w',encoding='utf-8')
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    out.write(f'\n===== {tag} old {i1+1}-{i2} new {j1+1}-{j2} | {hd.get(j1,hd.get(j1-1,""))}\n')
    a='\n'.join(o[i1:i2]); b='\n'.join(n[j1:j2])
    ta,tb=tok(a),tok(b)
    s2=difflib.SequenceMatcher(None,ta,tb,autojunk=False)
    for t,a1,a2,b1,b2 in s2.get_opcodes():
        if t=='equal': continue
        ctx=''.join(tb[max(0,b1-6):b1])[-60:]
        da=''.join(ta[a1:a2]).strip(); db=''.join(tb[b1:b2]).strip()
        if not da and not db: continue
        out.write(f'  [{t}] ctx«{ctx.strip()}»\n')
        if da: out.write(f'    - {da}\n')
        if db: out.write(f'    + {db}\n')
