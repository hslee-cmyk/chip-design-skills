import sys,re,json
diff=open('diff_285ec820_fc874bd6.diff',encoding='utf-8').read().splitlines()
mv=open('../design_v1152/simplify/moved_text.md',encoding='utf-8').read()
mvn=re.sub(r'\s+',' ',mv)
out=[]
for i,l in enumerate(diff,1):
    if l.startswith('-') and not l.startswith('---'):
        t=l[1:].strip()
        if not t: continue
        tn=re.sub(r'\s+',' ',t)
        full = tn in mvn
        # chunk check: fraction of 80-char chunks present
        ch=[tn[k:k+60] for k in range(0,len(tn),60)]
        frac=sum(c in mvn for c in ch)/len(ch)
        out.append(dict(diff_line=i,len=len(t),verbatim=full,chunk_frac=round(frac,3),head=t[:70]))
with open('moved_check.out.jsonl','w',encoding='utf-8') as f:
    for o in out: f.write(json.dumps(o,ensure_ascii=False)+'\n')
for o in out: print(o['diff_line'],o['len'],o['verbatim'],o['chunk_frac'],o['head'][:40])
