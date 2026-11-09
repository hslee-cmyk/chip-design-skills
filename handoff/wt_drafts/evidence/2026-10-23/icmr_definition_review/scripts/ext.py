import sys,fitz,re
p=sys.argv[1]; pat=re.compile(sys.argv[2],re.I); out=sys.argv[3]
d=fitz.open(p)
with open(out,'w',encoding='utf-8') as f:
    f.write(f"# {p} pages={len(d)}\n")
    for i,pg in enumerate(d):
        t=pg.get_text()
        if pat.search(t):
            f.write(f"\n=== PDF page {i+1}\n{t}\n")
