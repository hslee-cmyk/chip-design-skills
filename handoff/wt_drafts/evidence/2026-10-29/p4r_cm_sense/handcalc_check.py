"""손계산 A(R) = A_inf * R/(R + r_o), r_o = 1/(gds15+gds16) (op 값) 대 SPICE A_dm(DC) -- 이상 R."""
import json, math
rows=[json.loads(l) for l in open('results.jsonl',encoding='utf-8') if json.loads(l)['variant']=='ideal' and json.loads(l)['mode']=='lg']
inf=[r for r in rows if r['R']==1e9][0]
A_inf=10**(inf['A_dm_dc_db']/20)
op=inf['op']; ro=1/(op['@m.xm15.msky130_fd_pr__pfet_01v8[gds]']+op['@m.xm16.msky130_fd_pr__nfet_01v8[gds]'])
out=['R | SPICE A dB | hand A dB | diff dB']
for r in sorted(rows,key=lambda x:x['R']):
    R=r['R']; h=20*math.log10(A_inf*R/(R+ro))
    out.append(f"{R:.0e} | {r['A_dm_dc_db']:.3f} | {h:.3f} | {r['A_dm_dc_db']-h:+.3f}")
for name,Areq_db in (('gain_ss_db 54 (SF-1 전 선언)',54.0),):
    Areq=10**(Areq_db/20); Rmin=ro*Areq/(A_inf-Areq)
    out.append(f'R_min[{name}] = r_o*A_req/(A_inf-A_req) = {Rmin:.4g} ohm (A_inf {20*math.log10(A_inf):.2f} dB, r_o {ro:.4g})')
beta=10**((inf['T_dm']['t0_db']-inf['A_dm_dc_db'])/20)
Areq=(1/1e-3-1)/beta
out.append(f'static eps 0.1% -> T_req = 999 (60.0 dB), beta = {beta:.4f}, A_req = {Areq:.1f} ({20*math.log10(Areq):.2f} dB) vs A_inf {20*math.log10(A_inf):.2f} dB -> reachable: {A_inf>Areq}')
open('handcalc_check.txt','w',encoding='utf-8').write('\n'.join(out)+'\n'); print('\n'.join(out))
