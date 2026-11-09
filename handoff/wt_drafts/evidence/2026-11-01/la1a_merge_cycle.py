"""card LA-1a(사용자 결정 O-214) 추가 뒤 병합 선행 그래프 순환 판정 -- 계획 v6.38.6 스무째 커밋 작성용.

입력: icmr4_cand_files/merge_order_cycle.py 의 판정용 그래프(사람이 읽은 간선 + 원문 조각 단언, plan/v6386 65377396)를 그대로 불러온다
      (그 스크립트의 원문 조각 단언이 실패하면 여기서도 실패 = fail-closed).
더하는 간선(스무째 커밋 계획 문언):
  LA-1a 병합 선행 = LA-1 병합 선행 가운데 LA-1a 범위가 읽는 것: card B, IT-1 + IT-2, WB-1, UB-1(+NL-1), HC-S, TB-1, HC-1(+GC-8)
     (EO-1 코드 의존 = U17 ② front 판정 배선 -- LA-1에 남음; SF-1(표 #12 -- LA-1 범위 15 (g) 몫) -- LA-1에 남음; 둘 다 LA-1a에는 SPICE 다리·파일 겹침만)
  LA-1a → LA-1(생산 LA-1a: R6 블록·출발점 L 역산 READS·출발 회귀 가드 -- LA-1이 그 위에서 층 0 조립을 짓는다)
  기존 뒤따름(정방향, 순환 확인용): LA-1 → DE-1(표 #2) → SB-1(표 #1), LA-1 → OS-2(표 #8·#9), LA-1 → LA-2
판정: 그래프 전체 순환 없음 + LA-1a가 LA-1의 자손이 아님.
출력: la1a_merge_cycle.txt
"""
import runpy, os
HERE = os.path.dirname(os.path.abspath(__file__))
g = runpy.run_path(os.path.join(HERE, 'icmr4_cand_files', 'merge_order_cycle.py'), run_name='la1a')
E = g['E']
find_cycle = g['find_cycle']
anc = g['anc']
before = {k: set(v) for k, v in E.items()}
cy0 = find_cycle(before)
NEW = [(p, 'LA-1a') for p in ('cardB', 'IT-1+IT-2', 'WB-1', 'UB-1', 'HC-S', 'TB-1', 'HC-1', 'GC-8')]
NEW += [('LA-1a', 'LA-1'), ('LA-1', 'DE-1'), ('DE-1', 'SB-1'), ('LA-1', 'OS-2'), ('LA-1', 'LA-2')]
for a, b in NEW:
    E[a].add(b)
cy = find_cycle(E)
a_la1a, _ = anc('LA-1a', E)
a_la1, _ = anc('LA-1', E)
lines = ['# la1a_merge_cycle -- 판정용 그래프(merge_order_cycle.py B, plan/v6386 65377396 원문 조각 단언 통과) + LA-1a 간선',
         f'기존 그래프 순환: {" → ".join(cy0) if cy0 else "없음"}',
         '더한 간선: ' + ', '.join(f'{a} → {b}' for a, b in NEW),
         f'더한 뒤 순환: {" → ".join(cy) if cy else "없음"}',
         f'LA-1a 병합 조상 {len(a_la1a)}: ' + ', '.join(sorted(a_la1a)),
         f'LA-1 병합 조상 {len(a_la1)}: ' + ', '.join(sorted(a_la1)),
         f'LA-1a가 LA-1의 조상: {"LA-1a" in a_la1}; LA-1이 LA-1a의 조상: {"LA-1" in a_la1a}',
         f'LA-1a 조상 ⊆ LA-1 조상: {a_la1a <= a_la1}',
         'OP-5 관계: OP-5가 LA-1a 조상인가 = ' + str('OP-5' in a_la1a) + ' (OP-5 ↔ LA-1 미고정 사실 불변)']
open(os.path.join(HERE, 'la1a_merge_cycle.txt'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
