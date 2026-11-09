import json,sys,collections
d=json.load(open(sys.argv[1],encoding='utf-8'))
q=collections.Counter()
for p,i in d['files'].items():
    for r in i.get('reads',[]):
        if r.get('dest') is None: q[(r['mod'],r['name'],r['form'])]+=1
print(q)
