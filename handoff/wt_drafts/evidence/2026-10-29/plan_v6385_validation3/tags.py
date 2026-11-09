import re
L=open('new_gain-budget-gmid-sizing.plan.md',encoding='utf-8').read().split('\n')
out=open('tags.txt','w',encoding='utf-8')
TAG='Q-W1 승인 시'
full='→ v6.38.5 Q-W1 승인 시 front 점 계통 offset = 실현 평가 성분 (1)(2), 성분 (3) 흡수 -- 일괄 반영 목록 N5.3 Q-W1 행'
tot=0
for i,l in enumerate(L):
    c=l.count(TAG); f=l.count(full)
    if c: out.write(f'L{i+1}: "Q-W1 승인 시" {c}회, 전체 표지 {f}회\n'); tot+=c
out.write(f'합계 "Q-W1 승인 시" = {tot}\n\n')
# 옛 규칙 출현: 성분 (3), WB-1 → DE-1, (m, w_f) READS, 판정 W
pats=[r'WB-1 → DE-1',r'\(m, w_f\) READS',r'성분 \(3\)을 더해',r'판정 W의 \(m, w_f\)',r'성분 \(3\)의 레이아웃 전',r'front 점은[^.]{0,80}성분 \(3\)']
for p in pats:
    out.write(f'### {p}\n')
    for i,l in enumerate(L):
        for m in re.finditer(p,l):
            seg=l[m.start():m.start()+700]
            tagged = TAG in seg or TAG in l[max(0,m.start()-300):m.start()]
            out.write(f'L{i+1} tag_near={tagged}: ...{l[max(0,m.start()-150):m.end()+150]}...\n')
    out.write('\n')
out.close()
