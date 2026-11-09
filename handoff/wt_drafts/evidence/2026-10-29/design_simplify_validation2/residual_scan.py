# 190e764c 40·41·42에서 남은 O-169 꼴(옛 본문+대체 표지 공존)·경위 단서·as-built 줄 인용·판 표지 수를 세고 줄 목록을 쓴다
import re,json
cues={
 'replace_marker': r'대상 소멸|대체된다|대체됨|v1\.\d+(?:\.\d+)? 대체|대체 --|\(대체\)',
 'old_text': r'옛 문언|옛 문장|옛 \S+ 문언|\(기록·폐지|~~',
 'version_tag': r'\bv1\.\d+(?:\.\d+)?\b',
 'verif_ref': r'(?:재?검증|재판정|재검증 \d) ?[A-Z]{1,2}\d*-?\d+|검증 \d+ [A-Z]',
 'asbuilt_line': r'\.py:\d',
 'commit_hash': r'`[0-9a-f]{7,8}`|\b[0-9a-f]{8}\b',
 'strike': r'~~',
}
out={}
rows=[]
for d in ['40','41','42']:
    L=open(f'{d}_190e764c.md',encoding='utf-8').read().split('\n')
    tot=sum(len(l.encode('utf-8'))+1 for l in L)
    s={'bytes':tot,'lines':len(L)}
    for k,p in cues.items():
        hits=[(i+1,len(re.findall(p,l)),len(l.encode('utf-8'))) for i,l in enumerate(L) if re.search(p,l)]
        s[k]={'lines':len(hits),'count':sum(h[1] for h in hits),'line_bytes':sum(h[2] for h in hits)}
        if k in('replace_marker','old_text'):
            for h in hits: rows.append({'doc':d,'line':h[0],'cue':k,'bytes':h[2],'head':L[h[0]-1][:160]})
    out[d]=s
json.dump(out,open('residual_scan.out.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
with open('residual_scan.lines.jsonl','w',encoding='utf-8') as f:
    for r in rows: f.write(json.dumps(r,ensure_ascii=False)+'\n')
for d,s in out.items():
    print(d,s['bytes'],s['lines'],{k:(v['lines'],v['count']) for k,v in s.items() if isinstance(v,dict)})
