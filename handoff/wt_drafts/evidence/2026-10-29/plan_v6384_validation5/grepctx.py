import sys,re,glob
pat=re.compile(sys.argv[1]); out=open(sys.argv[2],'w',encoding='utf-8'); W=int(sys.argv[3]) if len(sys.argv)>3 else 180
files=sys.argv[4:] if len(sys.argv)>4 else sorted(glob.glob('snap/*.plan.md'))
for f in files:
    for i,l in enumerate(open(f,encoding='utf-8'),1):
        for m in pat.finditer(l):
            out.write(f'{f.split("/")[-1]}:{i}: ...{l[max(0,m.start()-W):m.end()+W].strip()}...\n')
