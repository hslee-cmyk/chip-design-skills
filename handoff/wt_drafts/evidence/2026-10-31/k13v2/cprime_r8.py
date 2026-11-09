# K13v2: R8을 (s2) PDK 선언 card(PD-R)에 넣는 안의 C' 사슬. 그래프 = k13_cprime/cprime_r910.py 의 base 그대로(파일에서 읽어 재사용).
# 최악 가정: PD-R이 레이아웃 행 구성 소비 card(WB-1·LA-0)와 SF-1보다 먼저 병합(같은 파일 병합 순서).
import ast, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, '..', 'k13_cprime', 'cprime_r910.py'), encoding='utf-8').read()
tree = ast.parse(src)
base = None
for node in tree.body:
    if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') == 'base':
        base = ast.literal_eval(node.value)
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
cases = {}
cases['baseline'] = dict(base)
g = {k: list(v) for k, v in base.items()}; g['PD-R'] = ['GL-1']
g['WB-1'] = g['WB-1'] + ['PD-R']; g['LA-0'] = g['LA-0'] + ['PD-R']; g['SF-1'] = g['SF-1'] + ['PD-R']
cases['(s2)+R8 PD-R -> WB-1·LA-0·SF-1 선행 최악'] = g
out = os.path.join(HERE, 'cprime_r8_out.txt')
open(out, 'w', encoding='utf-8').close()
for k, gg in cases.items():
    l, p = longest(gg)
    with open(out, 'a', encoding='utf-8') as fh:
        fh.write(k + '\t' + str(l) + '\t' + ' -> '.join(p) + '\n')
