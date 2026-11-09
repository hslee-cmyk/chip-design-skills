# 지운 낱말 구간(연속 삭제 토큰 묶음)이 design 이력 파일(190e764c)에 원문 그대로 있는지 대조.
# 사용: python moved_check2.py <worktree> <out.jsonl> <commit>...
import sys,subprocess,re,difflib,json
W=sys.argv[1]; out=sys.argv[2]; commits=sys.argv[3:]
DOCS=['docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md','docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md','docs/02-design/features/gain-budget-gmid-sizing.42-gap-checklist.design.md']
HIST='docs/02-design/features/gain-budget-gmid-sizing.design.history.md'
def show(rev,path):
    return subprocess.run(['git','-C',W,'show',f'{rev}:{path}'],capture_output=True).stdout.decode('utf-8')
hist=show('190e764c',HIST)
norm=lambda s: re.sub(r'\s+',' ',s).strip()
H=norm(hist)
tok=lambda s: re.findall(r'\S+|\s+',s)
res=[]
for c in commits:
    for d in DOCS:
        a=show(c+'~1',d); b=show(c,d)
        if a==b: continue
        sm=difflib.SequenceMatcher(None,a.split('\n'),b.split('\n'),autojunk=False)
        for op,i1,i2,j1,j2 in sm.get_opcodes():
            if op=='equal': continue
            A='\n'.join(a.split('\n')[i1:i2]); B='\n'.join(b.split('\n')[j1:j2])
            ta,tb=tok(A),tok(B)
            s2=difflib.SequenceMatcher(None,ta,tb,autojunk=False)
            for o,x1,x2,y1,y2 in s2.get_opcodes():
                if o in('delete','replace'):
                    seg=''.join(ta[x1:x2]); n=norm(seg)
                    if len(n)<40: continue
                    found = n in H
                    # try strip markdown list/quote prefixes and table pipes
                    if not found:
                        parts=[p for p in re.split(r'\s*\|\s*|\n',seg) if len(norm(p))>=40]
                        found_parts=[norm(p) in H for p in parts]
                        found = bool(parts) and all(found_parts)
                        partial = sum(found_parts)/len(parts) if parts else 0
                    else: partial=1
                    res.append({'commit':c,'doc':d.split('.')[1],'old_line':i1+1,'len':len(n),'found':found,'partial':round(partial,2),'head':n[:160]})
with open(out,'w',encoding='utf-8') as f:
    for r in res: f.write(json.dumps(r,ensure_ascii=False)+'\n')
import collections
agg=collections.defaultdict(lambda:[0,0,0,0])
for r in res:
    k=r['commit'];agg[k][0]+=1;agg[k][1]+=r['found'];agg[k][2]+=r['len'];agg[k][3]+=r['len'] if r['found'] else 0
for k,v in agg.items(): print(k,'segs',v[0],'found',v[1],'bytes',v[2],'found_bytes',v[3])
