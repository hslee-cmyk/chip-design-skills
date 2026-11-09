# 원칙 점검: fc874bd6 대 190e764c의 40·41·42 -- 새 backtick 이름, fail-closed 단서 수 변화(사라진 문장은 이력에 있는지), 숫자 리터럴 새로 생김, 회로 이름 새로 생김
import re,subprocess,json
W='C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115'
show=lambda r,p: subprocess.run(['git','-C',W,'show',f'{r}:{p}'],capture_output=True).stdout.decode('utf-8')
P='docs/02-design/features/gain-budget-gmid-sizing.%s.design.md'
names={'40':'40-engine','41':'41-gain-budget','42':'42-gap-checklist'}
hist=show('190e764c','docs/02-design/features/gain-budget-gmid-sizing.design.history.md')
circuits=['two_stage','current_reuse','nmcnr','folded','pushpull','common_gate','telescopic','ngcc','cnr_ota','erfc','sf_pushpull','r2r']
rep={}
for k,n in names.items():
    a=show('fc874bd6',P%n); b=show('190e764c',P%n)
    bt=lambda t:set(re.findall(r'`([^`\n]{1,80})`',t))
    new=sorted(bt(b)-bt(a))
    fc=lambda t:{c:len(re.findall(c,t)) for c in ['fail-closed','정의 불능','거부','정지','봉인 실패','fail\b','undefined']}
    num=lambda t:set(re.findall(r'(?<![\w.])\d+\.\d+(?:e-?\d+)?(?![\w.])',t))
    newnum=sorted(num(b)-num(a))
    cir={c:(len(re.findall(c,a)),len(re.findall(c,b))) for c in circuits}
    rep[k]={'new_backtick':new,'failclosed_before':fc(a),'failclosed_after':fc(b),'new_numbers':newnum,'circuit_counts':cir}
json.dump(rep,open('principle_check.out.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
for k,v in rep.items():
    print(k,'new backtick',v['new_backtick']); print('  fc before',v['failclosed_before']); print('  fc after ',v['failclosed_after']); print('  new numbers',v['new_numbers'][:30]); print('  circuits(before,after)',{c:x for c,x in v['circuit_counts'].items() if x[1]>x[0]})
