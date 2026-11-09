import sys,glob,re,os
pats=sys.argv[1:]
for f in sorted(glob.glob('snap/*.plan.md')):
    for i,l in enumerate(open(f,encoding='utf-8'),1):
        for p in pats:
            for m in re.finditer(re.escape(p),l):
                print(f'{os.path.basename(f)}:{i}: ...{l[max(0,m.start()-110):m.end()+110].strip()}...')
