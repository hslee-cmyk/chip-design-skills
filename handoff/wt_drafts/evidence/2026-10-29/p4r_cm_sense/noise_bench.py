"""폐루프 차동 출력 잡음(1 Hz~1 GHz 적분) 대 R -- 파일럿 r1 cl bench(base_pilot_r1_cl.cir), 이상 R."""
import os, re, subprocess, json, sys
HERE=os.path.dirname(os.path.abspath(__file__)); RUN=os.path.join(HERE,'runs')
NG=r"C:/ngspice/Spice64/bin/ngspice_con.exe"
base=open(os.path.join(HERE,'base_pilot_r1_cl.cir'),encoding='utf-8').read().split('.control')[0]
out=os.path.join(HERE,'noise_results.jsonl')
for R in [float(x) for x in sys.argv[1].split(',')]:
    lines=[l for l in base.split('\n') if not (l.lower().startswith('r1 ') or l.lower().startswith('r2 '))]
    lines+= [f'r1 Vom Voc {R:.6e}', f'r2 Voc Vop {R:.6e}']
    ctl=['.control','op','noise v(Vop,Vom) vsp dec 40 1 1e9','setplot noise2','print onoise_total','print onoise_r1','print onoise_r2','quit','.endc','.end']
    p=os.path.join(RUN,f'noise_R{R:.0e}.cir'.replace('+',''))
    open(p,'w',encoding='utf-8').write('\n'.join(lines+ctl)+'\n')
    r=subprocess.run([NG,'-b',p],capture_output=True,text=True,cwd=RUN)
    log=r.stdout+r.stderr
    open(p.replace('.cir','.log'),'w',encoding='utf-8').write(log)
    vals={m.group(1):float(m.group(2)) for m in re.finditer(r'^(onoise_\w+)\s*=\s*([-+0-9.eE]+)',log,re.M)}
    rec=dict(R=R,**vals)
    open(out,'a',encoding='utf-8').write(json.dumps(rec)+'\n')
    print(rec)
