import json,sys,collections
d=json.load(open(sys.argv[1],encoding='utf-8'))
for p,i in d['files'].items():
    for r in i.get('reads',[]):
        if r.get('dest') is None and r['form']!='getattr': print(p, r['line'], r['mod'], r['name'], r['form'])
