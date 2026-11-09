import json,glob,io,os
A='chip-design-skills/skills/analog-gmid-design/assets'
out=io.open('wt/_drafts/evidence/2026-10-29/principle_audit_C/spec_values.txt','w',encoding='utf-8')
def walk(o,path):
    if isinstance(o,dict):
        if 'value' in o or 'value_farad' in o or 'value_ohm' in o or 'values' in o or 'rule' in o:
            src=o.get('source',{})
            v={k:o[k] for k in o if k.startswith('value') or k in('rule','op','metric')}
            out.write(f"  {path}: {json.dumps(v,ensure_ascii=False)[:160]} | kind={src.get('kind')} origin={src.get('origin')} plan_id={src.get('plan_id')} | {str(src.get('record',src.get('citation','')))[:260]}\n")
        for k,x in o.items():
            if k=='source': continue
            walk(x,path+'.'+k)
    elif isinstance(o,list):
        for i,x in enumerate(o):
            walk(x,path+f'[{i}]')
for f in sorted(glob.glob(A+'/library/*.sizing_spec.json')+glob.glob(A+'/heldout/*.sizing_spec.json')):
    out.write('=== '+f.split('assets/')[1]+'\n')
    walk(json.load(io.open(f,encoding='utf-8')),'')
