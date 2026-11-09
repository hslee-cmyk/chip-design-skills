import re
op=open('old_gain-budget-gmid-sizing.plan.md',encoding='utf-8').read()
np_=open('new_gain-budget-gmid-sizing.plan.md',encoding='utf-8').read()
oh=open('old_gain-budget-gmid-sizing.history.md',encoding='utf-8').read().split('\n')
nh=open('new_gain-budget-gmid-sizing.history.md',encoding='utf-8').read().split('\n')
out=open('hist_check.txt','w',encoding='utf-8')
# old history lines preserved in order
import difflib
sm=difflib.SequenceMatcher(None,oh,nh,autojunk=False)
dele=[op_ for op_ in sm.get_opcodes() if op_[0] in('delete','replace')]
out.write('옛 history 줄 삭제·변경 opcodes: %d\n'%len(dele))
old9=__import__('subprocess').run(['git','-C','C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6385','show','634310e0:docs/01-plan/features/gain-budget-gmid-sizing.plan.md'],capture_output=True).stdout.decode('utf-8')
for i in range(1831,1848):
    l=nh[i]
    m=re.search(r'원문: «(.*)»',l)
    if not m: out.write(f'L{i+1}: «원문» 없음\n'); continue
    t=m.group(1).replace('\|','|')
    out.write(f'L{i+1}: in_old(9fc13765)={t in op} in_new={t in np_} in_634310e0={t in old9} len={len(t)} :: {l[:90]}\n')
out.close(); print(open('hist_check.txt',encoding='utf-8').read())
