import re,io,sys,glob,collections
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
pat=re.compile(r'(?:승인 대기|사용자 확인 대기|사용자 결정 대기|확인 대기)[^)\];|]{0,40}?(P\d+(?:-[A-Za-z0-9]+)?|U-[abc])')
for f in sorted(glob.glob('snap/*.plan.md')):
    c=collections.Counter(); lines=collections.defaultdict(set)
    for n,l in enumerate(open(f,encoding='utf-8').read().split('\n'),1):
        if n==11 and 'gain' in f: continue
        for m in pat.finditer(l): c[m.group(1)]+=1; lines[m.group(1)].add(n)
    print(f, dict(sorted(c.items())))
    for k in sorted(lines): print('   ',k,sorted(lines[k])[:12])
