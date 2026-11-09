# 기계 정리 커밋(줄 수 같음)의 줄별 문자 diff: 삽입 유무, 지운 조각을 패턴으로 분류, 표본 덤프.
import sys,subprocess,difflib,re,json,random,collections
W=sys.argv[1]; c=sys.argv[2]; out=sys.argv[3]
DOCS=['docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md','docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md','docs/02-design/features/gain-budget-gmid-sizing.42-gap-checklist.design.md']
show=lambda r,p: subprocess.run(['git','-C',W,'show',f'{r}:{p}'],capture_output=True).stdout.decode('utf-8')
PAT={
 'line': re.compile(r'^(:\d[\d\-,·]*( ?[,·] ?:?\d[\d\-]*)*)$|^:\d'),
 'vtag': re.compile(r'v1\.\d+'),
 'vref': re.compile(r'(검증|재검증|gap|R-|M-|N-|S-|MJ|V\d)'),
}
recs=[];cnt=collections.Counter()
for d in DOCS:
    a=show(c+'~1',d).split('\n'); b=show(c,d).split('\n')
    if len(a)!=len(b): print('LINECOUNT DIFF',d,len(a),len(b))
    for i,(x,y) in enumerate(zip(a,b)):
        if x==y: continue
        sm=difflib.SequenceMatcher(None,x,y,autojunk=False)
        dels=[];ins=[]
        for op,i1,i2,j1,j2 in sm.get_opcodes():
            if op in('delete','replace'): dels.append(x[i1:i2])
            if op in('insert','replace'): ins.append(y[j1:j2])
        cls=[]
        for s in dels:
            k='other'
            for n,p in PAT.items():
                if p.search(s): k=n;break
            cls.append(k);cnt[k]+=1
        recs.append({'doc':d.split('.')[1],'line':i+1,'dels':dels,'ins':ins,'cls':cls})
        if ins: cnt['ins_lines']+=1
json.dump(recs,open(out,'w',encoding='utf-8'),ensure_ascii=False,indent=0)
print(c,'changed lines',len(recs),dict(cnt))
