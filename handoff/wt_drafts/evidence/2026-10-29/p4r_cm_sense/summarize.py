import json, math
rows=[json.loads(l) for l in open('results.jsonl',encoding='utf-8')]
P=r'C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-29/p4r_cm_sense/summary.txt'
per_ohm_area = (0.33e-6**2)/48.2   # 엔진 면적 단위(area_decl: W_min^2/R□, sky130_pdk_decl poly_generic)
budget = 4e-8
out=[]
for v in ('ideal','par'):
    out.append(f'## variant={v}')
    out.append('R[ohm] | A_dm(DC) dB | T_dm(DC) dB | eps_static % | UGF_dm MHz | PM_dm deg | T_cm(DC) dB | UGF_cm MHz | PM_cm deg | r_out kohm | C_gg37a fF | Cpar_half fF | f_p(Voc) MHz | area 2R / budget %')
    for R in sorted({r['R'] for r in rows}):
        lg=[r for r in rows if r['R']==R and r['variant']==v and r['mode']=='lg']
        cm=[r for r in rows if r['R']==R and r['variant']==v and r['mode']=='cm']
        if not lg or not cm: continue
        lg,cm=lg[-1],cm[-1]
        op=lg['op']
        g15=op['@m.xm15.msky130_fd_pr__pfet_01v8[gds]']; g16=op['@m.xm16.msky130_fd_pr__nfet_01v8[gds]']
        ro=1/(g15+g16); cg=op['@m.xm37a.msky130_fd_pr__nfet_01v8[cgg]']
        cpar=lg['cpar_half_f']
        cvoc=cg+2*cpar
        fp=1/(2*math.pi*(R/2)*cvoc)
        t=lg['T_dm']; c=cm['T_cm']
        eps=100/(1+10**(t['t0_db']/20))
        area=2*(R*per_ohm_area)/budget*100
        f=lambda x,s=1: 'n/a' if x is None else f'{x/s:.3g}'
        out.append(f"{R:.0e} | {lg['A_dm_dc_db']:.2f} | {t['t0_db']:.2f} | {eps:.3f} | {f(t['ugf_hz'],1e6)} | {f(t['pm_deg'])} | {c['t0_db']:.2f} | {f(c['ugf_hz'],1e6)} | {f(c['pm_deg'])} | {ro/1e3:.2f} | {cg*1e15:.2f} | {cpar*1e15:.1f} | {fp/1e6:.3g} | {area:.2f}")
open(P,'w',encoding='utf-8').write('\n'.join(out)+'\n')
print('\n'.join(out))
