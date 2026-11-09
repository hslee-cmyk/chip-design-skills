import json,glob,io,re,subprocess
A='chip-design-skills/skills/analog-gmid-design/assets'
out=io.open('wt/_drafts/evidence/2026-10-29/principle_audit_C/measure_summary.txt','w',encoding='utf-8')
# M1: dof_rank_sample_count 선언과 출처
n=0;tot=0
for f in sorted(glob.glob(A+'/library/*.sizing_spec.json')+glob.glob(A+'/heldout/*.sizing_spec.json')):
    tot+=1
    s=json.load(io.open(f,encoding='utf-8'))['human'].get('search',{}).get('dof_rank_sample_count')
    if s: n+=1; out.write(f"M1 {f.split('assets/')[1]} dof_rank_sample_count={s.get('value')} source={s.get('source')}\n")
out.write(f"M1 합계 {n}/{tot} spec이 dof_rank_sample_count 선언\n")
P='wt/plan-v6385/docs/01-plan/features/gain-budget-gmid-sizing.plan.md'
t=io.open(P,encoding='utf-8').read()
m=re.search(r'옛 기본 10은 근거 없는 상수라[^.]*',t); out.write('M1 계획 문언: '+(m.group(0) if m else 'NOT FOUND')+'\n')
# M2: 제약 출처 분류 (kind/origin)
from collections import Counter
c=Counter()
for f in sorted(glob.glob(A+'/library/*.sizing_spec.json')+glob.glob(A+'/heldout/*.sizing_spec.json')):
    grp='heldout' if 'heldout' in f else 'library'
    for k in json.load(io.open(f,encoding='utf-8'))['human'].get('constraints',[]):
        src=k.get('source',{}); c[(grp,src.get('kind'),src.get('origin'))]+=1
for k,v in sorted(c.items(),key=str): out.write(f"M2 constraints {k} = {v}\n")
# M3: 계획 문언 heldout 발동 단언
for pat in [r'유일 소비자 = heldout[^;)]*', r'13회로 발동 = heldout[^)]*\)', r'13회로 해당 = erfc[^,)]*', r'cnr_ota 단계 A가[^(]*', r'erfc_ota 단계 A[^(]*']:
    for p in ['chip-design-skills/docs/01-plan/features/gain-budget-gmid-sizing.plan.md',P]:
        for mm in re.finditer(pat,io.open(p,encoding='utf-8').read()):
            out.write(f"M3 {p.split('/')[0]}: {mm.group(0)[:200]}\n")
# M4: 근거 문서가 heldout 지위를 다룬 횟수
for f in ['cbox_rereview.md','erfc_region.md','flow_derivation.md']:
    s=io.open('wt/_drafts/evidence/2026-10-29/'+f,encoding='utf-8').read()
    out.write(f"M4 {f}: DEC-98 {s.count('DEC-98')}, U-75 {s.count('U-75')}, U-76 {s.count('U-76')}, '개발 회로' {s.count('개발 회로')}\n")
s=io.open('wt/_drafts/evidence/2026-10-23/audit_r2r_fport_cmr.md',encoding='utf-8').read()
out.write(f"M4 audit_r2r_fport_cmr.md: DEC-98 {s.count('DEC-98')}, U-75 {s.count('U-75')}, heldout 언급 {s.count('heldout')}\n")
out.close()
