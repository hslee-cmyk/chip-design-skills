import io,sys,glob,os
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
for k in sys.argv[1:]:
    for f in sorted(glob.glob('snap/*.md')):
        ls=[n for n,l in enumerate(open(f,encoding='utf-8').read().split('\n'),1) if k in l]
        if ls: print(k, os.path.basename(f), ls[:20])
