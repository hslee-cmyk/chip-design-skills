# 검증 40 B40-M1: R9·R10 자리 대안의 C' 사슬(cprime.py 기준 그래프 재사용). C' card 사슬(검증 22 방식): CPG-1까지 가장 긴 직렬 사슬의 card 수(CPG-1 포함).
# 간선 = 계획 v6.38.6(plan/v6386 88d84f31) N6.1 card 표 '선행' 칸 + 병합 순서 규칙 표 #1~#18 + GL-1 → 엔진 card.
# card B(병합됨)는 뺌. SPICE 다리 선행 EO-1도 검증 22처럼 간선으로 셈. 통합 병합(HC-1+GC-8)은 한 마디.
import sys, json
base = {
    'IT12': ['GL-1'], 'EO-1': ['OP-3', 'IT12', 'GL-1'], 'OP-3': [],
    'HC-0': [], 'HC-D': ['HC-0'], 'HC-S': ['EO-1', 'HC-D', 'GL-1'],
    'TB-1': ['EO-1', 'GL-1'], 'XRUN-C': ['GL-1'],
    'HC-1': ['TB-1', 'HC-D', 'HC-S', 'IT12', 'EO-1', 'XRUN-C', 'GL-1'],
    'OP-7': [], 'WB-1': ['HC-S', 'OP-7', 'EO-1', 'GL-1'], 'LA-0': ['WB-1'],
    'NL-1': ['EO-1', 'GL-1'], 'SF-1': ['EO-1', 'IT12', 'GL-1'],
    'LA-1': ['WB-1', 'LA-0', 'IT12', 'NL-1', 'HC-S', 'TB-1', 'HC-1', 'EO-1', 'SF-1', 'GL-1'],
    'RS-1': ['LA-1', 'GL-1'], 'CPG-1': ['WB-1', 'RS-1', 'SF-1', 'LA-1'], 'GL-1': [],
}
def longest(g):
    memo = {}
    def f(n):
        if n in memo: return memo[n]
        best = (1, [n])
        for p in g.get(n, []):
            l, path = f(p)
            if l + 1 > best[0]: best = (l + 1, path + [n])
        memo[n] = best; return best
    return f('CPG-1')
out = {}
out['baseline'] = longest(base)
g1 = json.loads(json.dumps(base))  # (s1) R9·R10 = SF-1(가) 로더 커밋 안 -- 새 card 0
out['(s1) SF-1 안'] = longest(g1)
g2 = json.loads(json.dumps(base)); g2['PD-R'] = ['GL-1']  # (s2) 별도 card, 다른 card가 기대지 않음
out['(s2) 별도 card 독립'] = longest(g2)
g3 = json.loads(json.dumps(base)); g3['PD-R'] = ['GL-1']; g3['SF-1'] = g3['SF-1'] + ['PD-R']  # (s2) 최악: SF-1이 그 card 뒤 병합(같은 로더 파일 병합 순서)
out['(s2) SF-1 선행 최악'] = longest(g3)
g4 = json.loads(json.dumps(base)); g4['PDK-X'] = ['GL-1']; g4['SF-1'] = g4['SF-1'] + ['PDK-X']  # (나)에서 R9·R10 = 새 선행 card(PDK-X) 안
out['(나)+R9·R10 PDK-X 안'] = longest(g4)
with open(sys.argv[1], 'a', encoding='utf-8') as fh:
    for k, (l, p) in out.items():
        fh.write('%s' % k + chr(9) + '%d' % l + chr(9) + ' -> '.join(p) + chr(10))
