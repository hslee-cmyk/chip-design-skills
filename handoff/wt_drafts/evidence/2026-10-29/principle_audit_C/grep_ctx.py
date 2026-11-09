import re,sys,io
# usage: grep_ctx.py pattern width file...
pat=re.compile(sys.argv[1]); w=int(sys.argv[2])
out=io.open(sys.stdout.fileno(),'w',encoding='utf-8',closefd=False)
for f in sys.argv[3:]:
    for i,l in enumerate(io.open(f,encoding='utf-8',errors='replace'),1):
        for m in pat.finditer(l):
            s=max(0,m.start()-w); e=min(len(l),m.end()+w)
            out.write(f"{f.split('/')[-1]}:{i}:[{m.start()}] ...{l[s:e].strip()}...\n")
