import json,sys,os
d=sys.argv[1]; out=open(sys.argv[2],'w',encoding='utf-8')
for fn in ['wsweep.out.jsonl','wsweep2.out.jsonl','wsweep3.out.jsonl']:
    agg={}
    for line in open(os.path.join(d,fn),encoding='utf-8'):
        r=json.loads(line); k=r['kind']
        for b in r['interp']:
            a=agg.setdefault(k,{'w':0,'inv':0,'g':0})
            a['w']=max(a['w'],b['max_abs_err_lin_w']); a['inv']=max(a['inv'],b['max_abs_err_lin_invw']); a['g']=max(a['g'],b['max_abs_err_gmid_lin_w'])
    out.write(fn+' '+json.dumps({k:{x:round(v*100,2) for x,v in a.items()} for k,a in agg.items()})+'\n')
