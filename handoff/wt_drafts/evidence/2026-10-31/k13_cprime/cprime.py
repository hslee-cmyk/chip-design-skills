# C' card 사슬(검증 22 방식): CPG-1까지 가장 긴 직렬 사슬의 card 수(CPG-1 포함).
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
ga = json.loads(json.dumps(base))  # (가) SF-1 범위 안 -- 새 card 0
out['(가)'] = longest(ga)
gb = json.loads(json.dumps(base)); gb['PDK-X'] = ['GL-1']; gb['SF-1'] = gb['SF-1'] + ['PDK-X']  # (나) 새 선행 card(분리 병합)
out['(나) 분리 병합'] = longest(gb)
gc = json.loads(json.dumps(base)); gc['AREA-X'] = ['SF-1', 'GL-1']  # (다) DEC-79 식 card를 SF-1 뒤로(C′ 내용 밖)
out['(다)'] = longest(gc)
with open(sys.argv[1], 'w', encoding='utf-8') as fh:
    for k, (l, p) in out.items():
        fh.write('%s\t%d\t%s\n' % (k, l, ' -> '.join(p)))
